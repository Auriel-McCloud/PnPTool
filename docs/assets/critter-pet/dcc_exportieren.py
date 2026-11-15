# Export der Pets Mongo und Tummy-Acher (Mark, 15.11.2026: „Fang gut bauen an!“).
# Figuren aus dcc_entwurf.py (abgenommen), je Farbe eine eigene Art, je Art
# Ei + 6 Wachstumsschritte (`s1` … `s6`). Gleiche Animationsnamen und Takte wie
# beim Drachen, damit der Zustandsautomat (frontend/src/pets/bewegung.ts)
# unverändert jede Animation findet.
#
# Aufruf: python dcc_exportieren.py <repo-wurzel>
#   → frontend/public/pets/<art>/{ei,schluepfen,herz,z,tropfen}.png
#   → frontend/public/pets/<art>/s1..s6/<animation>.png + sprite.json
#   → frontend/src/pets/tierstufen.ts (Maße je Familie und Stufe, generiert)
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcc_entwurf as de  # noqa: E402

ARTEN = {
    "mongo": ("mongo", "A Dschungel"),
    "mongo_wueste": ("mongo", "B Wüste"),
    "mongo_bonbon": ("mongo", "C Bonbon"),
    "tummy": ("tummy", "A Fleisch"),
    "tummy_rosa": ("tummy", "B Rosa"),
    "tummy_lila": ("tummy", "C Lila"),
}
EI_SCHALE = {
    "A Dschungel": ((150, 170, 120), (206, 222, 176), (236, 244, 220)),
    "B Wüste": ((180, 160, 120), (232, 216, 180), (250, 242, 222)),
    "C Bonbon": ((180, 150, 200), (230, 212, 240), (248, 240, 252)),
}
STUFEN = ["s1", "s2", "s3", "s4", "s5", "s6"]
# Gleiche Takte wie der Drache (PetOverlay.tsx: SPRITE.animationen).
TAKT = {
    "idle": (24, 110), "lauf": (32, 35), "freuen": (8, 90), "klettern": (32, 35),
    "niesen": (22, 80), "sprung": (6, 70), "schlafen": (24, 150), "fressen": (16, 90),
    "einkringeln": (17, 80),
}
# Ei wie beim Drachen (BABY.ei): 48×58, 8 px Luft unter dem Ei.
EI_B, EI_H, EI_LUFT = 48, 58, 8
SCHLUEPF_FRAMES, SCHLUEPF_MS = 26, 70


def _sin(k, n):
    return math.sin(2 * math.pi * k / n)


def mongo_frames(st, p):
    """{animation: [(bild, hochversatz_px)]} plus Anker."""
    m = lambda **kw: de.mongo(st, p, **kw)  # noqa: E731
    f = {}
    f["idle"] = [(m(atem=_sin(k, 24), blink=k in (19, 20)), 0) for k in range(24)]
    f["lauf"] = [(m(pose="laufen", phase=k / 32), 0) for k in range(32)]
    f["klettern"] = [(m(pose="laufen", phase=k / 32, blink=True), 0) for k in range(32)]
    hops = [0, 2, 4, 5, 5, 4, 2, 0]
    f["freuen"] = [(m(freude=True, kiefer=0.45), h) for h in hops]
    f["niesen"] = [f["idle"][k % 24] for k in range(22)]
    f["sprung"] = [(m(schlaf=0.3), 0), (m(schlaf=0.15), 0), (m(pose="laufen", phase=0.25), 0),
                   (m(pose="laufen", phase=0.25), 0), (m(pose="laufen", phase=0.3), 0), (m(schlaf=0.2), 0)]
    f["schlafen"] = [(m(schlaf=1.0, atem=_sin(k, 24)), 0) for k in range(24)]
    fr = []
    for k in range(16):
        if k < 4:
            fr.append((m(kopf_tief=(k + 1) / 4), 0))
        elif k < 12:
            fr.append((m(kopf_tief=1.0, kiefer=0.8 if k % 2 == 0 else 0.0), 0))
        else:
            fr.append((m(kopf_tief=(15 - k) / 4), 0))
    f["fressen"] = fr
    f["einkringeln"] = [(m(schlaf=k / 16), 0) for k in range(17)]
    m(kopf_tief=1.0, kiefer=0.8)
    maul = de.ANKER["maul"]
    m(schlaf=1.0)
    kopf_schlaf = de.ANKER["kopf"]
    return f, maul, kopf_schlaf


