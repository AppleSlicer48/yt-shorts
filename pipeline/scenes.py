"""Emoji Started Because of One Tiny Heart - scenes (cartoon people kit, detailed 2.5D settings)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import CX, plate_img
from cartoon import person, PRESETS, paste_person, talk_frame

SS = 2

def _ss(w, h):
    im = Image.new('RGBA', (int(w * SS), int(h * SS)), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

def _down(im):
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)

def dk(c, f=0.75):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def lt(c, f=0.35):
    return tuple(int(v + (255 - v) * f) for v in c[:3])

def catmull(pts, n=14):
    out = []
    P_ = pts + pts[:3]
    for i in range(len(pts)):
        p0, p1, p2, p3 = P_[i], P_[i + 1], P_[i + 2], P_[i + 3]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out

# ---------------------------------------------------------------- the clog (generic foam clog, no logo)
HOLES = [(0.60, 0.30), (0.70, 0.26), (0.80, 0.30), (0.56, 0.42), (0.66, 0.38), (0.76, 0.40), (0.86, 0.43),
         (0.63, 0.51), (0.73, 0.50), (0.83, 0.54)]

def charm_draw(d, cx, cy, r, kind, col):
    if kind == 'flower':
        for k in range(5):
            a = k * 2 * math.pi / 5
            px, py = cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55
            d.ellipse([px - r * 0.5, py - r * 0.5, px + r * 0.5, py + r * 0.5], fill=col, outline=dk(col, 0.6), width=max(2, int(r * 0.08)))
        d.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=(255, 215, 60))
    elif kind == 'star':
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r * (1.05 if k % 2 == 0 else 0.45)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pts, fill=col, outline=dk(col, 0.6))
    elif kind == 'heart':
        d.ellipse([cx - r * 0.95, cy - r * 0.75, cx + r * 0.05, cy + r * 0.25], fill=col)
        d.ellipse([cx - r * 0.05, cy - r * 0.75, cx + r * 0.95, cy + r * 0.25], fill=col)
        d.polygon([(cx - r * 0.9, cy - r * 0.15), (cx + r * 0.9, cy - r * 0.15), (cx, cy + r * 0.95)], fill=col)
    elif kind == 'smile':
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=dk(col, 0.6), width=max(2, int(r * 0.1)))
        d.ellipse([cx - r * 0.45, cy - r * 0.4, cx - r * 0.15, cy - r * 0.05], fill=(40, 30, 30))
        d.ellipse([cx + r * 0.15, cy - r * 0.4, cx + r * 0.45, cy - r * 0.05], fill=(40, 30, 30))
        d.arc([cx - r * 0.55, cy - r * 0.4, cx + r * 0.55, cy + r * 0.6], 20, 160, fill=(40, 30, 30), width=max(2, int(r * 0.14)))
    elif kind == 'gem':
        d.polygon([(cx, cy - r), (cx + r * 0.8, cy - r * 0.2), (cx, cy + r), (cx - r * 0.8, cy - r * 0.2)], fill=col, outline=(255, 255, 255))
        d.polygon([(cx, cy - r), (cx + r * 0.3, cy - r * 0.2), (cx, cy + r * 0.2), (cx - r * 0.3, cy - r * 0.2)], fill=lt(col, 0.5))

CHARMS = [('flower', (240, 90, 160)), ('star', (255, 200, 40)), ('heart', (230, 50, 70)), ('smile', (255, 220, 60)),
          ('gem', (90, 200, 240)), ('flower', (170, 110, 230)), ('star', (120, 220, 120)), ('heart', (255, 130, 60)),
          ('gem', (240, 90, 160)), ('smile', (120, 210, 255))]

_CLOG = {}
def clog(w=600, color=(120, 200, 70), charms=0, flip=False):
    """Side view foam clog, toe pointing right. charms = number of holes filled (0..10)."""
    key = (w, tuple(color), charms, flip)
    if key in _CLOG:
        return _CLOG[key]
    h = int(w * 0.62)
    im, d = _ss(w, h)
    X = lambda u: u * w * SS
    Y = lambda v: v * h * SS
    sole = dk(color, 0.72)
    sole_pts = catmull([(X(0.02), Y(0.66)), (X(0.12), Y(0.60)), (X(0.5), Y(0.66)), (X(0.88), Y(0.68)), (X(0.99), Y(0.78)),
                        (X(0.95), Y(0.94)), (X(0.6), Y(0.92)), (X(0.2), Y(0.96)), (X(0.03), Y(0.9))])
    d.polygon(sole_pts, fill=sole)
    for k in range(9):
        x = X(0.08 + k * 0.1)
        d.line([(x, Y(0.88)), (x + X(0.03), Y(0.95))], fill=dk(sole, 0.7), width=max(2, int(SS * w * 0.012)))
    up = catmull([(X(0.06), Y(0.70)), (X(0.07), Y(0.42)), (X(0.22), Y(0.36)), (X(0.42), Y(0.30)), (X(0.56), Y(0.14)),
                  (X(0.75), Y(0.10)), (X(0.92), Y(0.22)), (X(0.99), Y(0.48)), (X(0.97), Y(0.74)), (X(0.6), Y(0.78)), (X(0.25), Y(0.78))])
    d.polygon(up, fill=color)
    d.polygon(catmull([(X(0.08), Y(0.66)), (X(0.5), Y(0.70)), (X(0.96), Y(0.66)), (X(0.97), Y(0.76)), (X(0.5), Y(0.80)), (X(0.07), Y(0.75))]), fill=dk(color, 0.88))
    d.arc([X(0.52), Y(0.14), X(0.98), Y(0.66)], 200, 290, fill=lt(color, 0.55), width=max(2, int(SS * w * 0.02)))
    d.polygon(catmull([(X(0.10), Y(0.40)), (X(0.25), Y(0.33)), (X(0.45), Y(0.30)), (X(0.52), Y(0.27)), (X(0.48), Y(0.36)), (X(0.30), Y(0.42)), (X(0.12), Y(0.46))]), fill=dk(color, 0.45))
    hr = w * 0.033 * SS
    for k, (u, v) in enumerate(HOLES):
        cx, cy = X(u), Y(v)
        d.ellipse([cx - hr, cy - hr * 0.85, cx + hr, cy + hr * 0.85], fill=dk(color, 0.42))
        d.arc([cx - hr, cy - hr * 0.85, cx + hr, cy + hr * 0.85], 200, 340, fill=dk(color, 0.3), width=SS * 2)
    sw = max(3, int(w * 0.06 * SS))
    d.arc([X(-0.04), Y(0.30), X(0.46), Y(0.80)], 100, 250, fill=dk(color, 0.9), width=sw)
    d.line([(X(0.17), Y(0.32)), (X(0.40), Y(0.46))], fill=dk(color, 0.9), width=sw)
    d.ellipse([X(0.38), Y(0.42), X(0.46), Y(0.55)], fill=lt(color, 0.25), outline=dk(color, 0.5), width=SS * 3)
    for k in range(min(charms, len(HOLES))):
        u, v = HOLES[k]
        kind, col = CHARMS[k]
        charm_draw(d, X(u), Y(v), hr * 1.9, kind, col)
    out = _down(im)
    if flip:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    _CLOG[key] = out
    return out

def hole_pos(w, k, flip=False):
    h = int(w * 0.62)
    u, v = HOLES[k]
    return ((1 - u) if flip else u) * w, v * h

def charm_sprite(k, r=40):
    im, d = _ss(r * 2.6, r * 2.6)
    kind, col = CHARMS[k % len(CHARMS)]
    charm_draw(d, r * 1.3 * SS, r * 1.3 * SS, r * SS, kind, col)
    return _down(im)

def put(img, sp, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale != 1.0:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if rot:
        sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        sp = sp.copy()
        sp.putalpha(sp.getchannel('A').point(lambda v: int(v * alpha)))
    paste_at(img, sp, int(cx - sp.width / 2), int(cy - sp.height / 2))

def floor_shadow(img, cx, y, w, a=0.35):
    sh = Image.new('RGBA', (int(w * 1.6), 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([20, 35, sh.width - 20, 85], fill=(0, 0, 0, int(255 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    paste_at(img, sh, int(cx - sh.width / 2), int(y - 60))

# ---------------------------------------------------------------- settings (plates)
_PL = {}
def cached(fn):
    def wrap(*a):
        k = (fn.__name__,) + a
        if k not in _PL:
            _PL[k] = fn(*a)
        return _PL[k].copy()
    return wrap

def finish_plate(im, vig=0.4, noise_seed=1):
    arr = to_arr(im)
    arr = arr * (0.94 + 0.08 * smooth_noise(PH, PW, 70, noise_seed, 3))[..., None]
    return plate_img(vignette(arr, vig))

def wood_floor(d, y0, base=(170, 120, 75)):
    d.rectangle([0, y0, PW, PH], fill=base)
    for k in range(-12, 13):
        xb = CX + k * 190
        d.line([(CX + (xb - CX) * 0.35, y0), (CX + (xb - CX) * 2.2, PH)], fill=dk(base, 0.78), width=5)
    y = y0
    gap = 40
    while y < PH:
        d.line([(0, y), (PW, y)], fill=dk(base, 0.86), width=3)
        gap *= 1.35
        y += gap

def window(d, x0, y0, x1, y1, scene='mountains', frame=(245, 245, 240)):
    d.rectangle([x0 - 22, y0 - 22, x1 + 22, y1 + 22], fill=frame)
    d.rectangle([x0, y0, x1, y1], fill=(150, 205, 240))
    hgt = y1 - y0
    wd = x1 - x0
    if scene == 'mountains':
        d.polygon([(x0, y0 + hgt * 0.75), (x0 + wd * 0.25, y0 + hgt * 0.32), (x0 + wd * 0.5, y0 + hgt * 0.62),
                   (x0 + wd * 0.72, y0 + hgt * 0.25), (x1, y0 + hgt * 0.6), (x1, y1), (x0, y1)], fill=(110, 130, 160))
        d.polygon([(x0 + wd * 0.25, y0 + hgt * 0.32), (x0 + wd * 0.2, y0 + hgt * 0.4), (x0 + wd * 0.31, y0 + hgt * 0.4)], fill=(250, 250, 255))
        d.polygon([(x0 + wd * 0.72, y0 + hgt * 0.25), (x0 + wd * 0.66, y0 + hgt * 0.34), (x0 + wd * 0.79, y0 + hgt * 0.34)], fill=(250, 250, 255))
        for k in range(7):
            tx = x0 + wd * (k + 0.5) / 7
            d.polygon([(tx, y1 - hgt * 0.28), (tx - 30, y1), (tx + 30, y1)], fill=(50, 100, 70))
    elif scene == 'city':
        for k in range(8):
            bx = x0 + wd * k / 8
            bh = hgt * (0.35 + 0.5 * ((k * 37) % 10) / 10)
            d.rectangle([bx + 6, y1 - bh, bx + wd / 8 - 6, y1], fill=(120, 140, 170))
            for wy in range(int(y1 - bh + 20), int(y1) - 20, 40):
                d.rectangle([bx + 20, wy, bx + 34, wy + 18], fill=(230, 235, 200))
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=frame, width=16)
    d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=frame, width=16)

@cached
def harbor_plate():
    arr = vgrad(PW, PH, [(0, '#5FB6EA'), (0.34, '#BFE6F7'), (0.36, '#2E8FC2'), (1, '#135C8A')])
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    hz = int(PH * 0.35)
    for (cx, cy, s) in ((220, 200, 1.0), (900, 330, 0.8), (1150, 120, 0.7)):
        for dx, dy, r in ((0, 0, 70), (60, -25, 60), (120, 5, 65), (-55, 15, 50)):
            d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=(255, 255, 255))
    d.polygon([(0, hz), (0, hz - 40), (300, hz - 70), (620, hz - 30), (900, hz - 60), (PW, hz - 25), (PW, hz)], fill=(80, 150, 110))
    for (bx, by, s) in ((260, hz + 60, 1.0), (1000, hz + 30, 0.7), (620, hz + 15, 0.5)):
        d.polygon([(bx - 110 * s, by), (bx + 120 * s, by), (bx + 90 * s, by + 40 * s), (bx - 85 * s, by + 40 * s)], fill=(250, 250, 250))
        d.line([(bx, by), (bx, by - 300 * s)], fill=(90, 80, 70), width=max(3, int(8 * s)))
        d.polygon([(bx + 6 * s, by - 290 * s), (bx + 6 * s, by - 20 * s), (bx + 150 * s, by - 20 * s)], fill=(255, 250, 240))
        d.polygon([(bx - 6 * s, by - 250 * s), (bx - 6 * s, by - 20 * s), (bx - 100 * s, by - 20 * s)], fill=(240, 120, 90))
    rng = np.random.default_rng(3)
    for k in range(90):
        y = hz + 20 + (k / 90) ** 1.6 * (PH - hz)
        x = rng.uniform(0, PW)
        L = 30 + (y - hz) * 0.12
        d.arc([x - L, y - 10, x + L, y + 10], 200, 340, fill=(170, 220, 245), width=max(2, int(2 + (y - hz) / 300)))
    dock_top = 1700
    d.polygon([(PW * 0.55, dock_top), (PW, dock_top - 60), (PW, PH), (PW * 0.42, PH)], fill=(150, 105, 65))
    for k in range(8):
        y = dock_top + k * 90
        d.line([(PW * 0.55 - (y - dock_top) * 0.06, y), (PW, y - 60 + k * 8)], fill=(110, 75, 45), width=6)
    for px in (PW * 0.56, PW * 0.93):
        d.rectangle([px - 34, dock_top - 260, px + 34, dock_top + 40], fill=(120, 85, 50))
        d.ellipse([px - 34, dock_top - 285, px + 34, dock_top - 240], fill=(160, 115, 70))
        d.line([(px - 34, dock_top - 200), (px + 34, dock_top - 180)], fill=(220, 200, 150), width=10)
    d.ellipse([PW * 0.93 - 80, dock_top - 230, PW * 0.93 + 80, dock_top - 70], outline=(240, 90, 60), width=36)
    return finish_plate(im, 0.35, 2)

@cached
def hallway_plate():
    im = Image.new('RGBA', (PW, PH), (235, 230, 215))
    d = ImageDraw.Draw(im)
    fy = 1620
    d.rectangle([0, 0, PW, fy], fill=(232, 226, 208))
    d.rectangle([0, 0, PW, 160], fill=(250, 250, 245))
    for x in range(0, PW, 260):
        d.rectangle([x + 40, 40, x + 220, 110], fill=(255, 255, 235))
    ly0, ly1 = 520, fy - 30
    for k in range(10):
        x = k * 130
        d.rectangle([x + 4, ly0, x + 126, ly1], fill=(70, 140, 205), outline=(40, 90, 140), width=4)
        for vy in range(ly0 + 40, ly0 + 120, 18):
            d.line([(x + 30, vy), (x + 100, vy)], fill=(40, 90, 140), width=5)
        d.rectangle([x + 98, ly0 + 380, x + 112, ly0 + 440], fill=(200, 205, 210))
        d.rectangle([x + 20, ly0 + 160, x + 70, ly0 + 200], fill=(245, 245, 240))
    d.rectangle([0, ly0 - 20, PW, ly0], fill=(40, 90, 140))
    d.rectangle([380, 220, 900, 470], fill=(190, 140, 90), outline=(120, 80, 50), width=12)
    for (x, y, c) in ((420, 250, (255, 240, 120)), (560, 270, (160, 220, 255)), (700, 245, (255, 170, 190)), (480, 360, (200, 255, 190)), (650, 370, (255, 255, 255)), (790, 330, (255, 210, 140))):
        d.rectangle([x, y, x + 90, y + 75], fill=c)
        d.ellipse([x + 38, y - 6, x + 52, y + 8], fill=(220, 40, 40))
    y, gap, k = fy, 50, 0
    while y < PH:
        d.rectangle([0, y, PW, y + gap], fill=(215, 210, 200) if k % 2 == 0 else (185, 180, 172))
        y += gap
        gap *= 1.25
        k += 1
    for j in range(-8, 9):
        d.line([(CX + j * 60, fy), (CX + j * 260, PH)], fill=(160, 155, 150), width=3)
    d.rectangle([0, fy - 30, PW, fy], fill=(90, 80, 70))
    return finish_plate(im, 0.35, 3)

@cached
def cabin_plate():
    im = Image.new('RGBA', (PW, PH), (180, 130, 85))
    d = ImageDraw.Draw(im)
    fy = 1680
    for k in range(0, fy, 70):
        d.rectangle([0, k, PW, k + 66], fill=(178 + (k // 70 % 3) * 6, 126, 82))
        d.line([(0, k + 66), (PW, k + 66)], fill=(130, 90, 55), width=4)
    window(d, 300, 300, 1000, 900, 'mountains', (245, 240, 225))
    d.rectangle([60, 1040, 520, 1066], fill=(110, 75, 45))
    for k, c in enumerate([(200, 60, 60), (60, 120, 190), (230, 190, 60), (90, 160, 90)]):
        d.rectangle([80 + k * 60, 930, 130 + k * 60, 1040], fill=c)
    d.line([(1120, 420), (1220, 1150)], fill=(140, 95, 55), width=26)
    d.ellipse([1170, 1060, 1270, 1260], fill=(140, 95, 55))
    wood_floor(d, fy, (150, 102, 64))
    d.ellipse([140, 1850, 1160, 2200], fill=(190, 70, 60))
    d.ellipse([220, 1890, 1080, 2160], outline=(240, 200, 120), width=12)
    d.rectangle([0, fy - 24, PW, fy], fill=(100, 65, 40))
    return finish_plate(im, 0.4, 4)

@cached
def deck_plate():
    arr = vgrad(PW, PH, [(0, '#7CCBF0'), (0.18, '#CBEFFB'), (0.2, '#3CA2D2'), (1, '#0F4F7A')])
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    hz = int(PH * 0.2)
    d.polygon([(0, hz), (0, hz - 30), (500, hz - 55), (900, hz - 20), (PW, hz - 40), (PW, hz)], fill=(90, 160, 110))
    d.polygon([(0, 500), (330, 560), (260, 1300), (0, 1350)], fill=(245, 245, 240))
    d.polygon([(0, 560), (318, 610), (312, 680), (0, 640)], fill=(40, 90, 160))
    for k in range(4):
        d.ellipse([40 + k * 60, 760, 80 + k * 60, 800], fill=(150, 200, 230), outline=(120, 120, 120), width=5)
    rng = np.random.default_rng(5)
    for k in range(140):
        y = hz + 20 + (k / 140) ** 1.4 * (PH - hz)
        x = rng.uniform(0, PW)
        L = 30 + (y - hz) * 0.1
        d.arc([x - L, y - 12, x + L, y + 12], 200, 340, fill=(150, 210, 240), width=max(2, int(2 + (y - hz) / 260)))
    d.polygon([(0, 1900), (PW, 1820), (PW, PH), (0, PH)], fill=(160, 112, 70))
    for k in range(7):
        x = k * 220
        d.line([(x, 1900 - x * 0.06), (x - 60, PH)], fill=(110, 75, 45), width=8)
    d.line([(0, 1900), (PW, 1820)], fill=(200, 150, 100), width=12)
    return finish_plate(im, 0.35, 5)

@cached
def boatshow_plate():
    arr = vgrad(PW, PH, [(0, '#58B4EC'), (0.4, '#C6EBFA'), (1, '#C6EBFA')])
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 900, PW, 1150], fill=(50, 140, 190))
    for k in range(9):
        x = 40 + k * 150
        d.line([(x, 1000), (x + 10, 260 + (k % 3) * 80)], fill=(235, 235, 235), width=8)
        d.polygon([(x - 70, 1000), (x + 90, 1000), (x + 60, 1040), (x - 50, 1040)], fill=(250, 250, 250))
    for (px, ph) in ((120, 520), (1180, 480)):
        d.line([(px, 1150), (px + 30, ph)], fill=(140, 100, 60), width=34)
        for a in range(0, 360, 45):
            r = math.radians(a)
            d.polygon([(px + 30, ph), (px + 30 + math.cos(r) * 230, ph + math.sin(r) * 90 + 40), (px + 30 + math.cos(r) * 150, ph + math.sin(r) * 60 + 70)], fill=(50, 140, 70))
    d.polygon([(150, 760), (CX, 560), (PW - 150, 760)], fill=(250, 250, 250))
    for k in range(6):
        x0 = 150 + k * (PW - 300) / 6
        d.polygon([(x0, 760), (x0 + (PW - 300) / 12, 830), (x0 + (PW - 300) / 6, 760)], fill=(230, 80, 70) if k % 2 == 0 else (250, 250, 250))
    d.rectangle([150, 760, 170, 1500], fill=(220, 220, 225))
    d.rectangle([PW - 170, 760, PW - 150, 1500], fill=(220, 220, 225))
    d.rectangle([0, 1150, PW, PH], fill=(175, 130, 85))
    y, g = 1150, 30
    while y < PH:
        d.line([(0, y), (PW, y)], fill=(130, 92, 58), width=4)
        y += g
        g *= 1.25
    return finish_plate(im, 0.3, 6)

@cached
def kitchen_plate():
    im = Image.new('RGBA', (PW, PH), (250, 240, 220))
    d = ImageDraw.Draw(im)
    for y in range(0, 1500, 90):
        for x in range(-(y // 90 % 2) * 45, PW, 90):
            d.rectangle([x + 3, y + 3, x + 87, y + 87], fill=(250, 246, 236), outline=(210, 200, 185), width=3)
    window(d, 380, 260, 900, 720, 'mountains', (255, 255, 255))
    d.polygon([(330, 230), (480, 230), (420, 780), (330, 780)], fill=(240, 120, 140))
    d.polygon([(950, 230), (800, 230), (860, 780), (950, 780)], fill=(240, 120, 140))
    d.rectangle([0, 120, 300, 620], fill=(110, 170, 160), outline=(70, 120, 110), width=8)
    d.rectangle([1000, 120, PW, 620], fill=(110, 170, 160), outline=(70, 120, 110), width=8)
    d.ellipse([260, 360, 284, 384], fill=(230, 200, 120))
    d.ellipse([1020, 360, 1044, 384], fill=(230, 200, 120))
    d.rectangle([0, 900, 300, 920], fill=(140, 95, 60))
    for k, c in enumerate([(240, 180, 70), (200, 80, 70), (120, 170, 90)]):
        d.rounded_rectangle([20 + k * 95, 780, 100 + k * 95, 900], 18, fill=c)
        d.rectangle([28 + k * 95, 765, 92 + k * 95, 790], fill=(200, 200, 205))
    d.rectangle([1000, 900, PW, 920], fill=(140, 95, 60))
    for k in range(3):
        d.ellipse([1020 + k * 90, 820, 1100 + k * 90, 900], fill=(250, 250, 250), outline=(180, 180, 190), width=5)
    wood_floor(d, 1500, (195, 150, 105))
    return finish_plate(im, 0.35, 7)

def table_front(img, y, color=(160, 110, 70), top=(205, 160, 110)):
    d = ImageDraw.Draw(img)
    d.polygon([(-20, y), (PW + 20, y), (PW + 20, y + 70), (-20, y + 70)], fill=top)
    d.rectangle([-20, y + 70, PW + 20, PH], fill=color)
    for x in range(0, PW, 160):
        d.line([(x, y + 70), (x, PH)], fill=dk(color, 0.85), width=4)
    d.line([(-20, y), (PW + 20, y)], fill=lt(top, 0.3), width=6)

@cached
def basement_plate():
    im = Image.new('RGBA', (PW, PH), (150, 150, 145))
    d = ImageDraw.Draw(im)
    for y in range(0, 1600, 110):
        for x in range(-(y // 110 % 2) * 110, PW, 220):
            d.rectangle([x + 4, y + 4, x + 216, y + 106], fill=(165 + (x * 7 + y) % 13, 162, 155), outline=(120, 118, 112), width=4)
    d.rectangle([520, 120, 820, 290], fill=(250, 250, 245))
    d.rectangle([540, 140, 800, 270], fill=(160, 210, 120))
    for k in range(9):
        d.rectangle([0, 520 + k * 120, 320 - k * 30, 560 + k * 120], fill=(150, 105, 65), outline=(100, 70, 40), width=4)
    d.line([(330, 420), (40, 1600)], fill=(110, 75, 45), width=18)
    for sy in (520, 860, 1200):
        d.rectangle([860, sy, PW, sy + 18], fill=(110, 115, 125))
        for k in range(3):
            d.rectangle([880 + k * 135, sy - 150, 990 + k * 135, sy], fill=(200, 160, 110), outline=(150, 115, 75), width=4)
            d.line([(880 + k * 135, sy - 120), (990 + k * 135, sy - 120)], fill=(150, 115, 75), width=6)
    d.line([(862, 300), (862, 1600)], fill=(110, 115, 125), width=14)
    d.line([(CX, 0), (CX, 260)], fill=(40, 40, 40), width=6)
    d.ellipse([CX - 36, 250, CX + 36, 330], fill=(255, 240, 170))
    d.rectangle([0, 1600, PW, PH], fill=(120, 120, 118))
    d.rectangle([0, 1600, PW, 1630], fill=(90, 90, 88))
    return finish_plate(im, 0.45, 8)

@cached
def office_plate():
    im = Image.new('RGBA', (PW, PH), (225, 230, 238))
    d = ImageDraw.Draw(im)
    window(d, 120, 200, 1176, 1000, 'city', (200, 205, 215))
    d.rectangle([60, 1350, 200, 1600], fill=(200, 120, 70))
    for a in range(-60, 61, 20):
        r = math.radians(a - 90)
        d.ellipse([130 + math.cos(r) * 150 - 40, 1300 + math.sin(r) * 200 - 80, 130 + math.cos(r) * 150 + 40, 1300 + math.sin(r) * 200 + 80], fill=(60, 150, 80))
    d.rectangle([1000, 1080, 1250, 1360], fill=(255, 255, 255), outline=(80, 80, 90), width=6)
    for k, hh in enumerate((60, 110, 170, 240)):
        d.rectangle([1030 + k * 55, 1330 - hh, 1070 + k * 55, 1330], fill=(60, 170, 90))
    d.line([(1040, 1360), (1000, 1620)], fill=(80, 80, 90), width=8)
    d.line([(1210, 1360), (1250, 1620)], fill=(80, 80, 90), width=8)
    d.rectangle([0, 1600, PW, PH], fill=(90, 95, 120))
    for k in range(-6, 7):
        d.line([(CX + k * 80, 1600), (CX + k * 300, PH)], fill=(80, 85, 110), width=4)
    return finish_plate(im, 0.35, 9)

@cached
def living_plate():
    im = Image.new('RGBA', (PW, PH), (200, 220, 205))
    d = ImageDraw.Draw(im)
    for x in range(0, PW, 80):
        d.rectangle([x, 0, x + 40, 1500], fill=(190, 212, 196))
    d.rectangle([140, 300, 460, 560], fill=(250, 245, 230), outline=(140, 95, 55), width=18)
    d.polygon([(170, 530), (280, 380), (360, 470), (430, 400), (430, 530)], fill=(90, 150, 200))
    d.rectangle([840, 260, 1120, 620], fill=(250, 245, 230), outline=(140, 95, 55), width=18)
    d.ellipse([920, 340, 1040, 460], fill=(240, 180, 60))
    d.polygon([(1080, 860), (1240, 860), (1200, 740), (1120, 740)], fill=(250, 230, 170))
    d.line([(1160, 860), (1160, 1500)], fill=(80, 70, 60), width=10)
    d.rounded_rectangle([60, 1080, 1000, 1360], 60, fill=(230, 120, 90))
    d.rounded_rectangle([20, 1240, 1040, 1560], 50, fill=(215, 105, 78))
    d.rounded_rectangle([0, 1150, 120, 1560], 40, fill=(200, 95, 70))
    d.rounded_rectangle([940, 1150, 1060, 1560], 40, fill=(200, 95, 70))
    wood_floor(d, 1560, (175, 128, 88))
    d.polygon([(100, 1800), (1200, 1800), (1296, 2250), (0, 2250)], fill=(90, 120, 180))
    d.polygon([(150, 1840), (1150, 1840), (1230, 2200), (60, 2200)], outline=(240, 220, 160), width=10)
    return finish_plate(im, 0.35, 10)

@cached
def bedroom_plate():
    im = Image.new('RGBA', (PW, PH), (250, 215, 225))
    d = ImageDraw.Draw(im)
    for y in range(40, 1500, 160):
        for x in range((y // 160 % 2) * 80, PW, 160):
            d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(255, 235, 240))
    d.line([(0, 140), (PW, 140)], fill=(120, 100, 100), width=2)
    for k in range(14):
        x = 40 + k * 90
        y = 140 + 30 * math.sin(k * 0.9)
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=[(255, 230, 120), (255, 160, 200), (160, 220, 255)][k % 3])
    d.ellipse([820, 300, 1220, 820], fill=(220, 230, 240), outline=(255, 255, 255), width=24)
    d.line([(900, 420), (980, 340)], fill=(255, 255, 255), width=14)
    d.rounded_rectangle([-40, 1000, 520, 1620], 40, fill=(160, 120, 210))
    d.rounded_rectangle([-40, 900, 300, 1120], 50, fill=(255, 255, 255))
    d.rectangle([-40, 1300, 520, 1620], fill=(140, 100, 190))
    d.rectangle([380, 300, 640, 640], fill=(120, 210, 200))
    d.ellipse([440, 380, 580, 520], fill=(255, 240, 120))
    d.rectangle([620, 900, 1250, 924], fill=(255, 255, 255))
    for k, c in enumerate([(255, 180, 200), (180, 220, 255), (200, 240, 180), (255, 220, 140)]):
        d.ellipse([650 + k * 150, 790, 770 + k * 150, 905], fill=c)
        d.ellipse([680 + k * 150, 830, 694 + k * 150, 844], fill=(50, 40, 40))
        d.ellipse([726 + k * 150, 830, 740 + k * 150, 844], fill=(50, 40, 40))
    d.rectangle([0, 1620, PW, PH], fill=(235, 225, 230))
    for x in range(0, PW, 120):
        d.line([(x, 1620), (x + (x - CX) * 0.8, PH)], fill=(215, 200, 210), width=4)
    d.ellipse([200, 1900, 1100, 2240], fill=(255, 190, 210))
    return finish_plate(im, 0.35, 11)

# ---------------------------------------------------------------- characters (same person = same look)
TEEN = dict(PRESETS['girl'])
FRIEND_A = dict(PRESETS['boy'], top=(240, 150, 50), hat_color=(40, 110, 190))
FRIEND_B = dict(PRESETS['worker'], hat=None, top=(60, 170, 160), hair='messy')
FRIEND_C = dict(PRESETS['boss'], top=(200, 70, 80), tie=None)
SHERI = dict(PRESETS['woman'], skin='light', hair='long', hair_color=(150, 95, 50), top=(240, 110, 160), dress=False, bottom=(60, 70, 120))
KID1 = dict(PRESETS['kid'])
KID2 = dict(PRESETS['girl'], child=True, top=(120, 200, 240), hair_color=(150, 95, 50), skin='light')
GRANDPA = dict(PRESETS['grandma'], hair='short', dress=False, top=(120, 140, 90), mustache=True)
EXEC = dict(PRESETS['boss'], skin='medium', hair_color=(40, 30, 25), top=(40, 50, 80), tie=(60, 170, 90))
SHOPPER1 = dict(PRESETS['salesman'])
SHOPPER2 = dict(PRESETS['grandma'])

def P(img, look, x, floor, t, expr='happy', talk=False, arm_l=15, arm_r=15, scale=0.9, bob=1.0, phase=0.0, look_dir=0.0):
    b = math.sin(t * 5 + phase) * 6 * bob
    spr, anc = person(**look, expr=expr, talk=talk, arm_l=arm_l, arm_r=arm_r, scale=scale, look=look_dir)
    ox, oy = paste_person(img, spr, anc, x, floor + b)
    return {k: (v[0] + ox, v[1] + oy) for k, v in anc.items() if k != 'height'}

# ---------------------------------------------------------------- scene base
class Sc:
    focus = (CX, 1152)
    z0, z1 = 1.0, 1.08
    punch = 0.08

    def __init__(self, words, dur, idx):
        self.words, self.dur, self.idx = words, dur, idx
        self.rd = 1 if idx % 2 == 0 else -1

    def we(self, key, which='t0'):
        for w in self.words:
            if key.lower() in w['w'].lower():
                return w[which]
        raise KeyError(key)

    def shots(self):
        return [(0.0, self.z0, self.z1, self.focus[0], self.focus[1])]

    def cam(self, t):
        sh = self.shots()
        k = 0
        for i, s in enumerate(sh):
            if t >= s[0]:
                k = i
        t0 = sh[k][0]
        t1 = sh[k + 1][0] if k + 1 < len(sh) else self.dur
        u = clamp01((t - t0) / max(0.01, t1 - t0))
        z = sh[k][1] + (sh[k][2] - sh[k][1]) * ease_in_out(u)
        p = 1 - ease_out((t - t0) / 0.3)
        z *= 1 + self.punch * p
        return z, sh[k][3], sh[k][4], 1.5 * p * self.rd

    def events(self):
        return []

    def dyn(self, img, t):
        pass

def chip_at(img, txt, cx, cy, t, t0, dot=(240, 90, 160)):
    if t < t0:
        return
    sp = chip(txt, 58, dot=dot)
    u = clamp01((t - t0) / 0.25)
    paste_center(img, sp, cx, cy, scale=0.6 + 0.4 * ease_back(u, 2.2), alpha=clamp01(u * 3))

def splash(img, cx, cy, t, t0, n=16, spread=260, col=(230, 245, 255)):
    if t < t0 or t > t0 + 1.2:
        return
    u = (t - t0)
    d = ImageDraw.Draw(img)
    for k in range(n):
        a = math.radians(200 + 140 * k / max(1, n - 1))
        v = spread * (0.6 + 0.5 * ((k * 7) % 5) / 5)
        x = cx + math.cos(a) * v * u * 1.6
        y = cy + math.sin(a) * v * u * 2.2 + 900 * u * u
        r = max(2, 18 * (1 - u))
        d.ellipse([x - r, y - r * 1.3, x + r, y + r * 1.3], fill=col)

def ripples(img, cx, cy, t, w=320):
    for k in range(3):
        ph = (t * 0.8 + k / 3) % 1
        rw = w * (0.6 + ph)
        a = int(200 * (1 - ph))
        ov = Image.new('RGBA', (int(rw * 2 + 20), int(rw * 0.5 + 20)), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([10, 10, ov.width - 10, ov.height - 10], outline=(220, 240, 255, a), width=6)
        paste_at(img, ov, int(cx - ov.width / 2), int(cy - ov.height / 2))

GREEN = (120, 200, 70)
PINK = (245, 120, 170)
BLUE = (80, 170, 230)
CLOG_COLS = [(120, 200, 70), (245, 120, 170), (80, 170, 230), (250, 200, 60), (170, 120, 230), (250, 130, 70), (240, 240, 240)]

def bill_sprite(w=170):
    im, d = _ss(w, w * 0.45)
    d.rounded_rectangle([0, 0, w * SS - 1, w * 0.45 * SS - 1], 10, fill=(130, 190, 110), outline=(70, 120, 60), width=6)
    d.ellipse([w * 0.35 * SS, w * 0.07 * SS, w * 0.65 * SS, w * 0.38 * SS], fill=(180, 225, 160), outline=(70, 120, 60), width=4)
    d.text((w * 0.43 * SS, w * 0.04 * SS), '$', font=font(int(w * 0.28 * SS)), fill=(60, 110, 50))
    return _down(im)


# ================================================================ NUTELLA props (generic, no logos)
CHOC = (112, 66, 36)
CHOC_TOP = (148, 92, 52)
CHOC_CUT = (135, 82, 46)
FOIL = (205, 210, 218)

_LOAF = {}
def loaf(w=900, h=None, foil=True, cut_x=None):
    """Solid hazelnut-cocoa loaf. front face + top + right side. foil wraps the left end."""
    h = h or int(w * 0.95)
    key = (w, h, foil)
    if key in _LOAF:
        return _LOAF[key]
    im, d = _ss(w, h)
    s = SS
    dep = h * 0.2
    fx1 = w * 0.86
    rng = np.random.default_rng(7)
    # top
    d.polygon([(0, dep * s), (w * 0.14 * s, 0), (w * s, 0), (fx1 * s, dep * s)], fill=CHOC_TOP)
    # right side
    d.polygon([(fx1 * s, dep * s), (w * s, 0), (w * s, (h - dep) * s), (fx1 * s, h * s - 1)], fill=dk(CHOC, 0.78))
    # front
    d.rectangle([0, dep * s, fx1 * s, h * s - 1], fill=CHOC)
    for k in range(260):
        x = rng.uniform(0.02, 0.98) * fx1
        y = rng.uniform(dep + 10, h - 10)
        r = rng.uniform(3, 8)
        d.ellipse([(x - r) * s, (y - r * 0.8) * s, (x + r) * s, (y + r * 0.8) * s], fill=(165, 110, 65) if k % 3 else (90, 50, 25))
    # gloss
    d.line([(w * 0.2 * s, dep * 0.45 * s), (w * 0.85 * s, dep * 0.45 * s)], fill=lt(CHOC_TOP, 0.35), width=int(10 * s))
    d.line([(fx1 * 0.05 * s, (dep + 20) * s), (fx1 * 0.05 * s, (h - 30) * s)], fill=lt(CHOC, 0.2), width=int(8 * s))
    if foil:
        fw = w * 0.34
        pts = [(0, dep * s - 6), (w * 0.14 * s, 0), ((w * 0.14 + fw) * s, 0)]
        # crinkly right edge going down front
        for k in range(12):
            yy = dep + (h - dep) * k / 11
            xx = fw + (14 if k % 2 else -10)
            pts.append((xx * s, yy * s))
        pts += [(0, h * s - 1)]
        d.polygon(pts, fill=FOIL)
        for k in range(18):
            x0 = rng.uniform(0.02, 0.9) * fw
            y0 = rng.uniform(dep, h)
            d.line([(x0 * s, y0 * s), ((x0 + rng.uniform(-40, 40)) * s, (y0 + rng.uniform(20, 70)) * s)], fill=(235, 238, 245) if k % 2 else (160, 165, 175), width=int(4 * s))
        d.polygon([(w * 0.14 * s, 0), ((w * 0.14 + fw) * s, 0), ((w * 0.12 + fw) * s, dep * 0.5 * s), (w * 0.07 * s, dep * 0.5 * s)], fill=(235, 238, 244))
    out = _down(im)
    _LOAF[key] = out
    return out

def slab_sprite(w=120, h=700):
    """A cut slice seen from the side (thin block)."""
    im, d = _ss(w + 40, h)
    s = SS
    d.polygon([(0, 30 * s), (40 * s, 0), ((w + 40) * s, 0), (w * s, 30 * s)], fill=CHOC_TOP)
    d.rectangle([0, 30 * s, w * s, h * s - 1], fill=CHOC_CUT)
    d.polygon([(w * s, 30 * s), ((w + 40) * s - 1, 0), ((w + 40) * s - 1, (h - 30) * s), (w * s, h * s - 1)], fill=dk(CHOC, 0.8))
    rng = np.random.default_rng(3)
    for k in range(40):
        x, y, r = rng.uniform(6, w - 6), rng.uniform(40, h - 10), rng.uniform(3, 7)
        d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=(170, 115, 70))
    return _down(im)

_JAR = {}
def jar(w=300, lid=True, level=1.0):
    key = (w, lid, level)
    if key in _JAR:
        return _JAR[key]
    h = int(w * 1.3)
    im, d = _ss(w, h)
    s = SS
    lh = h * 0.18
    body = [w * 0.04 * s, lh * 0.85 * s, w * 0.96 * s, h * s - 1]
    d.rounded_rectangle(body, int(w * 0.16 * s), fill=(225, 235, 240))
    top = lh * 0.85 + (h - lh * 0.85) * (1 - level) + 12
    if level > 0:
        d.rounded_rectangle([w * 0.08 * s, min(top, h - 40) * s, w * 0.92 * s, (h - 8) * s], int(min(w * 0.13, (h - 8 - min(top, h - 40)) / 2 - 1) * s), fill=(95, 55, 28))
    # label (generic: hazelnut + bread drawing, no text)
    ly0, ly1 = h * 0.42, h * 0.80
    d.rectangle([w * 0.04 * s, ly0 * s, w * 0.96 * s, ly1 * s], fill=(250, 248, 242))
    d.rectangle([w * 0.04 * s, ly0 * s, w * 0.96 * s, (ly0 + 10) * s], fill=(200, 60, 50))
    d.rectangle([w * 0.04 * s, (ly1 - 10) * s, w * 0.96 * s, ly1 * s], fill=(200, 60, 50))
    cx, cy = w * 0.38, (ly0 + ly1) / 2
    d.rounded_rectangle([(cx - w * 0.2) * s, (cy - w * 0.12) * s, (cx + w * 0.12) * s, (cy + w * 0.16) * s], int(w * 0.05 * s), fill=(225, 175, 105))
    d.rounded_rectangle([(cx - w * 0.16) * s, (cy - w * 0.08) * s, (cx + w * 0.08) * s, (cy + w * 0.12) * s], int(w * 0.04 * s), fill=(110, 62, 32))
    hx, hy = w * 0.68, cy
    d.ellipse([(hx - w * 0.11) * s, (hy - w * 0.09) * s, (hx + w * 0.11) * s, (hy + w * 0.12) * s], fill=(170, 105, 55))
    d.chord([(hx - w * 0.11) * s, (hy - w * 0.02) * s, (hx + w * 0.11) * s, (hy + w * 0.14) * s], 0, 180, fill=(215, 175, 125))
    # glass shine
    d.rounded_rectangle([w * 0.12 * s, (lh + 10) * s, w * 0.2 * s, (ly0 - 8) * s], int(6 * s), fill=(255, 255, 255, 170))
    if lid:
        d.rounded_rectangle([0, 0, w * s - 1, lh * s], int(w * 0.06 * s), fill=(250, 250, 250), outline=(205, 205, 210), width=int(3 * s))
        for k in range(1, 14):
            x = w * k / 14 * s
            d.line([(x, 6 * s), (x, (lh - 6) * s)], fill=(220, 220, 226), width=int(2 * s))
    out = _down(im)
    _JAR[key] = out
    return out

_NUT = {}
def nut(r=40, rot=0):
    key = (r, rot)
    if key in _NUT:
        return _NUT[key]
    im, d = _ss(r * 2.4, r * 2.6)
    s = SS
    cx, cy = r * 1.2 * s, r * 1.35 * s
    R = r * s
    d.ellipse([cx - R, cy - R * 0.95, cx + R, cy + R * 1.05], fill=(165, 100, 50))
    d.polygon([(cx - R * 0.45, cy - R * 0.75), (cx, cy - R * 1.3), (cx + R * 0.45, cy - R * 0.75)], fill=(165, 100, 50))
    d.chord([cx - R, cy - R * 0.05, cx + R, cy + R * 1.05], 0, 180, fill=(220, 180, 130))
    for k in range(6):
        x = cx - R * 0.7 + k * R * 0.28
        d.line([(x, cy + R * 0.2), (x + R * 0.05, cy + R * 0.9)], fill=(190, 150, 100), width=max(2, int(R * 0.06)))
    d.ellipse([cx - R * 0.55, cy - R * 0.7, cx - R * 0.15, cy - R * 0.3], fill=(205, 145, 90))
    out = _down(im)
    if rot:
        out = out.rotate(rot, resample=Image.BICUBIC, expand=True)
    _NUT[key] = out
    return out

def nut_d(d, x, y, r, seed=0):
    """Fast inline hazelnut for heaps."""
    c = [(165, 100, 50), (150, 90, 45), (180, 112, 58)][seed % 3]
    d.ellipse([x - r, y - r * 0.9, x + r, y + r], fill=c)
    d.chord([x - r, y, x + r, y + r], 0, 180, fill=(215, 172, 120))
    d.ellipse([x - r * 0.5, y - r * 0.65, x - r * 0.15, y - r * 0.3], fill=lt(c, 0.3))

def bread(w=300, spread=0.0, slab=False):
    h = int(w * 0.9)
    im, d = _ss(w, h)
    s = SS
    crust = (190, 125, 60)
    d.rounded_rectangle([0, h * 0.25 * s, w * s - 1, h * s - 1], int(w * 0.08 * s), fill=crust)
    d.ellipse([0, 0, w * 0.55 * s, h * 0.55 * s], fill=crust)
    d.ellipse([w * 0.45 * s, 0, w * s - 1, h * 0.55 * s], fill=crust)
    m = w * 0.07
    d.rounded_rectangle([m * s, h * 0.27 * s, (w - m) * s, (h - m) * s], int(w * 0.06 * s), fill=(245, 220, 165))
    d.ellipse([m * s, m * s, (w * 0.55 - m * 0.3) * s, h * 0.5 * s], fill=(245, 220, 165))
    d.ellipse([(w * 0.45 + m * 0.3) * s, m * s, (w - m) * s, h * 0.5 * s], fill=(245, 220, 165))
    if slab:
        d.rounded_rectangle([w * 0.16 * s, h * 0.3 * s, w * 0.84 * s, h * 0.8 * s], int(10 * s), fill=CHOC_CUT, outline=dk(CHOC, 0.8), width=int(4 * s))
        rng = np.random.default_rng(1)
        for k in range(14):
            x, y = rng.uniform(0.2, 0.8) * w, rng.uniform(0.35, 0.75) * h
            d.ellipse([(x - 5) * s, (y - 4) * s, (x + 5) * s, (y + 4) * s], fill=(175, 118, 72))
    if spread > 0:
        pts = []
        for k in range(28):
            a = 2 * math.pi * k / 28
            rr = 1 + 0.08 * math.sin(a * 5)
            pts.append((w * 0.5 * s + math.cos(a) * w * 0.36 * spread * rr * s, h * 0.55 * s + math.sin(a) * h * 0.3 * spread * rr * s))
        d.polygon(pts, fill=(105, 60, 30))
        d.arc([w * 0.3 * s, h * 0.4 * s, w * 0.7 * s, h * 0.7 * s], 200, 320, fill=(150, 95, 55), width=int(6 * s))
    return _down(im)

def knife(L=520):
    im, d = _ss(L, L * 0.18)
    s = SS
    hh = L * 0.18
    d.rounded_rectangle([0, hh * 0.3 * s, L * 0.32 * s, hh * 0.8 * s], int(10 * s), fill=(45, 40, 40))
    for k in range(3):
        x = L * (0.07 + k * 0.09)
        d.ellipse([(x - 6) * s, (hh * 0.55 - 6) * s, (x + 6) * s, (hh * 0.55 + 6) * s], fill=(200, 200, 205))
    d.polygon([(L * 0.32 * s, hh * 0.2 * s), (L * s - 1, hh * 0.55 * s), (L * 0.32 * s, hh * 0.95 * s)], fill=(215, 220, 228))
    d.line([(L * 0.32 * s, hh * 0.3 * s), (L * 0.95 * s, hh * 0.55 * s)], fill=(250, 252, 255), width=int(4 * s))
    return _down(im)

def bowl(w=620, fill=0.0, swirl=0.0):
    h = int(w * 0.62)
    im, d = _ss(w, h)
    s = SS
    d.chord([0, -h * 0.55 * s, w * s - 1, h * s - 1], 0, 180, fill=(235, 238, 242))
    d.chord([w * 0.08 * s, -h * 0.4 * s, w * 0.92 * s, h * 0.9 * s], 30, 150, fill=(215, 220, 228))
    d.rectangle([w * 0.1 * s, h * 0.55 * s, w * 0.9 * s, h * 0.6 * s], fill=(90, 150, 210))
    d.ellipse([0, 0, w * s - 1, h * 0.3 * s], fill=(205, 210, 218))
    if fill > 0:
        d.ellipse([w * 0.06 * s, h * 0.03 * s, w * 0.94 * s, h * 0.27 * s], fill=(150, 95, 50) if swirl == 0 else (105, 62, 32))
    d.ellipse([0, 0, w * s - 1, h * 0.3 * s], outline=(250, 250, 252), width=int(8 * s))
    return _down(im)

def sparkle(d, x, y, r, col=(255, 240, 150)):
    d.polygon([(x, y - r), (x + r * 0.22, y - r * 0.22), (x + r, y), (x + r * 0.22, y + r * 0.22), (x, y + r), (x - r * 0.22, y + r * 0.22), (x - r, y), (x - r * 0.22, y - r * 0.22)], fill=col)

def heart_d(d, cx, cy, r, col=(240, 80, 120)):
    d.ellipse([cx - r * 0.95, cy - r * 0.75, cx + r * 0.05, cy + r * 0.25], fill=col)
    d.ellipse([cx - r * 0.05, cy - r * 0.75, cx + r * 0.95, cy + r * 0.25], fill=col)
    d.polygon([(cx - r * 0.9, cy - r * 0.15), (cx + r * 0.9, cy - r * 0.15), (cx, cy + r * 0.95)], fill=col)

# ================================================================ NUTELLA plates
def subway_wall(d, y1, base=(245, 242, 235), line=(205, 200, 192), tw=120, th=60):
    for y in range(0, y1, th):
        off = (y // th % 2) * tw // 2
        for x in range(-off, PW, tw):
            d.rectangle([x + 2, y + 2, x + tw - 2, y + th - 2], fill=base, outline=line, width=3)

def shelf(d, x0, x1, y, items, col=(150, 105, 65)):
    d.rectangle([x0, y, x1, y + 22], fill=col)
    d.rectangle([x0, y + 22, x1, y + 34], fill=dk(col, 0.7))
    x = x0 + 20
    for (iw, ih, c, kind) in items:
        if x + iw > x1 - 10:
            break
        if kind == 'jar':
            d.rounded_rectangle([x, y - ih, x + iw, y], 10, fill=c)
            d.rectangle([x - 4, y - ih - 18, x + iw + 4, y - ih + 4], fill=(240, 240, 240))
        elif kind == 'tin':
            d.rectangle([x, y - ih, x + iw, y], fill=c, outline=dk(c, 0.7), width=4)
            d.rectangle([x, y - ih * 0.65, x + iw, y - ih * 0.35], fill=lt(c, 0.6))
        elif kind == 'box':
            d.rectangle([x, y - ih, x + iw, y], fill=c, outline=dk(c, 0.7), width=4)
            d.ellipse([x + iw * 0.25, y - ih * 0.7, x + iw * 0.75, y - ih * 0.3], fill=lt(c, 0.5))
        elif kind == 'plant':
            d.rectangle([x, y - ih * 0.4, x + iw, y], fill=(200, 110, 70))
            for a in range(-50, 60, 25):
                r = math.radians(a - 90)
                d.ellipse([x + iw / 2 + math.cos(r) * iw * 0.6 - 18, y - ih * 0.4 + math.sin(r) * ih * 0.6 - 30, x + iw / 2 + math.cos(r) * iw * 0.6 + 18, y - ih * 0.4 + math.sin(r) * ih * 0.6 + 30], fill=(70, 150, 80))
        x += iw + 22

@cached
def counter_plate(variant=0):
    base = [(245, 242, 235), (232, 240, 236)][variant]
    im = Image.new('RGBA', (PW, PH), base)
    d = ImageDraw.Draw(im)
    subway_wall(d, 1500, base, dk(base, 0.85))
    if variant == 0:
        window(d, 820, 640, 1230, 1100, 'mountains', (255, 255, 255))
        shelf(d, 0, 700, 900, [(90, 140, (230, 170, 80), 'jar'), (80, 110, (200, 80, 70), 'jar'), (140, 170, (120, 170, 210), 'tin'),
                                (100, 120, (240, 210, 120), 'jar'), (120, 160, (90, 160, 100), 'plant')])
        d.rectangle([60, 1100, 640, 1120], fill=(120, 120, 125))
        for k, L in enumerate((170, 210, 150, 190)):
            x = 110 + k * 130
            d.line([(x, 1120), (x, 1120 + L * 0.3)], fill=(90, 90, 95), width=6)
            d.ellipse([x - 26, 1120 + L * 0.3, x + 26, 1120 + L * 0.3 + 70], fill=[(200, 90, 60), (90, 90, 95), (220, 170, 70), (110, 160, 200)][k])
    else:
        shelf(d, 80, 1220, 820, [(110, 150, (210, 170, 110), 'tin'), (90, 120, (190, 80, 70), 'jar'), (130, 160, (240, 220, 180), 'box'),
                                  (100, 130, (230, 180, 90), 'jar'), (110, 150, (150, 110, 80), 'tin'), (120, 170, (90, 160, 100), 'plant'), (90, 120, (180, 60, 60), 'jar')])
        shelf(d, 80, 1220, 1180, [(140, 200, (235, 230, 220), 'box'), (100, 140, (200, 150, 90), 'jar'), (100, 130, (160, 200, 230), 'tin'),
                                   (120, 160, (240, 200, 120), 'box'), (90, 120, (220, 120, 80), 'jar'), (110, 150, (190, 170, 140), 'tin')])
    return finish_plate(im, 0.35, 21 + variant)

def counter_front(img, y, top=(225, 222, 215), front=(95, 130, 150)):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, y + 60], fill=top)
    d.line([(-20, y), (PW + 20, y)], fill=(250, 250, 250), width=6)
    d.rectangle([-20, y + 60, PW + 20, PH], fill=front)
    for x in range(0, PW + 1, 324):
        d.rectangle([x + 18, y + 90, x + 306, PH - 20], outline=dk(front, 0.8), width=6)
        d.rounded_rectangle([x + 140, y + 130, x + 184, y + 146], 6, fill=(210, 210, 215))

def board(img, cx, y, w=1000):
    d = ImageDraw.Draw(img)
    floor_shadow(img, cx, y + 70, w * 0.6, 0.3)
    d.rounded_rectangle([cx - w / 2, y - 10, cx + w / 2, y + 45], 18, fill=(200, 150, 95), outline=(150, 105, 60), width=5)

@cached
def shop_plate():
    im = Image.new('RGBA', (PW, PH), (235, 220, 190))
    d = ImageDraw.Draw(im)
    for x in range(0, PW, 64):
        d.rectangle([x, 0, x + 30, 1500], fill=(228, 210, 178))
    d.rectangle([40, 160, PW - 40, 1520], fill=(130, 88, 52))
    rows = [380, 680, 980, 1280]
    rng = np.random.default_rng(11)
    palette = [(200, 70, 60), (70, 120, 170), (230, 190, 80), (110, 150, 90), (235, 225, 205), (180, 120, 70)]
    for r, y in enumerate(rows):
        items = []
        for k in range(14):
            kind = ['tin', 'jar', 'box'][int(rng.integers(0, 3))]
            items.append((int(rng.integers(70, 110)), int(rng.integers(120, 220)), palette[int(rng.integers(0, 6))], kind))
        if r == 1:
            # the empty cocoa/chocolate gap in the middle row
            shelf(d, 60, 470, y, items[:4], (160, 112, 70))
            shelf(d, 470, 830, y, [], (160, 112, 70))
            shelf(d, 830, PW - 60, y, items[4:8], (160, 112, 70))
        else:
            shelf(d, 60, PW - 60, y, items, (160, 112, 70))
    d.line([(CX, 0), (CX, 90)], fill=(40, 40, 40), width=6)
    d.polygon([(CX - 90, 150), (CX + 90, 150), (CX + 50, 90), (CX - 50, 90)], fill=(60, 110, 80))
    for k in range(9):
        x = k * 150
        d.rectangle([x, 1520, x + 150, PH], fill=(225, 215, 195) if k % 2 == 0 else (120, 90, 70))
    for y in range(1520, PH, 140):
        d.line([(0, y), (PW, y)], fill=(90, 70, 55), width=3)
    return finish_plate(im, 0.4, 31)

def shop_counter(img, y=1560):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, y + 50], fill=(170, 120, 75))
    d.rectangle([-20, y + 50, PW + 20, PH], fill=(120, 80, 45))
    for x in range(0, PW, 108):
        d.line([(x, y + 50), (x, PH)], fill=(95, 62, 35), width=5)
    # scale
    d.rectangle([900, y - 30, 1160, y], fill=(80, 80, 85))
    d.rectangle([1010, y - 160, 1050, y - 30], fill=(80, 80, 85))
    d.chord([900, y - 220, 1160, y - 120], 0, 180, fill=(190, 160, 60))
    d.ellipse([985, y - 300, 1075, y - 210], fill=(245, 245, 240), outline=(80, 80, 85), width=6)

@cached
def street_plate():
    arr = vgrad(PW, PH, [(0, '#7CC5EE'), (0.35, '#D6F0FB'), (1, '#D6F0FB')])
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.polygon([(0, 760), (300, 600), (650, 720), (980, 580), (PW, 700), (PW, 1000), (0, 1000)], fill=(120, 170, 110))
    for k in range(10):
        x = 60 + k * 130
        d.line([(x, 760 - (k % 3) * 30), (x, 820)], fill=(90, 120, 70), width=6)
        for j in range(6):
            d.ellipse([x - 40 + j * 14, 700 - (k % 3) * 30 + (j % 2) * 20, x - 10 + j * 14, 730 - (k % 3) * 30 + (j % 2) * 20], fill=(80, 140, 80))
    # buildings left and right
    for (x0, x1, top, col) in ((-20, 360, 420, (235, 180, 120)), (PW - 380, PW + 20, 360, (230, 160, 110)), (330, 520, 640, (240, 215, 170))):
        d.rectangle([x0, top, x1, 1600], fill=col)
        d.polygon([(x0 - 20, top), (x1 + 20, top), ((x0 + x1) / 2, top - 70)], fill=(185, 90, 60))
        for wy in range(top + 80, 1400, 230):
            for wx in range(int(x0) + 50, int(x1) - 90, 150):
                d.rectangle([wx, wy, wx + 90, wy + 140], fill=(70, 60, 60))
                d.rectangle([wx - 34, wy, wx, wy + 140], fill=(70, 130, 90))
                d.rectangle([wx + 90, wy, wx + 124, wy + 140], fill=(70, 130, 90))
    # market stall awning
    d.rectangle([400, 1000, 900, 1040], fill=(120, 80, 45))
    for k in range(8):
        x0 = 380 + k * 70
        d.polygon([(x0, 900), (x0 + 70, 900), (x0 + 70, 1010), (x0 + 35, 1050), (x0, 1010)], fill=(220, 70, 60) if k % 2 == 0 else (250, 245, 235))
    d.line([(410, 1040), (410, 1650)], fill=(120, 80, 45), width=16)
    d.line([(890, 1040), (890, 1650)], fill=(120, 80, 45), width=16)
    # cobblestones
    d.rectangle([0, 1600, PW, PH], fill=(150, 140, 130))
    rng = np.random.default_rng(4)
    y, g = 1600, 40
    while y < PH:
        x = -rng.uniform(0, 60)
        while x < PW:
            w = g * 2.2
            d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + g - 4], 10, fill=(175 + int(rng.integers(-12, 12)), 165, 152))
            x += w
        y += g
        g *= 1.15
    return finish_plate(im, 0.35, 41)

def stall_table(img, y=1500, empty=True):
    d = ImageDraw.Draw(img)
    d.rectangle([300, y, 1000, y + 40], fill=(170, 120, 75))
    d.rectangle([320, y + 40, 980, y + 300], fill=(140, 95, 55))
    for k in range(3):
        bx = 340 + k * 220
        d.rectangle([bx, y - 110, bx + 190, y], fill=(200, 160, 105), outline=(140, 100, 60), width=6)
        if k == 1:
            for j in range(5):
                d.ellipse([bx + 70 + j * 10, y - 130 + (j % 2) * 6, bx + 90 + j * 10, y - 116 + (j % 2) * 6], fill=(95, 55, 30))
        elif k == 0:
            for j in range(9):
                d.ellipse([bx + 15 + j * 18, y - 140 - (j % 3) * 10, bx + 55 + j * 18, y - 100 - (j % 3) * 10], fill=(230, 90, 60))
        else:
            for j in range(8):
                d.ellipse([bx + 15 + j * 20, y - 140 - (j % 2) * 12, bx + 55 + j * 20, y - 100 - (j % 2) * 12], fill=(240, 200, 70))

@cached
def pastry_plate():
    im = Image.new('RGBA', (PW, PH), (250, 225, 225))
    d = ImageDraw.Draw(im)
    for x in range(0, PW, 100):
        d.rectangle([x, 0, x + 50, 1450], fill=(246, 214, 214))
    d.rectangle([0, 0, PW, 140], fill=(120, 60, 70))
    for k in range(10):
        x0 = k * 130
        d.chord([x0, 80, x0 + 130, 220], 0, 180, fill=(250, 245, 235) if k % 2 else (200, 80, 90))
    # back shelves with cakes
    for y in (720, 1060):
        d.rectangle([60, y, PW - 60, y + 24], fill=(250, 250, 250))
        for k in range(5):
            cx = 180 + k * 235
            d.rectangle([cx - 80, y - 110, cx + 80, y], fill=[(250, 220, 160), (240, 160, 180), (130, 80, 50), (250, 240, 230), (200, 120, 70)][k])
            d.rectangle([cx - 80, y - 130, cx + 80, y - 110], fill=(255, 250, 245))
            for j in range(4):
                d.ellipse([cx - 64 + j * 40, y - 150, cx - 40 + j * 40, y - 126], fill=(220, 40, 60))
            d.rectangle([cx - 100, y - 8, cx + 100, y], fill=(220, 220, 225))
    # framed picture
    d.rectangle([480, 260, 820, 520], fill=(250, 245, 230), outline=(160, 120, 60), width=16)
    d.polygon([(500, 500), (600, 360), (680, 440), (740, 380), (800, 500)], fill=(120, 170, 120))
    d.rectangle([0, 1450, PW, PH], fill=(235, 230, 225))
    for k in range(0, PW, 90):
        for j in range(1450, PH, 90):
            if (k // 90 + j // 90) % 2 == 0:
                d.rectangle([k, j, k + 90, j + 90], fill=(60, 60, 70))
    return finish_plate(im, 0.35, 51)

def display_case(img, y=1500):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, PH], fill=(245, 240, 235))
    d.rectangle([-20, y, PW + 20, y + 30], fill=(200, 160, 120))
    d.rectangle([20, y + 60, PW - 20, y + 420], fill=(205, 230, 240), outline=(170, 170, 180), width=8)
    for row in range(2):
        yy = y + 160 + row * 160
        d.rectangle([40, yy + 50, PW - 40, yy + 60], fill=(250, 250, 250))
        for k in range(7):
            cx = 120 + k * 175
            col = [(230, 180, 110), (150, 90, 50), (245, 210, 160), (240, 150, 170)][(k + row) % 4]
            d.ellipse([cx - 60, yy - 10, cx + 60, yy + 50], fill=col)
            d.ellipse([cx - 40, yy - 20, cx + 40, yy + 10], fill=lt(col, 0.4))
    d.line([(60, y + 80), (260, y + 400)], fill=(255, 255, 255), width=10)

@cached
def dining_plate():
    im = Image.new('RGBA', (PW, PH), (170, 200, 170))
    d = ImageDraw.Draw(im)
    for y in range(60, 1500, 140):
        for x in range((y // 140 % 2) * 70, PW, 140):
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(195, 220, 190))
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(240, 220, 150))
    d.rectangle([0, 1300, PW, 1500], fill=(150, 105, 70))
    window(d, 820, 360, 1180, 900, 'mountains', (250, 245, 230))
    # cupboard with plates
    d.rectangle([60, 360, 560, 1300], fill=(140, 95, 60))
    for y in (520, 760, 1000):
        d.rectangle([80, y, 540, y + 16], fill=(110, 72, 45))
        for k in range(4):
            d.ellipse([100 + k * 110, y - 120, 200 + k * 110, y - 4], fill=(250, 250, 245), outline=(80, 120, 190), width=8)
    d.rectangle([60, 330, 560, 370], fill=(110, 72, 45))
    d.rectangle([600, 1020, 760, 1180], fill=(250, 245, 230), outline=(110, 72, 45), width=12)
    d.ellipse([640, 1050, 720, 1130], fill=(220, 120, 110))
    wood_floor(d, 1500, (160, 112, 72))
    return finish_plate(im, 0.4, 61)

def cloth_table(img, y=1560):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, PH], fill=(250, 250, 250))
    sq = 70
    for x in range(-20, PW + 20, sq):
        for yy in range(y, PH, sq):
            if (x // sq + yy // sq) % 2 == 0:
                d.rectangle([x, yy, x + sq, yy + sq], fill=(215, 60, 60))
    d.rectangle([-20, y, PW + 20, y + 14], fill=(190, 45, 45))

@cached
def factory_plate():
    im = Image.new('RGBA', (PW, PH), (170, 180, 190))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 1550], fill=(185, 192, 200))
    for k in range(4):
        x0 = 40 + k * 310
        d.rectangle([x0, 140, x0 + 270, 600], fill=(220, 235, 245), outline=(100, 110, 120), width=12)
        for j in range(1, 3):
            d.line([(x0 + j * 90, 140), (x0 + j * 90, 600)], fill=(100, 110, 120), width=6)
        d.line([(x0, 370), (x0 + 270, 370)], fill=(100, 110, 120), width=6)
    d.rectangle([0, 660, PW, 700], fill=(120, 130, 140))
    d.line([(0, 740), (PW, 740)], fill=(200, 120, 60), width=24)
    d.line([(1150, 740), (1150, 1550)], fill=(200, 120, 60), width=24)
    # big steel vat
    d.rectangle([140, 820, 640, 1400], fill=(200, 205, 215), outline=(120, 125, 135), width=10)
    d.ellipse([140, 770, 640, 870], fill=(220, 225, 232), outline=(120, 125, 135), width=10)
    for y in (950, 1150, 1330):
        d.line([(140, y), (640, y)], fill=(150, 155, 165), width=8)
    d.ellipse([500, 980, 600, 1080], fill=(250, 250, 250), outline=(60, 60, 70), width=8)
    d.line([(550, 1030), (580, 1000)], fill=(220, 40, 40), width=6)
    d.rectangle([180, 1400, 230, 1560], fill=(120, 125, 135))
    d.rectangle([550, 1400, 600, 1560], fill=(120, 125, 135))
    # pipe from vat to filler
    d.line([(640, 1000), (820, 1000), (820, 1240)], fill=(150, 155, 165), width=40)
    d.rectangle([770, 1220, 870, 1300], fill=(120, 125, 135))
    d.rectangle([0, 1550, PW, PH], fill=(120, 125, 130))
    d.line([(0, 1600), (PW, 1600)], fill=(240, 200, 60), width=14)
    for k in range(-6, 7):
        d.line([(CX + k * 90, 1550), (CX + k * 330, PH)], fill=(105, 110, 115), width=4)
    return finish_plate(im, 0.4, 71)

def conveyor(img, y, t, speed=160):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, y + 40], fill=(60, 62, 68))
    off = (t * speed) % 80
    for x in range(-80, PW + 80, 80):
        d.line([(x + off, y + 4), (x + off, y + 36)], fill=(95, 98, 105), width=6)
    d.rectangle([-20, y + 40, PW + 20, y + 70], fill=(150, 155, 165))
    for x in range(60, PW, 260):
        d.rectangle([x, y + 70, x + 30, y + 330], fill=(110, 115, 125))

@cached
def warehouse_plate():
    im = Image.new('RGBA', (PW, PH), (200, 185, 160))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 1300], fill=(190, 175, 150))
    for k in range(-2, 8):
        x = k * 220
        d.line([(x, 0), (x + 220, 260)], fill=(120, 110, 95), width=14)
        d.line([(x + 220, 0), (x, 260)], fill=(120, 110, 95), width=14)
    d.line([(0, 260), (PW, 260)], fill=(110, 100, 85), width=20)
    d.rectangle([380, 360, 920, 900], fill=(140, 200, 235), outline=(110, 100, 85), width=16)
    d.polygon([(380, 780), (560, 600), (700, 720), (820, 620), (920, 700), (920, 900), (380, 900)], fill=(110, 160, 100))
    # stacked sacks
    for row in range(4):
        for k in range(4 - row):
            x = 20 + k * 120 + row * 60
            y = 1300 - row * 90
            d.rounded_rectangle([x, y - 90, x + 115, y], 30, fill=(205, 180, 130), outline=(160, 135, 95), width=5)
    d.rectangle([0, 1300, PW, PH], fill=(160, 150, 135))
    rng = np.random.default_rng(9)
    # two hazelnut mountains in the back
    for (cx, cy, rw, rh) in ((900, 1360, 520, 520), (300, 1420, 380, 300)):
        for k in range(900):
            u = rng.uniform(-1, 1)
            v = rng.uniform(0, 1)
            if v > 1 - abs(u) ** 1.6 * 0.0 - (1 - abs(u) ** 2):
                continue
            x = cx + u * rw
            y = cy - v * rh * (1 - u * u)
            nut_d(d, x, y, 18, k)
    return finish_plate(im, 0.4, 81)

def nut_heap(img, cx, base, rw, rh, seed=1, r=26):
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    pts = []
    for k in range(int(rw * rh / 260)):
        u = rng.uniform(-1, 1)
        v = rng.uniform(0, 1) * (1 - u * u)
        pts.append((cx + u * rw, base - v * rh, k))
    pts.sort(key=lambda p: p[1])
    for (x, y, k) in pts:
        nut_d(d, x, y, r, k)

# ================================================================ characters (same person = same look)
NTEEN = dict(PRESETS['girl'])
PIETRO = dict(PRESETS['chef'])
SHOPKEEP = dict(PRESETS['grandma'], top=(120, 90, 160), apron=(240, 240, 230))
NKID = dict(PRESETS['kid'], skin='light', hair_color=(120, 80, 40), top=(90, 150, 220))
MAMMA = dict(PRESETS['woman'], hair='bun', skin='tan', hair_color=(60, 40, 30), top=(200, 90, 90), apron=(245, 245, 235))
VENDOR = dict(PRESETS['salesman'], top=(110, 130, 90))
WORKERN = dict(PRESETS['worker'], top=(245, 245, 245), hat=None, hair='short', apron=(90, 140, 200))
MICHELE = dict(PRESETS['boss'], skin='tan', hair_color=(40, 30, 25), top=(60, 80, 130), tie=(180, 120, 60))
PARTNER = dict(PRESETS['boss'], skin='light', hair='messy', hair_color=(160, 160, 165), top=(90, 70, 60), glasses=True, tie=(60, 120, 80))
FARMER = dict(PRESETS['worker'], skin='brown', top=(200, 120, 60), hat='cap', hat_color=(60, 110, 60))

def hold(img, sp, a, hand='hand_r', dx=0, dy=0, rot=0, scale=1.0):
    hx, hy = a[hand]
    put(img, sp, hx + dx, hy + dy, scale, rot)


# ================================================================ EMOJI props (generic, no logos)
FONT_CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'

BM = {
    'heart': ["............", "..##....##..", ".####..####.", "############", "############", "############",
              ".##########.", "..########..", "...######...", "....####....", ".....##.....", "............"],
    'sun': [".....##.....", ".#...##...#.", "..#......#..", "....####....", "...######...", "##.######.##",
            "##.######.##", "...######...", "....####....", "..#......#..", ".#...##...#.", ".....##....."],
    'smile': ["...######...", "..#......#..", ".#........#.", "#..##..##..#", "#..##..##..#", "#..........#",
              "#.#......#.#", "#..#....#..#", ".#..####..#.", "..#......#..", "...######...", "............"],
    'umbrella': [".....##.....", "...######...", "..########..", ".##########.", "############", "#..#..#..#.#",
                 ".....##.....", ".....##.....", ".....##.....", ".....##.....", "..#..##.....", "...##......."],
    'note': ["......####..", "......#..#..", "......#..#..", "......#..#..", "......#..#..", "......#..#..",
             "......#..#..", "..####...#..", ".#####..##..", ".#####.###..", "..###..##...", "............"],
    'cloud': ["............", "............", "....###.....", "...#####....", "..#######.#.", ".##########.",
              "############", "############", ".##########.", "............", "............", "............"],
    'moon': ["....####....", "...###......", "..###.......", ".###........", ".###........", ".###........",
             ".###........", ".###........", "..###.......", "...###......", "....####....", "............"],
    'phone': ["...######...", "...#....#...", "...#....#...", "...#....#...", "...#....#...", "...######...",
              "...#.##.#...", "...######...", "...#.##.#...", "...######...", "...#.##.#...", "...######..."],
}
BM_KEYS = list(BM)
ICOL = [(230, 50, 80), (240, 140, 30), (40, 40, 45), (60, 110, 210), (40, 40, 45), (90, 150, 220), (200, 150, 20), (40, 40, 45)]

_PX = {}
def pixel_icon(kind, cell=10, col=(230, 50, 80), n=None, bg=None, grid=None):
    """12x12 pixel art. n = number of pixels drawn so far (for the drawing animation)."""
    key = (kind, cell, tuple(col), n, bg, grid)
    if key in _PX:
        return _PX[key]
    rows = BM[kind]
    im = Image.new('RGBA', (cell * 12, cell * 12), bg if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = 0
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '#':
                if n is not None and k >= n:
                    continue
                d.rectangle([x * cell, y * cell, x * cell + cell - 1, y * cell + cell - 1], fill=col)
                k += 1
    if grid:
        for i in range(13):
            d.line([(i * cell, 0), (i * cell, cell * 12)], fill=grid, width=max(1, cell // 14))
            d.line([(0, i * cell), (cell * 12, i * cell)], fill=grid, width=max(1, cell // 14))
    _PX[key] = im
    return im

def npix(kind):
    return sum(r.count('#') for r in BM[kind])

_PG = {}
def pager(w=560, body=(70, 190, 200), heart=1.0, blank=False):
    """90s pager standing upright: clip on top, LCD with a pixel heart. heart = heart scale (pulse)."""
    key = (w, tuple(body), round(heart, 2), blank)
    if key in _PG:
        return _PG[key]
    h = int(w * 1.6)
    im, d = _ss(w, h)
    s = SS
    d.rounded_rectangle([0, int(h * 0.04) * s, w * s - 1, h * s - 1], int(w * 0.16) * s, fill=dk(body, 0.7))
    d.rounded_rectangle([int(w * 0.03) * s, int(h * 0.04) * s, int(w * 0.97) * s, int(h * 0.975) * s], int(w * 0.15) * s, fill=body)
    d.rounded_rectangle([int(w * 0.08) * s, int(h * 0.07) * s, int(w * 0.25) * s, int(h * 0.55) * s], int(w * 0.05) * s, fill=lt(body, 0.35))
    # screen bezel + LCD
    sx0, sy0, sx1, sy1 = int(w * 0.12), int(h * 0.13), int(w * 0.88), int(h * 0.52)
    d.rounded_rectangle([sx0 * s, sy0 * s, sx1 * s, sy1 * s], int(w * 0.05) * s, fill=(40, 45, 50))
    lx0, ly0, lx1, ly1 = sx0 + int(w * 0.05), sy0 + int(w * 0.05), sx1 - int(w * 0.05), sy1 - int(w * 0.05)
    d.rectangle([lx0 * s, ly0 * s, lx1 * s, ly1 * s], fill=(170, 200, 140))
    # faint LCD dot rows (digits area) along the top
    for k in range(8):
        x = lx0 + 14 + k * (lx1 - lx0 - 28) / 8
        d.rectangle([x * s, (ly0 + 12) * s, (x + (lx1 - lx0) / 12) * s, (ly0 + 30) * s], fill=(150, 180, 125))
    out = _down(im)
    dd = ImageDraw.Draw(out)
    if not blank:
        cell = max(2, int((lx1 - lx0) * 0.55 / 12 * heart))
        hp = pixel_icon('heart', cell, (40, 50, 40))
        out.alpha_composite(hp, (int((lx0 + lx1) / 2 - hp.width / 2), int((ly0 + ly1) / 2 - hp.height / 2 + 14)))
    else:
        f = font(int(w * 0.09))
        dd.text(((lx0 + lx1) / 2 - f.getlength('- - -') / 2, (ly0 + ly1) / 2 - w * 0.05), '- - -', font=f, fill=(60, 70, 55))
    # buttons
    for k in range(3):
        bx = w * (0.22 + k * 0.28)
        dd.ellipse([bx - w * 0.09, h * 0.64, bx + w * 0.09, h * 0.64 + w * 0.13], fill=dk(body, 0.55))
        dd.ellipse([bx - w * 0.08, h * 0.635, bx + w * 0.08, h * 0.635 + w * 0.11], fill=(235, 235, 230))
    dd.rounded_rectangle([w * 0.3, h * 0.8, w * 0.7, h * 0.86], 10, fill=dk(body, 0.6))
    for k in range(5):
        dd.line([(w * 0.33, h * 0.885 + k * 9), (w * 0.67, h * 0.885 + k * 9)], fill=dk(body, 0.6), width=3)
    # little red light
    dd.ellipse([w * 0.8, h * 0.075, w * 0.86, h * 0.105], fill=(255, 70, 70))
    _PG[key] = out
    return out

def small_pager(w=150, body=(240, 120, 170), blank=False):
    return pager(w, body, 1.0, blank)

def heart_sp(r=40, col=(240, 70, 110)):
    im, d = _ss(r * 2.2, r * 2.2)
    heart_d(d, r * 1.1 * SS, r * 1.0 * SS, r * SS, col)
    d.ellipse([r * 0.45 * SS, r * 0.45 * SS, r * 0.75 * SS, r * 0.7 * SS], fill=lt(col, 0.6))
    return _down(im)

def hearts_burst(img, cx, cy, t, t0, n=9, spread=420, r=46):
    if t < t0:
        return
    u = t - t0
    for k in range(n):
        a = math.radians(-160 + 140 * k / max(1, n - 1))
        sp = spread * (0.7 + 0.3 * ((k * 5) % 3) / 2)
        k2 = ease_out(min(1, u / 0.8))
        x = cx + math.cos(a) * sp * k2
        y = cy + math.sin(a) * sp * k2 - 60 * u
        sc = (0.5 + 0.5 * ease_back(clamp01(u / 0.3), 2.0)) * (1.0 - 0.3 * clamp01(u - 1.2))
        put(img, heart_sp(r, [(240, 70, 110), (255, 120, 160), (230, 40, 80)][k % 3]), x, y, sc, 12 * math.sin(u * 4 + k))

def phone97(w=200, n_icons=6):
    """late-90s candy-bar phone with antenna and a little mono LCD of pixel icons"""
    h = int(w * 2.6)
    im, d = _ss(w, h + w * 0.5)
    s = SS
    top = int(w * 0.5)
    d.rounded_rectangle([w * 0.72 * s, 0, w * 0.86 * s, (top + 30) * s], int(w * 0.06) * s, fill=(60, 60, 70))
    d.rounded_rectangle([0, top * s, w * s - 1, (top + h) * s - 1], int(w * 0.2) * s, fill=(150, 155, 170))
    d.rounded_rectangle([w * 0.05 * s, (top + h * 0.02) * s, w * 0.95 * s, (top + h * 0.98) * s], int(w * 0.18) * s, fill=(185, 190, 205))
    d.rounded_rectangle([w * 0.12 * s, (top + h * 0.1) * s, w * 0.88 * s, (top + h * 0.42) * s], int(w * 0.06) * s, fill=(50, 55, 60))
    d.rectangle([w * 0.18 * s, (top + h * 0.13) * s, w * 0.82 * s, (top + h * 0.39) * s], fill=(165, 200, 150))
    out = _down(im)
    cw = int(w * 0.64 / 3 / 12)
    for k in range(min(n_icons, 6)):
        ic = pixel_icon(BM_KEYS[k], max(1, cw), (40, 50, 40))
        out.alpha_composite(ic, (int(w * 0.2 + (k % 3) * w * 0.205), int(top + h * 0.15 + (k // 3) * h * 0.11)))
    dd = ImageDraw.Draw(out)
    for r_ in range(4):
        for c_ in range(3):
            x = w * (0.22 + c_ * 0.28)
            y = top + h * (0.52 + r_ * 0.1)
            dd.rounded_rectangle([x - w * 0.1, y, x + w * 0.1, y + h * 0.06], 8, fill=(235, 235, 240), outline=(120, 120, 130), width=2)
    return out

def round_face(d, cx, cy, r, kind=0):
    """generic round yellow face (own simple design)"""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 205, 60), outline=(220, 150, 30), width=max(2, int(r * 0.06)))
    ink = (70, 45, 30)
    if kind == 0:   # big smile
        d.ellipse([cx - r * 0.42, cy - r * 0.38, cx - r * 0.18, cy - r * 0.02], fill=ink)
        d.ellipse([cx + r * 0.18, cy - r * 0.38, cx + r * 0.42, cy - r * 0.02], fill=ink)
        d.chord([cx - r * 0.55, cy - r * 0.1, cx + r * 0.55, cy + r * 0.62], 0, 180, fill=ink)
    elif kind == 1:  # heart eyes
        heart_d(d, cx - r * 0.32, cy - r * 0.2, r * 0.26, (235, 50, 80))
        heart_d(d, cx + r * 0.32, cy - r * 0.2, r * 0.26, (235, 50, 80))
        d.arc([cx - r * 0.45, cy - r * 0.1, cx + r * 0.45, cy + r * 0.55], 20, 160, fill=ink, width=max(2, int(r * 0.1)))
    elif kind == 2:  # wink
        d.ellipse([cx - r * 0.42, cy - r * 0.38, cx - r * 0.18, cy - r * 0.02], fill=ink)
        d.arc([cx + r * 0.15, cy - r * 0.3, cx + r * 0.45, cy], 200, 340, fill=ink, width=max(2, int(r * 0.1)))
        d.arc([cx - r * 0.45, cy - r * 0.1, cx + r * 0.45, cy + r * 0.55], 20, 160, fill=ink, width=max(2, int(r * 0.1)))
    else:            # surprised
        d.ellipse([cx - r * 0.4, cy - r * 0.38, cx - r * 0.2, cy - r * 0.08], fill=ink)
        d.ellipse([cx + r * 0.2, cy - r * 0.38, cx + r * 0.4, cy - r * 0.08], fill=ink)
        d.ellipse([cx - r * 0.16, cy + r * 0.15, cx + r * 0.16, cy + r * 0.5], fill=ink)

def smartphone(w=260):
    h = int(w * 2.0)
    im, d = _ss(w, h)
    s = SS
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], int(w * 0.16) * s, fill=(35, 35, 45))
    d.rounded_rectangle([w * 0.05 * s, w * 0.05 * s, w * 0.95 * s, (h - w * 0.05) * s], int(w * 0.13) * s, fill=(130, 190, 240))
    d.rounded_rectangle([w * 0.38 * s, w * 0.08 * s, w * 0.62 * s, w * 0.14 * s], 10 * s, fill=(35, 35, 45))
    r = w * 0.14
    for k in range(6):
        cx = w * (0.28 + (k % 2) * 0.44)
        cy = h * (0.25 + (k // 2) * 0.24)
        round_face(d, cx * s, cy * s, r * s, k % 4)
    return _down(im)

def envelope(w=130, col=(250, 248, 240), seal=(235, 60, 90)):
    h = int(w * 0.66)
    im, d = _ss(w, h)
    s = SS
    d.rectangle([0, 0, w * s - 1, h * s - 1], fill=col, outline=(170, 160, 150), width=3 * s)
    d.line([(0, 0), (w * s / 2, h * s * 0.55), (w * s, 0)], fill=(170, 160, 150), width=3 * s)
    heart_d(d, w * s / 2, h * s * 0.55, w * 0.1 * s, seal)
    return _down(im)

def dictionary(w=420, flip=0.0):
    """big open book seen from the front, a page mid-flip (flip 0..1)"""
    h = int(w * 0.7)
    im, d = _ss(w, h)
    s = SS
    d.rounded_rectangle([0, h * 0.06 * s, w * s - 1, h * s - 1], 12 * s, fill=(150, 40, 50))
    d.polygon([(w * 0.03 * s, h * 0.04 * s), (w * 0.5 * s, h * 0.1 * s), (w * 0.5 * s, h * 0.92 * s), (w * 0.03 * s, h * 0.88 * s)], fill=(250, 245, 230))
    d.polygon([(w * 0.97 * s, h * 0.04 * s), (w * 0.5 * s, h * 0.1 * s), (w * 0.5 * s, h * 0.92 * s), (w * 0.97 * s, h * 0.88 * s)], fill=(245, 238, 220))
    for k in range(9):
        y = h * (0.2 + k * 0.075)
        d.line([(w * 0.08 * s, y * s), (w * 0.44 * s, (y + h * 0.01) * s)], fill=(160, 150, 140), width=3 * s)
        d.line([(w * 0.56 * s, (y + h * 0.01) * s), (w * 0.92 * s, y * s)], fill=(160, 150, 140), width=3 * s)
    # flipping page
    x = w * (0.95 - 0.9 * flip)
    d.polygon([(w * 0.5 * s, h * 0.1 * s), (x * s, (h * 0.02 - 0.06 * h * math.sin(flip * math.pi)) * s),
               (x * s, (h * 0.86 - 0.06 * h * math.sin(flip * math.pi)) * s), (w * 0.5 * s, h * 0.92 * s)], fill=(255, 252, 242), outline=(200, 190, 175))
    return _down(im)

def crt(w=700, content=None):
    """chunky beige late-90s monitor; content = RGBA image pasted into the screen"""
    h = int(w * 0.86)
    im, d = _ss(w, h + int(w * 0.2))
    s = SS
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], int(w * 0.05) * s, fill=(215, 208, 190), outline=(160, 150, 130), width=4 * s)
    d.rounded_rectangle([w * 0.07 * s, w * 0.06 * s, w * 0.93 * s, h * 0.82 * s], int(w * 0.04) * s, fill=(45, 50, 55))
    d.rectangle([w * 0.1 * s, w * 0.09 * s, w * 0.9 * s, h * 0.79 * s], fill=(235, 240, 245))
    d.polygon([(w * 0.3 * s, h * s), (w * 0.7 * s, h * s), (w * 0.78 * s, (h + w * 0.18) * s), (w * 0.22 * s, (h + w * 0.18) * s)], fill=(190, 182, 165))
    d.ellipse([w * 0.84 * s, h * 0.87 * s, w * 0.88 * s, h * 0.92 * s], fill=(90, 220, 110))
    for k in range(4):
        d.line([(w * (0.1 + k * 0.04) * s, h * 0.9 * s), (w * (0.12 + k * 0.04) * s, h * 0.9 * s)], fill=(160, 150, 130), width=4 * s)
    out = _down(im)
    if content is not None:
        sw, sh_ = int(w * 0.8), int(h * 0.79 - w * 0.09)
        c = content.resize((sw, sh_), Image.NEAREST) if content.size != (sw, sh_) else content
        out.alpha_composite(c, (int(w * 0.1), int(w * 0.09)))
    return out

def screen_content(w, h, mode, n=None, t=0.0):
    """what the designer's monitor shows. mode 'draw' = big grid heart being drawn, 'set' = many tiny icons"""
    im = Image.new('RGBA', (w, h), (235, 240, 245, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 26], fill=(40, 80, 160))
    for k in range(3):
        d.rectangle([w - 26 - k * 26, 5, w - 8 - k * 26, 21], fill=(200, 200, 210))
    if mode == 'draw':
        cell = int(min(w, h - 40) * 0.85 / 12)
        ic = pixel_icon('heart', cell, (220, 40, 70), n=n, bg=(255, 255, 255, 255), grid=(170, 175, 185))
        im.alpha_composite(ic, ((w - ic.width) // 2, 26 + (h - 26 - ic.height) // 2))
    else:
        cols, rows = 16, 11
        cw = (w - 20) / cols
        ch = (h - 40) / rows
        cell = max(1, int(min(cw, ch) * 0.8 / 12))
        shown = n if n is not None else cols * rows
        for k in range(min(shown, cols * rows)):
            c_, r_ = k % cols, k // cols
            kind = BM_KEYS[(k * 7 + r_) % len(BM_KEYS)]
            ic = pixel_icon(kind, cell, ICOL[BM_KEYS.index(kind)])
            im.alpha_composite(ic, (int(10 + c_ * cw + (cw - ic.width) / 2), int(32 + r_ * ch + (ch - ic.height) / 2)))
    return im

def icon_panel(w=520, h=360, frame=(60, 45, 35)):
    """a framed museum panel: grid of tiny pixel icons on white"""
    im = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w + 59, h + 59], fill=frame)
    d.rectangle([22, 22, w + 37, h + 37], fill=(250, 250, 248))
    cols, rows = 13, 9
    cw, ch = (w - 40) / cols, (h - 40) / rows
    cell = max(1, int(min(cw, ch) * 0.85 / 12))
    for k in range(cols * rows):
        c_, r_ = k % cols, k // cols
        kind = BM_KEYS[(k * 5 + r_ * 3) % len(BM_KEYS)]
        ic = pixel_icon(kind, cell, ICOL[BM_KEYS.index(kind)])
        im.alpha_composite(ic, (int(42 + c_ * cw), int(42 + r_ * ch)))
    return im

