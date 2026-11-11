# Vorschau Flattern: Deckel schlagen wie Flügel, Rahmen wandert
import math, os
from PIL import Image, ImageDraw
from baerbel_design import VARIANTEN, offen

OUT = os.path.dirname(os.path.abspath(__file__))
V = list(VARIANTEN.values())
N = 16          # Frames pro Flügelschlag
MS = 45


def schlag(i):
    """Abschlag schnell (40 %), Aufschlag langsamer (60 %)."""
    t = i / N
    if t < 0.4:
        u = t / 0.4
        winkel = 50 - 85 * (0.5 - 0.5 * math.cos(u * math.pi))   # 50 -> -35
        nach = 0.9 * math.sin(u * math.pi)                        # Seiten hängen oben
        bob = -round(2 * math.sin(u * math.pi))                   # Körper hebt sich
    else:
        u = (t - 0.4) / 0.6
        winkel = -35 + 85 * (0.5 - 0.5 * math.cos(u * math.pi))
        nach = -0.7 * math.sin(u * math.pi)
        bob = round(1.5 * math.sin(u * math.pi))
    return winkel, nach, bob


def sprite_frames(v, lid_plan=None):
    fr = []
    for i in range(N):
        w, n, bob = schlag(i)
        fr.append((offen(v, w, n, band=i / N * 2 * math.pi), bob))
    return fr


# 1) Streifen aller Frames (Kontrolle)
st = Image.new("RGBA", (76 * N, 80), (60, 62, 70, 255))
for i, (f, bob) in enumerate(sprite_frames(V[1])):
    st.alpha_composite(f, (i * 76, 2 + bob))
st.resize((st.width * 2, st.height * 2), Image.NEAREST).save(f"{OUT}/flattern_streifen.png")

# 2) Vorschau: alle drei Gestalten flattern quer durchs Bild
BW, BH = 300, 130
frames = []
for vi, v in enumerate(V):
    fr = sprite_frames(v)
    n = 72
    for k in range(n):
        f, bob = fr[k % N]
        img = Image.new("RGBA", (BW, BH), (60, 62, 70, 255))
        x = -60 + (BW + 40) * k / n
        y = 30 + math.sin(k / n * 2 * math.pi * 1.5) * 12 + bob
        img.alpha_composite(f, (round(x), round(y)))
        frames.append(img.convert("RGB").resize((BW * 3, BH * 3), Image.NEAREST))
frames[0].save(f"{OUT}/flattern.gif", save_all=True, append_images=frames[1:], duration=MS, loop=0)

# 3) auf der Stelle, groß
gr = []
for k in range(N * 3):
    f, bob = sprite_frames(V[2])[k % N] if k == 0 else (None, None)
print("ok", len(frames))
