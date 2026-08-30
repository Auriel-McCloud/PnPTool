import uuid

from app.db.neo4j_driver import get_driver

_VISIBILITY_FIELDS = ["sichtbarkeit", "sichtbarFuer", "notizenSichtbarkeit", "notizenSichtbarFuer"]

# Felder des Charakterbogens. "weg" und "rasse" sind leer, solange niemand
# einen Charakter angelegt hat — NPCs brauchen sie meist gar nicht.
# Schaden wird nach Art getrennt gezählt (World of Darkness): Schlagschaden
# heilt schnell, schwerer Schaden langsam, aggravierter kaum. Angezeigt wird
# der schwerste zuerst, deshalb drei Zähler statt einer Summe.
_BOGEN_FELDER = [
    "weg",
    "rasse",
    "schadenSchlag",
    "schadenSchwer",
    "schadenAggraviert",
    "willenskraftVerbraucht",
    "iceSchaden",
    "erfahrung",
    "erfahrungAusgegeben",
    # Willenskraft ist abgeleitet (Entschlossenheit + Fassung); einzeln
    # gekaufte Punkte kommen als Bonus obendrauf.
    "willenskraftBonus",
    # Kopfzeile des Papierblatts (Neotopia.xlsx, Charakterblatt Zeilen 3-7).
    "konzept",
    "alter",
    "ambition",
    "verlangen",
    "ziel",
    "kapital",
    "schulden",
    # Solange die Erstellung nicht abgeschlossen ist, zeigt das Blatt den
    # Erstellungsablauf statt der Spielansicht.
    "erstellungAbgeschlossen",
]

PERSON_FIELDS = ["name", "personType", "description", "notes", *_BOGEN_FELDER, *_VISIBILITY_FIELDS]
ORT_FIELDS = ["name", "description", "notes", *_VISIBILITY_FIELDS]
EVENT_FIELDS = ["title", "timestamp", "description", "notes", *_VISIBILITY_FIELDS]


def _return_clause(alias: str, fields: list[str]) -> str:
    return ", ".join(f"{alias}.{f} AS {f}" for f in ["id", *fields])


# Ausgangswerte für die Bogenfelder. Bestandsdaten kennen sie nicht und
# liefern None — ohne Ersatz scheitert die Pydantic-Prüfung und reisst die
# komplette Liste mit 500 herunter (siehe Stolperstein 9 in CLAUDE.md).
_BOGEN_DEFAULTS: dict = {
    "weg": "KEINER",
    "rasse": "",
    "schadenSchlag": 0,
    "schadenSchwer": 0,
    "schadenAggraviert": 0,
    "willenskraftVerbraucht": 0,
    "iceSchaden": 0,
    "erfahrung": 0,
    "erfahrungAusgegeben": 0,
    "willenskraftBonus": 0,
    "konzept": "",
    "alter": "",
    "ambition": "",
    "verlangen": "",
    "ziel": "",
    "kapital": 0,
    "schulden": 0,
    "erstellungAbgeschlossen": False,
}


def _mit_defaults(record: dict) -> dict:
    """Ergänzt fehlende Bogenfelder. Nur Personen haben sie überhaupt."""
    daten = dict(record)
    for feld, ersatz in _BOGEN_DEFAULTS.items():
        if feld in daten and daten[feld] is None:
            daten[feld] = ersatz
    return daten


async def create_node(label: str, fields: list[str], campaign_id: str, data: dict) -> dict:
    driver = get_driver()
    node_id = str(uuid.uuid4())
    props = ", ".join(f"{f}: ${f}" for f in fields)
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (n:{label} {{id: $node_id, campaignId: $campaign_id, {props}}})
        CREATE (c)-[:HAT_ENTITAET]->(n)
        RETURN {_return_clause('n', fields)}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, node_id=node_id, **data)
        record = await result.single()
        return _mit_defaults(record)


async def list_nodes(label: str, fields: list[str], campaign_id: str, order_field: str = "name") -> list[dict]:
    driver = get_driver()
    query = f"MATCH (n:{label} {{campaignId: $campaign_id}}) RETURN {_return_clause('n', fields)} ORDER BY n.{order_field}"
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_mit_defaults(record) async for record in result]


