"""Velcro was invented because of a dog (2026-11-16)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish
from mw_scenes import glow, stamp_sprite, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import ground_shadow, figure, red_x

RED = (214, 50, 44)
YEL = (255, 210, 60)
BLUE = (40, 120, 200)
GREEN = (60, 170, 90)
WHITE = (255, 255, 255)
STRAP = (38, 44, 66)
DOGC = '#C98A4E'

class Base(S):
    focus = (CX, 1100)
    z0, z1 = 1.16, 1.24

# ====================================================================== plates
_PL = {}
def wall_plate(c0='#F2B266', c1='#B5562C', seed=3, spot=(CX, 900, 1300)):
    key = (c0, c1, seed, spot)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.9 + 0.1 * smooth_noise(PH, PW, 110, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, spot[0], spot[1], spot[2], 1.3))[..., None]
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    _PL[key] = img
    return img.copy()

def alps_plate():
    if 'alps' in _PL:
        return _PL['alps'].copy()
    arr = vgrad(PW, PH, [(0, '#7EC4F0'), (0.5, '#CFEAF8'), (1, '#CFEAF8')])
    img = to_img(arr).convert('RGBA')
    ov = OV(img, 0, 0, PW, PH)
    d = ov.d
    back = [(0, 1150), (160, 820), (330, 990), (560, 560), (760, 900), (930, 700), (1120, 940), (1296, 760), (1296, 1500), (0, 1500)]
    d.polygon(back, fill=(150, 170, 200, 255))
    for (px, py, w) in ((560, 560, 120), (930, 700, 90), (160, 820, 80), (1296, 760, 80)):
        d.polygon([(px, py), (px - w, py + w * 1.1), (px - w * 0.4, py + w * 0.9), (px, py + w * 1.2), (px + w * 0.5, py + w * 0.85), (px + w, py + w * 1.1)], fill=(250, 252, 255, 255))
    front = [(0, 1350), (260, 1020), (470, 1260), (700, 1000), (980, 1290), (1296, 1080), (1296, 1700), (0, 1700)]
    d.polygon(front, fill=(96, 120, 150, 255))
    for (px, py, w) in ((260, 1020, 90), (700, 1000, 100), (1296, 1080, 70)):
        d.polygon([(px, py), (px - w, py + w), (px - w * 0.3, py + w * 0.8), (px + w * 0.4, py + w * 0.95), (px + w, py + w)], fill=(245, 248, 252, 255))
    d.rectangle((0, 1560, PW, PH), fill=(98, 170, 78, 255))
    d.polygon([(0, 1560), (400, 1500), (900, 1540), (1296, 1490), (1296, 1600), (0, 1600)], fill=(98, 170, 78, 255))
    rng = np.random.default_rng(3)
    for (tx, ty, h) in ((70, 1600, 300), (1230, 1590, 340), (180, 1560, 220), (1120, 1550, 230)):
        d.rectangle((tx - 14, ty - 20, tx + 14, ty + 30), fill=(90, 60, 40, 255))
        for k in range(3):
            yy = ty - h * (0.3 + 0.3 * k)
            ww = h * (0.42 - 0.1 * k)
            d.polygon([(tx, yy - h * 0.38), (tx - ww, yy + h * 0.12), (tx + ww, yy + h * 0.12)], fill=(40, 100, 60, 255))
    for _ in range(140):
        x = float(rng.uniform(0, PW)); y = float(rng.uniform(1620, PH))
        d.line([(x, y), (x + rng.uniform(-10, 10), y - rng.uniform(20, 46))], fill=(60, 130, 55, 255), width=6)
    ov.commit()
    arr = vignette(to_arr(img), 0.35)
    img = plate_img(arr)
    _PL['alps'] = img
    return img.copy()

def space_wall_plate():
    if 'space' in _PL:
        return _PL['space'].copy()
    arr = vgrad(PW, PH, [(0, '#C9CFD8'), (1, '#7E8794')])
    arr = arr * (0.94 + 0.06 * smooth_noise(PH, PW, 120, 5, 3))[..., None]
    img = to_img(arr).convert('RGBA')
    ov = OV(img, 0, 0, PW, PH)
    d = ov.d
    for y in (260, 760, 1660, 2160):
        d.line([(0, y), (PW, y)], fill=(90, 98, 110, 255), width=8)
        for x in range(40, PW, 120):
            d.ellipse((x - 9, y + 22, x + 9, y + 40), fill=(150, 158, 170, 255))
    for x in (300, 1000):
        d.line([(x, 0), (x, 260)], fill=(90, 98, 110, 255), width=8)
    # porthole with Earth
    cx, cy, r = 1010, 520, 170
    d.ellipse((cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30), fill=(70, 76, 88, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(10, 14, 36, 255))
    rng = np.random.default_rng(9)
    for _ in range(30):
        a = rng.uniform(0, 6.28); q = rng.uniform(0, 0.9) * r
        x, y = cx + math.cos(a) * q, cy + math.sin(a) * q
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255, 255))
    d.chord((cx - r, cy + 20, cx + r, cy + r + 240), 180, 360, fill=(60, 140, 220, 255))
    d.chord((cx - r * 0.6, cy + 60, cx + r * 0.3, cy + 200), 180, 360, fill=(80, 170, 90, 255))
    ov.commit()
    img = plate_img(vignette(to_arr(img), 0.35))
    _PL['space'] = img
    return img.copy()

# ====================================================================== props
_SP = {}
def strap_tex(w, h, kind='loop', col=STRAP, seed=1):
    """Hook-and-loop strip. kind 'loop' = fuzzy, 'hook' = rows of tiny hooks."""
    key = ('strap', w, h, kind, col, seed)
    if key in _SP:
        return _SP[key]
    arr = np.ones((h, w, 3), np.float32) * (np.array(col, np.float32) / 255)
    if kind == 'loop':
        n = smooth_noise(h, w, 4, seed, 2)
        arr = arr * (0.75 + 0.6 * n[..., None])
    else:
        n = smooth_noise(h, w, 10, seed, 2)
        arr = arr * (0.85 + 0.3 * n[..., None])
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    if kind == 'hook':
        lc = tuple(min(255, int(c * 2.2 + 40)) for c in col) + (255,)
        for y in range(22, h - 16, 26):
            off = 13 if (y // 26) % 2 else 0
            for x in range(14 + off, w - 10, 26):
                d.arc((x - 7, y - 9, x + 7, y + 5), 180, 360, fill=lc, width=3)
                d.line([(x - 7, y - 2), (x - 7, y + 8)], fill=lc, width=3)
    else:
        rng = np.random.default_rng(seed)
        lc = tuple(min(255, int(c * 2.0 + 50)) for c in col) + (200,)
        for _ in range(int(w * h / 600)):
            x, y = rng.uniform(4, w - 4), rng.uniform(4, h - 4)
            r = rng.uniform(4, 8)
            a0 = rng.uniform(0, 360)
            d.arc((x - r, y - r, x + r, y + r), a0, a0 + 230, fill=lc, width=2)
    # stitched edges
    ec = tuple(min(255, int(c * 1.6 + 30)) for c in col) + (255,)
    for yy in (10, h - 12):
        for x in range(10, w - 10, 30):
            d.line([(x, yy), (x + 16, yy)], fill=ec, width=4)
    d.rectangle((0, 0, w - 1, h - 1), outline=tuple(int(c * 0.6) for c in col) + (255,), width=4)
    _SP[key] = im
    return im

def burr_sprite(r, seed=0):
    key = ('burr', r, seed)
    if key in _SP:
        return _SP[key]
    ss = 2
    R = int(r * 1.6)
    im = Image.new('RGBA', (2 * R * ss, 2 * R * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = R * ss
    rng = np.random.default_rng(seed)
    n = 46
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.05, 0.05)
        r0, r1 = r * 0.6 * ss, r * (1.3 + rng.uniform(-0.08, 0.08)) * ss
        x0, y0 = c + math.cos(a) * r0, c + math.sin(a) * r0
        x1, y1 = c + math.cos(a) * r1, c + math.sin(a) * r1
        d.line([(x0, y0), (x1, y1)], fill=(150, 112, 60, 255), width=max(2, int(r * 0.06 * ss)))
        hx, hy = x1 + math.cos(a + 2.2) * r * 0.14 * ss, y1 + math.sin(a + 2.2) * r * 0.14 * ss
        d.line([(x1, y1), (hx, hy)], fill=(150, 112, 60, 255), width=max(2, int(r * 0.05 * ss)))
    im = im.resize((2 * R, 2 * R), Image.LANCZOS)
    lay = Layer(2 * R, 2 * R)
    sphere(lay, (R, R), r * 0.78, '#7A5326', spec=0.15, shin=12)
    sp, x0, y0 = layer_sprite(lay, 0)
    im.alpha_composite(sp, (x0, y0))
    d = ImageDraw.Draw(im)
    for k in range(18):
        a = rng.uniform(0, 6.28); q = rng.uniform(0.1, 0.7) * r
        x, y = R + math.cos(a) * q, R + math.sin(a) * q
        d.line([(x, y), (x + math.cos(a) * r * 0.2, y + math.sin(a) * r * 0.2)], fill=(185, 145, 80, 255), width=max(2, int(r * 0.05)))
    _SP[key] = im
    return im

def dog_sprite(L, step=0.0, wag=0.0, burrs=0):
    """Wooden toy dog in side view facing right. L = body length scale."""
    step = round((step % 1) * 12) / 12
    wag = round(wag * 6) / 6
    key = ('dog', L, step, wag, burrs)
    if key in _SP:
        return _SP[key]
    lay = Layer(int(L * 1.5), int(L * 1.15))
    col = hexc(DOGC); j = col * 0.82; dark = hexc('#5A3418')
    kw = dict(grain=grain_map()[:lay.h, :lay.w], spec=0.28, shin=22)
    ox, oy = L * 0.62, L * 0.5
    P = lambda u, v: (ox + u * L, oy + v * L)
    sw = math.sin(step * 2 * math.pi) * 0.07
    # far legs
    for (x, s) in ((0.2, 1), (-0.24, -1)):
        capsule(lay, P(x, 0.05), P(x - s * sw, 0.42), 0.055 * L, 0.045 * L, j * 0.9, **kw)
        ellipsoid(lay, P(x - s * sw + 0.03, 0.44), 0.06 * L, 0.03 * L, 0, j * 0.85, **kw)
    # tail
    tx, ty = -0.36, -0.06
    capsule(lay, P(tx, ty), P(tx - 0.14, ty - 0.2 + 0.06 * wag), 0.03 * L, 0.02 * L, col, **kw)
    ellipsoid(lay, P(0, 0), 0.33 * L, 0.15 * L, 0, col, **kw)
    ellipsoid(lay, P(0.2, -0.02), 0.15 * L, 0.16 * L, 0, col, **kw)
    capsule(lay, P(0.25, -0.06), P(0.36, -0.26), 0.08 * L, 0.07 * L, col, **kw)
    ellipsoid(lay, P(0.41, -0.33), 0.13 * L, 0.11 * L, 0, col, **kw)
    capsule(lay, P(0.47, -0.29), P(0.6, -0.27), 0.065 * L, 0.055 * L, col, **kw)
    sphere(lay, P(0.62, -0.285), 0.035 * L, hexc('#2A1A10'), spec=0.5, shin=40)
    sphere(lay, P(0.46, -0.37), 0.022 * L, hexc('#1A1010'), spec=0.6, shin=40)
    ellipsoid(lay, P(0.35, -0.33), 0.05 * L, 0.11 * L, 0.35, dark, **kw)
    # near legs
    for (x, s) in ((0.24, -1), (-0.2, 1)):
        capsule(lay, P(x, 0.05), P(x + s * sw, 0.42), 0.058 * L, 0.048 * L, col, **kw)
        ellipsoid(lay, P(x + s * sw + 0.03, 0.44), 0.065 * L, 0.032 * L, 0, j, **kw)
    sp, x0, y0 = layer_sprite(lay, 2)
    if burrs:
        rng = np.random.default_rng(5)
        spots = [(-0.2, -0.05), (0.05, -0.1), (0.2, 0.05), (-0.05, 0.08), (0.38, -0.38), (-0.3, 0.02), (0.12, -0.12),
                 (-0.14, 0.1), (0.3, -0.18), (0.24, 0.28), (-0.22, 0.3), (0.0, -0.02)]
        for k, (u, v) in enumerate(spots[:burrs]):
            b = burr_sprite(int(L * 0.05), k)
            x, y = P(u, v)
            paste_at(sp, b, x - x0 - b.width / 2, y - y0 - b.height / 2)
    info = {'foot': (P(0, 0.465)[0] - x0, P(0, 0.465)[1] - y0)}
    _SP[key] = (sp, info)
    return _SP[key]

def draw_dog(img, L, cx, ground, step=0.0, wag=0.0, burrs=0, shadow=True):
    sp, info = dog_sprite(L, step, wag, burrs)
    if shadow:
        ground_shadow(img, cx, ground + 4, L * 1.3, 0.4)
    paste_at(img, sp, cx - info['foot'][0], ground - info['foot'][1])

def draw_man(img, Hh, cx, ground, step=0.0, walk=True):
    sp, info = figure(Hh, 'man', False, round((step % 1) * 12) / 12 if walk else 0.0)
    ground_shadow(img, cx, ground + 6, Hh * 0.38, 0.4)
    paste_at(img, sp, int(cx - info['foot'][0]), int(ground - info['foot'][1]))

def microscope_sprite(h=900):
    key = ('micro', h)
    if key in _SP:
        return _SP[key]
    w = int(h * 0.75)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = h / 900
    body = (236, 238, 242, 255); dark = (60, 66, 80, 255); mid = (150, 156, 170, 255)
    d.rounded_rectangle((60 * k, 780 * k, 560 * k, 880 * k), 30 * k, fill=dark)
    d.rounded_rectangle((330 * k, 220 * k, 460 * k, 800 * k), 50 * k, fill=body, outline=mid, width=int(6 * k))
    d.rectangle((120 * k, 560 * k, 470 * k, 610 * k), fill=dark)
    d.ellipse((400 * k, 440 * k, 470 * k, 510 * k), fill=mid)
    tube = [(150 * k, 120 * k), (260 * k, 70 * k), (420 * k, 430 * k), (310 * k, 480 * k)]
    d.polygon(tube, fill=body, outline=mid)
    d.polygon([(130 * k, 40 * k), (230 * k, 0), (270 * k, 90 * k), (170 * k, 135 * k)], fill=dark)
    d.polygon([(300 * k, 470 * k), (380 * k, 440 * k), (360 * k, 530 * k), (320 * k, 545 * k)], fill=dark)
    d.ellipse((290 * k, 520 * k, 350 * k, 560 * k), fill=(120, 200, 255, 255))
    _SP[key] = im
    return im

def arrow_sprite(w=260, h=120, col=WHITE):
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(10, 10 + h * 0.32), (10 + w * 0.62, 10 + h * 0.32), (10 + w * 0.62, 10), (10 + w, 10 + h / 2),
           (10 + w * 0.62, 10 + h), (10 + w * 0.62, 10 + h * 0.68), (10, 10 + h * 0.68)]
    d.polygon(pts, fill=col + (255,), outline=(20, 20, 30, 255), width=6)
    return im

def check_sprite(R=70, col=GREEN):
    im = Image.new('RGBA', (2 * R + 8, 2 * R + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 2 * R + 4, 2 * R + 4), fill=col + (255,), outline=(255, 255, 255, 255), width=8)
    d.line([(R * 0.55 + 4, R + 4), (R * 0.9 + 4, R * 1.35 + 4), (R * 1.5 + 4, R * 0.65 + 4)], fill=(255, 255, 255, 255), width=int(R * 0.22), joint='curve')
    return im

def qmark(size=150, col=(255, 255, 255)):
    return text_img('?', size, fill=col, stroke=10, stroke_fill=(20, 20, 30), shadow_px=4)

def shoe_sprite(w=420, col=(220, 70, 60)):
    key = ('shoe', w, col)
    if key in _SP:
        return _SP[key]
    h = int(w * 0.55)
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = w / 420
    d.polygon([(20 * k, 90 * k), (150 * k, 60 * k), (230 * k, 120 * k), (400 * k, 160 * k), (410 * k, 200 * k), (20 * k, 200 * k)], fill=col + (255,))
    d.rounded_rectangle((10 * k, 190 * k, 420 * k, 235 * k), 18 * k, fill=(250, 250, 250, 255), outline=(180, 180, 180, 255), width=3)
    for x in (95, 165):
        d.polygon([(x * k, 70 * k), ((x + 50) * k, 85 * k), ((x + 80) * k, 175 * k), ((x + 30) * k, 175 * k)], fill=STRAP + (255,))
    _SP[key] = im
    return im

def rocket_sprite(h=980):
    key = ('rocket', h)
    if key in _SP:
        return _SP[key]
    w = int(h * 0.55)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = w / 2
    bw = w * 0.36
    d.polygon([(cx - bw, h * 0.72), (cx - w * 0.48, h * 0.9), (cx - bw, h * 0.86)], fill=(214, 50, 44, 255))
    d.polygon([(cx + bw, h * 0.72), (cx + w * 0.48, h * 0.9), (cx + bw, h * 0.86)], fill=(214, 50, 44, 255))
    d.rounded_rectangle((cx - bw, h * 0.25, cx + bw, h * 0.88), int(bw * 0.4), fill=(245, 246, 250, 255), outline=(150, 156, 170, 255), width=6)
    d.pieslice((cx - bw, h * 0.02, cx + bw, h * 0.5), 180, 360, fill=(214, 50, 44, 255))
    d.ellipse((cx - bw * 0.45, h * 0.36, cx + bw * 0.45, h * 0.36 + bw * 0.9), fill=(90, 170, 230, 255), outline=(150, 156, 170, 255), width=10)
    d.rectangle((cx - bw * 0.5, h * 0.88, cx + bw * 0.5, h * 0.93), fill=(80, 86, 100, 255))
    _SP[key] = im
    return im

def pen_sprite():
    im = Image.new('RGBA', (60, 340), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 50, 300), 14, fill=(40, 110, 220, 255))
    d.polygon([(10, 300), (50, 300), (30, 335)], fill=(230, 230, 230, 255))
    d.rectangle((44, 30, 54, 130), fill=(200, 200, 210, 255))
    return im

def spoon_sprite():
    im = Image.new('RGBA', (120, 380), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 110, 150), fill=(215, 220, 228, 255), outline=(150, 156, 170, 255), width=5)
    d.rounded_rectangle((48, 140, 72, 370), 12, fill=(215, 220, 228, 255), outline=(150, 156, 170, 255), width=4)
    return im

def pouch_sprite(label='SNACK'):
    im = Image.new('RGBA', (260, 320), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 250, 310), 30, fill=(245, 236, 200, 255), outline=(170, 150, 100, 255), width=6)
    d.rectangle((60, 250, 200, 300), fill=STRAP + (255,))
    f = font(54)
    bb = f.getbbox(label)
    d.text((130 - (bb[2] + bb[0]) / 2, 120 - (bb[3] + bb[1]) / 2), label, font=f, fill=(150, 90, 40, 255))
    return im

def calendar_page(n, w=300):
    im = Image.new('RGBA', (w, int(w * 1.1)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, int(w * 1.1) - 1), 24, fill=(255, 255, 255, 255), outline=(40, 40, 50, 255), width=6)
    d.rounded_rectangle((0, 0, w - 1, int(w * 0.3)), 24, fill=RED + (255,))
    d.rectangle((0, int(w * 0.18), w - 1, int(w * 0.3)), fill=RED + (255,))
    f = font(int(w * 0.18))
    bb = f.getbbox('YEAR')
    d.text((w / 2 - (bb[2] + bb[0]) / 2, w * 0.15 - (bb[3] + bb[1]) / 2), 'YEAR', font=f, fill=(255, 255, 255, 255))
    f = font(int(w * 0.5))
    s = str(n)
    bb = f.getbbox(s)
    d.text((w / 2 - (bb[2] + bb[0]) / 2, w * 0.7 - (bb[3] + bb[1]) / 2), s, font=f, fill=(30, 30, 36, 255))
    return im

def word_sprite(parts, size):
    """parts: list of (text, color). Big outlined word."""
    f = font(size)
    widths = [f.getlength(t) for t, _ in parts]
    stroke = max(8, size // 12)
    asc, desc = f.getmetrics()
    w = int(sum(widths) + stroke * 2 + 40)
    h = asc + desc + stroke * 2 + 30
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(im)
    x = 20 + stroke
    for (t, c), ww in zip(parts, widths):
        ds.text((x, 15 + stroke + 8), t, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        x += ww
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    x = 20 + stroke
    for (t, c), ww in zip(parts, widths):
        d.text((x, 15 + stroke), t, font=f, fill=c, stroke_width=stroke, stroke_fill=(20, 20, 30))
        x += ww
    return im

# ====================================================================== the hero strap rip
class Hook(Base):
    """Frame 0: a giant hook-and-loop strap being ripped open mid-action, fibers flying."""
    z0, z1 = 1.12, 1.17
    LY = 1290      # top of the lower (loop) strip = contact line
    TH = 300       # strip thickness
    X0, X1 = -40, 1336
    HX = 520       # where the top strip leaves the bottom one
    def make_shakes(self):
        return [(0.0, 14, 0.35), (self.we('dog.') - 0.02, 14, 0.3)]
    def events(self):
        return [(0.0, 'tape', 0.9), (0.75, 'tape', 0.6), (self.we('because') - 0.03, 'pop', 0.5)]
    def plate(self):
        img = wall_plate('#FFB65C', '#C24A2A', 7, (CX, 1100, 1300))
        self.lower = strap_tex(self.X1 - self.X0, self.TH, 'loop', STRAP, 3)
        self.upper = strap_tex(self.X1 - self.X0, self.TH, 'hook', (56, 64, 92), 4)
        self.hand = get_hand(640, -2.0)
        self.burr = burr_sprite(70, 2)
        return img
    def hero(self, img, t):
        ly, th = self.LY, self.TH
        sh, pad = shadow_of(self.lower, 14, 0.45)
        paste_at(img, sh, self.X0 - pad + 12, ly - pad + 22)
        paste_at(img, self.lower, self.X0, ly)
        ang = math.radians(17 + 4 * math.sin(2 * math.pi * t / 1.5) + 1.5 * math.sin(7.3 * t))
        hx = self.HX
        # attached part (left) lies on top of the lower strip
        flat = self.upper.crop((0, 0, hx - self.X0, th))
        paste_at(img, flat, self.X0, ly - th)
        # peeled part: hinged at (hx, ly), rotated up by ang
        L = 600
        ca, sa = math.cos(ang), math.sin(ang)
        bl = (hx, ly); br = (hx + L * ca, ly - L * sa)
        tl = (hx - th * sa, ly - th * ca); tr = (br[0] - th * sa, br[1] - th * ca)
        peel = self.upper.crop((hx - self.X0 - 4, 0, min(self.upper.width, hx - self.X0 + int(L)), th))
        _quad_img(img, peel, [tl, tr, br, bl])
        # the hook side underneath (gap) highlight + fibers flying from the seam
        ov = OV(img, hx - 80, ly - 480, PW, ly + 40)
        rng = np.random.default_rng(int(t * 30) % 7)
        for k in range(16):
            u = ((t * 1.7 + k * 0.137) % 1.0)
            r = 40 + 420 * u
            a = math.radians(-8 - 26 * ((k * 0.61) % 1.0))
            x = hx + 40 + math.cos(a) * r
            y = ly - 10 + math.sin(a) * r
            al = int(255 * (1 - u))
            ov.d.arc(ov.box(x - 10, y - 10, x + 10, y + 10), 30 * k, 30 * k + 220, fill=(235, 235, 245, al), width=5)
        ov.commit()
        tip = ((tr[0] + br[0]) / 2 - 60 * ca, (tr[1] + br[1]) / 2 + 60 * sa)
        draw_hand(img, self.hand, (tip[0] + 20, tip[1] + 30), 0.35)
        b = 0.0
        if type(self) is Hook:
            u = (t - self.we('dog.') + 0.03) / 0.35
            if 0 < u < 1:
                b = math.sin(math.pi * u)
        self.draw_hdog(img, t, b)
    def draw_hdog(self, img, t, bounce=0.0):
        draw_dog(img, 560, CX - 60, 2150 - 60 * bounce, step=0.0, wag=math.sin(t * 14), burrs=6)
    def dyn(self, img, t):
        self.hero(img, t)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, 1180 + dy, dr

def _quad_img(img, tex, corners):
    lay_w = img.width
    xs = [c[0] for c in corners]; ys = [c[1] for c in corners]
    x0, y0 = int(min(xs)) - 4, int(min(ys)) - 4
    x1, y1 = int(max(xs)) + 4, int(max(ys)) + 4
    tmp = Layer(x1 - x0, y1 - y0)
    quad(tmp, tex, [(x - x0, y - y0) for x, y in corners], ss=1)
    sp, sx, sy = layer_sprite(tmp, 0)
    sh, pad = shadow_of(sp, 16, 0.5)
    paste_at(img, sh, x0 + sx - pad + 26, y0 + sy - pad + 34)
    paste_at(img, sp, x0 + sx, y0 + sy)

# ====================================================================== 1: 1941, Swiss engineer, dog, Alps
class Alps(Base):
    z0, z1 = 1.12, 1.22
    focus = (CX, 1250)
    def make_shakes(self):
        return [(self.we('1941,'), 12, 0.28), (self.we('Alps.'), 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1941,'), 'thud', 0.7), (self.we('Swiss') - 0.03, 'pop', 0.5),
                (self.we('George') - 0.03, 'pop', 0.5), (self.we('dog') - 0.02, 'bloop', 0.5), (self.we('trip') - 0.03, 'chime', 0.5)]
    def plate(self):
        self.st = stamp_sprite('1941', 150, color=BLUE, angle=-7)
        return alps_plate()
    def dyn(self, img, t):
        tD = self.we('dog')
        walk = t * 1.4
        drift = 20 * t
        draw_man(img, 1120, CX - 300 + drift, 2060, step=walk)
        if t > tD - 0.1:
            k = ease_back((t - tD + 0.1) / 0.35, 1.8)
            draw_dog(img, int(480 * max(0.05, k)), CX + 170 + drift, 2060, step=walk * 1.3, wag=math.sin(t * 12))
        stamp_in(img, self.st, CX + 270, 1000, t, self.we('1941,'))
        pop(img, C('SWISS ENGINEER', 72, bg=YEL), CX, 520, t, self.we('Swiss') - 0.05, out_t=self.we('George') - 0.3)
        pop(img, C('GEORGE DE MESTRAL', 70, bg=WHITE), CX, 520, t, self.we('George') - 0.05, out_t=self.we('Alps.') - 0.3)
        pop(img, C('THE ALPS', 80, bg=(120, 200, 255)), CX, 520, t, self.we('Alps.') - 0.05)

# ====================================================================== 2: covered in burrs
class Burrs(Base):
    z0, z1 = 1.14, 1.24
    focus = (CX, 1180)
    def make_shakes(self):
        return [(self.we('covered'), 12, 0.3), (self.we('burrs.'), 16, 0.32)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('home,'), 'pop', 0.5)]
        t0 = self.we('covered')
        for k in range(6):
            ev.append((t0 + k * 0.13, 'pop', 0.45))
        ev.append((self.we('sticky') - 0.03, 'thud', 0.7))
        return ev
    def plate(self):
        img = wall_plate('#B9E3A6', '#3E7A3A', 11, (CX, 1000, 1300))
        ov = OV(img, 0, 1500, PW, PH)
        ov.d.rectangle((0, 0, PW, PH - 1500), fill=(130, 92, 58, 255))
        for y in range(40, PH - 1500, 110):
            ov.d.line([(0, y), (PW, y + 8)], fill=(105, 72, 44, 255), width=5)
        ov.commit()
        self.st = stamp_sprite('STICKY BURRS!', 120, color=RED, angle=-6)
        self.pants = Image.new('RGBA', (240, 1000), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.pants)
        d.polygon([(10, 0), (230, 0), (220, 940), (20, 940)], fill=(70, 96, 150, 255))
        d.line([(120, 30), (120, 930)], fill=(50, 70, 120, 255), width=6)
        d.ellipse((0, 900, 240, 1000), fill=(60, 40, 30, 255))
        return img
    def dyn(self, img, t):
        tC = self.we('covered')
        n = 0 if t < tC else min(12, 1 + int((t - tC) / 0.1))
        paste_at(img, self.pants, 150, 560)
        paste_at(img, self.pants, 400, 560)
        ov = OV(img, 120, 520, 740, 640)
        ov.d.rounded_rectangle(ov.box(140, 530, 720, 620), 20, fill=(60, 50, 40, 255))
        ov.commit()
        draw_dog(img, 640, CX + 120, 1560, step=0.0, wag=math.sin(t * 10), burrs=n)
        rng = np.random.default_rng(8)
        for k in range(min(8, n)):
            b = burr_sprite(46, k + 10)
            x = 170 + (k % 2) * 250 + float(rng.uniform(20, 180))
            y = 700 + (k // 2) * 200 + float(rng.uniform(-30, 30))
            paste_center(img, b, x, y)
        pop(img, C('BACK HOME...', 76, bg=WHITE), CX, 520, t, self.we('home,') - 0.05, out_t=tC - 0.3)
        pop(img, C("HIS PANTS + DOG'S FUR", 64, bg=YEL), CX, 520, t, tC - 0.05)
        stamp_in(img, self.st, CX, 1800, t, self.we('burrs.') - 0.05)

# ====================================================================== 3: pull off vs microscope
class Microscope(Base):
    z0, z1 = 1.14, 1.24
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('microscope.') - 0.05, 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('pull'), 'tape', 0.6), (self.we('but'), 'swipe', 0.6),
                (self.we('under') - 0.03, 'ding', 0.7)]
    def plate(self):
        img = wall_plate('#2E4A5A', '#0E1A22', 5, (CX, 1000, 1200))
        ov = OV(img, 0, 1600, PW, PH)
        ov.d.rectangle((0, 0, PW, PH - 1600), fill=(120, 84, 52, 255))
        ov.d.rectangle((0, 0, PW, 22), fill=(160, 116, 74, 255))
        ov.commit()
        self.mic = microscope_sprite(1080)
        self.burr = burr_sprite(120, 3)
        self.hand = get_hand(600, -1.7)
        self.st = stamp_sprite('MICROSCOPE!', 120, color=BLUE, angle=-6)
        return img
    def dyn(self, img, t):
        tB = self.we('but')
        if t < tB:
            k = clamp01((t - self.we('pull')) / 0.5)
            bx, by = CX, 1050 - 380 * ease_out(k)
            draw_dog(img, 820, CX - 40, 1600 + 200, step=0.0, wag=math.sin(t * 9), burrs=6)
            paste_center(img, self.burr, bx, by, scale=0.8)
            draw_hand(img, self.hand, (bx + 30, by + 20), 0.3)
            pop(img, C('MOST PEOPLE: PULL IT OFF', 60, bg=WHITE), CX, 520, t, 0.05)
        else:
            k = ease_back((t - tB) / 0.35, 1.6)
            mx, my = CX + 40, 1620
            sh, pad = shadow_of(self.mic, 18, 0.45)
            paste_at(img, sh, mx - self.mic.width / 2 - pad + 20, my - self.mic.height - pad + 30)
            paste_center(img, self.mic, mx, my - self.mic.height / 2, scale=max(0.05, k))
            if k > 0.9:
                paste_center(img, self.burr, mx - 120, my - self.mic.height * 0.4, scale=0.45)
                glow(img, mx - 120, my - self.mic.height * 0.4, 200, (255, 255, 200), 0.4 + 0.2 * math.sin(t * 9))
            pop(img, C('HE PUT ONE UNDER A...', 60, bg=YEL), CX, 520, t, tB - 0.05)
            stamp_in(img, self.st, CX, 1820, t, self.we('microscope.') - 0.05)

# ====================================================================== 4: thousands of tiny hooks grabbing loops
def hooks_sprite(w, h, seed=1):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, int(h * 0.32)), fill=(120, 82, 40, 255))
    rng = np.random.default_rng(seed)
    for x in range(40, w - 20, 92):
        x = x + float(rng.uniform(-14, 14))
        y0 = h * 0.3
        y1 = h * 0.3 + float(rng.uniform(170, 230))
        d.line([(x, y0), (x, y1)], fill=(176, 130, 70, 255), width=22)
        d.arc((x - 2, y1 - 34, x + 64, y1 + 34), 0, 180, fill=(176, 130, 70, 255), width=22)
        d.line([(x + 62, y1), (x + 62, y1 - 34)], fill=(176, 130, 70, 255), width=20)
    return im

def loops_sprite(w, h, seed=2):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(h * 0.6), w, h), fill=(70, 96, 150, 255))
    for x in range(60, w - 20, 92):
        y = h * 0.62
        d.ellipse((x - 10, y - 250, x + 80, y + 30), outline=(150, 180, 235, 255), width=16)
    return im

class TinyHooks(Base):
    z0, z1 = 1.14, 1.22
    focus = (CX, 1150)
    R = 540
    def make_shakes(self):
        return [(self.we('grabbing'), 16, 0.34)]
    def events(self):
        return [(0.02, 'ding', 0.5), (self.we('thousands'), 'pop', 0.6), (self.we('hooks,'), 'tick', 0.5),
                (self.we('grabbing'), 'thud', 0.8), (self.we('grabbing') + 0.05, 'tape', 0.6), (self.we('loop'), 'pop', 0.5)]
    def plate(self):
        img = wall_plate('#1F2E3A', '#0A1016', 13, (CX, 1000, 1200))
        R = self.R
        self.hk = hooks_sprite(2 * R, 2 * R)
        self.lp = loops_sprite(2 * R, 2 * R)
        m = Image.new('L', (2 * R, 2 * R), 0)
        ImageDraw.Draw(m).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=255)
        self.mask = m
        rim = Image.new('RGBA', (2 * R + 80, 2 * R + 80), (0, 0, 0, 0))
        dr = ImageDraw.Draw(rim)
        dr.ellipse((0, 0, 2 * R + 79, 2 * R + 79), outline=(30, 30, 36, 255), width=56)
        dr.ellipse((30, 30, 2 * R + 49, 2 * R + 49), outline=(120, 126, 140, 255), width=10)
        self.rim = rim
        self.st = stamp_sprite('HOOKED!', 150, color=RED, angle=-8)
        return img
    def dyn(self, img, t):
        R = self.R
        tG = self.we('grabbing')
        k = ease_out((t - tG + 0.1) / 0.4)
        view = Image.new('RGBA', (2 * R, 2 * R), (235, 240, 230, 255))
        view.alpha_composite(self.lp, (0, int(260 - 300 * k)))
        view.alpha_composite(self.hk, (0, int(-40 + 10 * math.sin(t * 3))))
        view.putalpha(self.mask)
        cx, cy = CX, 1020
        paste_at(img, view, cx - R, cy - R)
        paste_at(img, self.rim, cx - R - 40, cy - R - 40)
        pop(img, C('THOUSANDS OF TINY HOOKS', 60, bg=YEL), CX, 380, t, self.we('thousands') - 0.05)
        stamp_in(img, self.st, CX, 1800, t, tG)
        pop(img, C('LOOPS', 70, bg=(150, 180, 235)), CX + 380, 1500, t, self.we('loop') - 0.05)

# ====================================================================== 5: copy a weed with cloth
class CopyWeed(Base):
    z0, z1 = 1.16, 1.26
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('weed'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('copy'), 'swipe', 0.5), (self.we('weed'), 'boom', 0.6)]
    def plate(self):
        img = wall_plate('#F7E3B5', '#B98A47', 23, (CX, 1000, 1300))
        self.burr = burr_sprite(190, 6)
        self.arr = arrow_sprite(260, 130)
        self.strip = strap_tex(420, 560, 'hook', (56, 64, 92), 6).rotate(-8, resample=Image.BICUBIC, expand=True)
        self.st = stamp_sprite('COPY A WEED?!', 120, color=RED, angle=-6)
        return img
    def dyn(self, img, t):
        tC, tW = self.we('copy'), self.we('cloth.')
        paste_center(img, self.burr, CX - 270, 1100 + 10 * math.sin(t * 6), scale=0.8 + 0.03 * math.sin(t * 8))
        pop(img, self.arr, CX + 10, 1100, t, tC - 0.05)
        if t > tW - 0.25:
            sh, pad = shadow_of(self.strip, 14, 0.45)
            k = ease_back((t - tW + 0.25) / 0.3, 1.8)
            paste_center(img, self.strip, CX + 290, 1100, scale=max(0.05, k) * 0.8)
        pop(img, C('BURR', 80, bg=WHITE), CX - 270, 760, t, 0.05)
        pop(img, C('CLOTH', 80, bg=YEL), CX + 290, 760, t, tW - 0.2)
        stamp_in(img, self.st, CX, 1800, t, self.we('weed'))

# ====================================================================== 6: cotton wore out, nylon, ~10 years
class Nylon(Base):
    z0, z1 = 1.14, 1.22
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('fast,'), 14, 0.3), (self.we('ten'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('wore'), 'crack', 0.6), (self.we('fast,'), 'buzzer', 0.6),
              (self.we('nylon,'), 'ding', 0.7)]
        tT = self.we('took')
        for k in range(8):
            ev.append((tT + k * 0.11, 'tick', 0.4))
        return ev
    def plate(self):
        img = wall_plate('#BFE3E0', '#4E8C8A', 13, (CX, 1000, 1300))
        self.cot = strap_tex(900, 260, 'loop', (226, 210, 180), 8)
        self.nyl = strap_tex(900, 260, 'hook', (40, 110, 200), 9)
        self.chk = check_sprite(80)
        self.cal = [calendar_page(n, 300) for n in range(1, 11)]
        return img
    def dyn(self, img, t):
        tW, tN, tT = self.we('wore'), self.we('nylon,'), self.we('took')
        k = ease_out((t - tW - 0.1) / 0.5)
        y = 820
        if t < tN + 0.3:
            l = self.cot.crop((0, 0, 450, 260)).rotate(-8 * k, resample=Image.BICUBIC, expand=True)
            r = self.cot.crop((450, 0, 900, 260)).rotate(10 * k, resample=Image.BICUBIC, expand=True)
            paste_center(img, l, CX - 225 - 60 * k, y + 50 * k)
            paste_center(img, r, CX + 225 + 60 * k, y + 70 * k)
            red_x(img, CX, y, 170, clamp01((t - self.we('fast,')) / 0.3))
            pop(img, C('COTTON WORE OUT', 66, bg=WHITE), CX, 520, t, 0.05, out_t=tN - 0.3)
        if t > tN - 0.1:
            kk = ease_back((t - tN + 0.1) / 0.3, 1.8)
            paste_center(img, self.nyl, CX, y + 20, scale=max(0.05, kk))
            pop(img, self.chk, CX + 420, y - 120, t, tN + 0.1)
            pop(img, C('NYLON WORKED!', 76, bg=(110, 220, 130)), CX, 520, t, tN - 0.05)
        if t > tT:
            n = min(10, 1 + int((t - tT) / 0.11))
            pop(img, self.cal[n - 1], CX, 1820, t, tT)
            pop(img, C('NEARLY 10 YEARS', 66, bg=YEL), CX, 1210, t, self.we('ten') - 0.05)

# ====================================================================== 7: the name
class Name(Base):
    z0, z1 = 1.14, 1.22
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('Velcro,'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Velcro,'), 'boom', 0.6), (self.we('French'), 'chime', 0.5),
                (self.we('velvet'), 'pop', 0.6), (self.we('and') - 0.03, 'pop', 0.6)]
    def plate(self):
        img = wall_plate('#B0306A', '#3A0E2A', 17, (CX, 1000, 1300))
        self.big = word_sprite([('VEL', YEL), ('CRO', (110, 220, 255))], 250)
        self.c1 = word_sprite([('VEL', YEL), ('OURS', WHITE)], 130)
        self.c2 = word_sprite([('CRO', (110, 220, 255)), ('CHET', WHITE)], 130)
        return img
    def dyn(self, img, t):
        tV, tF, tVe, tH = self.we('Velcro,'), self.we('French'), self.we('velvet'), self.we('hook.')
        pop(img, self.big, CX, 760, t, tV - 0.08)
        pop(img, C('FRENCH WORDS', 70, bg=WHITE), CX, 520, t, tF - 0.05)
        pop(img, self.c1, CX, 1060, t, tVe - 0.15)
        pop(img, C('= VELVET', 64, bg=YEL), CX, 1210, t, tVe - 0.05)
        pop(img, self.c2, CX, 1720, t, tH - 0.25)
        pop(img, C('= HOOK', 64, bg=(110, 220, 255)), CX, 1870, t, tH - 0.12)

# ====================================================================== 8: nobody cared
class NobodyCared(Base):
    def make_shakes(self):
        return [(self.we('nobody'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('nobody'), 'buzzer', 0.7), (self.we('cared'), 'bloop', 0.5)]
    def plate(self):
        img = wall_plate('#E9D7B8', '#9C7A55', 11, (CX, 1000, 1300))
        ov = OV(img, 0, 1380, PW, PH)
        ov.d.rectangle((0, 0, PW, PH - 1380), fill=(150, 96, 52, 255))
        ov.d.rectangle((0, 0, PW, 24), fill=(180, 120, 70, 255))
        ov.commit()
        lay = Layer()
        for x in (CX - 350, CX + 350):
            mannequin(lay, x, 1560, 980)
        img = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.q = qmark(190)
        self.strip = strap_tex(420, 300, 'loop', STRAP, 12)
        self.st = stamp_sprite('NOBODY CARED', 120, color=RED, angle=-6)
        return img
    def dyn(self, img, t):
        tN = self.we('nobody')
        paste_center(img, self.strip, CX, 1000 + 12 * math.sin(t * 5))
        for k, (x, y) in enumerate(((CX - 350, 640), (CX + 350, 640))):
            pop(img, self.q, x, y + 10 * math.sin(t * 6 + k), t, tN + k * 0.12)
        pop(img, C('AT FIRST...', 80, bg=WHITE), CX, 520, t, 0.05)
        stamp_in(img, self.st, CX, 1820, t, tN)

# ====================================================================== 9: NASA / Apollo, no more floating
class Apollo(Base):
    z0, z1 = 1.14, 1.22
    focus = (CX, 1180)
    def make_shakes(self):
        return [(self.we('stop'), 14, 0.3), (self.we('suddenly'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('NASA'), 'pop', 0.5), (self.we('Apollo'), 'riser', 0.4),
              (self.we('stop'), 'thud', 0.8), (self.we('floating'), 'tape', 0.6), (self.we('suddenly'), 'party', 0.7)]
        tE = self.we('everyone')
        for k in range(3):
            ev.append((tE + k * 0.15, 'pop', 0.45))
        return ev
    def plate(self):
        img = space_wall_plate()
        self.strip = strap_tex(1000, 150, 'loop', STRAP, 14)
        self.items = [pen_sprite(), spoon_sprite(), pouch_sprite('SNACK')]
        self.shoes = [shoe_sprite(380, c) for c in ((220, 70, 60), (60, 140, 220), (250, 190, 50))]
        return img
    def dyn(self, img, t):
        tS, tSu = self.we('stop'), self.we('suddenly')
        sy = 1300
        paste_center(img, self.strip, CX, sy)
        k = ease_out((t - tS + 0.15) / 0.35)
        homes = [(CX - 330, 330), (CX - 20, 330), (CX + 310, 330)]
        floats = [(CX - 330, 930, 40), (CX + 30, 800, -60), (CX + 310, 1000, 25)]
        for j, (sp, (hx, _), (fx, fy, rot)) in enumerate(zip(self.items, homes, floats)):
            ft = t * 0.9 + j * 1.7
            x = fx + 40 * math.sin(ft)
            y = fy + 50 * math.sin(ft * 1.3)
            a = rot + 25 * math.sin(ft * 0.8) + 30 * t
            ty = sy - sp.height * 0.35 + 40
            xx = x + (hx - x) * k
            yy = y + (ty - y) * k
            aa = a * (1 - k)
            r = sp.rotate(aa, resample=Image.BICUBIC, expand=True)
            paste_center(img, r, xx, yy)
        if t > tSu - 0.1:
            for j, x in enumerate((CX - 380, CX, CX + 380)):
                pop(img, self.shoes[j], x, 1830 + (j % 2) * 40, t, self.we('everyone') + j * 0.15)
        pop(img, C('NASA: APOLLO MISSIONS', 62, bg=WHITE), CX, 520, t, self.we('NASA') - 0.05, out_t=tS - 0.3)
        pop(img, C('NO MORE FLOATING!', 72, bg=YEL), CX, 520, t, tS - 0.05, out_t=tSu - 0.3)
        pop(img, C('SUDDENLY EVERYONE WANTED IT', 54, bg=(110, 220, 130)), CX, 520, t, tSu - 0.05)

# ====================================================================== 10: people think NASA invented it -> loops to the hook
class Outro(Hook):
    def make_shakes(self):
        return [(self.we('nope,'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('NASA'), 'riser', 0.5), (self.we('nope,'), 'buzzer', 0.8),
                (self.we('truth') - 0.05, 'swipe', 0.5)]
    def tswitch(self):
        return self.we('truth') - 0.1
    def plate(self):
        img = Hook.plate(self)
        self.hook_plate = img.copy()
        self.rocket = rocket_sprite(1000)
        self.st = stamp_sprite('NOPE!', 200, color=RED, angle=-8)
        return space_plate_dark()
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hook_plate, (0, 0))
            self.hero(img, t - self.dur)   # ends right where frame 0 begins
            return
        tN = self.we('nope,')
        bob = 14 * math.sin(t * 4)
        paste_center(img, self.rocket, CX, 1080 + bob)
        glow(img, CX, 1600 + bob, 200, (255, 170, 60), 0.7 + 0.2 * math.sin(t * 20))
        pop(img, C('MOST PEOPLE THINK...', 70, bg=WHITE), CX, 520, t, 0.05, out_t=self.we('NASA') - 0.3)
        pop(img, C('NASA INVENTED IT?', 74, bg=YEL), CX, 520, t, self.we('NASA') - 0.05)
        if t > tN:
            red_x(img, CX, 1080, 380, clamp01((t - tN) / 0.3))
        stamp_in(img, self.st, CX, 1820, t, tN)
    def cam(self, t):
        tw = self.tswitch()
        if t >= tw:
            return self.z0, CX, 1180, 0.0
        dx, dy, dr = self.shake(t)
        p = 1 - ease_out(t / 0.32)
        return 1.14 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1150 + dy, 2.0 * p + dr

def space_plate_dark():
    if 'spd' in _PL:
        return _PL['spd'].copy()
    arr = vgrad(PW, PH, [(0, '#0B1030'), (1, '#1E2A5A')])
    img = to_img(arr).convert('RGBA')
    ov = OV(img, 0, 0, PW, PH)
    rng = np.random.default_rng(4)
    for _ in range(220):
        x, y = rng.uniform(0, PW), rng.uniform(0, PH)
        r = rng.uniform(1.5, 4.5)
        ov.d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(rng.uniform(120, 255))))
    ov.d.ellipse((-400, 1900, PW + 400, PH + 1400), fill=(50, 120, 210, 255))
    ov.d.ellipse((100, 1980, 700, 2300), fill=(70, 160, 90, 255))
    ov.commit()
    img = plate_img(to_arr(img))
    _PL['spd'] = img
    return img.copy()

SCENES = [Hook, Alps, Burrs, Microscope, TinyHooks, CopyWeed, Nylon, Name, NobodyCared, Apollo, Outro]
