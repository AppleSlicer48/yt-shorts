import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from engine import *

CX, CY = PW / 2, PH / 2
GRAIN = None

def grain_map():
    global GRAIN
    if GRAIN is None:
        n = smooth_noise(PH, PW, 6, 77, 2)
        GRAIN = (0.94 + 0.12 * n).astype(np.float32)
    return GRAIN

# ---------------------------------------------------------------- textures
def ruler_tex(cm=15, ppc=110, h=200, base='#F4C534', dark='#D49A16', seed=3, ink=(28, 22, 14), label=None, mult=1):
    m = 46
    w = cm * ppc + 2 * m
    arr = wood(w, h, base, dark, seed=seed, stretch=24, rings=7, contrast=0.32)
    shade = np.linspace(1.08, 0.92, h)[:, None, None]
    img = to_img(arr * shade)
    d = ImageDraw.Draw(img)
    fnum = font(int(h * 0.25))
    for mm in range(cm * 10 + 1):
        x = m + mm * ppc / 10
        if mm % 10 == 0:
            L, wd = h * 0.34, 4
        elif mm % 5 == 0:
            L, wd = h * 0.24, 3
        else:
            L, wd = h * 0.15, 2
        d.line([(x, 0), (x, L)], fill=ink, width=wd)
        if mm % 10 == 0 and mm > 0 and mm < cm * 10:
            t = str(mm // 10 * mult)
            bb = fnum.getbbox(t)
            d.text((x - (bb[2] + bb[0]) / 2, h * 0.38 - bb[1]), t, font=fnum, fill=ink)
    d.line([(0, h - 3), (w, h - 3)], fill=(150, 100, 20), width=3)
    if label:
        fl = font(int(h * 0.17))
        d.text((m + 18, h * 0.70), label, font=fl, fill=ink)
    return img

def copper_tex(w=980, h=96, seed=11):
    base = vgrad(w, h, [(0, '#E89A64'), (0.45, '#B8643A'), (1, '#7A3A1E')])
    n = smooth_noise(h, w, 40, seed, 4)
    n2 = smooth_noise(h, w, 9, seed + 1, 2)
    patina = np.clip((n - 0.58) * 4, 0, 1)[..., None]
    pat = hexc('#4E8C7A')
    arr = base * (0.85 + 0.3 * n2[..., None])
    arr = arr * (1 - 0.55 * patina) + pat * 0.55 * patina
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    x = 30.0
    while x < w - 20:
        L = h * (0.25 + 0.25 * rng.random())
        d.line([(x, 0), (x + rng.normal(0, 1.5), L)], fill=(60, 25, 10), width=3)
        d.line([(x + 2, 0), (x + 2 + rng.normal(0, 1.5), L)], fill=(250, 190, 140), width=1)
        x += 34 + rng.normal(0, 7)
    return img

def ivory_tex(w=1100, h=150, seed=21):
    arr = wood(w, h, '#F3EAD3', '#D8C9A6', seed=seed, stretch=30, rings=5, contrast=0.25)
    img = to_img(arr * np.linspace(1.05, 0.9, h)[:, None, None])
    d = ImageDraw.Draw(img)
    step = 13
    k = 0
    x = 40
    while x < w - 40:
        L = h * (0.42 if k % 10 == 0 else 0.27 if k % 5 == 0 else 0.17)
        d.line([(x, 0), (x, L)], fill=(70, 55, 35), width=2)
        if k % 10 == 0:
            d.ellipse((x - 5, L + 6, x + 5, L + 16), outline=(70, 55, 35), width=2)
        x += step; k += 1
    return img

def cubit_tex(w=1080, h=118, seed=31):
    arr = wood(w, h, '#5A3720', '#2B170B', seed=seed, stretch=20, rings=9, contrast=0.55)
    img = to_img(arr * np.linspace(1.15, 0.8, h)[:, None, None])
    d = ImageDraw.Draw(img)
    seg = w / 28
    for i in range(29):
        x = i * seg
        top = 0 if i % 4 == 0 else h * 0.45
        d.line([(x, top), (x, h)], fill=(225, 190, 120), width=4 if i % 4 == 0 else 2)
    return img

def stone_tex(w, h, base='#8C847B', dark='#4F4842', seed=41, cell=60):
    n = smooth_noise(h, w, cell, seed, 5)
    f = smooth_noise(h, w, 4, seed + 3, 1)
    t = np.clip(n * 0.8 + f * 0.25, 0, 1)
    b, d = hexc(base), hexc(dark)
    return b * (1 - t[..., None]) + d * t[..., None]

# ---------------------------------------------------------------- mannequin arm
ARM_LIGHT = '#E2B47C'

def arm(layer, elbow, L, ang=0.0, color=ARM_LIGHT, upper=True):
    col = hexc(color)
    jcol = col * 0.86
    ex, ey = elbow
    ca, sa = math.cos(ang), math.sin(ang)
    def g(x, y):
        return (ex + (x * ca - y * sa) * L, ey + (x * sa + y * ca) * L)
    gr = grain_map()
    kw = dict(grain=gr, spec=0.28, shin=22)
    if upper:
        capsule(layer, g(-0.62, 0.18), g(0, 0), 0.092 * L, 0.078 * L, col, **kw)
    capsule(layer, g(0, 0), g(0.6, 0), 0.068 * L, 0.046 * L, col, **kw)
    sphere(layer, g(0, 0), 0.082 * L, jcol, **kw)
    sphere(layer, g(0.6, 0), 0.046 * L, jcol, **kw)
    # palm
    ellipsoid(layer, g(0.72, 0.0), 0.118 * L, 0.082 * L, ang, col, **kw)
    # thumb
    sphere(layer, g(0.67, -0.07), 0.026 * L, jcol, **kw)
    capsule(layer, g(0.67, -0.07), g(0.75, -0.115), 0.024 * L, 0.02 * L, col, **kw)
    sphere(layer, g(0.75, -0.115), 0.02 * L, jcol, **kw)
    capsule(layer, g(0.75, -0.115), g(0.81, -0.135), 0.019 * L, 0.016 * L, col, **kw)
    # fingers: (y offset, length) — middle finger tip lands exactly at x = 1.0
    fingers = [(-0.048, 0.155, -0.012), (-0.016, 0.19, -0.004), (0.016, 0.175, 0.004), (0.046, 0.135, 0.014)]
    for (yo, ln, spread) in fingers:
        bx = 0.81
        mx, my = bx + ln * 0.5, yo + spread * 0.5
        tx, ty = bx + ln, yo + spread
        sphere(layer, g(bx, yo), 0.021 * L, jcol, **kw)
        capsule(layer, g(bx, yo), g(mx, my), 0.019 * L, 0.017 * L, col, **kw)
        sphere(layer, g(mx, my), 0.017 * L, jcol, **kw)
        capsule(layer, g(mx, my), g(tx, ty), 0.016 * L, 0.013 * L, col, **kw)
    return g(1.0, -0.004)

# ---------------------------------------------------------------- helpers
def bracket(img, x0, x1, y, prog, color=(255, 210, 60), width=10, cap=34):
    if prog <= 0:
        return
    d = ImageDraw.Draw(img)
    xe = x0 + (x1 - x0) * clamp01(prog)
    sh = (0, 0, 0, 140)
    for off, c in ((5, sh), (0, color + (255,))):
        d.line([(x0, y - cap / 2 + off), (x0, y + cap / 2 + off)], fill=c, width=width)
        d.line([(x0, y + off), (xe, y + off)], fill=c, width=width)
        if prog >= 0.999:
            d.line([(x1, y - cap / 2 + off), (x1, y + cap / 2 + off)], fill=c, width=width)

def dashed_v(img, x, y0, y1, color, width=6, dash=26, gap=16):
    d = ImageDraw.Draw(img)
    y = y0
    while y < y1:
        d.line([(x, y), (x, min(y1, y + dash))], fill=color, width=width)
        y += dash + gap

def finish(bg, layer=None, sh=(26, 40, 22, 0.55)):
    if layer is not None:
        if sh:
            bg = shadow(bg, layer.a, sh[0], sh[1], sh[2], sh[3])
        bg = layer.comp(bg)
    return bg

def plate_img(arr):
    return to_img(arr).convert('RGBA')

# ---------------------------------------------------------------- scene base
class Scene:
    focus = (CX, 1060)
    z0, z1 = 1.0, 1.07
    punch = 0.13
    rot_dir = 1

    def __init__(self, words, dur, idx):
        self.words, self.dur, self.idx = words, dur, idx
        self.rot_dir = 1 if idx % 2 == 0 else -1

    def wt(self, key, which='t0'):
        for w in self.words:
            if key.lower() in w['w'].lower():
                return w[which]
        raise KeyError(key)

    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k * 0.85 + 0.15 * k)
        p = 1 - ease_out(t / 0.32)
        z *= 1 + self.punch * p
        rot = 2.2 * p * self.rot_dir
        return z, self.focus[0], self.focus[1], rot

    def dyn(self, img, t):
        pass

