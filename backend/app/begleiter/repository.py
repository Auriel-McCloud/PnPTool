"""Begleiter — Sprites, Geister und alles, was jemandem zur Seite steht.

Sie teilen sich ein Blatt mit Drohnen und Fahrzeugen: `Neotopia.xlsx`, Blatt
*DrohneFahrzeug*, ist überschrieben mit **"Drohne / Fahrzeug / Sprite /
Geist"** — dieselben vier Werte, dieselben vier freien Fertigkeiten.

Trotzdem **kein Gegenstand**, anders als das Fahrzeug: einen Geist trägt man
nicht im Rucksack, er hat kein Gewicht, keinen Preis und keinen
Aufbewahrungsort. Alles, was Gegenstände an Inventarlogik mitbringen, wäre
hier sinnlos oder irreführend.

Die Werte selbst liegen in `app/traits/begleiterblatt.py`, damit Fahrzeug und
Geist nicht auseinanderlaufen.
"""

import json
import uuid

from app.db.neo4j_driver import get_driver

RETURN_FIELDS = """
    b.id AS id, b.name AS name, b.art AS art, b.beziehung AS beziehung,
    b.beschreibung AS beschreibung, b.notizen AS notizen,
    b.stufe AS stufe, b.widerstand AS widerstand, b.angriff AS angriff,
    b.agilitaet AS agilitaet, b.fertigkeiten AS fertigkeiten,
    b.waffe AS waffe, b.waffenSchaden AS waffenSchaden, b.schadensart AS schadensart,
    b.sichtbarkeit AS sichtbarkeit, b.sichtbarFuer AS sichtbarFuer,
    p.id AS besitzerId, p.name AS besitzerName
"""


def _decode(record: dict) -> dict:
    """Ausgangswerte für alles, was Bestandsdaten noch nicht kennen.

    Gleiche Vorsicht wie bei den Gegenständen (Stolperstein 9): ein fehlendes
    Pflichtfeld lässt sonst die ganze Liste mit 500 abstürzen.
    """
    daten = dict(record)
    for feld in ("name", "art", "beziehung", "beschreibung", "notizen", "waffe", "schadensart"):
        daten[feld] = daten.get(feld) or ""
    for feld in ("stufe", "widerstand", "angriff", "agilitaet", "waffenSchaden"):
        daten[feld] = daten.get(feld) or 0
    daten["art"] = daten["art"] or "BEGLEITER"
    daten["sichtbarkeit"] = daten.get("sichtbarkeit") or "GM"
    daten["sichtbarFuer"] = daten.get("sichtbarFuer") or []
    try:
        roh = daten.get("fertigkeiten")
        daten["fertigkeiten"] = json.loads(roh) if roh else {}
    except (json.JSONDecodeError, TypeError):
        daten["fertigkeiten"] = {}
    return daten


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{campaignId: $campaign_id}})
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        RETURN {RETURN_FIELDS}
        ORDER BY b.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode(r) async for r in result]


async def anlegen(campaign_id: str, besitzer_person_id: str | None, daten: dict) -> dict | None:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    erzeuge = """
        MATCH (c:Campaign {id: $campaign_id})
        CREATE (b:Begleiter {
            id: $id, campaignId: $campaign_id, name: $name, art: $art,
            beziehung: $beziehung, beschreibung: $beschreibung, notizen: $notizen,
            stufe: $stufe, widerstand: $widerstand, angriff: $angriff, agilitaet: $agilitaet,
            fertigkeiten: $fertigkeiten, waffe: $waffe, waffenSchaden: $waffenSchaden,
            schadensart: $schadensart, sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        })
        CREATE (c)-[:HAT_ENTITAET]->(b)
    """
    if besitzer_person_id:
        query = f"""
            {erzeuge}
            WITH b
            MATCH (p:Person {{id: $besitzer_id, campaignId: $campaign_id}})
            CREATE (b)-[:BEGLEITET]->(p)
            RETURN {RETURN_FIELDS}
        """
    else:
        # Ohne Person: ein Geist, den noch niemand gebunden hat.
        query = f"""
            {erzeuge}
            WITH b
            OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
            RETURN {RETURN_FIELDS}
        """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            besitzer_id=besitzer_person_id,
            id=neue_id,
            name=daten["name"],
            art=daten["art"],
            beziehung=daten["beziehung"],
            beschreibung=daten["beschreibung"],
            notizen=daten["notizen"],
            stufe=daten["stufe"],
            widerstand=daten["widerstand"],
            angriff=daten["angriff"],
            agilitaet=daten["agilitaet"],
            fertigkeiten=json.dumps(daten.get("fertigkeiten") or {}),
            waffe=daten["waffe"],
            waffenSchaden=daten["waffenSchaden"],
            schadensart=daten["schadensart"],
            sichtbarkeit=daten["sichtbarkeit"],
            sichtbarFuer=daten["sichtbarFuer"],
        )
        record = await result.single()
        return _decode(record) if record else None


async def aendern(campaign_id: str, begleiter_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if "fertigkeiten" in geaendert:
        geaendert["fertigkeiten"] = json.dumps(geaendert["fertigkeiten"])
    if not geaendert:
        return await einzeln(campaign_id, begleiter_id)

    driver = get_driver()
    setzen = ", ".join(f"b.{f} = ${f}" for f in geaendert)
    query = f"""
        MATCH (b:Begleiter {{id: $id, campaignId: $campaign_id}})
        SET {setzen}
        WITH b
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=begleiter_id, **geaendert)
        record = await result.single()
        return _decode(record) if record else None


async def einzeln(campaign_id: str, begleiter_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{id: $id, campaignId: $campaign_id}})
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=begleiter_id)
        record = await result.single()
        return _decode(record) if record else None


async def besitzer_setzen(campaign_id: str, begleiter_id: str, person_id: str | None) -> dict | None:
    """Bindet den Begleiter an eine Person — oder löst die Bindung."""
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{id: $id, campaignId: $campaign_id}})
        OPTIONAL MATCH (b)-[alt:BEGLEITET]->(:Person)
        DELETE alt
        WITH b
        OPTIONAL MATCH (neu:Person {{id: $person_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN neu IS NULL THEN [] ELSE [1] END |
            CREATE (b)-[:BEGLEITET]->(neu)
        )
        WITH b
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=begleiter_id, person_id=person_id)
        record = await result.single()
        return _decode(record) if record else None


async def loeschen(campaign_id: str, begleiter_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Begleiter {id: $id, campaignId: $campaign_id})
            DETACH DELETE b
            RETURN count(b) AS geloescht
            """,
            campaign_id=campaign_id,
            id=begleiter_id,
        )
        record = await result.single()
        return bool(record and record["geloescht"])
