"""Ketchup was once sold as medicine (2026-11-17)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish, table_bg
from mw_scenes import glow, stamp_sprite, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import ground_shadow, red_x

RED = (214, 50, 44)
KRED = '#D2261C'
YEL = (255, 210, 60)
BLUE = (40, 120, 200)
GREEN = (60, 170, 90)
WHITE = (255, 255, 255)

class Base(S):
    focus = (CX, 1100)
    z0, z1 = 1.16, 1.24

# ====================================================================== text helpers
def word_sprite(parts, size):
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

def qmark(size=150, col=(255, 255, 255), txt='?'):
    return text_img(txt, size, fill=col, stroke=10, stroke_fill=(20, 20, 30), shadow_px=4)

def check_sprite(R=70, col=GREEN):
    im = Image.new('RGBA', (2 * R + 8, 2 * R + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 2 * R + 4, 2 * R + 4), fill=col + (255,), outline=(255, 255, 255, 255), width=8)
    d.line([(R * 0.55 + 4, R + 4), (R * 0.9 + 4, R * 1.35 + 4), (R * 1.5 + 4, R * 0.65 + 4)], fill=(255, 255, 255, 255), width=int(R * 0.22), joint='curve')
    return im

def with_shadow(img, sp, cx, cy, blur=14, a=0.45, dx=18, dy=26):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, cx - sp.width / 2 - pad + dx, cy - sp.height / 2 - pad + dy)
    paste_at(img, sp, cx - sp.width / 2, cy - sp.height / 2)

# ====================================================================== plates
_PL = {}
def wall_plate(c0='#F2B266', c1='#B5562C', seed=3, spot=(CX, 900, 1300), counter=None):
    key = (c0, c1, seed, spot, counter)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.9 + 0.1 * smooth_noise(PH, PW, 110, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, spot[0], spot[1], spot[2], 1.3))[..., None]
    if counter is not None:
        y0, col = counter
        top = vgrad(PW, PH - y0, [(0, col), (1, '#2A1A10')])
        arr[y0:] = top * (0.9 + 0.1 * smooth_noise(PH - y0, PW, 40, seed + 3, 2))[..., None]
        arr[y0:y0 + 10] *= 1.25
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    _PL[key] = img
    return img.copy()

def sea_plate():
    if 'sea' in _PL:
        return _PL['sea'].copy()
    arr = vgrad(PW, PH, [(0, '#5FB0E8'), (0.45, '#BFE3F7'), (0.46, '#2F78B8'), (1, '#123E6E')])
    img = to_img(arr).convert('RGBA')
    ov = OV(img, 0, 0, PW, PH)
    for (x, y, r) in ((250, 420, 70), (980, 330, 90), (620, 560, 60)):
        for k in range(4):
            ov.d.ellipse((x - r + k * r * 0.5, y - r * 0.6, x + r * 0.4 + k * r * 0.5, y + r * 0.4), fill=(255, 255, 255, 230))
    ov.commit()
    img = plate_img(vignette(to_arr(img), 0.35))
    _PL['sea'] = img
    return img.copy()

def table_plate(seed=5):
    key = ('table', seed)
    if key not in _PL:
        _PL[key] = plate_img(table_bg(seed))
    return _PL[key].copy()

# ====================================================================== props
_SP = {}

def label_tex(w, h, title='KETCHUP', bg=(250, 244, 228), fg=(200, 30, 24), sub=None):
    im = Image.new('RGBA', (w, h), bg + (255,))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w - 7, h - 7), radius=20, outline=fg + (255,), width=8)
    size = int(h * 0.36)
    f = font(size)
    while f.getlength(title) > w * 0.84 and size > 10:
        size -= 2
        f = font(size)
    tw = f.getlength(title)
    ty = h * 0.5 - size * 0.62 if sub else h * 0.5 - size * 0.7
    d.text(((w - tw) / 2, ty), title, font=f, fill=fg)
    if sub:
        f2 = font(int(size * 0.5))
        sw = f2.getlength(sub)
        d.text(((w - sw) / 2, ty + size * 1.1), sub, font=f2, fill=fg)
    arr = np.asarray(im, np.float32) / 255
    xs = np.linspace(-1, 1, w)
    sh = 0.72 + 0.28 * np.sqrt(np.clip(1 - xs ** 2, 0, 1))
    arr[..., :3] *= sh[None, :, None]
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')

def bottle_sprite(H=900):
    key = ('bottle', H)
    if key in _SP:
        return _SP[key]
    Wd = int(H * 0.6)
    lay = Layer(Wd, H + 10)
    cx = Wd / 2
    kw = dict(spec=0.55, shin=40)
    capsule(lay, (cx, H * 0.45), (cx, H * 0.80), H * 0.2, H * 0.2, KRED, **kw)
    capsule(lay, (cx, H * 0.25), (cx, H * 0.42), H * 0.1, H * 0.19, KRED, **kw)
    capsule(lay, (cx, H * 0.13), (cx, H * 0.22), H * 0.1, H * 0.1, '#F2F0EA', spec=0.4, shin=30)
    capsule(lay, (cx, H * 0.035), (cx, H * 0.12), H * 0.028, H * 0.06, '#F2F0EA', spec=0.4, shin=30)
    lw, lh = int(H * 0.34), int(H * 0.2)
    tex = label_tex(lw, lh, 'KETCHUP')
    y0 = H * 0.52
    quad(lay, tex, [(cx - lw / 2, y0), (cx + lw / 2, y0), (cx + lw / 2, y0 + lh), (cx - lw / 2, y0 + lh)])
    fill_poly(lay, [(cx - H * 0.15, H * 0.36), (cx - H * 0.115, H * 0.36), (cx - H * 0.115, H * 0.92), (cx - H * 0.15, H * 0.9)], '#FFFFFF', 0.28)
    sp, x0, y0_ = layer_sprite(lay, 2)
    _SP[key] = sp
    return sp

def rot_sprite(sp, ang, key=None):
    if key is not None:
        k = (key, round(ang, 1))
        if k in _SP:
            return _SP[k]
    r = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
    if key is not None:
        _SP[k] = r
    return r

def pill_sprite(L=110, ang=0, c1=KRED, c2='#F4F1EA'):
    q = int(round(ang / 15.0)) % 24
    key = ('pill', L, q, c1, c2)
    if key in _SP:
        return _SP[key]
    a = math.radians(q * 15)
    n = int(L * 1.5)
    lay = Layer(n, n)
    c = n / 2
    dx, dy = math.cos(a) * L * 0.3, math.sin(a) * L * 0.3
    r = L * 0.2
    capsule(lay, (c - dx, c - dy), (c, c), r, r, c1, spec=0.6, shin=40)
    capsule(lay, (c, c), (c + dx, c + dy), r, r, c2, spec=0.6, shin=40)
    sp, _, _ = layer_sprite(lay, 2)
    _SP[key] = sp
    return sp

def tomato_sprite(R=200):
    key = ('tomato', R)
    if key in _SP:
        return _SP[key]
    n = int(R * 2.6)
    lay = Layer(n, n)
    c = n / 2
    ellipsoid(lay, (c, c + R * 0.08), R, R * 0.86, 0, '#E3321F', spec=0.6, shin=36)
    ellipsoid(lay, (c - R * 0.35, c + R * 0.1), R * 0.45, R * 0.7, 0.1, '#E83A24', spec=0.3, shin=30, amb=0.42)
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = R * (0.5 if k % 2 == 0 else 0.16)
        pts.append((c + math.cos(ang) * rr * 1.1, c - R * 0.66 + math.sin(ang) * rr * 0.45))
    fill_poly(lay, pts, '#2E8B3A')
    capsule(lay, (c, c - R * 0.7), (c + R * 0.06, c - R * 0.95), R * 0.05, R * 0.04, '#3C7A2E', spec=0.3)
    sp, _, _ = layer_sprite(lay, 2)
    _SP[key] = sp
    return sp

def fish_sprite(L=420, col='#8FA9BF', slim=0.14):
    key = ('fish', L, col, slim)
    if key in _SP:
        return _SP[key]
    lay = Layer(int(L * 1.3), int(L * 0.6))
    cx, cy = L * 0.55, L * 0.3
    fill_poly(lay, [(cx - L * 0.36, cy), (cx - L * 0.55, cy - L * 0.16), (cx - L * 0.5, cy), (cx - L * 0.55, cy + L * 0.16)], '#6E8AA3')
    fill_poly(lay, [(cx - L * 0.05, cy - L * slim * 0.8), (cx + L * 0.08, cy - L * slim * 1.5), (cx + L * 0.12, cy - L * slim * 0.8)], '#6E8AA3')
    ellipsoid(lay, (cx, cy), L * 0.4, L * slim, 0, col, spec=0.7, shin=40)
    sphere(lay, (cx + L * 0.27, cy - L * slim * 0.25), L * 0.035, '#FFFFFF', spec=0.5)
    sphere(lay, (cx + L * 0.28, cy - L * slim * 0.25), L * 0.018, '#111111', spec=0.8)
    sp, _, _ = layer_sprite(lay, 2)
    d = ImageDraw.Draw(sp)
    _SP[key] = sp
    return sp

def walnut_sprite(R=150):
    key = ('walnut', R)
    if key in _SP:
        return _SP[key]
    n = int(R * 2.4)
    lay = Layer(n, n)
    c = n / 2
    ellipsoid(lay, (c, c), R, R * 0.84, 0.0, '#B07A42', spec=0.25, shin=14, crease=0.55)
    sp, _, _ = layer_sprite(lay, 2)
    d = ImageDraw.Draw(sp)
    rng = np.random.default_rng(4)
    w, h = sp.size
    for _ in range(26):
        x, y = rng.uniform(0.2, 0.8) * w, rng.uniform(0.2, 0.8) * h
        r = rng.uniform(0.06, 0.16) * R
        a0 = rng.uniform(0, 360)
        d.arc((x - r, y - r, x + r, y + r), a0, a0 + 140, fill=(110, 70, 34, 255), width=max(3, int(R * 0.03)))
    _SP[key] = sp
    return sp

def oyster_sprite(R=170):
    key = ('oyster', R)
    if key in _SP:
        return _SP[key]
    n = int(R * 2.6)
    lay = Layer(n, n)
    c = n / 2
    ellipsoid(lay, (c, c + R * 0.12), R * 1.05, R * 0.62, -0.15, '#8E877C', spec=0.25, shin=12)
    ellipsoid(lay, (c, c + R * 0.05), R * 0.8, R * 0.42, -0.15, '#E9E2D4', spec=0.6, shin=30)
    sphere(lay, (c + R * 0.1, c + R * 0.02), R * 0.18, '#F7F4FA', spec=0.9, shin=60)
    sp, _, _ = layer_sprite(lay, 2)
    d = ImageDraw.Draw(sp)
    w, h = sp.size
    for k in range(5):
        rr = R * (0.85 + 0.09 * k)
        d.arc((w / 2 - rr * 1.1, h / 2 - rr * 0.62 + R * 0.12, w / 2 + rr * 1.1, h / 2 + rr * 0.62 + R * 0.12), 20, 160, fill=(105, 98, 88, 255), width=5)
    _SP[key] = sp
    return sp

def jar_sprite(H=620):
    key = ('jar', H)
    if key in _SP:
        return _SP[key]
    Wd = int(H * 0.95)
    lay = Layer(Wd, H + 20)
    cx = Wd / 2
    ellipsoid(lay, (cx, H * 0.6), H * 0.42, H * 0.38, 0, '#9A5A2E', spec=0.35, shin=20)
    capsule(lay, (cx, H * 0.2), (cx, H * 0.3), H * 0.22, H * 0.26, '#8A4E26', spec=0.3, shin=20)
    ellipsoid(lay, (cx, H * 0.19), H * 0.24, H * 0.06, 0, '#B06A36', spec=0.3)
    ellipsoid(lay, (cx, H * 0.19), H * 0.19, H * 0.04, 0, '#5A3A18', spec=0.5, shin=40)
    fill_poly(lay, [(cx - H * 0.4, H * 0.55), (cx + H * 0.4, H * 0.55), (cx + H * 0.38, H * 0.62), (cx - H * 0.38, H * 0.62)], '#D9A060', 0.85)
    sp, _, _ = layer_sprite(lay, 2)
    _SP[key] = sp
    return sp

def ship_sprite(Wd=760):
    key = ('ship', Wd)
    if key in _SP:
        return _SP[key]
    Hh = int(Wd * 1.05)
    im = Image.new('RGBA', (Wd, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    hy = Hh * 0.72
    d.polygon([(0, hy), (Wd, hy - 20), (Wd * 0.84, Hh - 4), (Wd * 0.12, Hh - 4)], fill=(110, 66, 36, 255), outline=(60, 34, 18, 255))
    d.rectangle((Wd * 0.05, hy + 20, Wd * 0.95, hy + 34), fill=(230, 190, 90, 255))
    for mx, top in ((Wd * 0.35, Hh * 0.04), (Wd * 0.66, Hh * 0.12)):
        d.rectangle((mx - 9, top, mx + 9, hy), fill=(80, 50, 28, 255))
        for k, (yy0, yy1, ww) in enumerate(((top + 30, top + Hh * 0.28, Wd * 0.2), (top + Hh * 0.3, hy - 30, Wd * 0.25))):
            d.polygon([(mx - ww, yy0), (mx + ww, yy0), (mx + ww * 1.08, yy1), (mx - ww * 1.08, yy1)], fill=(248, 240, 220, 255), outline=(170, 150, 120, 255))
        d.polygon([(mx + 9, top), (mx + 80, top + 22), (mx + 9, top + 44)], fill=(214, 50, 44, 255))
    arr = np.asarray(im, np.float32) / 255
    ys = np.linspace(1.05, 0.8, Hh)
    arr[..., :3] *= ys[:, None, None]
    sp = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    _SP[key] = sp
    return sp

def card_sprite(w=640, h=760):
    key = ('card', w, h)
    if key in _SP:
        return _SP[key]
    arr = np.ones((h, w, 3), np.float32) * hexc('#F1E2BE')
    arr *= (0.86 + 0.14 * smooth_noise(h, w, 30, 8, 3))[..., None]
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(150, 110, 60, 255), width=8)
    f = font(62, FONT_SERIF)
    for k, line in enumerate(('TOMATO', 'KETCHUP')):
        tw = f.getlength(line)
        d.text(((w - tw) / 2, 50 + k * 74), line, font=f, fill=(120, 40, 20))
    for k in range(8):
        y = 250 + k * 56
        x1 = w - 60 - (k * 37 % 140)
        d.line([(60, y), (x1, y)], fill=(110, 80, 50, 255), width=6)
    _SP[key] = im
    return im

def bag_sprite(w=520):
    key = ('bag', w)
    if key in _SP:
        return _SP[key]
    h = int(w * 0.7)
    im = Image.new('RGBA', (w, h + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.arc((w * 0.3, 0, w * 0.7, 180), 180, 360, fill=(40, 30, 26, 255), width=26)
    d.polygon([(w * 0.08, 100), (w * 0.92, 100), (w, h + 116), (0, h + 116)], fill=(46, 36, 32, 255))
    d.rectangle((w * 0.02, 100, w * 0.98, 150), fill=(62, 50, 44, 255))
    d.rectangle((w * 0.44, 118, w * 0.56, 176), fill=(220, 180, 80, 255))
    d.rectangle((w * 0.4, 230, w * 0.6, 270), fill=(240, 240, 240, 255))
    d.rectangle((w * 0.48, 190, w * 0.52, 310), fill=(240, 240, 240, 255))
    d.rectangle((w * 0.4, 230, w * 0.6, 270), fill=(214, 50, 44, 255))
    d.rectangle((w * 0.465, 195, w * 0.535, 305), fill=(214, 50, 44, 255))
    _SP[key] = im
    return im

def pill_bottle_sprite(H=760):
    key = ('pbottle', H)
    if key in _SP:
        return _SP[key]
    Wd = int(H * 0.7)
    lay = Layer(Wd, H + 10)
    cx = Wd / 2
    capsule(lay, (cx, H * 0.42), (cx, H * 0.75), H * 0.25, H * 0.25, '#C0661E', spec=0.7, shin=50)
    capsule(lay, (cx - H * 0.2, H * 0.15), (cx + H * 0.2, H * 0.15), H * 0.075, H * 0.075, '#F2F0EA', spec=0.4, shin=30)
    lw, lh = int(H * 0.44), int(H * 0.3)
    tex = label_tex(lw, lh, 'TOMATO', sub='PILLS', fg=(200, 30, 24))
    y0 = H * 0.4
    quad(lay, tex, [(cx - lw / 2, y0), (cx + lw / 2, y0), (cx + lw / 2, y0 + lh), (cx - lw / 2, y0 + lh)])
    fill_poly(lay, [(cx - H * 0.2, H * 0.3), (cx - H * 0.16, H * 0.3), (cx - H * 0.16, H * 0.95), (cx - H * 0.2, H * 0.93)], '#FFFFFF', 0.25)
    sp, _, _ = layer_sprite(lay, 2)
    _SP[key] = sp
    return sp

def half_pill(L=520, side=0):
    key = ('half', L, side)
    if key in _SP:
        return _SP[key]
    n = int(L * 1.0)
    lay = Layer(n, int(L * 0.6))
    r = L * 0.2
    cy = L * 0.3
    if side == 0:
        capsule(lay, (r + 4, cy), (L * 0.5, cy), r, r, KRED, spec=0.6, shin=40)
    else:
        capsule(lay, (L * 0.5 - r * 0.0 + 10, cy), (L * 0.5 + L * 0.3, cy), r, r, '#F4F1EA', spec=0.6, shin=40)
    sp, _, _ = layer_sprite(lay, 2)
    _SP[key] = sp
    return sp

def tp_sprite(R=150):
    key = ('tp', R)
    if key in _SP:
        return _SP[key]
    lay = Layer(int(R * 2.6), int(R * 3.4))
    cx = R * 1.3
    capsule(lay, (cx, R * 1.0), (cx, R * 2.3), R, R, '#F7F7F2', spec=0.3, shin=16, amb=0.5)
    sp, _, _ = layer_sprite(lay, 2)
    d = ImageDraw.Draw(sp)
    w, h = sp.size
    d.rectangle((0, 0, w, R * 0.95), fill=(0, 0, 0, 0))
    d.ellipse((w / 2 - R, R * 0.6, w / 2 + R, R * 1.3), fill=(240, 240, 232, 255), outline=(200, 200, 190, 255), width=4)
    d.ellipse((w / 2 - R * 0.35, R * 0.83, w / 2 + R * 0.35, R * 1.07), fill=(160, 130, 100, 255))
    d.polygon([(w / 2 + R * 0.2, h - R * 0.9), (w / 2 + R * 1.25, h - R * 0.7), (w / 2 + R * 1.25, h - 4), (w / 2 + R * 0.2, h - 8)], fill=(244, 244, 238, 255))
    _SP[key] = sp
    return sp

def fries_sprite(w=520):
    key = ('fries', w)
    if key in _SP:
        return _SP[key]
    h = int(w * 1.15)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    for k in range(16):
        x = w * (0.18 + 0.64 * k / 15) + rng.uniform(-10, 10)
        top = h * rng.uniform(0.0, 0.18)
        a = rng.uniform(-0.15, 0.15)
        fw = w * 0.07
        pts = [(x - fw / 2, top), (x + fw / 2, top), (x + fw / 2 + a * h * 0.4, h * 0.55), (x - fw / 2 + a * h * 0.4, h * 0.55)]
        d.polygon(pts, fill=(246, 200, 70, 255), outline=(200, 140, 40, 255))
    d.polygon([(w * 0.05, h * 0.36), (w * 0.95, h * 0.36), (w * 0.82, h), (w * 0.18, h)], fill=(214, 40, 34, 255), outline=(150, 20, 20, 255))
    d.polygon([(w * 0.05, h * 0.36), (w * 0.5, h * 0.48), (w * 0.95, h * 0.36), (w * 0.93, h * 0.42), (w * 0.5, h * 0.55), (w * 0.07, h * 0.42)], fill=(184, 30, 26, 255))
    arr = np.asarray(im, np.float32) / 255
    xs = np.linspace(-1, 1, w)
    arr[..., :3] *= (0.82 + 0.25 * np.sqrt(np.clip(1 - xs ** 2, 0, 1)))[None, :, None]
    sp = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    _SP[key] = sp
    return sp

def plate_food_sprite(w=760):
    key = ('plate', w)
    if key in _SP:
        return _SP[key]
    h = int(w * 0.5)
    lay = Layer(w + 20, h + 20)
    ellipsoid(lay, (w / 2 + 10, h / 2 + 10), w / 2, h / 2, 0, '#F4F4F0', spec=0.4, shin=30, amb=0.55)
    ellipsoid(lay, (w / 2 + 10, h / 2 + 6), w * 0.38, h * 0.36, 0, '#E6E6E0', spec=0.2, amb=0.6)
    sp, _, _ = layer_sprite(lay, 2)
    d = ImageDraw.Draw(sp)
    rng = np.random.default_rng(3)
    for k in range(14):
        x = w * rng.uniform(0.3, 0.62); y = h * rng.uniform(0.3, 0.62)
        a = rng.uniform(0, math.pi)
        L = w * 0.13
        d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L * 0.5)], fill=(236, 186, 60, 255), width=int(w * 0.035))
    d.ellipse((w * 0.62, h * 0.34, w * 0.8, h * 0.6), fill=(200, 30, 22, 255))
    d.ellipse((w * 0.65, h * 0.37, w * 0.7, h * 0.43), fill=(240, 110, 100, 255))
    _SP[key] = sp
    return sp

def pile_sprite(w=900, h=240, n=60, seed=5, L=90):
    key = ('pile', w, h, n, seed, L)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (w + 200, h + 200), (0, 0, 0, 0))
    rng = np.random.default_rng(seed)
    pts = []
    for _ in range(n):
        u = rng.uniform(-1, 1)
        x = w / 2 + u * w / 2
        top = h * (1 - (1 - u * u) * 0.9)
        y = rng.uniform(top, h)
        pts.append((y, x, rng.uniform(0, 360)))
    for y, x, a in sorted(pts):
        sp = pill_sprite(L, a)
        paste_center(im, sp, x + 100, y + 100)
    _SP[key] = im
    return im

# ====================================================================== 0: hero bottle firing pills
class Hook(Base):
    """Frame 0: a giant ketchup bottle being squeezed, red-and-white pills bursting from the nozzle."""
    z0, z1 = 1.14, 1.2
    BC = (500, 1150)
    ANG = -56
    BH = 1080
    def make_shakes(self):
        return [(0.0, 12, 0.3), (self.we('pill') - 0.02, 16, 0.32)]
    def events(self):
        return [(0.0, 'bigpop', 0.8), (0.0, 'rattle', 0.6), (self.we('medicine...') - 0.03, 'ding', 0.6),
                (self.we('pill') - 0.02, 'boom', 0.7), (self.we('pill') + 0.1, 'rattle', 0.6)]
    def plate(self):
        img = wall_plate('#FFB65C', '#B8321E', 7, (CX, 1000, 1300), counter=(1690, '#7A4A2A'))
        b = rot_sprite(bottle_sprite(self.BH), self.ANG)
        self.bot = b
        self.bsh = shadow_of(b, 18, 0.5)
        pile = pile_sprite(1100, 200, 80, 5, 100)
        paste_center(img, pile, CX + 80, 1930)
        self.hand = get_hand(600, 0.5)
        self.medchip = C('+ MEDICINE', 92, bg=(90, 200, 120), fg=(255, 255, 255))
        self.st = C('IN PILL FORM!', 92, bg=YEL)
        return img
    def nozzle(self):
        a = math.radians(-self.ANG)
        d = self.BH * 0.47
        return (self.BC[0] + math.sin(a) * d, self.BC[1] - math.cos(a) * d)
    def hero(self, img, t):
        sq = 0.5 + 0.5 * math.sin(t * 2 * math.pi / 0.75)
        s = 1.0 + 0.015 * sq
        sh, pad = self.bsh
        paste_at(img, sh, self.BC[0] - self.bot.width / 2 - pad + 26, self.BC[1] - self.bot.height / 2 - pad + 34)
        paste_center(img, self.bot, self.BC[0], self.BC[1], scale=s)
        # hand squeezing the bottle body
        draw_hand(img, self.hand, (self.BC[0] - 60 + 14 * sq, self.BC[1] + 290), 0.2)
        nx, ny = self.nozzle()
        rng = np.random.default_rng(1)
        n = 40
        period = 1.6
        for k in range(n):
            age = (t + k * period / n) % period
            vx = -120 + 420 * ((k * 0.618) % 1.0)
            vy = -560 + 330 * ((k * 0.377) % 1.0)
            spin = 400 * (((k * 0.73) % 1.0) - 0.5)
            x = nx + 20 + vx * age
            y = ny + vy * age + 0.5 * 1500 * age * age
            if y > 2100 or x > 1300:
                continue
            L = 96 + 40 * ((k * 0.41) % 1.0)
            sp = pill_sprite(int(L // 8 * 8), spin * age + k * 47)
            paste_center(img, sp, x, y)
        glow(img, nx, ny, 160, (255, 230, 200), 0.35 + 0.2 * sq)
    def dyn(self, img, t):
        self.hero(img, t)
        tM, tP = self.we('medicine...'), self.we('pill')
        pop(img, self.medchip, CX, 1770, t, tM - 0.06, out_t=tP - 0.12)
        stamp_in(img, self.st, CX, 1770, t, tP - 0.04)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, 1140 + dy, dr

# ====================================================================== 1: no tomatoes
class NoTomato(Base):
    z0, z1 = 1.16, 1.26
    def make_shakes(self):
        return [(self.we("didn't"), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('first') - 0.03, 'pop', 0.5), (self.we("didn't"), 'buzzer', 0.7), (self.we('even'), 'crack', 0.5)]
    def plate(self):
        img = wall_plate('#FFE2A8', '#C8702E', 2, (CX, 1000, 1200), counter=(1640, '#8A5A34'))
        self.tom = tomato_sprite(300)
        self.bot = bottle_sprite(640)
        self.st = stamp_sprite('NO TOMATOES', 120, color=RED, angle=-7)
        return img
    def dyn(self, img, t):
        tD = self.we("didn't")
        with_shadow(img, self.bot, CX - 300, 1240 + 6 * math.sin(t * 5), a=0.4)
        bob = 10 * math.sin(t * 6)
        pop(img, self.tom, CX + 200, 980 + bob, t, 0.0, dur=0.25)
        pop(img, C('THE FIRST KETCHUP', 74, bg=WHITE), CX, 520, t, self.we('first') - 0.08)
        if t > tD:
            red_x(img, CX + 200, 980, 250, clamp01((t - tD) / 0.3))
        stamp_in(img, self.st, CX, 1830, t, tD + 0.05)

# ====================================================================== 2: fish sauce, China + SE Asia, ke-tsiap
class FishSauce(Base):
    z0, z1 = 1.16, 1.25
    def make_shakes(self):
        return [(self.we('fish'), 12, 0.28), (self.we('called') + 0.25, 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('salty') - 0.03, 'pop', 0.5), (self.we('fish'), 'splat', 0.6),
                (self.we('China') - 0.03, 'pop', 0.5), (self.we('Southeast') - 0.03, 'pop', 0.5), (self.we('called') + 0.2, 'boom', 0.6)]
    def plate(self):
        img = wall_plate('#E8C48A', '#7A3A1A', 9, (CX, 1000, 1300), counter=(1660, '#6A4024'))
        self.jar = jar_sprite(700)
        self.fish = [fish_sprite(330, c) for c in ('#8FA9BF', '#A9B8C4', '#7F98B0')]
        self.word = word_sprite([('KÊ-', YEL), ('TSIAP', WHITE)], 190)
        return img
    def dyn(self, img, t):
        tF, tC = self.we('fish'), self.we('called')
        jy = 980
        for k in range(3):
            t0 = tF - 0.5 + k * 0.35
            u = (t - t0) / 0.7
            if 0 <= u <= 1:
                x = CX + (-420 + 840 * ((k * 0.6) % 1)) * (1 - u)
                y = 700 + (jy - 740) * u - 380 * math.sin(math.pi * u) * (1 - u)
                sp = self.fish[k].rotate(-60 * u + 20, resample=Image.BICUBIC, expand=True)
                paste_center(img, sp, x, y)
        with_shadow(img, self.jar, CX, jy + 120, a=0.45)
        if t > tF + 0.15:
            for k in range(6):
                u = ((t - tF - 0.15) * 1.2 + k / 6) % 1
                glow(img, CX - 150 + 60 * k, 680 - 100 * u, 30, (240, 230, 210), 0.5 * (1 - u))
        pop(img, C('SALTY FISH SAUCE', 72, bg=WHITE), CX, 520, t, self.we('salty') - 0.06, out_t=self.we('China') - 0.15)
        pop(img, C('CHINA', 74, bg=YEL), CX - 230, 520, t, self.we('China') - 0.06, out_t=tC + 0.1)
        pop(img, C('SE ASIA', 74, bg=(120, 210, 255)), CX + 230, 520, t, self.we('Southeast') - 0.06, out_t=tC + 0.1)
        pop(img, self.word, CX, 560, t, tC + 0.18)
        pop(img, C('THE ORIGINAL "KETCHUP"', 58, bg=WHITE), CX, 1820, t, tC + 0.3)

# ====================================================================== 3: sailors to Europe, anchovies walnuts oysters
class Sailors(Base):
    z0, z1 = 1.16, 1.24
    def make_shakes(self):
        return [(self.we('oysters.'), 14, 0.3)]
    def tcut(self):
        return self.we('cooks') - 0.08
    def events(self):
        return [(0.02, 'wind', 0.6), (self.we('Europe,') - 0.03, 'pop', 0.5), (self.tcut(), 'swipe', 0.5),
                (self.we('anchovies,') - 0.03, 'pop', 0.6), (self.we('walnuts,') - 0.03, 'pop', 0.6),
                (self.we('even') - 0.03, 'bigpop', 0.6)]
    def plate(self):
        self.sea = sea_plate()
        self.ship = ship_sprite(820)
        self.fish = fish_sprite(400, '#9FB4C6', 0.1)
        self.nut = walnut_sprite(150)
        self.oy = oyster_sprite(170)
        self.jar = jar_sprite(420)
        return table_plate(5)
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            img.paste(self.sea, (0, 0))
            bob = 18 * math.sin(t * 3)
            x = CX - 160 + 90 * t
            sp = self.ship.rotate(3 * math.sin(t * 2.4), resample=Image.BICUBIC, expand=True)
            paste_center(img, sp, x, 1020 + bob)
            ov = OV(img, 0, 1340, PW, 1480)
            for k in range(-1, 14):
                xx = k * 110 + (t * 140) % 110
                ov.d.arc(ov.box(xx, 1360, xx + 110, 1440), 200, 340, fill=(255, 255, 255, 200), width=10)
            ov.commit()
            pop(img, C('TO EUROPE', 82, bg=WHITE), CX, 520, t, self.we('Europe,') - 0.08)
            return
        u = t - tc
        pop(img, C('ENGLISH KETCHUP WAS MADE OF...', 50, bg=WHITE), CX, 520, u + tc, tc)
        items = [(self.fish, 'ANCHOVIES', self.we('anchovies,'), (CX - 250, 680)),
                 (self.nut, 'WALNUTS', self.we('walnuts,'), (CX + 250, 680)),
                 (self.oy, 'OYSTERS', self.we('oysters.'), (CX, 1070))]
        for k, (sp, lab, tw, (x, y)) in enumerate(items):
            if t > tw - 0.1:
                with_shadow(img, sp, x, y + 8 * math.sin(t * 5 + k), a=0.4) if t > tw + 0.2 else pop(img, sp, x, y, t, tw - 0.1)
                pop(img, C(lab, 66, bg=YEL if k != 1 else (120, 210, 255)), x, y + (140 if k < 2 else 175), t, tw - 0.05)
        with_shadow(img, self.jar, CX, 1860, a=0.4)

# ====================================================================== 4: 1812 recipe
class Recipe(Base):
    z0, z1 = 1.16, 1.25
    def make_shakes(self):
        return [(self.we('1812,'), 16, 0.3), (self.we('first'), 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1812,'), 'thud', 0.8), (self.we('Philadelphia') - 0.03, 'pop', 0.5),
                (self.we('published') - 0.03, 'scratch', 0.6), (self.we('first') - 0.03, 'ding', 0.6)]
    def plate(self):
        img = wall_plate('#DCEBF4', '#6C8CA8', 4, (CX, 1000, 1300))
        self.card = card_sprite(620, 760)
        self.tom = tomato_sprite(110)
        self.st = stamp_sprite('1812', 170, color=BLUE, angle=-8)
        return img
    def dyn(self, img, t):
        tP = self.we('published')
        ang = 4 * math.sin(t * 1.5)
        cs = self.card.rotate(ang, resample=Image.BICUBIC, expand=True)
        y = 1060 + (1 - ease_out(t / 0.4)) * 300
        with_shadow(img, cs, CX, y, a=0.45)
        if t > tP:
            ov = OV(img, CX - 300, y - 120, CX + 300, y + 340)
            q = clamp01((t - tP) / 0.9)
            for k in range(int(q * 8)):
                yy = y - 120 + k * 56 + 10
                ov.d.line(ov.pts([(CX - 250, yy), (CX + 200 - (k * 37 % 140), yy)]), fill=(60, 30, 20, 255), width=8)
            ov.commit()
        for k, (x, yy) in enumerate(((CX - 330, 720), (CX + 330, 760), (CX + 300, 1360))):
            pop(img, self.tom, x, yy + 8 * math.sin(t * 6 + k), t, self.we('tomato') - 0.1 + 0.08 * k)
        stamp_in(img, self.st, CX + 280, 640, t, self.we('1812,'))
        pop(img, C('PHILADELPHIA SCIENTIST', 60, bg=WHITE), CX, 1760, t, self.we('Philadelphia') - 0.06, out_t=self.we('first') - 0.15)
        pop(img, C('ONE OF THE FIRST TOMATO RECIPES', 50, bg=YEL), CX, 1760, t, self.we('first') - 0.06)

# ====================================================================== 5: Americans scared of tomatoes
class Scared(Base):
    z0, z1 = 1.18, 1.3
    def make_shakes(self):
        return [(self.we('scared'), 18, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Americans'), 'pop', 0.5), (self.we('scared'), 'bloop', 0.7)]
    def plate(self):
        img = wall_plate('#C9E3B0', '#4E7A3A', 12, (CX, 1000, 1300), counter=(1760, '#6A4A2A'))
        lay = Layer()
        for x in (CX - 380, CX + 380):
            mannequin(lay, x, 1900, 1000)
        img = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.tom = tomato_sprite(220)
        self.q = qmark(170, txt='!?')
        self.st = stamp_sprite('SCARY?!', 150, color=RED, angle=-8)
        return img
    def dyn(self, img, t):
        tS = self.we('scared')
        k = 1 + 0.06 * math.sin(t * 9)
        paste_center(img, self.tom, CX, 1100 + 14 * math.sin(t * 7), scale=k)
        for j, x in enumerate((CX - 380, CX + 380)):
            pop(img, self.q, x, 760 + 10 * math.sin(t * 10 + j), t, tS - 0.15 + j * 0.1)
            if t > tS:
                for d in range(2):
                    u = ((t - tS) * 1.5 + d * 0.5) % 1
                    glow(img, x + (50 if d else -50), 920 + 120 * u, 18, (150, 210, 255), 1 - u)
        pop(img, C('LOTS OF AMERICANS...', 66, bg=WHITE), CX, 520, t, self.we('Americans') - 0.08)
        stamp_in(img, self.st, CX, 1800, t, tS + 0.05)
    def cam(self, t):
        z, fx, fy, rot = super().cam(t)
        return z, fx, 1140 + (fy - 1100), rot

# ====================================================================== 6: Ohio doctor 1830s
class Doctor(Base):
    z0, z1 = 1.16, 1.24
    def make_shakes(self):
        return [(self.we('1830s,'), 14, 0.3), (self.we('diarrhea'), 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1830s,'), 'thud', 0.8), (self.we('Ohio') - 0.03, 'pop', 0.5),
                (self.we('claimed') - 0.03, 'riser', 0.4), (self.we('diarrhea') - 0.03, 'pop', 0.6),
                (self.we('and') - 0.03, 'pop', 0.6)]
    def plate(self):
        img = wall_plate('#F4EEE2', '#8A9AA6', 6, (CX, 1000, 1300), counter=(1700, '#5A4A3E'))
        lay = Layer()
        mannequin(lay, CX - 290, 1880, 1120)
        img = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.bag = bag_sprite(420)
        self.tom = tomato_sprite(180)
        self.st = stamp_sprite('1830s', 150, color=BLUE, angle=-8)
        self.ck = check_sprite(46)
        return img
    def dyn(self, img, t):
        tC, tD, tI = self.we('claimed'), self.we('diarrhea'), self.we('indigestion.')
        if t > tC - 0.1:
            u = ease_back((t - tC + 0.1) / 0.4, 1.8)
            glow(img, CX + 250, 950, 260, (255, 240, 160), 0.6 * clamp01(u))
            paste_center(img, self.tom, CX + 250, 950 + 10 * math.sin(t * 5), scale=max(0.05, u))
        stamp_in(img, self.st, CX + 200, 650, t, self.we('1830s,'))
        pop(img, C('OHIO DOCTOR', 72, bg=WHITE), CX - 170, 520, t, self.we('Ohio') - 0.08)
        for k, (lab, tw) in enumerate((('DIARRHEA', tD), ('INDIGESTION', tI))):
            y = 1770 + k * 150
            pop(img, C(lab + '?', 62, bg=YEL), CX + 40, y, t, tw - 0.06)
            pop(img, self.ck, CX + 330, y, t, tw + 0.1)
    def cam(self, t):
        z, fx, fy, rot = super().cam(t)
        return z, fx, fy + 60 * clamp01((t - self.we('diarrhea') + 0.3) / 0.5), rot

# ====================================================================== 7: tomato extract into pills
class Pills(Base):
    z0, z1 = 1.16, 1.26
    def make_shakes(self):
        return [(self.we('pills.'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('sellers') - 0.03, 'cash', 0.6), (self.we('extract') - 0.03, 'splat', 0.6)]
        for k in range(4):
            ev.append((self.we('into') - 0.05 + k * 0.08, 'tick', 0.5))
        return ev
    def plate(self):
        img = wall_plate('#FFD9C2', '#B04A3A', 14, (CX, 1000, 1300), counter=(1720, '#7A4A2A'))
        self.pb = pill_bottle_sprite(720)
        self.tom = tomato_sprite(170)
        return img
    def dyn(self, img, t):
        tE, tP = self.we('extract'), self.we('pills.')
        with_shadow(img, self.pb, CX, 1600, a=0.45)
        # tomatoes squash into pills that drop into the bottle
        for k in range(5):
            t0 = 0.2 + k * 0.7
            u = (t - t0) / 0.9
            if u < 0 or u > 1:
                continue
            x = CX + (-260 + 130 * k) * (1 - u)
            y = 780 + (1330 - 780) * u
            if u < 0.45:
                paste_center(img, self.tom, x, y, scale=1 - 1.4 * u)
            else:
                paste_center(img, pill_sprite(110, 90 + 200 * u + k * 30), x, y)
        pop(img, C('$ SELLERS $', 74, bg=(110, 220, 130)), CX, 520, t, self.we('sellers') - 0.08, out_t=tE - 0.15)
        pop(img, C('TOMATO EXTRACT', 72, bg=YEL), CX, 520, t, tE - 0.08)

# ====================================================================== 8: twist - no tomato, laxatives
class Twist(Base):
    z0, z1 = 1.18, 1.28
    def make_shakes(self):
        return [(self.we('no'), 18, 0.35), (self.we('laxatives.'), 14, 0.3)]
    def events(self):
        return [(0.02, 'riser', 0.5), (self.we('twist?'), 'crack', 0.7), (self.we('no'), 'buzzer', 0.8),
                (self.we('just') - 0.03, 'bloop', 0.7)]
    def plate(self):
        img = wall_plate('#4A2A6A', '#150A22', 21, (CX, 1000, 1300))
        self.h0 = half_pill(560, 0)
        self.h1 = half_pill(560, 1)
        self.tom = tomato_sprite(90)
        self.tp = tp_sprite(130)
        self.st = stamp_sprite('NO TOMATO!', 140, color=RED, angle=-7)
        return img
    def dyn(self, img, t):
        tT, tN, tJ = self.we('twist?'), self.we('no'), self.we('just')
        split = ease_out((t - tT - 0.1) / 0.5) if t > tT + 0.1 else 0
        x0 = CX - 115 - 190 * split
        x1 = CX + 115 + 190 * split
        y = 1000 + 8 * math.sin(t * 6)
        r0 = self.h0.rotate(-12 * split, resample=Image.BICUBIC, expand=True)
        r1 = self.h1.rotate(12 * split, resample=Image.BICUBIC, expand=True)
        with_shadow(img, r0, x0, y, a=0.5)
        with_shadow(img, r1, x1, y, a=0.5)
        if split > 0.3:
            ov = OV(img, CX - 120, y - 200, CX + 120, y + 200)
            for k in range(8):
                u = ((t * 1.3) + k / 8) % 1
                xx = CX - 60 + (k * 37 % 120)
                ov.d.ellipse(ov.box(xx - 6, y + 60 - 200 * u - 6, xx + 6, y + 60 - 200 * u + 6), fill=(240, 240, 230, int(200 * (1 - u))))
            ov.commit()
        pop(img, C('THE TWIST?', 80, bg=YEL), CX, 520, t, 0.02, out_t=tN - 0.2)
        if t > tN - 0.1:
            paste_center(img, self.tom, CX, 560)
            red_x(img, CX, 560, 90, clamp01((t - tN) / 0.25))
        stamp_in(img, self.st, CX, 1640, t, tN + 0.05)
        if t > tJ - 0.1:
            pop(img, self.tp, CX - 270, 1940, t, tJ - 0.1)
            pop(img, C('JUST LAXATIVES', 64, bg=WHITE), CX + 160, 1900, t, tJ - 0.02)

# ====================================================================== 9: by 1850, craze over, back to dinner table
class Dinner(Base):
    z0, z1 = 1.16, 1.24
    def tcut(self):
        return self.we('ketchup') - 0.1
    def make_shakes(self):
        return [(self.we('1850,'), 16, 0.3), (self.we('over,'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1850,'), 'thud', 0.8), (self.we('over,') - 0.03, 'buzzer', 0.6),
                (self.tcut(), 'swipe', 0.5), (self.we('dinner') - 0.03, 'chime', 0.6)]
    def plate(self):
        self.wall = wall_plate('#BFC7CF', '#4A525A', 18, (CX, 1000, 1300), counter=(1700, '#5A4632'))
        self.pb = pill_bottle_sprite(700)
        self.bot = bottle_sprite(760)
        self.food = plate_food_sprite(780)
        self.st = stamp_sprite('1850', 170, color=BLUE, angle=-8)
        self.st2 = stamp_sprite('CRAZE OVER', 120, color=RED, angle=-6)
        return table_plate(8)
    def dyn(self, img, t):
        tc, tO = self.tcut(), self.we('over,')
        if t < tc:
            img.paste(self.wall, (0, 0))
            fall = ease_out((t - tO) / 0.5) if t > tO else 0
            sp = self.pb.rotate(-80 * fall, resample=Image.BICUBIC, expand=True)
            with_shadow(img, sp, CX + 40 * fall, 1180 + 300 * fall, a=0.45)
            if t > tO:
                red_x(img, CX + 40 * fall, 1180 + 300 * fall, 300, clamp01((t - tO) / 0.3))
            stamp_in(img, self.st, CX + 280, 640, t, self.we('1850,'))
            pop(img, C('BY ABOUT...', 70, bg=WHITE), CX - 200, 520, t, 0.02)
            stamp_in(img, self.st2, CX, 1840, t, tO)
            return
        with_shadow(img, self.food, CX + 150, 1080, a=0.4)
        with_shadow(img, self.bot, CX - 280, 900 + 6 * math.sin(t * 4), a=0.45)
        pop(img, C('BACK ON THE TABLE', 72, bg=YEL), CX, 520, t, tc + 0.05)

# ====================================================================== 10: fries -> loops to the hook
class Outro(Hook):
    def make_shakes(self):
        return [(self.we('fries...'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('landed') - 0.03, 'splat', 0.6), (self.we('your') - 0.03, 'pop', 0.5),
                (self.tswitch(), 'riser', 0.5)]
    def tswitch(self):
        return self.we('fries...') + 0.45
    def plate(self):
        img = Hook.plate(self)
        self.hook_plate = img.copy()
        self.fries = fries_sprite(560)
        self.kb = rot_sprite(bottle_sprite(720), 160)
        return table_plate(3)
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hook_plate, (0, 0))
            self.hero(img, t - self.dur)   # ends exactly where frame 0 begins
            return
        with_shadow(img, self.fries, CX, 1180, a=0.45)
        by = 430 + 20 * math.sin(t * 4)
        paste_center(img, self.kb, CX + 40, by)
        tL = self.we('landed')
        if t > tL - 0.3:
            q = clamp01((t - tL + 0.3) / 0.35)
            ov = OV(img, CX - 120, by + 300, CX + 160, 1000)
            y1 = by + 330 + (930 - by - 330) * q
            ov.d.line(ov.pts([(CX + 30, by + 330), (CX + 20 + 10 * math.sin(t * 20), y1)]), fill=(196, 24, 18, 255), width=36)
            ov.d.ellipse(ov.box(CX - 60, y1 - 34, CX + 100, y1 + 30), fill=(196, 24, 18, 255))
            ov.commit()
        pop(img, C('BEFORE YOUR FRIES...', 70, bg=WHITE), CX, 1860, t, 0.05)
    def cam(self, t):
        tw = self.tswitch()
        if t >= tw:
            dx, dy, dr = self.shake(t)
            return self.z0, CX, 1140, 0.0
        dx, dy, dr = self.shake(t)
        p = 1 - ease_out(t / 0.32)
        return 1.16 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1100 + dy, 2.0 * p + dr

SCENES = [Hook, NoTomato, FishSauce, Sailors, Recipe, Scared, Doctor, Pills, Twist, Dinner, Outro]
