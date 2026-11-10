import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import CX, CY, plate_img, dark_room
from mw_scenes import glow, stamp_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand
from cart_scenes import ground_shadow

# Great Molasses Flood (Boston, January 15, 1919)
GOLD = (240, 160, 60)
RED = (200, 50, 45)
YEL = (255, 210, 60)
DARK = (34, 36, 44)
WHITE = (255, 255, 255)
MOL = (58, 28, 10)
MOL_HI = (150, 78, 26)
BROWN = (110, 62, 30)

GROUND = 1300
_SP = {}
_PL = {}

# ====================================================================== backdrops
def street_plate(kind='winter', rail=True, seed=1):
    key = (kind, rail, seed)
    if key in _PL:
        return _PL[key].copy()
    if kind == 'winter':
        arr = vgrad(PW, PH, [(0, '#5E7590'), (0.45, '#A9B8C8'), (1, '#D9DEE4')])
    else:  # hot summer
        arr = vgrad(PW, PH, [(0, '#3D8FD6'), (0.45, '#9ED0F2'), (1, '#F6E2B0')])
    img = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(img, 'RGBA')
    rng = np.random.default_rng(seed)
    # brick buildings
    x = -40
    k = 0
    while x < PW + 40:
        w = rng.integers(200, 290)
        h = rng.integers(430, 640)
        base = [(150, 72, 52), (128, 60, 46), (170, 92, 64), (112, 70, 56)][k % 4]
        d.rectangle((x, GROUND - h, x + w, GROUND), fill=base + (255,))
        d.rectangle((x, GROUND - h - 18, x + w, GROUND - h), fill=tuple(int(c * 0.7) for c in base) + (255,))
        for wy in range(GROUND - h + 50, GROUND - 120, 110):
            for wx in range(x + 30, x + w - 50, 80):
                d.rectangle((wx, wy, wx + 44, wy + 66), fill=(46, 52, 66, 255))
                d.rectangle((wx, wy, wx + 44, wy + 8), fill=(210, 200, 180, 255))
        d.rectangle((x + w // 2 - 40, GROUND - 140, x + w // 2 + 40, GROUND), fill=(60, 40, 30, 255))
        x += w + 6
        k += 1
    # cobbles
    d.rectangle((0, GROUND, PW, PH), fill=(118, 116, 112, 255))
    for row, y in enumerate(range(GROUND + 10, PH, 46)):
        off = 0 if row % 2 == 0 else 40
        for xx in range(-80 + off, PW, 80):
            d.rounded_rectangle((xx + 4, y, xx + 74, y + 38), 10, fill=(100 + (xx * 7 + y) % 24, 98, 94, 255))
    d.rectangle((0, GROUND - 6, PW, GROUND + 8), fill=(70, 68, 66, 255))
    if rail:
        draw_rail(d, 0.0)
    _PL[key] = plate_img(vignette(to_arr(img), 0.35))
    return _PL[key].copy()

RAIL_Y = 760

def rail_y(x, bend):
    # sag concentrated around x = 0.62 * PW
    return RAIL_Y + bend * 190 * math.exp(-((x - PW * 0.62) / 260) ** 2)

def draw_rail(d, bend, off=(0, 0)):
    ox, oy = off
    xs = np.linspace(-20, PW + 20, 60)
    top = [(x - ox, rail_y(x, bend) - oy) for x in xs]
    bot = [(x - ox, rail_y(x, bend) + 70 - oy) for x in xs]
    d.polygon(top + bot[::-1], fill=(52, 56, 62, 255))
    d.line(top, fill=(90, 96, 104, 255), width=8)
    # lattice
    for i in range(len(xs) - 1):
        a, b = top[i], bot[i + 1]
        d.line((a, b), fill=(30, 32, 36, 255), width=5)
        d.line((bot[i], top[i + 1]), fill=(30, 32, 36, 255), width=5)
    for x in range(60, PW, 330):
        yb = rail_y(x, bend) + 70
        dx = bend * 60 * math.exp(-((x - PW * 0.62) / 260) ** 2)
        d.polygon([(x - 16 - ox, yb - oy), (x + 16 - ox, yb - oy), (x + 16 + dx - ox, GROUND - oy), (x - 16 + dx - ox, GROUND - oy)], fill=(44, 46, 52, 255))

# ====================================================================== props
def wave_poly(front, H, t, base=GROUND, x_start=-80):
    pts = []
    xs = np.linspace(x_start, front, 40)
    for x in xs:
        u = clamp01((x - x_start) / max(1, front - x_start))
        h = H * (0.42 + 0.5 * u ** 1.6) + 18 * math.sin(x / 70 + t * 5) + 10 * math.sin(x / 31 - t * 7)
        pts.append((x, base - h))
    # curling lip
    pts += [(front + 0.16 * H, base - H * 0.98), (front + 0.30 * H, base - H * 0.84), (front + 0.30 * H, base - H * 0.68),
            (front + 0.20 * H, base - H * 0.62), (front + 0.17 * H, base - H * 0.42), (front + 0.30 * H, base - H * 0.16),
            (front + 0.46 * H, base + 6)]
    return [(x_start, base + 12)] + pts + [(x_start, base + 12)]

def draw_wave(img, front, H, t, base=GROUND, drops=True, x_start=-80):
    poly = wave_poly(front, H, t, base, x_start)
    x0 = min(p[0] for p in poly) - 60; x1 = max(p[0] for p in poly) + 140
    y0 = min(p[1] for p in poly) - 140; y1 = base + 40
    ov = OV(img, x0, y0, x1, y1)
    ov.d.polygon(ov.pts(poly), fill=MOL + (255,))
    # glossy bands following the crest
    top = poly[1:41]
    for k, (dy, col, w) in enumerate(((14, MOL_HI + (230,), 16), (60, (110, 56, 20, 160), 10), (130, (90, 46, 16, 120), 8))):
        ov.d.line(ov.pts([(x, y + dy) for x, y in top]), fill=col, width=w, joint='curve')
    lip = poly[41:45]
    ov.d.line(ov.pts(lip), fill=(200, 120, 50, 220), width=12, joint='curve')
    # specular streaks
    rng = np.random.default_rng(4)
    for k in range(10):
        sx = x_start + (front - x_start) * rng.uniform(0.1, 0.95)
        sy = base - H * rng.uniform(0.15, 0.4)
        ln = rng.uniform(40, 110)
        ov.d.line(ov.pts([(sx + (t * 60) % 40, sy), (sx + ln + (t * 60) % 40, sy - 6)]), fill=(255, 220, 170, 90), width=6)
    if drops:
        for k in range(16):
            ph = (t * 1.4 + k * 0.137) % 1.0
            ang = -math.pi * (0.15 + 0.6 * ((k * 0.61) % 1))
            r0 = 30 + 260 * ph
            cx = front + 0.2 * H + r0 * math.cos(ang) * 0.9
            cy = base - H * 0.92 + r0 * math.sin(ang) + 520 * ph * ph
            rr = (22 - 12 * ph) * (0.6 + (k % 3) * 0.3)
            ov.d.ellipse(ov.box(cx - rr, cy - rr, cx + rr, cy + rr), fill=MOL + (255,))
            ov.d.ellipse(ov.box(cx - rr * 0.5, cy - rr * 0.6, cx - rr * 0.05, cy - rr * 0.15), fill=(200, 120, 60, 200))
    ov.commit()

def tank_sprite(w=620, h=700, leaks=0.0, paint=0.0, fill=None, crack=0.0):
    key = ('tank', w, h, round(leaks, 2), round(paint, 2), None if fill is None else round(fill, 3), round(crack, 2))
    if key in _SP:
        return _SP[key]
    pad = 60
    lay = Layer(w + pad * 2, h + pad * 2)
    W_, H_ = w + pad * 2, h + pad * 2
    im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # cylinder shading
    xs = np.linspace(-1, 1, w)
    shade = 0.55 + 0.45 * np.sqrt(np.clip(1 - xs ** 2, 0, 1)) - 0.15 * xs
    steel = np.array([150, 156, 160], np.float32)
    brown = np.array([96, 56, 28], np.float32)
    col = steel * (1 - paint) + brown * paint
    body = np.clip(col[None, None, :] * shade[None, :, None] * np.ones((h, 1, 1)), 0, 255).astype(np.uint8)
    bi = Image.fromarray(body, 'RGB').convert('RGBA')
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 18, fill=255)
    bi.putalpha(m)
    im.alpha_composite(bi, (pad, pad))
    # cutaway level
    if fill is not None:
        fy = pad + h - (h - 30) * fill
        d.rectangle((pad + 30, pad + 30, pad + w - 30, pad + h - 30), fill=(30, 34, 40, 255))
        d.rectangle((pad + 30, fy, pad + w - 30, pad + h - 30), fill=MOL + (255,))
        d.line((pad + 30, fy, pad + w - 30, fy), fill=MOL_HI + (255,), width=10)
    # roof
    d.pieslice((pad - 10, pad - 90, pad + w + 10, pad + 90), 180, 360, fill=tuple(int(c * 0.8) for c in col) + (255,))
    # seams + rivets
    for k in range(1, 6):
        y = pad + h * k / 6
        d.line((pad, y, pad + w, y), fill=(0, 0, 0, 70), width=5)
        for x in range(pad + 20, pad + w - 10, 36):
            d.ellipse((x - 5, y + 8, x + 5, y + 18), fill=(0, 0, 0, 60))
            d.ellipse((x - 4, y + 8, x + 1, y + 13), fill=(255, 255, 255, 60))
    # leak streaks
    if leaks > 0:
        rng = np.random.default_rng(8)
        for k in range(9):
            sx = pad + rng.uniform(0.1, 0.9) * w
            sy = pad + h * rng.uniform(0.15, 0.6)
            L = (pad + h - sy) * leaks * rng.uniform(0.6, 1.0)
            a = int(255 * (1 - paint))
            if a > 8:
                d.line((sx, sy, sx, sy + L), fill=MOL + (a,), width=12)
                d.ellipse((sx - 10, sy + L - 8, sx + 10, sy + L + 14), fill=MOL + (a,))
    if crack > 0:
        rng = np.random.default_rng(2)
        x, y = pad + w * 0.55, pad + h * 0.2
        pts = [(x, y)]
        for k in range(9):
            x += rng.uniform(-40, 40)
            y += h * 0.085 * crack
            pts.append((x, y))
        d.line(pts, fill=(20, 10, 6, 255), width=int(10 + 30 * crack), joint='curve')
    _SP[key] = im
    return im

def house_sprite(w=300, h=380, col=(176, 96, 66)):
    key = ('house', w, h, col)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (w + 20, h + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 110), (w // 2 + 10, 0), (w + 20, 110)], fill=(70, 48, 40, 255))
    d.rectangle((10, 110, w + 10, h + 110), fill=col + (255,))
    for wy in range(150, h + 20, 110):
        for wx in (40, w - 70):
            d.rectangle((wx, wy, wx + 50, wy + 70), fill=(46, 52, 66, 255))
            d.rectangle((wx, wy, wx + 50, wy + 8), fill=(220, 210, 190, 255))
    d.rectangle((w // 2 - 20, h + 30, w // 2 + 40, h + 110), fill=(60, 40, 30, 255))
    _SP[key] = im
    return im

def speedo(img, cx, cy, val, R=210):
    ov = OV(img, cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10)
    ov.d.ellipse(ov.box(cx - R, cy - R, cx + R, cy + R), fill=(40, 42, 50, 255))
    ov.d.ellipse(ov.box(cx - R * 0.9, cy - R * 0.9, cx + R * 0.9, cy + R * 0.9), fill=(245, 242, 232, 255))
    for k in range(9):
        a = math.radians(225 - k * 33.75)
        col = (210, 40, 40, 255) if k >= 6 else (40, 40, 46, 255)
        ov.d.line(ov.pts([(cx + R * 0.66 * math.cos(a), cy - R * 0.66 * math.sin(a)), (cx + R * 0.84 * math.cos(a), cy - R * 0.84 * math.sin(a))]), fill=col, width=9)
    a = math.radians(225 - val * 270)
    ov.d.line(ov.pts([(cx, cy), (cx + R * 0.74 * math.cos(a), cy - R * 0.74 * math.sin(a))]), fill=(210, 30, 30, 255), width=12)
    ov.d.ellipse(ov.box(cx - 22, cy - 22, cx + 22, cy + 22), fill=(40, 40, 46, 255))
    ov.commit()
    paste_center(img, text_img('MPH', int(R * 0.22), fill=(40, 40, 46)), cx, cy + R * 0.48)

def person_icon(h=110, col=(240, 240, 240)):
    key = ('person', h, col)
    if key in _SP:
        return _SP[key]
    w = int(h * 0.56)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((w * 0.28, 0, w * 0.72, h * 0.3), fill=col + (255,))
    d.rounded_rectangle((w * 0.08, h * 0.34, w * 0.92, h), radius=int(w * 0.3), fill=col + (255,))
    _SP[key] = im
    return im

def snow(img, t, n=60, seed=3, y1=PH):
    ov = OV(img, 0, 0, PW, y1)
    rng = np.random.default_rng(seed)
    for k in range(n):
        x0 = rng.uniform(0, PW); sp = rng.uniform(120, 260); r = rng.uniform(5, 12)
        y = (rng.uniform(0, y1) + t * sp) % y1
        x = x0 + 30 * math.sin(t * 1.5 + k)
        ov.d.ellipse(ov.box(x - r, y - r, x + r, y + r), fill=(255, 255, 255, 210))
    ov.commit()

def thermo(img, cx, cy, level, H=520):
    ov = OV(img, cx - 90, cy - H / 2 - 20, cx + 90, cy + H / 2 + 100)
    ov.d.rounded_rectangle(ov.box(cx - 40, cy - H / 2, cx + 40, cy + H / 2), 40, fill=(245, 245, 250, 255), outline=(60, 64, 72, 255), width=8)
    ov.d.ellipse(ov.box(cx - 75, cy + H / 2 - 40, cx + 75, cy + H / 2 + 90), fill=(60, 120, 220, 255), outline=(60, 64, 72, 255), width=8)
    top = cy + H / 2 - 20 - (H - 60) * level
    ov.d.rectangle(ov.box(cx - 20, top, cx + 20, cy + H / 2), fill=(60, 120, 220, 255))
    for k in range(6):
        y = cy - H / 2 + 50 + k * (H - 100) / 5
        ov.d.line(ov.pts([(cx + 40, y), (cx + 70, y)]), fill=(60, 64, 72, 255), width=6)
    ov.commit()

def brush_hand(img, hand, tip, ang_deg=0):
    # wooden mannequin hand holding a paint brush whose bristles sit at `tip`
    bx, by = tip
    ov = OV(img, bx - 60, by - 40, bx + 360, by + 260)
    ov.d.line(ov.pts([(bx + 40, by + 30), (bx + 330, by + 230)]), fill=(150, 96, 50, 255), width=26)
    ov.d.polygon(ov.pts([(bx - 10, by - 20), (bx + 50, by + 10), (bx + 30, by + 50), (bx - 40, by + 20)]), fill=(180, 180, 186, 255))
    ov.d.polygon(ov.pts([(bx - 40, by - 30), (bx - 5, by - 18), (bx - 45, by + 28), (bx - 70, by + 5)]), fill=BROWN + (255,))
    ov.commit()
    draw_hand(img, hand, (bx + 210, by + 130), 0.0)

# ====================================================================== scenes
class Hook(S):
    z0, z1 = 1.12, 1.2
    focus = (CX, 1000)
    punch = 0.08
    def make_shakes(self):
        return [(0.0, 14, 0.5), (self.we('swallowed'), 26, 0.5)]
    def events(self):
        return [(0.02, 'boom', 0.9), (self.we('MOLASSES') - 0.05, 'splat', 0.8), (self.we('swallowed'), 'thud', 0.8)]
    def plate(self):
        self.stamp = stamp_sprite('MOLASSES', 130, color=(225, 35, 35), angle=-7)
        bg = Image.new('RGBA', self.stamp.size, (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((26, 26, self.stamp.width - 26, self.stamp.height - 26), 30, fill=(255, 250, 240, 230))
        bg.alpha_composite(self.stamp)
        self.stamp = bg
        return street_plate('winter')
    def dyn(self, img, t):
        front = 640 + 210 * ease_out(t / 1.2) + 60 * t
        draw_wave(img, front, 900 + 40 * math.sin(t * 3), t)
        pop(img, C('25-FOOT WAVE', 72, bg=YEL), CX, 300, t, -1.0)
        stamp_in(img, self.stamp, CX, 560, t, self.we('MOLASSES') - 0.05)
        pop(img, C('BOSTON', 52, bg=DARK, fg=WHITE), CX + 330, 1180, t, self.we('Boston') - 0.05)

class Burst(S):
    z0, z1 = 1.0, 1.1
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('1919'), 10, 0.3), (self.we('BURST'), 30, 0.5)]
    def events(self):
        return [(0.05, 'wind', 0.5), (self.we('1919'), 'thud', 0.8), (self.we('North') - 0.05, 'pop', 0.5), (self.we('BURST') - 0.03, 'crack', 1.0), (self.we('BURST') + 0.08, 'boom', 0.8)]
    def plate(self):
        self.stamp = stamp_sprite('JAN 1919', 140, color=(200, 40, 40), angle=-7)
        return street_plate('winter', rail=False, seed=5)
    def dyn(self, img, t):
        snow(img, t, 40, 1, GROUND)
        tB = self.we('BURST') - 0.05
        cr = 0.0 if t < tB else ease_out((t - tB) / 0.25)
        tk = tank_sprite(620, 700, leaks=0.3, crack=cr)
        cy = 1300 - 760 / 2 - 30
        ground_shadow(img, CX, GROUND, 700, 0.5)
        paste_center(img, tk, CX + (8 * math.sin(t * 60) if t > tB else 0), cy)
        if t > tB:
            q = t - tB
            # jets of molasses spraying out of the split
            ov = OV(img, 0, 300, PW, GROUND + 30)
            for k in range(7):
                ang = math.radians(-160 + k * 23)
                L = 200 + 650 * ease_out(q / 0.6)
                x0, y0 = CX + 30, cy - 120 + k * 50
                pts = [(x0 + L * u * math.cos(ang) * 0.9, y0 + L * u * math.sin(ang) * 0.4 + 400 * (u * q) ** 2) for u in np.linspace(0, 1, 10)]
                for j, (x, y) in enumerate(pts):
                    r = 44 - 3 * j + 6 * math.sin(t * 20 + j + k)
                    ov.d.ellipse(ov.box(x - r, y - r * 0.8, x + r, y + r * 0.8), fill=MOL + (255,))
                    ov.d.ellipse(ov.box(x - r * 0.5, y - r * 0.6, x, y - r * 0.2), fill=MOL_HI + (200,))
            ov.commit()
            draw_wave(img, CX - 300 + 500 * ease_out(q / 0.8), 220 + 260 * ease_out(q / 0.8), t, drops=False, x_start=CX - 420)
        stamp_in(img, self.stamp, CX, 300, t, self.we('1919'))
        pop(img, C("BOSTON'S NORTH END", 50, dot=GOLD), CX, 520, t, self.we('North') - 0.05, out_t=tB)
        pop(img, C('BURST!', 70, bg=RED, fg=WHITE), CX, 520, t, tB)

class Gallons(S):
    z0, z1 = 1.02, 1.12
    focus = (CX, 960)
    def events(self):
        return [(0.05, 'bloop', 0.6), (self.we('2.3') - 0.05, 'riser', 0.6), (self.we('MILLION'), 'bigpop', 0.8), (self.we('sticky'), 'splat', 0.6)]
    def plate(self):
        return plate_img(dark_room('#3A3230', '#120E0C', spot=(CX, 900, 1100)))
    def dyn(self, img, t):
        t2 = self.we('2.3') - 0.05
        f = 0.15 + 0.8 * ease_out(clamp01((t - 0.0) / max(0.3, self.we('MILLION') + 0.3)))
        tk = tank_sprite(640, 760, fill=round(f * 40) / 40)
        paste_center(img, tk, CX, 900)
        # counter
        u = ease_out(clamp01((t - t2) / max(0.2, self.we('gallons') - t2)))
        n = int(2300000 * u / 1000) * 1000 if u < 1 else 2300000
        if t > t2:
            paste_center(img, text_img(f'{n:,}', 120, fill=YEL, stroke=10, shadow_px=6), CX, 300)
        pop(img, C('GALLONS OF MOLASSES', 52, bg=WHITE), CX, 470, t, self.we('gallons') - 0.05)
        pop(img, C('THICK + STICKY', 50, bg=(150, 78, 26), fg=WHITE), CX, 1220, t, self.we('thick') - 0.05)
        # slow drip
        dy = (t * 220) % 260
        ov = OV(img, CX - 40, 1270, CX + 40, 1290 + 300)
        ov.d.ellipse(ov.box(CX - 18, 1280 + dy, CX + 18, 1320 + dy), fill=MOL + (255,))
        ov.commit()

class Speed(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('HOUR'), 16, 0.4)]
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('raced'), 'wind', 0.7), (self.we('35') - 0.05, 'riser', 0.6), (self.we('miles'), 'thud', 0.7)]
    def plate(self):
        return street_plate('winter', rail=True, seed=1)
    def dyn(self, img, t):
        front = 60 + 1000 * (t / self.dur)
        ov = OV(img, 0, 400, PW, GROUND)
        for k in range(8):
            y = 520 + k * 90
            x = (front - 200 - (t * 1600 + k * 260) % 700)
            ov.d.line(ov.pts([(x - 380, y), (x, y)]), fill=(255, 255, 255, 120), width=8)
        ov.commit()
        draw_wave(img, front, 640, t)
        t35 = self.we('35') - 0.05
        v = 0.1 + 0.55 * ease_out(clamp01((t - t35) / 0.5)) + 0.02 * math.sin(t * 30) * (t > t35)
        speedo(img, PW - 300, 560, v, 190)
        if t > t35:
            pop(img, C('~35 MPH', 70, bg=YEL), 380, 420, t, t35)
        pop(img, C('FASTER THAN YOU CAN RUN', 44, bg=DARK, fg=WHITE), CX, 1200, t, self.we('miles') - 0.05)

class Wreck(S):
    z0, z1 = 1.02, 1.12
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('knocked'), 22, 0.45), (self.we('ELEVATED'), 22, 0.45)]
    def events(self):
        return [(self.we('knocked'), 'boom', 0.8), (self.we('foundations') - 0.05, 'thud', 0.6), (self.we('bent') - 0.03, 'crack', 0.9), (self.we('ELEVATED') - 0.05, 'pop', 0.5)]
    def plate(self):
        self.house = house_sprite(300, 400)
        return street_plate('winter', rail=False, seed=9)
    def dyn(self, img, t):
        tk = self.we('knocked') - 0.05
        tb = self.we('bent') - 0.05
        bend = ease_out(clamp01((t - tb) / 0.4))
        ov = OV(img, 0, RAIL_Y - 40, PW, GROUND + 4)
        draw_rail(ov.d, bend, (0, RAIL_Y - 40))
        ov.commit()
        q = clamp01((t - tk) / 0.7)
        hx = 820 + 160 * ease_out(q)
        ang = -14 * ease_out(q)
        rs = self.house.rotate(ang, resample=Image.BICUBIC, expand=True)
        paste_center(img, rs, hx, GROUND - 250 + 30 * ease_out(q))
        front = 250 + 500 * ease_out(clamp01(t / max(0.3, tk + 0.4)))
        draw_wave(img, front, 520, t)
        pop(img, C('OFF THEIR FOUNDATIONS', 48, bg=WHITE), CX, 300, t, self.we('foundations') - 0.1, out_t=tb - 0.1)
        pop(img, C('ELEVATED RAILWAY BENT', 48, bg=RED, fg=WHITE), CX, 300, t, tb)

