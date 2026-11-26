"""Nutella Used to Be a Brick - scenes (cartoon people kit, detailed 2.5D settings)."""
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

# ================================================================ scenes
# 0  Nutella started out as a brick you had to slice!
def brick_scene(img, t, t_slice, girl_expr='shocked', cut_done=False):
    P_ = P(img, NTEEN, 1010, 2000, t, girl_expr, arm_l=110 + 10 * math.sin(t * 7), arm_r=150 + 6 * math.sin(t * 6), scale=0.95, look_dir=-1)
    counter_front(img, 1600)
    board(img, 480, 1600, 860)
    LW, LH = 760, 820
    lf = loaf(LW, LH)
    lx, ly = 470 - LW / 2, 1600 - LH
    floor_shadow(img, 470, 1610, 440, 0.3)
    u = clamp01((t - t_slice) / 0.35) if t_slice is not None else 0
    cutx = lx + LW * 0.86 - 110
    kn = knife(430).rotate(-90, resample=Image.BICUBIC, expand=True)
    ky = 900 - 30 * abs(math.sin(t * 5)) * (1 - u) + 700 * ease_in_out(u)
    if u > 0:
        sl = slab_sprite(110, int(LH * 0.8))
        fall = clamp01((t - t_slice - 0.25) / 0.45)
        crop = lf.crop((0, 0, int(cutx - lx), lf.height))
        paste_at(img, crop, int(lx), int(ly))
        put(img, sl, cutx + 70 + 160 * ease_out(fall), 1600 - sl.height / 2 + 60 * fall, 1.0, -60 * ease_in_out(fall))
    else:
        paste_at(img, lf, int(lx), int(ly))
    put(img, kn, cutx, ky)
    d = ImageDraw.Draw(img)
    if u > 0:
        ph = clamp01((t - t_slice) / 0.8)
        for k in range(10):
            x = cutx + (k - 5) * 22 * ph * 3
            y = 1560 - 160 * math.sin(ph * math.pi) * (0.5 + (k % 3) * 0.3) + 40 * ph
            d.ellipse([x - 8, y - 6, x + 8, y + 6], fill=(150, 95, 55))
    return P_

class N0(Sc):
    def events(self):
        return [(self.we('brick') - 0.03, 'bigpop', 0.45), (self.we('slice') - 0.05, 'scratch', 0.6)]
    def shots(self):
        b = self.we('brick')
        return [(0.0, 1.08, 1.12, CX - 40, 1080), (b, 1.2, 1.25, CX - 40, 1180), (self.we('had'), 1.3, 1.36, CX + 40, 1260)]
    def plate(self):
        return counter_plate(0)
    def dyn(self, img, t):
        brick_scene(img, t, self.we('slice') - 0.05, 'shocked')

# 1  And it only exists because there wasn't enough chocolate.
class N1(Sc):
    def events(self):
        e = [(0.05, 'swipe', 0.3), (self.we('wasn') - 0.05, 'thud', 0.45)]
        return e
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('because'), 1.18, 1.24, CX, 1000), (self.we('enough'), 1.1, 1.14, CX + 80, 1250)]
    def plate(self):
        return shop_plate()
    def dyn(self, img, t):
        wz = self.we('wasn')
        sad = t > wz
        # chocolate bars vanish from the gap
        d = ImageDraw.Draw(img)
        n = 4 if t < self.we('because') else max(0, 4 - int((t - self.we('because')) / 0.35))
        for k in range(n):
            x = 500 + k * 80
            d.rectangle([x, 560, x + 62, 680], fill=(110, 60, 35), outline=(70, 35, 20), width=4)
            d.rectangle([x, 600, x + 62, 640], fill=(220, 190, 120))
        a = P(img, SHOPKEEP, 760, 2150, t, 'sad' if sad else 'nervous', talk=talk_frame(t) and not sad,
              arm_l=95 + 8 * math.sin(t * 10), arm_r=20, scale=0.98)
        P(img, NKID, 250, 2240, t, 'sad' if sad else 'think', arm_l=20, arm_r=130 if not sad else 30, scale=0.85, phase=2)
        shop_counter(img, 1620)
        # the shopkeeper tips an empty cocoa tin upside down
        hx, hy = a['hand_l']
        im, dd = _ss(170, 200)
        dd.rectangle([0, 0, 340, 400], fill=(150, 90, 50), outline=(90, 50, 25), width=10)
        dd.rectangle([0, 130, 340, 270], fill=(240, 220, 170))
        dd.ellipse([120, 150, 220, 250], fill=(110, 60, 30))
        tin = _down(im)
        put(img, tin, hx - 40, hy - 60, 1.0, 160 + 15 * math.sin(t * 12))
        if sad:
            for k in range(3):
                ph = ((t - wz) * 1.5 + k / 3) % 1
                d.ellipse([hx - 50 + k * 10, hy + 40 + ph * 400, hx - 40 + k * 10, hy + 50 + ph * 400], fill=(110, 60, 30))

