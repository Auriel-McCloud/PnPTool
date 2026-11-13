"""Critter-Pets: Wirtwahl und Wandern zwischen Tablets.

Ohne Datenbank: das Repository wird durch eine kleine Attrappe ersetzt,
die Leitungen durch Sockets, die nur mitschreiben.
"""

import asyncio
import random

import pytest

from app.pets import logic, motor as motor_modul
from app.pets.motor import PetMotor


class TestLogik:
    def test_naechster_wirt_bevorzugt_jemand_anderen(self):
        for _ in range(20):
            assert logic.naechster_wirt(["a", "b"], "a") == "b"

    def test_allein_kommt_es_zurueck(self):
        assert logic.naechster_wirt(["a"], "a") == "a"

    def test_niemand_online(self):
        assert logic.naechster_wirt([], "a") is None

    def test_gegenseite(self):
        assert logic.gegenseite("rechts") == "links"
        assert logic.gegenseite("links") == "rechts"

    def test_anteil_wird_begrenzt(self):
        assert logic.anteil(-3) == 0.0
        assert logic.anteil(7) == 1.0
        assert logic.anteil(0.25) == 0.25


class Socket:
    def __init__(self):
        self.post: list[dict] = []

    async def send_json(self, umschlag):
        self.post.append(umschlag)

    def letzte_pets(self) -> list[dict]:
        return [u["daten"] for u in self.post if u["typ"] == "pets"][-1]


@pytest.fixture
def welt(monkeypatch):
    """Ein Drache von Anna, Party: Anna, Ben, Cleo. Häufchen im Speicher."""
    stand = {
        "pets": [{
            "id": "drache", "name": "Feuerchen", "art": "drache",
            "besitzerId": "anna", "besitzerName": "Anna", "mitglieder": ["anna", "ben", "cleo"],
        }],
        "haeufchen": {},
        "pausiert": False,
    }

    async def pets_der_kampagne(cid):
        return [dict(p) for p in stand["pets"]]

    async def haeufchen_liste(cid, pid):
        return list(stand["haeufchen"].get(pid, []))

    async def haeufchen_anlegen(cid, pid, pet_id, x, y, art="haeufchen"):
        stand["haeufchen"].setdefault(pid, []).append({"id": f"h{x}", "petId": pet_id, "x": x, "y": y, "art": art})

    async def haeufchen_weg(cid, pid, hid):
        stand["haeufchen"][pid] = [h for h in stand["haeufchen"].get(pid, []) if h["id"] != hid]

    async def haeufchen_verschieben(cid, pid, hid, x, y):
        for h in stand["haeufchen"].get(pid, []):
            if h["id"] == hid and h["art"] == "haeufchen":
                h["x"], h["y"] = x, y

    async def pets_pausiert(cid):
        return stand["pausiert"]

    # Drachenperle: liegt als Spur mit art "perle" bei einer Person.
    def _perlen():
        return [(pid, h) for pid, liste in stand["haeufchen"].items() for h in liste if h["art"] == "perle"]

    async def perlen(cid):
        return {h["petId"]: {"id": h["id"], "petId": h["petId"], "personId": pid, "von": h.get("von")}
                for pid, h in _perlen()}

    async def perle_lesen(cid, hid):
        return next(({"id": h["id"], "petId": h["petId"], "personId": pid, "von": h.get("von")}
                     for pid, h in _perlen() if h["id"] == hid), None)

    async def perle_weg(cid, hid):
        for pid, liste in stand["haeufchen"].items():
            stand["haeufchen"][pid] = [h for h in liste if h["id"] != hid]

    async def perle_legen(cid, pid, pet_id, x):
        for _, h in _perlen():
            if h["petId"] == pet_id:
                await perle_weg(cid, h["id"])
        stand["perlen_nr"] = stand.get("perlen_nr", 0) + 1
        stand["haeufchen"].setdefault(pid, []).append(
            {"id": f"perle{stand['perlen_nr']}", "petId": pet_id, "x": x, "y": 1.0, "art": "perle", "von": None})

    async def perle_umlegen(cid, hid, ziel, x, von):
        alt = next(h for _, h in _perlen() if h["id"] == hid)
        await perle_weg(cid, hid)
        stand["haeufchen"].setdefault(ziel, []).append({**alt, "x": x, "von": von, "geworfen": True})

    repo = motor_modul.repository
    for name, fn in (("perlen", perlen), ("perle_lesen", perle_lesen), ("perle_weg", perle_weg),
                     ("perle_legen", perle_legen), ("perle_umlegen", perle_umlegen)):
        monkeypatch.setattr(repo, name, fn)
    monkeypatch.setattr(repo, "pets_pausiert", pets_pausiert)
    monkeypatch.setattr(repo, "pets_der_kampagne", pets_der_kampagne)
    monkeypatch.setattr(repo, "haeufchen_liste", haeufchen_liste)
    monkeypatch.setattr(repo, "haeufchen_anlegen", haeufchen_anlegen)
    monkeypatch.setattr(repo, "haeufchen_weg", haeufchen_weg)
    monkeypatch.setattr(repo, "haeufchen_verschieben", haeufchen_verschieben)
    m = PetMotor(zufall=random.Random(1), pause_min=0, pause_max=0)
    return m, stand


