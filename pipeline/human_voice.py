"""Use the user's own recorded voiceover instead of the AI voice.

Usage (from /home/claude/vid4, after `python3 tts.py af_heart 1.0` has written voice/meta.json):
    python3 human_voice.py /path/to/recording.(m4a|qta|mp3|wav)
    python3 assemble.py

What it does:
  1. converts the recording to 24 kHz mono,
  2. finds the spoken chunks between pauses,
  3. transcribes each chunk (whisper tiny) and lines the chunks up with the script's sentences
     (dynamic programming on word overlap; skips chunks that match nothing, drops a retake's
     earlier attempt when the user repeated a line),
  4. writes voice/sNN.wav for every sentence (overwriting the AI voice clips), shortening long
     pauses inside a sentence. meta.json from tts.py is kept, so subtitles stay word-timed.
Prints the alignment so you can check it; exits with code 2 if any sentence matched badly.
"""
import os, re, subprocess, sys, difflib
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asr_check import transcribe
from script_data import SENTENCES

SR = 24000


def norm_words(s):
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower().replace("-", " ")).split()


def sim(a_words, b_words):
    if not a_words or not b_words:
        return 0.0
    return difflib.SequenceMatcher(None, a_words, b_words).ratio()


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0', '-ac', '1', '-ar', str(SR),
                          '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def speech_chunks(a, min_sil=0.25, min_len=0.15):
    win = int(0.02 * SR)
    n = len(a) // win
    e = np.sqrt((a[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(e)
    floor = np.percentile(db, 10)
    thr = max(floor + 12, np.percentile(db, 90) - 30)
    on = db > thr
    chunks, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j < n:
                # extend until a pause of min_sil
                k = j
                while k < n and not on[k]:
                    k += 1
                if k - j >= min_sil / 0.02 or k >= n:
                    break
                j = k + 1
                while j < n and on[j]:
                    j += 1
            s, t = i * 0.02, j * 0.02
            if t - s >= min_len:
                chunks.append([s, t])
            i = j + 1
        else:
            i += 1
    return chunks


def main(path):
    a = load(path)
    a = a / (np.abs(a).max() + 1e-9) * 0.9
    chunks = speech_chunks(a)
    texts = []
    for s, t in chunks:
        x = a[int(s * SR):int(t * SR)]
        texts.append(transcribe(resample_poly(x, 2, 3).astype(np.float32)) if t - s > 0.3 else '')
    words = [norm_words(t) for t in texts]
    sents = [norm_words(' '.join(w[1] for w in s)) for s in SENTENCES]
    sents_d = [norm_words(' '.join(w[0] for w in s)) for s in SENTENCES]  # display form (digits)
    N, M = len(sents), len(chunks)

    # DP: assign chunks in order to sentences; each sentence gets >=1 contiguous chunk group; chunks may be skipped.
    NEG = -1e9
    best = np.full((N + 1, M + 1), NEG)
    back = {}
    best[0, :] = [-0.3 * j for j in range(M + 1)]  # skipping leading chunks costs a little
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            # skip chunk j-1
            if best[i, j - 1] - 0.3 > best[i, j]:
                best[i, j] = best[i, j - 1] - 0.3
                back[(i, j)] = ('skip', j - 1)
            for k in range(max(0, j - 5), j):
                if best[i - 1, k] <= NEG / 2:
                    continue
                grp = sum((words[c] for c in range(k, j)), [])
                sc = best[i - 1, k] + 2.0 * max(sim(grp, sents[i - 1]), sim(grp, sents_d[i - 1]))
                if sc > best[i, j]:
                    best[i, j] = sc
                    back[(i, j)] = ('grp', k)
    # trace back from best end
    j = int(np.argmax(best[N]))
    i = N
    groups = [None] * N
    while i > 0:
        kind, k = back[(i, j)]
        if kind == 'skip':
            j = k
            continue
        groups[i - 1] = list(range(k, j))
        i, j = i - 1, k

    bad = False
    os.makedirs('voice', exist_ok=True)
    for i, g in enumerate(groups):
        # drop an earlier attempt if the user repeated (retake) the same words later in the group
        keep = []
        for c in g:
            later = [d for d in g if d > c]
            if any(sim(words[c], words[d]) > 0.7 and len(words[c]) >= 3 for d in later):
                continue
            keep.append(c)
        out = []
        for n_, c in enumerate(keep):
            s, t = chunks[c]
            x = a[max(0, int((s - 0.06) * SR)):int((t + 0.06) * SR)].copy()
            f = int(0.01 * SR)
            x[:f] *= np.linspace(0, 1, f)
            x[-f:] *= np.linspace(1, 0, f)
            if n_:
                out.append(np.zeros(int(0.18 * SR), np.float32))
            out.append(x)
        y = np.concatenate(out)
        wavfile.write(f'voice/s{i:02d}.wav', SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
        got = ' '.join(texts[c] for c in keep)
        score = max(sim(norm_words(got), sents[i]), sim(norm_words(got), sents_d[i]))
        flag = '' if score >= 0.45 else '   <-- CHECK'
        bad |= score < 0.45
        print(f'{i:02d} [{score:.2f}] {len(y) / SR:5.2f}s  heard: {got}{flag}')
    skipped = [c for c in range(M) if not any(c in g for g in groups)]
    if skipped:
        print('skipped chunks:', [texts[c] for c in skipped])
    sys.exit(2 if bad else 0)


if __name__ == '__main__':
    main(sys.argv[1])