def scroll(w=300, h=760, glyph='絵', painting=False, u=1.0):
    """hanging scroll; u = how far unrolled (0..1)"""
    hh = max(40, int(h * u))
    im, d = _ss(w, hh + 60)
    s = SS
    d.rectangle([w * 0.08 * s, 30 * s, w * 0.92 * s, (hh + 30) * s], fill=(120, 150, 120))
    d.rectangle([w * 0.16 * s, 50 * s, w * 0.84 * s, (hh + 10) * s], fill=(250, 244, 225))
    d.rounded_rectangle([0, 18 * s, w * s - 1, 42 * s], 10 * s, fill=(110, 70, 40))
    d.rounded_rectangle([0, (hh + 22) * s, w * s - 1, (hh + 48) * s], 10 * s, fill=(110, 70, 40))
    d.line([(w * 0.3 * s, 18 * s), (w * 0.5 * s, 0), (w * 0.7 * s, 18 * s)], fill=(80, 60, 40), width=4 * s)
    out = _down(im)
    if u > 0.55:
        layer = Image.new('RGBA', (w, h + 60), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        f = ImageFont_cjk(int(w * (0.5 if len(glyph) == 1 else 0.42)))
        if len(glyph) == 1:
            gw = f.getlength(glyph)
            ld.text(((w - gw) / 2, 90), glyph, font=f, fill=(25, 20, 20))
        else:
            for k, g in enumerate(glyph):
                gw = f.getlength(g)
                ld.text(((w - gw) / 2, 80 + k * int(w * 0.5)), g, font=f, fill=(25, 20, 20))
        if painting:
            px0, py0, px1, py1 = w * 0.22, h * 0.5, w * 0.78, h * 0.85
            ld.rectangle([px0, py0, px1, py1], fill=(225, 235, 240))
            ld.polygon([(px0, py1), (px0 + (px1 - px0) * 0.35, py0 + 40), (px0 + (px1 - px0) * 0.6, py1 - 50), (px0 + (px1 - px0) * 0.8, py0 + 80), (px1, py1)], fill=(90, 110, 140))
            ld.ellipse([px1 - 70, py0 + 15, px1 - 30, py0 + 55], fill=(230, 80, 60))
        out.alpha_composite(layer.crop((0, 0, w, hh + 60)))
    return out

from PIL import ImageFont
_CJK = {}
def ImageFont_cjk(size):
    if size not in _CJK:
        _CJK[size] = ImageFont.truetype(FONT_CJK, size)
    return _CJK[size]

def brush(L=300):
    im, d = _ss(40, L)
    s = SS
    d.rectangle([12 * s, 0, 28 * s, L * 0.75 * s], fill=(150, 100, 50))
    d.polygon([(8 * s, L * 0.75 * s), (32 * s, L * 0.75 * s), (20 * s, L * s)], fill=(30, 25, 25))
    return _down(im)

def marker(L=170, col=(40, 40, 45)):
    im, d = _ss(34, L)
    s = SS
    d.rounded_rectangle([4 * s, 0, 30 * s, L * 0.8 * s], 6 * s, fill=(240, 240, 240), outline=(120, 120, 120), width=2 * s)
    d.rectangle([4 * s, L * 0.55 * s, 30 * s, L * 0.8 * s], fill=col)
    d.polygon([(8 * s, L * 0.8 * s), (26 * s, L * 0.8 * s), (17 * s, L * s)], fill=col)
    return _down(im)

# ================================================================ EMOJI plates
@cached
def classroom_plate():
    im = Image.new('RGBA', (PW, PH), (238, 228, 200))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 1560], fill=(236, 226, 198))
    d.rectangle([0, 1180, PW, 1560], fill=(160, 190, 170))
    d.line([(0, 1180), (PW, 1180)], fill=(120, 150, 130), width=10)
    # whiteboard
    d.rectangle([90, 400, 1206, 1080], fill=(170, 175, 185))
    d.rectangle([110, 420, 1186, 1060], fill=(252, 253, 255))
    d.rectangle([90, 1080, 1206, 1110], fill=(150, 155, 165))
    for k, c in enumerate([(220, 50, 50), (40, 90, 200), (40, 150, 80)]):
        d.rounded_rectangle([700 + k * 70, 1060, 750 + k * 70, 1080], 6, fill=c)
    # clock-free wall details: flag-less pennant string + poster
    for k in range(10):
        x = 60 + k * 125
        d.polygon([(x, 180), (x + 110, 180), (x + 55, 270)], fill=[(240, 120, 150), (120, 190, 240), (250, 210, 90)][k % 3])
    d.line([(40, 180), (PW - 40, 180)], fill=(120, 100, 90), width=4)
    d.rectangle([1000, 260, 1200, 360], fill=(250, 250, 250), outline=(200, 190, 170), width=4)
    for k in range(4):
        d.rectangle([1020 + k * 45, 280, 1050 + k * 45, 340], fill=[(240, 90, 90), (90, 170, 240), (250, 200, 70), (120, 200, 120)][k])
    wood_floor(d, 1560, (190, 150, 110))
    return finish_plate(im, 0.35, 31)