async def get_node(label: str, fields: list[str], campaign_id: str, node_id: str) -> dict | None:
    driver = get_driver()
    query = f"MATCH (n:{label} {{id: $node_id, campaignId: $campaign_id}}) RETURN {_return_clause('n', fields)}"
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, node_id=node_id)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def update_node(label: str, fields: list[str], campaign_id: str, node_id: str, data: dict) -> dict | None:
    changed = {k: v for k, v in data.items() if v is not None}
    if not changed:
        return await get_node(label, fields, campaign_id, node_id)

    driver = get_driver()
    set_clause = ", ".join(f"n.{f} = ${f}" for f in changed)
    query = f"""
        MATCH (n:{label} {{id: $node_id, campaignId: $campaign_id}})
        SET {set_clause}
        RETURN {_return_clause('n', fields)}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, node_id=node_id, **changed)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def delete_node(label: str, campaign_id: str, node_id: str) -> bool:
    driver = get_driver()
    # OPTIONAL MATCH auf BESITZT ist ein No-op für Ort/Event (haben nie ausgehende
    # BESITZT-Kanten), räumt aber bei Person auch die Gegenstände mit weg statt
    # sie als verwaiste Knoten zurückzulassen.
    query = f"""
        MATCH (n:{label} {{id: $node_id, campaignId: $campaign_id}})
        OPTIONAL MATCH (n)-[:BESITZT]->(owned)
        DETACH DELETE n, owned
        RETURN count(n) AS deleted
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, node_id=node_id)
        record = await result.single()
        return dict(record)["deleted"] > 0


async def create_verbindung(campaign_id: str, data: dict) -> dict:
    driver = get_driver()
    edge_id = str(uuid.uuid4())
    von_kind = data["vonKind"]
    zu_kind = data["zuKind"]
    query = f"""
        MATCH (a:{von_kind} {{id: $von_id, campaignId: $campaign_id}})
        MATCH (b:{zu_kind} {{id: $zu_id, campaignId: $campaign_id}})
        CREATE (a)-[r:VERBINDUNG {{
            id: $edge_id, typ: $typ, beschreibung: $beschreibung,
            seit: $seit, bis: $bis, sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        }}]->(b)
        RETURN r.id AS id, r.typ AS typ, r.beschreibung AS beschreibung,
               r.seit AS seit, r.bis AS bis, r.sichtbarkeit AS sichtbarkeit, r.sichtbarFuer AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            von_id=data["vonId"],
            zu_id=data["zuId"],
            edge_id=edge_id,
            typ=data["typ"],
            beschreibung=data["beschreibung"],
            seit=data["seit"],
            bis=data["bis"],
            sichtbarkeit=data["sichtbarkeit"],
            sichtbarFuer=data["sichtbarFuer"],
        )
        record = await result.single()
        if record is None:
            return None
        response = dict(record)
        response.update(vonKind=von_kind, vonId=data["vonId"], zuKind=zu_kind, zuId=data["zuId"])
        return response


async def list_verbindungen(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (a)-[r:VERBINDUNG]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
        RETURN r.id AS id, labels(a)[0] AS vonKind, a.id AS vonId,
               labels(b)[0] AS zuKind, b.id AS zuId,
               r.typ AS typ, r.beschreibung AS beschreibung,
               r.seit AS seit, r.bis AS bis, r.sichtbarkeit AS sichtbarkeit, r.sichtbarFuer AS sichtbarFuer,
               // Sichtbarkeit der beiden Endpunkte: eine für sich sichtbare
               // Verbindung darf trotzdem nicht ausgeliefert werden, wenn sie
               // an einer verborgenen Entität hängt — sonst verrät sie deren
               // Existenz. Wird in visibility.py ausgewertet und ist in
               // VerbindungResponse nicht enthalten, geht also nicht raus.
               a.sichtbarkeit AS vonSichtbarkeit, a.sichtbarFuer AS vonSichtbarFuer,
               b.sichtbarkeit AS zuSichtbarkeit, b.sichtbarFuer AS zuSichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]


async def delete_verbindung(campaign_id: str, edge_id: str) -> bool:
    driver = get_driver()
    query = """
        MATCH (a)-[r:VERBINDUNG {id: $edge_id}]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
        DELETE r
        RETURN count(r) AS deleted
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, edge_id=edge_id)
        record = await result.single()
        return dict(record)["deleted"] > 0
