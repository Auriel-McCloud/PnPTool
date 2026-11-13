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

    repo = motor_modul.repository
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
    assert set(lg.faehigkeiten("drache", "ehrwuerdig", 60)) == set(lg.ALLE_FAEHIGKEITEN)
    # Bärbel wächst nicht.
    assert lg.stufe("baerbel", "ei", 0, None) == ("jung", None)
    assert lg.risse(0, 8) == 0 and lg.risse(4, 8) == 2 and lg.risse(8, 8) == 4


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
