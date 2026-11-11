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
    return {"idle": (idle, 110), "lauf": (lauf, 35), "freuen": (freuen, 90), "klettern": (klettern, 35),
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
