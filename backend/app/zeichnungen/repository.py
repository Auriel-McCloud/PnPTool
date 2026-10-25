"""Neo4j-Zugriff fürs Whiteboard.

Eigenes, schlankes Repository statt Wiederverwendung der generischen
Entities-Funktionen (`app/entities/repository.py::create_node` & Co.):
`Zeichnung` ist kein Entitätstyp (keine Beziehungen, kein Graph-Knoten, keine
Ideenschmiede) — das Anhängen an die EntityKind-Maschinerie wäre Ballast ohne
Nutzen. Papierkorb-Prinzip wie überall sonst (`geloescht`-Flag, kein
Hard-Delete), hier aber mit einer eigenen Papierkorb-Leseroute, weil die SL
ein versehentlich gelöschtes Board zurückholen können soll.
"""

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
]


def _return_clause() -> str:
    return ", ".join(f"n.{f} AS {f}" for f in ["id", *FIELDS])


def _mit_defaults(record: dict) -> dict:
    """Bestandsdaten (None aus Neo4j) auf gültige Default-Werte heben —
    dasselbe Stolperstein-9-Muster wie bei Person/Ort (siehe CLAUDE.md)."""
    daten = dict(record)
    daten["bildUrl"] = daten.get("bildUrl") or ""
    daten["spielerDuerfenZeichnen"] = bool(daten.get("spielerDuerfenZeichnen"))
    daten["sichtbarkeit"] = daten.get("sichtbarkeit") or "GM"
    daten["sichtbarFuer"] = daten.get("sichtbarFuer") or []
    daten["geloescht"] = bool(daten.get("geloescht"))
    daten["erstelltAm"] = daten.get("erstelltAm") or ""

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
    }
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (n:Zeichnung {{id: $node_id, campaignId: $campaign_id, {", ".join(f"{f}: ${f}" for f in FIELDS)}}})
        CREATE (c)-[:HAT_ZEICHNUNG]->(n)
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, node_id=node_id, **props)
        record = await result.single()
        return _mit_defaults(record)


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (n:Zeichnung {{campaignId: $campaign_id}})
        WHERE NOT coalesce(n.geloescht, false)
        RETURN {_return_clause()} ORDER BY n.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_mit_defaults(r) async for r in result]


async def liste_papierkorb(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (n:Zeichnung {{campaignId: $campaign_id}})
        WHERE coalesce(n.geloescht, false)
        RETURN {_return_clause()} ORDER BY n.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_mit_defaults(r) async for r in result]


async def holen(campaign_id: str, zeichnung_id: str, *, nur_nicht_geloescht: bool = True) -> dict | None:
    driver = get_driver()
    filter_klausel = "AND NOT coalesce(n.geloescht, false)" if nur_nicht_geloescht else ""
    query = f"""
        MATCH (n:Zeichnung {{id: $zeichnung_id, campaignId: $campaign_id}})
        WHERE true {filter_klausel}
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, zeichnung_id=zeichnung_id)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def aktualisieren(campaign_id: str, zeichnung_id: str, daten: dict) -> dict | None:
    changed = {k: v for k, v in daten.items() if v is not None}
    if not changed:
        return await holen(campaign_id, zeichnung_id)

    driver = get_driver()
    set_clause = ", ".join(f"n.{f} = ${f}" for f in changed)
    query = f"""
        MATCH (n:Zeichnung {{id: $zeichnung_id, campaignId: $campaign_id}})
        SET {set_clause}
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, zeichnung_id=zeichnung_id, **changed)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def pfade_speichern(campaign_id: str, zeichnung_id: str, pfade: list[dict]) -> dict | None:
    """Ersetzt den gesamten Strich-Stand — kein Diff/Append, dieselbe
    Vollstand-Logik wie bei der Live-Übertragung (siehe verteiler.py:
    jede Änderung schickt den kompletten aktuellen Stand, kein inkrementelles
    Strich-für-Strich-Protokoll)."""
    driver = get_driver()
    query = """
        MATCH (n:Zeichnung {id: $zeichnung_id, campaignId: $campaign_id})
        SET n.pfade = $pfade
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, zeichnung_id=zeichnung_id, pfade=json.dumps(pfade)
        )
    return await holen(campaign_id, zeichnung_id)


async def setze_geloescht(campaign_id: str, zeichnung_id: str, geloescht: bool) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (n:Zeichnung {{id: $zeichnung_id, campaignId: $campaign_id}})
        SET n.geloescht = $geloescht
        RETURN {_return_clause()}
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, zeichnung_id=zeichnung_id, geloescht=geloescht
        )
        record = await result.single()
        return _mit_defaults(record) if record else None
