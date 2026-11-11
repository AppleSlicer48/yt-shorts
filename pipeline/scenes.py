import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import CX, CY, plate_img, dark_room
from mw_scenes import glow, stamp_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand

# NASA's Mars Climate Orbiter (launched Dec 11 1998, lost Sept 23 1999): pound-force-seconds vs newton-seconds
GOLD = (236, 176, 52)
RED = (214, 52, 40)
YEL = (255, 210, 60)
DARK = (28, 32, 46)
WHITE = (255, 255, 255)
GREEN = (70, 210, 120)
BLUE = (70, 150, 255)
MARS = np.array([0.78, 0.32, 0.14], np.float32)

_SP = {}
_PL = {}

# ====================================================================== backdrops
def space_plate(seed=1, c0='#03040B', c1='#141B36'):
    key = ('space', seed, c0, c1)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, c0), (0.6, c1), (1, c0)])
    rng = np.random.default_rng(seed)
    neb = smooth_noise(PH, PW, 260, seed, 3)
    arr = arr + (neb[..., None] - 0.5) * np.array([0.10, 0.04, 0.16], np.float32)
    img = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(img, 'RGBA')
    for k in range(420):
        x, y = rng.uniform(0, PW), rng.uniform(0, PH)
        r = rng.choice([1.2, 1.8, 2.6, 3.6], p=[0.5, 0.3, 0.15, 0.05])
        a = int(rng.uniform(120, 255))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    _PL[key] = img
    return img.copy()

