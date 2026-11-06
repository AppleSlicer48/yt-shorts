import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, table_bg
from mw_scenes import glow, stamp_sprite, lab_wall, bench, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of

STEEL = '#C9CED6'
GOLD = (240, 160, 60)

def lay_sprite(lay):
    return layer_sprite(lay, 2)

def with_shadow(img, sp, x, y, blur=14, a=0.45, dx=18, dy=24):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, x - pad + dx, y - pad + dy)
    paste_at(img, sp, x, y)

def desk_plate(seed=5):
    return plate_img(table_bg(seed))

def wall_plate(seed=3, c0='#3A2E26', c1='#140E0A'):
    arr = lab_wall(seed, c0, c1)
    arr = bench(arr, 1250, 1340)
    return plate_img(vignette(arr, 0.45))

# ---------------------------------------------------------------- safety pin
_PIN = {}
def safety_pin(L=700, open_k=0.0, r=13, color=STEEL, hl=None):
    """Horizontal safety pin: coil at left, clasp head at right. open_k 0=closed 1=open."""
    key = (L, round(open_k, 2), r, color, hl)
    if key in _PIN:
        return _PIN[key]
    pad = int(L * 0.25)
    lay = Layer(int(L + pad * 2), int(L * 0.75 + pad))
    cxl, cy = pad + L * 0.08, lay.h * 0.62
    R = L * 0.07
    gap = L * 0.12
    # bottom fixed leg from coil to clasp
    clx = pad + L * 0.95
    capsule(lay, (cxl, cy + R * 0.9), (clx, cy + R * 0.2), r, r, color, spec=0.9, shin=50)
    # coil: two loops
    for loop in range(2):
        ox = loop * r * 1.3
        n = 14
        for k in range(n):
            a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n
            p0 = (cxl + ox - R * math.cos(a0), cy + R * math.sin(a0) * 0.95)
            p1 = (cxl + ox - R * math.cos(a1), cy + R * math.sin(a1) * 0.95)
            capsule(lay, p0, p1, r, r, color, spec=0.9, shin=50)
    # top leg (the pin) rotates about coil top
    ang = -0.05 - 0.55 * open_k
    px, py = cxl + R * 0.2, cy - R * 0.95
    ex, ey = px + math.cos(ang) * L * 0.86, py + math.sin(ang) * L * 0.86
    capsule(lay, (px, py), (ex, ey), r, r * 0.25, color, spec=0.9, shin=50)
    # clasp head
    hx, hy = clx, cy - R * 0.3
    capsule(lay, (hx - L * 0.07, hy - R * 0.95), (hx + L * 0.03, hy - R * 0.95), r * 1.6, r * 1.6, color, spec=0.9, shin=50)
    capsule(lay, (hx + L * 0.03, hy - R * 0.95), (hx + L * 0.05, hy + R * 0.5), r * 1.6, r * 1.6, color, spec=0.9, shin=50)
    capsule(lay, (hx - L * 0.07, hy - R * 1.5), (hx + L * 0.04, hy - R * 1.5), r * 1.2, r * 1.2, color, spec=0.9, shin=50)
    sp, x0, y0 = lay_sprite(lay)
    info = {'coil': (cxl + r * 0.6 - x0, cy - y0), 'clasp': (hx - x0, hy - R - y0), 'tip': (ex - x0, ey - y0)}
    _PIN[key] = (sp, info)
    return _PIN[key]

def straight_pin(L=520, r=8):
    lay = Layer(int(L + 80), 120)
    capsule(lay, (40, 60), (40 + L, 60), r, 1.5, STEEL, spec=0.9, shin=50)
    sphere(lay, (40, 60), r * 3, '#D9433B', spec=0.7, shin=40)
    sp, _, _ = lay_sprite(lay)
    return sp

def money_sprite(seed=0, w=400, h=180):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(170, 198, 150, 255), outline=(70, 100, 62, 255), width=6)
    d.rectangle((14, 14, w - 15, h - 15), outline=(90, 125, 80, 255), width=3)
    d.ellipse((w / 2 - 60, h / 2 - 55, w / 2 + 60, h / 2 + 55), fill=(206, 222, 192, 255), outline=(90, 125, 80, 255), width=4)
    f = font(80); bb = f.getbbox('$')
    d.text((w / 2 - (bb[2] + bb[0]) / 2, h / 2 - (bb[3] + bb[1]) / 2), '$', font=f, fill=(60, 95, 55, 255))
    n = smooth_noise(h, w, 20, seed, 3)
    a = np.asarray(im, np.float32)
    a[..., :3] *= (0.9 + 0.15 * n)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