# ---------------------------------------------------------------- 0 & 12: hero ruler on table
def table_bg(seed=5):
    arr = wood(PW, PH, '#5A3822', '#2A160B', seed=seed, stretch=16, rings=40, contrast=0.55)
    planks = np.ones((PH, 1), np.float32)
    for y in range(0, PH, 420):
        planks[max(0, y - 3):y + 3] = 0.55
    arr = arr * planks[..., None]
    arr = arr * (0.35 + 0.95 * radial(PW, PH, CX, 1000, 1500, 1.6))[..., None]
    arr = arr * np.linspace(0.75, 1.0, PH)[:, None, None]
    return vignette(arr, 0.6)

class HeroRuler(Scene):
    z0, z1 = 1.04, 1.14
    def plate(self):
        bg = table_bg()
        lay = Layer()
        self.corners = bar_corners(CX, 1000, 1180, 210, -0.42, persp=0.1)
        slab(lay, ruler_tex(), self.corners, 30, '#B98418')
        self.ruler_a = lay.a[600:1450].copy()
        yy, xx = np.mgrid[600:1450, 0:PW].astype(np.float32)
        self.gl_coord = xx + (yy - 1000) * 0.9
        bg = finish(bg, lay, (30, 46, 24, 0.6))
        return plate_img(bg)

    def cam(self, t):
        k = ease_out(t / 1.3)
        z = 1.42 + (self.z0 - 1.42) * k + (self.z1 - self.z0) * clamp01((t - 1.3) / max(0.1, self.dur - 1.3))
        return z, CX, 1000 + 120 * (1 - k), -6 * (1 - k)

    def dyn(self, img, t):
        # specular glint sliding along the ruler
        k = clamp01((t - 0.25) / 1.1)
        if 0 < k < 1 and hasattr(self, 'gl_coord'):
            pos = -300 + k * 1900
            band = np.exp(-((self.gl_coord - pos) / 70.0) ** 2)
            a = (band * self.ruler_a * 0.55 * 255).astype(np.uint8)
            glint = Image.new('RGBA', (PW, 850), (255, 250, 230, 0))
            glint.putalpha(Image.fromarray(a))
            img.alpha_composite(glint, (0, 600))

