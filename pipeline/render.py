import json, math, os, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '/home/claude/vid4')
from engine import *
from scenes import SCENES

FPS = 30
OUT = '/home/claude/vid4/out'
os.makedirs(OUT, exist_ok=True)
TL = json.load(open('/home/claude/vid4/voice/timeline.json'))
SENTS = TL['sentences']
TOTAL_F = int(round(TL['total'] * FPS))

starts = [0] + [int(round((s['t0'] - 0.06) * FPS)) for s in SENTS[1:]]
ends = starts[1:] + [TOTAL_F]
SHOTS = list(zip(starts, ends))

# ---------------------------------------------------------------- captions
def clean(w):
    w = w.rstrip(',.:;')
    return w if any(ch.isdigit() for ch in w) else w.upper()

CHUNKS = []  # each: {'t0', 'words': [(text, t0, t1)]}
for s in SENTS:
    cur = []
    for k, w in enumerate(s['words']):
        cur.append(w)
        text = ' '.join(clean(x['w']) for x in cur)
        nxt = s['words'][k + 1] if k + 1 < len(s['words']) else None
        brk = w['w'][-1] in ',.:;?!' or len(cur) >= 3 or nxt is None
        if nxt is not None and not brk:
            if len(text + ' ' + clean(nxt['w'])) > 15:
                brk = True
        if brk:
            CHUNKS.append({'t0': cur[0]['t0'] - 0.03, 'words': [(clean(x['w']), x['t0'], x['t1']) for x in cur]})
            cur = []
for i, c in enumerate(CHUNKS):
    c['t1'] = CHUNKS[i + 1]['t0'] if i + 1 < len(CHUNKS) else TL['total'] + 1

YELLOW = (255, 209, 42)
_cap = {}

def caption_sprite(ci, active):
    key = (ci, active)
    if key in _cap:
        return _cap[key]
    words = [w[0] for w in CHUNKS[ci]['words']]
    size = 104
    while True:
        f = font(size)
        sp = f.getlength(' ')
        widths = [f.getlength(w) for w in words]
        tw = sum(widths) + sp * (len(words) - 1)
        if tw <= 940 or size <= 60:
            break
        size -= 4
    stroke = max(6, size // 10)
    asc, desc = f.getmetrics()
    h = asc + desc + stroke * 2 + 40
    w = int(tw + stroke * 2 + 60)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    shadow_l = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow_l)
    d = ImageDraw.Draw(im)
    x = 30 + stroke
    y = 20 + stroke
    for k, (word, ww) in enumerate(zip(words, widths)):
        ds.text((x, y + 7), word, font=f, fill=(0, 0, 0, 200), stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
        x += ww + sp
    shadow_l = shadow_l.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(shadow_l)
    x = 30 + stroke
    for k, (word, ww) in enumerate(zip(words, widths)):
        col = YELLOW if k == active else (255, 255, 255)
        d.text((x, y), word, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
        x += ww + sp
    _cap[key] = im
    return im

def draw_caption(frame, T):
    ci = None
    for i, c in enumerate(CHUNKS):
        if c['t0'] <= T < c['t1']:
            ci = i
            break
    if ci is None:
        return
    c = CHUNKS[ci]
    active = 0
    for k, (_, t0, t1) in enumerate(c['words']):
        if T >= t0 - 0.02:
            active = k
    sp = caption_sprite(ci, active)
    k = (T - c['t0']) / 0.14
    s = 0.8 + 0.2 * ease_back(k, 2.5) if k < 1 else 1.0
    paste_center(frame, sp, W / 2, 1275, scale=s)

# ---------------------------------------------------------------- camera
def camera(img, z, fx, fy, rot):
    r = math.radians(rot)
    ca, sa = math.cos(r), math.sin(r)
    hw, hh = (W / 2) * S / z, (H / 2) * S / z
    ew = hw * abs(ca) + hh * abs(sa)
    eh = hh * abs(ca) + hw * abs(sa)
    k = max(ew / (PW / 2), eh / (PH / 2), 1.0)
    if k > 1:
        z *= k * 1.001
        hw, hh = (W / 2) * S / z, (H / 2) * S / z
        ew = hw * abs(ca) + hh * abs(sa)
        eh = hh * abs(ca) + hw * abs(sa)
    fx = min(max(fx, ew), PW - ew)
    fy = min(max(fy, eh), PH - eh)
    sc = S / z
    # output (x,y) -> input: rotate about screen centre then scale
    a = sc * ca; b = -sc * sa
    d = sc * sa; e = sc * ca
    c = fx - a * (W / 2) - b * (H / 2)
    f = fy - d * (W / 2) - e * (H / 2)
    return img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), Image.BILINEAR)

