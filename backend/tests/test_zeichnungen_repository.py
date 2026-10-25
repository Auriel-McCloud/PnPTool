"""Whiteboard: Repository-CRUD + Papierkorb gegen echtes Neo4j.

Echte-Neo4j-Integrationstests nach demselben Muster wie test_flora_fauna.py.
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.zeichnungen import repository


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-zeichnungen-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Zeichnungen-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


def test_anlegen_setzt_defaults_und_leere_pfade():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            board = await repository.erstellen(cid, {"name": "Taktik-Skizze"})
            assert board["name"] == "Taktik-Skizze"
            assert board["pfade"] == []
            assert board["bildUrl"] == ""
            assert board["spielerDuerfenZeichnen"] is False
            assert board["sichtbarkeit"] == "GM"
            assert board["sichtbarFuer"] == []
            assert board["geloescht"] is False
            assert board["erstelltAm"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_anlegen_mit_allen_feldern():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            board = await repository.erstellen(
                cid,
                {
                    "name": "Gemeinsame Karte",
                    "bildUrl": "/uploads/karte.png",
                    "spielerDuerfenZeichnen": True,
                    "sichtbarkeit": "ALLE",
                    "sichtbarFuer": [],
                },
            )
            assert board["bildUrl"] == "/uploads/karte.png"
            assert board["spielerDuerfenZeichnen"] is True
            assert board["sichtbarkeit"] == "ALLE"
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_liste_blendet_geloeschte_aus():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            sichtbar = await repository.erstellen(cid, {"name": "Board A"})
            geloescht = await repository.erstellen(cid, {"name": "Board B"})
            await repository.setze_geloescht(cid, geloescht["id"], True)

            liste = await repository.liste(cid)
            assert [b["id"] for b in liste] == [sichtbar["id"]]

            papierkorb = await repository.liste_papierkorb(cid)
            assert [b["id"] for b in papierkorb] == [geloescht["id"]]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_holen_findet_geloeschtes_nur_wenn_explizit_erlaubt():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            board = await repository.erstellen(cid, {"name": "Board"})
            await repository.setze_geloescht(cid, board["id"], True)

            assert await repository.holen(cid, board["id"]) is None
            voll = await repository.holen(cid, board["id"], nur_nicht_geloescht=False)
            assert voll is not None and voll["geloescht"] is True
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_wiederherstellen_aus_dem_papierkorb():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            board = await repository.erstellen(cid, {"name": "Board"})
            await repository.setze_geloescht(cid, board["id"], True)
            wiederhergestellt = await repository.setze_geloescht(cid, board["id"], False)
            assert wiederhergestellt["geloescht"] is False
            assert [b["id"] for b in await repository.liste(cid)] == [board["id"]]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_aktualisieren_aendert_nur_gesetzte_felder():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            board = await repository.erstellen(cid, {"name": "Alter Name", "spielerDuerfenZeichnen": False})
            aktualisiert = await repository.aktualisieren(
                cid, board["id"], {"name": "Neuer Name", "spielerDuerfenZeichnen": None}
            )
            assert aktualisiert["name"] == "Neuer Name"
            # spielerDuerfenZeichnen war None im Update-Body -> unangetastet.
            assert aktualisiert["spielerDuerfenZeichnen"] is False
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_pfade_speichern_ersetzt_den_gesamten_stand():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            board = await repository.erstellen(cid, {"name": "Board"})
            erster_stand = [{"paths": [{"x": 1, "y": 2}], "strokeColor": "#000"}]
            nach_erstem = await repository.pfade_speichern(cid, board["id"], erster_stand)
            assert nach_erstem["pfade"] == erster_stand

            zweiter_stand = erster_stand + [{"paths": [{"x": 9, "y": 9}], "strokeColor": "#fff"}]
            nach_zweitem = await repository.pfade_speichern(cid, board["id"], zweiter_stand)
            assert nach_zweitem["pfade"] == zweiter_stand

            geleert = await repository.pfade_speichern(cid, board["id"], [])
            assert geleert["pfade"] == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_mehrere_boards_pro_kampagne_unabhaengig():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            a = await repository.erstellen(cid, {"name": "Board A"})
            b = await repository.erstellen(cid, {"name": "Board B"})
            await repository.pfade_speichern(cid, a["id"], [{"strokeColor": "#111"}])

            frisch_a = await repository.holen(cid, a["id"])
            frisch_b = await repository.holen(cid, b["id"])
            assert frisch_a["pfade"] == [{"strokeColor": "#111"}]
            assert frisch_b["pfade"] == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())
