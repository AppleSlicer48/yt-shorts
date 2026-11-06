import math
import calendar as _cal
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from scipy.ndimage import gaussian_filter
from engine import *
from base_scenes import pegboard, ARM_LIGHT, CX, CY, plate_img, grain_map, stone_tex
from mw_scenes import Scene, glow, stamp_sprite, bill_sprite, rgb, bench

WALL_H = 1580

# ====================================================================== utilities
_CH = {}

def C(*a, **k):
    key = (a, tuple(sorted(k.items())))
    if key not in _CH:
        _CH[key] = chip(*a, **k)
    return _CH[key]

class OV:
    """Small RGBA overlay for blended drawing onto the frame."""
    def __init__(self, img, x0, y0, x1, y1):
        self.img, self.x0, self.y0 = img, int(x0), int(y0)
        self.im = Image.new('RGBA', (max(1, int(x1) - int(x0)), max(1, int(y1) - int(y0))), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, x, y):
        return (x - self.x0, y - self.y0)

    def pts(self, pts):
        return [(x - self.x0, y - self.y0) for x, y in pts]

    def box(self, x0, y0, x1, y1):
        return (x0 - self.x0, y0 - self.y0, x1 - self.x0, y1 - self.y0)

    def commit(self):
        paste_at(self.img, self.im, self.x0, self.y0)

def keyframes(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, a), (t1, b) in zip(kf[:-1], kf[1:]):
        if t <= t1:
            u = ease_in_out((t - t0) / max(1e-6, t1 - t0))
            return tuple(av + (bv - av) * u for av, bv in zip(a, b))
    return kf[-1][1]

def stamp_in(img, sp, cx, cy, t, t0):
    if t < t0:
        return
    u = clamp01((t - t0) / 0.14)
    paste_center(img, sp, cx, cy, scale=2.3 - 1.3 * ease_out(u), alpha=clamp01(u * 2))

class S(Scene):
    def __init__(self, words, dur, idx):
        super().__init__(words, dur, idx)
        self.shakes = self.make_shakes()

    def make_shakes(self):
        return []

# ====================================================================== bubble wrap
_BUB = {}

def bubble_sprite(r):
    if r in _BUB:
        return _BUB[r]
    pad = int(r * 0.45) + 6
    n = 2 * r + 2 * pad
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2.0
    dx, dy = (xx - c) / r, (yy - c) / r
    d = np.sqrt(dx * dx + dy * dy)
    inside = np.clip((1 - d) * r + 0.5, 0, 1)
    sd = np.sqrt((dx - 0.15) ** 2 + (dy - 0.22) ** 2)
    sh = gaussian_filter(np.clip(1.06 - sd, 0, 1), r * 0.1) * 0.30
    q = np.clip(d, 0, 0.999)
    nz = np.sqrt(1 - q * q)
    nx, ny = dx * (d < 1), dy * (d < 1)
    ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
    fres = (1 - nz) ** 2.0
    body_a = (0.07 + 0.5 * fres) * inside
    body_c = np.stack([0.90 + 0.10 * ndl, 0.95 + 0.05 * ndl, np.ones_like(ndl)], -1)
    ring = np.exp(-((d - 0.88) / 0.07) ** 2) * inside * 0.28
    spec = np.clip(ndh ** 55 * 1.7, 0, 1) * inside
    g2 = np.exp(-(((dx - 0.45) / 0.15) ** 2 + ((dy - 0.5) / 0.09) ** 2)) * inside * 0.4
    P = np.zeros((n, n, 3), np.float32)
    A = np.zeros((n, n), np.float32)
    for col, al in ((np.zeros(3, np.float32), sh * (1 - 0.7 * inside)),
                    (body_c, body_a),
                    (np.array([0.22, 0.27, 0.33], np.float32), ring),
                    (np.ones(3, np.float32), spec),
                    (np.ones(3, np.float32), g2)):
        P = col * al[..., None] + P * (1 - al[..., None])
        A = al + A * (1 - al)
    out = np.where(A[..., None] > 1e-4, P / np.maximum(A[..., None], 1e-4), 0)
    arr = np.concatenate([np.clip(out, 0, 1), np.clip(A, 0, 1)[..., None]], -1)
    im = Image.fromarray((arr * 255 + 0.5).astype(np.uint8), 'RGBA')
    _BUB[r] = im
    return im

_POPPED = {}

def popped_sprite(r, seed=0):
    key = (r, seed)
    if key in _POPPED:
        return _POPPED[key]
    rng = np.random.default_rng(seed)
    S_ = 2 * r + 24
    ss = 2
    im = Image.new('RGBA', (S_ * ss, S_ * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S_ * ss / 2
    pts = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        rr = r * ss * rng.uniform(0.74, 1.0)
        pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr * 0.92))
    d.polygon(pts, fill=(235, 242, 248, 46), outline=(255, 255, 255, 150))
    for k in range(6):
        a = rng.uniform(0, math.pi)
        L = r * ss * rng.uniform(0.5, 1.0)
        ox, oy = rng.uniform(-0.45, 0.45, 2) * r * ss
        x0, y0 = c + ox - math.cos(a) * L / 2, c + oy - math.sin(a) * L / 2
        x1, y1 = c + ox + math.cos(a) * L / 2, c + oy + math.sin(a) * L / 2
        mx, my = (x0 + x1) / 2 + rng.normal(0, 5), (y0 + y1) / 2 + rng.normal(0, 5)
        d.line([(x0 + 3, y0 + 4), (mx + 3, my + 4), (x1 + 3, y1 + 4)], fill=(50, 60, 70, 60), width=4)
        d.line([(x0, y0), (mx, my), (x1, y1)], fill=(255, 255, 255, 175), width=4)
    im = im.resize((S_, S_), Image.LANCZOS)
    _POPPED[key] = im
    return im

def pop_burst(img, cx, cy, r, k):
    if not (0 < k < 1):
        return
    R = r * 3.3
    ov = OV(img, cx - R, cy - R, cx + R, cy + R)
    al = int(255 * (1 - k) ** 1.3)
    w = max(3, int(r * 0.15))
    for i in range(8):
        a = i * math.pi / 4 + 0.35
        r0, r1 = r * (1.05 + 0.9 * k), r * (1.45 + 1.6 * k)
        ov.d.line(ov.pts([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)]),
                  fill=(255, 255, 255, al), width=w)
    ov.commit()

def draw_press_bubble(img, x, y, r, t, t_press, t_pop, seed=0):
    if t < t_press:
        paste_center(img, bubble_sprite(r), x, y)
    elif t < t_pop:
        u = (t - t_press) / max(1e-3, t_pop - t_press)
        sp = bubble_sprite(r)
        w = int(sp.width * (1 + 0.12 * u))
        h = int(sp.height * (1 - 0.32 * u))
        paste_center(img, sp.resize((w, h), Image.BICUBIC), x, y + r * 0.12 * u)
    else:
        paste_center(img, popped_sprite(r, seed), x, y)
        pop_burst(img, x, y, r, (t - t_pop) / 0.22)

def hex_positions(x0, y0, x1, y1, sp):
    pts = []
    row = 0
    y = y0
    while y <= y1:
        x = x0 + (sp / 2 if row % 2 else 0)
        while x <= x1:
            pts.append((round(x, 1), round(y, 1)))
            x += sp
        y += sp * 0.866
        row += 1
    return pts

def paste_bubbles(img, pts, r):
    b = bubble_sprite(r)
    for (x, y) in pts:
        paste_center(img, b, x, y)

# ====================================================================== wooden pointing hand
def hand_sprite(L, ang, color=ARM_LIGHT):
    S_ = int(L * 2.5)
    lay = Layer(S_, S_)
    tx, ty = S_ * 0.5, S_ * 0.5
    ca, sa = math.cos(ang), math.sin(ang)

    def g(x, y):
        return (tx + (x * ca - y * sa) * L, ty + (x * sa + y * ca) * L)

    col = hexc(color)
    j = col * 0.86
    gr = (0.94 + 0.12 * smooth_noise(S_, S_, 6, 77, 2)).astype(np.float32)
    kw = dict(grain=gr, spec=0.28, shin=22)
    capsule(lay, g(-1.1, 0.1), g(-0.48, 0.05), 0.095 * L, 0.08 * L, col, **kw)
    sphere(lay, g(-0.48, 0.05), 0.08 * L, j, **kw)
    for (x, y, r) in ((-0.215, 0.07, 0.04), (-0.228, 0.126, 0.038), (-0.245, 0.177, 0.034)):
        capsule(lay, g(x, y), g(x - 0.075, y + 0.02), r * L * 0.92, r * L * 0.85, col, **kw)
        sphere(lay, g(x, y), r * L, j, **kw)
    ellipsoid(lay, g(-0.335, 0.06), 0.155 * L, 0.12 * L, ang, col, **kw)
    capsule(lay, g(-0.37, -0.06), g(-0.255, -0.105), 0.042 * L, 0.036 * L, col, **kw)
    sphere(lay, g(-0.255, -0.105), 0.036 * L, j, **kw)
    sphere(lay, g(-0.21, 0.0), 0.04 * L, j, **kw)
    capsule(lay, g(-0.21, 0), g(-0.11, 0), 0.037 * L, 0.035 * L, col, **kw)
    sphere(lay, g(-0.11, 0), 0.035 * L, j, **kw)
    capsule(lay, g(-0.11, 0), g(-0.033, 0), 0.034 * L, 0.031 * L, col, **kw)
    sp, x0, y0 = layer_sprite(lay, 2)
    return sp, (tx - x0, ty - y0)