# ---------------------------------------------------------------- hook banner
# Big text hook visible from frame 0 (stops the swipe before the voice even lands).
try:
    from script_data import HOOK_TEXT
except Exception:
    HOOK_TEXT = None
HOOK_SECS = 3.0
_hook = {}

def hook_sprite():
    if 'sp' in _hook:
        return _hook['sp']
    lines = HOOK_TEXT.upper().split('\n')
    size = 96
    while True:
        f = font(size)
        if max(f.getlength(l) for l in lines) <= 900 or size <= 56:
            break
        size -= 4
    asc, desc = f.getmetrics()
    lh = asc + desc
    w = int(max(f.getlength(l) for l in lines)) + 80
    h = lh * len(lines) + 50
    sp = Image.new('RGBA', (w + 20, h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    d.rounded_rectangle([10, 18, w + 10, h + 18], radius=28, fill=(0, 0, 0, 120))
    d.rounded_rectangle([10, 6, w + 10, h + 6], radius=28, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=6)
    for k, l in enumerate(lines):
        lw_ = f.getlength(l)
        d.text((10 + (w - lw_) / 2, 6 + 25 + k * lh), l, font=f, fill=(15, 15, 20))
    _hook['sp'] = sp
    return sp

def draw_hook(frame, T):
    if not HOOK_TEXT or T >= HOOK_SECS:
        return
    sp = hook_sprite()
    a = 1.0 if T < HOOK_SECS - 0.25 else (HOOK_SECS - T) / 0.25
    if a < 1:
        sp = sp.copy()
        sp.putalpha(sp.split()[3].point(lambda v: int(v * a)))
    frame.paste(sp, ((W - sp.width) // 2, 210), sp)

# ---------------------------------------------------------------- shots
def make_scene(i):
    s = SENTS[i]
    f0, f1 = SHOTS[i]
    st = f0 / FPS
    words = [{'w': w['w'], 't0': w['t0'] - st, 't1': w['t1'] - st} for w in s['words']]
    sc = SCENES[i](words, (f1 - f0) / FPS, i)
    return sc, f0, f1

def frame_at(sc, plate, f0, f):
    t = (f - f0) / FPS
    img = plate.copy()
    sc.dyn(img, t)
    z, fx, fy, rot = sc.cam(t)
    fr = camera(img, z, fx, fy, rot).convert('RGB')
    if hasattr(sc, 'post'):
        sc.post(fr, t)
    draw_caption(fr, f / FPS)
    draw_hook(fr, f / FPS)
    return fr

def render_shot(i):
    t_start = time.time()
    sc, f0, f1 = make_scene(i)
    plate = sc.plate()
    tmp = f'{OUT}/shot_{i:02d}.part.mp4'
    final = f'{OUT}/shot_{i:02d}.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                          '-pix_fmt', 'yuv420p', '-r', str(FPS), '-f', 'mp4', tmp], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame_at(sc, plate, f0, f).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, final)
    return i, f1 - f0, time.time() - t_start

def stills(which, frac=0.85):
    out = []
    for i in which:
        sc, f0, f1 = make_scene(i)
        plate = sc.plate()
        fs = frac if isinstance(frac, (list, tuple)) else [frac]
        for q in fs:
            f = min(f1 - 1, f0 + int((f1 - f0) * q))
            im = frame_at(sc, plate, f0, f)
            path = f'{OUT}/still_{i:02d}_{int(q*100):02d}.png'
            im.save(path)
            out.append(path)
    return out

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        which = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else range(len(SENTS))
        fr = [float(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else [0.85]
        for p in stills(which, fr):
            print(p)
    elif mode == 'shots':
        from multiprocessing import Pool
        which = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else list(range(len(SENTS)))
        # longest first for better packing
        which.sort(key=lambda i: -(SHOTS[i][1] - SHOTS[i][0]))
        with Pool(2) as pool:
            for i, n, dt in pool.imap_unordered(render_shot, which):
                print(f'shot {i}: {n} frames in {dt:.1f}s', flush=True)
    elif mode == 'events':
        ev = []
        for i in range(len(SENTS)):
            sc, f0, f1 = make_scene(i)
            if hasattr(sc, 'events'):
                for (tr, kind, gain) in sc.events():
                    if tr > sc.dur - 0.03:
                        continue
                    ev.append({'t': round(f0 / FPS + tr, 3), 'kind': kind, 'gain': gain})
        ev.sort(key=lambda e: e['t'])
        json.dump(ev, open(f'{OUT}/events.json', 'w'), indent=1)
        for e in ev:
            print(e)
    elif mode == 'info':
        print('total frames', TOTAL_F, 'shots', SHOTS)
        for c in CHUNKS:
            print(round(c['t0'], 2), [w[0] for w in c['words']])