# 2  So how did a brick become the spread everyone loves?
class N2(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('become') - 0.05, 'bigpop', 0.5), (self.we('spread') - 0.05, 'squeak', 0.4)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('become'), 1.15, 1.2, CX - 40, 1350), (self.we('everyone'), 1.08, 1.12, CX + 60, 1200)]
    def plate(self):
        return kitchen_plate()
    def dyn(self, img, t):
        bc = self.we('become')
        ev = self.we('everyone')
        expr = 'think' if t < bc else ('shocked' if t < ev else 'happy')
        a = P(img, NTEEN, 840, 2080, t, expr, talk=talk_frame(t) and t < bc, arm_l=110 + 15 * math.sin(t * 6), arm_r=150 if t < bc else 40, scale=0.98, look_dir=-1)
        table_front(img, 1640, (230, 120, 140), (245, 170, 185))
        u = clamp01((t - bc) / 0.4)
        if u < 1:
            lf = loaf(420, 420, True)
            put(img, lf, 330, 1640 - 210 + 20 * u, 1 - u)
        if u > 0:
            j = jar(360)
            floor_shadow(img, 330, 1650, 230, 0.3)
            put(img, j, 330, 1640 - 236, 0.4 + 0.6 * ease_back(u, 2.0))
        hx, hy = a['hand_l']
        put(img, bread(230, spread=clamp01((t - bc) / 1.0)), hx, hy - 70, 1.0, -12 + 4 * math.sin(t * 5))
        if t >= ev:
            d = ImageDraw.Draw(img)
            for k in range(5):
                ph = ((t - ev) * 0.8 + k / 5) % 1
                heart_d(d, 330 + (k - 2) * 70, 1150 - ph * 300, 26 * (1 - ph * 0.5), (240, 90, 130))

# 3  After World War Two, cocoa was super hard to get.
class N3(Sc):
    def events(self):
        return [(0.05, 'wind', 0.4), (self.we('cocoa') - 0.03, 'pop', 0.4), (self.we('hard') - 0.05, 'thud', 0.4)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('cocoa'), 1.2, 1.26, CX, 1300), (self.we('hard'), 1.12, 1.16, CX - 60, 1150)]
    def plate(self):
        return street_plate()
    def dyn(self, img, t):
        h = self.we('hard')
        P(img, VENDOR, 640, 1900, t, 'sad' if t > h else 'nervous', arm_l=150 if t > h else 40, arm_r=150 if t > h else 40, scale=0.8, phase=1)
        stall_table(img, 1520)
        P(img, PIETRO, 1050, 2250, t, 'think' if t < h else 'sad', talk=talk_frame(t) and t < h, arm_l=100 + 10 * math.sin(t * 6), arm_r=20, scale=0.95, look_dir=-1)
        P(img, dict(PRESETS['grandma'], hair_color=(70, 50, 40), glasses=False, top=(90, 140, 200)), 230, 2230, t, 'shocked' if t > h else 'smile', arm_l=20, arm_r=110, scale=0.9, phase=2, look_dir=1)

# 4  So pastry chef Pietro Ferrero got creative.
class N4(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('creative') - 0.05, 'ding', 0.6)]
    def shots(self):
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('Pietro'), 1.2, 1.26, CX, 1150), (self.we('creative'), 1.12, 1.16, CX + 40, 1250)]
    def plate(self):
        return pastry_plate()
    def dyn(self, img, t):
        c = self.we('creative')
        on = t >= c - 0.1
        a = P(img, PIETRO, CX, 2050, t, 'happy' if on else 'think', talk=talk_frame(t) and not on,
              arm_l=150 if on else 40, arm_r=(160 if on else 110) + 8 * math.sin(t * 8), scale=1.0)
        display_case(img, 1560)
        # basket of hazelnuts on the case
        d = ImageDraw.Draw(img)
        d.chord([820, 1420, 1180, 1660], 180, 360, fill=(200, 150, 90))
        nut_heap(img, 1000, 1545, 170, 90, 3, 22)
        d.rectangle([820, 1530, 1180, 1580], fill=(180, 130, 75))
        hx, hy = a['hand_r']
        put(img, nut(54), hx, hy - 60 - (30 if on else 0) * math.sin(clamp01((t - c) / 0.3) * math.pi), 1.0, 10 * math.sin(t * 4))
        if on:
            u = t - c
            for k in range(8):
                ang = k * math.pi / 4 + u
                r = 110 + 30 * math.sin(u * 6)
                sparkle(d, hx + math.cos(ang) * r, hy - 60 + math.sin(ang) * r, 20)

