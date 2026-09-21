"""Begleiter — Sprites, Geister und alles, was jemandem zur Seite steht.

Sie teilen sich ein Blatt mit Drohnen und Fahrzeugen: `Neotopia.xlsx`, Blatt
*DrohneFahrzeug*, ist überschrieben mit **"Drohne / Fahrzeug / Sprite /
Geist"** — dieselben vier Werte, dieselben vier freien Fertigkeiten.

Trotzdem **kein Gegenstand**, anders als das Fahrzeug: einen Geist trägt man
nicht im Rucksack, er hat kein Gewicht, keinen Preis und keinen
Aufbewahrungsort. Alles, was Gegenstände an Inventarlogik mitbringen, wäre
hier sinnlos oder irreführend.

Die Werte selbst liegen in `app/traits/begleiterblatt.py`, damit Fahrzeug und
Geist nicht auseinanderlaufen.

**KI (19.09.2026):** ein weiterer `art`-Wert auf demselben Knoten, mit
eigenen Zusatzfeldern (KI-Attribute) und einer eigenen Kantenart
`HAT_EINFLUSS_AUF` zu Ort/Fraktion/Event/Gegenstand — siehe
`einfluss_setzen`/`einfluss_entfernen`.

**CRITTER (20.09.2026, revidiert):** Tiere/Haustiere sind KEIN Begleiter-Art
mehr — Mark: "wir machen critter zu richtigen NPCs". Sie leben als echte
`Person`-Knoten (`istCritter=true`) in `app/entities/`, mit dem vollen
NPC-Charakterblatt statt des Drohne/Fahrzeug-Blatts. `loyalitaet`/
`ausbildung` sind deshalb aus diesem Modul entfernt.
"""

import json
import uuid

from app.db.neo4j_driver import get_driver

RETURN_FIELDS = """
    b.id AS id, b.name AS name, b.art AS art, b.beziehung AS beziehung,
    b.beschreibung AS beschreibung, b.notizen AS notizen,
    b.bildUrl AS bildUrl,
    b.stufe AS stufe, b.widerstand AS widerstand, b.angriff AS angriff,
    b.agilitaet AS agilitaet, b.fertigkeiten AS fertigkeiten,
    b.waffe AS waffe, b.waffenSchaden AS waffenSchaden, b.schadensart AS schadensart,
    b.charisma AS charisma, b.manipulation AS manipulation, b.fassung AS fassung,
    b.intelligenz AS intelligenz, b.geistesschaerfe AS geistesschaerfe,
    b.entschlossenheit AS entschlossenheit, b.matrixPraesenz AS matrixPraesenz,
    b.erfahrung AS erfahrung, b.erfahrungAusgegeben AS erfahrungAusgegeben,
    b.sichtbarkeit AS sichtbarkeit, b.sichtbarFuer AS sichtbarFuer,
    p.id AS besitzerId, p.name AS besitzerName, einfluss
"""

# Sammelt die Einfluss-Kanten eines Begleiters als Liste von Dicts. Eigene
# Subquery statt eines simplen OPTIONAL MATCH im Hauptpfad, weil sonst jede
# Kombination aus BEGLEITET-Kante und Einfluss-Kante das Ergebnis
# vervielfachen würde (gleiches Problem wie bei Party — siehe dort
# `_MITGLIEDER_UND_ZIEL`). `ziel.name` deckt Ort/Fraktion/Gegenstand ab,
# `ziel.title` das Event (einziger Entitätstyp mit anderem Namensfeld).
_EINFLUSS_SUBQUERY = """
    CALL (b) {
        OPTIONAL MATCH (b)-[r:HAT_EINFLUSS_AUF]->(ziel)
        WITH ziel, r WHERE ziel IS NOT NULL
        RETURN collect({
            zielKind: labels(ziel)[0], zielId: ziel.id,
            zielName: coalesce(ziel.name, ziel.title, ''), stufe: r.stufe
        }) AS einfluss
    }
"""

# Felder, die per SET/CREATE geschrieben werden (ohne Einfluss — der läuft
# über eigene Kanten, siehe unten).
_SCHREIBBARE_FELDER = [
    "name", "art", "beziehung", "beschreibung", "notizen", "bildUrl",
    "stufe", "widerstand", "angriff", "agilitaet", "fertigkeiten",
    "waffe", "waffenSchaden", "schadensart",
    "charisma", "manipulation", "fassung", "intelligenz", "geistesschaerfe",
    "entschlossenheit", "matrixPraesenz",
    "erfahrung", "erfahrungAusgegeben",
    "sichtbarkeit", "sichtbarFuer",
]