def school_desk(img, cx, y, w=520):
    d = ImageDraw.Draw(img)
    floor_shadow(img, cx, y + 260, w * 0.6, 0.3)
    d.polygon([(cx - w / 2, y), (cx + w / 2, y), (cx + w / 2 + 30, y + 50), (cx - w / 2 - 30, y + 50)], fill=(225, 185, 130))
    d.rectangle([cx - w / 2 - 30, y + 50, cx + w / 2 + 30, y + 80], fill=(180, 140, 95))
    for x in (cx - w / 2, cx + w / 2 - 20):
        d.rectangle([x, y + 80, x + 20, y + 300], fill=(120, 120, 130))
    d.rectangle([cx - 120, y - 12, cx + 40, y + 6], fill=(250, 250, 250), outline=(180, 180, 190))
    d.rectangle([cx + 80, y - 30, cx + 200, y + 4], fill=(90, 140, 220))

@cached
def tokyo_plate():
    arr = vgrad(PW, PH, [(0, '#3B2C6B'), (0.3, '#E7768A'), (0.5, '#F6B27A'), (1, '#F6B27A')])
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    # far buildings
    x = -40
    while x < PW:
        bw = rng.integers(120, 220)
        bh = rng.integers(500, 1000)
        d.rectangle([x, 1450 - bh, x + bw, 1450], fill=(70, 60, 110))
        for wy in range(1450 - bh + 30, 1430, 50):
            for wx in range(x + 18, x + bw - 20, 40):
                if rng.random() < 0.55:
                    d.rectangle([wx, wy, wx + 18, wy + 24], fill=(255, 225, 150))
        x += bw + 10
    # near buildings with vertical glowing signs (no text)
    for (bx, bw, top, col) in ((0, 300, 520, (120, 80, 120)), (980, 316, 440, (90, 70, 130))):
        d.rectangle([bx, top, bx + bw, 1500], fill=col)
        for k in range(5):
            sy = top + 60 + k * 170
            sc = [(255, 90, 140), (90, 220, 255), (255, 210, 80), (140, 255, 160), (255, 140, 60)][k]
            sx = bx + bw - 80 if bx == 0 else bx + 20
            d.rounded_rectangle([sx, sy, sx + 60, sy + 140], 10, fill=sc, outline=(255, 255, 255), width=4)
            for j in range(3):
                d.rectangle([sx + 18, sy + 18 + j * 40, sx + 42, sy + 40 + j * 40], fill=lt(sc, 0.6))
    # vending machine
    d.rectangle([340, 1080, 560, 1500], fill=(230, 60, 70))
    d.rectangle([360, 1100, 540, 1300], fill=(220, 235, 245))
    for r_ in range(3):
        for c_ in range(4):
            d.rounded_rectangle([372 + c_ * 42, 1112 + r_ * 62, 400 + c_ * 42, 1160 + r_ * 62], 6, fill=[(90, 160, 230), (250, 200, 60), (120, 200, 120), (240, 120, 160)][c_])
    d.rectangle([380, 1400, 520, 1450], fill=(60, 30, 35))
    # street lamp
    d.rectangle([880, 820, 900, 1500], fill=(60, 60, 70))
    d.ellipse([850, 790, 930, 850], fill=(255, 240, 190))
    # sidewalk + crosswalk
    d.rectangle([0, 1500, PW, PH], fill=(120, 115, 130))
    d.rectangle([0, 1500, PW, 1540], fill=(170, 165, 175))
    for k in range(7):
        y0 = 1620 + k * 95
        d.polygon([(100 - k * 20, y0), (PW - 100 + k * 20, y0), (PW - 90 + k * 22, y0 + 50), (90 - k * 22, y0 + 50)], fill=(235, 235, 240))
    return finish_plate(im, 0.35, 32)

