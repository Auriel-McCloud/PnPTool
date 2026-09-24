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
    # Häretiker-Flavor (24.09.2026): rein kosmetisches Zweitfeld neben "weg" —
    # bestimmt nur, welche Begriffe die Oberfläche für einen Magier-Charakter
    # zeigt (Magier-Vokabular oder Häretiker-Vokabular). Siehe schemas.py.
    "magieFlavor",
    "rasse",
    "schadenSchlag",
    "schadenSchwer",
    "schadenAggraviert",
    "willenskraftVerbraucht",
    "iceSchaden",
    "erfahrung",
    "erfahrungAusgegeben",
    # Extra-EP: individuelle Bonus-Punkte zusätzlich zu kampagnenweiten EP.
    "extraEP",
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
    # Welche Koerpersilhouette die Koerperkarte zeigt ("weiblich" |
    # "maennlich"). Am Charakter gespeichert, nicht an der Ansicht: sonst
    # muesste man bei jedem Wechsel neu umstellen.
    "silhouette",
]

# bildUrl: Aussehen einer Person, eines Ortes oder einer Szene. Die
# Spielleitung kann es per Blitz an alle schicken ("so sieht er aus").
# bilder: Bildergalerie mit mehreren Bildern und Primär-Flag
# istEntwurf: Markiert Einträge in der Ideenschmiede (noch nicht Teil der Kampagne)
PERSON_FIELDS = ["name", "personType", "description", "notes", "bildUrl", "bilder", "istEntwurf", "istCritter", "istKI", "istHaendler", "spezialisierung", "vertriebsart", "shopHintergrundUrl", *_BOGEN_FELDER, *_VISIBILITY_FIELDS]
# spotifyPlaylist{Uri,Name,Bild}: siehe app/spotify/ — Playlist, die beim
# Wechsel der aktiven Party an diesen Ort startet.
ORT_FIELDS = ["name", "description", "notes", "bildUrl", "bilder", "istEntwurf", "spotifyPlaylistUri", "spotifyPlaylistName", "spotifyPlaylistBild", *_VISIBILITY_FIELDS]
EVENT_FIELDS = ["title", "timestamp", "description", "notes", "bildUrl", "bilder", "istEntwurf", "spotifyPlaylistUri", "spotifyPlaylistName", "spotifyPlaylistBild", *_VISIBILITY_FIELDS]
# Fraktion: Organisationen, Konzerne, Gangs — was sie wollen (ziele) und
# womit sie es durchsetzen (ressourcen) sind eigene Felder statt Freitext in
# notes, weil beides regelmäßig getrennt abgefragt wird ("was plant die
# Zaibatsu?" vs. "was können sie aufbieten?").
FRAKTION_FIELDS = ["name", "description", "ziele", "ressourcen", "notes", "bildUrl", "bilder", "istEntwurf", *_VISIBILITY_FIELDS]


def _return_clause(alias: str, fields: list[str]) -> str:
    return ", ".join(f"{alias}.{f} AS {f}" for f in ["id", *fields])


# Ausgangswerte für die Bogenfelder. Bestandsdaten kennen sie nicht und
# liefern None — ohne Ersatz scheitert die Pydantic-Prüfung und reisst die
# komplette Liste mit 500 herunter (siehe Stolperstein 9 in CLAUDE.md).
_BOGEN_DEFAULTS: dict = {
    "weg": "KEINER",
    # Häretiker-Flavor: Bestandscharaktere kennen das Feld noch nicht.
    "magieFlavor": "MAGIER",
    "rasse": "",
    "istCritter": False,
    "istKI": False,
    "istHaendler": False,
    "spezialisierung": [],
    "vertriebsart": "PHYSISCH",
    "shopHintergrundUrl": "",
    "silhouette": "maennlich",
    "schadenSchlag": 0,
    "schadenSchwer": 0,
    "schadenAggraviert": 0,
    "willenskraftVerbraucht": 0,
    "iceSchaden": 0,
    "erfahrung": 0,
    "erfahrungAusgegeben": 0,
    "extraEP": 0,
    "willenskraftBonus": 0,
    "konzept": "",
    "alter": "",
    "ambition": "",
    "verlangen": "",
    "ziel": "",
    "kapital": 0,
    "schulden": 0,
    "erstellungAbgeschlossen": False,
    # Bestandsdaten kennen das Feld nicht; ohne Ersatz scheitert die
    # Pydantic-Pruefung (Stolperstein 9).
    "bildUrl": "",
    # Bildergalerie: leeres Array als Standard
    "bilder": [],
    # Ideenschmiede: Bestandsdaten sind keine Entwürfe
    "istEntwurf": False,
    # Spotify: Bestandsdaten (Orte/Events vor dieser Funktion) kennen die
    # Felder noch nicht.
    "spotifyPlaylistUri": "",
    "spotifyPlaylistName": "",
    "spotifyPlaylistBild": "",
    # Fraktion: Ziele/Ressourcen sind neu, Bestandsdaten kennen sie nicht.
    # ziele und ressourcen sind Listen von {titel, beschreibung}.
    "ziele": [],
    "ressourcen": [],
}


