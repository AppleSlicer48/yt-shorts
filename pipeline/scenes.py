"""Crocs Were Invented as Boat Shoes - scenes (cartoon people kit, detailed 2.5D settings)."""
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

# ---------------------------------------------------------------- 0  Crocs were invented as boat shoes!
def s0_visual(img, t):
    drop = clamp01(t / 0.5)
    cy = 1200 + 60 * ease_out(drop) + math.sin(t * 4) * 14
    rot = 42 - 14 * ease_out(drop) + math.sin(t * 3) * 3
    ripples(img, CX - 20, 1700, t, 380)
    put(img, clog(1120, GREEN), CX - 40, cy, 1.0, rot)
    splash(img, CX - 20, 1600, t, 0.0, 22, 360)
    splash(img, CX + 80, 1620, t, 0.55, 14, 240)

class S0(Sc):
    def events(self):
        return [(self.we('invented') + 0.2, 'splat', 0.35), (self.we('boat') - 0.03, 'bloop', 0.6)]
    def shots(self):
        c = self.we('invented')
        return [(0.0, 1.0, 1.04, CX, 1152), (c + 0.35, 1.3, 1.38, CX + 60, 1350)]
    def plate(self):
        return harbor_plate()
    def dyn(self, img, t):
        s0_visual(img, t)
        P(img, TEEN, 1090, 2150, t, 'shocked', arm_l=150 + 10 * math.sin(t * 9), arm_r=40, scale=0.92, look_dir=-1)

# ---------------------------------------------------------------- 1  And a mom got ten million dollars just for filling the holes.
class S1(Sc):
    def events(self):
        e = [(0.05, 'pop', 0.4), (self.we('million'), 'cash', 0.8)]
        for k in range(4):
            e.append((self.ct(k), 'pop', 0.45))
        return e
    def ct(self, k):
        a = self.we('mom')
        b = self.we('holes')
        return a + (b - a) * (k + 0.5) / 4
    def shots(self):
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('million'), 1.15, 1.22, CX, 1250), (self.we('filling'), 1.3, 1.4, CX + 120, 1500)]
    def plate(self):
        self.bill = bill_sprite()
        self.cs = [charm_sprite(k, 44) for k in range(10)]
        return kitchen_plate()
    def dyn(self, img, t):
        m = self.we('million')
        filled = sum(1 for k in range(4) if t >= self.ct(k) + 0.18)
        a = P(img, SHERI, CX - 260, 1720, t, 'happy' if t < m else 'shocked', talk=t < m and talk_frame(t),
              arm_l=20 if t < m else 150, arm_r=115 + 25 * math.sin(t * 7), scale=0.95)
        table_front(img, 1580)
        cl = clog(760, PINK, filled)
        cx0, cy0 = CX + 140 - cl.width / 2, 1500 - cl.height / 2
        floor_shadow(img, CX + 140, 1640, 380, 0.35)
        paste_at(img, cl, int(cx0), int(cy0))
        for k in range(4):
            t0 = self.ct(k)
            if t0 - 0.4 <= t < t0 + 0.18:
                u = clamp01((t - (t0 - 0.4)) / 0.58)
                hx, hy = a['hand_r']
                tx, ty = hole_pos(760, k)
                tx += cx0
                ty += cy0
                put(img, self.cs[k], hx + (tx - hx) * ease_in_out(u), hy + (ty - hy) * ease_in_out(u) - 180 * math.sin(u * math.pi))
        if t >= m:
            u = t - m
            for k in range(14):
                ang = math.radians(-165 + k * 11)
                sp = 520 + (k * 53) % 260
                x = CX + math.cos(ang) * sp * min(u, 1.2)
                y = 950 + math.sin(ang) * sp * min(u, 1.2) * 0.8 + 420 * u * u
                put(img, self.bill, x, y, 1.0, (k * 47 + u * 200) % 360)

