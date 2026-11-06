import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfilt

SR = 48000
TL = json.load(open('/home/claude/vid4/voice/timeline.json'))
EV = json.load(open('/home/claude/vid4/out/events.json'))
FPS = 30
sents = TL['sentences']
total_f = int(round(TL['total'] * FPS))
N = int(total_f / FPS * SR)
rng = np.random.default_rng(11)
t = np.arange(N) / SR

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bp', fs=SR, output='sos'), x)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'lp', fs=SR, output='sos'), x)

def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'hp', fs=SR, output='sos'), x)

def noise(n):
    return rng.uniform(-1, 1, n)

def norm(x, g):
    m = np.abs(x).max()
    return x / m * g if m > 0 else x

# ---------------------------------------------------------------- voice
sr, v = wavfile.read('/home/claude/vid4/voice/voice.wav')
v = resample_poly(v.astype(np.float32) / 32768, 2, 1)
voice = np.zeros(N, np.float32)
voice[:min(N, len(v))] = v[:N]
voice = hp(voice, 80)
voice = norm(voice, 0.8)
voice = np.tanh(voice * 1.7) / np.tanh(1.7)
voice = norm(voice, 0.88)

# ---------------------------------------------------------------- music (bouncy, curious)
def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)

BPM = 116
beat = 60 / BPM
bar = beat * 4
prog = [[65, 69, 72], [60, 64, 67], [62, 65, 69], [58, 62, 65]]  # F C Dm Bb
music = np.zeros(N, np.float32)

def pluck(f, dur=0.6, decay=0.995):
    L = int(SR / f)
    buf = rng.uniform(-1, 1, L)
    n = int(dur * SR)
    out = np.zeros(n)
    idx = 0
    for k in range(n):
        out[k] = buf[idx]
        nxt = (idx + 1) % L
        buf[idx] = decay * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    return out * np.exp(-np.arange(n) / SR * 4.0)

cache = {}
arp = np.zeros(N)
pattern = [0, 2, 1, 2, 0, 2, 1, 2]
step = beat / 2
k = 0
while k * step < N / SR:
    b = int(k * step / bar)
    ch = prog[b % 4]
    m = ch[pattern[k % 8]] + 12
    if m not in cache:
        cache[m] = pluck(note(m))
    s = cache[m]
    s0 = int(k * step * SR)
    L = min(len(s), N - s0)
    arp[s0:s0 + L] += s[:L] * (1.0 if k % 2 == 0 else 0.55)
    k += 1
arp = bp(arp, 220, 5000)
music += norm(arp, 0.5)

bass = np.zeros(N)
for b in range(int(N / SR / beat) + 1):
    ch = prog[int(b * beat / bar) % 4]
    f = note(ch[0] - 24)
    s0 = int(b * beat * SR)
    L = min(int(beat * 0.9 * SR), N - s0)
    if L <= 0:
        break
    tt = np.arange(L) / SR
    bass[s0:s0 + L] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) * (1.0 if b % 2 == 0 else 0.7)
music += norm(bass, 0.35)

perc = np.zeros(N)
kt = np.arange(int(0.25 * SR)) / SR
kick = np.sin(2 * np.pi * (48 * kt + 50 * (1 - np.exp(-kt * 35)) / 35)) * np.exp(-kt * 14)
snap_n = int(0.09 * SR)
snap = bp(noise(snap_n), 1500, 6000) * np.exp(-np.arange(snap_n) / SR * 45)
hat_n = int(0.04 * SR)
hat = hp(noise(hat_n), 7000) * np.exp(-np.arange(hat_n) / SR * 90)
b = 0
while b * beat < N / SR:
    s0 = int(b * beat * SR)
    if b % 4 in (0, 2):
        L = min(len(kick), N - s0); perc[s0:s0 + L] += kick[:L]
    else:
        L = min(len(snap), N - s0); perc[s0:s0 + L] += snap[:L] * 0.5
    s1 = int((b + 0.5) * beat * SR)
    if s1 < N:
        L = min(len(hat), N - s1); perc[s1:s1 + L] += hat[:L] * 0.25
    b += 1
music += norm(perc, 0.45)

