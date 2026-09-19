"""Party — wer gerade zusammen unterwegs ist.

Ursprüngliche Vision (Neotopia-Wiki, 28.08.2026, damals in CLAUDE.md
festgehalten und beim großen Verschlankungs-Commit verlorengegangen — hier
wieder aufgegriffen und umgesetzt): "Spieler bilden nicht immer eine
einzige feste Gruppe — sie können sich aufteilen (2 gehen shoppen, 2 gehen
zu einem NPC), wodurch mehrere gleichzeitige Partys entstehen." Mark wollte
z.B. einer Party einen Ort zuweisen und einer anderen einen NPC/ein Event.

**Abgrenzung zu Fraktion:** eine Fraktion ist eine dauerhafte Organisation
mit eigenen Zielen/Ressourcen (Konzern, Gang). Eine Party hat keine eigenen
Absichten — sie ist schlicht "wer gerade beisammen ist". Trotzdem als
dauerhaftes Objekt angelegt (Marks Entscheidung, 18.09.2026): einmal
angelegt, bleibt sie bestehen (auch leer), bis sie explizit gelöscht wird —
kein Ad-hoc-Wegwerfobjekt.

**Drei Beziehungen, alle nach demselben Muster wie
`begleiter/repository.py::besitzer_setzen`** (alte Kante löschen, neue
setzen, kein Verwaisen möglich):

- `(:Person)-[:MITGLIED_VON]->(:Party)` — eine Person ist höchstens in einer
  Party gleichzeitig (Marks Entscheidung). Tritt sie einer neuen bei,
  verlässt sie automatisch die alte.
- `(:Party)-[:BEFINDET_SICH_AN]->(:Ort|:Event)` — optional, analog zur
  Gegenstands-Ablage (`items/repository.py::set_ablage`). Eine Party ohne
  Ziel ist schlicht "unterwegs".
- **Aktiv-Exklusivität**: höchstens eine Party pro Kampagne ist `aktiv`
  (Property, kein Kanten-Muster nötig) — die aktive Party ist die gerade
  bespielte, ihr Aufenthaltsort soll später die Musik auslösen
  (Spotify/Yamaha-MusicCast-Anbindung, noch nicht gebaut, siehe CLAUDE.md).
  Aktivieren einer Party deaktiviert automatisch alle anderen der Kampagne —
  dasselbe Prinzip wie ein aktiver Kampf (`kampf/repository.py`).
"""

import uuid

from app.db.neo4j_driver import get_driver

RETURN_FIELDS = """
    party.id AS id, party.name AS name, party.beschreibung AS beschreibung,
    party.notizen AS notizen, party.aktiv AS aktiv,
    party.sichtbarkeit AS sichtbarkeit, party.sichtbarFuer AS sichtbarFuer,
    ziel.id AS aufenthaltsortId, coalesce(ziel.name, ziel.title) AS aufenthaltsortName,
    CASE WHEN ziel IS NULL THEN NULL ELSE labels(ziel)[0] END AS aufenthaltsortKind,
    [m IN mitglieder | {id: m.id, name: m.name, personType: m.personType}] AS mitglieder
"""

# Vor RETURN_FIELDS nötig: Mitglieder und Aufenthaltsort separat sammeln,
# damit die spätere Liste nicht durch das kartesische Produkt zweier
# OPTIONAL MATCHes vervielfacht wird (Neo4j würde sonst pro
# Mitglied-x-Aufenthaltsort-Kombination eine Zeile liefern).
_MITGLIEDER_UND_ZIEL = """
    OPTIONAL MATCH (m:Person)-[:MITGLIED_VON]->(party)
    WITH party, collect(m) AS mitglieder
    OPTIONAL MATCH (party)-[:BEFINDET_SICH_AN]->(ziel)
"""


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["beschreibung"] = daten.get("beschreibung") or ""
    daten["notizen"] = daten.get("notizen") or ""
    daten["aktiv"] = bool(daten.get("aktiv"))
    daten["sichtbarkeit"] = daten.get("sichtbarkeit") or "GM"
    daten["sichtbarFuer"] = daten.get("sichtbarFuer") or []
    daten["mitglieder"] = daten.get("mitglieder") or []
    return daten


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (party:Party {{campaignId: $campaign_id}})
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
        ORDER BY party.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode(dict(r)) async for r in result]