# ---------------------------------------------------------------- 2  So how did a boat clog end up on everyone's feet?
def feet_clogs(img, a, col, scale=0.9, charms=0):
    fx, fy = a['feet']
    w = int(220 * scale)
    for sx in (-1, 1):
        c = clog(w, col, charms, flip=(sx < 0))
        paste_at(img, c, int(fx + sx * 60 * scale - w / 2), int(fy - c.height * 0.8))

class S2(Sc):
    def events(self):
        return [(0.05, 'swipe', 0.3), (self.we('end') - 0.05, 'squeak', 0.5), (self.we('feet') - 0.05, 'pop', 0.5)]
    def shots(self):
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('end'), 1.5, 1.6, CX, 1750)]
    def plate(self):
        return hallway_plate()
    def dyn(self, img, t):
        walk = t * 120
        crowd = [(KID1, 260, BLUE, 2, 1900, 0.78, walk * 0.4), (dict(PRESETS['boy'], hat=None, top=(200, 80, 80)), 1040, (250, 200, 60), 0, 1900, 0.8, -walk * 0.4),
                 (TEEN, 640, PINK, 3, 2100, 0.95, 0)]
        for k, (look, x, col, ch, fl, sc, dx) in enumerate(crowd):
            isT = look is TEEN
            sw = 25 * math.sin(t * 7 + k)
            a = P(img, look, x + dx, fl, t, 'think' if isT else ('happy' if k == 0 else 'smile'), talk=isT and talk_frame(t),
                  arm_l=20 + sw, arm_r=(150 if isT else 20 - sw), scale=sc, phase=k, bob=1.6)
            feet_clogs(img, a, col, sc, ch)

# ---------------------------------------------------------------- 3  Three friends from Colorado found a foam clog made by a Canadian company.
def maple_box(w=300):
    im, d = _ss(w, w * 0.8)
    s = SS
    d.polygon([(0, w * 0.2 * s), (w * 0.75 * s, w * 0.2 * s), (w * s - 1, 0), (w * 0.25 * s, 0)], fill=(215, 175, 120))
    d.rectangle([0, w * 0.2 * s, w * 0.75 * s, w * 0.8 * s - 1], fill=(195, 150, 95))
    d.polygon([(w * 0.75 * s, w * 0.2 * s), (w * s - 1, 0), (w * s - 1, w * 0.6 * s), (w * 0.75 * s, w * 0.8 * s - 1)], fill=(160, 120, 75))
    cx, cy, r = w * 0.37 * s, w * 0.5 * s, w * 0.17 * s
    pts = []
    for k in range(22):
        a = -math.pi / 2 + k * 2 * math.pi / 22
        rr = r * (1.0 if k % 2 == 0 else 0.55) * (0.75 if k in (5, 6, 16, 17) else 1)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=(220, 40, 40))
    d.rectangle([cx - r * 0.08, cy + r * 0.5, cx + r * 0.08, cy + r * 1.1], fill=(220, 40, 40))
    return _down(im)

class S3(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('found') - 0.05, 'rustle', 0.6), (self.we('Canadian') - 0.05, 'ding', 0.5)]
    def shots(self):
        f = self.we('found')
        return [(0.0, 1.0, 1.05, CX, 1152), (f, 1.15, 1.22, CX, 1250), (self.we('Canadian'), 1.05, 1.1, CX, 1152)]
    def plate(self):
        img = cabin_plate()
        floor_shadow(img, 1080, 1830, 220, 0.35)
        put(img, maple_box(340), 1080, 1700, 1.0)
        return img
    def dyn(self, img, t):
        f = self.we('found')
        rv = t >= f
        P(img, FRIEND_B, 250, 1990, t, 'shocked' if rv else 'smile', arm_l=20, arm_r=110 if rv else 50, scale=0.82, phase=1)
        P(img, FRIEND_C, 1040, 2010, t, 'happy' if rv else 'think', arm_l=(140 if rv else 30) + 10 * math.sin(t * 8), arm_r=20, scale=0.82, phase=2)
        up = clamp01((t - f) / 0.35)
        a = P(img, FRIEND_A, 640, 2130, t, 'proud' if rv else 'smile', talk=talk_frame(t) and not rv, arm_l=20,
              arm_r=40 + 120 * ease_out(up), scale=0.92)
        hx, hy = a['hand_r']
        put(img, clog(400, (250, 240, 225)), hx + 30, hy - 70 * up, 1.0, -10 + 10 * up)
        chip_at(img, 'FOAM CREATIONS', CX, 700, t, self.we('Canadian') + 0.1, dot=(220, 40, 40))

