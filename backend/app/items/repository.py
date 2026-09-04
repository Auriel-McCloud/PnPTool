import json
import uuid

from app.db.neo4j_driver import get_driver

RETURN_FIELDS = """
    g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
    g.typ AS typ, g.preis AS preis, g.kraft AS kraft, g.cyberwall AS cyberwall,
    g.eigenschaften AS eigenschaften, g.zeigeInGraph AS zeigeInGraph,
    g.einzigartig AS einzigartig, g.hatMenge AS hatMenge, g.menge AS menge,
    g.istVorlage AS istVorlage, g.seltenheit AS seltenheit, g.automatischImShop AS automatischImShop,
    g.bildUrl AS bildUrl, g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer,
    g.gewicht AS gewicht, g.kapazitaet AS kapazitaet, g.istBehaelter AS istBehaelter,
    g.stufe AS stufe, g.widerstand AS widerstand, g.angriff AS angriff, g.agilitaet AS agilitaet,
    g.fahrzeugFertigkeiten AS fahrzeugFertigkeiten,
    g.deckBruteForce AS deckBruteForce, g.deckSchleichen AS deckSchleichen,
    g.deckDaten AS deckDaten, g.deckKompilieren AS deckKompilieren,
    g.immerSichtbar AS immerSichtbar,
    g.riggerBonus AS riggerBonus, g.maxDrohnen AS maxDrohnen,
    g.wVerlust AS wVerlust, g.koerperzone AS koerperzone,
    g.slot AS slot, g.istWaffe AS istWaffe,
    g.traitBoni AS traitBoni, g.ausruestungsfertigkeiten AS ausruestungsfertigkeiten,
    g.initiativeBonus AS initiativeBonus,
    g.weggeworfen AS weggeworfen, g.weggeworfenVon AS weggeworfenVon,
    g.ablage AS ablage,
    ziel.id AS ablageZielId, coalesce(ziel.name, ziel.title) AS ablageZielName,
    CASE WHEN ziel IS NULL THEN NULL ELSE labels(ziel)[0] END AS ablageZielKind
"""

# Muss vor jedem RETURN_FIELDS stehen: OPTIONAL, weil die meisten Gegenstaende
# am Koerper sind und gar kein Ziel haben.
LIEGT_IN = "OPTIONAL MATCH (g)-[:LIEGT_IN]->(ziel)"
# Nach einem CREATE *oder* SET verlangt Cypher ein WITH, bevor erneut
# gematcht werden darf ("WITH is required between SET and MATCH"). Nur dort
# verwenden, wo ausser g keine weitere Variable ins RETURN muss — WITH wirft
# alles andere weg.
LIEGT_IN_NACH_CREATE = "WITH g " + LIEGT_IN

# Felder, die eine Kopie nicht von ihrer Vorlage erbt: Identität, Herkunft
# und alles, was der Aufrufer selbst bestimmt.
_NICHT_KOPIEREN = {
    "id",
    "istVorlage",
    "sichtbarkeit",
    "sichtbarFuer",
    "automatischImShop",
    "bildUrl",
    # Kommen aus der Abfrage, sind aber keine eigenen Eigenschaften
    "ablageZielId",
    "ablageZielName",
    "ablageZielKind",
    "ownerId",
    "ownerName",
    "ownerPersonType",
    # Der Mülleimer ist ein Zustand dieses einen Stücks, keine Eigenschaft
    # der Vorlage — eine Kopie startet nie weggeworfen.
    "weggeworfen",
    "weggeworfenVon",
}


def _or_default(value, default):
    """Wie `value or default`, aber ohne die Falsy-Falle bei 0/False als gültigem Wert."""
    return value if value is not None else default


