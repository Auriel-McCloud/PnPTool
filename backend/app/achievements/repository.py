"""Achievements — Katalog + Verleihungen.

Siehe docs/wiki/entities/achievements.md für die vollständige Herleitung.
Zwei Knotentypen: `Achievement` (Definition, SL-Baukasten) und
`AchievementVerleihung` (eine Vergabe an eine Person, Papierkorb-Prinzip wie
überall sonst im Projekt — `geloescht`-Flag statt Hard-Delete).
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

ACHIEVEMENT_FELDER = [
    "name", "beschreibung", "icon", "art", "ausloeseArt", "einzigartig",
    "belohnungsArt", "belohnungsMenge", "belohnungsHintergrund", "zielGegenstandId",
]

_ACHIEVEMENT_RETURN = """
    a.id AS id, a.name AS name, a.beschreibung AS beschreibung, a.icon AS icon,
    a.art AS art, a.ausloeseArt AS ausloeseArt, a.einzigartig AS einzigartig,
    a.belohnungsArt AS belohnungsArt, a.belohnungsMenge AS belohnungsMenge,
    a.belohnungsHintergrund AS belohnungsHintergrund, a.zielGegenstandId AS zielGegenstandId
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_achievement(record: dict) -> dict:
    """Ausgangswerte für Bestandsdaten (Stolperstein 9: fehlendes Feld reisst
    sonst die ganze Liste mit 500 ab)."""
    a = dict(record)
    a["beschreibung"] = a.get("beschreibung") or ""
    a["icon"] = a.get("icon") or ""
    a["art"] = a.get("art") or "MANUELL"
    a["einzigartig"] = bool(a.get("einzigartig"))
    a["belohnungsArt"] = a.get("belohnungsArt") or "KEINE"
    a["belohnungsMenge"] = a.get("belohnungsMenge") or 0
    return a


# ===========================================================================
# Achievement — der Katalog
# ===========================================================================


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (a:Achievement {{campaignId: $campaign_id}})
        OPTIONAL MATCH (g:Gegenstand {{id: a.zielGegenstandId}})
        RETURN {_ACHIEVEMENT_RETURN}, g.name AS zielGegenstandName
        ORDER BY a.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode_achievement(dict(r)) async for r in result]


async def hole(campaign_id: str, achievement_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (a:Achievement {{id: $aid, campaignId: $campaign_id}})
        OPTIONAL MATCH (g:Gegenstand {{id: a.zielGegenstandId}})
        RETURN {_ACHIEVEMENT_RETURN}, g.name AS zielGegenstandName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, aid=achievement_id)
        record = await result.single()
        return _decode_achievement(dict(record)) if record else None


async def anlegen(campaign_id: str, daten: dict) -> dict:
    driver = get_driver()
    aid = str(uuid.uuid4())
    werte = {f: daten.get(f) for f in ACHIEVEMENT_FELDER}
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (a:Achievement {{
            id: $aid, campaignId: $campaign_id,
            name: $name, beschreibung: $beschreibung, icon: $icon, art: $art,
            ausloeseArt: $ausloeseArt, einzigartig: $einzigartig,
            belohnungsArt: $belohnungsArt, belohnungsMenge: $belohnungsMenge,
            belohnungsHintergrund: $belohnungsHintergrund, zielGegenstandId: $zielGegenstandId
        }})
        CREATE (c)-[:HAT_ACHIEVEMENT]->(a)
        RETURN {_ACHIEVEMENT_RETURN}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, aid=aid, **werte)
        record = await result.single()
        return _decode_achievement(dict(record))