def paper_sprite(w, h, lines, seed=1, tilt=0):
    arr = vgrad(w, h, [(0, '#F5EBD2'), (1, '#E2D2AE')]) * (0.92 + 0.12 * smooth_noise(h, w, 30, seed, 3))[..., None]
    im = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(170, 140, 90, 255), width=4)
    for (txt, size, y, col) in lines:
        f = font(size, FONT_SERIF)
        bb = f.getbbox(txt)
        d.text((w / 2 - (bb[2] + bb[0]) / 2, y - (bb[3] + bb[1]) / 2), txt, font=f, fill=col)
    return im.rotate(tilt, resample=Image.BICUBIC, expand=True)

# ====================================================================== scenes
class Hook(S):
    z0, z1 = 1.05, 1.15
    def make_shakes(self):
        return [(self.we('$15'), 18, 0.35)]
    def events(self):
        return [(0.15, 'swipe', 0.6), (self.we('pin') , 'ding', 0.6), (self.we('$15'), 'thud', 0.9)]
    def plate(self):
        img = desk_plate(5)
        self.pin = safety_pin(820)
        self.stamp = stamp_sprite('$15 DEBT', 150)
        return img
    def dyn(self, img, t):
        sp, info = self.pin
        k = ease_back(t / 0.4, 1.6)
        y = 900 - 500 * (1 - clamp01(k))
        sh, pad = shadow_of(sp, 16, 0.5)
        paste_at(img, sh, int(CX - sp.width / 2 - pad + 20), int(900 - sp.height / 2 - pad + 30))
        paste_center(img, sp, CX, y, scale=0.6 + 0.4 * clamp01(k))
        glow(img, CX, 900, 520, (255, 220, 160), 0.25 * clamp01(t / 0.5))
        pop(img, C('EVERYDAY OBJECT', 46, dot=GOLD), CX, 330, t, 0.25, out_t=self.we('$15') - 0.15)
        stamp_in(img, self.stamp, CX, 380, t, self.we('$15'))

class Debt(S):
    def make_shakes(self):
        return [(self.we('FIFTEEN'), 12, 0.3)]
    def events(self):
        return [(self.we('Walter') - 0.05, 'pop', 0.5), (self.we('FIFTEEN'), 'thud', 0.8)]
    def plate(self):
        img = wall_plate(4)
        lay = Layer(560, 900)
        mannequin(lay, 280, 880, 860)
        self.man, _, _ = lay_sprite(lay)
        self.note = paper_sprite(420, 300, [('I.O.U.', 80, 90, (60, 40, 30)), ('$15', 110, 205, (190, 40, 40))], 2, tilt=6)
        with_shadow(img, self.man, int(CX - 330 - self.man.width / 2), 1250 - self.man.height + 20)
        return img
    def dyn(self, img, t):
        pop(img, C('1849  ·  NEW YORK', 48, dot=GOLD), CX, 300, t, 0.1, out_t=self.we('Walter') - 0.2)
        pop(img, C('INVENTOR WALTER HUNT', 46, dot=GOLD), CX, 300, t, self.we('Walter') - 0.05)
        tF = self.we('FIFTEEN')
        if t > tF - 0.1:
            k = ease_back((t - tF + 0.1) / 0.35, 1.8)
            paste_center(img, self.note, CX + 230, 820 + 8 * math.sin(t * 3), scale=max(0.05, k))
        if t > self.we('BACK') - 0.1:
            pop(img, C('PAY IT BACK', 50, bg=(200, 60, 50), fg=(255, 255, 255)), CX + 230, 560, t, self.we('BACK') - 0.1)

def wire_points(x0, x1, y, k, n=160, seg=0.0):
    pts = []
    for i in range(n + 1):
        u = i / n
        x = x0 + (x1 - x0) * u
        amp = 70 * k * math.sin(math.pi * u) ** 0.5
        pts.append((x + amp * 0.6 * math.cos(u * 34 * k + seg), y + amp * math.sin(u * 34 * k + seg)))
    return pts

