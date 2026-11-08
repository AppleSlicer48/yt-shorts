import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, dark_room
from mw_scenes import glow, stamp_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import with_shadow, ground_shadow, wall_plate, money_sprite, figure, red_x

GOLD = (240, 160, 60)
RED = (200, 60, 50)
YEL = (255, 210, 60)
DISC_RED = (222, 58, 48)

# ====================================================================== props
_SP = {}
def _ss(im, w, h):
    return im.resize((w, h), Image.LANCZOS)

def disc_sprite(R=300, color=DISC_RED, tilt=0.42, ridges=True, metal=False, fluted=False, pie=False):
    """A flying disc / pie tin seen at an angle: ellipse with rim, rings and a soft highlight."""
    key = ('disc', R, color, tilt, ridges, metal, fluted, pie)
    if key in _SP:
        return _SP[key]
    ss = 3
    rx, ry = R, R * tilt
    th = R * 0.14  # rim thickness
    w, h = int(2 * rx + 40), int(2 * ry + th + 40)
    im = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda *p: tuple(v * ss for v in p)
    cx, cy = w / 2, 20 + ry
    col = np.array(color, np.float32)
    dk = tuple(int(c) for c in col * 0.55)
    md = tuple(int(c) for c in col * 0.78)
    # side wall (rim thickness)
    d.ellipse(s(cx - rx, cy - ry + th, cx + rx, cy + ry + th), fill=dk + (255,))
    d.rectangle(s(cx - rx, cy, cx + rx, cy + th), fill=dk + (255,))
    d.ellipse(s(cx - rx, cy - ry, cx + rx, cy + ry), fill=md + (255,))
    # top surface
    inset = R * (0.1 if not (metal or pie) else 0.14)
    d.ellipse(s(cx - rx + inset, cy - ry + inset * tilt, cx + rx - inset, cy + ry - inset * tilt), fill=tuple(int(c) for c in col) + (255,))
    if fluted:
        for k in range(48):
            a = k / 48 * 2 * math.pi
            x0, y0 = cx + (rx - inset * 0.15) * math.cos(a), cy + (ry - inset * 0.15 * tilt) * math.sin(a)
            x1, y1 = cx + (rx - inset * 0.95) * math.cos(a), cy + (ry - inset * 0.95 * tilt) * math.sin(a)
            d.line(s(x0, y0, x1, y1), fill=dk + (200,), width=3 * ss)
    if pie:
        pc = (226, 168, 84)
        d.ellipse(s(cx - rx + inset, cy - ry + inset * tilt - 6, cx + rx - inset, cy + ry - inset * tilt - 6), fill=pc + (255,))
        for k in range(6):
            a = k / 6 * 2 * math.pi + 0.3
            x0, y0 = cx + rx * 0.12 * math.cos(a), cy - 6 + ry * 0.12 * math.sin(a)
            x1, y1 = cx + rx * 0.5 * math.cos(a), cy - 6 + ry * 0.5 * math.sin(a)
            d.line(s(x0, y0, x1, y1), fill=(170, 110, 50, 255), width=8 * ss)
    elif ridges:
        for f in (0.5, 0.58, 0.66, 0.74):
            d.ellipse(s(cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f), outline=dk + (150,), width=4 * ss)
    elif metal:
        d.ellipse(s(cx - rx * 0.55, cy - ry * 0.55, cx + rx * 0.55, cy + ry * 0.55), outline=dk + (120,), width=3 * ss)
    im = _ss(im, w, h)
    hl = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((cx - rx * 0.75, cy - ry * 0.85, cx + rx * 0.05, cy - ry * 0.2), fill=(255, 255, 255, 120 if metal else 80))
    hl = hl.filter(ImageFilter.GaussianBlur(R * 0.08))
    a = np.minimum(np.asarray(hl.getchannel('A'), np.float32), np.asarray(im.getchannel('A'), np.float32))
    hl.putalpha(Image.fromarray(a.astype(np.uint8)))
    im.alpha_composite(hl)
    _SP[key] = im
    return im

TIN = (196, 200, 208)