def planet_sprite(R, kind='mars', light=(-0.55, -0.45)):
    key = ('planet', R, kind, light)
    if key in _SP:
        return _SP[key]
    pad = int(R * 0.18)
    n = 2 * (R + pad)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = (xx - n / 2) / R, (yy - n / 2) / R
    d = np.sqrt(dx * dx + dy * dy)
    inside = np.clip((1 - d) * R + 0.5, 0, 1)
    nz = np.sqrt(np.clip(1 - d * d, 0, 1))
    lx, ly = light
    lz = math.sqrt(max(0.05, 1 - lx * lx - ly * ly))
    ndl = np.clip(dx * lx + dy * ly + nz * lz, 0, 1)
    nse = smooth_noise(n, n, max(8, R // 5), 7 if kind == 'mars' else 3, 4)
    if kind == 'mars':
        base = MARS[None, None, :] * (0.75 + 0.5 * nse[..., None])
        dark = nse < 0.42
        base = np.where(dark[..., None], base * 0.62, base)
        cap = np.zeros_like(d, bool)
        base = np.where(cap[..., None], np.array([0.95, 0.9, 0.88], np.float32), base)
        atm = (1.0, 0.55, 0.35)
    else:
        ocean = np.array([0.12, 0.35, 0.78], np.float32)
        land = np.array([0.25, 0.6, 0.28], np.float32)
        base = np.where((nse > 0.55)[..., None], land, ocean)[..., :] * np.ones((n, n, 1), np.float32)
        cl = smooth_noise(n, n, max(6, R // 7), 11, 3) > 0.62
        base = np.where(cl[..., None], np.array([0.95, 0.96, 1.0], np.float32), base)
        atm = (0.5, 0.75, 1.0)
    col = base * (0.08 + 1.05 * ndl[..., None]) + 0.25 * np.array(atm, np.float32) * ((1 - nz) ** 3)[..., None] * (ndl[..., None] > 0.05)
    halo = np.exp(-((d - 1.0) / 0.06) ** 2) * (d >= 0.98) * np.clip(ndl * 0 + (dx * lx + dy * ly) * 1.2 + 0.4, 0, 1) * 0.8
    A = np.clip(inside + halo, 0, 1)
    rgb = np.where(inside[..., None] > 0, col, np.array(atm, np.float32))
    arr = np.concatenate([np.clip(rgb, 0, 1), A[..., None]], -1)
    im = Image.fromarray((arr * 255 + 0.5).astype(np.uint8), 'RGBA')
    _SP[key] = im
    return im

def orbiter_sprite(s=1.0, panel=True):
    """Gold-foil box bus, white dish, ONE big solar panel on one side (lopsided)."""
    key = ('orb', round(s, 3), panel)
    if key in _SP:
        return _SP[key]
    W_, H_ = int(900 * s), int(520 * s)
    im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bx0, by0, bx1, by1 = 120 * s, 170 * s, 330 * s, 400 * s
    # strut + panel to the right
    if panel:
        d.rectangle((bx1, 270 * s, 430 * s, 292 * s), fill=(170, 170, 178, 255))
        px0, py0, px1, py1 = 420 * s, 150 * s, 880 * s, 410 * s
        d.rectangle((px0, py0, px1, py1), fill=(22, 40, 92, 255), outline=(190, 196, 210, 255), width=max(2, int(8 * s)))
        nx, ny = 8, 5
        for i in range(nx):
            for j in range(ny):
                x0 = px0 + 8 * s + i * (px1 - px0 - 16 * s) / nx
                y0 = py0 + 8 * s + j * (py1 - py0 - 16 * s) / ny
                x1 = x0 + (px1 - px0 - 16 * s) / nx - 4 * s
                y1 = y0 + (py1 - py0 - 16 * s) / ny - 4 * s
                c = 60 + int(40 * ((i + j) % 2))
                d.rectangle((x0, y0, x1, y1), fill=(30, c, 170, 255))
                d.line((x0, y0, x1, y0), fill=(150, 190, 255, 160), width=max(1, int(2 * s)))
    # bus with foil shading
    for k in range(int(by1 - by0)):
        u = k / (by1 - by0)
        sh = 0.75 + 0.35 * math.sin(u * 9.0) * 0.3 + 0.25 * (1 - u)
        c = tuple(int(min(255, ch * sh)) for ch in GOLD)
        d.line((bx0, by0 + k, bx1, by0 + k), fill=c + (255,))
    rng = np.random.default_rng(5)
    for k in range(14):
        x = rng.uniform(bx0 + 10 * s, bx1 - 10 * s)
        y = rng.uniform(by0 + 10 * s, by1 - 10 * s)
        d.line((x, y, x + rng.uniform(-40, 40) * s, y + rng.uniform(10, 40) * s), fill=(255, 236, 170, 150), width=max(1, int(3 * s)))
    d.rectangle((bx0, by0, bx1, by1), outline=(150, 100, 20, 255), width=max(2, int(5 * s)))
    # dish antenna on top
    d.line((225 * s, by0, 225 * s, 120 * s), fill=(200, 200, 205, 255), width=max(2, int(10 * s)))
    d.ellipse((120 * s, 40 * s, 330 * s, 130 * s), fill=(236, 238, 242, 255), outline=(150, 150, 160, 255), width=max(2, int(5 * s)))
    d.ellipse((205 * s, 70 * s, 245 * s, 100 * s), fill=(170, 170, 180, 255))
    # thruster nozzles
    for (x, y) in ((bx0, by1 - 30 * s), (bx0, by0 + 30 * s)):
        d.polygon([(x, y - 14 * s), (x - 34 * s, y - 24 * s), (x - 34 * s, y + 24 * s), (x, y + 14 * s)], fill=(90, 92, 100, 255))
    _SP[key] = im
    return im

def orb_center_offset(s):
    # bus centre relative to sprite centre (for placing puffs / fire)
    return (225 * s - 450 * s, 285 * s - 260 * s)

def draw_orbiter(img, cx, cy, s=1.0, ang=0.0, panel=True):
    sp = orbiter_sprite(s, panel)
    if abs(ang) > 0.05:
        sp = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
    paste_center(img, sp, cx, cy)

def fire_trail(img, x, y, dirx, diry, L, t, width=90, a=1.0):
    """Flaming plasma trail streaming back from (x, y) along -dir."""
    n = math.hypot(dirx, diry)
    ux, uy = dirx / n, diry / n
    glow(img, x, y, width * 2.2, (255, 140, 40), 0.9 * a)
    ov = OV(img, min(x, x - ux * L) - width * 2, min(y, y - uy * L) - width * 2, max(x, x - ux * L) + width * 2, max(y, y - uy * L) + width * 2)
    for k in range(26):
        u = k / 25
        fl = 1 + 0.18 * math.sin(t * 40 + k * 1.7)
        r = width * (1.0 - 0.75 * u) * fl
        px = x - ux * L * u + 10 * math.sin(t * 30 + k)
        py = y - uy * L * u + 10 * math.cos(t * 27 + k)
        col = (255, int(240 - 170 * u), int(120 - 110 * u), int(230 * (1 - u) * a))
        ov.d.ellipse(ov.box(px - r, py - r, px + r, py + r), fill=col)
    ov.d.ellipse(ov.box(x - width * 0.5, y - width * 0.5, x + width * 0.5, y + width * 0.5), fill=(255, 255, 230, int(255 * a)))
    ov.im = ov.im.filter(ImageFilter.GaussianBlur(3))
    ov.commit()

def puff(img, x, y, k, dirx=-1, diry=0, size=70):
    """Thruster puff, k in [0,1] life."""
    if k <= 0 or k >= 1:
        return
    r = size * (0.4 + 1.2 * k)
    px, py = x + dirx * 180 * k, y + diry * 180 * k
    ov = OV(img, px - r - 4, py - r - 4, px + r + 4, py + r + 4)
    ov.d.ellipse(ov.box(px - r, py - r, px + r, py + r), fill=(235, 240, 255, int(220 * (1 - k))))
    ov.d.ellipse(ov.box(px - r * 0.5, py - r * 0.5, px + r * 0.3, py + r * 0.3), fill=(255, 255, 255, int(200 * (1 - k))))
    ov.commit()

def monitor_sprite(w, h, lines, accent=(80, 255, 150), title=None):
    key = ('mon', w, h, tuple(lines), accent, title)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (w + 40, h + 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w + 40, h + 40), 30, fill=(46, 50, 60, 255), outline=(20, 22, 28, 255), width=6)
    d.rectangle((20, 20, w + 20, h + 20), fill=(8, 16, 14, 255))
    for yy in range(24, h + 20, 8):
        d.line((20, yy, w + 20, yy), fill=(255, 255, 255, 10))
    d.rectangle((w / 2 - 20, h + 40, w / 2 + 60, h + 100), fill=(60, 64, 74, 255))
    d.rounded_rectangle((w / 2 - 110, h + 96, w / 2 + 150, h + 130), 12, fill=(60, 64, 74, 255))
    y = 50
    if title:
        f = font(40, FONT_BOLD)
        d.text((50, y), title, font=f, fill=accent + (180,))
        y += 70
    for ln in lines:
        f = font(64, FONT_BLACK)
        d.text((50, y), ln, font=f, fill=accent + (255,))
        y += 92
    _SP[key] = im
    return im

def weight_sprite(label, w=150, h=120, col=(120, 126, 140)):
    key = ('wt', label, w, h, col)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (w + 10, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.arc((w / 2 - 28, 0, w / 2 + 38, 60), 180, 360, fill=(70, 74, 84, 255), width=12)
    d.polygon([(18, 30), (w - 8, 30), (w + 6, h + 34), (4, h + 34)], fill=col + (255,))
    d.line((24, 36, w - 14, 36), fill=(255, 255, 255, 110), width=6)
    f = font(int(h * 0.42))
    bb = f.getbbox(label)
    d.text(((w + 10 - (bb[2] - bb[0])) / 2 - bb[0], 30 + (h + 4 - (bb[3] - bb[1])) / 2 - bb[1]), label, font=f, fill=(255, 255, 255, 255))
    _SP[key] = im
    return im

def dashed_path(ov, pts, color, width=8, dash=28, gap=18):
    acc = 0.0
    on = True
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while pos < L:
            step = min((dash if on else gap) - acc, L - pos)
            if on:
                a = pos / L; b = (pos + step) / L
                ov.d.line(ov.pts([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)]), fill=color, width=width)
            pos += step
            acc += step
            if acc >= (dash if on else gap) - 1e-6:
                acc = 0.0
                on = not on

# ====================================================================== scenes
class Hook(S):
    """Frame 0: the orbiter, wrapped in fire, plunging into a huge Mars."""
    z0, z1 = 1.1, 1.2
    focus = (CX, 1000)
    punch = 0.06
    def make_shakes(self):
        return [(0.0, 16, 0.6), (self.we('math'), 22, 0.45)]
    def events(self):
        return [(0.02, 'boom', 0.9), (0.1, 'wind', 0.6), (self.we('$125') - 0.05, 'cash', 0.8), (self.we('math') - 0.05, 'buzzer', 0.7)]
    def plate(self):
        img = space_plate(1)
        paste_center(img, planet_sprite(900), CX + 260, 2050)
        self.stamp = stamp_sprite('MATH MISTAKE', 120, color=(230, 40, 40), angle=-7)
        bg = Image.new('RGBA', self.stamp.size, (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((26, 26, self.stamp.width - 26, self.stamp.height - 26), 30, fill=(255, 250, 240, 235))
        bg.alpha_composite(self.stamp)
        self.stamp = bg
        return img
    def dyn(self, img, t):
        # streaks of the dive (motion from frame 0)
        x = 560 + 50 * t
        y = 820 + 55 * t
        fire_trail(img, x + 150, y + 190, 1.0, 1.1, 720 + 40 * math.sin(t * 9), t, 130)
        draw_orbiter(img, x, y, 0.78, ang=-38 + 4 * math.sin(t * 7))
        ov = OV(img, 0, 0, PW, PH)
        for k in range(9):
            ph = (t * 2.2 + k * 0.17) % 1
            sx = (k * 157) % PW
            sy = -200 + ph * 2600
            ov.d.line(ov.pts([(sx, sy), (sx + 90, sy + 100)]), fill=(255, 255, 255, 90), width=5)
        ov.commit()
        pop(img, C('$125 MILLION', 92, bg=YEL), CX, 300, t, -1.0)
        pop(img, C('NASA', 56, bg=DARK, fg=WHITE), CX, 470, t, -1.0)
        stamp_in(img, self.stamp, CX, 1720, t, self.we('math') - 0.05)

class Journey(S):
    z0, z1 = 1.02, 1.1
    focus = (CX, 1000)
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('Orbiter') - 0.05, 'pop', 0.5), (self.we('NINE') - 0.05, 'riser', 0.6), (self.we('months'), 'tick', 0.5)]
    def plate(self):
        img = space_plate(2)
        paste_center(img, planet_sprite(150, 'earth', (-0.3, -0.6)), 230, 1120)
        paste_center(img, planet_sprite(190), PW - 250, 640)
        return img
    def path(self, u):
        x0, y0 = 300, 1020
        x1, y1 = PW - 330, 720
        cx_, cy_ = CX, 1250
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx_ + u * u * x1
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy_ + u * u * y1
        return x, y
    def dyn(self, img, t):
        u = clamp01(0.05 + 0.95 * t / self.dur)
        ov = OV(img, 0, 500, PW, 1350)
        dashed_path(ov, [self.path(v) for v in np.linspace(0, 1, 50)], (255, 255, 255, 120), 7)
        ov.d.line(ov.pts([self.path(v) for v in np.linspace(0, u, 40)]), fill=YEL + (255,), width=9, joint='curve')
        ov.commit()
        x, y = self.path(u)
        x2, y2 = self.path(min(1, u + 0.02))
        ang = -math.degrees(math.atan2(y2 - y, x2 - x))
        draw_orbiter(img, x, y, 0.32, ang=ang * 0.4)
        pop(img, C('MARS CLIMATE ORBITER', 56, bg=WHITE, dot=RED), CX, 300, t, self.we('Mars') - 0.1)
        tn = self.we('NINE') - 0.05
        if t > tn:
            m = min(9, 1 + int((t - tn) / 0.08))
            pop(img, C(f'{m} MONTHS', 80, bg=YEL), CX, 1700, t, tn)
        pop(img, C('EARTH', 40, bg=DARK, fg=WHITE), 230, 1320, t, 0.1)
        pop(img, C('MARS', 40, bg=DARK, fg=WHITE), PW - 250, 880, t, 0.2)

class Lockheed(S):
    z0, z1 = 1.04, 1.12
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('POUND-SECONDS'), 12, 0.3)]
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('software') - 0.05, 'tick', 0.5), (self.we('thruster') - 0.05, 'wind', 0.5), (self.we('pushes') - 0.05, 'pop', 0.6), (self.we('in'), 'thud', 0.7)]
    def plate(self):
        self.hand = get_hand(520, -math.pi / 6)
        return plate_img(dark_room('#3B3F4C', '#0E1016', spot=(CX, 900, 1100)))
    def dyn(self, img, t):
        tp = self.we('POUND-SECONDS') - 0.1
        lines = ['IMPULSE:', '1.00']
        if t > tp:
            lines = ['IMPULSE:', '1.00 lbf·s']
        mon = monitor_sprite(860, 420, lines, accent=(255, 190, 70), title='GROUND SOFTWARE')
        paste_center(img, mon, CX, 920)
        # blinking cursor
        if int(t * 3) % 2 == 0:
            ov = OV(img, 0, 0, PW, PH)
            ov.d.rectangle(ov.box(CX + 260, 990, CX + 290, 1050), fill=(255, 190, 70, 255))
            ov.commit()
        # wooden hand pressing a key
        tap = 0.5 + 0.5 * math.sin(t * 9)
        draw_hand(img, self.hand, (CX + 330, 1090 + 18 * tap), tap * 0.2)
        pop(img, C('LOCKHEED MARTIN', 62, bg=WHITE, dot=GOLD), CX, 300, t, 0.0)
        tt = self.we('thruster') - 0.05
        pop(img, C('THRUSTER PUSHES', 50, bg=DARK, fg=WHITE), CX, 470, t, tt)
        pop(img, C('POUND-SECONDS', 78, bg=YEL), CX, 1700, t, tp)

