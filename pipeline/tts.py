import json, re, sys
import numpy as np
import onnxruntime as ort
from scipy.io import wavfile
sys.path.insert(0, '/home/claude/vid4')
from script_data import SENTENCES

K = '/home/claude/dl/kokoro-multi-lang-v1_0'
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'am_michael'
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.1
SR = 24000

vocab = {}
for line in open(f'{K}/tokens.txt', encoding='utf-8'):
    line = line.rstrip('\n')
    if not line:
        continue
    tok, idx = line[:-1].rsplit(' ', 1)[0] if False else None, None
    parts = line.rsplit(' ', 1)
    sym = parts[0] if parts[0] != '' else ' '
    vocab[sym] = int(parts[1])
if ' ' not in vocab:
    vocab[' '] = 16

lex = {}
for line in open(f'{K}/lexicon-us-en.txt', encoding='utf-8'):
    p = line.rstrip('\n').split(' ')
    if p[0] not in lex:
        lex[p[0]] = ''.join(p[1:])

MANUAL = {
    'betty': 'bˈɛɾi', 'minutes': 'mˈɪnəts',
    'havilland': 'hˈævɪlənd', 'de': 'də', 'comets': 'kˈɑməts', 'the': 'ðə', 'a': 'ɐ', 'ullrich': 'ˈʊlɹɪk', 'palms': 'pˈɑmz',
    'swallowed': 'swˈɑlOd', 'raced': 'ɹˈAst', 'centuries': 'sˈɛnʧəɹiz', 'bodies': 'bˈɑdiz', 'to': 'tə',
    'forties': 'fˈɔɹtiz', 'raytheon': 'ɹˈAθiˌɑn', 'percy': 'pˈɜɹsi', 'gets': 'ɡˈɛts',
    'chavannes': 'ʃɑvˈɑn', 'sealed': 'sˈild', 'ibm': 'ˌIbˌiˈɛm',
    'coover': 'kˈuvəɹ', 'joyner': 'ʤˈYnəɹ', 'canopies': 'kˈænəpiz', 'hardens': 'hˈɑɹdᵊnz', 'tv': 'tˌivˈi', 'realized': 'ɹˈiəlˌIzd', 'howe': 'hˈW', 'noticed': 'nˈOtɪst', 'goldman': 'ɡˈOldmən', 'orla': 'ˈɔɹlə', 'thirties': 'θˈɜɹtiz', 'wanted': 'wˈɑntɪd', 'ed': 'ˈɛd', 'frisbie': 'fɹˈɪzbi', 'hated': 'hˈAɾɪd', 'headrick': 'hˈɛdɹɪk', 'lucile': 'lusˈil', 'morrison': 'mˈɔɹɪsən', 'opened': 'ˈOpənd', 'renamed': 'ɹinˈAmd', 'students': 'stˈudᵊnts', 'kutol': 'kjˈutɔl', 'zufall': 'zˈufɔl', "mcvicker's": 'məkvˈɪkəɹz', 'cans': 'kˈænz', 'remembers': 'ɹəmˈɛmbəɹz', 'lockheed': 'lˈɑkhˌid', "that's": 'ðˈæts', 'epperson': 'ˈɛpəɹsən', 'epsicle': 'ˈɛpsɪkᵊl', "pop's": 'pˈɑps', 'patented': 'pˈætᵊntɪd', 'waited': 'wˈAɾɪd', 'icicle': 'ˈIsɪkᵊl', 'oh': 'ˈO', "here's": 'hˈɪɹz', "it's": 'ˈɪts',
}
VOWEL_START = set('aeiouæɑɐɒɔəɛɜɪʊʌAIOWYˈˌ')

def word_ph(w, nxt=None):
    w = w.lower()
    if w == 'the' and nxt is not None:
        nph = word_ph(nxt)
        first = nph.lstrip('ˈˌ')[:1]
        return 'ði' if first in 'aeiouæɑɐɒɔəɛɜɪʊʌAIOWY' else 'ðə'
    if w in MANUAL:
        return MANUAL[w]
    if w in lex:
        return lex[w]
    for suf, add in (("'s", 'z'), ('s', 'z')):
        if w.endswith(suf) and w[:-len(suf)] in lex:
            return lex[w[:-len(suf)]] + add
    raise KeyError(w)

PUNCT = set(',.!?:;')

def sentence_phonemes(sent):
    """Returns phoneme string plus per-display-word phoneme spans."""
    items = []  # (display_index, spoken_word, trailing_punct)
    for di, (disp, spoken) in enumerate(sent):
        ws = spoken.split(' ')
        for j, w in enumerate(ws):
            m = re.match(r"^(.*?)([,.!?:;]*)$", w)
            items.append((di, m.group(1), m.group(2)))
    out = ''
    spans = {}
    for k, (di, w, p) in enumerate(items):
        nxt = items[k + 1][1] if k + 1 < len(items) else None
        ph = word_ph(w, nxt)
        if out and not out.endswith(' '):
            out += ' '
        s = len(out)
        out += ph
        out += p
        e = len(out)
        if di in spans:
            spans[di] = (spans[di][0], e)
        else:
            spans[di] = (s, e)
    return out, [spans[i] for i in range(len(sent))]

sess = ort.InferenceSession(f'/home/claude/dl/kokoro/kokoro-v1.0.onnx', providers=['CPUExecutionProvider'])
voices = np.load('/home/claude/dl/kokoro/voices-v1.0.bin')
vstyle = voices[VOICE]

meta = []
for i, sent in enumerate(SENTENCES):
    ps, spans = sentence_phonemes(sent)
    toks = [vocab[c] for c in ps if c in vocab]
    dropped = [c for c in ps if c not in vocab]
    if dropped:
        print('dropped', dropped)
    style = vstyle[len(toks)]
    audio = sess.run(None, {'tokens': np.array([[0, *toks, 0]], dtype=np.int64),
                            'style': style.astype(np.float32),
                            'speed': np.array([SPEED], dtype=np.float32)})[0]
    wavfile.write(f"/home/claude/vid4/voice/s{i:02d}.wav", SR, (np.clip(audio,-1,1)*32767).astype(np.int16))
    meta.append({'i': i, 'phonemes': ps, 'spans': spans, 'dur': len(audio) / SR})
    print(i, f'{len(audio)/SR:.2f}s', ps)

json.dump(meta, open('/home/claude/vid4/voice/meta.json', 'w'), ensure_ascii=False, indent=1)
print('total', sum(m['dur'] for m in meta))
