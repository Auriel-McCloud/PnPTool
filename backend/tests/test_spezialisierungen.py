"""Fertigkeiten-Spezialisierung: Vergabe-Schwellen, Auto-Grant-Hook, CRUD.

Echte Neo4j-Integration wie test_achievements.py/test_hintergruende.py:
reine asyncio.run()-Aufrufe gegen Repository-Funktionen, keine HTTP-Schicht
(dieses Projekt nutzt bisher kein FastAPI-TestClient, siehe
test_tutorial_shop_rassen_features.py).
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.spezialisierungen import repository as spezialisierungen_repository
from app.traits import repository as traits_repository


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-spezialisierung-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Spezialisierung-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _person_anlegen(cid: str, name: str, **extra) -> str:
    pid = str(uuid.uuid4())
    driver = get_driver()
    felder = {"personType": "PC", "sichtbarkeit": "GM", "sichtbarFuer": [], **extra}
    props = ", ".join(f"{k}: ${k}" for k in felder)
    async with driver.session() as session:
        await session.run(
            f"""
            MATCH (c:Campaign {{id: $cid}})
            CREATE (p:Person {{id: $pid, campaignId: $cid, name: $name, {props}}})
            CREATE (c)-[:HAT_ENTITAET]->(p)
            """,
            cid=cid, pid=pid, name=name, **felder,
        )
    return pid


async def _trait_def_id(name: str, kategorie: str = "Fertigkeit") -> str:
    """Reale TraitDef-ID aus dem beim Serverstart geseedeten Katalog
    (seed_traits läuft beim App-Import, siehe app/main.py::lifespan —
    im Testlauf wird dasselbe Neo4j benutzt, der Katalog existiert also)."""
    return f"neotopia:{kategorie}:{name}"


# ===========================================================================
# Reine Funktion: Schwellen-Logik
# ===========================================================================


class TestAutomatischeSlotAnzahl:
    def test_kein_slot_unter_vier(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(0, 3) == 0

    def test_ein_slot_bei_erreichen_von_vier(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(3, 4) == 1

    def test_kein_slot_von_vier_auf_fuenf(self):
        """Nicht kumulativ dazwischen — 5 ist keine eigene Schwelle."""
        assert spezialisierungen_repository.automatische_slot_anzahl(4, 5) == 0

    def test_ein_weiterer_slot_bei_erreichen_von_sechs(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(5, 6) == 1

    def test_beide_slots_bei_sprung_von_drei_direkt_auf_sechs(self):
        """GM setzt den Wert von Hand / Charakter startet schon auf 6 —
        beide überschrittenen Schwellen (4 und 6) zählen auf einen Schlag."""
        assert spezialisierungen_repository.automatische_slot_anzahl(3, 6) == 2

    def test_kein_slot_beim_sinken(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(6, 3) == 0

    def test_kein_slot_bei_unveraendertem_wert(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(4, 4) == 0

    def test_null_crossing_oberhalb_von_sechs_bleibt_zwei(self):
        """Auch ein Sprung weit über 6 hinaus (z.B. 0 -> 10 bei Hexkraft-
        artigen Werten) vergibt nur die zwei definierten Slots, keinen dritten."""
        assert spezialisierungen_repository.automatische_slot_anzahl(0, 10) == 2


# ===========================================================================
# Auto-Grant-Hook: set_rating / steigere / set_ratings_bulk
# ===========================================================================


def test_set_rating_vergibt_slot_bei_schwelle_vier():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")

            await traits_repository.set_rating(cid, pid, trait_id, 3, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []

            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            assert len(slots) == 1
            assert slots[0]["quelle"] == "automatisch"
            assert slots[0]["text"] == ""
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_rating_vergibt_zweiten_slot_bei_schwelle_sechs_nicht_bei_fuenf():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")

            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            await traits_repository.set_rating(cid, pid, trait_id, 5, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1

            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 2
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_steigere_vergibt_slot_genau_wie_set_rating():
    """EP-Steigerungs-Pfad (traits/routes.py::steigere_wert) — eigene
    Repository-Funktion, muss denselben Hook feuern."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")

            await traits_repository.steigere(cid, pid, trait_id, 1)
            await traits_repository.steigere(cid, pid, trait_id, 2)
            await traits_repository.steigere(cid, pid, trait_id, 3)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []

            await traits_repository.steigere(cid, pid, trait_id, 4)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_ratings_bulk_vergibt_slot_bei_charaktererstellung_direkt_auf_vier():
    """Charaktererstellung: ein Fertigkeitspaket kann direkt eine 4 anlegen
    (kein vorheriger HAS_TRAIT-Knoten existiert) — alt muss dann als 0
    gelten, nicht als Fehler."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Frisch Erstellt")
            await traits_repository.set_ratings_bulk(cid, pid, {"Schusswaffen": 4, "Fahren": 2})
            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            trait_id = await _trait_def_id("Schusswaffen")
            assert len(slots) == 1
            assert slots[0]["traitDefId"] == trait_id
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_ratings_bulk_resubmission_vergibt_nicht_doppelt():
    """SL reicht die Erstellung erneut ein (Korrektur) — derselbe Endwert
    darf keinen zweiten Slot auslösen."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Frisch Erstellt")
            await traits_repository.set_ratings_bulk(cid, pid, {"Schusswaffen": 4})
            await traits_repository.set_ratings_bulk(cid, pid, {"Schusswaffen": 4})
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_sinken_entfernt_vergebenen_slot_nicht():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            await traits_repository.set_rating(cid, pid, trait_id, 2, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_attribut_bekommt_niemals_eine_spezialisierung():
    """Attribute sind explizit ausgeschlossen (Marks Vorgabe) — auch beim
    Überschreiten von 4/6 passiert hier nichts."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Körperkraft", "AttributKörperlich")
            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_sphaere_bekommt_niemals_eine_spezialisierung_in_diesem_branch():
    """Sphären-Spezialisierung ist ein separates, späteres Feature (eigene
    Schwellen 2/4/5) — in diesem Branch bewusst nicht gebaut."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Magierin")
            trait_id = await _trait_def_id("Kräfte", "Sphäre")
            await traits_repository.set_rating(cid, pid, trait_id, 5, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_neuroweaving_wert_selbst_bekommt_keine_spezialisierung():
    """NeuroWeavingWert (der Grundwert, mechanisch wie Hexkraft behandelt)
    ist kein Slot-Kandidat — nur die sechs NeuroWeaving-FERTIGKEITEN
    darunter sind es (siehe nächster Test)."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Weaver")
            trait_id = await _trait_def_id("NeuroWeaving", "NeuroWeavingWert")
            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_neuroweaving_fertigkeit_bekommt_spezialisierung():
    """Die NeuroWeaving-Fertigkeiten (z.B. Brute Force) zählen laut
    erstellung.py mechanisch als Fertigkeit — Slot-Vergabe greift genauso."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Weaver")
            trait_id = await _trait_def_id("Brute Force", "NeuroWeaving")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            assert len(slots) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