def coin_sprite(R, label, color=(205, 206, 210)):
    key = ('coin', R, label, color)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (2 * R + 20, 2 * R + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dk = tuple(int(c * 0.6) for c in color)
    d.ellipse((10, 20, 10 + 2 * R, 20 + 2 * R), fill=dk + (255,))
    d.ellipse((10, 10, 10 + 2 * R, 10 + 2 * R), fill=color + (255,))
    d.ellipse((10 + R * 0.12, 10 + R * 0.12, 10 + R * 1.88, 10 + R * 1.88), outline=dk + (255,), width=max(3, R // 18))
    f = font(int(R * 0.8))
    bb = f.getbbox(label)
    d.text((10 + R - (bb[0] + bb[2]) / 2, 10 + R - (bb[1] + bb[3]) / 2), label, font=f, fill=dk + (255,))
    _SP[key] = im
    return im

def urn_sprite():
    if 'urn' in _SP:
        return _SP['urn']
    L = Layer(420, 560)
    col = hexc('#3E6E8C')
    ellipsoid(L, (210, 330), 150, 190, 0, col, spec=0.6, shin=40)
    capsule(L, (210, 150), (210, 110), 70, 70, col * 0.9, spec=0.6, shin=40)
    ellipsoid(L, (210, 95), 105, 26, 0, col * 1.1, spec=0.6, shin=40)
    sphere(L, (210, 60), 30, hexc('#C9A24A'), spec=0.8, shin=50)
    capsule(L, (210, 470), (210, 505), 60, 90, col * 0.85, spec=0.5)
    ellipsoid(L, (210, 515), 110, 26, 0, col * 0.8, spec=0.5)
    sp, _, _ = layer_sprite(L, 2)
    _SP['urn'] = sp
    return sp

def frame_sprite(w=520, h=420):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(168, 124, 58, 255))
    d.rectangle((22, 22, w - 23, h - 23), fill=(110, 76, 34, 255))
    d.rectangle((38, 38, w - 39, h - 39), fill=(236, 228, 210, 255))
    return im

# ====================================================================== backdrops
_PL = {}
HZ = 1180

def sky_plate(kind='park', seed=1):
    key = (kind, seed)
    if key in _PL:
        return _PL[key].copy()
    hz = HZ
    if kind == 'beach':
        arr = vgrad(PW, PH, [(0, '#3D86C6'), (0.4, '#8CC4E8'), (0.51, '#D8ECF4'), (1, '#D8ECF4')])
        arr = arr + hexc('#FFF2C0') * (radial(PW, PH, 1000, 380, 600, 2.0) * 0.5)[..., None]
        sea = vgrad(PW, 160, [(0, '#2E7FB0'), (1, '#5FB0D0')])
        arr[hz - 160:hz] = sea
        arr[hz - 8:hz + 6] = hexc('#F2F6F4')
        sand = vgrad(PW, PH - hz, [(0, '#F0D49A'), (1, '#C9A062')])
        arr[hz:] = sand * (0.92 + 0.12 * smooth_noise(PH - hz, PW, 30, seed, 3))[..., None]
    else:
        arr = vgrad(PW, PH, [(0, '#4D92D0'), (0.45, '#A8D4EE'), (1, '#A8D4EE')])
        img = to_img(arr)
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(seed)
        x = -40
        while x < PW:
            bw = int(rng.integers(260, 420)); bh = int(rng.integers(380, 620))
            d.rectangle((x, hz - bh, x + bw, hz), fill=(150, 72, 52))
            d.polygon([(x - 10, hz - bh), (x + bw / 2, hz - bh - 140), (x + bw + 10, hz - bh)], fill=(90, 52, 44))
            for wy in range(hz - bh + 60, hz - 60, 120):
                for wx in range(x + 40, x + bw - 50, 90):
                    d.rectangle((wx, wy, wx + 46, wy + 70), fill=(240, 226, 170))
            x += bw + int(rng.integers(20, 60))
        arr = to_arr(img)
        arr = gaussian_filter(arr, (5, 5, 0))
        lawn = vgrad(PW, PH - hz, [(0, '#6DB45A'), (1, '#3E7E38')])
        arr[hz:] = lawn * (0.9 + 0.16 * smooth_noise(PH - hz, PW, 20, seed, 3))[..., None]
    out = plate_img(vignette(arr, 0.4))
    _PL[key] = out
    return out.copy()

def bakery_plate(seed=3):
    key = ('bakery', seed)
    if key in _PL:
        return _PL[key].copy()
    img = wall_plate(seed, '#5A3A26', '#1E120A')
    d = ImageDraw.Draw(img)
    sy = 760
    d.rectangle((90, sy, PW - 90, sy + 26), fill=(120, 80, 46, 255))
    d.rectangle((90, sy + 26, PW - 90, sy + 40), fill=(70, 44, 24, 255))
    pie = disc_sprite(120, TIN, 0.4, ridges=False, metal=True, pie=True)
    for k in range(4):
        x = 190 + k * 300
        paste_at(img, pie, int(x - pie.width / 2), int(sy - pie.height + 14))
    _PL[key] = img
    return img.copy()

def museum_plate():
    if 'museum' in _PL:
        return _PL['museum'].copy()
    arr = dark_room('#3A3440', '#121016', spot=(CX, 820, 900), strength=1.0)
    img = plate_img(arr)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1250, PW, PH), fill=(60, 44, 34, 255))
    d.rectangle((0, 1240, PW, 1256), fill=(30, 22, 18, 255))
    _PL['museum'] = img
    return img.copy()