# ---------------------------------------------------------------- 4  It floated, it didn't slip, and the holes let air in and water out.
class S4(Sc):
    def events(self):
        return [(0.05, 'bloop', 0.5), (self.we('slip') - 0.05, 'squeak', 0.6), (self.we('water') - 0.05, 'splat', 0.4)]
    def shots(self):
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('slip'), 1.15, 1.2, CX, 1500), (self.we('holes'), 1.3, 1.42, CX + 60, 1200)]
    def plate(self):
        self.cl = clog(900, BLUE)
        return deck_plate()
    def dyn(self, img, t):
        s = self.we('slip')
        h = self.we('holes')
        if t < s:
            y = 1150 + math.sin(t * 3.5) * 30
            ripples(img, CX + 80, y + 230, t, 360)
            put(img, self.cl, CX + 80, y, 1.0, math.sin(t * 2.5) * 5)
        elif t < h:
            u = t - s
            d = ImageDraw.Draw(img)
            for k in range(7):
                x = 160 + k * 150
                d.ellipse([x, 1975 - k * 6, x + 90, 1998 - k * 6], fill=(200, 230, 250))
            put(img, self.cl, CX + 40, 1770 + 14 * math.sin(u * 22) * math.exp(-u * 3), 1.0, 0)
        else:
            u = t - h
            y = 1180 + math.sin(t * 3) * 12
            put(img, self.cl, CX + 40, y, 1.0, 0)
            d = ImageDraw.Draw(img)
            cx0 = CX + 40 - 450
            cy0 = y - int(900 * 0.62) / 2
            wt = self.we('water')
            for k in range(10):
                hx, hy = hole_pos(900, k)
                hx += cx0
                hy += cy0
                if t < wt:
                    for j in range(3):
                        ph = (u * 1.6 + j / 3 + k * 0.13) % 1
                        r = 8 + 10 * (1 - ph)
                        yy = hy - 170 * (1 - ph)
                        d.ellipse([hx - r, yy - r, hx + r, yy + r], outline=(255, 255, 255), width=4)
                else:
                    for j in range(4):
                        ph = ((t - wt) * 2.2 + j / 4 + k * 0.11) % 1
                        yy = hy + 40 + ph * 520
                        d.ellipse([hx - 9, yy - 14, hx + 9, yy + 14], fill=(200, 235, 255))

# ---------------------------------------------------------------- 5  In 2002, they brought 200 pairs to a Florida boat show, and every pair sold out.
def booth_table(img):
    d = ImageDraw.Draw(img)
    d.rectangle([180, 1420, PW - 180, 1470], fill=(240, 240, 240))
    d.rectangle([200, 1470, PW - 200, 1800], fill=(60, 120, 190))
    d.rectangle([200, 1470, PW - 200, 1500], fill=(40, 90, 150))
    floor_shadow(img, CX, 1820, 520, 0.35)

