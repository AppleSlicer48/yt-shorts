import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import pegboard, ARM_LIGHT, CX, CY, plate_img, grain_map, stone_tex, table_bg
from mw_scenes import glow, stamp_sprite, rgb, bench, lab_wall, h2o_sprite, mannequin
from bw_scenes import S, C, OV, keyframes, stamp_in, get_hand, draw_hand, shadow_of

# ====================================================================== props
def lay_sprite(lay):
    sp, x0, y0 = layer_sprite(lay, 2)
    return sp, x0, y0

def with_shadow(img, sp, x, y, blur=14, a=0.45, dx=18, dy=24):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, x - pad + dx, y - pad + dy)
    paste_at(img, sp, x, y)

_GB = {}
def glue_bottle(scale=1.0):
    if scale in _GB:
        return _GB[scale]
    s = scale
    lay = Layer(int(360 * s) + 40, int(760 * s) + 40)
    cx = lay.w / 2
    capsule(lay, (cx, 330 * s), (cx, 640 * s), 120 * s, 120 * s, '#F2F2F0', spec=0.5, shin=40)
    capsule(lay, (cx, 250 * s), (cx, 300 * s), 70 * s, 100 * s, '#EDEDEA', spec=0.5, shin=40)
    capsule(lay, (cx, 150 * s), (cx, 250 * s), 26 * s, 52 * s, '#F08A24', spec=0.6, shin=40)
    capsule(lay, (cx, 40 * s), (cx, 150 * s), 8 * s, 24 * s, '#F08A24', spec=0.6, shin=40)
    sp, x0, y0 = lay_sprite(lay)
    d = ImageDraw.Draw(sp)
    ox, oy = -x0, -y0
    w = 240 * s
    d.rectangle((cx + ox - w / 2 + 4, 400 * s + oy, cx + ox + w / 2 - 4, 590 * s + oy), fill=(214, 40, 44, 255))
    f = font(int(78 * s))
    bb = f.getbbox('GLUE')
    d.text((cx + ox - (bb[2] + bb[0]) / 2, 495 * s + oy - (bb[3] + bb[1]) / 2), 'GLUE', font=f, fill=(255, 255, 255, 255))
    d.rectangle((cx + ox - w / 2 + 4, 412 * s + oy, cx + ox - w / 2 + 30, 578 * s + oy), fill=(255, 255, 255, 50))
    _GB[scale] = (sp, (cx + ox, 40 * s + oy))
    return _GB[scale]

def drop_sprite(r=22):
    lay = Layer(int(r * 3), int(r * 4))
    ellipsoid(lay, (r * 1.5, r * 2.4), r, r * 0.9, 0, '#E9F3F8', spec=0.9, shin=60, amb=0.6)
    capsule(lay, (r * 1.5, r * 0.8), (r * 1.5, r * 2.0), r * 0.15, r * 0.75, '#E9F3F8', spec=0.9, shin=60, amb=0.6)
    sp, _, _ = lay_sprite(lay)
    return sp

def beaker_sprite():
    w, h = 210, 260
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((20, 40, 20 + w, 40 + h), fill=(210, 235, 245, 70), outline=(235, 248, 255, 230), width=6)
    d.rectangle((26, 150, 14 + w, 34 + h), fill=(120, 200, 140, 170))
    d.line([(10, 40), (30 + w, 40)], fill=(235, 248, 255, 230), width=8)
    for k in range(3):
        d.line([(30, 90 + k * 50), (70, 90 + k * 50)], fill=(235, 248, 255, 200), width=4)
    d.polygon([(40, 50), (60, 50), (60, 290), (40, 290)], fill=(255, 255, 255, 60))
    return im