# ====================================================================== helpers
def fly_disc(img, sp, x, y, t, spin=1.0, scale=1.0, wob=4.0):
    ang = wob * math.sin(t * 7 * spin)
    rs = sp.rotate(ang, resample=Image.BICUBIC, expand=True) if abs(ang) > 0.05 else sp
    paste_center(img, rs, x, y, scale=scale)

def speed_lines(img, x, y, dx, n=4, a=120):
    ov = OV(img, min(x, x + dx) - 20, y - 120, max(x, x + dx) + 20, y + 120)
    for k in range(n):
        yy = y - 70 + k * 46
        ov.d.line(ov.pts([(x, yy), (x + dx * (0.6 + 0.1 * k), yy)]), fill=(255, 255, 255, a), width=8)
    ov.commit()

def put_figure(img, kind, foot_x, floor, Hh, push, flip=False):
    sp, info = figure(Hh, kind, push=push)
    fx = info['foot'][0]
    if flip:
        sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        fx = sp.width - fx
    ground_shadow(img, foot_x, floor + 6, Hh * 0.36)
    paste_at(img, sp, int(foot_x - fx), int(floor - info['foot'][1]))

# ====================================================================== scenes
class Hook(S):
    z0, z1 = 1.04, 1.14
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('HATED'), 18, 0.35)]
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('PIE') - 0.05, 'pop', 0.6), (self.we('HATED'), 'thud', 0.9)]
    def plate(self):
        self.disc = disc_sprite(300)
        self.tin = disc_sprite(170, TIN, 0.42, ridges=False, metal=True, fluted=True)
        st = stamp_sprite('HE HATED IT', 110, color=(220, 30, 30), angle=0)
        bg = Image.new('RGBA', st.size, (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((22, 22, st.width - 22, st.height - 22), 28, fill=(255, 250, 240, 230))
        bg.alpha_composite(st)
        self.stamp = bg.rotate(-6, resample=Image.BICUBIC, expand=True)
        return sky_plate('park', 2)
    def dyn(self, img, t):
        u = ease_out(t / 0.8)
        x = CX + 900 * (1 - u)
        y = 680 - 120 * (1 - u) + 14 * math.sin(t * 3)
        if u < 0.98:
            speed_lines(img, x + 300, y, 380 * (1 - u) + 60)
        ground_shadow(img, CX, 1300, 380, 0.25)
        fly_disc(img, self.disc, x, y, t)
        tP = self.we('PIE') - 0.05
        if t > tP:
            k = ease_back((t - tP) / 0.4, 1.8)
            fly_disc(img, self.tin, CX + 330, 470, t + 1, scale=max(0.05, k))
        pop(img, C('THE FRISBEE', 52, dot=GOLD), CX, 300, t, 0.15, out_t=tP - 0.1)
        pop(img, C('NAMED AFTER A PIE COMPANY', 46, bg=YEL), CX, 300, t, tP)
        stamp_in(img, self.stamp, CX, 1090, t, self.we('HATED'))

class Bakery(S):
    focus = (CX, 1000)
    def make_shakes(self):
        return [(self.we('1871'), 12, 0.3)]
    def events(self):
        return [(self.we('1871'), 'thud', 0.8), (self.we('William') - 0.05, 'pop', 0.5), (self.we('opened'), 'ding', 0.6)]
    def plate(self):
        self.stamp = stamp_sprite('1871', 150, color=(200, 40, 40), angle=-7)
        self.pie = disc_sprite(260, TIN, 0.42, ridges=False, metal=True, pie=True)
        img = bakery_plate()
        d = ImageDraw.Draw(img)
        d.rectangle((0, 1250, PW, 1300), fill=(150, 104, 60, 255))
        d.rectangle((0, 1300, PW, PH), fill=(70, 46, 26, 255))
        return img
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 330, t, self.we('1871'))
        tW, tO = self.we('William') - 0.05, self.we('opened')
        pop(img, C('BAKER WILLIAM FRISBIE', 46, dot=GOLD), CX, 540, t, tW)
        if t > tO - 0.1:
            k = ease_back((t - tO + 0.1) / 0.45, 1.6)
            ground_shadow(img, CX, 1262, 300, 0.45)
            paste_center(img, self.pie, CX, 1262 - self.pie.height / 2 + 300 * (1 - clamp01(k)), scale=max(0.05, min(1.05, k)))
            pop(img, C('FRISBIE PIE COMPANY', 50, bg=YEL), CX, 960, t, tO + 0.2)

class Campus(S):
    def events(self):
        return [(0.1, 'pop', 0.4), (self.we('college') - 0.05, 'pop', 0.5), (self.we('tossed'), 'swipe', 0.8), (self.we('its'), 'wind', 0.5)]
    def plate(self):
        self.tin = disc_sprite(150, TIN, 0.4, ridges=False, metal=True, fluted=True)
        self.hand = get_hand(560, -math.pi / 7)
        return sky_plate('park', 3)
    def dyn(self, img, t):
        pop(img, C('AS THE STORY GOES...', 46, bg=(40, 40, 46), fg=(255, 255, 255)), CX, 300, t, 0.05, out_t=self.we('college') - 0.15)
        pop(img, C('COLLEGE STUDENTS', 50, dot=GOLD), CX, 300, t, self.we('college') - 0.05)
        tT = self.we('tossed') - 0.1
        hx, hy = 260, 1080
        if t < tT:
            draw_hand(img, self.hand, (hx, hy), 0.0)
            fly_disc(img, self.tin, hx + 40, hy - 30, t, wob=0)
        else:
            q = t - tT
            for k in range(3):
                tk = q - k * 0.45
                if tk <= 0:
                    continue
                u = tk / 1.3
                x = hx + 40 + 1000 * u
                y = hy - 30 - 520 * math.sin(min(u, 1.2) * 1.3) + 260 * u * u
                if x < PW + 200:
                    fly_disc(img, self.tin, x, y, t + k, spin=2.0, wob=10)
            e = ease_out(q / 0.2)
            draw_hand(img, self.hand, (hx + 60 * e, hy - 40 * e), 0.1)
        pop(img, C('EMPTY PIE TINS', 50, bg=YEL), CX, 450, t, self.we('empty') - 0.05)

class Beach(S):
    def make_shakes(self):
        return [(self.we('1937'), 12, 0.3)]
    def events(self):
        return [(self.we('1937'), 'thud', 0.8), (self.we('Fred') - 0.05, 'pop', 0.5), (self.we('Lucile') - 0.05, 'pop', 0.5),
                (self.we('tossing'), 'swipe', 0.6), (self.we('CAKE'), 'ding', 0.5)]
    def plate(self):
        img = sky_plate('beach', 4)
        self.stamp = stamp_sprite('1937', 150, color=(200, 40, 40), angle=-7)
        self.pan = disc_sprite(110, (188, 192, 198), 0.4, ridges=False, metal=True)
        put_figure(img, 'man', 210, 1290, 640, True)
        put_figure(img, 'woman', 1080, 1290, 600, True, flip=True)
        return img
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 330, t, self.we('1937'))
        pop(img, C('FRED MORRISON', 42, bg=(70, 140, 200), fg=(255, 255, 255)), 330, 560, t, self.we('Fred') - 0.05)
        pop(img, C('LUCILE', 42, bg=(192, 80, 74), fg=(255, 255, 255)), 990, 560, t, self.we('Lucile') - 0.05)
        tT = self.we('tossing') - 0.05
        if t > tT:
            u = ((t - tT) / 0.9) % 2.0
            u = u if u <= 1 else 2 - u
            x = 440 + (850 - 440) * u
            y = 880 - 170 * math.sin(u * math.pi)
            fly_disc(img, self.pan, x, y, t, spin=2.0, wob=8)
        pop(img, C('A CAKE PAN', 50, bg=YEL), CX, 1080, t, self.we('CAKE') - 0.05)