def _decode(record: dict) -> dict:
    # Bei jeder neuen Property IMMER hier einen Fallback ergänzen — ein
    # fehlender Fallback für ein Pflichtfeld in GegenstandResponse lässt sonst
    # die komplette Liste mit 500 abstürzen, siehe Stolperstein #9 in CLAUDE.md.
    # Für Felder, bei denen 0/False ein gültiger (nicht der Default-)Wert sein
    # kann — einzigartig, menge — MUSS `_or_default` (is-not-None-Check) statt
    # `or` verwendet werden, sonst wird z.B. menge=0 fälschlich zu 1.
    record = dict(record)
    try:
        record["eigenschaften"] = json.loads(record["eigenschaften"]) if record["eigenschaften"] else {}
    except (json.JSONDecodeError, TypeError):
        record["eigenschaften"] = {}
    record["zeigeInGraph"] = bool(record.get("zeigeInGraph"))
    record["bildUrl"] = record.get("bildUrl") or ""
    record["typ"] = record.get("typ") or "Sonstiges"
    record["preis"] = record.get("preis") or 0
    record["kraft"] = record.get("kraft") or 0
    record["cyberwall"] = record.get("cyberwall") or 0
    record["einzigartig"] = _or_default(record.get("einzigartig"), True)
    record["hatMenge"] = _or_default(record.get("hatMenge"), False)
    record["menge"] = _or_default(record.get("menge"), 1)
    record["istVorlage"] = _or_default(record.get("istVorlage"), False)
    record["seltenheit"] = _or_default(record.get("seltenheit"), 1)
    record["automatischImShop"] = _or_default(record.get("automatischImShop"), False)
    # Bestandsdaten haben noch keine Ablage — was man besitzt, traegt man
    # ueblicherweise mit sich, deshalb RUCKSACK als Ausgangswert.
    # 0.0 ist ein gültiger Wert (gewichtslos bzw. kein Behälter), deshalb
    # _or_default statt `or` — sonst würde 0 auf den Default zurückfallen.
    record["gewicht"] = float(_or_default(record.get("gewicht"), 0.0))
    record["kapazitaet"] = float(_or_default(record.get("kapazitaet"), 0.0))
    # Ob etwas anderes hineinpasst. Frueher aus dem Typ geraten — ein Motorrad
    # ist aber ein Fahrzeug ohne Stauraum, und eine Kiste ist einer ohne Raeder.
    # Bestandsdaten: Behaelter ja, alles andere nein.
    record["istBehaelter"] = _or_default(record.get("istBehaelter"), record.get("typ") == "Behälter")
    # Werte des Drohnen-/Fahrzeugblatts (Neotopia.xlsx, Blatt DrohneFahrzeug).
    # Gesundheit = Stufe, Widerstand = Schadensreduktion, Angriff = Treffen und
    # Schaden, Agilitaet = Geschwindigkeit.
    # Cyberdeck-Werte B/S/D/K (Regelblatt Zeile 157/158): Bonuswürfel für die
    # jeweilige Matrix-Aktion.
    for feld in ("deckBruteForce", "deckSchleichen", "deckDaten", "deckKompilieren"):
        record[feld] = _or_default(record.get(feld), 0)
    # Manches lässt sich nicht am Körper tragen, ohne dass es jeder sieht —
    # ein Sturmgewehr fällt auf, ein Messer im Stiefel nicht. Reine Anzeige;
    # welche Folgen das hat, entscheidet die Spielleitung.
    record["immerSichtbar"] = _or_default(record.get("immerSichtbar"), False)
    # Riggerkonsole (Regelblatt Zeilen 158-167). Der Bonus kann negativ sein —
    # eine zusammengeschraubte Konsole macht das Steuern schwerer, nicht
    # leichter. Deshalb kein ge=0 im Schema.
    # Cyber- und Bioware kosten dauerhaft Willenskraft (Regelblatt Zeilen
    # 112-117). Der Verlust hängt am Preis je Bonuspunkt: billiges Chrom
    # reisst mehr aus einem heraus als teures.
    record["wVerlust"] = _or_default(record.get("wVerlust"), 0)
    record["koerperzone"] = record.get("koerperzone") or ""
    # Slot: welcher der drei Plaetze in der Zone belegt ist. None ist ein
    # gültiger Zustand (kein fester Platz) — deshalb kein _or_default mit 0.
    record["slot"] = record.get("slot")
    record["istWaffe"] = _or_default(record.get("istWaffe"), False)
    for feld in ("traitBoni", "ausruestungsfertigkeiten"):
        try:
            roh = record.get(feld)
            record[feld] = json.loads(roh) if roh else {}
        except (json.JSONDecodeError, TypeError):
            record[feld] = {}
    record["riggerBonus"] = _or_default(record.get("riggerBonus"), 0)
    # Initiative-Modifikator (Reflex-Booster & Co.). Bestandsdaten kennen das
    # Feld nicht und liefern None — ohne Ersatz scheitert die Pydantic-Prüfung
    # und reisst die ganze Liste mit 500 herunter (Stolperstein 9).
    record["initiativeBonus"] = _or_default(record.get("initiativeBonus"), 0)
    record["maxDrohnen"] = _or_default(record.get("maxDrohnen"), 0)
    record["stufe"] = _or_default(record.get("stufe"), 0)
    record["widerstand"] = _or_default(record.get("widerstand"), 0)
    record["angriff"] = _or_default(record.get("angriff"), 0)
    record["agilitaet"] = _or_default(record.get("agilitaet"), 0)
    try:
        roh = record.get("fahrzeugFertigkeiten")
        record["fahrzeugFertigkeiten"] = json.loads(roh) if roh else {}
    except (json.JSONDecodeError, TypeError):
        record["fahrzeugFertigkeiten"] = {}
    record["ablage"] = record.get("ablage") or "RUCKSACK"
    # Weggeworfen: Bestandsdaten haben die Property nicht (Neo4j gibt null).
    # Ohne Fallback schlägt die Pydantic-Validierung fehl und reisst die
    # ganze Liste mit — siehe Stolperstein #9 in CLAUDE.md.
    record["weggeworfen"] = _or_default(record.get("weggeworfen"), False)
    record["weggeworfenVon"] = record.get("weggeworfenVon") or ""
    return record


