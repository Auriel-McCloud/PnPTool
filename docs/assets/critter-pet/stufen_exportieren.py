# Exportiert die großen Wachstumsstufen des Drachen (Mark, 13.11.2026) und den
# Schlafkringel für ALLE Stufen ins Frontend.
# Aufruf: python stufen_exportieren.py C:/DEV/PnPTool/frontend/public/pets
#   → <art>/<stufe>/<animation>.png + sprite.json   (halbstark, jungdrache, gross, ehrwuerdig)
#   → <art>/schlafen.png, <art>/einkringeln.png      (junger Drache, im alten 84×48-Rahmen)
#   → <art>/baby/schlafen.png, <art>/baby/einkringeln.png
#   → frontend/src/pets/drachenstufen.ts             (Maße für PetOverlay — nicht von Hand ändern)
# Die alten Exporter (sprites_exportieren.py, jung_exportieren.py) schreiben
# `schlafen` nicht mehr selbst, sondern rufen `alt_schlaf()` von hier.
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drache_final as dr  # noqa: E402
import drache_jung as dj  # noqa: E402
import drache_stufen as ds  # noqa: E402
import drachen_varianten as dv  # noqa: E402

ARTEN = ("drache", "eisdrache", "blitzdrache")
OBEN = 4  # Luft über dem alten Rahmen (wie in den alten Exportern)


def _union(bilder):
    box = None
    for b in bilder:
        bb = b.getbbox()
        box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    return box


def _verschoben(bild, hoch):
    if not hoch:
        return bild
    v = Image.new("RGBA", bild.size, (0, 0, 0, 0))
    v.paste(bild, (0, -hoch))
    return v


def _streifen(bilder, box):
    w, h = box[2] - box[0], box[3] - box[1]
    s = Image.new("RGBA", (w * len(bilder), h), (0, 0, 0, 0))
    for i, b in enumerate(bilder):
        s.alpha_composite(b.crop(box), (i * w, 0))
    return s


