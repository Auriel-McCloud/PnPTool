import json
import uuid

from app.db.neo4j_driver import get_driver

RETURN_FIELDS = """
    g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
    g.typ AS typ, g.eigenschaften AS eigenschaften, g.zeigeInGraph AS zeigeInGraph,
    g.bildUrl AS bildUrl, g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer
"""


def _decode(record: dict) -> dict:
    record = dict(record)
    try:
        record["eigenschaften"] = json.loads(record["eigenschaften"]) if record["eigenschaften"] else {}
    except (json.JSONDecodeError, TypeError):
        record["eigenschaften"] = {}
    record["zeigeInGraph"] = bool(record.get("zeigeInGraph"))
    record["bildUrl"] = record.get("bildUrl") or ""
    return record


async def create_gegenstand(campaign_id: str, owner_person_id: str, data: dict) -> dict | None:
    driver = get_driver()
    item_id = str(uuid.uuid4())
    query = f"""
        MATCH (p:Person {{id: $owner_id, campaignId: $campaign_id}})
        CREATE (g:Gegenstand {{
            id: $item_id, campaignId: $campaign_id, name: $name, description: $description, notes: $notes,
            typ: $typ, eigenschaften: $eigenschaften, zeigeInGraph: $zeigeInGraph, bildUrl: '',
            sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        }})
        CREATE (p)-[:BESITZT]->(g)
        RETURN {RETURN_FIELDS}
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
            typ=data["typ"],
            eigenschaften=json.dumps(data["eigenschaften"]),
            zeigeInGraph=data["zeigeInGraph"],
            sichtbarkeit=data["sichtbarkeit"],
            sichtbarFuer=data["sichtbarFuer"],
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def list_gegenstaende(campaign_id: str, owner_person_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (p:Person {{id: $owner_id, campaignId: $campaign_id}})-[:BESITZT]->(g:Gegenstand)
        RETURN {RETURN_FIELDS}
        ORDER BY g.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, owner_id=owner_person_id)
        return [_decode(dict(record)) async for record in result]


async def update_gegenstand(campaign_id: str, item_id: str, data: dict) -> dict | None:
    changed = {k: v for k, v in data.items() if v is not None}
    if "eigenschaften" in changed:
        changed["eigenschaften"] = json.dumps(changed["eigenschaften"])

    driver = get_driver()
    if not changed:
        query = f"MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}}) RETURN {RETURN_FIELDS}"
        async with driver.session() as session:
            result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
            record = await result.single()
            return _decode(dict(record)) if record else None

    set_clause = ", ".join(f"g.{k} = ${k}" for k in changed)
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        SET {set_clause}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, **changed)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def set_bild_url(campaign_id: str, item_id: str, bild_url: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        SET g.bildUrl = $bild_url
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, bild_url=bild_url)
        record = await result.single()
        return _decode(dict(record)) if record else None


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
