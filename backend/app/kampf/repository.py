"""Kampfmodus — die Initiativliste, die alle am Tisch sehen.

Ein Kampf je Kampagne. Die Reihenfolge ergibt sich aus dem Regelblatt
(Zeilen 57-59):

* **Initiative = Geistesschärfe + Geschicklichkeit + Cyberware-Modifikator.**
* Bei gleicher Initiative gilt **Matrixnutzer vor Nahkämpfer vor Fernkämpfer**.
* **Angesagt wird in umgekehrter Reihenfolge** — wer zuletzt handelt, sagt
  zuerst an; dadurch kann die schnellste Person auf alles reagieren. Gewürfelt
  wird dann in der richtigen Reihenfolge.

Die Teilnehmer sind eigene Knoten statt einer Liste am Kampf: Neo4j kann keine
Listen aus Objekten als Eigenschaft, und ein Teilnehmer verweist ohnehin auf
eine Person oder einen Begleiter.
"""

import uuid

from app.db.neo4j_driver import get_driver

# Reihenfolge bei Gleichstand (Zeile 58). Kleinere Zahl handelt zuerst.
KAMPFART_RANG = {"MATRIX": 0, "NAHKAMPF": 1, "FERNKAMPF": 2}

TEILNEHMER_FELDER = """
    t.id AS id, t.name AS name, t.initiative AS initiative, t.kampfart AS kampfart,
    t.notiz AS notiz, t.erledigt AS erledigt,
    p.id AS personId, p.personType AS personType,
    b.id AS begleiterId
"""


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["name"] = daten.get("name") or ""
    daten["initiative"] = daten.get("initiative") or 0
    daten["kampfart"] = daten.get("kampfart") or "NAHKAMPF"
    daten["notiz"] = daten.get("notiz") or ""
    daten["erledigt"] = bool(daten.get("erledigt"))
    return daten


def sortiere(teilnehmer: list[dict]) -> list[dict]:
    """Handlungsreihenfolge: hohe Initiative zuerst, dann nach Kampfart."""
    return sorted(
        teilnehmer,
        key=lambda t: (-t["initiative"], KAMPFART_RANG.get(t["kampfart"], 9), t["name"].lower()),
    )


async def hole(campaign_id: str) -> dict | None:
    """Der laufende Kampf samt Teilnehmern, oder None."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            RETURN k.id AS id, k.runde AS runde, k.amZug AS amZug, k.begonnen AS begonnen
            """,
            campaign_id=campaign_id,
        )
        kampf = await result.single()
        if kampf is None:
            return None

        result = await session.run(
            f"""
            MATCH (k:Kampf {{id: $kampf_id}})-[:KAEMPFT]->(t:KampfTeilnehmer)
            OPTIONAL MATCH (t)-[:IST]->(p:Person)
            OPTIONAL MATCH (t)-[:IST]->(b:Begleiter)
            RETURN {TEILNEHMER_FELDER}
            """,
            kampf_id=kampf["id"],
        )
        teilnehmer = sortiere([_decode(r) async for r in result])

    return {
        "id": kampf["id"],
        "runde": kampf["runde"] or 1,
        # Kennung des Teilnehmers, der gerade handelt. Kennung statt Position,
        # weil sich die Reihenfolge ändern kann (jemand kommt dazu) — eine
        # Position zeigte danach auf jemand anderen.
        "amZug": kampf["amZug"],
        "teilnehmer": teilnehmer,
    }


async def beginne(campaign_id: str) -> dict:
    """Startet einen Kampf. Ein laufender wird dabei ersetzt."""
    await beende(campaign_id)
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            CREATE (k:Kampf {id: $id, campaignId: $campaign_id, runde: 1, amZug: null})
            CREATE (c)-[:HAT_KAMPF]->(k)
            """,
            campaign_id=campaign_id,
            id=str(uuid.uuid4()),
        )
    return await hole(campaign_id)


async def beende(campaign_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            OPTIONAL MATCH (k)-[:KAEMPFT]->(t:KampfTeilnehmer)
            DETACH DELETE k, t
            RETURN count(k) AS weg
            """,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def teilnehmer_hinzu(campaign_id: str, daten: dict) -> dict | None:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    # Verweis auf Person oder Begleiter, je nachdem was mitkommt. Beides
    # optional: ein namenloser Wachmann braucht keinen Knoten dahinter.
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            CREATE (t:KampfTeilnehmer {
                id: $id, name: $name, initiative: $initiative,
                kampfart: $kampfart, notiz: $notiz, erledigt: false
            })
            CREATE (k)-[:KAEMPFT]->(t)
            WITH t
            OPTIONAL MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END | CREATE (t)-[:IST]->(p))
            WITH t
            OPTIONAL MATCH (b:Begleiter {id: $begleiter_id, campaignId: $campaign_id})
            FOREACH (_ IN CASE WHEN b IS NULL THEN [] ELSE [1] END | CREATE (t)-[:IST]->(b))
            """,
            campaign_id=campaign_id,
            id=neue_id,
            name=daten["name"],
            initiative=daten["initiative"],
            kampfart=daten["kampfart"],
            notiz=daten.get("notiz") or "",
            person_id=daten.get("personId"),
            begleiter_id=daten.get("begleiterId"),
        )
    return await hole(campaign_id)


async def teilnehmer_aendern(campaign_id: str, teilnehmer_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if not geaendert:
        return await hole(campaign_id)
    driver = get_driver()
    setzen = ", ".join(f"t.{f} = ${f}" for f in geaendert)
    async with driver.session() as session:
        await session.run(
            f"""
            MATCH (:Kampf {{campaignId: $campaign_id}})-[:KAEMPFT]->(t:KampfTeilnehmer {{id: $id}})
            SET {setzen}
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
            **geaendert,
        )
    return await hole(campaign_id)


async def teilnehmer_entfernen(campaign_id: str, teilnehmer_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
            DETACH DELETE t
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
        )
    return await hole(campaign_id)


async def setze_am_zug(campaign_id: str, teilnehmer_id: str | None, runde: int | None = None) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            SET k.amZug = $am_zug
            FOREACH (_ IN CASE WHEN $runde IS NULL THEN [] ELSE [1] END | SET k.runde = $runde)
            """,
            campaign_id=campaign_id,
            am_zug=teilnehmer_id,
            runde=runde,
        )
    return await hole(campaign_id)


async def weiter(campaign_id: str) -> dict | None:
    """Einen Zug weiterrücken; am Ende der Liste beginnt die nächste Runde."""
    kampf = await hole(campaign_id)
    if kampf is None or not kampf["teilnehmer"]:
        return kampf

    reihenfolge = [t["id"] for t in kampf["teilnehmer"]]
    if kampf["amZug"] not in reihenfolge:
        # Kampfbeginn oder der bisher Handelnde ist ausgeschieden
        return await setze_am_zug(campaign_id, reihenfolge[0])

    naechster = reihenfolge.index(kampf["amZug"]) + 1
    if naechster < len(reihenfolge):
        return await setze_am_zug(campaign_id, reihenfolge[naechster])
    return await setze_am_zug(campaign_id, reihenfolge[0], runde=kampf["runde"] + 1)
