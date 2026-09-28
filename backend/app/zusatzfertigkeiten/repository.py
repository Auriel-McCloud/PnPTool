"""Zusatzfertigkeiten: campaign-gebundener Katalog (kein globaler Katalog +
Freigabe wie bei Rassen).

Mark, 28.09.2026, wörtlich: "im Kampagnen Menü eine einfache Tabelle machen
in der man Skills eintragen kann, nach dem diese ja grundsätzlich keine
Mechanik mit sich bringen müsste man nur einen Namen eine Kurz und Detail
Beschreibung hinzufügen können." Anders als bei Rassen gibt es deshalb
**keinen** globalen Ruleset-Katalog mit Freigabe-Kante — jede Zusatzfertigkeit
gehört direkt einer Kampagne (`campaignId`-Property, wie die meisten anderen
Entitäten, siehe docs/wiki/entities/neo4j-datenmodell.md) und ist sofort für
Spieler dieser Kampagne wählbar.

`(:Person)-[:HAT_ZUSATZFERTIGKEIT {rating: int}]->(:Zusatzfertigkeit)` ist
eine EIGENE Relation, nicht `HAS_TRAIT` — Zusatzfertigkeiten laufen nicht
über den TraitDef-Katalog (der ist ruleset-weit, nicht campaign-gebunden).
"""

import uuid

from app.db.neo4j_driver import get_driver

FELDER = """
    z.id AS id, z.campaignId AS campaignId, z.name AS name,
    z.kurzbeschreibung AS kurzbeschreibung, z.detailbeschreibung AS detailbeschreibung
"""


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["name"] = daten.get("name") or ""
    daten["kurzbeschreibung"] = daten.get("kurzbeschreibung") or ""
    daten["detailbeschreibung"] = daten.get("detailbeschreibung") or ""
    return daten


async def liste(campaign_id: str) -> list[dict]:
    """Der ganze Katalog dieser Kampagne — für SL-Tabelle UND Spieler-Popup."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (z:Zusatzfertigkeit {{campaignId: $campaign_id}}) RETURN {FELDER} ORDER BY z.name",
            campaign_id=campaign_id,
        )
        return [_decode(dict(rec)) async for rec in result]


async def hole(campaign_id: str, zusatzfertigkeit_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (z:Zusatzfertigkeit {{id: $id, campaignId: $campaign_id}}) RETURN {FELDER}",
            id=zusatzfertigkeit_id,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def anlegen(campaign_id: str, daten: dict) -> dict:
    """Neuer Katalogeintrag — sofort in dieser Kampagne wählbar.

    Kein zweiter Freigabe-Schritt wie bei Rassen: die Tabelle IST schon
    die Freigabe (Marks Vorgabe, siehe Modul-Docstring).
    """
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (c:Campaign {{id: $campaign_id}})
            CREATE (z:Zusatzfertigkeit {{
                id: $id, campaignId: $campaign_id, name: $name,
                kurzbeschreibung: $kurzbeschreibung, detailbeschreibung: $detailbeschreibung
            }})
            CREATE (c)-[:HAT_ENTITAET]->(z)
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


async def aendern(campaign_id: str, zusatzfertigkeit_id: str, daten: dict) -> dict | None:
    """Ändert Name/Beschreibung. Die Relation zu Personen trägt keinen
    eigenen Namenstext (anders als bei Rassen `Person.rasse`) — eine
    Umbenennung muss deshalb nirgendwo nachgezogen werden, das
    Charakterblatt liest den Namen live über die Kante."""
    aenderung = {k: v for k, v in daten.items() if v is not None}
    if not aenderung:
        return await hole(campaign_id, zusatzfertigkeit_id)

    setzen = ", ".join(f"z.{k} = ${k}" for k in aenderung)
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (z:Zusatzfertigkeit {{id: $id, campaignId: $campaign_id}}) SET {setzen} RETURN {FELDER}",
            id=zusatzfertigkeit_id,
            campaign_id=campaign_id,
            **aenderung,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def loeschen(campaign_id: str, zusatzfertigkeit_id: str) -> bool:
    """Löscht einen Katalogeintrag **samt der Kanten zu Personen**, die ihn
    gewählt haben (hartes DETACH DELETE, kein Papierkorb).

    Bewusst anders als bei Rassen (dort bleibt `Person.rasse` als reiner
    Text stehen, weil er losgelöst vom Katalogknoten existiert): eine
    Zusatzfertigkeit hat KEIN eigenes Textfeld am Charakter, sie IST die
    Kante `HAT_ZUSATZFERTIGKEIT` zum Katalogknoten. Bliebe der Knoten weg
    aber die Kante bestehen, zeigte das Charakterblatt eine kaputte
    Referenz ins Leere. Da Zusatzfertigkeiten ohnehin reiner Name +
    Beschreibung ohne Mechanik sind (Marks Vorgabe), ist der Verlust eines
    gewählten Eintrags beim Löschen im Katalog hinnehmbar — die SL entfernt
    damit bewusst etwas, das in dieser Kampagne nicht mehr existieren soll.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (z:Zusatzfertigkeit {id: $id, campaignId: $campaign_id}) DETACH DELETE z RETURN count(z) AS weg",
            id=zusatzfertigkeit_id,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def zusatzfertigkeiten_der_person(campaign_id: str, person_id: str) -> list[dict]:
    """Gewählte Zusatzfertigkeiten samt Stufe — für Charakterblatt/Bogen."""
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[r:HAT_ZUSATZFERTIGKEIT]->(z:Zusatzfertigkeit)
        RETURN z.id AS id, z.name AS name, z.kurzbeschreibung AS kurzbeschreibung,
               z.detailbeschreibung AS detailbeschreibung, r.rating AS rating
        ORDER BY z.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [_decode(dict(rec)) | {"rating": int(dict(rec)["rating"])} async for rec in result]


