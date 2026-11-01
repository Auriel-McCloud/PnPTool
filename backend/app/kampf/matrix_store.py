"""Kampf-Matrix: ICE-Pool, Sicht, Schalter. Zustand hängt am Kampf-Knoten."""

from __future__ import annotations

import json
import uuid

from app.db.neo4j_driver import get_driver
from app.entities.repository import PERSON_FIELDS, get_node
from app.items.repository import commlink_cyberwall
from app.kampf import matrix, repository
from app.kampf.matrix import leerer_stand
from app.traits.bogen import ice_max
from app.traits.repository import get_ratings_for_entity


def _werte(ratings: list[dict]) -> dict[str, int]:
    return {r["name"]: int(r["rating"] or 0) for r in ratings}


async def lade(campaign_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            RETURN k.id AS id, k.runde AS runde, k.matrixStand AS stand
            """,
            campaign_id=campaign_id,
        )
        record = await result.single()
    if record is None:
        return None
    roh = record["stand"]
    stand = leerer_stand()
    if roh:
        try:
            geladen = json.loads(roh)
            stand.update({k: geladen.get(k, stand[k]) for k in stand})
        except json.JSONDecodeError:
            pass
    return {"id": record["id"], "runde": int(record["runde"] or 1), "stand": stand}


async def speichere(campaign_id: str, stand: dict) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            SET k.matrixStand = $stand
            """,
            campaign_id=campaign_id,
            stand=json.dumps(stand),
        )


async def party_ids(campaign_id: str, person_id: str) -> set[str]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (ich:Person {id: $person_id, campaignId: $campaign_id})-[:MITGLIED_VON]->(party:Party)
            MATCH (andere:Person)-[:MITGLIED_VON]->(party)
            RETURN andere.id AS id
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        return {r["id"] async for r in result}


async def basis_ice(campaign_id: str, person_id: str) -> int:
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        return 0
    ratings = await get_ratings_for_entity(campaign_id, person_id)
    wall = await commlink_cyberwall(campaign_id, person_id)
    return ice_max(
        person.get("weg") or "KEINER",
        _werte(ratings),
        wall,
        bool(person.get("istDrohne")) or bool(person.get("istFahrzeug")),
    )


async def ist_akteur(campaign_id: str, person_id: str) -> bool:
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None or person.get("istKI"):
        return False
    if person.get("weg") == "NEUROWEAVER":
        return True
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
            WHERE g.typ = 'Cyberdeck' AND g.ablage = 'AUSGERUESTET'
              AND NOT coalesce(g.weggeworfen, false)
            RETURN count(g) AS n
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
    return bool(record and record["n"])


async def schaltbare(campaign_id: str, person_id: str) -> list[dict]:
    """Was an dieser Person ausgehen kann. Schusswaffe als Ganzes, sonst Upgrades."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
            WHERE NOT coalesce(g.weggeworfen, false) AND (
                (g.typ = 'Waffe' AND g.ablage = 'AUSGERUESTET')
                OR (g.typ = 'Cyberware' AND coalesce(g.verbaut, false))
                OR (g.typ IN ['Cyberdeck', 'Riggerkonsole'] AND g.ablage = 'AUSGERUESTET')
                OR (
                    coalesce(g.istAugment, false)
                    AND (g)-[:MONTIERT_AN]->(:Gegenstand)<-[:BESITZT]-(p)
                )
            )
            RETURN g.id AS id, g.name AS name, g.typ AS typ,
                   coalesce(g.kampfFertigkeit, '') AS kampfFertigkeit,
                   coalesce(g.deaktivModus, '') AS deaktivModus,
                   coalesce(g.istAugment, false) AS istAugment
            ORDER BY g.name
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        zeilen = [dict(r) async for r in result]
    aus = []
    for z in zeilen:
        if z["istAugment"]:
            aus.append({**z, "art": "upgrade"})
            continue
        if z["typ"] == "Waffe":
            modus = matrix.deaktiv_modus(z.get("deaktivModus") or "", z["kampfFertigkeit"])
            if modus == "komplett":
                aus.append({**z, "art": "waffe"})
            continue
        if z["typ"] == "Cyberware":
            aus.append({**z, "art": "cyber"})
        elif z["typ"] == "Cyberdeck":
            aus.append({**z, "art": "deck"})
        elif z["typ"] == "Riggerkonsole":
            aus.append({**z, "art": "konsole"})
    return aus


async def drohnen_fallen(campaign_id: str, rigger_id: str) -> list[str]:
    """Gesprungene Drohnen der Konsole fallen sofort aus dem Sprung und dem Kampf."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (d:Person {campaignId: $campaign_id})-[:BEGLEITET]->(:Person {id: $rigger_id})
            WHERE coalesce(d.riggerAktiv, false) = true
            SET d.riggerAktiv = false
            RETURN d.id AS id
            """,
            campaign_id=campaign_id,
            rigger_id=rigger_id,
        )
        ids = [r["id"] async for r in result]
        if ids:
            await session.run(
                """
                MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer)-[:IST]->(p:Person)
                WHERE p.id IN $ids
                DETACH DELETE t
                """,
                campaign_id=campaign_id,
                ids=ids,
            )
    return ids


async def drohnen_zurueck(campaign_id: str, ids: list[str]) -> None:
    """Der Sprung von vor dem Aus. Nicht wieder in die Initiative, nur verbunden."""
    if not ids:
        return
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (d:Person {campaignId: $campaign_id})
            WHERE d.id IN $ids
            SET d.riggerAktiv = true
            """,
            campaign_id=campaign_id,
            ids=ids,
        )