class Outro(HeroRuler):
    def plate(self):
        bg = table_bg(seed=6)
        lay = Layer()
        self.corners = bar_corners(CX + 70, 660, 1100, 190, -0.16, persp=0.06)
        slab(lay, ruler_tex(seed=4), self.corners, 28, '#B98418')
        bg = finish(bg, lay, (28, 42, 22, 0.6))
        lay2 = Layer()
        self.elbow = (250, 1080)
        arm(lay2, self.elbow, 820, -0.16)
        bg = finish(bg, lay2, (30, 50, 28, 0.6))
        return plate_img(bg)

    def cam(self, t):
        tE = self.wt('ELBOW')
        p = 1 - ease_out(t / 0.32)
        k = ease_in_out((t - tE + 0.2) / 1.0)
        z = (1.0 + 0.06 * clamp01(t / self.dur)) * (1 + 0.12 * p) + 0.22 * k
        fx = CX + (self.elbow[0] + 150 - CX) * k
        fy = 1000 + (self.elbow[1] - 40 - 1000) * k
        return z, fx, fy, 2.2 * p * self.rot_dir

    def dyn(self, img, t):
        tE = self.wt('ELBOW')
        if t >= tE:
            k = ease_back((t - tE) / 0.35, 2.0)
            r = 150 * k
            d = ImageDraw.Draw(img)
            ex, ey = self.elbow
            for off, c, wd in ((6, (0, 0, 0, 120), 14), (0, (255, 210, 60, 255), 12)):
                d.ellipse((ex - r, ey - r + off, ex + r, ey + r + off), outline=c, width=wd)

# ---------------------------------------------------------------- desert
def desert_bg(dusk=False):
    if not dusk:
        sky = vgrad(PW, PH, [(0, '#1E2C5C'), (0.22, '#45478A'), (0.38, '#C46E5C'), (0.445, '#F6AD60'), (1, '#F6AD60')])
        sand = [(0, '#E7A866'), (0.4, '#C98446'), (1, '#7E4523')]
        pyr_lit, pyr_dark = hexc('#E39A5C'), hexc('#8F5136')
        sun_c = hexc('#FFE1A0')
    else:
        sky = vgrad(PW, PH, [(0, '#0E1236'), (0.22, '#2C2A66'), (0.38, '#9E4A55'), (0.445, '#EE8A4E'), (1, '#EE8A4E')])
        sand = [(0, '#C9824C'), (0.4, '#9A5A33'), (1, '#4E2614')]
        pyr_lit, pyr_dark = hexc('#C97A48'), hexc('#5E3022')
        sun_c = hexc('#FFC98A')
    hz = int(0.445 * PH)
    arr = sky.copy()
    # sun glow + disc
    sx, sy = 960, hz - 40
    glow = radial(PW, PH, sx, sy, 700, 2.2)
    arr = arr + sun_c * (glow * 0.55)[..., None]
    disc = np.clip(80 - np.sqrt((np.mgrid[0:PH, 0:PW][1] - sx) ** 2 + (np.mgrid[0:PH, 0:PW][0] - sy) ** 2) + 0.5, 0, 1)
    arr = arr * (1 - disc[..., None]) + sun_c * disc[..., None]
    lay = Layer()
    haze = hexc('#E8A070') if not dusk else hexc('#B8604E')
    for (px, bw, ph, hz_k) in ((330, 560, 330, 0.25), (735, 330, 190, 0.4), (1060, 210, 120, 0.5)):
        apex = (px + bw * 0.08, hz - ph)
        left = [apex, (apex[0], hz + 2), (px - bw / 2, hz + 2)]
        right = [apex, (px + bw / 2, hz + 2), (apex[0], hz + 2)]
        fill_poly(lay, left, pyr_lit * (1 - hz_k) + haze * hz_k)
        fill_poly(lay, right, pyr_dark * (1 - hz_k) + haze * hz_k)
    arr = lay.comp(arr)
    # ground
    g = vgrad(PW, PH - hz, sand)
    xs = np.arange(PW)
    gl = Layer(PW, PH)
    gl.put(g, np.ones((PH - hz, PW), np.float32), 0, hz)
    arr = gl.comp(arr)
    # dune ridges
    for k, (yb, amp, fr, ph, c) in enumerate(((hz + 140, 40, 0.004, 0.5, '#D8945A'), (hz + 330, 70, 0.0032, 2.0, '#C27B42'),
                                                (hz + 600, 90, 0.0026, 4.1, '#A9622F'))):
        ridge = yb + amp * np.sin(xs * fr * 2 * np.pi + ph)
        pts = [(x, ridge[x]) for x in range(0, PW, 8)] + [(PW, PH), (0, PH)]
        lay = Layer()
        fill_poly(lay, pts, c, 0.75 if not dusk else 0.6)
        arr = lay.comp(arr)
        # lit crest line
        lay = Layer()
        crest = [(x, ridge[x] - 2) for x in range(0, PW, 8)] + [(x, ridge[x] + 3) for x in range(PW - 8, -1, -8)]
        fill_poly(lay, crest, '#FFD9A0', 0.35)
        arr = lay.comp(arr)
    return arr

class Desert(Scene):
    z0, z1 = 1.0, 1.08
    focus = (CX, 1150)
    def plate(self):
        arr = desert_bg()
        lay = Layer()
        top = [(250, 1170), (1046, 1170), (1150, 1360), (146, 1360)]
        stex = to_img(stone_tex(900, 260, '#D9AE7A', '#9C7046', seed=43, cell=50))
        slab(lay, stex, top, 230, '#A9774A', side_dark=0.6)
        arr = finish(arr, lay, (30, 30, 30, 0.5))
        lay = Layer()
        arm(lay, (300, 1250), 700, -0.05)
        arr = finish(arr, lay, (24, 34, 18, 0.5))
        return plate_img(vignette(arr, 0.45))

    def dyn(self, img, t):
        pop(img, chip('~ 3000 BC', 54, dot=(230, 120, 40)), CX, 470, t, 0.25)

