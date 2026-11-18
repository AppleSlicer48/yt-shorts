"""The chocolate chip cookie recipe was sold for $1 (2026-11-18)."""
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
CHOC = (74, 40, 22)

class Base(S):
    focus = (CX, 1100)
    z0, z1 = 1.18, 1.27

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
    """Per-pixel dome shading for a flat RGBA shape from its alpha."""
    h, w = a.shape
    from scipy.ndimage import distance_transform_edt
    d = distance_transform_edt(a > 0.5).astype(np.float32)
    m = max(1.0, d.max())
    hgt = np.sqrt(np.clip(d / m, 0, 1))
    gy, gx = np.gradient(hgt * m * 0.5)
    nz = np.ones_like(gx)
    nn = np.sqrt(gx * gx + gy * gy + nz * nz)
    nx, ny, nz = -gx / nn, -gy / nn, nz / nn
    ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    return (1 - strength) + strength * 1.25 * ndl, hgt

def blob_alpha(n, R, seed, wob=0.06, ss=3):
    rng = np.random.default_rng(seed)
    pts = []
    K = 64
    ph = rng.uniform(0, 6.28, 4)
    for k in range(K):
        a = 2 * math.pi * k / K
        r = R * (1 + wob * (math.sin(3 * a + ph[0]) * 0.5 + math.sin(5 * a + ph[1]) * 0.3 + math.sin(9 * a + ph[2]) * 0.2)
                 + rng.uniform(-wob, wob) * 0.4)
        pts.append((n / 2 + math.cos(a) * r, n / 2 + math.sin(a) * r))
    im = Image.new('L', (n * ss, n * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((n, n), Image.BOX), np.float32) / 255

def chunk_sprite(r=40, seed=0, col=CHOC):
    def mk():
        n = int(r * 2.6)
        rng = np.random.default_rng(seed + 100)
        pts = []
        K = 7
        for k in range(K):
            a = 2 * math.pi * k / K + rng.uniform(-0.3, 0.3)
            rr = r * rng.uniform(0.75, 1.15)
            pts.append((n / 2 + math.cos(a) * rr, n / 2 + math.sin(a) * rr))
        ss = 3
        im = Image.new('L', (n * ss, n * ss), 0)
        ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
        a = np.asarray(im.resize((n, n), Image.BOX), np.float32) / 255
        sh, _ = dome_shade(a, 0.7)
        base = np.array(col, np.float32) / 255
        rgb = base[None, None, :] * sh[..., None] * 1.15
        hl = np.clip(sh - 0.95, 0, 1) * 2.0
        rgb = rgb + hl[..., None] * 0.5
        arr = np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1)
        return Image.fromarray((arr * 255).astype(np.uint8), 'RGBA')
    return cached(('chunk', r, seed, col), mk)

