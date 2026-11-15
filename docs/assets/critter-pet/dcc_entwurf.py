# Entwurf 15.11.2026: zwei Pets nach Dungeon Crawler Carl (eigene Figuren, nur inspiriert).
# Mongo (Mongoliensis): Ei + 6 Schritte, vom komischen Küken zum gefiederten Raptor.
# Tummy-Acher: Ei + 6 Schritte, runde Fleischkugel auf zwei Beinen, frisst alles.
# Wachstum = Parameter-Satz derselben prozeduralen Figur (t = 0 Küken … 1 groß).
# Aufruf: python dcc_entwurf.py <zielordner>  → mongo_entwurf.png, tummy_entwurf.png
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

K = (24, 18, 30, 255)
W = (250, 248, 240, 255)
PUP = (30, 24, 36, 255)
MUND = (110, 26, 40, 255)
ZUNGE = (236, 100, 120, 255)

MONGO_PAL = {
    "A Dschungel": dict(D=(44, 88, 52), M=(76, 138, 70), L=(132, 190, 102), B=(206, 224, 156),
                        F=(226, 104, 40), F2=(250, 182, 60), G=(214, 136, 58), S=(30, 64, 40)),
    "B Wüste": dict(D=(128, 88, 50), M=(188, 138, 80), L=(230, 190, 122), B=(246, 226, 182),
                    F=(54, 66, 122), F2=(92, 146, 204), G=(176, 110, 60), S=(96, 58, 34)),
    "C Bonbon": dict(D=(106, 58, 138), M=(160, 100, 190), L=(212, 162, 232), B=(242, 212, 242),
                     F=(238, 86, 148), F2=(255, 204, 84), G=(236, 150, 90), S=(82, 42, 110)),
}
TUMMY_PAL = {
    "A Fleisch": dict(D=(146, 58, 44), M=(208, 108, 78), L=(240, 164, 126), S=(170, 74, 56), R=(230, 96, 80)),
    "B Rosa": dict(D=(196, 88, 110), M=(240, 140, 152), L=(255, 196, 196), S=(214, 108, 128), R=(255, 110, 130)),
    "C Lila": dict(D=(126, 78, 158), M=(176, 126, 204), L=(218, 184, 238), S=(150, 96, 184), R=(240, 120, 190)),
}


def c(p, k):
    v = p[k]
    return v if len(v) == 4 else (*v, 255)


def lerp(a, b, t):
    return a + (b - a) * t


def ell(d, cx, cy, rx, ry, farbe):
    d.ellipse([round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)], fill=farbe)


def outline(img, ohne=()):
    w, h = img.size
    px = img.load()
    out = img.copy()
    po = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] and px[nx, ny] not in ohne:
                        po[x, y] = K
                        break
    return out


def kette(punkte, schritte=60):
    """Catmull-Rom durch die Punkte, gleichmäßig abgetastet (Liste von (x, y, s∈0..1))."""
    pts = [punkte[0]] + list(punkte) + [punkte[-1]]
    roh = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(schritte):
            u = j / schritte
            u2, u3 = u * u, u * u * u
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
            roh.append((x, y))
    roh.append(punkte[-1])
    n = len(roh) - 1
    return [(x, y, i / n) for i, (x, y) in enumerate(roh)]


