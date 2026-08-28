import uuid

from app.db.neo4j_driver import get_driver


async def create_campaign(name: str, ruleset: str, gm_id: str) -> dict:
    driver = get_driver()
    campaign_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (g:GMUser {id: $gm_id})
            CREATE (c:Campaign {id: $campaign_id, name: $name, ruleset: $ruleset, createdAt: datetime()})
            CREATE (g)-[:OWNS]->(c)
            RETURN c.id AS id, c.name AS name, c.ruleset AS ruleset
            """,
            gm_id=gm_id,
            campaign_id=campaign_id,
            name=name,
            ruleset=ruleset,
        )
        record = await result.single()
        return dict(record)


async def list_campaigns_for_gm(gm_id: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (g:GMUser {id: $gm_id})-[:OWNS]->(c:Campaign) "
            "RETURN c.id AS id, c.name AS name, coalesce(c.ruleset, 'neotopia') AS ruleset ORDER BY c.name",
            gm_id=gm_id,
        )
        return [dict(record) async for record in result]


async def campaign_owned_by(campaign_id: str, gm_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (g:GMUser {id: $gm_id})-[:OWNS]->(c:Campaign {id: $campaign_id}) RETURN c.id AS id",
            gm_id=gm_id,
            campaign_id=campaign_id,
        )
        return await result.single() is not None


async def get_campaign(campaign_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign {id: $campaign_id}) RETURN c.id AS id, c.name AS name, coalesce(c.ruleset, 'neotopia') AS ruleset",
            campaign_id=campaign_id,
        )
        record = await result.single()
        return dict(record) if record else None