class Wire(S):
    def events(self):
        return [(self.we('WIRE') - 0.05, 'pop', 0.6), (self.we('twisting'), 'rattle', 0.5)]
    def plate(self):
        self.hand = get_hand(420, math.pi + 0.15)
        self.handL = get_hand(420, -0.15)
        return desk_plate(6)
    def dyn(self, img, t):
        tW, tT = self.we('WIRE'), self.we('twisting')
        if t > tW - 0.15:
            k = ease_in_out((t - tT) / 1.0) if t > tT else 0.0
            lift = 260 * (1 - ease_out((t - tW + 0.15) / 0.35))
            x0, x1, y = 230, PW - 230, 900 - lift
            pts = wire_points(x0, x1, y, k, seg=t * 2)
            ov = OV(img, 0, y - 200, PW, y + 260)
            ov.d.line(ov.pts([(x + 10, yy + 22) for x, yy in pts]), fill=(0, 0, 0, 90), width=20, joint='curve')
            ov.d.line(ov.pts(pts), fill=(150, 120, 70, 255), width=16, joint='curve')
            ov.d.line(ov.pts([(x - 2, yy - 4) for x, yy in pts]), fill=(240, 220, 160, 255), width=5, joint='curve')
            ov.commit()
            if t > tT - 0.2:
                draw_hand(img, self.hand, (x1 + 20, y + 50), 0.2)
                draw_hand(img, self.handL, (x0 - 20, y + 50), 0.2)
        pop(img, C('AS THE STORY GOES...', 46, dot=GOLD), CX, 300, t, 0.1)
        if t > tW:
            pop(img, C('A PIECE OF WIRE', 46, bg=(255, 210, 60)), CX, 470, t, tW)

class Hours(S):
    def events(self):
        return [(0.1, 'tick', 0.6), (self.we('THREE'), 'tick', 0.6), (self.we('HOURS'), 'tick', 0.6), (self.we('brand') - 0.1, 'ding', 0.8)]
    def plate(self):
        img = wall_plate(5)
        R = 300
        face = Image.new('RGBA', (2 * R + 40, 2 * R + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(face)
        c = R + 20
        d.ellipse((c - R, c - R, c + R, c + R), fill=(120, 78, 44, 255))
        d.ellipse((c - R + 30, c - R + 30, c + R - 30, c + R - 30), fill=(246, 238, 220, 255))
        for k in range(12):
            a = k * math.pi / 6
            r0 = R - 60 if k % 3 else R - 85
            d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + (R - 45) * math.sin(a), c - (R - 45) * math.cos(a))], fill=(40, 30, 25, 255), width=10 if k % 3 == 0 else 6)
        self.clock_c = (CX, 760)
        with_shadow(img, face, int(CX - c), int(760 - c))
        self.pin = safety_pin(560)
        return img
    def dyn(self, img, t):
        cx, cy = self.clock_c
        tP = self.we('brand') - 0.1
        spin = ease_in_out((t - 0.1) / max(0.3, tP - 0.2))
        mh = spin * 3 * 2 * math.pi
        hh = math.radians(30 * 0) + spin * 3 * math.pi / 6 * 1.0 + math.radians(300)
        ov = OV(img, cx - 300, cy - 300, cx + 300, cy + 300)
        ov.d.line(ov.pts([(cx, cy), (cx + 160 * math.sin(hh), cy - 160 * math.cos(hh))]), fill=(30, 25, 20, 255), width=18)
        ov.d.line(ov.pts([(cx, cy), (cx + 230 * math.sin(mh), cy - 230 * math.cos(mh))]), fill=(30, 25, 20, 255), width=10)
        ov.d.ellipse(ov.box(cx - 18, cy - 18, cx + 18, cy + 18), fill=(200, 60, 50, 255))
        ov.commit()
        pop(img, C('ABOUT 3 HOURS', 52, bg=(255, 210, 60)), CX, 300, t, self.we('THREE') - 0.05)
        if t > tP:
            sp, _ = self.pin
            k = ease_back((t - tP) / 0.35, 2)
            glow(img, CX, 1180, 330, (255, 230, 150), 0.5 * clamp01(k))
            paste_center(img, sp, CX, 1180, scale=max(0.05, k))