# 5  He used mostly hazelnuts and a little cocoa.
class N5(Sc):
    def events(self):
        e = [(0.05, 'rattle', 0.5), (self.we('hazelnuts'), 'rattle', 0.5), (self.we('little') - 0.03, 'pop', 0.35)]
        return e
    def shots(self):
        return [(0.0, 1.05, 1.1, CX, 1152), (self.we('hazelnuts'), 1.22, 1.28, CX + 40, 1250), (self.we('little'), 1.4, 1.46, CX + 160, 1100)]
    def plate(self):
        return counter_plate(1)
    def dyn(self, img, t):
        lt_ = self.we('little')
        a = P(img, PIETRO, 300, 2120, t, 'proud' if t > lt_ else 'happy', arm_l=20, arm_r=100 + 15 * math.sin(t * 7), scale=0.95)
        counter_front(img, 1660, (235, 225, 210), (170, 110, 80))
        bw = bowl(640, 1.0)
        bx, by = 760, 1660 - bw.height / 2 + 10
        floor_shadow(img, bx, 1680, 360, 0.3)
        # heap inside bowl grows
        g = clamp01(t / max(0.5, lt_))
        put(img, bw, bx, by)
        nut_heap(img, bx, by - bw.height * 0.32, 230, 40 + 120 * g, 5, 24)
        # stream of falling nuts from a scoop
        d = ImageDraw.Draw(img)
        if t < lt_ + 0.2:
            for k in range(14):
                ph = (t * 2.2 + k / 14) % 1
                x = bx - 40 + math.sin(k * 2.1) * 50
                y = 650 + ph * (by - bw.height * 0.3 - 650)
                put(img, nut(26, (k * 40) % 360), x, y)
            d.polygon([(bx - 200, 540), (bx + 120, 560), (bx + 60, 680), (bx - 150, 660)], fill=(200, 205, 212), outline=(140, 145, 155))
        # tiny spoon of cocoa
        if t >= lt_ - 0.3:
            u = clamp01((t - (lt_ - 0.3)) / 0.5)
            sx, sy = bx + 300, 1050 + 150 * u
            d.line([(sx, sy), (sx + 220, sy - 160)], fill=(190, 190, 198), width=14)
            d.ellipse([sx - 45, sy - 25, sx + 35, sy + 25], fill=(190, 190, 198))
            if u < 1:
                d.ellipse([sx - 35, sy - 30, sx + 25, sy + 5], fill=(80, 45, 25))
            else:
                ph = clamp01((t - lt_ - 0.2) / 0.6)
                for k in range(12):
                    px = sx - 20 + (k - 6) * 9 * (1 + ph)
                    py = sy + ph * 230 + (k % 3) * 10
                    d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(80, 45, 25))

# 6  In 1946, it was a solid loaf people sliced onto bread.
class N6(Sc):
    def events(self):
        e = [(0.05, 'rustle', 0.5), (self.we('solid') - 0.03, 'thud', 0.5)]
        for k in range(3):
            e.append((self.ct(k), 'scratch', 0.45))
        return e
    def ct(self, k):
        a = self.we('people')
        return a + 0.6 * k
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('solid'), 1.2, 1.26, CX - 40, 1400), (self.we('people'), 1.08, 1.12, CX, 1250)]
    def plate(self):
        return dining_plate()
    def dyn(self, img, t):
        pe = self.we('people')
        a = P(img, MAMMA, 330, 1930, t, 'happy' if t > pe else 'smile', talk=talk_frame(t) and t < pe,
              arm_l=20, arm_r=100 + (25 * math.sin((t - pe) * 10) if t > pe else 0), scale=0.95)
        kids_n = 0 if t < pe else min(3, 1 + int((t - pe) / 0.6))
        k_ = P(img, NKID, 1040, 1960, t, 'happy' if kids_n else 'shocked', arm_l=120 + 10 * math.sin(t * 8), arm_r=20, scale=0.85, phase=2, look_dir=-1)
        cloth_table(img, 1620)
        board(img, 660, 1620, 520)
        lf = loaf(420, 400, True)
        floor_shadow(img, 660, 1630, 260, 0.3)
        put(img, lf, 660, 1620 - lf.height / 2)
        hx, hy = a['hand_r']
        put(img, knife(300), hx + 110, hy, 1.0, -30 + (20 * math.sin((t - pe) * 10) if t > pe else 0))
        kx, ky = k_['hand_l']
        put(img, bread(230, slab=kids_n > 0), kx, ky - 60, 1.0, 8 * math.sin(t * 4))
        # finished slices on plates
        d = ImageDraw.Draw(img)
        for k in range(kids_n - 1):
            d.ellipse([900 + k * 150 - 70, 1700, 900 + k * 150 + 70, 1760], fill=(250, 250, 250), outline=(80, 120, 190), width=6)
            put(img, bread(130, slab=True), 900 + k * 150, 1690)
        chip_at(img, '1946', 1000, 720, t, self.we('1946'), dot=(215, 60, 60))