def gunsight_sprite(R=150):
    lay = Layer(int(R * 5), int(R * 2.6))
    cy = R * 1.3
    capsule(lay, (R * 0.6, cy), (R * 4.2, cy), R * 0.45, R * 0.45, '#3A4048', spec=0.5, shin=30)
    capsule(lay, (R * 3.6, cy), (R * 4.3, cy), R * 0.75, R * 0.75, '#30353C', spec=0.5, shin=30)
    capsule(lay, (R * 0.4, cy), (R * 1.0, cy), R * 0.62, R * 0.62, '#30353C', spec=0.5, shin=30)
    capsule(lay, (R * 2.2, cy - R * 0.4), (R * 2.2, cy - R * 0.75), R * 0.22, R * 0.22, '#2A2E34', spec=0.4)
    sp, _, _ = lay_sprite(lay)
    return sp

def lens_overlay(img, cx, cy, R, k):
    if k <= 0:
        return
    Rk = R * ease_back(min(1, k), 1.8)
    ov = OV(img, cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30)
    ov.d.ellipse(ov.box(cx - Rk - 18, cy - Rk - 18, cx + Rk + 18, cy + Rk + 18), fill=(30, 33, 38, 255))
    ov.d.ellipse(ov.box(cx - Rk, cy - Rk, cx + Rk, cy + Rk), fill=(150, 200, 225, 150))
    ov.d.line(ov.pts([(cx - Rk, cy), (cx + Rk, cy)]), fill=(20, 20, 20, 255), width=5)
    ov.d.line(ov.pts([(cx, cy - Rk), (cx, cy + Rk)]), fill=(20, 20, 20, 255), width=5)
    ov.d.ellipse(ov.box(cx - Rk * 0.3, cy - Rk * 0.3, cx + Rk * 0.3, cy + Rk * 0.3), outline=(220, 40, 40, 255), width=5)
    ov.d.ellipse(ov.box(cx - Rk * 0.75, cy - Rk * 0.8, cx - Rk * 0.2, cy - Rk * 0.4), fill=(255, 255, 255, 70))
    ov.commit()

def lab_plate(seed=3):
    arr = lab_wall(seed)
    arr = bench(arr, 1270, 1370)
    return plate_img(vignette(arr, 0.45))

# ====================================================================== scenes
class Hook(S):
    z0, z1 = 1.05, 1.16
    def make_shakes(self):
        return [(self.we('ACCIDENT'), 14, 0.3), (self.we('TWICE'), 22, 0.35)]
    def events(self):
        return [(0.25, 'bloop', 0.6), (self.we('ACCIDENT'), 'thud', 0.8), (self.we('TWICE'), 'thud', 1.0)]
    def plate(self):
        img = lab_plate(4)
        sp, tip = glue_bottle(0.85)
        self.bx, self.by = int(CX - tip[0]), int(680 - tip[1])
        self.tip = (CX, 680)
        with_shadow(img, sp, self.bx, self.by)
        self.drop = drop_sprite(24)
        self.s1 = stamp_sprite('ACCIDENT', 140)
        self.s2 = stamp_sprite('TWICE!', 170, angle=7)
        return img
    def dyn(self, img, t):
        u = clamp01((t - 0.05) / 0.5)
        if u < 1:
            paste_center(img, self.drop, self.tip[0], self.tip[1] - 40 + 900 * u * u, scale=0.4 + 0.6 * clamp01(u * 3))
        tA, tT = self.we('ACCIDENT'), self.we('TWICE')
        if t < tT:
            stamp_in(img, self.s1, CX, 300, t, tA)
        else:
            paste_center(img, self.s1, CX, 300)
            stamp_in(img, self.s2, CX, 520, t, tT)

