"""Rassen: Katalog global, Freigabe je Kampagne.

**Zwei Ebenen** (Marks Vorgabe vom 11.09.2026): der Baukasten pflegt einen
gemeinsamen Katalog — dieselbe Idee wie beim TraitDef-Katalog, der auch am
Ruleset hängt und nicht an einer Kampagne. Welche dieser Rassen in einer
*bestimmten* Runde wählbar sind, entscheidet der Spielleiter aber pro
Kampagne: *"es sollten nicht automatisch alle zur Verfügung stehen, sondern
nur ausgewählte"*. Das ist die Beziehung `(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`.

**Die Kennung ist eine UUID und enthält NICHT den Namen.** Genau daran ist
der Trait-Katalog gescheitert (siehe Stolperstein 6 in CLAUDE.md): dort lautet
sie `ruleset:category:name`, weshalb das Umbenennen von "Arete" zu "Hexkraft"
einen zweiten, leeren Knoten erzeugte statt den alten umzubenennen. Der
Baukasten soll Rassen umbenennen können, ohne dass so etwas passiert.

`Person.rasse` speichert weiterhin den **Namen**, nicht die Kennung — der Wert
wird an vielen Stellen als Text gebraucht (etwa "Unbekannter Ork" in der
Spielersicht des Kampfes, siehe kampf/sichtbarkeit.py). Damit dadurch nichts
verwaist, zieht `aendern` eine Umbenennung auf alle betroffenen Personen nach.
"""

import json
import uuid

from app.db.neo4j_driver import get_driver

RULESET = "neotopia"

FELDER = """
    r.id AS id, r.name AS name, r.beschreibung AS beschreibung, r.bildUrl AS bildUrl,
    r.modifikatoren AS modifikatoren, r.freiePunkte AS freiePunkte, r.sortOrder AS sortOrder
"""


def _decode(record: dict) -> dict:
    """Wie in items/repository.py: für jede Eigenschaft einen Rückfall, sonst
    reisst ein fehlendes Feld aus Bestandsdaten die ganze Liste mit."""
    daten = dict(record)
    try:
        daten["modifikatoren"] = json.loads(daten["modifikatoren"]) if daten.get("modifikatoren") else {}
    except (json.JSONDecodeError, TypeError):
        daten["modifikatoren"] = {}
    daten["name"] = daten.get("name") or ""
    daten["beschreibung"] = daten.get("beschreibung") or ""
    daten["bildUrl"] = daten.get("bildUrl") or ""
    # Neo4j kann Zahlenlisten direkt, anders als Maps — deshalb hier kein JSON.
    daten["freiePunkte"] = [int(p) for p in (daten.get("freiePunkte") or [])]
    daten["sortOrder"] = int(daten.get("sortOrder") or 0)
    return daten