class Coins(S):
    focus = (CX, 960)
    def make_shakes(self):
        return [(self.we('cost'), 10, 0.3)]
    def events(self):
        return [(self.we('Someone'), 'pop', 0.4), (self.we('25'), 'cash', 0.8), (self.we('pan'), 'swipe', 0.5), (self.we('cost'), 'thud', 0.7)]
    def plate(self):
        self.pan = disc_sprite(230, (188, 192, 198), 0.42, ridges=False, metal=True)
        self.q = coin_sprite(150, '25¢')
        self.n = coin_sprite(110, '5¢', (190, 190, 186))
        return sky_plate('beach', 5)
    def dyn(self, img, t):
        pop(img, C('SOMEONE OFFERED...', 46, dot=GOLD), CX, 300, t, 0.05, out_t=self.we('cost') - 0.15)
        ground_shadow(img, CX, 1290, 360, 0.35)
        paste_center(img, self.pan, CX, 1120 + 8 * math.sin(t * 3))
        t25 = self.we('25') - 0.05
        if t > t25:
            k = ease_back((t - t25) / 0.4, 2.0)
            paste_center(img, self.q, CX - 250, 720, scale=max(0.05, k))
        tc = self.we('cost') - 0.05
        if t > tc:
            k = ease_back((t - tc) / 0.4, 2.0)
            paste_center(img, self.n, CX + 270, 740, scale=max(0.05, k))
            pop(img, C('THE PAN COST 5¢', 50, bg=YEL), CX, 300, t, tc)