class Sights(S):
    def events(self):
        return [(self.we('GUN') - 0.05, 'swipe', 0.6)]
    def plate(self):
        img = lab_plate(5)
        sp = gunsight_sprite(140)
        with_shadow(img, sp, int(CX - sp.width / 2), 1270 - sp.height + 40)
        return img
    def dyn(self, img, t):
        pop(img, C('1942  ·  EASTMAN KODAK', 46, dot=(240, 160, 60)), CX, 300, t, 0.1, out_t=self.we('Harry') - 0.2)
        pop(img, C('CHEMIST HARRY COOVER', 46, dot=(240, 160, 60)), CX, 300, t, self.we('Harry') - 0.05, out_t=self.we('World') - 0.2)
        pop(img, C('WORLD WAR II', 50, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 300, t, self.we('World') - 0.05)
        lens_overlay(img, CX, 760, 260, (t - self.we('GUN') + 0.05) / 0.35)

class Everything(S):
    def make_shakes(self):
        return [(self.we('EVERYTHING') + 0.05, 14, 0.3), (self.we('CONTAINERS') + 0.05, 18, 0.4)]
    def events(self):
        return [(0.3, 'splat', 0.5), (self.we('EVERYTHING') + 0.05, 'thud', 0.7), (self.we('CONTAINERS') + 0.05, 'thud', 0.8)]
    def plate(self):
        self.base = lab_plate(6)
        self.beaker = beaker_sprite()
        self.bottle, _ = glue_bottle(0.55)
        lay = Layer(420, 80)
        capsule(lay, (30, 40), (360, 40), 14, 14, '#F2C230', spec=0.5)
        capsule(lay, (360, 40), (400, 40), 14, 3, '#E8C9A0', spec=0.4)
        self.pencil, _, _ = lay_sprite(lay)
        self.drop = drop_sprite(26)
        self.stamp = stamp_sprite('STUCK!', 160)
        return self.base
    def dyn(self, img, t):
        tE, tC = self.we('EVERYTHING'), self.we('CONTAINERS')
        u = ease_back((t - tE) / 0.3, 1.5)
        lift = 0
        if t > tC:
            lift = -260 * ease_out((t - tC) / 0.35) + 10 * math.sin(t * 40)
        objs = [(self.beaker, 250, 1150), (self.bottle, 1040, 1080), (self.pencil, 650, 1240)]
        target = [(510, 1120), (790, 1090), (650, 1220)]
        for (sp, x0, y0), (x1, y1) in zip(objs, target):
            x = x0 + (x1 - x0) * u
            y = y0 + (y1 - y0) * u + (lift if t > tC else 0)
            paste_center(img, sp, x, y)
        dd = clamp01((t - 0.0) / 0.3)
        if dd < 1:
            paste_center(img, self.drop, 650, 300 + 900 * dd * dd)
        elif t < tE:
            ov = OV(img, 560, 1215, 740, 1260)
            ov.d.ellipse(ov.box(570, 1220, 730, 1255), fill=(230, 242, 250, 200))
            ov.commit()
        if t > tC:
            stamp_in(img, self.stamp, CX, 460, t, tC + 0.05)

def trash_can():
    lay = Layer(420, 520)
    capsule(lay, (210, 120), (210, 430), 150, 125, '#8E969F', spec=0.5, shin=30)
    ellipsoid(lay, (210, 95), 170, 34, 0, '#6C737B', spec=0.5)
    ellipsoid(lay, (210, 92), 150, 24, 0, '#2A2D31', spec=0.1)
    sp, _, _ = lay_sprite(lay)
    return sp

class GaveUp(S):
    def make_shakes(self):
        return [(self.we('GAVE') + 0.05, 12, 0.25)]
    def events(self):
        return [(0.05, 'swipe', 0.5), (self.we('GAVE') + 0.05, 'buzzer', 0.6)]
    def plate(self):
        img = lab_plate(7)
        can = trash_can()
        self.can_pos = (CX + 120, 1270 - can.height + 30)
        with_shadow(img, can, *self.can_pos)
        self.lip = (CX + 120 + can.width / 2, 1270 - can.height + 30 + 95)
        self.bottle, _ = glue_bottle(0.5)
        self.stamp = stamp_sprite('REJECTED', 140)
        return img
    def dyn(self, img, t):
        u = clamp01(t / 0.55)
        if u < 1:
            x = 180 + (self.lip[0] - 180) * u
            y = 700 + (self.lip[1] - 700) * u - 420 * math.sin(math.pi * u)
            paste_center(img, self.bottle.rotate(-u * 300, resample=Image.BICUBIC, expand=True), x, y)
        stamp_in(img, self.stamp, CX, 420, t, self.we('GAVE'))

def jet_sprite():
    lay = Layer(1500, 560)
    fill_poly(lay, [(600, 330), (980, 330), (760, 520), (560, 520)], '#6F7984')
    fill_poly(lay, [(160, 280), (290, 280), (180, 70), (110, 70)], '#6F7984')
    capsule(lay, (120, 300), (1250, 300), 70, 110, '#8C96A1', spec=0.6, shin=40)
    capsule(lay, (1250, 300), (1420, 300), 110, 20, '#7D8792', spec=0.6, shin=40)
    ellipsoid(lay, (1060, 215), 170, 75, 0, '#9FD3F2', spec=1.0, shin=60, amb=0.5)
    return lay_sprite(lay)

class Jet(S):
    focus = (CX, 1000)
    def events(self):
        return [(0.05, 'swipe', 0.6)]
    def cam(self, t):
        z, fx, fy, rot = super().cam(t)
        k = ease_in_out((t - self.we('JET') + 0.3) / 0.8)
        return z + 0.45 * k, fx + (980 - fx) * k * 0.7, fy + (880 - fy) * k * 0.7, rot
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#3E7FD0'), (0.6, '#A9D6F2'), (1, '#E4F3FB')])
        img = plate_img(arr)
        rng = np.random.default_rng(2)
        for k in range(6):
            cl = Image.new('RGBA', (500, 200), (0, 0, 0, 0))
            dc = ImageDraw.Draw(cl)
            for j in range(5):
                x, r = 80 + j * 80, 50 + 30 * rng.random()
                dc.ellipse((x - r, 110 - r, x + r, 110 + r), fill=(255, 255, 255, 200))
            paste_center(img, cl.filter(ImageFilter.GaussianBlur(6)), rng.uniform(0, PW), rng.uniform(300, 1700))
        self.jet = jet_sprite()
        return img
    def dyn(self, img, t):
        sp, x0, y0 = self.jet
        X, Y = -150 - 60 * t, 620 + 12 * math.sin(t * 3)
        paste_at(img, sp, int(X + x0), int(Y + y0))
        pop(img, C('1951  ·  KINGSPORT, TENNESSEE', 46, dot=(240, 160, 60)), CX, 300, t, 0.1)
        pop(img, C('JET CANOPY', 46, bg=(140, 210, 255)), 1000, 640, t, self.we('JET'))

def prism_sprite(w=300, h=260, flip=False):
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(10, 10 + h), (10 + w, 10 + h), (10 + w, 10)] if not flip else [(10, 10 + h), (10 + w, 10 + h), (10, 10)]
    d.polygon(pts, fill=(170, 220, 245, 150), outline=(235, 250, 255, 255))
    d.line(pts + [pts[0]], fill=(235, 250, 255, 255), width=6)
    hl = [(pts[0][0] * 0.7 + pts[2][0] * 0.3, pts[0][1] * 0.7 + pts[2][1] * 0.3), (pts[1][0] * 0.4 + pts[2][0] * 0.6, pts[1][1] * 0.4 + pts[2][1] * 0.6)]
    d.line(hl, fill=(255, 255, 255, 160), width=10)
    return im

