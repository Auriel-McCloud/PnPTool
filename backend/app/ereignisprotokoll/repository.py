"""Ereignisprotokoll — das Sitzungs-Log.

Siehe docs/wiki/entities/ereignisprotokoll.md für die vollständige Herleitung
(Auslöser, Knoten-vs-Kante-Entscheidung, alle acht Kategorien).

Jede Kategorie ist ein eigener Knotentyp (kein generischer "typ"-Knoten),
aber alle tragen dieselben Basis-Properties (zeitpunkt, ingameZeitpunkt,
sitzungId, slNotiz, geloescht) — das ermöglicht die gemeinsame Zeitleiste
per Cypher-UNION (siehe `zeitleiste()` unten), ohne dass die einzelnen Typen
unsauber würden.

Papierkorb-Konvention wie überall im Projekt: `geloescht`-Flag statt
Hard-Delete, die SL darf jederzeit nachträglich korrigieren.
"""

import json
import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

# Bekannte Kategorie-Kennungen -> echter Neo4j-Label. Weisse Liste, weil der
# Labelname direkt in die Cypher-Abfrage eingeht (Injection-Schutz).
LOG_LABELS: dict[str, str] = {
    "ki": "KiProtokollEintrag",
    "gegenstand": "GegenstandsBewegung",
    "geld": "GeldBewegung",
    "aufenthalt": "Aufenthalt",
    "npcwissen": "NpcWissenszuwachs",
    "kampf": "KampfLogEintrag",
    "verhandlung": "VerhandlungsAusgang",
    "charakterentwicklung": "CharakterEntwicklung",
}


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


# ===========================================================================
# Sitzung — der Anker-Knoten pro Spielabend
# ===========================================================================


def _decode_sitzung(record: dict) -> dict:
    s = dict(record)
    s["ingameDatum"] = s.get("ingameDatum") or ""
    s["titel"] = s.get("titel") or ""
    s["notiz"] = s.get("notiz") or ""
    s["erstelltAm"] = s.get("erstelltAm") or ""
    return s


async def erzeuge_sitzung(campaign_id: str, datum: str, ingame_datum: str, titel: str, notiz: str) -> dict:
    driver = get_driver()
    sid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        CREATE (s:Sitzung {
            id: $sid, campaignId: $campaign_id, datum: $datum, ingameDatum: $ingame_datum,
            titel: $titel, notiz: $notiz, erstelltAm: $jetzt
        })
        CREATE (c)-[:HAT_SITZUNG]->(s)
        RETURN s.id AS id, s.datum AS datum, s.ingameDatum AS ingameDatum,
               s.titel AS titel, s.notiz AS notiz, s.erstelltAm AS erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, sid=sid, datum=datum,
            ingame_datum=ingame_datum, titel=titel, notiz=notiz, jetzt=_jetzt(),
        )
        record = await result.single()
        return _decode_sitzung(dict(record))


async def list_sitzungen(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (s:Sitzung {campaignId: $campaign_id})
        RETURN s.id AS id, s.datum AS datum, s.ingameDatum AS ingameDatum,
               s.titel AS titel, s.notiz AS notiz, s.erstelltAm AS erstelltAm
        ORDER BY s.datum DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode_sitzung(dict(r)) async for r in result]


async def get_sitzung(campaign_id: str, sitzung_id: str) -> dict | None:
    driver = get_driver()
    query = """
        MATCH (s:Sitzung {id: $sid, campaignId: $campaign_id})
        RETURN s.id AS id, s.datum AS datum, s.ingameDatum AS ingameDatum,
               s.titel AS titel, s.notiz AS notiz, s.erstelltAm AS erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, sid=sitzung_id)
        record = await result.single()
        return _decode_sitzung(dict(record)) if record else None


async def aktive_sitzung_id(campaign_id: str) -> str | None:
    """Die zuletzt angelegte Sitzung dieser Kampagne — Fallback-Zuordnung für
    automatische Log-Hooks (Kampf-Treffer, Verhandlungsausgang, ...), die
    selbst keine sitzungId übergeben. Die SL legt üblicherweise zu
    Spielbeginn eine neue Sitzung an ("Session 14"); solange sie das tut,
    landen automatisch erzeugte Einträge unter dem richtigen Abend. Ohne
    jede Sitzung (frische Kampagne, SL vergisst es) bleibt sitzungId einfach
    leer statt zu raten — kein Fehlerfall, nur unzugeordnet.
    """
    driver = get_driver()
    query = """
        MATCH (s:Sitzung {campaignId: $campaign_id})
        RETURN s.id AS id
        ORDER BY s.erstelltAm DESC
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        record = await result.single()
        return record["id"] if record else None


