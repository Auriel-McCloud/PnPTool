# Entwurf 17.11.2026: Vampir-Fledermaus (zwei Pet-Arten M/W).
# Grundgestalt ist immer die Fledermaus (Ei + 6 Stufen); ab Stufe 3 verwandelt sie
# sich nach Lust in die Vampirgestalt ihrer Stufe: 3 Kind, 4 Teenager,
# 5 junger Erwachsener (~18), 6 ausgewachsen. Eigene Figuren, prozedural.
# Aufruf: python vampir_entwurf.py <zielordner>
#   → fledermaus_entwurf.png, vampir_entwurf.png
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HIER = os.path.dirname(os.path.abspath(__file__))
for p in (HIER, "C:/DEV/PnPTool/docs/assets/critter-pet"):
    if p not in sys.path:
        sys.path.insert(0, p)
from dcc_entwurf import ei, tafel  # noqa: E402

S = 4  # Überabtastung: Formen in 4×, Mehrheitsentscheid auf 1×
K = (22, 16, 28, 255)
WEISS = (250, 248, 244, 255)


def rgba(f):
    return f if len(f) == 4 else (*f, 255)


def lerp(a, b, t):
    return a + (b - a) * t


# ── Leinwand mit Ebenen ──────────────────────────────────────────────────
class Leinwand:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def _form(self, d, f, fill):
        art = f[0]
        if art == "ell":
            _, cx, cy, rx, ry = f
            d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill)
        elif art == "poly":
            d.polygon([(x * S, y * S) for x, y in f[1]], fill=fill)
        elif art == "linie":
            pts, b = f[1], f[2]
            d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, round(b * S)), joint="curve")
            for x, y in pts:
                d.ellipse([(x - b / 2) * S, (y - b / 2) * S, (x + b / 2) * S, (y + b / 2) * S], fill=fill)
        elif art == "aus":
            self._form(d, f[1], 0)

    def maske(self, formen):
        m = Image.new("L", (self.w * S, self.h * S), 0)
        d = ImageDraw.Draw(m)
        for f in formen:
            self._form(d, f, 255)
        return m.resize((self.w, self.h), Image.BOX).point(lambda v: 255 if v >= 128 else 0)

    def lege(self, formen, farbe, kante=None, clip=None, maske=None):
        """Ebene in `farbe`. `kante`: Rand dort, wo schon etwas darunter liegt
        (innere Trennlinie), an der freien Silhouette nicht (die bekommt K)."""
        m = maske if maske is not None else self.maske(formen)
        if clip is not None:
            m = Image.composite(m, Image.new("L", m.size, 0), clip)
        if kante is not None:
            alt = self.img.copy().load()
            mp = m.load()
            rand = []
            for y in range(self.h):
                for x in range(self.w):
                    if not mp[x, y]:
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.w and 0 <= ny < self.h and not mp[nx, ny] and alt[nx, ny][3]:
                            rand.append((x, y))
                            break
        self.img.paste(rgba(farbe), (0, 0), m)
        if kante is not None:
            px = self.img.load()
            for x, y in rand:
                px[x, y] = rgba(kante)
        return m

    def licht(self, m, hell=None, dunkel=None, b=1, dx=1):
        """Einfache Fasen-Beleuchtung: linke/obere Kante hell, rechte Kante dunkel."""
        if dunkel is not None:
            ver = m.transform(m.size, Image.AFFINE, (1, 0, b * dx, 0, 1, 0))  # nach links geschoben
            band = Image.composite(m, Image.new("L", m.size, 0), ver.point(lambda v: 255 - v))
            self.img.paste(rgba(dunkel), (0, 0), band)
        if hell is not None:
            ver = m.transform(m.size, Image.AFFINE, (1, 0, -b * dx, 0, 1, -b))
            band = Image.composite(m, Image.new("L", m.size, 0), ver.point(lambda v: 255 - v))
            self.img.paste(rgba(hell), (0, 0), band)

    def px(self, x, y, farbe):
        x, y = round(x), round(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.putpixel((x, y), rgba(farbe))

    def karte(self, x0, y0, zeilen, farben, spiegel=False):
        """ASCII-Pixelkarte; Leerzeichen/Punkt = nichts."""
        for j, z in enumerate(zeilen):
            if spiegel:
                z = z[::-1]
            for i, ch in enumerate(z):
                if ch in farben:
                    self.px(x0 + i, y0 + j, farben[ch])

    def fertig(self):
        return umriss(self.img)


def umriss(img):
    w, h = img.size
    px = img.load()
    out = img.copy()
    po = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3]:
                        po[x, y] = K
                        break
    return out


# ══ Fledermaus ═══════════════════════════════════════════════════════════
FLED = {
    "M": dict(D=(50, 44, 74), M=(82, 74, 112), L=(124, 114, 156), B=(168, 156, 192),
              H=(36, 28, 50), H2=(66, 50, 86), H3=(92, 72, 112), O=(212, 136, 158), A=(214, 36, 56), R=(0, 0, 0, 0)),
    "W": dict(D=(90, 56, 104), M=(136, 96, 152), L=(186, 146, 200), B=(226, 198, 230),
              H=(58, 34, 70), H2=(100, 62, 112), H3=(134, 88, 144), O=(248, 160, 186), A=(226, 44, 96), R=(250, 150, 176)),
}


