"""Drogen schlucken: Uhren um die Funktionen, die Chrom schon hat.

Reine Funktionen, ohne Neo4j. Die Route und die Rast/Szene/Runde rufen sie
auf. Entscheidungen: docs/wiki/entities/drogen.md (04.11.2026).

Gifte sind die eine Ausnahme zur „keine Runden-Uhr“: sie ticken beim
Kampfrundenwechsel, solange die Wirkung läuft. Alles andere bleibt sofort,
Szene oder Rast.
"""

from __future__ import annotations

DAUERN = ("sofort", "szene", "rast")
HEIL_QUALITAETEN = ("", "minderwertig", "normal", "hochwertig")
NEBEN_SCHADEN = ("", "schlag", "aggraviert", "toedlich")
UMWANDELN = ("", "schlagZuToedlich", "allesZuAggraviert")
GIFT_ARTEN = ("", "schlag", "schwer", "aggraviert")


def heilen(schlag: int, schwer: int, aggraviert: int, menge: int, qualitaet: str) -> dict:
    """Heilmenge einer Droge. Hochwertig räumt Schlag und tödlich komplett,
    die Menge geht auf schwerheilbar. Normal: tödlich zuerst, Rest × 3 Schlag.
    Minderwertig: nur Schlag.
    """
    schlag = max(0, schlag)
    schwer = max(0, schwer)
    aggraviert = max(0, aggraviert)
    menge = max(0, menge)
    if menge <= 0 or qualitaet not in ("minderwertig", "normal", "hochwertig"):
        return _schaden(schlag, schwer, aggraviert)
    if qualitaet == "minderwertig":
        schlag = max(0, schlag - menge)
    elif qualitaet == "normal":
        ab = min(menge, schwer)
        schwer -= ab
        schlag = max(0, schlag - (menge - ab) * 3)
    else:
        schlag = 0
        schwer = 0
        aggraviert = max(0, aggraviert - menge)
    return _schaden(schlag, schwer, aggraviert)


def umwandeln(schlag: int, schwer: int, aggraviert: int, art: str) -> dict:
    """Vorhandenen Schaden verschieben, nichts addieren."""
    schlag = max(0, schlag)
    schwer = max(0, schwer)
    aggraviert = max(0, aggraviert)
    if art == "schlagZuToedlich":
        schwer += schlag
        schlag = 0
    elif art == "allesZuAggraviert":
        aggraviert += schlag + schwer
        schlag = 0
        schwer = 0
    return _schaden(schlag, schwer, aggraviert)


def schaden_drauf(schlag: int, schwer: int, aggraviert: int, art: str, menge: int) -> dict:
    """Nebenwirkung schreibt normalen Schaden: Schlag, tödlich, schwerheilbar."""
    schlag = max(0, schlag)
    schwer = max(0, schwer)
    aggraviert = max(0, aggraviert)
    menge = max(0, menge)
    if art == "schlag":
        schlag += menge
    elif art == "toedlich":
        schwer += menge
    elif art == "aggraviert":
        aggraviert += menge
    return _schaden(schlag, schwer, aggraviert)


def willenskraft_anwenden(verbraucht: int, maximum: int, delta: int) -> int:
    """Positiv gibt ausgegebene Willenskraft zurück, negativ verbraucht sie.
    Bleibt zwischen 0 und dem Maximum.
    """
    verbraucht = max(0, verbraucht)
    maximum = max(0, maximum)
    neu = verbraucht - delta
    return max(0, min(maximum, neu))


def reduktion_dazu(effektiv: int, drogen: int) -> int:
    """Droge addiert auf die effektive Reduktion, nicht in die Basis."""
    return max(0, effektiv) + max(0, drogen)