# 7  In 1951, it became a creamy spread called Supercrema.
class N7(Sc):
    def events(self):
        return [(0.05, 'tick', 0.4), (self.we('creamy') - 0.05, 'bloop', 0.5), (self.we('called') - 0.05, 'ding', 0.5)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('creamy'), 1.2, 1.26, CX - 60, 1250), (self.we('called'), 1.1, 1.14, CX + 80, 1350)]
    def plate(self):
        return factory_plate()
    def dyn(self, img, t):
        cr = self.we('creamy')
        d = ImageDraw.Draw(img)
        # swirling cream visible in vat window
        d.ellipse([200, 860, 580, 940], fill=(105, 62, 32))
        for k in range(3):
            a0 = (t * 200 + k * 120) % 360
            d.arc([230 + k * 40, 870 + k * 6, 550 - k * 40, 930 - k * 6], a0, a0 + 120, fill=(160, 105, 65), width=8)
        # filler nozzle stream
        conveyor(img, 1560, t)
        off = (t * 160) % 260
        for k in range(-1, 6):
            x = k * 260 + off - 60
            near = abs(x - 820) < 70
            put(img, jar(170, lid=not near and x > 820, level=1.0 if x > 820 else (0.6 if near else 0.0)), x, 1560 - 112)
        d.rectangle([810, 1300, 830, 1450], fill=(105, 62, 32))
        a = P(img, WORKERN, 1060, 2300, t, 'happy' if t > cr else 'smile', talk=talk_frame(t) and t < cr,
              arm_l=140 + 10 * math.sin(t * 7) if t > cr else 60, arm_r=30, scale=0.9, look_dir=-1)
        hx, hy = a['hand_l']
        if t > cr:
            put(img, bread(200, spread=1.0), hx, hy - 60, 1.0, -10)
        chip_at(img, '1951', 1000, 820, t, self.we('1951'), dot=(60, 150, 220))

# 8  In 1964, his son Michele renamed it Nutella.
class N8(Sc):
    def events(self):
        return [(0.05, 'pop', 0.4), (self.we('renamed') - 0.05, 'riser', 0.35), (self.we('renamed') + 0.35, 'party', 0.45)]
    def shots(self):
        return [(0.0, 1.0, 1.05, CX, 1152), (self.we('Michele'), 1.18, 1.24, CX - 120, 1150), (self.we('renamed'), 1.1, 1.16, CX - 40, 1050)]
    def plate(self):
        return office_plate()
    def dyn(self, img, t):
        rn = self.we('renamed')
        on = t >= rn
        a = P(img, MICHELE, 470, 2080, t, 'proud' if on else 'smile', talk=talk_frame(t) and not on,
              arm_l=20, arm_r=(165 if on else 90) + 5 * math.sin(t * 8), scale=1.0)
        P(img, PARTNER, 1060, 2120, t, 'happy' if on else 'think', arm_l=(130 + 25 * math.sin(t * 14)) if on else 30, arm_r=(130 + 25 * math.sin(t * 14 + 1)) if on else 30, scale=0.9, phase=1, look_dir=-1)
        table_front(img, 1700, (120, 85, 60), (160, 115, 80))
        hx, hy = a['hand_r']
        put(img, jar(330), hx, hy - 190, 1.0, 4 * math.sin(t * 5))
        if on:
            d = ImageDraw.Draw(img)
            u = t - rn
            for k in range(14):
                ang = math.radians(k * 360 / 14 + u * 40)
                r = 220 + 60 * (u % 1)
                sparkle(d, hx + math.cos(ang) * r, hy - 190 + math.sin(ang) * r, 18, [(255, 230, 120), (255, 255, 255), (250, 160, 190)][k % 3])
        chip_at(img, '1964', 1000, 760, t, self.we('1964'), dot=(200, 120, 60))