def fledermaus(stufe, g, pose="stehen", augen="offen"):
    """stufe 1..6, g 'M'/'W'. pose: stehen (Flügel angelegt), flug, haengen."""
    p = {k: rgba(v) for k, v in FLED[g].items()}
    t = (stufe - 1) / 5
    L_ = Leinwand(96, 70)
    cx, boden = 48, 66
    rk = lerp(7.2, 8.0, t)            # Kopf
    rb = lerp(5.6, 9.2, t)            # Rumpf
    rbh = rb * lerp(0.95, 1.12, t)
    by = boden - 2.2 - rbh            # Rumpfmitte
    ky = by - rbh * lerp(0.55, 0.85, t) - rk * 0.55  # Kopfmitte
    oh = lerp(5.5, 9.5, t)            # Ohrhöhe
    fl = pose == "flug"

    # Flügel hinten
    sy = by - rbh * 0.45
    if fl:
        sp = lerp(38, 82, t)
        for s in (-1, 1):
            wrist = (cx + s * sp * 0.30, sy - sp * 0.22)
            tips = [(cx + s * sp * 0.50, sy - sp * 0.10), (cx + s * sp * 0.48, sy + sp * 0.12),
                    (cx + s * sp * 0.33, sy + sp * 0.22)]
            koerper = (cx + s * rb * 0.6, by + rbh * 0.55)
            pts = [(cx + s * rb * 0.5, sy - 1), wrist, tips[0]]
            prev = tips[0]
            for tp in tips[1:] + [koerper]:
                mx, my = (prev[0] + tp[0]) / 2, (prev[1] + tp[1]) / 2
                pts.append((lerp(mx, wrist[0], 0.22), lerp(my, wrist[1], 0.22)))  # Bogen nach innen
                pts.append(tp)
                prev = tp
            m = L_.lege([("poly", pts)], p["H2"])
            L_.licht(m, hell=p["H3"], b=1, dx=-s)
            for tp in tips:
                L_.lege([("linie", [wrist, tp], 1.0)], p["H"])
            L_.lege([("linie", [(cx + s * rb * 0.5, sy), wrist], 1.6)], p["H"])
            L_.lege([("poly", [(wrist[0] - 1, wrist[1]), (wrist[0] + s * 1.5, wrist[1] - 2.6), (wrist[0] + 1, wrist[1])])], p["D"])
    else:
        zu = 1.0 if pose == "haengen" else 0.0
        for s in (-1, 1):
            br = rb * lerp(1.0, 0.7, zu)
            pts = [(cx + s * rb * 0.55, sy - 1), (cx + s * (br + 1.8), sy - 3.6),  # Daumen oben
                   (cx + s * (br + 2.6), by), (cx + s * (br + 1.8), boden - 1.8),
                   (cx + s * (br + 0.4), boden - 3.4), (cx + s * (br - 0.8), boden - 1.4),
                   (cx + s * rb * lerp(0.3, -0.1, zu), boden - 2.8)]
            m = L_.lege([("poly", pts)], p["H2"])
            L_.licht(m, hell=p["H3"], dunkel=p["H"], dx=-s)
            L_.px(cx + s * (br + 2.0), sy - 4.6, p["L"])  # Daumenkralle

    # Füße
    if not fl:
        for s in (-1, 1):
            L_.lege([("ell", cx + s * rb * 0.38, boden - 1.4, 1.6, 1.3)], p["D"])
    # Rumpf
    m = L_.lege([("ell", cx, by, rb, rbh)], p["M"], kante=p["D"])
    L_.licht(m, hell=p["L"], dunkel=p["D"], b=1)
    L_.lege([("ell", cx, by + rbh * 0.22, rb * 0.6, rbh * 0.62)], p["B"], clip=m)
    if stufe >= 4:  # Halskrause aus Fell
        n = 7
        pts = []
        for i in range(n + 1):
            a = math.pi * i / n
            r = rb * 0.95 + (1.6 if i % 2 else 0)
            pts.append((cx - math.cos(a) * r, by - rbh * 0.62 + math.sin(a) * 2.6 + (1.8 if i % 2 else 0)))
        pts += [(cx + rb * 0.8, by - rbh * 0.8), (cx - rb * 0.8, by - rbh * 0.8)]
        L_.lege([("poly", pts)], p["L"], kante=p["M"])

    # Ohren
    for s in (-1, 1):
        a = (cx + s * rk * 0.18, ky - rk * 0.55)
        b_ = (cx + s * rk * 0.95, ky - rk * 0.15)
        tip = (cx + s * rk * lerp(1.15, 1.05, t), ky - rk - oh)
        m = L_.lege([("poly", [a, tip, b_])], p["M"], kante=p["D"])
        inn = [(lerp(a[0], b_[0], 0.25), lerp(a[1], b_[1], 0.25) + 0.3), (lerp(tip[0], cx + s * rk * 0.55, 0.2), tip[1] + 2.2),
               (lerp(a[0], b_[0], 0.8), lerp(a[1], b_[1], 0.8))]
        L_.lege([("poly", inn)], p["O"], clip=m)
    # Kopf
    m = L_.lege([("ell", cx, ky, rk, rk * 0.9)], p["M"], kante=p["D"])
    L_.licht(m, hell=p["L"], dunkel=p["D"])
    # Haarbüschel
    if g == "W":
        L_.lege([("poly", [(cx - 2.5, ky - rk * 0.8), (cx, ky - rk * 1.25), (cx + 2.8, ky - rk * 1.05), (cx + 1.0, ky - rk * 0.65)])], p["L"])
        L_.px(cx + 2.6, ky - rk * 1.15 + 1, p["M"])
    else:
        L_.lege([("poly", [(cx - 2, ky - rk * 0.82), (cx - 0.6, ky - rk * 1.3), (cx + 0.6, ky - rk * 0.95), (cx + 2.0, ky - rk * 1.22), (cx + 2.4, ky - rk * 0.8)])], p["L"])
    # Gesicht
    er = lerp(2.7, 2.2, t)
    ey = ky + 0.2
    for s in (-1, 1):
        ex = cx + s * max(rk * 0.44, er + 1.7)
        if augen == "zu":
            L_.lege([("linie", [(ex - er, ey), (ex, ey + 0.8), (ex + er, ey)], 0.9)], K)
            continue
        L_.lege([("ell", ex, ey, er, er * 1.1)], K)
        if stufe >= 3:
            L_.lege([("ell", ex, ey + 0.4, er * 0.62, er * 0.62)], p["A"])
        L_.px(ex - er * 0.4, ey - er * 0.5, WEISS)
        L_.px(ex - er * 0.4 + 1, ey - er * 0.5, WEISS)
        L_.px(ex + er * 0.45, ey + er * 0.45, WEISS)
        if g == "W":  # Wimpern außen
            L_.px(ex + s * (er + 0.8), ey - er * 0.9, K)
            L_.px(ex + s * (er + 0.2), ey - er * 1.3, K)
        L_.px(ex + s * 1.2, ey + er + 1.2, p["O"])  # Bäckchen
        L_.px(ex + s * 2.2, ey + er + 1.2, p["O"])
    ny = ky + rk * 0.45
    L_.lege([("ell", cx, ny, 1.5, 0.9)], p["L"])
    L_.px(cx - 0.7, ny, p["D"])
    L_.px(cx + 0.7, ny, p["D"])
    my = ny + 1.4
    L_.karte(round(cx) - 2, round(my), ["K...K", ".KKK."], {"K": K})
    if stufe >= 3:
        lang = 2 if stufe >= 5 else 1
        for i in range(lang):
            L_.px(round(cx) - 1, round(my) + 2 + i, WEISS)
            L_.px(round(cx) + 1, round(my) + 2 + i, WEISS)
    bild = L_.fertig()
    if pose == "haengen":
        bild = bild.transpose(Image.FLIP_TOP_BOTTOM)
        bb = bild.getbbox()
        neu = Image.new("RGBA", (96, 74), (0, 0, 0, 0))
        neu.paste(bild, (0, 4 - bb[1]), bild)
        d = ImageDraw.Draw(neu)
        d.rectangle([cx - 16, 0, cx + 16, 3], fill=(96, 104, 128, 255))  # Kante (Popup/Menü)
        d.line([(cx - 16, 3), (cx + 16, 3)], fill=(60, 66, 86, 255))
        # Krallen um die Kante
        for s in (-1, 1):
            x = round(cx + s * rb * 0.38)
            d.point([(x - 1, 2), (x + 1, 2), (x, 2)], fill=rgba(FLED[g]["D"]))
        bild = neu
    return bild