class Plastic(S):
    def make_shakes(self):
        return [(self.we('1948'), 12, 0.3)]
    def events(self):
        return [(self.we('1948'), 'thud', 0.8), (self.we('PLASTIC') - 0.05, 'bigpop', 0.7), (self.we('called'), 'riser', 0.5)]
    def plate(self):
        self.pan = disc_sprite(280, (188, 192, 198), 0.42, ridges=False, metal=True)
        self.disc = disc_sprite(280, (232, 196, 60), 0.42, ridges=True)
        self.stamp = stamp_sprite('1948', 150, color=(200, 40, 40), angle=-7)
        arr = vgrad(PW, PH, [(0, '#0E1236'), (0.6, '#2C2A66'), (1, '#4A3A6E')])
        rng = np.random.default_rng(7)
        img = plate_img(arr)
        d = ImageDraw.Draw(img)
        for _ in range(160):
            x, y = int(rng.integers(0, PW)), int(rng.integers(0, 1250))
            r = rng.uniform(1.5, 4)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(rng.integers(120, 255))))
        return img
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 330, t, self.we('1948'))
        tP = self.we('PLASTIC') - 0.05
        y = 880 + 18 * math.sin(t * 2.5)
        tc = self.we('called') - 0.05
        if t > tc:
            ov = OV(img, CX - 360, y + 40, CX + 360, 1320)
            ov.d.polygon(ov.pts([(CX - 120, y + 60), (CX + 120, y + 60), (CX + 320, 1300), (CX - 320, 1300)]), fill=(180, 255, 200, 50))
            ov.commit()
        if t < tP:
            fly_disc(img, self.pan, CX, y, t)
        else:
            k = clamp01((t - tP) / 0.25)
            glow(img, CX, y, 420, (255, 220, 120), 0.6 * (1 - k) + 0.25)
            fly_disc(img, self.disc, CX, y, t, scale=1.0 + 0.12 * (1 - ease_out(k)))
            pop(img, C('PLASTIC', 54, bg=YEL), CX, 560, t, tP)
        if t > tc:
            pop(img, C('"FLYIN-SAUCER"', 54, bg=(110, 200, 120)), CX, 1180, t, tc)

