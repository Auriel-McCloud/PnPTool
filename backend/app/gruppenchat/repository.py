"""Neo4j-Zugriff für Gruppenchats.

    (:Gruppenchat {id, campaignId, name, offen})-[:TEILNEHMER {gelesenBis}]->(:Person)
    (:Nachricht)-[:VON]->(:Person)
    (:Nachricht)-[:IN]->(:Gruppenchat)

Gruppennachrichten haben **kein** `AN` — so tauchen sie in keiner der
Einzelchat-Abfragen (`kontakte/repository.py`, alle über `VON` + `AN`) auf.
`gelesenBis` ist ein ISO-Zeitstempel je Teilnehmer: ein einzelnes
„gelesen“-Häkchen an der Nachricht reicht bei mehreren Empfängern nicht.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver
from app.kontakte.logic import normalisiere_nachrichteninhalt

_TEILNEHMER = """
    collect(CASE WHEN p IS NULL THEN null ELSE {
        id: p.id, name: p.name, personType: coalesce(p.personType, 'NPC'),
        bildUrl: coalesce(p.bildUrl, ''), alias: coalesce(p.alias, ''),
        rasse: coalesce(p.rasse, '')
    } END) AS teilnehmer
"""


# Zeitpunkt der neuesten Nachricht der Gruppe ('' ohne Nachrichten). Als Pattern-Comprehension
# vor der Aggregation, damit die Teilnehmerliste nicht je Nachricht vervielfacht wird.
_LETZTE = """reduce(m = '', t IN [(n:Nachricht)-[:IN]->(g) | n.erstelltAm] |
        CASE WHEN t > m THEN t ELSE m END)"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


async def liste_fuer_gm(campaign_id: str) -> list[dict]:
    """Alle Gruppen der Kampagne, offene und geschlossene."""
    driver = get_driver()
    query = f"""
        MATCH (g:Gruppenchat {{campaignId: $campaign_id}})
        WITH g, {_LETZTE} AS letzte
        OPTIONAL MATCH (g)-[:TEILNEHMER]->(p:Person)
        RETURN g.id AS id, g.name AS name, coalesce(g.offen, true) AS offen,
               g.erstelltAm AS erstelltAm, 0 AS ungelesen,
               coalesce(nullif(letzte, ''), g.erstelltAm) AS letzteAktivitaet, {_TEILNEHMER}
        ORDER BY erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def liste_fuer_person(campaign_id: str, person_id: str) -> list[dict]:
    """Die offenen Gruppen eines Charakters, mit Zähler ungelesener Nachrichten."""
    driver = get_driver()
    query = f"""
        MATCH (g:Gruppenchat {{campaignId: $campaign_id}})-[mein:TEILNEHMER]->(:Person {{id: $person_id}})
        WHERE coalesce(g.offen, true)
        OPTIONAL MATCH (n:Nachricht {{campaignId: $campaign_id}})-[:IN]->(g)
        WHERE n.erstelltAm > coalesce(mein.gelesenBis, '')
          AND NOT (n)-[:VON]->(:Person {{id: $person_id}})
        WITH g, count(n) AS ungelesen
        WITH g, ungelesen, {_LETZTE} AS letzte
        OPTIONAL MATCH (g)-[:TEILNEHMER]->(p:Person)
        RETURN g.id AS id, g.name AS name, coalesce(g.offen, true) AS offen,
               g.erstelltAm AS erstelltAm, ungelesen,
               coalesce(nullif(letzte, ''), g.erstelltAm) AS letzteAktivitaet, {_TEILNEHMER}
        ORDER BY erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


async def hole(campaign_id: str, gruppe_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (g:Gruppenchat {{id: $gruppe_id, campaignId: $campaign_id}})
        WITH g, {_LETZTE} AS letzte
        OPTIONAL MATCH (g)-[:TEILNEHMER]->(p:Person)
        RETURN g.id AS id, g.name AS name, coalesce(g.offen, true) AS offen,
               0 AS ungelesen,
               coalesce(nullif(letzte, ''), g.erstelltAm) AS letzteAktivitaet, {_TEILNEHMER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, gruppe_id=gruppe_id)
        record = await result.single()
        return dict(record) if record else None


async def anlegen(campaign_id: str, name: str) -> str:
    """Legt eine leere Gruppe an. Mitglieder kommen über `teilnehmer_hinzu`."""
    gruppe_id = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (g:Gruppenchat {
                id: $id, campaignId: $campaign_id, name: $name,
                offen: true, erstelltAm: $jetzt
            })
            """,
            id=gruppe_id,
            campaign_id=campaign_id,
            name=name,
            jetzt=_jetzt(),
        )
    return gruppe_id


async def aendern(campaign_id: str, gruppe_id: str, name: str | None, offen: bool | None) -> bool:
    felder = {k: v for k, v in (("name", name), ("offen", offen)) if v is not None}
    if not felder:
        return await hole(campaign_id, gruppe_id) is not None
    setzen = ", ".join(f"g.{f} = ${f}" for f in felder)
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (g:Gruppenchat {{id: $gruppe_id, campaignId: $campaign_id}})
            SET {setzen}
            RETURN g.id AS id
            """,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
            **felder,
        )
        return await result.single() is not None