def tummy_frames(st, p):
    t = lambda **kw: de.tummy(st, p, **kw)  # noqa: E731
    f = {}
    f["idle"] = [(t(quetsch=0.06 * _sin(k, 24), blink=k in (19, 20)), 0) for k in range(24)]
    f["lauf"] = [(t(phase=k / 32, kipp=4 * _sin(k, 32)), 0) for k in range(32)]
    f["klettern"] = [(t(phase=k / 32, blink=True), 0) for k in range(32)]
    hops = [0, 3, 6, 8, 8, 6, 3, 0]
    qs = [0.25, -0.15, -0.2, -0.1, -0.1, -0.2, -0.15, 0.25]
    f["freuen"] = [(t(freude=True, mund=1.5, quetsch=q), h) for h, q in zip(hops, qs)]
    f["niesen"] = [f["idle"][k % 24] for k in range(22)]
    f["sprung"] = [(t(quetsch=q), 0) for q in (0.4, 0.2, -0.3, -0.3, -0.1, 0.3)]
    f["schlafen"] = [(t(schlaf=1.0, quetsch=0.04 * _sin(k, 24)), 0) for k in range(24)]
    mampf = [1.9, 1.9, 0.5, 1.6, 0.4, 1.6, 0.4, 1.6, 0.4, 1.6, 0.4, 1.2, 0.6, 1.0, 1.0, 1.0]
    f["fressen"] = [(t(mund=mm, quetsch=0.08 if mm < 1 else 0.0), 0) for mm in mampf]
    f["einkringeln"] = [(t(schlaf=k / 16), 0) for k in range(17)]
    t(mund=1.9)
    maul = de.ANKER["maul"]
    t(schlaf=1.0)
    kopf_schlaf = de.ANKER["kopf"]
    return f, maul, kopf_schlaf


def zuschnitt(frames, boden_unten):
    """Gemeinsamer Rahmen über alle Animationen; Füße auf derselben Linie.
    Rückgabe: (links, oben, breite, hoehe, fussLuft)."""
    links, oben, rechts, unten = 10 ** 6, 10 ** 6, -1, -1
    for liste in frames.values():
        for bild, dy in liste:
            bb = bild.getbbox()
            if not bb:
                continue
            links, rechts = min(links, bb[0]), max(rechts, bb[2])
            oben, unten = min(oben, bb[1] - dy), max(unten, bb[3] - dy)
    unten = max(unten, boden_unten)
    links -= 1
    rechts += 1
    oben -= 1
    b, h = rechts - links, unten - oben
    if b % 2:
        rechts += 1
        b += 1
    if h % 2:
        oben -= 1
        h += 1
    return links, oben, b, h, unten - boden_unten


def streifen(liste, links, oben, b, h):
    sheet = Image.new("RGBA", (b * len(liste), h), (0, 0, 0, 0))
    for i, (bild, dy) in enumerate(liste):
        teil = bild.crop((links, oben + dy, links + b, oben + dy + h))
        sheet.alpha_composite(teil, (i * b, 0))
    return sheet