def cookie_sprite(R=400, seed=3, bite=0.0):
    """Golden cookie with dark chocolate chunks. bite in 0..1 removes a bite from the top right."""
    key = ('cookie', R, seed, round(bite, 2))
    if key in _SP:
        return _SP[key]
    n = int(R * 2.3)
    a = blob_alpha(n, R, seed, 0.035)
    if bite > 0:
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        for (bx, by, br) in ((0.80, 0.22, 0.30), (0.62, 0.12, 0.22), (0.93, 0.42, 0.22)):
            m = np.sqrt((xx - n * bx) ** 2 + (yy - n * by) ** 2) < R * br * bite * 1.15
            a = a * (~m)
    sh, hgt = dome_shade(a, 0.5)
    noise = smooth_noise(n, n, max(4, R // 20), seed, 3)
    fine = smooth_noise(n, n, 3, seed + 9, 1)
    c_in = np.array([0.86, 0.62, 0.32], np.float32)
    c_out = np.array([0.66, 0.40, 0.17], np.float32)
    k = np.clip(1 - hgt, 0, 1)[..., None] ** 1.5
    rgb = c_in * (1 - k) + c_out * k
    rgb = rgb * (0.82 + 0.3 * noise[..., None]) * (0.92 + 0.16 * fine[..., None])
    rgb = rgb * sh[..., None]
    # crackle
    cr = smooth_noise(n, n, max(6, R // 8), seed + 3, 2)
    crack = np.exp(-((cr - 0.5) / 0.012) ** 2) * (hgt > 0.25)
    rgb = rgb * (1 - 0.35 * crack[..., None])
    img = Image.fromarray((np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1) * 255).astype(np.uint8), 'RGBA')
    rng = np.random.default_rng(seed + 50)
    for j in range(16):
        ang = rng.uniform(0, 6.28)
        rr = R * math.sqrt(rng.uniform(0.0, 0.72))
        x, y = n / 2 + math.cos(ang) * rr, n / 2 + math.sin(ang) * rr
        if a[int(y), int(x)] < 0.9:
            continue
        ch = chunk_sprite(int(R * rng.uniform(0.07, 0.11)), j + seed * 7)
        paste_center(img, ch, x, y)
    img.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    _SP[key] = img
    return img

def bar_sprite(w=760, h=420, cols=4, rows=2, wrapper=True, scored=1.0, label='SEMI-SWEET', sub='CHOCOLATE'):
    """Chocolate bar, partly unwrapped. scored 0..1 draws the groove grid."""
    key = ('bar', w, h, cols, rows, wrapper, round(scored, 2), label, sub)
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, w + 10, h + 10), radius=18, fill=(92, 50, 26, 255))
    arr = np.asarray(im, np.float32) / 255
    ys = np.linspace(1.15, 0.8, h + 20)[:, None]
    xs = np.linspace(1.08, 0.9, w + 20)[None, :]
    arr[..., :3] *= (ys * xs)[..., None]
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    gx = int(cols * scored + 0.999) if scored > 0 else 0
    for c in range(1, cols):
        if scored >= c / cols:
            x = 10 + w * c / cols
            d.line([(x, 14), (x, h + 6)], fill=(50, 24, 10, 255), width=9)
            d.line([(x + 6, 14), (x + 6, h + 6)], fill=(140, 84, 48, 255), width=3)
    for r in range(1, rows):
        if scored > 0:
            y = 10 + h * r / rows
            q = min(1.0, scored)
            d.line([(14, y), (14 + (w - 8) * q, y)], fill=(50, 24, 10, 255), width=9)
            d.line([(14, y + 6), (14 + (w - 8) * q, y + 6)], fill=(140, 84, 48, 255), width=3)
    d.line([(24, 20), (w - 4, 20)], fill=(170, 110, 70, 255), width=4)
    if wrapper:
        ww = int(w * 0.45)
        x0 = w + 10 - ww
        d.rectangle((x0, 0, w + 20, h + 20), fill=(246, 236, 214, 255))
        d.rectangle((x0, 0, x0 + 18, h + 20), fill=(222, 206, 176, 255))
        d.rectangle((x0 + 30, 24, w - 2, h - 4), outline=(160, 40, 30, 255), width=8)
        fs_ = int(h * 0.15)
        while font(fs_).getlength(label) > ww - 70 and fs_ > 12:
            fs_ -= 2
        f = font(fs_)
        tw = f.getlength(label)
        d.text((x0 + 18 + (ww - tw) / 2, h * 0.3), label, font=f, fill=(160, 40, 30))
        f2 = font(int(h * 0.11))
        tw2 = f2.getlength(sub)
        d.text((x0 + 18 + (ww - tw2) / 2, h * 0.55), sub, font=f2, fill=(90, 50, 26))
    _SP[key] = im
    return im

def icepick_sprite(L=620):
    def mk():
        lay = Layer(int(L * 0.4), L + 20)
        cx = L * 0.2
        capsule(lay, (cx, 40), (cx, L * 0.36), L * 0.06, L * 0.065, '#A0612E', spec=0.35, shin=20)
        capsule(lay, (cx, L * 0.36), (cx, L * 0.40), L * 0.07, L * 0.07, '#8D99A6', spec=0.8, shin=50)
        capsule(lay, (cx, L * 0.40), (cx, L * 0.98), L * 0.016, L * 0.004, '#C9D1DA', spec=0.9, shin=60)
        sp, _, _ = layer_sprite(lay, 2)
        return sp
    return cached(('pick', L), mk)

def bowl_sprite(w=900):
    def mk():
        h = int(w * 0.72)
        lay = Layer(w + 40, h + 40)
        cx = w / 2 + 20
        ellipsoid(lay, (cx, h * 0.55), w * 0.47, h * 0.5, 0, '#3E7FC4', spec=0.6, shin=40)
        ellipsoid(lay, (cx, h * 0.3), w * 0.47, h * 0.17, 0, '#5C9AD8', spec=0.3)
        ellipsoid(lay, (cx, h * 0.31), w * 0.42, h * 0.14, 0, '#E9C98F', spec=0.2, shin=14, amb=0.55)
        ellipsoid(lay, (cx - w * 0.05, h * 0.28), w * 0.25, h * 0.08, 0, '#F0D39C', spec=0.3, amb=0.6)
        sp, _, _ = layer_sprite(lay, 2)
        # cut the top half of the bowl body behind the dough rim
        return sp
    return cached(('bowl', w), mk)

def house_sprite(w=1100):
    def mk():
        h = int(w * 0.95)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        wall_top = h * 0.42
        d.polygon([(w * 0.02, wall_top + 10), (w * 0.5, h * 0.12), (w * 0.98, wall_top + 10)], fill=(150, 56, 44, 255))
        for k in range(8):
            y = h * 0.16 + k * (wall_top - h * 0.16) / 8
            xl = w * 0.5 - (y - h * 0.12) / (wall_top - h * 0.12) * w * 0.48
            d.line([(xl, y), (w - xl, y)], fill=(120, 40, 32, 255), width=4)
        d.rectangle((w * 0.66, h * 0.08, w * 0.76, h * 0.3), fill=(160, 74, 52, 255), outline=(110, 50, 36, 255), width=4)
        d.rectangle((w * 0.07, wall_top, w * 0.93, h * 0.98), fill=(246, 242, 232, 255))
        for k in range(14):
            y = wall_top + k * (h * 0.98 - wall_top) / 14
            d.line([(w * 0.07, y), (w * 0.93, y)], fill=(214, 208, 196, 255), width=3)
        for x in (w * 0.17, w * 0.68):
            d.rectangle((x, h * 0.55, x + w * 0.15, h * 0.75), fill=(250, 214, 120, 255), outline=(60, 80, 70, 255), width=8)
            d.line([(x + w * 0.075, h * 0.55), (x + w * 0.075, h * 0.75)], fill=(60, 80, 70, 255), width=6)
            d.line([(x, h * 0.65), (x + w * 0.15, h * 0.65)], fill=(60, 80, 70, 255), width=6)
            d.rectangle((x - w * 0.04, h * 0.55, x - w * 0.005, h * 0.75), fill=(46, 84, 64, 255))
            d.rectangle((x + w * 0.155, h * 0.55, x + w * 0.19, h * 0.75), fill=(46, 84, 64, 255))
        d.rectangle((w * 0.44, h * 0.6, w * 0.56, h * 0.98), fill=(150, 50, 40, 255), outline=(90, 30, 24, 255), width=6)
        d.ellipse((w * 0.53, h * 0.79, w * 0.55, h * 0.81), fill=(230, 190, 80, 255))
        # hanging sign
        d.rectangle((w * 0.3, h * 0.44, w * 0.7, h * 0.53), fill=(40, 70, 52, 255), outline=(230, 200, 120, 255), width=6)
        f = font(int(h * 0.05))
        t = 'TOLL HOUSE INN'
        d.text((w * 0.5 - f.getlength(t) / 2, h * 0.452), t, font=f, fill=(250, 230, 160))
        arr = np.asarray(im, np.float32) / 255
        arr[..., :3] *= np.linspace(1.05, 0.85, w)[None, :, None]
        return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    return cached(('house', w), mk)

def wrapper_sprite(w=760, h=980, lines=1.0):
    key = ('wrap', w, h, round(lines, 2))
    if key in _SP:
        return _SP[key]
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h), fill=(246, 236, 214, 255))
    d.rectangle((24, 24, w - 24, h - 24), outline=(160, 40, 30, 255), width=10)
    f = font(78)
    for k, t in enumerate(('COOKIE', 'RECIPE')):
        d.text(((w - f.getlength(t)) / 2, 60 + k * 92), t, font=f, fill=(160, 40, 30))
    n = 9
    shown = lines * n
    for k in range(n):
        q = clamp01(shown - k)
        if q <= 0:
            break
        y = 300 + k * 66
        x1 = 80 + (w - 160 - (k * 53 % 170)) * q
        d.line([(80, y), (x1, y)], fill=(70, 46, 30, 255), width=12)
    arr = np.asarray(im, np.float32) / 255
    arr[..., :3] *= (0.9 + 0.1 * smooth_noise(h, w, 30, 4, 2))[..., None]
    arr[..., :3] *= np.linspace(1.04, 0.88, w)[None, :, None]
    sp = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    _SP[key] = sp
    return sp

