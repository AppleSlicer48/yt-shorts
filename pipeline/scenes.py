import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, dark_room
from mw_scenes import glow, stamp_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import with_shadow, ground_shadow

GOLD = (240, 160, 60)
RED = (200, 50, 45)
YEL = (255, 210, 60)
DARK = (34, 36, 44)
WHITE = (255, 255, 255)
SKIN = '#C9CED6'

_SP = {}
_PL = {}

# ====================================================================== sky / sea backdrops
def sky_plate(kind='day', seed=1, sea=False, hz=1300):
    key = (kind, seed, sea, hz)
    if key in _PL:
        return _PL[key].copy()
    if kind == 'day':
        arr = vgrad(PW, PH, [(0, '#2F78C4'), (0.55, '#8FC4EC'), (1, '#CFE6F6')])
    elif kind == 'storm':
        arr = vgrad(PW, PH, [(0, '#1E2A3E'), (0.55, '#4A5A72'), (1, '#7A8798')])
    else:  # dusk
        arr = vgrad(PW, PH, [(0, '#24305E'), (0.5, '#C9706A'), (1, '#F2B27A')])
    img = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(img, 'RGBA')
    rng = np.random.default_rng(seed)
    cc = (255, 255, 255, 150) if kind == 'day' else ((150, 160, 178, 150) if kind == 'storm' else (255, 214, 190, 120))
    for _ in range(9):
        x, y = rng.uniform(-100, PW + 100), rng.uniform(150, 1150)
        for k in range(6):
            r = rng.uniform(60, 130)
            d.ellipse((x + k * 70 - r, y - r * 0.6, x + k * 70 + r, y + r * 0.6), fill=cc)
    img = img.filter(ImageFilter.GaussianBlur(10))
    if sea:
        d = ImageDraw.Draw(img, 'RGBA')
        s = vgrad(PW, PH - hz, [(0, '#2F6E96' if kind != 'storm' else '#2A4256'), (1, '#0F2C44')])
        img.paste(to_img(s), (0, hz))
        for k in range(40):
            y = hz + 20 + (k * 37) % (PH - hz - 20)
            x = (k * 211) % PW
            d.line((x, y, x + 140, y), fill=(255, 255, 255, 50), width=4)
    _PL[key] = img
    return img.copy()

def tarmac_plate():
    if 'tarmac' in _PL:
        return _PL['tarmac'].copy()
    img = sky_plate('storm', 4)
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle((0, 1250, PW, PH), fill=(70, 72, 76, 255))
    for x in range(0, PW, 260):
        d.rectangle((x, 1380, x + 140, 1396), fill=(240, 220, 120, 200))
    d.rectangle((0, 1240, PW, 1252), fill=(40, 42, 46, 255))
    _PL['tarmac'] = img
    return img.copy()

def hangar_plate():
    if 'hangar' in _PL:
        return _PL['hangar'].copy()
    arr = dark_room('#33404C', '#0E1318', spot=(CX, 900, 1200), strength=1.0)
    img = plate_img(arr)
    d = ImageDraw.Draw(img, 'RGBA')
    for x in range(-40, PW, 216):
        d.line((x, 0, x, 1250), fill=(0, 0, 0, 70), width=10)
    d.rectangle((0, 1250, PW, PH), fill=(46, 50, 56, 255))
    _PL['hangar'] = img
    return img.copy()