def blurred_desert(dark=0.8, dusk=False):
    arr = desert_bg(dusk)
    im = to_img(arr).filter(ImageFilter.GaussianBlur(22))
    return to_arr(im) * dark

class CubitArm(Scene):
    z0, z1 = 1.0, 1.06
    def plate(self):
        arr = blurred_desert(0.75)
        arr = vignette(arr, 0.5)
        lay = Layer()
        self.el = (190, 1000)
        self.tip = arm(lay, self.el, 960, 0.0)
        arr = finish(arr, lay, (24, 44, 24, 0.55))
        return plate_img(arr)

    def dyn(self, img, t):
        tE, tF = self.wt('ELBOW'), self.wt('FINGERTIP')
        tF1 = self.wt('FINGERTIP', 't1')
        y = 1150
        prog = (t - tE) / max(0.3, (tF1 - tE))
        bracket(img, self.el[0], self.tip[0], y, ease_in_out(prog))
        if t > tE:
            d = ImageDraw.Draw(img)
            r = 16
            for (x, yy), tt in ((self.el, tE), (self.tip, tF)):
                if t > tt:
                    d.ellipse((x - r, yy - r, x + r, yy + r), fill=(255, 210, 60), outline=(0, 0, 0), width=4)
        pop(img, chip('1 CUBIT', 64, bg=(255, 210, 60)), (self.el[0] + self.tip[0]) / 2, y + 100, t, tF1 - 0.1)

class TwoArms(Scene):
    z0, z1 = 1.0, 1.05
    def plate(self):
        arr = vignette(blurred_desert(0.62), 0.5)
        lay = Layer()
        self.ex = 175
        self.tipA = arm(lay, (self.ex, 760), 780, 0.0, '#E8BF8A')
        arr = finish(arr, lay, (20, 36, 20, 0.5))
        lay = Layer()
        self.tipB = arm(lay, (self.ex, 1150), 940, 0.0, '#C08452')
        arr = finish(arr, lay, (20, 36, 20, 0.5))
        img = plate_img(arr)
        dashed_v(img, self.ex, 600, 1300, (255, 255, 255, 200))
        return img

    def dyn(self, img, t):
        tD = self.wt('DIFFERENT')
        if t > tD - 0.05:
            red = (255, 70, 60, 255)
            dashed_v(img, int(self.tipA[0]), 620, 1300, red, 7)
            dashed_v(img, int(self.tipB[0]), 620, 1300, red, 7)
            y = 1290
            x0, x1 = self.tipA[0], self.tipB[0]
            k = ease_out((t - tD) / 0.3)
            d = ImageDraw.Draw(img)
            d.line([(x0, y), (x0 + (x1 - x0) * k, y)], fill=red, width=10)
            pop(img, chip('NOT THE SAME LENGTH', 50, bg=(255, 70, 60), fg=(255, 255, 255)), CX, 440, t, tD + 0.1)
        pop(img, chip('PERSON A', 40), 420, 600, t, 0.35)
        pop(img, chip('PERSON B', 40), 420, 1000, t, 0.5)

# ---------------------------------------------------------------- copper bar
def dark_room(c0='#2C2622', c1='#120F0D', spot=(CX, 950, 1100), strength=0.9, seed=51):
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.85 + 0.3 * smooth_noise(PH, PW, 90, seed, 4))[..., None]
    arr = arr * (0.45 + strength * radial(PW, PH, *spot, 1.5))[..., None]
    return vignette(arr, 0.55)

class CopperBar(Scene):
    z0, z1 = 1.0, 1.09
    def plate(self):
        arr = dark_room()
        lay = Layer()
        top = [(200, 1080), (1096, 1080), (1186, 1290), (110, 1290)]
        slab(lay, to_img(stone_tex(900, 210, '#8A8077', '#4A433D', seed=45)), top, 300, '#5E5650', 0.45)
        arr = finish(arr, lay, (0, 40, 30, 0.6))
        lay = Layer()
        self.bar = bar_corners(CX, 1175, 980, 96, -0.03, persp=0.05)
        slab(lay, copper_tex(), self.bar, 26, '#7A3D20')
        arr = finish(arr, lay, (16, 26, 12, 0.6))
        return plate_img(arr)

    def dyn(self, img, t):
        pop(img, chip('SUMER  ·  c. 2650 BC', 50, dot=(220, 120, 60)), CX, 520, t, self.wt('Sumerians'))
        tO = self.wt('OFFICIAL')
        x0, x1 = 170, 1126
        k = ease_in_out((t - tO) / 0.45)
        if t > tO:
            bracket(img, x0, x1, 1010, k)
        pop(img, chip('1 CUBIT ≈ 52 cm', 52, bg=(255, 210, 60)), CX, 900, t, tO + 0.35)

