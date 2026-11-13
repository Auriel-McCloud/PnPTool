# ENTWURF 13.11.2026 (noch nicht von Mark abgenommen, noch nicht im Frontend):
# die restlichen Wachstumsstufen des Drachen und das Einkringeln zum Schlafen.
# Mark: „immer größer, eleganter und wie chinesische Drachen … zum Schlafen
# einkringeln“. Stufen bisher: Ei, Schlüpfling (drache_jung.py), heutiger
# Drache (drache_final.py). Neu: Stufe 3–6 als Parameter-Satz EINER Figur —
# gilt damit automatisch für Drache, Eis- und Blitzdrache (drachen_varianten).
# Aufruf: python drache_stufen_entwurf.py <zielordner>
import math
import os
import sys
from types import SimpleNamespace as NS

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drache_final as dr  # noqa: E402
import drache_jung as dj  # noqa: E402
import drachen_varianten as dv  # noqa: E402

P = dr.PAL
ORIGINAL = dict(dr.PAL)
BG = (24, 26, 38, 255)
SCHRITT = 1.4      # Abstand der Körperkreise entlang der Wirbelsäule (px)
LUECKE = 14.0      # ab diesem Abstand entlang des Körpers gilt eine Berührung als „andere Windung“
GW, GH = 260, 170  # Arbeitsleinwand, wird später zugeschnitten
BODEN = 150        # Fußlinie auf der Arbeitsleinwand

# Je Stufe: L = Körperlänge waagrecht, lam = Abstand der Beinpaare (= Wellenlänge),
# amp = Höhe der Körperbögen, rt/rm = Radius Schwanzspitze/Rumpf, hals = (vor, hoch,
# S-Schwung), schn = Schnauzenlänge, horn/zweige = Geweih, mh = Rückenmähne,
# km/kmn = Kopfmähne Länge/Strähnen, wl = Schnurrhaare, quaste = Schwanzflamme,
# bein/bb/krallen = Beinlänge/-breite/Krallen (Beine bleiben kurz — Marks Grenze),
# a/eng/hub = Ring beim Schlafen (Außenradius, Einzug und Anheben je Windung).
STUFEN = {
    "baby": NS(name="Schlüpfling", L=20, lam=11, amp=0.8, hub_s=0, schlank=0.1, rt=1.6, rm=4.8, hals=(5, 6, 0.0), kr=(7.4, 6.6),
               schn=3.4, horn=3, zweige=0, mh=2.4, km=4, kmn=2, bart=3, wl=4, quaste=3.5, bein=3.5, bb=2, krallen=1,
               tuft=False, platten=False, schuppen=0, braue=False, zahn=False, a=7.5, eng=3.0, hub=4.5, baby=True),
    "jung": NS(name="Jungtier (heute)", L=50, lam=22, amp=2.0, hub_s=2, schlank=0.22, rt=1.5, rm=4.3, hals=(6, 9, 0.0), kr=(7.2, 6.2),
               schn=4.5, horn=8, zweige=1, mh=3.0, km=6, kmn=3, bart=4, wl=10, quaste=5.5, bein=4, bb=2, krallen=1,
               tuft=False, platten=False, schuppen=0, braue=False, zahn=False, a=11.0, eng=3.5, hub=5.5, baby=False),
    "s3": NS(name="Halbstarker", L=60, lam=30, amp=3.5, hub_s=7, schlank=0.24, rt=1.4, rm=4.4, hals=(7, 11, 0.3), kr=(7.2, 6.2),
             schn=5.0, horn=10, zweige=1, mh=3.5, km=8, kmn=3, bart=5, wl=13, quaste=7, bein=4.5, bb=2, krallen=2,
             tuft=False, platten=False, schuppen=1, braue=False, zahn=False, a=12.5, eng=3.5, hub=5.5, baby=False),
    "s4": NS(name="Jungdrache", L=70, lam=32, amp=4.5, hub_s=9, schlank=0.28, rt=1.4, rm=4.6, hals=(8, 14, 0.55), kr=(7.3, 6.2),
             schn=5.5, horn=12, zweige=2, mh=4.0, km=10, kmn=3, bart=6, wl=16, quaste=9, bein=5, bb=3, krallen=2,
             tuft=True, platten=True, schuppen=1, braue=True, zahn=False, a=14.0, eng=3.5, hub=5.8, baby=False),
    "s5": NS(name="Drache", L=80, lam=34, amp=5.5, hub_s=11, schlank=0.32, rt=1.3, rm=4.8, hals=(9, 17, 0.8), kr=(7.4, 6.1),
             schn=6.0, horn=14, zweige=2, mh=4.5, km=12, kmn=4, bart=7, wl=20, quaste=11, bein=5, bb=3, krallen=3,
             tuft=True, platten=True, schuppen=2, braue=True, zahn=True, a=15.5, eng=3.5, hub=6.0, baby=False),
    "s6": NS(name="Ehrwürdiger Drache", L=90, lam=36, amp=6.5, hub_s=14, schlank=0.36, rt=1.3, rm=5.0, hals=(10, 20, 1.0),
             kr=(7.6, 6.0), schn=6.5, horn=17, zweige=3, mh=5.0, km=15, kmn=5, bart=8, wl=25, quaste=13, bein=5.5,
             bb=3, krallen=3, tuft=True, platten=True, schuppen=2, braue=True, zahn=True, a=17.0, eng=3.5,
             hub=6.2,
             baby=False),
}
NEU = ["s3", "s4", "s5", "s6"]


