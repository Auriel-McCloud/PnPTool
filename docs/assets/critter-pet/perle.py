# Drachenperle (Mark, 13.11.2026): die leuchtende Perle des Ehrwürdigen Drachen —
# ein Ding auf dem Bildschirm, das man werfen kann. Dazu die Rufzeichen über
# seinem Kopf: „?“ beim Suchen, „!“ wenn er sie sieht oder sie ihm wegfliegt.
# Aufruf: python perle.py C:/DEV/PnPTool/frontend/public/pets
#   → perle.png (8 Frames à 16×16: Flammenkranz züngelt), frage.png, ausruf.png
import math
import os
import sys

from PIL import Image, ImageDraw

G, N = 16, 8
K = (30, 26, 60, 255)


def perle(f):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    t = f / N * 2 * math.pi
    # Flammen schlagen hinter der Perle nach oben (wie auf den alten Bildern):
    # drei Zungen, die abwechselnd höher züngeln.
    for k, (fx, breit) in enumerate(((4.0, 2.0), (7.5, 2.6), (11.0, 2.0))):
        hoch = 4.0 + 2.0 * math.sin(t + k * 2.1)
        neig = math.sin(t * 2 + k) * 1.0
        d.polygon([(fx - breit, 8), (fx + neig, 7 - hoch), (fx + breit, 8)], fill=(240, 120, 30, 255))
        d.polygon([(fx - breit * 0.5, 8), (fx + neig * 0.6, 8.5 - hoch * 0.6), (fx + breit * 0.5, 8)],
                  fill=(255, 214, 90, 255))
    # Perle: runde Kugel mit Outline, Schatten unten rechts, Glanz oben links
    d.ellipse([3, 6, 12, 15], fill=K)
    d.ellipse([4, 7, 11, 14], fill=(110, 180, 232, 255))
    d.ellipse([4, 7, 10, 13], fill=(206, 236, 255, 255))
    d.ellipse([5, 8, 7, 10], fill=(255, 255, 255, 255))
    # Schimmer wandert über die Kugel, ein Funke umkreist sie
    d.point((8 + round(math.sin(t) * 1.5), 12), fill=(160, 216, 250, 255))
    d.point((round(7.5 + math.cos(t) * 6.5), round(10.5 + math.sin(t) * 4.5)), fill=(255, 240, 170, 255))
    return img


def zeichen(zeilen, farbe):
    h, w = len(zeilen), max(len(z) for z in zeilen)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, z in enumerate(zeilen):
        for x, c in enumerate(z):
            if c == "k":
                im.putpixel((x, y), K)
            elif c == "w":
                im.putpixel((x, y), farbe)
    return im


FRAGE = [
    ".kkkkk.",
    "kwwwwwk",
    "kwkkkwk",
    "kkk.kwk",
    "..kkwwk",
    "..kwwkk",
    "..kwk..",
    "..kkk..",
    "..kwk..",
    "..kkk..",
]
AUSRUF = [
    "kkkk",
    "kwwk",
    "kwwk",
    "kwwk",
    "kwwk",
    "kwwk",
    "kkkk",
    "kwwk",
    "kwwk",
    "kkkk",
]

if __name__ == "__main__":
    ziel = sys.argv[1]
    s = Image.new("RGBA", (G * N, G), (0, 0, 0, 0))
    for f in range(N):
        s.alpha_composite(perle(f), (f * G, 0))
    s.save(os.path.join(ziel, "perle.png"))
    zeichen(FRAGE, (220, 235, 255, 255)).save(os.path.join(ziel, "frage.png"))
    zeichen(AUSRUF, (255, 214, 90, 255)).save(os.path.join(ziel, "ausruf.png"))
    if len(sys.argv) > 2:  # Vorschau
        bg = Image.new("RGBA", (G * N + 20, G + 4), (24, 26, 38, 255))
        bg.alpha_composite(s, (2, 2))
        bg.alpha_composite(zeichen(FRAGE, (220, 235, 255, 255)), (G * N + 3, 3))
        bg.alpha_composite(zeichen(AUSRUF, (255, 214, 90, 255)), (G * N + 13, 3))
        bg.resize((bg.width * 8, bg.height * 8), Image.NEAREST).save(sys.argv[2])
    print("ok")
