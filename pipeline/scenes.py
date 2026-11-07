import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, table_bg, grain_map
from mw_scenes import glow, stamp_sprite, lab_wall, bench
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of

GOLD = (240, 160, 60)
WOOD = '#B07A45'
STEEL = '#C9CED6'
FLOOR_Y = 1240

def lay_sprite(lay):
    return layer_sprite(lay, 2)

def with_shadow(img, sp, x, y, blur=14, a=0.45, dx=18, dy=24):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, x - pad + dx, y - pad + dy)
    paste_at(img, sp, x, y)

def ground_shadow(img, cx, y, w, a=0.45):
    ov = OV(img, cx - w, y - 60, cx + w, y + 60)
    ov.d.ellipse(ov.box(cx - w * 0.5, y - 18, cx + w * 0.5, y + 18), fill=(0, 0, 0, int(255 * a)))
    ov.im = ov.im.filter(ImageFilter.GaussianBlur(14))
    ov.commit()

def wall_plate(seed=3, c0='#3A2E26', c1='#140E0A'):
    arr = lab_wall(seed, c0, c1)
    arr = bench(arr, 1250, 1340)
    return plate_img(vignette(arr, 0.45))

# ---------------------------------------------------------------- grocery store backdrop
_STORE = {}
def store_plate(seed=1, blur=3.0, dark=1.0):
    key = (seed, blur, dark)
    if key in _STORE:
        return _STORE[key].copy()
    rng = np.random.default_rng(seed)
    arr = vgrad(PW, PH, [(0, '#E9DCC0'), (0.55, '#D6C29C'), (1, '#B59E78')])
    img = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(img)
    pal = [(214, 72, 56), (240, 180, 60), (70, 140, 200), (90, 170, 100), (235, 235, 225), (170, 90, 160), (230, 120, 50)]
    for sy in (520, 830, 1140):
        x = 30
        while x < PW - 60:
            kind = rng.integers(0, 3)
            col = pal[rng.integers(0, len(pal))]
            if kind == 0:  # box
                w, h = rng.integers(90, 140), rng.integers(170, 240)
                d.rounded_rectangle((x, sy - h, x + w, sy), 6, fill=col)
                d.rectangle((x + 10, sy - h * 0.65, x + w - 10, sy - h * 0.4), fill=(250, 245, 230))
                d.rectangle((x + w - 14, sy - h, x + w, sy), fill=tuple(int(c * 0.7) for c in col))
            elif kind == 1:  # cans
                w, h = 70, rng.integers(110, 140)
                for k in range(2):
                    xx = x + k * (w + 6)
                    d.rounded_rectangle((xx, sy - h, xx + w, sy), 10, fill=col)
                    d.rectangle((xx + 4, sy - h * 0.7, xx + w - 4, sy - h * 0.35), fill=(250, 245, 230))
                    d.rectangle((xx + w - 16, sy - h, xx + w - 6, sy), fill=(255, 255, 255, 90))
                w = 2 * w + 6
            else:  # jars
                w, h = 80, rng.integers(120, 160)
                d.rounded_rectangle((x, sy - h, x + w, sy), 20, fill=col)
                d.rectangle((x + 8, sy - h - 22, x + w - 8, sy - h + 6), fill=(200, 200, 205))
            x += w + rng.integers(8, 22)
        d.rectangle((0, sy, PW, sy + 34), fill=(120, 84, 50))
        d.rectangle((0, sy + 34, PW, sy + 46), fill=(70, 46, 26))
    arr = to_arr(img)
    arr = gaussian_filter(arr, (blur, blur, 0)) if blur else arr
    arr = arr * (0.9 + 0.12 * smooth_noise(PH, PW, 90, seed, 3))[..., None]
    # tiled floor
    fl = np.zeros((PH - FLOOR_Y, PW, 3), np.float32)
    yy, xx = np.mgrid[0:PH - FLOOR_Y, 0:PW].astype(np.float32)
    depth = 1 + yy / 220
    u = (xx - CX) / (90 * depth / 1.0) * 1.0
    v = np.log(depth) * 3.2
    chk = ((np.floor(u) + np.floor(v)) % 2).astype(np.float32)
    c1, c2 = hexc('#EDE6D6'), hexc('#3E5A6E')
    fl = c1 * (1 - chk[..., None]) + c2 * chk[..., None]
    fl *= np.linspace(0.85, 1.0, PH - FLOOR_Y)[:, None, None]
    arr[FLOOR_Y:] = fl
    arr[FLOOR_Y - 20:FLOOR_Y] = hexc('#5A3A22')
    arr = arr * dark * (0.55 + 0.6 * radial(PW, PH, CX, 900, 1500, 1.2))[..., None]
    out = plate_img(vignette(arr, 0.45))
    _STORE[key] = out
    return out.copy()