async def aendere_sitzung(campaign_id: str, sitzung_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if not geaendert:
        return await get_sitzung(campaign_id, sitzung_id)
    driver = get_driver()
    setzen = ", ".join(f"s.{k} = ${k}" for k in geaendert)
    query = f"""
        MATCH (s:Sitzung {{id: $sid, campaignId: $campaign_id}})
        SET {setzen}
        RETURN s.id AS id, s.datum AS datum, s.ingameDatum AS ingameDatum,
               s.titel AS titel, s.notiz AS notiz, s.erstelltAm AS erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, sid=sitzung_id, **geaendert)
        record = await result.single()
        return _decode_sitzung(dict(record)) if record else None


# ===========================================================================
# Gemeinsame Basis-Felder + generische Korrektur/Papierkorb-Funktionen
# ===========================================================================


def _basis_props() -> dict:
    return {"geloescht": False}


async def korrigiere_eintrag(campaign_id: str, kategorie: str, eintrag_id: str, felder: dict) -> bool:
    """SL darf jeden Log-Eintrag nachträglich korrigieren/ergänzen (Marks
    ausdrückliche Vorgabe) — generisch über alle Kategorien, weil die
    Feldnamen je Kategorie unterschiedlich sind."""
    label = LOG_LABELS.get(kategorie)
    if label is None or not felder:
        return False
    driver = get_driver()
    setzen = ", ".join(f"e.{k} = ${k}" for k in felder)
    query = f"""
        MATCH (e:{label} {{id: $eid, campaignId: $campaign_id}})
        SET {setzen}
        RETURN e.id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, eid=eintrag_id, **felder)
        return await result.single() is not None


