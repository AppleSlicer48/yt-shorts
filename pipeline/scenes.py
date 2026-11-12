"""Play-Doh was invented to clean wallpaper (2026-11-12)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, table_bg, grain_map
from mw_scenes import glow, stamp_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of, wallpaper_tex, keyframes
from cart_scenes import figure, ground_shadow, store_plate, red_x

GOLD = (240, 160, 60)
RED = (200, 60, 50)
YEL = (255, 210, 60)
DOUGH = '#EFE6D2'          # original off-white compound
COLS = {'white': DOUGH, 'red': '#E0453A', 'yellow': '#F6C93A', 'blue': '#2F7FD8'}

class Base(S):
    focus = (CX, CY)
    z0, z1 = 1.0, 1.06

def rgb_t(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))

# ---------------------------------------------------------------- dough
_BLOB = {}
def blob_sprite(rx, ry, color=DOUGH, seed=0, soot=0.0):
    key = (int(rx), int(ry), color, seed, round(soot, 2))
    if key in _BLOB:
        return _BLOB[key]
    w, h = int(rx * 2.4), int(ry * 2.4)
    L = Layer(w, h)
    c = hexc(color)
    cx, cy = w / 2, h / 2
    rng = np.random.default_rng(seed)
    for k in range(6):
        a = 2 * math.pi * k / 6 + rng.uniform(-0.4, 0.4)
        rr = rng.uniform(0.4, 0.55)
        px, py = cx + math.cos(a) * rx * 0.5, cy + math.sin(a) * ry * 0.5
        ellipsoid(L, (px, py), rx * rr, ry * rr, a, c * 0.97, spec=0.08, shin=10, amb=0.45)
    ellipsoid(L, (cx, cy), rx * 0.97, ry * 0.95, 0.0, c, spec=0.12, shin=10, amb=0.45)
    sp, x0, y0 = layer_sprite(L, 2)
    arr = np.asarray(sp, np.float32) / 255
    n = smooth_noise(sp.height, sp.width, 14, seed + 3, 3)
    fine = smooth_noise(sp.height, sp.width, 3, seed + 9, 1)
    mul = 0.93 + 0.1 * n + 0.05 * (fine - 0.5)
    if soot:
        yy = np.linspace(0, 1, sp.height)[:, None]
        sm = np.clip((yy - 0.45) * 2.2, 0, 1) * (0.6 + 0.6 * n)
        mul = mul * (1 - soot * 0.62 * sm)
    arr = arr.copy()
    arr[..., :3] *= mul[..., None]
    sp = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    _BLOB[key] = sp
    return sp

def paste_blob(img, sp, cx, cy, sx=1.0, sy=1.0, shadow=True):
    s2 = sp.resize((max(1, int(sp.width * sx)), max(1, int(sp.height * sy))), Image.BICUBIC)
    if shadow:
        sh, pad = shadow_of(s2, 16, 0.5)
        paste_at(img, sh, cx - s2.width / 2 - pad + 22, cy - s2.height / 2 - pad + 30)
    paste_at(img, s2, cx - s2.width / 2, cy - s2.height / 2)

# ---------------------------------------------------------------- cans (plain, no branding)
_CAN = {}
def can_sprite(w=300, h=330, body='#F2B630', dough=DOUGH, open_=True, label=None, label_size=40):
    key = (w, h, body, dough, open_, label, label_size)
    if key in _CAN:
        return _CAN[key]
    ss = 2
    eh = int(w * 0.28)
    W_, H_ = w + 40, h + eh + 40
    im = Image.new('RGBA', (W_ * ss, H_ * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 20, 20 + eh // 2
    bc = rgb_t(body)
    def col_at(i):
        u = i / (w - 1)
        k = 0.62 + 0.55 * math.sin(math.pi * (u * 0.9 + 0.05)) ** 0.7 - 0.25 * u
        return tuple(int(min(255, c * k)) for c in bc) + (255,)
    d.ellipse((x0 * ss, (y0 + h - eh / 2) * ss, (x0 + w) * ss, (y0 + h + eh / 2) * ss), fill=tuple(int(c * 0.6) for c in bc) + (255,))
    for i in range(w):
        d.line([((x0 + i) * ss, y0 * ss), ((x0 + i) * ss, (y0 + h) * ss)], fill=col_at(i), width=ss)
    for i in range(w):  # rounded bottom
        u = (i + 0.5) / w * 2 - 1
        dy = eh / 2 * math.sqrt(max(0, 1 - u * u))
        d.line([((x0 + i) * ss, (y0 + h) * ss), ((x0 + i) * ss, (y0 + h + dy) * ss)], fill=col_at(i), width=ss)
    d.ellipse((x0 * ss, (y0 - eh / 2) * ss, (x0 + w) * ss, (y0 + eh / 2) * ss), fill=(225, 228, 232, 255))
    if open_:
        dc = rgb_t(dough)
        d.ellipse(((x0 + 12) * ss, (y0 - eh / 2 + 8) * ss, (x0 + w - 12) * ss, (y0 + eh / 2 - 6) * ss), fill=tuple(int(c * 0.8) for c in dc) + (255,))
        d.ellipse(((x0 + 30) * ss, (y0 - eh / 2 + 12) * ss, (x0 + w - 40) * ss, (y0 + eh / 2 - 16) * ss), fill=dc + (255,))
    else:
        d.ellipse(((x0 + 10) * ss, (y0 - eh / 2 + 8) * ss, (x0 + w - 10) * ss, (y0 + eh / 2 - 8) * ss), fill=(200, 204, 210, 255))
    d.line([(x0 * ss, (y0 + 18) * ss), ((x0 + w) * ss, (y0 + 18) * ss)], fill=(255, 255, 255, 70), width=4 * ss)
    if label:
        lh = int(h * 0.42)
        ly = y0 + h * 0.3
        d.rectangle((x0 * ss, ly * ss, (x0 + w) * ss, (ly + lh) * ss), fill=(250, 244, 228, 255))
        f = font(label_size * ss)
        lines = label.split('\n')
        for k, ln in enumerate(lines):
            bb = f.getbbox(ln)
            tx = x0 * ss + (w * ss - (bb[2] - bb[0])) / 2 - bb[0]
            ty = ly * ss + lh * ss * (k + 0.5) / len(lines) - (bb[3] + bb[1]) / 2
            d.text((tx, ty), ln, font=f, fill=(60, 40, 30, 255))
    im = im.resize((W_, H_), Image.LANCZOS)
    _CAN[key] = im
    return im

def draw_can(img, sp, cx, base_y, scale=1.0, shadow=True):
    s2 = sp if abs(scale - 1.0) < 1e-3 else sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.LANCZOS)
    if shadow:
        ground_shadow(img, cx, base_y - 4, s2.width * 0.95, 0.5)
    paste_at(img, s2, cx - s2.width / 2, base_y - s2.height + 18 * scale)

# ---------------------------------------------------------------- walls
_WALL = {}
def walls(seed=2):
    """(clean, sooty) full-frame wallpaper plates."""
    if seed in _WALL:
        return _WALL[seed]
    arr = wallpaper_tex(PW, PH, c1='#D9A9A0', c2='#E8C4B8', motif='#FFF3E6', stripe=118, seed=seed)
    arr = arr * (0.72 + 0.42 * radial(PW, PH, CX, 1000, 1500, 1.2))[..., None]
    clean = vignette(arr, 0.35)
    n = smooth_noise(PH, PW, 120, seed + 11, 4)
    m = 0.36 + 0.22 * n
    soot = clean * m[..., None] + np.array([0.05, 0.045, 0.04]) * (1 - m[..., None]) * 0.5
    soot = gaussian_filter(soot, (0.6, 0.6, 0))
    _WALL[seed] = (plate_img(clean).convert('RGB'), plate_img(soot).convert('RGB'))
    return _WALL[seed]

def streak_mask(pts, width):
    m = Image.new('L', (PW, PH), 0)
    d = ImageDraw.Draw(m)
    d.line(pts, fill=255, width=int(width), joint='curve')
    x, y = pts[-1]
    d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=255)
    return m.filter(ImageFilter.GaussianBlur(10))

def soot_puff(img, cx, cy, r, k, seed=0):
    if k <= 0 or k >= 1:
        return
    rng = np.random.default_rng(seed)
    ov = OV(img, cx - r * 2.4, cy - r * 2.4, cx + r * 2.4, cy + r * 2.4)
    for j in range(9):
        a = rng.uniform(0, 2 * math.pi)
        dd = r * (0.3 + 1.1 * ease_out(k)) * rng.uniform(0.5, 1.0)
        rr = r * (0.35 + 0.5 * k) * rng.uniform(0.6, 1.0)
        x, y = cx + math.cos(a) * dd, cy + math.sin(a) * dd
        ov.d.ellipse(ov.box(x - rr, y - rr, x + rr, y + rr), fill=(30, 28, 26, int(170 * (1 - k))))
    ov.im = ov.im.filter(ImageFilter.GaussianBlur(10))
    ov.commit()

# ---------------------------------------------------------------- misc props
def coal_sprite(n=26, seed=3, w=700, h=330):
    rng = np.random.default_rng(seed)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(n):
        u = rng.uniform(0.1, 0.9)
        hgt = (1 - abs(u - 0.5) * 2) ** 0.7
        cx = u * w
        cy = h - 50 - rng.uniform(0, 1) * hgt * (h - 130)
        r = rng.uniform(42, 70)
        pts = []
        m = int(rng.integers(5, 8))
        for j in range(m):
            a = 2 * math.pi * j / m + rng.uniform(-0.3, 0.3)
            rr = r * rng.uniform(0.7, 1.05)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8))
        sh = int(rng.uniform(26, 48))
        d.polygon(pts, fill=(sh, sh, sh + 4, 255))
        d.polygon(pts[:3] + [(cx, cy)], fill=(sh + 40, sh + 40, sh + 48, 255))
    return im

def flame_sprite(w=170, h=260, outer=(70, 150, 255), inner=(200, 235, 255)):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for sc, col in ((1.0, outer), (0.55, inner)):
        r = w * 0.42 * sc
        cx, cyb = w / 2, h - 12 - r
        pts = []
        for j in range(41):
            a = math.pi * j / 20  # 0..2pi
            x = cx + math.sin(a) * r
            y = cyb - math.cos(a) * r if math.cos(a) < 0 else cyb - math.cos(a) * r * 0.0
            pts.append((x, y))
        # bottom half circle + pointed top
        poly = [(cx - r, cyb)] + [(cx + math.cos(math.pi - math.pi * j / 20) * r * -1 * -1, cyb + math.sin(math.pi * j / 20) * r) for j in range(21)]
        poly = [(cx - r * math.cos(math.pi * j / 20), cyb + r * math.sin(math.pi * j / 20)) for j in range(21)]
        top = cyb - (h - 20 - 2 * r) * sc - r
        poly += [(cx + r * 0.7, cyb - r * 0.8), (cx, top), (cx - r * 0.7, cyb - r * 0.8)]
        d.polygon(poly, fill=col + (235,))
    return im.filter(ImageFilter.GaussianBlur(3))

def cherry_sprite(R=70):
    L = Layer(int(R * 5), int(R * 5))
    c = hexc('#C8202E')
    capsule(L, (R * 1.6, R * 2.4), (R * 2.6, R * 0.6), 7, 6, hexc('#4E7A2A'))
    capsule(L, (R * 3.3, R * 2.6), (R * 2.6, R * 0.6), 7, 6, hexc('#4E7A2A'))
    sphere(L, (R * 1.5, R * 3.3), R, c, spec=0.7, shin=40)
    sphere(L, (R * 3.4, R * 3.5), R * 0.95, c * 0.95, spec=0.7, shin=40)
    ellipsoid(L, (R * 3.1, R * 0.7), R * 0.6, R * 0.25, -0.4, hexc('#5E9A34'), spec=0.3)
    return layer_sprite(L, 2)[0]

def vanilla_sprite(L_=420):
    Lr = Layer(int(L_ * 1.25), int(L_ * 0.7))
    spindle(Lr, (40, L_ * 0.5), (L_ * 1.1, L_ * 0.15), 22, '#3A2414', spec=0.4, crease=0.3)
    spindle(Lr, (60, L_ * 0.6), (L_ * 1.15, L_ * 0.32), 20, '#4A2E1A', spec=0.4, crease=0.3)
    return layer_sprite(Lr, 2)[0]

def wheat_sprite(Hh=520):
    Lw = Layer(int(Hh * 0.6), int(Hh * 1.05))
    cx = Lw.w / 2
    capsule(Lw, (cx, Hh * 1.0), (cx, Hh * 0.35), 6, 5, hexc('#C99A3E'))
    for k in range(7):
        y = Hh * (0.45 - k * 0.055)
        for s in (-1, 1):
            spindle(Lw, (cx, y + 20), (cx + s * 48, y - 34), 18, '#E2B04C', spec=0.3, crease=0.25)
    spindle(Lw, (cx, Hh * 0.08 + 10), (cx, Hh * 0.0 + 4), 16, '#E2B04C', crease=0.2)
    return layer_sprite(Lw, 2)[0]

def scent_waves(img, cx, y0, t, n=3, h=520, color=(255, 255, 255), a=0.8, spread=110):
    ov = OV(img, cx - spread * 2 - 80, y0 - h - 40, cx + spread * 2 + 80, y0 + 20)
    for j in range(n):
        x0 = cx + (j - (n - 1) / 2) * spread
        pts = []
        for s in range(40):
            u = s / 39
            y = y0 - u * h
            x = x0 + 34 * math.sin(u * 7 + t * 5 + j * 1.7) * (0.3 + u)
            pts.append((x, y))
        ov.d.line(ov.pts(pts), fill=color + (int(255 * a),), width=16, joint='curve')
    ov.im = ov.im.filter(ImageFilter.GaussianBlur(2))
    ov.commit()

def warm_bg(c0='#F3D9A6', c1='#C9875A', seed=4):
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.85 + 0.1 * smooth_noise(PH, PW, 90, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, CX, 1000, 1500, 1.2))[..., None]
    return plate_img(vignette(arr, 0.45))

def classroom_plate():
    arr = vgrad(PW, PH, [(0, '#E7D7B4'), (1, '#B9A17A')])
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 520, PW - 40, 1260), radius=14, fill=(112, 74, 40))
    d.rectangle((80, 560, PW - 80, 1220), fill=(34, 66, 50))
    f = font(140)
    d.text((620, 600), 'A B C', font=f, fill=(225, 230, 220))
    d.ellipse((960, 860, 1120, 1020), outline=(240, 220, 120), width=10)
    for k in range(8):
        a = k * math.pi / 4
        d.line([(1040 + 110 * math.cos(a), 940 + 110 * math.sin(a)), (1040 + 145 * math.cos(a), 940 + 145 * math.sin(a))], fill=(240, 220, 120), width=8)
    arr = to_arr(img)
    fl = wood(PW, PH - 1700, '#B07A45', '#6E4422', seed=6, stretch=10, rings=16, contrast=0.45)
    arr[1700:] = fl * np.linspace(1.0, 0.7, PH - 1700)[:, None, None]
    arr = arr * (0.6 + 0.5 * radial(PW, PH, CX, 1000, 1400, 1.2))[..., None]
    return plate_img(vignette(arr, 0.4))

def kid_table(img, y=1380, x0=520, x1=1240):
    lay = Layer()
    capsule(lay, (x0, y), (x1, y), 30, 30, hexc('#C98A4E'), spec=0.25, grain=grain_map()[:PH, :PW])
    for x in (x0 + 60, x1 - 60):
        capsule(lay, (x, y + 20), (x, y + 300), 18, 16, hexc('#8A5A30'))
    sp, X, Y = layer_sprite(lay, 2)
    sh, pad = shadow_of(sp, 16, 0.45)
    paste_at(img, sh, X - pad + 20, Y - pad + 30)
    paste_at(img, sp, X, Y)

def chart_sprite(k, w=900, h=600):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=(250, 248, 240, 245), outline=(40, 40, 46, 255), width=8)
    for gy in range(1, 5):
        d.line([(50, gy * h / 5), (w - 40, gy * h / 5)], fill=(210, 210, 214, 255), width=3)
    pts = [(60, 150), (200, 120), (330, 140), (440, 110), (560, 170), (680, 340), (830, 530)]
    q = 1 + (len(pts) - 1) * clamp01(k)
    n = int(q)
    seg = pts[:n]
    if n < len(pts):
        u = q - n
        a, b = pts[n - 1], pts[n]
        seg = seg + [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)]
    if len(seg) >= 2:
        d.line(seg, fill=(214, 50, 44, 255), width=24, joint='curve')
    return im

# ====================================================================== scenes
class Hook(Base):
    """Frame 0: a huge lump of dough already mid-rub across sooty wallpaper."""
    z0, z1 = 1.0, 1.05
    punch = 0.0
    y = 1000
    x0, x1 = 660, 800
    def make_shakes(self):
        return [(self.we('WALLPAPER') + 0.05, 16, 0.32)]
    def events(self):
        return [(0.02, 'rustle', 0.7), (0.9, 'squeak', 0.4), (self.we('WALLPAPER', 't1') + 0.01, 'thud', 0.85)]
    def plate(self):
        self.clean, self.soot = walls(2)
        self.blob = [blob_sprite(460, 400, seed=1, soot=s / 4) for s in range(5)]
        self.hand = get_hand(560, 2.35)
        self.chip = C('NOT A TOY... YET', 70, bg=RED, fg=(255, 255, 255))
        return self.soot.copy().convert('RGBA')
    def rub(self, img, t, x, si, chip=True):
        y = self.y + 14 * math.sin(t * 9)
        m = streak_mask([(-400, self.y + 40), (x - 150, y + 30)], 660)
        img.paste(self.clean, (0, 0), m)
        sq = 1 + 0.05 * math.sin(t * 9)
        paste_blob(img, self.blob[si], x, y, sx=sq, sy=1 / sq)
        draw_hand(img, self.hand, (x + 170, y - 250), 0.0)
    def dyn(self, img, t):
        u = clamp01(t / max(self.dur, 1e-3))
        x = self.x0 + (self.x1 - self.x0) * u
        self.rub(img, t, x, min(4, 1 + int(3 * u)))
        pop(img, self.chip, CX, 1830, t, self.we('WALLPAPER') + 0.05)

class Kutol(Base):
    focus = (CX, CY - 40)
    def make_shakes(self):
        return [(self.we('COAL'), 10, 0.25)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('KUTOL'), 'pop', 0.6), (self.we('putty') + 0.05, 'splat', 0.6),
                (self.we('COAL'), 'rattle', 0.6), (self.we('SOOT'), 'wind', 0.5)]
    def plate(self):
        clean, soot = walls(3)
        img = Image.fromarray((np.asarray(soot, np.float32) * 0.8).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)).convert('RGBA')
        ov = OV(img, 0, 1400, PW, PH)
        ov.d.rectangle((0, 0, PW, PH - 1400), fill=(84, 56, 34, 255))
        ov.d.rectangle((0, 0, PW, 26), fill=(120, 84, 52, 255))
        ov.commit()
        self.can = can_sprite(560, 600, body='#3D7A55', label='WALLPAPER\nCLEANER', label_size=64, open_=True)
        self.blob = blob_sprite(190, 140, seed=4)
        self.coal = coal_sprite(14, 5, 520, 260)
        return img
    def dyn(self, img, t):
        tK, tP, tC, tS = self.we('KUTOL'), self.we('putty'), self.we('COAL'), self.we('SOOT')
        sc = 1.0 + 0.06 * (1 - ease_out(t / 0.4))
        draw_can(img, self.can, CX - 140, 1430, scale=sc)
        if t > tP - 0.05:
            k = ease_back((t - tP + 0.05) / 0.4, 1.8)
            paste_blob(img, self.blob, 1020, 1300 - 260 * (1 - clamp01(k)), sx=max(0.05, k), sy=max(0.05, k))
        if t > tC - 0.1:
            u = ease_out((t - tC + 0.1) / 0.35)
            paste_at(img, self.coal, 1000 - self.coal.width / 2, 980 - self.coal.height / 2 - 300 * (1 - u))
        soot_puff(img, 1000, 960, 170, (t - tS) / 0.9, 2)
        pop(img, C('CINCINNATI, OHIO', 67, dot=GOLD), CX, 330, t, 0.5, out_t=tK - 0.12)
        pop(img, C('KUTOL PRODUCTS', 75, bg=YEL), CX, 330, t, tK - 0.05, out_t=tC - 0.12)
        pop(img, C('COAL SOOT REMOVER', 70, bg=(40, 40, 44), fg=(255, 255, 255)), CX, 330, t, tC - 0.05)

class CoalGas(Base):
    def make_shakes(self):
        return [(self.we('GAS'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('homes'), 'pop', 0.5), (self.we('coal'), 'rattle', 0.5), (self.we('GAS'), 'sizzle', 0.6)]
    def plate(self):
        img = warm_bg('#5A463A', '#1A120E', 7)
        self.coal = coal_sprite(34, 7, 900, 480)
        self.flame = flame_sprite(240, 380)
        return img
    def dyn(self, img, t):
        tH, tC, tG = self.we('homes'), self.we('coal'), self.we('GAS')
        pop(img, C('AFTER WORLD WAR II', 70, dot=GOLD), CX, 330, t, 0.05, out_t=tH - 0.1)
        pop(img, C('HOMES SWITCHED HEAT', 67, bg=YEL), CX, 330, t, tH - 0.05)
        sh = -330 * ease_in_out((t - tG + 0.15) / 0.45) if t > tG - 0.15 else 0
        cx = CX + sh
        glow(img, cx, 1150, 460, (255, 120, 40), 0.6 if t < tG else 0.25)
        paste_at(img, self.coal, cx - self.coal.width / 2, 1400 - self.coal.height)
        pop(img, C('COAL', 78, bg=(40, 40, 44), fg=(255, 255, 255)), cx, 800, t, tC - 0.1)
        if t > tG - 0.05:
            red_x(img, cx, 1180, 210, (t - tG) / 0.3)
            k = ease_back((t - tG + 0.05) / 0.35, 1.8)
            fx = CX + 300
            glow(img, fx, 1150, 380, (80, 150, 255), 0.65)
            for j in (0, 2, 1):
                fl = math.sin(t * 22 + j * 2) * 0.06
                paste_center(img, self.flame, fx + (j - 1) * 130, 1200 - 50 * (j == 1), scale=max(0.05, k * (0.8 + 0.25 * (j == 1) + fl)))
            pop(img, C('GAS', 83, bg=(50, 120, 220), fg=(255, 255, 255)), fx, 800, t, tG)

class Crash(Base):
    def make_shakes(self):
        return [(self.we('CRASHED'), 18, 0.35)]
    def events(self):
        return [(0.02, 'pop', 0.5), (self.we('customers'), 'buzzer', 0.4), (self.we('sales'), 'swipe', 0.5), (self.we('CRASHED', 't1') + 0.01, 'thud', 0.9)]
    def plate(self):
        img = warm_bg('#D9C3A0', '#8E6E4E', 8)
        self.can = can_sprite(240, 260, body='#3D7A55', open_=False, label='CLEANER', label_size=38)
        self.stamp = stamp_sprite('SALES CRASHED', 120, angle=-8)
        return img
    def dyn(self, img, t):
        tS, tX = self.we('sales'), self.we('CRASHED')
        k = 0.67 + 0.33 * clamp01((t - tS + 0.2) / (tX - tS + 0.25))
        paste_center(img, chart_sprite(k), CX, 900)
        pop(img, C('NO SOOT = NO CUSTOMERS', 64, bg=RED, fg=(255, 255, 255)), CX, 440, t, 0.05)
        for j, x in enumerate((300, 650, 1000)):
            tilt = 0
            if t > tX:
                tilt = 22 * ease_back(clamp01((t - tX) / 0.35)) * (1 if j % 2 else -1)
            draw_can(img, self.can.rotate(tilt, expand=True, resample=Image.BICUBIC), x, 1450, 0.85)
        stamp_in(img, self.stamp, CX, 900, t, tX)

class Teacher(Base):
    focus = (CX, CY - 20)
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Kay') - 0.05, 'ding', 0.6), (self.we("McVicker's") - 0.05, 'pop', 0.5),
                (self.we('tried'), 'pop', 0.5)]
    def plate(self):
        img = classroom_plate()
        sp, info = figure(1180, 'woman', push=False)
        ground_shadow(img, 290, 1790, 300)
        paste_at(img, sp, int(290 - info['foot'][0]), int(1790 - info['foot'][1]))
        kid_table(img, 1420)
        self.kids = [figure(600, k, push=True)[0] for k in ('man', 'woman', 'man')]
        self.blob = blob_sprite(120, 80, seed=6)
        return img
    def dyn(self, img, t):
        tK, tM, tT = self.we('Kay'), self.we("McVicker's"), self.we('tried')
        pop(img, C('NURSERY SCHOOL TEACHER', 65, dot=GOLD), CX, 330, t, 0.1, out_t=tK - 0.12)
        pop(img, C('KAY ZUFALL', 84, bg=YEL), CX, 330, t, tK - 0.05)
        pop(img, C("JOE McVICKER'S SISTER-IN-LAW", 52), CX, 460, t, tM - 0.05)
        for j, sp in enumerate(self.kids):
            tj = tT - 0.3 + j * 0.12
            if t > tj:
                k = ease_back((t - tj) / 0.35, 1.6)
                x = 680 + j * 220
                paste_at(img, sp, x - sp.width / 2, 1420 + 20 - sp.height * 0.6 + 160 * (1 - clamp01(k)))
        if t > tT - 0.1:
            paste_blob(img, self.blob, 900, 1360, sx=1 + 0.05 * math.sin(t * 7), sy=1 - 0.05 * math.sin(t * 7))

class Kids(Base):
    z0, z1 = 1.04, 1.12
    def make_shakes(self):
        return [(self.we('TOY'), 14, 0.3)]
    def events(self):
        return [(0.02, 'splat', 0.6), (self.we('squishing'), 'squeak', 0.4), (self.we('molding'), 'pop', 0.5),
                (self.we('pushed') - 0.05, 'pop', 0.5), (self.we('TOY', 't1') + 0.01, 'thud', 0.9)]
    def plate(self):
        img = plate_img(table_bg(9))
        self.big = blob_sprite(340, 260, seed=8)
        self.hand = get_hand(520, 2.2)
        self.snake = blob_sprite(250, 60, seed=9)
        self.ball = blob_sprite(110, 100, seed=10)
        self.stamp = stamp_sprite('SELL IT AS A TOY!', 100, color=(40, 120, 200), angle=-7)
        return img
    def dyn(self, img, t):
        tM, tP, tT = self.we('molding'), self.we('pushed'), self.we('TOY')
        pop(img, C('KIDS LOVED IT', 78, bg=YEL), CX, 330, t, 0.05, out_t=tP - 0.1)
        ph = (math.sin(t * 6.5) + 1) / 2
        sq = 1 + 0.22 * ph
        paste_blob(img, self.big, CX, 980 + 30 * ph, sx=sq, sy=1 / sq)
        draw_hand(img, self.hand, (CX + 130, 790 + 70 * ph), 0.3 * (1 - ph))
        if t > tM - 0.1:
            k = ease_back((t - tM + 0.1) / 0.35, 1.8)
            paste_blob(img, self.snake.rotate(12, expand=True, resample=Image.BICUBIC), 330, 1330, sx=max(0.05, k), sy=max(0.05, k))
            paste_blob(img, self.ball, 960, 1310, sx=max(0.05, k), sy=max(0.05, k))
        pop(img, C('"MAKE IT A TOY!"', 75, bg=(50, 120, 220), fg=(255, 255, 255)), CX, 330, t, tP - 0.05, out_t=tT - 0.1)
        stamp_in(img, self.stamp, CX, 380, t, tT)

class Name(Base):
    z0, z1 = 1.02, 1.1
    def make_shakes(self):
        return [(self.we('PLAY-DOH'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('husband') - 0.05, 'pop', 0.5), (self.we('name'), 'riser', 0.5), (self.we('PLAY-DOH', 't1') + 0.01, 'bigpop', 0.9)]
    def plate(self):
        img = warm_bg('#FBE3B0', '#E08A5A', 11)
        w, info = figure(1000, 'woman', push=False)
        m, info2 = figure(1060, 'man', push=False)
        self.figs = [(w, info, 230), (m, info2, 1060)]
        self.blob = blob_sprite(250, 190, seed=12)
        self.stamp = stamp_sprite('PLAY-DOH', 170, color=(214, 50, 44), angle=-8)
        return img
    def dyn(self, img, t):
        tH, tN, tP = self.we('husband'), self.we('name'), self.we('PLAY-DOH')
        sp, info, x = self.figs[0]
        ground_shadow(img, x, 1720, 260)
        paste_at(img, sp, int(x - info['foot'][0]), int(1720 - info['foot'][1]))
        if t > tH - 0.1:
            sp, info, x = self.figs[1]
            k = ease_out((t - tH + 0.1) / 0.3)
            xx = x + 360 * (1 - k)
            ground_shadow(img, xx, 1720, 260)
            paste_at(img, sp, int(xx - info['foot'][0]), int(1720 - info['foot'][1]))
        paste_blob(img, self.blob, CX, 1200 + 10 * math.sin(t * 6))
        pop(img, C('KAY + HER HUSBAND', 72, dot=GOLD), CX, 330, t, 0.1, out_t=tN - 0.1)
        pop(img, C('THE NAME?', 80, bg=YEL), CX, 330, t, tN - 0.05, out_t=tP - 0.05)
        stamp_in(img, self.stamp, CX, 440, t, tP)

class OneColor(Base):
    z0, z1 = 1.02, 1.14
    def make_shakes(self):
        return [(self.we('WHITE'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1956'), 'thud', 0.7), (self.we('ONE'), 'pop', 0.6), (self.we('WHITE', 't1') + 0.01, 'thud', 0.8)]
    def plate(self):
        img = store_plate(3, blur=6, dark=0.8)
        self.can = can_sprite(520, 470, body='#F2B630', dough=DOUGH)
        self.stamp = stamp_sprite('WHITE ONLY', 130, color=(226, 40, 40), angle=-7)
        self.st56 = stamp_sprite('1956', 160, color=(40, 120, 200), angle=-6)
        return img
    def dyn(self, img, t):
        t56, tO, tW = self.we('1956'), self.we('ONE'), self.we('WHITE')
        k = ease_back(t / 0.35, 1.6)
        draw_can(img, self.can, CX, 1430 + 300 * (1 - clamp01(k)))
        pop(img, C('1956', 84, bg=(40, 120, 200), fg=(255, 255, 255)), CX, 380, t, t56 - 0.05)
        pop(img, C('ONE COLOR', 80, bg=YEL), CX, 640, t, tO - 0.05, out_t=tW - 0.08)
        stamp_in(img, self.stamp, CX, 640, t, tW)

class Colors(Base):
    z0, z1 = 1.0, 1.06
    def events(self):
        return [(self.we('Red'), 'bigpop', 0.6), (self.we('yellow'), 'bigpop', 0.6), (self.we('blue'), 'bigpop', 0.6), (self.we('YEAR', 't1') + 0.01, 'ding', 0.6)]
    def plate(self):
        img = store_plate(3, blur=6, dark=0.8)
        self.cans = {c: can_sprite(360, 340, body=b, dough=COLS[c]) for c, b in
                     (('white', '#F2B630'), ('red', '#F2B630'), ('yellow', '#E0453A'), ('blue', '#F2B630'))}
        return img
    def dyn(self, img, t):
        tY = self.we('YEAR')
        pos = {'white': (350, 1000), 'red': (950, 1000), 'yellow': (350, 1440), 'blue': (950, 1440)}
        draw_can(img, self.cans['white'], *pos['white'])
        for c, key in (('red', 'Red'), ('yellow', 'yellow'), ('blue', 'blue')):
            t0 = self.we(key) - 0.08
            if t > t0:
                k = ease_back((t - t0) / 0.3, 2.0)
                x, y = pos[c]
                draw_can(img, self.cans[c], x, y, scale=max(0.05, k))
        pop(img, C('+ 3 COLORS', 78, bg=YEL), CX, 330, t, 0.05, out_t=tY - 0.1)
        pop(img, C('THE VERY NEXT YEAR', 72, bg=YEL), CX, 330, t, tY - 0.05)

class Smell(Base):
    z0, z1 = 1.04, 1.14
    def make_shakes(self):
        return [(self.we('TRADEMARK'), 16, 0.35)]
    def events(self):
        return [(self.we('2018'), 'thud', 0.7), (self.we('SMELL'), 'swipe', 0.6), (self.we('official'), 'riser', 0.4), (self.we('TRADEMARK', 't1') + 0.01, 'thud', 0.9)]
    def plate(self):
        img = warm_bg('#BFD8F2', '#5E7FB0', 13)
        self.can = can_sprite(540, 480, body='#F2B630', dough=COLS['red'])
        self.stamp = stamp_sprite('TRADEMARKED SMELL', 74, color=(214, 50, 44), angle=-7)
        self.st18 = stamp_sprite('2018', 160, color=(40, 120, 200), angle=-6)
        return img
    def dyn(self, img, t):
        t18, tS, tT = self.we('2018'), self.we('SMELL'), self.we('TRADEMARK')
        draw_can(img, self.can, CX, 1430, 1.0 + 0.03 * math.sin(t * 4))
        if t > tS - 0.1:
            a = clamp01((t - tS + 0.1) / 0.3) * 0.85
            scent_waves(img, CX, 960, t, 3, 560, (255, 255, 255), a, 150)
        pop(img, C('2018', 84, bg=(40, 120, 200), fg=(255, 255, 255)), CX, 330, t, t18 - 0.05)
        pop(img, C('ITS SMELL', 78, bg=YEL), CX, 600, t, tS - 0.05, out_t=tT - 0.1)
        stamp_in(img, self.stamp, CX, 640, t, tT)

class Recipe(Base):
    z0, z1 = 1.0, 1.08
    def events(self):
        return [(self.we('vanilla'), 'pop', 0.6), (self.we('CHERRY'), 'pop', 0.6), (self.we('salty') - 0.05, 'pop', 0.6), (self.we('wheat'), 'ding', 0.5)]
    def plate(self):
        img = warm_bg('#F7E1C2', '#C79A6E', 14)
        self.van = vanilla_sprite(430)
        self.cher = cherry_sprite(80)
        self.wheat = wheat_sprite(400)
        self.blob = blob_sprite(170, 120, seed=15)
        return img
    def dyn(self, img, t):
        items = [('vanilla', self.van, (330, 640), 840, C('SWEET VANILLA', 60, bg=(255, 245, 225))),
                 ('CHERRY', self.cher, (960, 610), 840, C('CHERRY', 66, bg=(200, 32, 46), fg=(255, 255, 255))),
                 ('salty', self.blob, (330, 1110), 1310, C('SALTY DOUGH', 60, bg=YEL)),
                 ('wheat', self.wheat, (960, 1090), 1310, C('WHEAT', 66, bg=(226, 176, 76)))]
        pop(img, C('THE OFFICIAL SMELL', 70, dot=GOLD), CX, 330, t, 0.02)
        for key, sp, (x, y), cy, ch in items:
            t0 = self.we(key) - 0.08
            if t > t0:
                k = ease_back((t - t0) / 0.32, 2.0)
                bob = 8 * math.sin(t * 5 + x)
                if sp is self.blob:
                    paste_blob(img, sp, x, y + bob, sx=max(0.05, k), sy=max(0.05, k))
                else:
                    paste_center(img, sp, x, y + bob, scale=max(0.05, k))
                pop(img, ch, x, cy, t, t0 + 0.05)

class Outro(Hook):
    """Billions of cans, then straight back to the dough on the sooty wall (loops into the hook)."""
    punch = 0.13
    def make_shakes(self):
        return []
    def events(self):
        return [(0.02, 'party', 0.4), (self.we('nobody') - 0.05, 'scratch', 0.6), (self.we('remembers'), 'rustle', 0.6)]
    def plate(self):
        img = super().plate()
        grid = warm_bg('#3A2C52', '#120C1E', 16)
        bodies = ['#F2B630', '#E0453A', '#2F7FD8', '#3BAA5C']
        doughs = list(COLS.values())
        for r in range(10):
            for c in range(7):
                sp = can_sprite(170, 160, body=bodies[(r + c) % 4], dough=doughs[(r * 2 + c) % 4])
                draw_can(grid, sp, 60 + c * 200 + (r % 2) * 90, 300 + r * 230, 1.0, shadow=False)
        self.grid = grid.convert('RGB')
        return img
    def dyn(self, img, t):
        tN = self.we('nobody') - 0.05
        if t < tN:
            img.paste(self.grid, (0, 0))
            pop(img, C('BILLIONS OF CANS', 84, bg=YEL), CX, 1000, t, 0.05)
            return
        tt = t - tN
        u = clamp01(tt / max(self.dur - tN, 1e-3))
        self.rub(img, tt, self.x0 - 160 + 160 * u, 1)
    def cam(self, t):
        tN = self.we('nobody') - 0.05
        dx, dy, dr = self.shake(t)
        if t < tN:
            z = 1.0 + 0.14 * (t / tN)
            return z, CX, CY, 0.0
        p = 1 - ease_out((t - tN) / 0.3)
        return 1.0 + 0.1 * p, CX, CY, 1.5 * p

SCENES = [Hook, Kutol, CoalGas, Crash, Teacher, Kids, Name, OneColor, Colors, Smell, Recipe, Outro]
