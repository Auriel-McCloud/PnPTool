"""Ware aus dem Regal an eine Person geben.

Vorlage: Kopie, das Regal bleibt. Unikat: dasselbe Stück. Liegt es nur im
Regal (kein BESITZT — der Laden ist ein Ort, keine Person), wird der Käufer
der erste Besitzer. Danach sind alle VERKAUFT-Kanten zu diesem Stück weg.
"""

from app.db.neo4j_driver import get_driver
from app.items import repository as items_repository


async def regale_raeumen(campaign_id: str, shop_id: str, gegenstand_id: str) -> None:
    """Nimmt das Stück aus jedem Laden. shop_id muss existieren, sonst passiert nichts."""
    driver = get_driver()
    query = """
        MATCH (ausloeser:Ort {id: $shop_id, campaignId: $campaign_id, istShop: true})
        MATCH (:Ort {campaignId: $campaign_id})-[r:VERKAUFT]->(g:Gegenstand {id: $gegenstand_id, campaignId: $campaign_id})
        DELETE r
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, shop_id=shop_id, gegenstand_id=gegenstand_id
        )


async def stueck_uebergeben(
    campaign_id: str, shop_id: str, gegenstand_id: str, kaeufer_id: str, anzahl: int = 1
) -> dict | None:
    """Gibt die Ware an den Käufer. None, wenn Stück oder Übergabe fehlt.

    `anzahl > 1` (20.11.2026, nur Vorlagen): EINE Kopie als Stapel —
    `hatMenge=true`, `menge = anzahl × Packungsgröße der Vorlage` (Vorlage
    ohne Menge zählt als 1). Kein automatisches Zusammenlegen mit einem
    schon vorhandenen Stapel, dafür gibt es „Zusammenlegen“. Ein
    Einzelstück mit anzahl > 1 lehnt die Kauf-Route vorher ab; kommt es
    trotzdem hier an, wird nichts übergeben (None).
    """
    gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
    if gegenstand is None:
        return None
    if gegenstand["istVorlage"]:
        quelle = gegenstand
        if anzahl > 1:
            packung = max(1, int(gegenstand.get("menge") or 1)) if gegenstand.get("hatMenge") else 1
            quelle = {**gegenstand, "hatMenge": True, "menge": anzahl * packung}
        return await items_repository.assign_copy(
            campaign_id, quelle, kaeufer_id, "SPEZIFISCH", [kaeufer_id]
        )
    if anzahl != 1:
        return None
    owner = await items_repository.get_owner_id(campaign_id, gegenstand_id)
    if owner is None:
        gekauft = await items_repository.assign_owner(
            campaign_id, gegenstand_id, kaeufer_id, "SPEZIFISCH", [kaeufer_id]
        )
    else:
        gekauft = await items_repository.transfer_owner(campaign_id, gegenstand_id, kaeufer_id)
        if gekauft is not None:
            gekauft = await items_repository.update_gegenstand(
                campaign_id,
                gegenstand_id,
                {"sichtbarkeit": "SPEZIFISCH", "sichtbarFuer": [kaeufer_id]},
            )
            from app.items.schloss import inhalt_mitnehmen

            await inhalt_mitnehmen(campaign_id, gegenstand_id, kaeufer_id)
    if gekauft is None:
        return None
    await regale_raeumen(campaign_id, shop_id, gegenstand_id)
    return gekauft


async def unikat_anlegen(
    campaign_id: str,
    shop_id: str,
    name: str,
    typ: str,
    preis: int,
    description: str = "",
) -> dict | None:
    """Legt ein besitzerloses Einzelstück an und hängt es an den Laden.

    None, wenn der Laden fehlt oder der Typ unbekannt ist. Das Stück ist
    keine Vorlage — der erste Kauf übergibt genau diesen Knoten.
    """
    from app.haendler import repository as shop_repository
    from app.items.routes import _create_data
    from app.items.schemas import GEGENSTAND_TYPEN, GegenstandCreate

    if typ not in GEGENSTAND_TYPEN:
        return None
    if await shop_repository.hole(campaign_id, shop_id) is None:
        return None
    body = GegenstandCreate(
        name=name.strip() or "Unbenanntes Einzelstück",
        description=description,
        typ=typ,
        preis=max(0, preis),
        einzigartig=True,
        automatischImShop=False,
    )
    gegenstand = await items_repository.create_gegenstand(
        campaign_id, None, _create_data(body, False, "GM", [])
    )
    if gegenstand is None:
        return None
    if not await shop_repository.verkauft_hinzufuegen(campaign_id, shop_id, gegenstand["id"], None):
        return None
    return gegenstand


class UnikatEinhangFehler(Exception):
    """Bestehendes Stück lässt sich nicht als Einzelstück ins Regal hängen."""

    def __init__(self, grund: str):
        super().__init__(grund)
        self.grund = grund


async def unikat_einhaengen(
    campaign_id: str, shop_id: str, gegenstand_id: str, preis: int | None
) -> None:
    """Hängt ein bestehendes Einzelstück an den Laden.

    Kopierbare Vorlagen bleiben Vorlagen (die nimmt der Vorlage-Picker).
    Eine einzigartige oder story-relevante Vorlage wird dabei zum Einzelstück,
    sonst würde der Kauf sie kopieren. Spielerbesitz bleibt tabu.
    """
    from app.entities.repository import PERSON_FIELDS, get_node
    from app.haendler import repository as shop_repository

    if await shop_repository.hole(campaign_id, shop_id) is None:
        raise UnikatEinhangFehler("laden")
    gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
    if gegenstand is None:
        raise UnikatEinhangFehler("gegenstand")
    owner = await items_repository.get_owner_id(campaign_id, gegenstand_id)
    if owner:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, owner)
        if person and person.get("personType") == "PC":
            raise UnikatEinhangFehler("spieler")
    if gegenstand["istVorlage"]:
        if not (gegenstand.get("einzigartig") or gegenstand.get("storyRelevant")):
            raise UnikatEinhangFehler("vorlage")
        if await items_repository.update_gegenstand(
            campaign_id,
            gegenstand_id,
            {"istVorlage": False, "einzigartig": True, "automatischImShop": False},
        ) is None:
            raise UnikatEinhangFehler("gegenstand")
    verkaufspreis = None if preis is None else max(0, preis)
    if not await shop_repository.verkauft_hinzufuegen(campaign_id, shop_id, gegenstand_id, verkaufspreis):
        raise UnikatEinhangFehler("laden")


async def critter_uebergeben(
    campaign_id: str, shop_id: str, critter_id: str, kaeufer_id: str
) -> dict | None:
    """Gibt einen im Tierladen gekauften Critter an den Käufer (Tierladen,
    18.11.2026) — dasselbe Grundmuster wie `stueck_uebergeben`, nur erzeugt
    die Übergabe eine `BEGLEITET`- statt eine `BESITZT`-Kante (siehe
    `entities/repository.py::critter_besitzer_setzen`). None, wenn der
    Critter fehlt oder die Bindung fehlschlägt."""
    from app.entities import repository as entities_repository
    from app.haendler import repository as shop_repository

    gekauft = await entities_repository.critter_besitzer_setzen(campaign_id, critter_id, kaeufer_id)
    if gekauft is None:
        return None
    await shop_repository.pet_regal_raeumen(campaign_id, critter_id)
    return gekauft