async def aendern(campaign_id: str, achievement_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if not geaendert:
        return await hole(campaign_id, achievement_id)
    driver = get_driver()
    setzen = ", ".join(f"a.{k} = ${k}" for k in geaendert)
    query = f"""
        MATCH (a:Achievement {{id: $aid, campaignId: $campaign_id}})
        SET {setzen}
        RETURN {_ACHIEVEMENT_RETURN}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, aid=achievement_id, **geaendert)
        record = await result.single()
        return _decode_achievement(dict(record)) if record else None


async def loeschen(campaign_id: str, achievement_id: str) -> bool:
    """Harter Löschvorgang für die Definition selbst — bewusst anders als bei
    Verleihungen: ein fehlerhaft angelegter Katalogeintrag (Tippfehler im
    Namen, falscher Trigger) soll sich ohne Leichen im Papierkorb entfernen
    lassen, solange noch keine Verleihung daran hängt."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (a:Achievement {id: $aid, campaignId: $campaign_id})
            WHERE NOT EXISTS { MATCH (:AchievementVerleihung)-[:ACHIEVEMENT]->(a) }
            DETACH DELETE a
            RETURN count(a) AS geloescht
            """,
            campaign_id=campaign_id, aid=achievement_id,
        )
        record = await result.single()
        return bool(record and record["geloescht"])


# ===========================================================================
# AchievementVerleihung — eine einzelne Vergabe
# ===========================================================================

_VERLEIHUNG_RETURN = """
    v.id AS id, p.id AS personId, p.name AS personName,
    a.id AS achievementId, a.name AS achievementName, a.icon AS achievementIcon,
    a.beschreibung AS achievementBeschreibung,
    v.zeitpunkt AS zeitpunkt, v.ingameZeitpunkt AS ingameZeitpunkt,
    v.sitzungId AS sitzungId, v.slNotiz AS slNotiz, v.geloescht AS geloescht,
    v.text AS text, v.abgeloest AS abgeloest
"""


def _decode_verleihung(record: dict) -> dict:
    v = dict(record)
    v["ingameZeitpunkt"] = v.get("ingameZeitpunkt") or ""
    v["slNotiz"] = v.get("slNotiz") or ""
    v["text"] = v.get("text") or ""
    v["geloescht"] = bool(v.get("geloescht"))
    v["abgeloest"] = bool(v.get("abgeloest"))
    return v


async def verleihungen_fuer_person(campaign_id: str, person_id: str) -> list[dict]:
    """Eigene Achievements eines Spielers — neuestes zuerst (Marks UI-Vorgabe)."""
    driver = get_driver()
    query = f"""
        MATCH (v:AchievementVerleihung {{campaignId: $campaign_id}})-[:PERSON]->(p:Person {{id: $person_id}})
        MATCH (v)-[:ACHIEVEMENT]->(a:Achievement)
        WHERE NOT coalesce(v.geloescht, false)
        RETURN {_VERLEIHUNG_RETURN}
        ORDER BY v.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [_decode_verleihung(dict(r)) async for r in result]


async def alle_verleihungen(campaign_id: str) -> list[dict]:
    """Alle Verleihungen der Kampagne — SL-Verwaltungsfenster."""
    driver = get_driver()
    query = f"""
        MATCH (v:AchievementVerleihung {{campaignId: $campaign_id}})-[:PERSON]->(p:Person)
        MATCH (v)-[:ACHIEVEMENT]->(a:Achievement)
        WHERE NOT coalesce(v.geloescht, false)
        RETURN {_VERLEIHUNG_RETURN}
        ORDER BY v.zeitpunkt DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode_verleihung(dict(r)) async for r in result]


async def hat_bereits(campaign_id: str, achievement_id: str, person_id: str) -> bool:
    """Hat diese Person dieses Achievement schon (nicht abgelöst)? Grundlage
    für die Vorschlags-Filterung — eine bereits vergebene AUTO-Verleihung
    darf nicht erneut vorgeschlagen werden."""
    driver = get_driver()
    query = """
        MATCH (v:AchievementVerleihung {campaignId: $campaign_id})-[:PERSON]->(p:Person {id: $person_id})
        MATCH (v)-[:ACHIEVEMENT]->(a:Achievement {id: $aid})
        WHERE NOT coalesce(v.geloescht, false) AND NOT coalesce(v.abgeloest, false)
        RETURN count(v) AS anzahl
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id, aid=achievement_id)
        record = await result.single()
        return bool(record and record["anzahl"] > 0)


