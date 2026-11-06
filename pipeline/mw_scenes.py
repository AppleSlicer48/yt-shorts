import math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from engine import *
from base_scenes import (Scene as BaseScene, arm, bracket, finish, plate_img, grain_map, stone_tex, wood,
                         table_bg, ARM_LIGHT, CX, CY)

RNG = np.random.default_rng(2026)

# ====================================================================== base
class Scene(BaseScene):
    shakes = ()  # list of (t0, amp, dur)

    def we(self, key, which='t0'):
        k = key.lower()
        for w in self.words:
            if re.sub(r'[^a-z0-9$]', '', w['w'].lower()) == re.sub(r'[^a-z0-9$]', '', k):
                return w[which]
        raise KeyError(key)

    def shake(self, t):
        dx = dy = dr = 0.0
        for (t0, amp, dur) in self.shakes:
            if t0 <= t < t0 + dur:
                k = 1 - (t - t0) / dur
                a = amp * k * k
                dx += a * math.sin(t * 91.0)
                dy += a * math.cos(t * 77.0)
                dr += a * 0.04 * math.sin(t * 63.0)
        return dx, dy, dr

    def cam(self, t):
        z, fx, fy, rot = super().cam(t)
        dx, dy, dr = self.shake(t)
        return z, fx + dx, fy + dy, rot + dr

    def events(self):
        return []

def lighten(c, k):
    c = hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)
    return tuple(int(min(255, max(0, v * k * 255))) for v in c)

def rgb(c):
    return tuple(int(v * 255) for v in hexc(c))

# ====================================================================== shared props
def lab_wall(seed=3, c0='#25302F', c1='#0E1414', spot=(CX, 900, 1250)):
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.88 + 0.24 * smooth_noise(PH, PW, 80, seed, 4))[..., None]
    img = to_img(arr)
    d = ImageDraw.Draw(img, 'RGBA')
    for x in range(-60, PW, 430):
        d.line([(x, 0), (x, PH)], fill=(0, 0, 0, 90), width=6)
        d.line([(x + 4, 0), (x + 4, PH)], fill=(255, 255, 255, 18), width=2)
        for y in range(60, PH, 220):
            for xx in (x + 26, x + 404):
                d.ellipse((xx - 7, y - 7, xx + 7, y + 7), fill=(0, 0, 0, 90))
                d.ellipse((xx - 6, y - 8, xx + 4, y + 2), fill=(255, 255, 255, 30))
    arr = to_arr(img)
    arr = arr * (0.35 + 0.95 * radial(PW, PH, *spot, 1.5))[..., None]
    return arr

def bench(arr, y_top=1290, y_front=1400, base='#6B4A30', dark='#3A2414'):
    lay = Layer()
    tex = to_img(wood(1400, 160, base, dark, seed=9, stretch=18, rings=6, contrast=0.5))
    slab(lay, tex, [(-30, y_top), (PW + 30, y_top), (PW + 30, y_front), (-30, y_front)], PH - y_front + 10, hexc(dark) * 0.9, 0.35)
    return finish(arr, lay, None)

def magnetron_sprite(r):
    """Cavity-magnetron anode block seen face-on with an oblique depth. Returns RGBA sprite, centre offset."""
    ss = 3
    dep = (0.16 * r, 0.12 * r)
    m = 12
    Wd = int(2 * r + dep[0] + 2 * m)
    Ht = int(2 * r + dep[1] + 2 * m)
    big = Image.new('RGBA', (Wd * ss, Ht * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy = (m + r) * ss, (m + r) * ss
    R = r * ss
    steps = 24
    for k in range(steps, -1, -1):
        f = k / steps
        ox, oy = dep[0] * ss * f, dep[1] * ss * f
        c = tuple(int(v) for v in np.array([120, 58, 26]) * (0.55 + 0.35 * (1 - f)))
        d.ellipse((cx + ox - R, cy + oy - R, cx + ox + R, cy + oy + R), fill=c + (255,))
    # front face: numpy shaded copper
    yy, xx = np.mgrid[0:Ht * ss, 0:Wd * ss].astype(np.float32)
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    inside = np.clip(R - rr + 0.5, 0, 1)
    lightk = np.clip(1.05 - ((xx - cx) * 0.45 + (yy - cy) * 0.6) / (2.2 * R), 0.55, 1.3)
    rings = 0.94 + 0.06 * np.sin(rr / (2.4 * ss))
    base = np.array([214, 124, 70], np.float32) / 255
    col = base[None, None, :] * (lightk * rings)[..., None]
    rim = np.clip(1 - np.abs(rr - R * 0.975) / (R * 0.03), 0, 1)
    tl = np.clip(-((xx - cx) + (yy - cy)) / (1.4 * R), 0, 1)
    col = col + (rim * tl * 0.5)[..., None]
    face = np.concatenate([np.clip(col, 0, 1), inside[..., None]], -1)
    face_im = Image.fromarray((face * 255).astype(np.uint8), 'RGBA')
    big.alpha_composite(face_im)
    d = ImageDraw.Draw(big)
    # cavities (keyholes) and the centre bore
    nh = 8
    for k in range(nh):
        a = 2 * math.pi * k / nh + math.pi / 8
        hx, hy = cx + math.cos(a) * 0.6 * R, cy + math.sin(a) * 0.6 * R
        hr = 0.15 * R
        sw = 0.075 * R
        # slot to the bore
        ex, ey = cx + math.cos(a) * 0.25 * R, cy + math.sin(a) * 0.25 * R
        pts = []
        nx_, ny_ = -math.sin(a) * sw / 2, math.cos(a) * sw / 2
        pts = [(hx + nx_, hy + ny_), (ex + nx_, ey + ny_), (ex - nx_, ey - ny_), (hx - nx_, hy - ny_)]
        d.polygon(pts, fill=(88, 40, 18, 255))
        d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(88, 40, 18, 255))
        o = 0.05 * R
        d.ellipse((hx - hr + o, hy - hr + o, hx + hr + o * 0.6, hy + hr + o * 0.6), fill=(24, 10, 4, 255))
    br = 0.27 * R
    d.ellipse((cx - br, cy - br, cx + br, cy + br), fill=(88, 40, 18, 255))
    o = 0.05 * R
    d.ellipse((cx - br + o, cy - br + o, cx + br + o * 0.5, cy + br + o * 0.5), fill=(22, 9, 4, 255))
    cr = 0.1 * R
    d.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(150, 150, 160, 255))
    d.ellipse((cx - cr * 0.5, cy - cr * 0.7, cx + cr * 0.1, cy - cr * 0.1), fill=(230, 230, 240, 255))
    sp = big.resize((Wd, Ht), Image.LANCZOS)
    return sp, (m + r, m + r)

_GLOW = {}

def glow(img, cx, cy, r, color, a):
    if a <= 0.01 or r < 2:
        return
    rq = max(4, int(round(r / 6.0)) * 6)
    key = (rq, color)
    if key not in _GLOW:
        _GLOW[key] = glow_sprite(rq, color, 1.0)
    paste_center(img, _GLOW[key], cx, cy, alpha=min(1.0, a))

