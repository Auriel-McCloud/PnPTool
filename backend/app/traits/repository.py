from app.db.neo4j_driver import get_driver
from app.spezialisierungen import repository as spezialisierungen_repository


async def list_catalog(ruleset: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (t:TraitDef {ruleset: $ruleset})
        RETURN t.id AS id, t.name AS name, t.category AS category,
               t.defaultMax AS defaultMax, t.sortOrder AS sortOrder,
               coalesce(t.description, '') AS description,
               coalesce(t.vorschlaege, []) AS vorschlaege
        ORDER BY t.category, t.sortOrder
    """
    async with driver.session() as session:
        result = await session.run(query, ruleset=ruleset)
        return [dict(record) async for record in result]


async def set_vorschlaege(trait_def_id: str, ruleset: str, vorschlaege: list[str]) -> dict | None:
    """Setzt die komplette Liste der Spezialisierungs-Vorschlagstexte einer
    TraitDef (GM-Oberfläche, Folge-Feature 22.10.2026, siehe
    traits/routes.py::set_trait_vorschlaege) — ersetzt, patcht nicht.

    Scoped auf `ruleset` wie `list_catalog`, NICHT auf eine Kampagne:
    TraitDef ist ruleset-weit (siehe traits/seed.py-Moduldocstring), nicht
    campaign-gebunden wie Zusatzfertigkeiten. Akzeptierter v1-Fehlbetrag:
    jede Kampagnen-SL dieses Regelwerks bearbeitet denselben gemeinsamen
    Katalogeintrag — es gibt (Stand 22.10.2026) ohnehin nur ein Regelwerk
    ('neotopia') in der Praxis, siehe Feature-Bericht.
    """
    driver = get_driver()
    query = """
        MATCH (t:TraitDef {id: $trait_def_id, ruleset: $ruleset})
        SET t.vorschlaege = $vorschlaege
        RETURN t.id AS id, t.name AS name, t.category AS category,
               t.defaultMax AS defaultMax, t.sortOrder AS sortOrder,
               coalesce(t.description, '') AS description,
               coalesce(t.vorschlaege, []) AS vorschlaege
    """
    async with driver.session() as session:
        result = await session.run(query, trait_def_id=trait_def_id, ruleset=ruleset, vorschlaege=vorschlaege)
        record = await result.single()
        return dict(record) if record else None


async def get_ratings_for_entity(campaign_id: str, entity_id: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})-[r:HAS_TRAIT]->(t:TraitDef)
        RETURN t.id AS traitDefId, t.name AS name, t.category AS category,
               r.rating AS rating, coalesce(r.maxOverride, t.defaultMax) AS max
        ORDER BY t.category, t.sortOrder
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, entity_id=entity_id)
        return [dict(record) async for record in result]


async def set_rating(
    campaign_id: str, entity_id: str, trait_def_id: str, rating: int, max_override: int | None
) -> dict | None:
    """Setzt einen Wert — und lässt ein vorhandenes Maximum in Ruhe.

    **`max_override=None` heisst "nicht anfassen", nicht "löschen".** Das war
    bis 11.09.2026 andersherum, mit einer stillen Nebenwirkung: das
    Charakterblatt schickt beim Klick auf einen Punkt immer `null` mit (siehe
    Charakterblatt.tsx), womit jede Wertänderung den **Rassendeckel**
    gelöscht hat. Ein Elf mit Widerstandsfähigkeit 5 stand danach wieder auf
    dem Katalogmaximum 6 — die Rasse war stillschweigend weg.

    Ein Zurücksetzen auf den Katalogwert gibt es dadurch nicht mehr; das ist
    richtig so, weil der Katalogwert für alles mit Rassenmodifikator ohnehin
    der falsche wäre. Geändert wird das Maximum ausdrücklich über die
    ±-Knöpfe im Blatt (die schicken eine Zahl) oder über den Rassen-Baukasten.

    **Fertigkeiten-Spezialisierung (22.10.2026):** dies ist einer von drei
    Wegen, über die ein Fertigkeits-Rating steigen kann (die anderen:
    `steigere`, `set_ratings_bulk`) — darum wird hier, nach dem Schreiben,
    geprüft, ob die Schwelle 4 oder 6 gerade überschritten wurde, und bei
    Bedarf automatisch ein Spezialisierungs-Slot vergeben. Siehe
    `_vergib_automatische_spezialisierungen` unten.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        MATCH (t:TraitDef {id: $trait_def_id})
        OPTIONAL MATCH (n)-[vorher:HAS_TRAIT]->(t)
        WITH n, t, coalesce(vorher.rating, 0) AS altRating
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = $rating,
            r.maxOverride = CASE WHEN $max_override IS NULL THEN r.maxOverride ELSE $max_override END
        RETURN t.id AS traitDefId, t.name AS name, t.category AS category,
               r.rating AS rating, coalesce(r.maxOverride, t.defaultMax) AS max,
               altRating AS altRating
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            entity_id=entity_id,
            trait_def_id=trait_def_id,
            rating=rating,
            max_override=max_override,
        )
        record = await result.single()
        if record is None:
            return None
        daten = dict(record)
        alt_rating = daten.pop("altRating")
        await _vergib_automatische_spezialisierungen(
            campaign_id, entity_id, trait_def_id, daten["category"], alt_rating, daten["rating"]
        )
        return daten


