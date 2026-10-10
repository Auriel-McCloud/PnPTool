"""Achievements — Repository + Trigger (10.10.2026).

Echte Neo4j-Integration wie test_tutorial_shop_rassen_features.py: reine
asyncio.run()-Aufrufe gegen Repository-Funktionen, keine HTTP-Schicht.
"""

import asyncio
import uuid

from app.achievements import belohnung, repository, trigger
from app.db.neo4j_driver import get_driver


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-achievements-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Achievement-Test'})", cid=cid)
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


def test_achievement_crud():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            achievement = await repository.anlegen(cid, {
                "name": "Hello World", "beschreibung": "Erster Charakter",
                "icon": "🌍", "art": "AUTO", "ausloeseArt": "CHARAKTER_ERSTELLT",
                "einzigartig": False, "belohnungsArt": "KEINE",
                "belohnungsMenge": 0, "belohnungsHintergrund": None, "zielGegenstandId": None,
            })
            assert achievement["name"] == "Hello World"
            assert achievement["ausloeseArt"] == "CHARAKTER_ERSTELLT"

            geholt = await repository.hole(cid, achievement["id"])
            assert geholt is not None
            assert geholt["icon"] == "🌍"

            geaendert = await repository.aendern(cid, achievement["id"], {"belohnungsArt": "EP", "belohnungsMenge": 10})
            assert geaendert is not None
            assert geaendert["belohnungsArt"] == "EP"
            assert geaendert["belohnungsMenge"] == 10
            # Unverändert gelassene Felder bleiben stehen.
            assert geaendert["name"] == "Hello World"

            assert await repository.loeschen(cid, achievement["id"]) is True
            assert await repository.hole(cid, achievement["id"]) is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_achievement_mit_verleihung_laesst_sich_nicht_loeschen():
    """Ein bereits vergebenes Achievement bleibt erhalten (Papierkorb-Analogie
    — Verleihungen dürfen keine Leichen zurücklassen)."""
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            achievement = await repository.anlegen(cid, {
                "name": "Mörder", "art": "MANUELL", "einzigartig": False,
                "belohnungsArt": "KEINE", "belohnungsMenge": 0,
            })
            await repository.verleihe(cid, achievement_id=achievement["id"], person_id=pid)

            assert await repository.loeschen(cid, achievement["id"]) is False
            assert await repository.hole(cid, achievement["id"]) is not None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_einzigartig_ablösen_bei_rekord():
    """Ein Rekord-Achievement (einzigartig=true) wandert: die alte Verleihung
    wird abgelöst, bleibt aber als Historie stehen (kein Hard-Delete)."""
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            fred = await _person_anlegen(cid, "Fred")
            jin = await _person_anlegen(cid, "Jin")
            achievement = await repository.anlegen(cid, {
                "name": "Meister Schaden verteilt", "art": "AUTO",
                "ausloeseArt": "MEISTE_SCHADEN_VERTEILT", "einzigartig": True,
                "belohnungsArt": "KEINE", "belohnungsMenge": 0,
            })

            v1 = await repository.verleihe(cid, achievement_id=achievement["id"], person_id=fred)
            assert v1 is not None
            assert await repository.aktueller_traeger(cid, achievement["id"]) == fred

            await repository.loese_ab(cid, achievement["id"], fred)
            v2 = await repository.verleihe(cid, achievement_id=achievement["id"], person_id=jin)
            assert v2 is not None
            assert await repository.aktueller_traeger(cid, achievement["id"]) == jin

            # Freds alte Verleihung bleibt stehen, nur abgelöst.
            alle = await repository.alle_verleihungen(cid)
            fred_eintrag = next(v for v in alle if v["personId"] == fred)
            assert fred_eintrag["abgeloest"] is True
            jin_eintrag = next(v for v in alle if v["personId"] == jin)
            assert jin_eintrag["abgeloest"] is False
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_verleihung_papierkorb_statt_loeschen():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Viktor")
            achievement = await repository.anlegen(cid, {
                "name": "Testerfolg", "art": "MANUELL", "einzigartig": False,
                "belohnungsArt": "KEINE", "belohnungsMenge": 0,
            })
            verleihung = await repository.verleihe(cid, achievement_id=achievement["id"], person_id=pid)
            assert len(await repository.verleihungen_fuer_person(cid, pid)) == 1

            assert await repository.setze_geloescht(cid, verleihung["id"], True) is True
            assert len(await repository.verleihungen_fuer_person(cid, pid)) == 0
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_trigger_charakter_erstellt_findet_pcs():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Erika", erstellungAbgeschlossen=True)
            achievement = await repository.anlegen(cid, {
                "name": "Hello World", "art": "AUTO", "ausloeseArt": "CHARAKTER_ERSTELLT",
                "einzigartig": False, "belohnungsArt": "KEINE", "belohnungsMenge": 0,
            })

            vorschlaege = await trigger.vorschlaege(cid)
            treffer = [v for v in vorschlaege if v["achievementId"] == achievement["id"]]
            assert len(treffer) == 1
            assert treffer[0]["personId"] == pid

            # Nach Vergabe erscheint die Person nicht mehr als Vorschlag.
            await repository.verleihe(cid, achievement_id=achievement["id"], person_id=pid)
            vorschlaege_danach = await trigger.vorschlaege(cid)
            treffer_danach = [v for v in vorschlaege_danach if v["achievementId"] == achievement["id"]]
            assert len(treffer_danach) == 0
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_trigger_erster_critter():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            halter = await _person_anlegen(cid, "Mio")
            critter_id = str(uuid.uuid4())
            driver = get_driver()
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Campaign {id: $cid})
                    MATCH (halter:Person {id: $halter})
                    CREATE (critter:Person {
                        id: $critter_id, campaignId: $cid, name: 'Mauzi', personType: 'NPC',
                        istCritter: true, sichtbarkeit: 'GM', sichtbarFuer: []
                    })
                    CREATE (c)-[:HAT_ENTITAET]->(critter)
                    CREATE (critter)-[:BEGLEITET]->(halter)
                    """,
                    cid=cid, halter=halter, critter_id=critter_id,
                )

            kandidaten = await repository.erster_critter_traeger(cid)
            assert any(k["personId"] == halter for k in kandidaten)
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_belohnung_ep_erhoeht_erfahrung():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Nox", erfahrung=5, erfahrungAusgegeben=0)
            achievement = {"belohnungsArt": "EP", "belohnungsMenge": 15, "name": "Belohnungstest"}
            await belohnung.einloesen(cid, "neotopia", person_id=pid, achievement=achievement)

            from app.entities.repository import PERSON_FIELDS, get_node

            person = await get_node("Person", PERSON_FIELDS, cid, pid)
            assert person is not None
            assert person["erfahrung"] == 20
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_belohnung_keine_tut_nichts():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Stille", erfahrung=5)
            achievement = {"belohnungsArt": "KEINE", "belohnungsMenge": 0, "name": "Kosmetisch"}
            await belohnung.einloesen(cid, "neotopia", person_id=pid, achievement=achievement)

            from app.entities.repository import PERSON_FIELDS, get_node

            person = await get_node("Person", PERSON_FIELDS, cid, pid)
            assert person is not None
            assert person["erfahrung"] == 5
        finally:
            await _aufraeumen(cid)

    _run(lauf())