def einnahme_aus_vorlage(vorlage: dict) -> dict:
    """Kopie der Wirkung. Sofort-Drogen starten den Crash nicht hier —
    die Route ruft `starte_nebenwirkung`, damit Umwandeln vor dem
    Speichern passiert.
    """
    dauer = vorlage.get("wirkungDauer") or "szene"
    if dauer not in DAUERN:
        dauer = "szene"
    return {
        "name": vorlage.get("name") or "Droge",
        "gegenstandId": vorlage.get("id") or "",
        "phase": "wirkung",
        "dauer": dauer,
        "wirkungBoni": dict(vorlage.get("traitBoni") or {}),
        "nebenwirkungBoni": dict(vorlage.get("nebenwirkungBoni") or {}),
        "wirkungInitiative": int(vorlage.get("initiativeBonus") or 0),
        "nebenwirkungInitiative": int(vorlage.get("nebenwirkungInitiative") or 0),
        "ruestungReduktion": int(vorlage.get("ruestungReduktionBasis") or 0),
        "zusatzaktionen": int(vorlage.get("zusatzaktionen") or 0),
        "spez": dict(vorlage.get("ausruestungsSpezialisierungen") or {}),
        "willenskraftNebenwirkung": int(vorlage.get("willenskraftNebenwirkung") or 0),
        "schadenArt": vorlage.get("nebenwirkungSchaden") or "",
        "schadenMenge": int(vorlage.get("nebenwirkungSchadenMenge") or 0),
        "umwandeln": vorlage.get("umwandeln") or "",
        "giftMenge": int(vorlage.get("giftMenge") or 0),
        "giftArt": vorlage.get("giftArt") or "",
        "traitBoni": dict(vorlage.get("traitBoni") or {}),
        "initiativeBonus": int(vorlage.get("initiativeBonus") or 0),
        "toedlich": 0,
        "toedlichTicks": 0,
        "modus": "",
        "frisch": False,
    }


def starte_nebenwirkung(einnahme: dict) -> dict:
    """Plus ist vorbei. Crash-Felder werden aktuell, Modus hängt an der Uhr."""
    neu = dict(einnahme)
    neu["phase"] = "nebenwirkung"
    neu["traitBoni"] = dict(einnahme.get("nebenwirkungBoni") or {})
    neu["initiativeBonus"] = int(einnahme.get("nebenwirkungInitiative") or 0)
    neu["ruestungReduktion"] = 0
    neu["zusatzaktionen"] = 0
    neu["giftMenge"] = 0
    if einnahme.get("dauer") == "rast":
        neu["modus"] = "weitere-rast"
        neu["frisch"] = True
    else:
        neu["modus"] = "rast"
        neu["frisch"] = False
    return neu


def crash_auf_person(person: dict, einnahme: dict) -> dict:
    """Einmalig, wenn der Crash einsetzt: umwandeln, dann Schaden, Willenskraft.
    Umwandeln und zusätzlicher Schaden bleiben getrennt — ist umwandeln gesetzt,
    wird kein Schaden addiert.
    """
    schlag = int(person.get("schadenSchlag") or 0)
    schwer = int(person.get("schadenSchwer") or 0)
    aggraviert = int(person.get("schadenAggraviert") or 0)
    art = einnahme.get("umwandeln") or ""
    if art:
        gewandelt = umwandeln(schlag, schwer, aggraviert, art)
    else:
        gewandelt = schaden_drauf(
            schlag, schwer, aggraviert,
            einnahme.get("schadenArt") or "",
            int(einnahme.get("schadenMenge") or 0),
        )
    return {
        "schadenSchlag": gewandelt["schadenSchlag"],
        "schadenSchwer": gewandelt["schadenSchwer"],
        "schadenAggraviert": gewandelt["schadenAggraviert"],
    }


def rast_vor_heilung(einnahmen: list[dict]) -> tuple[list[dict], list[dict]]:
    """Wirkung-bis-Rast kippt vor der Heilung in den Crash. Liefert die
    Einnahmen, deren Crash in dieser Rast einsetzt — die Route wandelt
    damit um, bevor die Rast-Formel läuft.
    """
    bleiben = []
    crash = []
    for ein in einnahmen:
        if ein.get("phase") == "wirkung" and ein.get("dauer") == "rast":
            gestartet = starte_nebenwirkung(ein)
            crash.append(gestartet)
            if _nebenwirkung_bleibt(gestartet):
                bleiben.append(gestartet)
        else:
            bleiben.append(ein)
    return bleiben, crash


def rast_danach(einnahmen: list[dict]) -> list[dict]:
    """Nach der Heilung: die Rast zählt mit, auch die, die den Crash startet."""
    bleiben = []
    for ein in einnahmen:
        if ein.get("phase") != "nebenwirkung":
            bleiben.append(ein)
            continue
        modus = ein.get("modus") or "rast"
        if modus == "zwei-rasten":
            ticks = int(ein.get("toedlichTicks") or 0) + 1
            if ticks >= 2:
                continue
            neu = dict(ein)
            neu["toedlichTicks"] = ticks
            neu["frisch"] = False
            bleiben.append(neu)
        elif modus == "weitere-rast":
            if ein.get("frisch"):
                neu = dict(ein)
                neu["frisch"] = False
                bleiben.append(neu)
            # sonst: die weitere Rast ist diese, Crash ist vorbei
        else:
            # bis Rast: diese Rast räumt den Crash
            continue
    return bleiben


