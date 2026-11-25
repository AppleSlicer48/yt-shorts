"""Cartoon people for Functional Fun! videos (replaces the wooden mannequins).

Flat, friendly explainer-style characters with faces, hair, outfits and
expressions. Everything returns an RGBA sprite (PIL Image) plus anchor points,
so scenes can paste it with paste_center / with_shadow like any other sprite.

    from cartoon import person, PRESETS
    spr, anc = person(**PRESETS['chef'], expr='shocked', arm_r=150, talk=True, scale=0.9)
    # anc['feet'] = (x, y) bottom-center inside the sprite; paste so feet land on the floor
    # anc['hand_l'], anc['hand_r'] = hand centers (to attach held props)
    # anc['head'] = head center

Animate by calling person() each frame with changing arm angles / expr / talk.
Results are cached by their arguments, so repeated poses are cheap.

Arm angles: 0 = hanging down, 90 = straight out to the side, 180 = straight up.
'arm_l' is the arm on the viewer's LEFT, 'arm_r' on the viewer's RIGHT.
Expressions: happy, smile, shocked, sad, angry, think, wink, proud, nervous.
"""
import math
from functools import lru_cache
from PIL import Image, ImageDraw

SS = 2                      # supersample factor
BASE_W, BASE_H = 760, 1360  # sprite size at scale 1 (person ~1040 px tall + hat room)
INK = (40, 30, 35)

SKINS = {
    'light': (246, 208, 178), 'tan': (226, 170, 125), 'medium': (196, 135, 95),
    'brown': (150, 98, 64), 'dark': (105, 68, 45),
}

PRESETS = {
    'chef':      dict(skin='tan', hair='short', hair_color=(70, 45, 35), top=(250, 250, 248), bottom=(60, 70, 110), hat='chef', apron=(210, 70, 55), mustache=True),
    'scientist': dict(skin='light', hair='messy', hair_color=(150, 150, 155), top=(250, 250, 250), bottom=(70, 80, 100), glasses=True, coat=True),
    'worker':    dict(skin='medium', hair='short', hair_color=(40, 30, 25), top=(70, 120, 190), bottom=(60, 60, 70), hat='hardhat'),
    'boss':      dict(skin='light', hair='side', hair_color=(110, 75, 45), top=(50, 55, 75), bottom=(40, 45, 60), tie=(200, 50, 50)),
    'girl':      dict(skin='tan', hair='ponytail', hair_color=(95, 55, 35), top=(240, 120, 160), bottom=(80, 110, 190)),
    'woman':     dict(skin='brown', hair='long', hair_color=(35, 25, 20), top=(130, 90, 200), bottom=(60, 60, 80), dress=True),
    'boy':       dict(skin='light', hair='short', hair_color=(200, 150, 80), top=(90, 180, 120), bottom=(70, 90, 150), hat='cap', hat_color=(220, 60, 60)),
    'kid':       dict(skin='dark', hair='curly', hair_color=(30, 20, 15), top=(250, 190, 60), bottom=(70, 90, 150), child=True),
    'grandma':   dict(skin='light', hair='bun', hair_color=(215, 215, 220), top=(160, 110, 170), bottom=(90, 80, 110), dress=True, glasses=True),
    'salesman':  dict(skin='tan', hair='side', hair_color=(60, 40, 30), top=(140, 100, 70), bottom=(70, 55, 45), tie=(40, 70, 140), hat='fedora'),
}


def _darker(c, f=0.78):
    return tuple(max(0, int(v * f)) for v in c[:3])