def _mit_defaults(record: dict) -> dict:
    """Ergänzt fehlende Bogenfelder. Nur Personen haben sie überhaupt."""
    daten = dict(record)
    for feld, ersatz in _BOGEN_DEFAULTS.items():
        if feld in daten and daten[feld] is None:
            daten[feld] = ersatz
    
    # Migration: bildUrl → bilder-Array
    if "bildUrl" in daten and "bilder" in daten:
        if not daten["bilder"] and daten["bildUrl"]:
            daten["bilder"] = [{"url": daten["bildUrl"], "istPrimaer": True}]
    
    # bilder aus JSON-String parsen (wurde so in Neo4j gespeichert)
    if "bilder" in daten and isinstance(daten["bilder"], str):
        import json
        try:
            daten["bilder"] = json.loads(daten["bilder"])
        except (json.JSONDecodeError, TypeError):
            daten["bilder"] = []

    # ziele aus JSON-String parsen (Liste von {titel, beschreibung})
    if "ziele" in daten and isinstance(daten["ziele"], str):
        import json
        try:
            daten["ziele"] = json.loads(daten["ziele"])
        except (json.JSONDecodeError, TypeError):
            daten["ziele"] = []

    # ressourcen aus JSON-String parsen (Liste von {titel, beschreibung})
    if "ressourcen" in daten and isinstance(daten["ressourcen"], str):
        import json
        try:
            daten["ressourcen"] = json.loads(daten["ressourcen"])
        except (json.JSONDecodeError, TypeError):
            daten["ressourcen"] = []

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
    import json
    changed = {k: v for k, v in data.items() if v is not None}
    
    # bilder-Array als JSON-String speichern (Neo4j kann keine Maps in Arrays)
    if "bilder" in changed and isinstance(changed["bilder"], list):
        changed["bilder"] = json.dumps(changed["bilder"])
    # ziele-Liste ebenfalls als JSON-String (Liste von {titel, beschreibung})
    if "ziele" in changed and isinstance(changed["ziele"], list):
        changed["ziele"] = json.dumps(changed["ziele"])
    # ressourcen-Liste ebenfalls als JSON-String
    if "ressourcen" in changed and isinstance(changed["ressourcen"], list):
        changed["ressourcen"] = json.dumps(changed["ressourcen"])
    
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


async def list_critter(campaign_id: str) -> list[dict]:
    """Alle Critter (Person mit istCritter=true) samt ihrem Menschen.

    Eigene, schlanke Abfrage statt der vollen `PERSON_FIELDS` — die
    Begleiter-Übersicht (`app/begleiter/routes.py`) braucht nur Name/Bild/
    Beziehungsziel, nicht den kompletten Charakterbogen. Critter (20.09.2026,
    Marks Entscheidung "wir machen critter zu richtigen NPCs") sind echte
    `Person`-Knoten, verknüpft über dieselbe BEGLEITET-Kante wie
    Sprite/Geist/KI — nur von Person zu Person statt von Begleiter zu Person.
    """
    driver = get_driver()
    query = """
        MATCH (n:Person {campaignId: $campaign_id, istCritter: true})
        OPTIONAL MATCH (n)-[:BEGLEITET]->(p:Person)
        RETURN n.id AS id, n.name AS name, n.bildUrl AS bildUrl,
               p.id AS besitzerId, p.name AS besitzerName,
               n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer
        ORDER BY n.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def critter_besitzer_setzen(campaign_id: str, critter_id: str, person_id: str | None) -> dict | None:
    """Bindet einen Critter an seinen Menschen — oder löst die Bindung.

    Gleiches Muster wie `app/begleiter/repository.py::besitzer_setzen`, nur
    von Person zu Person statt von Begleiter zu Person.
    """
    driver = get_driver()
    query = """
        MATCH (n:Person {id: $critter_id, campaignId: $campaign_id, istCritter: true})
        OPTIONAL MATCH (n)-[alt:BEGLEITET]->(:Person)
        DELETE alt
        WITH n
        OPTIONAL MATCH (neu:Person {id: $person_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN neu IS NULL THEN [] ELSE [1] END |
            CREATE (n)-[:BEGLEITET]->(neu)
        )
        WITH n
        OPTIONAL MATCH (n)-[:BEGLEITET]->(p:Person)
        RETURN n.id AS id, n.name AS name, n.bildUrl AS bildUrl,
               p.id AS besitzerId, p.name AS besitzerName,
               n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, critter_id=critter_id, person_id=person_id)
        record = await result.single()
        return dict(record) if record else None