class Ouch(S):
    def make_shakes(self):
        return [(self.we('JAB') + 0.05, 20, 0.35)]
    def events(self):
        return [(0.1, 'swipe', 0.5), (self.we('JAB') + 0.05, 'crack', 0.8)]
    def plate(self):
        self.pin = straight_pin(560)
        self.hand = get_hand(560, math.pi + 0.35)
        self.stamp = stamp_sprite('OUCH!', 170, angle=8)
        return desk_plate(7)
    def dyn(self, img, t):
        tJ = self.we('JAB')
        tip = (CX + 120, 900)
        draw_hand(img, self.hand, (tip[0] + 20, tip[1] - 20 - 20 * (t > tJ) * math.sin(t * 40)), 0.15)
        u = ease_in_out((t - tJ + 0.35) / 0.4)
        L = self.pin.width
        px = tip[0] - L + 40 - 300 * (1 - u)
        paste_at(img, self.pin, int(px), int(tip[1] - self.pin.height / 2 + 40))
        pop(img, C('PLAIN PIN = SHARP END', 46, dot=(220, 60, 50)), CX, 300, t, 0.15)
        if t > tJ:
            stamp_in(img, self.stamp, CX, 560, t, tJ + 0.05)

class Parts(S):
    focus = (CX, 1000)
    def events(self):
        return [(self.we('end'), 'pop', 0.35), (self.we('spring') - 0.1, 'bigpop', 0.35), (self.we('CLASP') - 0.05, 'pop', 0.6), (self.we('covered') + 0.1, 'tick', 0.7)]
    def plate(self):
        self.stamp = None
        return wall_plate(6, '#24464A', '#0C1A1A')
    def dyn(self, img, t):
        tC, tK, tS = self.we('COIL'), self.we('CLASP'), self.we('spring')
        tX = self.we('covered') + 0.1
        ok = 0.0
        if t > tS - 0.1 and t < tK:
            ok = 0.5 * math.sin(math.pi * clamp01((t - tS + 0.1) / 0.5))
        if t > tK:
            ok = 0.6 * (1 - ease_in_out((t - tK) / max(0.3, tX - tK)))
        sp, info = safety_pin(900, round(ok * 20) / 20)
        x0, y0 = int(CX - sp.width / 2), int(900 - sp.height / 2)
        with_shadow(img, sp, x0, y0)
        cxp, cyp = x0 + info['coil'][0], y0 + info['coil'][1]
        kxp, kyp = x0 + info['clasp'][0], y0 + info['clasp'][1]
        if t > tC:
            k = ease_out((t - tC) / 0.3)
            ov = OV(img, cxp - 130, cyp - 130, cxp + 130, cyp + 130)
            ov.d.ellipse(ov.box(cxp - 105 * k, cyp - 105 * k, cxp + 105 * k, cyp + 105 * k), outline=(255, 210, 60, 255), width=10)
            ov.commit()
            pop(img, C('COIL = SPRING', 46, bg=(255, 210, 60)), max(300, cxp + 60), cyp - 330, t, tC)
        if t > tK:
            k = ease_out((t - tK) / 0.3)
            ov = OV(img, kxp - 140, kyp - 140, kxp + 140, kyp + 140)
            ov.d.ellipse(ov.box(kxp - 115 * k, kyp - 115 * k, kxp + 115 * k, kyp + 115 * k), outline=(120, 220, 255, 255), width=10)
            ov.commit()
            pop(img, C('CLASP', 50, bg=(120, 200, 255)), min(PW - 220, kxp - 40), kyp + 270, t, tK)

class Safe(S):
    def events(self):
        return [(0.1, 'chime', 0.6), (self.we('more'), 'ding', 0.7)]
    def plate(self):
        img = desk_plate(8)
        sp, _ = safety_pin(640)
        with_shadow(img, sp, int(CX - sp.width / 2), int(980 - sp.height / 2))
        self.hand = get_hand(520, -0.25)
        self.ok = stamp_sprite('SAFE!', 160, color=(40, 160, 80), angle=-6)
        return img
    def dyn(self, img, t):
        k = ease_out(t / 0.4)
        draw_hand(img, self.hand, (CX - 140 - 200 * (1 - k), 920), 0.3)
        stamp_in(img, self.ok, CX, 480, t, self.we('more'))

