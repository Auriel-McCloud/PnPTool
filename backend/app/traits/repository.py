from app.db.neo4j_driver import get_driver


async def list_catalog(ruleset: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (t:TraitDef {ruleset: $ruleset})
        RETURN t.id AS id, t.name AS name, t.category AS category,
               t.defaultMax AS defaultMax, t.sortOrder AS sortOrder
        ORDER BY t.category, t.sortOrder
    """
    async with driver.session() as session:
        result = await session.run(query, ruleset=ruleset)
        return [dict(record) async for record in result]


async def get_ratings_for_entity(campaign_id: str, entity_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})-[r:HAS_TRAIT]->(t:TraitDef)
        RETURN t.id AS traitDefId, t.name AS name, t.category AS category,
               r.rating AS rating, coalesce(r.maxOverride, t.defaultMax) AS max
        ORDER BY t.category, t.sortOrder
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, entity_id=entity_id)
        return [dict(record) async for record in result]


async def set_rating(
    campaign_id: str, entity_id: str, trait_def_id: str, rating: int, max_override: int | None
) -> dict | None:
    """Setzt einen Wert — und lässt ein vorhandenes Maximum in Ruhe.

    **`max_override=None` heisst "nicht anfassen", nicht "löschen".** Das war
    bis 11.09.2026 andersherum, mit einer stillen Nebenwirkung: das
    Charakterblatt schickt beim Klick auf einen Punkt immer `null` mit (siehe
    Charakterblatt.tsx), womit jede Wertänderung den **Rassendeckel**
    gelöscht hat. Ein Elf mit Widerstandsfähigkeit 5 stand danach wieder auf
    dem Katalogmaximum 6 — die Rasse war stillschweigend weg.

    Ein Zurücksetzen auf den Katalogwert gibt es dadurch nicht mehr; das ist
    richtig so, weil der Katalogwert für alles mit Rassenmodifikator ohnehin
    der falsche wäre. Geändert wird das Maximum ausdrücklich über die
    ±-Knöpfe im Blatt (die schicken eine Zahl) oder über den Rassen-Baukasten.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        MATCH (t:TraitDef {id: $trait_def_id})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = $rating,
            r.maxOverride = CASE WHEN $max_override IS NULL THEN r.maxOverride ELSE $max_override END
        RETURN t.id AS traitDefId, t.name AS name, t.category AS category,
               r.rating AS rating, coalesce(r.maxOverride, t.defaultMax) AS max
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            entity_id=entity_id,
            trait_def_id=trait_def_id,
            rating=rating,
            max_override=max_override,
        )
        record = await result.single()
        return dict(record) if record else None


async def set_ratings_bulk(campaign_id: str, entity_id: str, werte: dict[str, int]) -> int:
    """Setzt viele Werte auf einmal — für die Charaktererstellung.

    Einzeln wären das rund fünfzig Abfragen; hier läuft alles in einer.
    `UNWIND` über die Paare, dann dasselbe `MERGE` wie bei `set_rating`.
    Werte mit 0 werden mitgeschrieben statt weggelassen: eine ausdrücklich
    auf 0 gesetzte Fertigkeit ist etwas anderes als eine nie berührte, und
    beim erneuten Einreichen einer Erstellung müssen alte Werte zurückfallen.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        UNWIND $paare AS paar
        MATCH (t:TraitDef {ruleset: $ruleset, name: paar.name})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = paar.wert
        RETURN count(r) AS gesetzt
    """
    paare = [{"name": name, "wert": int(wert)} for name, wert in werte.items()]
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, entity_id=entity_id, paare=paare, ruleset="neotopia"
        )
        record = await result.single()
        return dict(record)["gesetzt"] if record else 0


async def setze_maxima_bulk(campaign_id: str, entity_id: str, maxima: dict[str, int]) -> int:
    """Setzt dauerhafte Obergrenzen (`maxOverride`) für mehrere Werte.

    Für die Rassenmaxima bei der Erstellung: ein Troll darf bei Körperkraft
    dauerhaft über das Katalogmaximum hinaus, ein Elf bei
    Widerstandsfähigkeit darunter bleiben (siehe
    `erstellung.py::lebensmaxima`).

    Getrennt von `set_ratings_bulk`, weil dort **nur** der Wert geschrieben
    wird: würde es das Maximum mitschreiben, überschriebe jede erneut
    eingereichte Erstellung ein von der Spielleitung von Hand angehobenes
    Maximum. Hier ist das Setzen ausdrücklich gewollt.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        UNWIND $paare AS paar
        MATCH (t:TraitDef {ruleset: $ruleset, name: paar.name})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.maxOverride = paar.max
        RETURN count(r) AS gesetzt
    """
    paare = [{"name": name, "max": int(wert)} for name, wert in maxima.items()]
    if not paare:
        return 0
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, entity_id=entity_id, paare=paare, ruleset="neotopia"
        )
        record = await result.single()
        return dict(record)["gesetzt"] if record else 0


async def steigere(campaign_id: str, entity_id: str, trait_def_id: str, neuer_wert: int) -> dict | None:
    """Hebt einen einzelnen Wert an, ohne ein vorhandenes maxOverride zu verlieren.

    `set_rating` setzt `maxOverride` immer mit — hier soll ein vom Spielleiter
    vergebenes höheres Maximum aber bestehen bleiben.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        MATCH (t:TraitDef {id: $trait_def_id})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = $rating
        RETURN t.id AS traitDefId, t.name AS name, t.category AS category,
               r.rating AS rating, coalesce(r.maxOverride, t.defaultMax) AS max
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            entity_id=entity_id,
            trait_def_id=trait_def_id,
            rating=neuer_wert,
        )
        record = await result.single()
        return dict(record) if record else None
