"""Doritos were born from Disneyland trash: Casa de Fritos, stale tortillas, Arch West (2026-11-23).
Generic stand-ins only: plain triangle chips, unbranded bags, no logos or packaging art."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter as _gf
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish
from mw_scenes import glow, stamp_sprite, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import red_x

RED = (214, 50, 44)
YEL = (255, 210, 60)
GREEN = (60, 170, 90)
WHITE = (255, 255, 255)

class Base(S):
    focus = (CX, 1060)
    z0, z1 = 1.24, 1.34
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        p = 1 - ease_out(t / 0.3)
        z *= 1 + 0.1 * p
        dx, dy, dr = self.shake(t)
        return z, self.focus[0] + dx, self.focus[1] + dy, 2.0 * p * self.rot_dir + dr

# ====================================================================== helpers
_SP = {}
def cached(key, fn):
    if key not in _SP:
        _SP[key] = fn()
    return _SP[key]

def with_shadow(img, sp, cx, cy, blur=14, a=0.45, dx=18, dy=26):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, cx - sp.width / 2 - pad + dx, cy - sp.height / 2 - pad + dy)
    paste_at(img, sp, cx - sp.width / 2, cy - sp.height / 2)

def rot(sp, ang, key=None):
    if key is not None:
        k = (key, int(round(ang)) % 360)
        if k in _SP:
            return _SP[k]
    r = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
    if key is not None:
        _SP[k] = r
    return r

def qmark(size=200, col=WHITE):
    return cached(('q', size, col), lambda: text_img('?', size, fill=col, stroke=12, stroke_fill=(20, 20, 30), shadow_px=5))

def big_text(txt, size, col=WHITE):
    return cached(('bt', txt, size, col), lambda: text_img(txt, size, fill=col, stroke=max(8, size // 12), stroke_fill=(20, 20, 30), shadow_px=6))

def stamp(txt, size, color=RED, angle=-8):
    return cached(('st', txt, size, color, angle), lambda: stamp_sprite(txt, size, color=color, angle=angle))

_PL = {}
def wall_plate(c0, c1, seed=3, spot=(CX, 950, 1300), counter=None):
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

def ss_draw(w, h, ss=3):
    im = Image.new('RGBA', (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

def ss_done(im, w, h):
    return im.resize((int(w), int(h)), Image.LANCZOS)

# ---------------------------------------------------------------- chip (generic triangle tortilla chip)
def chip_sprite(L=400, cheesy=True, seed=0):
    def mk():
        ss = 3
        h = int(L * 0.9)
        pad = int(L * 0.08)
        Wd, Ht = L + 2 * pad, h + 2 * pad
        pts = [((pad + L / 2) * ss, pad * ss), ((pad + L) * ss, (pad + h) * ss), (pad * ss, (pad + h) * ss)]
        mask = Image.new('L', (Wd * ss, Ht * ss), 0)
        md = ImageDraw.Draw(mask)
        cx_, cy_ = sum(p[0] for p in pts) / 3, sum(p[1] for p in pts) / 3
        inner = [(cx_ + (x - cx_) * 0.9, cy_ + (y - cy_) * 0.9) for x, y in pts]
        md.polygon(inner, fill=255)
        md.line(inner + [inner[0]], fill=255, width=int(L * 0.1 * ss), joint='curve')
        for p in inner:
            r = L * 0.05 * ss
            md.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
        mask = mask.resize((Wd, Ht), Image.LANCZOS)
        m = np.asarray(mask, np.float32) / 255
        yy, xx = np.mgrid[0:Ht, 0:Wd].astype(np.float32)
        g = np.clip(1.18 - 0.45 * (xx / Wd) - 0.3 * (yy / Ht), 0.5, 1.2)
        rng = np.random.default_rng(seed)
        n = smooth_noise(Ht, Wd, max(6, L // 18), seed + 7, 3)
        if cheesy:
            base = np.array([252, 142, 42], np.float32) / 255
            spec = np.array([196, 66, 18], np.float32) / 255
        else:
            base = np.array([255, 208, 96], np.float32) / 255
            spec = np.array([196, 140, 60], np.float32) / 255
        col = base[None, None, :] * g[..., None] * (0.88 + 0.24 * n[..., None])
        sp = np.zeros((Ht, Wd), np.float32)
        for k in range(int(L * 0.12)):
            x, y = rng.uniform(0, Wd), rng.uniform(0, Ht)
            r = rng.uniform(1.5, max(2.0, L * 0.016))
            x0, x1 = int(max(0, x - 3 * r)), int(min(Wd, x + 3 * r + 1))
            y0, y1 = int(max(0, y - 3 * r)), int(min(Ht, y + 3 * r + 1))
            if x1 > x0 and y1 > y0:
                sp[y0:y1, x0:x1] += np.exp(-(((xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2) / (r * r)))
        sp = np.clip(sp, 0, 1)
        col = col * (1 - sp[..., None] * 0.6) + spec[None, None, :] * sp[..., None] * 0.6
        edge = np.clip(1 - _gf(m, max(1.0, L * 0.02)), 0, 1) * m
        col = col * (1 - 0.55 * edge[..., None])
        arr = np.concatenate([np.clip(col, 0, 1), m[..., None]], -1)
        return Image.fromarray((arr * 255).astype(np.uint8), 'RGBA')
    return cached(('chip', L, cheesy, seed), mk)

def trash_can(w=520):
    def mk():
        h = int(w * 1.15)
        ss = 2
        im, d = ss_draw(w + 40, h + 40, ss)
        Sx = lambda *v: tuple(x * ss for x in v)
        top, bot = 20 + h * 0.12, 20 + h
        d.polygon([Sx(20, top), Sx(w + 20, top), Sx(w - 30, bot), Sx(70, bot)], fill=(150, 160, 172, 255), outline=(70, 76, 86, 255))
        for k in range(1, 7):
            u = k / 7
            xt, xb = 20 + w * u, 70 + (w - 100) * u
            d.line([Sx(xt, top + 10), Sx(xb, bot - 6)], fill=(110, 118, 130, 255), width=10 * ss)
            d.line([Sx(xt + 9, top + 10), Sx(xb + 7, bot - 6)], fill=(196, 204, 214, 255), width=4 * ss)
        d.ellipse(Sx(0, 20 + h * 0.02, w + 40, 20 + h * 0.2), fill=(176, 184, 196, 255), outline=(70, 76, 86, 255), width=6 * ss)
        d.ellipse(Sx(30, 20 + h * 0.05, w + 10, 20 + h * 0.17), fill=(60, 52, 46, 255))
        return ss_done(im, w + 40, h + 40)
    return cached(('can', w), mk)

def tortilla_sprite(R=220, seed=0, squash=0.55):
    def mk():
        w, h = 2 * R + 20, int(2 * R * squash) + 40
        im, d = ss_draw(w, h, 2)
        d.ellipse((20, 50, (2 * R + 10) * 2, (2 * R * squash + 30) * 2), fill=(206, 166, 92, 255))
        d.ellipse((20, 20, (2 * R + 10) * 2, (2 * R * squash + 10) * 2), fill=(244, 222, 150, 255), outline=(206, 170, 96, 255), width=6)
        rng = np.random.default_rng(seed)
        for k in range(16):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 0.8) * R
            x, y = (R + 10 + math.cos(a) * r) * 2, (R * squash + 10 + math.sin(a) * r * squash) * 2
            s = rng.uniform(6, 16) * 2
            d.ellipse((x - s, y - s * squash, x + s, y + s * squash), fill=(176, 120, 60, 200))
        return ss_done(im, w, h)
    return cached(('tort', R, seed, squash), mk)

def bag_sprite(w=300, col=(214, 50, 44), seed=0):
    """Generic unbranded snack bag: crimped ends, a plain chip and the word CHIPS."""
    def mk():
        h = int(w * 1.35)
        ss = 2
        im, d = ss_draw(w + 20, h + 20, ss)
        dk = tuple(int(c * 0.78) for c in col) + (255,)
        d.rounded_rectangle((10 * ss, 30 * ss, (w + 10) * ss, (h - 10) * ss), radius=30 * ss, fill=col + (255,), outline=tuple(int(c * 0.55) for c in col) + (255,), width=5 * ss)
        d.rectangle((10 * ss, 10 * ss, (w + 10) * ss, 44 * ss), fill=dk)
        d.rectangle((10 * ss, (h - 34) * ss, (w + 10) * ss, (h + 4) * ss), fill=dk)
        for x in np.arange(14, w + 10, 14):
            d.line([(x * ss, 12 * ss), (x * ss, 42 * ss)], fill=tuple(int(c * 0.6) for c in col) + (255,), width=2 * ss)
            d.line([(x * ss, (h - 32) * ss), (x * ss, (h + 2) * ss)], fill=tuple(int(c * 0.6) for c in col) + (255,), width=2 * ss)
        d.rounded_rectangle(((w * 0.1 + 10) * ss, (h * 0.12 + 20) * ss, (w * 0.24) * ss, (h * 0.85) * ss), radius=16 * ss, fill=(255, 255, 255, 70))
        out = ss_done(im, w + 20, h + 20)
        c = chip_sprite(int(w * 0.52), True, seed)
        out.alpha_composite(c, (int(w / 2 + 10 - c.width / 2), int(h * 0.46)))
        t = text_img('CHIPS', int(w * 0.2), fill=WHITE, stroke=5, stroke_fill=(30, 20, 20))
        out.alpha_composite(t, (int(w / 2 + 10 - t.width / 2), int(h * 0.18)))
        return out
    return cached(('bag', w, col, seed), mk)

def cheese_sprite(w=320):
    def mk():
        h = int(w * 0.7)
        im, d = ss_draw(w + 20, h + 20, 2)
        pts = [(10, h * 0.45), (w + 10, h * 0.2), (w + 10, h + 10), (10, h + 10)]
        d.polygon([(x * 2, y * 2) for x, y in pts], fill=(255, 200, 50, 255), outline=(190, 130, 20, 255), width=6)
        d.polygon([(20, h * 0.9), ((w + 10) * 2, h * 0.4), ((w + 10) * 2, h * 0.72), (20, h * 1.16)], fill=(255, 226, 110, 255))
        for (x, y, r) in ((0.3, 0.75, 0.08), (0.62, 0.62, 0.06), (0.8, 0.85, 0.07), (0.48, 0.9, 0.04)):
            d.ellipse(((10 + w * x - w * r) * 2, (h * y - w * r) * 2, (10 + w * x + w * r) * 2, (h * y + w * r) * 2), fill=(222, 160, 30, 255))
        return ss_done(im, w + 20, h + 20)
    return cached(('cheese', w), mk)

def pan_sprite(w=560):
    def mk():
        h = int(w * 0.5)
        im, d = ss_draw(int(w * 1.6), h, 2)
        d.rounded_rectangle((w * 0.95 * 2, h * 0.38 * 2, w * 1.58 * 2, h * 0.52 * 2), radius=20, fill=(40, 34, 32, 255))
        d.ellipse((0, h * 0.1 * 2, w * 2, h * 0.95 * 2), fill=(50, 46, 46, 255))
        d.ellipse((w * 0.06 * 2, h * 0.16 * 2, w * 0.94 * 2, h * 0.84 * 2), fill=(214, 168, 60, 255))
        return ss_done(im, int(w * 1.6), h)
    return cached(('pan', w), mk)

def restaurant_sprite(w=900):
    """Generic adobe-style restaurant front with a striped awning (no real building likeness)."""
    def mk():
        h = int(w * 0.85)
        im, d = ss_draw(w, h, 2)
        S2 = lambda *v: tuple(x * 2 for x in v)
        d.rectangle(S2(0, h * 0.28, w, h), fill=(236, 186, 130, 255), outline=(150, 96, 60, 255), width=8)
        d.rectangle(S2(w * 0.05, h * 0.04, w * 0.95, h * 0.28), fill=(214, 120, 60, 255), outline=(140, 70, 30, 255), width=8)
        for k in range(10):
            x0 = k * w / 10
            c = (214, 50, 44, 255) if k % 2 == 0 else (255, 244, 220, 255)
            d.rectangle(S2(x0, h * 0.36, x0 + w / 10, h * 0.46), fill=c)
            d.pieslice(S2(x0, h * 0.41, x0 + w / 10, h * 0.51), 0, 180, fill=c)
        d.rounded_rectangle(S2(w * 0.38, h * 0.6, w * 0.62, h), radius=80, fill=(120, 70, 40, 255), outline=(80, 44, 24, 255), width=8)
        for x in (0.1, 0.72):
            d.rounded_rectangle(S2(w * x, h * 0.62, w * (x + 0.18), h * 0.86), radius=40, fill=(255, 226, 150, 255), outline=(150, 96, 60, 255), width=8)
        return ss_done(im, w, h)
    return cached(('rest', w), mk)

def knife_sprite(L=560):
    def mk():
        h = int(L * 0.2)
        im = Image.new('RGBA', (L, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, h * 0.3, L * 0.36, h * 0.8), radius=int(h * 0.2), fill=(120, 70, 40, 255), outline=(70, 40, 20, 255), width=4)
        d.polygon([(L * 0.36, h * 0.25), (L * 0.98, h * 0.42), (L * 0.98, h * 0.55), (L * 0.36, h * 0.85)], fill=(205, 212, 222, 255), outline=(120, 126, 140, 255))
        d.line([(L * 0.38, h * 0.36), (L * 0.95, h * 0.46)], fill=(245, 248, 255, 255), width=5)
        return im
    return cached(('knife', L), mk)

def heart_sprite(R=70, col=(236, 60, 90)):
    def mk():
        s = 3
        im, d = ss_draw(R * 2 + 8, R * 2 + 8, s)
        d.ellipse((4 * s, 8 * s, (R + 8) * s, (R + 8) * s), fill=col + (255,))
        d.ellipse((R * s, 8 * s, (2 * R + 4) * s, (R + 8) * s), fill=col + (255,))
        d.polygon([(6 * s, (R * 0.62) * s), ((2 * R + 2) * s, (R * 0.62) * s), ((R + 4) * s, (2 * R + 4) * s)], fill=col + (255,))
        return ss_done(im, R * 2 + 8, R * 2 + 8)
    return cached(('heart', R, col), mk)

def sparkle(img, x, y, r, a=1.0):
    if r < 2:
        return
    ov = OV(img, x - r - 4, y - r - 4, x + r + 4, y + r + 4)
    pts = []
    for k in range(8):
        ang = k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.25
        pts.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr))
    ov.d.polygon(ov.pts(pts), fill=(255, 236, 140, int(255 * a)))
    ov.commit()

def bill_sprite(w=300):
    def mk():
        h = int(w * 0.45)
        im = Image.new('RGBA', (w + 10, h + 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((5, 5, w + 5, h + 5), radius=10, fill=(120, 190, 110, 255), outline=(50, 110, 50, 255), width=6)
        d.ellipse((w / 2 - h * 0.3 + 5, h * 0.2 + 5, w / 2 + h * 0.3 + 5, h * 0.8 + 5), fill=(170, 220, 150, 255), outline=(50, 110, 50, 255), width=4)
        t = text_img('$', int(h * 0.42), fill=(40, 100, 40))
        im.alpha_composite(t, (int(w / 2 + 5 - t.width / 2), int(h / 2 + 5 - t.height / 2)))
        return im
    return cached(('bill', w), mk)

def arrow_right(img, x0, x1, y, k, col=YEL):
    if k <= 0:
        return
    x = x0 + (x1 - x0) * k
    ov = OV(img, x0 - 20, y - 110, x + 130, y + 110)
    ov.d.line(ov.pts([(x0, y), (x, y)]), fill=col + (255,), width=44)
    ov.d.polygon(ov.pts([(x - 10, y - 90), (x - 10, y + 90), (x + 110, y)]), fill=col + (255,), outline=(30, 30, 30, 255))
    ov.commit()

def man_plate(c0, c1, seed, xs, yf, Hh, counter=None):
    lay = Layer()
    for x in xs:
        mannequin(lay, x, yf, Hh)
    img = wall_plate(c0, c1, seed, (CX, 1000, 1250), counter)
    return to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')

# ====================================================================== 0: hook - giant chip bursting out of a trash can
CAN_Y = 1720
class Hook(Base):
    z0, z1 = 1.28, 1.34
    focus = (CX, 1110)
    def make_shakes(self):
        return [(0.0, 12, 0.25), (self.we('born'), 12, 0.3), (self.we('Disneyland'), 12, 0.3), (self.ttr(), 24, 0.45)]
    def ttr(self):
        return self.we('trash!') - 0.05
    def events(self):
        return [(0.0, 'bigpop', 0.6), (self.we('born') - 0.03, 'pop', 0.5), (self.we('Disneyland') - 0.03, 'chime', 0.5),
                (self.ttr(), 'thud', 0.8), (self.ttr() + 0.02, 'crack', 0.4)]
    def plate(self):
        self.can = trash_can(640)
        self.chip = chip_sprite(860, True, 1)
        self.minis = [chip_sprite(170, True, k + 3) for k in range(4)]
        self.st = stamp('TRASH!', 150)
        return wall_plate('#FFD7A8', '#B8502A', 23, (CX, 1050, 1250))
    def hero(self, img, t):
        for k in range(8):
            ph = (t * 0.9 + k / 8) % 1.0
            vx = (k - 3.5) * 230
            x = CX + (k - 3.5) * 60 + vx * ph
            y = CAN_Y - 300 - 1500 * ph + 1900 * ph * ph
            if y < CAN_Y - 230:
                paste_center(img, rot(self.minis[k % 4], (k * 47 + t * 300 * (1 if k % 2 else -1)) % 360, ('mc', k % 4)), x, y)
        with_shadow(img, self.can, CX, CAN_Y + 150, a=0.45, blur=20)
        ang = 8 * math.sin(t * 3.2)
        bob = 26 * math.sin(t * 4.0)
        with_shadow(img, rot(self.chip, ang, 'hc'), CX, 1240 + bob, a=0.35, blur=22, dx=24, dy=40)
    def dyn(self, img, t):
        self.hero(img, t)
        pop(img, C('DISNEYLAND', 96, bg=YEL), CX, 1640, t, self.we('Disneyland') - 0.06, out_t=self.ttr() - 0.05)
        stamp_in(img, self.st, CX, 1790, t, self.ttr())

# ====================================================================== 1: first ones didn't even have cheese
class NoCheese(Base):
    z0, z1 = 1.26, 1.32
    def make_shakes(self):
        return [(self.we('first'), 10, 0.25), (self.we('cheese.') - 0.05, 20, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('first') - 0.03, 'pop', 0.45), (self.we('even') - 0.03, 'bloop', 0.6),
                (self.we('cheese.') - 0.05, 'buzzer', 0.5)]
    def plate(self):
        self.chip = chip_sprite(800, False, 2)
        self.cheese = cheese_sprite(380)
        self.st = stamp('NO CHEESE?!', 120, angle=-7)
        return wall_plate('#FFF1B8', '#C98A2A', 19, (CX, 1000, 1250))
    def dyn(self, img, t):
        with_shadow(img, rot(self.chip, -6 + 5 * math.sin(t * 3), 'pc'), CX, 1130 + 14 * math.sin(t * 4), a=0.35, blur=20)
        if t > 0.62:
            pop(img, C('THE FIRST ONES', 92, bg=WHITE), CX, 560, t, 0.62)
        tc = self.we('even') - 0.08
        pop(img, self.cheese, CX + 310, 1560, t, tc)
        red_x(img, CX + 310, 1560, 170, clamp01((t - self.we('cheese.') + 0.1) / 0.3))
        stamp_in(img, self.st, CX - 80, 1800, t, self.we('cheese.') - 0.05)

# ====================================================================== 2: how did trash become a billion-dollar chip?
class Billion(Base):
    def make_shakes(self):
        return [(self.we('trash'), 12, 0.3), (self.we('billion-dollar') - 0.05, 22, 0.4)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('trash') - 0.03, 'thud', 0.55), (self.we('turn') - 0.03, 'riser', 0.4),
              (self.we('billion-dollar') - 0.05, 'cash', 0.6)]
        for k in range(3):
            ev.append((self.we('chip?') - 0.25 + k * 0.1, 'pop', 0.35))
        return ev
    def plate(self):
        self.can = trash_can(400)
        self.chip = chip_sprite(440, True, 4)
        self.bill = bill_sprite(280)
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300))
    def dyn(self, img, t):
        tb = self.we('billion-dollar') - 0.08
        with_shadow(img, self.can, CX - 280, 1100, a=0.4)
        arrow_right(img, CX - 60, CX + 40, 1100, ease_out(clamp01((t - self.we('turn') + 0.05) / 0.3)))
        if t > tb:
            glow(img, CX + 300, 1100, 360, (255, 230, 120), 0.5 * clamp01((t - tb) / 0.3))
            for k in range(12):
                t0 = tb + k * 0.07
                if t < t0:
                    continue
                u = t - t0
                x = CX + 300 + ((k * 137) % 440) - 220
                y = 640 + 800 * u
                if y < 1500:
                    paste_center(img, rot(self.bill, (k * 40 + u * 200) % 360, ('bl', k)), x, y, scale=0.7)
            pop(img, self.chip, CX + 300, 1100, t, tb)
            pop(img, C('$1,000,000,000', 96, bg=(120, 200, 110)), CX, 1720, t, tb)
        pop(img, C('TRASH', 92, bg=WHITE), CX - 280, 800, t, self.we('trash') - 0.06)
        for k in range(3):
            pop(img, qmark(180 + 40 * (k % 2), YEL if k % 2 else WHITE), CX - 360 + k * 360, 540 + 12 * math.sin(t * 6 + k), t, self.we('chip?') - 0.25 + k * 0.1)

# ====================================================================== 3: as the story goes, Disneyland had Casa de Fritos
class Casa(Base):
    z0, z1 = 1.22, 1.32
    def make_shakes(self):
        return [(self.we('Disneyland'), 12, 0.3), (self.we('Mexican'), 12, 0.3), (self.we('Casa'), 20, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('story') - 0.03, 'chime', 0.45), (self.we('Disneyland') - 0.03, 'party', 0.5),
                (self.we('Mexican') - 0.03, 'thud', 0.6), (self.we('restaurant') - 0.03, 'pop', 0.45), (self.we('Casa') - 0.03, 'boom', 0.55)]
    def plate(self):
        self.rest = restaurant_sprite(900)
        self.bal = [heart_sprite(60, c) for c in ((236, 60, 90), (60, 150, 236), (255, 200, 40))]
        self.st = stamp('CASA DE FRITOS', 92, angle=-6)
        return wall_plate('#BFE6FF', '#2A6FB0', 31, (CX, 1000, 1250), counter=(1500, '#8FBF60'))
    def dyn(self, img, t):
        td, tm, tc = self.we('Disneyland') - 0.08, self.we('Mexican') - 0.08, self.we('Casa') - 0.05
        if t < td:
            for k in range(3):
                pop(img, qmark(170, YEL if k % 2 else WHITE), CX - 320 + k * 320, 900 + 15 * math.sin(t * 5 + k), t, 0.25 + k * 0.15)
            pop(img, C('AS THE STORY GOES...', 86, bg=WHITE), CX, 1100, t, 0.0)
            return
        for k in range(6):
            u = (t - td) * 0.3 + k / 6
            x = CX - 480 + k * 190 + 20 * math.sin(t * 2 + k)
            y = 1500 - (u % 1.0) * 1100
            if t > td + k * 0.06:
                ov = OV(img, x - 4, y + 50, x + 4, y + 200)
                ov.d.line(ov.pts([(x, y + 55), (x, y + 200)]), fill=(255, 255, 255, 200), width=3)
                ov.commit()
                paste_center(img, self.bal[k % 3], x, y, scale=0.9)
        if t >= tm:
            k = ease_back(clamp01((t - tm) / 0.35), 1.8)
            with_shadow(img, self.rest, CX, 1160 + 500 * (1 - k), a=0.35, blur=18)
        pop(img, C('DISNEYLAND', 110, bg=YEL), CX, 560, t, td)
        if t > tm:
            pop(img, C('MEXICAN RESTAURANT', 70, bg=WHITE), CX, 1700, t, tm, out_t=tc - 0.1)
        stamp_in(img, self.st, CX, 1700, t, tc)

# ====================================================================== 4: cooks kept throwing old tortillas in the trash
class Toss(Base):
    def make_shakes(self):
        return [(self.we('throwing'), 10, 0.25), (self.we('trash.') - 0.05, 20, 0.4)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('cooks') - 0.03, 'pop', 0.45)]
        for k in range(4):
            ev.append((self.we('throwing') + 0.25 + k * 0.32, 'thud', 0.35))
        ev.append((self.we('trash.') - 0.06, 'buzzer', 0.45))
        return ev
    def plate(self):
        self.can = trash_can(520)
        self.torts = [tortilla_sprite(150, k, 0.6) for k in range(4)]
        self.hand = get_hand(560, -0.9)
        self.st = stamp('TOSSED!', 140)
        return wall_plate('#FFE7B0', '#C77A30', 8, (CX, 1000, 1300), counter=(1420, '#8A6040'))
    def dyn(self, img, t):
        cx_can = CX + 260
        with_shadow(img, self.can, cx_can, 1250, a=0.4)
        for k in range(5):
            paste_center(img, self.torts[k % 4], CX - 300, 1450 - k * 26)
        th = self.we('throwing') - 0.1
        for k in range(6):
            t0 = th + k * 0.32
            if t < t0:
                continue
            u = (t - t0) / 0.45
            if u > 1:
                continue
            x = CX - 300 + (cx_can - CX + 300) * u
            y = 1330 - 560 * math.sin(math.pi * u) - 300 * u
            paste_center(img, rot(self.torts[k % 4], (u * 400) % 360, ('tt', k % 4)), x, y)
        hk = abs(math.sin(t * 7))
        draw_hand(img, self.hand, (CX - 330 + 40 * hk, 1280 - 60 * hk))
        pop(img, C('THE COOKS', 92, bg=WHITE), CX, 560, t, 0.05, out_t=self.we('old') - 0.1)
        if t > self.we('old') - 0.1:
            pop(img, C('OLD TORTILLAS', 92, bg=YEL), CX, 560, t, self.we('old') - 0.08)
        stamp_in(img, self.st, CX, 1720, t, self.we('trash.') - 0.06)

# ====================================================================== 5: salesman: stop, cut them up and fry them!
class Salesman(Base):
    def ts(self):
        return self.we('stop,') - 0.06
    def tc(self):
        return self.we('cut') - 0.06
    def tf(self):
        return self.we('fry') - 0.06
    def make_shakes(self):
        return [(self.we('salesman'), 10, 0.25), (self.ts(), 22, 0.4), (self.tc(), 12, 0.3), (self.tf(), 16, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('salesman') - 0.03, 'pop', 0.5), (self.we('supplier') - 0.03, 'pop', 0.4),
                (self.ts(), 'buzzer', 0.5), (self.tc(), 'scratch', 0.6), (self.we('up') - 0.03, 'scratch', 0.5), (self.tf(), 'sizzle', 0.7)]
    def plate(self):
        self.p_man = man_plate('#C8F0D8', '#2F8A5A', 13, [CX], 2050, 1250)
        self.tort = tortilla_sprite(300, 2, 0.6)
        self.knife = knife_sprite(560)
        self.pan = pan_sprite(620)
        self.wedges = [chip_sprite(150, False, k + 10) for k in range(4)]
        self.st = stamp('STOP!', 170)
        self.st2 = stamp('FRY THEM!', 130, angle=-6)
        return wall_plate('#FFE7B0', '#C77A30', 8, (CX, 1000, 1300), counter=(1350, '#8A6040'))
    def dyn(self, img, t):
        ts, tc, tf = self.ts(), self.tc(), self.tf()
        if t < tc:
            img.paste(self.p_man, (0, 0))
            pop(img, C('A SALESMAN', 96, bg=WHITE), CX, 560, t, self.we('salesman') - 0.08)
            pop(img, C('FROM THE TORTILLA SUPPLIER', 58, bg=YEL), CX, 1660, t, self.we('supplier') - 0.1)
            stamp_in(img, self.st, CX, 1000, t, ts)
            return
        if t < tf:
            paste_center(img, self.tort, CX, 1150, scale=1.3)
            ov = OV(img, CX - 420, 900, CX + 420, 1400)
            cuts = clamp01((t - tc) / 0.5)
            for k in range(3):
                if cuts * 3 > k:
                    a = math.radians(30 + 60 * k)
                    ov.d.line(ov.pts([(CX - 370 * math.cos(a), 1160 - 200 * math.sin(a)), (CX + 370 * math.cos(a), 1160 + 200 * math.sin(a))]), fill=(150, 100, 50, 255), width=10)
            ov.commit()
            kk = abs(math.sin((t - tc) * 9))
            paste_center(img, rot(self.knife, -30 + 15 * kk, 'skn'), CX + 120, 950 + 120 * kk, scale=1.2)
            pop(img, C('CUT THEM UP', 96, bg=WHITE), CX, 560, t, tc)
            return
        with_shadow(img, self.pan, CX + 120, 1250, a=0.4)
        for k in range(4):
            x = CX - 120 + (k - 1.5) * 150
            y = 1240 + 14 * math.sin(t * 14 + k)
            pop(img, rot(self.wedges[k], k * 70 + 20, ('wd', k)), x, y, t, tf + k * 0.06)
        for k in range(10):
            ph = (t * 1.6 + k * 0.13) % 1
            sparkle(img, CX - 330 + (k * 73) % 460, 1200 - 200 * ph, 14 * (1 - ph) + 4, 0.8)
        stamp_in(img, self.st2, CX, 600, t, tf)

# ====================================================================== 6: guests loved them, chips went on the menu
class Menu(Base):
    def tm(self):
        return self.we('chips') - 0.08
    def make_shakes(self):
        return [(self.we('loved'), 14, 0.3), (self.tm(), 12, 0.3), (self.we('menu.') - 0.05, 18, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('loved') - 0.03, 'party', 0.55)]
        for k in range(3):
            ev.append((self.we('loved') + 0.05 + k * 0.1, 'pop', 0.3))
        ev += [(self.tm(), 'thud', 0.6), (self.we('menu.') - 0.08, 'ding', 0.7)]
        return ev
    def plate(self):
        self.p_g = man_plate('#FFE2C4', '#C2643C', 23, [CX - 380, CX, CX + 380], 2150, 1000)
        self.heart = heart_sprite(80)
        self.basket = [chip_sprite(200, False, k + 20) for k in range(6)]
        return wall_plate('#3A3A44', '#141418', 41, (CX, 1000, 1100))
    def dyn(self, img, t):
        tm = self.tm()
        if t < tm:
            img.paste(self.p_g, (0, 0))
            for k in range(3):
                x = CX - 380 + k * 380
                pop(img, self.heart, x, 1020 - 30 * math.sin(t * 5 + k), t, self.we('loved') - 0.05 + k * 0.1)
            pop(img, C('GUESTS LOVED THEM', 84, bg=WHITE), CX, 560, t, 0.05)
            return
        ov = OV(img, CX - 470, 700, CX + 470, 1500)
        ov.d.rounded_rectangle(ov.box(CX - 450, 720, CX + 450, 1480), radius=24, fill=(34, 48, 40, 255), outline=(140, 96, 56, 255), width=26)
        ov.commit()
        pop(img, big_text('MENU', 120, WHITE), CX, 840, t, tm)
        for k, (txt, d0) in enumerate((('TACOS', 0.08), ('TAMALES', 0.16))):
            pop(img, text_img(txt, 72, fill=(230, 230, 220)), CX, 990 + k * 110, t, tm + d0)
        pop(img, C('NEW: TORTILLA CHIPS!', 64, bg=YEL), CX, 1250, t, self.we('menu.') - 0.1)
        for k in range(6):
            paste_center(img, rot(self.basket[k], k * 55, ('bk', k)), CX - 300 + k * 120, 1390 + 10 * (k % 2))

# ====================================================================== 7: Arch West noticed; 1966 nationwide
class ArchWest(Base):
    def t66(self):
        return self.we('1966,') - 0.08
    def tn(self):
        return self.we('nationwide.') - 0.08
    def make_shakes(self):
        return [(self.we('boss'), 10, 0.25), (self.we('Arch'), 12, 0.3), (self.we('noticed,'), 14, 0.3), (self.t66(), 22, 0.4), (self.tn(), 18, 0.4)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('Frito-Lay') - 0.03, 'pop', 0.5), (self.we('Arch') - 0.03, 'chime', 0.55),
              (self.we('noticed,') - 0.03, 'ding', 0.7), (self.t66(), 'boom', 0.6), (self.we('sold') - 0.03, 'cash', 0.5)]
        for k in range(5):
            ev.append((self.we('sold') + 0.05 + k * 0.1, 'pop', 0.3))
        ev.append((self.tn(), 'thud', 0.5))
        return ev
    def plate(self):
        lay = Layer()
        mannequin(lay, CX, 2150, 1500)
        img = wall_plate('#5A4A8A', '#1C1838', 9, (CX, 1000, 900))
        self.p_vp = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.excl = big_text('!', 260, YEL)
        cols = [(214, 50, 44), (40, 110, 210), (60, 160, 80), (130, 60, 170), (240, 140, 30)]
        self.bags = [bag_sprite(220, cols[k % 5], k) for k in range(5)]
        self.st = stamp('NATIONWIDE!', 120, angle=-7)
        return wall_plate('#BFE6FF', '#2A6FB0', 31, (CX, 1000, 1250))
    def dyn(self, img, t):
        t66 = self.t66()
        if t < t66:
            img.paste(self.p_vp, (0, 0))
            glow(img, CX, 900, 600, (255, 240, 200), 0.35)
            pop(img, C('FRITO-LAY BOSS', 96, bg=WHITE), CX, 560, t, 0.05, out_t=self.we('Arch') - 0.1)
            if t > self.we('Arch') - 0.1:
                pop(img, C('ARCH WEST', 110, bg=YEL), CX, 560, t, self.we('Arch') - 0.08)
            pop(img, self.excl, CX + 300, 820 + 10 * math.sin(t * 9), t, self.we('noticed,') - 0.08)
            pop(img, C('NOTICED!', 90, bg=WHITE), CX, 1700, t, self.we('noticed,') - 0.06)
            return
        ts = self.we('sold') - 0.1
        n = 0 if t < ts else min(20, int((t - ts) * 14) + 1)
        for k in range(n):
            col, row = k % 5, k // 5
            x = CX - 440 + col * 220
            y = 760 + row * 240
            paste_center(img, self.bags[(k * 3) % 5], x, y + 10 * math.sin(t * 6 + k), scale=0.72)
        if n == 0:
            stamp_in(img, big_text('1966', 300, YEL), CX, 1100, t, t66)
        else:
            pop(img, C('1966', 120, bg=YEL), CX, 560, t, ts)
        stamp_in(img, self.st, CX, 1720, t, self.tn())

# ====================================================================== 8: plain toasted corn until nacho cheese in 1972
class Nacho(Base):
    def tu(self):
        return self.we('until') - 0.06
    def make_shakes(self):
        return [(self.we('plain'), 12, 0.3), (self.tu(), 10, 0.25), (self.we('nacho'), 16, 0.35), (self.we('1972.') - 0.06, 22, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('plain') - 0.03, 'pop', 0.45), (self.we('toasted') - 0.03, 'sizzle', 0.4),
                (self.tu(), 'riser', 0.45), (self.we('nacho') - 0.03, 'bigpop', 0.6), (self.we('1972.') - 0.06, 'boom', 0.55)]
    def plate(self):
        self.plain = chip_sprite(760, False, 2)
        self.cheesy = chip_sprite(760, True, 2)
        self.cheese = cheese_sprite(300)
        self.st = stamp('1972', 150)
        return wall_plate('#FFF1B8', '#C98A2A', 19, (CX, 1000, 1250))
    def dyn(self, img, t):
        tu, tn = self.tu(), self.we('nacho') - 0.08
        ang = -5 + 6 * math.sin(t * 2.5)
        cx, cy = CX, 1130 + 12 * math.sin(t * 4)
        with_shadow(img, rot(self.plain, ang, 'np'), cx, cy, a=0.35, blur=20)
        if t < tn:
            pop(img, C('JUST TOASTED CORN', 84, bg=WHITE), CX, 560, t, self.we('plain') - 0.08)
            if t > tu:
                for k in range(30):
                    ph = ((t - tu) * 1.8 + k / 30) % 1
                    x = CX - 360 + (k * 97) % 720
                    y = 680 + ph * 600
                    ov = OV(img, x - 12, y - 12, x + 12, y + 12)
                    ov.d.ellipse(ov.box(x - 9, y - 9, x + 9, y + 9), fill=(240, 120, 30, 230))
                    ov.commit()
            return
        u = clamp01((t - tn) / 0.35)
        sp = rot(self.cheesy, ang, 'nc')
        if u < 1:
            sp = sp.copy()
            sp.putalpha(sp.getchannel('A').point(lambda v: int(v * u)))
        paste_center(img, sp, cx, cy)
        glow(img, cx, cy, 420, (255, 200, 80), 0.35 * u)
        pop(img, self.cheese, CX + 330, 1580, t, tn + 0.05)
        pop(img, C('NACHO CHEESE', 104, bg=(240, 120, 30), fg=WHITE), CX, 560, t, tn)
        stamp_in(img, self.st, CX - 150, 1700, t, self.we('1972.') - 0.06)

# ====================================================================== 9: the name means little golden things
class Golden(Base):
    def make_shakes(self):
        return [(self.we('name'), 10, 0.25), (self.we('little'), 14, 0.3), (self.we('Spanish.') - 0.1, 12, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('name') - 0.03, 'pop', 0.5), (self.we('little') - 0.03, 'chime', 0.6)]
        for k in range(4):
            ev.append((self.we('golden') + k * 0.12, 'ding', 0.25))
        return ev
    def plate(self):
        self.chips = [chip_sprite(300, False, k + 30) for k in range(5)]
        return wall_plate('#5A4A8A', '#1C1838', 9, (CX, 1000, 900))
    def dyn(self, img, t):
        tl = self.we('little') - 0.08
        glow(img, CX, 1100, 500, (255, 220, 120), 0.45)
        for k in range(5):
            a = t * 0.8 + k * 2 * math.pi / 5
            x, y = CX + math.cos(a) * 340, 1100 + math.sin(a) * 300
            pop(img, rot(self.chips[k], (k * 72 + t * 40) % 360, ('gc', k)), x, y, t, 0.05 + k * 0.06)
        for k in range(8):
            ph = (t * 1.3 + k / 8) % 1
            sparkle(img, CX - 420 + (k * 131) % 840, 760 + (k * 211) % 700, 30 * math.sin(math.pi * ph) + 4)
        pop(img, C('THE NAME MEANS:', 84, bg=WHITE), CX, 560, t, 0.05, out_t=tl - 0.1)
        if t > tl - 0.1:
            pop(img, C('"LITTLE GOLDEN THINGS"', 72, bg=YEL), CX, 560, t, tl)
        pop(img, C('IN SPANISH', 86, bg=WHITE), CX, 1720, t, self.we('Spanish.') - 0.1)

# ====================================================================== 10: Frito-Lay can't confirm it... loop back to the hook
class Outro(Hook):
    def tswitch(self):
        return self.we('your') - 0.08
    def tb(self):
        return self.we('but') - 0.06
    def make_shakes(self):
        return [(self.we("can't"), 14, 0.3), (self.tb(), 10, 0.25), (self.tswitch(), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we("can't") - 0.03, 'buzzer', 0.5), (self.we('Disneyland') - 0.03, 'pop', 0.4),
                (self.tb(), 'riser', 0.45), (self.tswitch(), 'bigpop', 0.5)]
    def plate(self):
        Hook.plate(self)
        self.hp = wall_plate('#FFD7A8', '#B8502A', 23, (CX, 1050, 1250))
        self.cst = stamp("CAN'T CONFIRM", 104, angle=-7)
        self.bag = bag_sprite(440, (214, 50, 44), 5)
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300))
    def dyn(self, img, t):
        tw, tb = self.tswitch(), self.tb()
        if t >= tw:
            img.paste(self.hp, (0, 0))
            Hook.hero(self, img, t - tw)
            return
        if t < tb:
            with_shadow(img, rot(self.bag, 4 * math.sin(t * 3), 'ob'), CX, 1100, a=0.4)
            pop(img, C('FRITO-LAY', 104, bg=WHITE), CX, 560, t, 0.03)
            for k in range(2):
                pop(img, qmark(200, YEL), CX - 380 + 760 * k, 1000 + 15 * math.sin(t * 5 + k), t, self.we('Disneyland') - 0.08 + k * 0.1)
            stamp_in(img, self.cst, CX, 1700, t, self.we("can't") - 0.05)
            return
        with_shadow(img, self.can, CX, 1300, a=0.4)
        for k in range(3):
            pop(img, qmark(170, WHITE if k % 2 else YEL), CX - 320 + k * 320, 820, t, tb + 0.1 + k * 0.1)
        pop(img, C("BUT IF IT'S TRUE...", 92, bg=YEL), CX, 560, t, tb)
    def cam(self, t):
        tw = self.tswitch()
        dx, dy, dr = self.shake(t)
        if t >= tw:
            return Hook.z0, Hook.focus[0] + dx, Hook.focus[1] + dy, dr
        p = 1 - ease_out(t / 0.32)
        return 1.24 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1060 + dy, 2.0 * p + dr

SCENES = [Hook, NoCheese, Billion, Casa, Toss, Salesman, Menu, ArchWest, Nacho, Golden, Outro]
