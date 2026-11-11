# Bärbels Effekt-Animationen (Mark, 11.11.2026): Tentakelmonster will raus.
# Eigene Leinwand ETW×ETH mit dem Buch mittig (gleiche Lage wie die 76er-Sprites
# + Rand), weil die Tentakel weit aus dem Buch herausgreift. Das Frontend
# blendet die Figur währenddessen aus und zeigt diesen Streifen.
import math
import random
from PIL import Image, ImageDraw

from baerbel_design import zu, outline

ETW, ETH = 128, 120            # nach rechts/unten Platz für die Tentakel
RAND = 18                      # Lage der 76er-Leinwand in der Effekt-Leinwand (links/oben)
BUCH = (RAND + (76 - 52) // 2, RAND + (76 - 58) // 2)   # linke obere Ecke des Buchs

TENTAKEL_FRAMES = 44
TENTAKEL_MS = 80
SCHLAG_FRAME = 33

T_DUNKEL = (24, 70, 64, 255)
T_MITTEL = (46, 140, 112, 255)
T_HELL = (130, 214, 160, 255)
T_SAUGER = (244, 160, 196, 255)
SCHLEIM = (150, 240, 90, 255)
SCHLEIM_HELL = (226, 255, 176, 255)
K = (10, 24, 20, 255)


def glatt(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def tentakel_kette(f, bx, by):
    """Punkte (x, y, r) vom Ansatz im Spalt bis zur Spitze für Frame f."""
    if f < 11:
        return []
    if f <= 22:
        laenge = 44 * (1 - (1 - (f - 11) / 11) ** 2)
    elif f <= 33:
        laenge = 44 + (2 if f == 33 else 0)
    else:
        laenge = 44 * max(0.0, 1 - (f - 33) / 4)
    if laenge < 2:
        return []
    if f < 23:
        a0 = -12
    elif f < 31:
        a0 = -14 + 14 * math.sin((f - 23) * 0.9)     # tastet herum
    elif f <= 33:
        a0 = [-35, 20, 62][f - 31]                    # holt aus und klatscht runter
    else:
        a0 = 50
    n = 16
    seg = laenge / n
    w = math.radians(a0)
    x, y = bx, by
    pts = []
    ph = f * 0.75
    kringel = 0.2 if f < 31 else 0.07
    for i in range(n + 1):
        r = 4.8 * (1 - i / n) ** 0.8 + 0.7
        pts.append((x, y, r))
        # Wellen laufen zur Spitze, die Spitze rollt sich ein
        w += kringel * (0.6 + i / n) * math.sin(ph - i * 0.55)
        if f < 31 and i > n * 0.6:
            w -= 0.16 * (1 + 0.5 * math.sin(ph))
        x += math.cos(w) * seg
        y += math.sin(w) * seg
    return pts


def tentakel_frame(v, f, rnd_seed=5):
    img = Image.new("RGBA", (ETW, ETH), (0, 0, 0, 0))
    # Buch: rattert, Schließe springt auf, Spalt öffnet sich, knallt zu
    dx = 0
    if f < 6 or 36 <= f < 40:
        dx = 1 if f % 2 else -1
    if f < 6:
        spalt = 0
    elif f < 11:
        spalt = min(3, (f - 5) * 0.75)
    elif f < 36:
        spalt = 3 if f < 23 or f > 33 else 4
    else:
        spalt = max(0, 3 - (f - 35) * 1.5)
    buch = zu(v, spalt=spalt, schliesse_auf=4 <= f < 40, schreck=6 <= f < 40)
    bx0, by0 = BUCH[0] + dx, BUCH[1]
    img.alpha_composite(buch, (bx0, by0))

    t = Image.new("RGBA", (ETW, ETH), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    pts = tentakel_kette(f, bx0 + 42 + round(spalt) * 0.5, by0 + 26)
    for x, y, r in pts:
        d.ellipse([x - r - 0.6, y - r - 0.6, x + r + 0.6, y + r + 0.6], fill=T_DUNKEL)
    for x, y, r in pts:
        d.ellipse([x - r, y - r - 0.4, x + r - 0.6, y + r - 0.8], fill=T_MITTEL)
    for i, (x, y, r) in enumerate(pts[:-1]):
        nx, ny, _ = pts[i + 1]
        ang = math.atan2(ny - y, nx - x)
        # Unterseite (rechts der Laufrichtung) heller, mit Saugnäpfen
        ux, uy = -math.sin(ang), math.cos(ang)
        if r > 1.4:
            d.point((round(x + ux * r * 0.55), round(y + uy * r * 0.55)), fill=T_HELL)
        if i % 2 == 1 and r > 1.6:
            d.point((round(x + ux * r * 0.8), round(y + uy * r * 0.8)), fill=T_SAUGER)
        if i % 3 == 0 and r > 2:
            d.point((round(x - ux * r * 0.4), round(y - uy * r * 0.4)), fill=T_HELL)  # Glanz
    # Schleimtropfen: tropft beim Herumtasten, spritzt beim Klatschen
    rnd = random.Random(rnd_seed)
    if 15 <= f < 31 and pts:
        for k in range(2):
            t0 = 15 + k * 7
            if t0 <= f < t0 + 5:
                x, y, r = pts[min(len(pts) - 1, 9 + k * 3)]
                yy = y + r + (f - t0) ** 2 * 1.2
                d.rectangle([x, yy, x + 1, yy + 1], fill=SCHLEIM)
    if SCHLAG_FRAME <= f < SCHLAG_FRAME + 6:
        sx, sy = schlag_spitze(v)
        u = f - SCHLAG_FRAME
        for k in range(7):
            vx = rnd.uniform(-2.5, 2.5)
            vy = rnd.uniform(-3.5, -1)
            x = sx + vx * u * 1.6
            y = sy + vy * u * 1.6 + 0.5 * 0.9 * (u * 1.6) ** 2
            g = 2 if k % 2 else 1
            d.rectangle([x, y, x + g, y + g], fill=SCHLEIM)
            d.point((round(x), round(y)), fill=SCHLEIM_HELL)
    outline(t, K)
    img.alpha_composite(t)
    # Zuknallen: Staub und Sternchen
    if 37 <= f < 42:
        d2 = ImageDraw.Draw(img)
        u = f - 37
        for k, (ox, oy) in enumerate(((44, 4), (46, 26), (44, 46), (-2, 2), (20, -2))):
            x = bx0 + ox + (u + 1) * (2 if ox > 40 else -1 if ox < 0 else 0)
            y = by0 + oy - u * (1 if oy < 10 else 0)
            col = (255, 240, 150, 255) if k % 2 else (255, 255, 255, 255)
            d2.point((x, y), fill=col)
            if u < 3:
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    d2.point((x + ddx, y + ddy), fill=col)
    return img


def schlag_spitze(v):
    """Wo die Spitze beim Klatschen auftrifft (Effekt-Leinwand) — dort entsteht der Schleimfleck."""
    pts = tentakel_kette(SCHLAG_FRAME, BUCH[0] + 42 + 2, BUCH[1] + 26)
    x, y, _ = pts[-1]
    return round(x), round(y)


def tentakel_frames(v):
    return [tentakel_frame(v, f) for f in range(TENTAKEL_FRAMES)]
