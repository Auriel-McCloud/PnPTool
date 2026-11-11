# Bärbel-Sprites exportieren -> frontend/public/pets/baerbel/ + sprite.json
# Alle Animationen auf derselben Leinwand (76x76), Buch mittig. Schweben/Bob
# und Fortbewegung macht das Frontend (frontend/src/pets/flug.ts).
import json, math, os, random, sys
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
from baerbel_design import VARIANTEN, zu, offen, outline  # noqa: E402

ZIEL = os.path.normpath(os.path.join(HIER, "..", "..", "..", "frontend", "public", "pets", "baerbel"))
W = H = 76
V = list(VARIANTEN.values())
ANIM = {}


def leinwand():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def mittig_zu(b):
    im = leinwand()
    im.alpha_composite(b, ((W - b.width) // 2, (H - b.height) // 2))
    return im


def offen_bild(b, dy=0):
    im = leinwand()
    im.alpha_composite(b, (0, dy))
    return im


def sheet(name, frames, ms):
    s = Image.new("RGBA", (W * len(frames), H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.alpha_composite(f, (i * W, 0))
    s.save(os.path.join(ZIEL, f"{name}.png"))
    ANIM[name] = {"frames": len(frames), "ms": ms}


def puff(t, seed=3):
    """Verwandlungs-Wolke (gleich wie baerbel_vorschau.py, auf 76x76)."""
    img = leinwand()
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    cx, cy = W // 2, H // 2
    wachs = min(1.0, t / 0.45)
    zerfall = max(0.0, (t - 0.55) / 0.45)
    farben = [(190, 120, 255, 255), (240, 200, 255, 255), (255, 255, 255, 255), (140, 80, 220, 255)]
    for i in range(16):
        w = i / 16 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        dist = rnd.uniform(10, 20) * wachs + zerfall * 12
        r = rnd.uniform(6, 10) * wachs * (1 - zerfall) ** 1.3
        x = cx + math.cos(w + t * 2) * dist
        y = cy + math.sin(w + t * 2) * dist * 0.9
        if r >= 2:
            d.ellipse([x - r, y - r, x + r, y + r], fill=farben[3])
            d.ellipse([x - r + 1, y - r + 1, x + r - 2, y + r - 2], fill=farben[0])
            d.ellipse([x - r * 0.4, y - r * 0.6, x, y - r * 0.2], fill=farben[1])
    kr = 22 * math.sin(min(1, t / 0.9) * math.pi) ** 2
    if kr > 2:
        d.ellipse([cx - kr, cy - kr * 1.1, cx + kr, cy + kr * 1.1], fill=farben[0])
        d.ellipse([cx - kr * 0.6, cy - kr * 0.8, cx + kr * 0.2, cy - kr * 0.1], fill=farben[1])
    for i in range(14):
        w = rnd.uniform(0, 2 * math.pi)
        dist = 8 + t * rnd.uniform(14, 28)
        x = round(cx + math.cos(w) * dist)
        y = round(cy + math.sin(w) * dist)
        if rnd.random() < 0.3 + t * 0.6 and t < 0.97:
            col = farben[2] if i % 2 else (255, 230, 120, 255)
            d.point((x, y), fill=col)
            if i % 3 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    d.point((x + dx, y + dy), fill=col)
    return img


def schlag(i, n):
    t = i / n
    if t < 0.4:
        u = t / 0.4
        return 50 - 85 * (0.5 - 0.5 * math.cos(u * math.pi)), 0.9 * math.sin(u * math.pi), -round(2 * math.sin(u * math.pi))
    u = (t - 0.4) / 0.6
    return -35 + 85 * (0.5 - 0.5 * math.cos(u * math.pi)), -0.7 * math.sin(u * math.pi), round(1.5 * math.sin(u * math.pi))


def seiten():
    """Zerknitterte Seite (liegt) und flache Seite (fällt)."""
    P, p, g, K = (244, 234, 206, 255), (196, 180, 146, 255), (150, 120, 70, 255), (70, 52, 30, 255)
    knitter = Image.new("RGBA", (14, 11), (0, 0, 0, 0))
    d = ImageDraw.Draw(knitter)
    d.polygon([(1, 6), (3, 2), (7, 1), (11, 2), (13, 6), (11, 9), (6, 10), (2, 9)], fill=P)
    for a, b in (((3, 3), (6, 6)), ((6, 6), (11, 4)), ((6, 6), (5, 9)), ((9, 7), (12, 7))):
        d.line([a, b], fill=p)
    d.point((4, 7), fill=g)
    d.point((8, 3), fill=g)
    d.point((10, 8), fill=g)
    outline(knitter, K)
    flach = Image.new("RGBA", (14, 11), (0, 0, 0, 0))
    d = ImageDraw.Draw(flach)
    d.polygon([(1, 2), (12, 1), (13, 9), (2, 9)], fill=P)
    for y in (3, 5, 7):
        d.line([(3, y), (10, y)], fill=p)
    outline(flach, K)
    knitter.save(os.path.join(ZIEL, "seite.png"))
    flach.save(os.path.join(ZIEL, "seite_fliegt.png"))


if __name__ == "__main__":
    os.makedirs(ZIEL, exist_ok=True)
    for g, v in enumerate(V, start=1):
        # Schweben (zu): nur das Lesebändchen weht
        sheet(f"schweben_{g}", [mittig_zu(zu(v, band=round(2 * math.sin(i / 12 * 2 * math.pi)))) for i in range(12)], 140)
        # Flattern (offen): 16 Frames, Abschlag schnell
        fr = []
        for i in range(16):
            w, n, bob = schlag(i, 16)
            fr.append(offen_bild(offen(v, w, n, band=i / 16 * 2 * math.pi), bob))
        sheet(f"flattern_{g}", fr, 45)
        # Auf-/Zuklappen: zu -> Deckel fast senkrecht -> Flügelstellung
        kl = [mittig_zu(zu(v))] + [offen_bild(offen(v, w, 0, band=0)) for w in (86, 76, 64, 50)]
        sheet(f"klappen_{g}", kl, 60)
    # Blinzeln: Gestalt 2 schaut sich um und blinzelt, Gestalt 3 blinzelt
    plan2 = [(0, -1), (0, -2), (0, -2), (0, -2), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 2), (0, 2),
             (0, 2), (0, 1), (0, 0), (0.4, 0), (1, 0), (1, 0), (0.4, 0), (0, 0)]
    sheet("blinzeln_2", [mittig_zu(zu(V[1], lid, bl)) for lid, bl in plan2], 110)
    plan3 = [(0.4, 0), (1, 0), (1, 0), (0.4, 0), (0, 0)]
    sheet("blinzeln_3", [mittig_zu(zu(V[2], lid, bl)) for lid, bl in plan3], 70)
    # Verwandlungswolke (Effekt über dem Buch; Gestaltwechsel bei Frame 8)
    sheet("verwandeln", [puff(i / 15) for i in range(16)], 70)
    seiten()
    # Herz vom Drachen mitbenutzen
    herz = os.path.join(ZIEL, "..", "drache", "herz.png")
    Image.open(herz).save(os.path.join(ZIEL, "herz.png"))
    info = {"breite": W, "hoehe": H, "gestalten": len(V), "animationen": ANIM,
            "seite": {"breite": 14, "hoehe": 11}, "verwandelnWechselFrame": 8}
    with open(os.path.join(ZIEL, "sprite.json"), "w", encoding="utf8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print(json.dumps(ANIM))