async def setze_geloescht(campaign_id: str, kategorie: str, eintrag_id: str, geloescht: bool) -> bool:
    """Papierkorb statt Hard-Delete — genau wie überall sonst im Projekt."""
    label = LOG_LABELS.get(kategorie)
    if label is None:
        return False
    driver = get_driver()
    query = f"""
        MATCH (e:{label} {{id: $eid, campaignId: $campaign_id}})
        SET e.geloescht = $geloescht
        RETURN e.id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, eid=eintrag_id, geloescht=geloescht)
        return await result.single() is not None


# ===========================================================================
# 1. KiProtokollEintrag — loggt jede KI-Ausgabe dauerhaft
# ===========================================================================


async def log_ki_eintrag(
    campaign_id: str, *, anlass: str, prompt: str, antwort_text: str, uebernommen: bool,
    betrifft_id: str | None = None, sitzung_id: str | None = None,
    ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        CREATE (e:KiProtokollEintrag {
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, anlass: $anlass, prompt: $prompt, antwortText: $antwort_text,
            uebernommen: $uebernommen, betrifftId: $betrifft_id
        })
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        WITH e
        OPTIONAL MATCH (ziel {id: $betrifft_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN ziel IS NULL THEN [] ELSE [1] END | CREATE (e)-[:BETRIFFT]->(ziel))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            anlass=anlass, prompt=prompt, antwort_text=antwort_text, uebernommen=uebernommen,
            betrifft_id=betrifft_id,
        )
    return {"id": eid}


async def markiere_ki_eintrag_uebernommen(campaign_id: str, anlass: str, betrifft_id: str) -> None:
    """Markiert den zuletzt geloggten KI-Eintrag für dieses Anlass+Ziel als
    übernommen — für Fälle, in denen die Übernahme erst NACH dem Logging der
    Rohausgabe passiert (z.B. objekt-text: erst Vorschau loggen, dann bei
    tatsächlichem Anhängen ans Feld nachtragen)."""
    driver = get_driver()
    query = """
        MATCH (e:KiProtokollEintrag {campaignId: $campaign_id, anlass: $anlass, betrifftId: $betrifft_id})
        WITH e ORDER BY e.zeitpunkt DESC LIMIT 1
        SET e.uebernommen = true
    """
    async with driver.session() as session:
        await session.run(query, campaign_id=campaign_id, anlass=anlass, betrifft_id=betrifft_id)


async def list_ki_eintraege(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (e:KiProtokollEintrag {campaignId: $campaign_id})
        WHERE NOT coalesce(e.geloescht, false)
        OPTIONAL MATCH (e)-[:BETRIFFT]->(z)
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.anlass AS anlass,
               e.prompt AS prompt, e.antwortText AS antwortText, e.uebernommen AS uebernommen,
               e.betrifftId AS betrifftId, coalesce(z.name, z.title, '') AS betrifftName,
               CASE WHEN z IS NULL THEN NULL ELSE labels(z)[0] END AS betrifftKind
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


# ===========================================================================
# 2. GegenstandsBewegung — volle Besitzerkette
# ===========================================================================


async def log_gegenstandsbewegung(
    campaign_id: str, *, art: str, gegenstand_id: str,
    alter_besitzer_id: str | None = None, neuer_besitzer_id: str | None = None,
    ort_id: str | None = None, ort_kind: str | None = None, handel_id: str | None = None,
    sitzung_id: str | None = None, ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (e:GegenstandsBewegung {{
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, art: $art, handelId: $handel_id
        }})
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        WITH e
        OPTIONAL MATCH (g:Gegenstand {{id: $gegenstand_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN g IS NULL THEN [] ELSE [1] END | CREATE (e)-[:BETRIFFT]->(g))
        WITH e
        OPTIONAL MATCH (alt:Person {{id: $alter_besitzer_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN alt IS NULL THEN [] ELSE [1] END | CREATE (e)-[:ALTER_BESITZER]->(alt))
        WITH e
        OPTIONAL MATCH (neu:Person {{id: $neuer_besitzer_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN neu IS NULL THEN [] ELSE [1] END | CREATE (e)-[:NEUER_BESITZER]->(neu))
        WITH e
        OPTIONAL MATCH (ort {{id: $ort_id, campaignId: $campaign_id}}) WHERE $ort_id IS NOT NULL
        FOREACH (_ IN CASE WHEN ort IS NULL THEN [] ELSE [1] END | CREATE (e)-[:ORT]->(ort))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            art=art, handel_id=handel_id, gegenstand_id=gegenstand_id,
            alter_besitzer_id=alter_besitzer_id, neuer_besitzer_id=neuer_besitzer_id,
            ort_id=ort_id,
        )
    return {"id": eid}


async def list_gegenstandsbewegungen(campaign_id: str, gegenstand_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND g.id = $gegenstand_id" if gegenstand_id else ""
    query = f"""
        MATCH (e:GegenstandsBewegung {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        OPTIONAL MATCH (e)-[:BETRIFFT]->(g:Gegenstand)
        OPTIONAL MATCH (e)-[:ALTER_BESITZER]->(alt:Person)
        OPTIONAL MATCH (e)-[:NEUER_BESITZER]->(neu:Person)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.art AS art, e.handelId AS handelId,
               g.id AS gegenstandId, g.name AS gegenstandName,
               alt.id AS alterBesitzerId, alt.name AS alterBesitzerName,
               neu.id AS neuerBesitzerId, neu.name AS neuerBesitzerName
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, gegenstand_id=gegenstand_id)
        return [dict(r) async for r in result]


# ===========================================================================
# 3. GeldBewegung — Kapital, per handelId mit GegenstandsBewegung verknüpfbar
# ===========================================================================


async def log_geldbewegung(
    campaign_id: str, *, betrag: int, art: str,
    von_person_id: str | None = None, an_person_id: str | None = None,
    handel_id: str | None = None, sitzung_id: str | None = None,
    ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        CREATE (e:GeldBewegung {
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, betrag: $betrag, art: $art, handelId: $handel_id
        })
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        WITH e
        OPTIONAL MATCH (von:Person {id: $von_person_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN von IS NULL THEN [] ELSE [1] END | CREATE (e)-[:VON]->(von))
        WITH e
        OPTIONAL MATCH (an:Person {id: $an_person_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN an IS NULL THEN [] ELSE [1] END | CREATE (e)-[:AN]->(an))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            betrag=betrag, art=art, handel_id=handel_id,
            von_person_id=von_person_id, an_person_id=an_person_id,
        )
    return {"id": eid}


async def list_geldbewegungen(campaign_id: str, person_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND (von.id = $person_id OR an.id = $person_id)" if person_id else ""
    query = f"""
        MATCH (e:GeldBewegung {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        OPTIONAL MATCH (e)-[:VON]->(von:Person)
        OPTIONAL MATCH (e)-[:AN]->(an:Person)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.betrag AS betrag,
               e.art AS art, e.handelId AS handelId,
               von.id AS vonPersonId, von.name AS vonPersonName,
               an.id AS anPersonId, an.name AS anPersonName
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


# ===========================================================================
# 4. Aufenthalt — Party-/Personenbewegung mit Zeitstempel
# ===========================================================================


async def log_aufenthalt(
    campaign_id: str, *, ort_id: str, ort_kind: str,
    party_id: str | None = None, person_id: str | None = None,
    sitzung_id: str | None = None, ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (e:Aufenthalt {{
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false
        }})
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        WITH e
        MATCH (ort:{ort_kind} {{id: $ort_id, campaignId: $campaign_id}})
        CREATE (e)-[:ORT]->(ort)
        WITH e
        OPTIONAL MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN party IS NULL THEN [] ELSE [1] END | CREATE (e)-[:PARTY]->(party))
        WITH e
        OPTIONAL MATCH (person:Person {{id: $person_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN person IS NULL THEN [] ELSE [1] END | CREATE (e)-[:PERSON]->(person))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            ort_id=ort_id, party_id=party_id, person_id=person_id,
        )
    return {"id": eid}


async def list_aufenthalte(campaign_id: str, party_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND party.id = $party_id" if party_id else ""
    query = f"""
        MATCH (e:Aufenthalt {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        OPTIONAL MATCH (e)-[:PARTY]->(party:Party)
        OPTIONAL MATCH (e)-[:PERSON]->(person:Person)
        OPTIONAL MATCH (e)-[:ORT]->(ort)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz,
               party.id AS partyId, party.name AS partyName,
               person.id AS personId, person.name AS personName,
               ort.id AS ortId, coalesce(ort.name, ort.title) AS ortName,
               CASE WHEN ort IS NULL THEN NULL ELSE labels(ort)[0] END AS ortKind
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, party_id=party_id)
        return [dict(r) async for r in result]


async def party_war_schon_an(campaign_id: str, party_id: str, ort_id: str) -> bool:
    """Hat diese Party diesen Ort/dieses Event schon einmal besucht?

    Grundlage für die geplante KI-Auto-Steigerung (CLAUDE.md Punkt 8) —
    genau das fehlende Party-Besuchs-Log, das dort als Voraussetzung
    genannt wird.
    """
    driver = get_driver()
    query = """
        MATCH (e:Aufenthalt {campaignId: $campaign_id})-[:PARTY]->(party:Party {id: $party_id})
        MATCH (e)-[:ORT]->(ort {id: $ort_id})
        WHERE NOT coalesce(e.geloescht, false)
        RETURN count(e) AS anzahl
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, party_id=party_id, ort_id=ort_id)
        record = await result.single()
        return bool(record and record["anzahl"] > 0)


# ===========================================================================
# 5. NpcWissenszuwachs
# ===========================================================================


async def log_npc_wissenszuwachs(
    campaign_id: str, *, npc_person_id: str, wie_erfahren: str,
    ausloeser_id: str | None = None, sitzung_id: str | None = None,
    ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        MATCH (npc:Person {id: $npc_person_id, campaignId: $campaign_id})
        CREATE (e:NpcWissenszuwachs {
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, wieErfahren: $wie_erfahren
        })
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        CREATE (e)-[:NPC]->(npc)
        WITH e
        OPTIONAL MATCH (ausl {id: $ausloeser_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN ausl IS NULL THEN [] ELSE [1] END | CREATE (e)-[:AUSLOESER]->(ausl))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            npc_person_id=npc_person_id, wie_erfahren=wie_erfahren, ausloeser_id=ausloeser_id,
        )
        record = await result.single()
        return {"id": eid} if record else {"id": None}


async def list_npc_wissenszuwachs(campaign_id: str, npc_person_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND npc.id = $npc_person_id" if npc_person_id else ""
    query = f"""
        MATCH (e:NpcWissenszuwachs {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        MATCH (e)-[:NPC]->(npc:Person)
        OPTIONAL MATCH (e)-[:AUSLOESER]->(ausl)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.wieErfahren AS wieErfahren,
               npc.id AS npcPersonId, npc.name AS npcName,
               ausl.id AS ausloeserId, coalesce(ausl.name, ausl.title, '') AS ausloeserName
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, npc_person_id=npc_person_id)
        return [dict(r) async for r in result]


# ===========================================================================
# 6. KampfLogEintrag — mit automatischer Angreifer-Zuordnung
# ===========================================================================


async def log_kampf_eintrag(
    campaign_id: str, *, art: str, ziel_person_id: str,
    kampf_id: str = "", runde: int = 0,
    hp_art: str | None = None, hp_menge: int = 0, kaestchen_schaden: int = 0,
    angreifer_person_id: str | None = None,
    sitzung_id: str | None = None, ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        MATCH (ziel:Person {id: $ziel_person_id, campaignId: $campaign_id})
        CREATE (e:KampfLogEintrag {
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, kampfId: $kampf_id, runde: $runde, art: $art,
            hpArt: $hp_art, hpMenge: $hp_menge, kaestchenSchaden: $kaestchen_schaden
        })
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        CREATE (e)-[:ZIEL]->(ziel)
        WITH e
        OPTIONAL MATCH (angreifer:Person {id: $angreifer_person_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN angreifer IS NULL THEN [] ELSE [1] END | CREATE (e)-[:ANGREIFER]->(angreifer))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            kampf_id=kampf_id, runde=runde, art=art, hp_art=hp_art, hp_menge=hp_menge,
            kaestchen_schaden=kaestchen_schaden, ziel_person_id=ziel_person_id,
            angreifer_person_id=angreifer_person_id,
        )
        record = await result.single()
        return {"id": eid} if record else {"id": None}


async def list_kampf_eintraege(campaign_id: str, person_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND (ziel.id = $person_id OR angreifer.id = $person_id)" if person_id else ""
    query = f"""
        MATCH (e:KampfLogEintrag {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        MATCH (e)-[:ZIEL]->(ziel:Person)
        OPTIONAL MATCH (e)-[:ANGREIFER]->(angreifer:Person)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.kampfId AS kampfId,
               e.runde AS runde, e.art AS art, e.hpArt AS hpArt, e.hpMenge AS hpMenge,
               e.kaestchenSchaden AS kaestchenSchaden,
               ziel.id AS zielPersonId, ziel.name AS zielName,
               angreifer.id AS angreiferPersonId, angreifer.name AS angreiferName
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


async def hoechster_schaden(campaign_id: str, richtung: str) -> dict | None:
    """Höchster einzelner hpMenge-Wert über alle KampfLogEintrag — Grundlage
    für die Achievement-Trigger MEISTE_SCHADEN_GENOMMEN/_VERTEILT.

    richtung: "ZIEL" (Schaden genommen) oder "ANGREIFER" (Schaden verteilt).
    """
    driver = get_driver()
    kante = ":ZIEL" if richtung == "ZIEL" else ":ANGREIFER"
    query = f"""
        MATCH (e:KampfLogEintrag {{campaignId: $campaign_id}})-[{kante}]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false) AND e.hpMenge > 0
        RETURN p.id AS personId, p.name AS personName, e.hpMenge AS hpMenge, e.id AS eintragId
        ORDER BY e.hpMenge DESC
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        record = await result.single()
        return dict(record) if record else None


# ===========================================================================
# 7. VerhandlungsAusgang
# ===========================================================================


async def log_verhandlungsausgang(
    campaign_id: str, *, verhandlung_id: str, art: str, angenommen: bool,
    gesamtbetrag: int, positionen: list[dict], empfaenger_person_id: str,
    angeboten_von_person_id: str | None = None,
    sitzung_id: str | None = None, ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        MATCH (empfaenger:Person {id: $empfaenger_person_id, campaignId: $campaign_id})
        CREATE (e:VerhandlungsAusgang {
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, verhandlungId: $verhandlung_id, art: $art, angenommen: $angenommen,
            gesamtbetrag: $gesamtbetrag, positionenJson: $positionen_json
        })
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        CREATE (e)-[:EMPFAENGER]->(empfaenger)
        WITH e
        OPTIONAL MATCH (anbieter:Person {id: $angeboten_von_person_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN anbieter IS NULL THEN [] ELSE [1] END | CREATE (e)-[:ANGEBOTEN_VON]->(anbieter))
        RETURN e.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            verhandlung_id=verhandlung_id, art=art, angenommen=angenommen,
            gesamtbetrag=gesamtbetrag, positionen_json=json.dumps(positionen, ensure_ascii=False),
            empfaenger_person_id=empfaenger_person_id, angeboten_von_person_id=angeboten_von_person_id,
        )
        record = await result.single()
        return {"id": eid} if record else {"id": None}


async def list_verhandlungsausgaenge(campaign_id: str, person_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND empfaenger.id = $person_id" if person_id else ""
    query = f"""
        MATCH (e:VerhandlungsAusgang {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        MATCH (e)-[:EMPFAENGER]->(empfaenger:Person)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.verhandlungId AS verhandlungId,
               e.art AS art, e.angenommen AS angenommen, e.gesamtbetrag AS gesamtbetrag,
               e.positionenJson AS positionenJson,
               empfaenger.id AS empfaengerPersonId, empfaenger.name AS empfaengerName
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


async def zaehle_verhandlungsausgaenge_fuer(campaign_id: str, person_id: str) -> int:
    """Wie viele Verhandlungsausgänge existieren für diese Person? Grundlage
    für den Achievement-Trigger ERSTE_VERHANDLUNG."""
    driver = get_driver()
    query = """
        MATCH (e:VerhandlungsAusgang {campaignId: $campaign_id})-[:EMPFAENGER]->(p:Person {id: $person_id})
        WHERE NOT coalesce(e.geloescht, false)
        RETURN count(e) AS anzahl
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        return int(record["anzahl"]) if record else 0


# ===========================================================================
# 8. CharakterEntwicklung
# ===========================================================================


async def log_charakterentwicklung(
    campaign_id: str, *, person_id: str, art: str, alt: str, neu: str,
    trait_def_id: str | None = None, trait_name: str | None = None,
    kosten_oder_menge: int = 0, sitzung_id: str | None = None,
    ingame_zeitpunkt: str = "", sl_notiz: str = "",
) -> dict:
    driver = get_driver()
    eid = str(uuid.uuid4())
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
        CREATE (e:CharakterEntwicklung {
            id: $eid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, art: $art, traitDefId: $trait_def_id, traitName: $trait_name,
            alt: $alt, neu: $neu, kostenOderMenge: $kosten_oder_menge
        })
        CREATE (c)-[:HAT_EREIGNIS]->(e)
        CREATE (e)-[:PERSON]->(p)
        RETURN e.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, eid=eid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            person_id=person_id, art=art, trait_def_id=trait_def_id, trait_name=trait_name,
            alt=alt, neu=neu, kosten_oder_menge=kosten_oder_menge,
        )
        record = await result.single()
        return {"id": eid} if record else {"id": None}


async def list_charakterentwicklung(campaign_id: str, person_id: str | None = None) -> list[dict]:
    driver = get_driver()
    filter_klausel = "AND p.id = $person_id" if person_id else ""
    query = f"""
        MATCH (e:CharakterEntwicklung {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false)
        MATCH (e)-[:PERSON]->(p:Person)
        WHERE true {filter_klausel}
        RETURN e.id AS id, e.zeitpunkt AS zeitpunkt, e.ingameZeitpunkt AS ingameZeitpunkt,
               e.sitzungId AS sitzungId, e.slNotiz AS slNotiz, e.art AS art,
               e.traitDefId AS traitDefId, e.traitName AS traitName, e.alt AS alt, e.neu AS neu,
               e.kostenOderMenge AS kostenOderMenge, p.id AS personId, p.name AS personName
        ORDER BY e.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


# ===========================================================================
# Gemeinsame Zeitleiste — Cypher-UNION über alle Kategorien
# ===========================================================================


async def zeitleiste(campaign_id: str, sitzung_id: str | None = None) -> list[dict]:
    """"Was ist am Abend X passiert" — eine Abfrage über alle acht Kategorien.

    Liefert je Eintrag nur die Basis-Felder + Kategorie-Kennung; Details
    holt der Aufrufer bei Bedarf über die kategoriespezifischen list_*-
    Funktionen (kein Overengineering einer vollständig generischen
    Detail-Antwort).
    """
    driver = get_driver()
    sitzung_filter = "AND e.sitzungId = $sitzung_id" if sitzung_id else ""
    teile = []
    for kategorie, label in LOG_LABELS.items():
        teile.append(f"""
        MATCH (e:{label} {{campaignId: $campaign_id}})
        WHERE NOT coalesce(e.geloescht, false) {sitzung_filter}
        RETURN e.id AS id, '{kategorie}' AS kategorie, e.zeitpunkt AS zeitpunkt,
               e.ingameZeitpunkt AS ingameZeitpunkt, e.sitzungId AS sitzungId, e.slNotiz AS slNotiz
        """)
    query = "\nUNION\n".join(teile) + "\nORDER BY zeitpunkt DESC"
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, sitzung_id=sitzung_id)
        return [dict(r) async for r in result]
