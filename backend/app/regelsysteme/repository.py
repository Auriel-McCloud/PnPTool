"""Repository für Regelsysteme.

Datenmodell (Neo4j):
    (:Regelsystem {id, name, beschreibung, erstelltAm, aktualisiertAm})
    (:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


FELDER = """
    r.id AS id,
    r.name AS name,
    r.beschreibung AS beschreibung,
    r.erstelltAm AS erstelltAm,
    r.aktualisiertAm AS aktualisiertAm
"""


async def liste() -> list[dict]:
    """Alle Regelsysteme mit Kampagnen-Anzahl."""
    driver = get_driver()
    query = f"""
        MATCH (r:Regelsystem)
        OPTIONAL MATCH (c:Campaign)-[:NUTZT_REGELSYSTEM]->(r)
        RETURN {FELDER}, count(c) AS kampagnenAnzahl
        ORDER BY r.name
    """
    async with driver.session() as session:
        result = await session.run(query)
        return [dict(record) for record in await result.data()]


async def einzeln(regelsystem_id: str) -> dict | None:
    """Ein Regelsystem mit Kampagnen-Anzahl."""
    driver = get_driver()
    query = f"""
        MATCH (r:Regelsystem {{id: $id}})
        OPTIONAL MATCH (c:Campaign)-[:NUTZT_REGELSYSTEM]->(r)
        RETURN {FELDER}, count(c) AS kampagnenAnzahl
    """
    async with driver.session() as session:
        result = await session.run(query, id=regelsystem_id)
        record = await result.single()
        return dict(record) if record else None


async def anlegen(name: str, beschreibung: str = "") -> dict:
    """Neues Regelsystem erstellen."""
    driver = get_driver()
    jetzt = _jetzt()
    regelsystem_id = str(uuid.uuid4())
    query = f"""
        CREATE (r:Regelsystem {{
            id: $id,
            name: $name,
            beschreibung: $beschreibung,
            erstelltAm: $jetzt,
            aktualisiertAm: $jetzt
        }})
        RETURN {FELDER}, 0 AS kampagnenAnzahl
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            id=regelsystem_id,
            name=name,
            beschreibung=beschreibung,
            jetzt=jetzt,
        )
        record = await result.single()
        return dict(record)


async def aendern(regelsystem_id: str, daten: dict) -> dict | None:
    """Regelsystem aktualisieren."""
    driver = get_driver()
    # Nur gesetzte Felder übernehmen
    erlaubt = {"name", "beschreibung"}
    geaendert = {k: v for k, v in daten.items() if k in erlaubt and v is not None}
    if not geaendert:
        return await einzeln(regelsystem_id)

    set_clause = ", ".join(f"r.{k} = ${k}" for k in geaendert)
    query = f"""
        MATCH (r:Regelsystem {{id: $id}})
        SET {set_clause}, r.aktualisiertAm = $jetzt
        WITH r
        OPTIONAL MATCH (c:Campaign)-[:NUTZT_REGELSYSTEM]->(r)
        RETURN {FELDER}, count(c) AS kampagnenAnzahl
    """
    async with driver.session() as session:
        result = await session.run(
            query, id=regelsystem_id, jetzt=_jetzt(), **geaendert
        )
        record = await result.single()
        return dict(record) if record else None


async def loeschen(regelsystem_id: str) -> bool:
    """Regelsystem löschen (nur wenn keine Kampagnen es nutzen)."""
    driver = get_driver()
    # Prüfen ob noch Kampagnen verknüpft sind
    check_query = """
        MATCH (c:Campaign)-[:NUTZT_REGELSYSTEM]->(r:Regelsystem {id: $id})
        RETURN count(c) AS anzahl
    """
    delete_query = """
        MATCH (r:Regelsystem {id: $id})
        WHERE NOT exists((c:Campaign)-[:NUTZT_REGELSYSTEM]->(r))
        DETACH DELETE r
        RETURN count(r) AS geloescht
    """
    async with driver.session() as session:
        # Erst prüfen
        check_result = await session.run(check_query, id=regelsystem_id)
        check_record = await check_result.single()
        if check_record and check_record["anzahl"] > 0:
            return False  # Noch Kampagnen verknüpft

        # Dann löschen
        result = await session.run(delete_query, id=regelsystem_id)
        record = await result.single()
        return record is not None and record["geloescht"] > 0


async def seed_neotopia() -> dict:
    """NeotopiA Regelsystem anlegen falls nicht vorhanden."""
    driver = get_driver()
    query = f"""
        MERGE (r:Regelsystem {{name: 'NeotopiA'}})
        ON CREATE SET
            r.id = $id,
            r.beschreibung = $beschreibung,
            r.erstelltAm = $jetzt,
            r.aktualisiertAm = $jetzt
        WITH r
        OPTIONAL MATCH (c:Campaign)-[:NUTZT_REGELSYSTEM]->(r)
        RETURN {FELDER}, count(c) AS kampagnenAnzahl
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            id=str(uuid.uuid4()),
            beschreibung="WoD-Attribute + Shadowrun-Cyberware + Mage-Sphären in einem Cyberpunk-Setting.",
            jetzt=_jetzt(),
        )
        record = await result.single()
        return dict(record)