@cached
def designer_plate():
    im = Image.new('RGBA', (PW, PH), (70, 80, 110))
    d = ImageDraw.Draw(im)
    for x in range(0, PW, 110):
        d.rectangle([x, 0, x + 55, 1500], fill=(76, 86, 116))
    window(d, 90, 220, 540, 700, 'city', (210, 210, 220))
    d.rectangle([110, 240, 520, 680], fill=None)
    # shelf with binders and floppy disks
    d.rectangle([700, 420, 1240, 440], fill=(150, 105, 65))
    for k in range(9):
        d.rectangle([720 + k * 55, 250, 765 + k * 55, 420], fill=[(220, 80, 80), (80, 140, 220), (240, 200, 80), (90, 180, 120)][k % 4], outline=(40, 40, 50), width=3)
    d.rectangle([700, 700, 1240, 720], fill=(150, 105, 65))
    for k in range(6):
        d.rectangle([730 + k * 80, 620, 790 + k * 80, 700], fill=[(40, 40, 50), (60, 90, 160), (160, 50, 60)][k % 3])
        d.rectangle([745 + k * 80, 625, 775 + k * 80, 650], fill=(200, 200, 210))
    # cork board with paper sketches of tiny icons
    d.rectangle([140, 800, 560, 1120], fill=(190, 140, 90), outline=(120, 85, 50), width=10)
    for k in range(5):
        x, y = 170 + (k % 3) * 125, 830 + (k // 3) * 140
        d.rectangle([x, y, x + 100, y + 110], fill=(250, 250, 245))
        ic = pixel_icon(BM_KEYS[k + 1], 6, (60, 60, 70))
        im.alpha_composite(ic, (x + 14, y + 18))
        d.ellipse([x + 44, y - 6, x + 56, y + 6], fill=(220, 40, 40))
    d.rectangle([0, 1560, PW, PH], fill=(90, 85, 95))
    for k in range(-6, 7):
        d.line([(CX + k * 90, 1560), (CX + k * 320, PH)], fill=(80, 75, 85), width=4)
    return finish_plate(im, 0.45, 33)

def desk_front(img, y, top=(200, 160, 115), front=(150, 110, 75)):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, y + 50], fill=top)
    d.line([(-20, y), (PW + 20, y)], fill=lt(top, 0.3), width=6)
    d.rectangle([-20, y + 50, PW + 20, PH], fill=front)
    for x in (60, 700):
        d.rectangle([x, y + 90, x + 520, y + 230], outline=dk(front, 0.8), width=6)
        d.rounded_rectangle([x + 230, y + 150, x + 290, y + 166], 6, fill=(210, 200, 180))

