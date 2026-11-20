"""Bubble gum was invented by an accountant (Walter Diemer, Fleer, 1928) (2026-11-20)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish, table_bg
from mw_scenes import glow, stamp_sprite, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import red_x

RED = (214, 50, 44)
YEL = (255, 210, 60)
GREEN = (60, 170, 90)
WHITE = (255, 255, 255)
PINK = (255, 120, 170)
PINKH = '#FF7DB0'

class Base(S):
    focus = (CX, 1080)
    z0, z1 = 1.22, 1.32

# ====================================================================== helpers
def with_shadow(img, sp, cx, cy, blur=14, a=0.45, dx=18, dy=26):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, cx - sp.width / 2 - pad + dx, cy - sp.height / 2 - pad + dy)
    paste_at(img, sp, cx - sp.width / 2, cy - sp.height / 2)

_SP = {}
def cached(key, fn):
    if key not in _SP:
        _SP[key] = fn()
    return _SP[key]

def rot(sp, ang, key=None):
    if key is not None:
        k = (key, int(round(ang)) % 360)
        if k in _SP:
            return _SP[k]
    r = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
    if key is not None:
        _SP[k] = r
    return r

def qmark(size=220, col=(255, 255, 255)):
    return cached(('q', size, col), lambda: text_img('?', size, fill=col, stroke=12, stroke_fill=(20, 20, 30), shadow_px=5))

def bubble_sprite(R=440, col=PINKH, gray=False):
    """Glossy pink gum bubble."""
    def mk():
        lay = Layer(int(R * 2.3), int(R * 2.3))
        c = R * 1.15
        sphere(lay, (c, c), R, '#9A9288' if gray else col, spec=0.15 if gray else 0.55, shin=40, amb=0.5)
        sp, _, _ = layer_sprite(lay, 2)
        d = ImageDraw.Draw(sp, 'RGBA')
        cx, cy = sp.width / 2, sp.height / 2
        if not gray:
            # window highlight + rim light
            d.ellipse((cx - R * 0.62, cy - R * 0.66, cx - R * 0.2, cy - R * 0.36), fill=(255, 255, 255, 170))
            d.ellipse((cx - R * 0.2, cy - R * 0.7, cx - R * 0.08, cy - R * 0.58), fill=(255, 255, 255, 150))
            d.arc((cx - R * 0.9, cy - R * 0.9, cx + R * 0.9, cy + R * 0.9), 20, 80, fill=(255, 210, 230, 160), width=max(4, R // 25))
        else:
            rng = np.random.default_rng(5)
            for _ in range(9):
                a0 = rng.uniform(0, 6.28)
                x0, y0 = cx + math.cos(a0) * R * 0.3, cy + math.sin(a0) * R * 0.3
                pts = [(x0, y0)]
                for k in range(4):
                    a0 += rng.uniform(-0.6, 0.6)
                    x0 += math.cos(a0) * R * 0.16; y0 += math.sin(a0) * R * 0.16
                    pts.append((x0, y0))
                d.line(pts, fill=(60, 55, 50, 230), width=max(3, R // 40))
        return sp
    return cached(('bub', R, col, gray), mk)

def head_sprite(Hh=560, profile=True):
    """Wooden mannequin head + neck + shoulders, facing right; pencil behind the ear."""
    def mk():
        lay = Layer(int(Hh * 1.6), int(Hh * 1.6))
        col = hexc(ARM_LIGHT); j = col * 0.86
        kw = dict(grain=grain_map(), spec=0.28, shin=22)
        cx, cy = Hh * 0.7, Hh * 0.55
        ellipsoid(lay, (cx - Hh * 0.05, cy + Hh * 0.62), Hh * 0.5, Hh * 0.2, 0, col, **kw)
        capsule(lay, (cx, cy + Hh * 0.2), (cx - Hh * 0.02, cy + Hh * 0.5), Hh * 0.11, Hh * 0.12, j, **kw)
        ellipsoid(lay, (cx, cy), Hh * 0.27, Hh * 0.32, 0.15, col, **kw)
        ellipsoid(lay, (cx + Hh * 0.16, cy + Hh * 0.12), Hh * 0.13, Hh * 0.15, 0.4, col, **kw)
        ellipsoid(lay, (cx - Hh * 0.04, cy + Hh * 0.02), Hh * 0.05, Hh * 0.08, 0, j, **kw)  # ear
        sp, _, _ = layer_sprite(lay, 2)
        d = ImageDraw.Draw(sp)
        # pencil behind the ear
        ox = sp.width / 2 - lay.w / 2 if False else 0
        return sp
    return cached(('head', Hh), mk)

def pencil_sprite(L=300):
    def mk():
        im = Image.new('RGBA', (L + 10, 60), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((30, 12, L - 60, 48), fill=(245, 190, 40, 255))
        d.rectangle((30, 12, L - 60, 22), fill=(255, 215, 90, 255))
        d.rectangle((0, 12, 34, 48), fill=(240, 130, 150, 255))
        d.rectangle((28, 10, 44, 50), fill=(190, 190, 196, 255))
        d.polygon([(L - 60, 12), (L, 30), (L - 60, 48)], fill=(235, 200, 160, 255))
        d.polygon([(L - 20, 24), (L, 30), (L - 20, 36)], fill=(40, 40, 44, 255))
        return im
    return cached(('pencil', L), mk)

def ledger_sprite(w=960):
    def mk():
        h = int(w * 0.68)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 10, w, h), radius=20, fill=(40, 70, 50, 255))
        d.rectangle((24, 0, w / 2 - 6, h - 22), fill=(248, 244, 228, 255))
        d.rectangle((w / 2 + 6, 0, w - 24, h - 22), fill=(248, 244, 228, 255))
        d.line([(w / 2, 0), (w / 2, h - 22)], fill=(120, 110, 90, 255), width=6)
        f = font(34, FONT_BOLD)
        nums = ['$ 12.40', '$ 3.15', '$ 47.00', '$ 8.95', '$ 21.30', '$ 5.60', '$ 66.75', '$ 0.99']
        for k in range(8):
            y = 40 + k * (h - 90) / 8
            for side in (0, 1):
                x0 = 50 if side == 0 else w / 2 + 30
                d.line([(x0, y + 44), (x0 + w / 2 - 90, y + 44)], fill=(150, 190, 210, 255), width=3)
                d.text((x0 + w / 2 - 230, y), nums[(k + side * 3) % 8], font=f, fill=(40, 40, 60, 255))
                d.line([(x0 + 10, y + 22), (x0 + 120 + (k * 31 % 60), y + 22)], fill=(110, 110, 130, 255), width=8)
        d.line([(w * 0.72, 0), (w * 0.72, h - 22)], fill=(220, 120, 120, 255), width=3)
        d.line([(w * 0.22, 0), (w * 0.22, h - 22)], fill=(220, 120, 120, 255), width=3)
        return im
    return cached(('ledger', w), mk)

def goo_sprite(R=260, seed=1, col=(236, 200, 170), gloss=0.5):
    """Lumpy glossy gum blob (dome-shaded)."""
    def mk():
        from scipy.ndimage import gaussian_filter
        n = int(R * 2.4)
        rng = np.random.default_rng(seed)
        ph = rng.uniform(0, 6.28, 3)
        pts = []
        for k in range(72):
            a = 2 * math.pi * k / 72
            r = R * (1 + 0.07 * math.sin(3 * a + ph[0]) + 0.05 * math.sin(5 * a + ph[1]))
            pts.append((n / 2 + math.cos(a) * r, n / 2 + math.sin(a) * r * 0.75))
        ss = 3
        m = Image.new('L', (n * ss, n * ss), 0)
        ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
        a = np.asarray(m.resize((n, n), Image.BOX), np.float32) / 255
        hgt = gaussian_filter(a, R * 0.3)
        hgt = np.clip(hgt / max(1e-3, hgt.max()), 0, 1) * a
        gy, gx = np.gradient(hgt * R * 1.0)
        nn = np.sqrt(gx * gx + gy * gy + 1)
        nx, ny, nz = -gx / nn, -gy / nn, 1 / nn
        ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        base = np.array(col, np.float32) / 255
        rgb = base[None, None, :] * (0.42 + 0.72 * ndl)[..., None] + (ndh ** 30 * gloss)[..., None]
        return Image.fromarray((np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1) * 255 + 0.5).astype(np.uint8), 'RGBA')
    return cached(('goo', R, seed, col, gloss), mk)

def bowl_sprite(w=620, col=(255, 140, 185)):
    def mk():
        h = int(w * 0.62)
        lay = Layer(w + 40, h + 40)
        fill_poly(lay, [(20, 80), (w + 20, 80), (w * 0.8 + 20, h + 10), (w * 0.2 + 20, h + 10)], '#5FA8D8')
        fill_poly(lay, [(w * 0.62, 80), (w + 20, 80), (w * 0.8 + 20, h + 10), (w * 0.6, h + 10)], '#3F84B8')
        sp, _, _ = layer_sprite(lay, 2)
        d = ImageDraw.Draw(sp)
        d.ellipse((2, 20, sp.width - 2, 150), fill=(70, 130, 190, 255))
        d.ellipse((30, 34, sp.width - 30, 136), fill=col + (255,))
        return sp
    return cached(('bowl', w, col), mk)

def wrapped_piece(w=96, col=(255, 130, 175)):
    def mk():
        h = int(w * 0.55)
        im = Image.new('RGBA', (int(w * 1.7), h + 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x0 = int(w * 0.35)
        d.polygon([(0, 5), (x0, h * 0.35 + 5), (x0, h * 0.65 + 5), (0, h + 5)], fill=(250, 240, 210, 255))
        d.polygon([(im.width, 5), (im.width - x0, h * 0.35 + 5), (im.width - x0, h * 0.65 + 5), (im.width, h + 5)], fill=(250, 240, 210, 255))
        d.rounded_rectangle((x0 - 4, 5, im.width - x0 + 4, h + 5), radius=10, fill=col + (255,), outline=(180, 60, 100, 255), width=3)
        d.line([(x0 + 8, 12), (im.width - x0 - 8, 12)], fill=(255, 220, 235, 255), width=5)
        return im
    return cached(('wrap', w, col), mk)

def calendar_sprite(n, w=420):
    def mk():
        h = int(w * 1.05)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w, h), radius=26, fill=(250, 250, 246, 255), outline=(60, 60, 66, 255), width=6)
        d.rounded_rectangle((0, 0, w, h * 0.28), radius=26, fill=(214, 50, 44, 255))
        d.rectangle((0, h * 0.16, w, h * 0.28), fill=(214, 50, 44, 255))
        f = font(int(w * 0.12))
        t = 'MONTH'
        d.text(((w - f.getlength(t)) / 2, h * 0.06), t, font=f, fill=(255, 255, 255))
        f2 = font(int(w * 0.5))
        t2 = str(n)
        bb = f2.getbbox(t2)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], h * 0.62 - (bb[3] + bb[1]) / 2), t2, font=f2, fill=(30, 30, 36))
        for k in (0.25, 0.75):
            d.ellipse((w * k - 18, -14, w * k + 18, 22), fill=(80, 80, 86, 255))
        return im
    return cached(('cal', n, w), mk)

def bottle_sprite(col, full=True, w=200):
    def mk():
        h = int(w * 1.9)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        body = (w * 0.08, h * 0.3, w * 0.92, h * 0.98)
        d.rounded_rectangle(body, radius=int(w * 0.14), fill=(220, 235, 245, 110), outline=(240, 250, 255, 255), width=7)
        if full:
            d.rounded_rectangle((w * 0.12, h * 0.42, w * 0.88, h * 0.95), radius=int(w * 0.12), fill=col + (255,))
            d.line([(w * 0.22, h * 0.46), (w * 0.22, h * 0.86)], fill=(255, 255, 255, 140), width=10)
        d.rectangle((w * 0.34, h * 0.16, w * 0.66, h * 0.31), fill=(240, 250, 255, 200))
        d.rounded_rectangle((w * 0.28, 0, w * 0.72, h * 0.18), radius=14, fill=(40, 40, 46, 255))
        d.rectangle((w * 0.2, h * 0.58, w * 0.8, h * 0.74), fill=(250, 246, 230, 255))
        d.ellipse((w * 0.4, h * 0.6, w * 0.6, h * 0.72), fill=col + (255,))
        return im
    return cached(('bottle', col, full, w), mk)

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
        top = vgrad(PW, PH - y0, [(0, col), (1, '#1A1410')])
        arr[y0:] = top * (0.9 + 0.1 * smooth_noise(PH - y0, PW, 40, seed + 3, 2))[..., None]
        arr[y0:y0 + 10] *= 1.25
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    _PL[key] = img
    return img.copy()

def table_plate(seed=5):
    key = ('table', seed)
    if key not in _PL:
        _PL[key] = plate_img(table_bg(seed))
    return _PL[key].copy()

def hook_plate():
    return wall_plate('#7FD6E8', '#2A5FA0', 31, (CX, 950, 1250))

def night_plate():
    key = 'night'
    if key not in _PL:
        arr = vgrad(PW, PH, [(0, '#16224A'), (1, '#060914')])
        arr = arr * (0.8 + 0.35 * radial(PW, PH, CX, 1100, 1200, 1.2))[..., None]
        img = to_img(arr).convert('RGBA')
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(3)
        for _ in range(140):
            x, y = rng.uniform(0, PW), rng.uniform(0, 1300)
            r = rng.choice([2, 2, 3, 4])
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 230, 255))
        d.ellipse((PW - 430, 330, PW - 190, 570), fill=(250, 244, 210, 255))
        d.ellipse((PW - 360, 300, PW - 140, 520), fill=(22, 32, 70, 255))
        _PL[key] = img
    return _PL[key].copy()

# ====================================================================== 0: hook - head blowing a giant pink bubble
class Hook(Base):
    z0, z1 = 1.3, 1.36
    BX, BY = CX + 185, 1040
    def bub_r(self, t):
        # inflating from frame 0 (already big), wobbling
        return 360 + 40 * ease_out(clamp01(t / 2.2)) + 8 * math.sin(t * 9)
    def make_shakes(self):
        return [(0.0, 10, 0.25), (self.we('an') - 0.02, 18, 0.35)]
    def events(self):
        return [(0.0, 'bigpop', 0.6), (0.05, 'squeak', 0.45), (self.we('invented') - 0.03, 'pop', 0.45),
                (self.we('an') - 0.03, 'boom', 0.6)]
    def plate(self):
        self.head = head_sprite(620)
        self.bub = bubble_sprite(440)
        self.pen = rot(pencil_sprite(300), 25)
        self.st = stamp_sprite('AN ACCOUNTANT!', 96, color=RED, angle=-7)
        return hook_plate()
    def hero(self, img, t):
        hx, hy = CX - 150, 1130
        with_shadow(img, self.head, hx, hy, a=0.35, blur=18)
        # pencil behind the ear
        paste_center(img, self.pen, hx - 70, hy - 330)
        r = self.bub_r(t)
        s = r / 440
        paste_center(img, self.bub, self.BX + (r - 385) * 0.6, self.BY, scale=s)
    def dyn(self, img, t):
        self.hero(img, t)
        tA = self.we('an')
        stamp_in(img, self.st, CX, 1760, t, tA - 0.02)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, 1070 + dy, dr

# ====================================================================== 1: and the pink color has a weirder story
class WhyPink(Base):
    z0, z1 = 1.24, 1.36
    def make_shakes(self):
        return [(self.we('pink'), 14, 0.3), (self.we('weirder'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('pink') - 0.03, 'bloop', 0.6), (self.we('color') - 0.03, 'pop', 0.45),
                (self.we('weirder') - 0.03, 'riser', 0.5)]
    def plate(self):
        self.bub = bubble_sprite(330)
        return wall_plate('#FFD1E4', '#B23A78', 7, (CX, 1000, 1250))
    def dyn(self, img, t):
        glow(img, CX, 1000, 560, (255, 230, 240), 0.5)
        s = 1 + 0.03 * math.sin(t * 6)
        paste_center(img, self.bub, CX, 1000, scale=s)
        tW = self.we('weirder')
        for k in range(4):
            a = t * 1.3 + k * math.pi / 2
            x = CX + math.cos(a) * 460
            y = 1000 + math.sin(a) * 380
            pop(img, qmark(150 if k % 2 else 190, YEL if k % 2 else WHITE), x, y, t, tW - 0.06 + k * 0.08)
        pop(img, C('WHY PINK?', 110, bg=YEL), CX, 520, t, self.we('pink') - 0.06)
        pop(img, C('EVEN WEIRDER...', 84, bg=WHITE), CX, 1760, t, tW - 0.06)

# ====================================================================== 2: 1928, Walter Diemer kept the books
class Books(Base):
    z0, z1 = 1.22, 1.34
    def make_shakes(self):
        return [(self.we('1928'), 12, 0.25), (self.we('books'), 14, 0.3), (self.we('Philadelphia'), 10, 0.25)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1928') - 0.03, 'thud', 0.7), (self.we('Walter') - 0.03, 'pop', 0.5),
                (self.we('books') - 0.03, 'scratch', 0.6), (self.we('Philadelphia') - 0.03, 'ding', 0.5)]
    def plate(self):
        self.book = ledger_sprite(1000)
        self.hand = get_hand(520, -2.3)
        self.pen = rot(pencil_sprite(360), 125)
        self.st = stamp_sprite('ACCOUNTANT', 130, color=(40, 120, 70), angle=-8)
        return table_plate(4)
    def dyn(self, img, t):
        with_shadow(img, rot(self.book, 3, 'book'), CX, 1080, a=0.5)
        # hand writing with a pencil, moving along the line
        u = t * 2.2
        x = CX - 120 + 140 * math.sin(u)
        y = 1040 + 70 * ((t * 0.6) % 1) + 8 * abs(math.sin(u * 3))
        paste_center(img, self.pen, x + 80, y - 120)
        draw_hand(img, self.hand, (x + 20, y - 40))
        pop(img, C('1928', 100, bg=WHITE), CX - 300, 520, t, self.we('1928') - 0.06)
        pop(img, C('WALTER DIEMER', 80, bg=YEL), CX + 120, 660, t, self.we('Walter') - 0.06)
        stamp_in(img, self.st, CX, 1520, t, self.we('books') - 0.02)
        pop(img, C('PHILADELPHIA GUM COMPANY', 58, bg=WHITE), CX, 1830, t, self.we('Philadelphia') - 0.06)

# ====================================================================== 3: Blibber-Blubber was too sticky, shelved
class Sticky(Base):
    z0, z1 = 1.24, 1.34
    def tcut(self):
        return self.we('got') - 0.05
    def make_shakes(self):
        return [(self.we('BlibberBlubber'), 12, 0.3), (self.we('sticky'), 16, 0.35), (self.tcut(), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('BlibberBlubber') - 0.03, 'bloop', 0.6), (self.we('sticky') - 0.03, 'splat', 0.7),
                (self.tcut(), 'thud', 0.8)]
    def plate(self):
        self.goo = goo_sprite(300, 3, (240, 150, 185), 0.6)
        self.hand = get_hand(560, 1.45)
        self.st = stamp_sprite('SHELVED!', 150, color=RED, angle=-9)
        self.st2 = stamp_sprite('TOO STICKY', 120, color=(230, 120, 30), angle=6)
        return wall_plate('#F7C9A0', '#A0522D', 12, (CX, 1000, 1250), counter=(1380, '#6A4A30'))
    def dyn(self, img, t):
        tc = self.tcut()
        # stretchy strings between the gum lump and a lifting hand
        lift = 0.5 + 0.5 * math.sin(t * 2.4 - 1.2)
        hx, hy = CX + 60 + 30 * lift, 820 - 150 * lift
        gx, gy = CX - 40, 1150
        with_shadow(img, self.goo, gx, gy, a=0.4)
        ov = OV(img, CX - 500, 500, CX + 500, 1350)
        for k in range(-3, 4):
            x0 = gx + k * 45
            x1 = hx + k * 14
            w = max(10, int(34 - 3 * lift * abs(k) - 8 * lift))
            mid = ((x0 + x1) / 2 + 30 * math.sin(k + t * 3), (gy + hy) / 2 + 40)
            ov.d.line(ov.pts([(x0, gy - 60), mid, (x1, hy + 10)]), fill=(240, 140, 180, 250), width=w, joint='curve')
        ov.commit()
        draw_hand(img, self.hand, (hx, hy), lift=0.3)
        pop(img, C('BLIBBER-BLUBBER', 86, bg=YEL), CX, 520, t, self.we('BlibberBlubber') - 0.06)
        if t < tc:
            stamp_in(img, self.st2, CX, 1640, t, self.we('sticky') - 0.02)
        else:
            stamp_in(img, self.st, CX, 1640, t, tc)

# ====================================================================== 4: so the accountant mixed his own recipes
class Mixing(Base):
    z0, z1 = 1.22, 1.32
    def make_shakes(self):
        return [(self.we('accountant'), 12, 0.25), (self.we('mixing'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('accountant') - 0.03, 'pop', 0.5), (self.we('mixing') - 0.03, 'rattle', 0.6),
                (self.we('own') - 0.03, 'bloop', 0.5)]
    def plate(self):
        self.bowl = bowl_sprite(700, (250, 200, 210))
        self.hand = get_hand(520, -2.0)
        self.calc = None
        return wall_plate('#BFE7D6', '#2F7A62', 9, (CX, 950, 1250), counter=(1330, '#C8A070'))
    def dyn(self, img, t):
        with_shadow(img, self.bowl, CX, 1180, a=0.45)
        # swirl in the goo
        a = t * 6
        ov = OV(img, CX - 360, 940, CX + 360, 1120)
        for k in range(3):
            r = 90 + k * 70
            ov.d.arc(ov.box(CX - r * 1.6, 1030 - r * 0.35, CX + r * 1.6, 1030 + r * 0.35),
                     math.degrees(a + k) % 360, (math.degrees(a + k) + 130) % 360, fill=(255, 120, 170, 255), width=14)
        ov.commit()
        sx = CX + 160 * math.cos(a)
        sy = 1020 + 30 * math.sin(a)
        ov = OV(img, CX - 400, 500, CX + 450, 1100)
        ov.d.line(ov.pts([(sx, sy), (sx + 110, sy - 420)]), fill=(205, 160, 110, 255), width=30)
        ov.commit()
        draw_hand(img, self.hand, (sx + 120, sy - 330))
        # ingredient drops falling in
        for k in range(3):
            u = ((t * 1.4 + k / 3) % 1)
            paste_center(img, goo_sprite(30, k, [(250, 250, 250), (255, 170, 200), (240, 220, 150)][k], 0.5),
                         CX - 220 + k * 120, 600 + 420 * u * u)
        pop(img, C('THE ACCOUNTANT', 80, bg=WHITE), CX, 520, t, self.we('accountant') - 0.06)
        pop(img, C('HOMEMADE RECIPES', 84, bg=YEL), CX, 1740, t, self.we('own') - 0.06)

# ====================================================================== 5: after a year one batch worked, then hardened overnight
class Overnight(Base):
    z0, z1 = 1.22, 1.32
    def tcut(self):
        return self.we('then') - 0.06
    def make_shakes(self):
        return [(self.we('year,'), 12, 0.25), (self.we('worked'), 12, 0.25), (self.tcut(), 14, 0.3), (self.we('hardened'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('year,') - 0.03, 'tick', 0.5), (self.we('batch') - 0.03, 'squeak', 0.5),
                (self.we('worked') - 0.03, 'ding', 0.6), (self.tcut(), 'swipe', 0.5), (self.we('hardened') - 0.03, 'crack', 0.8)]
    def plate(self):
        self.goo = goo_sprite(270, 5, (255, 150, 190), 0.6)
        self.bub = bubble_sprite(300)
        self.gray = goo_sprite(270, 5, (150, 140, 135), 0.15)
        self.st = stamp_sprite('HARDENED!', 180, color=RED, angle=-8)
        self.night = night_plate()
        return wall_plate('#FFE9A8', '#D08A2E', 4, (CX, 950, 1250), counter=(1320, '#8A6040'))
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            tw = self.we('batch') - 0.1
            k = ease_out(clamp01((t - tw) / 0.9)) if t > tw else 0
            with_shadow(img, self.goo, CX, 1230, a=0.4)
            if k > 0:
                paste_center(img, self.bub, CX + 10, 1160 - 260 * k, scale=max(0.05, 0.35 + 0.65 * k))
            pop(img, C('1 YEAR LATER', 90, bg=WHITE), CX, 520, t, self.we('year,') - 0.06)
            pop(img, C('IT WORKED!', 90, bg=(120, 220, 140)), CX, 1760, t, self.we('worked') - 0.06)
            return
        img.paste(self.night, (0, 0))
        u = t - tc
        tH = self.we('hardened')
        sp = self.goo if t < tH - 0.05 else self.gray
        ov = OV(img, 0, 1320, PW, PH)
        ov.d.rectangle(ov.box(0, 1320, PW, PH), fill=(40, 34, 30, 255))
        ov.commit()
        with_shadow(img, sp, CX, 1180 + 6 * math.sin(u * 30) * (1 if tH - 0.05 < t < tH + 0.3 else 0), a=0.5)
        pop(img, C('OVERNIGHT...', 90, bg=(60, 80, 160), fg=WHITE), CX, 520, t, tc + 0.02)
        stamp_in(img, self.st, CX, 1680, t, tH - 0.02)

# ====================================================================== 6: four months later he cracked it
class Cracked(Base):
    z0, z1 = 1.22, 1.32
    def tcut(self):
        return self.we('finally') - 0.08
    def make_shakes(self):
        return [(self.tcut(), 12, 0.3), (self.we('cracked'), 18, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.4)]
        for k in range(4):
            ev.append((0.05 + k * self.tcut() / 4, 'rustle', 0.5))
        ev += [(self.tcut(), 'riser', 0.4), (self.we('cracked') - 0.03, 'bigpop', 0.7)]
        return ev
    def plate(self):
        self.cals = [calendar_sprite(n, 520) for n in (1, 2, 3, 4)]
        self.bub = bubble_sprite(420)
        self.st = stamp_sprite('CRACKED IT!', 128, color=(40, 150, 70), angle=-8)
        return wall_plate('#D9C9FF', '#5B3FA8', 21, (CX, 1000, 1250))
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            n = min(3, int(t / (tc / 4)))
            v = (t % (tc / 4)) / (tc / 4)
            with_shadow(img, self.cals[n], CX, 1060, a=0.45)
            if n < 3 and v > 0.6:
                k = (v - 0.6) / 0.4
                sp = rot(self.cals[n], 0)
                paste_center(img, rot(self.cals[n], -25 * k, ('calf', n)), CX - 200 * k, 1060 - 500 * k, alpha=1 - k)
            pop(img, C('4 MONTHS', 110, bg=YEL), CX, 1760, t, 0.15)
            return
        u = t - tc
        k = ease_back(clamp01(u / 0.4), 1.6)
        glow(img, CX, 1050, 600, (255, 230, 245), 0.6)
        paste_center(img, self.bub, CX, 1050, scale=max(0.05, k) * (1 + 0.02 * math.sin(t * 8)))
        stamp_in(img, self.st, CX, 1760, t, self.we('cracked') - 0.02)

# ====================================================================== 7: candy store sold all 100 pieces, a penny each, in one day
class Store(Base):
    z0, z1 = 1.22, 1.32
    def tsell(self):
        return self.we('sold') - 0.05
    def tend(self):
        return self.we('in') - 0.05
    def make_shakes(self):
        return [(self.we('100'), 14, 0.3), (self.we('penny'), 12, 0.25), (self.we('one', ), 0, 0.01), (self.tend(), 18, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('candy') - 0.03, 'ding', 0.5), (self.we('100') - 0.03, 'pop', 0.6),
              (self.we('penny') - 0.03, 'cash', 0.7)]
        ts, te = self.tsell(), self.tend()
        for k in range(8):
            ev.append((ts + (te - ts) * (k + 0.5) / 8, 'tick', 0.3))
        ev.append((te, 'cash', 0.9))
        return ev
    def plate(self):
        self.p = wrapped_piece(60)
        self.st = stamp_sprite('SOLD OUT IN 1 DAY!', 86, color=RED, angle=-6)
        img = wall_plate('#FFD9A8', '#C0603A', 2, (CX, 1000, 1250), counter=(1360, '#7A4A2C'))
        d = ImageDraw.Draw(img)
        # striped awning
        for k in range(9):
            x = k * PW / 8
            d.rectangle((x, 300, x + PW / 16, 420), fill=(214, 50, 44, 255))
            d.rectangle((x + PW / 16, 300, x + PW / 8, 420), fill=(250, 245, 235, 255))
        return img
    def dyn(self, img, t):
        ts, te = self.tsell(), self.tend()
        left = 100 if t < ts else max(0, int(round(100 * (1 - clamp01((t - ts) / (te - ts))))))
        # tray of 100 pieces: 10 x 10, pieces vanish in random order
        ov = OV(img, CX - 560, 640, CX + 560, 1340)
        ov.d.rounded_rectangle(ov.box(CX - 480, 660, CX + 480, 1320), radius=30, fill=(250, 240, 220, 255), outline=(150, 100, 60, 255), width=10)
        ov.commit()
        order = np.random.default_rng(7).permutation(100)
        gone = set(order[:100 - left].tolist())
        for k in range(100):
            if k in gone:
                continue
            r, c = divmod(k, 10)
            paste_center(img, self.p, CX - 414 + c * 92, 712 + r * 62)
        # live counter
        txt = f'{left} LEFT'
        sp = cached(('cnt', txt), lambda: text_img(txt, 110, fill=WHITE, stroke=12, stroke_fill=(20, 20, 30), shadow_px=5))
        if ts < t < te:
            paste_center(img, sp, CX, 1520)
        pop(img, C('CANDY STORE', 90, bg=WHITE), CX, 520, t, self.we('candy') - 0.06, out_t=self.we('100') - 0.12)
        pop(img, C('100 PIECES', 90, bg=YEL), CX, 520, t, self.we('100') - 0.06, out_t=self.we('penny') - 0.12)
        pop(img, C('1¢ EACH', 110, bg=WHITE), CX, 520, t, self.we('penny') - 0.06)
        stamp_in(img, self.st, CX, 1740, t, te)

# ====================================================================== 8: Dubble Bubble, taught salesmen to blow bubbles
class Salesmen(Base):
    z0, z1 = 1.22, 1.3
    def tsale(self):
        return self.we('taught') - 0.08
    def make_shakes(self):
        return [(self.we('Dubble'), 14, 0.3), (self.tsale(), 12, 0.25), (self.we('blow'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('Dubble') - 0.03, 'bigpop', 0.6), (self.tsale(), 'pop', 0.5)]
        for k in range(3):
            ev.append((self.we('blow') - 0.05 + k * 0.22, 'squeak', 0.4))
        return ev
    def plate(self):
        lay = Layer()
        for k, x in enumerate((CX - 380, CX, CX + 380)):
            mannequin(lay, x, 1900, 1050)
        img = wall_plate('#FFE07A', '#D2782A', 6, (CX, 1000, 1300), counter=(1820, '#6A4A30'))
        self.with_m = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.bub = bubble_sprite(200)
        self.big = bubble_sprite(420)
        self.st = stamp_sprite('BUBBLE LESSONS', 92, color=RED, angle=-6)
        return img
    def dyn(self, img, t):
        ts = self.tsale()
        if t < ts:
            glow(img, CX, 1030, 620, (255, 250, 220), 0.6)
            paste_center(img, self.big, CX, 1030, scale=1 + 0.03 * math.sin(t * 7))
            pop(img, C('DUBBLE BUBBLE', 110, bg=YEL), CX, 1700, t, self.we('Dubble') - 0.06)
            return
        img.paste(self.with_m, (0, 0))
        tB = self.we('blow')
        for k, x in enumerate((CX - 380, CX, CX + 380)):
            t0 = tB - 0.25 + k * 0.22
            g = ease_out(clamp01((t - t0) / 0.9)) if t > t0 else 0
            if g > 0:
                paste_center(img, self.bub, x, 920 + 60 - 60 * g + 10 * math.sin(t * 6 + k), scale=max(0.05, 0.2 + 0.8 * g))
        pop(img, C('SALESMEN', 96, bg=WHITE), CX, 520, t, ts + 0.02)
        stamp_in(img, self.st, CX, 1600, t, tB - 0.02)

# ====================================================================== 9: the pink? only food coloring in the factory
class OnlyPink(Base):
    z0, z1 = 1.2, 1.3
    def tcut(self):
        return self.we('It') - 0.08
    def make_shakes(self):
        return [(self.we('pink?'), 12, 0.3), (self.we('only'), 16, 0.35), (self.we('factory!'), 12, 0.3)]
    def events(self):
        return [(0.02, 'riser', 0.4), (self.we('pink?') - 0.03, 'bloop', 0.6), (self.tcut(), 'swipe', 0.5),
                (self.we('only') - 0.03, 'buzzer', 0.4), (self.we('coloring') - 0.03, 'ding', 0.7)]
    def plate(self):
        cols = [(214, 50, 44), (40, 110, 210), (60, 170, 90), (255, 120, 170)]
        self.bt = [bottle_sprite(c, full=(k == 3), w=220) for k, c in enumerate(cols)]
        self.bub = bubble_sprite(380)
        self.st = stamp_sprite('ONLY PINK!', 140, color=(220, 60, 130), angle=-8)
        return wall_plate('#E6E6EE', '#5A5A70', 15, (CX, 1000, 1250), counter=(1290, '#9A7050'))
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            paste_center(img, self.bub, CX, 1020, scale=1 + 0.03 * math.sin(t * 6))
            paste_center(img, qmark(240, YEL), CX + 330, 700 + 10 * math.sin(t * 5))
            return
        tO, tC = self.we('only'), self.we('coloring')
        xs = [CX - 450, CX - 150, CX + 150, CX + 450]
        for k, x in enumerate(xs):
            sc = 1.0
            if k == 3 and t > tC - 0.1:
                glow(img, x, 1080, 300, (255, 150, 200), 0.9)
                sc = 1 + 0.15 * (1 - clamp01((t - tC + 0.1) / 0.3))
            with_shadow(img, self.bt[k], x, 1070, a=0.4) if sc == 1.0 else paste_center(img, self.bt[k], x, 1070, scale=sc)
            if k < 3 and t > tO - 0.05 + k * 0.12:
                red_x(img, x, 1100, 120, clamp01((t - tO + 0.05 - k * 0.12) / 0.2))
        pop(img, C('FOOD COLORING', 84, bg=WHITE), CX, 520, t, tc + 0.02)
        stamp_in(img, self.st, CX, 1650, t, tC - 0.02)

# ====================================================================== 10: still pink thanks to an accountant -> loop to hook
class Outro(Hook):
    def tswitch(self):
        return self.we('thanks') - 0.1
    def make_shakes(self):
        return [(self.we('still'), 12, 0.3), (self.tswitch(), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('still') - 0.03, 'bloop', 0.5), (self.tswitch(), 'riser', 0.4)]
    def plate(self):
        img = Hook.plate(self)
        self.hp = img.copy()
        self.wr = [wrapped_piece(150, c) for c in ((255, 130, 175), (255, 160, 195), (240, 110, 160))]
        return wall_plate('#FFD1E4', '#B23A78', 7, (CX, 1000, 1250))
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hp, (0, 0))
            self.hero(img, t - self.dur)
            pop(img, C('THANKS TO AN ACCOUNTANT', 60, bg=YEL), CX, 1760, t, tw + 0.02)
            return
        glow(img, CX, 1050, 640, (255, 235, 245), 0.5)
        for k in range(9):
            r, c = divmod(k, 3)
            paste_center(img, rot(self.wr[k % 3], (k * 37) % 40 - 20, ('wr', k)), CX - 330 + c * 330, 780 + r * 270 + 10 * math.sin(t * 5 + k))
        pop(img, C('STILL PINK TODAY', 90, bg=WHITE), CX, 520, t, self.we('still') - 0.06)
    def cam(self, t):
        tw = self.tswitch()
        if t >= tw:
            # converge on the exact framing of frame 0
            k = clamp01((t - tw) / max(0.1, self.dur - tw))
            dx, dy, dr = self.shake(t)
            return self.z0 + 0.04 * (1 - k), CX + dx, 1070 + dy, dr
        dx, dy, dr = self.shake(t)
        p = 1 - ease_out(t / 0.32)
        return 1.22 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1080 + dy, 2.0 * p + dr

SCENES = [Hook, WhyPink, Books, Sticky, Mixing, Overnight, Cracked, Store, Salesmen, OnlyPink, Outro]