async def gewaehlte_ids(campaign_id: str, person_id: str) -> set[str]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (:Person {id: $person_id, campaignId: $campaign_id})-[:HAT_ZUSATZFERTIGKEIT]->(z:Zusatzfertigkeit) RETURN z.id AS id",
            campaign_id=campaign_id,
            person_id=person_id,
        )
        return {rec["id"] async for rec in result}


async def hinzufuegen(campaign_id: str, person_id: str, zusatzfertigkeit_id: str, rating: int = 1) -> dict | None:
    """Legt eine noch nicht gewählte Zusatzfertigkeit mit `rating` an.

    `MERGE` statt `CREATE`: ein zweiter Aufruf mit derselben Kombination
    überschreibt die Stufe statt eine zweite Kante danebenzulegen — die
    Route prüft zusätzlich vorher, ob die Person sie schon hat.
    """
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
        MATCH (z:Zusatzfertigkeit {id: $zid, campaignId: $campaign_id})
        MERGE (p)-[r:HAT_ZUSATZFERTIGKEIT]->(z)
        SET r.rating = $rating
        RETURN z.id AS id, z.name AS name, z.kurzbeschreibung AS kurzbeschreibung,
               z.detailbeschreibung AS detailbeschreibung, r.rating AS rating
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, zid=zusatzfertigkeit_id, rating=rating
        )
        record = await result.single()
        if record is None:
            return None
        daten = _decode(dict(record))
        daten["rating"] = int(record["rating"])
        return daten


async def steigere(campaign_id: str, person_id: str, zusatzfertigkeit_id: str, neuer_wert: int) -> dict | None:
    """Hebt die Stufe einer bereits gewählten Zusatzfertigkeit an."""
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[r:HAT_ZUSATZFERTIGKEIT]->(z:Zusatzfertigkeit {id: $zid})
        SET r.rating = $rating
        RETURN z.id AS id, z.name AS name, z.kurzbeschreibung AS kurzbeschreibung,
               z.detailbeschreibung AS detailbeschreibung, r.rating AS rating
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, zid=zusatzfertigkeit_id, rating=neuer_wert
        )
        record = await result.single()
        if record is None:
            return None
        daten = _decode(dict(record))
        daten["rating"] = int(record["rating"])
        return daten