async def aktueller_traeger(campaign_id: str, achievement_id: str) -> str | None:
    """Wer trägt gerade ein einzigartiges Achievement (nicht abgelöst)?
    `None` wenn noch nie vergeben. Grundlage für Rekord-Trigger
    (MEISTE_SCHADEN_*): die bisherige Trägerin muss vor einer neuen
    Verleihung auf abgeloest=true gesetzt werden."""
    driver = get_driver()
    query = """
        MATCH (v:AchievementVerleihung {campaignId: $campaign_id})-[:PERSON]->(p:Person)
        MATCH (v)-[:ACHIEVEMENT]->(:Achievement {id: $aid})
        WHERE NOT coalesce(v.geloescht, false) AND NOT coalesce(v.abgeloest, false)
        RETURN p.id AS personId
        ORDER BY v.zeitpunkt DESC
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, aid=achievement_id)
        record = await result.single()
        return record["personId"] if record else None


async def loese_ab(campaign_id: str, achievement_id: str, person_id: str) -> None:
    """Markiert die aktuelle Verleihung einer Person für ein Achievement als
    abgelöst — bei einem Rekord-Trigger, der den Träger wechselt."""
    driver = get_driver()
    query = """
        MATCH (v:AchievementVerleihung {campaignId: $campaign_id})-[:PERSON]->(:Person {id: $person_id})
        MATCH (v)-[:ACHIEVEMENT]->(:Achievement {id: $aid})
        WHERE NOT coalesce(v.geloescht, false) AND NOT coalesce(v.abgeloest, false)
        SET v.abgeloest = true
    """
    async with driver.session() as session:
        await session.run(query, campaign_id=campaign_id, aid=achievement_id, person_id=person_id)


async def verleihe(
    campaign_id: str, *, achievement_id: str, person_id: str, text: str = "",
    sl_notiz: str = "", sitzung_id: str | None = None, ingame_zeitpunkt: str = "",
) -> dict | None:
    driver = get_driver()
    vid = str(uuid.uuid4())
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        MATCH (p:Person {{id: $person_id, campaignId: $campaign_id}})
        MATCH (a:Achievement {{id: $aid, campaignId: $campaign_id}})
        CREATE (v:AchievementVerleihung {{
            id: $vid, campaignId: $campaign_id, zeitpunkt: $zeitpunkt,
            ingameZeitpunkt: $ingame_zeitpunkt, sitzungId: $sitzung_id, slNotiz: $sl_notiz,
            geloescht: false, text: $text, abgeloest: false
        }})
        CREATE (c)-[:HAT_EREIGNIS]->(v)
        CREATE (v)-[:PERSON]->(p)
        CREATE (v)-[:ACHIEVEMENT]->(a)
        RETURN {_VERLEIHUNG_RETURN}
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, vid=vid, zeitpunkt=_jetzt(),
            ingame_zeitpunkt=ingame_zeitpunkt, sitzung_id=sitzung_id, sl_notiz=sl_notiz,
            text=text, person_id=person_id, aid=achievement_id,
        )
        record = await result.single()
        return _decode_verleihung(dict(record)) if record else None


async def setze_geloescht(campaign_id: str, verleihung_id: str, geloescht: bool) -> bool:
    """Papierkorb-Prinzip wie überall sonst — kein Hard-Delete."""
    driver = get_driver()
    query = """
        MATCH (v:AchievementVerleihung {id: $vid, campaignId: $campaign_id})
        SET v.geloescht = $geloescht
        RETURN v.id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, vid=verleihung_id, geloescht=geloescht)
        return await result.single() is not None


# ===========================================================================
# Trigger-Hilfsabfragen — eigene Funktionen pro Datengrundlage, siehe
# trigger.py für die Zusammensetzung der einzelnen auslöseArt-Werte.
# ===========================================================================