# ══ Vampirgestalt ════════════════════════════════════════════════════════
HAUT = dict(L=(244, 232, 232), M=(222, 204, 210), D=(188, 164, 180))
STOFF = dict(D=(22, 18, 30), M=(40, 34, 52), L=(66, 58, 84))
ROT = dict(D=(110, 14, 34), M=(168, 28, 50), L=(220, 64, 80))
HEMD = dict(M=(232, 230, 238), D=(186, 184, 204))
GOLD = (222, 180, 76)
HAAR = {"M": dict(D=(18, 16, 28), M=(38, 34, 56), L=(80, 74, 112)),
        "W": dict(D=(36, 20, 44), M=(68, 40, 82), L=(122, 82, 138))}
AUGE = (210, 24, 44)
LIPPE = (178, 22, 48)

# Maße je Stufe (Höhe, Kopfradius, Schulter, Taille, Hüfte, Rumpflänge, Hals)
MASSE = {
    ("M", 3): dict(H=38, rk=8.4, sch=6.0, ta=5.2, hu=5.4, tor=11, hals=0.6),
    ("M", 4): dict(H=52, rk=7.4, sch=7.4, ta=5.6, hu=5.8, tor=16, hals=1.2),
    ("M", 5): dict(H=64, rk=6.8, sch=9.0, ta=6.2, hu=6.4, tor=20, hals=1.8),
    ("M", 6): dict(H=70, rk=6.6, sch=10.6, ta=6.8, hu=6.8, tor=22, hals=2.0),
    ("W", 3): dict(H=37, rk=8.4, sch=5.6, ta=5.0, hu=5.4, tor=10.5, hals=0.6),
    ("W", 4): dict(H=50, rk=7.3, sch=6.4, ta=4.8, hu=6.0, tor=15, hals=1.4),
    ("W", 5): dict(H=60, rk=6.6, sch=7.2, ta=4.0, hu=7.2, tor=18, hals=2.0),
    ("W", 6): dict(H=66, rk=6.4, sch=7.6, ta=4.0, hu=7.8, tor=20, hals=2.2),
}


