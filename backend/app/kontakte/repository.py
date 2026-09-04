"""Neo4j-Zugriff für Kontakte und Nachrichten.

Modell nach `docs/phase-5-messenger.md`:

    (:Person {personType:"PC"})-[:KENNT {...}]->(:Person {personType:"NPC"})
    (:Nachricht)-[:VON]->(:Person)
    (:Nachricht)-[:AN]->(:Person)

**Eine kanonische Richtung** (PC → NPC). "Beidseitig" beschreibt nur die
Berechtigung, im selben Chat in beide Richtungen zu schreiben — keine zweite
Kante.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver
from app.kontakte.logic import normalisiere_nachrichteninhalt

# Felder der KENNT-Kante plus das, was die Anzeige vom NPC braucht.
KONTAKT_FELDER = """
    r.id AS id, r.stufe AS stufe, r.echterNameBekannt AS echterNameBekannt,
    r.kontaktAnfrageStatus AS kontaktAnfrageStatus,
    r.alias AS persoenlicherAlias, r.persoenlicheNotizen AS persoenlicheNotizen,
    pc.id AS pcId, pc.name AS pcName,
    npc.id AS npcId, npc.name AS npcName, npc.alias AS npcAlias,
    npc.rasse AS npcRasse, npc.bildUrl AS npcBildUrl, npc.description AS npcDescription
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


async def liste_fuer_pc(campaign_id: str, pc_id: str) -> list[dict]:
    """Alle Kontakte eines Spielercharakters, mit Zähler ungelesener Post."""
    driver = get_driver()
    query = f"""
        MATCH (pc:Person {{id: $pc_id, campaignId: $campaign_id}})-[r:KENNT]->(npc:Person)
        OPTIONAL MATCH (n:Nachricht {{campaignId: $campaign_id}})-[:VON]->(npc)
        WHERE (n)-[:AN]->(pc) AND n.gelesenAm IS NULL
        RETURN {KONTAKT_FELDER}, count(n) AS ungelesen
        ORDER BY coalesce(r.alias, npc.alias, npc.name)
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, pc_id=pc_id)
        return [dict(r) async for r in result]


async def liste_fuer_gm(campaign_id: str) -> list[dict]:
    """Alle Kontaktbeziehungen der Kampagne — wer kennt wen."""
    driver = get_driver()
    query = f"""
        MATCH (pc:Person {{campaignId: $campaign_id, personType: 'PC'}})-[r:KENNT]->(npc:Person)
        RETURN {KONTAKT_FELDER}, 0 AS ungelesen
        ORDER BY pc.name, coalesce(r.alias, npc.alias, npc.name)
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def hole(campaign_id: str, kontakt_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (pc:Person {{campaignId: $campaign_id}})-[r:KENNT {{id: $kontakt_id}}]->(npc:Person)
        RETURN {KONTAKT_FELDER}, 0 AS ungelesen
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, kontakt_id=kontakt_id)
        record = await result.single()
        return dict(record) if record else None


async def anlegen(campaign_id: str, pc_id: str, npc_id: str, stufe: str = "GESEHEN") -> dict | None:
    """Legt Kontaktwissen an — oder gibt das vorhandene zurück.

    **Stuft niemals hoch.** Die Automatik darf ein bestehendes GESPROCHEN
    nicht auf GESEHEN zurückwerfen, und ein zweiter Aufruf soll nichts
    verändern (Spec: "Eine vorhandene Beziehung wird durch die Automatik
    niemals hochgestuft, zurückgesetzt oder gelöscht").
    """
    driver = get_driver()
    query = """
        MATCH (pc:Person {id: $pc_id, campaignId: $campaign_id, personType: 'PC'})
        MATCH (npc:Person {id: $npc_id, campaignId: $campaign_id, personType: 'NPC'})
        MERGE (pc)-[r:KENNT]->(npc)
        ON CREATE SET
            r.id = $id,
            r.stufe = $stufe,
            r.echterNameBekannt = false,
            r.kontaktAnfrageStatus = 'KEINE',
            r.alias = '',
            r.persoenlicheNotizen = '',
            r.erstelltAm = $jetzt,
            r.aktualisiertAm = $jetzt
        RETURN r.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            pc_id=pc_id,
            npc_id=npc_id,
            stufe=stufe,
            id=str(uuid.uuid4()),
            jetzt=_jetzt(),
        )
        record = await result.single()
        if record is None:
            return None
    return await hole(campaign_id, record["id"])


async def aendern(campaign_id: str, kontakt_id: str, daten: dict) -> dict | None:
    """Ändert Felder der KENNT-Kante. None-Werte werden übersprungen."""
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if not geaendert:
        return await hole(campaign_id, kontakt_id)

    setzen = ", ".join(f"r.{f} = ${f}" for f in geaendert)
    driver = get_driver()
    query = f"""
        MATCH (:Person {{campaignId: $campaign_id}})-[r:KENNT {{id: $kontakt_id}}]->(:Person)
        SET {setzen}, r.aktualisiertAm = $jetzt
        RETURN r.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, kontakt_id=kontakt_id, jetzt=_jetzt(), **geaendert
        )
        if await result.single() is None:
            return None
    return await hole(campaign_id, kontakt_id)