# ---------------------------------------------------------------- props
def wire_basket(w=420, h=260, taper=0.12, color=(205, 210, 218), handle=False, items=0, seed=0):
    ss = 2
    pad = 40
    im = Image.new('RGBA', ((w + pad * 2) * ss, (h + pad * 2 + (160 if handle else 0)) * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    oy = (160 if handle else 0) + pad
    tl, tr = (pad, oy), (pad + w, oy)
    bl, br = (pad + w * taper, oy + h), (pad + w * (1 - taper), oy + h)
    S_ = lambda p: (p[0] * ss, p[1] * ss)
    dark = tuple(int(c * 0.55) for c in color)
    rng = np.random.default_rng(seed)
    pal = [(214, 72, 56), (240, 180, 60), (70, 140, 200), (90, 170, 100), (170, 90, 160)]
    # items peeking out above rim
    for k in range(items):
        ix = pad + 30 + (w - 60) * (k + 0.5) / max(1, items) + rng.integers(-15, 15)
        iw, ih = rng.integers(60, 100), rng.integers(80, 150)
        col = pal[k % len(pal)]
        d.rounded_rectangle((S_((ix - iw / 2, oy - ih + 60)) + S_((ix + iw / 2, oy + 60))), 8 * ss, fill=col + (255,))
        d.rectangle((S_((ix - iw / 2 + 8, oy - ih * 0.5 + 60)) + S_((ix + iw / 2 - 8, oy - ih * 0.25 + 60))), fill=(250, 245, 230, 255))
    # back fill (dark interior)
    d.polygon([S_(tl), S_(tr), S_(br), S_(bl)], fill=dark + (110,))
    n = 9
    for k in range(n + 1):
        u = k / n
        top = (tl[0] + (tr[0] - tl[0]) * u, tl[1])
        bot = (bl[0] + (br[0] - bl[0]) * u, bl[1])
        d.line([S_(top), S_(bot)], fill=color + (255,), width=5 * ss)
    for k in range(1, 5):
        v = k / 5
        a = (tl[0] + (bl[0] - tl[0]) * v, tl[1] + h * v)
        b = (tr[0] + (br[0] - tr[0]) * v, tr[1] + h * v)
        d.line([S_(a), S_(b)], fill=color + (255,), width=5 * ss)
    d.line([S_(tl), S_(tr)], fill=(240, 242, 246, 255), width=12 * ss)
    d.line([S_(bl), S_(br)], fill=dark + (255,), width=10 * ss)
    d.line([S_(tl), S_(bl)], fill=color + (255,), width=9 * ss)
    d.line([S_(tr), S_(br)], fill=color + (255,), width=9 * ss)
    if handle:
        cx = pad + w / 2
        d.arc(S_((cx - w * 0.36, oy - 150)) + S_((cx + w * 0.36, oy + 150)), 180, 360, fill=(240, 242, 246, 255), width=11 * ss)
    im = im.resize((im.width // ss, im.height // ss), Image.LANCZOS)
    return im, (pad, oy)

_CART = {}
def chair_cart(stage=3, seat=True, items=0, seed=0, scale=1.0):
    """1937-style cart: wooden folding chair, wheels on the legs, wire basket on the seat.
    stage 1 = chair only, 2 = + wheels, 3 = + basket."""
    key = (stage, items, seed, scale)
    if key in _CART:
        return _CART[key]
    L = Layer(760, 900)
    kw = dict(grain=grain_map()[:900, :760], spec=0.28, shin=22)
    col = hexc(WOOD); dk = col * 0.75
    fy = 790
    # back post + backrest
    capsule(L, (210, 120), (240, 470), 15, 15, dk, **kw)
    capsule(L, (200, 150), (250, 150), 22, 22, col, **kw)
    capsule(L, (205, 240), (255, 240), 22, 22, col, **kw)
    # crossed legs
    capsule(L, (250, 470), (560, fy), 16, 16, dk, **kw)
    capsule(L, (560, 470), (250, fy), 17, 17, col, **kw)
    sphere(L, (405, 630), 14, hexc('#8A8F96'), spec=0.8, shin=40)
    # seat
    capsule(L, (220, 465), (590, 465), 20, 20, col, **kw)
    if stage >= 2:
        for x in (250, 560):
            sphere(L, (x, fy + 10), 46, hexc('#2A2C30'), spec=0.5, shin=30)
            sphere(L, (x, fy + 10), 18, hexc('#B8BDC4'), spec=0.9, shin=50)
    sp, x0, y0 = lay_sprite(L)
    sp = sp.copy()
    if stage >= 3:
        bk, (bx, by) = wire_basket(400, 230, 0.1, items=items, seed=seed)
        paste_at(sp, bk, int(405 - x0 - bk.width / 2), int(465 - x0 * 0 - y0 - by - 230 + 6))
    if scale != 1.0:
        sp = sp.resize((int(sp.width * scale), int(sp.height * scale)), Image.LANCZOS)
    # contact point = bottom centre
    _CART[key] = sp
    return sp

def modern_cart(scale=1.0):
    key = ('m', scale)
    if key in _CART:
        return _CART[key]
    bk, _ = wire_basket(520, 300, 0.16, color=(200, 206, 214))
    W_, H_ = bk.width + 160, bk.height + 260
    im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base_y = bk.height + 120
    # handle
    d.line([(bk.width - 40, 50), (bk.width + 120, 0)], fill=(210, 214, 220, 255), width=14)
    d.rounded_rectangle((bk.width + 90, -14, bk.width + 150, 22), 10, fill=(214, 72, 56, 255))
    # undercarriage
    d.line([(90, bk.height - 20), (110, base_y)], fill=(180, 186, 194, 255), width=12)
    d.line([(bk.width - 70, bk.height - 20), (bk.width - 60, base_y)], fill=(180, 186, 194, 255), width=12)
    d.line([(90, base_y), (bk.width - 40, base_y)], fill=(180, 186, 194, 255), width=14)
    for x in (110, bk.width - 70):
        d.ellipse((x - 38, base_y + 20, x + 38, base_y + 96), fill=(40, 42, 46, 255))
        d.ellipse((x - 14, base_y + 44, x + 14, base_y + 72), fill=(190, 195, 200, 255))
    im.alpha_composite(bk, (0, 0))
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    _CART[key] = im
    return im

def stroller_sprite():
    ss = 2
    w, h = 620, 640
    im = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda *p: tuple(v * ss for v in p)
    body = (88, 128, 168)
    d.chord(s(80, 150, 480, 470), 0, 180, fill=body + (255,))
    d.pieslice(s(70, 60, 330, 330), 180, 270, fill=tuple(int(c * 0.75) for c in body) + (255,))
    d.line(s(80, 310, 480, 310), fill=(240, 240, 240, 255), width=10 * ss)
    d.line(s(470, 300, 590, 140), fill=(60, 60, 66, 255), width=12 * ss)
    d.line(s(560, 140, 610, 140), fill=(60, 60, 66, 255), width=16 * ss)
    for x in (150, 420):
        d.line(s(x, 440, x, 520), fill=(60, 60, 66, 255), width=8 * ss)
        d.ellipse(s(x - 70, 470, x + 70, 610), outline=(40, 40, 44, 255), width=16 * ss)
        d.ellipse(s(x - 12, 528, x + 12, 552), fill=(190, 190, 196, 255))
        for k in range(6):
            a = k * math.pi / 3
            d.line(s(x, 540, x + 62 * math.cos(a), 540 + 62 * math.sin(a)), fill=(150, 150, 156, 255), width=3 * ss)
    return im.resize((w, h), Image.LANCZOS)

def money_sprite(seed=0, w=360, h=160):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(170, 198, 150, 255), outline=(70, 100, 62, 255), width=6)
    d.rectangle((14, 14, w - 15, h - 15), outline=(90, 125, 80, 255), width=3)
    d.ellipse((w / 2 - 55, h / 2 - 50, w / 2 + 55, h / 2 + 50), fill=(206, 222, 192, 255), outline=(90, 125, 80, 255), width=4)
    f = font(76); bb = f.getbbox('$')
    d.text((w / 2 - (bb[2] + bb[0]) / 2, h / 2 - (bb[3] + bb[1]) / 2), '$', font=f, fill=(60, 95, 55, 255))
    return im

# ---------------------------------------------------------------- figures
_FIG = {}
def figure(Hh=760, kind='man', push=True, step=0.0, color=ARM_LIGHT):
    """Wooden mannequin in side view facing right; arms forward when pushing. step: walk phase."""
    key = (Hh, kind, push, round(step, 2), color)
    if key in _FIG:
        return _FIG[key]
    lay = Layer(int(Hh * 0.9), int(Hh * 1.08))
    col = hexc(color); j = col * 0.86
    kw = dict(grain=grain_map()[:lay.h, :lay.w], spec=0.28, shin=22)
    cx, yf = lay.w * 0.4, lay.h - 10
    P = lambda u, v: (cx + u * Hh, yf - Hh + v * Hh)
    sw = math.sin(step * 2 * math.pi) * 0.09
    for s, c in ((-1, j * 0.9), (1, col)):
        hip = P(0, 0.50)
        knee = P(0.03 + s * sw * 0.5, 0.73)
        ank = P(s * sw, 0.945)
        capsule(lay, hip, knee, 0.05 * Hh, 0.04 * Hh, c, **kw)
        capsule(lay, knee, ank, 0.039 * Hh, 0.028 * Hh, c, **kw)
        sphere(lay, knee, 0.042 * Hh, c * 0.95, **kw)
        ellipsoid(lay, (ank[0] + 0.03 * Hh, ank[1] + 0.025 * Hh), 0.05 * Hh, 0.024 * Hh, 0, c, **kw)
    if kind == 'woman':
        fill_poly(lay, [P(-0.07, 0.43), P(0.07, 0.43), P(0.14, 0.70), P(-0.14, 0.70)], '#C0504A')
    ellipsoid(lay, P(0, 0.48), 0.09 * Hh, 0.06 * Hh, 0, col, **kw)
    ellipsoid(lay, P(0, 0.30), 0.085 * Hh, 0.13 * Hh, 0.08, col, **kw)
    capsule(lay, P(0.01, 0.175), P(0.015, 0.135), 0.03 * Hh, 0.027 * Hh, col, **kw)
    ellipsoid(lay, P(0.02, 0.075), 0.058 * Hh, 0.07 * Hh, 0, col, **kw)
    if kind == 'man':
        capsule(lay, P(-0.05, 0.02), P(0.09, 0.02), 0.022 * Hh, 0.022 * Hh, hexc('#4A3A2E'), spec=0.2)
        ellipsoid(lay, P(0.015, 0.0), 0.055 * Hh, 0.035 * Hh, 0, hexc('#4A3A2E'), spec=0.2)
    else:
        ellipsoid(lay, P(-0.04, 0.05), 0.04 * Hh, 0.04 * Hh, 0, hexc('#C0504A'), spec=0.3)
    sh = P(0.01, 0.21)
    if push:
        el, wr = P(0.12, 0.34), P(0.27, 0.36)
    else:
        el, wr = P(0.03, 0.37), P(0.04, 0.52)
    capsule(lay, sh, el, 0.034 * Hh, 0.028 * Hh, col, **kw)
    capsule(lay, el, wr, 0.028 * Hh, 0.022 * Hh, col, **kw)
    sphere(lay, sh, 0.04 * Hh, j, **kw)
    sphere(lay, el, 0.03 * Hh, j, **kw)
    sphere(lay, wr, 0.03 * Hh, col, **kw)
    sp, x0, y0 = lay_sprite(lay)
    info = {'foot': (cx - x0, yf - y0), 'hand': (wr[0] - x0, wr[1] - y0)}
    _FIG[key] = (sp, info)
    return _FIG[key]

def draw_cart_at(img, sp, cx, floor, shadow=True):
    if shadow:
        ground_shadow(img, cx, floor + 6, sp.width * 1.1, 0.5)
    paste_at(img, sp, int(cx - sp.width / 2), int(floor - sp.height + 8))

def draw_pusher(img, kind, foot_x, floor, step, Hh=700, cart_scale=0.62, items=0, seed=0):
    sp, info = figure(Hh, kind, True, round((step % 1) * 12) / 12)
    cart = chair_cart(3, items=items, seed=seed, scale=cart_scale)
    ground_shadow(img, foot_x, floor + 6, 260, 0.45)
    paste_at(img, sp, int(foot_x - info['foot'][0]), int(floor - info['foot'][1]))
    hx = foot_x - info['foot'][0] + info['hand'][0]
    draw_cart_at(img, cart, hx + cart.width / 2 - 20, floor)

def red_x(img, cx, cy, r, k):
    if k <= 0:
        return
    ov = OV(img, cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 20)
    q = clamp01(k * 2)
    ov.d.line(ov.pts([(cx - r, cy - r), (cx - r + 2 * r * q, cy - r + 2 * r * q)]), fill=(226, 40, 40, 255), width=34)
    q2 = clamp01(k * 2 - 1)
    if q2 > 0:
        ov.d.line(ov.pts([(cx + r, cy - r), (cx + r - 2 * r * q2, cy - r + 2 * r * q2)]), fill=(226, 40, 40, 255), width=34)
    ov.commit()

# ====================================================================== scenes
class Hook(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('FAKE'), 18, 0.35)]
    def events(self):
        return [(0.1, 'swipe', 0.6), (0.2, 'squeak', 0.5), (self.we('inventor'), 'pop', 0.5), (self.we('FAKE'), 'thud', 0.9)]
    def plate(self):
        self.cart = chair_cart(3)
        self.stamp = stamp_sprite('FAKE SHOPPERS', 120)
        return store_plate(1)
    def roll_x(self, t):
        return CX + 700 * (1 - ease_out(t / 0.9))
    def dyn(self, img, t):
        draw_cart_at(img, self.cart, self.roll_x(t), FLOOR_Y + 60)
        pop(img, C('THE FIRST SHOPPING CART', 48, dot=GOLD), CX, 300, t, 0.25, out_t=self.we('inventor') - 0.15)
        pop(img, C('NOBODY WANTED IT', 50, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 300, t, self.we('inventor') - 0.05, out_t=self.we('FAKE') - 0.12)
        stamp_in(img, self.stamp, CX, 330, t, self.we('FAKE'))

class Goldman(S):
    def events(self):
        return [(0.1, 'pop', 0.5), (self.we('Sylvan') - 0.05, 'pop', 0.5), (self.we('Humpty') - 0.05, 'ding', 0.6)]
    def plate(self):
        img = store_plate(2, blur=6, dark=0.8)
        sp, info = figure(860, 'man', push=False)
        ground_shadow(img, CX - 260, FLOOR_Y + 70, 300)
        paste_at(img, sp, int(CX - 260 - info['foot'][0]), int(FLOOR_Y + 70 - info['foot'][1]))
        return img
    def dyn(self, img, t):
        pop(img, C('1930s  ·  OKLAHOMA CITY', 48, dot=GOLD), CX, 300, t, 0.1, out_t=self.we('Sylvan') - 0.2)
        pop(img, C('GROCER SYLVAN GOLDMAN', 48, dot=GOLD), CX, 300, t, self.we('Sylvan') - 0.05)
        tH = self.we('Humpty') - 0.05
        if t > tH:
            pop(img, C('HUMPTY DUMPTY', 54, bg=(255, 210, 60)), CX + 230, 620, t, tH)
            pop(img, C('GROCERY STORES', 44), CX + 230, 740, t, tH + 0.12)

class Heavy(S):
    focus = (CX, 950)
    def make_shakes(self):
        return [(self.we('HEAVY'), 16, 0.35)]
    def events(self):
        return [(0.1, 'swipe', 0.5), (self.we('STOPPED'), 'buzzer', 0.4), (self.we('baskets'), 'rattle', 0.5), (self.we('HEAVY'), 'thud', 0.9)]
    def plate(self):
        self.baskets = [wire_basket(460, 280, 0.12, handle=True, items=n, seed=3)[0] for n in range(6)]
        self.hand = get_hand(520, 3 * math.pi / 4)
        self.stamp = stamp_sprite('TOO HEAVY!', 105, angle=-5)
        return store_plate(3, blur=7, dark=0.75)
    def dyn(self, img, t):
        tB, tH = self.we('baskets'), self.we('HEAVY')
        n = int(clamp01((t - tB + 0.6) / 1.0) * 5.99)
        bk = self.baskets[n]
        sag = 120 * ease_out((t - tH) / 0.3) if t > tH else 0
        cy = 700 + sag * 0.8 + 6 * math.sin(t * 5)
        ground_shadow(img, CX, FLOOR_Y + 40, 420, 0.35)
        paste_center(img, bk, CX, cy)
        draw_hand(img, self.hand, (CX - 10, cy - bk.height / 2 + 75), 0.1)
        pop(img, C('SHOPPERS STOPPED BUYING', 46, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 1170, t, self.we('STOPPED') - 0.05, out_t=tH - 0.1)
        stamp_in(img, self.stamp, CX, 1170, t, tH)

class Build(S):
    focus = (CX, 960)
    def events(self):
        return [(self.we('Fred') - 0.05, 'pop', 0.5), (self.we('FOLDING'), 'thud', 0.7), (self.we('WHEELS'), 'bigpop', 0.5),
                (self.we('BASKET'), 'rattle', 0.6)]
    def plate(self):
        self.st = [chair_cart(s) for s in (1, 2, 3)]
        return wall_plate(4, '#3A2E26', '#140E0A')
    def dyn(self, img, t):
        tF, tW, tB = self.we('FOLDING'), self.we('WHEELS'), self.we('BASKET')
        pop(img, C('MECHANIC FRED YOUNG', 46, dot=GOLD), CX, 300, t, self.we('Fred') - 0.05, out_t=tF - 0.15)
        if t > tF - 0.1:
            stage = 3 if t > tB else (2 if t > tW else 1)
            sp = self.st[stage - 1]
            drop = 0
            if stage == 1:
                drop = -400 * (1 - ease_back((t - tF + 0.1) / 0.35, 1.5))
            elif stage == 3:
                drop = 0
            cy = 1250 - sp.height / 2 + drop
            sc = 1.0 + (0.06 * (1 - ease_out((t - (tW if stage == 2 else tB)) / 0.25)) if stage > 1 else 0)
            ground_shadow(img, CX, 1262, sp.width, 0.5)
            paste_center(img, sp, CX, cy - (sp.height * (sc - 1)) / 2, scale=sc)
            pop(img, C('FOLDING CHAIR', 46), CX, 300, t, tF, out_t=tW - 0.1)
            pop(img, C('+ WHEELS', 50, bg=(255, 210, 60)), CX, 300, t, tW, out_t=tB - 0.1)
            pop(img, C('+ BASKET = CART', 50, bg=(255, 210, 60)), CX, 300, t, tB)

class Launch(S):
    def make_shakes(self):
        return [(self.we('June'), 14, 0.3)]
    def events(self):
        return [(self.we('June'), 'thud', 0.9), (self.we('rolled') - 0.1, 'squeak', 0.5)]
    def plate(self):
        self.cart = chair_cart(3, scale=0.55)
        self.stamp = stamp_sprite('JUNE 4, 1937', 110, color=(200, 40, 40), angle=-7)
        return store_plate(4)
    def dyn(self, img, t):
        tR = self.we('rolled') - 0.15
        for k in range(3):
            x0 = 250 + k * 400
            u = ease_out((t - tR - k * 0.08) / 0.6)
            x = x0 - 900 * (1 - u)
            draw_cart_at(img, self.cart, x, FLOOR_Y + 60)
        stamp_in(img, self.stamp, CX, 360, t, self.we('June'))

class Nobody(S):
    z0, z1 = 1.1, 1.16
    def make_shakes(self):
        return [(self.we('NOBODY'), 12, 0.3)]
    def events(self):
        return [(self.we('NOBODY'), 'buzzer', 0.6)]
    def plate(self):
        img = store_plate(4, dark=0.7)
        cart = chair_cart(3, scale=0.55)
        for k in range(3):
            draw_cart_at(img, cart, 250 + k * 400, FLOOR_Y + 60)
        self.stamp = stamp_sprite('NOBODY', 150, angle=-8)
        return img
    def dyn(self, img, t):
        pop(img, C('0 TAKERS', 54, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 300, t, 0.05)
        stamp_in(img, self.stamp, CX, 760, t, self.we('NOBODY'))

class Men(S):
    def events(self):
        return [(0.1, 'swipe', 0.5), (self.we('pushing'), 'squeak', 0.4), (self.we('looked'), 'trombone', 0.6)]
    def plate(self):
        return store_plate(5, blur=5, dark=0.85)
    def dyn(self, img, t):
        fx = 330 + 90 * ease_in_out(t / 1.5)
        draw_pusher(img, 'man', fx, FLOOR_Y + 60, t * 1.2)
        pop(img, C('MEN', 56, bg=(70, 140, 200), fg=(255, 255, 255)), CX, 300, t, 0.05)
        tL = self.we('looked')
        if t > tL - 0.05:
            pop(img, C('"UNMANLY"', 60, bg=(255, 210, 60)), CX, 450, t, tL - 0.05)
            red_x(img, CX + 40, 900, 170, (t - tL) / 0.35)

class Women(S):
    def events(self):
        return [(0.1, 'swipe', 0.5), (self.we('BABY') - 0.05, 'pop', 0.6), (self.we('STROLLERS'), 'thud', 0.6)]
    def plate(self):
        self.strl = stroller_sprite()
        self.stamp = stamp_sprite('NO THANKS', 120, angle=-7)
        return store_plate(6, blur=5, dark=0.85)
    def dyn(self, img, t):
        pop(img, C('WOMEN', 56, bg=(192, 80, 74), fg=(255, 255, 255)), CX, 300, t, 0.05)
        sp, info = figure(700, 'woman', push=False)
        ground_shadow(img, 300, FLOOR_Y + 66, 260)
        paste_at(img, sp, int(300 - info['foot'][0]), int(FLOOR_Y + 60 - info['foot'][1]))
        tB = self.we('BABY') - 0.1
        if t > tB:
            k = ease_back((t - tB) / 0.4, 1.6)
            ground_shadow(img, 820, FLOOR_Y + 66, 420)
            paste_center(img, self.strl, 820, FLOOR_Y + 60 - self.strl.height / 2 + 200 * (1 - clamp01(k)), scale=max(0.05, min(1.0, 0.5 + 0.5 * k)))
            pop(img, C('ENOUGH BABY STROLLERS', 44, bg=(255, 210, 60)), CX, 440, t, tB, out_t=self.we('STROLLERS') - 0.05)
        stamp_in(img, self.stamp, CX + 100, 520, t, self.we('STROLLERS') + 0.05)

class Models(S):
    z0, z1 = 1.0, 1.08
    def events(self):
        return [(self.we('MODELS'), 'ding', 0.7), (self.we('men') - 0.05, 'pop', 0.5), (self.we('women') - 0.05, 'pop', 0.5), (self.we('stroll'), 'squeak', 0.4)]
    def plate(self):
        return store_plate(7, blur=4)
    def dyn(self, img, t):
        tM = self.we('MODELS')
        pop(img, C('HE HIRED MODELS', 52, bg=(255, 210, 60)), CX, 300, t, tM - 0.05)
        if t > self.we('men') - 0.05:
            pop(img, C('MEN', 44, bg=(70, 140, 200), fg=(255, 255, 255)), CX - 140, 430, t, self.we('men') - 0.05)
        if t > self.we('women') - 0.05:
            pop(img, C('WOMEN', 44, bg=(192, 80, 74), fg=(255, 255, 255)), CX + 140, 430, t, self.we('women') - 0.05)
        # two pushers stroll across
        for k, kind in enumerate(('woman', 'man')):
            x = -450 + 220 * t - k * 620 + 200
            draw_pusher(img, kind, x + 650, FLOOR_Y + 60, t * 1.3 + k * 0.5, Hh=620, cart_scale=0.55, items=3, seed=k)

class Caught(S):
    def make_shakes(self):
        return [(self.we('made'), 10, 0.3)]
    def events(self):
        return [(self.we('real'), 'pop', 0.5), (self.we('ON'), 'chime', 0.6), (self.we('made'), 'cash', 0.9)]
    def plate(self):
        self.bills = [money_sprite(k) for k in range(7)]
        return store_plate(8, blur=4)
    def dyn(self, img, t):
        tM = self.we('made')
        kinds = ('man', 'woman', 'man')
        for k in range(3):
            x = 120 + k * 380 + 60 * t
            draw_pusher(img, kinds[k], x, FLOOR_Y + 60, t * 1.2 + k * 0.3, Hh=480, cart_scale=0.42, items=3, seed=k + 2)
        pop(img, C('REAL SHOPPERS CAUGHT ON', 46, dot=(110, 200, 120)), CX, 300, t, self.we('real') - 0.05, out_t=tM - 0.1)
        for k, b in enumerate(self.bills):
            tk = tM - 0.1 + k * 0.07
            if t < tk:
                continue
            q = ease_out((t - tk) / 0.35)
            paste_center(img, b.rotate(-14 + 6 * k, expand=True, resample=Image.BICUBIC), 220 + 140 * k, 120 + 620 * q - 40 * (k % 2))
        pop(img, C('MULTIMILLIONAIRE', 62, bg=(110, 200, 120)), CX, 300, t, tM + 0.1)

class Twist(S):
    def make_shakes(self):
        return [(self.we('NEST') + 0.15, 12, 0.3)]
    def events(self):
        return [(0.05, 'scratch', 0.7), (self.we('NEST'), 'rattle', 0.7), (self.we('Orla') - 0.05, 'pop', 0.6), (self.we('LICENSING'), 'thud', 0.9)]
    def plate(self):
        self.mc = modern_cart(0.95)
        self.stamp = stamp_sprite('LICENSED', 130, color=(40, 120, 200), angle=-7)
        return store_plate(9, blur=6, dark=0.85)
    def dyn(self, img, t):
        tN, tO, tL = self.we('NEST'), self.we('Orla'), self.we('LICENSING')
        pop(img, C('THE TWIST', 56, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 300, t, 0.05, out_t=tN - 0.2)
        pop(img, C('CARTS THAT NEST', 50, bg=(255, 210, 60)), CX, 300, t, tN - 0.1, out_t=tO - 0.2)
        pop(img, C('INVENTOR ORLA WATSON', 48, dot=GOLD), CX, 300, t, tO - 0.05, out_t=tL - 0.12)
        u = ease_in_out((t - tN + 0.1) / 0.7)
        sp = self.mc
        floor = FLOOR_Y + 40
        xa = CX - 120
        xb = CX + 230 - 240 * u
        draw_cart_at(img, sp, xa, floor)
        draw_cart_at(img, sp, xb, floor, shadow=False)
        stamp_in(img, self.stamp, CX, 330, t, tL)

class Outro(Hook):
    def make_shakes(self):
        return [(self.we('nobody'), 14, 0.3)]
    def events(self):
        return [(0.1, 'swipe', 0.6), (self.we('nobody'), 'thud', 0.8)]
    def dyn(self, img, t):
        draw_cart_at(img, self.cart, CX, FLOOR_Y + 60)
        pop(img, C('ALL BECAUSE OF A CART...', 46, dot=GOLD), CX, 300, t, 0.1, out_t=self.we('nobody') - 0.15)
        pop(img, C('NOBODY WANTED IT', 50, bg=(200, 60, 50), fg=(255, 255, 255)), CX, 300, t, self.we('nobody') - 0.05)

SCENES = [Hook, Goldman, Heavy, Build, Launch, Nobody, Men, Women, Models, Caught, Twist, Outro]
