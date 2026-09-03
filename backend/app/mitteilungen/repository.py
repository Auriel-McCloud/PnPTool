"""Neo4j-Zugriff für SL-Mitteilungen.

    (:Campaign)-[:HAT_MITTEILUNG]->(:Mitteilung {campaignId})

Die Empfänger stehen als Liste am Knoten statt als Kanten: Eine Mitteilung
ist ein einmaliger Vorgang, keine dauerhafte Beziehung — und die Liste wird
immer als Ganzes gelesen.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

_FELDER = """
    m.id AS id, m.art AS art, m.inhalt AS inhalt, m.bildUrl AS bildUrl,
    m.anAlle AS anAlle, m.empfaengerIds AS empfaengerIds,
    m.gelesenVon AS gelesenVon, m.erstelltAm AS erstelltAm
"""

# Wie viele Mitteilungen beim Verbinden nachgeladen werden. Eine Sitzung
# erzeugt selten mehr; alles Ältere ist ohnehin nicht mehr interessant.
NACHLADEN = 50


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mit_defaults(record) -> dict:
    m = dict(record)
    m["art"] = m.get("art") or "TEXT"
    m["inhalt"] = m.get("inhalt") or ""
    m["bildUrl"] = m.get("bildUrl") or ""
    m["anAlle"] = bool(m.get("anAlle"))
    m["empfaengerIds"] = m.get("empfaengerIds") or []
    m["gelesenVon"] = m.get("gelesenVon") or []
    m["erstelltAm"] = m.get("erstelltAm") or ""
    return m


async def create_mitteilung(
    campaign_id: str,
    art: str,
    inhalt: str,
    an_alle: bool,
    empfaenger_ids: list[str],
    bild_url: str = "",
) -> dict:
    driver = get_driver()
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (m:Mitteilung {{
            id: $mid, campaignId: $campaign_id,
            art: $art, inhalt: $inhalt, bildUrl: $bild_url,
            anAlle: $an_alle, empfaengerIds: $empfaenger_ids,
            gelesenVon: [], erstelltAm: $jetzt
        }})
        CREATE (c)-[:HAT_MITTEILUNG]->(m)
        RETURN {_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            mid=str(uuid.uuid4()),
            art=art,
            inhalt=inhalt,
            bild_url=bild_url,
            an_alle=an_alle,
            empfaenger_ids=empfaenger_ids,
            jetzt=_jetzt(),
        )
        record = await result.single()
        return _mit_defaults(record)


async def list_mitteilungen(campaign_id: str, limit: int = NACHLADEN) -> list[dict]:
    """Neueste zuerst — beim Verbinden interessiert das Letzte, nicht das Erste."""
    driver = get_driver()
    query = f"""
        MATCH (m:Mitteilung {{campaignId: $campaign_id}})
        RETURN {_FELDER}
        ORDER BY m.erstelltAm DESC
        LIMIT $limit
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, limit=limit)
        return [_mit_defaults(r) async for r in result]


async def als_gelesen(campaign_id: str, mitteilung_id: str, person_id: str) -> bool:
    """Vermerkt gelesen für genau diese Person.

    Idempotent: Mehrfaches Abhaken darf die Liste nicht aufblähen.
    """
    driver = get_driver()
    query = """
        MATCH (m:Mitteilung {id: $mid, campaignId: $campaign_id})
        SET m.gelesenVon = CASE
            WHEN $pid IN coalesce(m.gelesenVon, []) THEN m.gelesenVon
            ELSE coalesce(m.gelesenVon, []) + $pid
        END
        RETURN m.id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, mid=mitteilung_id, pid=person_id)
        return await result.single() is not None


async def alles_gelesen(campaign_id: str, person_id: str) -> int:
    """Alle offenen Mitteilungen dieser Person abhaken."""
    driver = get_driver()
    query = """
        MATCH (m:Mitteilung {campaignId: $campaign_id})
        WHERE NOT $pid IN coalesce(m.gelesenVon, [])
          AND (m.anAlle = true OR $pid IN coalesce(m.empfaengerIds, []))
        SET m.gelesenVon = coalesce(m.gelesenVon, []) + $pid
        RETURN count(m) AS anzahl
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, pid=person_id)
        record = await result.single()
        return int(record["anzahl"]) if record else 0


async def delete_mitteilung(campaign_id: str, mitteilung_id: str) -> bool:
    """Zurückziehen: ein versehentlich gesendetes Popup wieder einsammeln."""
    driver = get_driver()
    query = """
        MATCH (m:Mitteilung {id: $mid, campaignId: $campaign_id})
        DETACH DELETE m
        RETURN count(m) AS weg
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, mid=mitteilung_id)
        record = await result.single()
        return bool(record and record["weg"])
