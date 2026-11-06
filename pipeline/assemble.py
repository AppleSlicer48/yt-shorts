import json, sys
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, '/home/claude/vid4')
from script_data import SENTENCES

SR = 24000
meta = json.load(open('/home/claude/vid4/voice/meta.json'))
HOP = 240  # 10 ms

def env(x):
    n = len(x) // HOP
    f = x[:n * HOP].reshape(n, HOP)
    return np.sqrt((f ** 2).mean(1) + 1e-12)

LEAD = 0.6
GAP = 0.2
TAIL = 1.75
BREAK_CHARS = ',:?;.'

track = [np.zeros(int(LEAD * SR), np.float32)]
t = LEAD
timeline = []
for i, (m, sent) in enumerate(zip(meta, SENTENCES)):
    sr, a = wavfile.read(f'/home/claude/vid4/voice/s{i:02d}.wav')
    a = a.astype(np.float32) / 32768
    e = env(a)
    thr = e.max() * 0.04
    on = np.where(e > thr)[0]
    s0 = max(0, (on[0] - 3) * HOP)
    s1 = min(len(a), (on[-1] + 6) * HOP)
    clip = a[s0:s1]
    ce = e[max(0, on[0] - 3):on[-1] + 6]
    # internal pauses
    quiet = ce < e.max() * 0.03
    runs = []
    k = 0
    while k < len(quiet):
        if quiet[k]:
            j = k
            while j < len(quiet) and quiet[j]:
                j += 1
            if k > 5 and j < len(quiet) - 5 and (j - k) >= 6:
                runs.append((k, j))
            k = j
        else:
            k += 1
    breaks = [wi for wi, (d, _) in enumerate(sent[:-1]) if d[-1] in BREAK_CHARS]
    runs_sorted = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:len(breaks)])
    # phoneme weights per display word
    ph = m['phonemes']
    weights = []
    for (s, e2) in m['spans']:
        seg = ph[s:e2]
        weights.append(max(1, sum(1 for c in seg if c not in 'ˈˌ,.!?:; ')))
    dur = len(clip) / SR
    # segment boundaries in seconds
    seg_bounds = []  # list of (word_from, word_to_inclusive, t0, t1)
    dur0 = len(clip) / SR
    if breaks and runs:
        # expected break times from proportional weights
        tot_all = sum(weights)
        exp_t = [0.03 + (dur0 - 0.08) * sum(weights[:b + 1]) / tot_all for b in breaks]
        cand = list(runs)
        chosen = []
        for et in exp_t:
            if not cand:
                chosen.append(None); continue
            best = min(cand, key=lambda r: abs((r[0] + r[1]) / 2 * HOP / SR - et))
            if abs((best[0] + best[1]) / 2 * HOP / SR - et) < 0.6:
                chosen.append(best); cand.remove(best)
            else:
                chosen.append(None)
        cuts = []
        for et, r in zip(exp_t, chosen):
            cuts.append((r[0] * HOP / SR, r[1] * HOP / SR) if r else (et, et))
        cuts.sort()
        prev_w, prev_t = 0, 0.03
        for b, (c0, c1) in zip(breaks, cuts):
            seg_bounds.append((prev_w, b, prev_t, c0 + 0.02))
            prev_w, prev_t = b + 1, c1 - 0.02
        seg_bounds.append((prev_w, len(sent) - 1, prev_t, dur - 0.05))
    else:
        seg_bounds.append((0, len(sent) - 1, 0.03, dur - 0.05))
    words = []
    for (w0, w1, t0, t1) in seg_bounds:
        ws = weights[w0:w1 + 1]
        tot = sum(ws)
        acc = t0
        for wi, wt in zip(range(w0, w1 + 1), ws):
            d = (t1 - t0) * wt / tot
            words.append({'w': sent[wi][0], 't0': round(t + acc, 3), 't1': round(t + acc + d, 3)})
            acc += d
    timeline.append({'i': i, 't0': round(t, 3), 't1': round(t + dur, 3), 'words': words})
    track.append(clip)
    t += dur
    if i < len(SENTENCES) - 1:
        track.append(np.zeros(int(GAP * SR), np.float32))
        t += GAP
track.append(np.zeros(int(TAIL * SR), np.float32))
t += TAIL
voice = np.concatenate(track)
wavfile.write('/home/claude/vid4/voice/voice.wav', SR, (np.clip(voice, -1, 1) * 32767).astype(np.int16))
json.dump({'total': len(voice) / SR, 'sentences': timeline}, open('/home/claude/vid4/voice/timeline.json', 'w'), indent=1)
print('total voice track', round(len(voice) / SR, 2))
for s in timeline:
    print(s['i'], s['t0'], s['t1'], ' '.join(f"{w['w']}@{w['t0']:.2f}" for w in s['words']))