def morsel_sprite(R=46, ang=0):
    q = int(round(ang / 20.0)) % 18
    def mk():
        n = int(R * 3)
        lay = Layer(n, n)
        c = n / 2
        ellipsoid(lay, (c, c + R * 0.3), R, R * 0.7, 0, '#4A2816', spec=0.6, shin=36)
        capsule(lay, (c, c + R * 0.1), (c, c - R * 0.9), R * 0.6, R * 0.05, '#4A2816', spec=0.6, shin=36)
        sp, _, _ = layer_sprite(lay, 2)
        return sp.rotate(q * 20, resample=Image.BICUBIC, expand=True)
    return cached(('morsel', R, q), mk)

def bag_sprite(w=760, back=False):
    def mk():
        h = int(w * 1.25)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(w * 0.04, h * 0.06), (w * 0.96, h * 0.06), (w * 0.99, h * 0.98), (w * 0.01, h * 0.98)], fill=(236, 150, 40, 255))
        for k in range(10):
            x = w * 0.05 + k * w * 0.1
            d.line([(x, h * 0.0), (x, h * 0.07)], fill=(200, 120, 30, 255), width=int(w * 0.05))
        d.rectangle((w * 0.04, h * 0.0, w * 0.96, h * 0.07), fill=(214, 128, 30, 255))
        if back:
            d.rounded_rectangle((w * 0.1, h * 0.14, w * 0.9, h * 0.92), radius=26, fill=(250, 244, 228, 255))
            f = font(int(w * 0.085))
            t = 'COOKIE RECIPE'
            d.text(((w - f.getlength(t)) / 2, h * 0.17), t, font=f, fill=(150, 50, 30))
            for k in range(9):
                y = h * 0.3 + k * h * 0.065
                d.line([(w * 0.17, y), (w * 0.83 - (k * 41 % 120), y)], fill=(70, 46, 30, 255), width=12)
        else:
            f = font(int(w * 0.13))
            for k, t in enumerate(('SEMI-SWEET', 'MORSELS')):
                d.text(((w - f.getlength(t)) / 2, h * 0.18 + k * h * 0.13), t, font=f, fill=(110, 40, 20))
        arr = np.asarray(im, np.float32) / 255
        xs = np.linspace(-1, 1, w)
        arr[..., :3] *= (0.8 + 0.28 * np.sqrt(np.clip(1 - xs ** 2, 0, 1)))[None, :, None]
        sp = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
        if not back:
            for j, (x, y) in enumerate(((0.3, 0.7), (0.5, 0.76), (0.7, 0.7), (0.4, 0.84), (0.6, 0.84))):
                paste_center(sp, morsel_sprite(int(w * 0.07), j * 40), w * x, h * y)
        return sp
    return cached(('bag', w, back), mk)

def tray_sprite(w=1000):
    def mk():
        h = int(w * 0.62)
        lay = Layer(w + 30, h + 30)
        fill_poly(lay, [(20, 30), (w + 10, 30), (w + 10, h + 10), (20, h + 10)], '#9AA3AE')
        fill_poly(lay, [(40, 50), (w - 10, 50), (w - 10, h - 10), (40, h - 10)], '#B8C0CA')
        sp, _, _ = layer_sprite(lay, 2)
        return sp
    return cached(('tray', w), mk)