venv = np.convolve(np.abs(voice), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode='same')
duck = 1 - 0.5 * np.clip(venv / 0.08, 0, 1)
fade = np.minimum(1, t / 0.3)
tromb = [e['t'] for e in EV if e['kind'] == 'trombone']
if tromb:
    tt0 = tromb[0] - 0.15
    fade = fade * np.clip(1 - (t - tt0) / 0.25, 0, 1) ** 1
music = norm(music, 1.0) * 0.17 * duck * fade

# ---------------------------------------------------------------- sound effects
def env_exp(n, rate):
    return np.exp(-np.arange(n) / SR * rate)

def sfx_ding(g):
    n = int(1.4 * SR); tt = np.arange(n) / SR
    f = 1975.0
    s = sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * d) for r, a, d in ((1, 1, 2.6), (2.0, 0.25, 4), (2.76, 0.35, 5), (5.4, 0.12, 8)))
    s *= np.minimum(1, tt / 0.003)
    return norm(s, g * 0.55)

def sfx_thud(g):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (42 * tt + 70 * (1 - np.exp(-tt * 18)) / 18)) * np.exp(-tt * 7)
    s += lp(noise(n), 500) * np.exp(-tt * 30) * 0.8
    return norm(s, g * 0.75)

def sfx_sizzle(g):
    n = int(1.2 * SR); tt = np.arange(n) / SR
    s = bp(noise(n), 2500, 9000)
    crack = (rng.random(n) < 0.0015).astype(float)
    crack = np.convolve(crack, np.exp(-np.arange(200) / 30), mode='same')
    s = s * (0.5 + 2.5 * crack)
    s *= np.minimum(1, tt / 0.15) * np.minimum(1, (1.2 - tt) / 0.4)
    return norm(s, g * 0.35)

def sfx_pop(g):
    n = int(0.06 * SR); tt = np.arange(n) / SR
    s = hp(noise(n), 1500) * np.exp(-tt * 260)
    s += np.sin(2 * np.pi * (300 * tt + 600 * (1 - np.exp(-tt * 80)) / 80)) * np.exp(-tt * 90) * 0.8
    return norm(s, g * 0.6)

def sfx_boom(g):
    n = int(1.3 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (38 * tt + 70 * (1 - np.exp(-tt * 10)) / 10)) * np.exp(-tt * 3.5)
    s += lp(noise(n), 1800) * np.exp(-tt * 6) * 0.9
    s += hp(noise(n), 3000) * np.exp(-tt * 18) * 0.5
    return norm(np.tanh(s * 1.5), g * 0.55)

def sfx_splat(g):
    n = int(0.45 * SR); tt = np.arange(n) / SR
    s = lp(noise(n), 1400) * np.exp(-tt * 12) * np.minimum(1, tt / 0.004)
    s += np.sin(2 * np.pi * (90 * tt + 260 * (1 - np.exp(-tt * 25)) / 25)) * np.exp(-tt * 14) * 0.7
    for k in range(5):
        o = int(rng.uniform(0.03, 0.25) * SR)
        m = int(0.02 * SR)
        if o + m < n:
            s[o:o + m] += bp(noise(m), 500, 2500) * np.exp(-np.arange(m) / SR * 150) * 0.6
    return norm(s, g * 0.6)