# ====================================================================== props
def jet_sprite(L=1000, color=SKIN, windows='square', stripe=(40, 80, 160)):
    """Side view of a generic 1950s jetliner, nose to the right."""
    key = ('jet', L, color, windows, stripe)
    if key in _SP:
        return _SP[key]
    W_, H_ = int(L * 1.08), int(L * 0.42)
    lay = Layer(W_, H_)
    r = L * 0.06
    y = H_ * 0.58
    x0, x1 = L * 0.10, L * 0.92
    col = hexc(color)
    # tail fin and tailplane (behind body)
    fill_poly(lay, [(x0 + r * 0.4, y - r * 0.6), (x0 - r * 0.9, y - r * 4.2), (x0 + r * 0.6, y - r * 4.2), (x0 + r * 3.6, y - r * 0.8)], col * 0.82)
    fill_poly(lay, [(x0 + r * 0.6, y - r * 0.1), (x0 - r * 1.2, y - r * 0.6), (x0 - r * 0.6, y + r * 0.1), (x0 + r * 2.8, y + r * 0.2)], col * 0.7)
    capsule(lay, (x0 + r * 0.4, y - r * 0.25), (x0 + r * 4, y), r * 0.35, r, col, spec=0.6, shin=30)
    capsule(lay, (x0 + r * 3, y), (x1 - r * 1.2, y), r, r, col, spec=0.6, shin=30)
    capsule(lay, (x1 - r * 1.5, y), (x1 + r * 0.9, y + r * 0.25), r, r * 0.25, col, spec=0.6, shin=30)
    # wing (near side)
    fill_poly(lay, [(L * 0.46, y + r * 0.25), (L * 0.62, y + r * 0.2), (L * 0.50, y + r * 2.6), (L * 0.42, y + r * 2.6)], col * 0.62)
    capsule(lay, (L * 0.47, y + r * 0.45), (L * 0.60, y + r * 0.4), r * 0.28, r * 0.28, col * 0.75, spec=0.5)
    sp, _, _ = layer_sprite(lay, 2)
    ox, oy = _, _
    d = ImageDraw.Draw(sp, 'RGBA')
    # cheat line
    def P(x, yy):
        return (x - ox, yy - oy)
    d.rectangle((*P(x0 + r * 2.5, y + r * 0.05), *P(x1 - r * 0.2, y + r * 0.22)), fill=stripe + (230,))
    # windows
    ww = r * 0.42
    xs = np.arange(x0 + r * 4.2, x1 - r * 2.4, r * 0.78)
    for wx in xs:
        bx = (*P(wx - ww / 2, y - r * 0.5), *P(wx + ww / 2, y - r * 0.5 + ww * (1.0 if windows == 'square' else 1.35)))
        if windows == 'square':
            d.rounded_rectangle(bx, radius=max(1, ww * 0.12), fill=(30, 44, 70, 255))
        else:
            d.rounded_rectangle(bx, radius=ww * 0.5, fill=(30, 44, 70, 255))
    # cockpit
    d.polygon([P(x1 - r * 0.3, y - r * 0.55), P(x1 + r * 0.35, y - r * 0.3), P(x1 + r * 0.2, y - r * 0.12), P(x1 - r * 0.35, y - r * 0.3)], fill=(30, 44, 70, 255))
    _SP[key] = (sp, ox, oy)
    return _SP[key]

def jet_halves(L=1000, split=0.5):
    """Return the jet sprite cut in two at fraction `split` with jagged edges: (rear, front, cut_x)."""
    key = ('halves', L, split)
    if key in _SP:
        return _SP[key]
    sp, _, _ = jet_sprite(L)
    w, h = sp.size
    cx = int(w * split)
    rng = np.random.default_rng(3)
    ys = np.linspace(0, h, 14)
    pts = [(cx + rng.uniform(-28, 28), yy) for yy in ys]
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon([(0, 0)] + pts + [(0, h)], fill=255)
    rear = sp.copy(); a = np.minimum(np.asarray(sp.getchannel('A')), np.asarray(mask)); rear.putalpha(Image.fromarray(a))
    front = sp.copy(); a = np.minimum(np.asarray(sp.getchannel('A')), 255 - np.asarray(mask)); front.putalpha(Image.fromarray(a))
    _SP[key] = (rear, front, cx)
    return _SP[key]

def window_sprite(w=520, h=620, radius=0.05, pane='sky'):
    """Close-up of an aircraft window set into a riveted skin patch."""
    key = ('win', w, h, radius, pane)
    if key in _SP:
        return _SP[key]
    pad = 70
    im = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr = int(min(w, h) * radius)
    # bezel
    d.rounded_rectangle((pad - 46, pad - 46, pad + w + 46, pad + h + 46), radius=rr + 46, fill=(150, 156, 166, 255))
    d.rounded_rectangle((pad - 30, pad - 30, pad + w + 30, pad + h + 30), radius=rr + 30, fill=(110, 116, 126, 255))
    # pane
    if pane == 'sky':
        g = vgrad(w, h, [(0, '#3E86CC'), (0.6, '#9ACCF0'), (1, '#E4F2FA')])
    else:  # water
        g = vgrad(w, h, [(0, '#1C5A7A'), (1, '#0C2E44')])
    gi = to_img(g).convert('RGBA')
    gd = ImageDraw.Draw(gi, 'RGBA')
    if pane == 'sky':
        for (cx, cy, s) in ((0.3, 0.62, 1.0), (0.75, 0.75, 0.8), (0.55, 0.88, 1.2)):
            for k in range(4):
                gd.ellipse((w * cx - 90 * s + k * 50 * s - 60, h * cy - 40 * s, w * cx + k * 50 * s - 10, h * cy + 40 * s), fill=(255, 255, 255, 200))
    # glare
    gd.polygon([(w * 0.08, h * 0.05), (w * 0.32, h * 0.05), (w * 0.12, h * 0.6), (w * 0.0, h * 0.6)], fill=(255, 255, 255, 50))
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=rr, fill=255)
    gi.putalpha(m)
    im.alpha_composite(gi, (pad, pad))
    _SP[key] = im
    return im

