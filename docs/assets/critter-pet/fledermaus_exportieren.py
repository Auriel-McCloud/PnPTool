# Export der Vampir-Fledermaus (Mark, 17.11.2026: „Sehr gut! Bitte setz das um“).
# Figuren aus vampir_entwurf.py (abgenommen), zwei Arten: `fledermaus` (Mann)
# und `fledermaus_w` (Frau). Ei + 6 Schritte (`s1` … `s6`); ab `s3` kann sie
# sich in die Vampirgestalt ihrer Stufe verwandeln (Streifen `v_*`).
#
# Alle Streifen einer Stufe haben denselben Rahmen (beide Geschlechter gleich):
#   - stehen/fressen/v_*: Füße auf der Unterkante
#   - haengen/schlafen/freuen: kopfüber, die Krallen an der Oberkante (Zeile `griff`)
#   - flattern/taumeln: senkrecht mittig
# Die Steuerung (frontend/src/pets/fledermaus.ts) setzt den Rahmen danach.
#
# Aufruf: python fledermaus_exportieren.py <repo-wurzel>
#   → frontend/public/pets/<art>/{ei,schluepfen,herz,z,tropfen}.png
#   → frontend/public/pets/<art>/s1..s6/<animation>.png + sprite.json
#   → frontend/src/pets/fledermausstufen.ts (Maße und Takte, generiert)
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import dcc_exportieren as dx  # noqa: E402
import vampir_entwurf as ve  # noqa: E402

ARTEN = {"fledermaus": "M", "fledermaus_w": "W"}
STUFEN = ["s1", "s2", "s3", "s4", "s5", "s6"]
EI_SCHALE = {"M": ((70, 62, 96), (110, 100, 140), (160, 150, 190)),
             "W": ((120, 84, 136), (170, 130, 186), (214, 186, 226))}

# Takte — gleiche Werte in fledermausstufen.ts (generiert) für die Steuerung.
TAKT = {
    "flattern": (8, 70), "haengen": (24, 110), "schlafen": (24, 150), "stehen": (24, 110),
    "fressen": (16, 90), "freuen": (8, 90), "taumeln": (8, 60),
    "v_idle": (24, 110), "v_lauf": (16, 70), "v_freuen": (12, 90),
    "v_idle_hut": (24, 110), "v_lauf_hut": (16, 70), "v_freuen_hut": (12, 90), "v_hut": (12, 90),
    "verwandeln": (16, 70),
}
GRUPPE = {
    "flattern": "flug", "taumeln": "flug",
    "haengen": "haengen", "schlafen": "haengen", "freuen": "haengen",
}  # alles andere: "boden"

NORM = 220          # normierte Arbeitsfläche
NX = NORM // 2      # Figurmitte x
BODEN = 196         # Fußlinie (Unterkante) der Bodengruppe
GRIFF = 12          # Krallenlinie (Oberkante) der Hängegruppe

_cache: dict = {}


def _fl(stufe, g, **kw):
    key = ("f", stufe, g, tuple(sorted(kw.items())))
    if key not in _cache:
        _cache[key] = ve.fledermaus(stufe, g, stange=False, gross=True, **kw)
    return _cache[key]


def _vp(g, stufe, **kw):
    key = ("v", g, stufe, tuple(sorted(kw.items())))
    if key not in _cache:
        _cache[key] = ve.vampir(g, stufe, **kw)
    return _cache[key]


def _q(x):
    """Atem auf drei Stufen — feiner sieht man es nicht, spart Rechenzeit."""
    return round(x)


def bat_frames(st, g):
    f = {}
    f["flattern"] = [_fl(st, g, pose="flug", fluegel=v) for v in (-1, -0.55, 0.2, 0.85, 1, 0.5, -0.15, -0.75)]
    f["haengen"] = [_fl(st, g, pose="haengen", augen="zu" if k in (19, 20) else "offen",
                        atem=_q(math.sin(2 * math.pi * k / 24))) for k in range(24)]
    f["schlafen"] = [_fl(st, g, pose="haengen", augen="zu", atem=_q(math.sin(2 * math.pi * k / 24))) for k in range(24)]
    f["stehen"] = [_fl(st, g, augen="zu" if k in (19, 20) else "offen", atem=_q(math.sin(2 * math.pi * k / 24)))
                   for k in range(24)]
    f["fressen"] = [_fl(st, g, maul_auf=(4 <= k < 13 and k % 2 == 0)) for k in range(16)]
    f["freuen"] = [_fl(st, g, pose="haengen", augen="freude", atem=_q(math.sin(2 * math.pi * k / 8))) for k in range(8)]
    f["taumeln"] = [_fl(st, g, pose="flug", augen="kringel", zerzaust=True, fluegel=v)
                    for v in (-1, 0.3, 1, -0.2, -0.9, 0.6, 0.9, -0.4)]
    return f


