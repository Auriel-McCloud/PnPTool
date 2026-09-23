"""Neo4j-Zugriff für Verhandlungen.

    (:Campaign)-[:HAT_VERHANDLUNG]->(:Verhandlung {campaignId})

Bewusst eigener Knotentyp statt Wiederverwendung von :Mitteilung — eine
Verhandlung hat einen Status (offen/angenommen/abgelehnt) und eine fachliche
Nebenwirkung bei Annahme, eine Mitteilung ist ein reines Anzeige-Popup ohne
das. Die Zustellung ans Spieler-Gerät läuft trotzdem über denselben
Live-Mechanismus (siehe app/mitteilungen/verteiler.py — hier eigens
angesprochen statt eines Imports quer über Modulgrenzen, siehe routes.py).

positionen und kontext sind Neo4j-Maps/-Listen nicht direkt speicherbar
(nur primitive Arrays) — deshalb als JSON-Text abgelegt, wie an anderer
Stelle im Projekt üblich (z.B. items/repository.py::eigenschaften).
"""

import json
import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

_FELDER = """
    v.id AS id, v.empfaengerPersonId AS empfaengerPersonId, v.art AS art,
    v.positionen AS positionen, v.gesamtbetrag AS gesamtbetrag,
    v.kontext AS kontext, v.status AS status, v.erstelltAm AS erstelltAm
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode(record) -> dict:
    v = dict(record)
    v["positionen"] = json.loads(v["positionen"]) if v.get("positionen") else []
    v["kontext"] = json.loads(v["kontext"]) if v.get("kontext") else {}
    v["status"] = v.get("status") or "OFFEN"
    v["erstelltAm"] = v.get("erstelltAm") or ""
    return v


async def create_verhandlung(
    campaign_id: str,
    empfaenger_person_id: str,
    art: str,
    positionen: list[dict],
    kontext: dict,
) -> dict:
    gesamtbetrag = sum(p["betrag"] for p in positionen)
    driver = get_driver()
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (v:Verhandlung {{
            id: $vid, campaignId: $campaign_id,
            empfaengerPersonId: $empfaenger_person_id, art: $art,
            positionen: $positionen, gesamtbetrag: $gesamtbetrag,
            kontext: $kontext, status: 'OFFEN', erstelltAm: $jetzt
        }})
        CREATE (c)-[:HAT_VERHANDLUNG]->(v)
        RETURN {_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            vid=str(uuid.uuid4()),
            empfaenger_person_id=empfaenger_person_id,
            art=art,
            positionen=json.dumps(positionen),
            gesamtbetrag=gesamtbetrag,
            kontext=json.dumps(kontext),
            jetzt=_jetzt(),
        )
        record = await result.single()
        return _decode(record)


async def get_verhandlung(campaign_id: str, verhandlung_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (v:Verhandlung {{id: $vid, campaignId: $campaign_id}})
        RETURN {_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, vid=verhandlung_id)
        record = await result.single()
        return _decode(record) if record else None


async def list_offene_fuer(campaign_id: str, person_id: str) -> list[dict]:
    """Offene Angebote an diese Person — Aufhol-Liste beim (Wieder-)Verbinden.

    Ohne das würde ein Angebot verloren gehen, das ankam, während das Gerät
    schlief (Android trennt Hintergrund-Tabs, siehe mitteilungen/api.ts) —
    anders als bei SL-Mitteilungen gibt es hier keinen "stand"-Schnappschuss
    über den WebSocket, deshalb dieser eigene Weg.
    """
    driver = get_driver()
    query = f"""
        MATCH (v:Verhandlung {{campaignId: $campaign_id, empfaengerPersonId: $person_id, status: 'OFFEN'}})
        RETURN {_FELDER}
        ORDER BY v.erstelltAm DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [_decode(r) async for r in result]


async def setze_status(campaign_id: str, verhandlung_id: str, status: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (v:Verhandlung {{id: $vid, campaignId: $campaign_id}})
        SET v.status = $status
        RETURN {_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, vid=verhandlung_id, status=status)
        record = await result.single()
        return _decode(record) if record else None


async def delete_verhandlung(campaign_id: str, verhandlung_id: str) -> bool:
    """Testdaten-Aufräumen / SL zieht ein Angebot zurück."""
    driver = get_driver()
    query = """
        MATCH (v:Verhandlung {id: $vid, campaignId: $campaign_id})
        DETACH DELETE v
        RETURN count(v) AS weg
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, vid=verhandlung_id)
        record = await result.single()
        return bool(record and record["weg"])