@cached
def museum_plate():
    im = Image.new('RGBA', (PW, PH), (240, 238, 232))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 160], fill=(225, 222, 215))
    for x in range(100, PW, 360):
        d.rectangle([x, 140, x + 160, 165], fill=(70, 70, 75))
    d.rectangle([0, 1480, PW, 1510], fill=(200, 195, 185))
    # spotlight cones
    for cx in (CX, 140, PW - 140):
        cone = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
        ImageDraw.Draw(cone).polygon([(cx - 40, 165), (cx + 40, 165), (cx + 380, 1480), (cx - 380, 1480)], fill=(255, 248, 220, 70))
        cone = cone.filter(ImageFilter.GaussianBlur(30))
        im.alpha_composite(cone)
    # side frames (abstract paintings)
    d.rectangle([-60, 560, 230, 980], fill=(60, 45, 35))
    d.rectangle([-40, 580, 210, 960], fill=(90, 160, 200))
    d.ellipse([20, 640, 170, 790], fill=(240, 200, 70))
    d.rectangle([PW - 230, 600, PW + 60, 940], fill=(60, 45, 35))
    d.rectangle([PW - 210, 620, PW + 40, 920], fill=(230, 110, 90))
    d.rectangle([PW - 170, 700, PW - 60, 860], fill=(250, 230, 200))
    # label plaque under the centre panel
    d.rectangle([CX - 80, 1060, CX + 80, 1130], fill=(250, 250, 250), outline=(180, 175, 170), width=3)
    for k in range(3):
        d.line([(CX - 60, 1078 + k * 18), (CX + 60 - k * 30, 1078 + k * 18)], fill=(150, 150, 150), width=5)
    # wood floor + bench + rope posts
    wood_floor(d, 1510, (170, 130, 95))
    return finish_plate(im, 0.3, 34)