def szene_wechseln(einnahmen: list[dict]) -> tuple[list[dict], list[dict]]:
    """Szenen-Wirkung wird zum Crash bis zur nächsten Rast. Kein Tick."""
    bleiben = []
    crash = []
    for ein in einnahmen:
        if ein.get("phase") == "wirkung" and ein.get("dauer") == "szene":
            gestartet = starte_nebenwirkung(ein)
            gestartet["frisch"] = False
            crash.append(gestartet)
            if _nebenwirkung_bleibt(gestartet):
                bleiben.append(gestartet)
        else:
            bleiben.append(ein)
    return bleiben, crash


def gift_schaden(einnahmen: list[dict]) -> list[dict]:
    """Pro Kampfrunde, nur solange die Wirkung läuft. Sofort-Gifte ticken nicht."""
    treffer = []
    for ein in einnahmen:
        if ein.get("phase") != "wirkung":
            continue
        if ein.get("dauer") == "sofort":
            continue
        menge = int(ein.get("giftMenge") or 0)
        art = ein.get("giftArt") or ""
        if menge > 0 and art in ("schlag", "schwer", "aggraviert"):
            treffer.append({"name": ein.get("name") or "Gift", "art": art, "menge": menge})
    return treffer


def wirkende_boni(einnahmen: list[dict]) -> dict[str, int]:
    summe: dict[str, int] = {}
    for ein in einnahmen:
        for name, wert in (ein.get("traitBoni") or {}).items():
            summe[name] = summe.get(name, 0) + int(wert)
    return summe


def wirkende_initiative(einnahmen: list[dict]) -> int:
    return sum(int(ein.get("initiativeBonus") or 0) for ein in einnahmen)


def wirkende_reduktion(einnahmen: list[dict]) -> int:
    return sum(
        int(ein.get("ruestungReduktion") or 0)
        for ein in einnahmen
        if ein.get("phase") == "wirkung"
    )


def wirkende_spezialisierungen(einnahmen: list[dict]) -> dict[str, list[str]]:
    """Texte nur, solange die Wirkung läuft und der Name auch einen Bonus hat."""
    eintraege: dict[str, list[str]] = {}
    for ein in einnahmen:
        if ein.get("phase") != "wirkung":
            continue
        boni = ein.get("traitBoni") or {}
        spez = ein.get("spez") or {}
        for name in boni:
            for text in spez.get(name) or []:
                text = str(text)
                if not text:
                    continue
                bisher = eintraege.setdefault(name, [])
                if text not in bisher:
                    bisher.append(text)
    return eintraege


def wirkende_zusatzaktionen(einnahmen: list[dict]) -> list[dict]:
    return [
        {"name": ein.get("name") or "Droge", "zusatzaktionen": int(ein.get("zusatzaktionen") or 0), "id": ein.get("id")}
        for ein in einnahmen
        if ein.get("phase") == "wirkung" and int(ein.get("zusatzaktionen") or 0) != 0
    ]


def toedlich_summe(einnahmen: list[dict]) -> int:
    return sum(int(ein.get("toedlich") or 0) for ein in einnahmen if ein.get("phase") == "nebenwirkung")


def _nebenwirkung_bleibt(ein: dict) -> bool:
    if ein.get("traitBoni") or ein.get("initiativeBonus"):
        return True
    if int(ein.get("toedlich") or 0) > 0 or ein.get("modus") == "zwei-rasten":
        return True
    if ein.get("modus") in ("rast", "weitere-rast"):
        return bool(ein.get("traitBoni") or ein.get("initiativeBonus") or ein.get("toedlich"))
    return False


def _schaden(schlag: int, schwer: int, aggraviert: int) -> dict:
    return {
        "schadenSchlag": max(0, schlag),
        "schadenSchwer": max(0, schwer),
        "schadenAggraviert": max(0, aggraviert),
    }


# --- Neo4j: die Kopie, nicht das Stück ------------------------------------

import json
import uuid

from app.db.neo4j_driver import get_driver