def laufen(coro):
    return asyncio.run(coro)


def test_pet_startet_beim_besitzer(welt):
    m, _ = welt

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "ben", ben)
        assert ben.letzte_pets() == []  # Besitzerin noch nicht da: kein Pet
        await m.anmelden("k", "anna", anna)
        assert [p["id"] for p in anna.letzte_pets()] == ["drache"]
        assert ben.letzte_pets() == []
        m._takt.cancel()

    laufen(ablauf())


def test_rechts_raus_beim_naechsten_links_rein(welt):
    m, _ = welt

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        await m.raus("k", "anna", "drache", "rechts")
        assert anna.letzte_pets() == []
        await asyncio.sleep(0.01)
        pets = ben.letzte_pets()
        assert [p["id"] for p in pets] == ["drache"]
        assert pets[0]["seite"] == "links"
        m._takt.cancel()

    laufen(ablauf())


def test_nur_der_wirt_darf_es_losschicken(welt):
    m, _ = welt

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        await m.raus("k", "ben", "drache", "rechts")  # Ben hat es gar nicht
        assert [p["id"] for p in anna.letzte_pets()] == ["drache"]
        m._takt.cancel()

    laufen(ablauf())


def test_fremde_ausserhalb_der_party_bekommen_es_nie(welt):
    m, _ = welt

    async def ablauf():
        anna, fremd = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "fremd", fremd)
        for _ in range(5):
            await m.raus("k", "anna", "drache", "links")
            await asyncio.sleep(0.01)
        assert all(u["daten"] == [] for u in fremd.post if u["typ"] == "pets")
        m._takt.cancel()

    laufen(ablauf())


