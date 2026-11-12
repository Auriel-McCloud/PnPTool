# Vergleichstafel/Vorschau-GIFs der silberblauen Drachen-Varianten (Entwurf 12.11.2026).
# Aufruf: python wolkensalamander_entwurf.py <ausgabeordner>
import sys

from PIL import Image

sys.path.insert(0, "C:/DEV/PnPTool/docs/assets/critter-pet")
import drache_final as dr  # noqa: E402
import sprites_exportieren as ex  # noqa: E402

import drachen_varianten as dv  # noqa: E402
from drachen_varianten import FH, FW, N, blitz_sheet, eis_sheet  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def zusammen(niesen, atem, bg=(24, 26, 38, 255), scale=5):
    """Niesen + Atem als Vorschau-Frames (Atem setzt ab Niesen-Frame 6 ein)."""
    maul = ex.dr.wirbelsaeule(0.0, 2.0, 0)[-1]
    mx = round(maul[0] + 6 + 11)
    my = round(maul[1] - 9 + 4 + ex.OBEN)
    bw = dr.W + FW - 10
    frames = []
    for i, f in enumerate(niesen):
        bild, hoch = f if isinstance(f, tuple) else (f, 0)
        c = Image.new("RGBA", (bw, ex.HOEHE), bg)
        c.alpha_composite(bild, (0, ex.OBEN - hoch))
        if i >= 6:
            k = min(N - 1, int((i - 6) * 80 / 70))
            c.alpha_composite(atem.crop((k * FW, 0, (k + 1) * FW, FH)), (mx, my - FH // 2))
        frames.append(c.resize((bw * scale, ex.HOEHE * scale), Image.NEAREST))
    return frames


def gif(frames, name, ms):
    p = [f.convert("P", palette=Image.ADAPTIVE) for f in frames]
    p[0].save(f"{OUT}/{name}", save_all=True, append_images=p[1:], duration=ms, loop=0, disposal=2)


if __name__ == "__main__":
    eis, blitz = eis_sheet(), blitz_sheet()
    eis.save(f"{OUT}/eis.png")
    blitz.save(f"{OUT}/blitz.png")
    zeilen = []
    for pal in ("blitzdrache", "eisdrache"):
        dv.palette(pal)
        an = ex.animationen()
        niesen = an["niesen"][0]
        for atem, aname in ((eis, "eis"), (blitz, "blitz")):
            fr = zusammen(niesen, atem)
            gif(fr, f"niesen_{pal}_{aname}.gif", 80)
            zeilen.append((pal, aname, [fr[i] for i in (0, 9, 15)]))
        idle = [Image.new("RGBA", (dr.W, ex.HOEHE), (24, 26, 38, 255)) for _ in an["idle"][0]]
        for b, f in zip(idle, an["idle"][0]):
            b.alpha_composite(f, (0, ex.OBEN))
        gif([b.resize((dr.W * 6, ex.HOEHE * 6), Image.NEAREST) for b in idle], f"idle_{pal}.gif", 110)
    # Vergleichstafel: je Zeile Palette+Atem, 3 Schlüsselframes
    w, h = zeilen[0][2][0].size
    tafel = Image.new("RGBA", (w * 3, h * len(zeilen)), (24, 26, 38, 255))
    for r, (_, _, fs) in enumerate(zeilen):
        for c, f in enumerate(fs):
            tafel.paste(f, (c * w, r * h))
    tafel.save(f"{OUT}/tafel.png")
    print("ok", [(p, a) for p, a, _ in zeilen])