def bulb_sprite(R=110):
    def mk():
        lay = Layer(int(R * 2.6), int(R * 3.4))
        c = R * 1.3
        sphere(lay, (c, R * 1.2), R, '#FFE36A', spec=0.9, shin=40, amb=0.7)
        capsule(lay, (c, R * 2.0), (c, R * 2.6), R * 0.42, R * 0.42, '#9AA3AE', spec=0.7, shin=40)
        sp, _, _ = layer_sprite(lay, 2)
        return sp
    return cached(('bulb', R), mk)

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
        top = vgrad(PW, PH - y0, [(0, col), (1, '#2A1A10')])
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

def check_plate():
    """Red-and-white checked tablecloth."""
    if 'check' not in _PL:
        yy, xx = np.mgrid[0:PH, 0:PW]
        a = ((xx // 150) % 2).astype(np.float32)
        b = ((yy // 150) % 2).astype(np.float32)
        m = (a + b) / 2
        red = np.array([0.80, 0.18, 0.16], np.float32)
        wht = np.array([0.97, 0.94, 0.90], np.float32)
        arr = wht * (1 - m[..., None]) + red * m[..., None]
        arr = arr * (0.92 + 0.08 * smooth_noise(PH, PW, 30, 2, 2))[..., None]
        arr = arr * (0.55 + 0.6 * radial(PW, PH, CX, 1000, 1500, 1.3))[..., None]
        _PL['check'] = plate_img(vignette(np.clip(arr, 0, 1), 0.5))
    return _PL['check'].copy()

def outdoor_plate():
    if 'out' not in _PL:
        arr = vgrad(PW, PH, [(0, '#7EC4F0'), (0.55, '#D6EEFA'), (0.56, '#6FAE4A'), (1, '#2F6A2A')])
        arr = arr * (0.92 + 0.08 * smooth_noise(PH, PW, 60, 5, 3))[..., None]
        img = to_img(arr).convert('RGBA')
        ov = OV(img, 0, 0, PW, PH)
        for (x, y, r) in ((180, 330, 70), (1000, 260, 90)):
            for k in range(4):
                ov.d.ellipse((x - r + k * r * 0.5, y - r * 0.6, x + r * 0.4 + k * r * 0.5, y + r * 0.4), fill=(255, 255, 255, 235))
        for k in range(9):
            x = -60 + k * 170
            ov.d.ellipse((x, 1150, x + 260, 1420), fill=(52, 120, 50, 255))
        ov.commit()
        _PL['out'] = plate_img(vignette(to_arr(img), 0.35))
    return _PL['out'].copy()

# ====================================================================== 0: hook - spinning giant cookie, $1
class Hook(Base):
    z0, z1 = 1.3, 1.34
    CC = (CX, 1000)
    R = 450
    def make_shakes(self):
        return [(0.0, 12, 0.3), (self.we('just') - 0.02, 18, 0.35)]
    def events(self):
        return [(0.0, 'bigpop', 0.8), (0.0, 'rattle', 0.5), (self.we('recipe') - 0.03, 'pop', 0.5),
                (self.we('sold') - 0.03, 'cash', 0.6), (self.we('just') - 0.02, 'boom', 0.7)]
    def plate(self):
        self.cookie = cookie_sprite(self.R, 3)
        self.csh = shadow_of(self.cookie, 22, 0.5)
        self.bill = bill_sprite(2)
        self.st = stamp_sprite('$1', 230, color=(40, 150, 70), angle=-10)
        return check_plate()
    def hero(self, img, t):
        ang = -40 * t - 8
        sp = rot(self.cookie, ang, 'ck0')
        bob = 14 * math.sin(t * 5)
        sh, pad = self.csh
        paste_at(img, sh, self.CC[0] - self.cookie.width / 2 - pad + 30, self.CC[1] + bob * 0.3 - self.cookie.height / 2 - pad + 50)
        paste_center(img, sp, self.CC[0], self.CC[1] + bob)
        # chunks flying off the spinning cookie
        period = 1.4
        n = 16
        for k in range(n):
            age = (t + k * period / n) % period
            a = 2 * math.pi * ((k * 0.618) % 1.0)
            v = 700 + 300 * ((k * 0.37) % 1.0)
            r0 = self.R * 0.9
            x = self.CC[0] + math.cos(a) * (r0 + v * age)
            y = self.CC[1] + math.sin(a) * (r0 + v * age) + 500 * age * age
            if y < 700 and abs(x - CX) < 380:
                continue    # keep the hook banner clear
            ch = rot(chunk_sprite(46, k % 5), 300 * age + k * 40, ('chk', k % 5))
            paste_center(img, ch, x, y)
        # dollar bill fluttering beside it
        bx = self.CC[0] + 360 + 30 * math.sin(t * 3)
        by = self.CC[1] + 250 + 20 * math.sin(t * 4)
        paste_center(img, rot(self.bill, 18 + 14 * math.sin(t * 6), 'bill'), bx, by)
    def dyn(self, img, t):
        self.hero(img, t)
        tR, tD = self.we('recipe'), self.we('$1!')
        pop(img, C('THIS RECIPE', 92, bg=WHITE), CX, 1760, t, tR - 0.06, out_t=self.we('just') - 0.14)
        stamp_in(img, self.st, CX, 1760, t, self.we('just') - 0.02)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, 1150 + dy, dr

# ====================================================================== 1: 1930s, Ruth Wakefield, Toll House Inn
class Inn(Base):
    z0, z1 = 1.2, 1.3
    focus = (CX, 1080)
    def make_shakes(self):
        return [(self.we('1930s,'), 14, 0.3), (self.we('Toll'), 10, 0.25)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1930s,'), 'thud', 0.8), (self.we('Ruth') - 0.03, 'pop', 0.5),
                (self.we('Toll') - 0.03, 'ding', 0.6), (self.we('Massachusetts.') - 0.03, 'pop', 0.5)]
    def plate(self):
        img = outdoor_plate()
        self.house = house_sprite(1240)
        self.st = stamp_sprite('1930s', 150, color=BLUE, angle=-8)
        return img
    def dyn(self, img, t):
        y = 1000 + (1 - ease_out(t / 0.35)) * 120
        paste_center(img, self.house, CX, y)
        stamp_in(img, self.st, CX + 300, 520, t, self.we('1930s,'))
        pop(img, C('RUTH WAKEFIELD', 76, bg=YEL), CX, 1780, t, self.we('Ruth') - 0.06, out_t=self.we('Massachusetts.') - 0.12)
        pop(img, C('MASSACHUSETTS', 70, bg=WHITE), CX, 1780, t, self.we('Massachusetts.') - 0.06)

# ====================================================================== 2: chocolate bar + ice pick
class Chop(Base):
    z0, z1 = 1.2, 1.3
    def make_shakes(self):
        tc = self.we('chopped')
        return [(tc + k * 0.22, 10, 0.15) for k in range(4)] + [(self.we('ice'), 16, 0.3)]
    def stabs(self):
        tc = self.we('chopped')
        return [tc + k * 0.22 for k in range(4)] + [self.we('ice') + k * 0.2 for k in range(2)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('grabbed') - 0.03, 'rustle', 0.6), (self.we('bar') - 0.03, 'pop', 0.5)]
        for s in self.stabs():
            ev.append((s, 'crack', 0.55))
        ev.append((self.we('ice') - 0.03, 'ding', 0.5))
        return ev
    def plate(self):
        self.bar = bar_sprite(860, 470, 4, 2, True, 0.0)
        self.pick = icepick_sprite(700)
        self.hand = get_hand(560, -1.2)
        self.st = stamp_sprite('ICE PICK!', 150, color=RED, angle=-8)
        return table_plate(5)
    def dyn(self, img, t):
        tG, tC = self.we('grabbed'), self.we('chopped')
        st = self.stabs()
        hits = sum(1 for s in st if t >= s)
        by = 980
        if hits == 0:
            lift = ease_out((t - tG) / 0.4) if t > tG else 0
            y = by - 60 * lift
            with_shadow(img, rot(self.bar, -4 + 4 * lift, 'bar0'), CX, y, a=0.5)
            draw_hand(img, self.hand, (CX - 360, y - 60), 0.2)
        else:
            # broken pieces spread a little more with each stab
            spread = min(1.0, hits / 4)
            rng = np.random.default_rng(3)
            for k in range(14):
                a = rng.uniform(0, 6.28)
                r = rng.uniform(40, 360) * spread
                x = CX + math.cos(a) * r * 1.2
                y = by + math.sin(a) * r * 0.6
                ch = rot(chunk_sprite(int(rng.uniform(50, 80)), k % 6), rng.uniform(0, 360), ('bk', k % 6))
                with_shadow(img, ch, x, y, blur=6, a=0.4, dx=8, dy=10)
            if spread < 1:
                with_shadow(img, rot(self.bar, 0, 'bar0'), CX + 120 * spread, by, a=0.45)
        # ice pick bobbing up and down onto each stab
        if t > tC - 0.3:
            last = max([s for s in st if s <= t], default=tC)
            u = (t - last) / 0.22
            lift = 0 if t < tC else min(1, abs(math.sin(math.pi * min(u, 1))))
            px = CX - 80 + 50 * (hits % 3)
            py = by - 420 - 160 * lift
            paste_center(img, rot(self.pick, 8, 'pick'), px, py)
        pop(img, C('CHOCOLATE BAR', 72, bg=WHITE), CX, 1760, t, self.we('chocolate') - 0.06, out_t=self.we('ice') - 0.12)
        stamp_in(img, self.st, CX, 1760, t, self.we('ice'))
    def cam(self, t):
        z, fx, fy, rot_ = super().cam(t)
        return z, fx, fy - 60, rot_

# ====================================================================== 3: chunks into dough -> cookie born
class Dough(Base):
    z0, z1 = 1.18, 1.28
    def tcut(self):
        return self.we('chocolate') - 0.15
    def make_shakes(self):
        return [(self.tcut(), 16, 0.35)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('pea-sized') - 0.03, 'pop', 0.5)]
        for k in range(4):
            ev.append((self.we('chunks') + k * 0.25, 'tick', 0.5))
        ev += [(self.we('dough,') - 0.03, 'splat', 0.5), (self.tcut(), 'bigpop', 0.7), (self.we('born.') - 0.35, 'chime', 0.6)]
        return ev
    def plate(self):
        self.bowl = bowl_sprite(920)
        self.cookie = cookie_sprite(380, 8)
        self.pea = C('PEA-SIZED CHUNKS', 70, bg=WHITE)
        self.cc = C('CHOCOLATE CHIP COOKIE', 64, bg=YEL)
        return table_plate(7)
    def dyn(self, img, t):
        tc = self.tcut()
        if t < tc:
            with_shadow(img, self.bowl, CX, 1100, a=0.45)
            for k in range(12):
                t0 = 0.25 + k * 0.28
                u = (t - t0) / 0.55
                if u < 0 or t0 > tc:
                    continue
                x = CX - 260 + (k * 97 % 520)
                if u < 1:
                    y = 560 + (960 - 560) * u * u
                else:
                    y = 960 + 20 * ((k * 37) % 5)
                    x = x + 6 * math.sin(t * 5 + k)
                paste_center(img, rot(chunk_sprite(36, k % 6), k * 50 + 200 * min(u, 1), ('dc', k % 6)), x, y)
            # spoon stirring
            ang = t * 5
            sx, sy = CX + 160 * math.cos(ang), 960 + 30 * math.sin(ang)
            ov = OV(img, CX - 400, 400, CX + 400, 1100)
            ov.d.line(ov.pts([(sx, sy), (sx + 140, 520)]), fill=(150, 100, 60, 255), width=34)
            ov.d.ellipse(ov.box(sx - 50, sy - 26, sx + 50, sy + 26), fill=(160, 110, 66, 255))
            ov.commit()
            pop(img, self.pea, CX, 1760, t, self.we('pea-sized') - 0.08)
            return
        u = t - tc
        glow(img, CX, 1040, 520, (255, 230, 170), 0.5)
        s = 0.5 + 0.5 * ease_back(u / 0.4, 1.8)
        paste_center(img, rot(self.cookie, -10 * u, 'ck3'), CX, 1040, scale=min(1.0, s))
        pop(img, self.cc, CX, 1760, t, tc + 0.1)
        pop(img, C('BORN!', 96, bg=(110, 220, 130)), CX, 560, t, self.we('born.') - 0.1)

# ====================================================================== 4: so popular -> deal
class Popular(Base):
    z0, z1 = 1.2, 1.3
    def make_shakes(self):
        return [(self.we('a'), 16, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5)]
        for k in range(6):
            ev.append((0.15 + k * 0.22, 'pop', 0.45))
        ev += [(self.we('popular') - 0.03, 'party', 0.5), (self.we('a') - 0.03, 'thud', 0.8)]
        return ev
    def plate(self):
        self.tray = tray_sprite(1040)
        self.cks = [cookie_sprite(170, s) for s in (11, 12, 13)]
        self.hl = get_hand(520, 0.0)
        self.hr = get_hand(520, math.pi)
        self.st = stamp_sprite('DEAL!', 170, color=RED, angle=-8)
        return check_plate()
    def dyn(self, img, t):
        tD = self.we('a')
        with_shadow(img, self.tray, CX, 1060, a=0.4)
        pos = [(CX - 330, 900), (CX, 900), (CX + 330, 900), (CX - 330, 1200), (CX, 1200), (CX + 330, 1200)]
        for k, (x, y) in enumerate(pos):
            if t > tD - 0.4:
                continue
            pop(img, self.cks[k % 3], x, y + 6 * math.sin(t * 6 + k), t, 0.12 + k * 0.22)
        pop(img, C('SO POPULAR!', 80, bg=YEL), CX, 560, t, self.we('popular') - 0.08, out_t=tD - 0.2)
        if t > tD - 0.4:
            u = ease_out((t - tD + 0.4) / 0.4)
            draw_hand(img, self.hl, (CX - 500 + 470 * u, 1050), 0.2)
            draw_hand(img, self.hr, (CX + 500 - 470 * u, 1070), 0.2)
            for k, c in enumerate(self.cks):
                paste_center(img, c, CX - 280 + 280 * k, 1330)
        stamp_in(img, self.st, CX, 1780, t, tD)

# ====================================================================== 5: recipe printed on the wrappers
class Wrapper(Base):
    z0, z1 = 1.2, 1.3
    def make_shakes(self):
        return [(self.we('print'), 12, 0.28), (self.we('wrappers.') - 0.1, 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('print') - 0.03, 'thud', 0.6)]
        for k in range(6):
            ev.append((self.we('recipe') + k * 0.16, 'tick', 0.45))
        ev.append((self.we('chocolate') - 0.03, 'ding', 0.6))
        return ev
    def plate(self):
        self.bar = bar_sprite(560, 300, 3, 2, False, 1.0)
        return table_plate(9)
    def dyn(self, img, t):
        tP, tR = self.we('print'), self.we('recipe')
        q = clamp01((t - tR) / 1.2) if t > tR else 0
        y = 1060 + (1 - ease_out(t / 0.35)) * 260
        paste_center(img, self.bar, CX + 300, 1330)
        with_shadow(img, rot(wrapper_sprite(700, 900, q), 4, None), CX - 30, y, a=0.45)
        # stamp press coming down on "print"
        if tP - 0.2 < t < tP + 0.5:
            u = (t - tP + 0.2) / 0.7
            py = 300 + 300 * math.sin(math.pi * u)
            ov = OV(img, CX - 260, 100, CX + 260, 800)
            ov.d.rectangle(ov.box(CX - 220, py - 120, CX + 220, py), fill=(70, 70, 80, 255))
            ov.d.rectangle(ov.box(CX - 40, 100, CX + 40, py - 120), fill=(110, 110, 120, 255))
            ov.commit()
        pop(img, C('ON THE WRAPPER!', 76, bg=YEL), CX, 1790, t, self.we('chocolate') - 0.06)

# ====================================================================== 6: payment $1 + free chocolate for life
class Payment(Base):
    z0, z1 = 1.2, 1.3
    def make_shakes(self):
        return [(self.we('dollar...'), 14, 0.3), (self.we('life!'), 18, 0.35)]
    def events(self):
        ev = [(0.02, 'riser', 0.4), (self.we('payment?') - 0.03, 'pop', 0.5), (self.we('one') - 0.03, 'cash', 0.7),
              (self.we('free') - 0.03, 'bigpop', 0.6)]
        for k in range(5):
            ev.append((self.we('chocolate') + k * 0.2, 'thud', 0.35))
        return ev
    def plate(self):
        self.bill = bill_sprite(5)
        self.bar = bar_sprite(420, 230, 3, 2, True, 1.0)
        self.st = stamp_sprite('FOR LIFE!', 150, color=RED, angle=-8)
        self.ck = cookie_sprite(360, 15)
        self.q = text_img('?', 300, fill=(255, 255, 255), stroke=14, stroke_fill=(20, 20, 30), shadow_px=5)
        return wall_plate('#C9F0C9', '#3A8A50', 4, (CX, 1000, 1300))
    def dyn(self, img, t):
        tO, tF, tL = self.we('one'), self.we('free'), self.we('life!')
        if t < tO + 0.1:
            with_shadow(img, rot(self.ck, 6 * math.sin(t * 3), 'ck6'), CX - 120, 1060, a=0.4)
            paste_center(img, self.q, CX + 300, 860 + 14 * math.sin(t * 6), scale=1 + 0.06 * math.sin(t * 9))
        pop(img, C('HER PAYMENT?', 80, bg=WHITE), CX, 560, t, 0.05, out_t=tF - 0.15)
        if t > tF - 0.05:
            # bars raining down for life
            for k in range(14):
                t0 = tF + k * 0.12
                u = t - t0
                if u < 0:
                    continue
                x = CX - 420 + (k * 211 % 840)
                y = 300 + 1400 * u
                if y > 1700:
                    y = 1580 + 40 * ((k * 3) % 4)
                paste_center(img, rot(self.bar, (k * 47) % 60 - 30, ('rb', k % 6)), x, y)
        if t > tO - 0.1:
            k = ease_back((t - tO + 0.1) / 0.35, 2.0)
            sp = rot(self.bill, -8 + 4 * math.sin(t * 4), 'pbill')
            paste_center(img, sp, CX, 1000, scale=max(0.05, 1.9 * k))
        pop(img, C('REPORTEDLY', 72, bg=YEL), CX, 1780, t, self.we('reportedly') - 0.05, out_t=tF - 0.15)
        stamp_in(img, self.st, CX, 1790, t, tL - 0.05)

# ====================================================================== 7: pre-scored bars, then morsels
class Morsels(Base):
    z0, z1 = 1.2, 1.3
    def tcut(self):
        return self.we('then') - 0.05
    def make_shakes(self):
        return [(self.tcut(), 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('selling') - 0.03, 'cash', 0.5)]
        for k in range(4):
            ev.append((self.we('pre-scored') + k * 0.15, 'scratch', 0.45))
        ev += [(self.tcut(), 'swipe', 0.5), (self.we('tiny') - 0.03, 'rattle', 0.7), (self.we('chocolate') + 0.1, 'rattle', 0.6)]
        return ev
    def plate(self):
        self.bag = bag_sprite(640)
        return table_plate(4)
    def dyn(self, img, t):
        tc, tS = self.tcut(), self.we('pre-scored')
        if t < tc:
            q = clamp01((t - tS + 0.05) / 0.7) if t > tS - 0.05 else 0
            bar = bar_sprite(900, 560, 4, 3, True, q)
            with_shadow(img, bar, CX, 1050 + 6 * math.sin(t * 4), a=0.45)
            pop(img, C('PRE-SCORED BARS', 72, bg=YEL), CX, 1780, t, tS - 0.06)
            return
        u = t - tc
        with_shadow(img, self.bag, CX - 200, 1000, a=0.45)
        rng = np.random.default_rng(9)
        for k in range(40):
            t0 = 0.1 + k * 0.035
            v = u - t0
            if v < 0:
                continue
            x0 = CX + 60 + rng.uniform(-60, 60)
            x = x0 + 260 * min(v, 0.8) + rng.uniform(0, 200) * min(v, 0.8)
            y = 820 + 1400 * v * v
            fy = 1260 + rng.uniform(-60, 60)
            if y > fy:
                y = fy
            paste_center(img, morsel_sprite(40, int(rng.uniform(0, 360))), x, y)
        pop(img, C('CHOCOLATE MORSELS', 70, bg=WHITE), CX, 1780, t, self.we('tiny') - 0.06)

# ====================================================================== 8: recipe still on the bag today
class Today(Base):
    z0, z1 = 1.2, 1.32
    def make_shakes(self):
        return [(self.we('bag') + 0.1, 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('still') - 0.03, 'pop', 0.5), (self.we('bag') - 0.03, 'rustle', 0.6),
                (self.we('bag') + 0.1, 'ding', 0.7)]
    def plate(self):
        self.front = bag_sprite(760)
        self.back = bag_sprite(760, True)
        self.st = stamp_sprite('STILL TODAY', 130, color=RED, angle=-8)
        return check_plate()
    def dyn(self, img, t):
        tf = self.we('printed') - 0.1
        y = 1030 + 8 * math.sin(t * 4)
        if t < tf:
            sp = self.front
            sx = 1.0
        else:
            u = clamp01((t - tf) / 0.35)
            sp = self.front if u < 0.5 else self.back
            sx = abs(1 - 2 * u)
        if sx > 0.03:
            s2 = sp.resize((max(1, int(sp.width * sx)), sp.height), Image.BICUBIC)
            with_shadow(img, s2, CX, y, a=0.45)
        pop(img, C('THE SAME RECIPE', 72, bg=YEL), CX, 1700, t, self.we('recipe') - 0.06, out_t=self.we('bag'))
        stamp_in(img, self.st, CX, 1760, t, self.we('bag') + 0.1)

# ====================================================================== 9: twist - accident? she knew
class Twist(Base):
    z0, z1 = 1.2, 1.3
    def make_shakes(self):
        return [(self.we('accident,'), 14, 0.3), (self.we('knew'), 18, 0.35)]
    def events(self):
        return [(0.02, 'riser', 0.5), (self.we('twist?') - 0.03, 'crack', 0.7), (self.we('lucky') - 0.03, 'pop', 0.5),
                (self.we('accident,') + 0.3, 'buzzer', 0.7), (self.we('historians') - 0.03, 'pop', 0.5),
                (self.we('knew') - 0.03, 'ding', 0.7), (self.we('exactly') - 0.03, 'bigpop', 0.6)]
    def plate(self):
        img = wall_plate('#4A2A6A', '#150A22', 21, (CX, 1000, 1300))
        lay = Layer()
        mannequin(lay, CX, 1980, 1200)
        self.wall_m = to_img(finish(to_arr(img), lay, (16, 24, 16, 0.4))).convert('RGBA')
        self.cookie = cookie_sprite(330, 21)
        self.bulb = bulb_sprite(120)
        self.acc = stamp_sprite('LUCKY ACCIDENT?', 104, color=(240, 200, 60), angle=-7)
        self.knew = stamp_sprite('SHE KNEW!', 150, color=(90, 220, 120), angle=-7)
        return img
    def dyn(self, img, t):
        tA, tH, tK = self.we('lucky'), self.we('historians'), self.we('knew')
        if t < tH - 0.1:
            paste_center(img, rot(self.cookie, 10 * math.sin(t * 2), 'ck9'), CX, 1020 + 8 * math.sin(t * 5))
            pop(img, C('THE TWIST?', 84, bg=YEL), CX, 560, t, 0.02, out_t=tA - 0.15)
            stamp_in(img, self.acc, CX, 560, t, tA - 0.05)
            if t > self.we('accident,') + 0.3:
                red_x(img, CX, 560, 170, clamp01((t - self.we('accident,') - 0.3) / 0.3))
            return
        img.paste(self.wall_m, (0, 0))
        pop(img, C('HISTORIANS SAY...', 76, bg=WHITE), CX, 560, t, tH - 0.06, out_t=tK - 0.1)
        if t > tK - 0.1:
            glow(img, CX, 680, 300, (255, 240, 150), 0.6)
            pop(img, self.bulb, CX, 640, t, tK - 0.1)
        paste_center(img, self.cookie, CX + 330, 1250, scale=0.55)
        stamp_in(img, self.knew, CX, 1780, t, self.we('exactly') - 0.05)

# ====================================================================== 10: bite into a cookie -> loops to hook
class Outro(Hook):
    def tswitch(self):
        return self.we('remember...') + 0.5
    def make_shakes(self):
        return [(self.we('bite'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('bite') - 0.03, 'crack', 0.8), (self.we('cookie,') - 0.03, 'pop', 0.5),
                (self.tswitch(), 'riser', 0.5)]
    def plate(self):
        img = Hook.plate(self)
        self.hook_plate = img.copy()
        return table_plate(3)
    def dyn(self, img, t):
        tw = self.tswitch()
        if t >= tw:
            img.paste(self.hook_plate, (0, 0))
            self.hero(img, t - self.dur)   # ends exactly where frame 0 begins
            return
        tB = self.we('bite')
        b = clamp01((t - tB) / 0.15) if t > tB else 0
        sp = cookie_sprite(400, 3, bite=round(b * 4) / 4)
        with_shadow(img, sp, CX, 1030 + 6 * math.sin(t * 4), a=0.45)
        if t > tB:
            rng = np.random.default_rng(2)
            for k in range(10):
                u = t - tB
                x = CX + 250 + rng.uniform(-80, 140) + 200 * u * rng.uniform(-1, 1)
                y = 720 + rng.uniform(-40, 60) + 900 * u * u
                if y < 1500:
                    paste_center(img, chunk_sprite(int(rng.uniform(10, 22)), k % 4, (190, 130, 70)), x, y)
        pop(img, C('NEXT TIME YOU TAKE A BITE...', 58, bg=WHITE), CX, 1780, t, 0.05)
    def cam(self, t):
        tw = self.tswitch()
        if t >= tw:
            return self.z0, CX, 1150, 0.0
        dx, dy, dr = self.shake(t)
        p = 1 - ease_out(t / 0.32)
        return 1.2 + 0.06 * clamp01(t / tw) + 0.1 * p, CX + dx, 1100 + dy, 2.0 * p + dr

SCENES = [Hook, Inn, Chop, Dough, Popular, Wrapper, Payment, Morsels, Today, Twist, Outro]