class Prisms(S):
    def make_shakes(self):
        return [(self.we('STUCK') + 0.02, 16, 0.6)]
    def events(self):
        return [(self.we('chemical'), 'bloop', 0.6), (self.we('PRISMS'), 'thud', 0.6), (self.we('STUCK') + 0.02, 'squeak', 0.6)]
    def plate(self):
        self.pL, self.pR = prism_sprite(flip=False), prism_sprite(flip=True)
        self.drop = drop_sprite(24)
        self.hand = get_hand(420, math.pi + 0.15)
        self.handL = get_hand(420, -0.15)
        self.stamp = stamp_sprite('STUCK FOR GOOD', 120)
        return lab_plate(8)
    def dyn(self, img, t):
        tP, tS = self.we('PRISMS') - 0.25, self.we('STUCK')
        u = ease_in_out((t - tP) / 0.35)
        gap = 220 * (1 - u)
        pull = 0
        if t > tS:
            pull = 8 * math.sin(t * 50) + 14 * ease_out((t - tS) / 0.2)
        cy = 1000
        xl = CX - self.pL.width + 10 - gap / 2 - pull
        xr = CX - 10 + gap / 2 + pull
        tD = self.we('chemical')
        if t < tP + 0.2:
            dd = clamp01((t - tD + 0.3) / 0.35)
            if dd > 0:
                paste_center(img, self.drop, CX, 400 + (cy - 400) * min(1, dd * dd), scale=0.9)
        else:
            ov = OV(img, CX - 26, cy - 140, CX + 26, cy + 140)
            ov.d.rounded_rectangle(ov.box(CX - 14, cy - 120, CX + 14, cy + 125), 10, fill=(240, 250, 255, 200))
            ov.commit()
        paste_at(img, self.pL, int(xl), int(cy - self.pL.height / 2))
        paste_at(img, self.pR, int(xr), int(cy - self.pR.height / 2))
        if t > tS - 0.3:
            k = ease_out((t - tS + 0.3) / 0.3)
            draw_hand(img, self.hand, (xr + self.pR.width - 40 + 300 * (1 - k), cy + 60), 0.2)
            draw_hand(img, self.handL, (xl + 40 - 300 * (1 - k), cy + 60), 0.2)
            stamp_in(img, self.stamp, CX, 520, t, tS + 0.1)
        pop(img, C('FRED JOYNER', 48, dot=(240, 160, 60)), CX, 300, t, self.we('Fred') - 0.05)