def vamp_frames(st, g):
    if st < 3:
        return {}
    voll = g == "M" and st == 6  # Erwachsener Mann: Gehstock immer, Zylinder manchmal
    f = {}

    def satz(hut):
        k_ = dict(stock=voll, zylinder=hut)
        idle = [_vp(g, st, hub=1 if 6 <= k < 18 else 0, blink=k in (19, 20), **k_) for k in range(24)]
        lauf = [_vp(g, st, gang=k / 16, **k_) for k in range(16)]
        kuss = [0.08, 0.2, 0.34, 0.46, 0.5, 0.5, 0.62, 0.78, 0.92, 1.0, 1.0, 1.0]
        freuen = [_vp(g, st, kuss=v, **k_) for v in kuss]
        return idle, lauf, freuen

    f["v_idle"], f["v_lauf"], f["v_freuen"] = satz(False)
    if voll:
        f["v_idle_hut"], f["v_lauf_hut"], f["v_freuen_hut"] = satz(True)
        hoch = [0.15, 0.4, 0.7, 0.9, 1.0, 1.0, 1.0, 1.0, 0.8, 0.5, 0.2, 0.0]
        f["v_hut"] = [_vp(g, st, stock=True, zylinder=True, hut_hoch=v) for v in hoch]
    return f


def _bob(name, k):
    """Hochversatz (px) je Frame: Gehen wippt."""
    if name.startswith("v_lauf"):
        return round(abs(math.sin(2 * math.pi * k / 16)) * 1)
    return 0


def normieren(bild, art, gruppe, ref):
    """Bild in die normierte Fläche: Figurmitte bei NX, Füße auf BODEN bzw.
    Krallen auf GRIFF. `ref` = Bezugslinie im Quellbild (Füße / Krallen / Mitte)."""
    n = Image.new("RGBA", (NORM, NORM), (0, 0, 0, 0))
    cx = 48 if art == "f" else 36
    if gruppe == "boden":
        dy = BODEN - ref
    elif gruppe == "haengen":
        dy = GRIFF - ref
    else:
        dy = NORM // 2 - ref
    n.alpha_composite(bild, (NX - cx, dy))
    return n


