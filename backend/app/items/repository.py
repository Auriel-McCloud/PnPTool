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
    g.gewicht AS gewicht, g.kapazitaet AS kapazitaet,
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
    record["ablage"] = record.get("ablage") or "RUCKSACK"
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
            gewicht: $gewicht, kapazitaet: $kapazitaet
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
        OPTIONAL MATCH (p:Person)-[:BESITZT]->(g)
        {LIEGT_IN}
        RETURN {RETURN_FIELDS}, p.id AS ownerId, p.name AS ownerName, p.personType AS ownerPersonType
        ORDER BY p.name, g.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode(dict(record)) async for record in result]


async def update_gegenstand(campaign_id: str, item_id: str, data: dict) -> dict | None:
    changed = {k: v for k, v in data.items() if v is not None}
    if "eigenschaften" in changed:
        changed["eigenschaften"] = json.dumps(changed["eigenschaften"])

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
    copy = await create_gegenstand(
        campaign_id,
        ziel_person_id,
        {
            "name": source["name"],
            "description": source["description"],
            "notes": source["notes"],
            "typ": source["typ"],
            "preis": source["preis"],
            "kraft": source["kraft"],
            "seltenheit": source["seltenheit"],
            "eigenschaften": source["eigenschaften"],
            "zeigeInGraph": source["zeigeInGraph"],
            "einzigartig": True,
            "hatMenge": source["hatMenge"],
            "menge": source["menge"],
            "istVorlage": False,
            "automatischImShop": False,
            "sichtbarkeit": sichtbarkeit,
            "sichtbarFuer": sichtbar_fuer,
        },
    )
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

    Als Behälter zählen Gegenstände der Person, die selbst etwas aufnehmen
    können — derzeit über den Typ erkannt. Ein Gegenstand kann nicht in sich
    selbst liegen; verschachtelte Behälter sind erlaubt, aber ungeprüft
    (siehe CLAUDE.md).
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (o:Ort {campaignId: $campaign_id})
            RETURN o.id AS id, o.name AS name, 'Ort' AS kind
            UNION
            MATCH (p:Person {id: $person_id})-[:BESITZT]->(g:Gegenstand)
            WHERE g.typ IN ['Fahrzeug', 'Behälter']
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
            WHERE g.ablage IN ['AUSGERUESTET', 'RUCKSACK']
        WITH p, sum({_GEWICHT}) AS last
        OPTIONAL MATCH (p)-[r:HAS_TRAIT]->(t:TraitDef {{name: $attribut}})
        RETURN p.id AS id, p.name AS name, 'Person' AS art, p.personType AS personType,
               last AS last, coalesce(r.rating, 0) * $pro_punkt AS kapazitaet

        UNION

        MATCH (b:Gegenstand {{campaignId: $campaign_id}})
            WHERE coalesce(b.kapazitaet, 0) > 0
        OPTIONAL MATCH (g:Gegenstand)-[:LIEGT_IN]->(b)
        RETURN b.id AS id, b.name AS name, 'Gegenstand' AS art, NULL AS personType,
               sum({_GEWICHT}) AS last, b.kapazitaet AS kapazitaet
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, attribut=attribut, pro_punkt=pro_punkt)
        return [dict(record) async for record in result]


async def commlink_cyberwall(campaign_id: str, person_id: str) -> int:
    """Cyberwall-Wert des Commlinks, das diese Person bei sich hat.

    Zählt nur, was am Körper ist (ausgerüstet oder mitgeführt) — ein Commlink
    im Versteck schützt niemanden. Bei mehreren gilt der beste Wert, nicht die
    Summe: man ist über ein Gerät online, nicht über alle gleichzeitig.
    Ergibt 0, wenn keines da ist; dann ist die Person offline.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
            WHERE g.typ = 'Commlink' AND g.ablage IN ['AUSGERUESTET', 'RUCKSACK']
            RETURN max(coalesce(g.cyberwall, 0)) AS wert
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
        return int(record["wert"] or 0) if record else 0
