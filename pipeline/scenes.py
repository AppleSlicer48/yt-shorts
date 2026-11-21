"""Tissues weren't invented for your nose: Kleenex began as a cold cream remover (2026-11-21)."""
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

def box_sprite(w=760):
    """Generic tissue box (3/4 view), opening on top, no branding."""
    def mk():
        h = int(w * 0.5); dep = int(w * 0.28); sk = int(w * 0.16)
        W_, H_ = w + sk + 20, h + dep + 20
        lay = Layer(W_, H_)
        x0, y0 = 10, 10 + dep
        top = [(x0 + sk, 10), (x0 + sk + w, 10), (x0 + w, y0), (x0, y0)]
        fill_poly(lay, top, '#7EC3F0')
        fill_poly(lay, [(x0 + w, y0), (x0 + sk + w, 10), (x0 + sk + w, 10 + h), (x0 + w, y0 + h)], '#2F6FB0')
        fill_poly(lay, [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], '#4A93D6')
        sp = Image.fromarray((np.concatenate([np.clip(np.where(lay.a[..., None] > 1e-4, lay.p / np.maximum(lay.a[..., None], 1e-4), 0), 0, 1), lay.a[..., None]], -1) * 255 + 0.5).astype(np.uint8), 'RGBA')
        d = ImageDraw.Draw(sp, 'RGBA')
        for k in range(4):
            yy = y0 + h * (0.22 + 0.2 * k)
            pts = [(x0 + 8 + i * 8, yy + 14 * math.sin(i * 0.35 + k)) for i in range(int((w - 16) / 8) + 1)]
            d.line(pts, fill=(255, 255, 255, 110), width=10)
        cx, cy = x0 + sk / 2 + w / 2, 10 + dep / 2
        d.ellipse((cx - w * 0.3, cy - dep * 0.22, cx + w * 0.3, cy + dep * 0.22), fill=(25, 50, 90, 255))
        d.line([(x0, y0), (x0 + w, y0)], fill=(255, 255, 255, 120), width=4)
        return sp, (cx, cy)
    return cached(('box', w), mk)

def draw_tissue_up(img, cx, cy, hgt, t, w=300):
    """Puffy tissue poking up out of the box opening, fluttering."""
    if hgt < 5:
        return
    ov = OV(img, cx - w - 40, cy - hgt - 80, cx + w + 40, cy + 40)
    pts = []
    n = 24
    for i in range(n + 1):
        u = i / n
        x = cx - w / 2 + u * w
        y = cy - hgt * (0.35 + 0.65 * math.sin(math.pi * u)) + 16 * math.sin(t * 7 + u * 6)
        pts.append((x + 20 * math.sin(t * 5 + u * 3) * u, y))
    pts += [(cx + w * 0.32, cy + 10), (cx - w * 0.32, cy + 10)]
    ov.d.polygon(ov.pts(pts), fill=(250, 250, 252, 255), outline=(180, 186, 200, 255))
    for k in range(3):
        u = 0.3 + 0.2 * k
        x = cx - w / 2 + u * w
        ov.d.line(ov.pts([(x, cy), (x + 10 * math.sin(t * 6 + k), cy - hgt * 0.75)]), fill=(205, 210, 222, 255), width=7)
    ov.commit()