async def loeschen(campaign_id: str, gruppe_id: str) -> bool:
    """Löscht die Gruppe samt ihren Nachrichten."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (g:Gruppenchat {id: $gruppe_id, campaignId: $campaign_id})
            OPTIONAL MATCH (n:Nachricht)-[:IN]->(g)
            WITH g, collect(n) AS nachrichten
            FOREACH (n IN nachrichten | DETACH DELETE n)
            DETACH DELETE g
            RETURN 1 AS weg
            """,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
        )
        return await result.single() is not None


async def teilnehmer_hinzu(campaign_id: str, gruppe_id: str, person_id: str) -> bool:
    """Nimmt eine Person auf. `gelesenBis` = Beitrittszeit: die alte Historie
    ist lesbar, zählt aber nicht als ungelesen. Ein Mitglied bleibt unverändert."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (g:Gruppenchat {id: $gruppe_id, campaignId: $campaign_id})
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            WHERE p.personType IN ['PC', 'NPC']
            MERGE (g)-[t:TEILNEHMER]->(p)
            ON CREATE SET t.gelesenBis = $jetzt, t.beigetretenAm = $jetzt
            RETURN p.id AS id
            """,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
            person_id=person_id,
            jetzt=_jetzt(),
        )
        return await result.single() is not None


async def teilnehmer_entfernen(campaign_id: str, gruppe_id: str, person_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (:Gruppenchat {id: $gruppe_id, campaignId: $campaign_id})
                  -[t:TEILNEHMER]->(:Person {id: $person_id})
            DELETE t
            RETURN count(t) AS weg
            """,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def ist_teilnehmer(campaign_id: str, gruppe_id: str, person_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (:Gruppenchat {id: $gruppe_id, campaignId: $campaign_id})
                  -[t:TEILNEHMER]->(:Person {id: $person_id})
            RETURN count(t) AS anzahl
            """,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
        return bool(record and record["anzahl"])


async def nachrichten(campaign_id: str, gruppe_id: str) -> list[dict]:
    """Der Verlauf, älteste zuerst — mit allem, was die Anzeige vom Absender braucht."""
    driver = get_driver()
    query = """
        MATCH (n:Nachricht {campaignId: $campaign_id})-[:IN]->(:Gruppenchat {id: $gruppe_id})
        MATCH (n)-[:VON]->(von:Person)
        RETURN n.id AS id, n.inhalt AS inhalt, n.erstelltAm AS erstelltAm,
               n.erstelltVonRolle AS rolle,
               von.id AS vonId, von.name AS vonName,
               coalesce(von.personType, 'NPC') AS vonTyp,
               coalesce(von.bildUrl, '') AS vonBildUrl,
               coalesce(von.alias, '') AS vonAlias, coalesce(von.rasse, '') AS vonRasse
        ORDER BY n.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, gruppe_id=gruppe_id)
        return [dict(r) async for r in result]


async def sende(campaign_id: str, gruppe_id: str, von_id: str, inhalt: str, rolle: str) -> dict:
    """Legt eine Nachricht an. Nachrichten sind unveränderlich."""
    driver = get_driver()
    query = """
        MATCH (g:Gruppenchat {id: $gruppe_id, campaignId: $campaign_id})
        MATCH (von:Person {id: $von_id, campaignId: $campaign_id})
        CREATE (n:Nachricht {
            id: $id, campaignId: $campaign_id, inhalt: $inhalt,
            inhaltFormat: 'tiptap-json', erstelltAm: $jetzt,
            gelesenAm: null, erstelltVonRolle: $rolle
        })
        CREATE (n)-[:VON]->(von)
        CREATE (n)-[:IN]->(g)
        RETURN n.id AS id, n.inhalt AS inhalt, n.erstelltAm AS erstelltAm,
               von.id AS vonId, von.name AS vonName,
               coalesce(von.personType, 'NPC') AS vonTyp,
               coalesce(von.bildUrl, '') AS vonBildUrl,
               coalesce(von.alias, '') AS vonAlias, coalesce(von.rasse, '') AS vonRasse
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
            von_id=von_id,
            id=str(uuid.uuid4()),
            inhalt=normalisiere_nachrichteninhalt(inhalt),
            jetzt=_jetzt(),
            rolle=rolle,
        )
        record = await result.single()
        return dict(record) if record else {}


async def markiere_gelesen(campaign_id: str, gruppe_id: str, person_id: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Gruppenchat {id: $gruppe_id, campaignId: $campaign_id})
                  -[t:TEILNEHMER]->(:Person {id: $person_id})
            SET t.gelesenBis = $jetzt
            """,
            gruppe_id=gruppe_id,
            campaign_id=campaign_id,
            person_id=person_id,
            jetzt=_jetzt(),
        )


async def persoenliche_aliase(campaign_id: str, pc_id: str, person_ids: list[str]) -> dict[str, str]:
    """Die eigenen Alias-Namen eines Spielers für andere Personen (KENNT-Kante)."""
    if not person_ids:
        return {}
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (:Person {id: $pc_id, campaignId: $campaign_id})-[r:KENNT]->(p:Person)
            WHERE p.id IN $ids
            RETURN p.id AS id, coalesce(r.alias, '') AS alias
            """,
            pc_id=pc_id,
            campaign_id=campaign_id,
            ids=person_ids,
        )
        return {r["id"]: r["alias"] async for r in result}