async def liste() -> list[dict]:
    """Der ganze Katalog — für den Baukasten der Spielleitung."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (r:Rasse {{ruleset: $ruleset}}) RETURN {FELDER} ORDER BY r.sortOrder, r.name",
            ruleset=RULESET,
        )
        return [_decode(dict(rec)) async for rec in result]


async def liste_fuer_kampagne(campaign_id: str) -> list[dict]:
    """Nur die in dieser Kampagne freigegebenen Rassen — für die Erstellung."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (c:Campaign {{id: $campaign_id}})-[:ERLAUBT_RASSE]->(r:Rasse)
            RETURN {FELDER} ORDER BY r.sortOrder, r.name
            """,
            campaign_id=campaign_id,
        )
        return [_decode(dict(rec)) async for rec in result]


async def freigegebene_ids(campaign_id: str) -> list[str]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign {id: $campaign_id})-[:ERLAUBT_RASSE]->(r:Rasse) RETURN r.id AS id",
            campaign_id=campaign_id,
        )
        return [rec["id"] async for rec in result]


async def hole(rasse_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (r:Rasse {{id: $id}}) RETURN {FELDER}", id=rasse_id
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def anlegen(daten: dict) -> dict:
    """Neue Rasse im Katalog. Noch in keiner Kampagne freigegeben — das ist
    ein zweiter, bewusster Schritt der Spielleitung."""
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            f"""
            CREATE (r:Rasse {{
                id: $id, ruleset: $ruleset, name: $name, beschreibung: $beschreibung,
                bildUrl: '', modifikatoren: $modifikatoren, freiePunkte: $freiePunkte,
                sortOrder: $sortOrder
            }})
            RETURN {FELDER}
            """,
            id=neue_id,
            ruleset=RULESET,
            name=daten["name"],
            beschreibung=daten.get("beschreibung") or "",
            modifikatoren=json.dumps(daten.get("modifikatoren") or {}),
            freiePunkte=[int(p) for p in (daten.get("freiePunkte") or [])],
            sortOrder=int(daten.get("sortOrder") or 0),
        )
        return _decode(dict(await result.single()))


async def aendern(rasse_id: str, daten: dict) -> dict | None:
    """Ändert eine Rasse — und zieht eine Umbenennung auf die Personen nach.

    `Person.rasse` hält den Namen (siehe Modulkommentar). Ohne das Nachziehen
    stünde nach dem Umbenennen bei bestehenden Charakteren eine Rasse, die es
    nicht mehr gibt.
    """
    aenderung = {k: v for k, v in daten.items() if v is not None}
    if not aenderung:
        return await hole(rasse_id)

    vorher = await hole(rasse_id)
    if vorher is None:
        return None

    if "modifikatoren" in aenderung:
        aenderung["modifikatoren"] = json.dumps(aenderung["modifikatoren"])
    if "freiePunkte" in aenderung:
        aenderung["freiePunkte"] = [int(p) for p in aenderung["freiePunkte"]]

    setzen = ", ".join(f"r.{k} = ${k}" for k in aenderung)
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (r:Rasse {{id: $id}}) SET {setzen} RETURN {FELDER}",
            id=rasse_id,
            **aenderung,
        )
        record = await result.single()
        if record is None:
            return None

        neuer_name = aenderung.get("name")
        if neuer_name and neuer_name != vorher["name"]:
            await session.run(
                "MATCH (p:Person {rasse: $alt}) SET p.rasse = $neu",
                alt=vorher["name"],
                neu=neuer_name,
            )
        return _decode(dict(record))


async def loeschen(rasse_id: str) -> bool:
    """Löscht eine Rasse aus dem Katalog — samt aller Freigaben.

    Bestehende Charaktere behalten ihren Rassennamen als Text; ihr Bogen
    bleibt also lesbar, sie lässt sich nur nicht mehr neu wählen. Das ist
    gewollt: eine gespielte Figur soll nicht rückwirkend rasselos werden,
    bloss weil die Spielleitung im Baukasten aufräumt.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (r:Rasse {id: $id}) DETACH DELETE r RETURN count(r) AS weg", id=rasse_id
        )
        record = await result.single()
        return bool(record and record["weg"])


async def setze_freigabe(campaign_id: str, rasse_ids: list[str]) -> list[str]:
    """Welche Rassen in dieser Kampagne wählbar sind — ersetzt die bisherige
    Auswahl vollständig (die Oberfläche schickt immer den ganzen Satz)."""
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "MATCH (:Campaign {id: $campaign_id})-[e:ERLAUBT_RASSE]->() DELETE e",
            campaign_id=campaign_id,
        )
        if rasse_ids:
            await session.run(
                """
                MATCH (c:Campaign {id: $campaign_id})
                UNWIND $ids AS rid
                MATCH (r:Rasse {id: rid})
                MERGE (c)-[:ERLAUBT_RASSE]->(r)
                """,
                campaign_id=campaign_id,
                ids=rasse_ids,
            )
    return await freigegebene_ids(campaign_id)


