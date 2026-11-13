# ENTWURF 13.11.2026 (noch nicht von Mark abgenommen, noch nicht im Frontend)
# KI-Begleiter als Pet (Mark, 13.11.2026): „Datenwolke oder cooles, Licht
# pulsierendes, manchmal verschiedene Formen oder Gestalten annehmendes Wesen …
# ein Begleiter, der wachsen kann“.
# Drei Entwürfe derselben Idee, je fünf Wachstumsstufen, dazu die Gestalten,
# die sie annehmen, und Farbvarianten. Nur Aussehen, keine Animationen.
# Aufruf: python ki_entwurf.py <zielordner>   → ki_wachstum.png, ki_gestalten.png, ki_morph.gif
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

G = 56                      # Zelle in Sprite-Pixeln
SC = 4                      # Vergrößerung der Tafel
BG = (14, 16, 26, 255)

PALETTEN = {
    "cyan":      dict(kern=(255, 255, 255), hell=(170, 245, 255), mittel=(60, 200, 245), dunkel=(34, 112, 205), tief=(22, 58, 128), akzent=(255, 90, 200)),
    "magenta":   dict(kern=(255, 255, 255), hell=(255, 190, 245), mittel=(245, 90, 215), dunkel=(170, 50, 170), tief=(90, 28, 110), akzent=(90, 230, 255)),
    "gruen":     dict(kern=(255, 255, 255), hell=(200, 255, 190), mittel=(80, 235, 120), dunkel=(30, 150, 80), tief=(16, 80, 50), akzent=(255, 220, 90)),
    "bernstein": dict(kern=(255, 255, 255), hell=(255, 236, 170), mittel=(255, 180, 60), dunkel=(205, 105, 30), tief=(120, 55, 20), akzent=(120, 220, 255)),
}
AUGE = (10, 18, 44, 255)


def farbe(pal, k):
    c = pal[k] if isinstance(k, str) else k
    return (*c[:3], 255)


def px(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)


def scheibe(img, cx, cy, r, c, raster=False):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and (not raster or (x + y) % 2 == 0):
                px(img, x, y, c)


ZIFFERN = {"0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"]}


def ziffer(img, x, y, z, c):
    for j, zeile in enumerate(ZIFFERN[z]):
        for i, ch in enumerate(zeile):
            if ch == "#":
                px(img, x + i, y + j, c)


# ── A · Datenwolke: ein Schwarm aus Datenpunkten mit Augen ────────────────

A_STUFEN = [  # Punkte, Radius, Augen, Verbindungen, Ziffern, Umlaufbahn
    dict(n=5, r=3.0, augen=False, netz=False, ziffern=0, bahn=False),
    dict(n=14, r=6.0, augen=True, netz=False, ziffern=0, bahn=False),
    dict(n=28, r=9.0, augen=True, netz=True, ziffern=0, bahn=False),
    dict(n=46, r=12.5, augen=True, netz=True, ziffern=3, bahn=False),
    dict(n=70, r=15.5, augen=True, netz=True, ziffern=5, bahn=True),
]


def wolke_punkte(st, seed=7):
    """Punkte in Wolkenform (drei Kreise), Koordinaten relativ zur Mitte."""
    z = random.Random(seed)
    r = st["r"]
    kreise = [(0, -r * 0.2, r * 0.72), (-r * 0.7, r * 0.2, r * 0.48), (r * 0.7, r * 0.2, r * 0.48)]
    punkte = []
    while len(punkte) < st["n"]:
        x, y = z.uniform(-r * 1.25, r * 1.25), z.uniform(-r, r)
        if any((x - kx) ** 2 + (y - ky) ** 2 <= kr * kr for kx, ky, kr in kreise):
            d = math.hypot(x * 0.85, y * 1.2) / r
            punkte.append(dict(x=x, y=y, d=d, gross=z.random() < 0.3 and d < 0.8))
    return punkte