class Museum(Scene):
    z0, z1 = 1.0, 1.1
    focus = (CX, 1100)
    def plate(self):
        arr = dark_room('#16213A', '#05070D', (CX, 900, 1200), 0.8, seed=53)
        # spotlight cone
        cone = Image.new('L', (PW, PH), 0)
        ImageDraw.Draw(cone).polygon([(560, 0), (736, 0), (1020, 1250), (276, 1250)], fill=70)
        cone = np.asarray(cone.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
        arr = arr + hexc('#B8C8FF') * cone[..., None] * 0.6
        lay = Layer()
        # pedestal
        ptop = [(350, 1180), (946, 1180), (990, 1250), (306, 1250)]
        slab(lay, to_img(stone_tex(640, 80, '#3A3F4A', '#22252C', seed=55)), ptop, 700, '#2A2E37', 0.4)
        arr = finish(arr, lay, (0, 30, 30, 0.5))
        lay = Layer()
        self.bar = bar_corners(CX, 1150, 520, 52, 0.0, persp=0.0)
        slab(lay, copper_tex(980, 96, seed=12), self.bar, 16, '#7A3D20')
        arr = finish(arr, lay, (10, 16, 8, 0.6))
        img = plate_img(arr)
        # glass case
        g = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
        d = ImageDraw.Draw(g)
        d.rectangle((330, 700, 966, 1215), fill=(170, 200, 255, 22), outline=(210, 230, 255, 120), width=4)
        d.polygon([(380, 700), (470, 700), (330, 900), (330, 780)], fill=(255, 255, 255, 30))
        d.polygon([(760, 700), (800, 700), (560, 1215), (520, 1215)], fill=(255, 255, 255, 18))
        img.alpha_composite(g)
        # plaque
        pl = Image.new('RGBA', (300, 90), (0, 0, 0, 0))
        dp = ImageDraw.Draw(pl)
        dp.rounded_rectangle((0, 0, 299, 89), 10, fill=(196, 160, 88, 255), outline=(120, 90, 40, 255), width=3)
        f = font(34, FONT_SERIF)
        txt = 'c. 2650 BC'
        bb = f.getbbox(txt)
        dp.text((150 - (bb[2] + bb[0]) / 2, 45 - (bb[3] + bb[1]) / 2), txt, font=f, fill=(60, 40, 15))
        paste_center(img, pl, CX, 1330)
        return img

    def dyn(self, img, t):
        pop(img, chip('OLDEST KNOWN MEASURING ROD', 44, bg=(255, 210, 60)), CX, 560, t, self.wt('OLDEST') - 0.05)

# ---------------------------------------------------------------- Indus ivory
def brick_wall(seed=61):
    rng = np.random.default_rng(seed)
    img = Image.new('RGB', (PW, PH), (70, 40, 30))
    d = ImageDraw.Draw(img)
    bw, bh, m = 190, 70, 10
    for r, y in enumerate(range(-20, PH, bh + m)):
        off = (r % 2) * (bw + m) // 2
        for x in range(-bw + off, PW + bw, bw + m):
            c = np.array([176, 92, 58]) * (0.75 + 0.35 * rng.random())
            d.rectangle((x, y, x + bw, y + bh), fill=tuple(int(v) for v in c))
    arr = to_arr(img.filter(ImageFilter.GaussianBlur(6)))
    arr = arr * (0.85 + 0.3 * smooth_noise(PH, PW, 30, seed, 3))[..., None]
    arr = arr * (0.3 + 0.8 * radial(PW, PH, CX, 1000, 1200, 1.5))[..., None]
    return vignette(arr, 0.5)

class Indus(Scene):
    z0, z1 = 1.0, 1.07
    def plate(self):
        arr = brick_wall()
        lay = Layer()
        self.rc = bar_corners(CX, 1040, 1060, 150, -0.05, persp=0.03)
        slab(lay, ivory_tex(), self.rc, 24, '#CDBC97')
        arr = finish(arr, lay, (20, 36, 20, 0.6))
        return plate_img(arr)

    def dyn(self, img, t):
        pop(img, chip('INDUS VALLEY  ·  c. 2400 BC', 46, dot=(200, 90, 50)), CX, 520, t, self.wt('INDUS') - 0.05)
        tm = self.wt('marks')
        if t < tm:
            return
        k = ease_out((t - tm) / 0.45)
        lx, ly = 760 + 600 * (1 - k), 995
        R, zoom = 175, 2.6
        src_r = int(R / zoom)
        crop = img.crop((int(lx - src_r), int(ly - src_r), int(lx + src_r), int(ly + src_r))).resize((2 * R, 2 * R), Image.BICUBIC)
        mask = Image.new('L', (2 * R, 2 * R), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=255)
        lens = Image.new('RGBA', (2 * R + 120, 2 * R + 260), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lens)
        # handle
        dl.line([(R + 60 + R * 0.7, R + 60 + R * 0.7), (R + 60 + R * 1.15, R + 60 + R * 1.6)], fill=(45, 30, 22, 255), width=46)
        lens.paste(crop, (60, 60), mask)
        glare = Image.new('RGBA', (2 * R, 2 * R), (255, 255, 255, 0))
        ImageDraw.Draw(glare).ellipse((30, 20, R, R * 0.8), fill=(255, 255, 255, 40))
        lens.alpha_composite(glare, (60, 60))
        dl.ellipse((60 - 12, 60 - 12, 60 + 2 * R + 12, 60 + 2 * R + 12), outline=(40, 40, 45, 255), width=24)
        dl.ellipse((60 - 12, 60 - 12, 60 + 2 * R + 12, 60 + 2 * R + 12), outline=(190, 190, 200, 255), width=5)
        paste_at(img, lens, int(lx - R - 60), int(ly - R - 60))
        pop(img, chip('< 2 mm apart', 50, bg=(255, 210, 60)), lx + 20, ly - R - 90, t, self.wt('MILLIMETERS') - 0.05)

# ---------------------------------------------------------------- Egypt cubit rod
class Egypt(Scene):
    z0, z1 = 1.0, 1.06
    def plate(self):
        arr = vignette(to_arr(to_img(desert_bg(dusk=True)).filter(ImageFilter.GaussianBlur(10))) * 0.85, 0.45)
        lay = Layer()
        self.x0, self.x1, self.y0, self.y1 = 108, 1188, 990, 1108
        top = [(self.x0, self.y0), (self.x1, self.y0), (self.x1, self.y1), (self.x0, self.y1)]
        slab(lay, cubit_tex(), top, 34, '#2A170C', 0.5)
        arr = finish(arr, lay, (18, 40, 22, 0.6))
        return plate_img(arr)

    def dyn(self, img, t):
        pop(img, chip('EGYPT  ·  ROYAL CUBIT ≈ 52 cm', 44, dot=(240, 180, 60)), CX, 520, t, 0.2)
        seg = (self.x1 - self.x0) / 7
        tP = self.wt('7')
        tF = self.wt('28')
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        fn = font(58)
        for i in range(7):
            ti = tP + i * 0.09
            if t < ti:
                continue
            a = 1.0 if t < tF else 0.45
            xa = self.x0 + i * seg
            col = (255, 200, 70) if i % 2 == 0 else (255, 150, 50)
            d.rectangle((xa + 3, self.y0 + 3, xa + seg - 3, self.y1 - 3), fill=col + (int(110 * a),))
            k = ease_back((t - ti) / 0.25, 2.0)
            txt = str(i + 1)
            bb = fn.getbbox(txt)
            cx, cy = xa + seg / 2, self.y0 - 70 - 20 * (1 - k)
            d.text((cx - (bb[2] + bb[0]) / 2, cy - (bb[3] + bb[1]) / 2), txt, font=fn, fill=(255, 255, 255, int(255 * clamp01(k))),
                   stroke_width=5, stroke_fill=(0, 0, 0, int(255 * clamp01(k))))
        if t >= tF:
            fw = (self.x1 - self.x0) / 28
            for j in range(28):
                tj = tF + j * 0.022
                if t < tj:
                    continue
                x = self.x0 + j * fw
                d.rectangle((x + 3, self.y1 - 10, x + fw - 3, self.y1 + 26), fill=(255, 230, 120, 255))
        img.alpha_composite(ov)
        pop(img, chip('7 PALMS', 50, bg=(255, 200, 70)), 360, 1250, t, tP + 0.5)
        pop(img, chip('28 FINGERS', 50, bg=(255, 230, 120)), 900, 1250, t, tF + 0.3)

# ---------------------------------------------------------------- barleycorns
def parchment():
    arr = vgrad(PW, PH, [(0, '#E7D4A8'), (1, '#CDB383')])
    n = smooth_noise(PH, PW, 120, 71, 5)
    f = smooth_noise(PH, PW, 5, 72, 1)
    arr = arr * (0.82 + 0.25 * n[..., None] + 0.06 * f[..., None])
    arr = arr * (0.55 + 0.6 * radial(PW, PH, CX, 1000, 1300, 1.2))[..., None]
    return vignette(arr, 0.5)

class Barley(Scene):
    z0, z1 = 1.0, 1.07
    def plate(self):
        self.grains = []
        L, R = 300, 64
        self.L = L
        for k in range(3):
            lay = Layer(L + 120, 2 * R + 120)
            spindle(lay, (60, R + 60), (60 + L, R + 60), R, '#DDA845')
            sp, x0, y0 = layer_sprite(lay)
            shadow_im = Image.new('RGBA', (sp.width + 80, sp.height + 80), (0, 0, 0, 0))
            m = sp.getchannel('A').point(lambda v: int(v * 0.5))
            sh = Image.new('RGBA', sp.size, (40, 25, 5, 255)); sh.putalpha(m)
            shadow_im.alpha_composite(sh, (40, 40))
            shadow_im = shadow_im.filter(ImageFilter.GaussianBlur(12))
            self.grains.append((sp, shadow_im, x0 - 60, y0 - (R + 60)))
        return plate_img(parchment())

    def dyn(self, img, t):
        pop(img, chip('MEDIEVAL ENGLAND', 48, dot=(200, 40, 50)), CX, 520, t, self.wt('England') - 0.1)
        t3 = self.wt('3')
        total = 3 * self.L
        xs = [CX - total / 2 + k * self.L for k in range(3)]
        y = 1000
        for k, (sp, shi, ox, oy) in enumerate(self.grains):
            tk = t3 - 0.15 + k * 0.2
            if t < tk:
                continue
            u = clamp01((t - tk) / 0.38)
            # drop with a small bounce
            if u < 0.75:
                yy = y - 420 * (1 - (u / 0.75) ** 2)
            else:
                b = (u - 0.75) / 0.25
                yy = y - 30 * math.sin(math.pi * b)
            sa = clamp01(u * 1.3)
            shi2 = shi.copy(); shi2.putalpha(shi.getchannel('A').point(lambda v: int(v * sa)))
            paste_at(img, shi2, int(xs[k] + ox - 40 + 14), int(y + oy - 40 + 26))
            paste_at(img, sp, int(xs[k] + ox), int(yy + oy))
        tE = self.wt('end')
        tE1 = self.words[-1]['t1']
        prog = ease_in_out((t - tE) / max(0.3, tE1 - tE))
        bracket(img, xs[0], xs[0] + total, 1140, prog)
        pop(img, chip('= 1 INCH', 64, bg=(255, 210, 60)), CX, 1245, t, tE1 - 0.1)

# ---------------------------------------------------------------- globe
TILT = math.radians(24)

def globe_screen(lat, lon, c, R):
    x = math.cos(lat) * math.sin(lon)
    y = math.sin(lat)
    z = math.cos(lat) * math.cos(lon)
    y2 = y * math.cos(TILT) - z * math.sin(TILT)
    z2 = y * math.sin(TILT) + z * math.cos(TILT)
    return c[0] + x * R, c[1] - y2 * R, z2

class Globe(Scene):
    z0, z1 = 1.0, 1.08
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#050816'), (0.5, '#0B1636'), (1, '#04060E')])
        rng = np.random.default_rng(81)
        for _ in range(500):
            x, y = rng.integers(0, PW), rng.integers(0, PH)
            b = rng.random() ** 3
            arr[y:y + 2, x:x + 2] += b * 0.9
        self.c, self.R = (CX, 980), 440
        cx, cy = self.c; R = self.R
        x0, y0, x1, y1 = int(cx - R - 3), int(cy - R - 3), int(cx + R + 3), int(cy + R + 3)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        nx, ny = (xx - cx) / R, (yy - cy) / R
        rho2 = nx * nx + ny * ny
        a = np.clip((1 - np.sqrt(rho2)) * R + 0.5, 0, 1)
        nz = np.sqrt(np.clip(1 - rho2, 0, 1))
        # inverse tilt to world coords; screen y is down so world-up = -ny
        py, pz = -ny, nz
        wy = py * math.cos(TILT) + pz * math.sin(TILT)
        wz = -py * math.sin(TILT) + pz * math.cos(TILT)
        wx = nx
        lat = np.degrees(np.arcsin(np.clip(wy, -1, 1)))
        lon = np.degrees(np.arctan2(wx, wz))
        ocean = hexc('#1F6FB8') * (1 - 0.5 * np.clip(-wy, 0, 1))[..., None] + hexc('#0C3A6B') * (0.5 * np.clip(-wy, 0, 1))[..., None]
        # stylised land from smooth noise in lat/lon space
        ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        col = ocean * (0.25 + 0.95 * ndl)[..., None]
        spec = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1) ** 40 * 0.5
        col = col + spec[..., None]
        gw = 0.35 / np.maximum(nz, 0.25)
        grid = np.maximum(np.clip(1 - np.abs(((lat + 7.5) % 15) - 7.5) / gw, 0, 1),
                          np.clip(1 - np.abs(((lon + 7.5) % 15) - 7.5) * np.cos(np.radians(lat)) / gw, 0, 1))
        col = col * (1 - 0.35 * grid[..., None]) + hexc('#9FD0FF') * (0.35 * grid[..., None])
        # rim atmosphere
        col = col + hexc('#7FC4FF') * ((1 - nz) ** 4 * 0.6)[..., None]
        sub = arr[y0:y1, x0:x1]
        arr[y0:y1, x0:x1] = col * a[..., None] + sub * (1 - a[..., None])
        halo = radial(PW, PH, cx, cy, R * 1.25, 1.0) * (1 - np.clip((radial(PW, PH, cx, cy, R, 0.01) > 0).astype(np.float32), 0, 1))
        arr = arr + hexc('#3F8CFF') * (halo * 0.5)[..., None]
        return plate_img(arr)

    def dyn(self, img, t):
        pop(img, chip('FRANCE  ·  1790s', 50, dot=(60, 90, 220)), CX, 360, t, 0.2)
        d = ImageDraw.Draw(img)
        tN, tEq = self.wt('NORTH'), self.wt('EQUATOR')
        tEq1 = self.wt('EQUATOR', 't1')
        pole = globe_screen(math.pi / 2, 0, self.c, self.R)
        if t > tN - 0.1:
            k = ease_back((t - tN + 0.1) / 0.3, 2)
            r = 18 * k
            d.ellipse((pole[0] - r, pole[1] - r, pole[0] + r, pole[1] + r), fill=(255, 255, 255), outline=(0, 0, 0), width=4)
            pop(img, chip('NORTH POLE', 40), pole[0] + 210, pole[1] - 50, t, tN)
        if t > tEq - 0.1:
            pts = []
            for lo in np.linspace(-89, 89, 80):
                x, y, z = globe_screen(0, math.radians(lo), self.c, self.R)
                pts.append((x, y))
            k = ease_out((t - tEq + 0.1) / 0.35)
            n = max(2, int(len(pts) * k))
            d.line(pts[:n], fill=(0, 0, 0, 120), width=12)
            d.line(pts[:n], fill=(255, 210, 60), width=8)
            pop(img, chip('EQUATOR', 40, bg=(255, 210, 60)), self.c[0] - 270, pts[10][1] + 60, t, tEq)
        lon0 = math.radians(28)
        prog = ease_in_out((t - tN) / max(0.4, tEq1 - tN))
        if t > tN:
            pts = []
            for la in np.linspace(90, 90 - 90 * prog, max(2, int(60 * prog))):
                x, y, z = globe_screen(math.radians(la), lon0, self.c, self.R)
                pts.append((x, y))
            d.line(pts, fill=(0, 0, 0, 140), width=16)
            d.line(pts, fill=(255, 80, 60), width=11)
            if prog >= 0.999:
                mid = globe_screen(math.radians(45), lon0, self.c, self.R)
                pop(img, chip('10,000 km', 46, bg=(255, 80, 60), fg=(255, 255, 255)), mid[0] + 190, mid[1], t, tEq1 - 0.15)
        pop(img, chip('÷ 10,000,000  =  1 METER', 50, bg=(255, 210, 60)), CX, 1730, t, self.wt('ten-millionth') - 0.05)