# ── Ei (für beide) ────────────────────────────────────────────────────────
def ei(schale, punkt, seed, gross=1.0, flecken=14):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (40, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 20, 40 - 12 * gross
    rx, ry = 9 * gross, 12 * gross
    ell(d, cx, cy, rx, ry, schale[0])
    ell(d, cx - 0.6, cy - 0.8, rx - 1, ry - 1.2, schale[1])
    for _ in range(flecken):
        a = rnd.uniform(0, 2 * math.pi)
        r = math.sqrt(rnd.uniform(0, 0.8))
        x, y = cx + math.cos(a) * r * (rx - 2), cy + math.sin(a) * r * (ry - 2)
        rr = rnd.choice((0.6, 1.0, 1.4))
        ell(d, x, y, rr, rr, punkt)
    ell(d, cx - rx * 0.45, cy - ry * 0.45, 1.6, 2.4, schale[2])
    d.point((round(cx - rx * 0.45), round(cy - ry * 0.55)), fill=W)
    return outline(img)


# ── Mongo ─────────────────────────────────────────────────────────────────
def mongo(stufe, p, pose="stehen", phase=0.0):
    t = (stufe - 1) / 5
    # Mark 15.11.: „wenn er läuft, etwas gebückter, damit er gefährlicher aussieht“.
    # Gebückt wächst mit: das Küken watschelt aufrecht, der Große duckt sich.
    lauf = pose == "laufen"
    gb = t if lauf else 0.0
    ph = 2 * math.pi * phase
    D, M, L, B, F, F2, G, S = (c(p, k) for k in "D M L B F F2 G S".split())
    img = Image.new("RGBA", (150, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = 62, 96  # Hüfte x, Boden y

    bein = lerp(4.5, 21, t)
    rk = lerp(6.8, 8.6, t)  # Rumpfdicke
    hip = (ox, oy - bein * (1 - 0.14 * gb) - rk * 0.45 + gb * 1.2 * abs(math.sin(ph)))
    w = math.radians(lerp(-62, -10, t) + gb * 14)
    lang = lerp(2.5, 19, t)
    sch = (hip[0] + math.cos(w) * lang, hip[1] + math.sin(w) * lang)
    wn = lerp(-82, -58, t) + gb * 34
    hl = lerp(3.5, 20, t)  # Mark 15.11.: Hals beim Großen länger und dünner
    w1, w2 = math.radians(wn - 28 * gb), math.radians(wn + 26 * gb)  # gebückt: S-Hals, Kopf vorgestreckt
    mitte = (sch[0] + math.cos(w1) * hl * 0.5, sch[1] + math.sin(w1) * hl * 0.5)
    hals = (mitte[0] + math.cos(w2) * hl * 0.5, mitte[1] + math.sin(w2) * hl * 0.5)
    kr = lerp(5.6, 5.8, t)
    kopf = (hals[0] + kr * 0.35, hals[1] - kr * 0.25)

    # Schwanz: nach hinten, beim Küken aufgestellter Bürzel
    # Mark 15.11.: Schwanz dünner und länger wie beim echten Raptor — lang, steif,
    # fast waagrecht, zur Spitze leicht ansteigend.
    sl = lerp(4, 60, t)
    sa = math.radians(lerp(-140, -178, t))
    s1 = (hip[0] + math.cos(sa) * sl * 0.5, hip[1] + math.sin(sa) * sl * 0.5 + lerp(0, 0.5, t))
    s2 = (hip[0] + math.cos(sa) * sl, hip[1] + math.sin(sa) * sl - lerp(0, 4, t))
    schwanz = kette([s2, s1, hip])
    rumpf = kette([hip, sch])
    halsk = kette([sch, mitte, hals])

    def r_schwanz(s):
        return lerp(lerp(2.2, 0.6, t), rk * lerp(0.85, 0.62, t), s ** lerp(0.8, 2.2, t))

    def r_rumpf(s):
        return lerp(rk, rk * lerp(0.95, 0.78, t), s)

    def r_hals(s):
        return lerp(rk * lerp(0.9, 0.5, t), kr * lerp(0.9, 0.46, t), s)

    def bein_malen(vorne):
        bx = hip[0] + (1.5 if vorne else -1.5)
        lp = ph + (0 if vorne else math.pi)
        schritt = lerp(1.5, 8, t) if lauf else 0.0
        off = math.sin(lp) * schritt
        hebt = max(0.0, math.cos(lp)) * lerp(1, 3.5, t) if lauf else 0.0
        knie = (bx + lerp(1.5, 4, t) + off * 0.3, hip[1] + bein * 0.45)
        knoechel = (bx - lerp(0.5, 4.5, t) + off * 0.8, hip[1] + bein * 0.8 * (1 - 0.1 * gb) - hebt * 0.7)
        fuss = (bx + lerp(0.5, 2, t) + off, oy - 1 - hebt)
        gf = G if vorne else tuple(max(0, v - 40) if i < 3 else v for i, v in enumerate(G))
        mf = M if vorne else D
        # Keule
        ell(d, (hip[0] + knie[0]) / 2 + (0 if vorne else -1), (hip[1] + knie[1]) / 2, lerp(2.4, 5, t), lerp(2.6, 5.4, t), D if vorne else S)
        ell(d, (hip[0] + knie[0]) / 2 - 0.5, (hip[1] + knie[1]) / 2 - 0.7, lerp(1.8, 4, t), lerp(2, 4.4, t), mf)
        breit = 1 if t < 0.5 else 2
        d.line([knie, knoechel], fill=gf, width=breit)
        d.line([knoechel, fuss], fill=gf, width=breit)
        zl = lerp(4.5, 6, t)  # Küken: lächerlich große Füße
        d.line([(fuss[0] - 1, fuss[1]), (fuss[0] + zl, fuss[1])], fill=gf, width=1)
        d.line([(fuss[0], fuss[1]), (fuss[0] + zl * 0.7, fuss[1] - 1)], fill=gf, width=1)
        d.line([(fuss[0] - 1, fuss[1]), (fuss[0] - 2.5, fuss[1])], fill=gf, width=1)
        if t >= 0.4:  # Sichelkralle
            d.line([(fuss[0] + 1, fuss[1] - 1), (fuss[0] + 2, fuss[1] - 3), (fuss[0] + 3.5, fuss[1] - 3)], fill=W)

    def arm_malen(vorne):
        a0 = (sch[0] + (0.5 if vorne else -0.5), sch[1] + rk * 0.35)
        if t < 0.2:  # Küken: Flügelstummel am Körper
            ell(d, hip[0] + 1, hip[1] - 1, 3, 2.2, D if vorne else S)
            ell(d, hip[0] + 0.5, hip[1] - 1.6, 2.4, 1.6, L if vorne else M)
            return
        ell_ = (a0[0] + lerp(1, 3, t), a0[1] + lerp(2, 5, t))
        hand = (ell_[0] + lerp(1, 4, t), ell_[1] + lerp(0.5, 1.5, t))
        fl = lerp(1.5, 8, t)
        d.polygon([a0, ell_, hand, (hand[0] - 1, hand[1] + fl * 0.6), (ell_[0] - 1.5, ell_[1] + fl), (a0[0] - 2, a0[1] + fl * 0.7)],
                  fill=F if vorne else tuple(max(0, v - 50) if i < 3 else v for i, v in enumerate(F)))
        if t >= 0.4:  # gefaltete Flügelfedern hängen unter dem Arm, Spitzen gezackt
            fd = tuple(max(0, v - 30) if i < 3 else v for i, v in enumerate(F if vorne else D))
            for k in range(int(lerp(2, 6, t))):
                fx = ell_[0] - 1.5 + k * 1.1
                d.line([(fx, ell_[1]), (fx - 1, ell_[1] + fl * (0.9 + 0.12 * (k % 2)))], fill=fd, width=1)
        d.line([a0, ell_, hand], fill=M if vorne else D, width=2 if t > 0.5 else 1)
        if t >= 0.4:  # Krallen
            d.line([(hand[0] + 1, hand[1]), (hand[0] + 2, hand[1] + 2)], fill=W)
        d.point((round(hand[0] + 1), round(hand[1])), fill=W)

    bein_malen(False)
    arm_malen(False)

    teile = [(schwanz, r_schwanz), (rumpf, r_rumpf), (halsk, r_hals)]
    for pk, rf in teile:
        for x, y, s in pk:
            ell(d, x, y + 0.4, rf(s), rf(s), D)
    for pk, rf in teile:
        for x, y, s in pk:
            r = max(0.0, rf(s) - 0.9)
            ell(d, x - 0.3, y - 0.6 * min(1.0, rf(s) / 2), r, r, M)
    # Bauch
    # Bauch: beim Großen nur ein schmaler heller Streifen unten, der Rücken dominiert
    bh = lerp(0.42, 0.3, t)
    for pk, rf, an in ((rumpf, r_rumpf, True), (halsk, r_hals, True), (schwanz, r_schwanz, False)):
        if not an:
            continue
        for x, y, s in pk:
            r = rf(s)
            ell(d, x + r * 0.15, y + r * lerp(0.45, 0.6, t), r * 0.62, r * bh, B)
    # Rückenstreifen und Rückenfedern
    if t >= 0.2:
        alle = schwanz + rumpf
        for i in range(8, len(alle), 9):
            x, y, s = alle[i]
            r = r_schwanz(s) if i < len(schwanz) else r_rumpf(s)
            d.line([(x - 0.5, y - r * 0.9), (x + 1, y - r * 0.2)], fill=S, width=1)
        for i in range(4, len(rumpf), 12):
            x, y, s = rumpf[i]
            r = r_rumpf(s)
            hl_ = lerp(1, 3, t)
            d.line([(x, y - r + 0.5), (x - hl_, y - r - hl_ * 0.6)], fill=F, width=1)
    # Halsfedern (Mähne) ab der Mitte
    if t >= 0.4:
        for i in range(6, len(halsk), 10):
            x, y, s = halsk[i]
            r = r_hals(s)
            hl_ = lerp(1.5, 4, t)
            d.line([(x - r * 0.6, y - r * 0.5), (x - r * 0.6 - hl_, y - r * 0.2 + hl_ * 0.3)], fill=F2 if i % 20 < 10 else F, width=1)
    # Küken-Flaum
    if t < 0.5:
        rnd = random.Random(7)
        for _ in range(int(lerp(16, 0, t * 2))):
            a = rnd.uniform(-math.pi * 1.1, 0.15)
            x = hip[0] + math.cos(a) * (rk + 0.3)
            y = hip[1] - 1 + math.sin(a) * (rk + 0.3)
            ell(d, x, y, 1.2, 1.2, L)
    # Federsaum am hinteren Schwanzdrittel (statt Fächer, wie beim echten Raptor)
    if t >= 0.35:
        fl = lerp(1, 3.5, (t - 0.35) / 0.65)
        ende = int(len(schwanz) * 0.4)
        for i in range(2, ende, 5):
            x, y, s_ = schwanz[i]
            r = r_schwanz(s_)
            farbe = D if (i // 5) % 2 else S
            d.line([(x + 0.5, y - r), (x - fl, y - r - fl * 0.5)], fill=farbe, width=1)
            d.line([(x + 0.5, y + r), (x - fl, y + r + fl * 0.4)], fill=farbe, width=1)
        x, y, _ = schwanz[0]
        d.line([(x, y), (x - fl * 1.3, y - 0.5)], fill=F, width=1)

    # Kopf
    kx, ky = kopf
    offen = pose == "kreischen"
    sn = lerp(1.6, 11, t)
    if offen:  # Unterkiefer klappt runter
        uk = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ud = ImageDraw.Draw(uk)
        ell(ud, kx + kr * 0.5 + sn * 0.45, ky + kr * 0.55, sn * 0.55 + 1.5, 1.6, D)
        ell(ud, kx + kr * 0.5 + sn * 0.45, ky + kr * 0.5, sn * 0.55 + 1.2, 1.2, M)
        uk = uk.rotate(-28, resample=Image.NEAREST, center=(kx + kr * 0.2, ky + kr * 0.4))
        ell(d, kx + kr * 0.55 + sn * 0.3, ky + kr * 0.55, sn * 0.45 + 1.5, 2.2, MUND)
        img.alpha_composite(uk)
        d = ImageDraw.Draw(img)
    ell(d, kx, ky + 0.4, kr, kr * 0.95, D)
    ell(d, kx - 0.3, ky - 0.4, kr - 0.9, kr * 0.95 - 0.9, M)
    # Schnauze
    sx = kx + kr * 0.55 + sn * 0.5
    sy = ky + kr * lerp(0.15, 0.2, t)
    ell(d, sx, sy + 0.3, sn * 0.55 + 1.6, lerp(2.4, 2.9, t), D)
    ell(d, sx - 0.3, sy - 0.2, sn * 0.55 + 1.0, lerp(1.9, 2.2, t), M)
    if not offen:
        d.line([(kx + kr * 0.2, sy + lerp(1.6, 2.2, t)), (sx + sn * 0.5 + 1, sy + lerp(1.2, 1.6, t))], fill=K)
        zaehne = 1 if t < 0.3 else int(lerp(1, 5, t))
        for k in range(zaehne):
            zx = sx + sn * 0.45 - k * 2.2
            d.point((round(zx), round(sy + lerp(2.6, 2.6, t))), fill=W)
    else:
        for k in range(int(lerp(1, 5, t))):
            d.point((round(sx + sn * 0.45 - k * 2.2), round(sy + 2)), fill=W)
    d.point((round(sx + sn * 0.45), round(sy - 1)), fill=K)  # Nasenloch
    # Auge
    ar = lerp(2.7, 1.7, t)
    ax, ay = kx + kr * 0.1, ky - kr * 0.22
    ell(d, ax, ay, ar, ar + 0.3, W)
    d.rectangle([round(ax + ar * 0.2), round(ay - ar * 0.5), round(ax + ar * 0.2 + max(1, ar * 0.7)), round(ay + ar * 0.5)], fill=PUP)
    d.point((round(ax + ar * 0.2), round(ay - ar * 0.5)), fill=W)
    if t >= 0.4:  # Brauenwulst: frech statt böse
        d.line([(ax - ar, ay - ar - 0.5), (ax + ar + 1, ay - ar + 0.5)], fill=S, width=1)
    # Kamm
    n = int(lerp(1, 4, t)) + (1 if offen else 0)
    for k in range(n):
        bx = kx - kr * 0.2 - k * 1.6
        by = ky - kr * 0.75 + k * 0.6
        hl_ = lerp(2.5, 7.5, t) * (1 - k * 0.12) * (1.35 if offen else 1)
        wk = math.radians(lerp(-120, -150, t) - k * 14 - (15 if offen else 0))
        d.line([(bx, by), (bx + math.cos(wk) * hl_, by + math.sin(wk) * hl_)], fill=F if k % 2 == 0 else F2, width=2 if t > 0.5 else 1)

    bein_malen(True)
    arm_malen(True)
    return outline(img)


# ── Tummy-Acher ───────────────────────────────────────────────────────────
def tummy(stufe, p, pose="stehen"):
    """Mark 15.11. (Buchcover): seltsamer Fleischklops mit Dellen, Glubschaugen
    (ungleich groß, stehen über den Umriss), breites Grinsen mit EINEM Zahn,
    keine Arme, zwei Stummelbeine. Süß bleibt er trotzdem."""
    t = (stufe - 1) / 5
    D, M, L, S, R = (c(p, k) for k in "D M L S R".split())
    img = Image.new("RGBA", (110, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = 50, 86
    r = lerp(7, 21, t)
    bl = lerp(3, 6, t)
    platt = pose == "platt"
    rx, ry = (r * 1.5, r * 0.58) if platt else (r * 1.05, r * 0.95)
    if platt:
        bl = 0.5
    cx, cy = ox, oy - bl - ry * 0.95

    # Stummelbeine (hinten zuerst)
    for vorne, dx in ((False, -r * 0.4), (True, r * 0.15)):
        fx = cx + dx
        farbe = D if vorne else S
        bb = lerp(1.6, 3.4, t)
        if not platt:
            d.rectangle([round(fx - bb), round(cy + ry * 0.6), round(fx + bb), round(oy - 1)], fill=farbe)
        ell(d, fx + bb * 0.6, oy - 1.2, bb + 1.4, 1.4, farbe)

    # Klumpiger Körper: Grundellipse plus feste Beulen
    beulen = [(-2.5, 0.78, 0.42), (-1.75, 0.82, 0.4), (-1.0, 0.8, 0.36), (-0.25, 0.74, 0.38),
              (0.7, 0.7, 0.4), (2.35, 0.74, 0.4), (3.0, 0.6, 0.44), (1.6, 0.62, 0.42)]
    formen = [(cx, cy, rx * 0.9, ry * 0.9)]
    for a, dist, gr in beulen:
        formen.append((cx + math.cos(a) * rx * dist * 0.62, cy + math.sin(a) * ry * dist * 0.62,
                       r * gr * (1.35 if platt else 1), r * gr * (0.75 if platt else 1)))
    for x, y, a, b in formen:
        ell(d, x, y + 0.6, a, b, D)
    for x, y, a, b in formen:
        ell(d, x - 0.5, y - 0.7, max(0.0, a - 1), max(0.0, b - 1), M)
    # Schatten unten, Glanz oben links
    ell(d, cx + rx * 0.05, cy + ry * 0.7, rx * 0.6, ry * 0.15, S)
    ell(d, cx - rx * 0.42, cy - ry * 0.48, max(1.2, rx * 0.2), max(1.0, ry * 0.13), L)
    d.point((round(cx - rx * 0.46), round(cy - ry * 0.52)), fill=W)
    # Dellen: dunkle Mulde, heller Rand unten
    rnd = random.Random(11)
    for _ in range(int(lerp(3, 10, t))):
        a = rnd.uniform(-math.pi * 0.98, -0.1) if rnd.random() < 0.75 else rnd.uniform(2.2, 3.1)
        rr = rnd.uniform(0.3, 0.78)
        x, y = cx - rx * 0.2 + math.cos(a) * rr * rx * 0.8, cy + math.sin(a) * rr * ry * 0.8
        g = rnd.choice((0.9, 1.3, 1.8)) * lerp(0.75, 1.35, t)
        ell(d, x + 0.4, y + 0.6, g + 0.3, g * 0.75, L)
        ell(d, x, y, g, g * 0.7, S)
    # Sprenkel
    for _ in range(int(lerp(4, 14, t))):
        a = rnd.uniform(-math.pi, math.pi)
        rr = math.sqrt(rnd.uniform(0, 0.75))
        d.point((round(cx + math.cos(a) * rr * rx), round(cy + math.sin(a) * rr * ry)), fill=D)

    # Glubschaugen: ungleich groß, stehen über den Umriss
    weiss = (246, 236, 230, 255)
    iris = (84, 156, 214, 255)
    ader = (226, 150, 150, 255)
    ea = lerp(3.0, 6.2, t)
    augen = [(cx + rx * 0.08, cy - ry * 0.52, ea), (cx + rx * 0.78, cy - ry * 0.3, ea * 0.82)]
    if platt:
        augen = [(cx + rx * 0.05, cy - ry * 0.95, ea), (cx + rx * 0.6, cy - ry * 0.85, ea * 0.82)]
    for k, (ax, ay, e) in enumerate(augen):
        ell(d, ax, ay + 0.5, e + 1, e + 0.8, D)  # Lid-Wulst
        ell(d, ax, ay, e, e, weiss)
        if e > 4:
            d.line([(ax - e * 0.8, ay + e * 0.1), (ax - e * 0.45, ay + e * 0.2)], fill=ader)
        if platt:
            ix, iy = ax + (0.6 if k else -0.6), ay + 0.3  # schielt nach dem Plumps
        else:
            ix, iy = ax + e * 0.22, ay + e * 0.05
        ell(d, ix, iy, e * 0.56, e * 0.56, iris)
        ell(d, ix, iy, e * 0.27, e * 0.27, PUP)
        d.point((round(ix - e * 0.25), round(iy - e * 0.3)), fill=W)

    # Breites Grinsen mit EINEM Zahn (unten, steht hoch)
    mx0, mx1 = cx - rx * 0.12, cx + rx * 0.9
    my = cy + ry * (0.05 if platt else 0.12)
    mh = lerp(2.2, 6.0, t) * (1.9 if pose == "maul" else (0.45 if platt else 1))
    d.pieslice([round(mx0), round(my - mh), round(mx1), round(my + mh)], 0, 180, fill=MUND)
    d.line([(mx0, my), (mx1, my)], fill=K)
    if pose == "maul" or (not platt and t > 0.3):
        ell(d, (mx0 + mx1) / 2 + rx * 0.1, my + mh * 0.68, (mx1 - mx0) * 0.2, max(0.6, mh * 0.25), ZUNGE)
    zh = lerp(1.6, 4.2, t) * (0.7 if platt else 1)
    zx = mx0 + (mx1 - mx0) * 0.3
    zb = lerp(1.0, 2.0, t)
    d.polygon([(zx - zb, my + mh * 0.75), (zx + zb, my + mh * 0.75), (zx + zb * 0.4, my + mh * 0.75 - zh)], fill=W)
    return outline(img)


# ── Tafel ─────────────────────────────────────────────────────────────────
def schrift(groesse):
    for name in ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(name):
            return ImageFont.truetype(name, groesse)
    return ImageFont.load_default()


def tafel(titel, zeilen, spalten, ziel):
    """zeilen: [(label, [img, …])]; alle Bilder bodenbündig."""
    zuschnitt = []
    for label, bilder in zeilen:
        reihe = []
        for b in bilder:
            bb = b.getbbox()
            reihe.append(b.crop((bb[0], bb[1], bb[2], b.height)))
        zuschnitt.append((label, reihe))
    luecke = 8
    breite = max(sum(b.width for b in r) + luecke * (len(r) - 1) for _, r in zuschnitt)
    s = max(2, min(5, 1240 // breite))
    hoehen = [max(b.height for b in r) for _, r in zuschnitt]
    rand, kopf, lab = 24, 46, 22
    H = kopf + sum(h * s + lab + 18 for h in hoehen) + rand
    Wd = breite * s + rand * 2
    bild = Image.new("RGB", (Wd, H), (24, 26, 36))
    d = ImageDraw.Draw(bild)
    d.text((rand, 12), titel, fill=(220, 220, 230), font=schrift(22))
    y = kopf
    f = schrift(14)
    for (label, reihe), h in zip(zuschnitt, hoehen):
        d.text((rand, y), label, fill=(150, 160, 180), font=f)
        x = rand
        for i, b in enumerate(reihe):
            gross = b.resize((b.width * s, b.height * s), Image.NEAREST)
            bild.paste(gross, (x, y + lab + (h - b.height) * s), gross)
            if spalten and i < len(spalten):
                d.text((x, y + lab + h * s + 2), spalten[i], fill=(110, 116, 136), font=schrift(12))
            x += (b.width + luecke) * s
        y += h * s + lab + 18
    bild.save(ziel)
    return ziel


def main(ziel):
    os.makedirs(ziel, exist_ok=True)
    spalten = ["Ei", "1", "2", "3", "4", "5", "6"]
    eifarben = {
        "A Dschungel": ((150, 170, 120), (206, 222, 176), (236, 244, 220)),
        "B Wüste": ((180, 160, 120), (232, 216, 180), (250, 242, 222)),
        "C Bonbon": ((180, 150, 200), (230, 212, 240), (248, 240, 252)),
    }
    zeilen = []
    for name, p in MONGO_PAL.items():
        e = ei(eifarben[name], c(p, "S"), seed=3, gross=0.9)
        zeilen.append((f"Mongo {name}", [e] + [mongo(s, p) for s in range(1, 7)] + [mongo(6, p, "kreischen")]))
    tafel("MONGO (Mongoliensis) – Entwurf: Ei + 6 Schritte, rechts Kreischen", zeilen, spalten + ["schrei"], os.path.join(ziel, "mongo_entwurf.png"))

    zeilen = []
    for name, p in TUMMY_PAL.items():
        e = ei((c(p, "D"), c(p, "M"), c(p, "L")), c(p, "R"), seed=5, gross=0.85, flecken=8)
        zeilen.append((f"Tummy-Acher {name}", [e] + [tummy(s, p) for s in range(1, 7)] + [tummy(4, p, "maul"), tummy(4, p, "platt")]))
    tafel("TUMMY-ACHER – Entwurf: Ei + 6 Schritte, rechts Maul auf / plattgedrückt", zeilen, spalten + ["mampf", "platt"], os.path.join(ziel, "tummy_entwurf.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