async def set_ratings_bulk(campaign_id: str, entity_id: str, werte: dict[str, int]) -> int:
    """Setzt viele Werte auf einmal — für die Charaktererstellung.

    Einzeln wären das rund fünfzig Abfragen; hier läuft alles in einer.
    `UNWIND` über die Paare, dann dasselbe `MERGE` wie bei `set_rating`.
    Werte mit 0 werden mitgeschrieben statt weggelassen: eine ausdrücklich
    auf 0 gesetzte Fertigkeit ist etwas anderes als eine nie berührte, und
    beim erneuten Einreichen einer Erstellung müssen alte Werte zurückfallen.

    **Fertigkeiten-Spezialisierung (22.10.2026):** auch dieser Pfad kann ein
    Fertigkeits-Rating auf 4+ heben — direkt bei der Charaktererstellung
    (ein Fertigkeitspaket legt z.B. gleich eine 4 an) UND bei einer
    SL-Korrektur nach Erstellungsabschluss (`erstelle_charakter` erlaubt der
    SL ein erneutes Einreichen). Die Zeilen tragen deshalb zusätzlich die
    alte Bewertung mit (`OPTIONAL MATCH` VOR dem `MERGE`), damit nach dem
    Schreiben pro Zeile geprüft werden kann, ob die Schwelle 4/6 gerade
    überschritten wurde.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        UNWIND $paare AS paar
        MATCH (t:TraitDef {ruleset: $ruleset, name: paar.name})
        OPTIONAL MATCH (n)-[vorher:HAS_TRAIT]->(t)
        WITH n, t, paar, coalesce(vorher.rating, 0) AS altRating
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = paar.wert
        RETURN t.id AS traitDefId, t.category AS category, altRating AS altRating, paar.wert AS neuRating
    """
    paare = [{"name": name, "wert": int(wert)} for name, wert in werte.items()]
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, entity_id=entity_id, paare=paare, ruleset="neotopia"
        )
        zeilen = [dict(r) async for r in result]
    for zeile in zeilen:
        await _vergib_automatische_spezialisierungen(
            campaign_id, entity_id, zeile["traitDefId"], zeile["category"], zeile["altRating"], zeile["neuRating"]
        )
    return len(zeilen)