def museum_front(img, y=1700):
    d = ImageDraw.Draw(img)
    for x in (140, PW - 140):
        floor_shadow(img, x, y + 10, 80, 0.3)
        d.rectangle([x - 10, y - 260, x + 10, y], fill=(200, 170, 60))
        d.ellipse([x - 26, y - 290, x + 26, y - 240], fill=(220, 190, 70))
        d.ellipse([x - 50, y - 16, x + 50, y + 10], fill=(200, 170, 60))
    d.arc([140, y - 400, PW - 140, y - 120], 20, 160, fill=(170, 30, 50), width=18)

@cached
def stage_plate():
    im = Image.new('RGBA', (PW, PH), (110, 20, 40))
    d = ImageDraw.Draw(im)
    for x in range(0, PW, 90):
        d.rectangle([x, 0, x + 45, 1520], fill=(135, 30, 55))
        d.line([(x + 44, 0), (x + 44, 1520)], fill=(90, 15, 35), width=6)
    d.rectangle([0, 0, PW, 170], fill=(160, 35, 60))
    for x in range(0, PW, 130):
        d.chord([x - 10, 110, x + 140, 240], 0, 180, fill=(160, 35, 60))
    d.rectangle([0, 0, PW, 30], fill=(220, 180, 70))
    # string lights
    for k in range(16):
        x = 40 + k * 80
        y = 300 + 40 * math.sin(k * 0.8)
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=[(255, 230, 120), (255, 140, 180), (150, 220, 255)][k % 3])
    d.rectangle([0, 1520, PW, PH], fill=(80, 60, 70))
    d.rectangle([0, 1520, PW, 1560], fill=(60, 45, 55))
    for k in range(-6, 7):
        d.line([(CX + k * 90, 1560), (CX + k * 320, PH)], fill=(70, 52, 62), width=4)
    sp = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    ImageDraw.Draw(sp).ellipse([CX - 600, 1500, CX + 600, 2000], fill=(255, 240, 200, 70))
    im.alpha_composite(sp.filter(ImageFilter.GaussianBlur(40)))
    return finish_plate(im, 0.5, 35)

