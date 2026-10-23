from app.db.neo4j_driver import get_driver


async def get_all_nodes(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (n)
        WHERE n.campaignId = $campaign_id
          AND (n:Person OR n:Ort OR n:Event OR n:Fraktion OR n:Party OR (n:Gegenstand AND n.storyRelevant = true))
        RETURN n.id AS id, labels(n)[0] AS kind,
               coalesce(n.name, n.title) AS label,
               n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]


async def get_all_edges(campaign_id: str) -> list[dict]:
    """Echte VERBINDUNG-Kanten plus Mitgliedschaft/Aufenthaltsort aus dem
    Party-System (23.10.2026, Mark will im Graphen sehen können, wo seine
    Spieler gerade sind — dieselbe Erweiterung wie
    entities/repository.py::list_verbindungen, nur für die Canvas-Ansicht)."""
    driver = get_driver()
    query = """
        MATCH (a)-[r:VERBINDUNG]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
        RETURN r.id AS id, a.id AS source, b.id AS target,
               r.typ AS typ, r.sichtbarkeit AS sichtbarkeit, r.sichtbarFuer AS sichtbarFuer

        UNION ALL

        MATCH (a:Person)-[:MITGLIED_VON]->(b:Party)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
        RETURN 'mitglied:' + a.id AS id, a.id AS source, b.id AS target,
               'Mitglied von' AS typ, 'ALLE' AS sichtbarkeit, [] AS sichtbarFuer

        UNION ALL

        MATCH (a:Party)-[:BEFINDET_SICH_AN]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
        RETURN 'aufenthalt:' + a.id AS id, a.id AS source, b.id AS target,
               'Befindet sich an' AS typ, 'ALLE' AS sichtbarkeit, [] AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]