async def hot_wahl_frei(campaign_id: str, person_id: str) -> None:
    """Konsole wieder da: eine leere Wahl zählt nicht als verbraucht."""
    zustand = await repository.hot_lesen(campaign_id, person_id)
    if zustand["hotDrohneId"] or not zustand["hotDrohneRunde"]:
        return
    await repository.hot_schreiben(campaign_id, person_id, hot_drohne_id=None, hot_runde=0)


def merke_sprung(stand: dict, traeger_id: str, ids: list[str]) -> None:
    for eintrag in stand.get("aus") or []:
        if eintrag.get("traegerId") == traeger_id and eintrag.get("art") == "konsole":
            eintrag["gesprungeneIds"] = list(ids)


async def hot_wegen_aus(campaign_id: str, person_id: str) -> str:
    """Wirft aus Hot, solange Neurolink oder Konsole aus sind."""
    from app.items.repository import verbautes_chrom
    from app.kampf.hot import hot_verlust, kick_braucht_reset

    kampf = await lade(campaign_id)
    if kampf is None:
        return ""
    chrom = await verbautes_chrom(campaign_id, person_id)
    verlust = hot_verlust(aus_fuer(kampf["stand"], person_id), chrom)
    if not verlust:
        return ""
    zustand = await repository.hot_lesen(campaign_id, person_id)
    if verlust == "alles" and kick_braucht_reset("alles", zustand["hotDrohneId"], zustand["hotDrohneRunde"], zustand["matrixHot"]):
        await repository.hot_schreiben(
            campaign_id, person_id, hot_drohne_id=None, hot_runde=0, matrix_hot=False
        )
    elif verlust == "drohne" and kick_braucht_reset("drohne", zustand["hotDrohneId"], zustand["hotDrohneRunde"], False):
        await repository.hot_schreiben(campaign_id, person_id, hot_drohne_id=None, hot_runde=0)
    return verlust


def aktuelles_ice(stand: dict, person_id: str, maximum: int) -> int:
    roh = (stand.get("ice") or {}).get(person_id)
    if roh is None:
        return maximum
    return max(0, int(roh))


def merke_ice(stand: dict, person_id: str, wert: int) -> None:
    stand.setdefault("ice", {})[person_id] = wert


def gesehen(stand: dict, viewer_id: str) -> set[str]:
    return set((stand.get("gesehen") or {}).get(viewer_id) or [])


def schalte(stand: dict, traeger_id: str, von_id: str, ziele: list[dict]) -> None:
    liste = stand.setdefault("aus", [])
    for z in ziele:
        liste.append({
            "id": str(uuid.uuid4()),
            "traegerId": traeger_id,
            "vonId": von_id,
            "zielId": z["id"],
            "name": z["name"],
            "art": z["art"],
            "runden": int(z["runden"]),
        })


def aus_fuer(stand: dict, person_id: str) -> list[dict]:
    return [e for e in stand.get("aus") or [] if e.get("traegerId") == person_id]


def deck_aus(stand: dict, person_id: str) -> set[str]:
    return {
        e["zielId"]
        for e in aus_fuer(stand, person_id)
        if e.get("art") == "deck"
    }


async def tick(campaign_id: str, neue_runde: int) -> None:
    """Rundenwechsel: ICE voll, EW-Bonus läuft ab, Schalter ticken."""
    kampf = await lade(campaign_id)
    if kampf is None:
        return
    voll = await repository.hole(campaign_id)
    personen = set((kampf["stand"].get("ice") or {})) | set((kampf["stand"].get("ew") or {}))
    if voll:
        personen |= {t["personId"] for t in voll["teilnehmer"] if t.get("personId")}
    maxima = {pid: await basis_ice(campaign_id, pid) for pid in personen}
    alt = list(kampf["stand"].get("aus") or [])
    stand = matrix.runde_auffuellen(kampf["stand"], neue_runde, maxima)
    await speichere(campaign_id, stand)
    for eintrag in matrix.abgefallene(alt, stand["aus"], "konsole"):
        await drohnen_zurueck(campaign_id, eintrag.get("gesprungeneIds") or [])
        if eintrag.get("traegerId"):
            await hot_wahl_frei(campaign_id, eintrag["traegerId"])