def podium(img, y=1720):
    d = ImageDraw.Draw(img)
    blocks = [(CX - 560, CX - 200, 380, '2', (190, 195, 205)), (CX - 200, CX + 200, 560, '1', (245, 200, 70)), (CX + 200, CX + 560, 260, '3', (215, 140, 80))]
    floor_shadow(img, CX, y + 20, 800, 0.35)
    for x0, x1, hgt, lab, c in blocks:
        d.rectangle([x0, y - hgt, x1, y], fill=c, outline=dk(c, 0.7), width=6)
        d.rectangle([x0, y - hgt, x1, y - hgt + 30], fill=lt(c, 0.35))
        f = font(150)
        d.text(((x0 + x1) / 2 - f.getlength(lab) / 2, y - hgt + 60), lab, font=f, fill=(255, 255, 255), stroke_width=6, stroke_fill=dk(c, 0.6))
    return {'1': (CX, y - 560), '2': (CX - 380, y - 380), '3': (CX + 380, y - 260)}

@cached
def phoneshop_plate():
    im = Image.new('RGBA', (PW, PH), (225, 235, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 140], fill=(40, 120, 200))
    for x in range(30, PW, 200):
        d.rectangle([x, 40, x + 140, 100], fill=(250, 250, 255))
    # wall of display shelves holding generic phones
    for sy in (430, 760, 1090):
        d.rectangle([60, sy, PW - 60, sy + 24], fill=(250, 250, 250), outline=(170, 180, 190), width=3)
        for k in range(8):
            x = 110 + k * 140
            c = [(60, 60, 70), (200, 60, 80), (70, 130, 220), (230, 230, 235)][(k + sy // 330) % 4]
            d.rounded_rectangle([x, sy - 200, x + 80, sy - 10], 14, fill=c, outline=(40, 40, 50), width=3)
            d.rounded_rectangle([x + 10, sy - 185, x + 70, sy - 70], 6, fill=(150, 200, 235))
            d.rectangle([x + 20, sy + 4, x + 60, sy + 20], fill=(255, 220, 80))
    d.rectangle([0, 1500, PW, PH], fill=(200, 205, 215))
    for k in range(-6, 7):
        d.line([(CX + k * 90, 1500), (CX + k * 320, PH)], fill=(185, 190, 200), width=4)
    return finish_plate(im, 0.3, 36)

def glass_counter(img, y=1620):
    d = ImageDraw.Draw(img)
    d.rectangle([-20, y, PW + 20, y + 40], fill=(245, 248, 250))
    ov = Image.new('RGBA', (PW + 40, PH - y), (170, 210, 230, 120))
    paste_at(img, ov, -20, y + 40)
    d.line([(-20, y + 40), (PW + 20, y + 40)], fill=(255, 255, 255), width=6)
    for k in range(6):
        x = 80 + k * 210
        d.rounded_rectangle([x, y + 140, x + 90, y + 320], 14, fill=[(60, 60, 70), (230, 230, 235), (200, 60, 80)][k % 3])

@cached
def tatami_plate():
    im = Image.new('RGBA', (PW, PH), (235, 220, 185))
    d = ImageDraw.Draw(im)
    # shoji screens
    d.rectangle([0, 0, PW, 1460], fill=(110, 80, 50))
    for x0 in range(20, PW, 324):
        d.rectangle([x0, 60, x0 + 300, 1440], fill=(250, 245, 230))
        for gx in range(x0, x0 + 301, 75):
            d.line([(gx, 60), (gx, 1440)], fill=(140, 105, 70), width=8)
        for gy in range(60, 1441, 115):
            d.line([(x0, gy), (x0 + 300, gy)], fill=(140, 105, 70), width=8)
    d.rectangle([0, 1440, PW, 1480], fill=(100, 70, 45))
    # tatami floor
    d.rectangle([0, 1480, PW, PH], fill=(200, 195, 130))
    for k in range(-5, 6):
        d.line([(CX + k * 130, 1480), (CX + k * 420, PH)], fill=(170, 165, 105), width=4)
    d.line([(0, 1800), (PW, 1800)], fill=(60, 70, 50), width=14)
    return finish_plate(im, 0.35, 37)

def low_table(img, cx, y, w=640):
    d = ImageDraw.Draw(img)
    floor_shadow(img, cx, y + 140, w * 0.6, 0.3)
    d.polygon([(cx - w / 2, y), (cx + w / 2, y), (cx + w / 2 + 40, y + 60), (cx - w / 2 - 40, y + 60)], fill=(130, 60, 40))
    d.rectangle([cx - w / 2 - 40, y + 60, cx + w / 2 + 40, y + 90], fill=(95, 40, 25))
    for x in (cx - w / 2 - 10, cx + w / 2 - 10):
        d.rectangle([x, y + 90, x + 30, y + 160], fill=(95, 40, 25))
    d.rectangle([cx - 200, y + 8, cx + 40, y + 40], fill=(250, 248, 240))
    d.rounded_rectangle([cx + 90, y + 6, cx + 190, y + 40], 8, fill=(40, 40, 45))

# ================================================================ characters (same person = same look)
GIRL = dict(PRESETS['girl'], top=(240, 110, 160))
BFF = dict(PRESETS['boy'], top=(90, 170, 230), hat=None, hair='messy', hair_color=(60, 40, 30))
JP1 = dict(PRESETS['girl'], skin='light', hair='long', hair_color=(30, 25, 30), top=(250, 200, 70), bottom=(70, 70, 110))
JP2 = dict(PRESETS['girl'], skin='light', hair='ponytail', hair_color=(35, 25, 25), top=(120, 210, 190), bottom=(200, 80, 110))
EXEC2 = dict(PRESETS['boss'], skin='light', hair='side', hair_color=(30, 25, 25), top=(50, 60, 90), tie=(200, 60, 70))
KURITA = dict(PRESETS['boss'], skin='light', hair='short', hair_color=(30, 25, 25), top=(235, 235, 240), bottom=(60, 65, 85), tie=None, glasses=True)
GRAN = dict(PRESETS['grandma'])
CLERK = dict(PRESETS['salesman'], hat=None, top=(40, 120, 200), tie=(250, 200, 60))
TEACH = dict(PRESETS['grandma'], hair_color=(60, 50, 50), glasses=False, top=(120, 60, 80))

# ================================================================ scenes
def wx(sc, word, which='t0', nth=0):
    """exact (case-insensitive, punctuation stripped) word match"""
    k = 0
    for w in sc.words:
        if w['w'].strip(',.:;?!').lower() == word.lower():
            if k == nth:
                return w[which]
            k += 1
    raise KeyError(word)

PAGER_BODY = (70, 190, 200)

def giant_pager(img, t, cx=470, bottom=1700, w=600, t_heart=None, blank=False):
    pulse = 1.0
    if t_heart is not None and t >= t_heart:
        u = t - t_heart
        pulse = 1.0 + 0.35 * math.sin(min(u, 0.5) / 0.5 * math.pi) + 0.06 * math.sin(u * 9) * (u > 0.5)
    sp = pager(w, PAGER_BODY, round(pulse, 2), blank)
    floor_shadow(img, cx, bottom + 10, w * 0.55, 0.4)
    rot = 2.5 * math.sin(t * 3.2)
    cy = bottom - sp.height / 2 - 18 * abs(math.sin(t * 6.4)) * (t < 0.9)
    put(img, sp, cx, cy, 1.0, rot)
    return cx, cy - sp.height * 0.175   # LCD centre

def bedroom_scene(img, t, girl_expr, arm_l, arm_r, talk=False, t_heart=None):
    sx, sy = giant_pager(img, t, t_heart=t_heart)
    P(img, GIRL, 1010, 1990, t, girl_expr, talk=talk, arm_l=arm_l, arm_r=arm_r, scale=1.0, look_dir=-1)
    if t_heart is not None:
        hearts_burst(img, sx, sy, t, t_heart, n=9, spread=430, r=50)
    return sx, sy

# 0  Emoji took off because teens loved one tiny heart.
class E0(Sc):
    def events(self):
        return [(0.02, 'bigpop', 0.45), (self.we('teens') - 0.04, 'pop', 0.35), (self.we('one') - 0.05, 'chime', 0.5)]
    def shots(self):
        return [(0.0, 1.08, 1.12, CX, 1160), (self.we('teens'), 1.2, 1.24, CX + 20, 1220), (self.we('tiny') - 0.1, 1.32, 1.4, 500, 1150)]
    def plate(self):
        return bedroom_plate()
    def dyn(self, img, t):
        tn = self.we('teens')
        hh = self.we('tiny') - 0.1
        if t < tn:
            e, al, ar = 'shocked', 150 + 8 * math.sin(t * 9), 150 + 8 * math.sin(t * 8)
        elif t < hh:
            e, al, ar = 'happy', 120 + 20 * math.sin(t * 8), 30
        else:
            e, al, ar = 'happy', 160, 160
        bedroom_scene(img, t, e, al, ar, t_heart=hh)

# 1  And the word emoji has nothing to do with emotion.
class E1(Sc):
    def events(self):
        return [(0.05, 'squeak', 0.45), (self.we('has') - 0.05, 'squeak', 0.4), (self.we('nothing') - 0.03, 'buzzer', 0.4)]
    def shots(self):
        return [(0.0, 1.05, 1.1, CX, 1100), (self.we('has'), 1.2, 1.25, CX + 120, 1000), (self.we('nothing'), 1.1, 1.14, CX, 1150)]
    def plate(self):
        return classroom_plate()
    def reveal(self, img, txt, x, y, u, col=(40, 70, 170), size=130):
        if u <= 0:
            return None
        f = font(size, FONT_BOLD)
        w = int(f.getlength(txt)) + 20
        ti = Image.new('RGBA', (w, size + 60), (0, 0, 0, 0))
        ImageDraw.Draw(ti).text((10, 0), txt, font=f, fill=col)
        ti = ti.crop((0, 0, max(1, int(w * clamp01(u))), size + 60))
        paste_at(img, ti, int(x), int(y))
        return (x + w * clamp01(u), y + size * 0.7)
    def dyn(self, img, t):
        tw, th, tn = self.we('word'), self.we('has'), self.we('nothing')
        p1 = self.reveal(img, 'emoji', 150, 600, (t - tw + 0.2) / 0.45, size=120)
        p2 = self.reveal(img, 'emotion', 700, 600, (t - th) / 0.55, (200, 60, 90), size=120)
        d = ImageDraw.Draw(img)
        if t >= tn:
            u = clamp01((t - tn) / 0.25)
            cx, cy = 600, 690
            L = 75 * ease_back(u, 2)
            d.line([(cx - L, cy - 30), (cx + L, cy - 30)], fill=(220, 30, 40), width=22)
            d.line([(cx - L, cy + 30), (cx + L, cy + 30)], fill=(220, 30, 40), width=22)
            d.line([(cx + L * 0.6, cy - 95), (cx - L * 0.6, cy + 95)], fill=(220, 30, 40), width=22)
        # girl writing on the board
        writing = t < tn
        a = P(img, GIRL, 1060, 1960, t, 'happy' if writing else 'proud', arm_l=125 + 12 * math.sin(t * 14) * writing, arm_r=20 if writing else 60,
              scale=0.95, look_dir=-1)
        hold(img, marker(150, (40, 70, 170) if t < th else (200, 60, 90)), a, 'hand_l', 0, -40, -30 + 10 * math.sin(t * 14) * writing)
        P(img, BFF, 300, 2090, t, 'shocked' if t >= tn else 'smile', arm_l=150 if t >= tn else 20, arm_r=150 if t >= tn else 100, scale=0.95, phase=2, look_dir=1)
        school_desk(img, 360, 1740, 560)

# 2  So what does it actually mean?
class E2(Sc):
    def events(self):
        return [(0.05, 'rustle', 0.5), (self.we('actually') - 0.05, 'rustle', 0.45)]
    def shots(self):
        return [(0.0, 1.05, 1.1, CX, 1150), (self.we('actually'), 1.18, 1.24, CX - 60, 1250)]
    def plate(self):
        return living_plate()
    def dyn(self, img, t):
        P(img, BFF, 1020, 1960, t, 'think', arm_l=120 + 8 * math.sin(t * 6), arm_r=120 - 8 * math.sin(t * 6), scale=0.92, phase=1.3, look_dir=-1)
        a = P(img, GIRL, 450, 1990, t, 'think', arm_l=45, arm_r=45, scale=1.0, look_dir=1)
        fl = (t * 2.2) % 1
        bk = dictionary(520, fl)
        mx = (a['hand_l'][0] + a['hand_r'][0]) / 2
        my = (a['hand_l'][1] + a['hand_r'][1]) / 2
        put(img, bk, mx, my - 30, 1.0, 4 * math.sin(t * 3))

# 3  In the nineties, a Japanese pager let you send a little heart, and teens were obsessed.
class E3(Sc):
    def events(self):
        return [(0.05, 'swipe', 0.3), (self.we('pager') - 0.03, 'tick', 0.5), (self.we('send') + 0.1, 'bloop', 0.5),
                (self.we('obsessed') - 0.25, 'party', 0.35)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1150), (self.we('pager') - 0.05, 1.25, 1.3, 380, 1050), (self.we('send'), 1.05, 1.08, CX, 1120),
                (self.we('teens'), 1.15, 1.2, CX, 1200)]
    def plate(self):
        return tokyo_plate()
    def dyn(self, img, t):
        sd, ob = self.we('send') + 0.1, self.we('teens')
        crazy = t >= ob
        a1 = P(img, JP1, 290, 1950, t, 'happy' if t < ob else 'happy', talk=talk_frame(t) and sd - 0.6 < t < sd + 0.3,
               arm_l=20 if not crazy else 150, arm_r=140 + (8 * math.sin(t * 12) if crazy else 0), scale=0.95, look_dir=1)
        a2 = P(img, JP2, 1010, 1950, t, 'shocked' if sd + 0.7 < t < ob else ('happy' if crazy else 'smile'),
               arm_l=140 + (8 * math.sin(t * 11) if crazy else 0), arm_r=20 if not crazy else 150, scale=0.95, phase=2, look_dir=-1)
        p1 = (a1['hand_r'][0] + 10, a1['hand_r'][1] - 80)
        p2 = (a2['hand_l'][0] - 10, a2['hand_l'][1] - 80)
        put(img, pager(170, (240, 120, 170), 1.0, False), p1[0], p1[1], 1.0, -8)
        got = t >= sd + 0.7
        put(img, pager(170, (120, 160, 240), 1.0, not got), p2[0], p2[1], 1.0, 8)
        # heart flies across (and keeps flying back and forth once they're hooked)
        trips = [sd] + ([ob + k * 0.55 for k in range(6)] if crazy else [])
        for k, s0 in enumerate(trips):
            u = (t - s0) / 0.7
            if 0 <= u <= 1:
                a, b = (p1, p2) if k % 2 == 0 else (p2, p1)
                x = a[0] + (b[0] - a[0]) * ease_in_out(u)
                y = a[1] + (b[1] - a[1]) * u - 380 * math.sin(u * math.pi)
                put(img, heart_sp(46), x, y - 60, 1.0 + 0.3 * math.sin(u * math.pi))
        if crazy:
            hearts_burst(img, CX, 1000, t, ob, n=11, spread=520, r=40)

# 4  As the story goes, when a new model dropped it, people were so upset the company noticed.
class E4(Sc):
    def events(self):
        e = [(0.05, 'pop', 0.35), (self.we('dropped') - 0.03, 'buzzer', 0.45)]
        up = self.we('upset')
        e += [(up - 0.2 + k * 0.18, 'rustle', 0.35) for k in range(5)]
        e += [(self.we('company') - 0.05, 'thud', 0.4)]
        return e
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1150), (self.we('model'), 1.3, 1.35, 840, 1300), (self.we('people'), 1.05, 1.1, CX, 1150),
                (self.we('company'), 1.18, 1.24, CX - 40, 1150)]
    def plate(self):
        return office_plate()
    def dyn(self, img, t):
        dr, up, co = self.we('dropped'), self.we('people'), self.we('company')
        ex = 'smile' if t < dr else ('nervous' if t < co else 'shocked')
        a = P(img, EXEC2, 560, 1840, t, ex, arm_l=20 if t < co else 150, arm_r=60 + 10 * math.sin(t * 5) if t < co else 150, scale=0.95)
        if t >= up:
            P(img, JP2, 1060, 1960, t, 'angry', talk=talk_frame(t), arm_l=150 + 10 * math.sin(t * 10), arm_r=30, scale=0.9, phase=1, look_dir=-1)
        desk_front(img, 1500)
        # the new pager on the desk: the heart is gone
        put(img, pager(230, (150, 110, 210), 1.0, t >= dr), 860, 1500 - 175)
        floor_shadow(img, 860, 1510, 150, 0.3)
        if t >= dr:
            u = clamp01((t - dr) / 0.25)
            d = ImageDraw.Draw(img)
            cx, cy = 860, 1500 - 175 - 60
            r = 70 * ease_back(u, 2)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(230, 30, 40), width=14)
            d.line([(cx - r * 0.7, cy + r * 0.7), (cx + r * 0.7, cy - r * 0.7)], fill=(230, 30, 40), width=14)
        # angry letters pile up
        if t >= up - 0.2:
            n = int((t - up + 0.2) / 0.09)
            for k in range(min(n, 40)):
                s0 = up - 0.2 + k * 0.09
                u = clamp01((t - s0) / 0.45)
                tx = (90 + (k * 137) % 220) if k % 2 else (930 + (k * 137) % 230)
                ty = 1460 - (k // 8) * 22 - ((k * 31) % 30)
                y = -100 + (ty + 100) * ease_in_out(u)
                put(img, envelope(130), tx, y, 1.0, ((k * 47) % 50) - 25 + (1 - u) * 90)

# 5  So in 1999, a designer named Shigetaka Kurita drew 176 tiny pictures for phones, each just 12 by 12 pixels.
class E5(Sc):
    def events(self):
        e = [(0.05, 'swipe', 0.3), (self.we('designer') - 0.03, 'pop', 0.35)]
        dr = self.we('drew')
        e += [(dr + k * 0.12, 'tick', 0.35) for k in range(6)]
        e += [(self.we('176') - 0.03, 'bigpop', 0.45), (self.we('each') - 0.05, 'swipe', 0.3), (wx(self, '12') - 0.03, 'pop', 0.4)]
        return e
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1150), (self.we('designer'), 1.2, 1.25, 360, 1000), (self.we('drew'), 1.25, 1.3, 760, 1080),
                (self.we('176'), 1.1, 1.14, 700, 1060), (self.we('each'), 1.55, 1.62, 765, 1090)]
    def plate(self):
        return designer_plate()
    def dyn(self, img, t):
        ds, dr, n176, ea = self.we('designer'), self.we('drew'), self.we('176'), self.we('each')
        W_ = 660
        sw, sh_ = int(W_ * 0.8), int(W_ * 0.86 * 0.79 - W_ * 0.09)
        if t < n176:
            n = int(npix('heart') * clamp01((t - ds) / max(0.5, n176 - ds - 0.3)))
            sc_ = screen_content(sw, sh_, 'draw', n=n)
        elif t < ea:
            sc_ = screen_content(sw, sh_, 'set', n=int(176 * clamp01((t - n176) / 0.9)))
        else:
            sc_ = screen_content(sw, sh_, 'draw', n=None)
        mon = crt(W_, sc_)
        ex = 'think' if t < dr else ('happy' if t < ea else 'proud')
        a = P(img, KURITA, 290, 1900, t, ex, arm_l=20, arm_r=70 + 6 * math.sin(t * 9), scale=0.95, look_dir=1)
        desk_front(img, 1480)
        floor_shadow(img, 770, 1490, 330, 0.35)
        paste_at(img, mon, int(770 - mon.width / 2), int(1485 - mon.height))
        d = ImageDraw.Draw(img)
        # keyboard + mouse
        d.polygon([(560, 1510), (980, 1510), (1000, 1570), (540, 1570)], fill=(225, 220, 205), outline=(160, 150, 130))
        for k in range(3):
            d.line([(570 + k * 6, 1525 + k * 14), (970 - k * 6, 1525 + k * 14)], fill=(180, 172, 150), width=4)
        hx, hy = a['hand_r']
        d.ellipse([hx - 30, max(hy, 1470) - 10, hx + 30, max(hy, 1470) + 34], fill=(225, 220, 205), outline=(160, 150, 130), width=3)
        if n176 <= t < ea:
            chip_at(img, '176', 770, 640, t, n176, dot=(230, 50, 80))
        elif t >= wx(self, '12'):
            chip_at(img, '12 × 12', 770, 690, t, wx(self, '12'), dot=(60, 110, 210))

