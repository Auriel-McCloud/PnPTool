"""SL-Beratungschat in der Ideenschmiede.

Knoten `KiBeratung` / `KiBeratungNachricht` sind bewusst eigene Labels —
`sammle_kontext` matcht nur Person/Ort/Event/Fraktion/Gegenstand/WikiSeite,
dieser Chat landet also nie im Kanon, auch nicht als Entwurf. Verwerfen =
nicht freigeben; der nächste Chat sieht die Spinnereien nicht.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

_MAX_TURNS_ANS_MODELL = 30


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _titel_aus(text: str) -> str:
    zeile = " ".join((text or "").strip().split())
    if len(zeile) <= 48:
        return zeile or "Neue Beratung"
    return zeile[:47].rstrip() + "…"


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})-[:HAT_BERATUNG]->(b:KiBeratung)
            RETURN b.id AS id, b.titel AS titel,
                   b.erstelltAm AS erstelltAm, b.aktualisiertAm AS aktualisiertAm
            ORDER BY b.aktualisiertAm DESC
            """,
            campaign_id=campaign_id,
        )
        return [dict(r) async for r in result]


async def anlegen(campaign_id: str) -> dict | None:
    driver = get_driver()
    jetzt = _jetzt()
    beratung_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            CREATE (b:KiBeratung {
                id: $id, campaignId: $campaign_id,
                titel: 'Neue Beratung',
                erstelltAm: $jetzt, aktualisiertAm: $jetzt
            })
            CREATE (c)-[:HAT_BERATUNG]->(b)
            RETURN b.id AS id, b.titel AS titel,
                   b.erstelltAm AS erstelltAm, b.aktualisiertAm AS aktualisiertAm
            """,
            campaign_id=campaign_id,
            id=beratung_id,
            jetzt=jetzt,
        )
        record = await result.single()
        if record is None:
            return None
        daten = dict(record)
        daten["nachrichten"] = []
        return daten


async def laden(campaign_id: str, beratung_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        kopf = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})-[:HAT_BERATUNG]->(b:KiBeratung {id: $id})
            RETURN b.id AS id, b.titel AS titel,
                   b.erstelltAm AS erstelltAm, b.aktualisiertAm AS aktualisiertAm
            """,
            campaign_id=campaign_id,
            id=beratung_id,
        )
        record = await kopf.single()
        if record is None:
            return None
        daten = dict(record)
        nachrichten = await session.run(
            """
            MATCH (b:KiBeratung {id: $id, campaignId: $campaign_id})-[:ENTHAELT]->(m:KiBeratungNachricht)
            RETURN m.id AS id, m.rolle AS rolle, m.text AS text,
                   m.zeitpunkt AS zeitpunkt, m.reihenfolge AS reihenfolge
            ORDER BY m.reihenfolge
            """,
            campaign_id=campaign_id,
            id=beratung_id,
        )
        daten["nachrichten"] = [dict(r) async for r in nachrichten]
        return daten


async def nachricht_anhaengen(
    campaign_id: str,
    beratung_id: str,
    rolle: str,
    text: str,
) -> dict | None:
    """Hängt eine Nachricht an. Setzt den Titel beim ersten User-Turn."""
    driver = get_driver()
    jetzt = _jetzt()
    nachricht_id = str(uuid.uuid4())
    async with driver.session() as session:
        existiert = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})-[:HAT_BERATUNG]->(b:KiBeratung {id: $id})
            OPTIONAL MATCH (b)-[:ENTHAELT]->(alt:KiBeratungNachricht)
            RETURN b.titel AS titel, count(alt) AS anzahl
            """,
            campaign_id=campaign_id,
            id=beratung_id,
        )
        stand = await existiert.single()
        if stand is None:
            return None
        reihenfolge = int(stand["anzahl"])
        titel = stand["titel"]
        if rolle == "user" and reihenfolge == 0:
            titel = _titel_aus(text)
        await session.run(
            """
            MATCH (b:KiBeratung {id: $id, campaignId: $campaign_id})
            CREATE (m:KiBeratungNachricht {
                id: $mid, rolle: $rolle, text: $text,
                zeitpunkt: $jetzt, reihenfolge: $reihenfolge
            })
            CREATE (b)-[:ENTHAELT]->(m)
            SET b.aktualisiertAm = $jetzt, b.titel = $titel
            """,
            campaign_id=campaign_id,
            id=beratung_id,
            mid=nachricht_id,
            rolle=rolle,
            text=text,
            jetzt=jetzt,
            reihenfolge=reihenfolge,
            titel=titel,
        )
        return {
            "id": nachricht_id,
            "rolle": rolle,
            "text": text,
            "zeitpunkt": jetzt,
            "reihenfolge": reihenfolge,
        }


async def loeschen(campaign_id: str, beratung_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})-[:HAT_BERATUNG]->(b:KiBeratung {id: $id})
            OPTIONAL MATCH (b)-[:ENTHAELT]->(m:KiBeratungNachricht)
            DETACH DELETE m, b
            RETURN 1 AS n
            """,
            campaign_id=campaign_id,
            id=beratung_id,
        )
        record = await result.single()
        return record is not None


def fuer_modell(nachrichten: list[dict]) -> list[dict]:
    """Letzte N Turns, nur rolle+text — das sieht der Provider."""
    gekuerzt = nachrichten[-_MAX_TURNS_ANS_MODELL:]
    return [{"rolle": n["rolle"], "text": n["text"]} for n in gekuerzt]


def gespraech_als_prompt(nachrichten: list[dict]) -> str:
    """Gesprächsverlauf als Auftrag für den bestehenden Ideen-Generator."""
    zeilen = []
    for n in nachrichten:
        wer = "Spielleitung" if n["rolle"] == "user" else "Beratung"
        zeilen.append(f"{wer}: {n['text']}")
    return (
        "Aus dem folgenden Beratungsgespräch soll ein Entwurf entstehen. "
        "Setze nur um, was die Spielleitung als Richtung bestätigt oder "
        "offen stehen gelassen hat. Verworfene Ideen weglassen.\n\n"
        + "\n\n".join(zeilen)
    )