def glow_sprite(r, color=(255, 150, 60), strength=1.0):
    n = int(r * 2)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    arr = np.zeros((n, n, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

def draw_waves(img, origin, t, a0, a1, color=(90, 210, 255), speed=420, spacing=110, r0=60, rmax=900, width=9, phase=0.0):
    """Expanding wave arcs between angles a0..a1 (degrees, PIL convention)."""
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    ox, oy = origin
    k = 0
    base = (t * speed + phase) % spacing
    r = r0 + base
    while r < rmax:
        fade = max(0.0, 1 - (r - r0) / (rmax - r0))
        al = int(200 * fade)
        if al > 4:
            d.arc((ox - r, oy - r, ox + r, oy + r), a0, a1, fill=color + (int(al * 0.35),), width=width * 3)
            d.arc((ox - r, oy - r, ox + r, oy + r), a0, a1, fill=color + (al,), width=width)
        r += spacing
    img.alpha_composite(ov)

def place_magnetron(img, sp, off, cx, cy, glow=0.0, t=0.0):
    paste_at(img, sp, int(cx - off[0]), int(cy - off[1]))
    if glow > 0:
        r = int(sp.width * 0.16)
        glow(img, cx, cy, r, (255, 140, 50), glow * (0.85 + 0.15 * math.sin(t * 30)))

# ---------------------------------------------------------------- microwave oven
class Microwave:
    def __init__(self, x, y, w, h, depth=300, body='#2C3036', trim='#4D545E', handle='#B8BEC6', panel='#23262B', light_env=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        dx, dy = depth * 0.42, depth * 0.30
        self.dx, self.dy = dx, dy
        X0, Y0 = int(x - 12), int(y - dy - 12)
        X1, Y1 = int(x + w + dx + 12), int(y + h + 12)
        self.X0, self.Y0 = X0, Y0
        cw, ch = X1 - X0, Y1 - Y0
        ss = 3
        im = Image.new('RGBA', (cw * ss, ch * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        P = lambda px, py: ((px - X0) * ss, (py - Y0) * ss)
        bc = rgb(body)
        d.polygon([P(x + 14, y + 2), P(x + w - 6, y + 2), P(x + w + dx, y - dy), P(x + dx + 18, y - dy)], fill=lighten(body, 1.45 if not light_env else 1.12))
        d.polygon([P(x + w - 2, y + 10), P(x + w + dx, y - dy + 8), P(x + w + dx, y + h - dy - 10), P(x + w - 2, y + h - 8)], fill=lighten(body, 0.62))
        d.rounded_rectangle([P(x, y), P(x + w, y + h)], radius=24 * ss, fill=bc + (255,))
        # door
        dr = (x + 18, y + 18, x + 0.715 * w, y + h - 18)
        d.rounded_rectangle([P(dr[0], dr[1]), P(dr[2], dr[3])], radius=16 * ss, fill=lighten(body, 1.12) + (255,), outline=lighten(trim, 1.0) + (255,), width=4 * ss)
        wr = (x + 0.075 * w, y + 0.13 * h, x + 0.595 * w, y + 0.87 * h)
        self.win = wr
        d.rounded_rectangle([P(wr[0] - 6, wr[1] - 6), P(wr[2] + 6, wr[3] + 6)], radius=16 * ss, fill=(10, 10, 12, 255))
        d.rounded_rectangle([P(wr[0], wr[1]), P(wr[2], wr[3])], radius=12 * ss, fill=(0, 0, 0, 0))
        # handle
        hx = x + 0.655 * w
        d.rounded_rectangle([P(hx - 11, y + 0.2 * h), P(hx + 11, y + 0.8 * h)], radius=11 * ss, fill=rgb(handle) + (255,))
        d.rounded_rectangle([P(hx - 9, y + 0.2 * h + 4), P(hx - 2, y + 0.8 * h - 4)], radius=4 * ss, fill=(255, 255, 255, 140))
        # control panel
        px0 = x + 0.74 * w
        d.rounded_rectangle([P(px0, y + 18), P(x + w - 18, y + h - 18)], radius=12 * ss, fill=rgb(panel) + (255,))
        dsp = (px0 + 18, y + 0.10 * h, x + w - 36, y + 0.25 * h)
        self.disp = dsp
        d.rounded_rectangle([P(*dsp[:2]), P(*dsp[2:])], radius=6 * ss, fill=(6, 14, 9, 255), outline=(70, 76, 84, 255), width=2 * ss)
        bw = (x + w - 36 - (px0 + 18))
        for r_ in range(4):
            for c_ in range(3):
                bx = px0 + 18 + c_ * bw / 3 + 6
                by = y + 0.32 * h + r_ * 0.1 * h
                d.rounded_rectangle([P(bx, by), P(bx + bw / 3 - 12, by + 0.07 * h)], radius=5 * ss, fill=lighten(panel, 1.9) + (255,))
        d.rounded_rectangle([P(px0 + 24, y + 0.75 * h), P(x + w - 42, y + 0.86 * h)], radius=8 * ss, fill=(70, 160, 90, 255))
        sp = im.resize((cw, ch), Image.LANCZOS)
        a = np.asarray(sp, np.float32)
        g = np.linspace(1.12, 0.82, ch)[:, None]
        a[..., :3] *= g[..., None]
        self.body = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
        # glass overlay for the window
        gw, gh = int(wr[2] - wr[0]), int(wr[3] - wr[1])
        glass = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glass)
        gd.rounded_rectangle((0, 0, gw - 1, gh - 1), radius=12, fill=(10, 12, 16, 70))
        for yy in range(4, gh, 9):
            for xx in range(4 + (yy // 9 % 2) * 4, gw, 9):
                gd.ellipse((xx - 2, yy - 2, xx + 2, yy + 2), fill=(0, 0, 0, 80))
        gd.polygon([(gw * 0.08, 0), (gw * 0.3, 0), (gw * 0.05, gh), (0, gh), (0, gh * 0.7)], fill=(255, 255, 255, 22))
        self.glass = glass
        # interior glow (precomputed)
        yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
        dd = np.sqrt(((xx - gw * 0.5) / (gw * 0.7)) ** 2 + ((yy - gh * 0.35) / (gh * 0.8)) ** 2)
        k = np.clip(1 - dd, 0, 1) ** 1.2
        on = np.zeros((gh, gw, 4), np.float32)
        on[..., 0] = 60 + 195 * k; on[..., 1] = 40 + 175 * k; on[..., 2] = 10 + 90 * k; on[..., 3] = 255
        off = np.zeros((gh, gw, 4), np.float32)
        off[..., 0] = 14 + 16 * k; off[..., 1] = 14 + 14 * k; off[..., 2] = 16 + 12 * k; off[..., 3] = 255
        self.on_arr, self.off_arr = on, off
        mask = Image.new('L', (gw, gh), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, gw - 1, gh - 1), radius=12, fill=255)
        self.mask = mask
        self.bowl = self._bowl(gw)

    def _bowl(self, gw):
        lay = Layer(int(gw * 0.5), int(gw * 0.3))
        ellipsoid(lay, (lay.w / 2, lay.h * 0.55), lay.w * 0.36, lay.h * 0.32, 0, '#E9E4DA', spec=0.5)
        ellipsoid(lay, (lay.w / 2, lay.h * 0.4), lay.w * 0.3, lay.h * 0.12, 0, '#C2462E', spec=0.6)
        sp, _, _ = layer_sprite(lay, 2)
        return sp

    def draw(self, img, t, light=1.0, display='', disp_col=(110, 255, 140), spin=True):
        wr = self.win
        gw, gh = self.glass.size
        arr = self.off_arr * (1 - light) + self.on_arr * light
        inter = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        di = ImageDraw.Draw(inter)
        # turntable plate
        cxp, cyp = gw * 0.5, gh * 0.8
        di.ellipse((cxp - gw * 0.36, cyp - gh * 0.09, cxp + gw * 0.36, cyp + gh * 0.09),
                   fill=(int(150 + 80 * light), int(150 + 70 * light), int(140 + 50 * light), 255))
        bx = cxp + (math.sin(t * 2.2) * gw * 0.08 if spin else 0)
        paste_center(inter, self.bowl, bx, cyp - gh * 0.08, scale=1.0)
        inter.putalpha(self.mask)
        paste_at(img, inter, int(wr[0]), int(wr[1]))
        paste_at(img, self.glass, int(wr[0]), int(wr[1]))
        paste_at(img, self.body, self.X0, self.Y0)
        if display:
            d0, d1, d2, d3 = self.disp
            f = font(int((d3 - d1) * 0.62), FONT_BOLD)
            bb = f.getbbox(display)
            tx = (d0 + d2) / 2 - (bb[2] + bb[0]) / 2
            ty = (d1 + d3) / 2 - (bb[3] + bb[1]) / 2
            ImageDraw.Draw(img).text((tx, ty), display, font=f, fill=disp_col + (255,))

    def shadow_into(self, arr, k=0.6):
        a = np.zeros((PH, PW), np.float32)
        al = np.asarray(self.body.getchannel('A'), np.float32) / 255
        h, w = al.shape
        a[self.Y0:self.Y0 + h, self.X0:self.X0 + w] = al
        return shadow(arr, a, 30, 30, 26, k)

def kitchen_dark():
    arr = vgrad(PW, PH, [(0, '#1A2326'), (1, '#0C1012')])
    img = to_img(arr)
    d = ImageDraw.Draw(img, 'RGBA')
    tw, th = 150, 75
    for r, y in enumerate(range(0, 1300, th)):
        off = (r % 2) * tw // 2
        for x in range(-tw + off, PW + tw, tw):
            d.rounded_rectangle((x + 3, y + 3, x + tw - 3, y + th - 3), radius=8, fill=(40, 58, 62, 255))
            d.line([(x + 8, y + 6), (x + tw - 12, y + 6)], fill=(255, 255, 255, 25), width=3)
    arr = to_arr(img.filter(ImageFilter.GaussianBlur(1.2)))
    arr = arr * (0.25 + 0.95 * radial(PW, PH, CX, 1000, 1150, 1.4))[..., None]
    arr = bench(arr, 1270, 1385, '#4A3A30', '#231A14')
    return vignette(arr, 0.5)

def kitchen_bright():
    arr = vgrad(PW, PH, [(0, '#E9E2D6'), (1, '#CFC6B8')])
    img = to_img(arr)
    d = ImageDraw.Draw(img, 'RGBA')
    tw, th = 150, 75
    for r, y in enumerate(range(0, 1300, th)):
        off = (r % 2) * tw // 2
        for x in range(-tw + off, PW + tw, tw):
            d.rounded_rectangle((x + 3, y + 3, x + tw - 3, y + th - 3), radius=8, fill=(246, 244, 240, 255))
            d.line([(x + 8, y + 6), (x + tw - 12, y + 6)], fill=(255, 255, 255, 120), width=3)
    # upper cabinet underside light
    arr = to_arr(img.filter(ImageFilter.GaussianBlur(1.0)))
    arr = arr * (0.55 + 0.55 * radial(PW, PH, CX, 900, 1300, 1.2))[..., None]
    arr = bench(arr, 1270, 1385, '#C9955F', '#8A5A32')
    return vignette(arr, 0.35)

# ---------------------------------------------------------------- stamp
def stamp_sprite(txt, size=150, color=(226, 40, 40), angle=-9):
    f = font(size)
    bb = f.getbbox(txt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 40
    w, h = tw + pad * 2, th + pad * 2
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=26, outline=color + (255,), width=16)
    d.text((20 + pad - bb[0], 20 + pad - bb[1]), txt, font=f, fill=color + (255,))
    n = smooth_noise(im.height, im.width, 6, 5, 2)
    a = np.asarray(im.getchannel('A'), np.float32) * np.clip((n - 0.22) * 3.0, 0, 1)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)

# ====================================================================== 0 hook
class Hook(Scene):
    def plate(self):
        arr = kitchen_dark()
        self.mw = Microwave(170, 800, 820, 500, depth=300)
        arr = self.mw.shadow_into(arr, 0.65)
        self.stamp = stamp_sprite('OOPS!', 170)
        return plate_img(arr)

    def cam(self, t):
        k = ease_out(t / 1.1)
        wx = (self.mw.win[0] + self.mw.win[2]) / 2 if hasattr(self, 'mw') else 450
        wy = (self.mw.win[1] + self.mw.win[3]) / 2 if hasattr(self, 'mw') else 1050
        z = 1.75 + (1.06 - 1.75) * k + 0.05 * clamp01((t - 1.1) / 2)
        fx = wx + (CX - wx) * k
        fy = wy + (1060 - wy) * k
        dx, dy, dr = self.shake(t)
        return z, fx + dx, fy + dy, -3 * (1 - k) + dr

    def events(self):
        tA = self.we('ACCIDENT')
        self.shakes = [(tA + 0.12, 26, 0.4)]
        return [(self.we('invented') + 0.05, 'ding', 0.7), (tA + 0.12, 'thud', 0.9)]

    def dyn(self, img, t):
        if not self.shakes:
            self.events()
        tD = self.we('invented') + 0.05
        n = max(0, 3 - int(t / max(0.1, tD / 3)))
        disp = f'0:0{n}' if t < tD else ('END' if int(t * 4) % 2 == 0 else '')
        light = 1.0 if t < tD else max(0.0, 1 - (t - tD) / 0.25)
        self.mw.draw(img, t, light=light, display=disp)
        tA = self.we('ACCIDENT') + 0.0
        if t >= tA:
            u = clamp01((t - tA) / 0.14)
            s = 2.4 - 1.4 * ease_out(u)
            paste_center(img, self.stamp, CX, 520, scale=s, alpha=clamp01(u * 2))

# ====================================================================== 1 radar + magnetron
class RadarLab(Scene):
    def plate(self):
        arr = lab_wall()
        arr = bench(arr, 1330, 1430)
        self.sc_c, self.sc_r = (CX, 700), 255
        cx, cy = self.sc_c
        ro, ri = 300, 255
        x0, y0, x1, y1 = int(cx - ro - 4), int(cy - ro - 4), int(cx + ro + 4), int(cy + ro + 4)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        rm, hw = (ro + ri) / 2, (ro - ri) / 2
        u = np.clip((rr - rm) / hw, -1, 1)
        a = np.clip(hw - np.abs(rr - rm) + 0.5, 0, 1)
        nz = np.sqrt(np.clip(1 - u * u, 0, 1))
        nx = u * (xx - cx) / np.maximum(rr, 1); ny = u * (yy - cy) / np.maximum(rr, 1)
        col = hexc('#555B63')[None, None, :] * (0.3 + 0.8 * np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1))[..., None]
        col = col + (0.4 * np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1) ** 30)[..., None]
        # screen
        sa = np.clip(ri - rr + 0.5, 0, 1)
        sc = hexc('#03160A')[None, None, :] * np.ones_like(rr)[..., None]
        grid = np.zeros_like(rr)
        for q in (0.33, 0.66):
            grid = np.maximum(grid, np.clip(1 - np.abs(rr - ri * q) / 2.0, 0, 1))
        grid = np.maximum(grid, np.clip(1 - np.abs(xx - cx) / 1.5, 0, 1) * (rr < ri))
        grid = np.maximum(grid, np.clip(1 - np.abs(yy - cy) / 1.5, 0, 1) * (rr < ri))
        sc = sc + hexc('#2BFF6A')[None, None, :] * (grid * 0.28)[..., None]
        sc = sc * (1 - 0.5 * (rr / ri) ** 2)[..., None]
        sub = arr[y0:y1, x0:x1]
        sub = sub * (1 - sa[..., None]) + sc * sa[..., None]
        sub = sub * (1 - a[..., None]) + col * a[..., None]
        arr[y0:y1, x0:x1] = sub
        # shadow under the bezel
        arr = vignette(arr, 0.45)
        self.mag, self.mag_off = magnetron_sprite(190)
        self.mag_c = (CX, 1150)
        lay = Layer()
        top = [(470, 1290), (826, 1290), (846, 1340), (450, 1340)]
        slab(lay, to_img(stone_tex(400, 60, '#4B5058', '#2A2D33', 7)), top, 60, '#2B2F35', 0.5)
        arr = finish(arr, lay, (0, 20, 16, 0.5))
        img = plate_img(arr)
        place_magnetron(img, self.mag, self.mag_off, *self.mag_c)
        # blips
        self.blips = [(CX + 120, 620), (CX - 160, 760), (CX + 60, 840), (CX - 70, 560), (CX + 190, 760)]
        return img

    def cam(self, t):
        tM = self.wt('MAGNETRONS')
        tR = self.wt('RADAR')
        p = 1 - ease_out(t / 0.32)
        k1 = ease_in_out((t - tM + 0.25) / 0.55)
        k2 = ease_in_out((t - tR + 0.2) / 0.5)
        fy = 740 + (1150 - 740) * k1 + (760 - 1150) * k2
        z = (1.12 + 0.07 * clamp01(t / self.dur)) * (1 + 0.12 * p)
        return z, CX, fy, 2.2 * p * self.rot_dir

    def dyn(self, img, t):
        cx, cy = self.sc_c
        ri = self.sc_r
        ang = (t * 150) % 360
        ov = Image.new('RGBA', (2 * ri, 2 * ri), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for k in range(18):
            a1 = ang - k * 4
            d.pieslice((0, 0, 2 * ri, 2 * ri), a1 - 4, a1, fill=(60, 255, 120, int(120 * (1 - k / 18) ** 2)))
        e = (ri + ri * math.cos(math.radians(ang)), ri + ri * math.sin(math.radians(ang)))
        d.line([(ri, ri), e], fill=(170, 255, 190, 255), width=5)
        for (bx, by) in self.blips:
            ba = math.degrees(math.atan2(by - cy, bx - cx)) % 360
            since = ((ang - ba) % 360) / 150.0
            br = math.exp(-since * 1.6)
            r = 9
            d.ellipse((bx - cx + ri - r, by - cy + ri - r, bx - cx + ri + r, by - cy + ri + r), fill=(150, 255, 170, int(255 * br)))
        m = Image.new('L', ov.size, 0)
        ImageDraw.Draw(m).ellipse((0, 0, 2 * ri - 1, 2 * ri - 1), fill=255)
        ov.putalpha(ImageChops.multiply(ov.getchannel('A'), m))
        img.alpha_composite(ov, (int(cx - ri), int(cy - ri)))
        tM = self.wt('MAGNETRONS')
        if t > tM - 0.2:
            draw_waves(img, self.mag_c, t, 0, 360, speed=380, spacing=120, r0=200, rmax=640, width=7)
            glow(img, self.mag_c[0], self.mag_c[1], 60, (255, 140, 50), 0.9 + 0.1 * math.sin(t * 30))
        pop(img, chip('1940s', 54, dot=(240, 160, 60)), CX, 330, t, self.wt('1940s') - 0.1, out_t=self.wt('PERCY') - 0.25)
        pop(img, chip('ENGINEER PERCY SPENCER', 46, dot=(240, 160, 60)), CX, 330, t, self.wt('PERCY') - 0.05)
        pop(img, chip('MAGNETRON', 40, bg=(255, 150, 60)), 1000, 1150, t, tM + 0.1)
        pop(img, chip('RADAR', 44, bg=(60, 255, 120)), 1030, 470, t, self.wt('RADAR'))

# ====================================================================== 2 candy bar melts in the pocket
def fabric(seed=12, base='#8DB1D6'):
    n = smooth_noise(PH, PW, 160, seed, 4)
    f = smooth_noise(PH, PW, 2, seed + 1, 1)
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    twill = 0.5 + 0.5 * np.sin((xx + yy) * 0.9)
    shade = 0.78 + 0.32 * n + 0.05 * (f - 0.5) + 0.035 * twill
    return hexc(base)[None, None, :] * shade[..., None]

class CandyPocket(Scene):
    def plate(self):
        arr = fabric()
        # placket + buttons
        img = to_img(arr)
        d = ImageDraw.Draw(img, 'RGBA')
        d.rectangle((150, 0, 255, PH), fill=(0, 0, 0, 25))
        d.line([(160, 0), (160, PH)], fill=(255, 255, 255, 60), width=3)
        d.line([(245, 0), (245, PH)], fill=(255, 255, 255, 60), width=3)
        arr = to_arr(img)
        lay = Layer()
        for by in (520, 1060, 1600):
            ellipsoid(lay, (202, by), 34, 34, 0, '#EDEDE6', spec=0.4)
        arr = finish(arr, lay, (6, 10, 8, 0.5))
        self.bg_arr = arr
        # candy bar (behind pocket)
        bar = Layer()
        bx0, bx1, by0 = 560, 900, 520
        sq = (bx1 - bx0) / 3
        for r_ in range(2):
            for c_ in range(3):
                x0 = bx0 + c_ * sq; y0 = by0 + r_ * sq * 0.8
                pts = [(x0 + 6, y0 + 6), (x0 + sq - 6, y0 + 6), (x0 + sq - 6, y0 + sq * 0.8 - 6), (x0 + 6, y0 + sq * 0.8 - 6)]
                fill_poly(bar, [(x0, y0), (x0 + sq, y0), (x0 + sq, y0 + sq * 0.8), (x0, y0 + sq * 0.8)], '#3E1E0E')
                fill_poly(bar, pts, '#6B3A1E')
                fill_poly(bar, [(x0 + 6, y0 + 6), (x0 + sq - 6, y0 + 6), (x0 + sq - 14, y0 + 14), (x0 + 14, y0 + 14)], '#8F5A35')
        # wrapper
        zig = [(bx0 - 6, 760)] + [(bx0 + k * 28, 742 + (k % 2) * 26) for k in range(1, 13)] + [(bx1 + 6, 760)]
        fill_poly(bar, zig + [(bx1 + 6, 1150), (bx0 - 6, 1150)], '#C9252C')
        fill_poly(bar, [(bx0 - 6, 860), (bx1 + 6, 860), (bx1 + 6, 900), (bx0 - 6, 900)], '#F2E9D8')
        arr = finish(arr, bar, (14, 18, 14, 0.45))
        # pocket
        pk = [(470, 860), (1010, 860), (1010, 1310), (740, 1400), (470, 1310)]
        pl = Layer()
        a, x0, y0 = poly_alpha(pk)
        tex = self.bg_arr[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] * 1.05
        pl.put(tex.astype(np.float32), a, x0, y0)
        arr = finish(arr, pl, (8, 12, 10, 0.55))
        img = to_img(arr)
        d = ImageDraw.Draw(img, 'RGBA')
        inner = [(492, 905), (988, 905), (988, 1296), (740, 1376), (492, 1296), (492, 905)]
        for i in range(len(inner) - 1):
            (ax, ay), (bx, by) = inner[i], inner[i + 1]
            L = math.hypot(bx - ax, by - ay)
            n = int(L / 22)
            for k in range(n):
                if k % 2 == 0:
                    t0, t1 = k / n, (k + 1) / n
                    d.line([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)], fill=(230, 240, 255, 170), width=4)
        d.line([(470, 892), (1010, 892)], fill=(0, 0, 0, 40), width=3)
        self.mag, self.mag_off = magnetron_sprite(240)
        img = img.convert('RGBA')
        place_magnetron(img, self.mag, self.mag_off, -40, 700)
        arr = to_arr(img)
        arr = vignette(arr, 0.45)
        self.drips = [(598, 0.15, 150, 20), (664, 0.05, 420, 28), (736, 0.3, 230, 22), (806, 0.0, 560, 30), (868, 0.45, 110, 17)]
        return plate_img(arr)

    def events(self):
        return [(self.we('MELTED') - 0.35, 'sizzle', 0.5)]

    def dyn(self, img, t):
        draw_waves(img, (-40, 700), t, -60, 60, speed=420, spacing=115, r0=260, rmax=1100, width=8)
        glow(img, -40, 700, 70, (255, 140, 50), 0.9)
        pop(img, chip('AS THE STORY GOES...', 46), CX, 330, t, 0.15)
        tm0 = self.wt('CANDY') - 0.2
        tm1 = self.we('MELTED', 't1') + 0.6
        u = clamp01((t - tm0) / (tm1 - tm0))
        if u <= 0:
            return
        # the exposed chocolate turns glossy and soft, then runs down over the wrapper and pocket
        k = ease_in_out(u)
        ov = Image.new('RGBA', (380, 290), (0, 0, 0, 0))
        do = ImageDraw.Draw(ov)
        do.rounded_rectangle((10, 10, 370, 280), radius=int(20 + 50 * k), fill=(78, 38, 17, int(150 * k)))
        do.ellipse((70, 40, 290, 100), fill=(200, 140, 100, int(90 * k)))
        do.ellipse((100, 52, 200, 76), fill=(255, 225, 195, int(110 * k)))
        paste_at(img, ov, 550, 500)
        # stain soaking into the pocket
        st = int(170 * ease_out(clamp01((u - 0.35) / 0.65)))
        if st > 0:
            sm = Image.new('RGBA', (560, 260), (0, 0, 0, 0))
            ds = ImageDraw.Draw(sm)
            for (sx, sy, rx, ry) in ((120, 70, 90, 45), (250, 90, 120, 60), (380, 75, 100, 50), (300, 140, 70, 40)):
                ds.ellipse((sx - rx, sy - ry, sx + rx, sy + ry), fill=(70, 40, 25, st))
            sm = sm.filter(ImageFilter.GaussianBlur(14))
            paste_at(img, sm, 470, 830)
        lay = Layer(520, 900)
        ox, oy = 480, 640
        lip = ease_out(clamp01(u / 0.3))
        ellipsoid(lay, (730 - ox, 762 - oy), 178 * lip + 1, 22 * lip + 1, 0, '#4A240E', spec=0.6, shin=50)
        for (x, d0, L, r) in self.drips:
            kk = ease_out(clamp01((u - d0) / (1 - d0 + 1e-6)))
            if kk <= 0:
                continue
            Lk = 20 + kk * L
            capsule(lay, (x - ox, 765 - oy), (x - ox, 765 - oy + Lk), r, r * 0.55, '#4A240E', spec=0.65, shin=60)
            sphere(lay, (x - ox, 765 - oy + Lk + r * 0.1), r * 0.78, '#4A240E', spec=0.7, shin=60)
        if lay.a.max() > 0:
            sp, x0, y0 = layer_sprite(lay, 2)
            paste_at(img, sp, ox + x0, oy + y0)

# ====================================================================== 3 popcorn
def popcorn_sprites():
    out = []
    rng = np.random.default_rng(5)
    for v in range(5):
        lay = Layer(170, 170)
        n = 7
        for k in range(n):
            a = rng.random() * 2 * math.pi
            r = 22 + rng.random() * 26
            c = (85 + math.cos(a) * r, 85 + math.sin(a) * r)
            col = '#FFF4D6' if rng.random() > 0.3 else '#F6DE9A'
            sphere(lay, c, 26 + rng.random() * 12, col, spec=0.25, amb=0.5)
        sphere(lay, (85, 85), 30, '#FFF8E4', spec=0.25, amb=0.5)
        ellipsoid(lay, (85 + rng.normal(0, 12), 85 + rng.normal(0, 12)), 12, 8, rng.random() * 3, '#C98B3C', spec=0.5)
        sp, _, _ = layer_sprite(lay, 2)
        out.append(sp)
    return out

def kernel_sprite(seed):
    rng = np.random.default_rng(seed)
    lay = Layer(60, 60)
    a = rng.random() * math.pi
    ellipsoid(lay, (30, 30), 17, 13, a, '#E8A63A', spec=0.6, shin=40)
    ellipsoid(lay, (30 + 9 * math.cos(a), 30 + 9 * math.sin(a)), 7, 6, a, '#F4E3B0', spec=0.4)
    sp, _, _ = layer_sprite(lay, 2)
    return sp

class Popcorn(Scene):
    def plate(self):
        arr = lab_wall(5)
        arr = bench(arr, 1330, 1430)
        lay = Layer()
        self.el, self.L, self.ang = (1270, 1180), 780, math.pi + 0.1
        arm(lay, self.el, self.L, self.ang)
        arr = finish(arr, lay, (20, 40, 26, 0.55))
        img = plate_img(vignette(arr, 0.45))
        self.mag, self.mag_off = magnetron_sprite(220)
        place_magnetron(img, self.mag, self.mag_off, 40, 960)
        ca, sa = math.cos(self.ang), math.sin(self.ang)
        g = lambda x, y: (self.el[0] + (x * ca - y * sa) * self.L, self.el[1] + (x * sa + y * ca) * self.L)
        rng = np.random.default_rng(11)
        self.kernels = []
        for k in range(15):
            lx = 0.64 + rng.random() * 0.2
            ly = (rng.random() - 0.5) * 0.12
            self.kernels.append((g(lx, ly), kernel_sprite(k)))
        self.kernels.sort(key=lambda kk: kk[0][1])
        self.pops = popcorn_sprites()
        return img

    def _pop_times(self):
        t0 = self.we('started') - 0.05
        rng = np.random.default_rng(3)
        order = rng.permutation(15)
        times = {}
        for j, idx in enumerate(order):
            times[int(idx)] = t0 + j * 0.056 + rng.random() * 0.025
        return times

    def events(self):
        return [(tt, 'pop', 0.5 + 0.3 * ((i * 37) % 10) / 10) for i, tt in self._pop_times().items()]

    def dyn(self, img, t):
        draw_waves(img, (40, 960), t, -55, 55, speed=420, spacing=115, r0=240, rmax=1000, width=8)
        glow(img, 40, 960, 64, (255, 140, 50), 0.9)
        times = self._pop_times()
        rng = np.random.default_rng(9)
        parts = []
        for i, ((x, y), sp) in enumerate(self.kernels):
            vx = rng.uniform(-750, 650); vy = rng.uniform(-2100, -1400); vr = rng.uniform(-500, 500)
            v = int(rng.integers(0, len(self.pops)))
            ti = times[i]
            if t < ti:
                jit = 2.5 * math.sin(t * 60 + i) if t > ti - 0.6 else 0
                paste_center(img, sp, x + jit, y)
            else:
                dt = t - ti
                px = x + vx * dt
                py = y + vy * dt + 0.5 * 3400 * dt * dt
                s = 0.35 + 0.75 * ease_back(dt / 0.12, 2.0) if dt < 0.12 else 1.1
                parts.append((px, py, vr * dt, s, v))
        for (px, py, r, s, v) in parts:
            spr = self.pops[v].rotate(r, resample=Image.BICUBIC, expand=True)
            paste_center(img, spr, px, py, scale=s)
        pop(img, chip("WORLD'S FIRST MICROWAVE POPCORN", 42, bg=(255, 220, 90)), CX, 330, t, self.we('started') + 0.35)

# ====================================================================== 4 egg explodes
def shell_sprite(seed):
    rng = np.random.default_rng(seed)
    n = 6
    r = rng.uniform(22, 44)
    pts = [(60 + math.cos(2 * math.pi * k / n + rng.random() * 0.6) * r * rng.uniform(0.6, 1.2),
            60 + math.sin(2 * math.pi * k / n + rng.random() * 0.6) * r * rng.uniform(0.6, 1.2)) for k in range(n)]
    im = Image.new('RGBA', (120, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=(246, 236, 218, 255), outline=(200, 180, 150, 255))
    d.polygon([(p[0] * 0.6 + 24, p[1] * 0.6 + 20) for p in pts[:3]] + [(60, 60)], fill=(255, 250, 240, 255))
    return im

def yolk_sprite(r, seed):
    lay = Layer(int(r * 3), int(r * 3))
    ellipsoid(lay, (r * 1.5, r * 1.5), r, r * 0.8, seed * 0.7, '#F6B21C', spec=0.8, shin=40)
    sp, _, _ = layer_sprite(lay, 2)
    return sp

def splat_sprite(R, seed):
    rng = np.random.default_rng(seed)
    S = int(R * 3.2)
    m = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    d.ellipse((c - R, c - R, c + R, c + R), fill=255)
    for k in range(16):
        a = rng.random() * 2 * math.pi
        dd = R * rng.uniform(0.7, 1.35)
        rr = R * rng.uniform(0.12, 0.32)
        x, y = c + math.cos(a) * dd, c + math.sin(a) * dd
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
        if rng.random() < 0.5:
            d.line([(c + math.cos(a) * R * 0.8, c + math.sin(a) * R * 0.8), (x, y)], fill=255, width=int(rr))
    for k in range(4):
        x = c + rng.uniform(-R * 0.6, R * 0.6)
        L = R * rng.uniform(0.6, 1.3)
        w = R * rng.uniform(0.08, 0.16)
        d.rounded_rectangle((x - w, c, x + w, c + L), radius=int(w), fill=255)
        d.ellipse((x - w * 1.4, c + L - w, x + w * 1.4, c + L + w * 1.8), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 128 else int(v * 1.6))
    a = np.asarray(m, np.float32) / 255
    # fake thickness shading from the blurred mask gradient
    bl = np.asarray(m.filter(ImageFilter.GaussianBlur(R * 0.12)), np.float32) / 255
    gy, gx = np.gradient(bl)
    sh = np.clip(0.75 - (gx * -0.6 + gy * -0.8) * R * 0.35, 0.4, 1.4)
    yolk = np.array([248, 178, 30], np.float32)
    white = np.array([255, 246, 225], np.float32)
    mix = np.clip(bl * 1.4 - 0.3, 0, 1)[..., None]
    col = (white * (1 - mix) + yolk * mix) * sh[..., None]
    spec = np.clip((gx * -0.6 + gy * -0.8) * R * 0.9 - 0.3, 0, 1) ** 2 * 255
    col = col + spec[..., None]
    arr = np.concatenate([np.clip(col, 0, 255), (a * 235)[..., None]], -1).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

class EggKettle(Scene):
    def plate(self):
        arr = lab_wall(8)
        arr = bench(arr, 1300, 1400)
        lay = Layer()
        self.kc = (730, 1090)
        # handle
        pts = [(560, 930), (575, 800), (650, 720), (730, 700), (810, 720), (885, 800), (900, 930)]
        for a_, b_ in zip(pts[:-1], pts[1:]):
            capsule(lay, a_, b_, 20, 20, '#2A2A2E', spec=0.5)
        # spout
        capsule(lay, (960, 1060), (1120, 900), 52, 26, '#AEB5BE', spec=0.7, shin=50)
        ellipsoid(lay, self.kc, 300, 235, 0, '#C3CAD2', spec=0.85, shin=45, amb=0.32)
        arr = finish(arr, lay, (24, 30, 30, 0.6))
        img = to_img(arr)
        d = ImageDraw.Draw(img, 'RGBA')
        # opening and side hole
        d.ellipse((730 - 118, 868 - 34, 730 + 118, 868 + 34), fill=(18, 18, 22, 255))
        d.ellipse((465 - 30, 1080 - 36, 465 + 30, 1080 + 36), fill=(15, 15, 18, 255), outline=(220, 225, 230, 255), width=4)
        img = img.convert('RGBA')
        self.mag, self.mag_off = magnetron_sprite(230)
        place_magnetron(img, self.mag, self.mag_off, -60, 1080)
        self.base = to_arr(img)
        # egg + front lip sprites
        lay = Layer(220, 260)
        ellipsoid(lay, (110, 130), 70, 92, 0, '#F4E8D2', spec=0.35, amb=0.45)
        self.egg, _, _ = layer_sprite(lay, 2)
        lip = Image.new('RGBA', (300, 120), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lip)
        dl.chord((150 - 124, 60 - 38, 150 + 124, 60 + 38), 0, 180, fill=(190, 198, 206, 255))
        dl.chord((150 - 112, 60 - 30, 150 + 112, 60 + 30), 0, 180, fill=(0, 0, 0, 0))
        dl.arc((150 - 124, 60 - 38, 150 + 124, 60 + 38), 10, 170, fill=(240, 244, 248, 255), width=3)
        self.lip = lip
        self.shells = [shell_sprite(k) for k in range(12)]
        self.yolks = [yolk_sprite(18 + 6 * (k % 3), k) for k in range(9)]
        self.splats = [splat_sprite(150, 1), splat_sprite(120, 2), splat_sprite(95, 3)]
        return plate_img(self.base)

    def events(self):
        tX = self.we('EXPLODED') - 0.06
        tF = self.we('FACE', 't1') - 0.1
        self.shakes = [(tX, 40, 0.6), (tF, 18, 0.3)]
        return [(tX, 'boom', 0.95), (tF, 'splat', 0.9), (self.we('EGG') + 0.2, 'rattle', 0.35)]

    def dyn(self, img, t):
        if not self.shakes:
            self.events()
        tE = self.we('EGG')
        tX = self.we('EXPLODED') - 0.06
        draw_waves(img, (-60, 1080), t, -40, 40, speed=420, spacing=110, r0=250, rmax=560, width=8)
        glow(img, -60, 1080, 66, (255, 140, 50), 0.9)
        ex, ey = 730, 830
        if t < tX:
            amp = 9 * clamp01((t - tE) / max(0.3, tX - tE))
            rot = amp * math.sin(t * 46)
            jx = amp * 0.4 * math.sin(t * 71)
            egg = self.egg.rotate(rot, resample=Image.BICUBIC, expand=True)
            paste_center(img, egg, ex + jx, ey)
            # steam from the spout
            for k in range(4):
                ph = (t * 0.9 + k * 0.25) % 1
                a = (1 - ph) * 0.35 * clamp01((t - tE) / 0.6)
                r = 30 + 70 * ph
                glow(img, 1125 + 30 * ph, 880 - 260 * ph, r, (240, 240, 245), a * 1.5)
        paste_center(img, self.lip, 730, 868 + 22)
        if t >= tX:
            dt = t - tX
            rng = np.random.default_rng(4)
            # smoke
            for k in range(5):
                r = 80 + 420 * ease_out(dt / 0.9) * (0.6 + 0.1 * k)
                a = max(0, 0.5 - dt * 0.55)
                if a > 0:
                    glow(img, ex + rng.normal(0, 60), ey - 40 + rng.normal(0, 40), r, (230, 225, 210), a)
            for k, sp in enumerate(self.shells + self.yolks):
                a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
                sp_ = rng.uniform(1300, 2600)
                vx, vy = math.cos(a) * sp_, math.sin(a) * sp_
                px = ex + vx * dt
                py = ey + vy * dt + 0.5 * 3600 * dt * dt
                s = 1.0 + (2.2 if k % 3 == 0 else 0.6) * dt
                r = rng.uniform(-700, 700) * dt
                if py < PH + 200:
                    spr = sp.rotate(r, resample=Image.BICUBIC, expand=True)
                    paste_center(img, spr, px, py, scale=s)

    def post(self, fr, t):
        tX = self.we('EXPLODED') - 0.06
        if tX <= t < tX + 0.3:
            a = (1 - (t - tX) / 0.3) * 0.85
            white = Image.new('RGB', fr.size, (255, 248, 230))
            fr.paste(Image.blend(fr, white, a))
        tF = self.we('FACE', 't1') - 0.1
        if t >= tF:
            for k, (sp, sx, sy, d0) in enumerate(((self.splats[0], 250, 470, 0.0), (self.splats[1], 860, 900, 0.05),
                                                   (self.splats[2], 300, 1580, 0.09))):
                dt = t - tF - d0
                if dt < 0:
                    continue
                s = 0.3 + 0.7 * ease_out(dt / 0.08) if dt < 0.08 else 1.0
                paste_center(fr, sp, sx, sy + 30 * dt, scale=s * 1.25)

# ====================================================================== 5 water molecules
def h2o_sprite():
    lay = Layer(220, 200)
    c = (110, 115)
    for s in (-1, 1):
        a = math.radians(90 + s * 52.25)
        hx, hy = c[0] + math.cos(a) * 62 * -1, c[1] - math.sin(a) * 62
    sphere(lay, c, 50, '#E5483D', spec=0.5, shin=30)
    for s in (-1, 1):
        ang = math.radians(52.25) * s
        hx, hy = c[0] + math.sin(ang) * 62, c[1] + math.cos(ang) * 62
        sphere(lay, (hx, hy), 32, '#F3F3F3', spec=0.5, shin=30)
    sp, _, _ = layer_sprite(lay, 2)
    return sp

class Molecules(Scene):
    def plate(self):
        cool = vgrad(PW, PH, [(0, '#07142C'), (0.5, '#0D2A52'), (1, '#050B18')])
        warm = vgrad(PW, PH, [(0, '#2A0C06'), (0.5, '#6A2310'), (1, '#1A0603')])
        n = smooth_noise(PH, PW, 120, 3, 3)[..., None]
        cool = vignette(cool * (0.85 + 0.3 * n), 0.5)
        warm = vignette(warm * (0.85 + 0.3 * n), 0.5)
        self.cool, self.warm = plate_img(cool), plate_img(warm)
        self.h2o = h2o_sprite()
        rng = np.random.default_rng(21)
        self.mols = []
        for r_ in range(4):
            for c_ in range(3):
                x = 220 + c_ * 300 + (r_ % 2) * 120 + rng.normal(0, 18)
                y = 780 + r_ * 175 + rng.normal(0, 14)
                self.mols.append((x, y, rng.uniform(0, 360), rng.uniform(0, 6.28), rng.uniform(0.8, 1.05)))
        return self.cool

    def heat(self, t):
        return ease_in_out((t - self.wt('shaking')) / max(0.5, self.wt('HOT') - self.wt('shaking') + 0.3))

    def events(self):
        return [(self.wt('shaking') - 0.1, 'riser', 0.45), (self.wt('HOT') + 0.1, 'sizzle', 0.45)]

    def dyn(self, img, t):
        h = self.heat(t)
        if h > 0:
            img.paste(Image.blend(self.cool, self.warm, h))
        # wave
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        pts = [(x, 560 + 70 * math.sin((x / 190.0) - t * 9)) for x in range(0, PW + 10, 10)]
        d.line(pts, fill=(90, 210, 255, 70), width=26)
        d.line(pts, fill=(140, 230, 255, 255), width=9)
        img.alpha_composite(ov)
        jig = 0.25 + 0.75 * ease_in_out((t - self.wt('flip')) / 0.4)
        for (x, y, a0, ph, s) in self.mols:
            ang = a0 + (12 + 38 * jig) * math.sin(t * 2 * math.pi * 6.5 + ph)
            jx = (4 + 10 * h) * math.sin(t * 53 + ph * 3)
            jy = (4 + 10 * h) * math.cos(t * 47 + ph * 2)
            spr = self.h2o.rotate(ang, resample=Image.BICUBIC, expand=True)
            paste_center(img, spr, x + jx, y + jy, scale=s * 0.82)
            if h > 0.05:
                glow(img, x, y, 70, (255, 120, 40), 0.35 * h)
        # thermometer
        tx, ty0, ty1 = 1180, 760, 1300
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((tx - 34, ty0 - 34, tx + 34, ty1), radius=34, fill=(220, 235, 245, 120), outline=(240, 248, 255, 255), width=5)
        lvl = ty1 - (ty1 - ty0) * (0.18 + 0.78 * h)
        d.rounded_rectangle((tx - 16, lvl, tx + 16, ty1 + 10), radius=16, fill=(235, 50, 40, 255))
        d.ellipse((tx - 56, ty1 - 20, tx + 56, ty1 + 92), fill=(235, 50, 40, 255), outline=(240, 248, 255, 255), width=5)
        d.ellipse((tx - 36, ty1 - 6, tx - 6, ty1 + 24), fill=(255, 160, 150, 255))
        pop(img, chip('MICROWAVES', 40, bg=(140, 230, 255)), 230, 450, t, 0.2)
        pop(img, chip('2.45 BILLION TIMES A SECOND', 42, bg=(255, 220, 90)), CX + 60, 340, t, self.wt('BILLIONS') - 0.05)
        pop(img, chip('WATER MOLECULES', 42), 400, 690, t, self.wt('WATER') - 0.05)
        pop(img, chip('HOT!', 56, bg=(255, 80, 50), fg=(255, 255, 255)), tx - 30, 640, t, self.wt('HOT'))

# ====================================================================== 6 giant first microwave
def mannequin(layer, cx, yf, Hh, color=ARM_LIGHT):
    col = hexc(color); j = col * 0.86
    kw = dict(grain=grain_map(), spec=0.28, shin=22)
    P = lambda u, v: (cx + u * Hh, yf - Hh + v * Hh)
    for s in (-1, 1):
        hip, knee, ank = P(s * 0.055, 0.50), P(s * 0.062, 0.73), P(s * 0.064, 0.945)
        capsule(layer, hip, knee, 0.055 * Hh, 0.04 * Hh, col, **kw)
        capsule(layer, knee, ank, 0.039 * Hh, 0.028 * Hh, col, **kw)
        sphere(layer, knee, 0.043 * Hh, j, **kw)
        sphere(layer, ank, 0.03 * Hh, j, **kw)
        ellipsoid(layer, P(s * 0.075, 0.975), 0.05 * Hh, 0.024 * Hh, 0, col, **kw)
    ellipsoid(layer, P(0, 0.49), 0.105 * Hh, 0.062 * Hh, 0, col, **kw)
    ellipsoid(layer, P(0, 0.41), 0.078 * Hh, 0.07 * Hh, 0, j, **kw)
    ellipsoid(layer, P(0, 0.295), 0.118 * Hh, 0.125 * Hh, 0, col, **kw)
    capsule(layer, P(0, 0.175), P(0, 0.135), 0.03 * Hh, 0.027 * Hh, col, **kw)
    ellipsoid(layer, P(0, 0.075), 0.056 * Hh, 0.072 * Hh, 0, col, **kw)
    for s in (-1, 1):
        sh, el, wr = P(s * 0.128, 0.205), P(s * 0.152, 0.37), P(s * 0.162, 0.52)
        capsule(layer, sh, el, 0.035 * Hh, 0.029 * Hh, col, **kw)
        capsule(layer, el, wr, 0.028 * Hh, 0.022 * Hh, col, **kw)
        sphere(layer, sh, 0.042 * Hh, j, **kw)
        sphere(layer, el, 0.031 * Hh, j, **kw)
        ellipsoid(layer, P(s * 0.165, 0.565), 0.027 * Hh, 0.046 * Hh, 0, col, **kw)

def cabinet_sprite(w=480, h=1000, dep=150):
    dx, dy = dep * 0.72, dep * 0.52
    ss = 2
    Wd, Ht = int(w + dx + 20), int(h + dy + 20)
    X0, Y0 = 10, int(dy) + 10
    im = Image.new('RGBA', (Wd * ss, Ht * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda x, y: ((X0 + x) * ss, (Y0 + y) * ss)
    d.polygon([P(0, 0), P(w, 0), P(w + dx, -dy), P(dx, -dy)], fill=(206, 211, 216, 255))
    d.polygon([P(w, 0), P(w + dx, -dy), P(w + dx, h - dy), P(w, h)], fill=(108, 114, 121, 255))
    d.rectangle([P(0, 0), P(w, h)], fill=(170, 176, 183, 255))
    # vents top
    for k in range(6):
        y = 40 + k * 22
        d.rounded_rectangle([P(60, y), P(w - 60, y + 9)], radius=4 * ss, fill=(60, 64, 70, 255))
    # dials strip
    d.rectangle([P(30, 190), P(w - 30, 290)], fill=(122, 128, 136, 255))
    for k in range(3):
        cx_ = 110 + k * 130
        d.ellipse([P(cx_ - 34, 206), P(cx_ + 34, 274)], fill=(40, 42, 46, 255))
        d.ellipse([P(cx_ - 26, 214), P(cx_ + 26, 266)], fill=(200, 204, 210, 255))
        d.line([P(cx_, 240), P(cx_ + 18, 222)], fill=(30, 30, 30, 255), width=5 * ss)
    # oven door with window
    d.rounded_rectangle([P(40, 330), P(w - 40, 650)], radius=10 * ss, fill=(150, 156, 163, 255), outline=(90, 95, 102, 255), width=4 * ss)
    d.rounded_rectangle([P(80, 370), P(w - 120, 610)], radius=8 * ss, fill=(255, 196, 110, 255))
    d.rounded_rectangle([P(w - 95, 400), P(w - 70, 580)], radius=10 * ss, fill=(220, 224, 230, 255))
    # lower vents + kick plate
    for k in range(5):
        y = 760 + k * 26
        d.rounded_rectangle([P(60, y), P(w - 60, y + 10)], radius=4 * ss, fill=(70, 74, 80, 255))
    d.rectangle([P(0, h - 40), P(w, h)], fill=(70, 74, 80, 255))
    sp = im.resize((Wd, Ht), Image.LANCZOS)
    a = np.asarray(sp, np.float32)
    n = smooth_noise(Ht, Wd, 2, 4, 1)
    brushed = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((Wd, Ht)), np.float32) / 255
    g = np.linspace(1.15, 0.85, Ht)[:, None] * (0.95 + 0.1 * brushed)
    a[..., :3] *= g[..., None]
    # window glow inner gradient
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA'), (X0, Y0)

def vbracket(img, x, y0, y1, prog, color=(255, 210, 60), width=10, cap=34):
    if prog <= 0:
        return
    d = ImageDraw.Draw(img)
    ye = y1 - (y1 - y0) * clamp01(prog)
    for off, c in ((5, (0, 0, 0, 140)), (0, color + (255,))):
        d.line([(x - cap / 2 + off, y1), (x + cap / 2 + off, y1)], fill=c, width=width)
        d.line([(x + off, y1), (x + off, ye)], fill=c, width=width)
        if prog >= 0.999:
            d.line([(x - cap / 2 + off, y0), (x + cap / 2 + off, y0)], fill=c, width=width)

class GiantOven(Scene):
    def plate(self):
        wall = vgrad(PW, PH, [(0, '#E7D6B5'), (0.6, '#CDB68E'), (1, '#8E7655')])
        wall = wall * (0.92 + 0.12 * smooth_noise(PH, PW, 90, 6, 3))[..., None]
        img = to_img(wall)
        d = ImageDraw.Draw(img, 'RGBA')
        d.rectangle((0, 1060, PW, 1450), fill=(120, 92, 60, 120))
        d.line([(0, 1060), (PW, 1060)], fill=(255, 245, 225, 140), width=6)
        arr = to_arr(img)
        lay = Layer()
        tile = Image.new('RGB', (800, 400), (235, 228, 210))
        td = ImageDraw.Draw(tile)
        for r_ in range(4):
            for c_ in range(8):
                if (r_ + c_) % 2 == 0:
                    td.rectangle((c_ * 100, r_ * 100, c_ * 100 + 99, r_ * 100 + 99), fill=(40, 38, 36))
        quad(lay, tile, [(-500, 1450), (PW + 500, 1450), (PW + 1600, PH + 200), (-1600, PH + 200)])
        arr = lay.comp(arr)
        arr = arr * (0.45 + 0.75 * radial(PW, PH, CX, 1000, 1500, 1.3))[..., None]
        arr = vignette(arr, 0.45)
        lay = Layer()
        self.feet_y = 1450
        mannequin(lay, 330, self.feet_y, 930)
        arr = finish(arr, lay, (40, 10, 30, 0.45))
        self.cab, self.cab_off = cabinet_sprite()
        self.cab_x, self.cab_y = 640, 450  # front-face top-left
        ca = np.zeros((PH, PW), np.float32)
        al = np.asarray(self.cab.getchannel('A'), np.float32) / 255
        X, Y = self.cab_x - self.cab_off[0], self.cab_y - self.cab_off[1]
        ca[Y:Y + al.shape[0], X:X + al.shape[1]] = al
        self.cab_shadow = shadow(np.zeros((PH, PW, 3), np.float32) + 1, ca, 46, 18, 26, 0.6)
        self.base = arr
        self.landed = plate_img(arr * self.cab_shadow)
        return plate_img(arr)

    def events(self):
        self.shakes = [(0.42, 30, 0.45), (self.wt('POUNDS'), 14, 0.3)]
        return [(0.42, 'thud', 1.0), (self.wt('POUNDS'), 'thud', 0.6), (self.wt('THOUSANDS') + 0.05, 'cash', 0.6),
                (self.wt('FEET'), 'tick', 0.5)]

    def dyn(self, img, t):
        if not self.shakes:
            self.events()
        u = clamp01((t - 0.06) / 0.36)
        if u >= 1:
            img.paste(self.landed)
        yoff = -1700 * (1 - u * u)
        X, Y = self.cab_x - self.cab_off[0], self.cab_y - self.cab_off[1]
        paste_at(img, self.cab, X, int(Y + yoff))
        if u >= 1 and t < 0.9:
            for k in range(6):
                dt = t - 0.42
                a = max(0, 0.45 - dt * 0.9)
                if a > 0:
                    r = 40 + 260 * dt
                    glow(img, 640 + k * 100 + 60 * dt * (k - 2.5), 1440 - 30 * dt, r, (230, 215, 190), a)
        tF = self.wt('FEET')
        vbracket(img, 1240, 450, 1450, ease_in_out((t - tF + 0.15) / 0.4))
        pop(img, chip('NEARLY 6 FEET', 46, bg=(255, 210, 60)), 1000, 330, t, tF)
        pop(img, chip('≈ 750 POUNDS', 50, bg=(255, 255, 255)), 860, 905, t, self.wt('POUNDS') - 0.05)
        pop(img, chip('$ THOUSANDS', 50, bg=(120, 220, 120)), 330, 395, t, self.wt('THOUSANDS'))

# ====================================================================== 7 today
class Today(Scene):
    z0, z1 = 1.04, 1.14
    def plate(self):
        arr = kitchen_bright()
        self.mw = Microwave(210, 920, 720, 420, depth=260, body='#D8DCE1', trim='#A9AFB7', handle='#7E858E', panel='#2B2F35', light_env=True)
        arr = self.mw.shadow_into(arr, 0.35)
        return plate_img(arr)

    def events(self):
        return [(self.we('KITCHEN'), 'ding', 0.7)]

    def dyn(self, img, t):
        tK = self.we('KITCHEN')
        light = 1.0 if t < tK else max(0.0, 1 - (t - tK) / 0.3)
        disp = '0:0%d' % max(0, 2 - int(t / max(0.2, tK / 2))) if t < tK else 'ENJOY'
        self.mw.draw(img, t, light=light, display=disp)
        pop(img, chip('TODAY', 54, dot=(80, 200, 120)), CX, 470, t, 0.15)

# ====================================================================== 8 chalkboard
class Chalkboard(Scene):
    def plate(self):
        arr = vgrad(PW, PH, [(0, '#D9CDB4'), (1, '#A99877')])
        img = to_img(arr)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((50, 410, PW - 50, 1270), radius=14, fill=(112, 74, 40))
        d.rectangle((92, 450, PW - 92, 1230), fill=(30, 60, 45))
        d.rectangle((70, 1235, PW - 70, 1285), fill=(132, 92, 52))
        arr = to_arr(img)
        n = smooth_noise(PH, PW, 70, 31, 4)
        board = np.zeros((PH, PW), np.float32); board[450:1230, 92:PW - 92] = 1
        arr = arr + (np.clip(n - 0.45, 0, 1) * 0.18 * board)[..., None]
        lay = Layer()
        for (x0, c) in ((300, '#F4F1EA'), (380, '#F2C9C9'), (1000, '#F4F1EA')):
            capsule(lay, (x0, 1252), (x0 + 70, 1252), 10, 10, c, spec=0.2, amb=0.5)
        arr = finish(arr, lay, (4, 6, 4, 0.5))
        arr = arr * (0.6 + 0.5 * radial(PW, PH, CX, 900, 1300, 1.2))[..., None]
        # chalk text layers (revealed per frame)
        self.lines = []
        for k, txt in enumerate(('GRAMMAR', 'SCHOOL')):
            im = Image.new('L', (PW, 260), 0)
            f = font(190, FONT_BLACK)
            bb = f.getbbox(txt)
            ImageDraw.Draw(im).text((CX - (bb[2] + bb[0]) / 2, 130 - (bb[3] + bb[1]) / 2), txt, font=f, fill=255)
            nn = smooth_noise(260, PW, 2, 40 + k, 1)
            a = np.asarray(im, np.float32) / 255 * np.clip((nn - 0.18) * 2.2, 0, 1) * 0.92
            arr_l = np.zeros((260, PW, 4), np.uint8)
            arr_l[..., :3] = 242
            arr_l[..., 3] = (a * 255).astype(np.uint8)
            spr = Image.fromarray(arr_l, 'RGBA')
            xs = np.where(a.max(0) > 0.05)[0]
            self.lines.append((spr, 560 + k * 230 - 130, xs.min(), xs.max()))
        return plate_img(vignette(arr, 0.4))

    def events(self):
        tN = self.we('never')
        return [(0.15, 'scratch', 0.35), (0.65, 'scratch', 0.35), (tN + 0.05, 'swipe', 0.6), (tN + 0.3, 'swipe', 0.6)]

    def dyn(self, img, t):
        for k, (spr, y, x0, x1) in enumerate(self.lines):
            u = ease_in_out((t - 0.15 - k * 0.5) / 0.5)
            if u <= 0:
                continue
            xe = int(x0 + (x1 - x0 + 10) * u)
            img.alpha_composite(spr.crop((0, 0, xe, spr.height)), (0, int(y)))
        tN = self.we('never')
        d = ImageDraw.Draw(img)
        for k, ((ax, ay), (bx, by)) in enumerate((((170, 480), (1126, 1200)), ((1126, 480), (170, 1200)))):
            u = ease_out((t - tN - 0.05 - 0.25 * k) / 0.2)
            if u <= 0:
                continue
            ex, ey = ax + (bx - ax) * u, ay + (by - ay) * u
            d.line([(ax + 8, ay + 10), (ex + 8, ey + 10)], fill=(0, 0, 0, 120), width=58)
            d.line([(ax, ay), (ex, ey)], fill=(229, 45, 45), width=52)
        pop(img, chip('WORKING IN A MILL BY AGE 12', 42, dot=(229, 45, 45)), CX, 330, t, self.we('SCHOOL') - 0.1)

# ====================================================================== 9 patent and $2
def bill_sprite(seed):
    w, h = 470, 200
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(176, 200, 158, 255), outline=(70, 100, 62, 255), width=6)
    d.rectangle((16, 16, w - 17, h - 17), outline=(90, 125, 80, 255), width=3)
    d.ellipse((w / 2 - 70, h / 2 - 62, w / 2 + 70, h / 2 + 62), fill=(206, 222, 192, 255), outline=(90, 125, 80, 255), width=4)
    f = font(84); bb = f.getbbox('1')
    d.text((w / 2 - (bb[2] + bb[0]) / 2, h / 2 - (bb[3] + bb[1]) / 2), '1', font=f, fill=(60, 95, 55, 255))
    fs = font(34)
    for (x, y) in ((36, 26), (w - 60, 26), (36, h - 66), (w - 60, h - 66)):
        d.text((x, y), '1', font=fs, fill=(60, 95, 55, 255))
    ft = font(22)
    d.text((w / 2 - 70, h - 46), 'ONE DOLLAR', font=ft, fill=(60, 95, 55, 255))
    n = smooth_noise(h, w, 20, seed, 3)
    a = np.asarray(im, np.float32)
    a[..., :3] *= (0.9 + 0.15 * n)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

class Bonus(Scene):
    def plate(self):
        arr = table_bg(seed=8)
        lay = Layer()
        pw, ph = 700, 900
        paper = Image.new('RGB', (pw, ph), (241, 232, 210))
        d = ImageDraw.Draw(paper)
        f1 = font(64, FONT_SERIF); f2 = font(30, FONT_SERIF); f3 = font(26, FONT_SERIF)
        def ctext(y, s, f, c=(40, 30, 20)):
            bb = f.getbbox(s)
            d.text((pw / 2 - (bb[2] + bb[0]) / 2, y), s, font=f, fill=c)
        ctext(60, 'PATENT', f1)
        ctext(150, 'P. L. SPENCER', f2)
        ctext(195, 'Filed Oct. 8, 1945', f3, (90, 70, 50))
        d.line([(80, 250), (pw - 80, 250)], fill=(120, 100, 80), width=3)
        rng = np.random.default_rng(3)
        for k in range(14):
            y = 290 + k * 34
            d.rectangle((80, y, 80 + rng.integers(300, pw - 160), y + 10), fill=(170, 155, 135))
        d.ellipse((pw / 2 - 90, 790 - 90, pw / 2 + 90, 790 + 90), outline=(150, 120, 90), width=4)
        d.ellipse((pw / 2 - 30, 790 - 30, pw / 2 + 30, 790 + 30), outline=(150, 120, 90), width=4)
        for k in range(8):
            a = k * math.pi / 4
            d.line([(pw / 2 + math.cos(a) * 30, 790 + math.sin(a) * 30), (pw / 2 + math.cos(a) * 90, 790 + math.sin(a) * 90)], fill=(150, 120, 90), width=3)
        n = smooth_noise(ph, pw, 40, 4, 3)
        pa = to_arr(paper) * (0.9 + 0.12 * n)[..., None]
        quad(lay, to_img(pa), bar_corners(CX, 1000, pw, ph, 0.05))
        arr = finish(arr, lay, (24, 34, 26, 0.6))
        img = plate_img(arr)
        seal = Image.new('RGBA', (300, 340), (0, 0, 0, 0))
        dsl = ImageDraw.Draw(seal)
        dsl.polygon([(120, 170), (90, 330), (130, 300), (160, 335), (165, 175)], fill=(170, 30, 40, 255))
        dsl.polygon([(180, 170), (210, 330), (170, 300), (140, 335), (135, 175)], fill=(195, 40, 50, 255))
        pts = []
        for k in range(48):
            a = 2 * math.pi * k / 48
            rr = 95 if k % 2 == 0 else 80
            pts.append((150 + math.cos(a) * rr, 130 + math.sin(a) * rr))
        dsl.polygon(pts, fill=(212, 170, 60, 255))
        dsl.ellipse((150 - 66, 130 - 66, 150 + 66, 130 + 66), fill=(236, 200, 90, 255), outline=(170, 130, 40, 255), width=4)
        dsl.ellipse((150 - 50, 130 - 50, 150 + 50, 130 + 50), outline=(170, 130, 40, 255), width=3)
        paste_center(img, seal.rotate(8, resample=Image.BICUBIC, expand=True), 915, 790)
        self.bills = [bill_sprite(1), bill_sprite(2)]
        return img

    def events(self):
        t2 = self.we('$2.')
        return [(t2 + 0.05, 'cash', 0.55), (self.we('$2.', 't1') + 0.08, 'trombone', 0.75)]

    def dyn(self, img, t):
        t2 = self.we('$2.')
        land = t2 + 0.1
        for k, (bx, by, a_end, d0) in enumerate(((560, 1000, -12, 0.0), (760, 1090, 9, 0.35))):
            ts = 0.35 + d0
            if t < ts:
                continue
            u = clamp01((t - ts) / max(0.3, land - ts))
            y = -250 + (by + 250) * ease_in_out(u)
            sway = (1 - u) * 90 * math.sin((t - ts) * 4.2 + k)
            rot = a_end + (1 - u) * 25 * math.sin((t - ts) * 3.6 + k * 2)
            spr = self.bills[k].rotate(rot, resample=Image.BICUBIC, expand=True)
            if u >= 1:
                sh = spr.copy(); sh.putalpha(spr.getchannel('A').point(lambda v: v * 0.45))
                blk = Image.new('RGBA', sh.size, (0, 0, 0, 0)); blk.putalpha(sh.getchannel('A'))
                paste_center(img, blk.filter(ImageFilter.GaussianBlur(10)), bx + sway + 14, y + 22)
            paste_center(img, spr, bx + sway, y)
        pop(img, chip('PATENT BONUS:  $2', 60, bg=(255, 210, 60)), CX, 400, t, t2 + 0.05)

SCENES = [Hook, RadarLab, CandyPocket, Popcorn, EggKettle, Molecules, GiantOven, Today, Chalkboard, Bonus]