class WhamO(S):
    def make_shakes(self):
        return [(self.we('renamed') + 0.35, 14, 0.3)]
    def events(self):
        return [(0.05, 'pop', 0.5), (self.we('bought'), 'cash', 0.7), (self.we('renamed'), 'thud', 0.9)]
    def plate(self):
        self.disc = disc_sprite(300, DISC_RED, 0.42, ridges=True)
        self.stamp = stamp_sprite('FRISBEE', 160, color=(200, 40, 40), angle=-8)
        return wall_plate(6, '#2E3A48', '#10141A')
    def dyn(self, img, t):
        pop(img, C('TOY COMPANY WHAM-O', 48, dot=GOLD), CX, 300, t, 0.05)
        tB = self.we('bought') - 0.05
        tR = self.we('renamed') - 0.05
        if t > tB:
            pop(img, C('BOUGHT IT', 50, bg=(110, 200, 120)), CX, 450, t, tB, out_t=tR - 0.1)
        ground_shadow(img, CX, 1262, 360, 0.5)
        fly_disc(img, self.disc, CX, 1040 + 10 * math.sin(t * 3), t, wob=2)
        pop(img, C('AND RENAMED IT...', 50, bg=YEL), CX, 450, t, tR)
        stamp_in(img, self.stamp, CX, 720, t, self.we('renamed') + 0.35)

class Horror(S):
    def make_shakes(self):
        return [(self.we('HORROR'), 18, 0.35)]
    def events(self):
        return [(self.we('called'), 'buzzer', 0.35), (self.we('royalties'), 'cash', 0.9), (self.we('made'), 'party', 0.5)]
    def plate(self):
        self.stamp = stamp_sprite('"A HORROR"', 120, angle=-7)
        self.bills = [money_sprite(k) for k in range(8)]
        self.disc = disc_sprite(220, DISC_RED, 0.42, ridges=True)
        img = sky_plate('park', 8)
        put_figure(img, 'man', 300, 1290, 720, False)
        return img
    def dyn(self, img, t):
        tR = self.we('royalties') - 0.05
        pop(img, C('MORRISON ON THE NAME:', 44, dot=GOLD), CX, 300, t, 0.05, out_t=tR - 0.1)
        fly_disc(img, self.disc, 880, 900 + 10 * math.sin(t * 3), t)
        stamp_in(img, self.stamp, 800, 600, t, self.we('HORROR'))
        if t > tR:
            pop(img, C('ROYALTIES = RICH', 54, bg=(110, 200, 120)), CX, 300, t, tR)
            for k, b in enumerate(self.bills):
                tk = tR + k * 0.08
                if t < tk:
                    continue
                q = ease_out((t - tk) / 0.5)
                paste_center(img, b.rotate(-18 + 6 * k, expand=True, resample=Image.BICUBIC), 170 + 135 * k, 160 + 900 * q - 50 * (k % 2))

class Twist(S):
    z0, z1 = 1.02, 1.12
    def events(self):
        return [(0.05, 'scratch', 0.7), (self.we('Ed') - 0.05, 'pop', 0.6), (self.we('MODERN'), 'ding', 0.7), (self.we('went'), 'riser', 0.6)]
    def plate(self):
        self.disc = disc_sprite(330, (60, 120, 210), 0.42, ridges=True)
        return wall_plate(9, '#2A2A36', '#0E0E14')
    def dyn(self, img, t):
        pop(img, C('THE TWIST', 56, bg=RED, fg=(255, 255, 255)), CX, 300, t, 0.05, out_t=self.we('Ed') - 0.15)
        pop(img, C('ED HEADRICK', 54, dot=GOLD), CX, 300, t, self.we('Ed') - 0.05)
        tM = self.we('MODERN') - 0.05
        y = 980 + 10 * math.sin(t * 3)
        ground_shadow(img, CX, 1262, 400, 0.5)
        if t > tM:
            glow(img, CX, y, 460, (120, 180, 255), 0.35)
        fly_disc(img, self.disc, CX, y, t, wob=3)
        pop(img, C('DESIGNED THE MODERN FRISBEE', 42, bg=YEL), CX, 470, t, tM)

