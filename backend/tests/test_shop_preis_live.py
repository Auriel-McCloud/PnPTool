"""Shop-Preis folgt live dem Gegenstand, wenn die Kante keinen Sonderpreis trägt."""

import asyncio
import uuid

from app.db.neo4j_driver import close_driver, get_driver
from app.haendler import repository
from app.haendler.uebergabe import unikat_anlegen
from app.items.repository import update_gegenstand


def _run(coro):
    async def wrapped():
        try:
            return await coro
        finally:
            await close_driver()

    return asyncio.run(wrapped())


async def _kampagne() -> str:
    cid = f"test-shop-preis-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Preis-Live-Test'})", cid=cid)
    return cid


async def _weg(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _laden_mit_vorlage(cid: str, preis: int) -> tuple[str, str]:
    shop = str(uuid.uuid4())
    ware = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (:Ort {
                id: $shop, campaignId: $cid, name: 'Tutorial-Kiosk',
                istShop: true, istTutorialShop: true,
                sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (:Gegenstand {
                id: $ware, campaignId: $cid, name: 'Klappspaten',
                typ: 'Waffe', preis: $preis, istVorlage: true, bildUrl: ''
            })
            """,
            cid=cid,
            shop=shop,
            ware=ware,
            preis=preis,
        )
    return shop, ware


def test_sortiment_zieht_neuen_vorlagenpreis_nach_wenn_kein_sonderpreis_auf_der_kante():
    """Mark 05.11.2026: Preisänderung am Gegenstand muss im Shop ankommen,
    ohne die Ware rauszuschmeißen und neu hinzuzufügen."""

    async def szenario():
        cid = await _kampagne()
        try:
            shop, ware = await _laden_mit_vorlage(cid, 80)
            assert await repository.verkauft_hinzufuegen(cid, shop, ware, None)
            vorher = {e["gegenstandId"]: e for e in await repository.sortiment(cid, shop)}
            assert vorher[ware]["preis"] == 80

            geaendert = await update_gegenstand(cid, ware, {"preis": 250})
            assert geaendert is not None
            assert geaendert["preis"] == 250

            danach = {e["gegenstandId"]: e for e in await repository.sortiment(cid, shop)}
            assert danach[ware]["preis"] == 250

            driver = get_driver()
            async with driver.session() as session:
                treffer = await session.run(
                    """
                    MATCH (:Ort {id: $shop})-[r:VERKAUFT]->(:Gegenstand {id: $ware})
                    RETURN r.preis AS snapshot
                    """,
                    shop=shop,
                    ware=ware,
                )
                record = await treffer.single()
            assert record is not None
            assert record["snapshot"] is None
        finally:
            await _weg(cid)

    _run(szenario())


def test_unikat_anlegen_friert_den_preis_nicht_auf_der_kante():
    """KI-/Unikat-Anlegen schreibt denselben Betrag auf den Gegenstand —
    die Kante darf ihn nicht nochmal als Snapshot festhalten, sonst bleibt
    der Shop beim alten Wert, wenn der Gegenstand später geändert wird."""

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
            angelegt = await unikat_anlegen(cid, shop, "Reliquie", "Sonstiges", 400, "")
            assert angelegt is not None
            geaendert = await update_gegenstand(cid, angelegt["id"], {"preis": 900})
            assert geaendert is not None
            danach = {e["gegenstandId"]: e for e in await repository.sortiment(cid, shop)}
            assert danach[angelegt["id"]]["preis"] == 900
        finally:
            await _weg(cid)

    _run(szenario())