def vampir(g, stufe, zylinder=False, stock=False):
    """zylinder/stock: Accessoires des Mannes (Mark 17.11.: setzt sich manchmal
    einen Zylinder auf, eleganter Gehstock)."""
    m_ = MASSE[(g, stufe)]
    L_ = Leinwand(72, 96)
    cx, boden = 36, 94
    H, rk = m_["H"], m_["rk"]
    ky = boden - H + rk                 # Kopfmitte
    kinn = ky + rk * 0.92
    sy = kinn + m_["hals"]              # Schulterlinie
    hy = sy + m_["tor"]                 # Hüfte
    beine = boden - hy
    sch, ta, hu = m_["sch"], m_["ta"], m_["hu"]
    hz = HAAR[g]

    # ── Umhang (hinten) ──
    umhang = {3: 1.0, 4: 0.55, 5: 1.0, 6: 1.0}[stufe]
    kragen = {("M", 3): 1.0, ("M", 4): 0.0, ("M", 5): 0.7, ("M", 6): 1.25,
              ("W", 3): 0.6, ("W", 4): 0.0, ("W", 5): 0.0, ("W", 6): 1.25}[(g, stufe)]
    if umhang:
        unten = lerp(sy, boden - 1, umhang)
        weit = sch + lerp(3, {3: 7, 4: 5, 5: 9, 6: 14}[stufe], umhang)
        pts = [(cx - sch + 0.5, sy - 0.5), (cx + sch - 0.5, sy - 0.5),
               (cx + weit, unten), (cx + weit * 0.5, unten - 1.2), (cx, unten), (cx - weit * 0.5, unten - 1.2), (cx - weit, unten)]
        L_.lege([("poly", pts)], STOFF["M"])
        inn = [(cx - sch + 2, sy + 1), (cx + sch - 2, sy + 1), (cx + weit - 2.2, unten - 0.6),
               (cx + weit * 0.5, unten - 2.0), (cx, unten - 0.8), (cx - weit * 0.5, unten - 2.0), (cx - weit + 2.2, unten - 0.6)]
        mr = L_.lege([("poly", inn)], ROT["M"])
        L_.licht(mr, dunkel=ROT["D"], b=2)
        # Faltenlinien
        for s in (-1, 1):
            L_.lege([("linie", [(cx + s * (sch + 1), sy + 4), (cx + s * (weit - 4), unten - 2)], 0.8)], ROT["D"])
    if kragen:
        for s in (-1, 1):
            kh = rk * kragen
            pts = [(cx + s * (sch - 1.5), sy + 1), (cx + s * (rk * 0.55), kinn - 1),
                   (cx + s * (rk * 0.9 + kh * 0.25), ky - kh * 0.7), (cx + s * (rk * 1.25 + kh * 0.55), ky - kh * 0.35 - 1),
                   (cx + s * (sch + 1.5), sy + 1.5)]
            L_.lege([("poly", pts)], STOFF["M"])
            inn = [(cx + s * (rk * 0.7), kinn - 0.5), (cx + s * (rk * 0.95 + kh * 0.25), ky - kh * 0.5),
                   (cx + s * (rk * 1.15 + kh * 0.45), ky - kh * 0.25), (cx + s * (sch - 0.5), sy + 0.5)]
            L_.lege([("poly", inn)], ROT["M"])

    # ── Haar hinten (lang, Frauen) ──
    if g == "W" and stufe >= 4:
        lang = {4: hy - 2, 5: hy + 2, 6: hy + 8}[stufe]
        br = rk * {4: 1.05, 5: 1.25, 6: 1.35}[stufe]
        pts = [(cx - rk * 0.9, ky - rk * 0.4), (cx + rk * 0.9, ky - rk * 0.4)]
        if stufe == 4:
            pts += [(cx + br, lang), (cx - br, lang)]
        else:  # wellig
            n = 5
            rechts = [(cx + br + (1.2 if i % 2 else -0.4), lerp(ky, lang, i / n)) for i in range(1, n + 1)]
            pts += rechts + [(cx + br * 0.4, lang - 2), (cx - br * 0.4, lang - 1)] + [(2 * cx - x, y) for x, y in reversed(rechts)]
        mh = L_.lege([("poly", pts)], hz["M"])
        L_.licht(mh, hell=hz["L"], dunkel=hz["D"])

    # ── Beine ──
    knie = hy + beine * 0.5
    if g == "M":
        hose = STOFF["D"] if stufe != 4 else (34, 32, 48)
        for s in (-1, 1):
            pts = [(cx + s * 0.3, hy), (cx + s * hu, hy - 0.5), (cx + s * (hu * 0.62), boden - 2), (cx + s * 0.9, boden - 2)]
            mb = L_.lege([("poly", pts)], hose, kante=STOFF["D"])
            L_.licht(mb, hell=STOFF["L"] if stufe != 4 else (60, 58, 80), b=1, dx=-s)
            schuh = STOFF["D"] if stufe != 4 else (30, 30, 40)
            L_.lege([("ell", cx + s * (hu * 0.42 + 0.4), boden - 1.3, hu * 0.45 + 0.6, 1.4)], schuh, kante=K)
            if stufe == 4:  # Turnschuh-Sohle
                L_.lege([("poly", [(cx + s * 0.9, boden - 0.6), (cx + s * (hu * 0.84 + 0.8), boden - 0.6), (cx + s * (hu * 0.84 + 0.8), boden), (cx + s * 0.9, boden)])], (230, 230, 236))
            else:
                L_.px(cx + s * (hu * 0.42 + 0.4) - 1, boden - 2, STOFF["L"])
    else:
        bein_farbe = {3: (240, 238, 244), 4: (60, 44, 76), 5: HAUT["M"], 6: HAUT["M"]}[stufe]
        for s in (-1, 1):
            if stufe == 6 and s == -1:
                continue  # das andere Bein bleibt unterm Kleid
            pts = [(cx + s * 0.6, hy), (cx + s * hu * 0.8, hy), (cx + s * (hu * 0.42 + 0.6), boden - 2), (cx + s * 1.0, boden - 2)]
            mb = L_.lege([("poly", pts)], bein_farbe, kante=HAUT["D"] if stufe >= 5 else STOFF["M"])
            if stufe == 4:  # Ringelstrümpfe
                y = hy + 2
                while y < boden - 3:
                    L_.lege([("poly", [(cx - 8, y), (cx + 8, y), (cx + 8, y + 1), (cx - 8, y + 1)])], (24, 18, 32), clip=mb)
                    y += 2
            if stufe >= 5:
                L_.licht(mb, hell=HAUT["L"], dunkel=HAUT["D"], dx=-s)
            # Schuhe
            if stufe == 3:
                L_.lege([("ell", cx + s * (hu * 0.3 + 0.8), boden - 1.2, 2.2, 1.3)], STOFF["D"])
            elif stufe == 4:  # Stiefel
                L_.lege([("poly", [(cx + s * 0.9, knie + 4), (cx + s * (hu * 0.55 + 0.9), knie + 4), (cx + s * (hu * 0.62 + 1.6), boden), (cx + s * 0.6, boden)])], STOFF["D"], kante=K)
                L_.px(cx + s * (hu * 0.45), knie + 5, STOFF["L"])
            else:  # Absatzschuhe
                fx = cx + s * (hu * 0.42 + 0.9)
                L_.lege([("poly", [(fx - 1.6, boden - 2.5), (fx + 1.6, boden - 2.5), (fx + 1.2, boden - 0.5), (fx - 1.2, boden - 0.5)])], ROT["D"] if stufe == 5 else STOFF["D"])
                L_.px(fx + s * 1, boden, STOFF["D"])

    # ── Rumpf / Kleid ──
    tw = sy + m_["tor"] * 0.62
    rumpf = [(cx - sch, sy), (cx + sch, sy), (cx + ta, tw), (cx + hu, hy), (cx - hu, hy), (cx - ta, tw)]
    if g == "M":
        jacke = {3: STOFF["M"], 4: STOFF["M"], 5: STOFF["M"], 6: STOFF["M"]}[stufe]
        mr = L_.lege([("poly", rumpf)], jacke, kante=STOFF["D"])
        L_.licht(mr, hell=STOFF["L"], dunkel=STOFF["D"])
        if stufe == 3:  # Hemd-V, rote Fliege
            L_.lege([("poly", [(cx - 2.6, sy), (cx + 2.6, sy), (cx, tw + 1)])], HEMD["M"], clip=mr)
            L_.karte(round(cx) - 2, round(sy) + 1, ["RR.RR", "RRRRR", "RR.RR"], {"R": ROT["M"]})
        elif stufe == 4:  # offene Jacke, rotes Shirt mit Fledermaus-Logo
            ms = L_.lege([("poly", [(cx - 2.8, sy), (cx + 2.8, sy), (cx + 3.2, hy), (cx - 3.2, hy)])], ROT["M"], clip=mr)
            L_.licht(ms, dunkel=ROT["D"])
            L_.karte(round(cx) - 2, round(sy + m_["tor"] * 0.4), ["K...K", "KK.KK", ".KKK."], {"K": STOFF["D"]})
            L_.lege([("poly", [(cx - 2.5, sy), (cx + 2.5, sy), (cx + 1.5, sy + 1.5), (cx - 1.5, sy + 1.5)])], HAUT["M"])
        elif stufe == 5:  # weißes Hemd offen, schwarze Weste
            mh = L_.lege([("poly", [(cx - 3.4, sy), (cx + 3.4, sy), (cx + 2.4, hy - 2), (cx - 2.4, hy - 2)])], HEMD["M"], clip=mr)
            L_.licht(mh, dunkel=HEMD["D"])
            L_.lege([("poly", [(cx - 1.8, sy), (cx + 1.8, sy), (cx, sy + 5)])], HAUT["M"])  # offener Kragen
            for s in (-1, 1):
                L_.lege([("poly", [(cx + s * 1.8, sy - 0.5), (cx + s * 3.6, sy - 0.5), (cx + s * 2.6, sy + 2.6)])], HEMD["M"], kante=HEMD["D"])
            # Weste
            for s in (-1, 1):
                L_.lege([("poly", [(cx + s * 2.0, sy + 6), (cx + s * (ta + 0.5), sy + 3), (cx + s * (hu - 0.2), hy), (cx + s * 0.3, hy)])], STOFF["D"], clip=mr)
            for i in range(3):
                L_.px(cx - 0.5, sy + 8 + i * 3, GOLD)
        else:  # 6: Frack, rote Weste, Halstuch mit Rubin
            mw = L_.lege([("poly", [(cx - 4.0, sy), (cx + 4.0, sy), (cx + 3.2, hy - 1), (cx - 3.2, hy - 1)])], ROT["M"], clip=mr)
            L_.licht(mw, dunkel=ROT["D"])
            mh = L_.lege([("poly", [(cx - 2.6, sy - 0.5), (cx + 2.6, sy - 0.5), (cx + 1.6, sy + 7), (cx, sy + 8.5), (cx - 1.6, sy + 7)])], HEMD["M"])
            L_.licht(mh, dunkel=HEMD["D"])
            L_.lege([("ell", cx, sy + 3.0, 1.4, 1.4)], ROT["L"], kante=ROT["D"])
            L_.px(cx, sy + 3, GOLD)
            for i in range(3):
                L_.px(cx, sy + 11 + i * 3, GOLD)
            for s in (-1, 1):  # Revers
                L_.lege([("poly", [(cx + s * 4.2, sy), (cx + s * 2.6, sy + 11), (cx + s * 5.2, sy + 5)])], STOFF["L"], kante=STOFF["D"])
    else:
        if stufe == 3:  # Kleidchen mit Bubikragen
            rock_u = hy + beine * 0.42
            pts = rumpf[:3] + [(cx + hu + 3.5, rock_u), (cx - hu - 3.5, rock_u)] + rumpf[5:]
            mr = L_.lege([("poly", pts)], STOFF["M"], kante=STOFF["D"])
            L_.licht(mr, hell=STOFF["L"], dunkel=STOFF["D"])
            L_.lege([("poly", [(cx - hu - 3.5, rock_u - 1.4), (cx + hu + 3.5, rock_u - 1.4), (cx + hu + 3.5, rock_u), (cx - hu - 3.5, rock_u)])], ROT["M"], clip=mr)
            for s in (-1, 1):
                L_.lege([("ell", cx + s * 2.2, sy + 0.8, 2.4, 1.6)], HEMD["M"], kante=HEMD["D"])
            L_.karte(round(cx) - 2, round(sy) + 1, ["RR.RR", "RRRRR", "R...R"], {"R": ROT["M"]})
        elif stufe == 4:  # Kleid bis knapp übers Knie, rote Säume, langärmlig
            rock_u = knie
            pts = rumpf[:3] + [(cx + hu + 2.5, rock_u), (cx - hu - 2.5, rock_u)] + rumpf[5:]
            mr = L_.lege([("poly", pts)], STOFF["M"], kante=STOFF["D"])
            L_.licht(mr, hell=STOFF["L"], dunkel=STOFF["D"])
            L_.lege([("poly", [(cx - hu - 3, rock_u - 1.2), (cx + hu + 3, rock_u - 1.2), (cx + hu + 3, rock_u), (cx - hu - 3, rock_u)])], ROT["M"], clip=mr)
            L_.lege([("poly", [(cx - 2.2, sy), (cx + 2.2, sy), (cx, sy + 2.6)])], HAUT["M"])
            L_.lege([("poly", [(cx - ta - 1, tw - 0.5), (cx + ta + 1, tw - 0.5), (cx + ta + 1, tw + 0.8), (cx - ta - 1, tw + 0.8)])], ROT["M"], clip=mr)
        elif stufe == 5:  # schulterfreies Kleid bis zur Wade
            rock_u = knie + beine * 0.26
            haut = L_.lege([("poly", [(cx - sch, sy), (cx + sch, sy), (cx + ta + 1, sy + 4.2), (cx - ta - 1, sy + 4.2)])], HAUT["M"])
            L_.licht(haut, hell=HAUT["L"], dunkel=HAUT["D"])
            top = sy + 3.6
            pts = [(cx - ta - 1.4, top), (cx + ta + 1.4, top), (cx + ta, tw), (cx + hu, hy), (cx + hu + 3, rock_u), (cx - hu - 3, rock_u), (cx - hu, hy), (cx - ta, tw)]
            mr = L_.lege([("poly", pts)], STOFF["M"], kante=STOFF["D"])
            L_.licht(mr, hell=STOFF["L"], dunkel=STOFF["D"])
            L_.lege([("linie", [(cx - ta - 1, top + 0.4), (cx + ta + 1, top + 0.4)], 0.9)], ROT["M"])
            L_.lege([("linie", [(cx + 1.5, hy + 1), (cx + 2.8, rock_u - 1)], 0.8)], STOFF["D"])  # Falte
        else:  # 6: bodenlanges Abendkleid, V-Ausschnitt, Schlitz
            rock_u = boden - 1
            pts = [(cx - sch + 1.2, sy), (cx + sch - 1.2, sy), (cx + ta, tw), (cx + hu, hy), (cx + hu + 4.5, rock_u),
                   (cx + hu + 1.2, rock_u), (cx + 2.2, knie - 5), (cx + 0.4, rock_u), (cx - hu - 4, rock_u), (cx - hu, hy), (cx - ta, tw)]
            mr = L_.lege([("poly", pts)], (52, 18, 34), kante=(30, 10, 22))
            L_.licht(mr, hell=(92, 30, 52), dunkel=(30, 10, 22))
            L_.lege([("poly", [(cx - 2.6, sy - 0.5), (cx + 2.6, sy - 0.5), (cx, sy + 6)])], HAUT["M"])  # V-Ausschnitt
            L_.lege([("linie", [(cx - ta - 0.4, tw), (cx + ta + 0.4, tw)], 0.6)], (176, 138, 60))
            L_.px(cx, tw, GOLD)
            L_.lege([("linie", [(cx - 4, rock_u - 6), (cx - hu - 2, rock_u)], 0.8)], (30, 10, 22))  # Falte

    # ── Arme ──
    arm_b = {3: 2.4, 4: 2.3, 5: 2.3, 6: 2.6}[stufe] * (0.88 if g == "W" else 1)
    for s in (-1, 1):
        sx, s_y = cx + s * (sch - arm_b * 0.5), sy + arm_b * 0.5
        hand = (cx + s * (hu + arm_b * 0.4 + (1.6 if g == "M" else 1.4)), hy + {3: 0.5, 4: 2.5, 5: 4, 6: 4.5}[stufe])
        ell_ = (lerp(sx, hand[0], 0.5) + s * 0.8, lerp(s_y, hand[1], 0.5))
        if stock and s == 1:  # Mark 17.11.: Arm ausgestreckt, stützt sich elegant auf den Stock
            hand = (cx + sch + 8.5, hy - 0.5)  # Mark: Arm eine Spur kürzer
            ell_ = (lerp(sx, hand[0], 0.5) + 0.4, lerp(s_y, hand[1], 0.5) - 0.8)
        if g == "M":
            aermel = HEMD["M"] if stufe == 5 else STOFF["M"]
        else:
            aermel = {3: STOFF["M"], 4: STOFF["M"], 5: HAUT["M"], 6: HAUT["M"]}[stufe]
        ma = L_.lege([("linie", [(sx, s_y), ell_, hand], arm_b)], aermel, kante=STOFF["D"] if aermel != HAUT["M"] else HAUT["D"])
        if aermel == HAUT["M"]:
            L_.licht(ma, dunkel=HAUT["D"], dx=-s)
        if g == "W" and stufe == 6:  # Opernhandschuhe bis über den Ellbogen
            L_.lege([("linie", [(lerp(sx, ell_[0], 0.6), lerp(s_y, ell_[1], 0.6)), ell_, hand], arm_b)], STOFF["D"])
        if aermel == STOFF["M"]:
            L_.licht(ma, hell=STOFF["L"], dx=-s)
        if g == "M" and stufe == 6:  # Manschette
            L_.lege([("linie", [(lerp(ell_[0], hand[0], 0.85), lerp(ell_[1], hand[1], 0.85)), hand], arm_b * 0.9)], HEMD["M"])
        if stock and s == 1:  # Gehstock: schwarz lackiert, Silberknauf, Spitze am Boden
            fuss = (hand[0] + 1.2, boden - 0.5)
            L_.lege([("linie", [(hand[0], hand[1] + 4), fuss], 1.6)], K)
            L_.lege([("linie", [(hand[0] - 0.3, hand[1] + 8), (fuss[0] - 0.6, fuss[1] - 3)], 0.6)], (118, 106, 140))
            L_.lege([("ell", fuss[0], fuss[1] - 0.6, 0.9, 1.0)], (210, 214, 226))
            # Knauf als silberner Totenkopf (Mark 17.11.), die Hand liegt auf dem Schädeldach
            silber, schatten = (218, 222, 234), (132, 136, 156)
            tx, ty = round(hand[0] + 0.2), round(hand[1] + 2.2)  # Mark: eine Spur kleiner
            L_.karte(tx - 2, ty, [
                ".SSS.",
                "SSSSS",
                "SkSkd",
                ".SkS.",
                ".S.d.",
            ], {"S": silber, "k": (28, 22, 36), "d": schatten})
        L_.lege([("ell", hand[0], hand[1] + 1.2, arm_b * 0.5, arm_b * 0.62)], STOFF["D"] if (g == "W" and stufe == 6) else HAUT["M"], kante=HAUT["D"])

    # ── Hals, Kopf ──
    L_.lege([("poly", [(cx - 1.6, kinn - 2), (cx + 1.6, kinn - 2), (cx + 1.6, sy + 0.5), (cx - 1.6, sy + 0.5)])], HAUT["D"])
    if g == "W" and stufe >= 5:  # Samtband mit Stein
        L_.lege([("linie", [(cx - 1.6, sy - 0.6), (cx + 1.6, sy - 0.6)], 0.9)], STOFF["D"])
        L_.px(cx, sy, ROT["L"])
    mk = L_.lege([("ell", cx, ky, rk * 0.9, rk)], HAUT["M"], kante=HAUT["D"])
    L_.licht(mk, hell=HAUT["L"], dunkel=HAUT["D"])
    # Ohren (leicht spitz ab Stufe 5)
    for s in (-1, 1):
        ox = cx + s * rk * 0.9
        spitz = 1.6 if stufe >= 5 else 0.6
        L_.lege([("poly", [(ox - s * 0.6, ky - 0.6), (ox + s * spitz, ky - 1.6 - spitz), (ox + s * 0.8, ky + 2)])], HAUT["M"], kante=HAUT["D"])

    gesicht(L_, g, stufe, cx, ky, rk)
    haar_vorn(L_, g, stufe, cx, ky, rk, hz)
    if zylinder:
        zylinder_malen(L_, cx, ky, rk)
    return L_.fertig()