def shadow_of(sp, blur=10, alpha=0.42):
    a = sp.getchannel('A').point(lambda v: int(v * alpha))
    sh = Image.new('RGBA', sp.size, (0, 0, 0, 0))
    sh.putalpha(a)
    pad = 2 * blur
    big = Image.new('RGBA', (sp.width + 2 * pad, sp.height + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(sh, (pad, pad))
    return big.filter(ImageFilter.GaussianBlur(blur)), pad

_HANDS = {}

def get_hand(L, ang):
    key = (int(L), round(ang, 3))
    if key not in _HANDS:
        sp, off = hand_sprite(L, ang)
        sh, pad = shadow_of(sp, blur=max(6, int(L * 0.035)))
        _HANDS[key] = (sp, off, sh, pad)
    return _HANDS[key]

def draw_hand(img, hand, tip, lift=0.0):
    sp, off, sh, pad = hand
    sx, sy = 14 + 60 * lift, 20 + 80 * lift
    paste_at(img, sh, int(tip[0] - off[0] - pad + sx), int(tip[1] - off[1] - pad + sy))
    paste_at(img, sp, int(tip[0] - off[0]), int(tip[1] - off[1]))

# ====================================================================== rooms and props
def wallpaper_tex(w, h, c1='#8FD0BD', c2='#A9DDCB', motif='#F3ECD6', stripe=108, seed=2):
    img = Image.new('RGB', (w, h), rgb(c2))
    d = ImageDraw.Draw(img)
    for k, x in enumerate(range(0, w + stripe, stripe)):
        if k % 2 == 0:
            d.rectangle((x, 0, x + stripe - 1, h), fill=rgb(c1))
        d.line([(x, 0), (x, h)], fill=rgb(motif), width=3)
    for k, x in enumerate(range(stripe // 2, w + stripe, stripe)):
        if k % 2 == 1:
            for y in range(60, h, 150):
                s = 16
                d.polygon([(x, y - s), (x + s * 0.7, y), (x, y + s), (x - s * 0.7, y)], fill=rgb(motif))
    arr = to_arr(img)
    n = smooth_noise(h, w, 60, seed, 3)
    return arr * (0.93 + 0.09 * n[..., None])

def floor_and_wall(wall_arr):
    arr = np.zeros((PH, PW, 3), np.float32)
    arr[:WALL_H] = wall_arr
    fl = wood(PW, PH - WALL_H, '#9A6A40', '#5E3A1E', seed=4, stretch=10, rings=16, contrast=0.45)
    arr[WALL_H:] = fl * np.linspace(1.0, 0.62, PH - WALL_H)[:, None, None]
    arr[WALL_H - 44:WALL_H] = hexc('#F4EEE2') * np.linspace(1.06, 0.8, 44)[:, None, None]
    return arr

def wall_room(seed=1):
    arr = floor_and_wall(wallpaper_tex(PW, WALL_H, seed=seed))
    arr[:WALL_H - 44] = arr[:WALL_H - 44] * 0.93 + 0.055
    arr *= (0.55 + 0.6 * radial(PW, PH, CX, 820, 1500, 1.2))[..., None]
    return plate_img(vignette(arr, 0.4))

def wall_bubbles(img, r=26, sp=64, skip_near=None):
    pts = hex_positions(10, 10, PW - 10, WALL_H - 74, sp)
    target = None
    if skip_near is not None:
        target = min(pts, key=lambda p: (p[0] - skip_near[0]) ** 2 + (p[1] - skip_near[1]) ** 2)
    paste_bubbles(img, [p for p in pts if p != target], r)
    return target

def frame_sprite(w=470, h=370):
    m = 30
    im = Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((m + 14, m + 20, m + w + 14, m + h + 20), fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    fimg = to_img(vgrad(w, h, [(0, '#F2D27A'), (0.5, '#C9952E'), (1, '#8E6118')])).convert('RGBA')
    d = ImageDraw.Draw(fimg)
    b = 34
    pw_, ph_ = w - 2 * b, h - 2 * b
    pimg = to_img(vgrad(pw_, ph_, [(0, '#7EC3F0'), (0.6, '#CDEBFA'), (1, '#CDEBFA')]))
    pd = ImageDraw.Draw(pimg)
    pd.ellipse((pw_ * 0.68, ph_ * 0.12, pw_ * 0.68 + 60, ph_ * 0.12 + 60), fill=(255, 214, 90))
    pd.polygon([(0, ph_ * 0.7), (pw_ * 0.3, ph_ * 0.45), (pw_ * 0.62, ph_ * 0.72), (pw_, ph_ * 0.5), (pw_, ph_), (0, ph_)], fill=(92, 168, 92))
    pd.polygon([(0, ph_ * 0.86), (pw_ * 0.45, ph_ * 0.62), (pw_, ph_ * 0.9), (pw_, ph_), (0, ph_)], fill=(60, 130, 70))
    fimg.paste(pimg, (b, b))
    d.rectangle((b - 4, b - 4, w - b + 3, h - b + 3), outline=(110, 75, 20), width=4)
    d.rectangle((2, 2, w - 3, h - 3), outline=(255, 236, 170), width=3)
    im.alpha_composite(fimg, (m, m))
    return im

def sofa(img, cx=CX, y_seat=1430, w=920, color='#E0703F'):
    lay = Layer()
    x0, x1 = cx - w / 2, cx + w / 2
    c = hexc(color)
    for x in (x0 + 150, x1 - 150):
        capsule(lay, (x - 10, y_seat + 50), (x - 24, y_seat + 150), 13, 10, '#5A3A1E', spec=0.3)
    capsule(lay, (x0 + 120, y_seat - 170), (x1 - 120, y_seat - 170), 100, 100, c, spec=0.22, shin=18)
    for k in range(3):
        xa = x0 + 150 + k * (w - 300) / 3
        ellipsoid(lay, (xa + (w - 300) / 6, y_seat - 168), (w - 300) / 6 - 6, 92, 0, c * 1.04, spec=0.22, shin=18)
    capsule(lay, (x0 + 100, y_seat + 6), (x1 - 100, y_seat + 6), 72, 72, c * 0.9, spec=0.2, shin=18)
    for x in (x0 + 52, x1 - 52):
        capsule(lay, (x, y_seat - 130), (x, y_seat + 30), 64, 64, c * 0.96, spec=0.22, shin=18)
    sp, X, Y = layer_sprite(lay, 2)
    shd, pad = shadow_of(sp, 18, 0.45)
    paste_at(img, shd, X - pad + 26, Y - pad + 30)
    paste_at(img, sp, X, Y)

# ====================================================================== 0 hook: popping the wallpaper
class Hook(S):
    def make_shakes(self):
        return [(self.we('WALLPAPER') + 0.04, 18, 0.32)]

    def events(self):
        return [(0.30, 'bigpop', 1.0), (self.we('WALLPAPER') + 0.04, 'thud', 0.85)]

    def plate(self):
        img = wall_room(seed=1)
        self.r = 26
        self.target = wall_bubbles(img, self.r, 64, skip_near=(910, 860))
        paste_center(img, frame_sprite(), CX - 130, 640)
        sofa(img)
        self.hand = get_hand(330, -2.25)
        self.stamp = stamp_sprite('WALLPAPER?!', 116)
        return img

    def cam(self, t):
        tx, ty = getattr(self, 'target', (910, 860))
        k = ease_in_out((t - 0.45) / 0.75)
        z = 2.7 + (1.04 - 2.7) * k + 0.04 * clamp01((t - 1.2) / 1.5)
        fx = tx + (CX - tx) * k
        fy = ty + (1000 - ty) * k
        dx, dy, dr = self.shake(t)
        return z, fx + dx, fy + dy, dr

    def dyn(self, img, t):
        x, y = self.target
        draw_press_bubble(img, x, y, self.r, t, 0.12, 0.30, seed=3)
        hx, hy, lift = keyframes(t, [(0.0, (x + 110, y + 150, 1.0)), (0.12, (x, y, 0.0)), (0.34, (x, y, 0.0)),
                                     (0.8, (x + 430, y + 580, 1.0))])
        if t < 0.85:
            draw_hand(img, self.hand, (hx, hy), lift)
        stamp_in(img, self.stamp, CX, 330, t, self.we('WALLPAPER'))

# ====================================================================== 1 garage: two shower curtains
def curtain_sprite(w, h, base, seed, stripes=False):
    xs = np.arange(w, dtype=np.float32)
    fold = 0.78 + 0.24 * np.sin(xs / w * 2 * np.pi * 6.5 + seed)
    arr = np.ones((h, w, 3), np.float32) * hexc(base)[None, None, :] * fold[None, :, None]
    if stripes:
        band = ((xs // 46) % 2 == 0).astype(np.float32)
        arr = arr * (1 - 0.12 * band[None, :, None]) + 0.12 * band[None, :, None]
    arr = arr + 0.25 * np.clip(np.sin(xs / w * 2 * np.pi * 6.5 + seed + 0.9), 0, 1)[None, :, None] ** 8
    yy = np.arange(h, dtype=np.float32)[:, None]
    bottom = h - 18 - 10 * np.sin(xs / w * 2 * np.pi * 6.5 + seed)
    alpha = 0.66 * np.clip(bottom[None, :] - yy, 0, 1)
    rgba = np.concatenate([np.clip(arr, 0, 1), alpha[..., None]], -1)
    im = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    for x in range(20, w, 56):
        d.ellipse((x - 10, 0, x + 10, 20), fill=(205, 210, 215, 255), outline=(120, 125, 130, 255), width=3)
    return im

class Curtains(S):
    def events(self):
        tA = self.we('AIR') - 0.25
        span = max(0.6, self.we('inside', 't1') - tA - 0.1)
        ev = [(self.we('sealed') - 0.5, 'swipe', 0.5), (self.we('SHOWER'), 'sizzle', 0.45)]
        ev += [(tA + span * k / 9, 'bloop', 0.4 + 0.05 * (k % 3)) for k in range(9)]
        return ev

    def plate(self):
        arr = pegboard()
        arr = bench(arr, 1340, 1440)
        img = plate_img(arr)
        ov = OV(img, CX - 200, 0, CX + 200, 360)
        ov.d.line(ov.pts([(CX, 0), (CX, 120)]), fill=(30, 30, 30, 255), width=6)
        ov.d.rectangle(ov.box(CX - 20, 112, CX + 20, 140), fill=(60, 62, 66, 255))
        ov.commit()
        glow(img, CX, 175, 190, (255, 220, 150), 0.55)
        lay = Layer(200, 200)
        sphere(lay, (100, 100), 38, '#FFF3C8', spec=0.9, shin=30, amb=0.9)
        sp, x0, y0 = layer_sprite(lay, 2)
        paste_at(img, sp, CX - 100 + x0, 175 - 100 + y0)
        lay = Layer()
        capsule(lay, (40, 470), (PW - 40, 470), 13, 13, '#DADFE4', spec=0.8, shin=60)
        for x in (40, PW - 40):
            sphere(lay, (x, 470), 22, '#B9BFC6', spec=0.7, shin=50)
        sp, x0, y0 = layer_sprite(lay, 2)
        paste_at(img, sp, x0, y0)
        self.cw, self.ch, self.top = 500, 862, 462
        self.cL = curtain_sprite(self.cw, self.ch, '#8FD3F5', 0.3)
        self.cR = curtain_sprite(self.cw, self.ch, '#F6A9C4', 1.7, stripes=True)
        xc = CX - self.cw / 2
        self.bpts = hex_positions(xc + 46, self.top + 80, xc + self.cw - 40, self.top + self.ch - 64, 74)
        self.order = np.random.default_rng(7).permutation(len(self.bpts))
        self.r = 30
        self.film = Image.new('RGBA', (self.cw, self.ch - 30), (235, 242, 250, 70))
        return img

    def cam(self, t):
        z, fx, fy, rot = super().cam(t)
        k = ease_in_out((t - self.we('AIR') + 0.45) / 0.9)
        return z + 0.3 * k, fx, fy + (880 - fy) * k, rot

    def xs(self, t):
        tS = self.we('sealed')
        u = ease_in_out((t - (tS - 0.55)) / 0.65)
        xl0, xr0 = 70, PW - 70 - self.cw
        xc = CX - self.cw / 2
        return xl0 + (xc - xl0) * u, xr0 + (xc - xr0) * u

    def dyn(self, img, t):
        xl, xr = self.xs(t)
        paste_at(img, self.cR, int(xr), self.top)
        paste_at(img, self.cL, int(xl), self.top)
        t0, t1 = self.we('SHOWER') - 0.05, self.we('together') + 0.3
        if t0 <= t <= t1:
            u = clamp01((t - t0) / (t1 - t0))
            yb = self.top + 40 + (self.ch - 80) * u
            x0, x1 = xl - 14, xl + self.cw + 14
            ov = OV(img, x0 - 40, yb - 80, x1 + 40, yb + 80)
            for k, (hh, a) in enumerate(((62, 30), (40, 55), (24, 95), (12, 170), (5, 255))):
                ov.d.rounded_rectangle(ov.box(x0, yb - hh, x1, yb + hh), radius=hh, fill=(255, 120 + 30 * k, 40 + 45 * k, a))
            ov.d.rectangle(ov.box(x0 - 20, yb - 34, x1 + 20, yb - 16), fill=(70, 74, 80, 255))
            ov.d.rectangle(ov.box(x0 - 20, yb - 34, x1 + 20, yb - 29), fill=(170, 176, 184, 255))
            ov.commit()
        tA = self.we('AIR') - 0.25
        span = max(0.6, self.we('inside', 't1') - tA - 0.1)
        if t > tA - 0.2:
            f = self.film.copy()
            f.putalpha(f.getchannel('A').point(lambda v, k=clamp01((t - tA + 0.2) / 0.5): int(v * k)))
            paste_at(img, f, int(CX - self.cw / 2), self.top + 20)
        n = len(self.bpts)
        b = bubble_sprite(self.r)
        for rank, idx in enumerate(self.order):
            ti = tA + span * rank / n
            if t < ti:
                continue
            x, y = self.bpts[idx]
            if t - ti < 0.2:
                paste_center(img, b, x, y, scale=max(0.05, ease_back((t - ti) / 0.2, 2.2)))
            else:
                paste_center(img, b, x, y)
        pop(img, C('1957  ·  HAWTHORNE, NEW JERSEY', 44, dot=(240, 160, 60)), CX, 300, t, 0.1,
            out_t=self.we('Alfred') - 0.25)
        pop(img, C('ALFRED FIELDING & MARC CHAVANNES', 40), CX, 300, t, self.we('Alfred') - 0.05)

# ====================================================================== 2 the wallpaper flop
def roll_sprite(w, R):
    h = 2 * R
    ys = np.linspace(-1, 1, h)
    shade = 0.5 + 0.6 * np.sqrt(np.clip(1 - ys ** 2, 0, 1)) - 0.12 * ys
    arr = wallpaper_tex(w, h, seed=9) * shade[:, None, None]
    arr = arr + 0.35 * np.exp(-((ys + 0.45) / 0.12) ** 2)[:, None, None]
    body = to_img(arr).convert('RGBA')
    cap = int(R * 0.38)
    im = Image.new('RGBA', (w + 2 * cap + 4, h + 4), (0, 0, 0, 0))
    im.paste(body, (cap + 2, 2))
    d = ImageDraw.Draw(im)
    for cx in (cap + 2, cap + 2 + w):
        d.ellipse((cx - cap, 2, cx + cap, h + 2), fill=(236, 230, 214, 255), outline=(150, 140, 120, 255), width=2)
        for k in range(1, 6):
            f = k / 6
            d.ellipse((cx - cap * f, 2 + R * (1 - f), cx + cap * f, 2 + R * (1 + f)), outline=(170, 160, 140, 255), width=1)
        d.ellipse((cx - cap * 0.22, 2 + R * 0.78, cx + cap * 0.22, 2 + R * 1.22), fill=(120, 90, 60, 255))
    return im

class WallpaperFlop(S):
    def make_shakes(self):
        return [(self.we('FLOPPED', 't1') - 0.1, 14, 0.3)]

    def events(self):
        return [(0.12, 'rustle', 0.55), (self.we('FLOPPED', 't1') - 0.02, 'buzzer', 0.8)]

    def plate(self):
        wall = vgrad(PW, WALL_H, [(0, '#F1E7D3'), (1, '#E0D0B2')]) * (0.94 + 0.08 * smooth_noise(WALL_H, PW, 80, 5, 3))[..., None]
        arr = floor_and_wall(wall)
        arr *= (0.55 + 0.6 * radial(PW, PH, CX, 820, 1500, 1.2))[..., None]
        img = plate_img(vignette(arr, 0.4))
        # paste bucket and brush
        lay = Layer()
        capsule(lay, (195, 1590), (195, 1700), 92, 92, '#B8BEC6', spec=0.6, shin=40)
        ellipsoid(lay, (195, 1585), 92, 26, 0, '#E9E2CF', spec=0.3)
        capsule(lay, (230, 1440), (205, 1585), 9, 9, '#8A5A30', spec=0.3)
        sp, x0, y0 = layer_sprite(lay, 2)
        shd, pad = shadow_of(sp, 14, 0.4)
        paste_at(img, shd, x0 - pad + 20, y0 - pad + 24)
        paste_at(img, sp, x0, y0)
        self.sx0, self.sw, self.sy0, self.sy1 = CX - 280, 560, 300, 1310
        sh = self.sy1 - self.sy0
        st = to_img(wallpaper_tex(self.sw, sh, seed=3) * 0.93 + 0.055).convert('RGBA')
        for (x, y) in hex_positions(26, 22, self.sw - 26, sh - 22, 64):
            paste_center(st, bubble_sprite(26), x, y)
        self.strip = st
        self.strip_sh, self.sh_pad = shadow_of(st, 12, 0.35)
        self.roll = roll_sprite(self.sw + 30, 52)
        self.stamp = stamp_sprite('FLOP!', 170)
        return img

    def dyn(self, img, t):
        t0, t1 = 0.12, self.we('WALLPAPER') + 0.3
        u = ease_in_out((t - t0) / (t1 - t0))
        yr = self.sy0 + (self.sy1 - self.sy0) * u
        tF = self.we('FLOPPED')
        if t < tF:
            h = int(yr - self.sy0)
            if h > 2:
                p = self.sh_pad
                paste_at(img, self.strip_sh.crop((0, 0, self.strip_sh.width, h + 2 * p)), self.sx0 - p + 14, self.sy0 - p + 18)
                paste_at(img, self.strip.crop((0, 0, self.sw, h)), self.sx0, self.sy0)
            paste_center(img, self.roll, CX, yr)
        else:
            dt = t - tF
            dy = 0.5 * 5200 * dt * dt
            rot = -12 * ease_out(dt / 0.5)
            spr = self.strip.rotate(rot, resample=Image.BICUBIC, expand=True)
            paste_center(img, spr, CX + 50 * dt, (self.sy0 + self.sy1) / 2 + dy)
            paste_center(img, self.roll, CX + 80 * dt, self.sy1 + dy * 1.1)
            stamp_in(img, self.stamp, CX, 520, t, self.we('FLOPPED', 't1') - 0.1)
        pop(img, C('NEW!  TEXTURED WALLPAPER', 48, bg=(255, 210, 60)), CX, 200, t, self.we('TEXTURED') - 0.05, out_t=tF)

# ====================================================================== 3 the greenhouse flop
def tumbleweed_sprite(R=95, seed=4):
    rng = np.random.default_rng(seed)
    S_ = 2 * R + 20
    ss = 2
    im = Image.new('RGBA', (S_ * ss, S_ * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S_ * ss / 2
    for k in range(90):
        a0 = rng.uniform(0, 360)
        span = rng.uniform(60, 200)
        rr = rng.uniform(0.25, 0.95) * R * ss
        ox, oy = rng.normal(0, R * 0.22 * ss, 2)
        col = tuple(int(v) for v in np.array([150, 108, 58]) * rng.uniform(0.55, 1.1))
        d.arc((c + ox - rr, c + oy - rr, c + ox + rr, c + oy + rr), a0, a0 + span, fill=col + (255,), width=int(rng.integers(3, 7)))
    im = im.resize((S_, S_), Image.LANCZOS)
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).ellipse((S_ / 2 - R, S_ / 2 - R, S_ / 2 + R, S_ / 2 + R), fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel('A'), m))
    return im

class Greenhouse(S):
    def make_shakes(self):
        return [(self.we('TOO', 't1') - 0.08, 12, 0.28)]

    def events(self):
        return [(self.we('That') - 0.2, 'wind', 0.55), (self.we('TOO', 't1'), 'buzzer', 0.75)]

    def plate(self):
        arr = vgrad(PW, PH, [(0, '#6DB4E6'), (0.42, '#CBE8F7'), (0.55, '#EAF6FB'), (1, '#EAF6FB')])
        arr = arr + hexc('#FFF0B8') * (radial(PW, PH, 1120, 250, 650, 2.0) * 0.55)[..., None]
        lay = Layer()
        xs = list(range(0, PW + 9, 9))
        fill_poly(lay, [(x, 1130 - 55 * math.sin(x / 240.0) - 35 * math.sin(x / 105.0 + 1.3)) for x in xs] + [(PW, 1400), (0, 1400)], '#93C98F')
        arr = lay.comp(arr)
        g0 = 1250
        grass = vgrad(PW, PH - g0, [(0, '#74BC5E'), (1, '#2E6A2A')])
        arr[g0:] = grass * (0.88 + 0.18 * smooth_noise(PH - g0, PW, 10, 3, 2))[..., None]
        gx0, gx1, gy0, gy1 = 228, 1068, 770, 1262
        apex = (CX, 520)
        poly = [(gx0, gy0), apex, (gx1, gy0), (gx1, gy1), (gx0, gy1)]
        # contact shadow
        sh = np.zeros((PH, PW), np.float32)
        sh[gy1 - 8:gy1 + 26, gx0 - 10:gx1 + 30] = 1
        arr = shadow(arr, sh, 10, 6, 14, 0.4)
        img = plate_img(arr)
        sun = Image.new('RGBA', (240, 240), (0, 0, 0, 0))
        ImageDraw.Draw(sun).ellipse((40, 40, 200, 200), fill=(255, 236, 160, 255))
        paste_center(img, sun.filter(ImageFilter.GaussianBlur(3)), 1120, 250)
        inter = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
        di = ImageDraw.Draw(inter)
        di.polygon(poly, fill=(190, 218, 200, 255))
        di.rectangle((gx0, 1088, gx1, 1112), fill=(140, 100, 62, 255))
        di.rectangle((gx0, 1112, gx1, gy1), fill=(112, 142, 118, 255))
        img.alpha_composite(inter)
        arr = to_arr(img)
        lay = Layer()
        for k, x in enumerate(range(gx0 + 95, gx1 - 40, 132)):
            for j in range(6):
                a = -math.pi / 2 + (j - 2.5) * 0.45
                lx, ly = x + math.cos(a) * 44, 968 + math.sin(a) * 54
                ellipsoid(lay, (lx, ly), 36, 17, a, '#4FA34A' if (j + k) % 2 else '#3E8C3B', spec=0.3)
            fill_poly(lay, [(x - 42, 1010), (x + 42, 1010), (x + 32, 1088), (x - 32, 1088)], '#C8693A')
            fill_poly(lay, [(x - 48, 998), (x + 48, 998), (x + 48, 1018), (x - 48, 1018)], '#DD8A55')
        arr = lay.comp(arr)
        img = plate_img(arr)
        mask = Image.new('L', (PW, PH), 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        glass = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
        dg = ImageDraw.Draw(glass)
        dg.polygon(poly, fill=(225, 245, 252, 70))
        for x0 in (gx0 + 40, gx0 + 330, gx0 + 600):
            dg.polygon([(x0, gy1), (x0 + 90, gy1), (x0 + 330, 480), (x0 + 240, 480)], fill=(255, 255, 255, 42))
        glass.putalpha(ImageChops.multiply(glass.getchannel('A'), mask))
        img.alpha_composite(glass)
        pts = [p for p in hex_positions(gx0 + 10, 520, gx1 - 10, gy1 - 10, 48)
               if mask.getpixel((int(p[0]), int(p[1]))) and mask.getpixel((int(min(PW - 1, p[0] + 16)), int(max(0, p[1] - 16)))) and mask.getpixel((int(max(0, p[0] - 16)), int(max(0, p[1] - 16))))]
        paste_bubbles(img, pts, 19)
        fr = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
        df = ImageDraw.Draw(fr)
        bars = [((gx0, gy0), apex), (apex, (gx1, gy0)), ((gx0, gy0), (gx1, gy0)), ((gx0, 1015), (gx1, 1015)), ((gx0, gy1), (gx1, gy1)),
                ((gx0, gy0), (gx0, gy1)), ((gx1, gy0), (gx1, gy1)), (apex, (CX, gy1)), ((gx0 + 210, gy0 - 210 * 250 / 420), (gx0 + 210, gy1)),
                ((gx1 - 210, gy0 - 210 * 250 / 420), (gx1 - 210, gy1))]
        for (a, b_) in bars:
            df.line([(a[0] + 6, a[1] + 7), (b_[0] + 6, b_[1] + 7)], fill=(0, 0, 0, 60), width=16)
        for (a, b_) in bars:
            df.line([a, b_], fill=(246, 246, 240, 255), width=16)
        img.alpha_composite(fr)
        self.tw = tumbleweed_sprite()
        self.stamp = stamp_sprite('FLOPPED AGAIN', 120)
        return img

    def dyn(self, img, t):
        pop(img, C('GREENHOUSE INSULATION?', 50, bg=(150, 220, 120)), CX, 330, t, self.we('GREENHOUSE') - 0.05,
            out_t=self.we('TOO') - 0.25)
        t0 = self.we('That') - 0.15
        if t >= t0:
            u = (t - t0) / 1.7
            if u < 1:
                x = -200 + (PW + 400) * u
                y = 1215 - abs(math.sin(u * math.pi * 3)) * 90
                spr = self.tw.rotate(-u * 900, resample=Image.BICUBIC)
                paste_center(img, spr, x, y)
        stamp_in(img, self.stamp, CX, 360, t, self.we('TOO', 't1') - 0.08)

# ====================================================================== 4/5 the IBM 1401 room
def box_sprite(front, dep, top_col, side_col):
    w, h = front.size
    dx, dy = dep * 0.72, dep * 0.52
    Wd, Ht = int(w + dx + 4), int(h + dy + 4)
    X0, Y0 = 2, int(dy) + 2
    im = Image.new('RGBA', (Wd, Ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(X0, Y0), (X0 + w, Y0), (X0 + w + dx, Y0 - dy), (X0 + dx, Y0 - dy)], fill=top_col)
    d.polygon([(X0 + w, Y0), (X0 + w + dx, Y0 - dy), (X0 + w + dx, Y0 + h - dy), (X0 + w, Y0 + h)], fill=side_col)
    im.alpha_composite(front, (X0, Y0))
    return im, (X0, Y0)

def shade_v(img, k0=1.08, k1=0.82):
    a = np.asarray(img, np.float32)
    g = np.linspace(k0, k1, a.shape[0])[:, None, None]
    a[..., :3] *= g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

class IBMRoom(S):
    MX, MY, MW, MH = 90, 770, 620, 510
    TX, TY, TW, TH = 800, 520, 330, 760

    def make_shakes(self):
        try:
            return [(self.we('BREAKING') + 0.02, 22, 0.4)]
        except KeyError:
            return []

    def events(self):
        return [(self.we('BREAKING') + 0.02, 'crack', 0.85)]

    def room_plate(self):
        wall = vgrad(PW, PH, [(0, '#B9C6D2'), (0.55, '#A3B1BE'), (1, '#8796A4')])
        arr = wall * (0.95 + 0.07 * smooth_noise(PH, PW, 70, 21, 3))[..., None]
        for y in range(160, 1280, 180):
            arr[y:y + 3] *= 0.86
            arr[y + 3:y + 5] *= 1.06
        img = plate_img(arr)
        lay = Layer()
        tile = Image.new('RGB', (800, 400), (205, 209, 213))
        td = ImageDraw.Draw(tile)
        for r_ in range(4):
            for c_ in range(8):
                td.rectangle((c_ * 100 + 2, r_ * 100 + 2, c_ * 100 + 97, r_ * 100 + 97), fill=(214 - 8 * ((r_ + c_) % 2), 218 - 8 * ((r_ + c_) % 2), 222 - 8 * ((r_ + c_) % 2)))
        quad(lay, tile, [(-500, 1280), (PW + 500, 1280), (PW + 1600, PH + 200), (-1600, PH + 200)])
        arr = lay.comp(to_arr(img))
        arr = arr * (0.45 + 0.75 * radial(PW, PH, CX, 950, 1400, 1.3))[..., None]
        img = plate_img(vignette(arr, 0.45))
        # main processing unit
        f = Image.new('RGBA', (self.MW, self.MH), rgb('#D2D6DA') + (255,))
        d = ImageDraw.Draw(f)
        d.rectangle((24, 24, self.MW - 24, 222), fill=rgb('#2E3F50') + (255,))
        self.lamps = []
        for r_ in range(3):
            for c_ in range(12):
                x = 60 + c_ * (self.MW - 120) / 11
                y = 62 + r_ * 40
                d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(70, 80, 92, 255))
                self.lamps.append((self.MX + x, self.MY + y))
        for k in range(10):
            x = 64 + k * 54
            d.rounded_rectangle((x - 10, 176, x + 10, 206), 4, fill=(222, 222, 226, 255))
        d.rectangle((24, 240, self.MW / 2 - 6, self.MH - 44), outline=(160, 165, 170, 255), width=3)
        d.rectangle((self.MW / 2 + 6, 240, self.MW - 24, self.MH - 44), outline=(160, 165, 170, 255), width=3)
        d.rounded_rectangle((self.MW / 2 - 42, 320, self.MW / 2 - 28, 410), 6, fill=(150, 155, 160, 255))
        d.rounded_rectangle((self.MW / 2 + 28, 320, self.MW / 2 + 42, 410), 6, fill=(150, 155, 160, 255))
        d.rectangle((0, self.MH - 34, self.MW, self.MH), fill=(70, 76, 84, 255))
        main, off = box_sprite(shade_v(f), 110, (226, 229, 232, 255), (150, 156, 163, 255))
        # tape drive
        f = Image.new('RGBA', (self.TW, self.TH), rgb('#CBD0D5') + (255,))
        d = ImageDraw.Draw(f)
        d.rectangle((22, 26, self.TW - 22, 470), fill=rgb('#1C262F') + (255,), outline=(120, 128, 136, 255), width=5)
        d.rectangle((60, 500, 120, 700), fill=(40, 48, 56, 255))
        d.rectangle((self.TW - 120, 500, self.TW - 60, 700), fill=(40, 48, 56, 255))
        for k, c in enumerate(((220, 70, 60), (240, 200, 70), (90, 180, 100), (230, 230, 235))):
            d.rounded_rectangle((140, 512 + k * 45, self.TW - 140, 540 + k * 45), 6, fill=c + (255,))
        d.rectangle((0, self.TH - 34, self.TW, self.TH), fill=(70, 76, 84, 255))
        tape, toff = box_sprite(shade_v(f), 110, (220, 224, 228, 255), (146, 152, 160, 255))
        for sp, o, (X, Y) in ((main, off, (self.MX, self.MY)), (tape, toff, (self.TX, self.TY))):
            shd, pad = shadow_of(sp, 18, 0.45)
            paste_at(img, shd, X - o[0] - pad + 34, Y - o[1] - pad + 16)
            paste_at(img, sp, X - o[0], Y - o[1])
        self.win = (self.TX + 22, self.TY + 26, self.TX + self.TW - 22, self.TY + 470)
        self.reels = [(self.TX + self.TW / 2, self.TY + 140, 80), (self.TX + self.TW / 2, self.TY + 358, 52)]
        rng = np.random.default_rng(14)
        self.crack_c = (self.TX + self.TW / 2 + 30, self.TY + 250)
        self.cracks = []
        for k in range(9):
            a = 2 * math.pi * k / 9 + rng.normal(0, 0.2)
            pts = [self.crack_c]
            L = 0
            while L < rng.uniform(110, 230):
                L += rng.uniform(25, 45)
                aa = a + rng.normal(0, 0.25)
                pts.append((self.crack_c[0] + math.cos(aa) * L, self.crack_c[1] + math.sin(aa) * L))
            self.cracks.append(pts)
        return img

    def plate(self):
        return self.room_plate()

    def room_dyn(self, img, t):
        ov = OV(img, self.MX + 30, self.MY + 30, self.MX + self.MW - 30, self.MY + 200)
        rng = np.random.default_rng(int(t / 0.12) + 99)
        lit = rng.random(len(self.lamps)) < 0.42
        for (x, y), on in zip(self.lamps, lit):
            if on:
                ov.d.ellipse(ov.box(x - 15, y - 15, x + 15, y + 15), fill=(255, 210, 120, 70))
                ov.d.ellipse(ov.box(x - 9, y - 9, x + 9, y + 9), fill=(255, 236, 170, 255))
        ov.commit()
        x0, y0, x1, y1 = self.win
        ov = OV(img, x0, y0, x1, y1)
        for k, (cx, cy, rt) in enumerate(self.reels):
            th = (t * 210 if k == 0 else -t * 280) % 360
            R = 94
            ov.d.ellipse(ov.box(cx - rt, cy - rt, cx + rt, cy + rt), fill=(74, 52, 38, 255))
            for j in range(3):
                a0 = th + j * 120
                ov.d.pieslice(ov.box(cx - R, cy - R, cx + R, cy + R), a0, a0 + 62, fill=(176, 184, 192, 225))
            ov.d.ellipse(ov.box(cx - R, cy - R, cx + R, cy + R), outline=(196, 202, 208, 255), width=5)
            ov.d.ellipse(ov.box(cx - 24, cy - 24, cx + 24, cy + 24), fill=(205, 210, 215, 255))
            ov.d.ellipse(ov.box(cx - 8, cy - 8, cx + 8, cy + 8), fill=(60, 64, 70, 255))
        ov.commit()

    def dyn(self, img, t):
        self.room_dyn(img, t)
        pop(img, C('IBM', 54, dot=(70, 120, 200)), CX, 330, t, self.we('IBM') - 0.05, out_t=self.we('1401') - 0.15)
        pop(img, C('IBM 1401  ·  ANNOUNCED 1959', 44, dot=(70, 120, 200)), CX, 330, t, self.we('1401') - 0.05)
        tB = self.we('BREAKING') + 0.02
        if t >= tB:
            u = ease_out((t - tB) / 0.12)
            x0, y0, x1, y1 = self.win
            ov = OV(img, x0, y0, x1, y1)
            for pts in self.cracks:
                n = max(2, int(len(pts) * u + 0.999))
                seg = pts[:n]
                ov.d.line(ov.pts([(x + 2, y + 3) for x, y in seg]), fill=(0, 0, 0, 160), width=6)
                ov.d.line(ov.pts(seg), fill=(235, 245, 255, 240), width=4)
            ov.commit()
            pop(img, C('FRAGILE!', 60, bg=(230, 50, 45), fg=(255, 255, 255)), self.TX + self.TW / 2, self.TY - 120, t, tB)

def check_sprite(R=130):
    S_ = 2 * R + 60
    im = Image.new('RGBA', (S_, S_), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((30 + 8, 30 + 12, 30 + 2 * R + 8, 30 + 2 * R + 12), fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.ellipse((30, 30, 30 + 2 * R, 30 + 2 * R), fill=(60, 190, 90, 255), outline=(255, 255, 255, 255), width=10)
    c = 30 + R
    d.line([(c - R * 0.45, c + R * 0.02), (c - R * 0.1, c + R * 0.38), (c + R * 0.5, c - R * 0.35)], fill=(255, 255, 255, 255), width=int(R * 0.2), joint='curve')
    return im

def sheet_sprite(w, h, r=30, sp=74):
    im = Image.new('RGBA', (w, h), (225, 236, 246, 46))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(255, 255, 255, 120), width=4)
    for (x, y) in hex_positions(30, 30, w - 30, h - 30, sp):
        paste_center(im, bubble_sprite(r), x, y)
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    do = ImageDraw.Draw(ov)
    for x0 in (80, 420, 760):
        do.polygon([(x0, h), (x0 + 70, h), (x0 + 330, 0), (x0 + 260, 0)], fill=(255, 255, 255, 30))
    im.alpha_composite(ov)
    return im

class WrapComputer(IBMRoom):
    z0, z1 = 1.02, 1.1

    def make_shakes(self):
        return [(0.55, 10, 0.25)]

    def events(self):
        return [(0.1, 'rustle', 0.7), (self.we('PERFECT') + 0.02, 'ding', 0.6), (self.we('became') - 0.1, 'tape', 0.6),
                (self.we('CUSTOMER') + 0.05, 'cash', 0.6)]

    def plate(self):
        img = self.room_plate()
        self.sheet = sheet_sprite(1180, 900)
        self.check = check_sprite()
        return img

    def dyn(self, img, t):
        self.room_dyn(img, t)
        u = ease_out((t - 0.08) / 0.47)
        y = -950 + (420 + 950) * u
        paste_at(img, self.sheet, 58, int(y))
        tT = self.we('became') - 0.1
        if t >= tT:
            k = ease_out((t - tT) / 0.16)
            ov = OV(img, 40, 880, PW - 40, 980)
            ov.d.polygon(ov.pts([(50, 905), (50 + (PW - 100) * k, 895), (50 + (PW - 100) * k, 965), (50, 975)]), fill=(196, 150, 92, 210))
            ov.d.line(ov.pts([(50, 909), (50 + (PW - 100) * k, 899)]), fill=(240, 205, 150, 220), width=4)
            ov.commit()
        tP = self.we('PERFECT')
        if t >= tP:
            k = (t - tP) / 0.3
            s = ease_back(k, 2.4) if k < 1 else 1.0
            a = 1.0 if t < self.we('became') - 0.15 else max(0.0, 1 - (t - self.we('became') + 0.15) / 0.2)
            if a > 0:
                paste_center(img, self.check, CX, 760, scale=max(0.05, s), alpha=a)
        pop(img, C('IBM:  THEIR FIRST BIG CUSTOMER', 46, bg=(255, 210, 60)), CX, 300, t, self.we('CUSTOMER') - 0.05)

# ====================================================================== 6 billions
def upright_roll_sprite(R=150, H=560, br=21):
    ell = 0.3
    pad = 40
    W = 2 * R
    wi, hi = W + 2 * pad, int(H + 2 * R * ell + 2 * pad)
    cx, ytop = pad + R, pad + R * ell
    xs = np.arange(W, dtype=np.float32)
    u = (xs - R + 0.5) / R
    nz = np.sqrt(np.clip(1 - u * u, 0, 1))
    ndl = np.clip(u * LIGHT[0] + nz * LIGHT[2], 0, 1)
    ndh = np.clip(u * HALF[0] + nz * HALF[2], 0, 1)
    col = np.array([0.80, 0.88, 0.95])[None, :] * (0.62 + 0.45 * ndl)[:, None] + (0.55 * ndh ** 30)[:, None]
    body = np.ones((H, W, 3), np.float32) * col[None, :, :]
    yy = np.arange(H, dtype=np.float32)[:, None]
    body = body * (1.0 + 0.04 * np.sin(yy / 9.0))[..., None]
    im = Image.new('RGBA', (wi, hi), (0, 0, 0, 0))
    bimg = Image.fromarray((np.clip(body, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    m = Image.new('L', (W, H + int(R * ell)), 0)
    dm = ImageDraw.Draw(m)
    dm.rectangle((0, 0, W, H), fill=245)
    dm.ellipse((0, H - R * ell, W, H + R * ell), fill=245)
    full = Image.new('RGBA', m.size, (0, 0, 0, 0))
    full.paste(bimg, (0, 0))
    full.paste(bimg.crop((0, H - int(R * ell) - 1, W, H)).resize((W, int(R * ell) + 1)), (0, H))
    full.putalpha(m)
    im.alpha_composite(full, (pad, int(ytop)))
    b = bubble_sprite(br)
    step = 2 * math.asin(min(0.99, (br * 2.6) / (2 * R)))
    th = -1.35
    cols = []
    while th <= 1.35:
        cols.append(th)
        th += step
    for k, th in enumerate(cols):
        sx = max(0.12, math.cos(th))
        spr = b.resize((max(2, int(b.width * sx)), b.height), Image.BICUBIC)
        y = ytop + 50 + (k % 2) * 28
        while y < ytop + H - 20:
            paste_center(im, spr, cx + R * math.sin(th), y)
            y += 56
    d = ImageDraw.Draw(im)
    top = (cx - R, ytop - R * ell, cx + R, ytop + R * ell)
    d.ellipse(top, fill=(214, 228, 240, 255), outline=(150, 170, 190, 255), width=3)
    for k in range(1, 9):
        f = 0.3 + 0.7 * k / 9
        d.ellipse((cx - R * f, ytop - R * ell * f, cx + R * f, ytop + R * ell * f), outline=(170, 190, 208, 255), width=2)
    d.ellipse((cx - R * 0.3, ytop - R * ell * 0.3, cx + R * 0.3, ytop + R * ell * 0.3), fill=(184, 136, 82, 255))
    d.ellipse((cx - R * 0.2, ytop - R * ell * 0.2, cx + R * 0.2, ytop + R * ell * 0.2), fill=(52, 36, 22, 255))
    return im, (cx, ytop + H)

class Billions(S):
    def events(self):
        tB = self.we('BILLIONS')
        return [(tB, 'cash', 0.7), (tB + 0.45, 'cash', 0.5), (tB + 0.9, 'cash', 0.4)]

    def plate(self):
        arr = vgrad(PW, PH, [(0, '#1E2A3A'), (1, '#0B1018')])
        arr = arr * (0.9 + 0.2 * smooth_noise(PH, PW, 90, 8, 3))[..., None]
        fl0 = 1300
        floor = stone_tex(PW, PH - fl0, '#5B5F66', '#2E3136', seed=31, cell=80)
        arr[fl0:] = floor * np.linspace(1.0, 0.55, PH - fl0)[:, None, None]
        arr = arr * (0.4 + 0.85 * radial(PW, PH, CX, 900, 1150, 1.4))[..., None]
        img = plate_img(vignette(arr, 0.5))
        roll, base = upright_roll_sprite()
        for (x, yb, sc) in ((CX - 330, 1170, 0.82), (CX + 330, 1170, 0.82), (CX, 1295, 1.0)):
            sp = roll if sc == 1.0 else roll.resize((int(roll.width * sc), int(roll.height * sc)), Image.LANCZOS)
            bx, by = base[0] * sc, base[1] * sc
            sh = Image.new('RGBA', (int(380 * sc), int(110 * sc)), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((10, 10, sh.width - 10, sh.height - 10), fill=(0, 0, 0, 150))
            paste_center(img, sh.filter(ImageFilter.GaussianBlur(14)), x + 30 * sc, yb + 6)
            paste_at(img, sp, int(x - bx), int(yb - by))
        self.bills = [bill_sprite(k).resize((300, 128), Image.LANCZOS) for k in (1, 2, 3)]
        rng = np.random.default_rng(5)
        self.rain = [(rng.uniform(60, PW - 60), rng.uniform(-1100, -150), rng.uniform(850, 1300), rng.uniform(0, 6.28),
                      rng.uniform(-220, 220), int(rng.integers(0, 3))) for _ in range(28)]
        return img

    def dyn(self, img, t):
        tB = self.we('BILLIONS')
        if t >= tB - 0.1:
            dt = t - tB + 0.1
            for (x0, y0, vy, ph, vr, kind) in self.rain:
                y = y0 + vy * dt
                if y > PH + 150:
                    continue
                x = x0 + 70 * math.sin(t * 3.1 + ph)
                rot = vr * dt + 25 * math.sin(t * 4.2 + ph)
                spr = self.bills[kind].rotate(rot, resample=Image.BICUBIC, expand=True)
                paste_center(img, spr, x, y)
        pop(img, C('SEALED AIR  ·  FOUNDED 1960', 46, dot=(90, 170, 255)), CX, 260, t, self.we('SEALED') - 0.05, out_t=tB - 0.05)
        pop(img, C('$5.36 BILLION IN SALES (2025)', 46, bg=(120, 220, 120)), CX, 260, t, tB + 0.05)

# ====================================================================== 7 appreciation day
def calendar_sprite(year=2027, month=1, w=720):
    head, dn, cell_h = 150, 64, 100
    weeks = _cal.monthcalendar(year, month)
    h = head + dn + cell_h * len(weeks) + 24
    m = 36
    im = Image.new('RGBA', (w + 2 * m, h + 2 * m + 20), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((m + 16, m + 40, m + w + 16, m + 20 + h + 22), fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    paper = Image.new('RGBA', (w, h), (250, 247, 240, 255))
    d = ImageDraw.Draw(paper)
    d.rectangle((0, 0, w, head), fill=(214, 48, 42, 255))
    title = f'{_cal.month_name[month].upper()} {year}'
    f = font(76)
    bb = f.getbbox(title)
    d.text((w / 2 - (bb[2] + bb[0]) / 2, head / 2 + 8 - (bb[3] + bb[1]) / 2), title, font=f, fill=(255, 255, 255, 255))
    cw = w / 7
    fn = font(28, FONT_BOLD)
    for i, nm in enumerate(('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN')):
        bb = fn.getbbox(nm)
        d.text((cw * (i + 0.5) - (bb[2] + bb[0]) / 2, head + dn / 2 - (bb[3] + bb[1]) / 2), nm, font=fn, fill=(130, 118, 104, 255))
    fnum = font(48, FONT_BOLD)
    pos = {}
    for r_, wk in enumerate(weeks):
        for c_, day in enumerate(wk):
            x0, y0 = c_ * cw, head + dn + r_ * cell_h
            d.rectangle((x0, y0, x0 + cw, y0 + cell_h), outline=(226, 218, 204, 255), width=2)
            if day:
                txt = str(day)
                bb = fnum.getbbox(txt)
                col = (44, 38, 32, 255) if c_ < 5 else (204, 60, 50, 255)
                d.text((x0 + cw / 2 - (bb[2] + bb[0]) / 2, y0 + cell_h / 2 - (bb[3] + bb[1]) / 2), txt, font=fnum, fill=col)
                pos[day] = (m + x0 + cw / 2, m + 20 + y0 + cell_h / 2)
    im.alpha_composite(paper, (m, m + 20))
    d = ImageDraw.Draw(im)
    for x in (m + w * 0.25, m + w * 0.75):
        d.rounded_rectangle((x - 9, m - 4, x + 9, m + 44), 9, fill=(170, 176, 184, 255), outline=(110, 116, 124, 255), width=2)
    return im, pos

class Calendar(S):
    def events(self):
        return [(self.we('last') - 0.05, 'scratch', 0.5), (self.we('JANUARY') + 0.05, 'party', 0.75)]

    def plate(self):
        img = wall_room(seed=6)
        wall_bubbles(img, 26, 64)
        cal, pos = calendar_sprite()
        cx, cy = CX, 860
        paste_center(img, cal, cx, cy)
        ox, oy = cx - cal.width / 2, cy - cal.height / 2
        self.c25 = (ox + pos[25][0], oy + pos[25][1])
        lay = Layer(80, 80)
        sphere(lay, (40, 40), 20, '#D9342C', spec=0.6, shin=40)
        pin, _, _ = layer_sprite(lay, 2)
        paste_center(img, pin, cx, cy - cal.height / 2 + 30)
        rng = np.random.default_rng(12)
        cols = [(255, 90, 90), (255, 200, 60), (90, 200, 255), (130, 220, 120), (240, 120, 230), (255, 255, 255)]
        self.conf = [(rng.uniform(-1000, 1000), rng.uniform(-2000, -700), rng.uniform(0, 6.28), rng.uniform(-14, 14),
                      cols[int(rng.integers(0, len(cols)))], rng.uniform(14, 24)) for _ in range(80)]
        return img

    def dyn(self, img, t):
        pop(img, C('BUBBLE WRAP APPRECIATION DAY', 46, bg=(255, 210, 60)), CX, 230, t, self.we('APPRECIATION') - 0.1)
        t0, t1 = self.we('last') - 0.05, self.we('Monday') + 0.25
        if t >= t0:
            u = ease_in_out((t - t0) / (t1 - t0))
            cx, cy = self.c25
            pts = []
            n = max(2, int(64 * u))
            for k in range(n):
                a = -2.2 + 2 * math.pi * 1.1 * k / 63
                rr = 1 + 0.06 * math.sin(a * 3)
                pts.append((cx + math.cos(a) * 68 * rr, cy + math.sin(a) * 56 * rr + k * 0.12))
            ov = OV(img, cx - 100, cy - 90, cx + 100, cy + 100)
            ov.d.line(ov.pts(pts), fill=(225, 30, 40, 235), width=10, joint='curve')
            ov.commit()
        tC = self.we('JANUARY') + 0.05
        if t >= tC:
            dt = t - tC
            if dt < 2.0:
                ov = OV(img, 0, 0, PW, 1700)
                ox, oy = CX, 700
                for (vx, vy, ph, vr, col, s) in self.conf:
                    x = ox + vx * dt
                    y = oy + vy * dt + 0.5 * 2600 * dt * dt
                    if y > 1700:
                        continue
                    a = ph + vr * dt
                    ca, sa = math.cos(a), math.sin(a) * (0.4 + 0.6 * abs(math.sin(dt * 9 + ph)))
                    hw, hh = s, s * 0.5
                    q = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
                    ov.d.polygon(ov.pts([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in q]), fill=col + (255,))
                ov.commit()

# ====================================================================== 8 popping makes you calmer
def gauge_card():
    w, h = 760, 470
    m = 30
    im = Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m + 10, m + 16, m + w + 10, m + h + 16), 40, fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m, m, m + w, m + h), 40, fill=(250, 250, 252, 255))
    gc = (m + w / 2, m + 345)
    R = 270
    cols = [(225, 60, 50), (240, 140, 50), (245, 205, 60), (150, 210, 90), (70, 185, 90)]
    for i, col in enumerate(cols):
        a0 = 180 + 36 * i + 1.5
        d.arc((gc[0] - R, gc[1] - R, gc[0] + R, gc[1] + R), a0, a0 + 33, fill=col + (255,), width=62)
    f = font(34, FONT_BLACK)
    for txt, x, col in (('STRESSED', gc[0] - R + 31, (205, 55, 45)), ('CALM', gc[0] + R - 31, (50, 160, 80))):
        bb = f.getbbox(txt)
        d.text((x - (bb[2] + bb[0]) / 2, gc[1] + 40 - (bb[3] + bb[1]) / 2), txt, font=f, fill=col + (255,))
    return im, (gc[0] - im.width / 2, gc[1] - im.height / 2)

class Calm(S):
    def pop_times(self):
        tp0 = self.we('POPPING') - 0.3
        return [tp0 + 0.27 * k for k in range(5)]

    def events(self):
        return [(tt, 'bigpop', 0.6) for tt in self.pop_times()] + [(self.we('CALMER', 't1'), 'chime', 0.6)]

    def plate(self):
        bg = vgrad(PW, PH, [(0, '#C3BCEB'), (0.45, '#A6C6EE'), (1, '#7EA3D6')])
        bg = bg * (0.95 + 0.07 * smooth_noise(PH, PW, 80, 4, 3))[..., None]
        bg[820:] = bg[820:] * 0.94 + 0.05
        img = plate_img(vignette(bg, 0.35))
        self.r = 58
        pts = hex_positions(-30, 860, PW + 40, PH + 40, 136)
        row_y = min(set(p[1] for p in pts), key=lambda yv: abs(yv - 1080))
        row = sorted([p for p in pts if p[1] == row_y and 180 < p[0] < 1120], key=lambda p: p[0])[:5]
        self.pop_list = row
        paste_bubbles(img, [p for p in pts if p not in row], self.r)
        card, off = gauge_card()
        self.gc = (CX, 580)
        paste_center(img, card, self.gc[0] - off[0], self.gc[1] - off[1])
        self.hand = get_hand(560, -2.2)
        return img

    def dyn(self, img, t):
        times = self.pop_times()
        for k, (x, y) in enumerate(self.pop_list):
            draw_press_bubble(img, x, y, self.r, t, times[k] - 0.09, times[k], seed=k + 10)
        p = self.pop_list
        kf = [(0.0, (p[0][0] + 420, p[0][1] + 520, 1.0)), (max(0.05, times[0] - 0.35), (p[0][0] + 160, p[0][1] + 200, 0.8))]
        for k in range(5):
            kf.append((times[k] - 0.09, (p[k][0], p[k][1], 0.0)))
            kf.append((times[k] + 0.02, (p[k][0], p[k][1], 0.0)))
            if k < 4:
                kf.append(((times[k] + times[k + 1]) / 2 - 0.03, ((p[k][0] + p[k + 1][0]) / 2, p[k][1] - 10, 0.45)))
        kf.append((times[-1] + 0.5, (p[-1][0] + 480, p[-1][1] + 560, 1.0)))
        hx, hy, lift = keyframes(t, kf)
        if t < times[-1] + 0.55:
            draw_hand(img, self.hand, (hx, hy), lift)
        done = sum(clamp01((t - tt) / 0.18) for tt in times) / 5
        jitter = 3 * math.sin(t * 40) * (1 - done)
        ang = math.radians(162 - 144 * ease_in_out(done) + jitter)
        gx, gy = self.gc
        L = 225
        tip = (gx + math.cos(ang) * L, gy - math.sin(ang) * L)
        base_l = (gx + math.cos(ang + math.pi / 2) * 16, gy - math.sin(ang + math.pi / 2) * 16)
        base_r = (gx + math.cos(ang - math.pi / 2) * 16, gy - math.sin(ang - math.pi / 2) * 16)
        ov = OV(img, gx - 260, gy - 260, gx + 260, gy + 60)
        ov.d.polygon(ov.pts([(base_l[0] + 4, base_l[1] + 6), (tip[0] + 4, tip[1] + 6), (base_r[0] + 4, base_r[1] + 6)]), fill=(0, 0, 0, 70))
        ov.d.polygon(ov.pts([base_l, tip, base_r]), fill=(40, 44, 52, 255))
        ov.d.ellipse(ov.box(gx - 30, gy - 30, gx + 30, gy + 30), fill=(40, 44, 52, 255))
        ov.d.ellipse(ov.box(gx - 12, gy - 12, gx + 12, gy + 12), fill=(200, 205, 212, 255))
        ov.commit()
        pop(img, C('1992 STUDY', 50, dot=(120, 90, 220)), CX, 210, t, self.we('study') - 0.05)
        pop(img, C('CALMER', 54, bg=(70, 185, 90), fg=(255, 255, 255)), CX, 760, t, self.we('CALMER'))

# ====================================================================== 9 the bubble wrap that doesn't pop
def tube_row(w, H, cell, phase, deform=None):
    pad = 26
    hh = int(2 * H * 1.25 + 2 * pad)
    xs = np.arange(w, dtype=np.float32)
    frac = ((xs - phase) % cell) / cell
    prof = H * (0.56 + 0.44 * np.sin(np.pi * frac) ** 0.7)
    if deform is not None:
        prof = prof * deform(xs)
    dprof = np.gradient(prof)
    yy = np.arange(hh, dtype=np.float32)[:, None] - hh / 2
    v = yy / np.maximum(prof[None, :], 1)
    inside = np.clip(prof[None, :] - np.abs(yy) + 0.5, 0, 1)
    vz = np.sqrt(np.clip(1 - v ** 2, 0, 1))
    nx = np.broadcast_to(-dprof[None, :] * 1.6, v.shape)
    nn = np.sqrt(nx ** 2 + v ** 2 + vz ** 2) + 1e-6
    nx, ny, nz = nx / nn, v / nn, vz / nn
    ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
    fres = (1 - nz) ** 2
    body_a = (0.08 + 0.5 * fres) * inside
    body_c = np.stack([0.9 + 0.1 * ndl, 0.95 + 0.05 * ndl, np.ones_like(ndl)], -1)
    neck = np.exp(-(np.minimum(frac, 1 - frac) / 0.035) ** 2)[None, :] * inside * 0.35
    spec = np.clip(ndh ** 45 * 1.5, 0, 1) * inside
    sh = np.clip(prof[None, :] - np.abs(yy - H * 0.3) + 0.5, 0, 1)
    sh = gaussian_filter(np.roll(sh, 12, axis=1), 7) * 0.28
    P = np.zeros(v.shape + (3,), np.float32)
    A = np.zeros(v.shape, np.float32)
    for col, al in ((np.zeros(3, np.float32), sh * (1 - 0.7 * inside)), (body_c, body_a),
                    (np.array([0.22, 0.27, 0.33], np.float32), neck), (np.ones(3, np.float32), spec)):
        P = col * al[..., None] + P * (1 - al[..., None])
        A = al + A * (1 - al)
    out = np.where(A[..., None] > 1e-4, P / np.maximum(A[..., None], 1e-4), 0)
    arr = np.concatenate([np.clip(out, 0, 1), np.clip(A, 0, 1)[..., None]], -1)
    return Image.fromarray((arr * 255 + 0.5).astype(np.uint8), 'RGBA')

class NoPop(S):
    ROWS = (620, 810, 1000, 1190)
    PRESS_ROW = 1000
    CELL, H = 170, 66

    def press_windows(self):
        a = (self.we('One') - 0.18, self.we('DOESNT') - 0.1)
        b = (self.we('POP') - 0.08, self.we('POP', 't1') + 0.45)
        return a, b

    def events(self):
        a, b = self.press_windows()
        return [(a[0] + 0.05, 'squeak', 0.55), (b[0] + 0.05, 'squeak', 0.65),
                (self.we('POP', 't1') + 0.1, 'trombone', 0.8)]

    def plate(self):
        bg = vgrad(PW, PH, [(0, '#E3EAF0'), (1, '#AFC0CF')])
        bg = bg * (0.96 + 0.06 * smooth_noise(PH, PW, 80, 9, 3))[..., None]
        img = plate_img(vignette(bg, 0.35))
        self.w = PW + 40
        self.phase_main = (CX + 20 - self.CELL / 2) % self.CELL
        for k, y in enumerate(self.ROWS):
            if y == self.PRESS_ROW:
                continue
            ph = self.phase_main + (self.CELL / 2 if k % 2 else 0)
            row = tube_row(self.w, self.H, self.CELL, ph)
            paste_at(img, row, -20, int(y - row.height / 2))
        self.base_row = tube_row(self.w, self.H, self.CELL, self.phase_main)
        self.xp = CX
        self.hand = get_hand(560, -2.2)
        self.stamp = stamp_sprite('NO POP?!', 150)
        return img

    def press_amount(self, t):
        a, b = self.press_windows()
        amt = 0.0
        for (t0, t1) in (a, b):
            if t0 <= t <= t1 + 0.15:
                up = ease_out((t - t0) / 0.15)
                down = 1 - ease_in_out((t - t1) / 0.15) if t > t1 else 1.0
                amt = max(amt, up * down)
        return amt

    def dyn(self, img, t):
        amt = self.press_amount(t)
        y = self.PRESS_ROW
        if amt > 0.01:
            xr = self.xp + 20
            C_ = self.CELL

            def deform(xs, a=amt):
                return (1 - 0.45 * a * np.exp(-((xs - xr) / 62) ** 2)
                        + 0.2 * a * (np.exp(-((xs - xr - C_) / 75) ** 2) + np.exp(-((xs - xr + C_) / 75) ** 2)))
            row = tube_row(self.w, self.H, self.CELL, self.phase_main, deform)
        else:
            row = self.base_row
        paste_at(img, row, -20, int(y - row.height / 2))
        a, b = self.press_windows()
        x = self.xp
        yt = y - self.H * 0.15
        kf = [(0.0, (x + 520, yt + 640, 1.0)), (a[0] - 0.4, (x + 200, yt + 260, 0.8)), (a[0], (x, yt + 18, 0.0)),
              (a[1], (x, yt + 18, 0.0)), (a[1] + 0.12, (x + 40, yt + 60, 0.4)), (b[0], (x, yt + 22, 0.0)),
              (b[1], (x, yt + 22, 0.0)), (b[1] + 0.5, (x + 520, yt + 640, 1.0))]
        hx, hy, lift = keyframes(t, kf)
        draw_hand(img, self.hand, (hx, hy), lift)
        tE = self.we('POP', 't1')
        pop(img, C('2015  ·  iBUBBLE WRAP', 48, dot=(90, 170, 255)), CX, 250, t, self.we('2015') - 0.05, out_t=tE + 0.45)
        stamp_in(img, self.stamp, CX, 470 + 40, t, self.we('POP') + 0.02)
        pop(img, C('THE POPPABLE KIND IS STILL SOLD', 40), CX, 250, t, tE + 0.55)

SCENES = [Hook, Curtains, WallpaperFlop, Greenhouse, IBMRoom, WrapComputer, Billions, Calendar, Calm, NoPop]