async def setze_maxima_bulk(campaign_id: str, entity_id: str, maxima: dict[str, int]) -> int:
    """Setzt dauerhafte Obergrenzen (`maxOverride`) für mehrere Werte.

    Für die Rassenmaxima bei der Erstellung: ein Troll darf bei Körperkraft
    dauerhaft über das Katalogmaximum hinaus, ein Elf bei
    Widerstandsfähigkeit darunter bleiben (siehe
    `erstellung.py::lebensmaxima`).

    Getrennt von `set_ratings_bulk`, weil dort **nur** der Wert geschrieben
    wird: würde es das Maximum mitschreiben, überschriebe jede erneut
    eingereichte Erstellung ein von der Spielleitung von Hand angehobenes
    Maximum. Hier ist das Setzen ausdrücklich gewollt.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        UNWIND $paare AS paar
        MATCH (t:TraitDef {ruleset: $ruleset, name: paar.name})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.maxOverride = paar.max
        RETURN count(r) AS gesetzt
    """
    paare = [{"name": name, "max": int(wert)} for name, wert in maxima.items()]
    if not paare:
        return 0
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, entity_id=entity_id, paare=paare, ruleset="neotopia"
        )
        record = await result.single()
        return dict(record)["gesetzt"] if record else 0


async def steigere(campaign_id: str, entity_id: str, trait_def_id: str, neuer_wert: int) -> dict | None:
    """Hebt einen einzelnen Wert an, ohne ein vorhandenes maxOverride zu verlieren.

    `set_rating` setzt `maxOverride` immer mit — hier soll ein vom Spielleiter
    vergebenes höheres Maximum aber bestehen bleiben.

    **Fertigkeiten-Spezialisierung (22.10.2026):** EP-Steigerungen laufen
    über diese Funktion (traits/routes.py::steigere_wert) — einer der drei
    Pfade, die automatisch einen Slot vergeben können, siehe `set_rating`.
    """
    driver = get_driver()
    query = """
        MATCH (n {id: $entity_id, campaignId: $campaign_id})
        MATCH (t:TraitDef {id: $trait_def_id})
        OPTIONAL MATCH (n)-[vorher:HAS_TRAIT]->(t)
        WITH n, t, coalesce(vorher.rating, 0) AS altRating
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = $rating
        RETURN t.id AS traitDefId, t.name AS name, t.category AS category,
               r.rating AS rating, coalesce(r.maxOverride, t.defaultMax) AS max,
               altRating AS altRating
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            entity_id=entity_id,
            trait_def_id=trait_def_id,
            rating=neuer_wert,
        )
        record = await result.single()
        if record is None:
            return None
        daten = dict(record)
        alt_rating = daten.pop("altRating")
        await _vergib_automatische_spezialisierungen(
            campaign_id, entity_id, trait_def_id, daten["category"], alt_rating, daten["rating"]
        )
        return daten


async def _vergib_automatische_spezialisierungen(
    campaign_id: str, entity_id: str, trait_def_id: str, category: str, alt: int, neu: int
) -> None:
    """Gemeinsamer Auto-Grant-Hook für `set_rating`/`steigere`/`set_ratings_bulk`.

    Lebt HIER statt an jeder Route einzeln, weil jeder Pfad, der ein
    Fertigkeits-Rating anheben kann (GM-Punktklick, EP-Steigerung,
    Charaktererstellung/-korrektur, und jede künftige NPC-Autosteigerung,
    sobald sie eine dieser drei Funktionen zum Schreiben nutzt), am Ende
    durch GENAU eine dieser drei Repository-Funktionen läuft — ein Hook
    hier feuert also garantiert überall, ohne an jeder Route einzeln dafür
    sorgen zu müssen. Siehe app/spezialisierungen/repository.py für die
    Schwellen-Logik und den Knoten, der dabei entsteht.
    """
    if category not in spezialisierungen_repository.ALLE_SPEZIALISIERUNGS_KATEGORIEN:
        return
    schwellen = spezialisierungen_repository.schwellen_fuer(category)
    anzahl = spezialisierungen_repository.automatische_slot_anzahl(alt, neu, schwellen)
    if anzahl <= 0:
        return
    await spezialisierungen_repository.automatisch_anlegen(campaign_id, entity_id, trait_def_id, anzahl)