def zylinder_malen(L_, cx, ky, rk):
    """Zylinder leicht schräg auf dem Kopf, rotes Band, breite Krempe."""
    krempe = ky - rk * 0.62
    hoch = rk * 1.55
    b_unten, b_oben = rk * 0.72, rk * 0.8
    k = 0.8  # Schräglage nach rechts
    korpus = [(cx - b_unten + k * 0.3, krempe), (cx + b_unten + k * 0.3, krempe),
              (cx + b_oben + k, krempe - hoch), (cx - b_oben + k, krempe - hoch)]
    mz = L_.lege([("poly", korpus)], STOFF["M"], kante=STOFF["D"])
    L_.licht(mz, hell=STOFF["L"], dunkel=STOFF["D"])
    L_.lege([("ell", cx + k, krempe - hoch, b_oben, 1.0)], STOFF["L"], kante=STOFF["D"])  # Deckel
    L_.lege([("poly", [(cx - b_unten, krempe - 1.0), (cx + b_unten + 0.6, krempe - 1.0),
                      (cx + b_unten + 0.7, krempe - 2.8), (cx - b_unten + 0.1, krempe - 2.8)])], ROT["M"])  # Band
    L_.lege([("ell", cx + 0.3, krempe + 0.2, rk * 1.18, 1.3)], STOFF["D"], kante=K)  # Krempe
    L_.px(cx - rk * 0.9, krempe - 0.2, STOFF["L"])