class Idea(S):
    def events(self):
        return [(self.we('GLUE') - 0.05, 'ding', 0.7)]
    def plate(self):
        img = lab_plate(9)
        sp, tip = glue_bottle(1.0)
        with_shadow(img, sp, int(CX - tip[0]), int(560 - tip[1]))
        lay = Layer(320, 420)
        sphere(lay, (160, 150), 120, '#FFE58A', spec=0.9, shin=30, amb=0.9)
        capsule(lay, (160, 280), (160, 360), 55, 55, '#9AA1AA', spec=0.6)
        self.bulb, _, _ = lay_sprite(lay)
        return img
    def dyn(self, img, t):
        tG = self.we('realized')
        if t > tG:
            k = ease_back((t - tG) / 0.3, 2)
            glow(img, CX, 330, 230, (255, 230, 120), 0.7 * clamp01(k))
            paste_center(img, self.bulb, CX, 360, scale=max(0.05, k))
        pop(img, C('LATER CALLED: SUPER GLUE', 46, bg=(255, 210, 60)), CX, 1240, t, self.we('GLUE'))

class Water(S):
    def events(self):
        return [(self.we('WATER'), 'sizzle', 0.5), (self.we('AIR'), 'chime', 0.4)]
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#0B2246'), (0.5, '#123D73'), (1, '#071528')])
        img = plate_img(vignette(arr, 0.5))
        self.h2o = h2o_sprite()
        lay = Layer(700, 400)
        ellipsoid(lay, (350, 220), 300, 130, 0, '#E9F3F8', spec=0.9, shin=60, amb=0.55)
        self.drop, _, _ = lay_sprite(lay)
        lay = Layer(700, 400)
        ellipsoid(lay, (350, 220), 300, 130, 0, '#F6EFD8', spec=0.3, shin=20, amb=0.6)
        self.hard, _, _ = lay_sprite(lay)
        d = ImageDraw.Draw(self.hard)
        rng = np.random.default_rng(3)
        for k in range(26):
            x, y = rng.uniform(140, 520), rng.uniform(140, 260)
            d.line([(x, y), (x + rng.normal(0, 40), y + rng.normal(0, 20))], fill=(200, 185, 150, 255), width=4)
        rng = np.random.default_rng(8)
        self.mols = [(rng.uniform(0, PW), rng.uniform(300, 1300), rng.uniform(0, 360), rng.uniform(0, 6.28)) for _ in range(9)]
        return img
    def dyn(self, img, t):
        tW = self.we('WATER')
        h = ease_in_out((t - tW) / 0.5)
        cx, cy = CX, 1000
        if h < 1:
            paste_center(img, self.drop, cx, cy)
        if h > 0:
            paste_center(img, self.hard, cx, cy, alpha=h)
        for k, (x, y, a, ph) in enumerate(self.mols):
            pull = ease_in_out((t - 0.2 - k * 0.12) / 1.6)
            px = x + (cx + (k - 4) * 60 - x) * pull * 0.8
            py = y + (cy - 120 - y) * pull * 0.8
            if t > tW + 0.4:
                continue
            spr = self.h2o.rotate(a + t * 60, resample=Image.BICUBIC, expand=True)
            paste_center(img, spr, px + 8 * math.sin(t * 5 + ph), py, scale=0.7)
        pop(img, C('WATER', 50, bg=(120, 200, 255)), CX, 380, t, self.we('WATER') - 0.4, out_t=self.we('AIR') - 0.2)
        pop(img, C('EVEN MOISTURE IN THE AIR', 46, bg=(120, 200, 255)), CX, 380, t, self.we('AIR') - 0.1)
        pop(img, C('HARDENS!', 50, bg=(255, 210, 60)), CX, 1250, t, tW + 0.4)

