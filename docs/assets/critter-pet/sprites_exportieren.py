# Exportiert die Drachen-Animationen als transparente Sprite-Sheets fürs Frontend.
# Aufruf: python sprites_exportieren.py C:/DEV/PnPTool/frontend/public/pets/drache
# Jedes Sheet: Frames waagrecht nebeneinander, je W×H Pixel (Originalgröße,
# das Frontend skaliert mit image-rendering: pixelated).
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drache_final as dr  # noqa: E402
import wolke  # noqa: E402


# Luft oben, damit die Hörner beim Freuden-Hüpfer nicht abgeschnitten werden.
OBEN = 4
HOEHE = dr.H + OBEN


def sheet(frames):
    s = Image.new("RGBA", (dr.W * len(frames), HOEHE), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        # (Bild, Hüpfhöhe): der Hüpfer verschiebt das ganze Bild nach oben,
        # statt im 44-px-Rahmen die Hörner abzuschneiden.
        bild, hoch = f if isinstance(f, tuple) else (f, 0)
        s.alpha_composite(bild, (i * dr.W, OBEN - hoch))
    return s


def animationen():
    # Die Körperform bleibt im Rahmen stehen (Mark, 11.11.: keine Welle, die
    # durch den Körper läuft — das wirkte wie ein Tornado im eigenen Fenster).
    # Nur Beine tapsen, Körper wippt leicht, Quaste/Mähne/Schnurrhaare wehen.
    idle = []
    for i in range(24):
        t = i / 24 * 2 * math.pi
        idle.append(dr.frame(phase=t, welle=0.0, amp=3.0, bob=round(math.sin(t) * 0.6), blink=i in (17, 18),
                             schnurr=math.sin(t) * 0.5))
    lauf = []
    # 32 Frames à 35 ms = gleicher Schritt-Takt wie vorher 16 à 70, nur flüssiger
    # (Mark, 11.11.: „ein paar mehr Frames, damit es nicht so zuckelig wirkt“).
    for i in range(32):
        t = i / 32 * 2 * math.pi
        # Leichtes Wiegen auf der Stelle (pendelt, wandert nicht).
        lauf.append(dr.frame(phase=t, welle=math.sin(t) * 0.12, amp=3.0, leg=2.0,
                             bob=round(math.sin(2 * t) * 0.6), schnurr=1.0))
    # Freuen (gestreichelt): Hüpfer mit zugekniffenen Augen und offenem Maul.
    freuen = []
    for i in range(8):
        t = i / 8 * 2 * math.pi
        freuen.append((dr.frame(phase=t * 2, amp=3.0, blink=True, mund=True, schnurr=1.5),
                       round(abs(math.sin(t)) * 3)))
    # Sprung (Mark, 11.11.: klettern und springen): Beine weit gespreizt,
    # Maul offen, Quaste schlägt. Wenige Frames, er ist nur kurz in der Luft.
    sprung = []
    for i in range(6):
        t = i / 6 * 2 * math.pi
        sprung.append(dr.frame(phase=math.pi / 4 + math.sin(t) * 0.25, welle=0.0, amp=2.5, leg=2.5, mund=True,
                               schnurr=1.5))
    # Schlafen (oben auf einem Popup): flacher, Augen zu, atmet langsam.
    schlafen = []
    for i in range(24):
        t = i / 24 * 2 * math.pi
        schlafen.append((dr.frame(phase=0.0, welle=0.0, amp=1.6 + math.sin(t) * 0.3, blink=True, schnurr=-0.5),
                         -1))
    # Klettern (Mark, 11.11.: soll sich anstrengender anfühlen): wie Laufen,
    # aber Augen zusammengekniffen und Maul offen. Das Frontend schaltet die
    # Frames im Takt der Klimmzüge weiter, nicht nach Zeit.
    klettern = []
    for i in range(32):
        t = i / 32 * 2 * math.pi
        klettern.append(dr.frame(phase=t, welle=math.sin(t) * 0.15, amp=2.5, leg=2.5, blink=True, mund=True,
                                 schnurr=0.5))
    # Feuerniesen (Mark, 11.11.): Kopf zurück, Augen zu — dann ruckartig nach
    # vorn mit offenem Maul. Das Feuer selbst ist ein eigenes Sheet (feuer.png).
    # 22 Frames à 80 ms: Anlauf 0–5, Maul offen solange das Feuer läuft (6–19,
    # Mark, 11.11.: Feuer etwas länger), erholen 20–21.
    niesen = []
    for i in range(22):
        if i <= 5:  # Anlauf: Luft holen
            niesen.append((dr.frame(phase=i * 0.1, welle=0.0, amp=2.0 + i * 0.12, blink=i >= 3,
                                    schnurr=0.3 + i * 0.25), min(2, i // 2)))
        elif i <= 19:  # Hatschi! — Feuer strömt, Schnurrhaare flattern
            niesen.append((dr.frame(phase=0.6 + (i - 6) * 0.35, welle=0.0, amp=1.6, mund=True, blink=True,
                                    schnurr=-1.0 + math.sin(i) * 0.4), -1 if i < 9 else 0))
        else:  # erholen
            niesen.append(dr.frame(phase=0.6 + (i - 19) * 0.2, welle=0.0, amp=2.0, blink=i == 21, schnurr=0.0))
    # Fressen (Mark, 11.11.: „kann der Drache das Papier, das rumliegt, fressen,
    # wenn er daran vorbeiläuft“): schnuppern, Maul auf (Frame 3–5 fliegt die
    # Seite hinein, macht das Frontend), genüsslich kauen, schlucken.
    fressen = []
    for i in range(16):
        if i <= 2:
            fressen.append(dr.frame(phase=i * 0.3, welle=0.0, amp=2.4, schnurr=0.8 + i * 0.4))
        elif i <= 5:
            fressen.append((dr.frame(phase=1.0, welle=0.0, amp=2.4, mund=True, schnurr=1.6), 1))
        elif i <= 13:
            zu_ = i % 2 == 0
            fressen.append((dr.frame(phase=1.0 + i * 0.2, welle=0.0, amp=2.4, mund=not zu_, blink=True,
                                     schnurr=math.sin(i) * 0.8), 0 if zu_ else 1))
        else:
            fressen.append(dr.frame(phase=1.2, welle=0.0, amp=2.6, blink=i == 15, schnurr=0.0))
    return {"idle": (idle, 110), "lauf": (lauf, 35), "freuen": (freuen, 90), "klettern": (klettern, 35),
            "niesen": (niesen, 80), "fressen": (fressen, 90),
            "sprung": (sprung, 70), "schlafen": (schlafen, 150)}


def pixelbild(zeilen, farben):
    h, w = len(zeilen), max(len(z) for z in zeilen)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, z in enumerate(zeilen):
        for x, c in enumerate(z):
            if c in farben:
                im.putpixel((x, y), farben[c])
    return im


HAEUFCHEN = [
    "....kk......",
    "...kbbk.....",
    "....kbbk....",
    "..kkbbbbkk..",
    ".kbbhbbbbbk.",
    ".kbbbbbbhbk.",
    "kkbbbbbbbbkk",
    "kbbhbbbbbbbk",
    "kbbbbbbbbhbk",
    ".kkkkkkkkkk.",
]
def feuer_sheet():
    """Feuerstoß aus dem Maul: wächst nach rechts, zerfällt dann in Glut und Rauch."""
    import random
    # 16 Frames: wachsen 0–4, lodern 5–11, zerfallen 12–15 (Mark: etwas länger).
    fw, fh, n = 56, 28, 16
    s = Image.new("RGBA", (fw * n, fh), (0, 0, 0, 0))
    for f in range(n):
        rnd = random.Random(f * 7 + 3)
        laenge = fw * min(1.0, (f + 1) / 5) * (1 - 0.06 * ((f * 5) % 3) if 5 <= f <= 11 else 1)
        zerfall = max(0.0, (f - 11) / 4)  # 0 … 1
        for x in range(fw):
            if x > laenge:
                continue
            breite = 1.5 + x * 0.32
            for y in range(fh):
                dy = abs(y - fh / 2 + 0.5)
                if dy > breite:
                    continue
                # Ausgefranste, runde Spitze statt einer geraden Kante.
                if x > laenge - dy * 0.9 - rnd.uniform(0, 7):
                    continue
                if rnd.random() < zerfall * 0.85:
                    continue
                kern = 1 - dy / max(breite, 1)
                hitze = kern * (1 - x / fw * 0.6) + rnd.uniform(-0.15, 0.15) - zerfall * 0.5
                if zerfall > 0.5 and rnd.random() < 0.35:
                    farbe = (90, 80, 80, 200)  # Rauch
                elif hitze > 0.75:
                    farbe = (255, 244, 170, 255)
                elif hitze > 0.5:
                    farbe = (255, 196, 60, 255)
                elif hitze > 0.25:
                    farbe = (245, 120, 30, 255)
                else:
                    farbe = (200, 48, 30, 255)
                s.putpixel((f * fw + x, y), farbe)
    return s, {"breite": fw, "hoehe": fh, "frames": n, "ms": 70}


def brand_bild():
    """Rußfleck, etwa doppelt so groß wie der erste (Mark, 11.11.): unregelmäßig,
    dunkler Kern, ein paar Glutpunkte."""
    import random
    rnd = random.Random(11)
    w, h = 32, 18
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            dx = (x - w / 2 + 0.5) / (w / 2)
            dy = (y - h / 2 + 0.5) / (h / 2)
            d = (dx * dx + dy * dy) ** 0.5 + rnd.uniform(-0.18, 0.18) + 0.12 * math.sin(x * 0.9 + y * 0.4)
            if d > 1.0:
                continue
            if d < 0.45:
                farbe = (26, 16, 12, 240)
            elif d < 0.75:
                farbe = (48, 32, 24, 230)
            else:
                farbe = (80, 60, 46, 200)
            if d < 0.7 and rnd.random() < 0.035:
                farbe = (255, 120, 30, 255)
            im.putpixel((x, y), farbe)
    return im


TROPFEN = [
    "..k..",
    ".kwk.",
    ".kbk.",
    "kbbbk",
    "kbbbk",
    ".kkk.",
]
ZZZ = [
    "kkkkk",
    "kwwwk",
    "kkwkk",
    ".kwk.",
    "kkwkk",
    "kwwwk",
    "kkkkk",
]
HERZ = [
    ".kk...kk.",
    "krrk.krrk",
    "krlrkrrrk",
    "krrrrrrrk",
    ".krrrrrk.",
    "..krrrk..",
    "...krk...",
    "....k....",
]

if __name__ == "__main__":
    ziel = sys.argv[1]
    os.makedirs(ziel, exist_ok=True)
    meta = {"breite": dr.W, "hoehe": HOEHE, "animationen": {}}
    for name, (frames, dauer) in animationen().items():
        sheet(frames).save(os.path.join(ziel, f"{name}.png"))
        meta["animationen"][name] = {"frames": len(frames), "ms": dauer}
    pixelbild(HAEUFCHEN, {"k": (40, 22, 10, 255), "b": (120, 72, 30, 255), "h": (170, 112, 56, 255)}).save(
        os.path.join(ziel, "haeufchen.png"))
    pixelbild(HERZ, {"k": (60, 10, 20, 255), "r": (236, 64, 96, 255), "l": (255, 170, 190, 255)}).save(
        os.path.join(ziel, "herz.png"))
    feuer, feuer_meta = feuer_sheet()
    feuer.save(os.path.join(ziel, "feuer.png"))
    meta["feuer"] = feuer_meta
    brand_bild().save(os.path.join(ziel, "brand.png"))
    # Wolkenlauf (Mark, 12.11.): Glückswolken unter den Pfoten.
    wolken, wolken_meta = wolke.sheet()
    wolken.save(os.path.join(ziel, "wolke.png"))
    meta["wolke"] = wolken_meta
    # Wo das Maul im Sprite sitzt (Feuer setzt dort an).
    pts = dr.wirbelsaeule(0.0, 2.0, 0)
    nx, ny = pts[-1][0], pts[-1][1]
    meta["maul"] = [round(nx + 6 + 11), round(ny - 9 + 4 + OBEN)]
    pixelbild(TROPFEN, {"k": (20, 50, 90, 255), "w": (230, 245, 255, 255), "b": (120, 190, 255, 255)}).save(
        os.path.join(ziel, "tropfen.png"))
    pixelbild(ZZZ, {"k": (30, 30, 60, 255), "w": (220, 230, 255, 255)}).save(os.path.join(ziel, "z.png"))
    # Wie viele Pixel unter den Füßen leer sind — das Frontend setzt die Füße
    # damit genau auf Boden, Popup-Kante oder Wand.
    lauf_sheet = Image.open(os.path.join(ziel, "lauf.png"))
    alpha = lauf_sheet.getchannel("A")
    bbox = alpha.getbbox()
    meta["fussLuft"] = lauf_sheet.height - bbox[3]
    with open(os.path.join(ziel, "sprite.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta))
