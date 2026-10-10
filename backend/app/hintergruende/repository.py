"""Hintergründe: campaign-gebundener narrativer Katalog.

Wie Zusatzfertigkeiten: kein Freigabe-Schalter, sofort wählbar.
Mentor/Kontakte liegen NICHT hier — eigene Kanten, siehe seed.SYSTEM_SCHLUESSEL.
"""

import uuid

from app.db.neo4j_driver import get_driver
from app.hintergruende.seed import NARRATIVE_SEED

FELDER = """
    h.id AS id, h.campaignId AS campaignId, h.name AS name,
    h.kurzbeschreibung AS kurzbeschreibung, h.detailbeschreibung AS detailbeschreibung
"""


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["name"] = daten.get("name") or ""
    daten["kurzbeschreibung"] = daten.get("kurzbeschreibung") or ""
    daten["detailbeschreibung"] = daten.get("detailbeschreibung") or ""
    return daten


async def liste(campaign_id: str) -> list[dict]:
    await seed_wenn_leer(campaign_id)
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (h:Hintergrund {{campaignId: $campaign_id}}) RETURN {FELDER} ORDER BY h.name",
            campaign_id=campaign_id,
        )
        return [_decode(dict(rec)) async for rec in result]


async def seed_wenn_leer(campaign_id: str) -> None:
    """Befüllt den Katalog einmal, wenn noch kein Eintrag existiert.

    Einzelne Löschungen bleiben. Nur ein komplett leerer Katalog wird
    neu gesät (wer alle acht löscht, bekommt sie zurück).
    """
    driver = get_driver()
    async with driver.session() as session:
        count = await session.run(
            "MATCH (h:Hintergrund {campaignId: $campaign_id}) RETURN count(h) AS n",
            campaign_id=campaign_id,
        )
        rec = await count.single()
        if rec and int(rec["n"]) > 0:
            return
        for eintrag in NARRATIVE_SEED:
            await session.run(
                f"""
                MATCH (c:Campaign {{id: $campaign_id}})
                CREATE (h:Hintergrund {{
                    id: $id, campaignId: $campaign_id, name: $name,
                    kurzbeschreibung: $kurzbeschreibung, detailbeschreibung: $detailbeschreibung
                }})
                CREATE (c)-[:HAT_ENTITAET]->(h)
                """,
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                name=eintrag["name"],
                kurzbeschreibung=eintrag["kurzbeschreibung"],
                detailbeschreibung=eintrag["detailbeschreibung"],
            )


async def hole(campaign_id: str, hintergrund_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (h:Hintergrund {{id: $id, campaignId: $campaign_id}}) RETURN {FELDER}",
            id=hintergrund_id,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def anlegen(campaign_id: str, daten: dict) -> dict:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (c:Campaign {{id: $campaign_id}})
            CREATE (h:Hintergrund {{
                id: $id, campaignId: $campaign_id, name: $name,
                kurzbeschreibung: $kurzbeschreibung, detailbeschreibung: $detailbeschreibung
            }})
            CREATE (c)-[:HAT_ENTITAET]->(h)
            RETURN {FELDER}
            """,
            id=neue_id,
            campaign_id=campaign_id,
            name=daten["name"],
            kurzbeschreibung=daten.get("kurzbeschreibung") or "",
            detailbeschreibung=daten.get("detailbeschreibung") or "",
        )
        record = await result.single()
        return _decode(dict(record))


async def aendern(campaign_id: str, hintergrund_id: str, daten: dict) -> dict | None:
    aenderung = {k: v for k, v in daten.items() if v is not None}
    if not aenderung:
        return await hole(campaign_id, hintergrund_id)
    setzen = ", ".join(f"h.{k} = ${k}" for k in aenderung)
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (h:Hintergrund {{id: $id, campaignId: $campaign_id}}) SET {setzen} RETURN {FELDER}",
            id=hintergrund_id,
            campaign_id=campaign_id,
            **aenderung,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def loeschen(campaign_id: str, hintergrund_id: str) -> bool:
    """Katalogeintrag samt HAT_HINTERGRUND-Kanten. Wie Zusatzfertigkeiten."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (h:Hintergrund {id: $id, campaignId: $campaign_id}) DETACH DELETE h RETURN count(h) AS weg",
            id=hintergrund_id,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def hintergruende_der_person(campaign_id: str, person_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[r:HAT_HINTERGRUND]->(h:Hintergrund)
        RETURN h.id AS id, h.name AS name, h.kurzbeschreibung AS kurzbeschreibung,
               h.detailbeschreibung AS detailbeschreibung, r.rating AS rating
        ORDER BY h.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [_decode(dict(rec)) | {"rating": int(dict(rec)["rating"] or 0)} async for rec in result]


async def setze_rating(campaign_id: str, person_id: str, hintergrund_id: str, rating: int) -> dict | None:
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
        MATCH (h:Hintergrund {id: $hid, campaignId: $campaign_id})
        MERGE (p)-[r:HAT_HINTERGRUND]->(h)
        SET r.rating = $rating
        RETURN h.id AS id, h.name AS name, h.kurzbeschreibung AS kurzbeschreibung,
               h.detailbeschreibung AS detailbeschreibung, r.rating AS rating
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, hid=hintergrund_id, rating=rating
        )
        record = await result.single()
        if record is None:
            return None
        daten = _decode(dict(record))
        daten["rating"] = int(record["rating"])
        return daten


async def hole_kredithai(campaign_id: str, person_id: str) -> dict | None:
    """HAT_KREDITHAI des PCs, sonst None."""
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[r:HAT_KREDITHAI]->(h:Person)
        RETURN h.id AS haiId, r.rating AS rating, h.name AS name, h.istEntwurf AS istEntwurf
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        return dict(record) if record else None


async def setze_kredithai(campaign_id: str, person_id: str, hai_id: str, rating: int) -> None:
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
        MATCH (h:Person {id: $hai_id, campaignId: $campaign_id})
        MERGE (p)-[r:HAT_KREDITHAI]->(h)
        SET r.rating = $rating
    """
    async with driver.session() as session:
        await session.run(
            query,
            campaign_id=campaign_id,
            person_id=person_id,
            hai_id=hai_id,
            rating=int(rating),
        )


async def setze_schuldet_verbindung(
    campaign_id: str, person_id: str, hai_id: str, beschreibung: str
) -> None:
    """Eine Schuldet-Kante, Beschreibung bei Korrektur überschreiben."""
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
        MATCH (h:Person {id: $hai_id, campaignId: $campaign_id})
        MERGE (p)-[r:VERBINDUNG {typ: "Schuldet"}]->(h)
        ON CREATE SET
            r.id = $edge_id,
            r.seit = "",
            r.bis = "",
            r.sichtbarkeit = "GM",
            r.sichtbarFuer = []
        SET r.beschreibung = $beschreibung
    """
    async with driver.session() as session:
        await session.run(
            query,
            campaign_id=campaign_id,
            person_id=person_id,
            hai_id=hai_id,
            beschreibung=beschreibung,
            edge_id=str(uuid.uuid4()),
        )