class Navigators(S):
    z0, z1 = 1.04, 1.12
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('METRIC'), 18, 0.4)]
    def events(self):
        return [(0.05, 'scratch', 0.7), (self.we('navigators') - 0.05, 'pop', 0.5), (self.we('read') - 0.05, 'tick', 0.5), (self.we('METRIC') - 0.05, 'thud', 0.9)]
    def plate(self):
        self.stamp = stamp_sprite('METRIC', 140, color=(230, 40, 40), angle=-8)
        return plate_img(dark_room('#2F3A4C', '#0B0F18', spot=(CX, 900, 1100)))
    def dyn(self, img, t):
        tm = self.we('METRIC') - 0.05
        m1 = monitor_sprite(500, 300, ['1.00', 'lbf·s'], accent=(255, 190, 70), title='SENT')
        m2 = monitor_sprite(500, 300, ['1.00', 'N·s' if t > tm else '????'], accent=(90, 220, 255), title='READ AS')
        slide = ease_out(clamp01(t / 0.4))
        paste_center(img, m1, 340 - 200 * (1 - slide), 880, scale=1.0)
        paste_center(img, m2, PW - 340 + 200 * (1 - slide), 880, scale=1.0)
        # arrow between
        ov = OV(img, CX - 120, 760, CX + 120, 960)
        k = (t * 2) % 1
        ov.d.polygon(ov.pts([(CX - 70 + 40 * k, 830), (CX + 20 + 40 * k, 830), (CX + 20 + 40 * k, 800), (CX + 90 + 40 * k, 860), (CX + 20 + 40 * k, 920), (CX + 20 + 40 * k, 890), (CX - 70 + 40 * k, 890)]), fill=WHITE + (230,))
        ov.commit()
        pop(img, C("NASA'S NAVIGATORS", 60, bg=WHITE, dot=BLUE), CX, 300, t, self.we('navigators') - 0.1)
        stamp_in(img, self.stamp, CX, 1170, t, tm)
        pop(img, C('NEWTON-SECONDS', 70, bg=(90, 200, 255)), CX, 1700, t, self.we('newton-seconds') - 0.05)

