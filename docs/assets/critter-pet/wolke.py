"""Glückswolke (Xiangyun) für den Wolkenlauf des Drachen (Mark, 12.11.2026):
„chinesische Drachen erzeugen kleine Wolken unter ihren Klauen und laufen
darüber durch die Luft“. Eigener Streifen, das Frontend setzt die Wolken unter
seine Pfoten.

14 Frames à 110 ms: aufpuffen 0–2, schweben 3–9 (Locke dreht leicht, wippt),
zerfasern 10–13.
"""
import math
import random

from PIL import Image, ImageDraw

W, H = 36, 20
FRAMES = 14
MS = 110

HELL = (250, 252, 255, 255)
MITTE = (214, 230, 248, 255)
SCHATTEN = (150, 182, 222, 255)
LINIE = (70, 100, 150, 255)
GLANZ = (255, 236, 170, 255)

# Beulen: (x, y, r) in Leinwand-Pixeln bei voller Größe.
BEULEN = [(10, 11, 5.0), (17, 8.5, 6.2), (25, 10.5, 5.2), (14, 13, 4.2), (21, 13, 4.4)]
BODEN = 16  # flache Unterkante


def _form(skala: float, wipp: int, locke: float) -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, 11
    for bx, by, r in BEULEN:
        x = cx + (bx - 17.5) * skala
        y = cy + (by - 11) * skala + wipp
        rr = r * skala
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=MITTE)
    # flache Unterseite
    unten = cy + (BODEN - 11) * skala + wipp
    for y in range(H):
        for x in range(W):
            if y > unten and im.getpixel((x, y))[3]:
                im.putpixel((x, y), (0, 0, 0, 0))
    # Licht oben, Schatten unten
    px = im.load()
    for y in range(H):
        for x in range(W):
            if not px[x, y][3]:
                continue
            oben_frei = y == 0 or not px[x, y - 1][3]
            if y >= unten - 1.5 * skala:
                px[x, y] = SCHATTEN
            elif oben_frei or (y > 0 and px[x, y - 1] == HELL and y - 1 > 0 and not px[x, y - 2][3]):
                px[x, y] = HELL
    # Locke (Spirale) rechts — dreht sich ganz langsam
    if skala > 0.55:
        lx, ly = cx + 9 * skala, cy - 1 * skala + wipp
        for i in range(26):
            a = locke + i * 0.42
            r = (0.6 + i * 0.13) * skala
            x, y = round(lx + math.cos(a) * r), round(ly + math.sin(a) * r * 0.85)
            if 0 <= x < W and 0 <= y < H and px[x, y][3]:
                px[x, y] = SCHATTEN
        lx2 = cx - 7 * skala
        for i in range(18):
            a = -locke + i * 0.45 + math.pi
            r = (0.5 + i * 0.12) * skala
            x, y = round(lx2 + math.cos(a) * r), round(ly + 1 + math.sin(a) * r * 0.8)
            if 0 <= x < W and 0 <= y < H and px[x, y][3]:
                px[x, y] = SCHATTEN
    # Kontur
    neu = im.copy()
    npx = neu.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and px[xx, yy][3] and px[xx, yy] != LINIE:
                    npx[x, y] = LINIE
                    break
    return neu


def frame(i: int) -> Image.Image:
    rnd = random.Random(40 + i)
    if i <= 2:
        skala = 0.45 + 0.55 * (i + 1) / 3
        im = _form(skala, 0, i * 0.3)
        # Funkeln beim Aufpuffen
        for _ in range(3 - i):
            x, y = rnd.randrange(2, W - 2), rnd.randrange(1, 8)
            im.putpixel((x, y), GLANZ)
        return im
    if i <= 9:
        t = (i - 3) / 7
        return _form(1.0, round(math.sin(t * 2 * math.pi) * 0.6), 0.9 + t * 1.2)
    # Zerfasern: kleiner, Löcher, Ränder fransen aus
    z = (i - 9) / 4  # 0.25 … 1
    im = _form(1.0 - 0.15 * z, 1, 2.1 + z * 0.4)
    px = im.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] and rnd.random() < z * 0.8:
                px[x, y] = (0, 0, 0, 0)
            elif px[x, y][3]:
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, round(a * (1 - z * 0.55)))
    return im


def sheet() -> tuple[Image.Image, dict]:
    s = Image.new("RGBA", (W * FRAMES, H), (0, 0, 0, 0))
    for i in range(FRAMES):
        s.alpha_composite(frame(i), (i * W, 0))
    return s, {"breite": W, "hoehe": H, "frames": FRAMES, "ms": MS}


if __name__ == "__main__":
    import sys

    ziel = sys.argv[1] if len(sys.argv) > 1 else "wolke_vorschau.png"
    s, _ = sheet()
    s.resize((s.width * 6, s.height * 6), Image.NEAREST).save(ziel)