class Ashes(S):
    z0, z1 = 1.04, 1.1
    def make_shakes(self):
        return [(self.we('ASHES'), 8, 0.3)]
    def events(self):
        return [(self.we('died'), 'chime', 0.5), (self.we('ASHES'), 'thud', 0.6), (self.we('molded'), 'rustle', 0.6)]
    def plate(self):
        self.urn = urn_sprite()
        self.discs = [disc_sprite(150, c, 0.42, ridges=True) for c in ((60, 120, 210), (232, 196, 60), (222, 58, 48))]
        self.stamp = stamp_sprite('2002', 150, color=(200, 40, 40), angle=-7)
        img = plate_img(dark_room('#2C2A34', '#0C0B10', spot=(CX, 950, 1000)))
        d = ImageDraw.Draw(img)
        d.rectangle((0, 1250, PW, PH), fill=(48, 40, 36, 255))
        return img
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 330, t, self.we('2002'))
        tm = self.we('molded') - 0.05
        k = clamp01((t - tm) / 0.6)
        ground_shadow(img, CX, 1262, 300, 0.5)
        if k < 1:
            paste_center(img, self.urn, CX, 1262 - self.urn.height / 2, alpha=1 - k)
        pop(img, C('HIS ASHES', 50, bg=(220, 220, 228)), CX, 560, t, self.we('ASHES') - 0.05, out_t=tm + 0.3)
        if t > tm:
            for j, sp in enumerate(self.discs):
                dt = t - tm - j * 0.12
                if dt <= 0:
                    continue
                q = ease_back(dt / 0.45, 1.6)
                x = CX + (j - 1) * 360
                paste_center(img, sp, x, 1020 - 60 * (j == 1) + 8 * math.sin(t * 3 + j), scale=max(0.05, q))
            pop(img, C('MEMORIAL DISCS', 52, bg=YEL), CX, 560, t, tm + 0.35)

class Museum(S):
    def events(self):
        return [(self.we('sold'), 'cash', 0.6), (self.we('MUSEUM') - 0.05, 'ding', 0.7), (self.we('STILL'), 'wind', 0.7)]
    def plate(self):
        img = museum_plate()
        fr = frame_sprite()
        with_shadow(img, fr, int(CX - fr.width / 2), 480)
        dsc = disc_sprite(170, (60, 120, 210), 0.42, ridges=True)
        paste_center(img, dsc, CX, 480 + fr.height / 2)
        d = ImageDraw.Draw(img)
        d.rectangle((CX - 170, 1080, CX + 170, 1250), fill=(220, 214, 204, 255))
        d.rectangle((CX - 200, 1060, CX + 200, 1086), fill=(240, 236, 228, 255))
        self.disc = disc_sprite(160, (232, 196, 60), 0.42, ridges=True)
        return img
    def dyn(self, img, t):
        pop(img, C('SOLD TO FUND A MUSEUM', 46, dot=GOLD), CX, 300, t, self.we('sold') - 0.05)
        tS = self.we('STILL') - 0.1
        if t < tS:
            paste_center(img, self.disc, CX, 1020)
        else:
            u = ease_in_out((t - tS) / 1.0)
            fly_disc(img, self.disc, CX + 480 * u, 1020 - 260 * u, t, spin=2, wob=10)
            pop(img, C('STILL FLYING', 52, bg=YEL), CX, 1180, t, tS)

class Outro(Hook):
    def make_shakes(self):
        return [(self.we('pie'), 12, 0.3)]
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('pie') - 0.05, 'pop', 0.7)]
    def dyn(self, img, t):
        ground_shadow(img, CX, 1300, 380, 0.25)
        fly_disc(img, self.disc, CX, 680 + 14 * math.sin(t * 3), t)
        tP = self.we('pie') - 0.05
        if t > tP:
            k = ease_back((t - tP) / 0.4, 1.8)
            fly_disc(img, self.tin, CX + 330, 470, t + 1, scale=max(0.05, k))
        pop(img, C('ALL THANKS TO A TOY...', 46, dot=GOLD), CX, 300, t, 0.1, out_t=tP - 0.1)
        pop(img, C('NAMED AFTER A PIE COMPANY', 46, bg=YEL), CX, 300, t, tP)

SCENES = [Hook, Bakery, Campus, Beach, Coins, Plastic, WhamO, Horror, Twist, Ashes, Museum, Outro]
