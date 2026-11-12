# Marks Wahl 12.11.2026 („Perfekt!!!“): Drachen-Ei und Schlüpfling (Baby) — erste Wachstumsstufen.
# Mark: Phase 1 Ei (schlüpft nach 5–10× Antippen), Phase 2 Baby (läuft nur unten,
# frisst, macht Häufchen), ab 3 EP der heutige Drache.
# Gleiche Palette wie drache_final.py (dr.PAL) — Varianten über drachen_varianten.palette().
import math
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import drache_final as dr  # noqa: E402
import drachen_varianten as dv  # noqa: E402

P = dr.PAL


def ell(d, cx, cy, rx, ry, c):
    d.ellipse([round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)], fill=P[c])


def outline(img, ausnahmen=()):
    W, H = img.size
    px = img.load()
    out = img.copy()
    po = out.load()
    frei = {P[c] for c in ausnahmen}
    for y in range(H):
        for x in range(W):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and px[nx, ny][3] and px[nx, ny] not in frei:
                        po[x, y] = P["K"]
                        break
    return out


# ── Ei ────────────────────────────────────────────────────────────────────
EW, EH = 30, 34


def ei(kipp=0.0, risse=0, hopser=0, deckel=None, kopf=False, blink=False):
    """Ei mit Schuppenmuster. `risse` 0..4, `deckel` = (dx, dy, drehung) wenn die
    Kappe abfliegt, `kopf` = Baby-Kopf schaut aus der unteren Schale."""
    img = Image.new("RGBA", (EW * 2, EH * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = EW, EH + 8 - hopser
    # Schale unten (immer) und Kappe (wenn nicht abgeflogen) getrennt malen
    schale = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(schale)
    sd.ellipse([cx - 10, cy - 14, cx + 10, cy + 12], fill=P["D"])
    sd.ellipse([cx - 9, cy - 13, cx + 8, cy + 10], fill=P["R"])
    # Schuppenbögen in Gold
    muster = Image.new("RGBA", img.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(muster)
    for reihe, yy in enumerate(range(cy - 9, cy + 11, 4)):
        for xx in range(cx - 10 + (reihe % 2) * 2, cx + 11, 4):
            md.line([(xx - 1, yy), (xx, yy + 1), (xx + 1, yy)], fill=P["O"])
    innen = Image.new("L", img.size, 0)
    ImageDraw.Draw(innen).ellipse([cx - 8, cy - 11, cx + 7, cy + 9], fill=255)
    schale_muster = Image.new("RGBA", img.size, (0, 0, 0, 0))
    schale_muster.paste(muster, (0, 0), innen)
    schale.alpha_composite(schale_muster)
    sd = ImageDraw.Draw(schale)
    sd.ellipse([cx - 6, cy - 10, cx - 3, cy - 5], fill=P["L"])  # Glanz
    sd.point((cx - 5, cy - 9), fill=P["W"])
    # Risse: Zickzack, wachsen mit `risse`
    rissbahnen = [
        [(cx - 2, cy - 13), (cx - 1, cy - 10), (cx - 3, cy - 8), (cx - 1, cy - 6)],
        [(cx + 4, cy - 12), (cx + 3, cy - 9), (cx + 6, cy - 7)],
        [(cx - 1, cy - 6), (cx + 1, cy - 4), (cx - 1, cy - 2)],
        [(cx - 9, cy - 3), (cx - 6, cy - 4), (cx - 3, cy - 2), (cx, cy - 4), (cx + 3, cy - 2), (cx + 6, cy - 4), (cx + 9, cy - 3)],
    ]
    for bahn in rissbahnen[:risse]:
        sd.line(bahn, fill=P["K"], width=1)
    # Zickzack-Linie als Schnitt zwischen Kappe und Unterteil
    schnitt = [(cx - 11, cy - 3), (cx - 6, cy - 5), (cx - 3, cy - 2), (cx, cy - 5), (cx + 3, cy - 2), (cx + 6, cy - 5), (cx + 11, cy - 3)]
    maske = Image.new("L", img.size, 0)
    ImageDraw.Draw(maske).polygon([(0, 0), (img.size[0], 0), (img.size[0], schnitt[-1][1])] + schnitt[::-1] + [(0, schnitt[0][1])], fill=255)
    kappe = Image.new("RGBA", img.size, (0, 0, 0, 0))
    kappe.paste(schale, (0, 0), maske)
    unten = schale.copy()
    unten.paste((0, 0, 0, 0), (0, 0), maske)

    if kopf:
        baby = baby_kopf(blink)
        img.alpha_composite(baby, (cx - baby.width // 2, cy - 15))
    img.alpha_composite(unten)
    if deckel is None:
        img.alpha_composite(kappe)
    else:
        dx, dy, rot = deckel
        k = kappe.rotate(rot, resample=Image.NEAREST, center=(cx, cy - 6))
        img.alpha_composite(k, (round(dx), round(dy)))
    if kipp:
        img = img.rotate(kipp, resample=Image.NEAREST, center=(cx, cy + 12))
    return outline(img).crop((EW - 22, 6, EW + 26, EH * 2 - 4))


def baby_kopf(blink=False):
    """Nur Kopf + Hals, der aus der Schale lugt."""
    k = Image.new("RGBA", (24, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(k)
    hx, hy = 10, 10
    ell(d, hx, hy + 0.6, 7, 6, "D")
    ell(d, hx - 0.3, hy, 6.4, 5.4, "R")
    ell(d, hx - 2, hy - 3, 2, 1, "L")
    ell(d, hx + 5, hy + 2, 3.2, 2.4, "D")
    ell(d, hx + 4.8, hy + 1.6, 2.8, 2, "R")
    d.point((hx + 7, hy + 1), fill=P["K"])
    for bx in (hx - 3, hx + 1):
        d.line([(bx, hy - 5), (bx - 1, hy - 7)], fill=P["H"], width=2)
    if blink:
        d.line([(hx, hy - 1), (hx + 3, hy - 1)], fill=P["K"])
    else:
        ell(d, hx + 1.5, hy - 1, 2.4, 2.8, "W")
        d.rectangle([hx + 2, hy - 2, hx + 3, hy], fill=P["B"])
        d.point((hx + 2, hy - 2), fill=P["W"])
    return k


# ── Schlüpfling ───────────────────────────────────────────────────────────
BW, BH = 50, 34


def baby(phase=0.0, amp=1.5, bob=0, blink=False, leg=0.0, mund=False, welle=None, schale=False):
    """Kurzer, pummeliger Körper, großer Kopf, Hornstummel, kurze Schnurrhaare,
    Mini-Quaste. Wie beim großen Drachen bewegt sich die Figur nicht im Rahmen."""
    img = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = phase if welle is None else welle
    pts = []
    n = 12
    for i in range(n):
        t = i / (n - 1)
        x = 7 + t * 20
        a = amp * (1.0 - 0.6 * t)
        y = 22 + bob + math.sin(t * 1.8 * math.pi - w) * a
        r = 1.6 + 3.2 * min(1.0, t * 1.8)
        pts.append((x, y, r, t))

    # Stummelbeine
    for idx, ph in ((4, 0.0), (9, math.pi)):
        x, y, r, _ = pts[idx]
        s = math.sin(phase * 2 + ph) * leg
        for off, c in ((-1, "D"), (1, "R")):
            vorz = 1 if c == "R" else -1
            fx = x + off + s * vorz
            hub = max(0.0, math.cos(phase * 2 + ph) * vorz) * leg * 0.6
            fy = y + r + 3.5 - hub
            d.line([(x + off, y + r - 1), (fx, fy)], fill=P[c], width=2)
            d.point((fx + 1, fy), fill=P["H"])

    # Flaumige Mini-Mähne
    for x, y, r, t in pts[4::3]:
        fl = math.sin(phase + t * 5) * 0.7
        d.polygon([(x - 1.5, y - r + 1), (x - 2.5 + fl, y - r - 2), (x + 1, y - r + 1)], fill=P["M"])

    for x, y, r, t in pts:
        ell(d, x, y + 0.6, r, r, "D")
    for x, y, r, t in pts:
        ell(d, x - 0.2, y - 0.3, max(r - 0.7, 0.6), max(r - 0.7, 0.6), "R")
    for x, y, r, t in pts:
        if r > 2.4:
            ell(d, x, y + r * 0.55, r * 0.5, r * 0.32, "Y")

    # Mini-Quaste
    tx, ty, tr, _ = pts[0]
    fl = math.sin(phase * 1.5) * 1.0
    d.polygon([(tx + 1, ty - 1), (tx - 3, ty - 2 + fl), (tx - 3, ty + 2 + fl), (tx + 1, ty + 1)], fill=P["F"])

    # Kopf: groß im Verhältnis, kurzer Hals
    nx, ny, nr, _ = pts[-1]
    hx, hy = nx + 5, ny - 6
    ell(d, nx + 2.5, ny - 3 + 0.6, 4, 4, "D")
    ell(d, nx + 2.3, ny - 3, 3.4, 3.4, "R")
    for i in range(2):
        my = hy - 1 + i * 3
        d.polygon([(hx - 5, my - 1.5), (hx - 9 + math.sin(phase + i), my + 0.5), (hx - 5, my + 1.5)], fill=P["M"])
    ell(d, hx, hy + 0.6, 7.4, 6.6, "D")
    ell(d, hx - 0.3, hy, 6.9, 6.0, "R")
    ell(d, hx - 2, hy - 3.4, 2.4, 1.2, "L")
    # Stupsnase
    ell(d, hx + 6, hy + 2.2, 3.4, 2.6, "D")
    ell(d, hx + 5.8, hy + 1.8, 3.0, 2.2, "R")
    d.point((hx + 8, hy + 1), fill=P["K"])
    if mund:
        d.line([(hx + 4, hy + 4), (hx + 8, hy + 4)], fill=P["K"])
    else:
        d.point((hx + 6, hy + 4), fill=P["D"])
    # Hornstummel
    for bx in (hx - 3, hx + 1):
        d.line([(bx, hy - 5), (bx - 1, hy - 8)], fill=P["H"], width=2)
    # Großes Kulleraugen
    if blink:
        d.line([(hx, hy - 1), (hx + 4, hy - 1)], fill=P["K"])
    else:
        ell(d, hx + 2, hy - 1, 2.8, 3.2, "W")
        d.rectangle([hx + 3, hy - 2, hx + 4, hy + 1], fill=P["B"])
        d.point((hx + 3, hy - 2), fill=P["W"])
        d.point((hx + 2, hy + 1), fill=P["W"])
    # Kurze Schnurrhaare
    for sy, sgn in ((hy + 1, -1), (hy + 2, 1)):
        p = [(hx + 9 + u * 4, sy + sgn * u * 1.2 + math.sin(u * 3 + phase) * 0.6) for u in (0, 0.33, 0.66, 1)]
        d.line(p, fill=P["M"], width=1)
    # Eierschalen-Kappe auf dem Kopf (direkt nach dem Schlüpfen)
    if schale:
        d.polygon([(hx - 6, hy - 4), (hx - 4, hy - 9), (hx - 1, hy - 6), (hx + 2, hy - 10), (hx + 5, hy - 5)], fill=(250, 244, 226, 255))
        d.line([(hx - 6, hy - 4), (hx + 5, hy - 5)], fill=P["O"])
    return outline(img, ausnahmen=("M",))


# ── Vorschau ──────────────────────────────────────────────────────────────
BG = (24, 26, 38, 255)


def gif(frames, name, ms, scale=6):
    w = max(f.width for f in frames)
    h = max(f.height for f in frames)
    out = []
    for f in frames:
        bg = Image.new("RGBA", (w, h), BG)
        bg.alpha_composite(f, ((w - f.width) // 2, h - f.height))
        out.append(bg.resize((w * scale, h * scale), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
    dur = ms if isinstance(ms, list) else [ms] * len(out)
    out[0].save(name, save_all=True, append_images=out[1:], duration=dur, loop=0, disposal=2)


def schluepfen():
    """Ei wackelt, Risse wachsen mit jedem Tipp, Kappe fliegt, Baby schaut raus,
    klettert heraus mit Schalenhut."""
    fr, ms = [], []
    for i in range(8):
        fr.append(ei(kipp=math.sin(i / 8 * 2 * math.pi) * 4)); ms.append(120)
    for tipp in range(1, 5):
        for k in range(6):
            fr.append(ei(kipp=math.sin(k * 2.2) * (10 - k) * 1.2, risse=tipp, hopser=2 if k < 2 else 0)); ms.append(55)
        for k in range(4):
            fr.append(ei(risse=tipp)); ms.append(120)
    # Kappe hüpft hoch, dreht sich einmal und landet als Hütchen auf dem Kopf.
    for k in range(14):
        t = k / 13
        fr.append(ei(risse=4, deckel=(2 * t, -9 * t - 44 * t * (1 - t), -360 * t), kopf=k > 2)); ms.append(55)
    for k in range(12):
        fr.append(ei(risse=4, deckel=(2, -9, 0), kopf=True, blink=k in (6, 7))); ms.append(120)
    return fr, ms


def tafel(arten):
    zeilen = []
    for art in arten:
        if art != "drache":
            dv.palette(art)
        teile = [ei(), ei(risse=2), ei(risse=4), ei(risse=4, deckel=(40, 40, 0), kopf=True),
                 baby(schale=True), baby(), baby(phase=1.3, leg=1.6, amp=2.2, mund=True), baby(blink=True)]
        zeilen.append(teile)
        dr.PAL.update(ORIGINAL)
    sc = 5
    zw = sum(t.width for t in zeilen[0]) + 6 * len(zeilen[0]) + 4
    zh = max(t.height for t in zeilen[0]) + 6
    board = Image.new("RGBA", (zw, zh * len(zeilen)), BG)
    for r, teile in enumerate(zeilen):
        x = 4
        for t in teile:
            board.alpha_composite(t, (x, r * zh + zh - t.height - 3))
            x += t.width + 6
    return board.resize((board.width * sc, board.height * sc), Image.NEAREST)


ORIGINAL = dict(dr.PAL)

if __name__ == "__main__":
    out = sys.argv[1]
    tafel(["drache", "eisdrache", "blitzdrache"]).save(f"{out}/tafel.png")
    f, ms = schluepfen()
    gif(f, f"{out}/schluepfen.gif", ms)
    idle = [baby(phase=i / 20 * 2 * math.pi, amp=1.2, bob=round(math.sin(i / 20 * 2 * math.pi) * 0.6), blink=i in (14, 15)) for i in range(20)]
    gif(idle, f"{out}/baby_idle.gif", 110, 7)
    lauf = [baby(phase=i / 16 * 2 * math.pi, leg=1.6, amp=2.2, mund=True, welle=0.4) for i in range(16)]
    gif(lauf, f"{out}/baby_lauf.gif", 55, 7)
    # Größenvergleich Baby ↔ heutiger Drache
    v = Image.new("RGBA", (dr.W + BW + 10, dr.H + 4), BG)
    v.alpha_composite(baby(), (2, v.height - BH - 2))
    v.alpha_composite(dr.frame(), (BW + 8, v.height - dr.H - 2))
    v.resize((v.width * 5, v.height * 5), Image.NEAREST).save(f"{out}/vergleich.png")
    print("ok")
