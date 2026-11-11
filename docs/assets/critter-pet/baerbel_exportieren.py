# Bärbel-Sprites exportieren -> frontend/public/pets/baerbel/ + sprite.json
# Alle Animationen auf derselben Leinwand (76x76), Buch mittig. Schweben/Bob
# und Fortbewegung macht das Frontend (frontend/src/pets/flug.ts).
import json, math, os, random, sys
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
from baerbel_design import VARIANTEN, zu, offen, outline  # noqa: E402
from baerbel_effekte import (ETH, ETW, RAND, SCHLAG_FRAME, TENTAKEL_MS,  # noqa: E402
                             schlag_spitze, tentakel_frames)

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


PW = 112  # Wolken-Leinwand (größer als das Buch, mittig darüber)


def puff(t, seed=3):
    """Verwandlungswolke, wabernd (Mark, 11.11.2026: „intensiver oder länger,
    die könnte ruhig ein wenig wabern“). Phasen: aufquellen (0–0,25), wabern
    und das Buch ganz verdecken (0,25–0,75, Gestaltwechsel bei 0,5),
    zerfallen in aufsteigende Funken (0,75–1)."""
    img = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    cx, cy = PW // 2, PW // 2
    quell = glatt(min(1.0, t / 0.25))
    zerfall = glatt(max(0.0, (t - 0.75) / 0.25))
    dunkel, mittel, hell, rosa = (96, 40, 170, 255), (160, 90, 235, 255), (222, 186, 255, 255), (255, 150, 220, 255)
    weiss, gold = (255, 255, 255, 255), (255, 228, 120, 255)
    # Blasen im Kreis, die wabern (Radius und Lage schwingen) und langsam kreisen
    blasen = []
    for i in range(22):
        w0 = i / 22 * 2 * math.pi + rnd.uniform(-0.25, 0.25)
        dist0 = rnd.uniform(8, 26)
        r0 = rnd.uniform(8, 14)
        ph = rnd.uniform(0, 2 * math.pi)
        fq = rnd.uniform(2.5, 4.5)
        w = w0 + t * 2.2
        wab = math.sin(t * fq * 2 * math.pi + ph)
        dist = dist0 * (0.4 + 0.6 * quell) + zerfall * 22 + wab * 4
        r = r0 * quell * (1 - zerfall) ** 1.4 * (1 + 0.28 * wab)
        x = cx + math.cos(w) * dist
        y = cy + math.sin(w) * dist * 0.9 - zerfall * 10
        blasen.append((x, y, r, ph))
    for x, y, r, ph in blasen:  # dunkler Rand
        if r >= 2:
            d.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1], fill=dunkel)
    for x, y, r, ph in blasen:
        if r >= 2:
            d.ellipse([x - r, y - r, x + r - 1, y + r - 1], fill=mittel)
    for x, y, r, ph in blasen:  # Glanzkuppen, die mitwabern
        if r >= 4:
            hx = x - r * 0.35 + math.sin(t * 9 + ph) * 1.2
            hy = y - r * 0.45
            d.ellipse([hx - r * 0.35, hy - r * 0.25, hx + r * 0.2, hy + r * 0.15], fill=hell)
    # Kern deckt das Buch in der Mitte komplett
    kern = 23 * quell * (1 - zerfall) * (1 + 0.06 * math.sin(t * 7 * 2 * math.pi))
    if kern > 3:
        d.ellipse([cx - kern, cy - kern * 1.05, cx + kern, cy + kern * 1.05], fill=mittel)
        d.ellipse([cx - kern * 0.65, cy - kern * 0.8, cx + kern * 0.15, cy - kern * 0.15], fill=hell)
        # rosa Wirbel im Kern
        for k in range(10):
            a = t * 8 + k * 0.6
            rr = kern * (0.15 + k * 0.06)
            d.point((round(cx + math.cos(a) * rr), round(cy + math.sin(a) * rr * 0.9)), fill=rosa)
    # Funken: funkeln in der Wolke, steigen beim Zerfall auf
    for i in range(34):
        w = rnd.uniform(0, 2 * math.pi)
        basis = rnd.uniform(6, 34)
        steig = rnd.uniform(10, 30)
        an = rnd.uniform(0, 1)
        x = cx + math.cos(w + t * 1.5) * (basis * (0.5 + 0.5 * quell) + zerfall * 18)
        y = cy + math.sin(w + t * 1.5) * basis * 0.9 - zerfall * steig
        blink = math.sin(t * 2 * math.pi * 6 + an * 9) > 0.1
        if t < 0.04 or t > 0.985 or not blink:
            continue
        col = (weiss, gold, rosa)[i % 3]
        x, y = round(x), round(y)
        d.point((x, y), fill=col)
        if i % 4 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d.point((x + dx, y + dy), fill=col)
            if i % 8 == 0:
                for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                    d.point((x + dx, y + dy), fill=col)
    return img


def glatt(t):
    return t * t * (3 - 2 * t)


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
    # Verwandlungswolke (Effekt über dem Buch; Gestaltwechsel bei Frame 16)
    # 32 Frames à 70 ms (≈2,2 s), eigene Leinwand PW×PW
    pf = [puff(i / 31) for i in range(32)]
    ps = Image.new("RGBA", (PW * len(pf), PW), (0, 0, 0, 0))
    for i, f in enumerate(pf):
        ps.alpha_composite(f, (i * PW, 0))
    ps.save(os.path.join(ZIEL, "verwandeln.png"))
    ANIM["verwandeln"] = {"frames": len(pf), "ms": 70, "groesse": PW}
    # Tentakelmonster will raus (je Gestalt, Buch steckt mit im Streifen)
    for g, v in enumerate(V, start=1):
        fr = tentakel_frames(v)
        st = Image.new("RGBA", (ETW * len(fr), ETH), (0, 0, 0, 0))
        for i, f in enumerate(fr):
            st.alpha_composite(f, (i * ETW, 0))
        st.save(os.path.join(ZIEL, f"tentakel_{g}.png"))
        ANIM[f"tentakel_{g}"] = {"frames": len(fr), "ms": TENTAKEL_MS, "breite": ETW, "hoehe": ETH, "rand": RAND}
    seiten()
    # Herz vom Drachen mitbenutzen
    herz = os.path.join(ZIEL, "..", "drache", "herz.png")
    Image.open(herz).save(os.path.join(ZIEL, "herz.png"))
    info = {"breite": W, "hoehe": H, "gestalten": len(V), "animationen": ANIM,
            "seite": {"breite": 14, "hoehe": 11}, "verwandelnWechselFrame": 16,
            "tentakel": {"schlagFrame": SCHLAG_FRAME, "spitze": list(schlag_spitze(V[0])),
                         # Spitze in Frame 33–37 (Zurückreißen) — gepacktes Häufchen folgt ihr
                         "spitzen": [[98, 92], [96, 77], [88, 70], [80, 62], [72, 53]]}}
    with open(os.path.join(ZIEL, "sprite.json"), "w", encoding="utf8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print(json.dumps(ANIM))
