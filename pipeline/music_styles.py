"""Alternative background-music beds. make_music(style, N, SR, t, lp, hp, bp, noise, norm, rng) -> np.array
styles: 'none', 'mystery' (soft cinematic suspense), 'lofi' (mellow keys + soft beat)"""
import numpy as np


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def adsr(n, sr, a, r):
    e = np.ones(n)
    na, nr = max(1, int(a * sr)), max(1, int(r * sr))
    e[:na] = np.linspace(0, 1, min(na, n))[:n] if na <= n else np.linspace(0, 1, n)
    if nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def place(buf, sig, s0):
    if s0 >= len(buf):
        return
    L = min(len(sig), len(buf) - s0)
    buf[s0:s0 + L] += sig[:L]


def make_music(style, N, SR, t, lp, hp, bp, noise, norm, rng):
    out = np.zeros(N)
    if style == 'none':
        return out

    if style == 'mystery':
        # D minor, slow: Dm - Bb - F - C, 2 bars each at 92 bpm
        bpm = 92
        beat = 60 / bpm
        chord_len = beat * 8
        prog = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]
        pad = np.zeros(N)
        sub = np.zeros(N)
        k = 0
        while k * chord_len < N / SR:
            ch = prog[k % 4]
            s0 = int(k * chord_len * SR)
            n = int((chord_len + 0.8) * SR)
            tt = np.arange(n) / SR
            env = adsr(n, SR, 1.2, 1.4)
            sig = np.zeros(n)
            for m in ch[1:]:
                f = note(m)
                for det in (-0.12, 0.12):
                    ff = f * 2 ** (det / 12)
                    # soft saw-like (few harmonics)
                    for h, a in ((1, 1.0), (2, 0.35), (3, 0.18), (4, 0.08)):
                        sig += a * np.sin(2 * np.pi * ff * h * tt + rng.uniform(0, 6.28))
            place(pad, sig * env, s0)
            fs = note(ch[0] - 12)
            place(sub, np.sin(2 * np.pi * fs * tt) * env, s0)
            k += 1
        pad = lp(pad, 1400)
        out += norm(pad, 0.55)
        out += norm(sub, 0.35)
        # heartbeat-like soft pulse on beats 1 and 1-and
        pulse = np.zeros(N)
        kt = np.arange(int(0.3 * SR)) / SR
        thump = np.sin(2 * np.pi * (45 * kt + 30 * (1 - np.exp(-kt * 30)) / 30)) * np.exp(-kt * 11)
        b = 0
        while b * beat < N / SR:
            if b % 4 == 0:
                place(pulse, thump, int(b * beat * SR))
                place(pulse, thump * 0.6, int((b + 0.5) * beat * SR))
            b += 1
        out += norm(pulse, 0.4)
        # sparse music-box bell notes
        bells = np.zeros(N)
        scale = [74, 77, 81, 79, 76, 74, 72, 69]
        b = 0
        while b * beat * 2 < N / SR:
            m = scale[b % len(scale)]
            n = int(1.6 * SR)
            tt = np.arange(n) / SR
            f = note(m)
            s = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 2.6)
            place(bells, s * (1.0 if b % 2 == 0 else 0.6), int(b * beat * 2 * SR))
            b += 1
        out += norm(lp(bells, 6000), 0.22)
        return out

    if style == 'lofi':
        # Fmaj7 - Em7 - Dm7 - Cmaj7 at 80 bpm, one bar each
        bpm = 80
        beat = 60 / bpm
        bar = beat * 4
        prog = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
        keys = np.zeros(N)
        bass = np.zeros(N)
        k = 0
        while k * bar < N / SR:
            ch = prog[k % 4]
            for hit, (off, vel) in enumerate(((0, 1.0), (2.5, 0.6))):
                s0 = int((k * bar + off * beat) * SR)
                n = int(2.4 * SR)
                tt = np.arange(n) / SR
                sig = np.zeros(n)
                for i, m in enumerate(ch):
                    f = note(m + 12)
                    strum = i * 0.012
                    tt2 = np.clip(tt - strum, 0, None)
                    tone = np.sin(2 * np.pi * f * tt2) + 0.25 * np.sin(2 * np.pi * f * 2 * tt2) * np.exp(-tt2 * 4)
                    sig += tone * np.exp(-tt2 * 1.4) * (tt >= strum)
                sig *= 1 + 0.15 * np.sin(2 * np.pi * 4.5 * tt)  # tremolo (electric piano feel)
                place(keys, sig * vel, s0)
            n = int(bar * SR)
            tt = np.arange(n) / SR
            place(bass, np.sin(2 * np.pi * note(ch[0] - 12) * tt) * np.exp(-tt * 1.2), int(k * bar * SR))
            k += 1
        out += norm(lp(keys, 3200), 0.55)
        out += norm(bass, 0.35)
        drums = np.zeros(N)
        kt = np.arange(int(0.3 * SR)) / SR
        kick = np.sin(2 * np.pi * (50 * kt + 40 * (1 - np.exp(-kt * 30)) / 30)) * np.exp(-kt * 12)
        sn = int(0.18 * SR)
        snare = lp(bp(noise(sn), 900, 5000), 4000) * np.exp(-np.arange(sn) / SR * 22)
        hn = int(0.05 * SR)
        hat = hp(noise(hn), 6000) * np.exp(-np.arange(hn) / SR * 70)
        b = 0
        while b * beat < N / SR:
            s0 = int(b * beat * SR)
            if b % 4 in (0,):
                place(drums, kick, s0)
            if b % 4 == 2:
                place(drums, kick * 0.8, int((b + 0.5) * beat * SR))
            if b % 2 == 1:
                place(drums, snare * 0.5, s0)
            for h in range(2):
                place(drums, hat * (0.22 if h == 0 else 0.12), int((b + h * 0.55) * beat * SR))
            b += 1
        out += norm(drums, 0.4)
        crackle = np.zeros(N)
        idx = rng.integers(0, N, int(N / SR * 25))
        crackle[idx] = rng.uniform(-1, 1, len(idx))
        out += norm(bp(crackle, 1500, 8000), 0.05)
        return out

    raise ValueError(style)
