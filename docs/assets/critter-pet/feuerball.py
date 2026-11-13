# Feuerball (Mark, 13.11.2026: „Feuerbälle schießen, die weiter fliegen“) —
# das Geschoss der Drachen ab dem Halbstarken. Je Atem ein Streifen:
# Feuerball, Eisball (Eisdrache), Kugelblitz (Blitzdrache).
# Aufruf: python feuerball.py C:/DEV/PnPTool/frontend/public/pets [vorschau.png]
#   → ball_feuer.png, ball_eis.png, ball_blitz.png (je 6 Frames à 28×16,
#     Flug nach rechts, Schweif links; das Frontend spiegelt und dreht).
import math
import os
import random
import sys

from PIL import Image, ImageDraw

B, H, N = 28, 16, 6
MX, MY = 20.5, 8.0  # Mitte der Kugel

FARBEN = {
    "feuer": dict(kern=(255, 250, 210), hell=(255, 214, 90), mittel=(245, 130, 30), dunkel=(200, 60, 24), rand=(110, 30, 20)),
    "eis": dict(kern=(255, 255, 255), hell=(200, 240, 255), mittel=(110, 195, 245), dunkel=(60, 120, 215), rand=(30, 60, 130)),
    "blitz": dict(kern=(255, 255, 255), hell=(255, 250, 170), mittel=(170, 210, 255), dunkel=(110, 130, 235), rand=(50, 50, 130)),
}


def c(pal, k):
    return (*pal[k], 255)


def ball(art, f):
    pal = FARBEN[art]
    z = random.Random(f * 31 + len(art))
    img = Image.new("RGBA", (B, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    t = f / N * 2 * math.pi
    if art == "feuer":
        # Schweif: drei züngelnde Zungen, außen dunkel, innen hell
        for k, (dy, lang) in enumerate(((-3.0, 11), (0.0, 17), (3.0, 12))):
            l = lang + 2.5 * math.sin(t + k * 2.0)
            w = math.sin(t * 2 + k) * 1.6
            d.polygon([(MX - 2, MY + dy - 2.2), (MX - l, MY + dy + w), (MX - 2, MY + dy + 2.2)], fill=c(pal, "dunkel"))
            d.polygon([(MX - 2, MY + dy - 1.3), (MX - l * 0.68, MY + dy + w * 0.6), (MX - 2, MY + dy + 1.3)], fill=c(pal, "mittel"))
        d.polygon([(MX - 2, MY - 1.6), (MX - 9 - math.sin(t) * 2, MY), (MX - 2, MY + 1.6)], fill=c(pal, "hell"))
        for _ in range(4):  # Funken
            img.putpixel((int(z.uniform(1, MX - 8)), int(z.uniform(2, H - 3))), c(pal, z.choice(("hell", "mittel"))))
    elif art == "eis":
        # Schweif: kalter Dunst und Kristallsplitter
        for k in range(3):
            l = 12 + k * 3 + 2 * math.sin(t + k)
            d.line([(MX - 3, MY + (k - 1) * 3), (MX - l, MY + (k - 1) * 4.2)], fill=c(pal, "dunkel"))
        d.polygon([(MX - 2, MY - 2), (MX - 12 - math.sin(t) * 2, MY), (MX - 2, MY + 2)], fill=c(pal, "mittel"))
        for _ in range(7):
            x, y = int(z.uniform(1, MX - 6)), int(z.uniform(2, H - 3))
            img.putpixel((x, y), c(pal, z.choice(("kern", "hell", "hell"))))
            if z.random() < 0.4 and x + 1 < B:
                img.putpixel((x + 1, y), c(pal, "mittel"))
    else:
        # Kugelblitz: zuckende Bögen rund um die Kugel, kurzer Funkenschweif
        for k in range(4):
            w = t * 0.7 + k * math.pi / 2 + z.uniform(-0.4, 0.4)
            pts = [(MX + math.cos(w) * 3.5, MY + math.sin(w) * 3.5)]
            for s in range(1, 4):
                r = 3.5 + s * 1.6
                pts.append((MX + math.cos(w + z.uniform(-0.5, 0.5)) * r, MY + math.sin(w + z.uniform(-0.5, 0.5)) * r))
            d.line(pts, fill=c(pal, "mittel"))
            d.line(pts[:2], fill=c(pal, "hell"))
        for _ in range(6):
            x, y = int(z.uniform(2, MX - 7)), int(MY + z.uniform(-3.5, 3.5))
            img.putpixel((x, y), c(pal, z.choice(("hell", "mittel", "dunkel"))))
    # Kugel: Rand, Schale, heller Kern (pulsiert leicht)
    p = 0.4 * math.sin(t * 2)
    d.ellipse([MX - 5.6, MY - 5.6, MX + 5.6, MY + 5.6], fill=c(pal, "rand"))
    d.ellipse([MX - 4.8, MY - 4.8, MX + 4.8, MY + 4.8], fill=c(pal, "mittel" if art != "blitz" else "dunkel"))
    d.ellipse([MX - 3.6 - p, MY - 3.6 - p, MX + 3.6 + p, MY + 3.6 + p], fill=c(pal, "hell" if art != "blitz" else "mittel"))
    d.ellipse([MX - 2.0, MY - 2.4, MX + 2.4, MY + 2.0], fill=c(pal, "kern" if art != "feuer" else "hell"))
    d.ellipse([MX - 0.6, MY - 1.6, MX + 1.6, MY + 0.6], fill=c(pal, "kern"))
    if art == "eis":  # Facetten
        d.line([(MX - 3, MY + 1), (MX, MY + 4)], fill=c(pal, "dunkel"))
        img.putpixel((int(MX + 2), int(MY + 3)), c(pal, "dunkel"))
    return img


def streifen(art):
    s = Image.new("RGBA", (B * N, H), (0, 0, 0, 0))
    for f in range(N):
        s.alpha_composite(ball(art, f), (f * B, 0))
    return s


if __name__ == "__main__":
    ziel = sys.argv[1]
    for art in FARBEN:
        streifen(art).save(os.path.join(ziel, f"ball_{art}.png"))
    if len(sys.argv) > 2:
        bg = Image.new("RGBA", (B * N + 4, (H + 2) * 3 + 2), (24, 26, 38, 255))
        for i, art in enumerate(FARBEN):
            bg.alpha_composite(streifen(art), (2, 2 + i * (H + 2)))
        bg.resize((bg.width * 6, bg.height * 6), Image.NEAREST).save(sys.argv[2])
    print("ok")
