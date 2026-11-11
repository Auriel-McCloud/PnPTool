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
    # Die Welle läuft vom Kopf zum Schwanz (negative Phase) — so schiebt sich
    # eine Schlange vorwärts. Andersherum sieht es aus, als zische er
    # rückwärts. Viele Frames, kleine Ausschläge, sonst zuckt es.
    idle = []
    for i in range(24):
        t = i / 24 * 2 * math.pi
        idle.append(dr.frame(phase=-t, amp=1.2, bob=round(math.sin(t) * 0.6), blink=i in (17, 18),
                             schnurr=math.sin(t) * 0.5))
    lauf = []
    for i in range(24):
        t = i / 24 * 2 * math.pi
        lauf.append(dr.frame(phase=-t, amp=2.5, leg=1.5, mund=True, schnurr=1.0))
    # Freuen (gestreichelt): Hüpfer mit zugekniffenen Augen und offenem Maul.
    freuen = []
    for i in range(8):
        t = i / 8 * 2 * math.pi
        freuen.append((dr.frame(phase=t * 2, amp=3.0, blink=True, mund=True, schnurr=1.5),
                       round(abs(math.sin(t)) * 3)))
    return {"idle": (idle, 110), "lauf": (lauf, 60), "freuen": (freuen, 90)}


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
    with open(os.path.join(ziel, "sprite.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta))
