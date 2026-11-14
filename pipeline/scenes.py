"""The Slinky was invented for Navy ships, not kids (2026-11-14)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
from base_scenes import ARM_LIGHT, CX, CY, plate_img
from mw_scenes import glow, stamp_sprite, draw_waves
from bw_scenes import S, C, OV, stamp_in, get_hand, draw_hand, shadow_of
from cart_scenes import ground_shadow

GOLD = (240, 160, 60)
RED = (214, 50, 44)
YEL = (255, 210, 60)
BLUE = (40, 120, 200)
GREEN = (60, 160, 90)

class Base(S):
    focus = (CX, CY)
    z0, z1 = 1.0, 1.06

# ====================================================================== the coil
_RING = {}
RK = 0.30  # ellipse squash of a ring seen almost edge-on

def ring_sprite(R, rot):
    """One metal coil ring; rot = visual clockwise rotation in degrees (0 = horizontal ring)."""
    rq = int(round(rot / 4.0)) * 4 % 360
    key = (int(R), rq)
    if key in _RING:
        return _RING[key]
    ss = 3
    wd = max(5, R * 0.10)
    w, h = 2 * R + 2 * wd + 8, 2 * R * RK + 2 * wd + 8
    im = Image.new('RGBA', (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bx = (4 * ss + wd * ss / 2, 4 * ss + wd * ss / 2, (w - 4) * ss - wd * ss / 2, (h - 4) * ss - wd * ss / 2)
    d.arc(bx, 180, 360, fill=(70, 74, 84, 255), width=int(wd * ss * 1.05))
    d.arc(bx, 180, 360, fill=(128, 133, 145, 255), width=int(wd * ss * 0.55))
    d.arc(bx, 0, 180, fill=(52, 55, 64, 255), width=int(wd * ss * 1.15))
    d.arc(bx, 0, 180, fill=(196, 201, 212, 255), width=int(wd * ss * 0.8))
    inner = (bx[0] + wd * ss * 0.1, bx[1] + wd * ss * 0.12, bx[2] - wd * ss * 0.1, bx[3] - wd * ss * 0.12)
    d.arc(inner, 25, 150, fill=(255, 255, 255, 255), width=max(2, int(wd * ss * 0.22)))
    im = im.resize((int(w), int(h)), Image.LANCZOS)
    if rq:
        im = im.rotate(-rq, expand=True, resample=Image.BICUBIC)
    _RING[key] = im
    return im

def draw_rings(img, rings, R):
    for (x, y, rot) in rings:
        sp = ring_sprite(R, rot)
        paste_at(img, sp, x - sp.width / 2, y - sp.height / 2)

def stack_rings(P, n, R, pc):
    """Compressed coil standing on point P (floor contact)."""
    base = P[1] - R * RK - 2
    return [(P[0], base - j * pc, 0.0) for j in range(int(n))]

def arc_pt(A, B, h, th):
    s = (1 - math.cos(th)) / 2
    return (A[0] + (B[0] - A[0]) * s, A[1] + (B[1] - A[1]) * s - h * math.sin(th))

def arc_rings(A, B, h, th0, th1, n, R):
    out = []
    if n <= 0:
        return out
    off = R * RK + 2
    for q in np.linspace(0, 1, int(n)):
        th = th0 + (th1 - th0) * q
        x, y = arc_pt(A, B, h, th)
        x2, y2 = arc_pt(A, B, h, th + 0.02)
        a = math.degrees(math.atan2(y2 - y, x2 - x))
        out.append((x, y - off, a + 90))
    return out

def walk_rings(P, Q, u, N, R, pc, h):
    """Slinky stepping from P to Q. u in [0,2]: 0 = stacked on P, 1 = full arch, 2 = stacked on Q."""
    u = min(max(u, 0.0), 2.0)
    if u <= 1:
        m = int(round(N * u))
        st = stack_rings(P, N - m, R, pc)
        top = (P[0], P[1] - (N - m) * pc)
        return st + arc_rings(top, Q, h, 0.0, math.pi * u, m, R)
    v = u - 1
    nb = int(round(N * v))
    st = stack_rings(Q, nb, R, pc)
    top = (Q[0], Q[1] - nb * pc)
    return st + arc_rings(P, top, h, math.pi * v, math.pi, N - nb, R)

def slinky_stack(img, P, R, N, pc, tilt=0.0, pivot=None):
    rings = stack_rings(P, N, R, pc)
    if tilt:
        pv = pivot or P
        ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        rings = [(pv[0] + (x - pv[0]) * ca - (y - pv[1]) * sa, pv[1] + (x - pv[0]) * sa + (y - pv[1]) * ca, r + tilt) for x, y, r in rings]
    draw_rings(img, rings, R)

def motion_lines(img, cx, cy, R, t, color=(255, 255, 255)):
    ov = OV(img, cx - R - 40, cy - R - 40, cx + R + 40, cy + R + 40)
    for j in range(5):
        a = math.radians(200 + j * 28)
        k = (math.sin(t * 10 + j) + 1) / 2
        r0, r1 = R * 0.75, R * (0.95 + 0.1 * k)
        ov.d.line(ov.pts([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)]),
                  fill=color + (int(150 + 100 * k),), width=12)
    ov.commit()

# ====================================================================== plates
_PL = {}
def wall_plate(c0='#F2B266', c1='#B5562C', seed=3, spot=(CX, 900, 1300)):
    key = (c0, c1, seed)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.9 + 0.1 * smooth_noise(PH, PW, 110, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, spot[0], spot[1], spot[2], 1.3))[..., None]
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.45))
    _PL[key] = img
    return img.copy()

def stairs(img, P, dx, dy, k0, k1, col=(150, 92, 50)):
    """Side-view staircase whose step k landing point is P + k*(dx,dy)."""
    ov = OV(img, 0, 0, PW, PH)
    c = np.array(col, np.float32)
    cc = lambda m: tuple(int(min(255, v * m)) for v in c) + (255,)
    for k in range(k0, k1):
        x = P[0] + k * dx
        y = P[1] + k * dy
        if y > PH + 50 or x + dx / 2 < -50 or x - dx / 2 > PW + 50:
            continue
        xl, xr = x - dx / 2, x + dx / 2
        ov.d.rectangle((xl, y, xr, PH + 10), fill=cc(0.78))
        ov.d.rectangle((xl, y, xr, y + 34), fill=cc(1.15))
        ov.d.rectangle((xl, y + 34, xr, y + 48), fill=cc(0.55))
        ov.d.rectangle((xr - 18, y, xr, PH + 10), fill=cc(0.6))
        for gy in range(int(y + 110), PH, 90):
            ov.d.line([(xl, gy), (xr - 18, gy)], fill=cc(0.7), width=3)
    ov.commit()

def sea_plate():
    if 'sea' in _PL:
        return _PL['sea'].copy()
    arr = vgrad(PW, PH, [(0, '#2B3E6B'), (0.55, '#4A6FA5'), (1, '#0D1B33')])
    arr = arr * (0.9 + 0.1 * smooth_noise(PH, PW, 100, 8, 3))[..., None]
    img = plate_img(vignette(np.clip(arr, 0, 1), 0.4))
    _PL['sea'] = img
    return img.copy()

def dark_plate(c0='#3A2C52', c1='#120C1E', seed=16):
    key = ('dark', c0, c1, seed)
    if key in _PL:
        return _PL[key].copy()
    arr = vgrad(PW, PH, [(0, c0), (1, c1)])
    arr = arr * (0.85 + 0.1 * smooth_noise(PH, PW, 90, seed, 3))[..., None]
    arr = arr * (0.6 + 0.55 * radial(PW, PH, CX, 1000, 1500, 1.2))[..., None]
    img = plate_img(vignette(arr, 0.45))
    _PL[key] = img
    return img.copy()

def waves(img, t, y0, amp, col, phase=0.0, k=0.006, speed=2.0):
    ov = OV(img, 0, y0 - amp - 10, PW, PH)
    pts = [(x, y0 + amp * math.sin(x * k + t * speed + phase)) for x in range(-20, PW + 40, 20)]
    ov.d.polygon(ov.pts(pts + [(PW + 40, PH), (-20, PH)]), fill=col + (255,))
    ov.d.line(ov.pts(pts), fill=(230, 240, 255, 200), width=10)
    ov.commit()

# ====================================================================== 0: hook
class Hook(Base):
    """Frame 0: a giant metal coil already mid-flip down endless stairs."""
    z0, z1 = 1.08, 1.13
    R, N, PC, HH = 230, 46, 10, 520
    DX, DY = 600, 380
    SPEED = 1.45   # u per second (2 = one full step)
    U0 = 0.92
    P0 = (CX - 300, 1360)
    def make_shakes(self):
        return [(self.we('Navy') + 0.03, 14, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.6)]
        for k in range(1, 4):
            ev.append(((2 * k - self.U0) / self.SPEED, 'bloop', 0.55))
        ev += [(self.we('Navy') - 0.02, 'thud', 0.8)]
        return ev
    def plate(self):
        self.st = stamp_sprite('FOR NAVY SHIPS!', 112, color=RED, angle=-6)
        return wall_plate()
    def hero(self, img, t):
        u_all = self.U0 + self.SPEED * t
        u = u_all - 2 * math.floor(u_all / 2)
        # world scrolls so the arch stays centred
        P = (self.P0[0] + self.DX * (1 - u) / 2, self.P0[1] + self.DY * (1 - u) / 2)
        Q = (P[0] + self.DX, P[1] + self.DY)
        stairs(img, P, self.DX, self.DY, -3, 4)
        glow(img, (P[0] + Q[0]) / 2, P[1] - 150, 650, (255, 240, 210), 0.45)
        ground_shadow(img, P[0], P[1] + 4, self.R * 2.2, 0.35 * (1 - clamp01(u - 1)))
        ground_shadow(img, Q[0], Q[1] + 4, self.R * 2.2, 0.35 * clamp01(u - 0.6))
        draw_rings(img, walk_rings(P, Q, u, self.N, self.R, self.PC, self.HH), self.R)
    def dyn(self, img, t):
        self.hero(img, t)
        stamp_in(img, self.st, CX, 1990, t, self.we('Navy') - 0.02)
    def cam(self, t):
        k = clamp01(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * ease_in_out(k)
        dx, dy, dr = self.shake(t)
        return z, CX + dx, CY + dy, dr

# ====================================================================== 1: ship instruments
def gauge_sprite(r=230):
    im = Image.new('RGBA', (2 * r + 40, 2 * r + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = r + 20
    d.ellipse((c - r, c - r, c + r, c + r), fill=(185, 140, 60, 255))
    d.ellipse((c - r + 26, c - r + 26, c + r - 26, c + r - 26), fill=(248, 244, 230, 255), outline=(60, 50, 40, 255), width=6)
    for j in range(16):
        a = j * math.pi / 8
        r0, r1 = r - 50, (r - 80 if j % 2 == 0 else r - 64)
        d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0), (c + math.cos(a) * r1, c + math.sin(a) * r1)], fill=(40, 40, 46, 255), width=8)
    f = font(64)
    for txt, a in (('N', -90), ('E', 0), ('S', 90), ('W', 180)):
        x, y = c + math.cos(math.radians(a)) * (r - 125), c + math.sin(math.radians(a)) * (r - 125)
        bb = f.getbbox(txt)
        d.text((x - (bb[2] + bb[0]) / 2, y - (bb[3] + bb[1]) / 2), txt, font=f, fill=(40, 40, 46, 255))
    d.polygon([(c, c - r + 70), (c + 22, c), (c, c + 20), (c - 22, c)], fill=(214, 50, 44, 255))
    d.ellipse((c - 18, c - 18, c + 18, c + 18), fill=(40, 40, 46, 255))
    return im

class Ship(Base):
    z0, z1 = 1.1, 1.18
    focus = (CX, 1080)
    def make_shakes(self):
        return [(self.we('1943'), 12, 0.28), (self.we('rough'), 14, 0.3)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1943'), 'thud', 0.7), (self.we('Richard') - 0.03, 'pop', 0.5),
                (self.we('springs'), 'bloop', 0.5), (self.we('instruments'), 'tick', 0.4), (self.we('rough'), 'wind', 0.7)]
    def plate(self):
        self.g = gauge_sprite(230)
        self.st = stamp_sprite('1943', 150, color=BLUE, angle=-6)
        return sea_plate()
    def dyn(self, img, t):
        tR = self.we('rough')
        rough = 1.0 + 1.3 * clamp01((t - tR + 0.3) / 0.5)
        ang = 7 * rough * math.sin(t * 2.2)
        waves(img, t, 1760, 40 * rough, (40, 70, 120), 0.0)
        cx, cy = CX, 1600
        deck = rot_pts([(cx - 760, cy), (cx + 760, cy), (cx + 760, cy + 150), (cx - 760, cy + 150)], (cx, cy), math.radians(ang))
        ov = OV(img, 0, 1000, PW, PH)
        ov.d.polygon(ov.pts(deck), fill=(120, 80, 48, 255))
        for j in range(1, 8):
            p = rot_pts([(cx - 760 + j * 190, cy), (cx - 760 + j * 190, cy + 150)], (cx, cy), math.radians(ang))
            ov.d.line(ov.pts(p), fill=(80, 52, 30, 255), width=6)
        ov.commit()
        plat_y = 1260
        for sx in (-250, 250):
            base = rot_pts([(cx + sx, cy)], (cx, cy), math.radians(ang))[0]
            top = (cx + sx, plat_y + 30)
            rings = [(base[0] + (top[0] - base[0]) * q, base[1] + (top[1] - base[1]) * q - 18, 0.0) for q in np.linspace(0, 1, 13)]
            draw_rings(img, rings, 66)
        ov = OV(img, cx - 360, plat_y - 20, cx + 360, plat_y + 50)
        ov.d.rounded_rectangle(ov.box(cx - 350, plat_y - 10, cx + 350, plat_y + 34), 12, fill=(70, 74, 84, 255))
        ov.commit()
        g = self.g.rotate(3 * math.sin(t * 1.3), resample=Image.BICUBIC)
        sh, pad = shadow_of(g, 16, 0.4)
        paste_at(img, sh, cx - g.width / 2 - pad + 20, plat_y - 10 - g.height - pad + 30)
        paste_at(img, g, cx - g.width / 2, plat_y - 10 - g.height)
        stamp_in(img, self.st, CX - 360, 560, t, self.we('1943'))
        pop(img, C('ENGINEER RICHARD JAMES', 62, bg=YEL), CX, 330, t, self.we('Richard') - 0.05, out_t=self.we('instruments') - 0.1)
        pop(img, C('KEEP SHIP GEAR STEADY', 62, bg=(255, 255, 255)), CX, 330, t, self.we('instruments') - 0.05, out_t=tR - 0.1)
        pop(img, C('ROUGH SEAS!', 86, bg=(60, 150, 230), fg=(255, 255, 255)), CX, 330, t, tR - 0.05)

# ====================================================================== 2: knocked off the shelf
def shelf(img, y, x0=-20, x1=PW + 20):
    ov = OV(img, x0, y - 10, x1, y + 200)
    ov.d.rectangle(ov.box(x0, y, x1, y + 60), fill=(150, 96, 52, 255))
    ov.d.rectangle(ov.box(x0, y, x1, y + 14), fill=(190, 130, 76, 255))
    ov.d.rectangle(ov.box(x0, y + 60, x1, y + 80), fill=(90, 56, 30, 255))
    for bx in (x0 + 200, x1 - 260):
        ov.d.polygon(ov.pts([(bx, y + 80), (bx + 50, y + 80), (bx + 50, y + 190)]), fill=(110, 70, 38, 255))
    ov.commit()

class Shelf(Base):
    z0, z1 = 1.12, 1.2
    focus = (CX, 1080)
    SY = 1180
    def make_shakes(self):
        return [(self.we('knocked') + 0.05, 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('day'), 'pop', 0.5), (self.we('knocked') + 0.05, 'thud', 0.8), (self.we('spring'), 'riser', 0.4)]
    def plate(self):
        img = wall_plate('#8EC5D9', '#3E6E8C', 4)
        shelf(img, self.SY)
        self.hand = get_hand(520, math.pi)
        self.st = stamp_sprite('OOPS!', 170, color=RED, angle=-8)
        return img
    def dyn(self, img, t):
        tK = self.we('knocked') + 0.05
        slinky_stack(img, (270, self.SY), 100, 30, 9)
        slinky_stack(img, (1030, self.SY), 100, 30, 9)
        hx = 1300 - 380 * ease_out((t - 0.1) / max(0.2, tK - 0.1))
        if t > tK:
            hx = 920 + 160 * ease_out((t - tK) / 0.4)
        k = clamp01((t - tK) / 0.7)
        tilt = -95 * ease_in_out(k)
        P = (650, self.SY)
        pv = (P[0] - 110, P[1])
        dy = 1400 * (k - 0.55) ** 2 if k > 0.55 else 0.0
        slinky_stack(img, (P[0], P[1] + dy), 110, 30, 9, tilt, (pv[0], pv[1] + dy))
        draw_hand(img, self.hand, (hx - 60, self.SY - 200), 0.1)
        pop(img, C('ONE DAY...', 84, bg=YEL), CX, 330, t, self.we('day') - 0.1, out_t=tK - 0.1)
        stamp_in(img, self.st, CX, 420, t, tK)

# ====================================================================== 3: it walked (shelf -> books -> floor)
def books(img, x, y_top, w=360, n=4):
    ov = OV(img, x - w / 2 - 30, y_top - 10, x + w / 2 + 30, y_top + n * 110 + 10)
    cols = [(200, 60, 50), (60, 120, 200), (240, 190, 60), (70, 160, 100), (150, 80, 170)]
    h = 110
    for j in range(n):
        y = y_top + j * h
        off = (j % 2) * 18 - 9
        ov.d.rounded_rectangle(ov.box(x - w / 2 + off, y, x + w / 2 + off, y + h - 6), 10, fill=cols[j % 5] + (255,))
        ov.d.rectangle(ov.box(x - w / 2 + off + 20, y + 30, x + w / 2 + off - 20, y + 44), fill=(250, 240, 210, 255))
    ov.commit()

class Walked(Base):
    z0, z1 = 1.14, 1.2
    focus = (CX + 40, 1330)
    R, N, PC = 110, 34, 8
    def make_shakes(self):
        return [(self.we('WALKED'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('instead'), 'tick', 0.4), (self.we('falling'), 'bloop', 0.6)]
    def plate(self):
        img = wall_plate('#8EC5D9', '#3E6E8C', 4)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 1880, PW, PH), fill=(120, 84, 56, 255))
        d.rectangle((0, 1880, PW, 1900), fill=(160, 116, 80, 255))
        shelf(img, 900, -20, 520)
        books(img, 690, 1440, 340, 4)
        self.pts = [(330, 900), (690, 1440), (1050, 1880)]
        self.st = stamp_sprite('IT WALKED!', 140, color=RED, angle=-7)
        return img
    def dyn(self, img, t):
        tot = 2 * (len(self.pts) - 1)
        u_all = min(tot, 0.35 + t * 1.9)
        k = min(len(self.pts) - 2, int(u_all // 2))
        u = u_all - 2 * k
        P, Q = self.pts[k], self.pts[k + 1]
        draw_rings(img, walk_rings(P, Q, u, self.N, self.R, self.PC, 330), self.R)
        pop(img, C('INSTEAD OF FALLING...', 70, bg=YEL), CX, 600, t, self.we('instead') - 0.05, out_t=self.we('WALKED') - 0.1)
        stamp_in(img, self.st, CX, 640, t, self.we('WALKED'))

# ====================================================================== 4: end over end
class Alive(Hook):
    z0, z1 = 1.22, 1.32
    R, N, PC, HH = 170, 40, 10, 420
    DX, DY = 460, 340
    SPEED = 2.2
    U0 = 0.3
    P0 = (CX - 230, 1250)
    def make_shakes(self):
        return [(self.we('alive'), 12, 0.3)]
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('flipped'), 'pop', 0.5)]
        for k in range(1, 5):
            tl = (2 * k - self.U0) / self.SPEED
            if tl < self.dur - 0.35:
                ev.append((tl, 'bloop', 0.5))
        return ev
    def plate(self):
        return wall_plate('#C9A2E8', '#4C2F7A', 6)
    def dyn(self, img, t):
        self.hero(img, t)
        pop(img, C('END OVER END', 84, bg=YEL), CX, 470, t, self.we('end') - 0.05, out_t=self.we('like') - 0.1)
        pop(img, C('LIKE IT WAS ALIVE', 78, bg=(255, 255, 255)), CX, 470, t, self.we('like') - 0.05)
    def cam(self, t):
        z, fx, fy, r = super().cam(t)
        p = 1 - ease_out(t / 0.32)
        return z * (1 + 0.12 * p), fx, fy - 60, r + 2.2 * p

# ====================================================================== 5: dictionary
def book_sprite(w=1000, h=640, hl=False):
    im = Image.new('RGBA', (w + 60, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 30, w + 50, h + 70), 30, fill=(120, 40, 36, 255))
    d.polygon([(30, 20), (w / 2 + 30, 50), (w / 2 + 30, h + 50), (30, h + 30)], fill=(250, 246, 232, 255))
    d.polygon([(w / 2 + 30, 50), (w + 30, 20), (w + 30, h + 30), (w / 2 + 30, h + 50)], fill=(244, 238, 220, 255))
    d.line([(w / 2 + 30, 50), (w / 2 + 30, h + 50)], fill=(180, 170, 150, 255), width=6)
    for side in (0, 1):
        x0 = 80 + side * (w / 2)
        for j in range(9):
            y = 110 + j * 56
            if hl and side == 1 and 3 <= j <= 5:
                continue
            ln = w / 2 - 120 - (j * 37 % 90)
            d.line([(x0, y), (x0 + ln, y)], fill=(170, 160, 140, 255), width=12)
    if hl:
        x0, y0 = w / 2 + 90, 270
        d.rounded_rectangle((x0 - 24, y0 - 14, x0 + 360, y0 + 120), 20, fill=(255, 226, 80, 255))
        d.text((x0, y0 - 6), 'slinky', font=font(92, FONT_SERIF), fill=(30, 26, 30, 255))
    return im

class Dictionary(Base):
    z0, z1 = 1.04, 1.12
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('slinky'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('Betty'), 'pop', 0.5), (self.we('flipped'), 'rustle', 0.7),
                (self.we('dictionary'), 'rustle', 0.5), (self.we('perfect'), 'riser', 0.4), (self.we('slinky'), 'ding', 0.7),
                (self.we('sleek'), 'chime', 0.5)]
    def plate(self):
        img = dark_plate('#6B4A30', '#24160C', 18)
        self.b0 = book_sprite(1060, 680, False)
        self.b1 = book_sprite(1060, 680, True)
        self.hand = get_hand(480, 1.9)
        self.defn = C('= SLEEK & GRACEFUL', 70, bg=(255, 255, 255))
        self.st = stamp_sprite('SLINKY', 190, color=RED, angle=-7)
        return img
    def dyn(self, img, t):
        tF, tS = self.we('flipped'), self.we('slinky')
        b = self.b1 if t > tS - 0.05 else self.b0
        s = 1.0 + (0.05 * ease_back((t - tS) / 0.3) if t > tS else 0)
        bx, by = CX, 1200
        sh, pad = shadow_of(b, 20, 0.5)
        paste_at(img, sh, bx - b.width / 2 - pad + 20, by - b.height / 2 - pad + 40)
        paste_center(img, b, bx, by, scale=s)
        if tF - 0.1 < t < tS - 0.1:
            ph = ((t - tF) * 3.2) % 1
            w = 500 * math.cos(ph * math.pi)
            top = by - 330
            lift = 40 * math.sin(ph * math.pi)
            ov = OV(img, bx - 560, top - 120, bx + 560, top + 760)
            ov.d.polygon(ov.pts([(bx, top + 30), (bx + w, top - lift), (bx + w, top + 640 - lift), (bx, top + 670)]),
                         fill=(255, 252, 240, 255), outline=(180, 170, 150, 255))
            ov.commit()
            draw_hand(img, self.hand, (bx + w * 0.9, top + 220), 0.15)
        pop(img, C('HIS WIFE BETTY', 80, bg=YEL), CX, 330, t, self.we('Betty') - 0.05, out_t=self.we('perfect') - 0.1)
        pop(img, C('THE PERFECT NAME', 76, bg=(255, 255, 255)), CX, 330, t, self.we('perfect') - 0.05, out_t=tS - 0.05)
        stamp_in(img, self.st, CX, 420, t, tS)
        pop(img, self.defn, CX, 1830, t, self.we('sleek') - 0.08)

# ====================================================================== 6: department store, Christmas 1945
def store_sprite(w=1060, h=1100):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 120, w, h), fill=(176, 150, 120, 255))
    d.rectangle((0, 100, w, 150), fill=(140, 116, 92, 255))
    for r in range(2):
        for c in range(5):
            x, y = 50 + c * 200, 190 + r * 230
            d.rectangle((x, y, x + 150, y + 170), fill=(255, 214, 120, 255), outline=(110, 90, 70, 255), width=8)
            d.line([(x + 75, y), (x + 75, y + 170)], fill=(110, 90, 70, 255), width=6)
    d.rectangle((60, 680, w - 60, 760), fill=(40, 80, 60, 255))
    f = font(58)
    txt = 'DEPARTMENT STORE'
    d.text(((w - f.getlength(txt)) / 2, 690), txt, font=f, fill=(255, 240, 200, 255))
    for j in range(12):
        x = j * w / 12
        d.polygon([(x, 780), (x + w / 12, 780), (x + w / 12 + 10, 860), (x + 10, 860)], fill=((200, 50, 44) if j % 2 else (250, 245, 235)) + (255,))
    d.rectangle((90, 880, w - 90, h), fill=(255, 226, 150, 255), outline=(90, 70, 50, 255), width=12)
    return im

class Store(Base):
    z0, z1 = 1.02, 1.1
    focus = (CX, 1120)
    def make_shakes(self):
        return [(self.we('1945'), 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('1945'), 'thud', 0.7), (self.we('Philadelphia'), 'pop', 0.5),
                (self.we('show'), 'chime', 0.5), (self.we('off'), 'party', 0.4)]
    def plate(self):
        img = dark_plate('#1E2C55', '#0A1028', 21)
        sp = store_sprite()
        paste_at(img, sp, CX - sp.width / 2, 400)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 1500, PW, PH), fill=(232, 238, 246, 255))
        self.st = stamp_sprite('1945', 160, color=BLUE, angle=-6)
        self.pts = [(CX - 220, 1480), (CX + 80, 1480)]
        return img
    def dyn(self, img, t):
        ov = OV(img, 0, 300, PW, 560)
        cols = [(255, 80, 70), (90, 220, 110), (255, 210, 60), (90, 160, 255)]
        pts = [(x, 400 + 40 * math.sin(x / 130)) for x in range(-20, PW + 40, 30)]
        ov.d.line(ov.pts(pts), fill=(40, 50, 40, 255), width=5)
        for j, x in enumerate(range(20, PW, 70)):
            y = 410 + 40 * math.sin(x / 130)
            on = (j + int(t * 4)) % 3 != 0
            ov.d.ellipse(ov.box(x - 14, y - 6, x + 14, y + 26), fill=cols[j % 4] + (255 if on else 110,))
        ov.commit()
        u = (0.5 + t * 1.6) % 4
        P, Q = self.pts
        rings = walk_rings(P, Q, u, 24, 90, 6, 150) if u < 2 else walk_rings(Q, P, u - 2, 24, 90, 6, 150)
        draw_rings(img, rings, 90)
        ov = OV(img, 0, 0, PW, PH)
        rng = np.random.default_rng(3)
        for j in range(70):
            x = (rng.uniform(0, PW) + 30 * math.sin(t + j)) % PW
            y = (rng.uniform(0, PH) + t * 160 * rng.uniform(0.6, 1.2)) % PH
            r = rng.uniform(4, 10)
            ov.d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 210))
        ov.commit()
        stamp_in(img, self.st, CX - 300, 1750, t, self.we('1945'))
        pop(img, C('PHILADELPHIA', 72, bg=YEL), CX + 200, 1750, t, self.we('Philadelphia') - 0.05)
        pop(img, C('CHRISTMAS DEMO', 70, bg=(214, 50, 44), fg=(255, 255, 255)), CX, 1990, t, self.we('show') - 0.05)

# ====================================================================== 7: sloped board, 400 sold in 90 minutes
class Ramp(Base):
    z0, z1 = 1.0, 1.08
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('400'), 14, 0.3), (self.we('90'), 12, 0.28)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('walking'), 'bloop', 0.5), (self.we('sloped'), 'bloop', 0.4),
                (self.we('400'), 'cash', 0.8), (self.we('90'), 'ding', 0.6), (self.we('dollar'), 'cash', 0.6)]
    def plate(self):
        img = wall_plate('#F7D08A', '#C2783A', 9)
        self.A, self.B = (-80, 880), (PW + 80, 1420)
        ov = OV(img, 0, 0, PW, PH)
        a, b = self.A, self.B
        ov.d.polygon([(a[0], a[1]), (b[0], b[1]), (b[0], b[1] + 70), (a[0], a[1] + 70)], fill=(170, 112, 62, 255))
        ov.d.polygon([(a[0], a[1]), (b[0], b[1]), (b[0], b[1] + 16), (a[0], a[1] + 16)], fill=(210, 150, 92, 255))
        ov.commit()
        self.st = stamp_sprite('SOLD OUT!', 150, color=RED, angle=-8)
        return img
    def board_pt(self, s):
        return (self.A[0] + (self.B[0] - self.A[0]) * s, self.A[1] + (self.B[1] - self.A[1]) * s)
    def dyn(self, img, t):
        t4, tA = self.we('400'), self.we('all')
        for off in (0.0, 0.4, 0.8):
            prog = (t * 0.16 + off) % 1.2 - 0.1
            step = 0.17
            u_all = prog / step * 2
            k = math.floor(u_all / 2)
            u = u_all - 2 * k
            draw_rings(img, walk_rings(self.board_pt(k * step), self.board_pt((k + 1) * step), u, 24, 100, 6, 240), 100)
        k = clamp01((t - tA + 0.2) / max(0.3, t4 - tA + 0.2))
        n = int(round(400 * ease_in_out(k)))
        ov = OV(img, CX - 330, 1660, CX + 330, 2120)
        ov.d.rounded_rectangle(ov.box(CX - 320, 1680, CX + 320, 2100), 40, fill=(250, 248, 240, 255), outline=(30, 30, 36, 255), width=10)
        f = font(70)
        ov.d.text(ov.p(CX - f.getlength('SOLD') / 2, 1710), 'SOLD', font=f, fill=(120, 120, 130, 255))
        f2 = font(220)
        txt = str(n)
        ov.d.text(ov.p(CX - f2.getlength(txt) / 2, 1780), txt, font=f2, fill=(30, 30, 36, 255))
        ov.commit()
        pop(img, C('SLOPED BOARD', 72, bg=YEL), CX, 330, t, self.we('sloped') - 0.05, out_t=t4 - 0.1)
        stamp_in(img, self.st, CX, 420, t, t4)
        pop(img, C('IN 90 MINUTES', 74, bg=(60, 150, 230), fg=(255, 255, 255)), CX, 590, t, self.we('90') - 0.05)
        pop(img, C('$1 EACH', 84, bg=GREEN, fg=(255, 255, 255)), CX + 250, 760, t, self.we('dollar') - 0.05)

# ====================================================================== 8: radio antenna
def radio_sprite(w=560, h=420):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), 34, fill=(86, 98, 58, 255), outline=(40, 46, 26, 255), width=10)
    d.rounded_rectangle((30, 30, w - 30, 140), 20, fill=(50, 58, 34, 255))
    for j, x in enumerate((110, 250, 390)):
        d.ellipse((x - 50, 190, x + 50, 290), fill=(30, 34, 22, 255), outline=(150, 160, 120, 255), width=8)
        a = math.radians(-60 + j * 50)
        d.line([(x, 240), (x + math.cos(a) * 40, 240 + math.sin(a) * 40)], fill=(220, 220, 200, 255), width=8)
    d.rectangle((40, 320, w - 40, 380), fill=(60, 68, 40, 255))
    for x in range(60, w - 60, 30):
        d.line([(x, 330), (x, 370)], fill=(40, 46, 26, 255), width=6)
    d.ellipse((w - 110, 50, w - 60, 100), fill=(255, 80, 60, 255))
    return im

class Antenna(Base):
    z0, z1 = 1.02, 1.1
    focus = (CX, 1150)
    def make_shakes(self):
        return [(self.we('war'), 16, 0.32)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('war'), 'boom', 0.7), (self.we('soldiers'), 'pop', 0.5),
                (self.we('Vietnam'), 'thud', 0.6), (self.we('radio'), 'buzzer', 0.4)]
    def plate(self):
        img = dark_plate('#4F6B3A', '#162212', 23)
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(4)
        for j in range(16):
            x = j * 90 + rng.uniform(-20, 20)
            r = rng.uniform(120, 200)
            d.ellipse((x - r, 1720 - r, x + r, 1720 + r * 0.6), fill=(22, 40, 20, 255))
        d.rectangle((0, 1720, PW, PH), fill=(40, 52, 30, 255))
        self.radio = radio_sprite()
        self.st = stamp_sprite('RADIO ANTENNA!', 96, color=(255, 210, 60), angle=-6)
        return img
    def dyn(self, img, t):
        tA = self.we('Slinkys')
        rx, ry = CX - 60, 1600
        paste_at(img, self.radio, rx - self.radio.width / 2, ry)
        ext = ease_out((t - 0.05) / 0.9)
        top_h = 120 + 820 * ext
        base = (rx + 170, ry + 10)
        sway = 50 * math.sin(t * 2.5) * ext
        rings = []
        for q in np.linspace(0, 1, 34):
            rings.append((base[0] + sway * q * q, base[1] - top_h * q, math.degrees(math.atan2(2 * sway * q, top_h))))
        draw_rings(img, rings, 60)
        if t > tA - 0.3:
            tx, ty = rings[-1][0], rings[-1][1]
            draw_waves(img, (tx, ty), t, 200, 340, color=(255, 230, 120), speed=500, spacing=110, r0=60, rmax=620, width=10)
        pop(img, C('IT WENT TO WAR', 76, bg=YEL), CX, 330, t, self.we('war') - 0.1, out_t=self.we('Vietnam') - 0.1)
        pop(img, C('VIETNAM WAR', 80, bg=(255, 255, 255)), CX, 330, t, self.we('Vietnam') - 0.05)
        stamp_in(img, self.st, CX, 2110, t, self.we('radio'))

# ====================================================================== 9: 250 million
class Million(Base):
    z0, z1 = 1.12, 1.0
    punch = 0.1
    def make_shakes(self):
        return [(self.we('MILLION'), 20, 0.35)]
    def events(self):
        return [(0.02, 'swipe', 0.5), (self.we('over'), 'riser', 0.5), (self.we('250'), 'pop', 0.6), (self.we('MILLION'), 'boom', 0.85)]
    def plate(self):
        self.st = stamp_sprite('250 MILLION+', 140, color=RED, angle=-7)
        lay = Image.new('RGBA', (220, 260), (0, 0, 0, 0))
        draw_rings(lay, stack_rings((110, 240), 18, 70, 8), 70)
        self.small = lay
        return dark_plate('#2E4D7A', '#0C1A30', 17)
    def dyn(self, img, t):
        tM = self.we('MILLION')
        rows, cols = 9, 6
        cells = []
        for r in range(rows):
            for c in range(cols):
                x = 110 + c * 215 + (r % 2) * 50
                y = 160 + r * 250
                cells.append(((x - CX) ** 2 + (y - 1100) ** 2, x, y))
        cells.sort()
        n_show = max(8, int(len(cells) * clamp01((t + 0.3) / max(0.4, tM))))
        for k, (_, x, y) in enumerate(cells[:n_show]):
            paste_center(img, self.small, x, y + 8 * math.sin(t * 6 + k))
        pop(img, C('SINCE THEN...', 80, bg=YEL), CX, 330, t, 0.05, out_t=tM - 0.1)
        if t > tM:
            ov = OV(img, 0, 0, PW, PH)
            ov.d.rectangle((0, 0, PW, PH), fill=(0, 0, 0, int(110 * clamp01((t - tM) / 0.2))))
            ov.commit()
        stamp_in(img, self.st, CX, 1000, t, tM)

# ====================================================================== 10: outro -> loops into the hook
class Outro(Hook):
    def make_shakes(self):
        return []
    def events(self):
        ev = [(0.02, 'swipe', 0.5), (self.we('never') - 0.02, 'pop', 0.5)]
        for k in range(-4, 1):
            tl = (2 * k - self.U0) / self.SPEED + self.dur
            if 0.1 < tl < self.dur - 0.4:
                ev.append((tl, 'bloop', 0.45))
        return ev
    def dyn(self, img, t):
        self.hero(img, t - self.dur)   # ends exactly where frame 0 begins
        tN, tB = self.we('never'), self.we('because')
        pop(img, C('NOT BAD!', 84, bg=YEL), CX, 1990, t, 0.05, out_t=tN - 0.1)
        pop(img, C('NEVER MEANT FOR KIDS', 70, bg=(255, 255, 255)), CX, 1990, t, tN - 0.05, out_t=tB - 0.05)
    def cam(self, t):
        p = 1 - ease_out(t / 0.32)
        return self.z0 * (1 + 0.1 * p), CX, CY, 2.0 * p

SCENES = [Hook, Ship, Shelf, Walked, Alive, Dictionary, Store, Ramp, Antenna, Million, Outro]