def stufe_exportieren(st, ziele):
    """Beide Geschlechter einer Stufe: gemeinsamer Rahmen, Streifen schreiben."""
    roh = {}
    for g in ("M", "W"):
        fr = {}
        b = bat_frames(st, g)
        v = vamp_frames(st, g)
        steh_ref = b["stehen"][0].getbbox()[3]
        haeng_ref = b["haengen"][0].getbbox()[1]
        flug_ref = (b["flattern"][0].getbbox()[1] + b["flattern"][0].getbbox()[3]) // 2
        for name, liste in b.items():
            gr = GRUPPE.get(name, "boden")
            ref = {"boden": steh_ref, "haengen": haeng_ref, "flug": flug_ref}[gr]
            fr[name] = [normieren(x, "f", gr, ref) for x in liste]
        if v:
            v_ref = v["v_idle"][0].getbbox()[3]
            for name, liste in v.items():
                fr[name] = [normieren(x, "v", "boden", v_ref) for x in liste]
        roh[g] = fr

    # Gemeinsamer Rahmen
    halb, b_oben, h_unten, f_oben, f_unten = 0, BODEN, GRIFF, NORM, 0
    for g, fr in roh.items():
        for name, liste in fr.items():
            gr = GRUPPE.get(name, "boden")
            for k, x in enumerate(liste):
                bb = x.getbbox()
                if not bb:
                    continue
                halb = max(halb, NX - bb[0], bb[2] - NX)
                if gr == "boden":
                    b_oben = min(b_oben, bb[1] - _bob(name, k))
                elif gr == "haengen":
                    h_unten = max(h_unten, bb[3])
                else:
                    f_oben, f_unten = min(f_oben, bb[1]), max(f_unten, bb[3])
    breite = 2 * (halb + 1)
    boden_unten = BODEN  # Unterkante der Füße (exklusiv) = Unterkante des Rahmens
    hoehe = max(boden_unten - b_oben, h_unten - GRIFF + 2, f_unten - f_oben + 2)
    hoehe += hoehe % 2
    links = NX - breite // 2
    oben = {"boden": boden_unten - hoehe, "haengen": GRIFF - 1,
            "flug": (f_oben + f_unten) // 2 - hoehe // 2}

    puff = puff_streifen(breite, hoehe, st) if st >= 3 else None
    info = None
    for g, fr in roh.items():
        ordner = ziele[g]
        os.makedirs(ordner, exist_ok=True)
        for name, liste in fr.items():
            assert len(liste) == TAKT[name][0], (name, len(liste))
            gr = GRUPPE.get(name, "boden")
            sheet = Image.new("RGBA", (breite * len(liste), hoehe), (0, 0, 0, 0))
            for k, x in enumerate(liste):
                o = oben[gr] + _bob(name, k)
                sheet.alpha_composite(x.crop((links, o, links + breite, o + hoehe)), (k * breite, 0))
            sheet.save(os.path.join(ordner, f"{name}.png"))
        if puff is not None:
            puff.save(os.path.join(ordner, "verwandeln.png"))
        # Anker (Sprite-Pixel im Rahmen)
        steh = fr["stehen"][0].getbbox()
        haeng = fr["haengen"][0].getbbox()
        flug = fr["flattern"][0].getbbox()
        vamp = fr["v_idle"][0].getbbox() if "v_idle" in fr else None
        neu = {
            "breite": breite, "hoehe": hoehe, "fussLuft": 0,
            "griff": GRIFF - oben["haengen"],
            # Maul beim Stehen (Fressen am Napf): oberes Drittel der Figur
            "maul": [breite // 2, round(steh[1] + (steh[3] - steh[1]) * 0.42 - oben["boden"])],
            "kopfStehen": [breite // 2, steh[1] - oben["boden"] + 3],
            "kopfHaengen": [breite // 2, haeng[3] - oben["haengen"] - 6],
            "kopfFlug": [breite // 2, flug[1] - oben["flug"] + 4],
            "kopfVampir": [breite // 2, vamp[1] - oben["boden"] + 2] if vamp else None,
            "animationen": {a: {"frames": n, "ms": ms} for a, (n, ms) in TAKT.items() if a in fr or (a == "verwandeln" and puff is not None)},
        }
        with open(os.path.join(ordner, "sprite.json"), "w", encoding="utf-8") as fh:
            json.dump(neu, fh, indent=2)
        info = info or neu
        if g == "M":
            info = neu  # Maße gleich; Animationsliste vom Mann (hat die Hut-Streifen)
    return info


def puff_streifen(breite, hoehe, st):
    """Verwandlungswolke: Rauch quillt auf, Mini-Fledermäuse stieben heraus,
    der Rauch zerfasert. Mitte = Körpermitte der Bodenfiguren."""
    import random
    n, rnd = TAKT["verwandeln"][0], random.Random(40 + st)
    cx, cy = breite / 2, hoehe * 0.62
    r_max = min(breite, hoehe) * 0.42
    wolken = [(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.35, 0.6), rnd.choice((0, 1, 2))) for _ in range(22)]
    flatterer = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.7, 1.2), rnd.uniform(0.6, 1.0)) for _ in range(6)]
    farben = [(96, 78, 120), (138, 118, 160), (186, 170, 206)]
    sheet = Image.new("RGBA", (breite * n, hoehe), (0, 0, 0, 0))
    for k in range(n):
        t = k / (n - 1)
        bild = Image.new("RGBA", (breite, hoehe), (0, 0, 0, 0))
        d = ImageDraw.Draw(bild)
        wachs = min(1.0, t / 0.4)
        weg = max(0.0, (t - 0.55) / 0.45)
        for (ux, uy, rr, fi) in wolken:
            r = r_max * rr * (0.4 + 0.6 * wachs) * (1 - 0.5 * weg)
            x = cx + ux * r_max * (0.5 + 0.7 * weg)
            y = cy + uy * r_max * 0.9 - weg * r_max * 0.5
            a = int(235 * (1 - weg ** 1.5))
            if a <= 8 or r < 1:
                continue
            c = farben[fi]
            d.ellipse([x - r, y - r, x + r, y + r], fill=(*c, a))
        if t > 0.3:
            for (w, v, gr) in flatterer:
                tt = (t - 0.3) / 0.7
                x = cx + math.cos(w) * r_max * (0.3 + 1.1 * tt * v)
                y = cy + math.sin(w) * r_max * (0.3 + 0.9 * tt * v) - tt * r_max * 0.6
                s_ = 2.6 * gr
                schlag = 1.2 if k % 2 else -0.6
                d.polygon([(x - 2 * s_, y + schlag), (x - s_, y), (x, y - 0.8 * s_), (x + s_, y), (x + 2 * s_, y + schlag),
                           (x + s_, y + 0.8 * s_), (x, y + 0.3 * s_), (x - s_, y + 0.8 * s_)], fill=(34, 26, 46, 255))
        sheet.alpha_composite(bild, (k * breite, 0))
    return sheet


def ei_sheets(g):
    p = ve.FLED[g]
    schale, punkt, seed = EI_SCHALE[g], ve.rgba(p["A"]), 4
    eier = [dx.ei_bild(schale, punkt, seed, risse=r) for r in range(5)]
    sheet = Image.new("RGBA", (dx.EI_B * 5, dx.EI_H), (0, 0, 0, 0))
    for i, e in enumerate(eier):
        sheet.alpha_composite(e, (i * dx.EI_B, 0))
    kueken = _fl(1, g)
    kueken_blinz = _fl(1, g, augen="zu")
    hoehe_k = kueken.getbbox()[3] - kueken.getbbox()[1]
    bilder = []
    for k in range(dx.SCHLUEPF_FRAMES):
        if k < 8:
            bilder.append(dx.ei_bild(schale, punkt, seed, risse=4, kipp=[0, -6, 0, 6, 0, -9, 0, 9][k]))
        elif k < 10:
            bilder.append(dx.ei_bild(schale, punkt, seed, risse=4, kipp=[-4, 4][k - 8]))
        else:
            j = k - 10
            kap = (j * 7 + 2, j * 25) if j < 6 else (60, 0)
            hoch = min(hoehe_k, round((j + 1) * hoehe_k / 8))
            fig = kueken_blinz if k in (21, 22) else kueken
            bilder.append(dx.ei_bild(schale, punkt, seed, risse=4, kappe_weg=kap, kueken=fig, kueken_hoch=hoch))
    sl = Image.new("RGBA", (dx.EI_B * dx.SCHLUEPF_FRAMES, dx.EI_H), (0, 0, 0, 0))
    for i, e in enumerate(bilder):
        sl.alpha_composite(e, (i * dx.EI_B, 0))
    return sheet, sl


def main(wurzel):
    pets = os.path.join(wurzel, "frontend", "public", "pets")
    ziele = {}
    for art, g in ARTEN.items():
        z = os.path.join(pets, art)
        os.makedirs(z, exist_ok=True)
        ziele[g] = z
        for nebenbei in ("herz.png", "z.png", "tropfen.png"):
            shutil.copy(os.path.join(pets, "drache", nebenbei), os.path.join(z, nebenbei))
        ei, sl = ei_sheets(g)
        ei.save(os.path.join(z, "ei.png"))
        sl.save(os.path.join(z, "schluepfen.png"))
    masse = {}
    for i, name in enumerate(STUFEN):
        masse[name] = stufe_exportieren(i + 1, {g: os.path.join(z, name) for g, z in ziele.items()})
        print(name, masse[name]["breite"], "x", masse[name]["hoehe"], flush=True)
    ts = [
        "// Erzeugt von docs/assets/critter-pet/fledermaus_exportieren.py — nicht von Hand ändern.",
        "// Vampir-Fledermaus (Mark, 17.11.2026): Ei + 6 Schritte, Mann und Frau mit denselben",
        "// Rahmen je Stufe (frontend/public/pets/<art>/<stufe>/sprite.json). Ab s3 Vampirgestalt (v_*).",
        "",
        "export interface FledermausStufe {",
        "  breite: number;",
        "  hoehe: number;",
        "  /** Leerraum unter den Füßen (Boden-Streifen). */",
        "  fussLuft: number;",
        "  /** Zeile der Krallen beim Kopfüber-Hängen (Hänge-Streifen). */",
        "  griff: number;",
        "  /** Maul beim Stehen — dort landet das Futter. */",
        "  maul: readonly [number, number];",
        "  kopfStehen: readonly [number, number];",
        "  kopfHaengen: readonly [number, number];",
        "  kopfFlug: readonly [number, number];",
        "  /** Kopf der Vampirgestalt (null: noch keine Vampirgestalt). */",
        "  kopfVampir: readonly [number, number] | null;",
        "}",
        "",
        "export const FLEDERMAUS_STUFEN: Record<string, FledermausStufe> = {",
    ]
    for name, m in masse.items():
        kv = f"[{m['kopfVampir'][0]}, {m['kopfVampir'][1]}]" if m["kopfVampir"] else "null"
        ts.append(f"  {name}: {{ breite: {m['breite']}, hoehe: {m['hoehe']}, fussLuft: {m['fussLuft']}, griff: {m['griff']}, "
                  f"maul: [{m['maul'][0]}, {m['maul'][1]}], kopfStehen: [{m['kopfStehen'][0]}, {m['kopfStehen'][1]}], "
                  f"kopfHaengen: [{m['kopfHaengen'][0]}, {m['kopfHaengen'][1]}], kopfFlug: [{m['kopfFlug'][0]}, {m['kopfFlug'][1]}], "
                  f"kopfVampir: {kv} }},")
    ts += ["};", "", "/** Takte aller Streifen (frames × ms). */",
           "export const FLEDERMAUS_TAKT: Record<string, { frames: number; ms: number }> = {"]
    for a, (n, ms) in TAKT.items():
        ts.append(f"  {a}: {{ frames: {n}, ms: {ms} }},")
    ts += ["};", ""]
    with open(os.path.join(wurzel, "frontend", "src", "pets", "fledermausstufen.ts"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(ts))
    print("exportiert:", ", ".join(ARTEN))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(HIER, "..", "..", "..")))
