"""Post-it Notes came from a glue that failed (2026-11-15)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish
from mw_scenes import glow, stamp_sprite, lab_wall, bench, mannequin
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import ground_shadow

RED = (214, 50, 44)
YEL = (255, 210, 60)
BLUE = (40, 120, 200)
GREEN = (60, 170, 90)
NOTE = (255, 226, 74)
INK = (40, 52, 110)

class Base(S):
    focus = (CX, 1100)
    z0, z1 = 1.18, 1.24

# ====================================================================== plates
_PL = {}
def wall_plate(c0='#F2B266', c1='#B5562C', seed=3, spot=(CX, 900, 1300)):
    key = (c0, c1, seed, spot)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.9 + 0.1 * smooth_noise(PH, PW, 110, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, spot[0], spot[1], spot[2], 1.3))[..., None]
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    _PL[key] = img
    return img.copy()

def lab_plate():
    if 'lab' in _PL:
        return _PL['lab'].copy()
    arr = lab_wall(5, '#2E4A5A', '#0E1A22', (CX, 900, 1300))
    arr = bench(arr, 1330, 1430)
    img = plate_img(vignette(arr, 0.4))
    _PL['lab'] = img
    return img.copy()

def church_plate():
    if 'church' in _PL:
        return _PL['church'].copy()
    arr = vgrad(PW, PH, [(0, '#5B3A6E'), (1, '#1E1028')])
    arr = arr * (0.88 + 0.12 * smooth_noise(PH, PW, 90, 21, 3))[..., None]
    img = to_img(arr).convert('RGBA')
    ov = OV(img, 0, 0, PW, PH)
    for x in (200, PW - 200):
        ov.d.rounded_rectangle((x - 120, 150, x + 120, 900), 120, fill=(255, 214, 140, 70))
        ov.d.rounded_rectangle((x - 96, 176, x + 96, 880), 96, fill=(255, 226, 170, 60))
        ov.d.line([(x, 176), (x, 880)], fill=(60, 30, 70, 120), width=8)
        ov.d.line([(x - 96, 520), (x + 96, 520)], fill=(60, 30, 70, 120), width=8)
    ov.commit()
    arr = to_arr(img) * (0.55 + 0.6 * radial(PW, PH, CX, 900, 1300, 1.3))[..., None]
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    _PL['church'] = img
    return img.copy()

def desk(img, y, col=(150, 96, 52)):
    ov = OV(img, 0, y - 10, PW, PH)
    ov.d.rectangle((0, 10, PW, PH - y + 10), fill=col + (255,))
    ov.d.rectangle((0, 10, PW, 34), fill=tuple(min(255, int(c * 1.2)) for c in col) + (255,))
    for gy in range(90, PH - int(y), 120):
        ov.d.line([(0, gy), (PW, gy + 10)], fill=tuple(int(c * 0.8) for c in col) + (255,), width=4)
    ov.commit()

# ====================================================================== sticky notes
_NT = {}
def note_sprite(s, col=NOTE, peel=0.0, scribble=0, corner='br'):
    """Square sticky note (s px). peel 0..1 folds the chosen corner up toward the viewer."""
    pq = round(peel / 0.02) * 0.02
    key = (int(s), col, pq, scribble, corner)
    if key in _NT:
        return _NT[key]
    ss = 2
    S2 = int(s * ss)
    im = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dd = pq * S2 * 0.7
    face = [(0, 0), (S2, 0), (S2, S2 - dd), (S2 - dd, S2), (0, S2)] if dd > 1 else [(0, 0), (S2, 0), (S2, S2), (0, S2)]
    d.polygon(face, fill=col + (255,))
    top = tuple(int(c * 0.93) for c in col)
    d.rectangle((0, 0, S2, int(S2 * 0.16)), fill=top + (255,))
    grad = Image.new('L', (1, S2))
    grad.putdata([int(40 * (y / S2) ** 2) for y in range(S2)])
    shade = Image.new('RGBA', (S2, S2), (120, 80, 0, 0))
    shade.putalpha(grad.resize((S2, S2)))
    mask = im.getchannel('A')
    sh2 = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
    sh2.paste(shade, (0, 0), mask)
    im.alpha_composite(sh2)
    d = ImageDraw.Draw(im)
    if scribble:
        rng = np.random.default_rng(scribble)
        for j in range(3):
            y = S2 * (0.32 + j * 0.16)
            pts = []
            x0, x1 = S2 * 0.14, S2 * (0.86 - 0.18 * rng.random())
            for k in range(26):
                x = x0 + (x1 - x0) * k / 25
                pts.append((x, y + S2 * 0.018 * math.sin(k * 1.7 + j) + S2 * 0.01 * rng.standard_normal()))
            d.line(pts, fill=INK + (230,), width=max(3, int(S2 * 0.016)), joint='curve')
    if dd > 1:
        flap = [(S2, S2 - dd), (S2 - dd, S2), (S2 - dd, S2 - dd)]
        shl = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
        ImageDraw.Draw(shl).polygon([(S2, S2 - dd), (S2 - dd, S2), (S2 - dd * 1.08, S2 - dd * 1.08)], fill=(0, 0, 0, 90))
        im.alpha_composite(shl.filter(ImageFilter.GaussianBlur(max(2, dd * 0.06))))
        lite = tuple(min(255, int(c * 1.06 + 12)) for c in col)
        ImageDraw.Draw(im).polygon(flap, fill=lite + (255,))
        ImageDraw.Draw(im).line([flap[0], flap[1]], fill=tuple(int(c * 0.8) for c in col) + (255,), width=max(2, int(S2 * 0.006)))
    im = im.resize((int(s), int(s)), Image.LANCZOS)
    if corner == 'bl':
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    _NT[key] = im
    return im

def put_note(img, s, cx, cy, ang=0.0, peel=0.0, scribble=0, col=NOTE, sh=0.38, lift=0.0, corner='br'):
    sp = note_sprite(s, col, peel, scribble, corner)
    if abs(ang) > 0.05:
        sp = sp.rotate(-ang, resample=Image.BICUBIC, expand=True)
    shs, pad = shadow_of(sp, max(5, int(s * 0.03)), sh)
    paste_at(img, shs, cx - sp.width / 2 - pad + s * (0.03 + lift * 0.08), cy - sp.height / 2 - pad + s * (0.04 + lift * 0.1))
    paste_at(img, sp, cx - sp.width / 2, cy - sp.height / 2)

def local_to_world(cx, cy, s, ang, lx, ly):
    """Note-local point (0..s, origin top-left) -> plate coords for a note centred at cx,cy rotated ang deg (clockwise)."""
    a = math.radians(ang)
    x, y = lx - s / 2, ly - s / 2
    return cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)

def pad_sprite(s, n=10, col=NOTE):
    key = ('pad', s, n, col)
    if key in _NT:
        return _NT[key]
    th = int(s * 0.03) * n // 3 + 8
    im = Image.new('RGBA', (s + 20, s + th + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((10, 10, 10 + s, 10 + s + th), fill=tuple(int(c * 0.82) for c in col) + (255,))
    for j in range(0, th, 6):
        d.line([(10, 10 + s + j), (10 + s, 10 + s + j)], fill=tuple(int(c * 0.7) for c in col) + (255,), width=2)
    im.alpha_composite(note_sprite(s, col), (10, 10))
    _NT[key] = im
    return im

# ====================================================================== other props
def glue_bottle(h=520):
    w = int(h * 0.46)
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bx0, by0, bx1, by1 = 20, 20 + h * 0.34, 20 + w, 20 + h
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=int(w * 0.22), fill=(246, 246, 242, 255))
    for k in range(int(w * 0.35)):
        a = int(60 * (k / (w * 0.35)))
        d.line([(bx1 - k, by0 + 30), (bx1 - k, by1 - 30)], fill=(150, 150, 160, 60 - a))
    d.polygon([(20 + w * 0.22, by0 + 6), (20 + w * 0.78, by0 + 6), (20 + w * 0.6, 20 + h * 0.14), (20 + w * 0.4, 20 + h * 0.14)], fill=(240, 120, 30, 255))
    d.polygon([(20 + w * 0.46, 20 + h * 0.14), (20 + w * 0.54, 20 + h * 0.14), (20 + w * 0.51, 20), (20 + w * 0.49, 20)], fill=(240, 120, 30, 255))
    ly0 = by0 + (by1 - by0) * 0.25
    d.rectangle((bx0 + 14, ly0, bx1 - 14, ly0 + (by1 - by0) * 0.42), fill=(40, 120, 200, 255))
    f = font(int(w * 0.24))
    bb = f.getbbox('GLUE')
    d.text((20 + w / 2 - (bb[2] + bb[0]) / 2, ly0 + (by1 - by0) * 0.21 - (bb[3] + bb[1]) / 2), 'GLUE', font=f, fill=(255, 255, 255, 255))
    return im

_WB = {}
def wood_block(w, h, seed=3, base='#C98B4E', dark='#8A5426'):
    key = (w, h, seed)
    if key not in _WB:
        tex = to_img(wood(w, h, base, dark, seed=seed, stretch=14, rings=4, contrast=0.45)).convert('RGBA')
        d = ImageDraw.Draw(tex)
        d.rectangle((0, 0, w - 1, h - 1), outline=(90, 50, 20, 255), width=5)
        d.rectangle((0, 0, w, 10), fill=(230, 170, 110, 255))
        _WB[key] = tex
    return _WB[key]

def book_closed(w=520, h=700, col=(140, 30, 40)):
    im = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, 15 + w, 15 + h), 22, fill=col + (255,))
    d.rectangle((15 + w - 34, 30, 15 + w - 6, 15 + h - 15), fill=(245, 236, 210, 255))
    d.rectangle((15, 15, 70, 15 + h), fill=tuple(int(c * 0.7) for c in col) + (255,))
    f = font(int(w * 0.17))
    bb = f.getbbox('HYMNS')
    cx = 15 + (w + 40) / 2 - 10
    d.rounded_rectangle((cx - (bb[2] - bb[0]) / 2 - 24, 90, cx + (bb[2] - bb[0]) / 2 + 24, 110 + bb[3] - bb[1] + 30), 14, outline=(230, 190, 90, 255), width=8)
    d.text((cx - (bb[2] + bb[0]) / 2, 115 - bb[1]), 'HYMNS', font=f, fill=(240, 200, 100, 255))
    return im

def book_open(w=1000, h=640, col=(140, 30, 40)):
    im = Image.new('RGBA', (w + 40, h + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 30, w + 30, h + 50), 26, fill=col + (255,))
    cx = (w + 40) / 2
    for side in (-1, 1):
        x0, x1 = (30, cx - 6) if side < 0 else (cx + 6, w + 10)
        d.polygon([(x0, 40), (x1, 56), (x1, h + 30), (x0, h + 20)] if side < 0 else [(x0, 56), (x1, 40), (x1, h + 20), (x0, h + 30)], fill=(250, 243, 222, 255))
        for k in range(9):
            y = 120 + k * 56
            xa, xb = x0 + 50, x1 - 50
            d.line([(xa, y), (xb, y)], fill=(120, 110, 100, 255), width=6)
            if k % 3 == 1:
                for nx in range(int(xa) + 30, int(xb) - 20, 90):
                    d.ellipse((nx - 12, y - 20, nx + 12, y - 2), fill=(40, 36, 40, 255))
                    d.line([(nx + 10, y - 12), (nx + 10, y - 60)], fill=(40, 36, 40, 255), width=5)
    d.line([(cx, 50), (cx, h + 30)], fill=(150, 130, 110, 255), width=6)
    return im

def slip_sprite(w=90, h=300, col=(252, 252, 246)):
    im = Image.new('RGBA', (w, h), col + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(200, 200, 190, 255), width=3)
    return im

def music_note(size=90, col=(255, 236, 170)):
    im = Image.new('RGBA', (size, int(size * 1.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = size * 0.22
    d.ellipse((4, size * 1.3 - 2 * r - 6, 4 + 2.6 * r, size * 1.3 - 6), fill=col + (255,))
    d.line([(4 + 2.5 * r, size * 1.3 - r - 6), (4 + 2.5 * r, 6)], fill=col + (255,), width=int(size * 0.09))
    d.polygon([(4 + 2.5 * r, 6), (size - 6, size * 0.3), (size - 6, size * 0.5), (4 + 2.5 * r, size * 0.24)], fill=col + (255,))
    return im

def qmark(size=150, col=(255, 255, 255)):
    return text_img('?', size, fill=col, stroke=10, stroke_fill=(20, 20, 30), shadow_px=4)

def shop_sprite(w=470, h=420, awning=(214, 50, 44)):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((20, 80, w - 20, h - 10), fill=(236, 220, 196, 255), outline=(90, 70, 60, 255), width=6)
    n = 6
    for k in range(n):
        x0 = 10 + k * (w - 20) / n
        c = awning if k % 2 == 0 else (250, 250, 250)
        d.polygon([(x0, 40), (x0 + (w - 20) / n, 40), (x0 + (w - 20) / n, 130), (x0, 130)], fill=c + (255,))
        d.ellipse((x0, 110, x0 + (w - 20) / n, 150), fill=c + (255,))
    d.rectangle((60, 190, w * 0.55, h - 40), fill=(150, 200, 230, 255), outline=(90, 70, 60, 255), width=6)
    d.rectangle((w * 0.64, 200, w - 60, h - 10), fill=(120, 80, 50, 255))
    for y in (240, 300):
        for x in range(80, int(w * 0.55) - 40, 60):
            d.rectangle((x, y, x + 40, y + 34), fill=NOTE + (255,))
    return im

def door_sprite(w=360, h=760):
    im = Image.new('RGBA', (w + 40, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w + 40, h + 20), fill=(70, 50, 40, 255))
    d.rectangle((20, 20, w + 20, h + 20), fill=(20, 16, 14, 255))
    return im

def door_leaf(w=360, h=740):
    im = Image.new('RGBA', (w, h), (190, 140, 90, 255))
    d = ImageDraw.Draw(im)
    for (y0, y1) in ((40, h * 0.45), (h * 0.52, h - 40)):
        d.rectangle((40, y0, w - 40, y1), outline=(130, 90, 55, 255), width=10)
    d.ellipse((w - 70, h * 0.5 - 18, w - 34, h * 0.5 + 18), fill=(240, 200, 90, 255))
    return im

def check_sprite(R=70, col=GREEN):
    im = Image.new('RGBA', (2 * R + 8, 2 * R + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 2 * R + 4, 2 * R + 4), fill=col + (255,), outline=(255, 255, 255, 255), width=8)
    d.line([(R * 0.55 + 4, R + 4), (R * 0.9 + 4, R * 1.35 + 4), (R * 1.5 + 4, R * 0.65 + 4)], fill=(255, 255, 255, 255), width=int(R * 0.22), joint='curve')
    return im

def motion_marks(img, x, y, ang_deg, t, n=4, L=90, col=(255, 255, 255)):
    ov = OV(img, x - 260, y - 260, x + 260, y + 260)
    for j in range(n):
        a = math.radians(ang_deg + (j - (n - 1) / 2) * 22)
        k = (math.sin(t * 12 + j * 1.3) + 1) / 2
        r0, r1 = 70 + 20 * k, 70 + L + 30 * k
        ov.d.line(ov.pts([(x + math.cos(a) * r0, y + math.sin(a) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1)]),
                  fill=col + (int(140 + 110 * k),), width=12)
    ov.commit()

# ====================================================================== 0: hook
class Hook(Base):
    """Frame 0: a giant sticky note already being peeled off the wall, corner flapping, notes flying."""
    z0, z1 = 1.07, 1.11
    NS = 860
    NC = (CX - 10, 1150)
    def make_shakes(self):
        return [(self.we('glue') - 0.02, 16, 0.32)]
    def events(self):
        return [(0.02, 'tape', 0.7), (0.9, 'rustle', 0.5), (self.we('glue') - 0.02, 'thud', 0.85)]
    def plate(self):
        self.st = stamp_sprite('FAILED GLUE!', 120, color=RED, angle=-6)
        self.hand = get_hand(620, -2.25)
        img = wall_plate('#3C7FC0', '#173B66', 7, (CX, 1100, 1300))
        rng = np.random.default_rng(15)
        for (x, y) in ((150, 520), (1140, 470), (120, 1900), (1170, 1960), (640, 2160), (330, 2140), (980, 2150), (90, 1150), (1210, 1250)):
            put_note(img, 230, x, y, float(rng.uniform(-18, 18)), scribble=int(rng.integers(1, 99)), sh=0.3)
        return img
    def hero(self, img, t):
        ang = -4 + 3.5 * math.sin(2.1 * t + 0.6)
        peel = 0.46 + 0.14 * math.sin(3.4 * t)
        cx, cy = self.NC
        s = self.NS
        put_note(img, s, cx, cy, ang, peel, scribble=7, sh=0.45)
        dd = peel * s * 0.7
        tip = local_to_world(cx, cy, s, ang, s - dd * 0.98, s - dd * 0.98)
        motion_marks(img, tip[0] + 40, tip[1] + 30, 20, t)
        draw_hand(img, self.hand, (tip[0] + 25, tip[1] + 25), 0.25)
        for j, (x0, ph, sz) in enumerate(((180, 0.0, 200), (1120, 1.7, 220), (240, 3.3, 170))):
            u = ((t * 0.55 + ph / 6.28) % 1.0)
            y = 760 + 900 * u
            x = x0 + 60 * math.sin(t * 3 + ph)
            put_note(img, sz, x, y, 35 * math.sin(t * 4 + ph) + 20, peel=0.2, sh=0.3, lift=0.6)
    def dyn(self, img, t):
        self.hero(img, t)
        stamp_in(img, self.st, CX, 1960, t, self.we('glue') - 0.02)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, CY + dy, dr

# ====================================================================== 1: super strong glue
class StrongGlue(Base):
    def make_shakes(self):
        return [(self.we('1968,'), 12, 0.28), (self.we('strong'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1968,'), 'thud', 0.7), (self.we('Spencer') - 0.03, 'pop', 0.5),
                (self.we('make'), 'squeak', 0.5), (self.we('strong'), 'boom', 0.6)]
    def plate(self):
        self.st = stamp_sprite('1968', 150, color=BLUE, angle=-7)
        self.bottle = glue_bottle(640).rotate(-150, resample=Image.BICUBIC, expand=True)
        self.bsh = shadow_of(self.bottle, 14, 0.4)
        self.hand = get_hand(560, 0.25)
        return lab_plate()
    def dyn(self, img, t):
        tS, tM = self.we('strong'), self.we('make')
        bw, bh = 640, 230
        b1 = wood_block(bw, bh, 3)
        y_bot = 1330 - bh
        sh, pad = shadow_of(b1, 14, 0.45)
        paste_at(img, sh, CX - bw / 2 - pad + 16, y_bot - pad + 24)
        paste_at(img, b1, CX - bw / 2, y_bot)
        g = clamp01((t - tM) / 0.8)
        if g > 0:
            ov = OV(img, CX - 300, y_bot - 40, CX + 300, y_bot + 40)
            ov.d.ellipse(ov.box(CX - 260 * g, y_bot - 16, CX + 260 * g, y_bot + 22), fill=(250, 250, 245, 255))
            ov.d.ellipse(ov.box(CX - 200 * g, y_bot - 14, CX - 40 * g, y_bot - 2), fill=(255, 255, 255, 255))
            ov.commit()
        if t < tS - 0.15:
            bx, by = CX + 120, 760 + 10 * math.sin(t * 9)
            paste_at(img, self.bsh[0], bx - self.bottle.width / 2 - self.bsh[1] + 20, by - self.bottle.height / 2 - self.bsh[1] + 30)
            paste_at(img, self.bottle, bx - self.bottle.width / 2, by - self.bottle.height / 2)
            tipx, tipy = bx - 175, by + 150
            k = (t * 2.2) % 1.0
            ov = OV(img, tipx - 60, tipy - 20, tipx + 60, y_bot + 10)
            ov.d.line(ov.pts([(tipx, tipy), (tipx + (CX - tipx) * 0.2, y_bot)]), fill=(250, 250, 245, 255), width=20)
            ov.d.ellipse(ov.box(tipx - 18, tipy + (y_bot - tipy) * k - 18, tipx + 18, tipy + (y_bot - tipy) * k + 18), fill=(255, 255, 255, 255))
            ov.commit()
        dk = clamp01((t - (tS - 0.15)) / 0.15)
        yt = (y_bot - bh - 10) - 900 * (1 - dk) ** 2
        if t > tS - 0.3:
            b2 = wood_block(bw, bh, 8)
            paste_at(img, b2, CX - bw / 2, yt)
            if dk >= 1:
                draw_hand(img, self.hand, (CX - 120, yt + 40), 0.0)
                glow(img, CX, y_bot, 520, (255, 240, 200), 0.5 * clamp01(1 - (t - tS) / 0.5))
        stamp_in(img, self.st, CX, 1760, t, self.we('1968,'))
        pop(img, C('CHEMIST SPENCER SILVER', 62, bg=YEL), CX, 330, t, self.we('Spencer') - 0.05, out_t=tS - 0.30)
        pop(img, C('SUPER STRONG GLUE', 80, bg=(255, 255, 255)), CX, 330, t, tS - 0.05)

# ====================================================================== 2: weak glue, peeled right off
class WeakGlue(Base):
    def make_shakes(self):
        return [(self.we('opposite:'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('opposite:'), 'buzzer', 0.6), (self.we('weak'), 'squeak', 0.5),
                (self.we('peeled'), 'tape', 0.8)]
    def plate(self):
        self.st = stamp_sprite('WEAK GLUE', 130, color=RED, angle=-6)
        self.hand = get_hand(560, -1.75)
        return lab_plate()
    def dyn(self, img, t):
        tO, tP = self.we('opposite:'), self.we('peeled')
        bw, bh = 640, 230
        y_bot = 1330 - bh
        b1 = wood_block(bw, bh, 3)
        sh, pad = shadow_of(b1, 14, 0.45)
        paste_at(img, sh, CX - bw / 2 - pad + 16, y_bot - pad + 24)
        paste_at(img, b1, CX - bw / 2, y_bot)
        lk = ease_out((t - tO) / 0.6)
        tilt = -14 * lk
        b2 = wood_block(bw, bh, 8).rotate(-tilt, resample=Image.BICUBIC, expand=True)
        yt = (y_bot - bh - 10) - 330 * lk
        cxb = CX + 60 * lk
        paste_at(img, b2, cxb - b2.width / 2, yt - (b2.height - bh) / 2)
        draw_hand(img, self.hand, (cxb + 40, yt + 30), 0.3 * lk)
        if 0 < lk < 0.6:
            ov = OV(img, CX - 320, yt, CX + 320, y_bot + 10)
            for x in (-200, -60, 90, 220):
                ov.d.line(ov.pts([(CX + x, y_bot), (CX + x + 40 * lk, yt + bh + 10)]), fill=(255, 255, 255, int(230 * (1 - lk / 0.6))), width=10)
            ov.commit()
        pk = clamp01((t - tP + 0.1) / 0.5)
        if t > tO + 0.4:
            put_note(img, 360, CX - 120, y_bot - 30 - 260 * ease_out(pk), -10 + 30 * pk, peel=0.1 + 0.5 * pk, sh=0.35, lift=pk)
        pop(img, C('THE EXACT OPPOSITE!', 70, bg=YEL), CX, 330, t, tO - 0.05)
        stamp_in(img, self.st, CX, 1720, t, self.we('weak'))
        pop(img, C('PEELS RIGHT OFF', 64, bg=(255, 255, 255)), CX, 1930, t, tP - 0.05)

# ====================================================================== 3: five years, no use
class NoUse(Base):
    def make_shakes(self):
        return [(self.we('nobody'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5)]
        for k in range(5):
            ev.append((0.15 + k * 0.22, 'tick', 0.5))
        ev += [(self.we('3M,'), 'pop', 0.5), (self.we('nobody'), 'buzzer', 0.6), (self.we('use'), 'pop', 0.45)]
        return ev
    def plate(self):
        img = wall_plate('#E9D7B8', '#9C7A55', 11, (CX, 1000, 1300))
        desk(img, 1380)
        lay = Layer()
        for x in (CX - 380, CX + 380):
            mannequin(lay, x, 1520, 900)
        img = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.q = qmark(190)
        self.bottle = glue_bottle(420)
        self.st = stamp_sprite('NO USE?!', 140, color=RED, angle=-6)
        return img
    def dyn(self, img, t):
        tN, t3 = self.we('nobody'), self.we('3M,')
        paste_at(img, self.bottle, CX - self.bottle.width / 2, 1400 - self.bottle.height + 8 * math.sin(t * 5))
        yrs = min(5, 1 + int(max(0, t - 0.1) / 0.22))
        pop(img, C(f'{yrs} YEAR' + ('S' if yrs > 1 else ''), 96, bg=YEL), CX, 330, t, 0.05, out_t=t3 - 0.30)
        pop(img, C('PITCHED ALL OVER 3M', 66, bg=(255, 255, 255)), CX, 330, t, t3 - 0.05, out_t=tN - 0.30)
        for k, (x, y) in enumerate(((CX - 380, 520), (CX + 380, 520), (CX, 820))):
            pop(img, self.q, x, y + 10 * math.sin(t * 6 + k), t, tN + k * 0.12)
        stamp_in(img, self.st, CX, 1760, t, self.we('use'))

# ====================================================================== 4: Art Fry at choir practice
class Choir(Base):
    def make_shakes(self):
        return [(self.we('up'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Art') - 0.03, 'pop', 0.5), (self.we('up'), 'thud', 0.7),
                (self.we('choir'), 'chime', 0.5)]
    def plate(self):
        img = church_plate()
        lay = Layer()
        mannequin(lay, CX, 1640, 1180)
        img = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.book = book_closed(300, 400).rotate(-8, resample=Image.BICUBIC, expand=True)
        self.note = music_note(100)
        self.st = stamp_sprite('FED UP!', 140, color=RED, angle=-8)
        return img
    def dyn(self, img, t):
        tA, tU, tC = self.we('Art'), self.we('up'), self.we('choir')
        bx, by = CX - 10, 1050 + 6 * math.sin(t * 4)
        paste_at(img, self.book, bx - self.book.width / 2, by - self.book.height / 2)
        for j in range(5):
            u = (t * 0.45 + j / 5) % 1.0
            x = CX + (-420 if j % 2 else 420) + 60 * math.sin(t * 2 + j)
            paste_center(img, self.note, x, 1300 - 900 * u, alpha=clamp01(min(u * 5, (1 - u) * 4)))
        pop(img, C('COWORKER ART FRY', 72, bg=YEL), CX, 330, t, tA - 0.05, out_t=self.we('church') - 0.30)
        pop(img, C('CHURCH CHOIR', 80, bg=(255, 255, 255)), CX, 330, t, self.we('church') - 0.05)
        stamp_in(img, self.st, CX, 1760, t, tU)

# ====================================================================== 5: bookmarks fall out
class FallOut(Base):
    def make_shakes(self):
        return [(self.we('falling'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('bookmarks'), 'pop', 0.5), (self.we('falling'), 'rustle', 0.8),
                (self.we('hymn'), 'buzzer', 0.5)]
    def plate(self):
        img = church_plate()
        self.book = book_open(1060, 640)
        self.slip = slip_sprite(90, 320)
        return img
    def dyn(self, img, t):
        tF = self.we('falling')
        by = 600
        sh, pad = shadow_of(self.book, 16, 0.45)
        paste_at(img, sh, CX - self.book.width / 2 - pad + 18, by - pad + 26)
        paste_at(img, self.book, CX - self.book.width / 2, by)
        for j, (x0, d0, rot) in enumerate(((CX - 280, 0.0, 40), (CX + 60, 0.12, -55), (CX + 300, 0.25, 70))):
            k = clamp01((t - tF + 0.25 - d0) / 1.2)
            y = by - 120 + 1300 * k ** 2
            x = x0 + 120 * math.sin(k * 5 + j)
            sp = self.slip.rotate(rot * k + (j - 1) * 6, resample=Image.BICUBIC, expand=True)
            paste_at(img, sp, x - sp.width / 2, y - sp.height / 2)
        pop(img, C('PAPER BOOKMARKS', 72, bg=YEL), CX, 330, t, self.we('bookmarks') - 0.05, out_t=tF - 0.30)
        pop(img, C('KEPT FALLING OUT!', 72, bg=(255, 255, 255)), CX, 330, t, tF - 0.05)

# ====================================================================== 6: coated with weak glue: stuck, then peeled clean
class Coated(Base):
    def make_shakes(self):
        return [(self.we('stuck,'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('coated'), 'squeak', 0.5), (self.we('stuck,'), 'thud', 0.75),
                (self.we('peeled'), 'tape', 0.8)]
    def plate(self):
        img = church_plate()
        self.book = book_open(1060, 640)
        self.brush_hand = get_hand(520, math.pi + 0.2)
        self.hand = get_hand(560, -1.9)
        self.st = stamp_sprite('STUCK!', 150, color=BLUE, angle=-8)
        return img
    def dyn(self, img, t):
        tCo, tS, tP = self.we('coated'), self.we('stuck,'), self.we('peeled')
        by = 600
        sh, pad = shadow_of(self.book, 16, 0.45)
        paste_at(img, sh, CX - self.book.width / 2 - pad + 18, by - pad + 26)
        paste_at(img, self.book, CX - self.book.width / 2, by)
        s = 360
        if t < tS - 0.2:
            x, y = CX + 10, 640
            put_note(img, s, x, y, -4, col=(252, 252, 246), sh=0.4, lift=0.6)
            gk = clamp01((t - tCo + 0.2) / 0.8)
            ov = OV(img, x - s / 2, y - s / 2, x + s / 2, y - s / 2 + 70)
            ov.d.rectangle(ov.box(x - s / 2 + 4, y - s / 2 + 6, x - s / 2 + 4 + (s - 8) * gk, y - s / 2 + 60), fill=(255, 255, 255, 230))
            ov.d.rectangle(ov.box(x - s / 2 + 4, y - s / 2 + 6, x - s / 2 + 4 + (s - 8) * gk, y - s / 2 + 18), fill=(220, 230, 240, 255))
            ov.commit()
            bx = x - s / 2 + (s - 8) * gk
            ov = OV(img, bx - 40, y - s / 2 - 160, bx + 260, y - s / 2 + 70)
            ov.d.rounded_rectangle(ov.box(bx - 26, y - s / 2 - 10, bx + 26, y - s / 2 + 60), 8, fill=(250, 250, 250, 255))
            ov.d.line(ov.pts([(bx, y - s / 2 - 10), (bx + 200, y - s / 2 - 140)]), fill=(150, 90, 50, 255), width=26)
            ov.commit()
            draw_hand(img, self.brush_hand, (bx + 230, y - s / 2 - 150), 0.3)
        else:
            pk = clamp01((t - tP) / 0.6)
            dk = ease_out((t - (tS - 0.2)) / 0.2)
            x, y = CX - 220, 900 - 380 * ease_out(pk)
            yy = 640 + (y - 640) * dk
            xx = CX + 10 + (x - CX - 10) * dk
            ang = -4 + 18 * pk
            put_note(img, s, xx, yy, ang, peel=0.05 + 0.45 * pk, col=(252, 252, 246), sh=0.4, lift=pk)
            if t > tP:
                dd = (0.05 + 0.45 * pk) * s * 0.7
                tip = local_to_world(xx, yy, s, ang, s - dd, s - dd)
                draw_hand(img, self.hand, (tip[0] + 10, tip[1] + 10), 0.3)
        stamp_in(img, self.st, CX, 1760, t, tS)
        pop(img, C('THAT WEAK GLUE', 70, bg=YEL), CX, 330, t, self.we('weak') - 0.05, out_t=tS - 0.30)
        pop(img, C('IT STICKS...', 76, bg=(255, 255, 255)), CX, 330, t, tS - 0.05, out_t=tP - 0.30)
        pop(img, C('...AND PEELS OFF CLEAN!', 66, bg=(110, 220, 130)), CX, 330, t, tP - 0.05)

# ====================================================================== 7: why yellow? lab next door
class Yellow(Base):
    def make_shakes(self):
        return [(self.we('accident.'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('yellow?'), 'pop', 0.6), (self.we('accident.'), 'thud', 0.8),
                (self.we('lab'), 'squeak', 0.6), (self.we('scrap'), 'rustle', 0.7)]
    def plate(self):
        img = wall_plate('#BFE3E0', '#4E8C8A', 13, (CX, 1000, 1300))
        desk(img, 1380, (120, 90, 70))
        self.door = door_sprite(380, 800)
        self.leaf = door_leaf(380, 780)
        self.q = qmark(320, (255, 226, 74))
        self.st = stamp_sprite('ACCIDENT!', 140, color=RED, angle=-7)
        return img
    def dyn(self, img, t):
        tY, tA, tL, tScr = self.we('yellow?'), self.we('accident.'), self.we('lab'), self.we('scrap')
        dx = CX + 230
        dy0 = 1380 - 800
        paste_at(img, self.door, dx - 200, dy0 - 10)
        ok = ease_out((t - tL) / 0.45)
        lw = max(4, int(380 * (1 - 0.82 * ok)))
        leaf = self.leaf.resize((lw, 780))
        paste_at(img, leaf, dx - 180, dy0 + 10)
        if t > tL + 0.2:
            k = ease_out((t - tL - 0.2) / 0.6)
            for j in range(9):
                put_note(img, 260, dx - 20 - 520 * k + (j % 3) * 14, 1330 - j * 22, (j * 37 % 13) - 6, sh=0.25)
        if t < tL + 0.2:
            put_note(img, 520, CX - 220, 1000, -6 + 2 * math.sin(t * 5), scribble=0, sh=0.4)
            pop(img, self.q, CX - 220, 990, t, tY - 0.1)
        pop(img, C('WHY YELLOW?', 86, bg=YEL), CX, 330, t, 0.05, out_t=tL - 0.30)
        stamp_in(img, self.st, CX, 1760, t, tA)
        pop(img, C('THE LAB NEXT DOOR', 66, bg=(255, 255, 255)), CX, 330, t, tL - 0.05, out_t=tScr - 0.40)
        pop(img, C('ONLY HAD YELLOW SCRAP PAPER', 54, bg=YEL), CX, 330, t, tScr - 0.15)

# ====================================================================== 8: four cities, sales flopped
class Flop(Base):
    def make_shakes(self):
        return [(self.we('flopped.'), 18, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5)]
        for k in range(4):
            ev.append((0.1 + k * 0.12, 'pop', 0.45))
        ev += [(self.we('sales'), 'buzzer', 0.7), (self.we('sales') + 0.3, 'thud', 0.7)]
        return ev
    def plate(self):
        img = wall_plate('#F4C6A0', '#A2593B', 17, (CX, 1000, 1300))
        self.shop = shop_sprite(470, 420)
        self.st = stamp_sprite('FLOP!', 190, color=RED, angle=-8)
        return img
    def dyn(self, img, t):
        tS = self.we('sales')
        pos = [(CX - 270, 720), (CX + 270, 720), (CX - 270, 1180), (CX + 270, 1180)]
        for k, (x, y) in enumerate(pos):
            pop(img, self.shop, x, y, t, 0.05 + k * 0.12)
        if t > tS - 0.1:
            k = ease_out((t - tS + 0.1) / 0.6)
            pts = [(140, 620), (420, 760), (620, 700), (1150, 700 + 700 * k)]
            ov = OV(img, 0, 0, PW, PH)
            ov.d.line(pts, fill=(214, 40, 40, 255), width=40, joint='curve')
            ex, ey = pts[-1]
            ov.d.polygon([(ex - 60, ey - 50), (ex + 50, ey - 40), (ex + 20, ey + 80)], fill=(214, 40, 40, 255))
            ov.commit()
        pop(img, C('TESTED IN 4 CITIES', 72, bg=YEL), CX, 330, t, 0.05)
        stamp_in(img, self.st, CX, 1780, t, self.we('flopped.'))

# ====================================================================== 9: Boise free samples, 90%
class Boise(Base):
    def make_shakes(self):
        return [(self.we('90%'), 16, 0.32)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('free'), 'party', 0.6), (self.we('Boise,'), 'pop', 0.5),
              (self.we('90%'), 'bigpop', 0.8)]
        for k in range(3):
            ev.append((self.we('tried') + 0.1 + k * 0.2, 'ding', 0.4))
        return ev
    def plate(self):
        img = wall_plate('#9ED7A8', '#2E7A4A', 19, (CX, 1000, 1300))
        desk(img, 1400)
        self.chk = check_sprite(80)
        rng = np.random.default_rng(4)
        self.rain = [(float(rng.uniform(120, PW - 120)), float(rng.uniform(0, 1)), float(rng.uniform(-40, 40)), int(rng.integers(150, 230))) for _ in range(16)]
        return img
    def dyn(self, img, t):
        tF, tB, t9, tT = self.we('free'), self.we('Boise,'), self.we('90%'), self.we('tried')
        if t > tF - 0.2:
            for j, (x, ph, rot, s) in enumerate(self.rain):
                k = clamp01((t - tF + 0.2 - ph * 1.2) / 0.9)
                if k <= 0:
                    continue
                y = -200 + (1330 - (j % 4) * 26 + 200) * ease_in_out(k)
                put_note(img, s, x, y, rot * (1 - k) + (j * 29 % 21) - 10, sh=0.3, lift=1 - k)
        if t > t9 - 0.1:
            k = ease_out((t - t9 + 0.1) / 0.7)
            ov = OV(img, CX - 330, 560, CX + 330, 1220)
            ov.d.ellipse(ov.box(CX - 300, 590, CX + 300, 1190), fill=(255, 255, 255, 235))
            ov.d.arc(ov.box(CX - 270, 620, CX + 270, 1160), -90, -90 + 324 * k, fill=(40, 170, 80, 255), width=50)
            ov.commit()
            txt = text_img(f'{int(round(90 * k))}%', 230, fill=(30, 30, 36))
            paste_center(img, txt, CX, 890)
            for j, x in enumerate((CX - 380, CX, CX + 380)):
                pop(img, self.chk, x, 1300, t, tT + 0.1 + j * 0.2)
        pop(img, C('FREE SAMPLES!', 86, bg=YEL), CX, 330, t, tF - 0.05, out_t=t9 - 0.30)
        pop(img, C('BOISE, IDAHO', 86, bg=(255, 255, 255)), CX, 1760, t, tB - 0.05)
        pop(img, C("SAID THEY'D BUY THEM", 66, bg=(110, 220, 130)), CX, 330, t, t9 - 0.05)

# ====================================================================== 10: 1980 stores nationwide -> loops into the hook
class Outro(Hook):
    def make_shakes(self):
        return [(self.we('1980,'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1980,'), 'thud', 0.7), (self.we('nationwide,'), 'cash', 0.6),
                (self.we('wild,'), 'pop', 0.5)]
    def tswitch(self):
        return self.we('because...') - 0.05
    def plate(self):
        img = Hook.plate(self)
        self.hook_plate = img.copy()
        self.st80 = stamp_sprite('1980', 170, color=BLUE, angle=-7)
        store = wall_plate('#F7E3B5', '#B98A47', 23, (CX, 1000, 1300))
        ov = OV(store, 0, 0, PW, PH)
        for y in (720, 1120, 1520, 1920):
            ov.d.rectangle((40, y, PW - 40, y + 46), fill=(150, 96, 52, 255))
            ov.d.rectangle((40, y, PW - 40, y + 12), fill=(190, 130, 76, 255))
        ov.commit()
        pad = pad_sprite(200, 12)
        for y in (720, 1120, 1520, 1920):
            for x in range(70, PW - 200, 230):
                paste_at(store, pad, x, y - pad.height + 6)
        return store
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hook_plate, (0, 0))
            self.hero(img, t - self.dur)   # ends exactly where frame 0 begins
            return
        stamp_in(img, self.st80, CX, 560, t, self.we('1980,'))
        pop(img, C('IN STORES NATIONWIDE', 70, bg=YEL), CX, 330, t, self.we('stores') - 0.05)
        pop(img, C('WILD, BECAUSE...', 76, bg=(255, 255, 255)), CX, 1800, t, self.we('wild,') - 0.05)
    def cam(self, t):
        tw = self.tswitch()
        if t >= tw:
            return self.z0, CX, CY, 0.0
        dx, dy, dr = self.shake(t)
        p = 1 - ease_out(t / 0.32)
        return 1.08 + 0.05 * clamp01(t / tw) + 0.1 * p, CX + dx, 1100 + dy, 2.0 * p + dr

SCENES = [Hook, StrongGlue, WeakGlue, NoUse, Choir, FallOut, Coated, Yellow, Flop, Boise, Outro]