def gesicht(L_, g, stufe, cx, ky, rk):
    x0 = round(cx)
    ey = round(ky + rk * 0.12)
    f = {"K": K, "R": AUGE, "W": WEISS, "M": (120, 30, 44), "Z": WEISS, "L": LIPPE, "B": (226, 160, 172), "H": HAUT["D"]}
    if stufe == 3:  # große Kinderaugen, Grinsen mit Zähnchen
        auge = ["KKK", "RRW" if g == "M" else "RRW", "RRR"]
        dx = 4 if rk > 8 else 3
        for s in (-1, 1):
            L_.karte(x0 + s * dx - 1, ey - 1, auge, f, spiegel=False)
            if g == "W":
                L_.px(x0 + s * (dx + 2), ey - 2, K)
            L_.px(x0 + s * (dx + 1), ey + 3, "B" and f["B"])
        L_.karte(x0 - 2, ey + 4, ["K...K", ".KKK.", ".Z.Z."], f)
    elif stufe == 4:
        for s in (-1, 1):
            L_.karte(x0 + s * 3 - (1 if s < 0 else 0), ey - 1, ["KK", "RW"] if s < 0 else ["KK", "WR"], f)
            if g == "W":
                L_.px(x0 + s * 4 + (0 if s < 0 else 1), ey - 2, K)
        if g == "M":
            L_.karte(x0 - 1, ey + 3, ["KKK", "..Z"], f)       # schmollend, ein Zähnchen
        else:
            L_.karte(x0 - 1, ey + 3, [".M.", "Z.Z"], f)
    else:  # 5/6: halb gesenkte Lider, schmal, Augenbrauen
        for s in (-1, 1):
            ex = x0 + s * 3 - (2 if s < 0 else 0)
            lid = ["KKK", "RRK" if s < 0 else "KRR"] if g == "W" else ["KKK", ".RR" if s < 0 else "RR."]
            L_.karte(ex, ey - 1, lid, f)
            if g == "W":
                L_.px(ex + (-1 if s < 0 else 3), ey - 2, K)  # Wimpernschwung
            # Brauen
            b = ["..KK", "KK.."] if s < 0 else ["KK..", "..KK"]
            if g == "M":
                L_.karte(ex - (1 if s < 0 else 0), ey - 4, b if stufe == 6 else [b[1] if s < 0 else b[0]], {"K": HAAR["M"]["D"]})
            else:
                L_.karte(ex, ey - 3, [".KK" if s < 0 else "KK."], {"K": HAAR["W"]["D"]})
        if g == "M":  # Schmunzeln mit einem Fangzahn
            L_.karte(x0 - 1, ey + 4, ["..m", "mm.", "Z.."], {**f, "m": (132, 70, 86)})
        else:  # rote Lippen
            L_.karte(x0 - 1, ey + 4, ["LLL"] if stufe == 5 else ["LLL", ".L."], f)