class Patent(S):
    def make_shakes(self):
        return [(self.we('April'), 14, 0.3)]
    def events(self):
        return [(0.05, 'rustle', 0.6), (self.we('April'), 'thud', 0.9), (self.we('PATENT'), 'pop', 0.5)]
    def plate(self):
        img = desk_plate(9)
        self.doc = paper_sprite(760, 960, [('UNITED STATES', 54, 110, (60, 40, 30)), ('PATENT', 96, 210, (60, 40, 30)),
                                           ('No. 6,281', 74, 340, (150, 40, 40))], 4)
        dd = ImageDraw.Draw(self.doc)
        # sketch of a pin on the document
        cx, cy = 380, 620
        dd.ellipse((cx - 260, cy - 30, cx - 200, cy + 30), outline=(60, 50, 40), width=6)
        dd.line([(cx - 210, cy - 26), (cx + 230, cy - 46)], fill=(60, 50, 40), width=6)
        dd.line([(cx - 210, cy + 28), (cx + 250, cy + 10)], fill=(60, 50, 40), width=6)
        dd.rectangle((cx + 210, cy - 60, cx + 270, cy + 20), outline=(60, 50, 40), width=6)
        for k in range(5):
            dd.line([(140, 760 + k * 34), (620 - (k == 4) * 200, 760 + k * 34)], fill=(140, 120, 95), width=5)
        with_shadow(img, self.doc, int(CX - self.doc.width / 2), 300)
        self.stamp = stamp_sprite('APRIL 10, 1849', 104, color=(200, 40, 40), angle=-8)
        return img
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 1060, t, self.we('April'))

class Sold(S):
    def make_shakes(self):
        return [(self.we('just'), 12, 0.3)]
    def events(self):
        return [(self.we('sold'), 'swipe', 0.6), (self.we('just'), 'cash', 0.9)]
    def plate(self):
        self.bills = [money_sprite(k) for k in range(6)]
        self.stamp = stamp_sprite('SOLD', 170, angle=-8)
        self.doc = paper_sprite(380, 480, [('PATENT', 54, 70, (60, 40, 30)), ('RIGHTS', 54, 140, (60, 40, 30))], 4, tilt=-8)
        return wall_plate(7)
    def dyn(self, img, t):
        tS, tM = self.we('sold'), self.we('just')
        u = ease_in_out((t - tS) / 0.5)
        paste_center(img, self.doc, CX - 40 - 250 * u, 760)
        for k, b in enumerate(self.bills):
            tk = tM - 0.25 + k * 0.06
            if t < tk:
                continue
            q = ease_out((t - tk) / 0.25)
            paste_center(img, b.rotate(-10 + 5 * k, expand=True, resample=Image.BICUBIC), CX + 220 + 10 * k, 300 + (1080 - 40 * k - 300) * q)
        stamp_in(img, self.stamp, CX - 290, 640, t, tS + 0.2)
        pop(img, C('$400', 64, bg=(120, 200, 120)), CX + 230, 340, t, tM)

class Times(S):
    def events(self):
        return [(self.we('26'), 'riser', 0.5), (self.we('TIMES'), 'thud', 0.8)]
    def plate(self):
        return wall_plate(8, '#1E2A40', '#0A0F18')
    def dyn(self, img, t):
        base = 1250
        g = ease_out((t - 0.05) / 0.5)
        hb = 640 * ease_in_out((t - self.we('26') + 0.2) / 0.6)
        ov = OV(img, 0, 200, PW, base + 10)
        ov.d.rounded_rectangle(ov.box(260, base - 32 * g, 500, base), 12, fill=(220, 80, 70, 255))
        if hb > 2:
            ov.d.rounded_rectangle(ov.box(780, base - hb, 1020, base), 12, fill=(110, 200, 120, 255))
        ov.d.line(ov.pts([(160, base), (PW - 160, base)]), fill=(240, 240, 240, 255), width=8)
        ov.commit()
        pop(img, C('OWED $15', 44, bg=(220, 80, 70), fg=(255, 255, 255)), 380, base - 110, t, 0.1)
        if hb > 2:
            pop(img, C('GOT $400', 44, bg=(110, 200, 120)), 900, base - hb - 80, t, self.we('26') - 0.1)
        pop(img, C('26× MORE', 66, bg=(255, 210, 60)), CX, 300, t, self.we('TIMES'))

