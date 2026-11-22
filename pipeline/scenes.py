"""One wife's kitchen accidents gave us the Band-Aid: Earle Dickson, 1920 (2026-11-22)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish, table_bg, ruler_tex
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


TAN = (228, 172, 122)
TAN_D = (186, 128, 84)

def bandage_sprite(L=600, h=None, wrap=False):
    """Generic adhesive bandage strip (horizontal), gauze pad in the middle, no branding."""
    h = h or int(L * 0.27)
    def mk():
        im = Image.new('RGBA', (L + 8, h + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((4, 4, L + 4, h + 4), radius=h // 2, fill=TAN + (255,), outline=TAN_D + (255,), width=max(3, h // 40))
        # highlight band
        d.rounded_rectangle((h * 0.3, h * 0.16, L - h * 0.3, h * 0.3), radius=int(h * 0.07), fill=(244, 200, 156, 255))
        pw = L * 0.34
        px0, px1 = L / 2 + 4 - pw / 2, L / 2 + 4 + pw / 2
        d.rounded_rectangle((px0, h * 0.18, px1, h * 0.86), radius=int(h * 0.08), fill=(252, 246, 236, 255), outline=(222, 210, 192, 255), width=max(2, h // 60))
        step = max(8, int(h * 0.09))
        for x in np.arange(px0 + step, px1 - 2, step):
            d.line([(x, h * 0.22), (x, h * 0.82)], fill=(236, 226, 210, 255), width=2)
        for y in np.arange(h * 0.22 + step, h * 0.82, step):
            d.line([(px0 + 4, y), (px1 - 4, y)], fill=(236, 226, 210, 255), width=2)
        r = max(2, h // 45)
        for side in (0, 1):
            xa = (h * 0.45, px0 - h * 0.15) if side == 0 else (px1 + h * 0.15, L - h * 0.45)
            for x in np.arange(xa[0], xa[1], h * 0.17):
                for y in (h * 0.38, h * 0.62):
                    d.ellipse((x - r, y - r, x + r, y + r), fill=TAN_D + (255,))
        return im
    return cached(('band', L, h), mk)

FINGER = dict(p0=(150, 2050), p1=(820, 860), r=175)

def finger_sprite():
    """Giant wooden mannequin index finger, diagonal from bottom-left."""
    def mk():
        lay = Layer()
        col = hexc(ARM_LIGHT); j = col * 0.86
        kw = dict(grain=grain_map(), spec=0.3, shin=22)
        p0, p1, r = np.array(FINGER['p0'], float), np.array(FINGER['p1'], float), FINGER['r']
        mid = p0 + (p1 - p0) * 0.5
        capsule(lay, p0, mid, r * 1.05, r * 0.98, col, **kw)
        sphere(lay, mid, r * 1.02, j, **kw)
        capsule(lay, mid, p1, r * 0.96, r * 0.9, col, **kw)
        v = (p1 - p0) / np.linalg.norm(p1 - p0)
        nail = p1 - v * r * 0.55
        sp, x0, y0 = layer_sprite(lay, 2)
        return sp, x0, y0
    return cached('finger', mk)

def finger_pt(u):
    p0, p1 = np.array(FINGER['p0'], float), np.array(FINGER['p1'], float)
    return p0 + (p1 - p0) * u

FING_ANG = math.degrees(math.atan2(-(FINGER['p1'][1] - FINGER['p0'][1]), FINGER['p1'][0] - FINGER['p0'][0]))  # ~60 deg

def wrapped_bandage():
    """Bandage wrapped around the finger: rotated perpendicular, clipped to the finger silhouette."""
    def mk():
        fsp, fx0, fy0 = finger_sprite()
        b = bandage_sprite(520, 190)
        rb = b.rotate(FING_ANG - 90, resample=Image.BICUBIC, expand=True)
        c = finger_pt(0.72)
        canvas = Image.new('RGBA', fsp.size, (0, 0, 0, 0))
        canvas.alpha_composite(rb, (int(c[0] - fx0 - rb.width / 2), int(c[1] - fy0 - rb.height / 2)))
        fa = np.asarray(fsp.getchannel('A'), np.float32) / 255
        arr = np.asarray(canvas, np.float32)
        # cylindrical shading across the finger
        arr[..., 3] *= fa
        arr[..., :3] *= 0.9
        out = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
        return out
    return cached('wrapped', mk)

def draw_finger(img, t, cut=True, wrapped=False, dx=0, dy=0):
    fsp, fx0, fy0 = finger_sprite()
    with_shadow(img, fsp, fx0 + fsp.width / 2 + dx, fy0 + fsp.height / 2 + dy, a=0.4, blur=20)
    if cut and not wrapped:
        c = finger_pt(0.72)
        ov = OV(img, c[0] - 140 + dx, c[1] - 140 + dy, c[0] + 140 + dx, c[1] + 140 + dy)
        a = math.radians(FING_ANG - 90)
        ux, uy = math.cos(a), -math.sin(a)
        ov.d.line(ov.pts([(c[0] - ux * 70 + dx, c[1] - uy * 70 + dy), (c[0] + ux * 70 + dx, c[1] + uy * 70 + dy)]), fill=(200, 30, 40, 255), width=14)
        ov.commit()
    if wrapped:
        w = wrapped_bandage()
        paste_at(img, w, fx0 + dx, fy0 + dy)

def cotton_sprite(R=150, seed=0):
    def mk():
        im = Image.new('RGBA', (R * 3, R * 3), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        rng = np.random.default_rng(seed)
        c = R * 1.5
        for k in range(9):
            a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.2, 0.6) * R
            x, y, s = c + math.cos(a) * rr, c + math.sin(a) * rr * 0.7, rng.uniform(0.45, 0.7) * R
            d.ellipse((x - s, y - s, x + s, y + s), fill=(232, 232, 238, 255))
        for k in range(9):
            a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.1, 0.5) * R
            x, y, s = c + math.cos(a) * rr - 10, c + math.sin(a) * rr * 0.7 - 14, rng.uniform(0.35, 0.55) * R
            d.ellipse((x - s, y - s, x + s, y + s), fill=(252, 252, 255, 255))
        return im.filter(ImageFilter.GaussianBlur(1.5))
    return cached(('cot', R, seed), mk)

def knife_sprite(L=620):
    def mk():
        h = int(L * 0.2)
        im = Image.new('RGBA', (L, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, h * 0.3, L * 0.36, h * 0.8), radius=int(h * 0.2), fill=(120, 70, 40, 255), outline=(70, 40, 20, 255), width=4)
        for x in (0.1, 0.2, 0.3):
            d.ellipse((L * x - 7, h * 0.55 - 7, L * x + 7, h * 0.55 + 7), fill=(220, 210, 190, 255))
        d.polygon([(L * 0.36, h * 0.25), (L * 0.98, h * 0.42), (L * 0.98, h * 0.55), (L * 0.36, h * 0.85)], fill=(205, 212, 222, 255), outline=(120, 126, 140, 255))
        d.line([(L * 0.38, h * 0.36), (L * 0.95, h * 0.46)], fill=(245, 248, 255, 255), width=5)
        return im
    return cached(('knife', L), mk)

def carrot_sprite(L=420):
    def mk():
        h = int(L * 0.32)
        im = Image.new('RGBA', (L + 120, h + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(110, 20), (L + 110, h / 2 + 20), (110, h + 20)], fill=(240, 130, 40, 255), outline=(190, 90, 20, 255))
        for k in range(4):
            x = 170 + k * L * 0.2
            d.line([(x, 20 + h * (0.1 + 0.08 * k)), (x + 20, 20 + h * (0.3 + 0.05 * k))], fill=(200, 100, 30, 255), width=5)
        for k in range(3):
            d.polygon([(110, h / 2 + 20), (10, h / 2 - 30 + k * 30), (30, h / 2 - 10 + k * 30)], fill=(70, 160, 60, 255))
        return im
    return cached(('carrot', L), mk)

def scissors_sprite(L=360, open_=0.4):
    key = ('sc', L, round(open_, 2))
    def mk():
        im = Image.new('RGBA', (L * 2, L * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = (L, L)
        for s in (-1, 1):
            a = s * open_ * 0.5
            tip = (c[0] + math.cos(a) * L * 0.9, c[1] + math.sin(a) * L * 0.9)
            n = (-math.sin(a), math.cos(a))
            d.polygon([(c[0] + n[0] * 14, c[1] + n[1] * 14), tip, (c[0] - n[0] * 14, c[1] - n[1] * 14)], fill=(200, 206, 216, 255), outline=(110, 116, 130, 255))
            hb = (c[0] - math.cos(-a) * L * 0.45, c[1] + math.sin(-a) * L * 0.45 * -1 + s * L * 0.12)
            d.ellipse((hb[0] - L * 0.16, hb[1] - L * 0.12, hb[0] + L * 0.16, hb[1] + L * 0.12), outline=(214, 50, 44, 255), width=int(L * 0.06))
            d.line([c, hb], fill=(214, 50, 44, 255), width=int(L * 0.06))
        d.ellipse((c[0] - 12, c[1] - 12, c[0] + 12, c[1] + 12), fill=(80, 80, 90, 255))
        return im
    return cached(key, mk)

def money_chip(txt, size=150):
    return C(txt, size, bg=(120, 200, 110))

def arrow_down(img, cx, y0, y1, k, col=RED):
    if k <= 0:
        return
    y = y0 + (y1 - y0) * k
    ov = OV(img, cx - 110, y0 - 20, cx + 110, y + 120)
    ov.d.line(ov.pts([(cx, y0), (cx, y)]), fill=col + (255,), width=40)
    ov.d.polygon(ov.pts([(cx - 90, y - 10), (cx + 90, y - 10), (cx, y + 100)]), fill=col + (255,))
    ov.commit()

def check_mark(img, cx, cy, r, k, col=GREEN):
    if k <= 0:
        return
    ov = OV(img, cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30)
    p0, p1, p2 = (cx - r, cy), (cx - r * 0.3, cy + r * 0.7), (cx + r, cy - r * 0.8)
    q = clamp01(k * 2)
    ov.d.line(ov.pts([p0, (p0[0] + (p1[0] - p0[0]) * q, p0[1] + (p1[1] - p0[1]) * q)]), fill=col + (255,), width=40)
    q2 = clamp01(k * 2 - 1)
    if q2 > 0:
        ov.d.line(ov.pts([p1, (p1[0] + (p2[0] - p1[0]) * q2, p1[1] + (p1[1] * 0 + p2[1] - p1[1]) * q2)]), fill=col + (255,), width=40)
    ov.commit()

def shelf_box(w=520):
    """Plain bandage tin/box, no branding: just a bandage icon."""
    def mk():
        h = int(w * 0.62)
        im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((10, 10, w + 10, h + 10), radius=24, fill=(214, 60, 52, 255), outline=(120, 24, 20, 255), width=8)
        d.rounded_rectangle((40, 36, w - 20, h - 16), radius=16, outline=(255, 230, 220, 200), width=5)
        b = bandage_sprite(int(w * 0.66))
        im.alpha_composite(b, (int(10 + w / 2 - b.width / 2), int(10 + h / 2 - b.height / 2)))
        return im
    return cached(('sbox', w), mk)

def scout_lay(lay, x, yf, Hh):
    mannequin(lay, x, yf, Hh)

def kerchief(img, x, yf, Hh):
    P = lambda u, v: (x + u * Hh, yf - Hh + v * Hh)
    ov = OV(img, x - Hh * 0.2, yf - Hh * 0.9, x + Hh * 0.2, yf - Hh * 0.6)
    ov.d.polygon(ov.pts([P(-0.11, 0.185), P(0.11, 0.185), P(0, 0.33)]), fill=(214, 60, 52, 255), outline=(120, 24, 20, 255))
    ov.commit()

def machine_sprite(w=760):
    def mk():
        h = int(w * 0.7)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, h * 0.1, w * 0.7, h), radius=26, fill=(90, 110, 140, 255), outline=(40, 50, 70, 255), width=8)
        d.rectangle((w * 0.7, h * 0.62, w, h * 0.74), fill=(60, 60, 70, 255))
        for k in range(3):
            cx, cy = w * (0.16 + 0.19 * k), h * 0.4
            d.ellipse((cx - 50, cy - 50, cx + 50, cy + 50), fill=(200, 205, 215, 255), outline=(40, 50, 70, 255), width=6)
            d.line([(cx, cy), (cx + 36, cy - 20)], fill=(40, 50, 70, 255), width=8)
        d.rectangle((w * 0.08, h * 0.7, w * 0.6, h * 0.82), fill=(255, 210, 60, 255))
        d.rectangle((w * 0.3, 0, w * 0.4, h * 0.12), fill=(70, 80, 100, 255))
        return im
    return cached(('mach', w), mk)

def pile_positions(n, seed=3):
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        u = rng.uniform(-1, 1)
        yb = 1240 - 380 * (1 - abs(u) ** 1.5)
        out.append((CX + u * 520, rng.uniform(yb, 1250), rng.uniform(-80, 80)))
    out.sort(key=lambda p: p[1])
    return out

# ====================================================================== 0: hook - giant finger, bandage slapping on
class Hook(Base):
    z0, z1 = 1.3, 1.36
    focus = (CX, 1100)
    def make_shakes(self):
        return [(0.0, 10, 0.25), (self.we('accidents') , 12, 0.3), (self.tland(), 22, 0.4)]
    def tland(self):
        return self.we('Band-Aid!') - 0.05
    def events(self):
        return [(0.0, 'swipe', 0.5), (self.we('kitchen') - 0.03, 'pop', 0.45),
                (self.we('accidents') - 0.03, 'crack', 0.5), (self.we('gave') - 0.03, 'tape', 0.8), (self.we('the') - 0.03, 'thud', 0.6)]
    def plate(self):
        self.b = bandage_sprite(560, 205)
        self.hand = get_hand(540, -2.2)
        self.st = stamp_sprite('BAND-AID!', 140, color=RED, angle=-7)
        self.ouch = big_text('OUCH!', 120, YEL)
        return wall_plate('#FFE2C4', '#C2643C', 23, (CX, 1000, 1250))
    def hero(self, img, t, land=None):
        tl = self.tland() if land is None else land
        wrapped = t >= tl
        draw_finger(img, t, cut=True, wrapped=wrapped)
        if not wrapped:
            c = finger_pt(0.72)
            k = ease_in_out(clamp01(t / max(0.1, tl)))
            # bandage hovers above-right and swoops onto the cut
            sx, sy = c[0] + 330 * (1 - k) + 20 * math.sin(t * 5), c[1] - 260 * (1 - k)
            ang = FING_ANG - 90 + 35 * (1 - k)
            rb = rot(self.b, ang, 'hb')
            with_shadow(img, rb, sx, sy, a=0.35, dx=30 * (1 - k) + 10, dy=40 * (1 - k) + 12)
            draw_hand(img, self.hand, (sx + 150, sy - 40))
    def dyn(self, img, t):
        self.hero(img, t)
        tl = self.tland()
        if t < tl:
            pop(img, self.ouch, CX + 250, 1640, t, self.we('accidents') - 0.05)
        stamp_in(img, self.st, CX, 1700, t, tl)

# ====================================================================== 1: so weird, almost nobody bought them
class Weird(Base):
    def make_shakes(self):
        return [(self.we('weird,'), 14, 0.3), (self.we('nobody'), 18, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('first') - 0.03, 'pop', 0.4), (self.we('weird,') - 0.03, 'bloop', 0.6),
                (self.we('nobody') - 0.03, 'buzzer', 0.5)]
    def plate(self):
        self.box = shelf_box(760)
        self.st = stamp_sprite('NOBODY BOUGHT THEM', 70, color=RED, angle=-6)
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300), counter=(1260, '#7A5A40'))
    def dyn(self, img, t):
        tw = self.we('weird,')
        bob = 6 * math.sin(t * 5)
        with_shadow(img, rot(self.box, 4 * math.sin(t * 2.4), 'wb'), CX, 1080 + bob, a=0.4)
        pop(img, C('THE FIRST ONES...', 92, bg=WHITE), CX, 560, t, 0.05)
        for k in range(3):
            pop(img, qmark(170 + 50 * (k % 2), YEL if k % 2 else WHITE), CX - 360 + k * 360, 780 + 12 * math.sin(t * 6 + k), t, tw - 0.08 + k * 0.1)
        stamp_in(img, self.st, CX, 1700, t, self.we('nobody') - 0.02)

# ====================================================================== 2: 1920, Josephine kept nicking her fingers while cooking
class Kitchen(Base):
    z0, z1 = 1.26, 1.38
    def make_shakes(self):
        return [(self.we('1920,'), 14, 0.3), (self.we('Josephine'), 10, 0.25), (self.we('nicking'), 18, 0.35), (self.we('fingers'), 12, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('1920,') - 0.03, 'thud', 0.7), (self.we('Earle') - 0.03, 'pop', 0.5),
              (self.we('Josephine') - 0.03, 'chime', 0.5)]
        tn = self.we('nicking') - 0.03
        ev += [(tn, 'crack', 0.55), (tn + 0.4, 'crack', 0.45), (self.we('while') - 0.03, 'sizzle', 0.5)]
        return ev
    def plate(self):
        self.knife = knife_sprite(600)
        self.carrot = carrot_sprite(420)
        self.hand = get_hand(700, -0.5)
        self.ouch = big_text('OUCH!', 120, YEL)
        return wall_plate('#FFF1B8', '#C98A2A', 19, (CX, 1000, 1250), counter=(1100, '#8A6040'))
    def dyn(self, img, t):
        tn = self.we('nicking')
        paste_center(img, self.carrot, CX + 80, 1040, scale=1.3)
        hand_tip = (CX - 60, 1010)
        draw_hand(img, self.hand, hand_tip)
        chop = abs(math.sin(t * 6.5))
        kx, ky = CX + 140, 820 + 150 * (1 - chop)
        paste_center(img, rot(self.knife, -18 + 10 * chop, 'kn'), kx, ky, scale=1.25)
        if t < self.we('Earle') - 0.06:
            pop(img, C('1920', 140, bg=YEL), CX, 560, t, self.we('1920,') - 0.08)
        else:
            pop(img, C('EARLE DICKSON', 88, bg=WHITE), CX, 560, t, self.we('Earle') - 0.06)
            pop(img, C('+ HIS WIFE JOSEPHINE', 72, bg=YEL), CX, 690, t, self.we('Josephine') - 0.06)
        for k in range(3):
            t0 = tn - 0.05 + k * 0.4
            if t > t0:
                rx, ry = hand_tip[0] - 120 + k * 60, hand_tip[1] - 30 + k * 30
                ov = OV(img, rx - 60, ry - 60, rx + 60, ry + 60)
                ov.d.line(ov.pts([(rx - 35, ry - 10), (rx + 35, ry + 10)]), fill=(200, 30, 40, 255), width=12)
                ov.commit()
        pop(img, self.ouch, CX + 250, 1560, t, tn - 0.05)
        pop(img, C('OUCH AGAIN!', 74, bg=RED, fg=WHITE), CX - 150, 1730, t, tn + 0.5)

# ====================================================================== 3: cotton buyer at Johnson & Johnson, had an idea
class Cotton(Base):
    def make_shakes(self):
        return [(self.we('cotton'), 12, 0.3), (self.we('Johnson'), 12, 0.3), (self.we('idea.'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('cotton') - 0.03, 'bloop', 0.6), (self.we('Johnson') - 0.03, 'pop', 0.5),
                (self.we('had') - 0.05, 'ding', 0.7)]
    def plate(self):
        self.cots = [cotton_sprite(150 + 20 * (k % 3), k) for k in range(7)]
        self.bulb = bulb_sprite(150)
        self.man = None
        lay = Layer()
        mannequin(lay, CX, 1980, 1150)
        img = wall_plate('#C8F0D8', '#2F8A5A', 13, (CX, 1000, 1250))
        self.p_man = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        return img
    def dyn(self, img, t):
        ti = self.we('he') - 0.1
        if t >= ti:
            img.paste(self.p_man, (0, 0))
            pop(img, self.bulb, CX, 650 + 8 * math.sin(t * 8), t, ti)
            pop(img, C('AN IDEA!', 110, bg=YEL), CX, 1700, t, self.we('idea.') - 0.08)
            return
        for k, c in enumerate(self.cots):
            x = CX - 360 + (k % 4) * 240 + (120 if k >= 4 else 0)
            y = 900 + (k // 4) * 270 + 10 * math.sin(t * 4 + k)
            pop(img, c, x, y, t, -0.2 + k * 0.05)
        pop(img, C('COTTON BUYER', 100, bg=WHITE), CX, 560, t, -0.15)
        pop(img, C('JOHNSON & JOHNSON', 68, bg=YEL), CX, 1700, t, self.we('Johnson') - 0.06)

# ====================================================================== 4: gauze pads along sticky tape, snip one off
class Build(Base):
    z0, z1 = 1.26, 1.34
    def tsnip(self):
        return self.we('snip') - 0.05
    def make_shakes(self):
        return [(self.we('gauze'), 10, 0.25), (self.we('tape,'), 12, 0.3), (self.tsnip(), 20, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('stuck') - 0.03, 'tape', 0.6)]
        tg = self.we('gauze') - 0.05
        for k in range(4):
            ev.append((tg + k * 0.2, 'pop', 0.45))
        ev += [(self.tsnip(), 'scratch', 0.7), (self.tsnip() + 0.12, 'crack', 0.4)]
        return ev
    def plate(self):
        self.st = stamp_sprite('SNIP!', 150, color=RED, angle=-8)
        self.pad = cached('padsp', lambda: Image.new('RGBA', (170, 150), (0, 0, 0, 0)))
        return wall_plate('#BFE6FF', '#2A6FB0', 31, (CX, 1000, 1250), counter=(1200, '#B08055'))
    def dyn(self, img, t):
        y = 980
        ts = self.tsnip()
        cutx = CX + 315
        L = 1500 * (0.35 + 0.65 * ease_out(clamp01(t / 0.9)))
        x0 = CX - 750
        sh = 140 * ease_out(clamp01((t - ts) / 0.3)) if t > ts else 0
        ov = OV(img, 0, y - 150, PW, y + 150)
        segs = [(x0, min(x0 + L, cutx)), (cutx + sh, x0 + L + sh)] if x0 + L > cutx else [(x0, x0 + L)]
        for (a, b) in segs:
            if b - a < 4:
                continue
            ov.d.rectangle(ov.pts([(a, y - 125), (b, y + 125)]), fill=TAN + (255,), outline=TAN_D + (255,), width=4)
            for x in np.arange(a + 30, b - 10, 50):
                for yy in (y - 95, y + 95):
                    ov.d.ellipse(ov.pts([(x - 6, yy - 6), (x + 6, yy + 6)]), fill=TAN_D + (255,))
        ov.commit()
        tg = self.we('gauze') - 0.08
        pads = [CX - 470, CX - 160, CX + 150, CX + 470]
        for k, px in enumerate(pads):
            if t < tg + k * 0.2:
                continue
            u = ease_back(clamp01((t - tg - k * 0.2) / 0.3), 2)
            dx = sh if k == 3 else 0
            ov = OV(img, px - 140 + dx, y - 110, px + 140 + dx, y + 110)
            hw, hh = 105 * u, 85 * u
            ov.d.rounded_rectangle(ov.pts([(px - hw + dx, y - hh), (px + hw + dx, y + hh)]), radius=12, fill=(252, 246, 236, 255), outline=(220, 206, 186, 255), width=4)
            for q in range(-3, 4):
                ov.d.line(ov.pts([(px + q * 28 * u + dx, y - hh + 8), (px + q * 28 * u + dx, y + hh - 8)]), fill=(236, 226, 210, 255), width=2)
            ov.commit()
        pop(img, C('HIS HOMEMADE FIX:', 84, bg=WHITE), CX, 560, t, 0.0, out_t=tg - 0.1)
        if t > tg - 0.1:
            pop(img, C('GAUZE PADS', 96, bg=WHITE), CX, 560, t, tg)
        pop(img, C('STICKY TAPE', 84, bg=YEL), CX, 1190, t, self.we('sticky') - 0.06)
        if t > ts - 0.5:
            k = ease_out(clamp01((t - ts + 0.5) / 0.35))
            op = 0.45 if t < ts else 0.08
            sx, sy = cutx, y - 60 - 500 * (1 - k)
            ov = OV(img, sx - 260, sy - 520, sx + 260, sy + 240)
            for sgn in (-1, 1):
                ang = math.pi / 2 + sgn * op / 2
                tip = (sx + math.cos(ang) * 230, sy + math.sin(ang) * 230)
                nx, ny = -math.sin(ang), math.cos(ang)
                ov.d.polygon(ov.pts([(sx + nx * 40, sy + ny * 40), tip, (sx - nx * 40, sy - ny * 40)]), fill=(210, 216, 226, 255), outline=(100, 106, 120, 255))
                hx, hy = sx - math.cos(ang) * 230, sy - math.sin(ang) * 230
                ov.d.line(ov.pts([(sx, sy), (hx, hy)]), fill=(214, 50, 44, 255), width=26)
                ov.d.ellipse(ov.pts([(hx - 70, hy - 90), (hx + 70, hy + 40)]), outline=(214, 50, 44, 255), width=26)
            ov.d.ellipse(ov.pts([(sx - 16, sy - 16), (sx + 16, sy + 16)]), fill=(60, 60, 70, 255))
            ov.commit()
        stamp_in(img, self.st, CX, 1700, t, ts)

def hexc_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (0,)

# ====================================================================== 5: bosses weren't impressed, until he showed it on himself
class Bosses(Base):
    def tu(self):
        return self.we('until') - 0.06
    def make_shakes(self):
        return [(self.we("weren't"), 12, 0.3), (self.tu(), 12, 0.3), (self.we('himself.'), 16, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we("weren't") - 0.03, 'buzzer', 0.45), (self.tu(), 'swipe', 0.5),
                (self.we('showed') - 0.03, 'tape', 0.6), (self.we('on') - 0.03, 'ding', 0.6)]
    def plate(self):
        lay = Layer()
        for x in (CX - 380, CX, CX + 380):
            mannequin(lay, x, 2050, 1050)
        img = wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300))
        self.p_b = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.st = stamp_sprite('IT WORKS!', 118, color=GREEN, angle=-7)
        return wall_plate('#C8F0D8', '#2F8A5A', 13, (CX, 1000, 1250))
    def dyn(self, img, t):
        tu = self.tu()
        if t < tu:
            img.paste(self.p_b, (0, 0))
            pop(img, C('THE BOSSES', 96, bg=WHITE), CX, 560, t, 0.05)
            red_x(img, CX, 1000, 200, clamp01((t - self.we("weren't") + 0.05) / 0.3))
            pop(img, C('NOT IMPRESSED', 96, bg=RED, fg=WHITE), CX, 1700, t, self.we('impressed...') - 0.06)
            return
        tw = self.we('showed') - 0.05
        draw_finger(img, t, cut=True, wrapped=t > tw)
        if t <= tw:
            c = finger_pt(0.72)
            k = ease_out(clamp01((t - tu) / max(0.1, tw - tu)))
            paste_center(img, rot(bandage_sprite(560, 205), FING_ANG - 90 + 30 * (1 - k), 'bb'), c[0] + 300 * (1 - k), c[1] - 240 * (1 - k))
        pop(img, C('ON HIMSELF', 100, bg=YEL), CX, 560, t, tw)
        check_mark(img, CX + 330, 1560, 100, clamp01((t - self.we('himself.') + 0.1) / 0.3))
        stamp_in(img, self.st, CX - 60, 1720, t, self.we('himself.') - 0.1)

# ====================================================================== 6: handmade strips, 18 inches long
class Long(Base):
    z0, z1 = 1.0, 1.06
    def make_shakes(self):
        return [(self.we('handmade'), 12, 0.3), (self.we('18'), 22, 0.4), (self.we('long!'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('handmade') - 0.03, 'tape', 0.6), (self.we('strips,') - 0.03, 'swipe', 0.5),
                (self.we('18') - 0.03, 'boom', 0.6), (self.we('inches') - 0.03, 'riser', 0.4)]
    def plate(self):
        self.rul = cached('rul', lambda: ruler_tex(cm=18, ppc=62, h=150, label=None).convert('RGBA'))
        self.st = stamp_sprite('18 INCHES!', 120, color=RED, angle=-7)
        self.today = bandage_sprite(186, 60)
        return wall_plate('#FFE7B0', '#C77A30', 8, (CX, 1000, 1300))
    def dyn(self, img, t):
        tu = self.we('handmade') - 0.1
        k = 0.12 + 0.88 * ease_out(clamp01(t / max(0.2, self.we('18') - 0.1)))
        x0 = CX - self.rul.width / 2
        L = self.rul.width * k
        y = 950
        ov = OV(img, 0, y - 130, PW, y + 130)
        if L > 4:
            ov.d.rounded_rectangle(ov.pts([(x0, y - 110), (x0 + L, y + 110)]), radius=50, fill=TAN + (255,), outline=TAN_D + (255,), width=5)
            ov.d.rectangle(ov.pts([(x0 + 30, y - 70), (x0 + max(31, L - 30), y + 70)]), fill=(252, 246, 236, 255), outline=(222, 210, 192, 255), width=3)
            for xx in np.arange(x0 + 60, x0 + L - 30, 40):
                ov.d.line(ov.pts([(xx, y - 66), (xx, y + 66)]), fill=(236, 226, 210, 255), width=2)
        ov.commit()
        if t > self.we('18') - 0.15:
            pop(img, self.rul, CX, 1140, t, self.we('18') - 0.15)
            pop(img, C('vs. TODAY:', 60, bg=WHITE), CX - 140, 760, t, self.we('inches') - 0.05)
            pop(img, self.today, CX + 160, 760, t, self.we('inches'))
        pop(img, C('HANDMADE', 92, bg=WHITE), CX, 560, t, tu)
        stamp_in(img, self.st, CX, 1700, t, self.we('18') - 0.02)

# ====================================================================== 7: first year only $3,000 worth
class Sales(Base):
    def make_shakes(self):
        return [(self.we('year,'), 10, 0.25), (self.we('$3,000'), 22, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('first') - 0.03, 'pop', 0.45), (self.we('sold') - 0.03, 'cash', 0.5),
                (self.we('$3,000') - 0.03, 'buzzer', 0.5)]
    def plate(self):
        self.box = shelf_box(420)
        self.big = big_text('$3,000', 230, (120, 220, 110))
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300), counter=(1260, '#4A4060'))
    def dyn(self, img, t):
        t3 = self.we('$3,000') - 0.08
        pop(img, C('FIRST YEAR SALES', 92, bg=WHITE), CX, 560, t, 0.05)
        if t < t3:
            for k in range(3):
                paste_center(img, rot(self.box, (k - 1) * 8, ('sb', k)), CX - 330 + k * 330, 1050 + 8 * math.sin(t * 5 + k))
            return
        pop(img, self.big, CX, 900, t, t3)
        arrow_down(img, CX + 0, 1060, 1180, ease_out(clamp01((t - t3 - 0.2) / 0.4)))
        pop(img, C('ONLY!', 110, bg=RED, fg=WHITE), CX, 1700, t, t3 + 0.1)

# ====================================================================== 8: free to Boy Scouts, machines made them smaller
class Scouts(Base):
    def tm(self):
        return self.we('machines') - 0.08
    def make_shakes(self):
        return [(self.we('free'), 16, 0.35), (self.tm(), 12, 0.3), (self.we('smaller.'), 12, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('free') - 0.03, 'party', 0.55), (self.we('Boy') - 0.03, 'pop', 0.5),
              (self.tm(), 'rattle', 0.6)]
        for k in range(4):
            ev.append((self.tm() + 0.3 + k * 0.22, 'pop', 0.35))
        return ev
    def plate(self):
        lay = Layer()
        for x in (CX - 380, CX, CX + 380):
            mannequin(lay, x, 2150, 950)
        img = wall_plate('#C8F0D8', '#2F8A5A', 13, (CX, 1000, 1250))
        self.p_s = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        for x in (CX - 380, CX, CX + 380):
            kerchief(self.p_s, x, 2150, 950)
        self.small = [rot(bandage_sprite(300), a, ('sm', a)) for a in (-30, 10, 40, -10)]
        self.mach = machine_sprite(640)
        self.st = stamp_sprite('FREE!', 170, color=RED, angle=-8)
        return wall_plate('#BFE6FF', '#2A6FB0', 31, (CX, 1000, 1250), counter=(1260, '#B08055'))
    def dyn(self, img, t):
        tm = self.tm()
        if t < tm:
            img.paste(self.p_s, (0, 0))
            tf = self.we('free') - 0.1
            for k in range(10):
                t0 = tf + k * 0.08
                if t < t0:
                    continue
                u = (t - t0)
                x = CX - 450 + (k * 97) % 900
                y = 600 + 520 * u + 20 * math.sin(u * 6 + k)
                if y < 1250:
                    paste_center(img, self.small[k % 4], x, y)
            stamp_in(img, self.st, CX, 560, t, tf)
            pop(img, C('BOY SCOUTS', 100, bg=YEL), CX, 1700, t, self.we('Boy') - 0.06)
            return
        with_shadow(img, self.mach, CX - 110, 1020, a=0.4)
        for k in range(4):
            t0 = tm + 0.3 + k * 0.22
            if t < t0:
                continue
            u = ease_out(clamp01((t - t0) / 0.4))
            paste_center(img, self.small[k % 4], CX + 230 + 60 * u + (k % 2) * 80, 1090 - (200 + 120 * k) * u, scale=0.8)
        pop(img, C('MACHINE-MADE', 92, bg=WHITE), CX, 560, t, tm + 0.02)
        pop(img, C('SMALLER!', 110, bg=YEL), CX, 1700, t, self.we('smaller.') - 0.08)

# ====================================================================== 9: VP + 100 billion -> loop back to the hook
class Outro(Hook):
    def tswitch(self):
        return self.we('all') - 0.08
    def tb(self):
        return self.we('100') - 0.08
    def tland(self):
        return 99.0
    def make_shakes(self):
        return [(self.we('vice'), 12, 0.3), (self.tb(), 18, 0.4), (self.tswitch(), 10, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('vice') - 0.03, 'chime', 0.6), (self.tb(), 'boom', 0.6)]
        for k in range(5):
            ev.append((self.tb() + 0.15 + k * 0.12, 'pop', 0.3))
        ev.append((self.tswitch(), 'riser', 0.4))
        return ev
    def plate(self):
        Hook.plate(self)
        self.hp = wall_plate('#FFE2C4', '#C2643C', 23, (CX, 1000, 1250))
        lay = Layer()
        mannequin(lay, CX, 2100, 1450)
        img = wall_plate('#5A4A8A', '#1C1838', 9, (CX, 1000, 900))
        self.p_vp = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.small = [rot(bandage_sprite(240), a, ('sm2', a)) for a in range(-80, 81, 20)]
        self.pile = pile_positions(70)
        self.star = star_sprite(70)
        return wall_plate('#FFF1B8', '#C98A2A', 19, (CX, 1000, 1250))
    def dyn(self, img, t):
        tw, tb = self.tswitch(), self.tb()
        if t >= tw:
            img.paste(self.hp, (0, 0))
            Hook.hero(self, img, (t - tw) * 0.2, land=99)
            return
        if t < tb:
            img.paste(self.p_vp, (0, 0))
            glow(img, CX, 900, 600, (255, 240, 200), 0.4)
            for k in range(5):
                a = t * 0.9 + k * 2 * math.pi / 5
                pop(img, self.star, CX + math.cos(a) * 420, 1000 + math.sin(a) * 300, t, self.we('vice') - 0.06 + k * 0.05)
            pop(img, C('EARLE', 100, bg=WHITE), CX, 560, t, 0.03, out_t=self.we('vice') - 0.1)
            pop(img, C('VICE PRESIDENT', 100, bg=YEL), CX, 560, t, self.we('vice') - 0.06)
            return
        n = min(len(self.pile), int((t - tb) * 90) + 1)
        for k in range(n):
            x, y, a = self.pile[k]
            u = ease_out(clamp01((t - tb - k / 90) / 0.25))
            paste_center(img, self.small[k % len(self.small)], x, y - 400 * (1 - u))
        pop(img, C('100 BILLION+', 130, bg=YEL), CX, 600, t, tb)
    def cam(self, t):
        tw = self.tswitch()
        dx, dy, dr = self.shake(t)
        if t >= tw:
            return Hook.z0, Hook.focus[0] + dx, Hook.focus[1] + dy, dr
        p = 1 - ease_out(t / 0.32)
        return 1.24 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1060 + dy, 2.0 * p + dr

SCENES = [Hook, Weird, Kitchen, Cotton, Build, Bosses, Long, Sales, Scouts, Outro]