def sheet_sprite(w=520, seed=0, angle=0):
    """Crinkly crepe tissue sheet."""
    def mk():
        im = Image.new('RGBA', (w + 40, w + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        rng = np.random.default_rng(seed)
        pts = []
        for k in range(40):
            a = 2 * math.pi * k / 40
            r = w * 0.47 * (1 + 0.04 * rng.standard_normal())
            sq = 1 / max(abs(math.cos(a)), abs(math.sin(a))) ** 0.8
            pts.append((w / 2 + 20 + math.cos(a) * r * min(sq, 1.35) * 0.78, w / 2 + 20 + math.sin(a) * r * min(sq, 1.35) * 0.78))
        d.polygon(pts, fill=(250, 250, 248, 255), outline=(170, 176, 190, 255))
        for k in range(12):
            y = w * 0.16 + k * (w * 0.68) / 12
            xs = np.linspace(w * 0.18, w * 0.86, 30)
            d.line([(x, y + 5 * math.sin(x * 0.12 + k)) for x in xs], fill=(205, 208, 218, 255), width=4)
        return im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return cached(('sheet', w, seed, angle), mk)

def gasmask_sprite(w=620):
    """Generic old-style gas mask with a round filter canister."""
    def mk():
        h = int(w * 1.25)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((w * 0.08, h * 0.02, w * 0.92, h * 0.72), fill=(88, 98, 72, 255), outline=(40, 46, 32, 255), width=10)
        d.ellipse((w * 0.14, h * 0.06, w * 0.6, h * 0.42), fill=(108, 120, 88, 255))
        for ex in (0.32, 0.68):
            d.ellipse((w * (ex - 0.15), h * 0.18, w * (ex + 0.15), h * 0.42), fill=(60, 60, 60, 255))
            d.ellipse((w * (ex - 0.12), h * 0.2, w * (ex + 0.12), h * 0.4), fill=(150, 200, 215, 255))
            d.ellipse((w * (ex - 0.09), h * 0.22, w * (ex - 0.02), h * 0.28), fill=(240, 250, 255, 220))
        d.rectangle((w * 0.42, h * 0.55, w * 0.58, h * 0.7), fill=(60, 66, 50, 255))
        d.ellipse((w * 0.26, h * 0.64, w * 0.74, h * 0.99), fill=(140, 140, 132, 255), outline=(60, 60, 56, 255), width=10)
        for r in (0.16, 0.1):
            d.ellipse((w * (0.5 - r), h * (0.815 - r * 0.8), w * (0.5 + r), h * (0.815 + r * 0.8)), outline=(90, 90, 86, 255), width=8)
        return im
    return cached(('mask', w), mk)

def jar_sprite(w=340):
    def mk():
        h = int(w * 0.9)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((w * 0.04, h * 0.28, w * 0.96, h * 0.98), radius=int(w * 0.12), fill=(240, 160, 190, 255), outline=(150, 70, 100, 255), width=7)
        d.rectangle((w * 0.04, h * 0.5, w * 0.96, h * 0.62), fill=(255, 255, 255, 230))
        d.ellipse((w * 0.04, h * 0.12, w * 0.96, h * 0.44), fill=(252, 250, 244, 255), outline=(200, 190, 180, 255), width=6)
        d.ellipse((w * 0.3, h * 0.08, w * 0.7, h * 0.3), fill=(255, 255, 255, 255))
        d.ellipse((w * 0.42, h * 0.02, w * 0.56, h * 0.16), fill=(255, 255, 255, 255))
        d.line([(w * 0.18, h * 0.66), (w * 0.18, h * 0.9)], fill=(255, 220, 235, 200), width=12)
        return im
    return cached(('jar', w), mk)

def head_sprite(Hh=600):
    """Wooden mannequin head + neck + shoulders, facing right. Returns (sprite, nose-tip offset)."""
    def mk():
        lay = Layer(int(Hh * 1.6), int(Hh * 1.6))
        col = hexc(ARM_LIGHT); j = col * 0.86
        kw = dict(grain=grain_map(), spec=0.28, shin=22)
        cx, cy = Hh * 0.7, Hh * 0.55
        ellipsoid(lay, (cx - Hh * 0.05, cy + Hh * 0.62), Hh * 0.5, Hh * 0.2, 0, col, **kw)
        capsule(lay, (cx, cy + Hh * 0.2), (cx - Hh * 0.02, cy + Hh * 0.5), Hh * 0.11, Hh * 0.12, j, **kw)
        ellipsoid(lay, (cx, cy), Hh * 0.27, Hh * 0.32, 0.15, col, **kw)
        ellipsoid(lay, (cx + Hh * 0.16, cy + Hh * 0.12), Hh * 0.13, Hh * 0.15, 0.4, col, **kw)
        ellipsoid(lay, (cx + Hh * 0.27, cy + Hh * 0.02), Hh * 0.06, Hh * 0.045, 0.5, col, **kw)  # nose
        ellipsoid(lay, (cx - Hh * 0.04, cy + Hh * 0.02), Hh * 0.05, Hh * 0.08, 0, j, **kw)  # ear
        sp, x0, y0 = layer_sprite(lay, 2)
        return sp, (cx + Hh * 0.31 - x0, cy + Hh * 0.02 - y0)
    return cached(('head', Hh), mk)

def envelope_sprite(w=240, seed=0):
    def mk():
        h = int(w * 0.64)
        im = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        tint = [(250, 246, 232), (244, 240, 250), (255, 250, 240)][seed % 3]
        d.rectangle((4, 4, w, h), fill=tint + (255,), outline=(120, 110, 100, 255), width=4)
        d.line([(4, 4), (w / 2, h * 0.58), (w, 4)], fill=(150, 140, 125, 255), width=5)
        d.rectangle((w * 0.76, h * 0.12, w * 0.92, h * 0.38), fill=(214, 70, 60, 255))
        for k in range(3):
            d.line([(w * 0.3, h * (0.66 + 0.1 * k)), (w * 0.7, h * (0.66 + 0.1 * k))], fill=(90, 90, 110, 255), width=4)
        return im
    return cached(('env', w, seed), mk)

def hanky_sprite(w=460):
    """Cloth handkerchief with a checked border."""
    def mk():
        im = Image.new('RGBA', (w, w), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w, w), radius=20, fill=(235, 240, 250, 255))
        b = w * 0.12
        for k in range(10):
            col = (60, 110, 200, 255) if k % 2 == 0 else (235, 240, 250, 255)
            x = k * w / 10
            d.rectangle((x, 0, x + w / 10, b), fill=col)
            d.rectangle((x, w - b, x + w / 10, w), fill=col)
            d.rectangle((0, x, b, x + w / 10), fill=col)
            d.rectangle((w - b, x, w, x + w / 10), fill=col)
        d.rectangle((b * 1.6, b * 1.6, w - b * 1.6, w - b * 1.6), outline=(60, 110, 200, 255), width=6)
        return im
    return cached(('hanky', w), mk)

def bin_sprite(w=380):
    def mk():
        h = int(w * 1.15)
        im = Image.new('RGBA', (w + 40, h + 60), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(20, 60), (w + 20, 60), (w * 0.88 + 20, h + 40), (w * 0.12 + 20, h + 40)], fill=(111, 123, 136, 255))
        d.polygon([(w * 0.62, 60), (w + 20, 60), (w * 0.88 + 20, h + 40), (w * 0.58, h + 40)], fill=(86, 97, 109, 255))
        d.ellipse((0, 20, w + 40, 110), fill=(40, 44, 50, 255), outline=(150, 160, 170, 255), width=8)
        for k in range(4):
            x = (w + 40) * (0.25 + 0.17 * k)
            d.line([(x, 130), (x - 6 + k * 4, h + 10)], fill=(130, 140, 150, 255), width=6)
        return im
    return cached(('bin', w), mk)