async def erster_critter_traeger(campaign_id: str) -> list[dict]:
    """Alle Personen, die mindestens einen Critter per BEGLEITET-Kante
    gebunden haben — Grundlage für ERSTER_CRITTER."""
    driver = get_driver()
    query = """
        MATCH (critter:Person {campaignId: $campaign_id, istCritter: true})-[:BEGLEITET]->(p:Person)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def erste_drohne_traeger(campaign_id: str) -> list[dict]:
    """Alle Personen mit mindestens einem gebundenen Begleiter (Art BEGLEITER,
    nicht Sprite/Geist) — Grundlage für ERSTE_DROHNE."""
    driver = get_driver()
    query = """
        MATCH (b:Begleiter {campaignId: $campaign_id, art: "BEGLEITER"})-[:BEGLEITET]->(p:Person)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def erster_besitz_ziel_traeger(campaign_id: str, gegenstand_id: str) -> list[dict]:
    """Alle Personen, die den Zielgegenstand (per Vorlage) jemals besessen
    haben — Grundlage für ERSTER_BESITZ_ZIEL. Vorlagen-Besitz zählt über die
    Kopien: eine Person zählt, sobald sie eine Kopie der Vorlage besitzt ODER
    besessen hat (GegenstandsBewegung-Log), nicht nur aktuell."""
    driver = get_driver()
    query = """
        MATCH (e:GegenstandsBewegung {campaignId: $campaign_id})-[:NEUER_BESITZER]->(p:Person)
        MATCH (e)-[:BETRIFFT]->(g:Gegenstand {id: $gegenstand_id})
        WHERE NOT coalesce(e.geloescht, false)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, gegenstand_id=gegenstand_id)
        return [dict(r) async for r in result]


async def kampf_tote_in_sitzung(campaign_id: str, sitzung_id: str) -> set[str]:
    """Person-IDs, die in dieser Sitzung als KampfLogEintrag-Ziel starben —
    Grundlage für ERSTE_SITZUNG_UEBERLEBT (wer NICHT in dieser Menge ist)."""
    driver = get_driver()
    query = """
        MATCH (e:KampfLogEintrag {campaignId: $campaign_id, sitzungId: $sitzung_id, art: "TOD"})-[:ZIEL]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false)
        RETURN DISTINCT p.id AS personId
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, sitzung_id=sitzung_id)
        return {r["personId"] async for r in result}


async def erste_sitzung_id(campaign_id: str) -> str | None:
    """Die älteste Sitzung dieser Kampagne (nach erstelltAm) — Grundlage für
    ERSTE_SITZUNG_UEBERLEBT, das beim Anlegen der ZWEITEN Sitzung prüft."""
    driver = get_driver()
    query = """
        MATCH (s:Sitzung {campaignId: $campaign_id})
        RETURN s.id AS id
        ORDER BY s.erstelltAm ASC
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        record = await result.single()
        return record["id"] if record else None


async def anzahl_sitzungen(campaign_id: str) -> int:
    driver = get_driver()
    query = "MATCH (s:Sitzung {campaignId: $campaign_id}) RETURN count(s) AS anzahl"
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        record = await result.single()
        return int(record["anzahl"]) if record else 0


async def erster_kill_kandidat(campaign_id: str) -> dict | None:
    """Der allererste Kill campaign-weit (ältester KampfLogEintrag mit
    art=TOD) — Grundlage für ERSTER_KILL. Nur ein Ergebnis, weil es per
    Definition höchstens einen "ersten" geben kann."""
    driver = get_driver()
    query = """
        MATCH (e:KampfLogEintrag {campaignId: $campaign_id, art: "TOD"})-[:ANGREIFER]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false)
        RETURN p.id AS personId, p.name AS personName
        ORDER BY e.zeitpunkt ASC
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        record = await result.single()
        return dict(record) if record else None


