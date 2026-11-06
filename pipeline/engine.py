"""Small 2.5D software renderer: shaded capsules/ellipsoids, textured quads, soft shadows."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter

W, H = 1080, 1920
S = 1.2
PW, PH = int(W * S), int(H * S)  # plate size 1296 x 2304

FONT_BLACK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
FONT_BOLD = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
FONT_SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
_fcache = {}

def font(size, path=FONT_BLACK):
    k = (path, size)
    if k not in _fcache:
        _fcache[k] = ImageFont.truetype(path, size)
    return _fcache[k]

LIGHT = np.array([-0.42, -0.58, 0.70])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1.0])
HALF = HALF / np.linalg.norm(HALF)

def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

# ---------------- easing ----------------
def clamp01(x):
    return max(0.0, min(1.0, x))

def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    t = clamp01(t)
    return 3 * t * t - 2 * t * t * t

def ease_back(t, s=1.7):
    t = clamp01(t)
    t -= 1
    return t * t * ((s + 1) * t + s) + 1

# ---------------- backgrounds ----------------
def vgrad(w, h, stops):
    """stops: list of (pos 0..1, hexcolor)"""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3), np.float32)
    ps = [p for p, _ in stops]
    cs = np.array([hexc(c) for _, c in stops])
    for k in range(3):
        out[:, k] = np.interp(ys, ps, cs[:, k])
    return np.repeat(out[:, None, :], w, axis=1)

def radial(w, h, cx, cy, r, power=2.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** power

def vignette(img, strength=0.55, power=2.2):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h / 2) / (h * 0.62)) ** 2)
    v = 1 - strength * np.clip(d, 0, 1.4) ** power
    return img * np.clip(v, 0, 1)[..., None]

def smooth_noise(h, w, cell, seed=0, octaves=3):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        gh, gw = h // c + 3, w // c + 3
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * c, gh * c), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32)[:h, :w] / 255)
        tot += amp
        amp *= 0.5
    return out / tot

def wood(w, h, base, dark, seed=1, stretch=14, rings=22, contrast=0.5):
    """Grain runs along x."""
    n = smooth_noise(h, max(8, w // stretch) + 4, 18, seed, 3)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    g = np.sin((yy / h * rings + n * 6.0) * np.pi) * 0.5 + 0.5
    g = g ** 3
    fine = smooth_noise(h, w, 3, seed + 5, 1)
    t = np.clip(g * contrast + (fine - 0.5) * 0.25 + (n - 0.5) * 0.3, 0, 1)
    b, d = hexc(base), hexc(dark)
    return b[None, None, :] * (1 - t[..., None]) + d[None, None, :] * t[..., None]

def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))

def to_arr(img):
    return np.asarray(img.convert('RGB'), np.float32) / 255

# ---------------- layer ----------------
class Layer:
    """Premultiplied RGBA float layer the size of the plate."""
    def __init__(self, w=PW, h=PH):
        self.w, self.h = w, h
        self.p = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)

    def put(self, rgb, a, x0, y0):
        h, w = a.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + w), min(self.h, y0 + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        rgb = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        a = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        P = self.p[Y0:Y1, X0:X1]
        A = self.a[Y0:Y1, X0:X1]
        self.p[Y0:Y1, X0:X1] = rgb * a[..., None] + P * (1 - a[..., None])
        self.a[Y0:Y1, X0:X1] = a + A * (1 - a)

    def put_pil(self, im, x0, y0):
        arr = np.asarray(im.convert('RGBA'), np.float32) / 255
        self.put(arr[..., :3], arr[..., 3], x0, y0)

    def comp(self, bg):
        return self.p + bg * (1 - self.a[..., None])

def shadow(bg, alpha, dx, dy, blur, k=0.55, color=(0, 0, 0)):
    s = gaussian_filter(alpha, blur)
    s = np.roll(np.roll(s, int(dy), 0), int(dx), 1)
    c = np.array(color, np.float32)
    return bg * (1 - k * s[..., None]) + c * (k * s[..., None])

# ---------------- shaded primitives ----------------
def _bbox(xs, ys, pad, w, h):
    x0 = int(max(0, np.floor(min(xs) - pad)))
    x1 = int(min(w, np.ceil(max(xs) + pad)))
    y0 = int(max(0, np.floor(min(ys) - pad)))
    y1 = int(min(h, np.ceil(max(ys) + pad)))
    return x0, y0, x1, y1

def _shade(nx, ny, nz, base, amb=0.38, dif=0.78, spec=0.35, shin=28, rim=0.0):
    ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
    col = base[None, None, :] * (amb + dif * ndl)[..., None]
    col = col + (spec * ndh ** shin)[..., None]
    if rim:
        col = col + (rim * (1 - nz) ** 3)[..., None]
    return col

def capsule(layer, p0, p1, r0, r1, color, spec=0.3, shin=24, amb=0.38, grain=None):
    color = hexc(color) if isinstance(color, str) else np.asarray(color, np.float32)
    p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
    rm = max(r0, r1)
    x0, y0, x1, y1 = _bbox([p0[0], p1[0]], [p0[1], p1[1]], rm + 2, layer.w, layer.h)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    v = p1 - p0
    L2 = float(v @ v) + 1e-6
    t = np.clip(((xx - p0[0]) * v[0] + (yy - p0[1]) * v[1]) / L2, 0, 1)
    cx = p0[0] + t * v[0]; cy = p0[1] + t * v[1]
    r = r0 + (r1 - r0) * t
    dx = xx - cx; dy = yy - cy
    d = np.sqrt(dx * dx + dy * dy)
    a = np.clip(r - d + 0.5, 0, 1)
    q = np.clip(d / np.maximum(r, 1e-3), 0, 0.999)
    nz = np.sqrt(1 - q * q)
    inv = 1 / np.maximum(d, 1e-3)
    nx = dx * inv * q; ny = dy * inv * q
    col = _shade(nx, ny, nz, color, amb=amb, spec=spec, shin=shin)
    if grain is not None:
        col = col * grain[y0:y1, x0:x1, None]
    layer.put(col, a, x0, y0)

def ellipsoid(layer, c, rx, ry, ang, color, spec=0.3, shin=24, amb=0.38, grain=None, crease=0.0):
    color = hexc(color) if isinstance(color, str) else np.asarray(color, np.float32)
    R = max(rx, ry)
    x0, y0, x1, y1 = _bbox([c[0]], [c[1]], R + 2, layer.w, layer.h)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    ca, sa = np.cos(ang), np.sin(ang)
    lx = (xx - c[0]) * ca + (yy - c[1]) * sa
    ly = -(xx - c[0]) * sa + (yy - c[1]) * ca
    u = lx / rx; w_ = ly / ry
    rho = np.sqrt(u * u + w_ * w_)
    edge = (1 - rho) * min(rx, ry)
    a = np.clip(edge + 0.5, 0, 1)
    z = np.sqrt(np.clip(1 - rho * rho, 0, 1))
    rz = min(rx, ry)
    nlx, nly, nz = u / rx, w_ / ry, z / rz
    nn = np.sqrt(nlx ** 2 + nly ** 2 + nz ** 2) + 1e-6
    nlx, nly, nz = nlx / nn, nly / nn, nz / nn
    nx = nlx * ca - nly * sa
    ny = nlx * sa + nly * ca
    col = _shade(nx, ny, nz, color, amb=amb, spec=spec, shin=shin)
    if crease:
        col = col * (1 - crease * np.exp(-(w_ / 0.08) ** 2) * (np.abs(u) < 0.92))[..., None]
    if grain is not None:
        col = col * grain[y0:y1, x0:x1, None]
    layer.put(col, a, x0, y0)

def sphere(layer, c, r, color, **kw):
    ellipsoid(layer, c, r, r, 0.0, color, **kw)

def spindle(layer, p0, p1, R, color, spec=0.35, shin=30, amb=0.4, crease=0.35):
    """Grain-like shape thick in the middle, pointed at both ends."""
    color = hexc(color) if isinstance(color, str) else np.asarray(color, np.float32)
    p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
    x0, y0, x1, y1 = _bbox([p0[0], p1[0]], [p0[1], p1[1]], R + 2, layer.w, layer.h)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    v = p1 - p0
    L2 = float(v @ v)
    tr = ((xx - p0[0]) * v[0] + (yy - p0[1]) * v[1]) / L2
    t = np.clip(tr, 0, 1)
    cx = p0[0] + t * v[0]; cy = p0[1] + t * v[1]
    r = R * np.clip(np.sin(np.pi * t), 0, 1) ** 0.62 + 1.0
    dx = xx - cx; dy = yy - cy
    d = np.sqrt(dx * dx + dy * dy)
    a = np.clip(r - d + 0.5, 0, 1) * ((tr >= -0.002) & (tr <= 1.002))
    q = np.clip(d / r, 0, 0.999)
    nz = np.sqrt(1 - q * q)
    inv = 1 / np.maximum(d, 1e-3)
    nx = dx * inv * q; ny = dy * inv * q
    # axial tilt
    Lv = np.sqrt(L2)
    ax, ay = v / Lv
    slope = np.cos(np.pi * t) * 0.9
    nx = nx - ax * slope * (1 - q) * 0.6
    ny = ny - ay * slope * (1 - q) * 0.6
    nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    col = _shade(nx / nn, ny / nn, nz / nn, color, amb=amb, spec=spec, shin=shin)
    # crease along the axis (a groove on one side)
    perp = (dx * -ay + dy * ax) / np.maximum(r, 1)
    col = col * (1 - crease * np.exp(-((perp + 0.15) / 0.09) ** 2) * (t > 0.08) * (t < 0.92))[..., None]
    layer.put(col, a, x0, y0)

# ---------------- polygons / quads ----------------
def poly_alpha(pts, ss=4):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = int(np.floor(min(xs))) - 2, int(np.floor(min(ys))) - 2
    x1, y1 = int(np.ceil(max(xs))) + 2, int(np.ceil(max(ys))) + 2
    w, h = x1 - x0, y1 - y0
    im = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in pts], fill=255)
    im = im.resize((w, h), Image.BOX)
    return np.asarray(im, np.float32) / 255, x0, y0

def fill_poly(layer, pts, color, alpha=1.0):
    a, x0, y0 = poly_alpha(pts)
    col = hexc(color) if isinstance(color, str) else np.asarray(color, np.float32)
    rgb = np.broadcast_to(col, a.shape + (3,)).astype(np.float32)
    layer.put(rgb, a * alpha, x0, y0)

def _persp_coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def quad(layer, tex, corners, ss=2):
    """Map texture (PIL RGB/RGBA) onto quad corners [tl, tr, br, bl] (plate coords)."""
    tex = tex.convert('RGBA')
    tw, th = tex.size
    pad = Image.new('RGBA', (tw + 4, th + 4), (0, 0, 0, 0))
    pad.paste(tex, (2, 2))
    xs = [c[0] for c in corners]; ys = [c[1] for c in corners]
    x0, y0 = int(np.floor(min(xs))) - 2, int(np.floor(min(ys))) - 2
    x1, y1 = int(np.ceil(max(xs))) + 2, int(np.ceil(max(ys))) + 2
    w, h = x1 - x0, y1 - y0
    dst = [((x - x0) * ss, (y - y0) * ss) for x, y in corners]
    src = [(2, 2), (tw + 2, 2), (tw + 2, th + 2), (2, th + 2)]
    co = _persp_coeffs(dst, src)
    out = pad.transform((w * ss, h * ss), Image.PERSPECTIVE, co, Image.BICUBIC)
    if ss != 1:
        out = out.resize((w, h), Image.LANCZOS)
    arr = np.asarray(out, np.float32) / 255
    a = arr[..., 3]
    rgb = np.where(a[..., None] > 1e-4, arr[..., :3], 0)
    layer.put(rgb, a, x0, y0)

def slab(layer, tex, top, thickness, side_color, side_dark=0.55):
    """A flat bar: textured top quad [tl,tr,br,bl] plus the front (near) face below it."""
    tl, tr, br, bl = top
    fb = [bl, br, (br[0], br[1] + thickness), (bl[0], bl[1] + thickness)]
    a, x0, y0 = poly_alpha(fb)
    col = hexc(side_color) if isinstance(side_color, str) else np.asarray(side_color, np.float32)
    hh, ww = a.shape
    gy = np.linspace(1.0, side_dark, hh)[:, None, None]
    rgb = np.broadcast_to(col, (hh, ww, 3)) * gy
    layer.put(rgb.astype(np.float32), a, x0, y0)
    # right end face if visible
    rf = [tr, br, (br[0], br[1] + thickness), (tr[0], tr[1] + thickness)]
    if tr[0] < br[0] + 400:
        a2, x2, y2 = poly_alpha(rf)
        layer.put(np.broadcast_to(col * 0.7, a2.shape + (3,)).astype(np.float32), a2 * 0.0, x2, y2)
    quad(layer, tex, top)
    # top-edge specular line
    cap = [tl, tr, (tr[0], tr[1] + 3), (tl[0], tl[1] + 3)]
    a3, x3, y3 = poly_alpha(cap)
    layer.put(np.ones(a3.shape + (3,), np.float32), a3 * 0.25, x3, y3)

def rot_pts(pts, c, ang):
    ca, sa = np.cos(ang), np.sin(ang)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]

def bar_corners(cx, cy, length, width, ang, persp=0.0):
    """Corners [tl,tr,br,bl] of a bar centred at (cx,cy), rotated by ang; persp narrows the right end."""
    hl, hw = length / 2, width / 2
    wr = hw * (1 - persp)
    pts = [(cx - hl, cy - hw), (cx + hl, cy - wr), (cx + hl, cy + wr), (cx - hl, cy + hw)]
    return rot_pts(pts, (cx, cy), ang)

# ---------------- text ----------------
def text_img(txt, size, fill=(255, 255, 255), stroke=0, stroke_fill=(0, 0, 0), path=FONT_BLACK, shadow_px=0):
    f = font(size, path)
    bb = f.getbbox(txt, stroke_width=stroke)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    pad = stroke + shadow_px * 3 + 4
    im = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow_px:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - bb[0], pad - bb[1] + shadow_px), txt, font=f, fill=(0, 0, 0, 170),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(shadow_px))
        im.alpha_composite(sh)
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def chip(txt, size=46, bg=(255, 255, 255), fg=(20, 20, 24), dot=None, padx=34, pady=18):
    f = font(size, FONT_BLACK)
    bb = f.getbbox(txt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    extra = int(size * 0.75) if dot else 0
    w, h = tw + padx * 2 + extra, th + pady * 2
    m = 30
    im = Image.new('RGBA', (w + m * 2, h + m * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + w, m + h + 8), radius=h // 2, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m, m, m + w, m + h), radius=h // 2, fill=bg + (255,))
    x = m + padx
    if dot:
        r = size * 0.22
        cy = m + h / 2
        d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=dot)
        x += extra
    d.text((x - bb[0], m + pady - bb[1]), txt, font=f, fill=fg)
    return im

def paste_center(base, sprite, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    sp = sprite
    if abs(scale - 1) > 1e-3:
        sp = sprite.resize((max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = sp.getchannel('A').point(lambda v: int(v * alpha))
        sp = sp.copy(); sp.putalpha(a)
    paste_at(base, sp, int(round(cx - sp.width / 2)), int(round(cy - sp.height / 2)))

def paste_at(base, sp, x, y):
    """alpha_composite that tolerates sprites hanging off the edges."""
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.width, x + sp.width), min(base.height, y + sp.height)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (x, y, x + sp.width, y + sp.height):
        sp = sp.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    if base.mode == 'RGBA':
        base.alpha_composite(sp, (x0, y0))
    else:
        base.paste(sp, (x0, y0), sp)

def pop(base, sprite, cx, cy, t, t0, dur=0.32, out_t=None):
    """Pop a sprite in with an overshoot at time t0 (seconds); optional fade out at out_t."""
    if t < t0:
        return
    k = (t - t0) / dur
    s = ease_back(k, 2.2) if k < 1 else 1.0
    a = clamp01(k * 2.5)
    if out_t is not None and t > out_t:
        a *= clamp01(1 - (t - out_t) / 0.2)
    paste_center(base, sprite, cx, cy, scale=max(0.02, s), alpha=a)

def layer_sprite(layer, pad=4):
    """Crop a Layer to its content and return (PIL RGBA, x0, y0)."""
    ys, xs = np.where(layer.a > 0.003)
    y0, y1 = max(0, ys.min() - pad), min(layer.h, ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(layer.w, xs.max() + pad)
    a = layer.a[y0:y1, x0:x1]
    rgb = np.where(a[..., None] > 1e-4, layer.p[y0:y1, x0:x1] / np.maximum(a[..., None], 1e-4), 0)
    arr = np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1)
    return Image.fromarray((arr * 255 + 0.5).astype(np.uint8), 'RGBA'), x0, y0