class S5(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('200') - 0.05, 'thud', 0.6), (self.we('sold'), 'cash', 0.8)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('Florida'), 1.1, 1.15, CX, 1250), (self.we('every'), 1.0, 1.06, CX, 1152)]
    def plate(self):
        self.cls = [clog(210, c) for c in CLOG_COLS]
        return boatshow_plate()
    def dyn(self, img, t):
        e = self.we('every')
        end = self.we('sold', 't1')
        sel = t >= e
        P(img, FRIEND_A, 430, 1560, t, 'shocked' if sel else 'happy', talk=talk_frame(t) and not sel, arm_l=30, arm_r=110 + 20 * math.sin(t * 6), scale=0.66)
        P(img, FRIEND_C, 870, 1560, t, 'proud' if sel else 'smile', arm_l=150 if sel else 30, arm_r=150 if sel else 30, scale=0.66, phase=2)
        booth_table(img)
        n0 = 18
        n = n0 if t < e else int(round(n0 * (1 - clamp01((t - e) / max(0.3, end - e)))))
        for k in range(n):
            row, col = divmod(k, 6)
            put(img, self.cls[k % len(self.cls)], 300 + col * 140 + (row % 2) * 40, 1385 - row * 62, 0.8)
        if sel:
            P(img, SHOPPER1, 200, 2260, t, 'happy', arm_l=20, arm_r=150, scale=0.85, phase=1)
            P(img, SHOPPER2, 1090, 2260, t, 'shocked', arm_l=160, arm_r=20, scale=0.85, phase=3)
        chip_at(img, 'FORT LAUDERDALE', CX, 660, t, self.we('Florida'), dot=(60, 170, 230))

# ---------------------------------------------------------------- 6  Then a mom named Sheri started sticking charms in her kids' Crocs.
class S6(Sc):
    def events(self):
        e = [(0.05, 'pop', 0.4)]
        for k in range(5):
            e.append((self.ct(k), 'pop', 0.4))
        return e
    def ct(self, k):
        a = self.we('started')
        return a + (self.dur - 0.4 - a) * k / 5
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('charms'), 1.22, 1.3, CX + 60, 1450), (self.we('kids'), 1.05, 1.1, CX, 1200)]
    def plate(self):
        self.cs = [charm_sprite(k, 36) for k in range(10)]
        return kitchen_plate()
    def dyn(self, img, t):
        P(img, KID1, 1090, 1880, t, 'happy' if t > self.ct(1) else 'smile', arm_l=140 + 15 * math.sin(t * 9), arm_r=20, scale=0.85, phase=1)
        a = P(img, SHERI, 560, 1760, t, 'happy', talk=False, arm_l=20, arm_r=110 + 20 * math.sin(t * 6), scale=0.95)
        P(img, KID2, 210, 1880, t, 'shocked' if t > self.ct(2) else 'smile', arm_l=20, arm_r=140, scale=0.85, phase=2)
        table_front(img, 1620)
        filled = sum(1 for k in range(5) if t >= self.ct(k) + 0.25)
        c1 = clog(520, BLUE, filled)
        c2 = clog(460, PINK, max(0, filled - 2), flip=True)
        x1, y1 = 800, 1560
        put(img, c2, 330, 1590)
        paste_at(img, c1, int(x1 - c1.width / 2), int(y1 - c1.height / 2))
        for k in range(5):
            t0 = self.ct(k)
            if t0 - 0.2 <= t < t0 + 0.25:
                u = clamp01((t - (t0 - 0.2)) / 0.45)
                hx, hy = a['hand_r']
                tx, ty = hole_pos(520, k)
                tx += x1 - c1.width / 2
                ty += y1 - c1.height / 2
                put(img, self.cs[k], hx + (tx - hx) * ease_in_out(u), hy + (ty - hy) * ease_in_out(u) - 120 * math.sin(u * math.pi))