def stufe_exportieren(ziel, key):
    """Alle Streifen einer großen Stufe + sprite.json. Gibt die Maße zurück."""
    st = ds.STUFEN[key]
    anis = {}
    for name, (frames, ms) in ds.animationen(st).items():
        anis[name] = ([_verschoben(*f) if isinstance(f, tuple) else f for f in frames], ms)
    box = _union([b for frames, _ in anis.values() for b in frames])
    box = (box[0] - 1, box[1] - 1, box[2] + 1, ds.BODEN + 3)
    # Gerade Maße: am Handy wird mit 1,5 skaliert — ungerade Breiten gäben halbe
    # Bildschirm-Pixel und damit Ränder vom Nachbar-Frame.
    box = (box[0], box[1] - (box[3] - box[1]) % 2, box[2] + (box[2] - box[0]) % 2, box[3])
    os.makedirs(ziel, exist_ok=True)
    meta = {"breite": box[2] - box[0], "hoehe": box[3] - box[1], "animationen": {}}
    for name, (frames, ms) in anis.items():
        _streifen(frames, box).save(os.path.join(ziel, f"{name}.png"))
        meta["animationen"][name] = {"frames": len(frames), "ms": ms}
    lauf_unten = _union(anis["lauf"][0])[3]
    meta["fussLuft"] = box[3] - lauf_unten
    _, z = ds.roh_wach(st, mit_z=True)
    meta["maul"] = [round(z.maul[0] - box[0]), round(z.maul[1] - box[1])]
    _, zr = ds.roh_ring(st, mit_z=True)
    ring_oben = _union(anis["schlafen"][0])[1]
    meta["schlafZ"] = [round(zr.kopf[0] - box[0]), ring_oben - box[1]]
    meta["feuerSkala"] = ds.FEUER_SKALA[key]
    with open(os.path.join(ziel, "sprite.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta


def _alt_rahmen(key, inhalt):
    """Wo der alte Rahmen (junger Drache 84×48, Schlüpfling 50×38) auf der
    Arbeitsleinwand der neuen Zeichnung liegt: Füße auf dieselbe Linie,
    waagrecht so, dass sich alte und neue Figur am besten decken — aber nur
    Lagen, in denen alle Kringel-Frames (`inhalt` = ihre gemeinsame Box) in
    den Rahmen passen."""
    if key == "jung":
        alt = Image.new("RGBA", (dr.W, dr.H + OBEN), (0, 0, 0, 0))
        alt.alpha_composite(dr.frame(phase=0.0, welle=0.0, amp=3.0), (0, OBEN))
    else:
        alt = Image.new("RGBA", (dj.BW, dj.BH + OBEN), (0, 0, 0, 0))
        alt.alpha_composite(dj.baby(phase=0.0, welle=0.0, amp=1.4), (0, OBEN))
    neu = ds.roh_wach(ds.STUFEN[key])
    oy = neu.getbbox()[3] - alt.getbbox()[3]
    a = alt.getchannel("A")
    beste, ox = -1, 0
    for kandidat in range(inhalt[2] - alt.width, inhalt[0] + 1):
        n = neu.crop((kandidat, oy, kandidat + alt.width, oy + alt.height)).getchannel("A")
        deckung = sum(1 for p, q in zip(a.tobytes(), n.tobytes()) if p and q)
        if deckung > beste:
            beste, ox = deckung, kandidat
    return (ox, oy, ox + alt.width, oy + alt.height)


def alt_schlaf(ziel, key):
    """Schlafkringel + Einkringeln für die beiden alten Stufen (`jung`, `baby`)
    in deren bestehendem Rahmen. Gibt die Einträge für sprite.json zurück."""
    st = ds.STUFEN[key]
    schlafen, ein = ds.schlafen_frames(st), ds.einkringeln_frames(st)
    u = _union(schlafen + ein)
    box = _alt_rahmen(key, u)
    if u[0] < box[0] or u[1] < box[1] or u[2] > box[2] or u[3] > box[3]:
        raise SystemExit(f"{key}: Kringel passt nicht in den alten Rahmen {box}: {u}")
    _streifen(schlafen, box).save(os.path.join(ziel, "schlafen.png"))
    _streifen(ein, box).save(os.path.join(ziel, "einkringeln.png"))
    _, zr = ds.roh_ring(st, mit_z=True)
    return {
        "animationen": {"schlafen": {"frames": len(schlafen), "ms": 150},
                        "einkringeln": {"frames": len(ein), "ms": ds.EINKRINGELN_MS}},
        "schlafZ": [round(zr.kopf[0] - box[0]), _union(schlafen)[1] - box[1]],
    }


def ts_schreiben(pfad, stufen, alt):
    z = ["// Erzeugt von docs/assets/critter-pet/stufen_exportieren.py — nicht von Hand ändern.",
         "// Maße der großen Drachen-Stufen (Mark, 13.11.2026) und Schlaf-Anker aller Stufen,",
         "// gleiche Werte wie frontend/public/pets/<art>/<stufe>/sprite.json.",
         "",
         "/** Übergang wach → eingekringelt (einkringeln.png); rückwärts = aufwachen. */",
         f"export const EINKRINGELN = {{ frames: {stufen[ds.NEU[0]]['animationen']['einkringeln']['frames']}, ms: {ds.EINKRINGELN_MS} }} as const;",
         "",
         "export interface DrachenStufe {",
         "  breite: number;",
         "  hoehe: number;",
         "  fussLuft: number;",
         "  /** Maul im Sprite — dort setzen Feuer und Futter an. */",
         "  maul: readonly [number, number];",
         "  /** Wo das Zzz über dem Schlafkringel sitzt (Kopf-x, Oberkante). */",
         "  schlafZ: readonly [number, number];",
         "  /** Der Atem wächst mit. */",
         "  feuerSkala: number;",
         "}",
         "",
         "/** Schlüssel = `stufe` im Pet-Dict = Ordner unter /pets/<art>/. */",
         "export const DRACHEN_STUFEN: Record<string, DrachenStufe> = {"]
    for key in ds.NEU:
        m = stufen[key]
        z.append(f"  {key}: {{ breite: {m['breite']}, hoehe: {m['hoehe']}, fussLuft: {m['fussLuft']}, "
                 f"maul: [{m['maul'][0]}, {m['maul'][1]}], schlafZ: [{m['schlafZ'][0]}, {m['schlafZ'][1]}], "
                 f"feuerSkala: {m['feuerSkala']} }},")
    z += ["};", "", "/** Zzz-Anker für Schlüpfling und jungen Drachen (alte Rahmen). */",
          "export const SCHLAF_Z: Record<string, readonly [number, number]> = {"]
    for key in ("baby", "jung"):
        z.append(f"  {key}: [{alt[key]['schlafZ'][0]}, {alt[key]['schlafZ'][1]}],")
    z += ["};", ""]
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(z))


def _json_ergaenzen(pfad, extra):
    with open(pfad, encoding="utf-8") as f:
        meta = json.load(f)
    meta["animationen"].update(extra["animationen"])
    meta["schlafZ"] = extra["schlafZ"]
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    basis = sys.argv[1]
    original = dict(dr.PAL)
    stufen, alt = None, None
    for art in ARTEN:
        dr.PAL.update(original)
        dr.KEIN_OUTLINE.clear()
        dr.KEIN_OUTLINE.add(dr.PAL["F"])
        if art != "drache":
            dv.palette(art)
        s_ = {key: stufe_exportieren(os.path.join(basis, art, key), key) for key in ds.NEU}
        a_ = {"jung": alt_schlaf(os.path.join(basis, art), "jung"),
              "baby": alt_schlaf(os.path.join(basis, art, "baby"), "baby")}
        _json_ergaenzen(os.path.join(basis, art, "sprite.json"), a_["jung"])
        _json_ergaenzen(os.path.join(basis, art, "baby", "sprite.json"), a_["baby"])
        # Maße hängen nicht von der Farbe ab — sonst stimmt die eine TS-Datei nicht.
        assert stufen is None or (s_ == stufen and a_ == alt), f"{art}: Maße weichen ab"
        stufen, alt = s_, a_
        print(art, "ok")
    dr.PAL.update(original)
    ts = os.path.normpath(os.path.join(basis, "..", "..", "src", "pets", "drachenstufen.ts"))
    ts_schreiben(ts, stufen, alt)
    print(json.dumps({k: {x: v for x, v in m.items() if x != "animationen"} for k, m in stufen.items()}))
    print(json.dumps({k: m["schlafZ"] for k, m in alt.items()}), ts)