def person(scale=1.0, skin='tan', hair='short', hair_color=(70, 45, 35), top=(90, 140, 210), bottom=(60, 70, 110),
           hat=None, hat_color=(220, 60, 60), apron=None, tie=None, coat=False, dress=False, glasses=False,
           mustache=False, child=False, expr='happy', talk=False, arm_l=15, arm_r=15, look=0.0, blink=False,
           facing=0):
    """Return (sprite, anchors). look: -1..1 moves the pupils left/right. facing: -1/0/1 small head turn."""
    key = (round(scale, 3), skin, hair, tuple(hair_color), tuple(top), tuple(bottom), hat, tuple(hat_color),
           tuple(apron) if apron else None, tuple(tie) if tie else None, coat, dress, glasses, mustache, child,
           expr, talk, int(round(arm_l)), int(round(arm_r)), round(look, 2), blink, facing)
    return _person(*key)


@lru_cache(maxsize=512)
def _person(scale, skin, hair, hair_color, top, bottom, hat, hat_color, apron, tie, coat, dress, glasses, mustache,
            child, expr, talk, arm_l, arm_r, look, blink, facing):
    k = SS * scale * (0.78 if child else 1.0)
    W, H = int(BASE_W * SS * scale), int(BASE_H * SS * scale)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    P = lambda v: v * k
    skin_c = SKINS.get(skin, skin) if isinstance(skin, str) else skin
    cx = W / 2
    feet_y = H - P(30) if not child else H - 30 * SS * scale
    body_h = 430
    leg_h = 300
    hip_y = feet_y - P(leg_h)
    sh_y = hip_y - P(body_h) + P(60)           # shoulder line
    head_r = 135
    head_cy = sh_y - P(head_r) - P(20)
    head_cx = cx + P(14) * facing

    # ---- legs + shoes
    if not dress:
        for sx in (-1, 1):
            d.rounded_rectangle([cx + sx * P(55) - P(40), hip_y - P(30), cx + sx * P(55) + P(40), feet_y - P(20)],
                                radius=P(34), fill=bottom)
    else:
        for sx in (-1, 1):
            d.rounded_rectangle([cx + sx * P(50) - P(22), hip_y + P(60), cx + sx * P(50) + P(22), feet_y - P(20)],
                                radius=P(20), fill=skin_c)
    for sx in (-1, 1):
        d.ellipse([cx + sx * P(62) - P(62), feet_y - P(48), cx + sx * P(62) + P(62), feet_y + P(14)], fill=(50, 40, 40))

    # ---- arms (drawn behind body), shoulder pivots
    def arm(side, ang):
        a = math.radians(ang)
        px, py = cx + side * P(135), sh_y + P(40)
        L = P(330)
        ex = px + side * math.sin(a) * L * 0.5
        ey = py + math.cos(a) * L * 0.5
        bend = math.radians(ang + (18 if ang < 120 else -10))
        hx = ex + side * math.sin(bend) * L * 0.5
        hy = ey + math.cos(bend) * L * 0.5
        sleeve = (250, 250, 248) if coat else top
        d.line([px, py, ex, ey], fill=sleeve, width=int(P(70)))
        d.ellipse([px - P(35), py - P(35), px + P(35), py + P(35)], fill=sleeve)
        d.ellipse([ex - P(35), ey - P(35), ex + P(35), ey + P(35)], fill=sleeve)
        d.line([ex, ey, hx, hy], fill=sleeve if ang < 60 else skin_c, width=int(P(58 if ang < 60 else 50)))
        d.ellipse([hx - P(42), hy - P(42), hx + P(42), hy + P(42)], fill=skin_c)
        d.ellipse([hx + side * P(20) - P(16), hy - P(34), hx + side * P(20) + P(16), hy - P(2)], fill=skin_c)  # thumb
        return hx, hy

    hand_l = arm(-1, arm_l)
    hand_r = arm(1, arm_r)

    # ---- torso
    body_top = sh_y - P(10)
    if dress:
        d.polygon([(cx - P(130), body_top + P(40)), (cx + P(130), body_top + P(40)),
                   (cx + P(190), hip_y + P(150)), (cx - P(190), hip_y + P(150))], fill=top)
        d.rounded_rectangle([cx - P(135), body_top, cx + P(135), hip_y - P(40)], radius=P(80), fill=top)
    else:
        d.rounded_rectangle([cx - P(145), body_top, cx + P(145), hip_y + P(25)], radius=P(85), fill=top)
    if coat:
        d.rounded_rectangle([cx - P(155), body_top, cx + P(155), hip_y + P(120)], radius=P(80), fill=(250, 250, 250), outline=(205, 205, 210), width=int(P(5)))
        d.polygon([(cx - P(40), body_top), (cx + P(40), body_top), (cx, body_top + P(150))], fill=top)
        d.line([cx, body_top + P(150), cx, hip_y + P(110)], fill=(205, 205, 210), width=int(P(5)))
    if hat == 'chef':
        for yy in (0.25, 0.45, 0.65):
            y = body_top + (hip_y - body_top) * yy
            d.ellipse([cx - P(12), y - P(12), cx + P(12), y + P(12)], fill=(200, 60, 50))
    if apron:
        d.rounded_rectangle([cx - P(115), body_top + P(200), cx + P(115), hip_y + P(110)], radius=P(28), fill=apron)
        d.line([cx - P(100), body_top + P(205), cx - P(60), body_top + P(20)], fill=apron, width=int(P(12)))
        d.line([cx + P(100), body_top + P(205), cx + P(60), body_top + P(20)], fill=apron, width=int(P(12)))
    if tie:
        d.polygon([(cx - P(18), body_top + P(10)), (cx + P(18), body_top + P(10)), (cx + P(28), body_top + P(190)),
                   (cx, body_top + P(225)), (cx - P(28), body_top + P(190))], fill=tie)
        d.polygon([(cx - P(70), body_top), (cx, body_top + P(60)), (cx + P(70), body_top), (cx, body_top + P(10))], fill=(250, 250, 250))
    # neck
    d.rounded_rectangle([head_cx - P(38), head_cy + P(95), head_cx + P(38), body_top + P(20)], radius=P(14), fill=_darker(skin_c, 0.9))

    # ---- hair behind head
    hc = hair_color
    if hair in ('long', 'ponytail'):
        d.rounded_rectangle([head_cx - P(150), head_cy - P(110), head_cx + P(150), head_cy + P(200 if hair == 'long' else 90)], radius=P(90), fill=hc)
        if hair == 'ponytail':
            d.ellipse([head_cx + P(110), head_cy - P(40), head_cx + P(230), head_cy + P(170)], fill=hc)
    if hair == 'curly':
        for a in range(0, 360, 30):
            r = math.radians(a)
            x, y = head_cx + math.cos(r) * P(120), head_cy - P(20) + math.sin(r) * P(110)
            if y < head_cy + P(40):
                d.ellipse([x - P(58), y - P(58), x + P(58), y + P(58)], fill=hc)

    # ---- head + ears
    for sx in (-1, 1):
        d.ellipse([head_cx + sx * P(128) - P(24), head_cy - P(10), head_cx + sx * P(128) + P(24), head_cy + P(50)], fill=skin_c)
    d.ellipse([head_cx - P(head_r), head_cy - P(head_r), head_cx + P(head_r), head_cy + P(head_r)], fill=skin_c)

    # ---- hair on top
    if hair in ('short', 'side', 'long', 'ponytail', 'bun', 'messy'):
        d.chord([head_cx - P(140), head_cy - P(150), head_cx + P(140), head_cy + P(60)], 180, 360, fill=hc)
        if hair == 'side':
            d.polygon([(head_cx - P(140), head_cy - P(40)), (head_cx + P(60), head_cy - P(140)), (head_cx + P(140), head_cy - P(40))], fill=hc)
        if hair in ('long', 'ponytail'):
            d.pieslice([head_cx - P(150), head_cy - P(150), head_cx + P(50), head_cy + P(40)], 180, 300, fill=hc)
        if hair == 'bun':
            d.ellipse([head_cx - P(60), head_cy - P(230), head_cx + P(60), head_cy - P(110)], fill=hc)
        if hair == 'messy':
            for a in (-60, -30, 0, 30, 60):
                r = math.radians(a - 90)
                x, y = head_cx + math.cos(r) * P(130), head_cy + math.sin(r) * P(120)
                d.ellipse([x - P(40), y - P(40), x + P(40), y + P(40)], fill=hc)

    # ---- face
    ey = head_cy - P(5)
    eye_dx = P(50)
    px = look * P(8)
    for sx in (-1, 1):
        ex = head_cx + sx * eye_dx + P(10) * facing
        if blink or (expr == 'wink' and sx == 1):
            d.arc([ex - P(18), ey - P(8), ex + P(18), ey + P(18)], 200, 340, fill=INK, width=int(P(7)))
        elif expr == 'shocked':
            d.ellipse([ex - P(26), ey - P(30), ex + P(26), ey + P(26)], fill=(255, 255, 255), outline=INK, width=int(P(5)))
            d.ellipse([ex + px - P(11), ey - P(11), ex + px + P(11), ey + P(11)], fill=INK)
        elif expr in ('happy', 'proud') and not talk:
            d.arc([ex - P(20), ey - P(14), ex + P(20), ey + P(16)], 200, 340, fill=INK, width=int(P(8)))
        else:
            d.ellipse([ex + px - P(16), ey - P(20), ex + px + P(16), ey + P(16)], fill=INK)
            d.ellipse([ex + px - P(5), ey - P(14), ex + px + P(4), ey - P(5)], fill=(255, 255, 255))
        # brows
        by = ey - P(48)
        if expr == 'angry':
            d.line([ex - sx * P(28), by - P(6), ex + sx * P(22), by + P(12)], fill=_darker(hc, 0.8), width=int(P(9)))
        elif expr in ('sad', 'nervous'):
            d.line([ex - sx * P(28), by + P(10), ex + sx * P(22), by - P(6)], fill=_darker(hc, 0.8), width=int(P(9)))
        elif expr == 'shocked':
            d.arc([ex - P(28), by - P(26), ex + P(28), by + P(6)], 200, 340, fill=_darker(hc, 0.8), width=int(P(9)))
        elif expr == 'think' and sx == 1:
            d.line([ex - P(26), by - P(12), ex + P(26), by - P(2)], fill=_darker(hc, 0.8), width=int(P(9)))
        else:
            d.line([ex - P(26), by, ex + P(26), by - P(4)], fill=_darker(hc, 0.8), width=int(P(9)))
    if glasses:
        for sx in (-1, 1):
            ex = head_cx + sx * eye_dx + P(10) * facing
            d.ellipse([ex - P(38), ey - P(38), ex + P(38), ey + P(34)], outline=(40, 40, 45), width=int(P(7)))
        d.line([head_cx - P(12), ey - P(6), head_cx + P(12), ey - P(6)], fill=(40, 40, 45), width=int(P(6)))
    # cheeks
    if expr not in ('angry', 'sad'):
        for sx in (-1, 1):
            d.ellipse([head_cx + sx * P(80) - P(22), ey + P(30), head_cx + sx * P(80) + P(22), ey + P(54)], fill=(240, 140, 130))
    # mouth
    mx, my = head_cx + P(10) * facing, head_cy + P(65)
    if expr == 'shocked':
        d.ellipse([mx - P(22), my - P(16), mx + P(22), my + P(38)], fill=(120, 40, 45))
    elif talk:
        d.chord([mx - P(36), my - P(18), mx + P(36), my + P(40)], 0, 180, fill=(120, 40, 45))
        d.chord([mx - P(20), my + P(12), mx + P(20), my + P(40)], 0, 180, fill=(235, 110, 110))
    elif expr in ('sad', 'nervous'):
        d.arc([mx - P(34), my + P(6), mx + P(34), my + P(50)], 200, 340, fill=INK, width=int(P(8)))
    elif expr == 'angry':
        d.line([mx - P(30), my + P(18), mx + P(30), my + P(18)], fill=INK, width=int(P(8)))
    elif expr == 'think':
        d.line([mx - P(24), my + P(14), mx + P(18), my + P(8)], fill=INK, width=int(P(8)))
    else:
        d.chord([mx - P(42), my - P(20), mx + P(42), my + P(44)], 0, 180, fill=(120, 40, 45))
        d.chord([mx - P(34), my - P(16), mx + P(34), my + P(6)], 0, 180, fill=(255, 255, 255))
    if mustache:
        for sx in (-1, 1):
            d.ellipse([mx + sx * P(28) - P(30), my - P(26), mx + sx * P(28) + P(30), my], fill=_darker(hc, 0.9))

    # ---- hats
    if hat == 'chef':
        hy = head_cy - P(head_r)
        d.rectangle([head_cx - P(110), hy - P(30), head_cx + P(110), hy + P(40)], fill=(255, 255, 255))
        for ox, r in ((-75, 75), (0, 95), (75, 75)):
            d.ellipse([head_cx + P(ox) - P(r), hy - P(170) - P(r) * 0.6, head_cx + P(ox) + P(r), hy - P(20) + P(r) * 0.2], fill=(255, 255, 255))
    elif hat == 'cap':
        hy = head_cy - P(70)
        d.chord([head_cx - P(140), hy - P(90), head_cx + P(140), hy + P(90)], 180, 360, fill=hat_color)
        d.rounded_rectangle([head_cx - P(10), hy - P(12), head_cx + P(190), hy + P(14)], radius=P(12), fill=_darker(hat_color))
    elif hat == 'hardhat':
        hy = head_cy - P(70)
        d.chord([head_cx - P(150), hy - P(110), head_cx + P(150), hy + P(100)], 180, 360, fill=(250, 200, 40))
        d.rounded_rectangle([head_cx - P(175), hy - P(10), head_cx + P(175), hy + P(16)], radius=P(10), fill=(230, 175, 30))
    elif hat == 'fedora':
        hy = head_cy - P(95)
        d.ellipse([head_cx - P(185), hy - P(10), head_cx + P(185), hy + P(40)], fill=(70, 55, 45))
        d.rounded_rectangle([head_cx - P(110), hy - P(110), head_cx + P(110), hy + P(20)], radius=P(40), fill=(85, 65, 50))
        d.rectangle([head_cx - P(110), hy - P(20), head_cx + P(110), hy + P(5)], fill=(40, 30, 25))

    out = img.resize((W // SS, H // SS), Image.LANCZOS)
    f = 1 / SS
    anchors = {
        'feet': (cx * f, feet_y * f),
        'hand_l': (hand_l[0] * f, hand_l[1] * f),
        'hand_r': (hand_r[0] * f, hand_r[1] * f),
        'head': (head_cx * f, head_cy * f),
        'height': (feet_y - (head_cy - P(head_r))) * f,
    }
    return out, anchors


def paste_person(img, spr, anc, x, floor_y, shadow=True):
    """Paste a person so their feet stand at (x, floor_y) on img. Adds a soft floor shadow."""
    from PIL import ImageFilter
    fx, fy = anc['feet']
    ox, oy = int(x - fx), int(floor_y - fy)
    if shadow:
        w = spr.width * 0.5
        sh = Image.new('RGBA', (int(w * 1.4), 90), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([10, 25, sh.width - 10, 65], fill=(0, 0, 0, 80))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        img.alpha_composite(sh, (int(x - sh.width / 2), int(floor_y - 45)))
    img.alpha_composite(spr, (ox, oy))
    return ox, oy


def talk_frame(t, words=None):
    """Mouth open/closed flip for a character who is speaking (about 8 flaps per second)."""
    return int(t * 8) % 2 == 0
