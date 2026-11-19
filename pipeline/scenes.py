"""Silly Putty was a failed WWII rubber substitute (2026-11-19)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img, grain_map, finish, table_bg
from mw_scenes import glow, stamp_sprite, mannequin, bill_sprite
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import red_x

RED = (214, 50, 44)
YEL = (255, 210, 60)
BLUE = (40, 120, 200)
GREEN = (60, 170, 90)
WHITE = (255, 255, 255)
PINK = (250, 138, 150)

class Base(S):
    focus = (CX, 1100)
    z0, z1 = 1.2, 1.3

# ====================================================================== helpers
def with_shadow(img, sp, cx, cy, blur=14, a=0.45, dx=18, dy=26):
    sh, pad = shadow_of(sp, blur, a)
    paste_at(img, sh, cx - sp.width / 2 - pad + dx, cy - sp.height / 2 - pad + dy)
    paste_at(img, sp, cx - sp.width / 2, cy - sp.height / 2)

_SP = {}
def cached(key, fn):
    if key not in _SP:
        _SP[key] = fn()
    return _SP[key]

def rot(sp, ang, key=None):
    if key is not None:
        k = (key, int(round(ang)) % 360)
        if k in _SP:
            return _SP[k]
    r = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
    if key is not None:
        _SP[k] = r
    return r

def dome_shade(a, strength=0.55):
    from scipy.ndimage import distance_transform_edt
    d = distance_transform_edt(a > 0.5).astype(np.float32)
    m = max(1.0, d.max())
    hgt = np.sqrt(np.clip(d / m, 0, 1))
    gy, gx = np.gradient(hgt * m * 0.5)
    nz = np.ones_like(gx)
    nn = np.sqrt(gx * gx + gy * gy + nz * nz)
    nx, ny, nz = -gx / nn, -gy / nn, nz / nn
    ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
    return (1 - strength) + strength * 1.25 * ndl, hgt, ndh

def blob_alpha(n, R, seed, wob=0.06, ss=3):
    rng = np.random.default_rng(seed)
    pts = []
    K = 64
    ph = rng.uniform(0, 6.28, 4)
    for k in range(K):
        a = 2 * math.pi * k / K
        r = R * (1 + wob * (math.sin(3 * a + ph[0]) * 0.5 + math.sin(5 * a + ph[1]) * 0.3 + math.sin(2 * a + ph[2]) * 0.2))
        pts.append((n / 2 + math.cos(a) * r, n / 2 + math.sin(a) * r))
    im = Image.new('L', (n * ss, n * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((n, n), Image.BOX), np.float32) / 255

def putty_sprite(R=300, seed=1, wob=0.05, col=PINK):
    """Glossy pink putty blob."""
    def mk():
        n = int(R * 2.3)
        a = blob_alpha(n, R, seed, wob)
        from scipy.ndimage import gaussian_filter
        hgt = gaussian_filter(a, R * 0.32)
        hgt = np.clip(hgt / max(1e-3, hgt.max()), 0, 1) * a
        gy, gx = np.gradient(hgt * R * 1.1)
        nz = np.ones_like(gx)
        nn = np.sqrt(gx * gx + gy * gy + nz * nz)
        nx, ny, nz = -gx / nn, -gy / nn, nz / nn
        ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        sh = 0.42 + 0.75 * ndl
        base = np.array(col, np.float32) / 255
        noise = smooth_noise(n, n, max(4, R // 6), seed + 4, 2)
        rgb = base[None, None, :] * sh[..., None] * (0.94 + 0.1 * noise[..., None])
        rim = np.clip(1 - hgt * 1.4, 0, 1) ** 3
        rgb = rgb * (1 - 0.25 * rim[..., None])
        spec = np.clip(ndh, 0, 1) ** 30 * 0.6
        rgb = rgb + spec[..., None]
        arr = np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1)
        return Image.fromarray((arr * 255 + 0.5).astype(np.uint8), 'RGBA')
    return cached(('putty', R, seed, wob, col), mk)

def squash(sp, sx, sy, key):
    qx, qy = round(sx / 0.02) * 0.02, round(sy / 0.02) * 0.02
    k = (key, qx, qy)
    if k not in _SP:
        _SP[k] = sp.resize((max(1, int(sp.width * qx)), max(1, int(sp.height * qy))), Image.BICUBIC)
    return _SP[k]

def ball_sprite(R, col='#2A2A2E'):
    def mk():
        lay = Layer(int(R * 2.4), int(R * 2.4))
        sphere(lay, (R * 1.2, R * 1.2), R, col, spec=0.5, shin=30)
        sp, _, _ = layer_sprite(lay, 2)
        return sp
    return cached(('ball', R, col), mk)

def egg_sprite(R=300, col='#D8302A'):
    """Plastic egg (closed): egg-shaped glossy shell with a seam."""
    def mk():
        from scipy.ndimage import gaussian_filter
        w, h = int(R * 1.9), int(R * 2.5)
        ss = 3
        pts = []
        for k in range(96):
            a = 2 * math.pi * k / 96
            ry = R * 1.12
            rx = R * 0.84 * (1 - 0.13 * math.cos(a - math.pi / 2) * -1) if False else R * 0.84 * (1 + 0.12 * math.sin(a))
            pts.append((w / 2 + math.cos(a) * rx, h * 0.52 + math.sin(a) * ry))
        im = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
        a = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        hgt = gaussian_filter(a, R * 0.3)
        hgt = np.clip(hgt / max(1e-3, hgt.max()), 0, 1) * a
        gy, gx = np.gradient(hgt * R * 1.1)
        nn = np.sqrt(gx * gx + gy * gy + 1)
        nx, ny, nz = -gx / nn, -gy / nn, 1 / nn
        ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        base = hexc(col)
        rgb = base[None, None, :] * (0.38 + 0.8 * ndl)[..., None] + (ndh ** 45 * 0.9)[..., None]
        sp = Image.fromarray((np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1) * 255 + 0.5).astype(np.uint8), 'RGBA')
        d = ImageDraw.Draw(sp)
        y = h * 0.52
        ov = Image.new('RGBA', sp.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).arc((w / 2 - R * 0.84, y - R * 0.18, w / 2 + R * 0.84, y + R * 0.18), 0, 180,
                               fill=(90, 10, 10, 220), width=max(3, R // 25))
        sp.alpha_composite(Image.composite(ov, Image.new('RGBA', sp.size, (0, 0, 0, 0)), Image.fromarray((a * 255).astype(np.uint8))))
        return sp
    return cached(('egg', R, col), mk)

def egg_halves(R=300, col='#D8302A'):
    def mk():
        e = egg_sprite(R, col)
        cut = int(e.height * 0.52 + 300 * 0.0)
        top = e.crop((0, 0, e.width, cut))
        bot = e.crop((0, cut, e.width, e.height))
        # inner rim on the cup
        b2 = Image.new('RGBA', (bot.width, bot.height + R // 5), (0, 0, 0, 0))
        b2.alpha_composite(bot, (0, R // 10))
        d = ImageDraw.Draw(b2)
        d.ellipse((bot.width * 0.07, 0, bot.width * 0.93, R // 5), fill=(120, 18, 16, 255))
        return top, b2
    return cached(('halves', R, col), mk)

def tire_sprite(R=380):
    def mk():
        n = int(R * 2.2)
        im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = n / 2
        d.ellipse((c - R, c - R, c + R, c + R), fill=(38, 38, 42, 255))
        for k in range(36):
            a = 2 * math.pi * k / 36
            x0, y0 = c + math.cos(a) * R * 0.86, c + math.sin(a) * R * 0.86
            x1, y1 = c + math.cos(a + 0.06) * R, c + math.sin(a + 0.06) * R
            d.line([(x0, y0), (x1, y1)], fill=(20, 20, 22, 255), width=int(R * 0.06))
        d.ellipse((c - R * 0.62, c - R * 0.62, c + R * 0.62, c + R * 0.62), fill=(60, 60, 66, 255))
        d.ellipse((c - R * 0.5, c - R * 0.5, c + R * 0.5, c + R * 0.5), fill=(170, 176, 186, 255))
        d.ellipse((c - R * 0.16, c - R * 0.16, c + R * 0.16, c + R * 0.16), fill=(110, 116, 126, 255))
        for k in range(5):
            a = 2 * math.pi * k / 5
            x, y = c + math.cos(a) * R * 0.32, c + math.sin(a) * R * 0.32
            d.ellipse((x - R * 0.05, y - R * 0.05, x + R * 0.05, y + R * 0.05), fill=(90, 94, 100, 255))
        arr = np.asarray(im, np.float32) / 255
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        lit = 1.15 - 0.4 * ((xx + yy) / (2 * n))
        arr[..., :3] *= lit[..., None]
        return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    return cached(('tire', R), mk)

def flask_sprite(w=300, liquid=(240, 240, 240), label=None, powder=False):
    def mk():
        h = int(w * 1.35)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        neck = w * 0.18
        body = [(w / 2 - neck, 0), (w / 2 + neck, 0), (w / 2 + neck, h * 0.35), (w * 0.97, h * 0.97), (w * 0.03, h * 0.97),
                (w / 2 - neck, h * 0.35)]
        d.polygon(body, fill=(200, 230, 245, 120), outline=(240, 250, 255, 255))
        lv = h * 0.55
        k = (lv - h * 0.35) / (h * 0.62)
        xl = w / 2 - neck - (w * 0.47 - neck) * k
        d.polygon([(xl, lv), (w - xl, lv), (w * 0.97, h * 0.97), (w * 0.03, h * 0.97)], fill=liquid + (255,))
        if powder:
            rng = np.random.default_rng(3)
            for _ in range(120):
                x = rng.uniform(w * 0.1, w * 0.9); y = rng.uniform(lv + 8, h * 0.95)
                d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(205, 205, 210, 255))
        d.line([(w / 2 - neck, 0), (w / 2 - neck, h * 0.35), (w * 0.03, h * 0.97), (w * 0.97, h * 0.97), (w / 2 + neck, h * 0.35),
                (w / 2 + neck, 0)], fill=(235, 248, 255, 255), width=8)
        d.line([(w / 2 - neck * 0.4, h * 0.05), (w / 2 - neck * 0.4, h * 0.3)], fill=(255, 255, 255, 200), width=6)
        d.rectangle((w / 2 - neck - 10, 0, w / 2 + neck + 10, 18), fill=(235, 248, 255, 255))
        return im
    return cached(('flask', w, liquid, powder), mk)

def beaker_sprite(w=420, fill=0.0, col=(250, 138, 150)):
    key = ('beaker', w, round(fill, 2))
    if key in _SP:
        return _SP[key]
    h = int(w * 1.05)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((10, 20, w - 10, h - 6), fill=(200, 230, 245, 90))
    if fill > 0:
        top = h - 6 - (h - 40) * 0.6 * fill
        d.rectangle((14, top, w - 14, h - 10), fill=col + (255,))
        d.ellipse((14, top - 18, w - 14, top + 18), fill=tuple(min(255, int(c * 1.12)) for c in col) + (255,))
    d.line([(10, 20), (10, h - 6), (w - 10, h - 6), (w - 10, 20)], fill=(235, 248, 255, 255), width=10)
    for k in range(4):
        y = h * 0.3 + k * h * 0.15
        d.line([(w - 70, y), (w - 14, y)], fill=(235, 248, 255, 220), width=5)
    _SP[key] = im
    return im

def catalog_sprite(w=900):
    def mk():
        h = int(w * 1.25)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, w, h), fill=(248, 240, 222, 255))
        d.rectangle((0, 0, w, h * 0.15), fill=(176, 40, 36, 255))
        f = font(int(w * 0.075))
        t = 'HOLIDAY GIFTS'
        d.text(((w - f.getlength(t)) / 2, h * 0.035), t, font=f, fill=(255, 240, 200))
        cols = [(70, 120, 190), (90, 160, 90), (230, 170, 50)]
        boxes = [(0.06, 0.2, 0.46, 0.5), (0.54, 0.2, 0.94, 0.5), (0.06, 0.56, 0.46, 0.86), (0.54, 0.56, 0.94, 0.86)]
        for k, (x0, y0, x1, y1) in enumerate(boxes):
            d.rounded_rectangle((w * x0, h * y0, w * x1, h * y1), radius=18, outline=(120, 90, 60, 255), width=5,
                                fill=(255, 250, 238, 255))
            if k != 3:
                cx, cy = w * (x0 + x1) / 2, h * (y0 + y1) / 2 - h * 0.02
                c = cols[k % 3]
                if k == 0:
                    d.rectangle((cx - 70, cy - 60, cx + 70, cy + 60), fill=c + (255,))
                elif k == 1:
                    d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=c + (255,))
                else:
                    d.polygon([(cx, cy - 75), (cx + 80, cy + 60), (cx - 80, cy + 60)], fill=c + (255,))
                for j in range(2):
                    y = h * y1 - h * 0.06 + j * 22
                    d.line([(w * x0 + 40, y), (w * x1 - 60 - j * 50, y)], fill=(150, 130, 110, 255), width=10)
        x0, y0, x1, y1 = boxes[3]
        cx, cy = w * (x0 + x1) / 2, h * (y0 + y1) / 2 - h * 0.03
        paste_center(im, putty_sprite(80, 4), cx, cy)
        f2 = font(int(w * 0.036))
        for j, t in enumerate(('BOUNCING', 'PUTTY')):
            d = ImageDraw.Draw(im)
            d.text((cx - f2.getlength(t) / 2, h * y1 - h * 0.085 + j * f2.size * 1.1), t, font=f2, fill=(160, 40, 30))
        arr = np.asarray(im, np.float32) / 255
        arr[..., :3] *= (0.92 + 0.08 * smooth_noise(h, w, 30, 4, 2))[..., None]
        return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    return cached(('cat', w), mk)

def item_box(w=900):
    """Return the catalog-relative centre of the putty box."""
    h = int(w * 1.25)
    return w * 0.74, h * 0.68

def gift_sprite(w=300):
    def mk():
        lay = Layer(w + 20, int(w * 1.1) + 20)
        fill_poly(lay, [(10, w * 0.3), (w + 10, w * 0.3), (w + 10, w * 1.05), (10, w * 1.05)], '#3C8CD0')
        fill_poly(lay, [(0, w * 0.18), (w + 20, w * 0.18), (w + 20, w * 0.36), (0, w * 0.36)], '#4FA0E0')
        fill_poly(lay, [(w * 0.44, w * 0.18), (w * 0.62, w * 0.18), (w * 0.62, w * 1.05), (w * 0.44, w * 1.05)], '#F2D04A')
        sp, _, _ = layer_sprite(lay, 2)
        d = ImageDraw.Draw(sp)
        c = sp.width * 0.53
        d.ellipse((c - w * 0.3, 0, c, w * 0.2), outline=(242, 208, 74, 255), width=int(w * 0.07))
        d.ellipse((c, 0, c + w * 0.3, w * 0.2), outline=(242, 208, 74, 255), width=int(w * 0.07))
        return sp
    return cached(('gift', w), mk)

def magazine_sprite(w=800):
    def mk():
        h = int(w * 1.3)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, w, h), fill=(246, 244, 236, 255))
        f = font(int(w * 0.07))
        t = 'TALK OF THE TOWN'
        d.text(((w - f.getlength(t)) / 2, h * 0.05), t, font=f, fill=(30, 30, 34))
        d.line([(w * 0.08, h * 0.14), (w * 0.92, h * 0.14)], fill=(30, 30, 34, 255), width=5)
        for col in range(2):
            x0 = w * 0.08 + col * w * 0.44
            for k in range(16):
                y = h * 0.18 + k * h * 0.048
                if col == 1 and 5 <= k <= 11:
                    continue
                d.line([(x0, y), (x0 + w * 0.38 - (k * 37 % 70), y)], fill=(90, 90, 96, 255), width=9)
        # small egg illustration in the right column
        e = egg_sprite(70)
        paste_center(im, e, w * 0.71, h * 0.6)
        arr = np.asarray(im, np.float32) / 255
        arr[..., :3] *= (0.93 + 0.07 * smooth_noise(h, w, 30, 8, 2))[..., None]
        return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    return cached(('mag', w), mk)

def envelope_sprite(w=220, seed=0):
    def mk():
        h = int(w * 0.62)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        tone = (250, 246, 232) if seed % 2 else (236, 226, 200)
        d.rectangle((0, 0, w - 1, h - 1), fill=tone + (255,), outline=(150, 130, 100, 255), width=4)
        d.line([(0, 0), (w / 2, h * 0.55), (w, 0)], fill=(150, 130, 100, 255), width=4)
        d.rectangle((w * 0.75, h * 0.62, w * 0.9, h * 0.88), fill=(200, 60, 50, 255))
        return im
    return cached(('env', w, seed), mk)

def capsule_ship(w=520):
    def mk():
        h = int(w * 1.1)
        lay = Layer(w + 40, h + 40)
        cx = w / 2 + 20
        fill_poly(lay, [(cx - w * 0.14, 30), (cx + w * 0.14, 30), (cx + w * 0.46, h * 0.72), (cx - w * 0.46, h * 0.72)], '#C9CED6')
        fill_poly(lay, [(cx + w * 0.02, 30), (cx + w * 0.14, 30), (cx + w * 0.46, h * 0.72), (cx + w * 0.18, h * 0.72)], '#9EA5B0')
        fill_poly(lay, [(cx - w * 0.48, h * 0.72), (cx + w * 0.48, h * 0.72), (cx + w * 0.4, h * 0.86), (cx - w * 0.4, h * 0.86)], '#7A818C')
        fill_poly(lay, [(cx - w * 0.3, h * 0.86), (cx + w * 0.3, h * 0.86), (cx + w * 0.2, h * 1.02), (cx - w * 0.2, h * 1.02)], '#4C525C')
        ellipsoid(lay, (cx - w * 0.05, h * 0.4), w * 0.07, w * 0.09, 0, '#2A3E66', spec=0.9, shin=40)
        sp, _, _ = layer_sprite(lay, 2)
        return sp
    return cached(('ship', w), mk)

def wrench_sprite(L=460):
    def mk():
        im = Image.new('RGBA', (L + 40, int(L * 0.4)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cy = im.height / 2
        d.rounded_rectangle((60, cy - L * 0.05, L - 40, cy + L * 0.05), radius=20, fill=(176, 184, 196, 255))
        d.ellipse((L - 110, cy - L * 0.13, L + 30, cy + L * 0.13), fill=(176, 184, 196, 255))
        d.rectangle((L - 30, cy - L * 0.045, L + 40, cy + L * 0.045), fill=(0, 0, 0, 0))
        d.ellipse((0, cy - L * 0.12, 130, cy + L * 0.12), fill=(176, 184, 196, 255))
        d.ellipse((35, cy - L * 0.055, 95, cy + L * 0.055), fill=(0, 0, 0, 0))
        d.line([(80, cy - L * 0.03), (L - 60, cy - L * 0.03)], fill=(225, 230, 238, 255), width=6)
        return im
    return cached(('wrench', L), mk)

def qmark(size=220, col=(255, 255, 255)):
    return cached(('q', size, col), lambda: text_img('?', size, fill=col, stroke=12, stroke_fill=(20, 20, 30), shadow_px=5))

# ====================================================================== plates
_PL = {}
def wall_plate(c0='#F2B266', c1='#B5562C', seed=3, spot=(CX, 900, 1300), counter=None):
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

def table_plate(seed=5):
    key = ('table', seed)
    if key not in _PL:
        _PL[key] = plate_img(table_bg(seed))
    return _PL[key].copy()

def space_plate(moon=True):
    key = ('space', moon)
    if key not in _PL:
        arr = vgrad(PW, PH, [(0, '#0B1230'), (1, '#02040C')])
        arr = arr * (0.8 + 0.4 * radial(PW, PH, CX, 900, 1300, 1.2))[..., None]
        rng = np.random.default_rng(7)
        for _ in range(500):
            x, y = int(rng.uniform(0, PW)), int(rng.uniform(0, PH))
            r = int(rng.choice([1, 1, 2, 3]))
            arr[max(0, y - r):y + r, max(0, x - r):x + r] = rng.uniform(0.6, 1.0)
        img = to_img(arr).convert('RGBA')
        if moon:
            lay = Layer()
            sphere(lay, (PW - 120, PH - 330), 520, '#B9B6AE', spec=0.1, amb=0.3)
            sp, x0, y0 = layer_sprite(lay, 2)
            d = ImageDraw.Draw(sp)
            rng2 = np.random.default_rng(3)
            for _ in range(18):
                cx, cy = rng2.uniform(80, sp.width - 80), rng2.uniform(80, sp.height - 80)
                r = rng2.uniform(20, 70)
                if sp.getpixel((int(cx), int(cy)))[3] > 250:
                    d.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), fill=(140, 138, 132, 255))
            img.alpha_composite(sp, (x0, y0))
        _PL[key] = img
    return _PL[key].copy()

def panel_plate():
    if 'panel' not in _PL:
        arr = vgrad(PW, PH, [(0, '#5F6672'), (1, '#2B3038')])
        arr = arr * (0.9 + 0.1 * smooth_noise(PH, PW, 50, 9, 2))[..., None]
        img = to_img(vignette(arr, 0.5)).convert('RGBA')
        d = ImageDraw.Draw(img)
        for gx in range(3):
            for gy in range(5):
                x, y = 100 + gx * 380, 260 + gy * 400
                d.rounded_rectangle((x, y, x + 330, y + 340), radius=20, outline=(40, 44, 52, 255), width=8)
                for k in range(3):
                    d.ellipse((x + 40 + k * 95, y + 40, x + 100 + k * 95, y + 100),
                              fill=[(220, 70, 60, 255), (240, 200, 70, 255), (80, 200, 110, 255)][(gx + gy + k) % 3])
                d.rectangle((x + 40, y + 160, x + 290, y + 200), fill=(30, 34, 40, 255))
        _PL['panel'] = img
    return _PL['panel'].copy()

def hook_plate():
    return wall_plate('#59C2D6', '#1D4F86', 31, (CX, 950, 1250), counter=(1505, '#E8A060'))

# ====================================================================== 0: hook - giant putty blob bouncing
class Hook(Base):
    z0, z1 = 1.32, 1.36
    R = 420
    PER = 0.9
    def make_shakes(self):
        return [(0.0, 12, 0.25), (self.we('failed') - 0.02, 18, 0.35)]
    def events(self):
        ev = [(0.0, 'bigpop', 0.7)]
        for k in range(4):
            tb = self.impact(k)
            if 0 <= tb < self.we('experiment!') - 0.1:
                ev.append((tb, 'bloop', 0.55))
        ev.append((self.we('failed') - 0.03, 'buzzer', 0.5))
        ev.append((self.we('World') - 0.03, 'boom', 0.6))
        return ev
    def impact(self, k):
        return 0.22 + k * self.PER
    def plate(self):
        self.ball = putty_sprite(self.R, 1, 0.03)
        self.st = stamp_sprite('FAILED!', 200, color=RED, angle=-8)
        return hook_plate()
    def hero(self, img, t, cy=1045):
        # bounce: phase such that frame 0 is mid-fall, already stretched
        ph = ((t - 0.22) % self.PER) / self.PER  # 0 = impact
        h = 4 * ph * (1 - ph)
        y = cy + 40 - 140 * h
        v = 1 - 2 * ph   # + rising, - falling
        if ph < 0.12 or ph > 0.94:
            q = (ph if ph < 0.5 else ph - 1) / 0.12
            sq = 1 - abs(q)
            sx, sy = 1 + 0.28 * sq, 1 - 0.24 * sq
        else:
            st = 0.12 * abs(v)
            sx, sy = 1 - st * 0.6, 1 + st
        sp = squash(self.ball, sx, sy, 'hb')
        floor = cy + 40 + self.R
        # contact shadow
        sw = 0.6 + 0.4 * (1 - h)
        ov = OV(img, CX - 500, floor - 70, CX + 500, floor + 70)
        ov.d.ellipse(ov.box(CX - 380 * sw, floor - 34 * sw, CX + 380 * sw, floor + 34 * sw), fill=(0, 0, 0, int(110 * sw)))
        ov.commit()
        paste_at(img, sp, CX - sp.width / 2, y + self.ball.height / 2 - sp.height)
        # speed lines above when falling / below when rising
        if 0.12 < ph < 0.94 and abs(v) > 0.3:
            ov = OV(img, CX - 520, y - 700, CX + 520, y + 700)
            for k in (-2, -1, 0, 1, 2):
                x = CX + k * 150
                y0 = y - self.R * 1.05 if v < 0 else y + self.R * 1.05
                d = -1 if v < 0 else 1
                ov.d.line(ov.pts([(x, y0), (x, y0 + d * (90 + 40 * abs(k % 2)))]), fill=(255, 255, 255, 200), width=14)
            ov.commit()
    def dyn(self, img, t):
        self.hero(img, t)
        tF, tW = self.we('failed'), self.we('World')
        if tF - 0.02 <= t < tW - 0.05:
            stamp_in(img, self.st, CX, 1760, t, tF - 0.02)
        pop(img, C('WORLD WAR II', 96, bg=YEL), CX, 1760, t, tW - 0.06)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, 1060 + dy, dr

# ====================================================================== 1: war needs cheap rubber
class War(Base):
    z0, z1 = 1.22, 1.32
    focus = (CX, 1080)
    def make_shakes(self):
        return [(self.we('war,'), 14, 0.3), (self.we('substitute.') - 0.1, 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('war,') - 0.03, 'thud', 0.8), (self.we('cheap') - 0.03, 'pop', 0.5),
                (self.we('rubber') - 0.03, 'squeak', 0.5)]
    def plate(self):
        self.tire = tire_sprite(390)
        self.st = stamp_sprite('WWII', 150, color=(230, 200, 90), angle=-6)
        return wall_plate('#8C8F5A', '#2E331C', 12, (CX, 1000, 1200))
    def dyn(self, img, t):
        tS = self.we('substitute.')
        k = ease_out((t - tS + 0.15) / 0.35) if t > tS - 0.15 else 0
        x = CX - 220 * k
        with_shadow(img, rot(self.tire, -140 * t, 'tire'), x, 1050, a=0.5, blur=18)
        if k > 0:
            paste_center(img, qmark(300, YEL), CX + 330, 1000 + 12 * math.sin(t * 7), scale=max(0.05, ease_back(k, 2)))
        if t > self.we('war,') - 0.04:
            stamp_in(img, self.st, CX + 280, 560, t, self.we('war,') - 0.04)
        pop(img, C('NEEDED: CHEAP RUBBER', 66, bg=WHITE), CX, 1760, t, self.we('cheap') - 0.06)

# ====================================================================== 2: GE lab, James Wright mixes boric acid + silicone oil
class Lab(Base):
    z0, z1 = 1.2, 1.32
    focus = (CX, 1080)
    def make_shakes(self):
        return [(self.we('James'), 10, 0.25), (self.we('mixed'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('General') - 0.03, 'ding', 0.5), (self.we('James') - 0.03, 'pop', 0.5),
                (self.we('boric') - 0.03, 'rattle', 0.6), (self.we('silicone') - 0.03, 'bloop', 0.6),
                (self.we('with') - 0.03, 'pop', 0.4)]
    def plate(self):
        self.fl = flask_sprite(360, (236, 236, 240), powder=True)
        self.fr = flask_sprite(360, (246, 220, 120))
        self.hand = get_hand(420, -1.3)
        self.mannequin = None
        return table_plate(6)
    def dyn(self, img, t):
        tB, tSi, tM = self.we('boric'), self.we('silicone'), self.we('mixed')
        fill = 0.0
        # left flask pours on "boric"
        aL = 0 if t < tB - 0.2 else -60 * ease_out((t - tB + 0.2) / 0.35)
        aR = 0 if t < tSi - 0.2 else 60 * ease_out((t - tSi + 0.2) / 0.35)
        if t > tB:
            fill += 0.4 * clamp01((t - tB) / 0.8)
        if t > tSi:
            fill += 0.5 * clamp01((t - tSi) / 0.8)
        # stream particles
        if aL < -40:
            for k in range(14):
                u = ((t * 2.2 + k / 14) % 1)
                x = CX - 210 + 110 * u
                y = 760 + 360 * u * u
                paste_center(img, cached(('dot', 9), lambda: text_img('•', 40, fill=(240, 240, 245))), x, y)
        if aR > 40:
            ov = OV(img, CX, 700, CX + 300, 1200)
            ov.d.line(ov.pts([(CX + 200, 770), (CX + 140, 900), (CX + 90, 1130)]), fill=(246, 220, 120, 230), width=26)
            ov.commit()
        bk = beaker_sprite(500, round(fill * 20) / 20, (250, 160, 170) if t > tSi else (232, 232, 236))
        with_shadow(img, bk, CX, 1240, a=0.4)
        with_shadow(img, rot(self.fl, aL, 'fl'), CX - 330 + (110 if aL < -1 else 0), 860 if aL < -1 else 1040, a=0.4)
        with_shadow(img, rot(self.fr, aR, 'fr'), CX + 330 - (110 if aR > 1 else 0), 860 if aR > 1 else 1040, a=0.4)
        if t < tB - 0.2:
            pass
        pop(img, C('BORIC ACID', 60, bg=WHITE), CX - 260, 1580, t, tB - 0.06)
        pop(img, C('SILICONE OIL', 60, bg=YEL), CX + 260, 1700, t, tSi - 0.06)
        pop(img, C('GENERAL ELECTRIC', 70, bg=WHITE), CX, 560, t, self.we('General') - 0.06, out_t=self.we('James') - 0.12)
        pop(img, C('JAMES WRIGHT', 84, bg=YEL), CX, 560, t, self.we('James') - 0.06)
        # stirring rod once mixed
        if t > tM:
            a = (t - tM) * 7
            sx = CX + 110 * math.cos(a)
            ov = OV(img, CX - 300, 700, CX + 300, 1250)
            ov.d.line(ov.pts([(sx, 1180), (sx + 60, 760)]), fill=(225, 245, 255, 255), width=18)
            ov.commit()

# ====================================================================== 3: bounced higher than rubber
class Bounce(Base):
    z0, z1 = 1.2, 1.28
    def make_shakes(self):
        return [(self.we('higher'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5)]
        for k in range(3):
            if 0.25 + k * 0.6 < self.we('rubber!') - 0.1:
                ev.append((0.25 + k * 0.6, 'bloop', 0.45))
        ev.append((self.we('higher') - 0.03, 'ding', 0.6))
        return ev
    def plate(self):
        self.rb = ball_sprite(190)
        self.pb = putty_sprite(190, 2, 0.03)
        return wall_plate('#F3D28A', '#C27A35', 14, (CX, 950, 1200), counter=(1430, '#6A4A30'))
    def dyn(self, img, t):
        floor = 1430
        for k, (x, sp, hmax, per) in enumerate(((CX - 260, self.rb, 380, 0.6), (CX + 260, self.pb, 560, 0.6))):
            ph = ((t + 0.25) % per) / per
            h = 4 * ph * (1 - ph)
            y = floor - 150 - hmax * h
            sq = 0.2 * max(0, 1 - min(ph, 1 - ph) / 0.08)
            s2 = squash(sp, 1 + sq, 1 - sq, ('bb', k))
            ov = OV(img, x - 200, floor - 40, x + 200, floor + 40)
            sw = 0.5 + 0.5 * (1 - h)
            ov.d.ellipse(ov.box(x - 150 * sw, floor - 18, x + 150 * sw, floor + 18), fill=(0, 0, 0, int(90 * sw)))
            ov.commit()
            paste_at(img, s2, x - s2.width / 2, y + 150 + sp.height / 2 - s2.height)
        # height markers
        ov = OV(img, 0, 500, PW, floor)
        for (x, hm, col) in ((CX - 260, 380, (40, 40, 44, 255)), (CX + 260, 560, (230, 70, 90, 255))):
            yy = floor - 300 - hm
            ov.d.line(ov.pts([(x - 170, yy), (x + 170, yy)]), fill=col, width=10)
        ov.commit()
        pop(img, C('RUBBER', 58, bg=(60, 60, 66), fg=(255, 255, 255)), CX - 260, 1560, t, 0.1)
        pop(img, C('THE GOO', 58, bg=PINK), CX + 260, 1560, t, 0.2)
        pop(img, C('25% HIGHER!', 92, bg=YEL), CX, 560, t, self.we('higher') - 0.06)

# ====================================================================== 4: rejected, no use
class Rejected(Base):
    z0, z1 = 1.2, 1.3
    def tcut(self):
        return self.we('nobody') - 0.08
    def make_shakes(self):
        return [(self.we('rejected'), 18, 0.35), (self.tcut(), 10, 0.25)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('government') - 0.03, 'pop', 0.4), (self.we('rejected') - 0.02, 'thud', 0.9),
                (self.tcut(), 'buzzer', 0.35), (self.we('find') - 0.03, 'pop', 0.4)]
    def plate(self):
        self.blob = putty_sprite(260, 5, 0.08)
        self.st = stamp_sprite('REJECTED', 170, color=RED, angle=-10)
        self.paper = None
        return table_plate(8)
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            ov = OV(img, CX - 470, 520, CX + 470, 1520)
            ov.d.rectangle(ov.box(CX - 430, 560, CX + 430, 1480), fill=(246, 240, 226, 255))
            for k in range(9):
                y = 640 + k * 70
                if 860 < y < 1300:
                    continue
                ov.d.line(ov.pts([(CX - 360, y), (CX + 360 - (k * 53 % 160), y)]), fill=(120, 110, 100, 255), width=12)
            ov.commit()
            with_shadow(img, self.blob, CX, 1080 + 6 * math.sin(t * 5), a=0.4)
            pop(img, C('U.S. GOVERNMENT', 70, bg=WHITE), CX, 1760, t, self.we('government') - 0.06)
            stamp_in(img, self.st, CX, 1060, t, self.we('rejected') - 0.02)
            return
        u = t - tc
        glow(img, CX, 1050, 520, (255, 255, 255), 0.25)
        paste_center(img, rot(self.blob, 8 * math.sin(u * 3), 'blb4'), CX, 1080, scale=0.85)
        for k in range(5):
            a = u * 1.6 + k * 2 * math.pi / 5
            x = CX + math.cos(a) * 390
            y = 1060 + math.sin(a) * 260
            pop(img, qmark(170 if k % 2 else 130), x, y, t, tc + 0.05 + k * 0.08)
        pop(img, C('NO USE?!', 100, bg=YEL), CX, 1760, t, self.we('find') - 0.06)

# ====================================================================== 5: toy store catalog, gift for adults (twist 1)
class Store(Base):
    z0, z1 = 1.18, 1.32
    def make_shakes(self):
        return [(self.we('gift'), 12, 0.25), (self.we('Bouncing'), 16, 0.3)]
    def events(self):
        return [(0.02, 'riser', 0.4), (self.we('toy') - 0.03, 'ding', 0.6), (self.we('gift') - 0.03, 'bigpop', 0.6),
                (self.we('adults,') - 0.03, 'pop', 0.5), (self.we('Bouncing') - 0.03, 'bloop', 0.7)]
    def plate(self):
        self.cat = catalog_sprite(860)
        self.gift = gift_sprite(300)
        self.st = stamp_sprite('BOUNCING PUTTY', 110, color=RED, angle=-7)
        return wall_plate('#E8B4D0', '#7A3460', 17, (CX, 1000, 1300))
    def cat_pos(self):
        return CX, 1080
    def dyn(self, img, t):
        cx, cy = self.cat_pos()
        y = cy + (1 - ease_out(t / 0.3)) * 200
        with_shadow(img, rot(self.cat, -3, 'cat'), cx, y, a=0.45)
        ix, iy = item_box(860)
        px, py = cx - self.cat.width / 2 + ix, y - self.cat.height / 2 + iy
        if t > self.we('Bouncing') - 0.1:
            k = clamp01((t - self.we('Bouncing') + 0.1) / 0.25)
            ov = OV(img, px - 240, py - 260, px + 240, py + 260)
            ov.d.rounded_rectangle(ov.box(px - 200, py - 230, px + 200, py + 230), radius=24, outline=(255, 210, 60, 255), width=int(16 * k) + 1)
            ov.commit()
        pop(img, C('TOY STORE', 84, bg=YEL), CX, 560, t, self.we('toy') - 0.06, out_t=self.we('adults,') - 0.12)
        pop(img, C('GIFT FOR ADULTS!', 80, bg=WHITE), CX, 560, t, self.we('adults,') - 0.06)
        if t > self.we('gift') - 0.06:
            pop(img, rot(self.gift, 10 * math.sin(t * 5), 'gift'), CX - 330, 1380, t, self.we('gift') - 0.06)
        stamp_in(img, self.st, CX, 1760, t, self.we('Bouncing') - 0.02)
    def cam(self, t):
        z, fx, fy, r = super().cam(t)
        ix, iy = item_box(860)
        tx = CX - self.cat.width / 2 + ix
        ty = 1080 - self.cat.height / 2 + iy
        k = ease_in_out(clamp01((t - 0.5) / max(0.1, self.dur - 0.5)))
        return z, fx + (tx - fx) * 0.22 * k, fy + (ty - 120 - fy) * 0.3 * k, r

# ====================================================================== 6: Peter Hodgson, Yale students, plastic eggs
class Eggs(Base):
    z0, z1 = 1.2, 1.3
    def tgrid(self):
        return self.we('pack') - 0.1
    def make_shakes(self):
        return [(self.we('Peter'), 12, 0.25), (self.tgrid(), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('Peter') - 0.03, 'pop', 0.5), (self.we('Yale') - 0.03, 'ding', 0.5)]
        for k in range(6):
            ev.append((self.tgrid() + 0.1 + k * 0.18, 'pop', 0.4))
        return ev
    def plate(self):
        self.top, self.bot = egg_halves(300)
        self.blob = putty_sprite(150, 7, 0.06)
        self.small = egg_sprite(150)
        self.st = stamp_sprite('PLASTIC EGGS', 120, color=RED, angle=-7)
        lay = Layer()
        mannequin(lay, CX, 2050, 1150)
        img = wall_plate('#9FD8F0', '#2C6E9E', 23, (CX, 950, 1250), counter=(1400, '#C8A070'))
        self.with_m = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        return img
    def dyn(self, img, t):
        tg = self.tgrid()
        if t < tg:
            # big open egg on the counter, blob hovering above it
            with_shadow(img, self.bot, CX - 60, 1170, a=0.4)
            paste_center(img, rot(self.top, 25, 'etop'), CX + 250, 880)
            paste_center(img, self.blob, CX - 60, 930 + 16 * math.sin(t * 5 + 1.5))
            pop(img, C('PETER HODGSON', 80, bg=YEL), CX, 560, t, self.we('Peter') - 0.06, out_t=self.we('Yale') - 0.12)
            pop(img, C('YALE STUDENTS', 80, bg=WHITE), CX, 560, t, self.we('Yale') - 0.06)
            return
        pos = [(CX - 340, 860), (CX, 860), (CX + 340, 860), (CX - 340, 1190), (CX, 1190), (CX + 340, 1190)]
        for k, (x, y) in enumerate(pos):
            t0 = tg + 0.1 + k * 0.18
            if t < t0:
                continue
            if t < t0 + 0.12:
                paste_center(img, putty_sprite(70, k, 0.06), x, y - 120 + 120 * (t - t0) / 0.12)
            pop(img, self.small, x, y + 4 * math.sin(t * 6 + k), t, t0 + 0.08)
        stamp_in(img, self.st, CX, 1760, t, self.we('plastic') - 0.02)
        pop(img, C('YALE STUDENTS', 70, bg=WHITE), CX, 560, t, tg)

# ====================================================================== 7: renamed Silly Putty, $1 an egg
class Dollar(Base):
    z0, z1 = 1.2, 1.3
    def make_shakes(self):
        return [(self.we('Silly'), 14, 0.3), (self.we('one'), 18, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('renamed') - 0.03, 'pop', 0.5), (self.we('Silly') - 0.03, 'bigpop', 0.7),
                (self.we('sold') - 0.03, 'cash', 0.4), (self.we('one') - 0.03, 'cash', 0.8)]
    def plate(self):
        self.egg = egg_sprite(330)
        self.bill = bill_sprite(4)
        self.st = stamp_sprite('$1', 230, color=(40, 150, 70), angle=-10)
        return wall_plate('#FFE07A', '#D2782A', 4, (CX, 1000, 1300))
    def dyn(self, img, t):
        tO = self.we('one')
        glow(img, CX, 1060, 560, (255, 250, 200), 0.5)
        sp = rot(self.egg, 8 * math.sin(t * 3), 'egg7')
        with_shadow(img, sp, CX - (120 if t > tO - 0.1 else 0), 1000 + 10 * math.sin(t * 4), a=0.4)
        if t > tO - 0.1:
            k = ease_back((t - tO + 0.1) / 0.35, 2.0)
            paste_center(img, rot(self.bill, -14 + 4 * math.sin(t * 4), 'bill7'), CX + 270, 1300, scale=max(0.05, 1.1 * k))
        pop(img, C('SILLY PUTTY', 110, bg=YEL), CX, 560, t, self.we('Silly') - 0.06)
        stamp_in(img, self.st, CX, 1760, t, tO - 0.02)

# ====================================================================== 8: flopped at a toy fair
class Flop(Base):
    z0, z1 = 1.25, 1.18
    def make_shakes(self):
        return [(self.we('flopped'), 16, 0.35)]
    def events(self):
        return [(0.02, 'buzzer', 0.4), (self.we('flopped') - 0.02, 'thud', 0.7)]
    def plate(self):
        self.egg = egg_sprite(300)
        self.st = stamp_sprite('FLOP!', 230, color=RED, angle=-9)
        img = wall_plate('#9A9AA2', '#3A3A44', 8, (CX, 1000, 1200), counter=(1250, '#5A4A3A'))
        d = ImageDraw.Draw(img)
        d.rectangle((CX - 520, 520, CX + 520, 640), fill=(200, 60, 54, 255))
        f = font(80)
        txt = 'TOY FAIR'
        d.text((CX - f.getlength(txt) / 2, 532), txt, font=f, fill=(255, 240, 220))
        return img
    def dyn(self, img, t):
        sag = ease_out(t / 0.6)
        with_shadow(img, rot(self.egg, -8 * sag, 'egg8'), CX, 1010 + 20 * sag, a=0.4)
        stamp_in(img, self.st, CX, 1760, t, self.we('flopped') - 0.02)

# ====================================================================== 9: The New Yorker -> 250,000 orders in 3 days (twist 2)
class Orders(Base):
    z0, z1 = 1.2, 1.3
    def tcut(self):
        return self.we('over') - 0.05
    def make_shakes(self):
        return [(self.we('mentioned'), 12, 0.25), (self.we('orders'), 18, 0.35), (self.we('three'), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('New') - 0.03, 'rustle', 0.6), (self.we('mentioned') - 0.03, 'ding', 0.6),
              (self.tcut(), 'riser', 0.5)]
        for k in range(10):
            ev.append((self.tcut() + 0.1 + k * 0.2, 'tick', 0.35))
        ev += [(self.we('orders') - 0.03, 'cash', 0.8), (self.we('poured') - 0.03, 'rustle', 0.6), (self.we('three') - 0.03, 'boom', 0.6)]
        return ev
    def plate(self):
        self.mag = magazine_sprite(820)
        self.envs = [envelope_sprite(230, s) for s in range(2)]
        return wall_plate('#BFE6C8', '#2E7A4A', 9, (CX, 1000, 1300))
    def dyn(self, img, t):
        tc, tO = self.tcut(), self.we('orders')
        if t < tc:
            y = 1080 + (1 - ease_out(t / 0.3)) * 240
            with_shadow(img, rot(self.mag, 3, 'mag'), CX, y, a=0.45)
            if t > self.we('mentioned') - 0.1:
                k = clamp01((t - self.we('mentioned') + 0.1) / 0.3)
                mx, my = CX + 0.21 * 820, y + 0.1 * 1066
                ov = OV(img, mx - 260, my - 260, mx + 260, my + 260)
                ov.d.ellipse(ov.box(mx - 200, my - 220, mx + 200, my + 220), outline=(220, 40, 40, 255), width=int(18 * k) + 1)
                ov.commit()
            pop(img, C('THE NEW YORKER', 84, bg=WHITE), CX, 560, t, self.we('New') - 0.06)
            return
        u = t - tc
        rng = np.random.default_rng(4)
        for k in range(26):
            t0 = k * 0.09
            v = u - t0
            if v < 0:
                continue
            x = rng.uniform(120, PW - 120)
            yf = rng.uniform(1150, 1500)
            y = min(yf, 380 + 1600 * v * v)
            paste_center(img, rot(self.envs[k % 2], rng.uniform(-30, 30), ('env', k % 2)), x, y)
        # counter
        dur = max(0.2, self.we('250,000') - tc + 0.35)
        q = ease_out(clamp01(u / dur))
        n = int(round(250000 * q / 1000.0)) * 1000 if q < 1 else 250000
        txt = f'{n:,}'
        sp = cached(('cnt', txt), lambda: text_img(txt, 190, fill=(255, 255, 255), stroke=14, stroke_fill=(20, 20, 30), shadow_px=6))
        sc = 1.0 + (0.15 * (1 - clamp01((t - tO) / 0.3)) if t > tO else 0)
        paste_center(img, sp, CX, 900, scale=sc)
        pop(img, C('ORDERS!', 86, bg=YEL), CX, 1100, t, tO - 0.06)
        pop(img, C('IN JUST 3 DAYS!', 88, bg=WHITE), CX, 1760, t, self.we('three') - 0.06)

# ====================================================================== 10: Apollo 8 1968, held tools down in zero gravity
class Apollo(Base):
    z0, z1 = 1.2, 1.3
    def tcut(self):
        return self.we('hold') - 0.1
    def make_shakes(self):
        return [(self.we('Apollo'), 12, 0.3), (self.tcut(), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.6), (self.we('1968,') - 0.03, 'thud', 0.6), (self.we('Apollo') - 0.03, 'riser', 0.5),
                (self.we('space,') - 0.03, 'chime', 0.6), (self.tcut(), 'swipe', 0.5), (self.we('tools') - 0.03, 'splat', 0.7)]
    def plate(self):
        self.ship = capsule_ship(560)
        self.egg = egg_sprite(90, '#C9CED6')
        self.blob = putty_sprite(125, 9, 0.1)
        self.wr = wrench_sprite(520)
        self.st = stamp_sprite('IN SPACE!', 150, color=(90, 200, 255), angle=-8)
        self.panel = panel_plate()
        return space_plate()
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            x = CX - 80 + 40 * t
            y = 1000 - 20 * t
            paste_center(img, rot(self.ship, -18 + 3 * math.sin(t), 'ship'), x, y)
            paste_center(img, rot(self.egg, t * 60, 'segg'), x + 360, y - 260 + 20 * math.sin(t * 2))
            pop(img, C('1968', 84, bg=WHITE), CX - 250, 560, t, self.we('1968,') - 0.06)
            pop(img, C('APOLLO 8', 84, bg=YEL), CX + 200, 560, t, self.we('Apollo') - 0.06)
            stamp_in(img, self.st, CX, 1760, t, self.we('space,') - 0.02)
            return
        img.paste(self.panel, (0, 0))
        u = t - tc
        tT = self.we('tools')
        # wrench floats in, putty pins it to the panel
        k = ease_out(u / 0.5)
        wx = CX + 600 * (1 - k)
        wa = 35 * (1 - k) + 10 * math.sin(u * 2) * (1 - clamp01((t - tT) / 0.2))
        with_shadow(img, rot(self.wr, wa, 'wr'), wx, 1080 - 40 * (1 - k), a=0.5, blur=10)
        if t > tT - 0.08:
            s = ease_back((t - tT + 0.08) / 0.25, 2)
            paste_center(img, self.blob, CX - 10, 1080, scale=max(0.05, s))
        pop(img, C('HOLDS TOOLS IN ZERO-G', 64, bg=YEL), CX, 1760, t, tT - 0.06)

# ====================================================================== 11: nobody wanted it -> loop to hook
class Outro(Hook):
    def tswitch(self):
        return self.we('remember...') + 0.25
    def make_shakes(self):
        return [(self.we('nobody'), 12, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('nobody') - 0.03, 'pop', 0.5), (self.we('because') - 0.03, 'riser', 0.5)]
    def plate(self):
        img = Hook.plate(self)
        self.hp = img.copy()
        self.small = putty_sprite(270, 5, 0.08)
        self.eggs = egg_sprite(120)
        return wall_plate('#8E8E98', '#33333C', 6, (CX, 1000, 1200), counter=(1350, '#4A4038'))
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hp, (0, 0))
            self.hero(img, t - self.dur)   # ends exactly where frame 0 begins
            return
        sag = ease_out(t / 0.8)
        with_shadow(img, squash(self.small, 1 + 0.1 * sag, 1 - 0.1 * sag, 'sad'), CX, 1180, a=0.4)
        pop(img, C('NOBODY WANTED IT', 76, bg=WHITE), CX, 560, t, self.we('nobody') - 0.06)
        pop(img, C('...BUT', 90, bg=YEL), CX, 1760, t, self.we('because') - 0.06)
    def cam(self, t):
        tw = self.tswitch()
        if t >= tw:
            return self.z0, CX, 1060, 0.0
        dx, dy, dr = self.shake(t)
        p = 1 - ease_out(t / 0.32)
        return 1.22 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1100 + dy, 2.0 * p + dr

SCENES = [Hook, War, Lab, Bounce, Rejected, Store, Eggs, Dollar, Flop, Orders, Apollo, Outro]
