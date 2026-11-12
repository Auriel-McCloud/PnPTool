# Farb-/Atem-Varianten des kleinen Drachen (Mark, 12.11.2026: „Wolke Salamander“
# ist in Wahrheit unser Babydrache, nur silberblau). Gleiche Figur aus
# drache_final.py, nur umgefärbt; statt Feuer spuckt er Eis bzw. Blitze.
# Mark: der blauere (blauer Körper, silberner Bauch/Mähne) ist der Eisdrache,
# der silberne (silberner Körper, blaue Mähne) der Blitzdrache.
# Benutzt von sprites_exportieren.py (Aufruf mit Art als zweitem Argument).
import random

from PIL import Image, ImageDraw

import drache_final as dr

PALETTEN = {
    # Blitzdrache: Silberkörper, blaue Mähne
    "blitzdrache": {
        "K": (16, 22, 44, 255), "D": (92, 108, 138, 255), "R": (172, 188, 212, 255),
        "L": (238, 245, 252, 255), "Y": (140, 196, 242, 255), "O": (92, 146, 210, 255),
        "H": (214, 234, 255, 255), "M": (70, 150, 240, 255), "F": (110, 196, 255, 255),
    },
    # Eisdrache: blauer Körper, silberner Bauch und Mähne
    "eisdrache": {
        "K": (12, 22, 52, 255), "D": (44, 84, 150, 255), "R": (96, 148, 214, 255),
        "L": (196, 224, 250, 255), "Y": (210, 220, 234, 255), "O": (150, 164, 186, 255),
        "H": (236, 242, 250, 255), "M": (196, 208, 226, 255), "F": (232, 240, 252, 255),
    },
}


def palette(art):
    """Färbt die Drachenfigur um (wirkt auf alle folgenden dr.frame-Aufrufe)."""
    dr.PAL.update(PALETTEN[art])
    dr.KEIN_OUTLINE.clear()
    dr.KEIN_OUTLINE.add(dr.PAL["F"])


# Gleiches Format wie feuer.png (56×28, 16 Frames à 70 ms) — das Frontend
# lädt einfach /pets/<art>/feuer.png.
FW, FH, N = 56, 28, 16


def eis_sheet():
    """Frostatem: kalter Kegel, Eiskristalle, zerfällt in Schneeflocken."""
    s = Image.new("RGBA", (FW * N, FH), (0, 0, 0, 0))
    for f in range(N):
        rnd = random.Random(f * 7 + 3)
        laenge = FW * min(1.0, (f + 1) / 5) * (1 - 0.06 * ((f * 5) % 3) if 5 <= f <= 11 else 1)
        zerfall = max(0.0, (f - 11) / 4)
        for x in range(FW):
            if x > laenge:
                continue
            breite = 1.5 + x * 0.30
            for y in range(FH):
                dy = abs(y - FH / 2 + 0.5)
                if dy > breite or x > laenge - dy * 0.9 - rnd.uniform(0, 7):
                    continue
                if rnd.random() < zerfall * 0.9 or rnd.random() < 0.12 + x / FW * 0.25:
                    continue  # luftiger als Feuer: Nebelschwaden
                kern = 1 - dy / max(breite, 1)
                kalt = kern * (1 - x / FW * 0.6) + rnd.uniform(-0.15, 0.15) - zerfall * 0.5
                if kalt > 0.72:
                    c = (250, 254, 255, 255)
                elif kalt > 0.48:
                    c = (190, 236, 255, 240)
                elif kalt > 0.25:
                    c = (110, 196, 250, 220)
                else:
                    c = (70, 130, 220, 170)
                s.putpixel((f * FW + x, y), c)
        # Eiskristalle (kleine Sterne) im Strahl
        d = ImageDraw.Draw(s)
        for _ in range(4 + round(zerfall * 6)):
            if laenge < 8:
                break
            kx = rnd.uniform(6, laenge - 2)
            ky = FH / 2 + rnd.uniform(-1, 1) * (1 + kx * 0.28) + zerfall * rnd.uniform(0, 5)
            if ky < 1 or ky > FH - 2:
                continue
            gx, gy = f * FW + round(kx), round(ky)
            w = (255, 255, 255, 255)
            d.point((gx, gy), fill=w)
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d.point((gx + ddx, gy + ddy), fill=(170, 230, 255, 255))
    return s


def blitz_sheet():
    """Blitzatem: zackige Entladungen mit Verästelungen, flackernd."""
    s = Image.new("RGBA", (FW * N, FH), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    for f in range(N):
        rnd = random.Random(f * 13 + 5)
        laenge = FW * min(1.0, (f + 1) / 4)
        zerfall = max(0.0, (f - 11) / 4)
        if f >= 12 and f % 2 == 1:
            # Nachflackern: nur Funken
            for _ in range(6 - (f - 12)):
                fx, fy = rnd.uniform(4, FW - 4), rnd.uniform(5, FH - 5)
                d.point((f * FW + round(fx), round(fy)), fill=(220, 240, 255, 255))
            continue
        for b in range(2 if f < 12 else 1):
            pts = [(0.0, FH / 2)]
            x, y = 0.0, FH / 2
            while x < laenge * (1 - zerfall * 0.5):
                x += rnd.uniform(3, 6)
                y = max(3, min(FH - 4, y + rnd.uniform(-4, 4) * (0.4 + x / FW)))
                pts.append((x, y))
            ox = f * FW
            p = [(ox + a, c) for a, c in pts]
            if len(p) < 2:
                continue
            haupt = b == 0
            d.line(p, fill=(80, 120, 255, 160), width=3 if haupt else 2)   # Leuchten
            d.line(p, fill=(150, 220, 255, 255), width=2 if haupt else 1)
            d.line(p, fill=(255, 255, 255, 255), width=1)
            # Verästelungen
            for a, c in pts[2::2]:
                if rnd.random() < 0.6:
                    ex_, ey = a + rnd.uniform(2, 6), c + rnd.choice((-1, 1)) * rnd.uniform(3, 6)
                    ey = max(1, min(FH - 2, ey))
                    d.line([(ox + a, c), (ox + ex_, ey)], fill=(170, 210, 255, 255), width=1)
        # Funken an der Spitze
        for _ in range(3):
            fx = min(FW - 2, laenge) - rnd.uniform(0, 6)
            fy = FH / 2 + rnd.uniform(-8, 8)
            d.point((f * FW + round(fx), round(fy)), fill=(255, 255, 210, 255))
    return s


def atem_sheet(art):
    return eis_sheet() if art == "eisdrache" else blitz_sheet()
