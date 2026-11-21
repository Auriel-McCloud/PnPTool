"""Shop: Anzahl beim Kauf + Warenkorb (20.11.2026).

Echte Neo4j-Abfragen (dev-Container), die Routen-Funktionen werden direkt
mit einem Viewer aufgerufen. Gemockt sind nur das Ereignisprotokoll (um den
gebuchten Betrag prüfen zu können) und — beim Rassen-Feature — der globale
Rassen-Katalog, damit der Test keine geteilte Rasse anlegen/löschen muss.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.db.neo4j_driver import close_driver, get_driver
from app.ereignisprotokoll import hooks
from app.haendler import kauf
from app.haendler import repository as haendler_repository
from app.haendler.routes import bestellung_liefern, kaufen, kaufen_warenkorb
from app.haendler.schemas import KaufRequest, WarenkorbKaufRequest, WarenkorbPosition
from app.haendler.uebergabe import unikat_anlegen
from app.items import repository as items_repository
from app.items.routes import _create_data
from app.items.schemas import GegenstandCreate
from app.rassen import repository as rassen_repository


def _run(coro):
    async def wrapped():
        try:
            return await coro
        finally:
            await close_driver()

    return asyncio.run(wrapped())


@pytest.fixture(autouse=True)
def _protokoll_stumm(monkeypatch):
    handel = AsyncMock()
    geld = AsyncMock()
    monkeypatch.setattr(hooks, "handel", handel)
    monkeypatch.setattr(hooks, "geld", geld)
    return handel, geld


async def _laden(vertriebsart: str = "PHYSISCH", tutorial: bool = False) -> tuple[str, str]:
    cid = f"test-shop-warenkorb-{uuid.uuid4()}"
    shop = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (c:Campaign {id: $cid, name: 'Warenkorb-Test'})
            CREATE (o:Ort {
                id: $shop, campaignId: $cid, name: 'Futterkiste',
                istShop: true, istTutorialShop: $tutorial, vertriebsart: $art,
                spezialisierung: [], sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (c)-[:HAT_ENTITAET]->(o)
            """,
            cid=cid,
            shop=shop,
            art=vertriebsart,
            tutorial=tutorial,
        )
    return cid, shop