async def create_gegenstand(campaign_id: str, owner_person_id: str | None, data: dict) -> dict | None:
    """owner_person_id=None erzeugt einen besitzerlosen Gegenstand (= Vorlage,
    siehe Invariante in schemas.py). Ist eine ID gegeben, muss die Person
    existieren, sonst liefert die Query keine Zeile (item wird None)."""
    driver = get_driver()
    item_id = str(uuid.uuid4())
    create_clause = """
        CREATE (g:Gegenstand {
            id: $item_id, campaignId: $campaign_id, name: $name, description: $description, notes: $notes,
            typ: $typ, preis: $preis, kraft: $kraft, cyberwall: $cyberwall, eigenschaften: $eigenschaften,
            zeigeInGraph: $zeigeInGraph, einzigartig: $einzigartig, hatMenge: $hatMenge, menge: $menge,
            istVorlage: $istVorlage, seltenheit: $seltenheit, automatischImShop: $automatischImShop, bildUrl: '',
            sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer, ablage: $ablage,
            gewicht: $gewicht, kapazitaet: $kapazitaet, istBehaelter: $istBehaelter,
            stufe: $stufe, widerstand: $widerstand, angriff: $angriff, agilitaet: $agilitaet,
            fahrzeugFertigkeiten: $fahrzeugFertigkeiten,
            deckBruteForce: $deckBruteForce, deckSchleichen: $deckSchleichen,
            deckDaten: $deckDaten, deckKompilieren: $deckKompilieren,
            immerSichtbar: $immerSichtbar,
            riggerBonus: $riggerBonus, maxDrohnen: $maxDrohnen,
            wVerlust: $wVerlust, koerperzone: $koerperzone, slot: $slot, istWaffe: $istWaffe,
            traitBoni: $traitBoni, ausruestungsfertigkeiten: $ausruestungsfertigkeiten,
            initiativeBonus: $initiativeBonus
        })
    """
    if owner_person_id:
        query = f"""
            MATCH (p:Person {{id: $owner_id, campaignId: $campaign_id}})
            {create_clause}
            CREATE (p)-[:BESITZT]->(g)
            {LIEGT_IN_NACH_CREATE}
            RETURN {RETURN_FIELDS}
        """
    else:
        query = f"""{create_clause}
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}"""

    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            owner_id=owner_person_id,
            item_id=item_id,
            name=data["name"],
            description=data["description"],
            notes=data["notes"],
            typ=data["typ"],
            preis=data["preis"],
            kraft=data["kraft"],
            cyberwall=data.get("cyberwall") or 0,
            eigenschaften=json.dumps(data["eigenschaften"]),
            zeigeInGraph=data["zeigeInGraph"],
            einzigartig=data["einzigartig"],
            hatMenge=data["hatMenge"],
            menge=data["menge"],
            istVorlage=data["istVorlage"],
            seltenheit=data["seltenheit"],
            automatischImShop=data["automatischImShop"],
            istBehaelter=_or_default(data.get("istBehaelter"), data["typ"] == "Behälter"),
            stufe=data.get("stufe") or 0,
            widerstand=data.get("widerstand") or 0,
            angriff=data.get("angriff") or 0,
            agilitaet=data.get("agilitaet") or 0,
            fahrzeugFertigkeiten=json.dumps(data.get("fahrzeugFertigkeiten") or {}),
            deckBruteForce=data.get("deckBruteForce") or 0,
            deckSchleichen=data.get("deckSchleichen") or 0,
            deckDaten=data.get("deckDaten") or 0,
            deckKompilieren=data.get("deckKompilieren") or 0,
            immerSichtbar=bool(data.get("immerSichtbar")),
            riggerBonus=data.get("riggerBonus") or 0,
            maxDrohnen=data.get("maxDrohnen") or 0,
            wVerlust=data.get("wVerlust") or 0,
            koerperzone=data.get("koerperzone") or "",
            slot=data.get("slot"),
            istWaffe=bool(data.get("istWaffe")),
            traitBoni=json.dumps(data.get("traitBoni") or {}),
            initiativeBonus=int(data.get("initiativeBonus") or 0),
            ausruestungsfertigkeiten=json.dumps(data.get("ausruestungsfertigkeiten") or {}),
            sichtbarkeit=data["sichtbarkeit"],
            sichtbarFuer=data["sichtbarFuer"],
            ablage=data.get("ablage") or "RUCKSACK",
            gewicht=float(data.get("gewicht") or 0.0),
            kapazitaet=float(data.get("kapazitaet") or 0.0),
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def list_gegenstaende(campaign_id: str, owner_person_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (p:Person {{id: $owner_id, campaignId: $campaign_id}})-[:BESITZT]->(g:Gegenstand)
        WHERE NOT coalesce(g.weggeworfen, false)
        {LIEGT_IN}
        RETURN {RETURN_FIELDS}
        ORDER BY g.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, owner_id=owner_person_id)
        return [_decode(dict(record)) async for record in result]


async def list_alle_gegenstaende(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{campaignId: $campaign_id}})
        WHERE NOT coalesce(g.weggeworfen, false)
        OPTIONAL MATCH (p:Person)-[:BESITZT]->(g)
        {LIEGT_IN}
        RETURN {RETURN_FIELDS}, p.id AS ownerId, p.name AS ownerName, p.personType AS ownerPersonType
        ORDER BY p.name, g.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode(dict(record)) async for record in result]