def sfx_rattle(g):
    n = int(0.75 * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    per = int(SR / 19)
    m = int(0.012 * SR)
    for k in range(0, n - m, per):
        amp = 0.3 + 0.7 * k / n
        s[k:k + m] += bp(noise(m), 2500, 6500) * np.exp(-np.arange(m) / SR * 300) * amp
    return norm(s, g * 0.5)

def sfx_riser(g):
    n = int(1.6 * SR); tt = np.arange(n) / SR
    f = 200 * (4.5 ** (tt / 1.6))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * (tt / 1.6) ** 1.5
    s += bp(noise(n), 1000, 6000) * (tt / 1.6) ** 2 * 0.4
    s *= np.minimum(1, (1.6 - tt) / 0.08)
    return norm(s, g * 0.35)

def sfx_cash(g):
    n = int(0.9 * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for o, f in ((0.0, 2637.0), (0.11, 3520.0)):
        i = int(o * SR)
        tq = tt[:n - i]
        s[i:] += sum(a * np.sin(2 * np.pi * f * r * tq) * np.exp(-tq * d) for r, a, d in ((1, 1, 6), (1.51, 0.5, 9), (2.73, 0.3, 12)))
        mm = int(0.02 * SR)
        s[i:i + mm] += hp(noise(mm), 4000) * 0.8
    return norm(s, g * 0.45)

def sfx_tick(g):
    n = int(0.05 * SR)
    return norm(bp(noise(n), 2000, 8000) * env_exp(n, 200), g * 0.4)

def sfx_scratch(g):
    n = int(0.45 * SR); tt = np.arange(n) / SR
    s = bp(noise(n), 1500, 4500) * (0.6 + 0.4 * np.sin(2 * np.pi * 32 * tt))
    s *= np.minimum(1, tt / 0.03) * np.minimum(1, (0.45 - tt) / 0.08)
    return norm(s, g * 0.35)

def sfx_swipe(g):
    n = int(0.22 * SR); tt = np.arange(n) / SR
    s = bp(noise(n), 800, 5000) * np.sin(np.pi * tt / 0.22) ** 2
    return norm(s, g * 0.45)

def sfx_trombone(g):
    notes = [(58, 0.25), (57, 0.25), (56, 0.25), (55, 0.62)]
    out = []
    for i, (m, d) in enumerate(notes):
        n = int(d * SR); tt = np.arange(n) / SR
        f0 = note(m)
        vib = 1 + (0.012 * np.sin(2 * np.pi * 6 * tt) * np.minimum(1, tt / 0.15) if i == 3 else 0)
        f = f0 * vib * (1 - 0.03 * np.exp(-tt * 25))
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = sum(np.sin(h * ph) / h for h in range(1, 14))
        cutoff_env = 0.3 + 0.7 * np.minimum(1, tt / 0.08)
        s = lp(s, 1700) * cutoff_env
        a = np.minimum(1, tt / 0.02) * np.minimum(1, (d - tt) / (0.05 if i < 3 else 0.25))
        out.append(s * a)
    s = np.concatenate(out)
    return norm(s, g * 0.32)


def sfx_bigpop(g):
    n = int(0.22 * SR); tt = np.arange(n) / SR
    click = hp(noise(n), 900) * np.exp(-tt * 420)
    snap = bp(noise(n), 2500, 9000) * np.exp(-tt * 900) * 0.9
    body = np.sin(2 * np.pi * (165 * tt + 120 * (1 - np.exp(-tt * 60)) / 60)) * np.exp(-tt * 55) * 0.8
    tail = lp(noise(n), 2500) * np.exp(-tt * 45) * 0.1
    return norm(click + snap + body + tail, g * 0.85)

def sfx_bloop(g):
    n = int(0.09 * SR); tt = np.arange(n) / SR
    f = 280 + 950 * tt / 0.09
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.09) ** 1.5
    return norm(s, g * 0.32)

def sfx_buzzer(g):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 105 * tt)) * 0.6 + np.sign(np.sin(2 * np.pi * 111 * tt)) * 0.4
    s = lp(s, 1800) * np.minimum(1, tt / 0.01) * np.minimum(1, (0.5 - tt) / 0.06)
    return norm(s, g * 0.33)

def sfx_wind(g):
    n = int(1.7 * SR); tt = np.arange(n) / SR
    s = bp(noise(n), 250, 1200) * np.sin(np.pi * tt / 1.7) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * 1.1 * tt))
    return norm(s, g * 0.33)

def sfx_crack(g):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    s = hp(noise(n), 2500) * np.exp(-tt * 22) * 0.6
    for o in rng.uniform(0, 0.16, 7):
        i = int(o * SR); m = int(0.006 * SR)
        s[i:i + m] += hp(noise(m), 1500) * 2.0
    s += np.sin(2 * np.pi * 85 * tt) * np.exp(-tt * 18) * 0.7
    return norm(s, g * 0.7)

def sfx_rustle(g):
    n = int(0.65 * SR); tt = np.arange(n) / SR
    am = np.clip(lp(rng.uniform(0, 1, n), 40) * 6, 0, 1) ** 2
    s = bp(noise(n), 1500, 9000) * (0.3 + 0.7 * am) * np.sin(np.pi * tt / 0.65) ** 0.7
    return norm(s, g * 0.4)