async def list_ki(campaign_id: str) -> list[dict]:
    """Alle KI-Personen (Person mit istKI=true) für die Begleiter-Übersicht.

    Eigene, schlanke Abfrage wie `list_critter` — die Begleiter-Übersicht
    braucht nur Name/Bild/Besitzer, nicht den kompletten Charakterbogen.
    KI (20.09.2026, revidiert — Mark: "mach jetzt das Gleiche für die KI")
    ist wie Critter eine echte `Person` statt einer eigenen Begleiter-Art,
    kann aber wie bisher an eine Person gebunden sein (z.B. der Neuroweaver,
    der sie geschrieben hat) oder frei stehen (Stadt-KI wie Babel).
    """
    driver = get_driver()
    query = """
        MATCH (n:Person {campaignId: $campaign_id, istKI: true})
        OPTIONAL MATCH (n)-[:BEGLEITET]->(p:Person)
        RETURN n.id AS id, n.name AS name, n.bildUrl AS bildUrl,
               p.id AS besitzerId, p.name AS besitzerName,
               n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer
        ORDER BY n.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(r) async for r in result]


async def ki_besitzer_setzen(campaign_id: str, ki_id: str, person_id: str | None) -> dict | None:
    """Bindet eine KI an eine Person — oder löst die Bindung.

    Gleiches Muster wie `critter_besitzer_setzen`.
    """
    driver = get_driver()
    query = """
        MATCH (n:Person {id: $ki_id, campaignId: $campaign_id, istKI: true})
        OPTIONAL MATCH (n)-[alt:BEGLEITET]->(:Person)
        DELETE alt
        WITH n
        OPTIONAL MATCH (neu:Person {id: $person_id, campaignId: $campaign_id})
        FOREACH (_ IN CASE WHEN neu IS NULL THEN [] ELSE [1] END |
            CREATE (n)-[:BEGLEITET]->(neu)
        )
        WITH n
        OPTIONAL MATCH (n)-[:BEGLEITET]->(p:Person)
        RETURN n.id AS id, n.name AS name, n.bildUrl AS bildUrl,
               p.id AS besitzerId, p.name AS besitzerName,
               n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, ki_id=ki_id, person_id=person_id)
        record = await result.single()
        return dict(record) if record else None


# Erlaubte Ziel-Typen für Einfluss-Kanten — siehe schemas.EinflussZielKind.
_EINFLUSS_ZIELE = {"Ort", "Fraktion", "Event", "Gegenstand"}

# Sammelt die Einfluss-Kanten einer Person als Liste von Dicts — Aggregations-
# Subquery statt eines simplen OPTIONAL MATCH, sonst multipliziert eine
# zweite parallele OPTIONAL-MATCH-Kante (z.B. BEGLEITET) das Ergebnis
# (dasselbe Problem wie bei `begleiter/repository.py::_EINFLUSS_SUBQUERY`,
# von dort verschoben — 20.09.2026, KI ist jetzt eine Person).
_PERSON_EINFLUSS_SUBQUERY = """
    CALL (n) {
        OPTIONAL MATCH (n)-[r:HAT_EINFLUSS_AUF]->(ziel)
        WITH ziel, r WHERE ziel IS NOT NULL
        RETURN collect({
            zielKind: labels(ziel)[0], zielId: ziel.id,
            zielName: coalesce(ziel.name, ziel.title, ''), stufe: r.stufe
        }) AS einfluss
    }
"""


async def person_einfluss_liste(campaign_id: str, person_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (n:Person {{id: $person_id, campaignId: $campaign_id}})
        {_PERSON_EINFLUSS_SUBQUERY}
        RETURN einfluss
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        return record["einfluss"] if record else []


async def person_einfluss_setzen(
    campaign_id: str, person_id: str, ziel_kind: str, ziel_id: str, stufe: int
) -> list[dict] | None:
    """Setzt (oder aktualisiert) die Einfluss-Stufe einer Person (typischerweise
    einer KI) auf ein Ziel. `MERGE` auf die Kante, damit ein zweites Setzen
    auf dasselbe Ziel die Stufe aktualisiert statt eine zweite Kante
    danebenzulegen."""
    if ziel_kind not in _EINFLUSS_ZIELE:
        return None
    driver = get_driver()
    query = f"""
        MATCH (n:Person {{id: $person_id, campaignId: $campaign_id}})
        MATCH (ziel:{ziel_kind} {{id: $ziel_id, campaignId: $campaign_id}})
        MERGE (n)-[r:HAT_EINFLUSS_AUF]->(ziel)
        SET r.stufe = $stufe
        WITH n
        {_PERSON_EINFLUSS_SUBQUERY}
        RETURN einfluss
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, ziel_id=ziel_id, stufe=stufe
        )
        record = await result.single()
        return record["einfluss"] if record else None


async def person_einfluss_entfernen(campaign_id: str, person_id: str, ziel_kind: str, ziel_id: str) -> list[dict] | None:
    """Nimmt der SL im Kampf gezielt einen Einflussbereich weg — kappt die Kante ganz."""
    if ziel_kind not in _EINFLUSS_ZIELE:
        return None
    driver = get_driver()
    query = f"""
        MATCH (n:Person {{id: $person_id, campaignId: $campaign_id}})
        MATCH (n)-[r:HAT_EINFLUSS_AUF]->(ziel:{ziel_kind} {{id: $ziel_id, campaignId: $campaign_id}})
        DELETE r
        WITH n
        {_PERSON_EINFLUSS_SUBQUERY}
        RETURN einfluss
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id, ziel_id=ziel_id)
        record = await result.single()
        return record["einfluss"] if record else None


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
