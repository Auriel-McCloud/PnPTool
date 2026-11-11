# Vorschau: Schweben, Blinzeln, Verwandlung zwischen den drei Gestalten
import math, random, os
from PIL import Image, ImageDraw
from baerbel_design import VARIANTEN, zu

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 76, 80
BG = (60, 62, 70, 255)
V = list(VARIANTEN.values())


def puff(t, seed=3):
    """Verwandlungs-Wolke: wächst bis t=0.5 (deckt das Buch), zerfällt dann in Funken."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    cx, cy = W // 2, H // 2 - 2
    wachs = min(1.0, t / 0.45)
    zerfall = max(0.0, (t - 0.55) / 0.45)
    farben = [(190, 120, 255, 255), (240, 200, 255, 255), (255, 255, 255, 255), (140, 80, 220, 255)]
    for i in range(16):
        w = i / 16 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        dist = rnd.uniform(10, 22) * wachs + zerfall * 14
        r = rnd.uniform(6, 11) * wachs * (1 - zerfall) ** 1.3
        x = cx + math.cos(w + t * 2) * dist
        y = cy + math.sin(w + t * 2) * dist * 0.9
        if r >= 2:
            d.ellipse([x - r, y - r, x + r, y + r], fill=farben[3])
            d.ellipse([x - r + 1, y - r + 1, x + r - 2, y + r - 2], fill=farben[0])
            d.ellipse([x - r * 0.4, y - r * 0.6, x, y - r * 0.2], fill=farben[1])
    # Kern deckt das Buch zur Mitte der Verwandlung
    kr = 22 * math.sin(min(1, t / 0.9) * math.pi) ** 2
    if kr > 2:
        d.ellipse([cx - kr, cy - kr * 1.1, cx + kr, cy + kr * 1.1], fill=farben[0])
        d.ellipse([cx - kr * 0.6, cy - kr * 0.8, cx + kr * 0.2, cy - kr * 0.1], fill=farben[1])
    # Funken (Sternchen)
    for i in range(14):
        w = rnd.uniform(0, 2 * math.pi)
        dist = 8 + t * rnd.uniform(18, 34)
        x = round(cx + math.cos(w) * dist)
        y = round(cy + math.sin(w) * dist)
        if rnd.random() < 0.3 + t * 0.6 and t < 0.97:
            col = farben[2] if i % 2 else (255, 230, 120, 255)
            d.point((x, y), fill=col)
            if i % 3 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    d.point((x + dx, y + dy), fill=col)
    return img


def bild(var, lid=0.0, blick=0, bob=0, dx=0, effekt=None):
    img = Image.new("RGBA", (W, H), BG)
    b = zu(var, lid, blick)
    # Schatten am Boden
    sd = ImageDraw.Draw(img)
    sw = 14 - bob
    sd.ellipse([W // 2 - sw, H - 7, W // 2 + sw, H - 4], fill=(45, 46, 52, 255))
    img.alpha_composite(b, ((W - b.width) // 2 + dx, 8 + bob))
    if effekt is not None:
        img.alpha_composite(effekt)
    return img


frames, dauer = [], []


def add(im, ms):
    frames.append(im)
    dauer.append(ms)


def schwebe_bob(i):
    return round(math.sin(i / 12 * 2 * math.pi) * 2)


blinzel = [0.4, 1.0, 1.0, 0.4]
zaehler = [0]


def schweben(var, n, blinks=(), blick_plan=None):
    for i in range(n):
        k = zaehler[0]
        zaehler[0] += 1
        lid, blick = 0.0, 0
        for b0 in blinks:
            if b0 <= i < b0 + len(blinzel):
                lid = blinzel[i - b0]
        if blick_plan:
            blick = blick_plan(i)
        add(bild(var, lid, blick, schwebe_bob(k)), 90)


def verwandeln(von, nach):
    # Zittern
    for i in range(8):
        add(bild(von, 0, 0, schwebe_bob(zaehler[0]), dx=(1 if i % 2 else -1)), 50)
    n = 16
    for i in range(n):
        t = i / (n - 1)
        var = von if t < 0.5 else nach
        add(bild(var, 0, 0, schwebe_bob(zaehler[0]), effekt=puff(t)), 70)
        zaehler[0] += 1


klass, grim, gesicht = V
schweben(klass, 30)
verwandeln(klass, grim)
# Grimoire: schaut herum, blinzelt
schweben(grim, 44, blinks=(6, 30), blick_plan=lambda i: -2 if 14 <= i < 22 else (2 if 22 <= i < 28 else 0))
verwandeln(grim, gesicht)
schweben(gesicht, 44, blinks=(8, 26, 31), blick_plan=lambda i: 1 if 14 <= i < 24 else 0)
verwandeln(gesicht, klass)

S = 5
big = [f.convert("RGB").resize((W * S, H * S), Image.NEAREST) for f in frames]
big[0].save(f"{OUT}/verwandlung.gif", save_all=True, append_images=big[1:], duration=dauer, loop=0)

# Kontrollstreifen
idx = [34, 40, 45, 48, 52, 61, 62, 70, 76, 131, 132, 140]
st = Image.new("RGB", (W * len(idx), H))
for j, i in enumerate(idx):
    st.paste(frames[i].convert("RGB"), (j * W, 0))
st.resize((st.width * 3, st.height * 3), Image.NEAREST).save(f"{OUT}/kontrolle.png")
print(len(frames), sum(dauer))