async def list_weggeworfene(campaign_id: str) -> list[dict]:
    """Der Mülleimer der Spielleitung.

    Das Gegenstück zu allen anderen Listen: hier steht **nur**, was
    weggeworfen wurde. Ein weggeworfener Gegenstand behält seinen Besitzer,
    damit nachvollziehbar bleibt, aus wessen Inventar er stammt — er ist
    bloss überall sonst ausgeblendet.
    """
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{campaignId: $campaign_id}})
        WHERE coalesce(g.weggeworfen, false)
        OPTIONAL MATCH (p:Person)-[:BESITZT]->(g)
        {LIEGT_IN}
        RETURN {RETURN_FIELDS}, p.id AS ownerId, p.name AS ownerName, p.personType AS ownerPersonType
        ORDER BY g.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode(dict(record)) async for record in result]


async def update_gegenstand(campaign_id: str, item_id: str, data: dict) -> dict | None:
    changed = {k: v for k, v in data.items() if v is not None}
    if "eigenschaften" in changed:
        changed["eigenschaften"] = json.dumps(changed["eigenschaften"])
    # Neo4j kennt keine Map-Eigenschaften — wie bei eigenschaften als Text.
    if "fahrzeugFertigkeiten" in changed:
        changed["fahrzeugFertigkeiten"] = json.dumps(changed["fahrzeugFertigkeiten"])
    if "traitBoni" in changed:
        changed["traitBoni"] = json.dumps(changed["traitBoni"])
    if "ausruestungsfertigkeiten" in changed:
        changed["ausruestungsfertigkeiten"] = json.dumps(changed["ausruestungsfertigkeiten"])

    driver = get_driver()
    if not changed:
        query = f"MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}}) {LIEGT_IN} RETURN {RETURN_FIELDS}"
        async with driver.session() as session:
            result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
            record = await result.single()
            return _decode(dict(record)) if record else None

    set_clause = ", ".join(f"g.{k} = ${k}" for k in changed)
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        SET {set_clause}
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, **changed)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def get_gegenstand(campaign_id: str, item_id: str) -> dict | None:
    driver = get_driver()
    query = f"MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}}) {LIEGT_IN_NACH_CREATE} RETURN {RETURN_FIELDS}"
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def assign_copy(
    campaign_id: str, source: dict, ziel_person_id: str, sichtbarkeit: str, sichtbar_fuer: list[str]
) -> dict | None:
    """Erzeugt eine unabhängige Kopie einer Vorlage für eine Zielperson.

    einzigartig wird immer auf True gesetzt (die Kopie ist ab jetzt ein
    individualisierbares Einzelstück), istVorlage immer auf False (eine
    zugewiesene Kopie ist selbst keine Vorlage mehr). hatMenge/menge werden
    dagegen unverändert von der Vorlage übernommen, nicht zurückgesetzt.
    """
    # Alles übernehmen und nur gezielt überschreiben, statt die Felder
    # einzeln aufzuzählen: eine Positivliste muss bei jeder neuen Eigenschaft
    # mitgepflegt werden, was hier schon zweimal vergessen wurde (Gewicht und
    # Kapazität beim Traglast-Feature, Cyberwall bei den Commlinks) — die
    # Werte fielen dann bei jeder Zuweisung still auf ihren Standard zurück.
    daten = {k: v for k, v in source.items() if k not in _NICHT_KOPIEREN}
    daten.update(
        {
            # Die Kopie ist ein Einzelstück, keine Vorlage mehr.
            "istVorlage": False,
            "einzigartig": True,
            # Ein zugewiesenes Stück ist kein Shop-Muster mehr.
            "automatischImShop": False,
            "sichtbarkeit": sichtbarkeit,
            "sichtbarFuer": sichtbar_fuer,
        }
    )
    copy = await create_gegenstand(campaign_id, ziel_person_id, daten)
    if copy is None or not source["bildUrl"]:
        return copy
    return await set_bild_url(campaign_id, copy["id"], source["bildUrl"])


