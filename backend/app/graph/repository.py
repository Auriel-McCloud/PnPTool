from app.db.neo4j_driver import get_driver


async def get_all_nodes(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (n)
        WHERE n.campaignId = $campaign_id
          AND (n:Person OR n:Ort OR n:Event OR (n:Gegenstand AND n.zeigeInGraph = true))
        RETURN n.id AS id, labels(n)[0] AS kind,
               coalesce(n.name, n.title) AS label,
               n.sichtbarkeit AS sichtbarkeit
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]


async def get_all_edges(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (a)-[r:VERBINDUNG]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
        RETURN r.id AS id, a.id AS source, b.id AS target,
               r.typ AS typ, r.sichtbarkeit AS sichtbarkeit
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]
