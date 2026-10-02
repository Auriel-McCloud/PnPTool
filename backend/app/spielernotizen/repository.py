"""SpielerNotiz hängt am Zugang, nicht am Charakter.

(:Spieler)-[:HAT_NOTIZ]->(:SpielerNotiz {campaignId})

Damit bleiben die Notizen, wenn der Charakter wechselt. campaignId liegt
zusätzlich am Knoten, damit der Kampagnen-Export sie mitnimmt.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

FELDER = """
    n.id AS id, n.titel AS titel, n.inhalt AS inhalt,
    n.erstelltAm AS erstelltAm, n.geaendertAm AS geaendertAm
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["titel"] = daten.get("titel") or ""
    daten["inhalt"] = daten.get("inhalt") or ""
    daten["erstelltAm"] = str(daten.get("erstelltAm") or "")
    daten["geaendertAm"] = str(daten.get("geaendertAm") or "")
    return daten


async def liste(spieler_id: str, campaign_id: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (s:Spieler {{id: $spieler_id}})-[:HAT_NOTIZ]->(n:SpielerNotiz {{campaignId: $campaign_id}})
            RETURN {FELDER}
            ORDER BY n.geaendertAm DESC
            """,
            spieler_id=spieler_id,
            campaign_id=campaign_id,
        )
        return [_decode(dict(rec)) async for rec in result]


async def anlegen(spieler_id: str, campaign_id: str, daten: dict) -> dict:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    jetzt = _jetzt()
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (s:Spieler {{id: $spieler_id}})-[:GEHOERT_ZU]->(:Campaign {{id: $campaign_id}})
            CREATE (n:SpielerNotiz {{
                id: $id, campaignId: $campaign_id, titel: $titel, inhalt: $inhalt,
                erstelltAm: $jetzt, geaendertAm: $jetzt
            }})
            CREATE (s)-[:HAT_NOTIZ]->(n)
            RETURN {FELDER}
            """,
            id=neue_id,
            spieler_id=spieler_id,
            campaign_id=campaign_id,
            titel=daten["titel"],
            inhalt=daten.get("inhalt") or "",
            jetzt=jetzt,
        )
        record = await result.single()
        if record is None:
            raise RuntimeError("Spielerzugang nicht gefunden")
        return _decode(dict(record))


async def aendern(spieler_id: str, campaign_id: str, notiz_id: str, daten: dict) -> dict | None:
    setzt = ["n.geaendertAm = $jetzt"]
    params: dict = {
        "spieler_id": spieler_id,
        "campaign_id": campaign_id,
        "id": notiz_id,
        "jetzt": _jetzt(),
    }
    if daten.get("titel") is not None:
        setzt.append("n.titel = $titel")
        params["titel"] = daten["titel"]
    if daten.get("inhalt") is not None:
        setzt.append("n.inhalt = $inhalt")
        params["inhalt"] = daten["inhalt"]
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (s:Spieler {{id: $spieler_id}})-[:HAT_NOTIZ]->(n:SpielerNotiz {{id: $id, campaignId: $campaign_id}})
            SET {", ".join(setzt)}
            RETURN {FELDER}
            """,
            **params,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def loeschen(spieler_id: str, campaign_id: str, notiz_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler {id: $spieler_id})-[:HAT_NOTIZ]->(n:SpielerNotiz {id: $id, campaignId: $campaign_id})
            DETACH DELETE n
            RETURN 1 AS ok
            """,
            spieler_id=spieler_id,
            campaign_id=campaign_id,
            id=notiz_id,
        )
        return await result.single() is not None
