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

    repo = motor_modul.repository
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
