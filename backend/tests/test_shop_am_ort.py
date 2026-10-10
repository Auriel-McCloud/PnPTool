"""Shop hängt am Ort: Ware und Spezialisierung am Laden, Person nur Gesicht."""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.haendler import repository


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-shop-ort-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "CREATE (c:Campaign {id: $cid, name: 'Shop-Ort-Test'})",
            cid=cid,
        )
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "MATCH (n {campaignId: $cid}) DETACH DELETE n",
            cid=cid,
        )
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _zwei_haendler_ein_ort(cid: str) -> tuple[str, str, str, str]:
    """Ort + zwei Händler + eine Ware, noch im ALTEN Modell (VERKAUFT an Person)."""
    ort_id = str(uuid.uuid4())
    h1 = str(uuid.uuid4())
    h2 = str(uuid.uuid4())
    ware = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (c:Campaign {id: $cid})
            CREATE (o:Ort {
                id: $ort_id, campaignId: $cid, name: 'Nachtmarkt',
                description: 'Stände unter Neon', bildUrl: '/markt.jpg',
                sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (h1:Person {
                id: $h1, campaignId: $cid, name: 'Mira',
                personType: 'NPC', istHaendler: true,
                spezialisierung: ['Waffe'], vertriebsart: 'PHYSISCH',
                shopHintergrundUrl: '/alt.jpg', bildUrl: '/mira.jpg',
                description: 'soll nicht die Shop-Beschreibung sein',
                sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (h2:Person {
                id: $h2, campaignId: $cid, name: 'Kai',
                personType: 'NPC', istHaendler: true,
                spezialisierung: ['Waffe'], vertriebsart: 'PHYSISCH',
                bildUrl: '/kai.jpg', sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (g:Gegenstand {
                id: $ware, campaignId: $cid, name: 'Klappmesser',
                typ: 'Waffe', preis: 50, istVorlage: true, bildUrl: ''
            })
            CREATE (c)-[:HAT_ENTITAET]->(o)
            CREATE (c)-[:HAT_ENTITAET]->(h1)
            CREATE (c)-[:HAT_ENTITAET]->(h2)
            CREATE (c)-[:HAT_ENTITAET]->(g)
            CREATE (h1)-[:BEFINDET_SICH_AN]->(o)
            CREATE (h2)-[:BEFINDET_SICH_AN]->(o)
            CREATE (h1)-[:VERKAUFT {preis: 40}]->(g)
            """,
            cid=cid,
            ort_id=ort_id,
            h1=h1,
            h2=h2,
            ware=ware,
        )
    return ort_id, h1, h2, ware


def test_migration_hebt_ware_und_felder_auf_den_ort():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort_id, h1, h2, ware = await _zwei_haendler_ein_ort(cid)
            await repository.shops_auf_orte_heben(cid)

            shops = await repository.liste(cid)
            assert len(shops) == 1
            shop = shops[0]
            assert shop["id"] == ort_id
            assert shop["name"] == "Nachtmarkt"
            assert shop["beschreibung"] == "Stände unter Neon"
            assert shop["spezialisierung"] == ["Waffe"]
            assert shop["vertriebsart"] == "PHYSISCH"
            namen = sorted(h["name"] for h in shop["haendler"])
            assert namen == ["Kai", "Mira"]

            sortiment = await repository.sortiment(cid, ort_id)
            ids = [e["gegenstandId"] for e in sortiment if not e["automatisch"]]
            assert ware in ids

            driver = get_driver()
            async with driver.session() as session:
                alt = await session.run(
                    """
                    MATCH (:Person {campaignId: $cid})-[r:VERKAUFT]->()
                    RETURN count(r) AS n
                    """,
                    cid=cid,
                )
                assert (await alt.single())["n"] == 0
                neu = await session.run(
                    """
                    MATCH (:Ort {id: $ort_id})-[r:VERKAUFT]->()
                    RETURN count(r) AS n
                    """,
                    ort_id=ort_id,
                )
                assert (await neu.single())["n"] == 1
                betreibt = await session.run(
                    """
                    MATCH (h:Person)-[:BETREIBT]->(:Ort {id: $ort_id})
                    RETURN count(h) AS n
                    """,
                    ort_id=ort_id,
                )
                assert (await betreibt.single())["n"] == 2
            assert h1 and h2
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_export_weissliste_kennt_betreibt():
    from app.campaigns.export_import import KNOWN_REL_TYPES

    assert "BETREIBT" in KNOWN_REL_TYPES


def test_haendler_ohne_ort_legt_keinen_laden_an():
    """Ein bloßes istHaendler ohne Ort ist ein Gesicht, kein Shop.

    Früher legte shops_auf_orte_heben dafür einen Laden aus dem NPC-Namen
    an. Mark (10.10.2026): Shops entstehen über Orte, nicht über NPCs.
    """
    from app.entities import repository as entities_repository
    from app.entities.repository import ORT_FIELDS

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            hid = str(uuid.uuid4())
            driver = get_driver()
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Campaign {id: $cid})
                    CREATE (h:Person {
                        id: $hid, campaignId: $cid, name: 'Chibi Testhändler',
                        personType: 'NPC', istHaendler: true,
                        sichtbarkeit: 'GM', sichtbarFuer: []
                    })
                    CREATE (c)-[:HAT_ENTITAET]->(h)
                    """,
                    cid=cid,
                    hid=hid,
                )

            await repository.shops_auf_orte_heben(cid)
            orte = await entities_repository.list_nodes("Ort", ORT_FIELDS, cid)
            assert orte == []
            assert await repository.liste(cid) == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_standort_entfernen_meldet_keinen_404():
    """Regression (05.10.2026): standort_setzen(ort_id=None) räumte die
    Kante serverseitig korrekt weg, gab aber in JEDEM Fall None zurück —
    die Route konnte "erfolgreich entbunden" nicht von "Händler nicht
    gefunden" unterscheiden und warf immer 404, obwohl die Aktion
    geklappt hatte (gefunden beim Test des "Entfernen"-Knopfs im neuen
    Ort-Laden-Fenster)."""
    from app.entities import repository as entities_repository
    from app.entities.repository import PERSON_FIELDS

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort_id, h1, h2, _ware = await _zwei_haendler_ein_ort(cid)
            await repository.shops_auf_orte_heben(cid)

            # Erfolgreiches Entbinden: Person existiert und ist Händler.
            ergebnis = await repository.standort_setzen(cid, h1, None)
            assert ergebnis is not False  # nicht "nicht gefunden"
            assert ergebnis is None  # kein Shop-Eintrag mehr für DIESEN Händler

            person = await entities_repository.get_node("Person", PERSON_FIELDS, cid, h1)
            assert person is not None  # Person existiert weiterhin

            # Echtes 404: Person existiert gar nicht.
            nicht_gefunden = await repository.standort_setzen(cid, str(uuid.uuid4()), None)
            assert nicht_gefunden is False
        finally:
            await _aufraeumen(cid)

    _run(lauf())