async def _kaeufer(cid: str, kapital: int, rasse: str = "", fertig: bool = True) -> str:
    pid = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (p:Person {
                id: $pid, campaignId: $cid, name: 'Käuferin', personType: 'PC',
                kapital: $kapital, rasse: $rasse, erstellungAbgeschlossen: $fertig,
                tutorialAusgegeben: 0, sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            """,
            cid=cid,
            pid=pid,
            kapital=kapital,
            rasse=rasse,
            fertig=fertig,
        )
    return pid


async def _vorlage(cid: str, shop: str, name: str, preis: int, typ: str = "Verbrauchsgegenstand", **felder) -> str:
    """Kopierbare Vorlage im Regal. Verbrauchsgegenstand = stapelbar per Default
    (einzigartig=false, hatMenge=true, menge=1, siehe GegenstandCreate)."""
    body = GegenstandCreate(name=name, typ=typ, preis=preis, automatischImShop=False, **felder)
    g = await items_repository.create_gegenstand(cid, None, _create_data(body, True, "GM", []))
    assert g is not None and g["istVorlage"] is True
    assert await haendler_repository.verkauft_hinzufuegen(cid, shop, g["id"], None)
    return g["id"]


async def _besitz(cid: str, pid: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $pid, campaignId: $cid})-[:BESITZT]->(g:Gegenstand)
            RETURN g.name AS name, g.hatMenge AS hatMenge, g.menge AS menge
            ORDER BY g.name
            """,
            cid=cid,
            pid=pid,
        )
        return [dict(r) async for r in result]


async def _person(cid: str, pid: str) -> dict:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $pid, campaignId: $cid})
            RETURN p.kapital AS kapital, p.rassenFeatureGenutzt AS genutzt,
                   p.tutorialAusgegeben AS ausgegeben
            """,
            cid=cid,
            pid=pid,
        )
        return dict(await result.single())


async def _im_regal(cid: str, shop: str) -> set[str]:
    return {e["gegenstandId"] for e in await haendler_repository.sortiment(cid, shop)}


async def _weg(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


def _spieler(pid: str) -> Viewer:
    return Viewer(role="PLAYER", person_id=pid)


def _korb(*zeilen: tuple[str, int]) -> WarenkorbKaufRequest:
    return WarenkorbKaufRequest(positionen=[WarenkorbPosition(gegenstandId=g, anzahl=n) for g, n in zeilen])


# --- Einzelkauf mit Anzahl ----------------------------------------------------


def test_anzahl_ergibt_einen_stapel_und_kostet_das_vielfache(_protokoll_stumm):
    handel, _ = _protokoll_stumm

    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            antwort = await kaufen(cid, shop, KaufRequest(gegenstandId=futter, anzahl=3), _spieler(pid))
            assert antwort.kapitalNeu == 64
            assert antwort.gegenstand["hatMenge"] is True
            assert antwort.gegenstand["menge"] == 3
            assert await _besitz(cid, pid) == [{"name": "Tierfutter", "hatMenge": True, "menge": 3}]
            assert (await _person(cid, pid))["kapital"] == 64
            # Vorlage bleibt im Regal (unendlich verfügbar)
            assert futter in await _im_regal(cid, shop)
            assert handel.await_args.kwargs["betrag"] == 36
            assert handel.await_args.kwargs["detail"].startswith("3× ")
        finally:
            await _weg(cid)

    _run(szenario())


def test_anzahl_1_bleibt_wie_bisher():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100)
            seil = await _vorlage(cid, shop, "Seil", 7, typ="Sonstiges", einzigartig=False, hatMenge=False)
            antwort = await kaufen(cid, shop, KaufRequest(gegenstandId=seil), _spieler(pid))
            assert antwort.kapitalNeu == 93
            assert await _besitz(cid, pid) == [{"name": "Seil", "hatMenge": False, "menge": 1}]
        finally:
            await _weg(cid)

    _run(szenario())


def test_packungsgroesse_der_vorlage_wird_multipliziert():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100)
            muni = await _vorlage(cid, shop, "Munition", 5, typ="Sonstiges", einzigartig=False, hatMenge=True, menge=10)
            await kaufen(cid, shop, KaufRequest(gegenstandId=muni, anzahl=2), _spieler(pid))
            assert await _besitz(cid, pid) == [{"name": "Munition", "hatMenge": True, "menge": 20}]
            assert (await _person(cid, pid))["kapital"] == 90
        finally:
            await _weg(cid)

    _run(szenario())


def test_unikat_mit_anzahl_ist_400_und_nichts_passiert():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 1000)
            messer = await unikat_anlegen(cid, shop, "Das eine Messer", "Waffe", 80)
            with pytest.raises(HTTPException) as fehler:
                await kaufen(cid, shop, KaufRequest(gegenstandId=messer["id"], anzahl=2), _spieler(pid))
            assert fehler.value.status_code == 400
            assert await _besitz(cid, pid) == []
            assert (await _person(cid, pid))["kapital"] == 1000
            assert messer["id"] in await _im_regal(cid, shop)
        finally:
            await _weg(cid)

    _run(szenario())


def test_einzigartige_vorlage_mit_anzahl_ist_400():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 1000)
            amulett = await _vorlage(cid, shop, "Amulett", 10, typ="Sonstiges", einzigartig=True)
            with pytest.raises(HTTPException) as fehler:
                await kaufen(cid, shop, KaufRequest(gegenstandId=amulett, anzahl=2), _spieler(pid))
            assert fehler.value.status_code == 400
            assert await _besitz(cid, pid) == []
        finally:
            await _weg(cid)

    _run(szenario())


def test_guthaben_zaehlt_die_gesamtsumme():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 30)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            with pytest.raises(HTTPException) as fehler:
                await kaufen(cid, shop, KaufRequest(gegenstandId=futter, anzahl=3), _spieler(pid))
            assert fehler.value.status_code == 409
            assert "36¥ nötig" in fehler.value.detail
            assert await _besitz(cid, pid) == []
            assert (await _person(cid, pid))["kapital"] == 30
        finally:
            await _weg(cid)

    _run(szenario())


def test_rassen_feature_macht_nur_ein_stueck_gratis(monkeypatch):
    monkeypatch.setattr(
        rassen_repository,
        "liste_fuer_kampagne",
        AsyncMock(return_value=[{"name": "Testvolk", "gratisErsterKaufTyp": "Verbrauchsgegenstand"}]),
    )

    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100, rasse="Testvolk")
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            erste = await kaufen(cid, shop, KaufRequest(gegenstandId=futter, anzahl=3), _spieler(pid))
            assert erste.kapitalNeu == 76  # 2 × 12, ein Stück gratis
            assert (await _person(cid, pid))["genutzt"] is True
            zweite = await kaufen(cid, shop, KaufRequest(gegenstandId=futter, anzahl=3), _spieler(pid))
            assert zweite.kapitalNeu == 40  # Feature verbraucht → voller Preis
        finally:
            await _weg(cid)

    _run(szenario())


def test_tutorial_shop_bleibt_stueck_fuer_stueck():
    async def szenario():
        cid, shop = await _laden(tutorial=True)
        try:
            pid = await _kaeufer(cid, 100, fertig=False)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            with pytest.raises(HTTPException) as fehler:
                await kaufen(cid, shop, KaufRequest(gegenstandId=futter, anzahl=2), _spieler(pid))
            assert fehler.value.status_code == 400
            with pytest.raises(HTTPException) as fehler:
                await kaufen_warenkorb(cid, shop, _korb((futter, 1)), _spieler(pid))
            assert fehler.value.status_code == 400
            # Einzelkauf ohne Anzahl geht weiter (TutorialShopPopup)
            antwort = await kaufen(cid, shop, KaufRequest(gegenstandId=futter), _spieler(pid))
            assert antwort.kapitalNeu == 88
            assert antwort.tutorialAusgegeben == 12
        finally:
            await _weg(cid)

    _run(szenario())


# --- Warenkorb ----------------------------------------------------------------


def test_warenkorb_stapel_und_unikat_gemischt(_protokoll_stumm):
    handel, _ = _protokoll_stumm

    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            messer = (await unikat_anlegen(cid, shop, "Das eine Messer", "Waffe", 50))["id"]
            antwort = await kaufen_warenkorb(cid, shop, _korb((futter, 2), (messer, 1)), _spieler(pid))
            assert antwort.bezahlt == 74
            assert antwort.kapitalNeu == 26
            assert antwort.fehlgeschlagen == []
            assert [(z.name, z.anzahl, z.preis) for z in antwort.gekauft] == [
                ("Tierfutter", 2, 24),
                ("Das eine Messer", 1, 50),
            ]
            assert await _besitz(cid, pid) == [
                {"name": "Das eine Messer", "hatMenge": False, "menge": 1},
                {"name": "Tierfutter", "hatMenge": True, "menge": 2},
            ]
            assert (await _person(cid, pid))["kapital"] == 26
            regal = await _im_regal(cid, shop)
            assert futter in regal and messer not in regal
            assert sorted(c.kwargs["betrag"] for c in handel.await_args_list) == [24, 50]
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_zu_teuer_kauft_gar_nichts():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 60)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            messer = (await unikat_anlegen(cid, shop, "Das eine Messer", "Waffe", 50))["id"]
            with pytest.raises(HTTPException) as fehler:
                await kaufen_warenkorb(cid, shop, _korb((futter, 2), (messer, 1)), _spieler(pid))
            assert fehler.value.status_code == 409
            assert "74¥ nötig" in fehler.value.detail
            assert await _besitz(cid, pid) == []
            assert (await _person(cid, pid))["kapital"] == 60
            assert messer in await _im_regal(cid, shop)
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_unikat_inzwischen_weg_kauft_gar_nichts():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 1000)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            messer = (await unikat_anlegen(cid, shop, "Das eine Messer", "Waffe", 50))["id"]
            # Jemand anderes war schneller: das Stück hängt nicht mehr im Regal.
            await haendler_repository.verkauft_entfernen(cid, shop, messer)
            with pytest.raises(HTTPException) as fehler:
                await kaufen_warenkorb(cid, shop, _korb((futter, 2), (messer, 1)), _spieler(pid))
            assert fehler.value.status_code == 409
            assert "Das eine Messer" in fehler.value.detail
            assert await _besitz(cid, pid) == []
            assert (await _person(cid, pid))["kapital"] == 1000
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_doppelte_zeile_ist_400():
    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 1000)
            messer = (await unikat_anlegen(cid, shop, "Das eine Messer", "Waffe", 50))["id"]
            with pytest.raises(HTTPException) as fehler:
                await kaufen_warenkorb(cid, shop, _korb((messer, 1), (messer, 1)), _spieler(pid))
            assert fehler.value.status_code == 400
            assert await _besitz(cid, pid) == []
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_rassen_feature_genau_einmal(monkeypatch):
    monkeypatch.setattr(
        rassen_repository,
        "liste_fuer_kampagne",
        AsyncMock(return_value=[{"name": "Testvolk", "gratisErsterKaufTyp": "Verbrauchsgegenstand"}]),
    )

    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100, rasse="Testvolk")
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            trank = await _vorlage(cid, shop, "Heiltrank", 20)
            antwort = await kaufen_warenkorb(cid, shop, _korb((futter, 2), (trank, 1)), _spieler(pid))
            # Nur das erste passende Stück (1× Tierfutter) ist gratis.
            assert [(z.name, z.preis) for z in antwort.gekauft] == [("Tierfutter", 12), ("Heiltrank", 20)]
            assert antwort.bezahlt == 32
            assert antwort.kapitalNeu == 68
            assert (await _person(cid, pid))["genutzt"] is True
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_fehlschlag_mittendrin_wird_erstattet(monkeypatch):
    """Erstellung läuft (Tutorial-Buchung vorab): die gescheiterte Zeile
    kommt zurück, der Rest bleibt gekauft."""
    echte_uebergabe = kauf.stueck_uebergeben

    async def scheitert_beim_messer(campaign_id, shop_id, gegenstand_id, kaeufer_id, anzahl=1):
        if gegenstand_id == messer_id["id"]:
            return None
        return await echte_uebergabe(campaign_id, shop_id, gegenstand_id, kaeufer_id, anzahl)

    monkeypatch.setattr(kauf, "stueck_uebergeben", scheitert_beim_messer)
    messer_id: dict = {}

    async def szenario():
        cid, shop = await _laden()
        try:
            pid = await _kaeufer(cid, 100, fertig=False)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            messer_id["id"] = (await unikat_anlegen(cid, shop, "Das eine Messer", "Waffe", 50))["id"]
            antwort = await kaufen_warenkorb(
                cid, shop, _korb((futter, 2), (messer_id["id"], 1)), _spieler(pid)
            )
            assert antwort.bezahlt == 24
            assert antwort.erstattet == 50
            assert [z.name for z in antwort.fehlgeschlagen] == ["Das eine Messer"]
            assert antwort.kapitalNeu == 76
            assert antwort.tutorialAusgegeben == 24
            person = await _person(cid, pid)
            assert person["kapital"] == 76 and person["ausgegeben"] == 24
            assert await _besitz(cid, pid) == [{"name": "Tierfutter", "hatMenge": True, "menge": 2}]
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_digital_bestellung_traegt_anzahl_und_liefert_stapel(_protokoll_stumm):
    _, geld = _protokoll_stumm

    async def szenario():
        cid, shop = await _laden(vertriebsart="DIGITAL")
        try:
            pid = await _kaeufer(cid, 100)
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            antwort = await kaufen_warenkorb(cid, shop, _korb((futter, 3),), _spieler(pid))
            assert antwort.gegenstaende == []
            assert len(antwort.bestellungen) == 1
            bestellung = antwort.bestellungen[0]
            assert bestellung["anzahl"] == 3 and bestellung["preis"] == 36
            assert antwort.kapitalNeu == 64
            assert geld.await_args.kwargs["betrag"] == 36
            assert await _besitz(cid, pid) == []
            geliefert = await bestellung_liefern(cid, bestellung["id"])
            assert geliefert["status"] == "GELIEFERT" and geliefert["anzahl"] == 3
            assert await _besitz(cid, pid) == [{"name": "Tierfutter", "hatMenge": True, "menge": 3}]
        finally:
            await _weg(cid)

    _run(szenario())


def test_warenkorb_sl_braucht_kaeufer():
    async def szenario():
        cid, shop = await _laden()
        try:
            futter = await _vorlage(cid, shop, "Tierfutter", 12)
            with pytest.raises(HTTPException) as fehler:
                await kaufen_warenkorb(cid, shop, _korb((futter, 1)), Viewer(role="GM", person_id=None))
            assert fehler.value.status_code == 400
        finally:
            await _weg(cid)

    _run(szenario())
