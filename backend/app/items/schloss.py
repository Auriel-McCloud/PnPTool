"""Verschlossene Behälter: Passwort, Schlüssel oder Tastenfolge.

Genau eine Art pro Kiste. Auf bleibt auf, bis die Spielleitung wieder
zusperrt. Die Lösung und die Tastenfolge verlassen den Server nie in
Richtung Spieler — nur das Rätsel und die gerade aufleuchtende Runde.
"""

import json
import random

from app.db.neo4j_driver import get_driver

SCHLOSS_ARTEN = ("passwort", "schluessel", "spiel")
TASTEN = 5


def ist_verschlossen(item: dict) -> bool:
    return (item.get("schlossArt") or "") in SCHLOSS_ARTEN and not item.get("aufgeschlossen")


def passwort_passt(eingabe: str, loesung: str) -> bool:
    """Großschreibung und Randleerzeichen egal — am Tisch tippt man daneben."""
    return (eingabe or "").strip().casefold() == (loesung or "").strip().casefold()


def neue_folge(laenge: int) -> list[int]:
    n = max(1, int(laenge or 1))
    return [random.randint(0, TASTEN - 1) for _ in range(n)]


def folge_lesen(roh) -> list[int]:
    if isinstance(roh, list):
        return [int(x) for x in roh]
    if not roh:
        return []
    try:
        gelesen = json.loads(roh)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(gelesen, list):
        return []
    return [int(x) for x in gelesen]


def anzeige_fuer(folge: list[int], geschaffte_runden: int) -> list[int]:
    """Die nächste Runde: eine Taste mehr als schon geschafft."""
    return folge[: max(0, geschaffte_runden) + 1]


def zug_passt(eingabe: list[int], folge: list[int], geschaffte_runden: int) -> bool:
    soll = anzeige_fuer(folge, geschaffte_runden)
    return list(eingabe) == soll and len(soll) > 0


def schloss_patch_anpassen(bisher: dict, daten: dict) -> str | None:
    """Prüft einen GM-PATCH und setzt Spielstand zurück, wenn das Schloss wechselt.

    Gibt eine Fehlermeldung zurück oder None. `daten` wird ergänzt.
    """
    art = daten.get("schlossArt", bisher.get("schlossArt") or "")
    if art not in ("", *SCHLOSS_ARTEN):
        return "Unbekannte Schloss-Art."
    if art == "passwort":
        loesung = daten.get("schlossPasswort", bisher.get("schlossPasswort") or "")
        if not (loesung or "").strip():
            return "Passwort-Schloss braucht eine Lösung."
    if art == "schluessel":
        sid = daten.get("schluesselId", bisher.get("schluesselId") or "")
        if not sid:
            return "Schlüssel-Schloss braucht einen bestimmten Schlüssel."
        if sid == bisher.get("id"):
            return "Eine Kiste kann nicht ihr eigener Schlüssel sein."
    if art == "spiel":
        laenge = daten.get("spielLaenge", bisher.get("spielLaenge") or 0)
        if not laenge or int(laenge) < 1:
            daten["spielLaenge"] = 4
    art_neu = "schlossArt" in daten and daten.get("schlossArt") != (bisher.get("schlossArt") or "")
    wieder_zu = daten.get("aufgeschlossen") is False and bisher.get("aufgeschlossen")
    if art_neu or wieder_zu or daten.get("schlossArt") == "":
        daten["aufgeschlossen"] = False if art else daten.get("aufgeschlossen", False)
        daten["spielRunde"] = 0
        daten["spielFolge"] = "[]"
    if art == "" and "schlossArt" in daten:
        daten["aufgeschlossen"] = False
        daten["spielRunde"] = 0
        daten["spielFolge"] = "[]"
    return None


async def ids_in_verschlossenem(campaign_id: str) -> set[str]:
    """Gegenstände, die (auch verschachtelt) in einer noch zuen Kiste liegen."""
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {campaignId: $campaign_id})-[:LIEGT_IN*1..8]->(b:Gegenstand)
        WHERE b.schlossArt IN ['passwort', 'schluessel', 'spiel']
          AND NOT coalesce(b.aufgeschlossen, false)
        RETURN DISTINCT g.id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return {record["id"] async for record in result}


async def inhalt_mitnehmen(campaign_id: str, behaelter_id: str, ziel_person_id: str) -> None:
    """Was in der Kiste liegt, wandert mit — gleiche Sichtbarkeit wie die Kiste."""
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {id: $item_id, campaignId: $campaign_id})
        MATCH (neu:Person {id: $ziel_person_id, campaignId: $campaign_id})
        MATCH (inhalt:Gegenstand)-[:LIEGT_IN*1..8]->(g)
        WHERE inhalt.campaignId = $campaign_id
        WITH DISTINCT inhalt, neu, g
        OPTIONAL MATCH (:Person)-[r:BESITZT]->(inhalt)
        DELETE r
        WITH DISTINCT inhalt, neu, g
        SET inhalt.istVorlage = false,
            inhalt.sichtbarkeit = g.sichtbarkeit,
            inhalt.sichtbarFuer = g.sichtbarFuer
        MERGE (neu)-[:BESITZT]->(inhalt)
    """
    async with driver.session() as session:
        await session.run(
            query,
            campaign_id=campaign_id,
            item_id=behaelter_id,
            ziel_person_id=ziel_person_id,
        )


async def spiel_lesen(campaign_id: str, item_id: str) -> dict | None:
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {id: $item_id, campaignId: $campaign_id})
        RETURN g.schlossArt AS schlossArt, g.aufgeschlossen AS aufgeschlossen,
               g.spielLaenge AS spielLaenge, g.spielFolge AS spielFolge,
               g.spielRunde AS spielRunde
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        if record is None:
            return None
        daten = dict(record)
        daten["folge"] = folge_lesen(daten.get("spielFolge"))
        daten["spielRunde"] = int(daten.get("spielRunde") or 0)
        daten["spielLaenge"] = int(daten.get("spielLaenge") or 4)
        daten["aufgeschlossen"] = bool(daten.get("aufgeschlossen"))
        return daten


async def spiel_schreiben(campaign_id: str, item_id: str, folge: list[int], runde: int, auf: bool) -> None:
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {id: $item_id, campaignId: $campaign_id})
        SET g.spielFolge = $folge, g.spielRunde = $runde, g.aufgeschlossen = $auf
    """
    async with driver.session() as session:
        await session.run(
            query,
            campaign_id=campaign_id,
            item_id=item_id,
            folge=json.dumps(folge),
            runde=runde,
            auf=auf,
        )


async def besitzt_erreichbaren_schluessel(campaign_id: str, person_id: str, schluessel_id: str) -> bool:
    if not schluessel_id:
        return False
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(k:Gegenstand {id: $schluessel_id, campaignId: $campaign_id})
        WHERE NOT coalesce(k.weggeworfen, false)
        RETURN k.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, schluessel_id=schluessel_id
        )
        record = await result.single()
        if record is None:
            return False
    verborgen = await ids_in_verschlossenem(campaign_id)
    return schluessel_id not in verborgen