class Twist(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    punch = 0.18
    def make_shakes(self):
        return [(self.we('twist'), 14, 0.35)]
    def events(self):
        return [(self.we('twist') - 0.05, 'scratch', 0.8), (self.we('LEAKED') - 0.05, 'bloop', 0.7), (self.we('painted') - 0.05, 'swipe', 0.7), (self.we('BROWN'), 'thud', 0.8)]
    def plate(self):
        self.hand = get_hand(460, -math.pi / 1.6)
        self.stamp = stamp_sprite('PAINTED BROWN', 110, color=(225, 35, 35), angle=-8)
        return plate_img(dark_room('#3C4450', '#10141A', spot=(CX, 900, 1100)))
    def dyn(self, img, t):
        tl = self.we('LEAKED') - 0.05
        tp = self.we('painted') - 0.05
        leaks = 0.2 + 0.8 * ease_out(clamp01((t - tl) / 0.6))
        paint = ease_in_out(clamp01((t - tp) / 0.9))
        tk = tank_sprite(560, 680, leaks=round(leaks, 1), paint=round(paint * 20) / 20)
        paste_center(img, tk, CX, 880)
        if t > tp - 0.2:
            yb = 560 + 600 * ((t - tp) * 1.6 % 1.0)
            brush_hand(img, self.hand, (CX + 120 - 200 * math.sin(t * 6), yb))
        pop(img, C('THE TWIST?', 66, bg=YEL), CX, 300, t, 0.0, out_t=tl - 0.05)
        pop(img, C('IT LEAKED FROM THE START', 46, bg=WHITE), CX, 300, t, tl, out_t=self.we('BROWN') - 0.1)
        stamp_in(img, self.stamp, CX, 320, t, self.we('BROWN') - 0.05)
        pop(img, C('TO HIDE THE LEAKS', 48, bg=DARK, fg=WHITE), CX, 1220, t, self.we('hide') - 0.05)

class Cold(S):
    z0, z1 = 1.02, 1.12
    focus = (CX, 1000)
    def events(self):
        return [(0.05, 'wind', 0.7), (self.we('cold') - 0.05, 'tick', 0.6), (self.we('thickened') - 0.05, 'splat', 0.7), (self.we('GLUE') - 0.05, 'squeak', 0.7)]
    def plate(self):
        self.hand = get_hand(560, -math.pi / 2)
        img = street_plate('winter', rail=False, seed=12)
        d = ImageDraw.Draw(img, 'RGBA')
        d.rectangle((0, 980, PW, PH), fill=MOL + (255,))
        for y in range(1000, PH, 70):
            d.line((0, y, PW, y + 12), fill=(110, 56, 20, 90), width=6)
        return img
    def dyn(self, img, t):
        snow(img, t, 50, 7, 980)
        th = self.we('thickened') - 0.05
        lvl = 0.75 - 0.6 * ease_out(clamp01(t / max(0.4, th + 0.3)))
        thermo(img, 260, 560, lvl, 420)
        # wooden mannequin arm pulled out of the goo, strands stretching
        tg = self.we('trapping') - 0.05
        lift = 60 * ease_out(clamp01((t - tg) / 0.6)) * (1 + 0.15 * math.sin(t * 7))
        tip = (CX + 100, 900 - lift)
        ov = OV(img, CX - 200, 700 - lift, CX + 420, 1100)
        for k in range(5):
            x = CX + 80 + k * 40
            ov.d.line(ov.pts([(x, 1000), (x + 10 * math.sin(t * 3 + k), 900 - lift * 0.8), (x + 20, 840 - lift)]), fill=MOL + (230,), width=18 - 2 * k, joint='curve')
        ov.commit()
        bx, by = tip
        ov = OV(img, bx - 220, by - 260, bx + 260, by + 120)
        boot = [(bx - 60, by - 240), (bx + 60, by - 240), (bx + 60, by - 40), (bx + 200, by - 10), (bx + 210, by + 60), (bx - 70, by + 60)]
        ov.d.polygon(ov.pts(boot), fill=(70, 46, 30, 255))
        ov.d.rectangle(ov.box(bx - 70, by + 40, bx + 210, by + 70), fill=(36, 24, 16, 255))
        ov.d.line(ov.pts([(bx - 40, by - 220), (bx - 40, by - 60)]), fill=(120, 84, 56, 255), width=10)
        for k in range(4):
            yy = by + 60 - k * 40
            ov.d.line(ov.pts([(bx - 70, yy), (bx + 200 - k * 40, yy + 8)]), fill=MOL + (230,), width=14)
        ov.commit()
        ov = OV(img, CX - 100, 950, CX + 450, 1060)
        ov.d.ellipse(ov.box(CX - 10, 965, CX + 360, 1040), fill=MOL + (255,))
        ov.d.arc(ov.box(CX - 10, 965, CX + 360, 1040), 200, 330, fill=MOL_HI + (255,), width=8)
        ov.commit()
        pop(img, C('WINTER COLD', 54, bg=WHITE, dot=(60, 120, 220)), CX + 150, 300, t, 0.05)
        pop(img, C('THICK AS GLUE', 60, bg=YEL), CX, 1220, t, self.we('GLUE') - 0.1)
        pop(img, C('IT THICKENED', 50, bg=(150, 78, 26), fg=WHITE), CX + 150, 460, t, th)

class Toll(S):
    z0, z1 = 1.02, 1.08
    focus = (CX, 960)
    punch = 0.06
    def events(self):
        return [(self.we('21') - 0.02, 'thud', 0.7), (self.we('150') - 0.05, 'tick', 0.5)]
    def plate(self):
        img = plate_img(dark_room('#2E3038', '#0C0D10', spot=(CX, 900, 1100), strength=1.0))
        return img
    def dyn(self, img, t):
        t21 = self.we('21') - 0.05
        n = int(clamp01((t - t21) / 0.9) * 21)
        ic = person_icon(96, (235, 235, 240))
        for k in range(n):
            paste_center(img, ic, 210 + (k % 7) * 146, 520 + (k // 7) * 130)
        pop(img, C('21 LIVES LOST', 64, bg=WHITE), CX, 300, t, t21)
        t150 = self.we('150') - 0.05
        if t > t150:
            m = int(clamp01((t - t150) / 0.8) * 150)
            sm = person_icon(40, (150, 156, 170))
            for k in range(m):
                paste_center(img, sm, 130 + (k % 25) * 43, 960 + (k // 25) * 52)
            pop(img, C('ABOUT 150 INJURED', 52, bg=DARK, fg=WHITE), CX, 1340 - 60, t, t150)

class Outro(S):
    z0, z1 = 1.02, 1.08
    focus = (CX, 1000)
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('locals') - 0.05, 'pop', 0.5), (self.we('hot') - 0.05, 'sizzle', 0.6), (self.we('smell') - 0.05, 'riser', 0.6)]
    def plate(self):
        img = street_plate('summer', rail=True, seed=1)
        d = ImageDraw.Draw(img, 'RGBA')
        for k in range(7):
            x = 120 + k * 170
            d.ellipse((x - 90, GROUND + 60 + (k % 3) * 70, x + 120, GROUND + 120 + (k % 3) * 70), fill=MOL + (40,))
        self.wave_plate = street_plate('winter')
        return img
    def dyn(self, img, t):
        glow(img, PW - 220, 220, 260, (255, 210, 90), 0.9)
        ov = OV(img, PW - 330, 110, PW - 110, 330)
        ov.d.ellipse(ov.box(PW - 300, 140, PW - 140, 300), fill=(255, 226, 120, 255))
        ov.commit()
        # wavy smell lines rising from the street
        ov = OV(img, 0, 700, PW, GROUND + 260)
        for k in range(7):
            x0 = 160 + k * 165
            ph = (t * 0.9 + k * 0.3) % 1
            pts = [(x0 + 26 * math.sin(yy / 40 + t * 5 + k), yy) for yy in np.linspace(GROUND + 180 - ph * 120, 760 + 300 * (1 - ph), 16)]
            ov.d.line(ov.pts(pts), fill=(150, 90, 40, int(200 * (1 - ph * 0.6))), width=12, joint='curve')
        ov.commit()
        pop(img, C('FOR DECADES...', 56, bg=DARK, fg=WHITE), CX, 300, t, 0.0, out_t=self.we('hot') - 0.1)
        pop(img, C('HOT DAYS = MOLASSES SMELL', 46, bg=YEL), CX, 300, t, self.we('hot') - 0.05, out_t=self.dur - 0.75)
        pop(img, C('LOCALS SAID', 46, bg=WHITE), CX, 470, t, self.we('locals') - 0.05, out_t=self.dur - 0.75)
        # final beat: the wave crashes back in (loops into the hook)
        td = self.we('the', 't0') if False else self.dur - 0.75
        if t > td:
            m = ease_in_out(clamp01((t - td) / 0.45))
            fr = self.wave_plate.copy()
            draw_wave(fr, 640, 900, t)
            paste_center(fr, C('25-FOOT WAVE', 72, bg=YEL), CX, 300)
            img.alpha_composite(Image.blend(img, fr, m))

SCENES = [Hook, Burst, Gallons, Speed, Wreck, Twist, Cold, Toll, Outro]
