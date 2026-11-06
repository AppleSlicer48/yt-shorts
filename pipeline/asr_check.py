import base64, glob, sys
import numpy as np
import onnxruntime as ort
from scipy.io import wavfile
from scipy.signal import resample_poly

D = '/home/claude/dl/sherpa-onnx-whisper-tiny.en'
enc = ort.InferenceSession(f'{D}/tiny.en-encoder.onnx', providers=['CPUExecutionProvider'])
dec = ort.InferenceSession(f'{D}/tiny.en-decoder.onnx', providers=['CPUExecutionProvider'])
toks = {}
for line in open(f'{D}/tiny.en-tokens.txt'):
    p = line.split()
    if len(p) == 2:
        toks[int(p[1])] = base64.b64decode(p[0])

def mel_filters(sr=16000, n_fft=400, n_mels=80):
    def hz_to_mel(f):
        f = np.asarray(f, float)
        f_sp = 200.0 / 3
        mels = f / f_sp
        min_log_hz = 1000.0
        min_log_mel = min_log_hz / f_sp
        logstep = np.log(6.4) / 27.0
        return np.where(f >= min_log_hz, min_log_mel + np.log(np.maximum(f, 1e-10) / min_log_hz) / logstep, mels)
    def mel_to_hz(m):
        m = np.asarray(m, float)
        f_sp = 200.0 / 3
        freqs = f_sp * m
        min_log_hz = 1000.0
        min_log_mel = min_log_hz / f_sp
        logstep = np.log(6.4) / 27.0
        return np.where(m >= min_log_mel, min_log_hz * np.exp(logstep * (m - min_log_mel)), freqs)
    fftfreqs = np.linspace(0, sr / 2, n_fft // 2 + 1)
    mel_f = mel_to_hz(np.linspace(hz_to_mel(0), hz_to_mel(sr / 2), n_mels + 2))
    fdiff = np.diff(mel_f)
    ramps = mel_f[:, None] - fftfreqs[None, :]
    w = np.zeros((n_mels, len(fftfreqs)))
    for i in range(n_mels):
        lower = -ramps[i] / fdiff[i]
        upper = ramps[i + 2] / fdiff[i + 1]
        w[i] = np.maximum(0, np.minimum(lower, upper))
    enorm = 2.0 / (mel_f[2:n_mels + 2] - mel_f[:n_mels])
    w *= enorm[:, None]
    return w

MEL = mel_filters()

def log_mel(x):
    x = np.pad(x, (200, 200), mode='reflect')
    win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(400) / 400)
    n = 1 + (len(x) - 400) // 160
    frames = np.lib.stride_tricks.as_strided(x, (n, 400), (x.strides[0] * 160, x.strides[0]))
    spec = np.abs(np.fft.rfft(frames * win, axis=1)) ** 2
    spec = spec[:-1]
    m = MEL @ spec.T
    lm = np.log10(np.maximum(m, 1e-10))
    lm = np.maximum(lm, lm.max() - 8.0)
    return ((lm + 4.0) / 4.0).astype(np.float32)

def transcribe(x16):
    x16 = np.concatenate([x16, np.zeros(16000 * 30 - len(x16), np.float32)])
    mel = log_mel(x16)[None, :, :3000]
    ck, cv = enc.run(None, {'mel': mel})
    sk = np.zeros((4, 1, 448, 384), np.float32)
    sv = np.zeros((4, 1, 448, 384), np.float32)
    seq = [50257, 50362]
    out = []
    tokens = np.array([seq], np.int64)
    offset = 0
    for _ in range(120):
        logits, sk, sv = dec.run(None, {'tokens': tokens, 'in_n_layer_self_k_cache': sk, 'in_n_layer_self_v_cache': sv,
                                        'n_layer_cross_k': ck, 'n_layer_cross_v': cv, 'offset': np.array([offset], np.int64)})
        offset += tokens.shape[1]
        nxt = int(logits[0, -1].argmax())
        if nxt == 50256:
            break
        out.append(nxt)
        tokens = np.array([[nxt]], np.int64)
    return b''.join(toks.get(t, b'') for t in out).decode('utf-8', 'replace').strip()

if __name__ == '__main__':
    sr, a = wavfile.read(sys.argv[1])
    a = a.astype(np.float32) / 32768
    a16 = resample_poly(a, 2, 3).astype(np.float32)
    # chunk on given boundaries or 25 s
    step = 16000 * 25
    for k in range(0, len(a16), step):
        print(transcribe(a16[k:k + step]))