class Factor(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('4.45'), 14, 0.35), (self.we('UNDERESTIMATED'), 20, 0.45)]
    def events(self):
        return [(0.05, 'thud', 0.7), (self.we('4.45') - 0.05, 'riser', 0.6), (self.we('newtons'), 'ding', 0.6), (self.we('every') - 0.05, 'rattle', 0.5), (self.we('was'), 'buzzer', 0.7)]
    def plate(self):
        self.stamp = stamp_sprite('UNDERESTIMATED', 96, color=(230, 40, 40), angle=-7)
        return plate_img(dark_room('#40382F', '#110E0B', spot=(CX, 950, 1100)))
    def dyn(self, img, t):
        t4 = self.we('4.45') - 0.05
        n_right = clamp01((t - t4) / 0.7) * 4.45
        # balance: left heavier until right is filled
        tilt = 0.22 * (1 - clamp01(n_right / 4.45)) + 0.02 * math.sin(t * 5)
        px, py = CX, 760
        L = 420
        lx, ly = px - L * math.cos(tilt), py + L * math.sin(tilt)
        rx, ry = px + L * math.cos(tilt), py - L * math.sin(tilt)
        ov = OV(img, 0, 500, PW, 1350)
        ov.d.polygon(ov.pts([(px - 30, py), (px + 30, py), (px + 90, 1300), (px - 90, 1300)]), fill=(120, 90, 50, 255))
        ov.d.rectangle(ov.box(px - 200, 1280, px + 200, 1320), fill=(90, 66, 36, 255))
        ov.d.line(ov.pts([(lx, ly), (rx, ry)]), fill=(200, 160, 80, 255), width=22)
        ov.d.ellipse(ov.box(px - 28, py - 28, px + 28, py + 28), fill=(230, 190, 100, 255))
        for (x, y) in ((lx, ly), (rx, ry)):
            ov.d.line(ov.pts([(x, y), (x - 110, y + 200)]), fill=(180, 180, 186, 255), width=5)
            ov.d.line(ov.pts([(x, y), (x + 110, y + 200)]), fill=(180, 180, 186, 255), width=5)
            ov.d.chord(ov.box(x - 150, y + 150, x + 150, y + 260), 0, 180, fill=(200, 164, 90, 255))
        ov.commit()
        paste_center(img, weight_sprite('1 lbf', 190, 150, (196, 120, 40)), lx, ly + 105)
        whole = int(n_right)
        for k in range(whole):
            paste_center(img, weight_sprite('N', 80, 64), rx - 105 + (k % 3) * 100, ry + 160 - 30 - (k // 3) * 90)
        if n_right > 4.0 + 1e-3:
            paste_center(img, weight_sprite('.45', 60, 48), rx - 5 + 100, ry + 160 - 120)
        pop(img, C('1 POUND-FORCE', 60, bg=WHITE, dot=GOLD), CX, 300, t, 0.0)
        if t > t4:
            pop(img, C('= 4.45 NEWTONS', 74, bg=YEL), CX, 450, t, t4)
        stamp_in(img, self.stamp, CX, 1700, t, self.we('every') - 0.05)

class Twist(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    punch = 0.18
    def make_shakes(self):
        return [(self.we('twist'), 14, 0.35), (self.we('TEN'), 16, 0.4)]
    def events(self):
        ev = [(self.we('twist') - 0.05, 'scratch', 0.8), (self.we('lopsided') - 0.05, 'squeak', 0.6), (self.we('solar') - 0.05, 'chime', 0.5)]
        tf = self.we('fire') - 0.05
        for k in range(6):
            ev.append((tf + k * 0.32, 'pop', 0.45))
        ev.append((self.we('TEN') - 0.05, 'bigpop', 0.8))
        return ev
    def plate(self):
        return space_plate(4)
    def dyn(self, img, t):
        ts = self.we('solar') - 0.1
        tf = self.we('fire') - 0.05
        # sunlight arrows pushing on the big panel
        if t > ts:
            ov = OV(img, 0, 500, PW, 1300)
            for k in range(5):
                ph = ((t - ts) * 1.6 + k * 0.2) % 1
                y = 640 + k * 110
                x = PW + 60 - ph * 520
                ov.d.line(ov.pts([(x, y), (x + 140, y)]), fill=YEL + (int(255 * (1 - ph)),), width=10)
                ov.d.polygon(ov.pts([(x - 30, y), (x + 4, y - 22), (x + 4, y + 22)]), fill=YEL + (int(255 * (1 - ph)),))
            ov.commit()
        # slow unwanted spin, kicked back by each thruster burst
        spin = 6 * math.sin(t * 2.2) + (4 * ((t - ts) % 0.32) / 0.32 if t > tf else 0)
        cx, cy = CX - 60, 930
        draw_orbiter(img, cx, cy, 0.92, ang=spin)
        if t > tf:
            for k in range(14):
                tk = tf + k * 0.32
                if tk < t:
                    q = (t - tk) / 0.45
                    side = 1 if k % 2 == 0 else -1
                    puff(img, cx - 340, cy + side * 90, q, -1, side * 0.3, 60)
            n = min(10, 1 + int((t - tf) / 0.2))
            pop(img, C(f'x{n} THRUSTER FIRINGS', 60, bg=YEL), CX, 1700, t, tf)
        pop(img, C('THE TWIST?', 70, bg=YEL), CX, 300, t, 0.0, out_t=self.we('lopsided') - 0.1)
        pop(img, C('LOPSIDED SOLAR PANEL', 56, bg=WHITE, dot=BLUE), CX, 300, t, self.we('lopsided') - 0.05)
        if t > ts:
            pop(img, C('SUNLIGHT PUSHES IT', 44, bg=DARK, fg=WHITE), CX + 200, 470, t, ts + 0.2)

class Glitch(S):
    z0, z1 = 1.04, 1.12
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('GLITCH'), 12, 0.3)]
    def events(self):
        return [(0.05, 'tick', 0.6), (self.we('odd') - 0.05, 'buzzer', 0.5), (self.we('assumed') - 0.05, 'swipe', 0.6), (self.we('was'), 'thud', 0.6)]
    def plate(self):
        self.stamp = stamp_sprite('"JUST A GLITCH"', 92, color=(230, 40, 40), angle=-6)
        return plate_img(dark_room('#2A3440', '#090C12', spot=(CX, 900, 1100)))
    def dyn(self, img, t):
        # tracking screen: predicted dashed line vs measured dots drifting away
        x0, y0, x1, y1 = 140, 560, PW - 140, 1250
        ov = OV(img, x0 - 30, y0 - 30, x1 + 30, y1 + 30)
        ov.d.rounded_rectangle(ov.box(x0 - 24, y0 - 24, x1 + 24, y1 + 24), 30, fill=(46, 50, 60, 255))
        ov.d.rectangle(ov.box(x0, y0, x1, y1), fill=(6, 18, 14, 255))
        for gx in range(x0, x1, 100):
            ov.d.line(ov.pts([(gx, y0), (gx, y1)]), fill=(40, 120, 80, 90), width=2)
        for gy in range(y0, y1, 100):
            ov.d.line(ov.pts([(x0, gy), (x1, gy)]), fill=(40, 120, 80, 90), width=2)
        pred = [(x0 + 40 + u * (x1 - x0 - 80), y1 - 120 - u * 420) for u in np.linspace(0, 1, 20)]
        dashed_path(ov, pred, (90, 255, 150, 255), 8)
        n = int(clamp01(t / (self.dur * 0.8)) * 16) + 1
        for k in range(n):
            u = k / 15
            px, py = pred[0][0] + u * (x1 - x0 - 80), pred[0][1] - u * 420 + 160 * u ** 1.8
            r = 16 if k == n - 1 and int(t * 6) % 2 == 0 else 12
            ov.d.ellipse(ov.box(px - r, py - r, px + r, py + r), fill=(255, 90, 80, 255))
        ov.commit()
        paste_center(img, text_img('PREDICTED', 34, fill=(90, 255, 150)), x1 - 160, y0 + 60)
        paste_center(img, text_img('MEASURED', 34, fill=(255, 110, 100)), x1 - 160, y1 - 150)
        pop(img, C('ODD DATA', 64, bg=WHITE, dot=RED), CX, 300, t, self.we('odd') - 0.05)
        stamp_in(img, self.stamp, CX, 1700, t, self.we('assumed') - 0.05)

ALT_Y = {226: 520, 80: 1020, 57: 1170}

class Altitude(S):
    z0, z1 = 1.02, 1.1
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('57'), 18, 0.4)]
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('1999') - 0.03, 'thud', 0.7), (self.we('skimmed') - 0.05, 'wind', 0.7), (self.we('57') - 0.05, 'riser', 0.6), (self.we('KILOMETERS'), 'boom', 0.8), (self.we('not') - 0.05, 'pop', 0.5)]
    def plate(self):
        img = space_plate(6)
        # Mars horizon with layered atmosphere
        ov = OV(img, 0, 0, PW, PH)
        for k, (yy, a) in enumerate(((ALT_Y[80] - 60, 40), (ALT_Y[80] + 40, 70), (ALT_Y[57] + 80, 110), (1320, 160))):
            ov.d.ellipse(ov.box(-1800, yy, PW + 1800, yy + 4000), fill=(255, 140, 80, a))
        ov.commit()
        paste_center(img, planet_sprite(2600), CX, 1350 + 2600 + 40)
        self.stamp = stamp_sprite('1999', 120, color=(230, 40, 40), angle=-7)
        return img
    def dyn(self, img, t):
        ov = OV(img, 0, 400, PW, 1300)
        dashed_path(ov, [(60, ALT_Y[226]), (PW - 60, ALT_Y[226])], (90, 255, 150, 255), 8)
        ov.d.line(ov.pts([(60, ALT_Y[80]), (PW - 60, ALT_Y[80])]), fill=(255, 70, 60, 230), width=8)
        ov.commit()
        # actual path dives down to 57 km
        ts = self.we('skimmed') - 0.1
        u = clamp01((t - ts) / 1.4)
        xs = np.linspace(-40, PW + 40, 40)
        def yv(x):
            q = (x - CX) / 520
            return ALT_Y[57] - (ALT_Y[57] - 360) * min(1, q * q)
        xe = -40 + (PW + 80) * u
        pts = [(x, yv(x)) for x in xs if x <= xe]
        if len(pts) > 1:
            ov = OV(img, 0, 300, PW, 1300)
            ov.d.line(ov.pts(pts), fill=YEL + (255,), width=10, joint='curve')
            ov.commit()
        if u > 0:
            ex = min(xe, PW - 60)
            ey = yv(ex)
            if abs(ex - CX) < 260:
                glow(img, ex, ey, 140, (255, 140, 60), 0.8)
            draw_orbiter(img, ex, ey, 0.24, ang=-15)
        paste_center(img, C('PLANNED: 226 KM', 44, bg=(70, 200, 120), fg=(10, 30, 16)), CX, ALT_Y[226] - 62)
        paste_center(img, C('SURVIVAL LIMIT ~80 KM', 40, bg=RED, fg=WHITE), CX, ALT_Y[80] - 60)
        t57 = self.we('57') - 0.05
        if t > t57:
            pop(img, C('ACTUAL: 57 KM', 64, bg=YEL), CX, 1700, t, t57)
        stamp_in(img, self.stamp, CX, 280, t, self.we('1999') - 0.05)