# 6  Today, that set is in New York's Museum of Modern Art.
class E6(Sc):
    def events(self):
        return [(0.05, 'swipe', 0.3), (self.we('Museum') - 0.03, 'chime', 0.5)]
    def shots(self):
        return [(0.0, 1.05, 1.1, CX, 1000), (self.we('York'), 1.1, 1.14, CX, 1150), (self.we('Modern'), 1.22, 1.28, CX, 950)]
    def plate(self):
        self.panel = icon_panel(640, 420)
        return museum_plate()
    def dyn(self, img, t):
        mu = self.we('Museum')
        paste_at(img, self.panel, int(CX - self.panel.width / 2), 540)
        if t >= mu:
            d = ImageDraw.Draw(img)
            for k in range(6):
                ph = ((t - mu) * 0.9 + k / 6) % 1
                ang = k * math.pi / 3 + (t - mu)
                sparkle(d, CX + math.cos(ang) * 420, 770 + math.sin(ang) * 300, 26 * (1 - abs(ph - 0.5)))
        museum_front(img, 1760)
        P(img, GIRL, 360, 1990, t, 'happy' if t < mu else 'shocked', arm_l=20, arm_r=150 if t >= mu else 110, scale=0.92, look_dir=1)
        P(img, GRAN, 960, 1990, t, 'smile' if t < mu else 'proud', talk=talk_frame(t) and t < mu, arm_l=110, arm_r=20, scale=0.9, phase=1.5, look_dir=-1)

# 7  Plot twist: it wasn't even the first.
class E7(Sc):
    def events(self):
        return [(0.03, 'scratch', 0.5), (self.we('wasn') - 0.03, 'swipe', 0.35), (self.we('even'), 'bigpop', 0.45)]
    def shots(self):
        return [(0.0, 1.12, 1.16, CX, 1150), (self.we('wasn'), 1.0, 1.04, CX, 1150), (self.we('first') - 0.1, 1.2, 1.25, CX, 1050)]
    def plate(self):
        self.panel = icon_panel(300, 200)
        return stage_plate()
    def dyn(self, img, t):
        wn, ev = self.we('wasn'), self.we('even')
        spots = podium(img, 1720)
        u = clamp01((t - wn) / 0.4)
        x1, y1 = spots['1']
        x2, y2 = spots['2']
        px = x1 + (x2 - x1) * ease_in_out(u)
        py = y1 + (y2 - y1) * ease_in_out(u) - 120 * math.sin(u * math.pi)
        paste_at(img, self.panel, int(px - self.panel.width / 2), int(py - self.panel.height))
        if t >= ev:
            v = clamp01((t - ev) / 0.3)
            ph = phone97(170)
            y = -300 + (y1 - ph.height / 2 + 300) * ease_out(v)
            put(img, ph, x1, y, 1.0, 8 * (1 - v))
            if v >= 1:
                d = ImageDraw.Draw(img)
                for k in range(8):
                    ang = k * math.pi / 4 + t
                    sparkle(d, x1 + math.cos(ang) * 200, y + math.sin(ang) * 260, 24)
        P(img, GIRL, 1060, 2010, t, 'shocked' if t >= wn else 'think', arm_l=150 + 6 * math.sin(t * 9), arm_r=150 + 6 * math.sin(t * 8), scale=0.92, look_dir=-1)

# 8  Another Japanese phone had 90 emoji back in 1997, and that's the family your iPhone emoji came from.
class E8(Sc):
    def events(self):
        e = [(0.05, 'pop', 0.35), (self.we('90') - 0.03, 'tick', 0.5), (self.we('1997') - 0.05, 'ding', 0.45),
             (self.we('family') - 0.05, 'swipe', 0.3), (self.we('iPhone') - 0.04, 'chime', 0.45)]
        return e
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1150), (self.we('90') - 0.05, 1.3, 1.36, 380, 1050), (self.we('family') - 0.05, 1.0, 1.04, CX, 1120),
                (self.we('iPhone') - 0.05, 1.06, 1.1, CX + 60, 1080)]
    def plate(self):
        return phoneshop_plate()
    def dyn(self, img, t):
        n90, fa, ip = self.we('90'), self.we('family'), self.we('iPhone')
        a = P(img, CLERK, 330, 1840, t, 'happy' if t < fa else 'proud', talk=talk_frame(t) and t < fa, arm_l=20, arm_r=(125 if t < fa else 70) + 5 * math.sin(t * 5), scale=0.95)
        if t >= fa:
            b = P(img, GIRL, 930, 1990, t, 'shocked' if t < ip else 'happy', arm_l=20, arm_r=135 + 5 * math.sin(t * 6), scale=0.92, phase=2, look_dir=-1)
        glass_counter(img, 1560)
        n = 0 if t < n90 else 1 + int(clamp01((t - n90) / 0.6) * 5)
        ph = phone97(200, n)
        hx, hy = a['hand_r']
        put(img, ph, hx + (10 if t < fa else -90), hy - (160 if t < fa else 40), 1.0, -6)
        if t >= fa:
            sp = smartphone(220)
            gx, gy = b['hand_r']
            gx, gy = gx - 150, gy - 200
            if t >= ip:
                glow = Image.new('RGBA', (420, 620), (0, 0, 0, 0))
                ImageDraw.Draw(glow).rounded_rectangle([60, 60, 360, 560], 60, fill=(255, 240, 150, 150))
                glow = glow.filter(ImageFilter.GaussianBlur(30))
                put(img, glow, gx, gy)
            put(img, sp, gx, gy, 1.0, 6)
            # family link: dotted golden arc from old phone to new phone with hearts
            u = clamp01((t - fa) / 0.6)
            d = ImageDraw.Draw(img)
            p0 = (hx + 10, hy - 420)
            p1 = (gx, gy - 260)
            for k in range(int(28 * u)):
                s_ = k / 28
                x = p0[0] + (p1[0] - p0[0]) * s_
                y = p0[1] + (p1[1] - p0[1]) * s_ - 260 * math.sin(s_ * math.pi)
                d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, 205, 60))
            if u >= 1:
                for k in range(3):
                    s_ = ((t - fa) * 0.5 + k / 3) % 1
                    x = p0[0] + (p1[0] - p0[0]) * s_
                    y = p0[1] + (p1[1] - p0[1]) * s_ - 260 * math.sin(s_ * math.pi)
                    put(img, heart_sp(30), x, y)

# 9  Now, the name. E means picture, moji means character.
class E9(Sc):
    def events(self):
        return [(0.05, 'rustle', 0.4), (wx(self, 'E') - 0.05, 'pop', 0.45), (self.we('moji') - 0.05, 'pop', 0.45)]
    def shots(self):
        e = wx(self, 'E')
        return [(0.0, 1.0, 1.05, CX, 1100), (e - 0.05, 1.2, 1.25, 420, 880), (self.we('moji') - 0.05, 1.2, 1.25, 880, 880)]
    def plate(self):
        return tatami_plate()
    def dyn(self, img, t):
        e, m = wx(self, 'E'), self.we('moji')
        u1 = clamp01((t - e + 0.05) / 0.35)
        u2 = clamp01((t - m + 0.05) / 0.35)
        s1 = scroll(330, 820, '絵', True, max(0.05, u1))
        s2 = scroll(330, 820, '文字', False, max(0.05, u2))
        paste_at(img, s1, int(400 - s1.width / 2), 250)
        paste_at(img, s2, int(900 - s2.width / 2), 250)
        a = P(img, TEACH, 640, 1860, t, 'happy' if t < e else 'proud', talk=talk_frame(t) and t < e, arm_l=20,
              arm_r=150 if t >= m else (130 if t >= e else 60), scale=0.85)
        hold(img, brush(240), a, 'hand_r', 0, -60, -20 + 8 * math.sin(t * 6))
        P(img, GIRL, 1130, 2010, t, 'think' if t < e else 'happy', arm_l=110, arm_r=20, scale=0.85, phase=2, look_dir=-1)
        low_table(img, 640, 1720, 600)

# 10  Emotion? Total coincidence. And it all started with one tiny heart.
class E10(Sc):
    def events(self):
        return [(0.05, 'bloop', 0.4), (self.we('coincidence') - 0.03, 'pop', 0.35), (self.we('one') - 0.05, 'chime', 0.5)]
    def shots(self):
        return [(0.0, 1.12, 1.16, CX + 120, 1200), (self.we('coincidence'), 1.2, 1.24, CX + 150, 1250),
                (self.we('started'), 1.08, 1.12, CX, 1160), (self.we('tiny') - 0.1, 1.32, 1.4, 500, 1150)]
    def plate(self):
        return bedroom_plate()
    def dyn(self, img, t):
        co, st, hh = self.we('coincidence'), self.we('started'), self.we('tiny') - 0.1
        if t < co:
            e, al, ar, tk = 'think', 120, 120, False
        elif t < st:
            e, al, ar, tk = 'happy', 30, 140 + 10 * math.sin(t * 9), talk_frame(t)
        else:
            e, al, ar, tk = 'happy', 160 if t > hh else 120, 160 if t > hh else 30, False
        bedroom_scene(img, t, e, al, ar, tk, t_heart=hh)

SCENES = [E0, E1, E2, E3, E4, E5, E6, E7, E8, E9, E10]