# ---------------------------------------------------------------- 7  She turned it into a basement business called Jibbitz.
class S7(Sc):
    def events(self):
        return [(0.05, 'thud', 0.4), (self.we('business') - 0.05, 'rattle', 0.5), (self.we('Jibbitz') - 0.05, 'ding', 0.6)]
    def shots(self):
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('business'), 1.2, 1.28, CX + 60, 1400)]
    def plate(self):
        self.cs = [charm_sprite(k, 26) for k in range(10)]
        return basement_plate()
    def dyn(self, img, t):
        j = self.we('Jibbitz')
        P(img, GRANDPA, 1010, 1800, t, 'happy', arm_l=110 + 20 * math.sin(t * 8), arm_r=100, scale=0.8, phase=2)
        P(img, SHERI, 420, 1820, t, 'proud' if t > j else 'happy', talk=talk_frame(t) and t < j,
          arm_l=(160 if t > j else 100) + 10 * math.sin(t * 7), arm_r=100, scale=0.95)
        table_front(img, 1580, (120, 120, 130), (200, 200, 205))
        d = ImageDraw.Draw(img)
        for k in range(3):
            bx = 180 + k * 330
            d.rounded_rectangle([bx, 1480, bx + 260, 1620], 16, fill=[(250, 200, 60), (120, 200, 240), (240, 120, 170)][k], outline=(80, 80, 90), width=5)
        for q in range(24):
            put(img, self.cs[q % 10], 210 + (q % 8) * 115 + (q // 8) * 12, 1465 + (q // 8) * 18 - (q % 3) * 8)
        for q in range(5):
            ph = (t * 0.7 + q / 5) % 1
            x = 60 + ph * 1100
            d.rounded_rectangle([x, 1720, x + 110, 1860], 10, fill=(250, 250, 255), outline=(170, 170, 180), width=4)
            put(img, self.cs[(q * 3) % 10], x + 55, 1790)
        chip_at(img, '2005', 1080, 700, t, self.we('business'), dot=(250, 200, 60))

# ---------------------------------------------------------------- 8  And in 2006, Crocs bought it for ten million dollars. Seriously.
class S8(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('bought') - 0.03, 'thud', 0.6), (self.we('million'), 'cash', 0.9), (self.we('Seriously') - 0.05, 'party', 0.4)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('bought'), 1.12, 1.18, CX, 1300), (self.we('Seriously'), 1.25, 1.32, CX - 160, 1150)]
    def plate(self):
        self.bill = bill_sprite(150)
        return office_plate()
    def dyn(self, img, t):
        b = self.we('bought')
        m = self.we('million')
        se = self.we('Seriously')
        a = P(img, EXEC, 920, 2000, t, 'smile', talk=talk_frame(t) and b < t < m, arm_l=40 + 60 * clamp01((t - b) / 0.4), arm_r=20, scale=0.92, phase=1)
        expr = 'smile' if t < m else ('shocked' if t < se else 'happy')
        arms = 150 if t >= se else (30 if t < m else 70)
        P(img, SHERI, 360, 2000, t, expr, arm_l=arms + 8 * math.sin(t * 9), arm_r=arms + 8 * math.sin(t * 9 + 1), scale=0.95)
        hx, hy = a['hand_l']
        d = ImageDraw.Draw(img)
        k = clamp01((t - b) / 0.6)
        bx = (hx - 60) + (650 - hx + 60) * ease_in_out(k) if t < m else 650
        by = 1760
        d.rounded_rectangle([bx - 150, by - 100, bx + 150, by + 100], 18, fill=(110, 70, 40), outline=(60, 35, 20), width=8)
        d.rectangle([bx - 40, by - 135, bx + 40, by - 100], outline=(60, 35, 20), width=12)
        if t >= m:
            u = t - m
            d.rectangle([bx - 140, by - 200, bx + 140, by - 100], fill=(90, 55, 30))
            for q in range(4):
                put(img, self.bill, bx - 90 + q * 60, by - 120 - q * 8, 1.0, -10 + q * 6)
            for q in range(10):
                ang = math.radians(-150 + q * 13)
                put(img, self.bill, bx + math.cos(ang) * 600 * min(u, 1), by - 100 + math.sin(ang) * 700 * min(u, 1) + 500 * u * u, 1.0, (q * 61 + u * 240) % 360)
        chip_at(img, '+ UP TO $10M MORE', CX, 660, t, se - 0.1, dot=(60, 170, 90))