async def einzeln(campaign_id: str, party_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (party:Party {{id: $id, campaignId: $campaign_id}})
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=party_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def anlegen(campaign_id: str, daten: dict) -> dict | None:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (party:Party {{
            id: $id, campaignId: $campaign_id, name: $name,
            beschreibung: $beschreibung, notizen: $notizen, aktiv: false,
            sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        }})
        CREATE (c)-[:HAT_ENTITAET]->(party)
        WITH party
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            id=neue_id,
            name=daten["name"],
            beschreibung=daten["beschreibung"],
            notizen=daten["notizen"],
            sichtbarkeit=daten["sichtbarkeit"],
            sichtbarFuer=daten["sichtbarFuer"],
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def aendern(campaign_id: str, party_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if not geaendert:
        return await einzeln(campaign_id, party_id)

    driver = get_driver()
    setzen = ", ".join(f"party.{f} = ${f}" for f in geaendert)
    query = f"""
        MATCH (party:Party {{id: $id, campaignId: $campaign_id}})
        SET {setzen}
        WITH party
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, id=party_id, **geaendert)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def mitglied_hinzufuegen(campaign_id: str, party_id: str, person_id: str) -> dict | None:
    """Nimmt eine Person in die Party auf — verlässt dabei automatisch eine
    etwaige vorherige Party (eine Person ist höchstens in einer Party
    gleichzeitig, Marks Entscheidung 18.09.2026)."""
    driver = get_driver()
    query = f"""
        MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
        MATCH (p:Person {{id: $person_id, campaignId: $campaign_id}})
        OPTIONAL MATCH (p)-[alt:MITGLIED_VON]->(:Party)
        DELETE alt
        CREATE (p)-[:MITGLIED_VON]->(party)
        WITH party
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, party_id=party_id, person_id=person_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def mitglied_entfernen(campaign_id: str, party_id: str, person_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
        OPTIONAL MATCH (p:Person {{id: $person_id, campaignId: $campaign_id}})-[r:MITGLIED_VON]->(party)
        DELETE r
        WITH party
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, party_id=party_id, person_id=person_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def aufenthaltsort_setzen(campaign_id: str, party_id: str, ziel_id: str | None, ziel_kind: str | None) -> dict | None:
    """Setzt oder löst den Aufenthaltsort — dieselbe "alte Kante weg, neue
    rein"-Logik wie bei der Gegenstands-Ablage. `ziel_id=None` heißt
    "unterwegs, kein fester Ort"."""
    driver = get_driver()
    async with driver.session() as session:
        if ziel_id and ziel_kind in ("Ort", "Event"):
            query = f"""
                MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
                MATCH (neu:{ziel_kind} {{id: $ziel_id, campaignId: $campaign_id}})
                OPTIONAL MATCH (party)-[alt:BEFINDET_SICH_AN]->()
                DELETE alt
                CREATE (party)-[:BEFINDET_SICH_AN]->(neu)
                WITH party
                {_MITGLIEDER_UND_ZIEL}
                RETURN {RETURN_FIELDS}
            """
            result = await session.run(query, campaign_id=campaign_id, party_id=party_id, ziel_id=ziel_id)
        else:
            query = f"""
                MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
                OPTIONAL MATCH (party)-[alt:BEFINDET_SICH_AN]->()
                DELETE alt
                WITH party
                {_MITGLIEDER_UND_ZIEL}
                RETURN {RETURN_FIELDS}
            """
            result = await session.run(query, campaign_id=campaign_id, party_id=party_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def aktivieren(campaign_id: str, party_id: str) -> dict | None:
    """Macht diese Party zur aktiven — deaktiviert dabei automatisch alle
    anderen der Kampagne (höchstens eine Party ist gleichzeitig aktiv,
    Marks Entscheidung 18.09.2026: die aktive Party löst später die Musik
    aus, die zu ihrem Aufenthaltsort gehört)."""
    driver = get_driver()
    query = f"""
        MATCH (andere:Party {{campaignId: $campaign_id}})
        WHERE andere.id <> $party_id
        SET andere.aktiv = false
        WITH count(andere) AS _
        MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
        SET party.aktiv = true
        WITH party
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, party_id=party_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def deaktivieren(campaign_id: str, party_id: str) -> dict | None:
    """Setzt nur diese Party auf inaktiv, ohne eine andere zu aktivieren —
    z.B. wenn die SL eine Pause macht und niemand gerade "dran" ist."""
    driver = get_driver()
    query = f"""
        MATCH (party:Party {{id: $party_id, campaignId: $campaign_id}})
        SET party.aktiv = false
        WITH party
        {_MITGLIEDER_UND_ZIEL}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, party_id=party_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def loeschen(campaign_id: str, party_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (party:Party {id: $id, campaignId: $campaign_id})
            DETACH DELETE party
            RETURN count(party) AS geloescht
            """,
            campaign_id=campaign_id,
            id=party_id,
        )
        record = await result.single()
        return bool(record and record["geloescht"])


async def get_party_von_person(campaign_id: str, person_id: str) -> dict | None:
    """Die Party, in der diese Person gerade Mitglied ist — oder None."""
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:MITGLIED_VON]->(party:Party)
        RETURN party.id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        if record is None:
            return None
        return await einzeln(campaign_id, record["id"])