def test_besitzer_geht_pet_verschwindet(welt):
    m, _ = welt

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        await m.raus("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        assert ben.letzte_pets() != []
        await m.abmelden("k", "anna", anna)
        assert ben.letzte_pets() == []
        m._takt.cancel() if m._takt else None

    laufen(ablauf())


def test_wirt_geht_pet_zieht_um(welt):
    m, _ = welt

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        await m.raus("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        await m.abmelden("k", "ben", ben)
        assert [p["id"] for p in anna.letzte_pets()] == ["drache"]
        m._takt.cancel()

    laufen(ablauf())


def test_haeufchen_nur_vom_wirt_und_bleibt(welt):
    m, stand = welt

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        await m.haeufchen("k", "ben", "drache", 0.5, 0.9)  # Ben hat das Pet nicht
        assert stand["haeufchen"].get("ben") is None
        await m.haeufchen("k", "anna", "drache", 0.5, 0.9)
        await m.raus("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        assert len(stand["haeufchen"]["anna"]) == 1  # bleibt liegen
        await m.wegmachen("k", "anna", "h0.5")
        assert stand["haeufchen"]["anna"] == []
        m._takt.cancel()

    laufen(ablauf())


def test_brandfleck_bleibt_und_fremde_art_wird_ignoriert(welt):
    m, stand = welt

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        await m.haeufchen("k", "anna", "drache", 0.3, 0.4, "brand")
        await m.haeufchen("k", "anna", "drache", 0.3, 0.4, "konfetti")  # gibt es nicht
        assert [h["art"] for h in stand["haeufchen"]["anna"]] == ["brand"]
        letzte = [u["daten"] for u in anna.post if u["typ"] == "haeufchen"][-1]
        assert letzte[0]["art"] == "brand"
        m._takt.cancel()

    laufen(ablauf())


def test_heruntergefallenes_haeufchen_merkt_neue_position(welt):
    m, stand = welt

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        await m.haeufchen("k", "anna", "drache", 0.5, 0.4)
        await m.verschieben("k", "anna", "h0.5", 0.5, 1.7)  # wird auf 0..1 begrenzt
        assert stand["haeufchen"]["anna"][0]["y"] == 1.0
        letzte = [u["daten"] for u in anna.post if u["typ"] == "haeufchen"][-1]
        assert letzte[0]["y"] == 1.0
        m._takt.cancel()

    laufen(ablauf())


def test_baerbel_verliert_seiten(welt):
    """Bärbel (Gegenstand-Pet, 11.11.2026) hinterlässt Seiten statt Häufchen."""
    m, stand = welt
    stand["pets"].append({
        "id": "buch", "name": "Bärbel", "art": "baerbel",
        "besitzerId": "anna", "besitzerName": "Anna", "mitglieder": ["anna", "ben", "cleo"],
    })

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        assert sorted((p["id"], p["art"]) for p in anna.letzte_pets()) == [("buch", "baerbel"), ("drache", "drache")]
        await m.haeufchen("k", "anna", "buch", 0.5, 0.3, "seite")
        assert [h["art"] for h in stand["haeufchen"]["anna"]] == ["seite"]
        m._takt.cancel()

    laufen(ablauf())


def test_pet_arten_und_spuren():
    assert "baerbel" in logic.PET_ARTEN
    assert "seite" in logic.SPUR_ARTEN
    assert "schleim" in logic.SPUR_ARTEN  # Tentakelmonster
    assert set(logic.FALLENDE_SPUREN) == {"haeufchen", "seite"}


def test_abgedreht_oder_kampf_pets_weg_und_danach_wieder_da(welt):
    """Mark, 11.11.2026: Schalter in den Kampagnenoptionen, im Kampf automatisch aus."""
    m, stand = welt

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        assert [p["id"] for p in anna.letzte_pets()] == ["drache"]
        stand["pausiert"] = True
        await m.abgleich("k")
        assert anna.letzte_pets() == []
        stand["pausiert"] = False
        await m.abgleich("k")
        assert [p["id"] for p in anna.letzte_pets()] == ["drache"]
        m._takt.cancel()

    laufen(ablauf())

def test_kampf_blendet_spuren_aus_und_danach_wieder_ein(welt):
    """Mark, 11.11.: Häufchen und Schmutz im Kampf weg, danach wieder da. Nicht gelöscht."""
    m, stand = welt

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        await m.haeufchen("k", "anna", "drache", 0.4, 1, "haeufchen")
        await m.haeufchen("k", "anna", "drache", 0.2, 0.8, "brand")
        assert len(stand["haeufchen"]["anna"]) == 2
        stand["pausiert"] = True
        await m.abgleich("k")
        letzte = [u["daten"] for u in anna.post if u["typ"] == "haeufchen"][-1]
        assert letzte == []
        assert len(stand["haeufchen"]["anna"]) == 2
        stand["pausiert"] = False
        await m.abgleich("k")
        letzte = [u["daten"] for u in anna.post if u["typ"] == "haeufchen"][-1]
        assert len(letzte) == 2
        m._takt.cancel()

    laufen(ablauf())


def test_baerbel_liest_nach_anwesenheit_und_bleibt_bis_antippen(welt, monkeypatch):
    """Mark, 11.11.: alle 15 Minuten Anwesenheit, nicht im Kampf, bis zum Antippen."""
    m, stand = welt
    m.lesen_min = 0
    m.lesen_max = 0
    stand["pets"].append({
        "id": "buch", "name": "Bärbel", "art": "baerbel",
        "besitzerId": "anna", "besitzerName": "Anna", "mitglieder": ["anna", "ben"],
    })

    async def falsch(*_a, **_k):
        return {"stelle": "Johannes 1,5", "zitat": "Und das Licht scheint in der Finsternis."}

    monkeypatch.setattr("app.pets.vorlesen.erzeugen", falsch)

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        await m.lesen_takt("k", 1)
        lesen = [u for u in anna.post if u["typ"] == "vorlesen"]
        assert lesen and lesen[-1]["stelle"] == "Johannes 1,5"
        assert anna.letzte_pets()
        assert any(p.get("lesung", {}).get("stelle") == "Johannes 1,5" for p in anna.letzte_pets())
        await m.gelesen("k", "anna", "buch")
        assert all(not p.get("lesung") for p in anna.letzte_pets())
        stand["pausiert"] = True
        await m.abgleich("k")
        vorher = len([u for u in anna.post if u["typ"] == "vorlesen"])
        await m.lesen_takt("k", 999)
        assert len([u for u in anna.post if u["typ"] == "vorlesen"]) == vorher
        m._takt.cancel()

    laufen(ablauf())


def test_baerbel_wiederholt_keine_stelle(monkeypatch):
    """Mark, 12.11.: zweimal dasselbe Zitat — gleiche Stelle wird durch einen anderen Vers ersetzt."""
    from app.pets import vorlesen

    vorlesen._ZULETZT.clear()
    prompts = []

    async def lage(*_a, **_k):
        return "Spieler sind da."

    async def ki(prompt, *_a, **_k):
        prompts.append(prompt)
        return {"stelle": "Psalm 23,4", "zitat": "Und ob ich schon wanderte im finstern Tal, fürchte ich kein Unglück."}

    monkeypatch.setattr(vorlesen, "lage", lage)
    monkeypatch.setattr(vorlesen, "generiere_json", ki)

    erste = asyncio.run(vorlesen.erzeugen("k", "anna", ["anna"]))
    zweite = asyncio.run(vorlesen.erzeugen("k", "anna", ["anna"]))
    assert erste["stelle"] == "Psalm 23,4"
    assert zweite["stelle"] != "Psalm 23,4"
    assert "psalm23,4" in prompts[1]

def test_baerbel_fliegt_zum_vorlesen_heim(welt, monkeypatch):
    """Mark, 12.11.: Bibelverse nur beim Besitzer — woanders fliegt sie heim."""
    m, stand = welt
    m.lesen_min = 0
    m.lesen_max = 0
    stand["pets"] = [{
        "id": "buch", "name": "Bärbel", "art": "baerbel",
        "besitzerId": "anna", "besitzerName": "Anna", "mitglieder": ["anna", "ben", "cleo"],
    }]

    async def falsch(*_a, **_k):
        return {"stelle": "Psalm 23,1", "zitat": "Der Herr ist mein Hirte."}

    monkeypatch.setattr("app.pets.vorlesen.erzeugen", falsch)

    async def ablauf():
        anna, ben, cleo = Socket(), Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        await m.anmelden("k", "cleo", cleo)
        await m.raus("k", "anna", "buch", "rechts")
        await asyncio.sleep(0.01)
        wirt = next(p for p, s in (("ben", ben), ("cleo", cleo)) if s.letzte_pets())
        bei = ben if wirt == "ben" else cleo
        await m.lesen_takt("k", 1)
        # Beim Fremden: kein Vers, nur der Heimweg.
        assert not [u for u in bei.post if u["typ"] == "vorlesen"]
        pets = bei.letzte_pets()
        assert pets[0].get("heim") is True and not pets[0].get("lesung")
        # Sie fliegt raus und landet beim Besitzer, nicht beim Dritten.
        await m.raus("k", wirt, "buch", "links")
        await asyncio.sleep(0.01)
        bei_anna = anna.letzte_pets()
        assert [p["id"] for p in bei_anna] == ["buch"]
        assert bei_anna[0]["lesung"]["stelle"] == "Psalm 23,1"
        assert not bei_anna[0].get("heim")
        m._takt.cancel()

    laufen(ablauf())


def test_wachstum_stufen_und_faehigkeiten():
    """Mark, 12.11.: Ei → Baby (nur unten) → ab 3 EP klettern/niesen/hüpfen."""
    from app.pets import logic as lg

    assert lg.stufe("drache", "ei", 50, None) == ("ei", None)
    assert lg.stufe("drache", "geschluepft", 12, 10) == ("baby", 2)
    assert lg.stufe("drache", "geschluepft", 13, 10) == ("jung", 3)
    # Bestand ohne Stufe bleibt groß und kann alles.
    assert lg.stufe("drache", None, 0, None) == ("jung", None)
    assert lg.faehigkeiten("drache", "jung", None) == list(lg.ALLE_FAEHIGKEITEN)
    assert lg.faehigkeiten("drache", "ei", None) == []
    assert lg.faehigkeiten("eisdrache", "baby", 2) == []
    kann = lg.faehigkeiten("blitzdrache", "jung", 3)
    assert {"klettern", "niesen", "springen"} <= set(kann) and "wolken" not in kann and "menue" not in kann
    # Mark: Burgermenü ab 8 EP, Wolkenlauf ab 13 EP.
    assert "menue" in lg.faehigkeiten("drache", "jung", 8) and "wolken" not in lg.faehigkeiten("drache", "jung", 12)
    assert "wolken" in lg.faehigkeiten("drache", "jung", 13)
    # Mark, 13.11.: größere Gestalten — alle 5 EP ein Schritt, alle 3 Schritte
    # eine neue Gestalt (15/30/45/60 EP seit dem Schlüpfen).
    assert lg.stufe("drache", "geschluepft", 14, 10) == ("jung", 4)
    # Zwischenformen: jeder Schritt (5 EP) eine eigene, etwas größere Form.
    assert lg.stufe("drache", "geschluepft", 15, 10) == ("jung1", 5)
    assert lg.stufe("drache", "geschluepft", 24, 10) == ("jung2", 14)
    assert lg.stufe("drache", "geschluepft", 25, 10) == ("halbstark", 15)
    assert lg.stufe("drache", "geschluepft", 32, 10)[0] == "halbstark1"
    assert lg.stufe("drache", "geschluepft", 68, 10)[0] == "gross2"
    assert len(lg.STUFEN_FOLGE) == 13
    assert lg.stufe("eisdrache", "geschluepft", 40, 10)[0] == "jungdrache"
    assert lg.stufe("blitzdrache", "geschluepft", 55, 10)[0] == "gross"
    assert lg.stufe("drache", "geschluepft", 70, 10)[0] == "ehrwuerdig"
    assert lg.stufe("drache", "geschluepft", 500, 10)[0] == "ehrwuerdig"
    # Kampagnen-Einstellung `petWachstumEp`: 10 EP je Schritt → doppelt so langsam.
    assert lg.stufe("drache", "geschluepft", 39, 10, 10)[0] == "jung2"
    assert lg.stufe("drache", "geschluepft", 40, 10, 10)[0] == "halbstark"
    # SL setzt eine Stufe: die nötigen EP seit dem Schlüpfen ergeben wieder genau sie.
    for name in lg.STUFEN_FOLGE:
        for je in (1, 5, 10):
            ep = lg.gewachsen_fuer(name, je)
            if je >= lg.JUNG_AB_EP or lg.STUFEN_FOLGE.index(name) * je >= lg.JUNG_AB_EP:
                assert lg.stufe("drache", "geschluepft", ep, 0, je)[0] == name, (name, je)
    assert lg.gewachsen_fuer("baby") == 0 and lg.gewachsen_fuer("ei") is None
    # Die Großen können alles.
    assert set(lg.faehigkeiten("drache", "ehrwuerdig", 60)) == set(lg.ALLE_FAEHIGKEITEN) | {"perle", "feuerball"}
    # Feuerball ab dem Halbstarken, nicht für Bestandsdrachen.
    assert "feuerball" in lg.faehigkeiten("eisdrache", "halbstark", 15)
    assert "feuerball" not in lg.faehigkeiten("drache", "jung2", 14)
    assert "feuerball" not in lg.faehigkeiten("drache", "jung", None)
    # Bärbel wächst nicht.
    assert lg.stufe("baerbel", "ei", 0, None) == ("jung", None)
    assert lg.risse(0, 8) == 0 and lg.risse(4, 8) == 2 and lg.risse(8, 8) == 4


def test_ki_waechst_ohne_ei_in_dreizehn_schritten():
    """Mark, 13.11.: die KI ist ein Begleiter, der wachsen kann — Funke bis Entität."""
    from app.pets import logic as lg

    assert "ki" in lg.PET_ARTEN and lg.waechst("ki") and lg.ist_ki("ki") and not lg.ist_drache("ki")
    assert len(lg.KI_FOLGE) == len(lg.STUFEN_FOLGE) == 13
    # Kein Ei, kein Baby: ab dem ersten EP zählt jeder Schritt.
    assert lg.stufe("ki", "geschluepft", 10, 10) == ("funke", 0)
    assert lg.stufe("ki", "geschluepft", 14, 10) == ("funke", 4)
    assert lg.stufe("ki", "geschluepft", 15, 10)[0] == "funke1"
    assert lg.stufe("ki", "geschluepft", 25, 10)[0] == "keim"
    assert lg.stufe("ki", "geschluepft", 70, 10)[0] == "entitaet"
    assert lg.stufe("ki", "geschluepft", 900, 10)[0] == "entitaet"
    assert lg.stufe("ki", "geschluepft", 30, 10, 10)[0] == "funke2"
    # Ohne Stufenfeld (KI an einem Gegenstand) bleibt sie ein Funke.
    assert lg.stufe("ki", None, 500, None) == ("funke", None)
    for name in lg.KI_FOLGE:
        for je in (1, 5, 10):
            assert lg.stufe("ki", "geschluepft", lg.gewachsen_fuer(name, je), 0, je)[0] == name
    # Jede Art nur mit ihren eigenen Stufen.
    assert lg.stufe_passt("ki", "wesen1") and not lg.stufe_passt("ki", "ei") and not lg.stufe_passt("ki", "gross")
    assert lg.stufe_passt("drache", "ei") and lg.stufe_passt("eisdrache", "gross") and not lg.stufe_passt("drache", "keim")
    assert not lg.stufe_passt("baerbel", "jung")
    assert lg.faehigkeiten("ki", "entitaet", 60) == []


def test_feuerball_fliegt_aufs_nachbar_tablet(welt):
    """Mark, 13.11.: Feuerbälle, die weiter fliegen — über den Rand hinaus landet
    er bei jemand anderem aus der Party und hinterlässt dort einen großen Fleck."""
    m, stand = welt
    m.feuerball_flug = 0
    stand["pets"][0].update({"art": "eisdrache", "stufe": "halbstark", "kann": ["niesen", "feuerball"]})

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        # Allein am Tisch: er verpufft.
        await m.feuerball("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        assert stand["haeufchen"] == {}
        await m.anmelden("k", "ben", ben)
        # Nur wer den Drachen hat, kann schießen.
        await m.feuerball("k", "ben", "drache", "rechts")
        assert not [u for u in anna.post + ben.post if u["typ"] == "feuerball"]
        await m.feuerball("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        ball = [u for u in ben.post if u["typ"] == "feuerball"]
        assert len(ball) == 1 and ball[0]["seite"] == "links" and ball[0]["art"] == "eisdrache"
        assert not [u for u in anna.post if u["typ"] == "feuerball"]
        flecken = stand["haeufchen"]["ben"]
        assert len(flecken) == 1 and flecken[0]["art"] == "eiskrater"
        assert [u for u in ben.post if u["typ"] == "haeufchen"][-1]["daten"] == flecken
        # Nicht im Sekundentakt.
        await m.feuerball("k", "anna", "drache", "links")
        await asyncio.sleep(0.01)
        assert len([u for u in ben.post if u["typ"] == "feuerball"]) == 1
        # Zu jung: kein Feuerball.
        stand["pets"][0].update({"stufe": "jung2", "kann": ["niesen"]})
        await m.abgleich("k")
        m._pets["k"]["drache"].feuerball_zuletzt = -1e9
        await m.feuerball("k", "anna", "drache", "rechts")
        assert len([u for u in ben.post if u["typ"] == "feuerball"]) == 1
        m._takt.cancel()

    laufen(ablauf())


def test_drachenperle_werfen_suchen_zurueckbringen(welt):
    """Mark, 13.11.: Perle aus dem Bild werfen → sie liegt auf einem anderen Tablet,
    der Drache sucht (ohne zu wissen wo), hebt sie auf und bringt sie dem Werfer."""
    from app.pets import logic as lg

    assert "perle" in lg.faehigkeiten("drache", "ehrwuerdig", 60)
    assert "perle" not in lg.faehigkeiten("drache", "gross2", 58)
    assert "perle" not in lg.faehigkeiten("drache", "jung", None)  # Bestandsdrache
    # Suche: kein Tablet doppelt, bis alle durch sind.
    gesucht = {"ben"}
    assert lg.such_ziel(["anna", "ben", "cleo"], "anna", gesucht, random.Random(1)) == "cleo"
    assert lg.perle_ziel(["anna"], "anna") == "anna" and lg.perle_ziel(["anna", "ben"], "anna") == "ben"

    m, stand = welt
    stand["pets"][0].update({"stufe": "ehrwuerdig", "kann": ["klettern", "perle"]})

    async def ablauf():
        anna, ben, cleo = Socket(), Socket(), Socket()
        for name, s in (("anna", anna), ("ben", ben), ("cleo", cleo)):
            await m.anmelden("k", name, s)
        assert anna.letzte_pets()[0]["perle"] is None
        # Nur wo der Drache ist, kann er die Perle herausholen.
        await m.perle("k", "ben", "drache", 0.5)
        assert stand["haeufchen"].get("ben", []) == []
        await m.perle("k", "anna", "drache", 0.5)
        assert anna.letzte_pets()[0]["perle"] == "spiel"
        perle_id = stand["haeufchen"]["anna"][0]["id"]
        # Ein zweites Mal herausholen geht nicht — es gibt nur eine.
        await m.perle("k", "anna", "drache", 0.2)
        assert len(stand["haeufchen"]["anna"]) == 1
        # Ben kann Annas Perle nicht werfen.
        await m.perle_wurf("k", "ben", perle_id)
        assert stand["haeufchen"]["anna"]
        # Anna wirft sie hinaus: sie liegt bei jemand anderem, der Drache sucht.
        await m.perle_wurf("k", "anna", perle_id)
        assert stand["haeufchen"]["anna"] == []
        wo = next(p for p in ("ben", "cleo") if stand["haeufchen"].get(p))
        assert stand["haeufchen"][wo][0]["von"] == "anna"
        assert anna.letzte_pets()[0]["perle"] == "sucht"
        # Er läuft raus und sucht Tablet für Tablet, bis er dort ist, wo sie liegt.
        besucht = []
        wirt = "anna"
        for _ in range(3):
            await m.raus("k", wirt, "drache", "rechts")
            await asyncio.sleep(0.01)
            wirt = next(n for n, s in (("anna", anna), ("ben", ben), ("cleo", cleo)) if s.letzte_pets())
            besucht.append(wirt)
            if wirt == wo:
                break
        assert wirt == wo and len(set(besucht)) == len(besucht) and "anna" not in besucht
        sock = {"ben": ben, "cleo": cleo}[wo]
        assert sock.letzte_pets()[0]["perle"] == "gefunden"
        # Aufheben: Perle weg vom Schirm, er trägt sie und geht direkt zu Anna.
        await m.perle_gefunden("k", wo, "drache", perle_id)
        assert stand["haeufchen"][wo] == [] and sock.letzte_pets()[0]["perle"] == "bringt"
        await m.raus("k", wo, "drache", "links")
        await asyncio.sleep(0.01)
        assert anna.letzte_pets()[0]["perle"] == "zurueck"
        # Bei Anna legt er sie ab — jetzt ist sie wieder zum Spielen da.
        await m.perle("k", "anna", "drache", 0.4)
        assert anna.letzte_pets()[0]["perle"] == "spiel" and stand["haeufchen"]["anna"][0]["von"] is None
        # Wer die Perle nur weiterwirft, bleibt nicht der, dem sie gebracht wird.
        pid2 = stand["haeufchen"]["anna"][0]["id"]
        await m.perle_wurf("k", "anna", pid2)
        wo2 = next(p for p in ("ben", "cleo") if stand["haeufchen"].get(p))
        await m.perle_wurf("k", wo2, pid2)
        liegt = next(h for liste in stand["haeufchen"].values() for h in liste if h["art"] == "perle")
        assert liegt["von"] == "anna"
        m._takt.cancel()

    laufen(ablauf())


def test_drachenperle_einstecken_tablet_aus_und_verwaist(welt, monkeypatch):
    """Einstecken gilt sofort (sonst sucht er auf dem nächsten Tablet); liegt die
    Perle auf einem Tablet, das ausgeht, kullert sie weiter; ohne Drachen
    verschwindet sie."""
    m, stand = welt
    stand["pets"][0].update({"stufe": "ehrwuerdig", "kann": ["klettern", "perle"]})

    async def haeufchen_lesen(cid, pid, hid):
        return next(({"id": h["id"], "art": h["art"]} for h in stand["haeufchen"].get(pid, []) if h["id"] == hid), None)

    monkeypatch.setattr(motor_modul.repository, "haeufchen_lesen", haeufchen_lesen)

    def perlen_bei():
        return sorted(pid for pid, liste in stand["haeufchen"].items() for h in liste if h["art"] == "perle")

    async def ablauf():
        anna, ben, cleo = Socket(), Socket(), Socket()
        for name, s in (("anna", anna), ("ben", ben), ("cleo", cleo)):
            await m.anmelden("k", name, s)
        await m.perle("k", "anna", "drache", 0.5)
        pid = stand["haeufchen"]["anna"][0]["id"]
        # Ben kann sie nicht wegtippen — nur der Drache steckt sie ein, wo er ist.
        stand["haeufchen"].setdefault("ben", [])
        await m.wegmachen("k", "ben", pid)
        assert perlen_bei() == ["anna"]
        await m.wegmachen("k", "anna", pid)
        assert perlen_bei() == [] and anna.letzte_pets()[0]["perle"] is None
        # Danach wandert er normal weiter, nicht suchend.
        await m.raus("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        wirt = next(n for n, s in (("ben", ben), ("cleo", cleo)) if s.letzte_pets())
        assert {"ben": ben, "cleo": cleo}[wirt].letzte_pets()[0]["perle"] is None

        # Perle liegt bei Ben, Ben macht sein Tablet aus: sie kullert zu jemandem, der da ist.
        await m.perle("k", wirt, "drache", 0.5)
        pid = stand["haeufchen"][wirt][0]["id"]
        await m.perle_wurf("k", wirt, pid)
        liegt = perlen_bei()[0]
        assert liegt != wirt
        await m.abmelden("k", liegt, {"anna": anna, "ben": ben, "cleo": cleo}[liegt])
        assert perlen_bei() and perlen_bei()[0] != liegt
        h = next(h for liste in stand["haeufchen"].values() for h in liste if h["art"] == "perle")
        assert h["von"] == wirt  # zurückgebracht wird sie weiter dem Werfer

        # SL stellt den Drachen jünger: die Perle verschwindet.
        stand["pets"][0].update({"stufe": "gross", "kann": ["klettern"]})
        await m.abgleich("k")
        assert perlen_bei() == []
        # Perle eines Drachen, den es nicht mehr gibt: weg.
        stand["haeufchen"]["anna"] = [{"id": "alt", "petId": "fort", "x": 0.5, "y": 1.0, "art": "perle", "von": None}]
        await m.abgleich("k")
        assert perlen_bei() == []
        m._takt.cancel()

    laufen(ablauf())


def test_sl_macht_alle_tablets_sauber_naepfe_bleiben(welt, monkeypatch):
    """Mark, 13.11.: SL-Knopf räumt alle Spuren weg; jedes Tablet bekommt sofort die neue Liste."""
    m, stand = welt
    stand["haeufchen"] = {
        "anna": [{"id": "h1", "petId": "drache", "x": 0.2, "y": 1, "art": "brand"},
                 {"id": "n1", "petId": "", "x": 0.5, "y": 1, "art": "napf"}],
        "ben": [{"id": "h2", "petId": "drache", "x": 0.4, "y": 1, "art": "haeufchen"}],
    }

    async def spuren_alle_weg(cid):
        n = 0
        for pid, liste in stand["haeufchen"].items():
            n += sum(1 for h in liste if h["art"] != "napf")
            stand["haeufchen"][pid] = [h for h in liste if h["art"] == "napf"]
        return n

    monkeypatch.setattr(motor_modul.repository, "spuren_alle_weg", spuren_alle_weg)

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        assert await m.sauber("k") == 2
        letzte = lambda s: [n for n in s.post if n["typ"] == "haeufchen"][-1]["daten"]  # noqa: E731
        assert [h["id"] for h in letzte(anna)] == ["n1"]
        assert letzte(ben) == []
        m._takt.cancel()

    laufen(ablauf())


def test_ei_bleibt_beim_besitzer_und_schluepft_durch_tippen(welt, monkeypatch):
    m, stand = welt
    stand["pets"][0].update({"stufe": "ei", "kann": [], "risse": 0})

    async def ei_tippen(cid, pid):
        p = stand["pets"][0]
        p["tipps"] = p.get("tipps", 0) + 1
        if p["tipps"] >= 2:
            p.update({"stufe": "baby", "kann": [], "risse": 0})
            return True
        p["risse"] = 2
        return False

    monkeypatch.setattr(motor_modul.repository, "ei_tippen", ei_tippen)

    async def ablauf():
        anna, ben = Socket(), Socket()
        await m.anmelden("k", "anna", anna)
        await m.anmelden("k", "ben", ben)
        assert anna.letzte_pets()[0]["stufe"] == "ei"
        # Ein Ei wandert nicht: auch nach „raus“ landet es wieder bei Anna.
        await m.raus("k", "anna", "drache", "rechts")
        await asyncio.sleep(0.01)
        assert ben.letzte_pets() == []
        assert [p["id"] for p in anna.letzte_pets()] == ["drache"]
        # Ben kann nicht aus der Ferne tippen.
        await m.tippen("k", "ben", "drache")
        assert stand["pets"][0].get("tipps") is None
        await m.tippen("k", "anna", "drache")
        assert anna.letzte_pets()[0]["risse"] == 2
        await m.tippen("k", "anna", "drache")
        assert anna.letzte_pets()[0]["stufe"] == "baby"
        m._takt.cancel()

    laufen(ablauf())


def test_napf_nur_vom_drachen_leer_gefressen_heilt_und_macht_zutraulich(welt, monkeypatch):
    """Mark, 12.11.: Napf bleibt, bis der Drache ihn frisst; heilt 3 Schlag, +5 Zutraulichkeit."""
    m, stand = welt
    log = []

    async def haeufchen_lesen(cid, pid, hid):
        return next(({"id": h["id"], "art": h["art"]} for h in stand["haeufchen"].get(pid, []) if h["id"] == hid), None)

    async def critter_heilen(cid, critter_id, schlag):
        log.append(("heilen", critter_id, schlag))

    async def zutraulich(cid, pid, pet_id, plus, abklingen_s=0.0):
        log.append(("zutraulich", pid, pet_id, plus, abklingen_s))
        return plus

    repo = motor_modul.repository
    monkeypatch.setattr(repo, "haeufchen_lesen", haeufchen_lesen)
    monkeypatch.setattr(repo, "critter_heilen", critter_heilen)
    monkeypatch.setattr(repo, "zutraulichkeit_erhoehen", zutraulich)

    async def ablauf():
        anna = Socket()
        await m.anmelden("k", "anna", anna)
        await m.napf_hinstellen("k", "anna")
        napf = [h for h in stand["haeufchen"]["anna"] if h["art"] == "napf"]
        assert len(napf) == 1 and napf[0]["y"] == 1.0
        # Antippen (ohne Pet) räumt ihn nicht weg.
        await m.wegmachen("k", "anna", napf[0]["id"])
        assert stand["haeufchen"]["anna"]
        # Der Drache frisst ihn leer.
        await m.wegmachen("k", "anna", napf[0]["id"], "drache")
        assert not stand["haeufchen"]["anna"]
        assert ("heilen", "drache", 3) in log
        assert ("zutraulich", "anna", "drache", 5, 0.0) in log
        await m.streicheln("k", "anna", "drache")
        assert ("zutraulich", "anna", "drache", 1, 300) in log
        # Wer das Pet nicht auf dem Schirm hat, streichelt nicht.
        vorher = len(log)
        await m.streicheln("k", "ben", "drache")
        assert len(log) == vorher
        m._takt.cancel()

    laufen(ablauf())
