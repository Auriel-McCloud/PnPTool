"""Neo4j-Zugriff für Battlemaps. Eigenes schlankes Repository, analog Zeichnung."""

import json
import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

FIELDS = [
    "name",
    "pfade",
    "bildUrl",
    "spielerDuerfenZeichnen",
    "sichtbarkeit",
    "sichtbarFuer",
    "geloescht",
    "erstelltAm",
    "hexGroesse",
    "originX",
    "originY",
    "spawnPcQ",
    "spawnPcR",
    "spawnNpcQ",
    "spawnNpcR",
    "ortIds",
    "eventIds",
    "waende",
]


def _return_clause() -> str:
    return ", ".join(f"n.{f} AS {f}" for f in ["id", *FIELDS])


def _mit_defaults(record: dict) -> dict:
    daten = dict(record)
    daten["bildUrl"] = daten.get("bildUrl") or ""
    daten["spielerDuerfenZeichnen"] = bool(daten.get("spielerDuerfenZeichnen"))
    daten["sichtbarkeit"] = daten.get("sichtbarkeit") or "GM"
    daten["sichtbarFuer"] = daten.get("sichtbarFuer") or []
    daten["geloescht"] = bool(daten.get("geloescht"))
    daten["erstelltAm"] = daten.get("erstelltAm") or ""
    daten["hexGroesse"] = int(daten.get("hexGroesse") or 48)
    daten["originX"] = float(daten.get("originX") or 0)
    daten["originY"] = float(daten.get("originY") or 0)
    for feld in ("spawnPcQ", "spawnPcR", "spawnNpcQ", "spawnNpcR"):
        roh = daten.get(feld)
        daten[feld] = int(roh) if roh is not None else None
    daten["ortIds"] = daten.get("ortIds") or []
    daten["eventIds"] = daten.get("eventIds") or []
    waende = daten.get("waende")
    if isinstance(waende, str):
        try:
            waende = json.loads(waende)
        except (json.JSONDecodeError, TypeError):
            waende = []
    daten["waende"] = waende if isinstance(waende, list) else []
    pfade = daten.get("pfade")
    if isinstance(pfade, str):
        try:
            pfade = json.loads(pfade)
        except (json.JSONDecodeError, TypeError):
            pfade = []
    daten["pfade"] = pfade if isinstance(pfade, list) else []
    return daten


async def erstellen(campaign_id: str, daten: dict) -> dict:
    driver = get_driver()
    node_id = str(uuid.uuid4())
    erstellt_am = datetime.now(timezone.utc).isoformat()
    props = {
        "name": daten["name"],
        "pfade": json.dumps([]),
        "bildUrl": daten.get("bildUrl") or "",
        "spielerDuerfenZeichnen": bool(daten.get("spielerDuerfenZeichnen")),
        "sichtbarkeit": daten.get("sichtbarkeit") or "GM",
        "sichtbarFuer": daten.get("sichtbarFuer") or [],
        "geloescht": False,
        "erstelltAm": erstellt_am,
        "hexGroesse": int(daten.get("hexGroesse") or 48),
        "originX": float(daten.get("originX") or 0),
        "originY": float(daten.get("originY") or 0),
        "spawnPcQ": daten.get("spawnPcQ"),
        "spawnPcR": daten.get("spawnPcR"),
        "spawnNpcQ": daten.get("spawnNpcQ"),
        "spawnNpcR": daten.get("spawnNpcR"),
        "ortIds": daten.get("ortIds") or [],
        "eventIds": daten.get("eventIds") or [],
        "waende": json.dumps(daten.get("waende") or []),
    }
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (n:Battlemap {{id: $node_id, campaignId: $campaign_id, {", ".join(f"{f}: ${f}" for f in FIELDS)}}})
        CREATE (c)-[:HAT_BATTLEMAP]->(n)
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, node_id=node_id, **props)
        record = await result.single()
        return _mit_defaults(record)


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (n:Battlemap {{campaignId: $campaign_id}})
        WHERE NOT coalesce(n.geloescht, false)
        RETURN {_return_clause()} ORDER BY n.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_mit_defaults(r) async for r in result]


async def liste_papierkorb(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (n:Battlemap {{campaignId: $campaign_id}})
        WHERE coalesce(n.geloescht, false)
        RETURN {_return_clause()} ORDER BY n.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_mit_defaults(r) async for r in result]


async def holen(campaign_id: str, karte_id: str, *, nur_nicht_geloescht: bool = True) -> dict | None:
    driver = get_driver()
    filter_klausel = "AND NOT coalesce(n.geloescht, false)" if nur_nicht_geloescht else ""
    query = f"""
        MATCH (n:Battlemap {{id: $karte_id, campaignId: $campaign_id}})
        WHERE true {filter_klausel}
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, karte_id=karte_id)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def aktualisieren(campaign_id: str, karte_id: str, daten: dict) -> dict | None:
    changed = {k: v for k, v in daten.items() if v is not None}
    if "waende" in changed:
        changed["waende"] = json.dumps(changed["waende"])
    if not changed:
        return await holen(campaign_id, karte_id)
    driver = get_driver()
    set_clause = ", ".join(f"n.{f} = ${f}" for f in changed)
    query = f"""
        MATCH (n:Battlemap {{id: $karte_id, campaignId: $campaign_id}})
        SET {set_clause}
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, karte_id=karte_id, **changed)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def pfade_speichern(campaign_id: str, karte_id: str, pfade: list[dict]) -> dict | None:
    driver = get_driver()
    query = """
        MATCH (n:Battlemap {id: $karte_id, campaignId: $campaign_id})
        SET n.pfade = $pfade
    """
    async with driver.session() as session:
        await session.run(query, campaign_id=campaign_id, karte_id=karte_id, pfade=json.dumps(pfade))
    return await holen(campaign_id, karte_id)


async def setze_geloescht(campaign_id: str, karte_id: str, geloescht: bool) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (n:Battlemap {{id: $karte_id, campaignId: $campaign_id}})
        SET n.geloescht = $geloescht
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, karte_id=karte_id, geloescht=geloescht)
        record = await result.single()
        return _mit_defaults(record) if record else None