def _pack(ein: dict) -> str:
    return json.dumps(ein, ensure_ascii=False)


def _unpack(roh: str | None) -> dict | None:
    if not roh:
        return None
    try:
        return json.loads(roh)
    except (json.JSONDecodeError, TypeError):
        return None


async def liste(campaign_id: str, person_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:HAT_EINNAHME]->(e:Einnahme)
        RETURN e.id AS id, e.payload AS payload
        ORDER BY e.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        einnahmen = []
        async for record in result:
            ein = _unpack(record["payload"])
            if ein is None:
                continue
            ein["id"] = record["id"]
            einnahmen.append(ein)
        return einnahmen


async def ersetzen(campaign_id: str, person_id: str, einnahmen: list[dict]) -> None:
    """Ersetzt alle laufenden Einnahmen dieser Person. Die Kopie ist die
    Wahrheit — die Vorlage darf sich danach ändern.
    """
    driver = get_driver()
    zeilen = []
    for ein in einnahmen:
        kopie = dict(ein)
        kopie.pop("id", None)
        zeilen.append({
            "id": ein.get("id") or str(uuid.uuid4()),
            "name": ein.get("name") or "Droge",
            "payload": _pack(kopie),
        })
    loeschen = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:HAT_EINNAHME]->(alt:Einnahme)
        DETACH DELETE alt
    """
    async with driver.session() as session:
        await session.run(loeschen, campaign_id=campaign_id, person_id=person_id)
        if not zeilen:
            return
        await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            UNWIND $zeilen AS z
            CREATE (e:Einnahme {id: z.id, campaignId: $campaign_id, name: z.name, payload: z.payload})
            CREATE (p)-[:HAT_EINNAHME]->(e)
            """,
            campaign_id=campaign_id,
            person_id=person_id,
            zeilen=zeilen,
        )


async def boni(campaign_id: str, person_id: str) -> dict[str, int]:
    return wirkende_boni(await liste(campaign_id, person_id))


async def initiative(campaign_id: str, person_id: str) -> int:
    return wirkende_initiative(await liste(campaign_id, person_id))


async def reduktion(campaign_id: str, person_id: str) -> int:
    return wirkende_reduktion(await liste(campaign_id, person_id))


async def zusatz(campaign_id: str, person_id: str) -> list[dict]:
    return wirkende_zusatzaktionen(await liste(campaign_id, person_id))


async def toedlich(campaign_id: str, person_id: str) -> int:
    return toedlich_summe(await liste(campaign_id, person_id))


async def wende_crashes(campaign_id: str, person_id: str, person: dict, crashes: list[dict]) -> dict:
    """Umwandeln und Nebenwirkungs-Schaden, bevor die Rast heilt."""
    from app.entities.repository import PERSON_FIELDS, update_node
    from app.items.repository import willenskraft_verlust
    from app.traits.bogen import willenskraft_max
    from app.traits.repository import get_ratings_for_entity

    werte = await get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: int(w.get("rating") or 0) for w in werte}
    maximum = willenskraft_max(nach_name, 0, await willenskraft_verlust(campaign_id, person_id))
    felder = {
        "schadenSchlag": int(person.get("schadenSchlag") or 0),
        "schadenSchwer": int(person.get("schadenSchwer") or 0),
        "schadenAggraviert": int(person.get("schadenAggraviert") or 0),
        "willenskraftVerbraucht": int(person.get("willenskraftVerbraucht") or 0),
    }
    for crash in crashes:
        felder.update(crash_auf_person(felder, crash))
        felder["willenskraftVerbraucht"] = willenskraft_anwenden(
            felder["willenskraftVerbraucht"], maximum, int(crash.get("willenskraftNebenwirkung") or 0),
        )
    aktualisiert = await update_node("Person", PERSON_FIELDS, campaign_id, person_id, felder)
    return aktualisiert or {**person, **felder}


async def szene_fuer(campaign_id: str, person_id: str) -> None:
    """Party hat Ort oder Event gewechselt. Szenen-Wirkung wird zum Crash."""
    einnahmen = await liste(campaign_id, person_id)
    bleiben, crash = szene_wechseln(einnahmen)
    if crash:
        from app.entities.repository import PERSON_FIELDS, get_node
        person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        if person is not None:
            await wende_crashes(campaign_id, person_id, person, crash)
    await ersetzen(campaign_id, person_id, bleiben)

