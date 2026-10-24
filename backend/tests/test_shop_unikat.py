"""Ein Einzelstück im Regal gibt es nur einmal — auch ohne Personen-Besitzer."""

import asyncio
import uuid

from app.db.neo4j_driver import close_driver, get_driver
from app.haendler.uebergabe import UnikatEinhangFehler, stueck_uebergeben, unikat_anlegen, unikat_einhaengen
from app.items.repository import get_gegenstand, get_owner_id, setze_vorlagen_art


def _run(coro):
    async def wrapped():
        try:
            return await coro
        finally:
            await close_driver()

    return asyncio.run(wrapped())


async def _kampagne() -> str:
    cid = f"test-shop-unikat-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Unikat-Test'})", cid=cid)
    return cid


async def _weg(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _regal(cid: str) -> tuple[str, str, str]:
    """Laden, Käufer, besitzerloses Unikat an VERKAUFT."""
    shop = str(uuid.uuid4())
    kaeufer = str(uuid.uuid4())
    stueck = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (o:Ort {
                id: $shop, campaignId: $cid, name: 'Nachtmarkt',
                istShop: true, sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (k:Person {
                id: $kaeufer, campaignId: $cid, name: 'Käufer',
                personType: 'PC', kapital: 1000, sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (g:Gegenstand {
                id: $stueck, campaignId: $cid, name: 'Das eine Messer',
                typ: 'Waffe', preis: 80, istVorlage: false, einzigartig: true, bildUrl: ''
            })
            CREATE (o)-[:VERKAUFT {preis: 80}]->(g)
            """,
            cid=cid,
            shop=shop,
            kaeufer=kaeufer,
            stueck=stueck,
        )
    return shop, kaeufer, stueck


def test_besitzerloses_unikat_wechselt_den_besitzer_und_verlaesst_das_regal():
    async def szenario():
        cid = await _kampagne()
        try:
            shop, kaeufer, stueck = await _regal(cid)
            gekauft = await stueck_uebergeben(cid, shop, stueck, kaeufer)
            assert gekauft is not None
            assert gekauft["id"] == stueck
            assert await get_owner_id(cid, stueck) == kaeufer
            danach = await get_gegenstand(cid, stueck)
            assert danach is not None
            assert danach["istVorlage"] is False
            driver = get_driver()
            async with driver.session() as session:
                treffer = await session.run(
                    """
                    MATCH (:Ort {id: $shop})-[:VERKAUFT]->(:Gegenstand {id: $stueck})
                    RETURN count(*) AS n
                    """,
                    shop=shop,
                    stueck=stueck,
                )
                record = await treffer.single()
            assert record["n"] == 0
        finally:
            await _weg(cid)

    _run(szenario())


def test_unikat_anlegen_legt_ein_besitzerloses_einzelstueck_ins_regal():
    async def szenario():
        cid = await _kampagne()
        shop = str(uuid.uuid4())
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (:Ort {
                        id: $shop, campaignId: $cid, name: 'Tresen',
                        istShop: true, sichtbarkeit: 'ALLE', sichtbarFuer: []
                    })
                    """,
                    cid=cid,
                    shop=shop,
                )
            angelegt = await unikat_anlegen(cid, shop, "Reliquie", "Sonstiges", 400, "Liegt nur einmal hier.")
            assert angelegt is not None
            assert angelegt["istVorlage"] is False
            assert angelegt["einzigartig"] is True
            assert await get_owner_id(cid, angelegt["id"]) is None
            async with driver.session() as session:
                treffer = await session.run(
                    """
                    MATCH (:Ort {id: $shop})-[r:VERKAUFT]->(g:Gegenstand {id: $id})
                    RETURN r.preis AS preis, g.istVorlage AS istVorlage
                    """,
                    shop=shop,
                    id=angelegt["id"],
                )
                record = await treffer.single()
            assert record is not None
            assert record["preis"] == 400
            assert record["istVorlage"] is False
        finally:
            await _weg(cid)

    _run(szenario())


def test_spielerbesitz_laesst_sich_nicht_ins_regal_haengen():
    async def szenario():
        cid = await _kampagne()
        shop = str(uuid.uuid4())
        spieler = str(uuid.uuid4())
        stueck = str(uuid.uuid4())
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (:Ort {id: $shop, campaignId: $cid, name: 'Tresen', istShop: true, sichtbarkeit: 'ALLE'})
                    CREATE (p:Person {id: $spieler, campaignId: $cid, name: 'Aki', personType: 'PC', sichtbarkeit: 'ALLE'})
                    CREATE (g:Gegenstand {id: $stueck, campaignId: $cid, name: 'Eigenes Messer', typ: 'Waffe', preis: 10, istVorlage: false, einzigartig: true})
                    CREATE (p)-[:BESITZT]->(g)
                    """,
                    cid=cid, shop=shop, spieler=spieler, stueck=stueck,
                )
            try:
                await unikat_einhaengen(cid, shop, stueck, None)
                raise AssertionError("Spielerbesitz hätte abgelehnt werden müssen")
            except UnikatEinhangFehler as fehler:
                assert fehler.grund == "spieler"
        finally:
            await _weg(cid)

    _run(szenario())


def test_einzigartige_vorlage_wird_beim_einhaengen_zum_einzelstueck():
    async def szenario():
        cid = await _kampagne()
        shop = str(uuid.uuid4())
        stueck = str(uuid.uuid4())
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (:Ort {id: $shop, campaignId: $cid, name: 'Tresen', istShop: true, sichtbarkeit: 'ALLE'})
                    CREATE (:Gegenstand {
                        id: $stueck, campaignId: $cid, name: 'Amulett',
                        typ: 'Sonstiges', preis: 50, istVorlage: true, einzigartig: true
                    })
                    """,
                    cid=cid, shop=shop, stueck=stueck,
                )
            await unikat_einhaengen(cid, shop, stueck, 90)
            danach = await get_gegenstand(cid, stueck)
            assert danach is not None
            assert danach["istVorlage"] is False
            assert danach["einzigartig"] is True
            assert await get_owner_id(cid, stueck) is None
            async with driver.session() as session:
                treffer = await session.run(
                    """
                    MATCH (:Ort {id: $shop})-[r:VERKAUFT]->(:Gegenstand {id: $stueck})
                    RETURN r.preis AS preis
                    """,
                    shop=shop, stueck=stueck,
                )
                record = await treffer.single()
            assert record["preis"] == 90
        finally:
            await _weg(cid)

    _run(szenario())


def test_kopierbare_vorlage_bleibt_vorlage_und_wird_nicht_als_unikat_eingehaengt():
    async def szenario():
        cid = await _kampagne()
        shop = str(uuid.uuid4())
        stueck = str(uuid.uuid4())
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (:Ort {id: $shop, campaignId: $cid, name: 'Tresen', istShop: true, sichtbarkeit: 'ALLE'})
                    CREATE (:Gegenstand {
                        id: $stueck, campaignId: $cid, name: 'Serienmesser',
                        typ: 'Waffe', preis: 20, istVorlage: true, einzigartig: false, storyRelevant: false
                    })
                    """,
                    cid=cid, shop=shop, stueck=stueck,
                )
            try:
                await unikat_einhaengen(cid, shop, stueck, None)
                raise AssertionError("Kopierbare Vorlage hätte abgelehnt werden müssen")
            except UnikatEinhangFehler as fehler:
                assert fehler.grund == "vorlage"
            danach = await get_gegenstand(cid, stueck)
            assert danach is not None and danach["istVorlage"] is True
        finally:
            await _weg(cid)

    _run(szenario())


def test_keine_vorlage_am_stueck_verkauft_den_knoten_selbst():
    async def szenario():
        cid = await _kampagne()
        shop = str(uuid.uuid4())
        kaeufer = str(uuid.uuid4())
        stueck = str(uuid.uuid4())
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (o:Ort {id: $shop, campaignId: $cid, name: 'Tresen', istShop: true, sichtbarkeit: 'ALLE'})
                    CREATE (:Person {id: $kaeufer, campaignId: $cid, name: 'Käufer', personType: 'PC', kapital: 500, sichtbarkeit: 'ALLE'})
                    CREATE (g:Gegenstand {
                        id: $stueck, campaignId: $cid, name: 'Reliquie',
                        typ: 'Sonstiges', preis: 40, istVorlage: true, einzigartig: false
                    })
                    CREATE (o)-[:VERKAUFT {preis: 40}]->(g)
                    """,
                    cid=cid, shop=shop, kaeufer=kaeufer, stueck=stueck,
                )
            umgestellt = await setze_vorlagen_art(cid, stueck, True)
            assert umgestellt is not None
            assert umgestellt["istVorlage"] is False
            gekauft = await stueck_uebergeben(cid, shop, stueck, kaeufer)
            assert gekauft is not None and gekauft["id"] == stueck
            assert await get_owner_id(cid, stueck) == kaeufer
        finally:
            await _weg(cid)

    _run(szenario())