def haar_vorn(L_, g, stufe, cx, ky, rk, hz):
    oben = ky - rk
    if g == "M":
        if stufe == 4:  # Emo-Pony über das rechte Auge
            pts = [(cx - rk * 1.0, ky + 0.5), (cx - rk * 1.05, oben + 1), (cx - 2, oben - 1.5), (cx + rk * 0.9, oben + 0.5),
                   (cx + rk * 1.05, ky + 3), (cx + rk * 0.5, ky + 2.2), (cx + 1.0, ky + 1.4), (cx - 0.5, ky - 1.6),
                   (cx - rk * 0.55, ky - rk * 0.35), (cx - rk * 0.8, ky + 0.8)]
            mh = L_.lege([("poly", pts)], hz["M"], kante=hz["D"])
            L_.licht(mh, hell=hz["L"], dunkel=hz["D"])
            L_.lege([("linie", [(cx + 2, oben + 1), (cx + rk * 0.6, ky + 0.8)], 0.7)], hz["D"])
        else:  # zurückgekämmt mit Witwenspitze
            spitze = ky - rk * {3: 0.45, 5: 0.4, 6: 0.5}[stufe]
            pts = [(cx - rk * 0.98, ky + 0.5), (cx - rk * 1.0, oben + 0.5), (cx - rk * 0.4, oben - 2.0), (cx + rk * 0.4, oben - 2.0),
                   (cx + rk * 1.0, oben + 0.5), (cx + rk * 0.98, ky + 0.5), (cx + rk * 0.82, ky - rk * 0.25),
                   (cx + rk * 0.45, ky - rk * 0.5), (cx, spitze), (cx - rk * 0.45, ky - rk * 0.5), (cx - rk * 0.82, ky - rk * 0.25)]
            mh = L_.lege([("poly", pts)], hz["M"], kante=hz["D"])
            L_.licht(mh, hell=hz["L"], dunkel=hz["D"])
            L_.lege([("linie", [(cx - 2, oben - 0.5), (cx - rk * 0.75, ky - 1)], 0.7)], hz["L"])
            if stufe == 5:  # lose Strähne in der Stirn
                L_.lege([("linie", [(cx + 0.5, spitze - 1), (cx + 1.8, ky - 0.5), (cx + 1.2, ky + 1)], 0.9)], hz["M"], kante=hz["D"])
            if stufe == 6:  # graue Schläfen
                for s in (-1, 1):
                    L_.px(cx + s * rk * 0.92, ky - 0.5, (150, 146, 170))
                    L_.px(cx + s * rk * 0.92, ky + 0.5, (120, 116, 140))
    else:
        if stufe == 3:  # Zöpfe mit roten Bändern
            for s in (-1, 1):
                zx = cx + s * (rk + 2.2)
                mz = L_.lege([("ell", zx, ky + 1.5, 2.6, 4.8)], hz["M"], kante=hz["D"])
                L_.licht(mz, hell=hz["L"], dunkel=hz["D"])
                L_.lege([("ell", cx + s * (rk + 0.4), ky - 2.6, 1.4, 1.2)], ROT["M"])
        pony = {3: ky - rk * 0.25, 4: ky - 0.8, 5: ky - rk * 0.3, 6: ky - rk * 0.35}[stufe]
        pts = [(cx - rk * 1.02, ky + (6 if stufe >= 4 else 0.6)), (cx - rk * 1.05, oben + 1), (cx - rk * 0.3, oben - 1.8),
               (cx + rk * 0.5, oben - 1.6), (cx + rk * 1.05, oben + 1), (cx + rk * 1.02, ky + (6 if stufe >= 4 else 0.6))]
        if stufe == 4:  # gerader Pony
            pts += [(cx + rk * 0.78, ky + 3), (cx + rk * 0.72, pony), (cx - rk * 0.72, pony), (cx - rk * 0.78, ky + 3)]
        else:  # Seitenscheitel, Pony schwingt zur Seite
            pts += [(cx + rk * 0.8, ky + 1), (cx + rk * 0.6, ky - rk * 0.45), (cx - 0.5, pony + 0.6),
                    (cx - rk * 0.55, ky - rk * 0.62), (cx - rk * 0.8, ky + 1)]
        mh = L_.lege([("poly", pts)], hz["M"], kante=hz["D"])
        L_.licht(mh, hell=hz["L"], dunkel=hz["D"])
        if stufe >= 5:  # Locke vorn über die Schulter
            s = 1
            L_.lege([("linie", [(cx + s * rk * 0.95, ky + 2), (cx + s * rk * 1.15, ky + rk + 3), (cx + s * rk * 0.85, ky + rk + 7)], 1.8)], hz["M"], kante=hz["D"])
        if stufe == 6:
            L_.lege([("ell", cx - rk * 0.7, oben + 0.6, 1.2, 1.0)], ROT["L"])  # Haarschmuck (Rose)
            L_.px(cx - rk * 0.7, oben + 0.6, ROT["D"])