async def loeschen(campaign_id: str, kontakt_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (:Person {campaignId: $campaign_id})-[r:KENNT {id: $kontakt_id}]->(:Person)
            DELETE r
            RETURN count(r) AS weg
            """,
            campaign_id=campaign_id,
            kontakt_id=kontakt_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def offene_anfragen(campaign_id: str) -> list[dict]:
    """Kontaktanfragen, über die die Spielleitung noch entscheiden muss."""
    driver = get_driver()
    query = f"""
        MATCH (pc:Person {{campaignId: $campaign_id}})-[r:KENNT]->(npc:Person)
        WHERE r.kontaktAnfrageStatus = 'OFFEN'
        RETURN {KONTAKT_FELDER}, 0 AS ungelesen
        ORDER BY r.aktualisiertAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


# ---------------------------------------------------------------- Nachrichten


async def nachrichten(campaign_id: str, pc_id: str, npc_id: str) -> list[dict]:
    """Der Verlauf eines Einzelchats, älteste zuerst."""
    driver = get_driver()
    query = """
        MATCH (n:Nachricht {campaignId: $campaign_id})
        MATCH (n)-[:VON]->(von:Person)
        MATCH (n)-[:AN]->(an:Person)
        WHERE (von.id = $pc_id AND an.id = $npc_id)
           OR (von.id = $npc_id AND an.id = $pc_id)
        RETURN n.id AS id, n.inhalt AS inhalt, n.erstelltAm AS erstelltAm,
               n.gelesenAm AS gelesenAm, n.erstelltVonRolle AS rolle,
               von.id AS vonId
        ORDER BY n.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, pc_id=pc_id, npc_id=npc_id)
        return [dict(r) async for r in result]


async def sende(campaign_id: str, von_id: str, an_id: str, inhalt: str, rolle: str) -> dict:
    """Legt eine Nachricht an. Nachrichten sind unveränderlich."""
    driver = get_driver()
    query = """
        MATCH (von:Person {id: $von_id, campaignId: $campaign_id})
        MATCH (an:Person {id: $an_id, campaignId: $campaign_id})
        CREATE (n:Nachricht {
            id: $id, campaignId: $campaign_id, inhalt: $inhalt,
            inhaltFormat: 'tiptap-json', erstelltAm: $jetzt,
            gelesenAm: null, erstelltVonRolle: $rolle
        })
        CREATE (n)-[:VON]->(von)
        CREATE (n)-[:AN]->(an)
        RETURN n.id AS id, n.inhalt AS inhalt, n.erstelltAm AS erstelltAm,
               n.gelesenAm AS gelesenAm, n.erstelltVonRolle AS rolle,
               von.id AS vonId
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            von_id=von_id,
            an_id=an_id,
            id=str(uuid.uuid4()),
            # Klartext wird zu TipTap-JSON; Emojis bleiben Unicode.
            inhalt=normalisiere_nachrichteninhalt(inhalt),
            jetzt=_jetzt(),
            rolle=rolle,
        )
        record = await result.single()
        return dict(record) if record else {}


async def markiere_gelesen(campaign_id: str, pc_id: str, npc_id: str) -> int:
    """Hakt alle eingehenden Nachrichten dieses Chats ab."""
    driver = get_driver()
    query = """
        MATCH (n:Nachricht {campaignId: $campaign_id})-[:VON]->(:Person {id: $npc_id})
        MATCH (n)-[:AN]->(:Person {id: $pc_id})
        WHERE n.gelesenAm IS NULL
        SET n.gelesenAm = $jetzt
        RETURN count(n) AS anzahl
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, pc_id=pc_id, npc_id=npc_id, jetzt=_jetzt()
        )
        record = await result.single()
        return int(record["anzahl"]) if record else 0


async def graph_daten(campaign_id: str) -> tuple[list[dict], list[dict]]:
    """Knoten und Kanten für die automatische GESEHEN-Erkennung.

    Liefert dasselbe Format, das `logic.erreichbare_npcs` erwartet.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (n {campaignId: $campaign_id})
            WHERE n:Person OR n:Ort OR n:Event
            RETURN n.id AS id, labels(n)[0] AS kind, n.personType AS personType,
                   n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer,
                   n.kontaktwissenWeitergeben AS kontaktwissenWeitergeben
            """,
            campaign_id=campaign_id,
        )
        nodes = [dict(r) async for r in result]

        result = await session.run(
            """
            MATCH (a {campaignId: $campaign_id})-[v:VERBINDUNG]->(b {campaignId: $campaign_id})
            RETURN v.id AS id, a.id AS source, b.id AS target,
                   v.sichtbarkeit AS sichtbarkeit, v.sichtbarFuer AS sichtbarFuer
            """,
            campaign_id=campaign_id,
        )
        edges = [dict(r) async for r in result]

    return nodes, edges