# ---------------------------------------------------------------- 9  Time magazine even called Crocs one of the 50 worst inventions.
def magazine(w=520):
    h = int(w * 1.3)
    im, d = _ss(w, h)
    s = SS
    d.rectangle([0, 0, w * s - 1, h * s - 1], fill=(250, 248, 240), outline=(60, 60, 70), width=8)
    d.rectangle([20 * s, 20 * s, (w - 20) * s, 120 * s], fill=(40, 50, 70))
    for k in range(3):
        d.rectangle([40 * s, (h - 150 + k * 36) * s, (w - 160 + k * 30) * s, (h - 130 + k * 36) * s], fill=(150, 150, 160))
    c = clog(int(w * 0.75), GREEN)
    im.alpha_composite(c.resize((c.width * s, c.height * s)), (int(w * 0.12 * s), int(h * 0.3 * s)))
    d.line([(w * 0.18 * s, h * 0.26 * s), (w * 0.82 * s, h * 0.72 * s)], fill=(220, 40, 40), width=34)
    d.line([(w * 0.82 * s, h * 0.26 * s), (w * 0.18 * s, h * 0.72 * s)], fill=(220, 40, 40), width=34)
    return _down(im)

class S9(Sc):
    def events(self):
        return [(0.05, 'rustle', 0.5), (self.we('worst') - 0.05, 'buzzer', 0.35)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('called'), 1.15, 1.22, CX + 120, 1250), (self.we('worst'), 1.28, 1.36, CX - 140, 1100)]
    def plate(self):
        self.mag = magazine(460)
        return living_plate()
    def dyn(self, img, t):
        w = self.we('worst')
        a = P(img, FRIEND_A, 880, 2080, t, 'angry' if t > w else 'nervous', arm_l=115, arm_r=20, scale=0.95, phase=1)
        P(img, TEEN, 320, 2130, t, 'shocked' if t > self.we('called') else 'think', arm_l=20, arm_r=150 if t > w else 40, scale=0.9, phase=2, look_dir=1)
        hx, hy = a['hand_l']
        put(img, self.mag, hx - 110, hy - 250, 1.0, 6 + 2 * math.sin(t * 3))
        chip_at(img, '2010', CX - 140, 640, t, self.we('magazine') + 0.2, dot=(220, 40, 40))

# ---------------------------------------------------------------- 10  But the holes made for boats became the fun part, and it all started because...
class S10(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('fun') - 0.05, 'chime', 0.5), (self.we('started') - 0.05, 'riser', 0.4)]
    def shots(self):
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('fun'), 1.15, 1.22, CX, 1250), (self.we('started'), 1.0, 1.0, CX, 1152)]
    def plate(self):
        self.hp = harbor_plate()
        return bedroom_plate()
    def dyn(self, img, t):
        f = self.we('fun')
        a = P(img, TEEN, 620, 2150, t, 'happy' if t > f else 'smile', talk=talk_frame(t) and t < f, arm_l=150 if t > f else 30,
              arm_r=120 + 15 * math.sin(t * 6), scale=0.95)
        n = 10 if t > f else 4 + int(clamp01(t / max(0.1, f)) * 5)
        hx, hy = a['hand_r']
        put(img, clog(620, PINK, n), hx + 40, hy - 170, 1.0, 8 * math.sin(t * 4))
        if t > f:
            hx2, hy2 = a['hand_l']
            put(img, clog(500, BLUE, 8, flip=True), hx2 - 20, hy2 - 140, 1.0, -8 * math.sin(t * 4))
        st = self.we('started')
        k = clamp01((t - (st + 0.2)) / max(0.2, self.dur - st - 0.3))
        if k > 0:
            hp = self.hp.copy()
            s0_visual(hp, 0.9)
            hp.putalpha(hp.getchannel('A').point(lambda v: int(v * k)))
            img.alpha_composite(hp)

SCENES = [S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10]
