"""Stanley cups were almost forgotten until a Utah shopping blog saved them (2026-11-24).
Generic stand-ins only: plain unbranded tumblers and bottles, no logos or packaging art."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish
from mw_scenes import glow, stamp_sprite, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import red_x

RED = (214, 50, 44)
YEL = (255, 210, 60)
GREEN = (60, 170, 90)
WHITE = (255, 255, 255)
PINK = (244, 150, 186)
SAGE = (160, 186, 150)
CREAM = (238, 226, 200)
LILAC = (186, 160, 226)
BLUE = (120, 180, 230)
CUP_COLS = [PINK, SAGE, CREAM, LILAC, BLUE, (250, 186, 120)]

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

def shade_cyl(im, x0, x1, k_dark=0.55, k_hi=0.35):
    """Horizontal cylinder shading over an RGBA sprite (columns x0..x1)."""
    a = np.asarray(im, np.float32) / 255
    w = a.shape[1]
    xs = np.arange(w, dtype=np.float32)
    u = np.clip((xs - x0) / max(1, x1 - x0), 0, 1)
    shade = 1 - k_dark * (u ** 2.2) - 0.25 * ((1 - u) ** 6)
    hi = k_hi * np.exp(-((u - 0.24) / 0.07) ** 2)
    rgb = a[..., :3] * shade[None, :, None] + hi[None, :, None]
    a[..., :3] = np.clip(rgb, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8), 'RGBA')

# ---------------------------------------------------------------- generic big tumbler (handle + lid + straw), no logo
def cup_sprite(H=900, col=PINK):
    def mk():
        ss = 2
        Wd = int(H * 0.78)
        im, d = ss_draw(Wd, H, ss)
        Z = lambda *v: tuple(x * ss for x in v)
        bw = H * 0.46
        cxp = H * 0.29
        top, bot = H * 0.24, H * 0.98
        c = col + (255,)
        dk = tuple(int(v * 0.7) for v in col) + (255,)
        # handle
        hx0, hx1 = cxp + bw * 0.36, cxp + bw * 0.5 + H * 0.2
        d.rounded_rectangle(Z(hx0, top + H * 0.08, hx1, top + H * 0.5), radius=int(H * 0.08 * ss), fill=dk)
        d.rounded_rectangle(Z(hx0 + H * 0.02, top + H * 0.14, hx1 - H * 0.07, top + H * 0.44), radius=int(H * 0.05 * ss), fill=(0, 0, 0, 0))
        # body: wide top, tapers to narrow base (car-cup-holder base)
        body = [(cxp - bw / 2, top), (cxp + bw / 2, top), (cxp + bw * 0.42, top + H * 0.42), (cxp + bw * 0.33, top + H * 0.5),
                (cxp + bw * 0.33, bot), (cxp - bw * 0.33, bot), (cxp - bw * 0.33, top + H * 0.5), (cxp - bw * 0.42, top + H * 0.42)]
        body_im, bd = ss_draw(Wd, H, ss)
        bd.polygon([Z(*p) for p in body], fill=c)
        bd.ellipse(Z(cxp - bw * 0.33, bot - H * 0.03, cxp + bw * 0.33, bot + H * 0.012), fill=c)
        body_im = shade_cyl(body_im, (cxp - bw / 2) * ss, (cxp + bw / 2) * ss)
        im.alpha_composite(body_im)
        d = ImageDraw.Draw(im)
        # base band
        d.rectangle(Z(cxp - bw * 0.33, bot - H * 0.07, cxp + bw * 0.33, bot - H * 0.055), fill=tuple(int(v * 0.8) for v in col) + (255,))
        # lid
        lid_im, ld = ss_draw(Wd, H, ss)
        ld.rounded_rectangle(Z(cxp - bw * 0.53, top - H * 0.07, cxp + bw * 0.53, top + H * 0.02), radius=int(H * 0.03 * ss), fill=(236, 236, 240, 255))
        ld.ellipse(Z(cxp - bw * 0.5, top - H * 0.1, cxp + bw * 0.5, top - H * 0.04), fill=(250, 250, 252, 255))
        lid_im = shade_cyl(lid_im, (cxp - bw * 0.53) * ss, (cxp + bw * 0.53) * ss, 0.35, 0.2)
        # straw (behind lid top edge)
        sd = ImageDraw.Draw(im)
        sd.polygon(Z(cxp + bw * 0.02, top - H * 0.07, cxp + bw * 0.1, top - H * 0.07, cxp + bw * 0.24, 0, cxp + bw * 0.16, 0), fill=tuple(int(v * 0.85) for v in col) + (255,))
        im.alpha_composite(lid_im)
        sd = ImageDraw.Draw(im)
        sd.polygon(Z(cxp + bw * 0.03, top - H * 0.1, cxp + bw * 0.1, top - H * 0.1, cxp + bw * 0.24, 0, cxp + bw * 0.16, 0), fill=tuple(int(v * 0.85) for v in col) + (255,))
        sd.polygon(Z(cxp + bw * 0.045, top - H * 0.1, cxp + bw * 0.065, top - H * 0.1, cxp + bw * 0.2, 0, cxp + bw * 0.18, 0), fill=(255, 255, 255, 120))
        return ss_done(im, Wd, H)
    return cached(('cup', H, col), mk)

def thermos_sprite(H=820):
    """Generic vintage green steel vacuum bottle with a cup-cap."""
    def mk():
        ss = 2
        Wd = int(H * 0.42)
        im, d = ss_draw(Wd, H, ss)
        Z = lambda *v: tuple(x * ss for x in v)
        g = (64, 120, 74, 255)
        cxp = Wd / 2
        bw = Wd * 0.8
        d.rounded_rectangle(Z(cxp - bw / 2, H * 0.24, cxp + bw / 2, H * 0.99), radius=int(bw * 0.18 * ss), fill=g)
        d.rounded_rectangle(Z(cxp - bw * 0.36, H * 0.15, cxp + bw * 0.36, H * 0.26), radius=int(10 * ss), fill=(170, 176, 182, 255))
        d.rounded_rectangle(Z(cxp - bw * 0.46, H * 0.02, cxp + bw * 0.46, H * 0.17), radius=int(16 * ss), fill=(70, 128, 80, 255))
        for y in (0.4, 0.82):
            d.rectangle(Z(cxp - bw / 2, H * y, cxp + bw / 2, H * (y + 0.025)), fill=(46, 90, 54, 255))
        im = shade_cyl(im, (cxp - bw / 2) * ss, (cxp + bw / 2) * ss, 0.5, 0.3)
        return ss_done(im, Wd, H)
    return cached(('thermos', H), mk)

def tent_sprite(w=520):
    def mk():
        h = int(w * 0.75)
        im, d = ss_draw(w, h, 2)
        Z = lambda *v: tuple(x * 2 for x in v)
        d.polygon(Z(w * 0.5, 0, w, h, 0, h), fill=(236, 140, 50, 255), outline=(150, 80, 20, 255))
        d.polygon(Z(w * 0.5, 0, w * 0.72, h, w * 0.28, h), fill=(200, 100, 30, 255))
        d.polygon(Z(w * 0.5, h * 0.35, w * 0.62, h, w * 0.38, h), fill=(60, 36, 20, 255))
        return ss_done(im, w, h)
    return cached(('tent', w), mk)

def hardhat_sprite(w=360):
    def mk():
        h = int(w * 0.6)
        im, d = ss_draw(w, h, 2)
        Z = lambda *v: tuple(x * 2 for x in v)
        d.pieslice(Z(w * 0.12, h * 0.05, w * 0.88, h * 1.4), 180, 360, fill=(255, 200, 40, 255))
        d.rounded_rectangle(Z(0, h * 0.68, w, h * 0.86), radius=12, fill=(230, 170, 20, 255))
        d.rectangle(Z(w * 0.46, h * 0.08, w * 0.54, h * 0.7), fill=(240, 186, 30, 255))
        return ss_done(im, w, h)
    return cached(('hat', w), mk)

def phone_sprite(w=420, col=PINK):
    def mk():
        h = int(w * 1.9)
        im, d = ss_draw(w, h, 2)
        Z = lambda *v: tuple(x * 2 for x in v)
        d.rounded_rectangle(Z(0, 0, w, h), radius=int(w * 0.16 * 2), fill=(30, 30, 36, 255))
        d.rounded_rectangle(Z(w * 0.06, w * 0.06, w * 0.94, h - w * 0.06), radius=int(w * 0.12 * 2), fill=(255, 246, 250, 255))
        d.rounded_rectangle(Z(w * 0.36, w * 0.09, w * 0.64, w * 0.16), radius=20, fill=(30, 30, 36, 255))
        out = ss_done(im, w, h)
        hd = chip('SHOP BLOG', int(w * 0.1), bg=(255, 120, 170), fg=WHITE, padx=18, pady=8)
        out.alpha_composite(hd, (int(w / 2 - hd.width / 2), int(w * 0.14)))
        c = cup_sprite(int(h * 0.5), col)
        out.alpha_composite(c, (int(w / 2 - c.width * 0.37), int(h * 0.24)))
        ht = heart_sprite(int(w * 0.08))
        for k in range(3):
            out.alpha_composite(ht, (int(w * 0.18 + k * w * 0.24), int(h * 0.82)))
        return out
    return cached(('phone', w, col), mk)

def box_sprite(w=240):
    def mk():
        h = int(w * 0.8)
        im, d = ss_draw(w, h, 2)
        Z = lambda *v: tuple(x * 2 for x in v)
        d.polygon(Z(0, h * 0.2, w * 0.7, h * 0.2, w * 0.7, h, 0, h), fill=(206, 156, 96, 255), outline=(130, 90, 50, 255))
        d.polygon(Z(w * 0.7, h * 0.2, w, 0, w, h * 0.8, w * 0.7, h), fill=(170, 120, 70, 255), outline=(130, 90, 50, 255))
        d.polygon(Z(0, h * 0.2, w * 0.3, 0, w, 0, w * 0.7, h * 0.2), fill=(226, 180, 120, 255), outline=(130, 90, 50, 255))
        d.rectangle(Z(w * 0.3, h * 0.2, w * 0.4, h), fill=(236, 220, 180, 200))
        return ss_done(im, w, h)
    return cached(('box', w), mk)

def clock_sprite(R=300):
    def mk():
        im, d = ss_draw(2 * R + 20, 2 * R + 20, 2)
        Z = lambda *v: tuple(x * 2 for x in v)
        d.ellipse(Z(10, 10, 2 * R + 10, 2 * R + 10), fill=(255, 255, 255, 255), outline=(40, 40, 50, 255), width=40)
        for k in range(12):
            a = k * math.pi / 6
            r0, r1 = R * 0.78, R * 0.9
            d.line(Z(R + 10 + math.cos(a) * r0, R + 10 + math.sin(a) * r0, R + 10 + math.cos(a) * r1, R + 10 + math.sin(a) * r1), fill=(40, 40, 50, 255), width=16)
        return ss_done(im, 2 * R + 20, 2 * R + 20)
    return cached(('clock', R), mk)

def draw_clock_hands(img, cx, cy, R, ang_m, ang_h):
    ov = OV(img, cx - R, cy - R, cx + R, cy + R)
    for a, L, wd in ((ang_h, 0.5, 26), (ang_m, 0.75, 16)):
        ov.d.line(ov.pts([(cx, cy), (cx + math.sin(a) * R * L, cy - math.cos(a) * R * L)]), fill=(214, 50, 44, 255), width=wd)
    ov.d.ellipse(ov.box(cx - 24, cy - 24, cx + 24, cy + 24), fill=(40, 40, 50, 255))
    ov.commit()

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

def fade(sp, a):
    if a >= 1:
        return sp
    sp = sp.copy()
    sp.putalpha(sp.getchannel('A').point(lambda v: int(v * max(0, a))))
    return sp

def man_plate(c0, c1, seed, xs, yf, Hh, counter=None):
    lay = Layer()
    for x in xs:
        mannequin(lay, x, yf, Hh)
    img = wall_plate(c0, c1, seed, (CX, 1000, 1250), counter)
    return to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')

# ====================================================================== 0: hook - giant tumbler flickering out of existence
class Hook(Base):
    z0, z1 = 1.26, 1.34
    focus = (CX, 1110)
    def tst(self):
        return self.we('vanished') - 0.05
    def make_shakes(self):
        return [(0.0, 12, 0.25), (self.we('Stanley'), 8, 0.2), (self.we('almost'), 10, 0.25), (self.tst(), 20, 0.4), (self.we('from') - 0.05, 12, 0.3)]
    def events(self):
        return [(self.we('almost') - 0.03, 'pop', 0.3), (self.tst(), 'buzzer', 0.35),
                (self.we('from') - 0.03, 'chime', 0.35)]
    def plate(self):
        self.cup = cup_sprite(1020, PINK)
        self.st = stamp('ALMOST GONE!', 120)
        return wall_plate('#FFD6E6', '#B0507E', 23, (CX, 1050, 1250))
    def hero(self, img, t, flicker=True):
        ang = 7 * math.sin(t * 3.4)
        bob = 24 * math.sin(t * 4.2)
        a = 1.0
        if flicker and t > self.tst():
            u = t - self.tst()
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.cos(u * 16)) if u < 0.8 else 0.6 + 0.4 * (0.5 + 0.5 * math.cos(u * 6))
        for k in range(6):
            ph = (t * 0.8 + k / 6) % 1
            sparkle(img, CX - 430 + (k * 173) % 860, 1500 - 700 * ph, 30 * math.sin(math.pi * ph) + 4)
        with_shadow(img, fade(rot(self.cup, ang, 'hc'), a), CX + 40, 1240 + bob, a=0.35 * a, blur=22, dx=24, dy=40)
    def dyn(self, img, t):
        self.hero(img, t)
        stamp_in(img, self.st, CX, 1760, t, self.tst())
        pop(img, C('STANLEY CUP', 90, bg=YEL), CX, 1590, t, self.we('Stanley') - 0.06, out_t=self.tst() - 0.1)

# ====================================================================== 1: three women with a shopping blog saved it
class Saved(Base):
    def make_shakes(self):
        return [(self.we('three'), 10, 0.25), (self.we('blog'), 12, 0.3), (self.we('saved') - 0.05, 22, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('three') - 0.03, 'pop', 0.5), (self.we('women') - 0.03, 'pop', 0.4),
                (self.we('blog') - 0.03, 'bloop', 0.6), (self.we('saved') - 0.05, 'party', 0.6)]
    def plate(self):
        self.p_w = man_plate('#FFE6F0', '#C0608A', 17, [CX - 380, CX, CX + 380], 2120, 1050)
        self.phone = phone_sprite(440, PINK)
        self.heart = heart_sprite(70)
        self.st = stamp('SAVED!', 170, color=GREEN, angle=-7)
        return wall_plate('#FFE6F0', '#C0608A', 17, (CX, 1000, 1250))
    def dyn(self, img, t):
        tb = self.we('blog') - 0.1
        if t < tb:
            img.paste(self.p_w, (0, 0))
            pop(img, C('3 WOMEN', 110, bg=WHITE), CX, 600, t, self.we('three') - 0.08)
            return
        with_shadow(img, rot(self.phone, 4 * math.sin(t * 3), 'ph'), CX, 1080 + 10 * math.sin(t * 4), a=0.4, blur=20)
        for k in range(6):
            ph = ((t - tb) * 0.9 + k / 6) % 1
            x = CX + (380 if k % 2 else -380) + 30 * math.sin(t * 3 + k)
            paste_center(img, self.heart, x, 1500 - 900 * ph, scale=0.6 + 0.4 * math.sin(math.pi * ph))
        pop(img, C('A SHOPPING BLOG', 90, bg=YEL), CX, 560, t, tb)
        stamp_in(img, self.st, CX, 1740, t, self.we('saved') - 0.05)

# ====================================================================== 2: what did they tell Stanley?
class Question(Base):
    def make_shakes(self):
        return [(self.we('tell'), 10, 0.25), (self.we('changed'), 14, 0.3), (self.we('everything?') - 0.05, 18, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('tell') - 0.03, 'pop', 0.5), (self.we('changed') - 0.03, 'riser', 0.45)]
        for k in range(3):
            ev.append((self.we('that') + k * 0.1, 'pop', 0.35))
        return ev
    def plate(self):
        self.cups = [cup_sprite(620, c) for c in (SAGE, PINK, CREAM)]
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300))
    def dyn(self, img, t):
        tc = self.we('changed') - 0.08
        glow(img, CX, 1100, 520, (255, 220, 240), 0.35)
        for j in (0, 2, 1):
            x = CX + (j - 1) * 340
            y = 1150 + (0 if j == 1 else 70) + 14 * math.sin(t * 4 + j)
            pop(img, rot(self.cups[j], (j - 1) * -8, ('qc', j)), x + 40, y, t, 0.04 + 0.12 * abs(j - 1))
        pop(img, C('WHAT DID THEY SAY?', 84, bg=WHITE), CX, 560, t, 0.05)
        if t > tc:
            pop(img, C('IT CHANGED EVERYTHING', 70, bg=YEL), CX, 1740, t, tc)
        for k in range(3):
            pop(img, qmark(170 + 40 * (k % 2), YEL if k % 2 else WHITE), CX - 380 + k * 380, 800 + 14 * math.sin(t * 6 + k), t, self.we('that') + k * 0.1)

# ====================================================================== 3: 1913 steel bottles for workers and campers
class Steel1913(Base):
    def t13(self):
        return self.we('1913,') - 0.06
    def make_shakes(self):
        return [(self.t13(), 20, 0.4), (self.we('steel'), 12, 0.3), (self.we('workers') - 0.05, 14, 0.3), (self.we('campers.') - 0.05, 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.t13(), 'boom', 0.55), (self.we('steel') - 0.03, 'ding', 0.6),
                (self.we('bottles') - 0.03, 'pop', 0.4), (self.we('workers') - 0.05, 'thud', 0.6), (self.we('and') - 0.03, 'pop', 0.5)]
    def plate(self):
        self.th = thermos_sprite(900)
        self.hat = hardhat_sprite(380)
        self.tent = tent_sprite(460)
        return wall_plate('#E9DCC0', '#7A6040', 41, (CX, 1000, 1250))
    def dyn(self, img, t):
        t13, ts = self.t13(), self.we('steel') - 0.08
        if t < ts:
            stamp_in(img, big_text('1913', 320, YEL), CX, 1100, t, max(0.0, t13))
            pop(img, C('BACK IN...', 90, bg=WHITE), CX, 600, t, 0.03)
            return
        x_th = CX - 230
        with_shadow(img, rot(self.th, 5 * math.sin(t * 3), 'th'), x_th, 1120, a=0.4, blur=18)
        pop(img, C('1913', 100, bg=YEL), CX, 560, t, ts)
        pop(img, C('STEEL BOTTLE', 70, bg=WHITE), x_th, 1660, t, self.we('bottles') - 0.08)
        tw, tc = self.we('workers') - 0.08, self.we('and') - 0.06
        pop(img, self.hat, CX + 290, 900 + 10 * math.sin(t * 5), t, tw)
        pop(img, C('WORKERS', 70, bg=WHITE), CX + 290, 1080, t, tw)
        pop(img, self.tent, CX + 290, 1500, t, tc)
        pop(img, C('CAMPERS', 70, bg=(236, 140, 50), fg=WHITE), CX + 290, 1740, t, tc)

# ====================================================================== 4: 2016 Quencher, slow sales, stopped restocking
class SlowSales(Base):
    def tsl(self):
        return self.we('slow,') - 0.06
    def trs(self):
        return self.we('restocking') - 0.06
    def make_shakes(self):
        return [(self.we('Quencher'), 12, 0.3), (self.we('2016,'), 16, 0.35), (self.tsl(), 14, 0.3), (self.trs(), 22, 0.4)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Quencher') - 0.03, 'pop', 0.5), (self.we('2016,') - 0.03, 'boom', 0.5),
                (self.we('sales') - 0.03, 'riser', 0.3), (self.tsl(), 'bloop', 0.55), (self.trs(), 'buzzer', 0.55)]
    def plate(self):
        self.cup = cup_sprite(860, SAGE)
        self.st = stamp('NO RESTOCK', 130)
        self.p_shelf = wall_plate('#E6E6EA', '#6A6A78', 12, (CX, 1000, 1250), counter=(1500, '#9A9AA4'))
        return wall_plate('#DDF0E0', '#3E7A56', 15, (CX, 1000, 1250))
    def dyn(self, img, t):
        ts, tsl, trs = self.we('sales') - 0.1, self.tsl(), self.trs()
        if t < ts:
            with_shadow(img, rot(self.cup, 5 * math.sin(t * 3), 'sc'), CX + 40, 1150, a=0.38, blur=20)
            pop(img, C('THE QUENCHER', 96, bg=WHITE), CX, 560, t, 0.03)
            pop(img, C('2016', 110, bg=YEL), CX, 1740, t, self.we('2016,') - 0.08)
            return
        if t < trs:
            ov = OV(img, CX - 470, 640, CX + 470, 1620)
            ov.d.line(ov.pts([(CX - 420, 700), (CX - 420, 1560), (CX + 440, 1560)]), fill=(30, 30, 40, 255), width=14)
            k = ease_out(clamp01((t - ts) / 0.9))
            pts = [(CX - 400 + 820 * u, 900 + 560 * (u ** 1.3) + 40 * math.sin(u * 12)) for u in np.linspace(0, k, 24)]
            if k > 0.02:
                ov.d.line(ov.pts(pts), fill=(214, 50, 44, 255), width=22, joint='curve')
            ov.commit()
            pop(img, C('SALES', 100, bg=WHITE), CX, 560, t, ts)
            stamp_in(img, stamp('SO SLOW...', 120, color=(90, 90, 110)), CX + 80, 1000, t, tsl)
            return
        img.paste(self.p_shelf, (0, 0))
        ov = OV(img, CX - 520, 1300, CX + 520, 1540)
        ov.d.rectangle(ov.box(CX - 500, 1480, CX + 500, 1520), fill=(120, 90, 60, 255))
        ov.commit()
        for k in range(3):
            pop(img, qmark(150, WHITE), CX - 320 + k * 320, 1300, t, trs + 0.1 + k * 0.08)
        pop(img, C('EMPTY SHELF', 90, bg=WHITE), CX, 600, t, trs)
        stamp_in(img, self.st, CX, 1020, t, trs)

# ====================================================================== 5: Utah blog founders bought 5,000 cups
class Bought(Base):
    def t5k(self):
        return self.we('5,000') - 0.06
    def make_shakes(self):
        return [(self.we('Utah'), 12, 0.3), (self.we('bought'), 12, 0.3), (self.t5k(), 22, 0.4), (self.we('followers.') - 0.1, 12, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('founders') - 0.03, 'pop', 0.45), (self.we('Utah') - 0.03, 'chime', 0.55),
              (self.we('bought') - 0.03, 'cash', 0.6), (self.t5k(), 'boom', 0.55)]
        for k in range(5):
            ev.append((self.t5k() + 0.15 + k * 0.14, 'thud', 0.3))
        ev.append((self.we('followers.') - 0.3, 'party', 0.45))
        return ev
    def plate(self):
        self.p_w = man_plate('#FFE6F0', '#C0608A', 17, [CX - 380, CX, CX + 380], 2120, 1050)
        self.box = box_sprite(250)
        self.cups = [cup_sprite(300, c) for c in CUP_COLS]
        self.heart = heart_sprite(60)
        return wall_plate('#FFF1D8', '#C08A50', 7, (CX, 1000, 1250), counter=(1560, '#9A7050'))
    def dyn(self, img, t):
        tb, t5 = self.we('bought') - 0.08, self.t5k()
        if t < tb:
            img.paste(self.p_w, (0, 0))
            pop(img, C('THE FOUNDERS', 96, bg=WHITE), CX, 600, t, 0.03, out_t=self.we('Utah') - 0.1)
            if t > self.we('Utah') - 0.1:
                pop(img, C('IN UTAH', 110, bg=YEL), CX, 600, t, self.we('Utah') - 0.08)
            return
        n = 0 if t < t5 else min(15, int((t - t5) * 12) + 1)
        for k in range(n):
            col, row = k % 5, k // 5
            paste_center(img, self.box, CX - 440 + col * 220, 1460 - row * 170)
        if n == 0:
            for k in range(3):
                pop(img, self.cups[k], CX - 300 + k * 300 + 30, 1150, t, tb + k * 0.06)
        pop(img, C('BOUGHT', 100, bg=WHITE), CX, 560, t, tb, out_t=t5 - 0.1)
        if t > t5 - 0.1:
            pop(img, C('5,000 CUPS', 120, bg=YEL), CX, 560, t, t5)
        tf = self.we('followers.') - 0.3
        if t > tf:
            for k in range(5):
                ph = ((t - tf) * 1.2 + k / 5) % 1
                paste_center(img, self.heart, CX - 400 + k * 200, 900 - 200 * ph, scale=0.6 + 0.3 * math.sin(math.pi * ph))
            pop(img, C('FOR THEIR FOLLOWERS', 70, bg=WHITE), CX, 1760, t, tf)

# ====================================================================== 6: sold out in just days
class SoldOut(Base):
    def make_shakes(self):
        return [(self.we('sold'), 14, 0.3), (self.we('days.') - 0.05, 22, 0.4)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('sold') - 0.03, 'cash', 0.6)]
        for k in range(4):
            ev.append((self.we('sold') + 0.1 + k * 0.12, 'pop', 0.3))
        ev.append((self.we('days.') - 0.3, 'boom', 0.6))
        return ev
    def plate(self):
        self.box = box_sprite(250)
        self.st = stamp('SOLD OUT!', 160)
        return wall_plate('#FFF1D8', '#C08A50', 7, (CX, 1000, 1250), counter=(1560, '#9A7050'))
    def dyn(self, img, t):
        ts = self.we('sold') - 0.08
        for k in range(15):
            col, row = k % 5, k // 5
            gone = ts + (14 - k) * 0.06
            if t < gone:
                paste_center(img, self.box, CX - 440 + col * 220, 1460 - row * 170)
            elif t < gone + 0.3:
                u = (t - gone) / 0.3
                paste_center(img, fade(self.box, 1 - u), CX - 440 + col * 220, 1460 - row * 170 - 500 * u)
        pop(img, C('IN JUST DAYS', 100, bg=YEL), CX, 560, t, self.we('just') - 0.08)
        stamp_in(img, self.st, CX, 1060, t, ts + 0.15)

# ====================================================================== 7: next 5,000 sold out in about an hour
class OneHour(Base):
    def th(self):
        return self.we('hour!') - 0.06
    def make_shakes(self):
        return [(self.we('next'), 10, 0.25), (self.we('5,000'), 16, 0.35), (self.we('sold'), 12, 0.3), (self.th(), 24, 0.45)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('next') - 0.03, 'pop', 0.45), (self.we('5,000') - 0.03, 'boom', 0.5)]
        for k in range(6):
            ev.append((self.we('sold') + k * 0.16, 'tick', 0.45))
        ev.append((self.we('an') - 0.03, 'ding', 0.8))
        return ev
    def plate(self):
        self.clock = clock_sprite(330)
        self.st = stamp('~1 HOUR!', 160)
        return wall_plate('#FFE0D0', '#B0402C', 29, (CX, 1000, 1250))
    def dyn(self, img, t):
        tsd = self.we('sold') - 0.06
        glow(img, CX, 1100, 520, (255, 230, 200), 0.35)
        with_shadow(img, self.clock, CX, 1100, a=0.4, blur=18)
        sp = 0 if t < tsd else (t - tsd)
        draw_clock_hands(img, CX, 1100, 330, sp * 14.0, sp * 1.17)
        pop(img, C('THE NEXT 5,000', 96, bg=WHITE), CX, 560, t, 0.03)
        pop(img, C('SOLD OUT', 96, bg=YEL), CX, 1700, t, tsd, out_t=self.we('an') - 0.15)
        stamp_in(img, self.st, CX, 1720, t, self.we('an') - 0.06)

# ====================================================================== 8: $70 million -> $750 million
class Sales(Base):
    def t70(self):
        return self.we('$70') - 0.06
    def t750(self):
        return self.we('$750') - 0.06
    def make_shakes(self):
        return [(self.we('jumped'), 14, 0.3), (self.t70(), 14, 0.3), (self.t750(), 24, 0.45)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('yearly') - 0.03, 'pop', 0.45), (self.we('jumped') - 0.03, 'bloop', 0.6),
                (self.t70(), 'pop', 0.55), (self.we('to') - 0.03, 'riser', 0.55), (self.t750(), 'cash', 0.8)]
    def plate(self):
        self.bill = bill_sprite(260)
        return wall_plate('#DFF3DA', '#2E7A40', 11, (CX, 1000, 1250))
    def dyn(self, img, t):
        t70, t750, tr = self.t70(), self.t750(), self.we('to') - 0.08
        base_y = 1600
        ov = OV(img, CX - 500, 600, CX + 500, base_y + 30)
        ov.d.line(ov.pts([(CX - 460, base_y), (CX + 460, base_y)]), fill=(30, 30, 40, 255), width=14)
        h70 = 90 * ease_out(clamp01((t - t70) / 0.4))
        if h70 > 1:
            ov.d.rounded_rectangle(ov.box(CX - 380, base_y - h70, CX - 120, base_y), radius=12, fill=(150, 160, 150, 255), outline=(60, 70, 60, 255), width=6)
        h750 = 880 * ease_out(clamp01((t - tr) / (t750 - tr + 0.4)))
        if h750 > 1:
            ov.d.rounded_rectangle(ov.box(CX + 100, base_y - h750, CX + 400, base_y), radius=12, fill=(80, 190, 100, 255), outline=(30, 100, 40, 255), width=6)
        ov.commit()
        if t > t70:
            pop(img, C('$70M', 100, bg=WHITE), CX - 250, 1130, t, t70)
            pop(img, C('2019', 60, bg=WHITE), CX - 250, base_y + 110, t, t70)
        if t > tr:
            pop(img, C('2023', 60, bg=WHITE), CX + 250, base_y + 110, t, tr)
        if t > t750:
            pop(img, C('$750M', 110, bg=YEL), CX + 250, base_y - h750 - 30, t, t750)
            for k in range(10):
                t0 = t750 + k * 0.08
                if t < t0:
                    continue
                u = t - t0
                y = 640 + 900 * u
                if y < 1500:
                    paste_center(img, rot(self.bill, (k * 40 + u * 220) % 360, ('bl', k)), CX - 450 + (k * 137) % 900, y, scale=0.7)
        if t < t70:
            pop(img, C('YEARLY SALES', 100, bg=WHITE), CX, 1000, t, self.we('yearly') - 0.08)

# ====================================================================== 9: secret - wrong people: not campers, but women
class Secret(Base):
    def tn(self):
        return self.we('Not') - 0.06
    def tw(self):
        return self.we('women!') - 0.06
    def make_shakes(self):
        return [(self.we('secret?'), 14, 0.3), (self.we('wrong'), 18, 0.35), (self.tn(), 12, 0.3), (self.tw(), 24, 0.45)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('secret?') - 0.03, 'riser', 0.5), (self.we('told') - 0.03, 'pop', 0.4),
              (self.we('wrong') - 0.03, 'buzzer', 0.55), (self.we('campers,') - 0.03, 'scratch', 0.5), (self.we('but') - 0.03, 'party', 0.7)]
        return ev
    def plate(self):
        self.tent = tent_sprite(600)
        self.cups = [cup_sprite(380, c) for c in CUP_COLS]
        self.p_w = man_plate('#FFE6F0', '#C0608A', 17, [CX - 380, CX, CX + 380], 2120, 1050)
        self.st = stamp('WRONG PEOPLE!', 110)
        return wall_plate('#2C2A3A', '#121018', 41, (CX, 1000, 1000))
    def dyn(self, img, t):
        tn, tw, twr = self.tn(), self.we('but') - 0.06, self.we('wrong') - 0.06
        if t < tn:
            glow(img, CX, 1100, 480, (255, 220, 120), 0.5)
            pop(img, big_text('SECRET?', 200, YEL), CX, 1100, t, 0.0, out_t=twr - 0.1)
            pop(img, C('THEY TOLD STANLEY...', 80, bg=WHITE), CX, 560, t, self.we('told') - 0.08)
            stamp_in(img, self.st, CX, 1100, t, twr)
            return
        if t < tw:
            with_shadow(img, self.tent, CX, 1150, a=0.4)
            pop(img, C('NOT CAMPERS', 100, bg=WHITE), CX, 560, t, tn)
            red_x(img, CX, 1150, 300, clamp01((t - self.we('campers,')) / 0.3))
            return
        img.paste(self.p_w, (0, 0))
        for k in range(6):
            x = CX - 450 + k * 180
            pop(img, self.cups[k], x + 30, 1640 + 12 * math.sin(t * 5 + k), t, tw + k * 0.03)
        pop(img, C('WOMEN!', 150, bg=(236, 90, 140), fg=WHITE), CX, 600, t, tw, dur=0.2)

# ====================================================================== 10: pretty wild... loop back to the hook
class Outro(Hook):
    def tswitch(self):
        return self.we('few') - 0.08
    def tst(self):
        return 99.0
    def make_shakes(self):
        return [(self.we('wild,'), 14, 0.3), (self.tswitch(), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('wild,') - 0.03, 'bigpop', 0.5), (self.we('because') - 0.03, 'riser', 0.45),
                (self.tswitch(), 'pop', 0.5)]
    def plate(self):
        Hook.plate(self)
        self.hp = wall_plate('#FFD6E6', '#B0507E', 23, (CX, 1050, 1250))
        self.cups = [cup_sprite(420, c) for c in CUP_COLS]
        return wall_plate('#D8D4F2', '#4E4A8A', 5, (CX, 1000, 1300))
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hp, (0, 0))
            Hook.hero(self, img, t - tw, flicker=False)
            pop(img, C('A FEW YEARS EARLIER...', 76, bg=WHITE), CX, 1740, t, tw)
            return
        for k in range(6):
            a = t * 0.9 + k * 2 * math.pi / 6
            x, y = CX + math.cos(a) * 340, 1120 + math.sin(a) * 330
            pop(img, self.cups[k], x + 30, y, t, 0.03 + k * 0.05)
        pop(img, C('PRETTY WILD...', 100, bg=YEL), CX, 560, t, self.we('wild,') - 0.08)
    def cam(self, t):
        tw = self.tswitch()
        dx, dy, dr = self.shake(t)
        if t >= tw:
            return Hook.z0, Hook.focus[0] + dx, Hook.focus[1] + dy, dr
        p = 1 - ease_out(t / 0.32)
        return 1.24 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1060 + dy, 2.0 * p + dr

SCENES = [Hook, Saved, Question, Steel1913, SlowSales, Bought, SoldOut, OneHour, Sales, Secret, Outro]