def box_sprite_910():
    w, h = 230, 330
    im = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(w, 12), (w + 24, 0), (w + 24, h - 12), (w, h)], fill=(150, 30, 30, 255))
    d.rectangle((0, 12, w, h), fill=(210, 45, 45, 255))
    d.polygon([(0, 12), (24, 0), (w + 24, 0), (w, 12)], fill=(235, 95, 90, 255))
    d.rectangle((14, 70, w - 14, 200), fill=(250, 245, 230, 255))
    f1, f2 = font(40), font(66)
    for txt, f, y in (('EASTMAN', f1, 105), ('910', f2, 165)):
        bb = f.getbbox(txt)
        d.text((w / 2 - (bb[2] + bb[0]) / 2, y - (bb[3] + bb[1]) / 2), txt, font=f, fill=(40, 30, 25, 255))
    return im

class OnSale(S):
    def events(self):
        return [(self.we('sale'), 'cash', 0.6)]
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#F1E3C4'), (1, '#C9B48A')])
        arr = arr * (0.55 + 0.6 * radial(PW, PH, CX, 900, 1400, 1.2))[..., None]
        img = plate_img(vignette(arr, 0.4))
        lay = Layer()
        for y in (880, 1290):
            capsule(lay, (40, y), (PW - 40, y), 22, 22, '#8A5A30', spec=0.3)
        sp, x0, y0 = lay_sprite(lay)
        paste_at(img, sp, x0, y0)
        self.box = box_sprite_910()
        return img
    def dyn(self, img, t):
        for row, y in enumerate((880, 1290)):
            for k in range(4):
                tk = 0.05 + row * 0.25 + k * 0.08
                if t < tk:
                    continue
                s = ease_back((t - tk) / 0.25, 2)
                paste_center(img, self.box, 210 + k * 290, y - 22 - self.box.height / 2 * s, scale=max(0.05, s))
        pop(img, C('1958', 60, dot=(240, 160, 60)), CX, 300, t, self.we('1958') - 0.05)