def farbe(c):
    return P[c] if isinstance(c, str) else c


def dunkler(c, f=0.8):
    r, g, b, a = P[c]
    return (int(r * f), int(g * f), int(b * f), a)


# ── Zeichner: malt Farbe und merkt sich je Pixel, zu welcher Körperstelle es gehört ──
class Z:
    def __init__(self):
        self.img = Image.new("RGBA", (GW, GH), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.sm = Image.new("F", (GW, GH), -1000.0)  # Position entlang des Körpers
        self.ds = ImageDraw.Draw(self.sm)
        self.rk = Image.new("I", (GW, GH), 0)        # Malreihenfolge (höher = weiter vorn)
        self.dk = ImageDraw.Draw(self.rk)
        self.rang = 1

    def ell(self, cx, cy, rx, ry, c, s):
        box = [round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)]
        self.d.ellipse(box, fill=farbe(c))
        self.ds.ellipse(box, fill=s)
        self.dk.ellipse(box, fill=self.rang)

    def poly(self, pts, c, s):
        self.d.polygon(pts, fill=farbe(c))
        self.ds.polygon(pts, fill=s)
        self.dk.polygon(pts, fill=self.rang)

    def line(self, pts, c, s, width=1):
        self.d.line(pts, fill=farbe(c), width=width)
        self.ds.line(pts, fill=s, width=width)
        self.dk.line(pts, fill=self.rang, width=width)

    def point(self, xy, c, s):
        xy = (round(xy[0]), round(xy[1]))
        self.d.point(xy, fill=P[c])
        self.ds.point(xy, fill=s)
        self.dk.point(xy, fill=self.rang)

    def fertig(self):
        """Auto-Outline außen (wie drache_final) plus Trennlinie, wo eine Windung
        über einer anderen liegt (eingekringelt)."""
        px, sm, rk = self.img.load(), self.sm.load(), self.rk.load()
        frei = {P["F"], P["M"]}
        out = self.img.copy()
        po = out.load()
        for y in range(GH):
            for x in range(GW):
                c = px[x, y]
                nachbarn = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                if c[3] == 0:
                    for nx, ny in nachbarn:
                        if 0 <= nx < GW and 0 <= ny < GH and px[nx, ny][3] and px[nx, ny] not in frei:
                            po[x, y] = P["K"]
                            break
                elif c not in frei:
                    for nx, ny in nachbarn:
                        if 0 <= nx < GW and 0 <= ny < GH and px[nx, ny][3] and px[nx, ny] not in frei \
                                and abs(sm[x, y] - sm[nx, ny]) > LUECKE and rk[x, y] < rk[nx, ny]:
                            po[x, y] = P["K"]
                            break
        return out


def radius(st, u):
    r = st.rt + (st.rm - st.rt) * min(1.0, u / (0.55 if st.schuppen >= 2 else 0.42)) ** 0.75
    return r