def punkt_farbe(pal, d):
    return farbe(pal, "kern" if d < 0 else "hell" if d < 0.38 else "mittel" if d < 0.72 else "dunkel")


def wolke(pal, stufe, cx=G / 2, cy=G / 2, puls=0.0, punkte=None, augen_zu=False):
    st = A_STUFEN[stufe]
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = punkte if punkte is not None else wolke_punkte(st)
    k = 1 + puls * 0.12
    pos = [(cx + p["x"] * k, cy + p["y"] * k) for p in pts]
    if st["bahn"]:
        for i in range(40):  # hintere Hälfte der Umlaufbahn
            t = math.pi + i / 40 * math.pi
            if i % 2 == 0:
                px(img, cx + math.cos(t) * (st["r"] + 7), cy + 2 + math.sin(t) * 4.5, farbe(pal, "tief"))
    if st["netz"]:
        for i, (x, y) in enumerate(pos):
            nah = sorted(((math.hypot(x - a, y - b), j) for j, (a, b) in enumerate(pos) if j != i))[:2]
            for dist, j in nah:
                if dist < 6.5:
                    d.line([(x, y), pos[j]], fill=farbe(pal, "tief"))
    if stufe >= 1:  # dichter Kern, in dem die Augen sitzen
        kr = st["r"] * 0.42
        scheibe(img, cx, cy, kr + 1, farbe(pal, "dunkel"), raster=True)
        scheibe(img, cx, cy, kr, farbe(pal, "mittel"))
        scheibe(img, cx, cy - 0.5, kr - 1, farbe(pal, "hell"))
    for p, (x, y) in zip(pts, pos):
        c = punkt_farbe(pal, p["d"])
        px(img, x, y, c)
        if p["gross"]:
            px(img, x + 1, y, c), px(img, x, y + 1, c), px(img, x + 1, y + 1, c)
    if stufe == 0:
        px(img, cx, cy, farbe(pal, "kern"))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px(img, cx + dx, cy + dy, farbe(pal, "hell"))
    z = random.Random(40 + stufe)
    for i in range(st["ziffern"]):
        w = -2.6 + i * 5.2 / max(1, st["ziffern"] - 1) if st["ziffern"] > 1 else 0
        zx = cx + math.sin(w) * (st["r"] + 3) - 1
        zy = cy - math.cos(w) * (st["r"] * 0.9 + 2) - 2
        ziffer(img, zx, zy, z.choice("01"), farbe(pal, "dunkel" if i % 2 else "mittel"))
    if st["augen"]:
        ab = 1 if stufe == 1 else 2 if stufe < 4 else 3
        for s in (-1, 1):
            ex = cx + s * ab - (0 if s > 0 else 1)
            if augen_zu:
                px(img, ex, cy, AUGE), px(img, ex + (1 if stufe >= 3 else 0), cy, AUGE)
            else:
                px(img, ex, cy - 1, AUGE), px(img, ex, cy, AUGE)
                if stufe >= 3:
                    px(img, ex + 1, cy - 1, AUGE), px(img, ex + 1, cy, AUGE)
    if st["bahn"]:
        for i in range(40):  # vordere Hälfte
            t = i / 40 * math.pi
            if i % 2 == 0:
                px(img, cx + math.cos(t) * (st["r"] + 7), cy + 2 + math.sin(t) * 4.5, farbe(pal, "mittel"))
        sx, sy = cx + math.cos(0.9) * (st["r"] + 7), cy + 2 + math.sin(0.9) * 4.5
        scheibe(img, sx, sy, 1.2, farbe(pal, "akzent"))
        px(img, sx, sy, farbe(pal, "kern"))
    return img


# ── B · Lichtkern: pulsierende Kugel mit Ringen ───────────────────────────