def tv_frame():
    w, h = 900, 760
    im = Image.new('RGBA', (w + 60, h + 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), 60, fill=(120, 78, 44, 255))
    d.rounded_rectangle((40, 40, 20 + w, 20 + h), 50, fill=(140, 92, 52, 255))
    d.rounded_rectangle((90, 90, w - 170, h - 30), 70, fill=(0, 0, 0, 0), outline=(40, 30, 22, 255), width=24)
    for k in range(2):
        d.ellipse((w - 110, 160 + k * 160, w - 30, 240 + k * 160), fill=(60, 45, 30, 255), outline=(200, 170, 120, 255), width=6)
    d.line([(200, 30 + h), (160, h + 140)], fill=(60, 40, 25, 255), width=14)
    d.line([(w - 140, 30 + h), (w - 100, h + 140)], fill=(60, 40, 25, 255), width=14)
    return im, (110, 110, w - 190, h - 50)

class Lift(S):
    def make_shakes(self):
        return [(self.we('LIFT') + 0.05, 10, 0.3)]
    def events(self):
        return [(self.we('drop'), 'bloop', 0.6), (self.we('LIFT') + 0.05, 'riser', 0.5)]
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#3B2A20'), (1, '#140D09')])
        arr = arr * (0.5 + 0.7 * radial(PW, PH, CX, 900, 1100, 1.4))[..., None]
        img = plate_img(vignette(arr, 0.4))
        self.tv, self.scr = tv_frame()
        self.tv_pos = (int(CX - self.tv.width / 2), 520)
        lay = Layer(500, 760)
        mannequin(lay, 250, 740, 600)
        self.man, _, _ = lay_sprite(lay)
        return img
    def dyn(self, img, t):
        X, Y = self.tv_pos
        sx0, sy0, sx1, sy1 = [v + o for v, o in zip(self.scr, (X, Y, X, Y))]
        tL = self.we('LIFT')
        rise = -160 * ease_out((t - tL) / 0.6) + (6 * math.sin(t * 8) if t > tL else 0)
        scr = Image.new('RGBA', (int(sx1 - sx0), int(sy1 - sy0)), (190, 200, 205, 255))
        ds = ImageDraw.Draw(scr)
        ds.rectangle((0, scr.height - 90, scr.width, scr.height), fill=(120, 125, 130, 255))
        bx = scr.width / 2
        top = 150 + rise
        ds.rectangle((bx - 170, top - 40, bx + 170, top - 10), fill=(120, 128, 136, 255))
        ds.rectangle((bx - 170, top - 10, bx + 170, top + 18), fill=(150, 158, 166, 255))
        ds.line([(bx - 100, 0), (bx - 100, top - 40)], fill=(60, 60, 60, 255), width=5)
        ds.line([(bx + 100, 0), (bx + 100, top - 40)], fill=(60, 60, 60, 255), width=5)
        m = self.man.resize((int(self.man.width * 0.62), int(self.man.height * 0.62)))
        paste_center(scr, m, bx, top + 18 + m.height / 2 - 30)
        g = scr.convert('L').convert('RGBA')
        a = np.asarray(g, np.float32)
        a[..., :3] *= (0.93 + 0.07 * np.sin(np.arange(a.shape[0]) * 1.2))[:, None, None]
        g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
        img.alpha_composite(g, (int(sx0), int(sy0)))
        paste_at(img, self.tv, X, Y)
        pop(img, C('ONE DROP', 52, bg=(255, 210, 60)), CX, 380, t, self.we('drop') - 0.05)

class Outro(Hook):
    def make_shakes(self):
        return [(self.we('GAVE') + 0.05, 18, 0.35)]
    def events(self):
        return [(self.we('GAVE') + 0.05, 'thud', 0.8), (self.we('on', 't1') + 0.1, 'bloop', 0.5)]
    def plate(self):
        img = super().plate()
        self.s3 = stamp_sprite('GAVE UP?!', 150, angle=-6)
        return img
    def dyn(self, img, t):
        stamp_in(img, self.s3, CX, 330, t, self.we('GAVE'))

SCENES = [Hook, Sights, Everything, GaveUp, Jet, Prisms, Idea, Water, OnSale, Lift, Outro]