async def assign_owner(
    campaign_id: str, item_id: str, ziel_person_id: str, sichtbarkeit: str, sichtbar_fuer: list[str]
) -> dict | None:
    """Gibt einer besitzerlosen Vorlage eine Besitzer:in, OHNE zu kopieren —
    für einzigartige/MacGuffin-Vorlagen, die nicht vervielfältigt werden
    dürfen (siehe routes.py::zuweisen, Gegenstück zu assign_copy). Setzt
    istVorlage=false (Invariante). Kein Effekt, wenn schon ein Besitzer
    existiert (dafür ist transfer_owner da)."""
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        OPTIONAL MATCH (alt:Person)-[:BESITZT]->(g)
        WITH g, alt
        WHERE alt IS NULL
        MATCH (neu:Person {{id: $ziel_person_id, campaignId: $campaign_id}})
        SET g.istVorlage = false, g.sichtbarkeit = $sichtbarkeit, g.sichtbarFuer = $sichtbar_fuer
        CREATE (neu)-[:BESITZT]->(g)
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            item_id=item_id,
            ziel_person_id=ziel_person_id,
            sichtbarkeit=sichtbarkeit,
            sichtbar_fuer=sichtbar_fuer,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def get_owner_id(campaign_id: str, item_id: str) -> str | None:
    driver = get_driver()
    query = """
        MATCH (p:Person)-[:BESITZT]->(g:Gegenstand {id: $item_id, campaignId: $campaign_id})
        RETURN p.id AS ownerId
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        return record["ownerId"] if record else None


async def transfer_owner(campaign_id: str, item_id: str, ziel_person_id: str) -> dict | None:
    """Verschiebt einen bestehenden Gegenstand zu einer anderen Person (kein Kopieren — für
    Vorlagen-Kopien siehe assign_copy)."""
    driver = get_driver()
    query = f"""
        MATCH (alt:Person)-[r:BESITZT]->(g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        MATCH (neu:Person {{id: $ziel_person_id, campaignId: $campaign_id}})
        DELETE r
        CREATE (neu)-[:BESITZT]->(g)
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, ziel_person_id=ziel_person_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def remove_owner(campaign_id: str, item_id: str) -> dict | None:
    """Entfernt die Besitzer-Zuordnung und macht den Gegenstand zu einer
    besitzerlosen Vorlage. Liefert None, wenn der Gegenstand aktuell gar
    keinen Besitzer hat (schon eine Vorlage ist)."""
    driver = get_driver()
    query = f"""
        MATCH (p:Person)-[r:BESITZT]->(g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        DELETE r
        SET g.istVorlage = true
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def wegwerfen(campaign_id: str, item_id: str, von: str) -> dict | None:
    """Legt einen Gegenstand in den Mülleimer der Spielleitung.

    **Bewusst kein Löschen**: ein einzigartiges Stück wäre sonst für immer
    fort, und ein weggeworfener Gegenstand liegt im Spiel gedanklich am
    Boden — die Spielleitung kann ihn jederzeit wieder vergeben. Gelöscht
    wird nur ausdrücklich, in einem zweiten Schritt.

    Der Besitzer bleibt bestehen, damit im Mülleimer noch steht, aus wessen
    Inventar das Stück stammt. Eine Ablage-Verknüpfung wird dagegen gelöst:
    was weggeworfen wurde, liegt in keinem Rucksack mehr, und sonst zählte
    sein Gewicht weiter gegen den Behälter.
    """
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        WHERE NOT coalesce(g.weggeworfen, false)
        OPTIONAL MATCH (g)-[alt:LIEGT_IN]->()
        DELETE alt
        SET g.weggeworfen = true, g.weggeworfenVon = $von
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, von=von)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def zurueckholen(campaign_id: str, item_id: str) -> dict | None:
    """Holt einen Gegenstand aus dem Mülleimer zurück.

    Er landet als *gelagert ohne Ziel* wieder im Spiel — nicht am Körper
    seines alten Besitzers: wer etwas weggeworfen hat, hat es nicht mehr in
    der Hand. Wohin es tatsächlich kommt, entscheidet die Spielleitung
    danach über das gewohnte Umlegen.
    """
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        WHERE coalesce(g.weggeworfen, false)
        SET g.weggeworfen = false, g.weggeworfenVon = '', g.ablage = 'GELAGERT'
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def set_bild_url(campaign_id: str, item_id: str, bild_url: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        SET g.bildUrl = $bild_url
        {LIEGT_IN_NACH_CREATE}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, bild_url=bild_url)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def delete_gegenstand(campaign_id: str, item_id: str) -> bool:
    driver = get_driver()
    query = """
        MATCH (g:Gegenstand {id: $item_id, campaignId: $campaign_id})
        DETACH DELETE g
        RETURN count(g) AS deleted
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
        record = await result.single()
        return dict(record)["deleted"] > 0


# Wo ein Gegenstand steckt. AUSGERUESTET und RUCKSACK sind am Körper und
# brauchen kein Ziel; GELAGERT verweist über :LIEGT_IN auf einen Ort oder
# einen anderen Gegenstand (z.B. ein Fahrzeug).
ABLAGE_ARTEN = {"AUSGERUESTET", "RUCKSACK", "GELAGERT"}


async def set_ablage(campaign_id: str, item_id: str, ablage: str, ziel_id: str | None) -> dict | None:
    """Legt einen Gegenstand um.

    Ein Ziel ergibt nur bei GELAGERT Sinn und muss zur selben Kampagne
    gehören — sonst könnte man Dinge in fremde Kampagnen schieben. Beim
    Wechsel zurück an den Körper wird eine bestehende Verknüpfung gelöst.
    """
    if ablage not in ABLAGE_ARTEN:
        return None

    driver = get_driver()
    async with driver.session() as session:
        if ablage == "GELAGERT" and ziel_id:
            query = f"""
                MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
                MATCH (neu) WHERE neu.id = $ziel_id AND neu.campaignId = $campaign_id
                  AND (neu:Ort OR neu:Gegenstand) AND neu.id <> $item_id
                OPTIONAL MATCH (g)-[alt:LIEGT_IN]->()
                DELETE alt
                SET g.ablage = $ablage
                CREATE (g)-[:LIEGT_IN]->(neu)
                WITH g
                {LIEGT_IN}
                RETURN {RETURN_FIELDS}
            """
            params = {"item_id": item_id, "campaign_id": campaign_id, "ziel_id": ziel_id, "ablage": ablage}
        else:
            query = f"""
                MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
                OPTIONAL MATCH (g)-[alt:LIEGT_IN]->()
                DELETE alt
                SET g.ablage = $ablage
                WITH g
                {LIEGT_IN}
                RETURN {RETURN_FIELDS}
            """
            params = {"item_id": item_id, "campaign_id": campaign_id, "ablage": ablage}

        result = await session.run(query, **params)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def get_owner_person_id(campaign_id: str, item_id: str) -> str | None:
    """Wem gehört der Gegenstand? Für die Rechteprüfung beim Umlegen."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (p:Person)-[:BESITZT]->(g:Gegenstand {id: $item_id, campaignId: $campaign_id}) RETURN p.id AS id",
            item_id=item_id,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return record["id"] if record else None


async def moegliche_ablageziele(campaign_id: str, person_id: str) -> list[dict]:
    """Orte und eigene Behälter-Gegenstände, in denen etwas liegen kann.

    Behälter ist, was ausdrücklich als solcher markiert ist (`istBehaelter`) —
    **nicht**, was einen bestimmten Typ trägt. Ein Motorrad ist ein Fahrzeug
    ohne Stauraum, eine Kiste hat Stauraum ohne Räder.

    Der Rückfall für Bestandsdaten muss derselbe sein wie in `_decode`, sonst
    widersprechen sich Abfrage und Antwort: die Auswahl böte ein Fahrzeug als
    Ziel an, während die Oberfläche es nicht als Fach führt.

    Ein Gegenstand kann nicht in sich selbst liegen; verschachtelte Behälter
    sind erlaubt, aber ungeprüft (siehe CLAUDE.md).
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (o:Ort {campaignId: $campaign_id})
            RETURN o.id AS id, o.name AS name, 'Ort' AS kind
            UNION
            MATCH (p:Person {id: $person_id})-[:BESITZT]->(g:Gegenstand)
            WHERE coalesce(g.istBehaelter, g.typ = 'Behälter')
              AND NOT coalesce(g.weggeworfen, false)
            RETURN g.id AS id, g.name AS name, 'Gegenstand' AS kind
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        return [dict(record) async for record in result]


# Gewicht eines Gegenstands inklusive Stückzahl: 20 Schuss Munition wiegen
# zwanzigmal so viel wie einer.
_GEWICHT = "coalesce(g.gewicht, 0.0) * (CASE WHEN g.hatMenge THEN coalesce(g.menge, 1) ELSE 1 END)"


async def traglast_uebersicht(campaign_id: str, attribut: str, pro_punkt: float) -> list[dict]:
    """Was jeder Träger schleppt und was er schleppen könnte.

    Träger sind Personen (Traglast aus einem Attribut) und Gegenstände mit
    eigener Kapazität (Fahrzeuge, Behälter). Orte bleiben aussen vor — ein
    Versteck hat keine sinnvolle Obergrenze.

    **Nicht rekursiv:** liegt ein gefüllter Rucksack im Auto, zählt gegen das
    Auto nur das Eigengewicht des Rucksacks, nicht dessen Inhalt. Für eine
    Anzeige ohne Regelwirkung ist das vertretbar; sollte daraus je eine echte
    Mechanik werden, muss das hier nachgezogen werden.
    """
    driver = get_driver()
    query = f"""
        MATCH (p:Person {{campaignId: $campaign_id}})
        OPTIONAL MATCH (p)-[:BESITZT]->(g:Gegenstand)
            WHERE g.ablage IN ['AUSGERUESTET', 'RUCKSACK'] AND NOT coalesce(g.weggeworfen, false)
        WITH p, sum({_GEWICHT}) AS last
        OPTIONAL MATCH (p)-[r:HAS_TRAIT]->(t:TraitDef {{name: $attribut}})
        RETURN p.id AS id, p.name AS name, 'Person' AS art, p.personType AS personType,
               last AS last, coalesce(r.rating, 0) * $pro_punkt AS kapazitaet

        UNION

        MATCH (b:Gegenstand {{campaignId: $campaign_id}})
            WHERE coalesce(b.kapazitaet, 0) > 0 AND NOT coalesce(b.weggeworfen, false)
        OPTIONAL MATCH (g:Gegenstand)-[:LIEGT_IN]->(b)
            WHERE NOT coalesce(g.weggeworfen, false)
        RETURN b.id AS id, b.name AS name, 'Gegenstand' AS art, NULL AS personType,
               sum({_GEWICHT}) AS last, b.kapazitaet AS kapazitaet
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, attribut=attribut, pro_punkt=pro_punkt)
        return [dict(record) async for record in result]


async def commlink_cyberwall(campaign_id: str, person_id: str) -> int:
    """Cyberwall dieser Person aus ihren mitgeführten Geräten.

    **Commlink:** bestimmt den Grundwert. Bei mehreren gilt der beste, nicht
    die Summe — man ist über *ein* Gerät online, nicht über alle zugleich.
    Die Liste im Regelwerk reicht von Meta Link (1) bis Transs Avalon (6);
    das Feld ist aber nicht begrenzt.

    **Cyberdeck:** addiert seinen Bonus obendrauf (im Regelwerk als "Cywall+1"
    bis "Cywall+4" notiert). Mehrere Decks werden summiert — anders als bei
    Commlinks, weil es Zusatzausrüstung ist und kein Zugangsgerät.

    Zählt nur, was am Körper ist: ein Gerät im Versteck schützt niemanden.
    Ergibt 0, wenn nichts da ist — dann ist die Person offline.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
            WHERE g.ablage IN ['AUSGERUESTET', 'RUCKSACK'] AND NOT coalesce(g.weggeworfen, false)
            RETURN
              max(CASE WHEN g.typ = 'Commlink' THEN coalesce(g.cyberwall, 0) ELSE 0 END) AS grund,
              sum(CASE WHEN g.typ = 'Cyberdeck' THEN coalesce(g.cyberwall, 0) ELSE 0 END) AS bonus
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
        if record is None:
            return 0
        grund = int(record["grund"] or 0)
        # Ohne Commlink kein Zugang — ein Deck allein bringt nichts, es
        # verstärkt nur eine vorhandene Verbindung.
        return grund + int(record["bonus"] or 0) if grund > 0 else 0


# Welche Eigenschaft am Deck zu welcher Matrix-Aktion gehört (Zeile 157:
# "Brute Force = B, Schleichen = S, Daten Verarbeiten = D, Kompilieren = K").
DECK_WERTE = {
    "Brute Force": "deckBruteForce",
    "Schleichen": "deckSchleichen",
    "Daten Verarbeiten": "deckDaten",
    "Kompilieren": "deckKompilieren",
}


async def deck_boni(campaign_id: str, person_id: str) -> dict[str, int]:
    """Bonuswürfel aus den ausgerüsteten Cyberdecks.

    **Mehrere Decks addieren sich nicht** (Marks Vorgabe): es zählt je Aktion
    der höchste Wert. Wer zwei Decks trägt, bekommt also das Beste aus beiden,
    aber nicht die Summe — sonst wäre das Stapeln von Geräten die einzige
    sinnvolle Bauweise.

    Nur **ausgerüstete** Decks zählen; eines im Rucksack nützt niemandem.
    """
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        WHERE g.typ = 'Cyberdeck' AND g.ablage = 'AUSGERUESTET' AND NOT coalesce(g.weggeworfen, false)
        RETURN max(coalesce(g.deckBruteForce, 0)) AS bruteForce,
               max(coalesce(g.deckSchleichen, 0)) AS schleichen,
               max(coalesce(g.deckDaten, 0)) AS daten,
               max(coalesce(g.deckKompilieren, 0)) AS kompilieren
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        if record is None:
            return {}
        werte = {
            "Brute Force": record["bruteForce"] or 0,
            "Schleichen": record["schleichen"] or 0,
            "Daten Verarbeiten": record["daten"] or 0,
            "Kompilieren": record["kompilieren"] or 0,
        }
        # Nur zurückgeben, was tatsächlich etwas beiträgt — eine Liste aus
        # lauter Nullen sagt nichts und verstellt die Anzeige.
        return {k: v for k, v in werte.items() if v > 0}


# Typen, die im Körper stecken und dauerhaft Willenskraft kosten.
# MagWare läuft über dieselbe Formel wie Cyber-/Bioware (Mark, 02.09.2026):
# der Willenskraftverlust regelt die Kosten bereits ausreichend, es braucht
# keine eigene magische Kostenformel — MagWare ist bewusst nur eine dritte
# Flavor-Kategorie neben Cyberware/Bioware, keine eigene Mechanik.
CHROM_TYPEN = ("Cyberware", "Bioware", "MagWare")


async def willenskraft_verlust(campaign_id: str, person_id: str) -> int:
    """Dauerhafter Willenskraftverlust durch eingebautes Chrom.

    Gezählt wird nur, was **ausgerüstet** ist — Cyberware im Rucksack ist
    noch nicht eingebaut und kostet deshalb nichts. Wer sie ausbauen lässt,
    legt sie weg, und der Verlust fällt weg.

    **Summiert wird ungerundet, gerundet erst am Ende** — und mindestens ein
    Punkt fällt an, sobald überhaupt etwas anfällt (`chrom.verlust_gesamt`).
    Deshalb holt die Abfrage die einzelnen Werte statt gleich zu summieren:
    aus einer fertigen Summe liesse sich nicht mehr richtig runden.
    """
    from app.items.chrom import verlust_gesamt

    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        WHERE g.typ IN $typen AND g.ablage = 'AUSGERUESTET' AND NOT coalesce(g.weggeworfen, false)
        RETURN collect(coalesce(g.wVerlust, 0)) AS einzeln
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id,
                                   typen=list(CHROM_TYPEN))
        record = await result.single()
        return verlust_gesamt([float(w) for w in (record["einzeln"] if record else [])])


