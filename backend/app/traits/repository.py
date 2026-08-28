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
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        MATCH (t:TraitDef {id: $trait_def_id})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = $rating, r.maxOverride = $max_override
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