class Outro(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('BURNED'), 20, 0.5)]
    def events(self):
        return [(0.03, 'wind', 0.7), (self.we('BURNED') - 0.05, 'sizzle', 0.8), (self.we('and') - 0.05, 'boom', 0.6)]
    def plate(self):
        img = space_plate(1)
        paste_center(img, planet_sprite(900), CX + 260, 2050)
        self.hook = Hook([{'w': '$125', 't0': 99, 't1': 99}, {'w': 'math', 't0': 99, 't1': 99}], self.dur, 0)
        self.hook_plate = self.hook.plate()
        return img
    def dyn(self, img, t):
        tb = self.we('BURNED') - 0.05
        x = 380 + 260 * clamp01(t / self.dur)
        y = 600 + 380 * clamp01(t / self.dur)
        heat = 0.3 + 0.7 * ease_out(clamp01((t - tb) / 0.5))
        fire_trail(img, x + 40, y + 70, 1.0, 1.1, 300 + 500 * heat, t, 70 + 70 * heat, a=heat)
        draw_orbiter(img, x, y, 0.55, ang=-38 + 10 * math.sin(t * 8))
        pop(img, C('LIKELY BURNED UP', 70, bg=RED, fg=WHITE), CX, 300, t, tb)
        # final beat: crossfade into the opening frame for a seamless loop
        td = self.dur - 0.5
        if t > td:
            m = ease_in_out(clamp01((t - td) / 0.4))
            fr = self.hook_plate.copy()
            self.hook.dyn(fr, 0.0)
            img.alpha_composite(Image.blend(img, fr, m))

SCENES = [Hook, Journey, Lockheed, Navigators, Factor, Twist, Glitch, Altitude, Outro]