# ---------------------------------------------------------------- folding ruler
def pegboard():
    arr = vgrad(PW, PH, [(0, '#24464A'), (1, '#10201F')])
    arr = arr * (0.9 + 0.2 * smooth_noise(PH, PW, 60, 91, 3))[..., None]
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    for y in range(40, PH, 80):
        for x in range(40, PW, 80):
            d.ellipse((x - 9, y - 9 + 3, x + 9, y + 9 + 3), fill=(60, 95, 95))
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(8, 16, 16))
    arr = to_arr(img)
    arr = arr * (0.35 + 0.85 * radial(PW, PH, CX, 1000, 1200, 1.4))[..., None]
    return vignette(arr, 0.5)

class Folding(Scene):
    z0, z1 = 1.0, 1.05
    N, SL, SW = 5, 244, 84
    def plate(self):
        self.segs = []
        for i in range(self.N):
            tex = ruler_tex(cm=2, ppc=96, h=self.SW, base='#F6D04D', dark='#E0A92A', seed=7 + i, ink=(25, 20, 15))
            tex = tex.resize((self.SL, self.SW), Image.LANCZOS)
            d = ImageDraw.Draw(tex)
            f = font(30)
            num = str((i + 1) * 20)
            d.text((self.SL / 2 - 18, self.SW * 0.40), num, font=f, fill=(200, 30, 30))
            sh = tex.convert('RGBA')
            g = Image.new('L', sh.size, 0)
            gd = ImageDraw.Draw(g)
            for yy in range(self.SW):
                gd.line([(0, yy), (self.SL, yy)], fill=int(255 * (1.0 - 0.35 * yy / self.SW)))
            sh = Image.composite(sh, Image.new('RGBA', sh.size, (60, 40, 10, 255)), g)
            pad = Image.new('RGBA', (self.SL + 8, self.SW + 8), (0, 0, 0, 0))
            pad.paste(sh, (4, 4))
            self.segs.append(pad)
        lay = Layer(60, 60)
        sphere(lay, (30, 30), 13, '#C9A04A', spec=0.6, shin=40)
        self.rivet, _, _ = layer_sprite(lay, 2)
        return plate_img(pegboard())

    def chain(self, u):
        th = (1 - u) * math.radians(78)
        pts = [(0.0, 0.0)]
        angs = []
        for i in range(self.N):
            a = th if i % 2 == 0 else -th
            angs.append(a)
            x, y = pts[-1]
            pts.append((x + self.SL * math.cos(a), y - self.SL * math.sin(a)))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ox = CX - (min(xs) + max(xs)) / 2
        oy = 1020 - (min(ys) + max(ys)) / 2
        return [(x + ox, y + oy) for x, y in pts], angs

    def dyn(self, img, t):
        pop(img, chip('GERMANY  ·  1851', 50, dot=(240, 200, 60)), CX, 470, t, 0.2)
        tf = self.wt('FOLDING') - 1.1
        u = 0.0 + ease_in_out((t - tf) / 1.4)
        pts, angs = self.chain(u)
        # shadow
        sm = Image.new('L', (PW // 4, PH // 4), 0)
        sd = ImageDraw.Draw(sm)
        for i in range(self.N):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            sd.line([((x0 + 22) / 4, (y0 + 36) / 4), ((x1 + 22) / 4, (y1 + 36) / 4)], fill=150, width=self.SW // 4)
        sm = sm.filter(ImageFilter.GaussianBlur(5)).resize((PW, PH), Image.BILINEAR)
        img.alpha_composite(Image.merge('RGBA', (sm.point(lambda v: 0),) * 3 + (sm,)))
        order = list(range(self.N))
        for i in order:
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            a = angs[i]
            sp = self.segs[i].rotate(math.degrees(a), resample=Image.BICUBIC, expand=True)
            paste_center(img, sp, (x0 + x1) / 2, (y0 + y1) / 2)
        for p in pts[1:-1]:
            paste_center(img, self.rivet, p[0], p[1])

# ---------------------------------------------------------------- light
class Light(Scene):
    z0, z1 = 1.0, 1.06
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#03050B'), (0.5, '#08112A'), (1, '#03050B')])
        img = to_img(arr)
        d = ImageDraw.Draw(img, 'RGBA')
        vy = 900
        for k in range(-12, 13):
            d.line([(CX + k * 40, vy + 260), (CX + k * 260, PH)], fill=(60, 140, 255, 45), width=2)
        y = vy + 260
        step = 30
        while y < PH:
            d.line([(0, y), (PW, y)], fill=(60, 140, 255, 40), width=2)
            step *= 1.18
            y += step
        arr = to_arr(img)
        lay = Layer()
        # emitter box
        top = [(130, 850), (300, 850), (320, 905), (110, 905)]
        slab(lay, to_img(stone_tex(200, 60, '#5A6270', '#2A2F38', 93)), top, 110, '#2B313B', 0.5)
        arr = finish(arr, lay, (10, 20, 12, 0.5))
        lay = Layer()
        sphere(lay, (318, 958), 24, '#9FD8FF', spec=0.8, shin=50)
        arr = finish(arr, lay, None)
        lay = Layer()
        self.r0, self.r1 = 180, 1116
        top = bar_corners((self.r0 + self.r1) / 2, 1180, self.r1 - self.r0, 150, 0.0)
        slab(lay, ruler_tex(cm=10, ppc=100, h=130, label='1 METER', mult=10), top, 22, '#B98418')
        arr = finish(arr, lay, (12, 26, 14, 0.5))
        return plate_img(vignette(arr, 0.4))

    def dyn(self, img, t):
        pop(img, chip('TODAY  ·  SINCE 1983', 46, dot=(90, 200, 255)), CX, 470, t, 0.2)
        tL = self.wt('LIGHT')
        if t >= tL - 0.15:
            k = ease_in_out((t - tL + 0.15) / 0.35)
            xe = 330 + (PW - 330) * k
            band = Image.new('RGBA', (PW, 240), (0, 0, 0, 0))
            bd = ImageDraw.Draw(band)
            yb = 120
            flick = 1 + 0.06 * math.sin(t * 40)
            bd.line([(330, yb), (xe, yb)], fill=(80, 190, 255, int(230 * flick)), width=70)
            band = band.filter(ImageFilter.GaussianBlur(24))
            bd = ImageDraw.Draw(band)
            bd.line([(330, yb), (xe, yb)], fill=(150, 220, 255, 255), width=18)
            bd.line([(330, yb), (xe, yb)], fill=(255, 255, 255, 255), width=8)
            r = 26
            bd.ellipse((xe - r, yb - r, xe + r, yb + r), fill=(255, 255, 255, 220))
            img.alpha_composite(band, (0, 958 - yb))
        tS = self.wt('SPLIT')
        pop(img, chip('1 / 299,792,458 of a second', 46, bg=(90, 200, 255)), CX, 740, t, tS - 0.1)

SCENES = [HeroRuler, Desert, CubitArm, TwoArms, CopperBar, Museum, Indus, Egypt, Barley, Globe, Folding, Light, Outro]
