# Futternapf (Mark, 12.11.2026): steht unten auf dem Bildschirm, bis ein Drache
# ihn leer frisst. Aufruf: python napf.py C:/DEV/PnPTool/frontend/public/pets
import os
import random
import sys

from PIL import Image, ImageDraw

W, H = 22, 13
K = (30, 14, 10, 255)


def napf():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Futterberg: Bröckchen und ein Stück Fleisch mit Knochen
    rnd = random.Random(7)
    for _ in range(26):
        x = rnd.randint(5, 16)
        y = rnd.randint(2, 6) + abs(x - 10.5) // 3
        c = rnd.choice([(150, 92, 44, 255), (186, 120, 60, 255), (120, 70, 34, 255)])
        d.rectangle([x, y, x + 1, y + 1], fill=c)
    d.ellipse([7, 1, 13, 5], fill=(196, 64, 60, 255))
    d.point((9, 2), fill=(240, 140, 130, 255))
    d.line([(12, 2), (16, 0)], fill=(244, 236, 214, 255), width=1)
    d.point((16, 0), fill=(255, 255, 240, 255))
    d.point((17, 1), fill=(255, 255, 240, 255))
    # Napf: roter Rand, dunkler Körper, Glanz
    d.polygon([(1, 6), (20, 6), (18, 11), (3, 11)], fill=(150, 34, 40, 255))
    d.rectangle([1, 6, 20, 7], fill=(214, 64, 60, 255))
    d.line([(3, 9), (7, 9)], fill=(236, 120, 110, 255))
    d.line([(4, 12), (17, 12)], fill=(90, 20, 26, 255))
    # Umriss
    px = img.load()
    out = img.copy()
    po = out.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] == 0 and any(
                0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                po[x, y] = K
    return out


if __name__ == "__main__":
    ziel = sys.argv[1]
    napf().save(os.path.join(ziel, "napf.png"))
    napf().resize((W * 10, H * 10), Image.NEAREST).save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "napf_vorschau.png")) if len(sys.argv) > 2 else None
    print("ok")
