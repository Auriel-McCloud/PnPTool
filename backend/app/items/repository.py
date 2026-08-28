import uuid

from app.db.neo4j_driver import get_driver


async def create_gegenstand(campaign_id: str, owner_person_id: str, data: dict) -> dict | None:
    driver = get_driver()
    item_id = str(uuid.uuid4())
    query = """
        MATCH (p:Person {id: $owner_id, campaignId: $campaign_id})
        CREATE (g:Gegenstand {
            id: $item_id, campaignId: $campaign_id, name: $name, description: $description, notes: $notes,
            sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        })
        CREATE (p)-[:BESITZT]->(g)
        RETURN g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
               g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            owner_id=owner_person_id,
            item_id=item_id,
            name=data["name"],
            description=data["description"],
            notes=data["notes"],
            sichtbarkeit=data["sichtbarkeit"],
            sichtbarFuer=data["sichtbarFuer"],
        )
        record = await result.single()
        return dict(record) if record else None


async def list_gegenstaende(campaign_id: str, owner_person_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $owner_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        RETURN g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
               g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer
        ORDER BY g.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, owner_id=owner_person_id)
        return [dict(record) async for record in result]


async def update_gegenstand(campaign_id: str, item_id: str, data: dict) -> dict | None:
    changed = {k: v for k, v in data.items() if v is not None}
    if not changed:
        driver = get_driver()
        query = """
            MATCH (g:Gegenstand {id: $item_id, campaignId: $campaign_id})
            RETURN g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
                   g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer
        """
        async with driver.session() as session:
            result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
            record = await result.single()
            return dict(record) if record else None

    driver = get_driver()
    set_clause = ", ".join(f"g.{k} = ${k}" for k in changed)
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        SET {set_clause}
        RETURN g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
               g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, **changed)
        record = await result.single()
        return dict(record) if record else None


async def delete_gegenstand(campaign_id: str, item_id: str) -> bool:
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {id: $item_id, campaignId: $campaign_id})
        DETACH DELETE g
        RETURN count(g) AS deleted
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        return dict(record)["deleted"] > 0