async def initiative_modifikator(campaign_id: str, person_id: str) -> int:
    """Initiative-Bonus aus getragener Cyberware (Regelblatt Zeile 57).

    Der Reflex-Booster gibt je nach Stufe +1/+3/+6 (Zeilen 421-444). Gezählt
    wird nur, was **ausgerüstet** ist — ein Booster im Rucksack beschleunigt
    niemanden. Anders als beim Willenskraftverlust ist hier keine Rundung
    nötig, deshalb summiert die Abfrage direkt.

    Nicht auf CHROM_TYPEN eingeschränkt: auch eine Droge ("Dash", Zeile 174:
    Initiative +2) oder ein Artefakt darf die Reihenfolge verschieben.
    """
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        WHERE g.ablage = 'AUSGERUESTET' AND NOT coalesce(g.weggeworfen, false)
        RETURN coalesce(sum(coalesce(g.initiativeBonus, 0)), 0) AS summe
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        return int(record["summe"]) if record else 0


async def slot_konflikt(campaign_id: str, person_id: str, koerperzone: str, slot: int, eigene_item_id: str) -> str | None:
    """Prüft, ob ein anderes ausgerüstetes Stück derselben Person schon
    denselben Platz belegt (Regelblatt: je Zone drei Plätze).

    Nur AUSGERUESTETE Chrom-/Bio-/MagWare zählt — im Rucksack liegende Ware
    ist nicht eingebaut und blockiert deshalb keinen Platz. Gibt den Namen
    des blockierenden Gegenstands zurück, oder None wenn der Platz frei ist.
    Ein Gegenstand blockiert sich beim eigenen Update nicht selbst.
    """
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        WHERE g.typ IN $typen AND g.ablage = 'AUSGERUESTET' AND NOT coalesce(g.weggeworfen, false)
          AND g.koerperzone = $koerperzone AND g.slot = $slot AND g.id <> $eigene_item_id
        RETURN g.name AS name
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            person_id=person_id,
            koerperzone=koerperzone,
            slot=slot,
            eigene_item_id=eigene_item_id,
            typen=list(CHROM_TYPEN),
        )
        record = await result.single()
        return record["name"] if record else None