def sewing_machine():
    lay = Layer(1000, 760)
    col = '#2B2F36'
    fill_poly(lay, [(80, 600), (920, 600), (900, 700), (100, 700)], '#6B4A30')
    capsule(lay, (220, 560), (220, 250), 70, 60, col, spec=0.6, shin=40)
    capsule(lay, (220, 210), (760, 210), 75, 75, col, spec=0.6, shin=40)
    capsule(lay, (760, 210), (760, 380), 55, 45, col, spec=0.6, shin=40)
    capsule(lay, (180, 560), (800, 560), 40, 40, col, spec=0.6, shin=40)
    capsule(lay, (760, 380), (760, 500), 8, 4, STEEL, spec=0.9, shin=50)
    sphere(lay, (120, 260), 90, '#8A6A3A', spec=0.6)
    sp, _, _ = lay_sprite(lay)
    d = ImageDraw.Draw(sp)
    for x in range(300, 700, 70):
        d.ellipse((x, 170, x + 30, 200), fill=(210, 170, 80, 255))
    return sp

class Twist(S):
    def make_shakes(self):
        return [(self.we('FIGHT'), 18, 0.35)]
    def events(self):
        return [(0.05, 'scratch', 0.7), (self.we('SEWING') - 0.05, 'pop', 0.6), (self.we('FIGHT'), 'boom', 0.7), (self.we('Elias') - 0.05, 'pop', 0.5)]
    def plate(self):
        img = wall_plate(9)
        sp = sewing_machine()
        self.sm = sp
        self.stamp = stamp_sprite('PATENT FIGHT', 120, angle=-7)
        return img
    def dyn(self, img, t):
        pop(img, C('THE TWIST', 56, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 300, t, 0.05, out_t=self.we('SEWING') - 0.2)
        tSw = self.we('SEWING') - 0.1
        if t > tSw:
            k = ease_back((t - tSw) / 0.4, 1.6)
            sh, pad = shadow_of(self.sm, 16, 0.45)
            y = 1250 - self.sm.height + 10
            paste_at(img, sh, int(CX - self.sm.width / 2 - pad + 20), int(y - pad + 26))
            paste_center(img, self.sm, CX, y + self.sm.height / 2 + 300 * (1 - clamp01(k)))
            pop(img, C("ONE OF THE WORLD'S FIRST SEWING MACHINES", 38, dot=GOLD), CX, 300, t, tSw, out_t=self.we('Elias') - 0.2)
        tF = self.we('FIGHT')
        stamp_in(img, self.stamp, CX, 520, t, tF)
        if t > self.we('Elias') - 0.05:
            pop(img, C('VS. ELIAS HOWE', 50, bg=(255, 210, 60)), CX, 300, t, self.we('Elias') - 0.05)

class Outro(Hook):
    def make_shakes(self):
        return [(self.we('fifteen'), 18, 0.35)]
    def events(self):
        return [(0.15, 'swipe', 0.6), (self.we('fifteen'), 'thud', 0.9)]
    def plate(self):
        img = super().plate()
        self.s3 = stamp_sprite('$15', 190, angle=-6)
        return img
    def dyn(self, img, t):
        sp, info = self.pin
        sh, pad = shadow_of(sp, 16, 0.5)
        paste_at(img, sh, int(CX - sp.width / 2 - pad + 20), int(900 - sp.height / 2 - pad + 30))
        paste_center(img, sp, CX, 900)
        glow(img, CX, 900, 520, (255, 220, 160), 0.25)
        pop(img, C('STILL USED EVERY DAY', 46, dot=GOLD), CX, 330, t, self.we('every') - 0.05, out_t=self.we('fifteen') - 0.15)
        stamp_in(img, self.s3, CX, 380, t, self.we('fifteen'))

SCENES = [Hook, Debt, Wire, Hours, Ouch, Parts, Safe, Patent, Sold, Times, Twist, Outro]