def verwandlung_puff(g, stufe, seed=7):
    """Kleine Vorschau: Rauch mit Mini-Fledermäusen (Übergang)."""
    import random
    rnd = random.Random(seed)
    img = Image.new("RGBA", (72, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(26):
        x, y = rnd.uniform(14, 58), rnd.uniform(30, 80)
        r = rnd.uniform(3, 7)
        c = rnd.choice(((120, 100, 140, 200), (160, 140, 180, 200), (90, 72, 110, 220)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    fb = FLED[g]
    for _ in range(5):
        x, y = rnd.uniform(16, 56), rnd.uniform(12, 50)
        d.polygon([(x - 4, y - 1), (x - 2, y), (x, y - 1.5), (x + 2, y), (x + 4, y - 1), (x + 2.5, y + 1.5), (x, y + 0.5), (x - 2.5, y + 1.5)], fill=rgba(fb["H"]))
    return umriss(img)


def main(ziel):
    os.makedirs(ziel, exist_ok=True)
    spalten = ["Ei", "1", "2", "3", "4", "5", "6", "fliegt", "hängt"]
    eifarben = {"M": ((70, 62, 96), (110, 100, 140), (160, 150, 190)), "W": ((120, 84, 136), (170, 130, 186), (214, 186, 226))}
    zeilen = []
    for g, name in (("M", "Fledermaus M"), ("W", "Fledermaus W")):
        e = ei(eifarben[g], rgba(FLED[g]["A"]), seed=4, gross=0.85, flecken=6)
        zeilen.append((name, [e] + [fledermaus(s, g) for s in range(1, 7)] + [fledermaus(4, g, "flug"), fledermaus(4, g, "haengen")]))
    tafel("FLEDERMAUS M/W – Ei + 6 Stufen, rechts fliegt und hängt kopfüber", zeilen, spalten,
          os.path.join(ziel, "fledermaus_entwurf.png"))

    zeilen = []
    for g, name in (("M", "Vampir M"), ("W", "Vampir W")):
        extra = [vampir("M", 6, zylinder=True, stock=True)] if g == "M" else []
        zeilen.append((name, [fledermaus(s, g) for s in (3, 4, 5, 6)] + [vampir(g, s) for s in (3, 4, 5, 6)] + extra))
    tafel("VAMPIRGESTALT – je Stufe: links die Fledermaus, rechts ihre Vampirgestalt", zeilen,
          ["Fl. 3", "Fl. 4", "Fl. 5", "Fl. 6", "3 Kind", "4 Teen", "5 ~18", "6 erwachsen", "6 Zylinder+Stock"],
          os.path.join(ziel, "vampir_entwurf.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HIER)