# Erlaubte Ziel-Typen für Einfluss-Kanten — siehe schemas.EinflussZielKind.
_EINFLUSS_ZIELE = {"Ort", "Fraktion", "Event", "Gegenstand"}


def _decode(record: dict) -> dict:
    """Ausgangswerte für alles, was Bestandsdaten noch nicht kennen.

    Gleiche Vorsicht wie bei den Gegenständen (Stolperstein 9): ein fehlendes
    Pflichtfeld lässt sonst die ganze Liste mit 500 abstürzen.
    """
    daten = dict(record)
    for feld in ("name", "art", "beziehung", "beschreibung", "notizen", "waffe", "schadensart", "bildUrl"):
        daten[feld] = daten.get(feld) or ""
    for feld in (
        "stufe", "widerstand", "angriff", "agilitaet", "waffenSchaden",
        "charisma", "manipulation", "fassung", "intelligenz", "geistesschaerfe",
        "entschlossenheit", "matrixPraesenz",
        "erfahrung", "erfahrungAusgegeben",
    ):
        daten[feld] = daten.get(feld) or 0
    daten["art"] = daten["art"] or "BEGLEITER"
    daten["sichtbarkeit"] = daten.get("sichtbarkeit") or "GM"
    daten["sichtbarFuer"] = daten.get("sichtbarFuer") or []
    daten["einfluss"] = daten.get("einfluss") or []
    try:
        roh = daten.get("fertigkeiten")
        daten["fertigkeiten"] = json.loads(roh) if roh else {}
    except (json.JSONDecodeError, TypeError):
        daten["fertigkeiten"] = {}
    return daten


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{campaignId: $campaign_id}})
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        {_EINFLUSS_SUBQUERY}
        RETURN {RETURN_FIELDS}
        ORDER BY b.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode(r) async for r in result]


async def anlegen(campaign_id: str, besitzer_person_id: str | None, daten: dict) -> dict | None:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    erzeuge = """
        MATCH (c:Campaign {id: $campaign_id})
        CREATE (b:Begleiter {
            id: $id, campaignId: $campaign_id, name: $name, art: $art,
            beziehung: $beziehung, beschreibung: $beschreibung, notizen: $notizen,
            bildUrl: $bildUrl,
            stufe: $stufe, widerstand: $widerstand, angriff: $angriff, agilitaet: $agilitaet,
            fertigkeiten: $fertigkeiten, waffe: $waffe, waffenSchaden: $waffenSchaden,
            schadensart: $schadensart,
            charisma: $charisma, manipulation: $manipulation, fassung: $fassung,
            intelligenz: $intelligenz, geistesschaerfe: $geistesschaerfe,
            entschlossenheit: $entschlossenheit, matrixPraesenz: $matrixPraesenz,
            erfahrung: $erfahrung, erfahrungAusgegeben: $erfahrungAusgegeben,
            sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        })
        CREATE (c)-[:HAT_ENTITAET]->(b)
    """
    if besitzer_person_id:
        query = f"""
            {erzeuge}
            WITH b
            MATCH (p:Person {{id: $besitzer_id, campaignId: $campaign_id}})
            CREATE (b)-[:BEGLEITET]->(p)
            WITH b, p
            {_EINFLUSS_SUBQUERY}
            RETURN {RETURN_FIELDS}
        """
    else:
        # Ohne Person: ein Geist, den noch niemand gebunden hat.
        query = f"""
            {erzeuge}
            WITH b
            OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
            {_EINFLUSS_SUBQUERY}
            RETURN {RETURN_FIELDS}
        """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            besitzer_id=besitzer_person_id,
            id=neue_id,
            name=daten["name"],
            art=daten["art"],
            beziehung=daten["beziehung"],
            beschreibung=daten["beschreibung"],
            notizen=daten["notizen"],
            bildUrl=daten.get("bildUrl") or "",
            stufe=daten["stufe"],
            widerstand=daten["widerstand"],
            angriff=daten["angriff"],
            agilitaet=daten["agilitaet"],
            fertigkeiten=json.dumps(daten.get("fertigkeiten") or {}),
            waffe=daten["waffe"],
            waffenSchaden=daten["waffenSchaden"],
            schadensart=daten["schadensart"],
            charisma=daten.get("charisma") or 0,
            manipulation=daten.get("manipulation") or 0,
            fassung=daten.get("fassung") or 0,
            intelligenz=daten.get("intelligenz") or 0,
            geistesschaerfe=daten.get("geistesschaerfe") or 0,
            entschlossenheit=daten.get("entschlossenheit") or 0,
            matrixPraesenz=daten.get("matrixPraesenz") or 0,
            erfahrung=daten.get("erfahrung") or 0,
            erfahrungAusgegeben=daten.get("erfahrungAusgegeben") or 0,
            sichtbarkeit=daten["sichtbarkeit"],
            sichtbarFuer=daten["sichtbarFuer"],
        )
        record = await result.single()
        return _decode(record) if record else None


