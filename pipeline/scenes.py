"""An 11-year-old invented the Popsicle by accident (2026-11-13)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, table_bg, grain_map
from mw_scenes import glow, stamp_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of, keyframes
from cart_scenes import figure, ground_shadow, red_x

GOLD = (240, 160, 60)
RED = (200, 60, 50)
YEL = (255, 210, 60)
BLUE = (40, 120, 200)
ICE = (120, 200, 255)
POPC = '#EE5A3C'      # soda-orange/red ice
POPC2 = '#F2A23A'
WOOD = (214, 172, 112)

class Base(S):
    focus = (CX, CY)
    z0, z1 = 1.0, 1.06

def rgb_t(c):
    if not isinstance(c, str):
        return tuple(c)
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))

# ---------------------------------------------------------------- props
def stick_sprite(w=78, L=330):
    ss = 2
    im = Image.new('RGBA', (w * ss, L * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * ss - 1, L * ss - 1), radius=w * ss // 2, fill=WOOD + (255,))
    arr = np.asarray(im, np.float32) / 255
    hh, ww = arr.shape[:2]
    u = np.linspace(0, 1, ww)[None, :]
    k = 0.72 + 0.4 * np.sin(np.pi * (u * 0.9 + 0.05)) ** 0.6 - 0.15 * u
    n = smooth_noise(hh, ww, 6, 31, 2)
    gr = 0.92 + 0.12 * np.sin((u * 9 + n * 2.5) * np.pi) * 0.5
    arr[..., :3] *= (k * gr)[..., None]
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    return im.resize((w, L), Image.LANCZOS)

def shade_x(arr, a, hi=0.27, k0=0.70):
    hh, ww = arr.shape[:2]
    u = np.linspace(0, 1, ww)[None, :]
    k = k0 + 0.48 * np.sin(np.pi * (u * 0.9 + 0.05)) ** 0.7 - 0.22 * u
    arr = arr * k[..., None]
    hl = np.exp(-((u - hi) / 0.045) ** 2) * 0.55
    arr = arr + hl[..., None] * (1 - arr) * 0.9
    return arr

_POP = {}
def popsicle_sprite(w=380, h=600, color=POPC, stick_L=330, frost=0.35, bite=False, melt=0.0):
    """Classic ice pop: rounded top, wooden stick out of the bottom. Returns sprite (stick bottom centre at bottom)."""
    key = (w, h, color, stick_L, frost, bite, round(melt, 2))
    if key in _POP:
        return _POP[key]
    ss = 2
    W_, H_ = w + 60, h + stick_L - 40 + 60
    m = Image.new('L', (W_ * ss, H_ * ss), 0)
    d = ImageDraw.Draw(m)
    x0, y0 = 30, 30
    d.rounded_rectangle((x0 * ss, y0 * ss, (x0 + w) * ss, (y0 + h) * ss), radius=int(w * 0.48 * ss), fill=255)
    d.rounded_rectangle((x0 * ss, (y0 + h * 0.5) * ss, (x0 + w) * ss, (y0 + h) * ss), radius=int(36 * ss), fill=255)
    if melt > 0:
        rng = np.random.default_rng(5)
        for j in range(4):
            dx = x0 + w * (0.15 + 0.22 * j) + rng.uniform(-15, 15)
            ln = (40 + rng.uniform(0, 80)) * melt
            r = 22 + rng.uniform(0, 10)
            d.rounded_rectangle(((dx - r) * ss, (y0 + h - 30) * ss, (dx + r) * ss, (y0 + h + ln) * ss), radius=int(r * ss), fill=255)
    m = m.resize((W_, H_), Image.LANCZOS)
    a = np.asarray(m, np.float32) / 255
    col = np.array(rgb_t(color), np.float32) / 255
    arr = np.broadcast_to(col, a.shape + (3,)).copy()
    yy = np.linspace(0, 1, H_)[:, None]
    arr = arr * (1.05 - 0.2 * yy)[..., None]
    arr = shade_x(arr, a)
    n = smooth_noise(H_, W_, 4, 7, 2)
    fr = np.clip((n - 0.55) * 4, 0, 1) * frost
    arr = arr * (1 - fr[..., None]) + np.array([0.95, 0.97, 1.0]) * fr[..., None]
    ice = Image.fromarray((np.dstack([np.clip(arr, 0, 1), a]) * 255).astype(np.uint8), 'RGBA')
    out = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    st = stick_sprite(int(w * 0.21), stick_L)
    out.alpha_composite(st, (int(x0 + w / 2 - st.width / 2), int(y0 + h - 60)))
    out.alpha_composite(ice)
    # crisp rim highlight
    _POP[key] = out
    return out

def cup_ice_sprite(w=330, h=380, color=POPC, stick_L=300):
    """Ice frozen in the shape of a cup, hanging under a stick (stick on top)."""
    ss = 2
    W_, H_ = w + 60, h + stick_L + 40
    m = Image.new('L', (W_ * ss, H_ * ss), 0)
    d = ImageDraw.Draw(m)
    x0, y0 = 30, stick_L - 10
    bw = w * 0.72
    d.polygon([(x0 * ss, y0 * ss), ((x0 + w) * ss, y0 * ss), ((x0 + w / 2 + bw / 2) * ss, (y0 + h) * ss),
               ((x0 + w / 2 - bw / 2) * ss, (y0 + h) * ss)], fill=255)
    d.rounded_rectangle(((x0 + w / 2 - bw / 2) * ss, (y0 + h - 50) * ss, (x0 + w / 2 + bw / 2) * ss, (y0 + h + 12) * ss), radius=30 * ss, fill=255)
    m = m.resize((W_, H_), Image.LANCZOS)
    a = np.asarray(m, np.float32) / 255
    col = np.array(rgb_t(color), np.float32) / 255
    arr = np.broadcast_to(col, a.shape + (3,)).copy()
    arr = shade_x(arr, a)
    n = smooth_noise(H_, W_, 4, 9, 2)
    fr = np.clip((n - 0.5) * 4, 0, 1) * 0.45
    arr = arr * (1 - fr[..., None]) + np.array([0.95, 0.97, 1.0]) * fr[..., None]
    ice = Image.fromarray((np.dstack([np.clip(arr, 0, 1), a]) * 255).astype(np.uint8), 'RGBA')
    out = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    st = stick_sprite(64, stick_L + 60)
    out.alpha_composite(st, (int(x0 + w / 2 - 32), 0))
    out.alpha_composite(ice)
    return out

_CUP = {}
def cup_sprite(w=380, h=440, level=0.72, liquid=(238, 120, 60), frozen=0.0, stick=True, stick_ang=8):
    """Glass of soda water on its own; frozen 0..1 turns it into opaque frosty ice. Base at bottom of sprite."""
    key = (w, h, round(level, 2), liquid, round(frozen, 2), stick, stick_ang)
    if key in _CUP:
        return _CUP[key]
    ss = 2
    stick_L = 380
    W_, H_ = w + 140, h + stick_L
    im = Image.new('RGBA', (W_ * ss, H_ * ss), (0, 0, 0, 0))
    x0, y0 = 70, stick_L - 40
    bw = w * 0.76
    def P(x, y):
        return (x * ss, y * ss)
    body = [P(x0, y0), P(x0 + w, y0), P(x0 + w / 2 + bw / 2, y0 + h), P(x0 + w / 2 - bw / 2, y0 + h)]
    d = ImageDraw.Draw(im)
    d.polygon(body, fill=(200, 230, 245, 70))
    # liquid
    ly = y0 + h * (1 - level)
    fx = lambda y: (w - (w - bw) * (y - y0) / h) / 2
    lq = [P(x0 + w / 2 - fx(ly), ly), P(x0 + w / 2 + fx(ly), ly), P(x0 + w / 2 + bw / 2 - 6, y0 + h - 8), P(x0 + w / 2 - bw / 2 + 6, y0 + h - 8)]
    lc = tuple(int(c * (1 - frozen) + c2 * frozen) for c, c2 in zip(liquid, (240, 96, 64)))
    d.polygon(lq, fill=lc + (int(170 + 85 * frozen),))
    im2 = Image.new('RGBA', im.size, (0, 0, 0, 0))
    if stick:
        st = stick_sprite(54 * ss, stick_L * ss).rotate(stick_ang, expand=True, resample=Image.BICUBIC)
        im2.alpha_composite(st, (int((x0 + w / 2 - 50) * ss), int((y0 - stick_L * 0.42) * ss)))
    im2.alpha_composite(im)
    im = im2
    d = ImageDraw.Draw(im)
    d.polygon(lq, fill=lc + (int(110 + 120 * frozen),))
    d.ellipse((P(x0 + w / 2 - fx(ly), ly - 22)[0], P(0, ly - 22)[1], P(x0 + w / 2 + fx(ly), 0)[0], P(0, ly + 22)[1]),
              fill=tuple(min(255, int(c * 1.15)) for c in lc) + (230,))
    # glass rim + highlights
    d.ellipse((P(x0, y0 - 30)[0], P(0, y0 - 30)[1], P(x0 + w, 0)[0], P(0, y0 + 30)[1]), outline=(235, 248, 255, 230), width=7 * ss)
    d.line([P(x0 + 34, y0 + 30), P(x0 + w / 2 - bw / 2 + 30, y0 + h - 40)], fill=(255, 255, 255, 170), width=16 * ss)
    d.line([P(x0 + w - 30, y0 + 40), P(x0 + w / 2 + bw / 2 - 22, y0 + h - 60)], fill=(255, 255, 255, 90), width=8 * ss)
    d.line([body[1], body[2]], fill=(220, 240, 250, 200), width=5 * ss)
    d.line([body[0], body[3]], fill=(220, 240, 250, 200), width=5 * ss)
    d.ellipse((P(x0 + w / 2 - bw / 2, y0 + h - 18)[0], P(0, y0 + h - 18)[1], P(x0 + w / 2 + bw / 2, 0)[0], P(0, y0 + h + 14)[1]), outline=(220, 240, 250, 200), width=6 * ss)
    im = im.resize((W_, H_), Image.LANCZOS)
    if frozen > 0:
        # frost overlay on the glass
        arr = np.asarray(im, np.float32) / 255
        n = smooth_noise(H_, W_, 5, 21, 3)
        m = Image.new('L', (W_, H_), 0)
        ImageDraw.Draw(m).polygon([(x0, y0), (x0 + w, y0), (x0 + w / 2 + bw / 2, y0 + h), (x0 + w / 2 - bw / 2, y0 + h)], fill=255)
        mk = np.asarray(m, np.float32) / 255 * np.clip((n - 0.35) * 2.2, 0, 1) * frozen * 0.8
        arr[..., :3] = arr[..., :3] * (1 - mk[..., None]) + mk[..., None] * np.array([0.93, 0.97, 1.0])
        arr[..., 3] = np.maximum(arr[..., 3], mk)
        im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    _CUP[key] = im
    return im

def draw_cup(img, sp, cx, base_y, scale=1.0, shadow=True):
    s2 = sp if abs(scale - 1) < 1e-3 else sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.LANCZOS)
    if shadow:
        ground_shadow(img, cx, base_y - 4, s2.width * 0.7, 0.45)
    paste_at(img, s2, cx - s2.width / 2, base_y - s2.height + 4 * scale)

def sparkles(img, cx, cy, R, t, n=10, seed=0, size=26, color=(255, 255, 255)):
    rng = np.random.default_rng(seed)
    ov = OV(img, cx - R - 60, cy - R - 60, cx + R + 60, cy + R + 60)
    for j in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rr = R * rng.uniform(0.55, 1.0)
        ph = rng.uniform(0, 6.28)
        k = (math.sin(t * 7 + ph) + 1) / 2
        s = size * (0.4 + 0.8 * k)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        al = int(255 * (0.3 + 0.7 * k))
        ov.d.polygon(ov.pts([(x, y - s), (x + s * 0.22, y - s * 0.22), (x + s, y), (x + s * 0.22, y + s * 0.22),
                             (x, y + s), (x - s * 0.22, y + s * 0.22), (x - s, y), (x - s * 0.22, y - s * 0.22)]), fill=color + (al,))
    ov.commit()

def shards(img, cx, cy, t, n=12, seed=1, speed=900, color=(215, 240, 255)):
    rng = np.random.default_rng(seed)
    ov = OV(img, 0, 0, PW, PH)
    for j in range(n):
        a = rng.uniform(0, 2 * math.pi)
        v = speed * rng.uniform(0.5, 1.0)
        ph = rng.uniform(0, 1)
        tt = (t * 0.8 + ph) % 1.0
        x = cx + math.cos(a) * v * tt
        y = cy + math.sin(a) * v * tt + 300 * tt * tt
        s = 18 + 20 * rng.uniform(0, 1)
        ang = t * 6 + j
        pts = [(x + math.cos(ang + q) * s * (1 if q % 2 else 0.5), y + math.sin(ang + q) * s * (1 if q % 2 else 0.5)) for q in (0, 1.6, 3.1, 4.6)]
        ov.d.polygon(pts, fill=color + (int(230 * (1 - tt)),))
    ov.commit()

def sky_plate(c0, c1, seed=3, stars=0, glow_xy=None, glow_col=(255, 220, 150), glow_r=600):
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.9 + 0.08 * smooth_noise(PH, PW, 120, seed, 3))[..., None]
    if glow_xy:
        g = radial(PW, PH, glow_xy[0], glow_xy[1], glow_r, 1.6)
        arr = arr + g[..., None] * (np.array(glow_col) / 255 * 0.6)
    img = plate_img(np.clip(arr, 0, 1))
    if stars:
        rng = np.random.default_rng(seed)
        d = ImageDraw.Draw(img)
        for _ in range(stars):
            x, y, r = rng.uniform(0, PW), rng.uniform(0, 1200), rng.uniform(2, 5)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 240, 255))
    return img

def porch(img, night=0.0, warm=0.0):
    """Porch railing across the frame (rail top at y=1420) + floor planks below. Darkened by night."""
    lay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    base = np.array([176, 120, 74], np.float32)
    k = (1 - 0.62 * night) * (1 + 0.1 * warm)
    tint = np.array([1 - 0.25 * night, 1 - 0.15 * night, 1 + 0.15 * night])
    c = lambda m: tuple(int(min(255, v)) for v in base * m * k * tint) + (255,)
    # floor
    d.rectangle((0, 1880, PW, PH), fill=c(0.75))
    for y in range(1880, PH, 70):
        d.line([(0, y), (PW, y)], fill=c(0.5), width=5)
    # balusters
    for x in range(-20, PW + 60, 120):
        d.rounded_rectangle((x, 1470, x + 48, 1890), 8, fill=c(0.92))
        d.rectangle((x + 34, 1470, x + 48, 1890), fill=c(0.7))
    d.rectangle((0, 1830, PW, 1885), fill=c(0.82))
    # rail cap
    d.rounded_rectangle((-20, 1405, PW + 20, 1478), 10, fill=c(1.05))
    d.rectangle((-20, 1450, PW + 20, 1478), fill=c(0.72))
    # posts
    for x in (40, PW - 150):
        d.rectangle((x, 1300, x + 110, 1900), fill=c(0.95))
        d.rectangle((x + 80, 1300, x + 110, 1900), fill=c(0.7))
        d.rectangle((x - 12, 1280, x + 122, 1320), fill=c(1.08))
    sh, pad = shadow_of(lay, 14, 0.5)
    paste_at(img, sh, -pad + 10, -pad + 18)
    img.alpha_composite(lay)

RAIL = 1418

def moon(img, cx, cy, r, a=1.0):
    glow(img, cx, cy, r * 2.6, (200, 220, 255), 0.5 * a)
    ov = OV(img, cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4)
    ov.d.ellipse(ov.box(cx - r, cy - r, cx + r, cy + r), fill=(250, 248, 230, int(255 * a)))
    ov.d.ellipse(ov.box(cx - r * 0.5, cy - r * 0.3, cx - r * 0.15, cy + r * 0.05), fill=(225, 222, 205, int(255 * a)))
    ov.d.ellipse(ov.box(cx + r * 0.2, cy + r * 0.25, cx + r * 0.5, cy + r * 0.55), fill=(228, 225, 208, int(255 * a)))
    ov.commit()

def thermo_sprite(level, w=150, h=760):
    """level 0..1 of the tube; a red line marks freezing (32F) at 0.42."""
    im = Image.new('RGBA', (w + 200, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0 = 20
    d.rounded_rectangle((x0, 0, x0 + w, h), radius=w // 2, fill=(250, 250, 250, 255), outline=(40, 40, 46, 255), width=8)
    br = w * 0.42
    cx = x0 + w / 2
    tube_top, tube_bot = 50, h - 2 * br - 10
    lv = tube_bot - (tube_bot - tube_top) * level
    col = (60, 140, 230) if level < 0.42 else (220, 50, 40)
    d.rounded_rectangle((cx - 24, lv, cx + 24, h - br), radius=24, fill=col + (255,))
    d.ellipse((cx - br, h - 2 * br - 20, cx + br, h - 20), fill=col + (255,))
    for j in range(9):
        y = tube_bot - (tube_bot - tube_top) * j / 8
        d.line([(x0 + w - 44, y), (x0 + w - 12, y)], fill=(40, 40, 46, 255), width=6)
    fy = tube_bot - (tube_bot - tube_top) * 0.42
    d.line([(x0 + w - 10, fy), (x0 + w + 40, fy)], fill=(40, 120, 220, 255), width=10)
    d.text((x0 + w + 48, fy - 40), '32°F', font=font(56), fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(20, 20, 30, 255))
    return im

def frost_edges(img, k, seed=4):
    if k <= 0:
        return
    n = smooth_noise(PH // 4, PW // 4, 20, seed, 3)
    yy, xx = np.mgrid[0:PH // 4, 0:PW // 4].astype(np.float32)
    e = np.minimum.reduce([xx, yy, PW // 4 - xx, PH // 4 - yy]) / (PW / 4)
    m = np.clip((0.28 * k - e) * 6 + (n - 0.5) * 1.2 * k, 0, 1) * min(1, k * 1.5)
    a = Image.fromarray((m * 220).astype(np.uint8)).resize((PW, PH), Image.BICUBIC)
    lay = Image.new('RGBA', (PW, PH), (225, 240, 255, 0))
    lay.putalpha(a)
    img.alpha_composite(lay)

# ---------------------------------------------------------------- shared plates
_PL = {}
def summer_plate(seed=2):
    if 'summer' not in _PL:
        arr = vgrad(PW, PH, [(0, '#5EC8F0'), (0.6, '#2E8FD0'), (1, '#1B4F8F')])
        yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
        ang = np.arctan2(yy - 1050, xx - CX)
        rays = (np.sin(ang * 14) > 0.2).astype(np.float32) * 0.10
        rays = gaussian_filter(rays, 3)
        arr = arr + rays[..., None]
        arr = arr + radial(PW, PH, CX, 1050, 900, 1.5)[..., None] * np.array([0.35, 0.3, 0.12])
        _PL['summer'] = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    return _PL['summer'].copy()

def porch_plate(kind='day'):
    if kind in _PL:
        return _PL[kind].copy()
    if kind == 'day':
        img = sky_plate('#8FD3F5', '#E9F4E8', 5, glow_xy=(1050, 420), glow_r=700)
        night = 0.0
    elif kind == 'night':
        img = sky_plate('#0B1430', '#26355E', 6, stars=90)
        night = 1.0
    else:  # morning
        img = sky_plate('#F7B27A', '#FCE3B8', 7, glow_xy=(300, 1250), glow_col=(255, 200, 120), glow_r=900)
        night = 0.0
    d = ImageDraw.Draw(img)
    # distant trees / hills behind the railing
    rng = np.random.default_rng(3)
    hill = (60, 120, 80) if kind == 'day' else ((20, 30, 50) if kind == 'night' else (150, 110, 80))
    for j in range(14):
        x = j * 100 + rng.uniform(-30, 30)
        r = rng.uniform(110, 190)
        d.ellipse((x - r, 1330 - r * 0.9, x + r, 1330 + r), fill=hill + (255,))
    d.rectangle((0, 1320, PW, 1480), fill=hill + (255,))
    porch(img, night=night, warm=1.0 if kind == 'morning' else 0.0)
    _PL[kind] = img
    return img.copy()

def park_plate():
    if 'park' in _PL:
        return _PL['park'].copy()
    img = sky_plate('#5DB8EE', '#CFEFFF', 9, glow_xy=(1000, 300), glow_r=600)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1240, PW, 1400), fill=(40, 120, 190, 255))
    for y in range(1260, 1400, 34):
        d.line([(0, y), (PW, y)], fill=(120, 190, 235, 255), width=4)
    d.rectangle((0, 1400, PW, PH), fill=(238, 214, 160, 255))
    n = smooth_noise(PH - 1400, PW, 30, 4, 3)
    arr = to_arr(img)
    arr[1400:] *= (0.88 + 0.2 * n)[..., None]
    img = plate_img(arr)
    # roller coaster track silhouette (left)
    d = ImageDraw.Draw(img)
    pts = [(x, 1050 - 260 * math.sin(x / 140) ** 2) for x in range(-40, 620, 10)]
    d.line(pts, fill=(200, 60, 50, 255), width=22)
    for x in range(0, 600, 60):
        y = 1050 - 260 * math.sin(x / 140) ** 2
        d.line([(x, y), (x, 1240)], fill=(170, 50, 45, 255), width=10)
    _PL['park'] = img
    return img.copy()

def ferris(img, cx, cy, R, t):
    ov = OV(img, cx - R - 80, cy - R - 80, cx + R + 80, cy + R + 600)
    ov.d.line(ov.pts([(cx, cy), (cx - R * 0.6, cy + R + 300)]), fill=(240, 240, 245, 255), width=22)
    ov.d.line(ov.pts([(cx, cy), (cx + R * 0.6, cy + R + 300)]), fill=(240, 240, 245, 255), width=22)
    ov.d.ellipse(ov.box(cx - R, cy - R, cx + R, cy + R), outline=(250, 250, 255, 255), width=16)
    cols = [(230, 70, 60), (250, 200, 60), (60, 160, 230), (90, 190, 110)]
    for k in range(12):
        a = t * 0.6 + k * math.pi / 6
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        ov.d.line(ov.pts([(cx, cy), (x, y)]), fill=(240, 240, 245, 255), width=8)
        c = cols[k % 4]
        ov.d.rounded_rectangle(ov.box(x - 38, y, x + 38, y + 62), 12, fill=c + (255,))
    ov.d.ellipse(ov.box(cx - 30, cy - 30, cx + 30, cy + 30), fill=(200, 200, 210, 255))
    ov.commit()

def dark_plate(c0='#3A2C52', c1='#120C1E', seed=16):
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.85 + 0.1 * smooth_noise(PH, PW, 90, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, CX, 1000, 1500, 1.2))[..., None]
    return plate_img(vignette(arr, 0.45))

def paper_sprite(w=760, h=960, title='PATENT', year='1924'):
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((20, 20, 20 + w, 20 + h), fill=(246, 238, 214, 255), outline=(120, 100, 70, 255), width=6)
    f = font(92, FONT_SERIF)
    bb = f.getbbox(title)
    d.text((20 + (w - bb[2]) / 2, 60), title, font=f, fill=(50, 40, 30, 255))
    d.line([(80, 190), (w - 40, 190)], fill=(90, 70, 50, 255), width=5)
    for k in range(5):
        y = 240 + k * 46
        d.line([(80, y), (w - 40 - (k % 2) * 120, y)], fill=(150, 135, 110, 255), width=10)
    # line drawing of an ice pop
    cx, top = 20 + w / 2, 500
    d.rounded_rectangle((cx - 110, top, cx + 110, top + 300), radius=100, outline=(60, 50, 40, 255), width=8)
    d.rectangle((cx - 110, top + 160, cx + 110, top + 300), outline=None)
    d.rounded_rectangle((cx - 28, top + 296, cx + 28, top + 430), radius=26, outline=(60, 50, 40, 255), width=8)
    d.text((40 + 20, h - 70), 'FIG. 1', font=font(40, FONT_SERIF), fill=(60, 50, 40, 255))
    return im.rotate(-4, expand=True, resample=Image.BICUBIC)

def bubble_sprite(txt, size=78):
    f = font(size)
    bb = f.getbbox(txt)
    w, h = bb[2] - bb[0] + 90, bb[3] - bb[1] + 70
    im = Image.new('RGBA', (w + 40, h + 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=h // 2, fill=(255, 255, 255, 255), outline=(20, 20, 26, 255), width=8)
    d.polygon([(60, 20 + h - 6), (130, 20 + h - 6), (50, 20 + h + 80)], fill=(255, 255, 255, 255))
    d.line([(60, 20 + h - 2), (50, 20 + h + 80), (130, 20 + h - 4)], fill=(20, 20, 26, 255), width=8)
    d.text((20 + 45 - bb[0], 20 + 35 - bb[1]), txt, font=f, fill=(20, 20, 26, 255))
    return im

def quote_sprite(lines, size=96):
    f = font(size)
    lh = size + 26
    w = int(max(f.getlength(l) for l in lines)) + 120
    h = lh * len(lines) + 90
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 28, 20 + w, 28 + h), radius=40, fill=(0, 0, 0, 120))
    d.rounded_rectangle((20, 16, 20 + w, 16 + h), radius=40, fill=(255, 250, 238, 255), outline=(20, 20, 26, 255), width=8)
    for k, l in enumerate(lines):
        lw_ = f.getlength(l)
        d.text((20 + (w - lw_) / 2, 16 + 45 + k * lh), l, font=f, fill=(30, 26, 30, 255))
    return im

def icicle_sprite(w=200, h=420):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(10, 0), (w - 10, 0), (w / 2, h - 4)], fill=(200, 235, 255, 235))
    d.polygon([(w * 0.3, 0), (w * 0.45, 0), (w / 2, h * 0.8)], fill=(255, 255, 255, 200))
    d.line([(10, 0), (w / 2, h - 4), (w - 10, 0)], fill=(120, 190, 235, 255), width=6)
    return im

def spin_pop(img, sp, cx, cy, ang, scale=1.0):
    r = sp.rotate(ang, expand=True, resample=Image.BICUBIC)
    if abs(scale - 1) > 1e-3:
        r = r.resize((int(r.width * scale), int(r.height * scale)), Image.BICUBIC)
    sh, pad = shadow_of(r, 18, 0.45)
    paste_at(img, sh, cx - r.width / 2 - pad + 30, cy - r.height / 2 - pad + 40)
    paste_at(img, r, cx - r.width / 2, cy - r.height / 2)

# ====================================================================== scenes
class Hook(Base):
    """Frame 0: a giant ice pop already spinning, frost shards bursting off it."""
    z0, z1 = 1.0, 1.07
    punch = 0.0
    focus = (CX, CY)
    PY = 1235
    def make_shakes(self):
        return [(self.we('ACCIDENT') + 0.03, 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.7), (0.05, 'crack', 0.55), (self.we('11yearold') + 0.05, 'pop', 0.5),
                (self.we('popsicle'), 'chime', 0.5), (self.we('ACCIDENT') + 0.03, 'thud', 0.9)]
    def plate(self):
        self.pop = popsicle_sprite(500, 790, POPC, 420, 0.4)
        self.stamp = stamp_sprite('BY ACCIDENT!', 120, color=(226, 40, 40), angle=-7)
        return summer_plate()
    def hero(self, img, t, a_off=0.0):
        ang = 16 * math.sin(t * 3.2 + a_off) - 4
        bob = 18 * math.sin(t * 4.1)
        glow(img, CX, self.PY - 200, 700, (255, 240, 200), 0.55)
        shards(img, CX, self.PY - 300, t + 0.35, 14, 1, 1000)
        spin_pop(img, self.pop, CX, self.PY + bob, ang, 1.0 + 0.03 * math.sin(t * 6))
        sparkles(img, CX, self.PY - 300, 460, t, 12, 2, 34)
    def dyn(self, img, t):
        self.hero(img, t)
        pop(img, C('AGE 11', 86, bg=YEL), CX + 340, 1700, t, self.we('11yearold') + 0.05)
        stamp_in(img, self.stamp, CX, 2010, t, self.we('ACCIDENT') + 0.03)

class Stir(Base):
    z0, z1 = 1.22, 1.3
    focus = (CX, 1020)
    def make_shakes(self):
        return [(self.we('1905'), 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1905'), 'thud', 0.7), (self.we('Frank') - 0.03, 'pop', 0.5),
                (self.we('stirred'), 'tick', 0.4), (self.we('powder'), 'rustle', 0.6), (self.we('WATER') - 0.05, 'bloop', 0.5)]
    def plate(self):
        img = porch_plate('day')
        self.hand = get_hand(430, 1.75)
        self.st = stamp_sprite('1905', 150, color=BLUE, angle=-6)
        return img
    def dyn(self, img, t):
        tS, tP, tW = self.we('stirred'), self.we('powder'), self.we('WATER')
        lvl = 0.5 if t < tW - 0.2 else 0.5 + 0.22 * ease_out((t - tW + 0.2) / 0.5)
        ang = int(round(10 * math.sin(t * 9) / 4)) * 4 if t > tS else 6
        cup = cup_sprite(400, 470, lvl, (238, 120, 60), 0.0, True, ang)
        cx, by = CX, RAIL + 12
        draw_cup(img, cup, cx, by)
        top = (cx - 2 + 160 * math.sin(math.radians(-ang)) * 0.9, by - 660)
        draw_hand(img, self.hand, (top[0] + 20, top[1] + 70), 0.1)
        if t > tP - 0.1:  # powder falling in
            ov = OV(img, cx - 260, 300, cx + 260, by)
            rng = np.random.default_rng(int(t * 30))
            for j in range(40):
                x = cx + 70 + rng.normal(0, 26)
                y = 560 + rng.uniform(0, by - 560 - 300)
                ov.d.ellipse(ov.box(x - 7, y - 7, x + 7, y + 7), fill=(250, 150, 70, 230))
            ov.commit()
            pk = ease_back((t - tP + 0.1) / 0.3)
            ov = OV(img, cx - 40, 380, cx + 260, 620)
            ov.d.polygon(ov.pts([(cx + 30, 440), (cx + 230, 410), (cx + 250, 560), (cx + 90, 580)]), fill=(250, 245, 230, int(255 * clamp01(pk))))
            ov.d.text(ov.p(cx + 80, 470), 'SODA', font=font(44), fill=(220, 80, 40, int(255 * clamp01(pk))))
            ov.commit()
        stamp_in(img, self.st, CX - 280, 520, t, self.we('1905'))
        pop(img, C('FRANK EPPERSON', 72, bg=YEL), CX, 330, t, self.we('Frank') - 0.05, out_t=tP - 0.12)
        pop(img, C('SODA POWDER', 72, bg=(240, 110, 50), fg=(255, 255, 255)), CX, 330, t, tP - 0.05, out_t=tW - 0.1)
        pop(img, C('+ WATER', 80, bg=(60, 150, 230), fg=(255, 255, 255)), CX, 330, t, tW - 0.05)

class Overnight(Base):
    z0, z1 = 1.2, 1.3
    focus = (CX, 1060)
    def make_shakes(self):
        return [(self.we('OVERNIGHT'), 10, 0.25)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('outside'), 'wind', 0.5), (self.we('OVERNIGHT'), 'chime', 0.6), (self.we('wooden'), 'tick', 0.5)]
    def plate(self):
        self.day = porch_plate('day')
        self.night = porch_plate('night')
        self.cup = cup_sprite(400, 470, 0.72, (238, 120, 60), 0.0, True, 6)
        self.st = stamp_sprite('OVERNIGHT', 140, color=BLUE, angle=-6)
        return self.day.copy()
    def dyn(self, img, t):
        tO = self.we('OVERNIGHT')
        k = clamp01((t - tO + 0.6) / 0.6)
        if k > 0:
            img.paste(Image.blend(self.day, self.night, k), (0, 0))
        if k > 0.3:
            moon(img, 1060, 760 - 80 * k, 110, clamp01((k - 0.3) / 0.5))
        draw_cup(img, self.cup, CX, RAIL + 12)
        pop(img, C('LEFT OUTSIDE', 76, bg=YEL), CX, 330, t, self.we('outside') - 0.05, out_t=tO - 0.1)
        stamp_in(img, self.st, CX, 360, t, tO)
        if t > self.we('wooden') - 0.1:
            pop(img, C('STICK STILL IN IT', 62), CX - 170, 880, t, self.we('wooden') - 0.05)

class Freeze(Base):
    z0, z1 = 1.14, 1.24
    focus = (CX, 1080)
    def make_shakes(self):
        return [(self.we('FREEZING'), 16, 0.32)]
    def events(self):
        return [(0.02, 'wind', 0.6), (self.we('story'), 'pop', 0.4), (self.we('dropped'), 'riser', 0.5), (self.we('FREEZING'), 'crack', 0.8)]
    def plate(self):
        self.st = stamp_sprite('BELOW FREEZING', 104, color=(40, 120, 220), angle=-7)
        return porch_plate('night')
    def dyn(self, img, t):
        tD, tF = self.we('dropped'), self.we('FREEZING')
        fz = clamp01((t - tF + 0.1) / 0.8)
        moon(img, 1060, 640, 100)
        cup = cup_sprite(400, 470, 0.72, (238, 120, 60), round(fz * 5) / 5, True, 6)
        draw_cup(img, cup, CX - 170, RAIL + 12)
        lv = 0.72 - 0.47 * ease_in_out((t - tD + 0.2) / (tF - tD + 0.5))
        th = thermo_sprite(lv)
        paste_at(img, th, 900 - 95, 640)
        frost_edges(img, 0.25 + 0.75 * fz)
        if fz > 0:
            sparkles(img, CX - 170, 1150, 260, t, 8, 5, 26, (220, 240, 255))
        pop(img, C('AS THE STORY GOES...', 64, dot=GOLD), CX, 330, t, 0.1, out_t=tF - 0.1)
        stamp_in(img, self.st, CX, 380, t, tF)

class Morning(Base):
    z0, z1 = 1.1, 1.22
    focus = (CX, 1060)
    def make_shakes(self):
        return [(self.we('SOLID'), 16, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('morning'), 'chime', 0.5), (self.we('frozen'), 'crack', 0.6), (self.we('SOLID'), 'thud', 0.85)]
    def plate(self):
        img = porch_plate('morning')
        self.cup = cup_sprite(400, 470, 0.72, (238, 120, 60), 1.0, True, 6)
        self.st = stamp_sprite('FROZEN SOLID', 120, color=(40, 120, 220), angle=-7)
        return img
    def dyn(self, img, t):
        sun = 1250 - 160 * ease_out(t / 1.2)
        glow(img, 300, sun, 520, (255, 220, 140), 0.8)
        ov = OV(img, 160, sun - 140, 440, sun + 140)
        ov.d.ellipse(ov.box(180, sun - 120, 420, sun + 120), fill=(255, 236, 170, 255))
        ov.commit()
        porch_fg = getattr(self, 'fg', None)
        if porch_fg is None:
            lay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
            porch(lay, 0.0, 1.0)
            self.fg = lay
        img.alpha_composite(self.fg)
        draw_cup(img, self.cup, CX, RAIL + 12, 1.0 + 0.02 * math.sin(t * 5))
        sparkles(img, CX, 1080, 300, t, 12, 7, 32)
        pop(img, C('BY MORNING...', 76, bg=YEL), CX, 330, t, 0.05, out_t=self.we('SOLID') - 0.1)
        stamp_in(img, self.st, CX, 380, t, self.we('SOLID'))

class Lick(Base):
    z0, z1 = 1.0, 1.1
    focus = (CX, 1080)
    def make_shakes(self):
        return [(self.we('LICKED'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('pulled'), 'scratch', 0.5), (self.we('LICKED'), 'squeak', 0.6), (self.we('right'), 'pop', 0.5)]
    def plate(self):
        img = porch_plate('morning')
        self.cup = cup_sprite(400, 470, 0.0, (238, 120, 60), 0.5, False)
        self.ice = cup_ice_sprite(300, 350, '#F06240', 300)
        self.hand = get_hand(430, 1.75)
        self.st = stamp_sprite('SLURP!', 150, color=(226, 40, 40), angle=-8)
        return img
    def dyn(self, img, t):
        tP, tL = self.we('pulled'), self.we('LICKED')
        draw_cup(img, self.cup, CX, RAIL + 12)
        u = ease_in_out((t - tP + 0.1) / 0.6)
        ix, iy = CX, RAIL - 380 - 300 * u
        ang = 6 * math.sin(t * 5) * u
        r = self.ice.rotate(ang, expand=True, resample=Image.BICUBIC)
        sh, pad = shadow_of(r, 14, 0.4)
        paste_at(img, sh, ix - r.width / 2 - pad + 24, iy - r.height / 2 - pad + 30)
        paste_at(img, r, ix - r.width / 2, iy - r.height / 2)
        draw_hand(img, self.hand, (ix + 20, iy - r.height / 2 + 80), 0.1)
        if t > tL - 0.05:
            sparkles(img, ix, iy + 150, 300, t, 10, 9, 34)
        pop(img, C('FROZEN SODA ON A STICK', 60, bg=YEL), CX, 330, t, 0.15, out_t=tL - 0.08)
        stamp_in(img, self.st, CX, 1830, t, tL)

class Years(Base):
    z0, z1 = 1.14, 1.22
    focus = (CX, 1050)
    def make_shakes(self):
        return [(self.we('crazy'), 10, 0.25), (self.we('YEARS'), 20, 0.35)]
    def events(self):
        return [(0.02, 'scratch', 0.6), (self.we('crazy'), 'pop', 0.6), (self.we('waited'), 'tick', 0.5),
                (self.we('about'), 'tick', 0.5), (self.we('YEARS'), 'boom', 0.8)]
    def plate(self):
        self.st = stamp_sprite('18 YEARS!', 170, color=(226, 40, 40), angle=-8)
        self.pop = popsicle_sprite(300, 460, POPC, 280, 0.4)
        return dark_plate('#2E4D7A', '#0C1A30', 17)
    def dyn(self, img, t):
        tW, tY = self.we('waited'), self.we('YEARS')
        k = clamp01((t - tW) / (tY - tW + 0.05))
        year = 1905 + int(round(18 * ease_in_out(k)))
        # calendar card
        ov = OV(img, CX - 360, 560, CX + 360, 1360)
        ov.d.rounded_rectangle(ov.box(CX - 330, 600, CX + 330, 1330), 40, fill=(250, 248, 240, 255), outline=(30, 30, 36, 255), width=10)
        ov.d.rectangle(ov.box(CX - 325, 605, CX + 325, 780), fill=(214, 50, 44, 255))
        for x in (CX - 180, CX + 180):
            ov.d.rounded_rectangle(ov.box(x - 22, 570, x + 22, 650), 16, fill=(60, 60, 66, 255))
        f = font(240)
        txt = str(year)
        bb = f.getbbox(txt)
        flip = (t * 18) % 1 if 0 < k < 1 else 0
        ov.d.text(ov.p(CX - (bb[2] - bb[0]) / 2 - bb[0], 900 - bb[1] + 20 * flip), txt, font=f, fill=(30, 30, 36, 255))
        ov.commit()
        spin_pop(img, self.pop, 1060, 1350, 18 + 6 * math.sin(t * 4), 0.85)
        pop(img, C('THE CRAZY PART', 78, bg=YEL), CX, 330, t, self.we('crazy') - 0.05, out_t=tY - 0.1)
        stamp_in(img, self.st, CX, 420, t, tY)

class Park(Base):
    z0, z1 = 1.04, 1.12
    def make_shakes(self):
        return [(self.we('1923'), 10, 0.25), (self.we('NEPTUNE'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1923'), 'thud', 0.7), (self.we('sold'), 'cash', 0.6),
                (self.we('amusement'), 'party', 0.4), (self.we('NEPTUNE'), 'ding', 0.6)]
    def plate(self):
        img = park_plate()
        cols = [POPC, '#F2A23A', '#8E5BD8', '#E84A86', '#4FB6E8']
        self.pops = [popsicle_sprite(150, 230, c, 130, 0.3) for c in cols]
        self.st = stamp_sprite('1923', 160, color=BLUE, angle=-6)
        return img
    def dyn(self, img, t):
        tS, tN = self.we('sold'), self.we('NEPTUNE')
        ferris(img, 960, 820, 330, t)
        # stand
        ov = OV(img, 120, 1320, PW - 120, 2170)
        ov.d.rectangle(ov.box(180, 1920, PW - 180, 2160), fill=(250, 245, 235, 255), outline=(40, 40, 46, 255), width=8)
        for j in range(8):
            x = 180 + j * (PW - 360) / 8
            ov.d.rectangle(ov.box(x, 1920, x + (PW - 360) / 16, 2160), fill=(220, 60, 50, 255))
        ov.d.polygon(ov.pts([(140, 1460), (PW - 140, 1460), (PW - 180, 1560), (180, 1560)]), fill=(220, 60, 50, 255))
        ov.d.rectangle(ov.box(200, 1560, 220, 1920), fill=(240, 240, 240, 255))
        ov.d.rectangle(ov.box(PW - 220, 1560, PW - 200, 1920), fill=(240, 240, 240, 255))
        ov.commit()
        for j, sp in enumerate(self.pops):
            tj = tS - 0.1 + j * 0.12
            if t > tj:
                k = ease_back((t - tj) / 0.3, 2.0)
                x = 290 + j * 180
                paste_center(img, sp, x, 1790 - 6 * math.sin(t * 5 + j), scale=max(0.05, k))
        if t < tN - 0.05:
            stamp_in(img, self.st, 300, 420, t, self.we('1923'))
        pop(img, C('AMUSEMENT PARK', 66, bg=YEL), CX + 150, 330, t, self.we('amusement') - 0.05, out_t=tN - 0.1)
        pop(img, C('NEPTUNE BEACH', 84, bg=(40, 120, 200), fg=(255, 255, 255)), CX, 330, t, tN - 0.05)
        pop(img, C('ALAMEDA, CALIFORNIA', 52, dot=GOLD), CX, 470, t, tN + 0.25)

class Epsicle(Base):
    z0, z1 = 1.02, 1.1
    def make_shakes(self):
        return [(self.we('EPSICLE'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('EPSICLE'), 'bigpop', 0.8), (self.we('name'), 'pop', 0.6), (self.we('plus'), 'pop', 0.5)]
    def plate(self):
        self.pop = popsicle_sprite(360, 560, POPC, 320, 0.4)
        self.ic = icicle_sprite(170, 380)
        self.st = stamp_sprite('THE EPSICLE', 130, color=(214, 50, 44), angle=-7)
        return summer_plate()
    def dyn(self, img, t):
        tE, tN, tP = self.we('EPSICLE'), self.we('name'), self.we('plus')
        spin_pop(img, self.pop, CX, 1050, 8 * math.sin(t * 3), 1.0)
        stamp_in(img, self.st, CX, 380, t, tE)
        pop(img, C('EPPERSON', 76, bg=YEL), 370, 1820, t, tN - 0.08)
        pop(img, C('+', 96, bg=(255, 255, 255)), CX + 30, 1820, t, tP - 0.05)
        if t > tP:
            k = ease_back((t - tP) / 0.3, 2.0)
            paste_center(img, self.ic, 1050, 700, scale=max(0.05, k))
        pop(img, C('ICICLE', 76, bg=(120, 200, 255)), 990, 1820, t, tP + 0.15)

class Kids(Base):
    z0, z1 = 1.04, 1.12
    focus = (CX, 1100)
    def make_shakes(self):
        return [(self.we('THAT'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('KIDS'), 'pop', 0.6), (self.we('pops'), 'bigpop', 0.7), (self.we('THAT'), 'thud', 0.8)]
    def plate(self):
        img = summer_plate()
        ov = OV(img, 0, 1380, PW, PH)
        ov.d.ellipse(ov.box(-300, 1400, PW + 300, 2600), fill=(90, 170, 90, 255))
        ov.commit()
        self.kids = [figure(h, k, push=False) for h, k in ((720, 'man'), (650, 'woman'), (590, 'man'))]
        self.pops = [popsicle_sprite(90, 140, c, 90, 0.3) for c in (POPC, '#F2A23A', '#E84A86')]
        self.bub = bubble_sprite("POP'S 'SICLE!", 84)
        self.st = stamp_sprite('THE NAME STUCK', 104, color=(214, 50, 44), angle=-7)
        return img
    def dyn(self, img, t):
        tK, tP, tT = self.we('KIDS'), self.we('pops'), self.we('THAT')
        for j, (sp, info) in enumerate(self.kids):
            tj = 0.0 + j * 0.12
            if t < tj:
                continue
            k = ease_back((t - tj) / 0.32, 1.7)
            x = 300 + j * 330
            foot = 1480 + 260 * (1 - clamp01(k))
            hop = 14 * abs(math.sin(t * 6 + j))
            ground_shadow(img, x, 1480, 200)
            fx, fy = x - info['foot'][0], foot - info['foot'][1] - hop
            paste_at(img, sp, fx, fy)
            paste_center(img, self.pops[j], fx + info['hand'][0] + 10, fy + info['hand'][1] - 60)
        pop(img, C('HIS OWN KIDS', 76, bg=YEL), CX, 330, t, tK - 0.05, out_t=tT - 0.1)
        pop(img, self.bub, CX + 120, 640, t, tP - 0.05)
        stamp_in(img, self.st, CX, 380, t, tT)

class Broke(Base):
    z0, z1 = 1.02, 1.1
    def make_shakes(self):
        return [(self.we('1924'), 10, 0.25), (self.we('BROKE'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('patented'), 'tape', 0.5), (self.we('1924'), 'thud', 0.7),
                (self.we('later'), 'tick', 0.5), (self.we('BROKE'), 'buzzer', 0.7), (self.we('sold'), 'cash', 0.6)]
    def plate(self):
        self.paper = paper_sprite()
        self.st = stamp_sprite('BROKE', 180, color=(214, 50, 44), angle=-10)
        self.sold = stamp_sprite('RIGHTS SOLD', 120, color=(250, 200, 60), angle=6)
        return dark_plate('#7A5A3A', '#2A1A10', 18)
    def dyn(self, img, t):
        tB, tS = self.we('BROKE'), self.we('sold')
        k = ease_back(t / 0.35, 1.5)
        y = 1080 + 400 * (1 - clamp01(k))
        if t > tS:
            y += 900 * ease_in_out((t - tS - 0.2) / 0.6)
        paste_center(img, self.paper, CX, y)
        pop(img, C('PATENT: 1924', 80, bg=YEL), CX, 330, t, self.we('1924') - 0.05, out_t=self.we('later') - 0.1)
        pop(img, C('ONE YEAR LATER...', 72, dot=GOLD), CX, 330, t, self.we('later') - 0.05)
        stamp_in(img, self.st, CX, 1000, t, tB)
        stamp_in(img, self.sold, CX, 1830, t, tS + 0.05)

class Quote(Base):
    z0, z1 = 1.0, 1.1
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('said') , 'pop', 0.5), (self.we('i') + 0.05, 'tape', 0.5)]
    def plate(self):
        self.pop = popsicle_sprite(300, 460, POPC, 280, 0.2, melt=1.0)
        self.q = quote_sprite(['"I HAVEN\'T BEEN', 'THE SAME', 'SINCE."'], 100)
        return dark_plate('#34385A', '#0E1020', 19)
    def dyn(self, img, t):
        spin_pop(img, self.pop, 980, 1450 + 10 * math.sin(t * 2), -14, 1.1)
        # drips falling
        for j in range(3):
            ph = (t * 0.9 + j * 0.33) % 1
            ov = OV(img, 880, 1500, 1200, 2300)
            ov.d.ellipse(ov.box(980 + j * 30 - 14, 1700 + ph * 450, 980 + j * 30 + 14, 1740 + ph * 450), fill=(238, 90, 60, int(255 * (1 - ph))))
            ov.commit()
        pop(img, C('YEARS LATER...', 76, dot=GOLD), CX, 330, t, 0.05)
        pop(img, self.q, CX, 780, t, self.we('said') - 0.05)

class Outro(Hook):
    """Ice pops everywhere, then straight back to the giant spinning pop (loops into the hook)."""
    punch = 0.13
    def make_shakes(self):
        return []
    def events(self):
        return [(0.02, 'party', 0.4), (self.we('all') - 0.05, 'swipe', 0.6)]
    def plate(self):
        img = super().plate()
        grid = dark_plate('#3A6EA8', '#122A48', 20)
        cols = [POPC, '#F2A23A', '#8E5BD8', '#E84A86', '#4FB6E8', '#5CC46A']
        for r in range(6):
            for c in range(6):
                sp = popsicle_sprite(140, 210, cols[(r + c * 2) % 6], 120, 0.3)
                sp = sp.rotate(((r * 7 + c * 3) % 5 - 2) * 8, expand=True, resample=Image.BICUBIC)
                paste_at(grid, sp, 40 + c * 210 + (r % 2) * 60 - 40, 170 + r * 360)
        self.grid = grid.convert('RGB')
        return img
    def dyn(self, img, t):
        tN = self.we('all') - 0.05
        if t < tN:
            img.paste(self.grid, (0, 0))
            pop(img, C("NOW IT'S EVERYWHERE", 80, bg=YEL), CX, 1000, t, 0.05)
            return
        self.hero(img, t - tN + 2.0)
    def cam(self, t):
        tN = self.we('all') - 0.05
        dx, dy, dr = self.shake(t)
        if t < tN:
            z = 1.0 + 0.14 * (t / tN)
            return z, CX, CY, 0.0
        p = 1 - ease_out((t - tN) / 0.3)
        return 1.0 + 0.1 * p, CX, CY, 1.5 * p

SCENES = [Hook, Stir, Overnight, Freeze, Morning, Lick, Years, Park, Epsicle, Kids, Broke, Quote, Outro]