def sfx_tape(g):
    n = int(0.32 * SR); tt = np.arange(n) / SR
    s = bp(noise(n), 700, 5000) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 70 * tt))) * np.minimum(1, (0.32 - tt) / 0.05)
    return norm(s, g * 0.45)

def sfx_party(g):
    n = int(0.75 * SR); tt = np.arange(n) / SR
    f = 520 + 140 * np.minimum(1, tt / 0.15)
    ph = 2 * np.pi * np.cumsum(f) / SR
    horn = sum(np.sin(h * ph) / h for h in range(1, 9)) * np.minimum(1, tt / 0.02) * np.minimum(1, (0.75 - tt) / 0.12)
    horn = lp(horn, 3000) * 0.6
    m = int(0.05 * SR)
    horn[:m] += hp(noise(m), 1200) * np.exp(-np.arange(m) / SR * 120) * 1.5
    return norm(horn, g * 0.45)

def sfx_chime(g):
    n = int(1.6 * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.2) for f in (1046.5, 1318.5, 1568.0))
    s *= np.minimum(1, tt / 0.004)
    return norm(s, g * 0.4)

def sfx_squeak(g):
    n = int(0.24 * SR); tt = np.arange(n) / SR
    f = 700 + 500 * np.sin(np.pi * tt / 0.24) + 40 * np.sin(2 * np.pi * 32 * tt)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    s = s * np.sin(np.pi * tt / 0.24) ** 1.2
    s += lp(noise(n), 600) * np.exp(-tt * 20) * 0.4
    return norm(s, g * 0.32)

def sfx_whoosh(g, dur=0.42):
    L = int(dur * SR)
    n = noise(L)
    tt = np.arange(L) / L
    lo = lp(n, 600)
    hi = bp(n, 1500, 7000)
    w = (lo * (1 - tt) + hi * np.sin(np.pi * tt) * 0.8) * np.sin(np.pi * tt) ** 2
    return norm(w, g)

FX = {'ding': sfx_ding, 'thud': sfx_thud, 'sizzle': sfx_sizzle, 'pop': sfx_pop, 'boom': sfx_boom, 'splat': sfx_splat,
      'rattle': sfx_rattle, 'riser': sfx_riser, 'cash': sfx_cash, 'tick': sfx_tick, 'scratch': sfx_scratch,
      'swipe': sfx_swipe, 'trombone': sfx_trombone, 'bigpop': sfx_bigpop, 'bloop': sfx_bloop, 'buzzer': sfx_buzzer,
      'wind': sfx_wind, 'crack': sfx_crack, 'rustle': sfx_rustle, 'tape': sfx_tape, 'party': sfx_party, 'chime': sfx_chime,
      'squeak': sfx_squeak}

sfx = np.zeros(N)
sfx_d = np.zeros(N)
DUCKED = {'bloop', 'rustle', 'wind', 'sizzle', 'scratch', 'tape', 'squeak', 'chime', 'cash', 'party', 'ding', 'swipe', 'tick', 'bigpop'}

def add(sig, at, bus=None):
    bus = sfx if bus is None else bus
    s0 = int(at * SR)
    if s0 >= N:
        return
    a = max(0, s0)
    b = min(N, s0 + len(sig))
    bus[a:b] += sig[a - s0:b - s0]

for e in EV:
    add(FX[e['kind']](e['gain']), e['t'], sfx_d if e['kind'] in DUCKED else sfx)
# whoosh into every cut, plus one at the very start
starts = [int(round((s['t0'] - 0.06) * FPS)) for s in sents[1:]]
for f in starts:
    add(sfx_whoosh(0.26, 0.32), f / FPS - 0.1, sfx_d)
add(sfx_whoosh(0.35, 0.5)[::-1], 0.0)

mix = voice + music + sfx + sfx_d * (1 - 0.5 * np.clip(venv / 0.08, 0, 1))
# loudness: bring speech to about -15 dBFS RMS, then soft-limit the peaks
sp = np.concatenate([mix[int(x['t0'] * SR):int(x['t1'] * SR)] for x in sents])
rms = np.sqrt((sp ** 2).mean())
mix = mix * (10 ** (-15.0 / 20) / rms)
mix = np.tanh(mix * 1.05)
mix = norm(mix, 0.96)
wavfile.write('/home/claude/vid4/out/mix.wav', SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))
print('seconds', N / SR, 'events', len(EV))