# ── Ei und Schlüpfen ──────────────────────────────────────────────────────
def ei_bild(schale, punkt, seed, risse=0, kipp=0.0, kappe_weg=None, kueken=None, kueken_hoch=0):
    """Ei im 48×58-Rahmen. `kappe_weg` = (dy, drehung) fliegt ab; `kueken` = Figur,
    die um `kueken_hoch` px aus der unteren Schale steigt."""
    roh = de.ei(schale, punkt, seed, gross=0.9)  # 40×44, Boden bei y≈40
    bb = roh.getbbox()
    ei_img = roh.crop(bb)
    cx = EI_B // 2
    unten = EI_H - EI_LUFT
    x0, y0 = cx - ei_img.width // 2, unten - ei_img.height
    rahmen = Image.new("RGBA", (EI_B, EI_H), (0, 0, 0, 0))
    ei_voll = Image.new("RGBA", (EI_B, EI_H), (0, 0, 0, 0))
    ei_voll.alpha_composite(ei_img, (x0, y0))
    d = ImageDraw.Draw(ei_voll)
    mx, oy, h = cx, y0, ei_img.height
    bahnen = [
        [(mx - 1, oy + 2), (mx + 1, oy + 5), (mx - 1, oy + 8)],
        [(mx + 4, oy + 4), (mx + 3, oy + 7), (mx + 5, oy + 9)],
        [(mx - 5, oy + 6), (mx - 3, oy + 9), (mx - 1, oy + 8)],
        [(mx - 8, oy + h * 0.45), (mx - 4, oy + h * 0.4), (mx - 1, oy + h * 0.47), (mx + 2, oy + h * 0.4),
         (mx + 5, oy + h * 0.47), (mx + 8, oy + h * 0.42)],
    ]
    for bahn in bahnen[:risse]:
        d.line(bahn, fill=de.K, width=1)
    schnitt_y = oy + h * 0.44
    if kappe_weg is not None or kueken is not None:
        maske = Image.new("L", ei_voll.size, 0)
        ImageDraw.Draw(maske).rectangle([0, 0, EI_B, round(schnitt_y)], fill=255)
        kappe = Image.new("RGBA", ei_voll.size, (0, 0, 0, 0))
        kappe.paste(ei_voll, (0, 0), maske)
        untere = ei_voll.copy()
        untere.paste((0, 0, 0, 0), (0, 0, EI_B, round(schnitt_y) + 1))
        # Zackenrand an der Schale
        ud = ImageDraw.Draw(untere)
        for i, xx in enumerate(range(mx - 9, mx + 10, 3)):
            ud.point((xx, round(schnitt_y) + 1 + (i % 2)), fill=(0, 0, 0, 0))
        if kueken is not None:
            # steigt aus der Schale: unten abgeschnitten, sonst ragt es unter dem Ei heraus
            kb = kueken.getbbox()
            k = kueken.crop(kb)
            boden = unten - 3
            lage = Image.new("RGBA", rahmen.size, (0, 0, 0, 0))
            lage.alpha_composite(k, (cx - k.width // 2 + 2, boden - kueken_hoch))
            lage.paste((0, 0, 0, 0), (0, boden, EI_B, EI_H))
            rahmen.alpha_composite(lage)
        rahmen.alpha_composite(untere)
        if kappe_weg is not None:
            dy, rot = kappe_weg
            kap = kappe.rotate(rot, resample=Image.NEAREST, center=(mx, schnitt_y))
            rahmen.alpha_composite(kap, (2, -round(dy)))
        elif kueken is None:
            rahmen.alpha_composite(kappe)
    else:
        rahmen.alpha_composite(ei_voll)
    if kipp:
        rahmen = rahmen.rotate(kipp, resample=Image.NEAREST, center=(cx, unten))
    return rahmen


def ei_sheets(familie, farbe, p):
    if familie == "mongo":
        schale, punkt, seed = EI_SCHALE[farbe], de.c(p, "S"), 3
    else:
        schale, punkt, seed = (de.c(p, "D"), de.c(p, "M"), de.c(p, "L")), de.c(p, "R"), 5
    eier = [ei_bild(schale, punkt, seed, risse=r) for r in range(5)]
    sheet = Image.new("RGBA", (EI_B * 5, EI_H), (0, 0, 0, 0))
    for i, e in enumerate(eier):
        sheet.alpha_composite(e, (i * EI_B, 0))
    kueken = de.mongo(1, p) if familie == "mongo" else de.tummy(1, p)
    kueken_blinz = de.mongo(1, p, blink=True) if familie == "mongo" else de.tummy(1, p, blink=True)
    hoehe_k = kueken.getbbox()[3] - kueken.getbbox()[1]
    bilder = []
    for k in range(SCHLUEPF_FRAMES):
        if k < 8:
            bilder.append(ei_bild(schale, punkt, seed, risse=4, kipp=[0, -6, 0, 6, 0, -9, 0, 9][k]))
        elif k < 10:
            bilder.append(ei_bild(schale, punkt, seed, risse=4, kipp=[-4, 4][k - 8]))
        else:
            j = k - 10
            kap = (j * 7 + 2, j * 25) if j < 6 else (60, 0)
            hoch = min(hoehe_k, round((j + 1) * hoehe_k / 8))
            fig = kueken_blinz if k in (21, 22) else kueken
            bilder.append(ei_bild(schale, punkt, seed, risse=4, kappe_weg=kap, kueken=fig, kueken_hoch=hoch))
    sl = Image.new("RGBA", (EI_B * SCHLUEPF_FRAMES, EI_H), (0, 0, 0, 0))
    for i, e in enumerate(bilder):
        sl.alpha_composite(e, (i * EI_B, 0))
    return sheet, sl


def main(wurzel):
    pets = os.path.join(wurzel, "frontend", "public", "pets")
    masse = {"mongo": {}, "tummy": {}}
    for art, (familie, farbe) in ARTEN.items():
        p = (de.MONGO_PAL if familie == "mongo" else de.TUMMY_PAL)[farbe]
        ziel = os.path.join(pets, art)
        os.makedirs(ziel, exist_ok=True)
        for nebenbei in ("herz.png", "z.png", "tropfen.png"):
            shutil.copy(os.path.join(pets, "drache", nebenbei), os.path.join(ziel, nebenbei))
        ei, sl = ei_sheets(familie, farbe, p)
        ei.save(os.path.join(ziel, "ei.png"))
        sl.save(os.path.join(ziel, "schluepfen.png"))
        for i, name in enumerate(STUFEN):
            st = i + 1
            frames, maul, kopf = (mongo_frames if familie == "mongo" else tummy_frames)(st, p)
            boden = frames["idle"][0][0].getbbox()[3]
            links, oben, b, h, fl = zuschnitt(frames, boden)
            ordner = os.path.join(ziel, name)
            os.makedirs(ordner, exist_ok=True)
            for anim, liste in frames.items():
                assert len(liste) == TAKT[anim][0], (anim, len(liste))
                streifen(liste, links, oben, b, h).save(os.path.join(ordner, f"{anim}.png"))
            info = {
                "breite": b, "hoehe": h,
                "animationen": {a: {"frames": n, "ms": ms} for a, (n, ms) in TAKT.items()},
                "fussLuft": fl,
                "maul": [round(maul[0] - links), round(maul[1] - oben)],
                "schlafZ": [round(kopf[0] - links), max(0, round(kopf[1] - oben))],
            }
            with open(os.path.join(ordner, "sprite.json"), "w", encoding="utf-8") as fh:
                json.dump(info, fh, indent=2)
            masse[familie][name] = info
    ts = [
        "// Erzeugt von docs/assets/critter-pet/dcc_exportieren.py — nicht von Hand ändern.",
        "// Mongo und Tummy-Acher (Mark, 15.11.2026): Ei + 6 Schritte, je Farbe eine Art,",
        "// alle Farben einer Familie mit denselben Maßen (frontend/public/pets/<art>/<stufe>/sprite.json).",
        "",
        "export interface TierStufe {",
        "  breite: number;",
        "  hoehe: number;",
        "  fussLuft: number;",
        "  /** Maul im Sprite (blickt nach rechts) — dort landet, was er frisst. */",
        "  maul: readonly [number, number];",
        "  /** Kopf im Schlaf — dort steigt das Zzz auf. */",
        "  schlafZ: readonly [number, number];",
        "}",
        "",
        "export const TIER_STUFEN: Record<\"mongo\" | \"tummy\", Record<string, TierStufe>> = {",
    ]
    for fam, stufen in masse.items():
        ts.append(f"  {fam}: {{")
        for name, m in stufen.items():
            ts.append(f"    {name}: {{ breite: {m['breite']}, hoehe: {m['hoehe']}, fussLuft: {m['fussLuft']}, "
                      f"maul: [{m['maul'][0]}, {m['maul'][1]}], schlafZ: [{m['schlafZ'][0]}, {m['schlafZ'][1]}] }},")
        ts.append("  },")
    ts.append("};")
    ts.append("")
    with open(os.path.join(wurzel, "frontend", "src", "pets", "tierstufen.ts"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(ts))
    print("exportiert:", ", ".join(ARTEN))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
