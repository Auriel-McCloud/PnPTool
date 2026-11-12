# Exportiert Ei, Schlüpfen und Baby-Drachen (erste Wachstumsstufen, Mark 12.11.2026)
# für alle drei Drachen-Arten.
# Aufruf: python jung_exportieren.py C:/DEV/PnPTool/frontend/public/pets
#   → <art>/ei.png, <art>/schluepfen.png, <art>/baby/<animation>.png,
#     <art>/baby/hut_<animation>.png (mit Eierschalen-Hütchen), <art>/baby/sprite.json
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drache_final as dr  # noqa: E402
import drachen_varianten as dv  # noqa: E402
import drache_jung as dj  # noqa: E402

ORIGINAL = dict(dr.PAL)
OBEN = 4
B = dj.baby


def sheet(frames, w, h, oben=0):
    s = Image.new("RGBA", (w * len(frames), h + oben), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        bild, hoch = f if isinstance(f, tuple) else (f, 0)
        s.alpha_composite(bild, (i * w, oben - hoch))
    return s


def baby_animationen(hut=False):
    """Wie beim großen Drachen (sprites_exportieren.py), nur mit dem Schlüpfling."""
    idle = [B(phase=i / 24 * 2 * math.pi, welle=0.0, amp=1.4, bob=round(math.sin(i / 24 * 2 * math.pi) * 0.6),
              blink=i in (17, 18), schale=hut) for i in range(24)]
    # Tapsig: etwas mehr Wippen als der Große.
    lauf = [B(phase=i / 32 * 2 * math.pi, welle=math.sin(i / 32 * 2 * math.pi) * 0.15, amp=1.8, leg=1.6,
              bob=round(math.sin(2 * i / 32 * 2 * math.pi) * 0.8), mund=True, schale=hut) for i in range(32)]
    freuen = [(B(phase=i / 8 * 4 * math.pi, amp=1.8, blink=True, mund=True, schale=hut),
               round(abs(math.sin(i / 8 * 2 * math.pi)) * 3)) for i in range(8)]
    if hut:
        return {"idle": (idle, 110), "lauf": (lauf, 35), "freuen": (freuen, 90)}
    sprung = [B(phase=math.pi / 4 + math.sin(i / 6 * 2 * math.pi) * 0.25, welle=0.0, amp=1.5, leg=2.0, mund=True)
              for i in range(6)]
    schlafen = [(B(phase=0.0, welle=0.0, amp=0.8 + math.sin(i / 24 * 2 * math.pi) * 0.3, blink=True), -1)
                for i in range(24)]
    klettern = [B(phase=i / 32 * 2 * math.pi, welle=math.sin(i / 32 * 2 * math.pi) * 0.15, amp=1.5, leg=2.0,
                  blink=True, mund=True) for i in range(32)]
    niesen = [B(phase=i * 0.1, welle=0.0, amp=1.4, blink=i % 7 == 0) for i in range(22)]
    fressen = []
    for i in range(16):
        if i <= 2:
            fressen.append(B(phase=i * 0.3, welle=0.0, amp=1.4))
        elif i <= 5:
            fressen.append((B(phase=1.0, welle=0.0, amp=1.4, mund=True), 1))
        elif i <= 13:
            zu = i % 2 == 0
            fressen.append((B(phase=1.0 + i * 0.2, welle=0.0, amp=1.4, mund=not zu, blink=True), 0 if zu else 1))
        else:
            fressen.append(B(phase=1.2, welle=0.0, amp=1.6, blink=i == 15))
    return {"idle": (idle, 110), "lauf": (lauf, 35), "freuen": (freuen, 90), "klettern": (klettern, 35),
            "niesen": (niesen, 80), "fressen": (fressen, 90), "sprung": (sprung, 70), "schlafen": (schlafen, 150)}


def ei_bilder():
    """ei.png: Risse 0–4 (ein Frame je Stufe). schluepfen.png: Kappe fliegt und
    landet als Hütchen, Baby blinzelt raus. Alle Frames auf derselben Leinwand."""
    eier = [dj.ei(risse=r) for r in range(5)]
    sch = []
    for k in range(14):
        t = k / 13
        sch.append(dj.ei(risse=4, deckel=(2 * t, -9 * t - 44 * t * (1 - t), -360 * t), kopf=k > 2))
    for k in range(12):
        sch.append(dj.ei(risse=4, deckel=(2, -9, 0), kopf=True, blink=k in (6, 7)))
    return eier, sch


if __name__ == "__main__":
    basis = sys.argv[1]
    for art in ("drache", "eisdrache", "blitzdrache"):
        dr.PAL.update(ORIGINAL)
        if art != "drache":
            dv.palette(art)
        ziel = os.path.join(basis, art, "baby")
        os.makedirs(ziel, exist_ok=True)
        meta = {"breite": dj.BW, "hoehe": dj.BH + OBEN, "animationen": {}}
        for hut in (False, True):
            for name, (frames, ms) in baby_animationen(hut).items():
                datei = ("hut_" if hut else "") + name
                sheet(frames, dj.BW, dj.BH, OBEN).save(os.path.join(ziel, f"{datei}.png"))
                if not hut:
                    meta["animationen"][name] = {"frames": len(frames), "ms": ms}
        lauf = Image.open(os.path.join(ziel, "lauf.png"))
        meta["fussLuft"] = lauf.height - lauf.getchannel("A").getbbox()[3]
        # Maul (Stupsnase vorn) — für Fressen/Greifen; Niesen kann das Baby nicht.
        meta["maul"] = [46, 18 + OBEN]
        eier, sch = ei_bilder()
        ew, eh = eier[0].size
        sheet(eier, ew, eh).save(os.path.join(basis, art, "ei.png"))
        sheet(sch, ew, eh).save(os.path.join(basis, art, "schluepfen.png"))
        unten = eier[0].getchannel("A").getbbox()[3]
        meta["ei"] = {"breite": ew, "hoehe": eh, "frames": len(eier), "fussLuft": eh - unten,
                      "schluepfen": {"frames": len(sch), "ms": 70}}
        with open(os.path.join(ziel, "sprite.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(art, json.dumps(meta))
    dr.PAL.update(ORIGINAL)