B_STUFEN = [  # Kernradius, Strahlen, Ringe (rx-Zuschlag, ry, Neigung°)
    dict(rc=1.0, strahl=2, ringe=[]),
    dict(rc=2.2, strahl=3, ringe=[]),
    dict(rc=3.2, strahl=4, ringe=[(7, 2.6, -18)]),
    dict(rc=4.2, strahl=5, ringe=[(8, 3.0, -38), (8, 3.0, 38)]),
    dict(rc=5.2, strahl=6, ringe=[(15, 4.6, 0), (12, 3.6, 62), (12, 3.6, -62)]),
]


def ring(img, pal, cx, cy, rx, ry, grad, vorn, sat):
    w = math.radians(grad)
    n = int(rx * 8)
    for i in range(n):
        t = i / n * 2 * math.pi
        ist_vorn = math.sin(t) > 0
        if ist_vorn != vorn:
            continue
        x, y = rx * math.cos(t), ry * math.sin(t)
        X, Y = cx + x * math.cos(w) - y * math.sin(w), cy + x * math.sin(w) + y * math.cos(w)
        if vorn or i % 2 == 0:  # hinten nur gepunktet
            px(img, X, Y, farbe(pal, "mittel" if vorn else "dunkel"))
    if vorn and sat is not None:
        x, y = rx * math.cos(sat), ry * math.sin(sat)
        X, Y = cx + x * math.cos(w) - y * math.sin(w), cy + x * math.sin(w) + y * math.cos(w)
        scheibe(img, X, Y, 1.2, farbe(pal, "akzent"))
        px(img, X, Y, farbe(pal, "kern"))


def kern(pal, stufe, cx=G / 2, cy=G / 2, puls=0.0):
    st = B_STUFEN[stufe]
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    rc = st["rc"]
    for i, (zx, ry, grad) in enumerate(st["ringe"]):
        ring(img, pal, cx, cy, rc + zx, ry, grad, False, None)
    hof = rc + 3.5 + puls * 1.5
    scheibe(img, cx, cy, hof, farbe(pal, "tief"), raster=True)
    scheibe(img, cx, cy, rc + 2.0 + puls, farbe(pal, "dunkel"))
    scheibe(img, cx, cy, rc + 1.0, farbe(pal, "mittel"))
    scheibe(img, cx, cy, rc, farbe(pal, "hell"))
    scheibe(img, cx - 0.4, cy - 0.4, max(0.5, rc - 1.2), farbe(pal, "kern"))
    L = st["strahl"]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(int(rc + 3), int(rc + 3 + L)):
            if k < rc + 3 + L - 2 or (k - int(rc + 3 + L)) % 2:
                px(img, cx + dx * k, cy + dy * k, farbe(pal, "hell" if k < rc + 3 + L / 2 else "mittel"))
    if stufe >= 4:  # kurze Diagonalstrahlen: Krone
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            for k in range(7, 9):
                px(img, cx + dx * k, cy + dy * k, farbe(pal, "mittel"))
    if stufe >= 1:
        ab = 1 if stufe < 3 else 2
        for s in (-1, 1):
            ex = cx + s * ab - (0 if s > 0 else 1)
            px(img, ex, cy, AUGE)
            if stufe >= 2:
                px(img, ex, cy - 1, AUGE)
    for i, (zx, ry, grad) in enumerate(st["ringe"]):
        ring(img, pal, cx, cy, rc + zx, ry, grad, True, 0.7 + i * 1.3 if stufe >= 3 else None)
    return img


# ── C · Glitch-Geist: Hologramm-Gestalt aus Bildzeilen ────────────────────

C_STUFEN = [  # Höhe, Breite, Augen, Hände, Reif, Splitter
    dict(h=5, w=4, augen=False, haende=False, reif=False, splitter=0),
    dict(h=11, w=8, augen=True, haende=False, reif=False, splitter=0),
    dict(h=17, w=11, augen=True, haende=False, reif=False, splitter=2),
    dict(h=23, w=13, augen=True, haende=True, reif=False, splitter=3),
    dict(h=30, w=15, augen=True, haende=True, reif=True, splitter=5),
]