# 9  Nut, for hazelnut, plus ella, a sweet-sounding Italian ending.
class N9(Sc):
    def events(self):
        return [(0.02, 'bigpop', 0.45), (self.we('ella') - 0.04, 'chime', 0.5), (self.we('sweet') - 0.03, 'pop', 0.4)]
    def shots(self):
        return [(0.0, 1.05, 1.1, CX - 140, 1150), (self.we('ella'), 1.05, 1.1, CX + 140, 1150), (self.we('sweet'), 1.0, 1.04, CX, 1200)]
    def plate(self):
        return bedroom_plate()
    def dyn(self, img, t):
        el = self.we('ella')
        sw = self.we('sweet')
        expr = 'shocked' if t < el else ('wink' if t > sw else 'happy')
        a = P(img, NTEEN, 640, 2160, t, expr, talk=talk_frame(t), arm_l=150 if t > sw else 100, arm_r=110 + 10 * math.sin(t * 6), scale=0.98)
        # giant hazelnut on the left
        u = clamp01(t / 0.3)
        put(img, nut(150), 250, 1150 + 20 * math.sin(t * 3), 0.3 + 0.7 * ease_back(u, 2.0), 10 * math.sin(t * 2))
        hx, hy = a['hand_r']
        put(img, jar(300), hx + 30, hy - 170, 1.0, 5 * math.sin(t * 4))
        if t >= el:
            d = ImageDraw.Draw(img)
            v = t - el
            for k in range(7):
                ph = (v * 0.7 + k / 7) % 1
                heart_d(d, 1000 + (k - 3) * 45 + 30 * math.sin(k + v * 3), 1250 - ph * 520, 30 * (1 - ph * 0.4), [(240, 80, 120), (255, 150, 190), (250, 110, 150)][k % 3])

# 10  Now its maker buys about a quarter of the world's hazelnuts, all because of a brick you had to slice.
class N10(Sc):
    def events(self):
        return [(0.05, 'rattle', 0.5), (self.we('quarter') - 0.03, 'cash', 0.5), (self.we('brick') - 0.08, 'swipe', 0.35),
                (self.we('slice') - 0.1, 'scratch', 0.5)]
    def shots(self):
        b = self.we('brick')
        return [(0.0, 1.0, 1.06, CX, 1152), (self.we('quarter'), 1.15, 1.22, CX + 80, 1300), (b - 0.05, 1.18, 1.22, CX, 1100)]
    def plate(self):
        self.cp = counter_plate(0)
        return warehouse_plate()
    def dyn(self, img, t):
        b = self.we('brick') - 0.05
        if t >= b:
            img.paste(self.cp, (0, 0))
            brick_scene(img, t, self.we('slice') - 0.12, 'happy')
            return
        q = self.we('quarter')
        nut_heap(img, CX, 1900, 520, 380, 8, 26)
        a = P(img, FARMER, 1050, 2200, t, 'shocked' if t > q else 'happy', arm_l=130 + 30 * math.sin(t * 6), arm_r=30, scale=0.92, look_dir=-1)
        # scoop throwing nuts
        d = ImageDraw.Draw(img)
        hx, hy = a['hand_l']
        d.line([(hx, hy), (hx - 160, hy + 120)], fill=(130, 90, 55), width=16)
        d.polygon([(hx - 230, hy + 90), (hx - 120, hy + 150), (hx - 160, hy + 230), (hx - 270, hy + 170)], fill=(190, 195, 205))
        for k in range(10):
            ph = (t * 1.3 + k / 10) % 1
            put(img, nut(24, (k * 50) % 360), hx - 200 - ph * 500, hy + 100 - 400 * math.sin(ph * math.pi) + ph * 300)
        P(img, NTEEN, 240, 2240, t, 'shocked' if t > q else 'smile', arm_l=20, arm_r=150 if t > q else 90, scale=0.85, phase=2, look_dir=1)
        chip_at(img, '~25%', CX, 760, t, q, dot=(165, 100, 50))

SCENES = [N0, N1, N2, N3, N4, N5, N6, N7, N8, N9, N10]