def factory_sprite(w=760):
    def mk():
        h = int(w * 0.8)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((w * 0.68, h * 0.05, w * 0.8, h * 0.5), fill=(150, 80, 60, 255))
        d.polygon([(0, h * 0.45), (w * 0.33, h * 0.25), (w * 0.33, h * 0.45), (w * 0.66, h * 0.25), (w * 0.66, h * 0.45), (w, h * 0.25), (w, h), (0, h)], fill=(190, 100, 70, 255))
        d.rectangle((0, h * 0.45, w, h), fill=(180, 92, 64, 255))
        for k in range(4):
            d.rectangle((w * (0.08 + 0.23 * k), h * 0.58, w * (0.2 + 0.23 * k), h * 0.76), fill=(255, 225, 140, 255))
        d.rectangle((w * 0.42, h * 0.8, w * 0.58, h), fill=(90, 50, 40, 255))
        return im
    return cached(('fac', w), mk)

def bulb_sprite(R=120):
    def mk():
        im = Image.new('RGBA', (R * 3, R * 3), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = R * 1.5
        for k in range(8):
            a = k * math.pi / 4
            d.line([(c + math.cos(a) * R * 1.15, c - R * 0.2 + math.sin(a) * R * 1.15), (c + math.cos(a) * R * 1.45, c - R * 0.2 + math.sin(a) * R * 1.45)], fill=(255, 230, 80, 255), width=12)
        d.ellipse((c - R * 0.8, c - R, c + R * 0.8, c + R * 0.6), fill=(255, 225, 70, 255), outline=(40, 40, 40, 255), width=8)
        d.rectangle((c - R * 0.35, c + R * 0.55, c + R * 0.35, c + R * 0.95), fill=(150, 150, 160, 255), outline=(40, 40, 40, 255), width=6)
        return im
    return cached(('bulb', R), mk)

def star_sprite(R=60, col=(255, 230, 90)):
    def mk():
        im = Image.new('RGBA', (R * 2 + 4, R * 2 + 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            r = R if k % 2 == 0 else R * 0.42
            pts.append((R + 2 + math.cos(a) * r, R + 2 + math.sin(a) * r))
        d.polygon(pts, fill=col + (255,), outline=(60, 40, 10, 255))
        return im
    return cached(('star', R, col), mk)

# ====================================================================== plates
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

def hook_plate():
    return wall_plate('#BFE6FF', '#2A6FB0', 31, (CX, 1000, 1250), counter=(1420, '#B08055'))

# ====================================================================== 0: hook - giant tissue box, hand pulling a tissue
class Hook(Base):
    z0, z1 = 1.3, 1.36
    focus = (CX, 1080)
    BX, BY = CX + 10, 1230
    def make_shakes(self):
        return [(0.0, 10, 0.25), (self.we('nose!') - 0.02, 18, 0.35)]
    def events(self):
        return [(0.0, 'swipe', 0.5), (0.04, 'rustle', 0.6), (self.we('invented') - 0.03, 'pop', 0.45),
                (self.we('nose!') - 0.03, 'buzzer', 0.5)]
    def plate(self):
        self.box, self.op = box_sprite(760)
        self.hand = get_hand(520, -1.75)
        self.st = stamp_sprite('NOT FOR NOSES!', 104, color=RED, angle=-7)
        return hook_plate()
    def hero(self, img, t):
        bx0, by0 = self.BX - self.box.width / 2, self.BY - self.box.height / 2
        with_shadow(img, self.box, self.BX, self.BY, a=0.4, blur=18)
        ox, oy = bx0 + self.op[0], by0 + self.op[1]
        pull = 300 + 120 * (0.5 + 0.5 * math.sin(t * 3.2 - 1.4))
        draw_tissue_up(img, ox, oy, pull, t, 340)
        draw_hand(img, self.hand, (ox + 40, oy - pull + 30))
    def dyn(self, img, t):
        self.hero(img, t)
        tN = self.we('nose!')
        stamp_in(img, self.st, CX, 1680, t, tN - 0.02)
        if t > tN - 0.05:
            red_x(img, CX + 330, 820, 90, clamp01((t - tN + 0.05) / 0.25))

# ====================================================================== 1: company didn't figure it out, customers did
class Customers(Base):
    def tcut(self):
        return self.we('Its') - 0.06
    def make_shakes(self):
        return [(self.we("didn't"), 12, 0.3), (self.tcut(), 12, 0.3), (self.we('customers'), 16, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we("didn't") - 0.03, 'buzzer', 0.4), (self.tcut(), 'swipe', 0.4),
                (self.we('customers') - 0.03, 'ding', 0.7)]
    def plate(self):
        self.fac = factory_sprite(900)
        self.bulb = bulb_sprite(130)
        lay = Layer()
        for x in (CX - 360, CX, CX + 360):
            mannequin(lay, x, 1960, 1120)
        img = wall_plate('#FFE7B0', '#C77A30', 8, (CX, 1000, 1300), counter=(1880, '#6A4A30'))
        self.crowd = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300), counter=(1420, '#4A4060'))
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            with_shadow(img, self.fac, CX, 1080, a=0.4)
            for k in range(3):
                pop(img, qmark(150 + 40 * (k % 2), YEL if k % 2 else WHITE), CX - 280 + k * 280, 700 + 10 * math.sin(t * 6 + k), t, max(0.95, self.we('figure') - 0.06) + k * 0.1)
            pop(img, C('THE COMPANY: CLUELESS', 70, bg=WHITE), CX, 1680, t, self.we("didn't") - 0.06)
            return
        img.paste(self.crowd, (0, 0))
        for k, x in enumerate((CX - 360, CX, CX + 360)):
            pop(img, self.bulb, x, 760 + 8 * math.sin(t * 7 + k), t, self.we('customers') - 0.06 + k * 0.1)
        pop(img, C('ITS CUSTOMERS DID!', 90, bg=YEL), CX, 1700, t, self.we('customers') - 0.06)

# ====================================================================== 2: WWI gas mask filter
class GasMask(Base):
    z0, z1 = 1.24, 1.4
    def make_shakes(self):
        return [(self.we('War'), 12, 0.3), (self.we('crinkly'), 12, 0.3), (self.we('filter'), 16, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('World') - 0.03, 'boom', 0.55), (self.we('crinkly') - 0.03, 'rustle', 0.7),
                (self.we('filter') - 0.03, 'thud', 0.7), (self.we('masks!') - 0.03, 'pop', 0.4)]
    def plate(self):
        self.mask = gasmask_sprite(640)
        self.sheet = sheet_sprite(420, 1, 8)
        self.st = stamp_sprite('GAS MASK FILTER', 96, color=RED, angle=-6)
        return wall_plate('#C9C9A6', '#4A4A34', 11, (CX, 1000, 1250))
    def dyn(self, img, t):
        tC, tF = self.we('crinkly'), self.we('filter')
        mx, my = CX - 120, 1020
        with_shadow(img, self.mask, mx, my, a=0.45)
        if t > tC - 0.1:
            k = ease_back(clamp01((t - tC + 0.1) / 0.5), 1.4)
            sx = mx + 40 + 380 * k
            sy = my + 280 - 160 * k + 10 * math.sin(t * 4)
            paste_center(img, self.sheet, sx, sy, scale=max(0.05, 0.3 + 0.7 * k))
            pop(img, C('CRINKLY PAPER', 64, bg=WHITE), min(sx, CX + 220), sy - 250, t, tC + 0.3)
        pop(img, C('WORLD WAR I', 110, bg=YEL), CX, 520, t, self.we('World') - 0.06)
        stamp_in(img, self.st, CX, 1700, t, tF - 0.02)

# ====================================================================== 3: 1924 Kleenex, a cold cream remover
class ColdCream(Base):
    def t1(self):
        return self.we('1924') - 0.08
    def t2(self):
        return self.we('cold') - 0.08
    def t3(self):
        return self.we('wiping') - 0.1
    def make_shakes(self):
        return [(self.t1(), 14, 0.3), (self.we('Kleenex'), 12, 0.3), (self.t2(), 12, 0.3), (self.t3(), 12, 0.3), (self.we('makeup.'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.t1(), 'thud', 0.7), (self.we('Kleenex') - 0.03, 'pop', 0.6),
                (self.t2(), 'bloop', 0.6), (self.t3(), 'rustle', 0.6), (self.we('makeup.') - 0.03, 'ding', 0.6)]
    def plate(self):
        self.mask = gasmask_sprite(560)
        self.box, self.op = box_sprite(700)
        self.jar = jar_sprite(420)
        self.head, self.nose = head_sprite(760)
        self.hand = get_hand(480, -2.6)
        self.sheet = sheet_sprite(260, 2, -20)
        self.mr = stamp_sprite('MAKEUP REMOVER', 92, color=(200, 50, 120), angle=-6)
        self.p1 = wall_plate('#C9C9A6', '#4A4A34', 11, (CX, 1000, 1250))
        self.p2 = hook_plate()
        self.p3 = wall_plate('#FFD6E4', '#B04A78', 7, (CX, 1000, 1250))
        return self.p1
    def dyn(self, img, t):
        t1, t2, t3 = self.t1(), self.t2(), self.t3()
        if t < t1:
            k = ease_out(clamp01(t / max(0.1, t1)))
            paste_center(img, rot(self.mask, 25 * k, 'mrot'), CX - 60, 1020 + 500 * k * k, alpha=1 - 0.6 * k)
            pop(img, C('AFTER THE WAR...', 96, bg=WHITE), CX, 520, t, 0.1)
            return
        if t < t3:
            img.paste(self.p2 if t < t2 else self.p3, (0, 0))
            k = ease_back(clamp01((t - t1) / 0.35), 1.6)
            if t < t2:
                bx, sc = CX, max(0.05, k)
                paste_center(img, self.box, bx, 1120, scale=sc)
                bx0, by0 = bx - self.box.width / 2, 1120 - self.box.height / 2
                if k > 0.95:
                    draw_tissue_up(img, bx0 + self.op[0], by0 + self.op[1], 260, t, 300)
                pop(img, C('1924', 130, bg=YEL), CX, 520, t, t1 + 0.02)
                pop(img, C('KLEENEX', 110, bg=WHITE), CX, 1700, t, self.we('Kleenex') - 0.06)
            else:
                paste_center(img, self.box, CX - 230, 1120, scale=0.72)
                pop(img, self.jar, CX + 300, 1060, t, t2)
                pop(img, C('COLD CREAM REMOVER', 78, bg=WHITE), CX, 560, t, t2 + 0.02)
            return
        img.paste(self.p3, (0, 0))
        hx, hy = CX - 140, 1080
        with_shadow(img, self.head, hx, hy, a=0.35)
        u = t - t3
        nx = hx - self.head.width / 2 + self.nose[0]
        ny = hy - self.head.height / 2 + self.nose[1]
        cx = nx - 90 + 50 * math.sin(u * 9)
        cy = ny + 90 + 25 * math.cos(u * 9)
        paste_center(img, self.sheet, cx, cy)
        draw_hand(img, self.hand, (cx + 40, cy + 40))
        pop(img, C('WIPE OFF MAKEUP', 84, bg=WHITE), CX, 520, t, t3 + 0.02)
        stamp_in(img, self.mr, CX, 1700, t, self.we('makeup.') - 0.02)

# ====================================================================== 4: ads said movie stars used it
class Stars(Base):
    z0, z1 = 1.22, 1.32
    def make_shakes(self):
        return [(self.we('famous'), 12, 0.3), (self.we('stars'), 16, 0.35), (self.we('pretty'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Ads') - 0.03, 'pop', 0.5), (self.we('movie') - 0.03, 'riser', 0.4),
                (self.we('stars') - 0.03, 'chime', 0.7), (self.we('pretty') - 0.03, 'ding', 0.5)]
    def plate(self):
        self.head, _ = head_sprite(760)
        self.box, _ = box_sprite(440)
        self.st = star_sprite(70)
        self.st2 = stamp_sprite('PRETTY SKIN', 110, color=(200, 50, 120), angle=-6)
        return wall_plate('#3A2E5A', '#0C0A18', 9, (CX, 1000, 900))
    def dyn(self, img, t):
        glow(img, CX, 1000, 650, (255, 240, 200), 0.55)
        with_shadow(img, self.head, CX - 80, 1060, a=0.3)
        paste_center(img, rot(self.box, 8, 'sbox'), CX + 300, 1240 + 8 * math.sin(t * 4))
        tS = self.we('stars')
        for k in range(6):
            a = t * 0.9 + k * math.pi / 3
            pop(img, self.st, CX - 40 + math.cos(a) * 470, 1000 + math.sin(a) * 400, t, tS - 0.08 + k * 0.06)
        pop(img, C('"AS USED BY MOVIE STARS"', 64, bg=YEL), CX, 520, t, self.we('Ads') - 0.06)
        stamp_in(img, self.st2, CX, 1700, t, self.we('pretty') - 0.02)

# ====================================================================== 5: the name: Kleen = clean, ex from Kotex
class Name(Base):
    def make_shakes(self):
        return [(self.we('Kleen'), 14, 0.3), (self.we('clean,'), 10, 0.25), (self.we('ex'), 14, 0.3), (self.we('Kotex.'), 16, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('name?') - 0.03, 'pop', 0.4), (self.we('Kleen') - 0.03, 'thud', 0.7),
                (self.we('clean,') - 0.03, 'ding', 0.5), (self.we('ex') - 0.03, 'bloop', 0.6), (self.we('Kotex.') - 0.03, 'boom', 0.5)]
    def plate(self):
        self.kl = big_text('KLEEN', 175, WHITE)
        self.ex = big_text('EX', 175, YEL)
        self.box, _ = box_sprite(720)
        return wall_plate('#BFE6FF', '#2A5FA0', 17, (CX, 1000, 1250))
    def dyn(self, img, t):
        tK, tE, tX = self.we('Kleen'), self.we('ex'), self.we('Kotex.')
        wk, we_ = self.kl.width, self.ex.width
        tot = wk + we_ - 110
        kx = CX - tot / 2 + wk / 2
        exf = CX - tot / 2 + wk - 110 + we_ / 2
        if t < tK - 0.05:
            paste_center(img, self.box, CX, 1100)
            pop(img, qmark(260, YEL), CX + 330, 760 + 12 * math.sin(t * 6), t, 0.0)
            pop(img, C('THE NAME?', 110, bg=WHITE), CX, 520, t, self.we('name?') - 0.06)
            return
        pop(img, self.kl, kx, 1000, t, tK - 0.05)
        pop(img, C('= CLEAN', 100, bg=WHITE), kx, 720, t, self.we('clean,') - 0.06)
        if t > tE - 0.06:
            k = ease_out(clamp01((t - tE + 0.06) / 0.4))
            sx, sy = CX + 300, 1640
            paste_center(img, self.ex, sx + (exf - sx) * k, sy + (1000 - sy) * k, scale=0.6 + 0.4 * k)
            pop(img, C('"EX" FROM KOTEX', 92, bg=YEL), CX, 1700, t, tX - 0.06)

# ====================================================================== 6: customers kept writing in
class Letters(Base):
    def make_shakes(self):
        return [(self.we('writing'), 12, 0.3), (self.we('different'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5)]
        tw = self.we('writing') - 0.1
        for k in range(5):
            ev.append((tw + k * 0.3, 'rustle' if k % 2 else 'pop', 0.4))
        ev.append((self.we('different') - 0.03, 'riser', 0.5))
        return ev
    def plate(self):
        self.envs = [rot(envelope_sprite(320, k), (k * 29) % 40 - 20) for k in range(8)]
        self.box, _ = box_sprite(600)
        return wall_plate('#FFE7B0', '#C77A30', 8, (CX, 1000, 1300), counter=(1420, '#8A5A38'))
    def dyn(self, img, t):
        with_shadow(img, self.box, CX, 1200, a=0.4)
        tw = self.we('writing') - 0.1
        for k in range(8):
            t0 = tw + k * 0.22
            if t < t0:
                continue
            u = ease_out(clamp01((t - t0) / 0.45))
            ex, ey = CX - 420 + (k % 4) * 280, 760 + (k // 4) * 240
            sx, sy = ex + (1 if k % 2 else -1) * 700, ey - 400
            paste_center(img, self.envs[k], sx + (ex - sx) * u, sy + (ey - sy) * u)
        pop(img, C('CUSTOMER LETTERS', 86, bg=WHITE), CX, 1720, t, self.we('customers') - 0.06)
        pop(img, C('A DIFFERENT USE?!', 90, bg=YEL), CX, 480, t, self.we('different') - 0.06)

# ====================================================================== 7: by 1930 the letters swamped the company
class Swamped(Base):
    z0, z1 = 1.22, 1.3
    def make_shakes(self):
        return [(self.we('1930'), 14, 0.3), (self.we('swamped'), 22, 0.45)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('1930') - 0.03, 'thud', 0.7)]
        ts = self.we('letters') - 0.05
        for k in range(6):
            ev.append((ts + k * 0.12, 'rustle', 0.4))
        ev.append((self.we('swamped') - 0.03, 'boom', 0.7))
        return ev
    def plate(self):
        self.fac = factory_sprite(860)
        self.envs = [rot(envelope_sprite(230, k), (k * 37) % 70 - 35) for k in range(12)]
        self.st = stamp_sprite('SWAMPED!', 170, color=RED, angle=-8)
        rng = np.random.default_rng(9)
        self.pos = [(rng.uniform(CX - 480, CX + 480), rng.uniform(760, 1500)) for _ in range(60)]
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300), counter=(1420, '#4A4060'))
    def dyn(self, img, t):
        with_shadow(img, self.fac, CX, 1100, a=0.4)
        ts = self.we('letters') - 0.1
        n = 0 if t < ts else min(60, int((t - ts) * 45) + 1)
        for k in range(n):
            x, y = self.pos[k]
            u = ease_out(clamp01((t - ts - k / 45) / 0.25))
            paste_center(img, self.envs[k % 12], x, y - 500 * (1 - u))
        pop(img, C('1930', 130, bg=YEL), CX, 520, t, self.we('1930') - 0.06)
        stamp_in(img, self.st, CX, 1720, t, self.we('swamped') - 0.02)

# ====================================================================== 8: people were blowing their noses
class Noses(Base):
    z0, z1 = 1.28, 1.38
    def make_shakes(self):
        return [(self.we('blow') - 0.02, 24, 0.5)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('blow') - 0.03, 'squeak', 0.7), (self.we('blow') + 0.12, 'bigpop', 0.5)]
    def plate(self):
        self.head, self.nose = head_sprite(800)
        self.hand = get_hand(480, -2.9)
        self.sheet = sheet_sprite(320, 3, 10)
        self.st = stamp_sprite('BLOWING NOSES!', 104, color=RED, angle=-7)
        self.honk = big_text('HONK!', 130, YEL)
        return wall_plate('#C8F0D8', '#2F8A5A', 13, (CX, 1000, 1250))
    def dyn(self, img, t):
        hx, hy = CX - 180, 1080
        tb = self.we('blow')
        sh = 8 * math.sin(t * 40) if t > tb else 0
        with_shadow(img, self.head, hx + sh, hy, a=0.35)
        nx = hx - self.head.width / 2 + self.nose[0] + sh
        ny = hy - self.head.height / 2 + self.nose[1]
        paste_center(img, self.sheet, nx + 30, ny + 10, scale=1 + (0.08 * math.sin(t * 30) if t > tb else 0))
        draw_hand(img, self.hand, (nx + 80, ny + 70))
        pop(img, self.honk, CX + 170, 700, t, tb - 0.05)
        stamp_in(img, self.st, CX, 1700, t, tb - 0.02)

# ====================================================================== 9: handkerchief you can throw away -> loop
class Outro(Hook):
    def tswitch(self):
        return self.we('even') - 0.1
    def make_shakes(self):
        return [(self.we('handkerchief'), 12, 0.3), (self.we('throw'), 16, 0.35), (self.tswitch(), 10, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('handkerchief') - 0.03, 'pop', 0.5), (self.we('throw') - 0.03, 'swipe', 0.6),
                (self.we('away...') - 0.03, 'thud', 0.6), (self.tswitch(), 'riser', 0.4)]
    def plate(self):
        Hook.plate(self)
        self.hp = hook_plate()
        self.hk = hanky_sprite(480)
        self.bin = bin_sprite(420)
        return wall_plate('#FFF1B8', '#C98A2A', 19, (CX, 1000, 1250), counter=(1420, '#8A6040'))
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hp, (0, 0))
            self.hero(img, t - self.dur)
            return
        tT = self.we('throw') - 0.05
        with_shadow(img, self.bin, CX + 260, 1230, a=0.4)
        if t < tT:
            paste_center(img, rot(self.hk, 8 * math.sin(t * 3), 'hk'), CX - 200, 1000)
        else:
            u = clamp01((t - tT) / 0.5)
            x = CX - 200 + 460 * u
            y = 1000 - 380 * math.sin(math.pi * u) + 120 * u
            if u < 1:
                paste_center(img, rot(self.hk, -200 * u, 'hk2'), x, y, scale=1 - 0.6 * u)
        pop(img, C('THE HANDKERCHIEF', 90, bg=WHITE), CX, 520, t, self.we('handkerchief') - 0.06)
        pop(img, C('YOU CAN THROW AWAY', 90, bg=YEL), CX, 1720, t, self.we('throw') - 0.06)
    def cam(self, t):
        tw = self.tswitch()
        dx, dy, dr = self.shake(t)
        if t >= tw:
            k = clamp01((t - tw) / max(0.1, self.dur - tw))
            return self.z0 + 0.04 * (1 - k), self.focus[0] + dx, self.focus[1] + dy, dr
        p = 1 - ease_out(t / 0.32)
        return 1.24 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1060 + dy, 2.0 * p + dr

SCENES = [Hook, Customers, GasMask, ColdCream, Stars, Name, Letters, Swamped, Noses, Outro]