def abtasten(fein):
    """Feine Punktfolge → Punkte in gleichem Abstand SCHRITT, mit Bogenlänge s."""
    pts, s, rest = [(fein[0][0], fein[0][1], 0.0)], 0.0, SCHRITT
    for (x0, y0), (x1, y1) in zip(fein, fein[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        while seg >= rest and seg > 0:
            k = rest / seg
            x0, y0 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
            seg -= rest
            s += SCHRITT
            pts.append((x0, y0, s))
            rest = SCHRITT
        rest -= seg
    return pts


def kette_wach(st, welle=0.0):
    """Wirbelsäule im Stehen: Beinpaare an den Tiefpunkten, dazwischen ein Bogen
    nach oben, Schwanz steigt nach hinten an, Hals im S-Schwung zum Kopf."""
    x0 = 60.0
    xf = x0 + st.L - 6      # Vorderbeine
    xr = xf - st.lam        # Hinterbeine
    yb = BODEN - st.bein - st.rm
    fein = []
    for i in range(801):
        x = x0 + st.L * i / 800
        y = yb - st.amp * (1 - math.cos(2 * math.pi * (x - xf) / st.lam)) / 2
        if x < xr:
            k = (xr - x) / (xr - x0)
            y -= st.hub_s * k ** 1.8 + math.sin(welle) * 1.2 * k
        fein.append((x, y))
    koerper_ende = len(abtasten(fein)) - 1
    ex, ey = fein[-1]
    dx, dy, sk = st.hals
    p0, p3 = (ex, ey), (ex + dx, ey - dy)
    p1 = (ex + 4 + 9 * sk, ey - dy * 0.10)
    p2 = (ex + dx - 4 - 12 * sk, ey - dy * 0.75)
    for i in range(1, 201):
        t = i / 200
        m = 1 - t
        fein.append((m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                     m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]))
    roh = abtasten(fein)
    s_koerper = roh[koerper_ende][2]
    gesamt = roh[-1][2]
    pts = []
    for x, y, s in roh:
        u = min(1.0, s / s_koerper)
        r = radius(st, u)
        if s > s_koerper:  # Hals wird zum Kopf hin schlanker
            r *= 1 - st.schlank * (s - s_koerper) / max(gesamt - s_koerper, 1)
        pts.append(NS(x=x, y=y, s=s, u=u, r=r, hals=s > s_koerper, bx=0.0, by=1.0))
    for i, q in enumerate(pts):  # Bauchrichtung = Körperrichtung um 90° gedreht
        v, w = pts[max(i - 2, 0)], pts[min(i + 2, len(pts) - 1)]
        tx, ty = w.x - v.x, w.y - v.y
        n = math.hypot(tx, ty) or 1
        q.bx, q.by = -ty / n, tx / n
    bein_h = min(range(len(pts)), key=lambda i: abs(pts[i].x - xr) + (1000 if pts[i].hals else 0))
    bein_v = min(range(len(pts)), key=lambda i: abs(pts[i].x - xf) + (1000 if pts[i].hals else 0))
    return pts, (bein_h, bein_v), s_koerper


def koerper(z, st, pts, idxs, phase, ohne_d=(0, 0), maehne=True, nur_maehne=False):
    """Mähne, dunkle Lage, Grundfarbe, Bauch, Details für einen zusammenhängenden
    Abschnitt der Kette. `ohne_d` = so viele Kreise am Anfang/Ende ohne dunkle Lage
    (Naht zu einem schon gemalten Nachbar-Abschnitt)."""
    if maehne and not st.baby:
        for i in idxs:
            p = pts[i]
            if i % 3 or p.s < 9:
                continue
            h = st.mh * (0.55 + 0.45 * p.u) * (1.15 if p.hals else 1.0)
            fl = math.sin(phase + p.s * 0.25) * 1.0
            # Zacke steht auf dem Rücken (entgegen der Bauchrichtung), leicht nach hinten geneigt
            rx_, ry_ = -p.bx, -p.by
            fx_, fy_ = p.x + rx_ * (p.r - 1), p.y + ry_ * (p.r - 1)
            z.poly([(fx_ + ry_ * 2, fy_ - rx_ * 2), (fx_ + rx_ * (h + 1) + ry_ * 1.5 + fl * abs(ry_), fy_ + ry_ * (h + 1) - rx_ * 1.5),
                    (fx_ - ry_ * 1.5, fy_ + rx_ * 1.5)], "M", p.s)
    elif maehne:
        for i in idxs:
            p = pts[i]
            if i % 5 or p.s < 6:
                continue
            fl = math.sin(phase + p.s * 0.4) * 0.7
            z.poly([(p.x - 1.5, p.y - p.r + 1), (p.x - 2.5 + fl, p.y - p.r - 2), (p.x + 1, p.y - p.r + 1)], "M", p.s)
    if nur_maehne:
        return
    n = len(idxs)
    for j, i in enumerate(idxs):
        if j < ohne_d[0] or j >= n - ohne_d[1]:
            continue
        p = pts[i]
        z.ell(p.x, p.y + 0.6, p.r, p.r, "D", p.s)
    for i in idxs:
        p = pts[i]
        z.ell(p.x - 0.2, p.y - 0.3, max(p.r - 0.7, 0.6), max(p.r - 0.7, 0.6), "R", p.s)
    for i in idxs:
        p = pts[i]
        if p.r > 2.2:
            z.ell(p.x + p.bx * p.r * 0.7, p.y + p.by * p.r * 0.7, p.r * (0.4 * abs(p.by) + 0.17 * abs(p.bx)),
                  p.r * (0.17 * abs(p.by) + 0.4 * abs(p.bx)), "Y", p.s)
    for i in idxs:
        p = pts[i]
        if p.r <= 2.2:
            continue
        if st.platten and i % 3 == 0:      # Bauchplatten
            z.line([(p.x + p.bx * p.r * 0.58, p.y + p.by * p.r * 0.58), (p.x + p.bx * p.r * 0.85, p.y + p.by * p.r * 0.85)], "O", p.s)
        elif not st.platten and i % 5 == 0:
            z.point((p.x, p.y + p.r * 0.55), "O", p.s)
        if i % 5 == 0:                     # Glanzschuppen oben
            z.point((p.x - 1, p.y - p.r * 0.4), "L", p.s)
        if st.schuppen >= 1 and i % 5 == 2 and not p.hals:
            z.point((p.x, p.y - p.r * 0.05), "D", p.s)
        if st.schuppen >= 2 and i % 5 == 4:
            z.point((p.x, p.y - p.r * 0.62), "L", p.s)


def beine(z, st, pts, anker, phase, leg):
    """Kurze Beine (Marks Grenze: nicht länger), bei den Großen mit Schenkel und Pfote."""
    for idx, ph in zip(anker, (0.0, math.pi)):
        p = pts[idx]
        sw = math.sin(phase * 2 + ph) * leg
        for off, c in ((-1.5, "D"), (1.5, "R")):
            vorz = 1 if c == "R" else -1
            fx = p.x + off + sw * vorz
            hub = max(0.0, math.cos(phase * 2 + ph) * vorz) * leg * 0.7
            fy = BODEN - hub
            z.line([(p.x + off, p.y + p.r - 1), (fx, fy)], c, p.s, width=2)
            if st.bb >= 3:
                z.ell(p.x + off - 0.5, p.y + p.r + 0.5, 2.2, 2.4, c, p.s)   # Schenkel
                z.line([(fx - 1, fy), (fx + 2, fy)], c, p.s)                # Pfote
            for k in range(st.krallen):
                z.point((fx + 1 + k, fy), "H", p.s)


def flammenbueschel(z, st, pts, anker, phase):
    """Kleine Flammen an den Fersen — typisch für chinesische Drachen."""
    for idx in anker:
        p = pts[idx]
        fl = math.sin(phase * 1.5 + idx) * 1.0
        x = p.x - 2.5
        z.poly([(x, BODEN - 4), (x - 5, BODEN - 6 + fl), (x - 3, BODEN - 3), (x - 5, BODEN - 1 + fl), (x, BODEN - 1)], "F", p.s)


def quaste(z, st, pts, phase, hoch=False):
    """Schwanzflamme: mehrere Zungen in Verlängerung der Schwanzspitze."""
    a, b = pts[0], pts[min(4, len(pts) - 1)]
    wx, wy = a.x - b.x, a.y - b.y
    if hoch:
        wx, wy = wx * 0.3, -abs(wy) - 2
    n = math.hypot(wx, wy) or 1
    wx, wy = wx / n, wy / n
    q = st.quaste
    fl = math.sin(phase * 1.5) * 1.5

    def pkt(vor, quer, flack=0.0):
        return (a.x + wx * vor - wy * quer, a.y + wy * vor + wx * quer + flack)

    if q < 6.5:
        z.poly([pkt(-1, -1), pkt(q, -2, fl), pkt(q * 0.7, 0, fl), pkt(q, 3, fl), pkt(-1, 1)], "F", 0)
        return
    z.poly([pkt(-1, -1.5), pkt(q * 0.55, -q * 0.42, fl), pkt(q * 0.5, -q * 0.12, fl), pkt(q, -q * 0.08, fl * 1.3),
            pkt(q * 0.6, q * 0.1, fl), pkt(q * 0.75, q * 0.42, fl), pkt(q * 0.3, q * 0.22), pkt(-1, 1.5)], "F", 0)
    if q >= 9:  # heller Kern
        z.poly([pkt(0, -0.8), pkt(q * 0.5, -q * 0.05, fl * 0.6), pkt(0, 0.8)], "Y", 0)


def geweih(z, bx, by, laenge, zweige, s, hinten=False):
    """Geweih-Horn. Das hintere ist dunkler und liegt flacher, damit sich die
    beiden bei langen Hörnern nicht zu einem Kamm vermischen."""
    c = dunkler("H", 0.78) if hinten and laenge > 4 else "H"
    if laenge <= 4:
        z.line([(bx, by - 1), (bx - 1, by - 1 - laenge)], c, s, width=2)
        return
    if hinten and laenge > 9:
        r1, r2 = (-0.72, -0.69), (-0.90, -0.44)
    else:
        r1, r2 = (-0.42, -0.91), (-0.68, -0.73)
    h = laenge / 2
    p0 = (bx, by)
    p1 = (bx + r1[0] * h, by + r1[1] * h)
    p2 = (p1[0] + r2[0] * h, p1[1] + r2[1] * h)
    z.line([p0, p1, p2], c, s, width=2)
    stellen = {0: [], 1: [0.42], 2: [0.34, 0.72], 3: [0.28, 0.55, 0.82]}[zweige]
    tl = 2.6 + laenge * 0.1
    for f in stellen:
        if f <= 0.5:
            sx, sy = p0[0] + (p1[0] - p0[0]) * f * 2, p0[1] + (p1[1] - p0[1]) * f * 2
        else:
            sx, sy = p1[0] + (p2[0] - p1[0]) * (f - 0.5) * 2, p1[1] + (p2[1] - p1[1]) * (f - 0.5) * 2
        z.line([(sx, sy), (sx + tl * (0.1 if hinten else 0.45), sy - tl)], c, s, width=1)


def kopf(z, st, hx, hy, s, phase=0.0, blink=False, mund=False, schnurr=0.0, liegt=None):
    """Kopf wie in drache_final, Schnauze/Geweih/Mähne/Schnurrhaare wachsen mit.
    `liegt` = Bodenhöhe, wenn er schläft (Schnurrhaare und Bart hängen)."""
    rx, ry = st.kr
    hx, hy = round(hx), round(hy)
    for n, bx in enumerate((hx - 3, hx + 1) if st.baby else (hx - 4, hx + 1)):
        geweih(z, bx, hy - 4, st.horn, st.zweige, s, hinten=n == 0)
    # Kopfmähne: Strähnen fächern nach hinten auf, bei den Großen lang und wallend
    for i in range(st.kmn):
        f = i / max(st.kmn - 1, 1)
        my = hy - 3 + f * 8 if not st.baby else hy - 1 + i * 3
        lang = st.km * (0.8 + 0.3 * f) * (0.55 if liegt else 1.0)
        win = math.radians(-12 + 62 * f + (20 if liegt else 0)) if st.km >= 7 else 0.08 + 0.1 * i
        tx = hx - 4 - lang * math.cos(win) + math.sin(phase + i) * 1.2
        ty = my + lang * math.sin(win)
        if lang < 7:
            z.poly([(hx - 4, my - 2), (tx, ty), (hx - 4, my + 2)], "M", s)
        else:
            w = math.sin(phase + i * 1.3) * 1.2
            mx, mmy = (hx - 4 + tx) / 2, (my + ty) / 2
            z.poly([(hx - 3, my - 2), (mx + 1, mmy - 2.4 + w), (tx, ty), (mx - 1, mmy + 1.4 + w), (hx - 3, my + 2)], "M", s)
    z.ell(hx, hy + 0.6, rx, ry, "D", s)
    z.ell(hx - 0.3, hy, rx - 0.5, ry - 0.6, "R", s)
    z.ell(hx - 2, hy - 3, 2.5, 1.2, "L", s)
    # Schnauze
    scx = hx + 7 + (st.schn - 4.5) * 0.8 - (1.0 if st.baby else 0)
    z.ell(scx, hy + 2, st.schn, 3, "D", s)
    z.ell(scx - 0.2, hy + 1.5, st.schn - 0.4, 2.5, "R", s)
    rechts = scx + st.schn
    z.point((rechts - 1.5, hy), "K", s)
    if st.schn >= 5.5:  # Nasenhöcker
        z.point((rechts - 2.5, hy - 1), "L", s)
    if mund:
        z.line([(hx + 4, hy + 4), (rechts - 1.5, hy + 4)], "K", s)
    else:
        z.line([(hx + 5, hy + 3), (rechts - 2.5, hy + 3)], "D", s)
    if st.zahn:
        z.point((rechts - 4, hy + 4), "W", s)
    # Kinnbart
    z.poly([(hx + 3, hy + 4), (hx + 1 + schnurr - (st.bart - 4) * 0.4, hy + 4 + st.bart), (hx + 6, hy + 5)], "M", s)
    # Auge
    if blink:
        z.line([(hx, hy - 1), (hx + 4, hy - 1)], "K", s)
    elif st.baby:
        z.ell(hx + 2, hy - 1, 2.8, 3.2, "W", s)
        z.d.rectangle([hx + 3, hy - 2, hx + 4, hy + 1], fill=P["B"])
        z.point((hx + 3, hy - 2), "W", s)
        z.point((hx + 2, hy + 1), "W", s)
    else:
        z.ell(hx + 2, hy - 1.2, 2.2, 2.8, "W", s)
        z.d.rectangle([hx + 3, hy - 2, hx + 4, hy], fill=P["B"])
        z.point((hx + 3, hy - 2), "W", s)
    if not st.baby:
        z.line([(hx - 1, hy - 5), (hx + 5, hy - 4)], "K", s)  # Braue
    if st.braue:  # Flammenbraue
        z.poly([(hx + 1, hy - 5), (hx - 5, hy - 9 + math.sin(phase) * 0.6), (hx - 2, hy - 5)], "M", s)
    # Schnurrhaare: lang und geschwungen, bei den Großen im S-Bogen
    wl = st.wl
    for oben in (True, False):
        pfad = []
        for k in range(14):
            u = k / 13
            wackel = math.sin(u * 4 + phase + (0 if oben else 1)) * (1 + schnurr) * u
            if liegt is not None:      # hängen nach vorn auf den Boden
                x = rechts - 1.5 + wl * (0.55 if oben else 0.3) * math.sin(u * 1.7)
                y = min(liegt - 1, hy + 1 + (wl * 0.45 * u if oben else wl * 0.5 * u ** 0.7) + wackel * 0.3)
            elif oben:
                x = rechts - 1.5 + wl * 0.78 * math.sin(u * 1.9)
                y = hy + 1 - wl * 0.42 * u ** 1.5 + wackel
            else:
                x = rechts - 1.5 + wl * 0.6 * math.sin(u * 2.5)
                y = hy + 2 + wl * 0.5 * u + wackel * 0.8
            pfad.append((x, y))
        z.line(pfad, "M", s, width=1)


def zuschneiden(img, rand=2, unten=None):
    b = img.getbbox()
    u = b[3] + rand if unten is None else unten
    return img.crop((b[0] - rand, b[1] - rand, b[2] + rand, u))


def roh_wach(st, phase=0.0, blink=False, leg=0.0, mund=False, schnurr=0.0, welle=0.0):
    z = Z()
    pts, anker, _ = kette_wach(st, welle)
    beine(z, st, pts, anker, phase, leg)
    koerper(z, st, pts, list(range(len(pts))), phase)
    if st.tuft:
        flammenbueschel(z, st, pts, anker, phase)
    quaste(z, st, pts, phase)
    e = pts[-1]
    kopf(z, st, e.x + 1, e.y - 1, e.s + 6, phase, blink, mund, schnurr)
    return z.fertig()


def wach(st, **kw):
    """Fertiges Bild, unten bündig mit der Fußlinie + 2 px."""
    return zuschneiden(roh_wach(st, **kw), unten=BODEN + 3)


# ── Eingekringelt schlafen ────────────────────────────────────────────────
FLACH = 0.38  # Ring von schräg vorn gesehen: Höhe/Breite der Ellipse


def kette_ring(st, atem=0.0):
    """Körper als gestapelte Spirale (wie ein aufgerolltes Tau): Brust außen
    unten, jede weitere Windung enger und höher, die Schwanzspitze stellt sich
    oben in der Mitte auf. Punkte Schwanz → Hals."""
    wach_pts, anker, s_koerper = kette_wach(st)
    gesamt = wach_pts[-1].s
    s_bein = [wach_pts[i].s for i in anker]
    cx, cy = 110.0, 110.0
    phi0 = math.radians(38)
    a0 = st.a * (1 + 0.03 * atem)
    pts = []
    phi, s = phi0, gesamt
    while s >= 0:
        runden = (phi - phi0) / (2 * math.pi)
        a = max(a0 - st.eng * runden, 1.5)
        b = a * FLACH
        hub = st.hub * runden * (1 + 0.06 * atem)
        u_ges = s / gesamt
        if u_ges < 0.10:  # Schwanzspitze stellt sich auf
            hub += (1 - u_ges / 0.10) ** 2 * (2 + st.quaste * 0.2)
        u = min(1.0, s / s_koerper)
        r = radius(st, u)
        if s > s_koerper:
            r *= 1 - st.schlank * (s - s_koerper) / max(gesamt - s_koerper, 1)
        pts.append(NS(x=cx + a * math.cos(phi), y=cy + b * math.sin(phi) - hub, s=s, u=u, r=r,
                      hals=s > s_koerper, tiefe=b * math.sin(phi), halb=int(phi // math.pi), phi=phi, bx=0.0, by=1.0))
        phi += SCHRITT / math.hypot(a * math.sin(phi), b * math.cos(phi))
        s -= SCHRITT
    pts.reverse()
    boden = cy + st.a * FLACH + st.rm
    return pts, s_bein, boden


def roh_ring(st, atem=0.0, phase=0.0):
    z = Z()
    pts, s_bein, boden = kette_ring(st, atem)
    gruppen = {}
    for i, p in enumerate(pts):
        gruppen.setdefault(p.halb, []).append(i)
    reihen = sorted(gruppen.values(), key=lambda g: sum(pts[i].tiefe for i in g) / len(g))
    for g in reihen:
        z.rang += 1
        hinten = [i for i in g if math.sin(pts[i].phi) < 0.2]  # Rückenmähne nur hinten/seitlich
        koerper(z, st, pts, hinten, phase, ohne_d=(len(hinten), 0), nur_maehne=True)
        koerper(z, st, pts, g, phase, ohne_d=(0 if g[0] == 0 else 3, 0 if g[-1] == len(pts) - 1 else 3), maehne=False)
        if g[0] == 0:
            quaste(z, st, pts, phase, hoch=True)
        for sb in s_bein:  # eingezogene Pfoten schauen vorn unten heraus
            i = min(g, key=lambda k: abs(pts[k].s - sb))
            p = pts[i]
            if abs(p.s - sb) < SCHRITT and math.sin(p.phi) > 0.35:
                z.ell(p.x + 1, p.y + p.r - 0.3, 3, 1.6, "D", p.s)
                z.ell(p.x + 0.8, p.y + p.r - 0.6, 2.4, 1.1, "R", p.s)
                for k in range(max(2, st.krallen)):
                    z.point((p.x + 2 + k, p.y + p.r + 0.6), "H", p.s)
    z.rang += 1
    e = pts[-1]
    hy = boden - st.kr[1] - 0.5 + (0.6 if atem > 0.5 else 0)
    kopf(z, st, e.x + 5, hy, e.s + 6, phase, blink=True, schnurr=-0.5, liegt=boden)
    return z.fertig(), boden


def ring(st, **kw):
    img, boden = roh_ring(st, **kw)
    return zuschneiden(img, unten=round(boden) + 3)


# ── Einkringeln (Übergang) ────────────────────────────────────────────────
def _winkel(pts):
    """Richtungen Kopf → Schwanz, fortlaufend (ohne 2π-Sprünge), und Längen."""
    w, l = [], []
    for i in range(len(pts) - 1, 0, -1):
        dx, dy = pts[i - 1].x - pts[i].x, pts[i - 1].y - pts[i].y
        a = math.atan2(dy, dx)
        if w:
            while a - w[-1] > math.pi:
                a -= 2 * math.pi
            while a - w[-1] < -math.pi:
                a += 2 * math.pi
        w.append(a)
        l.append(math.hypot(dx, dy))
    return w, l


def roh_einkringeln(st, t, phase=0.0):
    """t = 0 liegt er gestreckt am Boden, t = 1 ist er eingekringelt. Die
    Krümmung wird überblendet — er rollt sich vom Schwanz her zum Kopf ein."""
    P_, _, s_k = kette_wach(st)
    Q, s_bein, boden = kette_ring(st)
    n = min(len(P_), len(Q))
    P_, Q = P_[-n:], Q[-n:]
    brust = min(range(n), key=lambda i: abs(P_[i].s - s_k))
    qx, qy = P_[brust].x - Q[-1].x + 2, BODEN - boden
    def weich(v):
        v = max(0.0, min(1.0, v))
        return v * v * (3 - 2 * v)

    # Der Schwanz rollt sich zuerst ein, die Windung wandert dann zum Kopf.
    ki = [weich(t * 1.6 - 0.6 * i / (n - 1)) for i in range(n)]
    k = ki[-1]       # Kopf-Ende
    ks = ki[0]       # Schwanz-Ende
    wa, la = _winkel(P_)
    wb, lb = _winkel(Q)
    while wb[0] - wa[0] > math.pi:
        wb = [v - 2 * math.pi for v in wb]
    while wb[0] - wa[0] < -math.pi:
        wb = [v + 2 * math.pi for v in wb]
    x = P_[-1].x * (1 - k) + (Q[-1].x + qx) * k
    y = (P_[-1].y + st.bein) * (1 - k) + (Q[-1].y + qy) * k
    pts = [None] * n
    for j in range(n):
        i = n - 1 - j
        q = Q[i]
        pts[i] = NS(x=x, y=y, s=P_[i].s, u=P_[i].u, r=P_[i].r, hals=P_[i].hals, halb=q.halb, tiefe=q.tiefe, phi=q.phi,
                    bx=P_[i].bx * (1 - ki[i]), by=P_[i].by * (1 - ki[i]) + ki[i])
        if j < n - 1:
            w = wa[j] * (1 - ki[i]) + wb[j] * ki[i]
            l = la[j] * (1 - ki[i]) + lb[j] * ki[i]
            x, y = x + math.cos(w) * l, y + math.sin(w) * l
    z = Z()
    gruppen = {}
    for i, q in enumerate(pts):
        gruppen.setdefault(q.halb if ks > 0.25 else 0, []).append(i)
    for g in sorted(gruppen.values(), key=lambda g: sum(pts[i].tiefe for i in g) / len(g)):
        z.rang += 1
        mit = [i for i in g if ki[i] < 0.6 or math.sin(pts[i].phi) < 0.2]
        koerper(z, st, pts, mit, phase, nur_maehne=True)
        koerper(z, st, pts, g, phase, ohne_d=(0 if g[0] == 0 else 3, 0 if g[-1] == n - 1 else 3), maehne=False)
        if g[0] == 0:
            quaste(z, st, pts, phase, hoch=ks > 0.7)
    z.rang += 1
    e = pts[-1]
    hy0, hy1 = e.y - 1, BODEN - st.kr[1] - 0.5
    kopf(z, st, e.x + 1 + 4 * k, hy0 * (1 - k) + hy1 * k, e.s + 6, phase, blink=k > 0.35, schnurr=-0.5 * k,
         liegt=BODEN if k > 0.6 else None)
    return z.fertig()


def roh_hinlegen(st, k, phase=0.0, blink=False):
    """Er lässt sich auf den Bauch sinken (Beine verschwinden unter dem Körper)."""
    z = Z()
    pts, anker, _ = kette_wach(st)
    for q in pts:
        q.y += st.bein * k
    beine(z, st, pts, anker, phase, 0.0)
    koerper(z, st, pts, list(range(len(pts))), phase)
    quaste(z, st, pts, phase)
    e = pts[-1]
    kopf(z, st, e.x + 1, e.y - 1, e.s + 6, phase, blink)
    return z.fertig()


def schlaf_film(st):
    """Wach → hinlegen → einkringeln → schlafen (atmen) → aufwachen."""
    roh, ms = [], []
    for i in range(10):
        roh.append(roh_wach(st, phase=i / 10 * 2 * math.pi, blink=i in (6, 7))); ms.append(110)
    for i in range(1, 5):
        roh.append(roh_hinlegen(st, i / 4, phase=i * 0.4, blink=i >= 3)); ms.append(90)
    N = 14
    for i in range(1, N):
        roh.append(roh_einkringeln(st, i / N, phase=i * 0.3)); ms.append(80)
    dx = None
    for i in range(36):
        at = math.sin(i / 18 * 2 * math.pi)
        img, boden = roh_ring(st, atem=at, phase=i / 18 * 2 * math.pi * 0.5)
        if dx is None:  # Ring an dieselbe Stelle setzen wie das Ende des Einkringelns
            P_, _, s_k = kette_wach(st)
            Q, _, _ = kette_ring(st)
            brust = min(range(len(P_)), key=lambda j: abs(P_[j].s - s_k))
            dx, dy = round(P_[brust].x - Q[-1].x + 2), round(BODEN - boden)
        verschoben = Image.new("RGBA", img.size, (0, 0, 0, 0))
        verschoben.paste(img, (dx, dy))
        roh.append(verschoben); ms.append(150)
    for i in range(N - 1, 0, -2):
        roh.append(roh_einkringeln(st, i / N, phase=i * 0.3)); ms.append(70)
    for i in range(3, 0, -1):
        roh.append(roh_hinlegen(st, i / 4, phase=i * 0.4)); ms.append(80)
    # gemeinsamer Ausschnitt über alle Frames
    box = None
    for f in roh:
        b = f.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    box = (box[0] - 2, box[1] - 2, box[2] + 2, BODEN + 3)
    return [f.crop(box) for f in roh], ms


# ── Tafeln ────────────────────────────────────────────────────────────────
def mit_farbe(art, fn):
    if art != "drache":
        dv.palette(art)
    try:
        return fn()
    finally:
        dr.PAL.update(ORIGINAL)
        dr.KEIN_OUTLINE.clear()
        dr.KEIN_OUTLINE.add(dr.PAL["F"])


def reihe(bilder, abstand=6, hoehe=None):
    h = hoehe or max(b.height for b in bilder)
    w = sum(b.width for b in bilder) + abstand * (len(bilder) + 1)
    r = Image.new("RGBA", (w, h + 4), BG)
    x = abstand
    for b in bilder:
        r.alpha_composite(b, (x, h + 2 - b.height))
        x += b.width + abstand
    return r


def stapel(reihen, sc):
    w = max(r.width for r in reihen)
    t = Image.new("RGBA", (w, sum(r.height for r in reihen)), BG)
    y = 0
    for r in reihen:
        t.alpha_composite(r, (0, y))
        y += r.height
    return t.resize((t.width * sc, t.height * sc), Image.NEAREST)


def alle_wach():
    """Alle sechs Stufen im Größenvergleich: Baby und heutiger Drache aus den
    abgenommenen Generatoren, Stufe 3–6 neu."""
    alt = zuschneiden(dr.frame(welle=0.0, amp=3.0), unten=None)
    return [zuschneiden(dj.baby()), alt] + [wach(STUFEN[k]) for k in NEU]


def alle_ring():
    return [ring(STUFEN[k]) for k in ["baby", "jung"] + NEU]


def gif(frames, name, ms, scale):
    w, h = max(f.width for f in frames), max(f.height for f in frames)
    out = []
    for f in frames:
        bg = Image.new("RGBA", (w, h), BG)
        bg.alpha_composite(f, ((w - f.width) // 2, h - f.height))
        out.append(bg.resize((w * scale, h * scale), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
    out[0].save(name, save_all=True, append_images=out[1:], duration=ms, loop=0, disposal=2)


def tafel(sc=3):
    """Eine Farbe: oben Stufe 1–4, darunter 5–6, unten alle eingekringelt; mit Nummern."""
    from PIL import ImageFont
    w_, r_ = alle_wach(), alle_ring()
    zeilen = [reihe(w_[:4], abstand=8), reihe(w_[4:], abstand=8), reihe(r_, abstand=8)]
    bild = stapel(zeilen, sc)
    d = ImageDraw.Draw(bild)
    font = ImageFont.load_default()
    y = 0
    for zeile, teile, start in ((zeilen[0], w_[:4], 1), (zeilen[1], w_[4:], 5), (zeilen[2], r_, 1)):
        x = 8
        for n, t in enumerate(teile):
            d.text((x * sc, y * sc + 2), str(start + n), fill=(150, 156, 180, 255), font=font)
            x += t.width + 8
        y += zeile.height
    return bild


if __name__ == "__main__":
    ziel = sys.argv[1]
    os.makedirs(ziel, exist_ok=True)
    tafel().save(f"{ziel}/stufen_rot.png")
    for art in ("eisdrache", "blitzdrache"):
        mit_farbe(art, tafel).save(f"{ziel}/stufen_{art}.png")
    gross = STUFEN["s6"]
    stapel([reihe([wach(gross), ring(gross)], abstand=10)], 5).save(f"{ziel}/ehrwuerdig.png")
    fr, ms = schlaf_film(gross)
    gif(fr, f"{ziel}/einkringeln.gif", ms, 4)
    for kx in NEU:
        print(kx, STUFEN[kx].name, "wach", wach(STUFEN[kx]).size, "ring", ring(STUFEN[kx]).size)
    print("ok")