# ===========================================================================
# CRUD: benennen (Zweiphasen-Namensrecht) und gekaufte Slots
# ===========================================================================


def test_gekaufter_slot_kommt_zusaetzlich_zum_automatischen_und_traegt_eigene_quelle():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            await spezialisierungen_repository.gekauft_anlegen(cid, pid, trait_id)

            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            assert len(slots) == 2
            quellen = sorted(s["quelle"] for s in slots)
            assert quellen == ["automatisch", "gekauft"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_benennen_setzt_text_und_benanntvonspieler_flag():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            [slot] = await spezialisierungen_repository.fuer_person(cid, pid)

            aktualisiert = await spezialisierungen_repository.benennen(
                cid, pid, slot["id"], "Pistolen", als_spieler=True
            )
            assert aktualisiert is not None
            assert aktualisiert["text"] == "Pistolen"
            assert aktualisiert["benanntVonSpieler"] is True
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_benennen_unbekannter_slot_gibt_none():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            ergebnis = await spezialisierungen_repository.benennen(
                cid, pid, "nicht-vorhanden", "x", als_spieler=True
            )
            assert ergebnis is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_vorschlaege_landen_im_traitkatalog():
    """TRAIT_VORSCHLAEGE (seed.py) muss über list_catalog()/TraitDefResponse
    beim Client ankommen — ohne das zeigt das Popup nie Vorschlag-Chips."""

    async def lauf():
        katalog = await traits_repository.list_catalog("neotopia")
        schusswaffen = next(t for t in katalog if t["name"] == "Schusswaffen")
        assert "Pistolen" in schusswaffen["vorschlaege"]
        # Eine Fertigkeit ohne eigene Vorschläge liefert eine leere Liste,
        # nicht None/fehlendes Feld — sonst crasht die Pydantic-Validierung.
        unbekannt = next(t for t in katalog if t["name"] == "Diebeshandwerk")
        assert unbekannt["vorschlaege"] == []
    _run(lauf())