async def setze_bild(rasse_id: str, bild_url: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            f"MATCH (r:Rasse {{id: $id}}) SET r.bildUrl = $url RETURN {FELDER}",
            id=rasse_id,
            url=bild_url,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def seed_rassen() -> None:
    """Übernimmt die fünf eingebauten Rassen einmalig in die Datenbank.

    Läuft bei jedem Start (wie `traits/seed.py`), tut danach aber nichts mehr:
    gesucht wird über den **Namen**, angelegt nur was fehlt. Eine im Baukasten
    umbenannte oder gelöschte Rasse kommt also nicht wieder — sonst könnte die
    Spielleitung nichts dauerhaft ändern.

    Bestehende Kampagnen bekommen alle vorhandenen Rassen freigegeben. Ohne
    das stünde nach dem Update plötzlich keine Rasse mehr zur Wahl, obwohl
    vorher alle fünf offen waren — die Freigabe ist neu, das bisherige
    Verhalten war "alle".
    """
    from app.traits.erstellung import RASSEN

    driver = get_driver()
    async with driver.session() as session:
        for i, (name, daten) in enumerate(RASSEN.items()):
            await session.run(
                """
                MATCH (r:Rasse {ruleset: $ruleset, name: $name})
                WITH count(r) AS vorhanden
                WHERE vorhanden = 0
                CREATE (:Rasse {
                    id: $id, ruleset: $ruleset, name: $name, beschreibung: $beschreibung,
                    bildUrl: '', modifikatoren: $modifikatoren, freiePunkte: $freiePunkte,
                    sortOrder: $sortOrder
                })
                """,
                id=str(uuid.uuid4()),
                ruleset=RULESET,
                name=name,
                beschreibung=daten["beschreibung"],
                modifikatoren=json.dumps(daten["modifikatoren"]),
                freiePunkte=daten["freiePunkte"],
                sortOrder=i + 1,
            )

        # Kampagnen ohne jede Freigabe bekommen alles — siehe Docstring.
        await session.run(
            """
            MATCH (c:Campaign)
            WHERE NOT (c)-[:ERLAUBT_RASSE]->()
            MATCH (r:Rasse {ruleset: $ruleset})
            MERGE (c)-[:ERLAUBT_RASSE]->(r)
            """,
            ruleset=RULESET,
        )

    await _rassenmaxima_nachtragen()


async def _rassenmaxima_nachtragen() -> int:
    """Trägt den Rassendeckel bei Charakteren nach, die vor dem Bugfix
    erstellt wurden.

    Bis 11.09.2026 schrieb die Erstellung nur die Werte, nie das Maximum
    (`set_ratings_bulk` kannte kein `maxOverride`) — der Rassenmodifikator
    verpuffte also nach der Erstellung, und jedes Attribut fiel auf das
    Katalogmaximum zurück. Diese Nachbesserung holt das für bestehende
    Charaktere nach.

    **Setzt nur, wo noch nichts steht.** Ein von der Spielleitung von Hand
    angehobenes Maximum (die Elder-NPC mit Schusswaffen 8) bleibt damit
    unangetastet — sonst würde ein Serverstart ihre Sonderregelung
    zurücksetzen.
    """
    # Die Modifikatoren liegen als JSON-Text am Knoten (Neo4j kann keine
    # Maps als Eigenschaft). Sie hier in Python zu lesen statt im Cypher
    # spart die Abhängigkeit von APOC, das in dieser Installation nicht
    # vorausgesetzt ist.
    gesamt = 0
    driver = get_driver()
    async with driver.session() as session:
        for rasse in await liste():
            if not rasse["modifikatoren"]:
                continue
            result = await session.run(
                """
                UNWIND keys($mods) AS attribut
                MATCH (p:Person {rasse: $name})-[h:HAS_TRAIT]->(t:TraitDef {ruleset: $ruleset, name: attribut})
                WHERE h.maxOverride IS NULL
                SET h.maxOverride = t.defaultMax + $mods[attribut]
                RETURN count(h) AS gesetzt
                """,
                name=rasse["name"],
                mods=rasse["modifikatoren"],
                ruleset=RULESET,
            )
            record = await result.single()
            gesamt += record["gesetzt"] if record else 0
    if gesamt:
        print(f"[seed] Rassenmaxima nachgetragen: {gesamt} Attribut(e)")
    return gesamt
