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
    campaign_id: str, shop_id: str, gegenstand_id: str, kaeufer_id: str
) -> dict | None:
    """Gibt die Ware an den Käufer. None, wenn Stück oder Übergabe fehlt."""
    gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
    if gegenstand is None:
        return None
    if gegenstand["istVorlage"]:
        return await items_repository.assign_copy(
            campaign_id, gegenstand, kaeufer_id, "SPEZIFISCH", [kaeufer_id]
        )
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
    if not await shop_repository.verkauft_hinzufuegen(campaign_id, shop_id, gegenstand["id"], body.preis):
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
    verkaufspreis = gegenstand["preis"] if preis is None else max(0, preis)
    if not await shop_repository.verkauft_hinzufuegen(campaign_id, shop_id, gegenstand_id, verkaufspreis):
        raise UnikatEinhangFehler("laden")