async def aendern(campaign_id: str, begleiter_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if "fertigkeiten" in geaendert:
        geaendert["fertigkeiten"] = json.dumps(geaendert["fertigkeiten"])
    if not geaendert:
        return await einzeln(campaign_id, begleiter_id)

    driver = get_driver()
    setzen = ", ".join(f"b.{f} = ${f}" for f in geaendert)
    query = f"""
        MATCH (b:Begleiter {{id: $id, campaignId: $campaign_id}})
        SET {setzen}
        WITH b
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        {_EINFLUSS_SUBQUERY}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=begleiter_id, **geaendert)
        record = await result.single()
        return _decode(record) if record else None


async def einzeln(campaign_id: str, begleiter_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{id: $id, campaignId: $campaign_id}})
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        {_EINFLUSS_SUBQUERY}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=begleiter_id)
        record = await result.single()
        return _decode(record) if record else None


async def besitzer_setzen(campaign_id: str, begleiter_id: str, person_id: str | None) -> dict | None:
    """Bindet den Begleiter an eine Person — oder löst die Bindung."""
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{id: $id, campaignId: $campaign_id}})
        OPTIONAL MATCH (b)-[alt:BEGLEITET]->(:Person)
        DELETE alt
        WITH b
        OPTIONAL MATCH (neu:Person {{id: $person_id, campaignId: $campaign_id}})
        FOREACH (_ IN CASE WHEN neu IS NULL THEN [] ELSE [1] END |
            CREATE (b)-[:BEGLEITET]->(neu)
        )
        WITH b
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        {_EINFLUSS_SUBQUERY}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=begleiter_id, person_id=person_id)
        record = await result.single()
        return _decode(record) if record else None


async def einfluss_setzen(
    campaign_id: str, begleiter_id: str, ziel_kind: str, ziel_id: str, stufe: int
) -> dict | None:
    """Setzt (oder aktualisiert) eine Einfluss-Stufe auf ein Ziel.

    `MERGE` auf die Kante statt CREATE: ein zweites Setzen auf dasselbe Ziel
    aktualisiert die Stufe, statt eine zweite Kante danebenzulegen. `stufe=0`
    wird bewusst NICHT automatisch gelöscht — eine Spielleitung könnte "0,
    aber im Blick behalten" von "gar keine Beziehung" unterscheiden wollen;
    zum echten Entfernen gibt es `einfluss_entfernen`.
    """
    if ziel_kind not in _EINFLUSS_ZIELE:
        return None
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{id: $begleiter_id, campaignId: $campaign_id}})
        MATCH (ziel:{ziel_kind} {{id: $ziel_id, campaignId: $campaign_id}})
        MERGE (b)-[r:HAT_EINFLUSS_AUF]->(ziel)
        SET r.stufe = $stufe
        WITH b
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        {_EINFLUSS_SUBQUERY}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, begleiter_id=begleiter_id, ziel_id=ziel_id, stufe=stufe
        )
        record = await result.single()
        return _decode(record) if record else None


async def einfluss_entfernen(campaign_id: str, begleiter_id: str, ziel_kind: str, ziel_id: str) -> dict | None:
    """Nimmt der SL im Kampf gezielt einen Einflussbereich weg — kappt die Kante ganz."""
    if ziel_kind not in _EINFLUSS_ZIELE:
        return None
    driver = get_driver()
    query = f"""
        MATCH (b:Begleiter {{id: $begleiter_id, campaignId: $campaign_id}})
        MATCH (b)-[r:HAT_EINFLUSS_AUF]->(ziel:{ziel_kind} {{id: $ziel_id, campaignId: $campaign_id}})
        DELETE r
        WITH b
        OPTIONAL MATCH (b)-[:BEGLEITET]->(p:Person)
        {_EINFLUSS_SUBQUERY}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, begleiter_id=begleiter_id, ziel_id=ziel_id)
        record = await result.single()
        return _decode(record) if record else None


async def loeschen(campaign_id: str, begleiter_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Begleiter {id: $id, campaignId: $campaign_id})
            DETACH DELETE b
            RETURN count(b) AS geloescht
            """,
            campaign_id=campaign_id,
            id=begleiter_id,
        )
        record = await result.single()
        return bool(record and record["geloescht"])