def skin_plate(base='#B8BEC8', dark='#7E8692', seed=2, under=False):
    key = ('skin', base, seed, under)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, base), (0.5, '#D6DBE2'), (1, dark)])
    arr = arr * (0.94 + 0.1 * smooth_noise(PH, PW, 60, seed, 3))[..., None]
    if under:
        arr = arr * np.array([0.7, 0.85, 1.0], np.float32) * 0.7
    img = to_img(arr).convert('RGBA')
    d = ImageDraw.Draw(img, 'RGBA')
    for y in range(80, PH, 330):
        d.line((0, y, PW, y), fill=(60, 64, 72, 120), width=5)
        for x in range(20, PW, 54):
            d.ellipse((x - 6, y + 22, x + 6, y + 34), fill=(90, 94, 104, 170))
            d.ellipse((x - 4, y + 22, x + 2, y + 28), fill=(255, 255, 255, 90))
    for x in range(100, PW, 430):
        d.line((x, 0, x, PH), fill=(60, 64, 72, 90), width=4)
    _PL[key] = plate_img(vignette(to_arr(img), 0.4))
    return _PL[key].copy()

def crack_paths(cx, cy, w, h, seed=5, n_per=2, length=520):
    """Jagged crack polylines radiating from the four window corners."""
    rng = np.random.default_rng(seed)
    paths = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for j in range(n_per):
                x, y = cx + sx * w / 2, cy + sy * h / 2
                ang = math.atan2(sy, sx) + rng.uniform(-0.45, 0.45)
                pts = [(x, y)]
                seg = length / 9
                for k in range(9):
                    ang += rng.uniform(-0.5, 0.5)
                    x += math.cos(ang) * seg * rng.uniform(0.7, 1.2)
                    y += math.sin(ang) * seg * rng.uniform(0.7, 1.2)
                    pts.append((x, y))
                paths.append(pts)
    return paths