async def moerder_kandidaten(campaign_id: str) -> list[dict]:
    """Jede Person, die irgendwann einen Kill hatte — Grundlage für MOERDER
    (jeder kriegt sein eigenes, nicht nur der erste)."""
    driver = get_driver()
    query = """
        MATCH (e:KampfLogEintrag {campaignId: $campaign_id, art: "TOD"})-[:ANGREIFER]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def erster_kauf_kandidaten(campaign_id: str) -> list[dict]:
    """Jede Person mit mindestens einer GEKAUFT-Bewegung — Grundlage für
    ERSTER_KAUF."""
    driver = get_driver()
    query = """
        MATCH (e:GegenstandsBewegung {campaignId: $campaign_id, art: "GEKAUFT"})-[:NEUER_BESITZER]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def erste_verhandlung_kandidaten(campaign_id: str) -> list[dict]:
    """Jede Person mit mindestens einem VerhandlungsAusgang — Grundlage für
    ERSTE_VERHANDLUNG."""
    driver = get_driver()
    query = """
        MATCH (e:VerhandlungsAusgang {campaignId: $campaign_id})-[:EMPFAENGER]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def geheimnistraeger_kandidaten(campaign_id: str) -> list[dict]:
    """Personen, Orte, Events, Fraktionen oder Gegenstände mit
    `sichtbarkeit: SPEZIFISCH` und GENAU einer Person in `sichtbarFuer` —
    Grundlage für GEHEIMNISTRAEGER. State-basiert wie CHARAKTER_ERSTELLT
    (kein Log-Eintrag, lebt direkt am bestehenden Sichtbarkeitsfeld)."""
    driver = get_driver()
    query = """
        MATCH (n {campaignId: $campaign_id})
        WHERE (n:Person OR n:Ort OR n:Event OR n:Fraktion OR n:Gegenstand)
          AND n.sichtbarkeit = "SPEZIFISCH" AND size(coalesce(n.sichtbarFuer, [])) = 1
        MATCH (p:Person {id: n.sichtbarFuer[0]})
        RETURN p.id AS personId, p.name AS personName,
               n.id AS betrifftId, coalesce(n.name, n.title, '') AS betrifftName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def frisch_erstellte_pcs(campaign_id: str) -> list[dict]:
    """PCs mit `erstellungAbgeschlossen: true` — Grundlage für
    CHARAKTER_ERSTELLT. State-basiert, kein Ereignisprotokoll-Eintrag
    (Charaktererstellung selbst wird nicht geloggt, siehe
    docs/wiki/entities/ereignisprotokoll.md)."""
    driver = get_driver()
    query = """
        MATCH (p:Person {campaignId: $campaign_id, erstellungAbgeschlossen: true})
        RETURN p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def endboss_besiegt_kandidaten(campaign_id: str) -> list[dict]:
    """Angreifer, die einen `Person{istEndboss:true}` mit einem
    `KampfLogEintrag{art:"TOD"}` getötet haben — Grundlage für
    ENDBOSS_BESIEGT."""
    driver = get_driver()
    query = """
        MATCH (e:KampfLogEintrag {campaignId: $campaign_id, art: "TOD"})-[:ZIEL]->(:Person {istEndboss: true})
        MATCH (e)-[:ANGREIFER]->(p:Person)
        WHERE NOT coalesce(e.geloescht, false)
        RETURN DISTINCT p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def beschreibung_sichtbar_fuer_pcs(campaign_id: str, gegenstand_id: str) -> list[dict]:
    """Welche PCs sehen die Beschreibung dieses Gegenstands aktuell?
    Grundlage für ERSTE_BESCHREIBUNG_ZIEL — state-basiert wie
    GEHEIMNISTRAEGER/CHARAKTER_ERSTELLT (keine Historie der
    Sichtbarkeits-Änderungen, nur der aktuelle Stand zählt)."""
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {id: $gegenstand_id, campaignId: $campaign_id})
        MATCH (p:Person {campaignId: $campaign_id, personType: "PC"})
        WHERE coalesce(g.sichtbarkeit, "GM") = "ALLE"
           OR (coalesce(g.sichtbarkeit, "GM") = "SPEZIFISCH" AND p.id IN coalesce(g.sichtbarFuer, []))
        RETURN p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, gegenstand_id=gegenstand_id)
        return [dict(r) async for r in result]


async def alle_pcs(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (p:Person {campaignId: $campaign_id, personType: "PC"})
        RETURN p.id AS personId, p.name AS personName
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]