def geist_halbbreite(st, y):
    """Halbe Breite in Zeile y (0 = Scheitel): runder Kopf, dann schmaler Schweif."""
    h, w = st["h"], st["w"]
    kopf = w / 2
    if y <= kopf * 1.5:
        dy = (y - kopf) / kopf
        return kopf * math.sqrt(max(0.0, 1 - min(1.0, dy * dy))) if y < kopf else kopf
    t = (y - kopf * 1.5) / max(1.0, h - kopf * 1.5)
    return max(0.6, kopf * (1 - t) ** 1.4 + math.sin(t * 7) * 0.8 * (1 - t))


def geist(pal, stufe, cx=G / 2, cy=G / 2, glitch=(0.33, 0.62)):
    st = C_STUFEN[stufe]
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    h = st["h"]
    oben = int(cy - h / 2)
    weit = 1 if stufe < 2 else 2
    versatz = {int(h * g): (weit if i % 2 == 0 else -weit) for i, g in enumerate(glitch)} if stufe >= 1 else {}
    for y in range(h):
        hb = geist_halbbreite(st, y)
        schweif = (y / h) ** 2 * 3 * math.sin(y * 0.55)  # Schweif schwingt zur Seite
        mx = cx + schweif + versatz.get(y, 0)
        l, r = int(round(mx - hb)), int(round(mx + hb))
        for x in range(l, r + 1):
            rand = x in (l, r) or y == 0
            if rand:
                c = farbe(pal, "hell")
            else:
                c = farbe(pal, "mittel" if y % 2 == 0 else "dunkel")
            if y > h * 0.75 and (x + y) % 2:  # löst sich unten in Pixel auf
                continue
            px(img, x, oben + y, c)
        if y in versatz:  # Farbsaum an der verrutschten Zeile
            px(img, (r + 1) if versatz[y] > 0 else (l - 1), oben + y, farbe(pal, "akzent"))
    z = random.Random(90 + stufe)
    for _ in range(2 + stufe):  # fallende Pixel
        px(img, cx + z.uniform(-st["w"] / 2, st["w"] / 2), oben + h + z.uniform(0, 4), farbe(pal, "dunkel"))
    if stufe == 0:
        px(img, cx, oben + 1, farbe(pal, "kern")), px(img, cx - 1, oben + 2, farbe(pal, "kern"))
    if st["augen"]:
        ay = oben + int(st["w"] / 2) - (0 if stufe > 1 else 1)
        ab = max(1, st["w"] // 4)
        if stufe >= 2:  # dunkles Visier
            for x in range(int(cx - st["w"] / 2 + 2), int(cx + st["w"] / 2 - 1)):
                px(img, x, ay, farbe(pal, "tief")), px(img, x, ay + 1, farbe(pal, "tief"))
        for s in (-1, 1):
            ex = cx + s * ab - (0 if s > 0 else 1)
            px(img, ex, ay, farbe(pal, "kern"))
            if stufe >= 2:
                px(img, ex, ay + 1, farbe(pal, "kern"))
            if stufe >= 3:
                px(img, ex + (1 if s < 0 else -1), ay, farbe(pal, "kern")), px(img, ex + (1 if s < 0 else -1), ay + 1, farbe(pal, "kern"))
    if st["haende"]:
        hy = oben + int(h * 0.52)
        for s in (-1, 1):
            hx = cx + s * (st["w"] / 2 + 4)
            for j in range(3):
                for i in range(3):
                    if (i, j) not in ((0, 0), (2, 0), (0, 2), (2, 2)) or (stufe == 4 and j < 2):
                        px(img, hx - 1 + i, hy + j + (1 if s > 0 else 0), farbe(pal, "hell" if j == 0 else "mittel"))
    if st["reif"]:
        for i in range(36):
            t = i / 36 * 2 * math.pi
            px(img, cx + math.cos(t) * 6, oben - 4 + math.sin(t) * 1.6, farbe(pal, "hell" if math.sin(t) > 0 else "mittel"))
    for i in range(st["splitter"]):
        w = z.uniform(0, 2 * math.pi)
        sx, sy = cx + math.cos(w) * (st["w"] / 2 + 7 + z.uniform(0, 3)), cy + math.sin(w) * (h / 2 - 2)
        c = farbe(pal, "akzent" if i == 0 else "mittel")
        px(img, sx, sy, c), px(img, sx + 1, sy, c), px(img, sx, sy + 1, farbe(pal, "dunkel"))
    return img


# ── Gestalten, die sie annehmen ───────────────────────────────────────────

GESTALTEN = {
    "Katze": [
        "#.........#",
        "##.......##",
        "###.....###",
        "###########",
        "###########",
        "##o#####o##",
        "##o#####o##",
        "###########",
        "#####o#####",
        ".#########.",
        "..#######..",
    ],
    "Totenkopf": [
        "..#######..",
        ".#########.",
        "###########",
        "###########",
        "#oo#####oo#",
        "#oo#####oo#",
        "#####o#####",
        ".#########.",
        "..#######..",
        "..#.#.#.#..",
        "..#.#.#.#..",
    ],
    "Herz": [
        ".###...###.",
        "#####.#####",
        "###########",
        "###########",
        "###########",
        ".#########.",
        "..#######..",
        "...#####...",
        "....###....",
        ".....#.....",
    ],
    "Schlüssel": [
        ".###.........",
        "#####........",
        "##o##########",
        "##o##########",
        "#####...#.##.",
        ".###....#.##.",
    ],
    "Pfeil": [
        "......#......",
        "......##.....",
        "#########....",
        "##########...",
        "###########..",
        "##########...",
        "#########....",
        "......##.....",
        "......#......",
    ],
    "Warnung": [
        ".....#.....",
        "....###....",
        "....###....",
        "...##o##...",
        "...##o##...",
        "..###o###..",
        "..#######..",
        ".####o####.",
        ".#########.",
        "###########",
    ],
}


def _zelle(maske, i, j):
    return maske[j][i] if 0 <= j < len(maske) and 0 <= i < len(maske[j]) else "."


def gestalt_punkte(maske, seed=3):
    """Zielpunkte (relativ zur Mitte) für den Schwarm: Rand dicht und hell, innen locker."""
    z = random.Random(seed)
    hh, ww = len(maske), max(len(m) for m in maske)
    pts = []
    for j in range(hh):
        for i in range(ww):
            if _zelle(maske, i, j) == "o":  # Augen/Löcher glühen weiß
                pts += [dict(x=i * 2 + a - ww, y=j * 2 + b - hh, d=-1.0, gross=False) for a in range(2) for b in range(2)]
            if _zelle(maske, i, j) != "#":
                continue
            rand = any(_zelle(maske, i + a, j + b) != "#" for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            for a in range(2):
                for b in range(2):
                    if rand or z.random() < 0.5:
                        pts.append(dict(x=i * 2 + a - ww, y=j * 2 + b - hh, d=0.5 if rand else 0.9, gross=False))
    return pts


def gestalt(pal, stil, maske, cx=G / 2, cy=G / 2):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    hh, ww = len(maske), max(len(m) for m in maske)
    x0, y0 = int(cx - ww), int(cy - hh)
    if stil == "A":
        for p in gestalt_punkte(maske):
            px(img, cx + p["x"], cy + p["y"], punkt_farbe(pal, p["d"]))
        z = random.Random(5)
        for _ in range(12):  # Streupunkte: ein Schwarm, keine feste Form
            w = z.uniform(0, 2 * math.pi)
            px(img, cx + math.cos(w) * (ww + z.uniform(2, 5)), cy + math.sin(w) * (hh + z.uniform(2, 5)), farbe(pal, "dunkel"))
        return img
    glitch = {int(hh * 2 * 0.3): 2, int(hh * 2 * 0.7): -2} if stil == "C" else {}
    for j in range(hh * 2):
        for i in range(ww * 2):
            ch = _zelle(maske, i // 2, j // 2)
            if ch != "#":
                continue
            rand = any(_zelle(maske, (i + a) // 2, (j + b) // 2) != "#" for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            x = x0 + i + glitch.get(j, 0)
            if stil == "B":  # Lichtlinien: heller Umriss, innen nur Schimmer
                if rand:
                    px(img, x, y0 + j, farbe(pal, "hell"))
                elif (i + j) % 2 == 0:
                    px(img, x, y0 + j, farbe(pal, "tief"))
            else:            # Bildzeilen
                px(img, x, y0 + j, farbe(pal, "hell" if rand else "mittel" if j % 2 == 0 else "dunkel"))
        if j in glitch:
            px(img, x0 + (ww * 2 + 2 if glitch[j] > 0 else -3), y0 + j, farbe(pal, "akzent"))
    if stil == "B":  # der Kern funkelt an der Form
        fx, fy = x0 + ww * 2 - 1, y0
        for k in range(-3, 4):
            px(img, fx + k, fy, farbe(pal, "hell")), px(img, fx, fy + k, farbe(pal, "hell"))
        scheibe(img, fx, fy, 1.2, farbe(pal, "kern"))
    return img


# ── Tafeln ────────────────────────────────────────────────────────────────

def leuchten(img, sc=SC):
    """Vergrößern und Schein dazu — im Tool macht das später ein CSS-Filter."""
    gross = img.resize((img.width * sc, img.height * sc), Image.NEAREST)
    feld = Image.new("RGBA", gross.size, BG)
    schein = gross.filter(ImageFilter.GaussianBlur(sc * 1.6))
    weit = gross.filter(ImageFilter.GaussianBlur(sc * 3.5))
    for lage in (weit, weit, schein, schein, gross):
        feld.alpha_composite(lage)
    return feld


def schrift(gr):
    for name in ("consolab.ttf", "consola.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, gr)
        except OSError:
            pass
    return ImageFont.load_default()


def tafel(zeilen, spalten_titel, pfad, rand=160, zelle=G):
    """zeilen: [(titel, untertitel, [bilder])]; `zelle` schneidet die Mitte aus."""
    z = zelle * SC
    ab = (G - zelle) // 2
    n = max(len(b) for _, _, b in zeilen)
    kopf = 34
    t = Image.new("RGBA", (rand + n * z, kopf + len(zeilen) * z), BG)
    d = ImageDraw.Draw(t)
    f, fk = schrift(19), schrift(14)
    for i, s in enumerate(spalten_titel):
        d.text((rand + i * z + z / 2, kopf / 2), s, font=fk, fill=(150, 170, 200, 255), anchor="mm")
    for j, (titel, unter, bilder) in enumerate(zeilen):
        d.text((10, kopf + j * z + z / 2 - 12), titel, font=f, fill=(210, 235, 255, 255), anchor="lm")
        d.text((10, kopf + j * z + z / 2 + 12), unter, font=fk, fill=(120, 140, 170, 255), anchor="lm")
        for i, b in enumerate(bilder):
            t.alpha_composite(leuchten(b.crop((ab, ab, ab + zelle, ab + zelle))), (rand + i * z, kopf + j * z))
        d.line([(0, kopf + j * z), (t.width, kopf + j * z)], fill=(40, 46, 66, 255))
    t.convert("RGB").save(pfad)
    return t.size


def morph_gif(pfad, pal, maske):
    """Schwarm pulsiert, zieht sich zur Katze zusammen, hält, löst sich wieder."""
    st = A_STUFEN[3]
    heim = wolke_punkte(st)
    ziel = gestalt_punkte(maske)
    z = random.Random(11)
    n = max(len(heim), len(ziel))
    heim = [heim[i % len(heim)] for i in range(n)]
    ziel = [ziel[i % len(ziel)] for i in range(n)]
    ziel.sort(key=lambda p: math.atan2(p["y"], p["x"]))
    heim.sort(key=lambda p: math.atan2(p["y"], p["x"]))
    wirbel = [z.uniform(0, 2 * math.pi) for _ in range(n)]
    frames = []

    def weich(t):
        return t * t * (3 - 2 * t)

    plan = [("puls", 16), ("hin", 12), ("form", 14), ("zurueck", 12)]
    for art, anzahl in plan:
        for f in range(anzahl):
            t = f / anzahl
            if art == "puls":
                frames.append(wolke(pal, 3, puls=math.sin(t * 2 * math.pi), augen_zu=(f in (9, 10))))
                continue
            k = 1.0 if art == "form" else weich(t) if art == "hin" else 1 - weich(t)
            img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
            for a, b, w in zip(heim, ziel, wirbel):
                streu = math.sin(k * math.pi) * 5  # unterwegs wirbeln sie durcheinander
                x = a["x"] + (b["x"] - a["x"]) * k + math.cos(w + k * 4) * streu
                y = a["y"] + (b["y"] - a["y"]) * k + math.sin(w + k * 4) * streu
                if art == "form":
                    x += math.sin(f * 0.9 + w) * 0.35
                px(img, G / 2 + x, G / 2 + y, punkt_farbe(pal, a["d"] + (b["d"] - a["d"]) * k))
            frames.append(img)
    streifen = Image.new("RGBA", (G * 4 * 6, G * 4), BG)
    for i, f in enumerate((0, 4, 20, 24, 32, 47)):
        streifen.alpha_composite(leuchten(frames[f]), (i * G * 4, 0))
    streifen.convert("RGB").save(pfad.replace(".gif", "_streifen.png"))
    gross = [leuchten(f, 5).convert("RGB").quantize(colors=96, method=Image.Quantize.MEDIANCUT) for f in frames]
    gross[0].save(pfad, save_all=True, append_images=gross[1:], duration=90, loop=0, disposal=2)
    return len(frames)


if __name__ == "__main__":
    ziel = sys.argv[1]
    os.makedirs(ziel, exist_ok=True)
    P = PALETTEN["cyan"]
    stufen = ["1 · Funke", "2 · Keim", "3 · Geist", "4 · Wesen", "5 · Entität"]
    print(tafel([
        ("A  Datenwolke", "Daten-Schwarm", [wolke(P, s) for s in range(5)]),
        ("B  Lichtkern", "Kugel mit Ringen", [kern(P, s) for s in range(5)]),
        ("C  Glitch-Geist", "Hologramm", [geist(P, s) for s in range(5)]),
    ], stufen, os.path.join(ziel, "ki_wachstum.png")))
    namen = list(GESTALTEN)
    farben = [
        wolke(PALETTEN["magenta"], 3), kern(PALETTEN["magenta"], 3), geist(PALETTEN["magenta"], 3),
        wolke(PALETTEN["gruen"], 3), kern(PALETTEN["bernstein"], 3), geist(PALETTEN["gruen"], 3),
    ]
    print(tafel([
        ("A  Datenwolke", "formt sich", [gestalt(P, "A", GESTALTEN[n]) for n in namen]),
        ("B  Lichtkern", "zeichnet Licht", [gestalt(P, "B", GESTALTEN[n]) for n in namen]),
        ("C  Glitch-Geist", "flackert um", [gestalt(P, "C", GESTALTEN[n]) for n in namen]),
        ("Farben", "frei wählbar", farben),
    ], namen, os.path.join(ziel, "ki_gestalten.png"), zelle=46))
    print(morph_gif(os.path.join(ziel, "ki_morph.gif"), P, GESTALTEN["Katze"]))