def draw_cracks(img, paths, prog, width=9):
    if prog <= 0:
        return
    xs = [p[0] for pp in paths for p in pp]; ys = [p[1] for pp in paths for p in pp]
    ov = OV(img, min(xs) - 30, min(ys) - 30, max(xs) + 30, max(ys) + 30)
    for pp in paths:
        n = len(pp) - 1
        m = prog * n
        k = int(m)
        pts = pp[:k + 1]
        if k < n:
            f = m - k
            a, b = pp[k], pp[k + 1]
            pts = pts + [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
        if len(pts) > 1:
            ov.d.line(ov.pts(pts), fill=(20, 16, 16, 255), width=width, joint='curve')
            ov.d.line(ov.pts([(x + 3, y + 3) for x, y in pts]), fill=(255, 255, 255, 90), width=2)
    ov.commit()

def corner_glow(img, cx, cy, w, h, a, r=150):
    for sx in (-1, 1):
        for sy in (-1, 1):
            glow(img, cx + sx * w / 2, cy + sy * h / 2, r, (255, 50, 30), a)

def gauge_sprite(R=170):
    if ('gauge', R) in _SP:
        return _SP[('gauge', R)]
    im = Image.new('RGBA', (2 * R + 20, 2 * R + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = R + 10
    d.ellipse((c - R, c - R, c + R, c + R), fill=(60, 64, 72, 255))
    d.ellipse((c - R * 0.88, c - R * 0.88, c + R * 0.88, c + R * 0.88), fill=(240, 238, 230, 255))
    for k in range(11):
        a = math.radians(225 - k * 27)
        r0, r1 = R * 0.68, R * 0.82
        col = (200, 40, 40, 255) if k >= 8 else (40, 40, 46, 255)
        d.line((c + r0 * math.cos(a), c - r0 * math.sin(a), c + r1 * math.cos(a), c - r1 * math.sin(a)), fill=col, width=7)
    f = font(int(R * 0.2))
    d.text((c, c + R * 0.45), 'PRESSURE', font=f, fill=(40, 40, 46, 255), anchor='mm')
    _SP[('gauge', R)] = im
    return im

def draw_gauge(img, cx, cy, val, R=170):
    paste_center(img, gauge_sprite(R), cx, cy)
    a = math.radians(225 - val * 270)
    ov = OV(img, cx - R, cy - R, cx + R, cy + R)
    ov.d.line(ov.pts([(cx, cy), (cx + R * 0.72 * math.cos(a), cy - R * 0.72 * math.sin(a))]), fill=(200, 30, 30, 255), width=10)
    ov.d.ellipse(ov.box(cx - 18, cy - 18, cx + 18, cy + 18), fill=(40, 40, 46, 255))
    ov.commit()

def check_badge(R=90, ok=True):
    key = ('chk', R, ok)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (2 * R + 10, 2 * R + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = R + 5
    d.ellipse((5, 5, 5 + 2 * R, 5 + 2 * R), fill=((60, 180, 90) if ok else (210, 50, 45)) + (255,))
    if ok:
        d.line([(c - R * 0.45, c + R * 0.02), (c - R * 0.1, c + R * 0.38), (c + R * 0.5, c - R * 0.35)], fill=WHITE + (255,), width=int(R * 0.22), joint='curve')
    else:
        k = R * 0.42
        d.line((c - k, c - k, c + k, c + k), fill=WHITE + (255,), width=int(R * 0.22))
        d.line((c - k, c + k, c + k, c - k), fill=WHITE + (255,), width=int(R * 0.22))
    _SP[key] = im
    return im

def puff(img, x, y, r, a=0.6, col=(90, 90, 96)):
    ov = OV(img, x - r - 20, y - r - 20, x + r + 20, y + r + 20)
    ov.d.ellipse(ov.box(x - r, y - r, x + r, y + r), fill=col + (int(255 * a),))
    ov.im = ov.im.filter(ImageFilter.GaussianBlur(r * 0.25))
    ov.commit()

def place_jet(img, sp, cx, cy, ang=0.0, scale=1.0):
    rs = sp.rotate(ang, resample=Image.BICUBIC, expand=True) if abs(ang) > 0.05 else sp
    paste_center(img, rs, cx, cy, scale=scale)

# ====================================================================== scenes
WIN_W, WIN_H = 560, 600
WIN_CY = 900

class Hook(S):
    z0, z1 = 1.05, 1.16
    focus = (CX, 960)
    punch = 0.0
    def make_shakes(self):
        return [(self.we('ripped'), 26, 0.45), (self.we('APART'), 16, 0.35)]
    def events(self):
        return [(0.02, 'crack', 0.8), (self.we('SHAPE') - 0.05, 'thud', 0.6), (self.we('ripped'), 'boom', 0.9), (self.we('first') - 0.05, 'pop', 0.5)]
    def plate(self):
        self.win = window_sprite(WIN_W, WIN_H, 0.06)
        self.paths = crack_paths(CX, WIN_CY, WIN_W + 60, WIN_H + 60, seed=5, n_per=2, length=560)
        self.stamp = stamp_sprite('TORN APART', 120, color=(225, 35, 35), angle=-7)
        bg = Image.new('RGBA', self.stamp.size, (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((26, 26, self.stamp.width - 26, self.stamp.height - 26), 30, fill=(255, 250, 240, 225))
        bg.alpha_composite(self.stamp)
        self.stamp = bg
        return skin_plate()
    def dyn(self, img, t):
        tR = self.we('ripped') - 0.04
        # split the skin apart after "ripped"
        sep = 0.0 if t < tR else 70 * ease_out((t - tR) / 0.35)
        pulse = 0.55 + 0.35 * math.sin(t * 9)
        corner_glow(img, CX, WIN_CY, WIN_W + 60, WIN_H + 60, pulse, 170)
        paste_center(img, self.win, CX, WIN_CY)
        prog = 0.6 + 0.4 * ease_out(t / max(0.1, tR))
        draw_cracks(img, self.paths, min(1, prog), 10)
        if sep > 0:
            # jagged dark rift opening through the window
            ov = OV(img, 0, WIN_CY - 260, PW, WIN_CY + 260)
            rng = np.random.default_rng(9)
            xs = np.linspace(0, PW, 18)
            top = [(x, WIN_CY - sep / 2 + rng.uniform(-30, 30)) for x in xs]
            bot = [(x, WIN_CY + sep / 2 + rng.uniform(-30, 30)) for x in xs[::-1]]
            ov.d.polygon(ov.pts(top + bot), fill=(14, 18, 30, 255))
            ov.commit()
        pop(img, C('SQUARE WINDOWS', 56, bg=YEL), CX, 300, t, -1.0, out_t=self.we('first') - 0.15)
        pop(img, C('THE FIRST JET AIRLINER', 50, dot=GOLD), CX, 300, t, self.we('first') - 0.05)
        stamp_in(img, self.stamp, CX, WIN_CY, t, self.we('APART') - 0.05)

class Comet(S):
    z0, z1 = 1.0, 1.08
    def make_shakes(self):
        return [(self.we('1952'), 12, 0.3)]
    def events(self):
        return [(0.05, 'wind', 0.6), (self.we('1952'), 'thud', 0.8), (self.we('COMET') - 0.05, 'pop', 0.6), (self.we('flying'), 'ding', 0.6)]
    def plate(self):
        self.jet, _, _ = jet_sprite(1050)
        self.stamp = stamp_sprite('1952', 150, color=(200, 40, 40), angle=-7)
        self.hand = get_hand(520, -math.pi / 2.3)
        return sky_plate('day', 2)
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 320, t, self.we('1952'))
        u = t / self.dur
        x = CX + 120 - 240 * u
        y = 930 + 14 * math.sin(t * 2.2)
        for k in range(3):
            yy = y - 30 + k * 30
            ov = OV(img, x - 1000, yy - 10, x - 380, yy + 10)
            ov.d.line(ov.pts([(x - 1000, yy), (x - 420, yy)]), fill=(255, 255, 255, 90), width=6)
            ov.commit()
        place_jet(img, self.jet, x, y, -2)
        pop(img, C('DE HAVILLAND COMET', 50, dot=GOLD), CX, 520, t, self.we('de') - 0.05)
        tp = self.we('flying') - 0.05
        pop(img, C('PASSENGERS BY JET!', 50, bg=YEL), CX, 1200, t, tp)

class Elba(S):
    z0, z1 = 1.04, 1.12
    def make_shakes(self):
        return [(self.we('1954'), 10, 0.3), (self.we('broke'), 24, 0.45)]
    def events(self):
        return [(self.we('1954'), 'thud', 0.8), (self.we('broke'), 'crack', 0.9), (self.we('broke') + 0.1, 'boom', 0.7), (self.we('near') - 0.05, 'pop', 0.5)]
    def plate(self):
        self.jet, _, _ = jet_sprite(950)
        self.rear, self.front, self.cut = jet_halves(950, 0.5)
        self.stamp = stamp_sprite('1954', 150, color=(200, 40, 40), angle=-7)
        img = sky_plate('storm', 3, sea=True)
        d = ImageDraw.Draw(img, 'RGBA')
        d.polygon([(860, 1302), (930, 1262), (1010, 1250), (1090, 1270), (1160, 1302)], fill=(40, 70, 50, 255))
        return img
    def dyn(self, img, t):
        stamp_in(img, self.stamp, CX, 320, t, self.we('1954'))
        tb = self.we('broke') - 0.05
        y0 = 860
        if t < tb:
            place_jet(img, self.jet, CX + 40 - 60 * t, y0 + 8 * math.sin(t * 3))
        else:
            q = t - tb
            e = ease_out(q / 0.6)
            cx = CX + 40 - 60 * tb
            w = self.jet.width
            # halves drift apart and tumble
            place_jet(img, self.rear, cx - 90 * e - 40 * q, y0 + 130 * q * q + 40 * e, 10 * e + 6 * q)
            place_jet(img, self.front, cx + 90 * e + 40 * q, y0 + 160 * q * q + 30 * e, -12 * e - 8 * q)
            for k in range(5):
                puff(img, cx + (k - 2) * 26, y0 + 10 * k - 30 * q, 30 + 70 * e + 10 * k, 0.5 * (1 - clamp01(q / 2.5)))
        pop(img, C('NEAR ELBA, ITALY', 46, bg=WHITE), 1010, 1150, t, self.we('near') - 0.05)
        pop(img, C('ALL 35 ON BOARD LOST', 50, bg=DARK, fg=WHITE), CX, 520, t, self.we('killing') - 0.05)

class Another(S):
    z0, z1 = 1.0, 1.08
    def make_shakes(self):
        return [(self.we('ANOTHER'), 14, 0.3), (self.we('sea') + 0.1, 12, 0.3)]
    def events(self):
        return [(0.05, 'tick', 0.5), (self.we('ANOTHER'), 'thud', 0.8), (self.we('fell'), 'riser', 0.5), (self.we('sea'), 'splat', 0.8), (self.we('21') - 0.05, 'pop', 0.4)]
    def plate(self):
        self.jet, _, _ = jet_sprite(820)
        return sky_plate('dusk', 6, sea=True, hz=1120)
    def dyn(self, img, t):
        pop(img, C('MONTHS LATER...', 48, bg=DARK, fg=WHITE), CX, 300, t, 0.0, out_t=self.we('ANOTHER') - 0.1)
        pop(img, C('A SECOND COMET', 52, bg=YEL), CX, 300, t, self.we('ANOTHER') - 0.05)
        tf = self.we('fell') - 0.1
        ts = self.we('sea') + 0.05
        if t < tf:
            place_jet(img, self.jet, CX - 40 + 30 * t, 700)
        else:
            u = clamp01((t - tf) / max(0.2, ts - tf))
            x = CX - 40 + 30 * tf + 220 * u
            y = 700 + 420 * ease_in_out(u) ** 1.4
            if t < ts + 0.05:
                place_jet(img, self.jet, x, y, -32 * u)
                puff(img, x - 200, y - 120 * u, 50, 0.4)
            if t > ts - 0.05:
                q = clamp01((t - ts + 0.05) / 0.6)
                ov = OV(img, x - 400, 700, x + 400, 1160)
                for k in range(9):
                    a = math.pi * (0.1 + 0.8 * k / 8)
                    L = 330 * ease_out(q) * (0.6 + 0.4 * (k % 2))
                    ov.d.line(ov.pts([(x, 1120), (x - L * math.cos(a), 1120 - L * math.sin(a))]), fill=(235, 245, 255, int(230 * (1 - q * 0.6))), width=22)
                ov.commit()
        pop(img, C('21 PEOPLE LOST', 52, bg=DARK, fg=WHITE), CX, 520, t, self.we('21') - 0.05)

class Tank(S):
    z0, z1 = 1.02, 1.1
    def make_shakes(self):
        return [(self.we('GROUNDED'), 16, 0.35)]
    def events(self):
        return [(self.we('GROUNDED'), 'thud', 0.9), (self.we('engineers') - 0.05, 'pop', 0.5), (self.we('sank'), 'splat', 0.8), (self.we('WATER'), 'bloop', 0.7)]
    def plate(self):
        self.jet, _, _ = jet_sprite(900)
        self.fus, _, _ = jet_sprite(820, windows='square')
        self.stamp = stamp_sprite('GROUNDED', 140, color=(225, 35, 35), angle=-8)
        self.tarmac = tarmac_plate()
        return hangar_plate()
    def dyn(self, img, t):
        te = self.we('engineers') - 0.1
        if t < te:
            img.paste(self.tarmac, (0, 0))
            ground_shadow(img, CX, 1250, 820, 0.5)
            place_jet(img, self.jet, CX, 1250 - self.jet.height * 0.42)
            stamp_in(img, self.stamp, CX, 640, t, self.we('GROUNDED') - 0.05)
            pop(img, C('EVERY COMET', 50, dot=GOLD), CX, 300, t, 0.0)
            return
        pop(img, C('ENGINEERS', 50, dot=GOLD), CX, 300, t, te)
        # tank
        tx0, tx1, ty0, ty1 = 130, PW - 130, 560, 1300
        ov = OV(img, tx0 - 20, ty0 - 20, tx1 + 20, ty1 + 20)
        ov.d.rectangle(ov.box(tx0 - 16, ty0 - 16, tx1 + 16, ty1 + 16), fill=(70, 76, 86, 255))
        ov.d.rectangle(ov.box(tx0, ty0, tx1, ty1), fill=(18, 26, 34, 255))
        ov.commit()
        ts = self.we('sank') - 0.05
        sink = ease_in_out(clamp01((t - ts) / 0.8))
        fy = 520 + 420 * sink
        place_jet(img, self.fus, CX, fy)
        tw = self.we('WATER') - 0.05
        fill = 0.25 + 0.75 * ease_out(clamp01((t - ts) / 1.2))
        wy = ty1 - (ty1 - ty0 - 40) * fill
        ov = OV(img, tx0, ty0, tx1, ty1)
        ov.d.rectangle(ov.box(tx0, wy, tx1, ty1), fill=(60, 150, 210, 120))
        ov.d.line(ov.pts([(tx0, wy), (tx1, wy)]), fill=(200, 235, 255, 200), width=6)
        ov.commit()
        pop(img, C('A GIANT WATER TANK', 52, bg=YEL), CX, 440, t, tw)

class Pressure(S):
    z0, z1 = 1.04, 1.12
    focus = (CX, 1000)
    def events(self):
        return [(0.05, 'bloop', 0.6), (self.we('again'), 'tick', 0.6), (self.we('and') + 0.05, 'tick', 0.6), (self.we('THOUSANDS') - 0.05, 'riser', 0.6), (self.we('like'), 'bloop', 0.5)]
    def plate(self):
        self.fus, _, _ = jet_sprite(900)
        self.icon, _, _ = jet_sprite(110)
        img = hangar_plate()
        d = ImageDraw.Draw(img, 'RGBA')
        tx0, tx1, ty0, ty1 = 130, PW - 130, 560, 1300
        d.rectangle((tx0 - 16, ty0 - 16, tx1 + 16, ty1 + 16), fill=(70, 76, 86, 255))
        d.rectangle((tx0, ty0, tx1, ty1), fill=(40, 100, 140, 255))
        d.line((tx0, ty0 + 40, tx1, ty0 + 40), fill=(200, 235, 255, 200), width=6)
        return img
    def dyn(self, img, t):
        ph = (math.sin(t * 2 * math.pi * 1.6) + 1) / 2
        place_jet(img, self.fus, CX, 940, scale=1.0 + 0.05 * ph)
        for k in range(4):
            by = 1250 - ((t * 260 + k * 170) % 600)
            puff(img, 260 + k * 250, by, 16, 0.5, (210, 240, 255))
        draw_gauge(img, PW - 280, 1180, 0.2 + 0.7 * ph, 120)
        pop(img, C('PRESSURE UP... AND DOWN', 46, bg=WHITE), CX, 300, t, 0.05, out_t=self.we('like') - 0.15)
        tT = self.we('THOUSANDS') - 0.05
        pop(img, C('LIKE THOUSANDS OF FLIGHTS', 46, bg=YEL), CX, 300, t, self.we('like') - 0.05)
        if t > tT:
            n = int(clamp01((t - tT) / 0.9) * 18)
            for k in range(n):
                paste_center(img, self.icon, 150 + (k % 9) * 125, 405 + (k // 9) * 62)

class Split(S):
    z0, z1 = 1.06, 1.2
    focus = (CX, 960)
    punch = 0.18
    def make_shakes(self):
        return [(self.we('SPLIT'), 28, 0.45)]
    def events(self):
        return [(self.we('SPLIT') - 0.03, 'crack', 1.0), (self.we('SPLIT') + 0.05, 'boom', 0.6), (self.we('window') - 0.05, 'ding', 0.7)]
    def plate(self):
        self.win = window_sprite(WIN_W, WIN_H, 0.06, pane='water')
        self.paths = crack_paths(CX, WIN_CY, WIN_W + 60, WIN_H + 60, seed=11, n_per=3, length=460)
        self.paths = self.paths[6:9]  # cracks from the top-right corner
        return skin_plate(under=True)
    def dyn(self, img, t):
        paste_center(img, self.win, CX, WIN_CY)
        tS = self.we('SPLIT') - 0.05
        if t > tS:
            draw_cracks(img, self.paths, ease_out((t - tS) / 0.3), 16)
            cx, cy = CX + (WIN_W + 60) / 2, WIN_CY - (WIN_H + 60) / 2
            glow(img, cx, cy, 200, (255, 60, 30), 0.7)
        tc = self.we('CORNER') - 0.1
        if t > tc:
            cx, cy = CX + (WIN_W + 60) / 2, WIN_CY - (WIN_H + 60) / 2
            k = ease_back((t - tc) / 0.35, 1.8)
            r = 120 * max(0.05, k)
            ov = OV(img, cx - 160, cy - 160, cx + 160, cy + 160)
            ov.d.ellipse(ov.box(cx - r, cy - r, cx + r, cy + r), outline=(255, 210, 40, 255), width=14)
            ov.commit()
            pop(img, C('AT A WINDOW CORNER', 52, bg=YEL), CX, 300, t, tc)
        pop(img, C('IT SPLIT OPEN', 54, bg=RED, fg=WHITE), CX, 300, t, tS, out_t=tc - 0.1)

class Stress(S):
    z0, z1 = 1.02, 1.1
    def events(self):
        return [(0.05, 'pop', 0.5), (self.we('STRESS') - 0.05, 'thud', 0.7), (self.we('far'), 'riser', 0.6), (self.we('than'), 'bigpop', 0.7)]
    def plate(self):
        self.win = window_sprite(420, 450, 0.06)
        img = plate_img(dark_room('#2E3440', '#0E1116', spot=(CX, 900, 1100)))
        return img
    def dyn(self, img, t):
        cx, cy, w, h = CX, 780, 480, 510
        tS = self.we('STRESS') - 0.05
        # stress flow lines bending around the window and bunching at the corners
        ov = OV(img, 0, 300, PW, 1260)
        sh = (t * 160) % 60
        for k in range(-7, 8):
            x = cx + k * 70
            pts = []
            for yy in np.linspace(330, 1230, 40):
                dy = (yy - cy) / (h / 2 + 40)
                push = (w / 2 + 50) * np.exp(-dy ** 4) * np.sign(k) * max(0, 1 - abs(k) / 8) if k != 0 else 0
                pts.append((x + push * 0.9, yy))
            col = (255, 120, 80, 200) if abs(k) <= 4 else (140, 190, 255, 140)
            ov.d.line(ov.pts(pts), fill=col, width=6)
        ov.commit()
        heat = 0.25 + 0.65 * ease_out(clamp01((t - tS) / 0.6)) + 0.1 * math.sin(t * 10)
        corner_glow(img, cx, cy, w, h, heat, 140)
        paste_center(img, self.win, cx, cy)
        pop(img, C('CORNERS = STRESS HOTSPOTS', 46, bg=RED, fg=WHITE), CX, 300, t, tS)
        # expected vs actual bars
        tf = self.we('far') - 0.05
        if t > tf:
            u = ease_out(clamp01((t - tf) / 0.5))
            v = ease_out(clamp01((t - self.we('than')) / 0.6))
            bx, by = 200, 1150
            ov = OV(img, 100, 1080, PW - 60, 1330)
            ov.d.rounded_rectangle(ov.box(bx + 270, by - 30, bx + 270 + 260 * u, by + 10), 18, fill=(120, 200, 130, 255))
            ov.d.rounded_rectangle(ov.box(bx + 270, by + 50, bx + 270 + 680 * v, by + 90), 18, fill=(230, 60, 45, 255))
            ov.commit()
            paste_center(img, text_img('EXPECTED', 50, stroke=6), bx + 120, by - 10)
            paste_center(img, text_img('ACTUAL', 50, stroke=6), bx + 120, by + 70)

class Outro(S):
    z0, z1 = 1.04, 1.12
    focus = (CX, 960)
    def events(self):
        return [(0.05, 'swipe', 0.6), (self.we('ROUNDED') - 0.05, 'ding', 0.8), (self.we('every') - 0.05, 'pop', 0.5)]
    def plate(self):
        self.round = window_sprite(WIN_W, WIN_H + 80, 0.42)
        self.square = window_sprite(WIN_W, WIN_H, 0.06)
        self.ok = check_badge(80, True)
        self.hand = get_hand(560, -math.pi / 6)
        return skin_plate()
    def dyn(self, img, t):
        tb = self.we('because') - 0.05
        tR = self.we('ROUNDED') - 0.05
        # in the last beat the round window morphs back to the square one (loops to the hook)
        m = ease_in_out(clamp01((t - tb) / 0.5))
        if m < 1:
            paste_center(img, self.round, CX, WIN_CY, alpha=1 - m)
        if m > 0:
            paste_center(img, self.square, CX, WIN_CY, alpha=m)
        pop(img, C('EVERY AIRLINER TODAY', 48, dot=GOLD), CX, 300, t, self.we('every') - 0.05)
        if t > tR and m < 0.5:
            k = ease_back((t - tR) / 0.4, 1.8)
            paste_center(img, self.ok, CX + 330, WIN_CY - 330, scale=max(0.05, k), alpha=1 - 2 * m)
            pop(img, C('ROUNDED CORNERS', 54, bg=(110, 200, 120)), CX, 430, t, tR, out_t=tb)
        if t < tb:
            e = ease_out(t / 0.6)
            draw_hand(img, self.hand, (CX - 240 + 40 * e, WIN_CY + 260 - 30 * e), 0.0)

SCENES = [Hook, Comet, Elba, Another, Tank, Pressure, Split, Stress, Outro]