async def ausruestungs_trait_boni(campaign_id: str, person_id: str) -> dict[str, int]:
    """Bonuswürfel auf bestehende Attribute/Fertigkeiten/Sphären aus
    ausgerüsteten Gegenständen (`traitBoni`), aufsummiert über alle Stücke.

    Anders als bei Cyberdecks (siehe `deck_boni`, dort zählt das Beste) wird
    hier **summiert**: mehrere Implantate mit je +1 auf Wahrnehmung sollen
    sich addieren, weil es unterschiedliche Verbesserungen sind statt
    austauschbarer Geräte derselben Funktion.
    """
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        WHERE g.ablage = 'AUSGERUESTET' AND NOT coalesce(g.weggeworfen, false)
          AND g.traitBoni IS NOT NULL AND g.traitBoni <> '' AND g.traitBoni <> '{}'
        RETURN collect(g.traitBoni) AS alle
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        record = await result.single()
        summe: dict[str, int] = {}
        for roh in (record["alle"] if record else []):
            try:
                boni = json.loads(roh)
            except (json.JSONDecodeError, TypeError):
                continue
            for name, wert in boni.items():
                summe[name] = summe.get(name, 0) + int(wert)
        return summe


async def ausruestungsfertigkeiten_liste(campaign_id: str, person_id: str) -> list[dict]:
    """Neue Fertigkeiten, die ausschliesslich durch ausgerüstete Gegenstände
    entstehen (`ausruestungsfertigkeiten`) — analog zu `deck_boni`, aber ohne
    festen Typ-Bezug (jeder Gegenstandstyp kann das Feld tragen, nicht nur
    Cyberdecks). Liefert je Fertigkeit den höchsten Bonus UND von welchem
    Gegenstand er stammt, damit das Blatt zeigen kann, woher sie kommt.
    """
    driver = get_driver()
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
        WHERE g.ablage = 'AUSGERUESTET' AND NOT coalesce(g.weggeworfen, false)
          AND g.ausruestungsfertigkeiten IS NOT NULL AND g.ausruestungsfertigkeiten <> ''
          AND g.ausruestungsfertigkeiten <> '{}'
        RETURN g.name AS itemName, g.ausruestungsfertigkeiten AS roh
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        eintraege: dict[str, dict] = {}
        async for record in result:
            try:
                fertigkeiten = json.loads(record["roh"])
            except (json.JSONDecodeError, TypeError):
                continue
            for name, wert in fertigkeiten.items():
                wert = int(wert)
                bisher = eintraege.get(name)
                if bisher is None or wert > bisher["bonus"]:
                    eintraege[name] = {"name": name, "bonus": wert, "quelle": record["itemName"]}
        return list(eintraege.values())
