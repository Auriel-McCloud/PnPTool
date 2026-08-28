import json
import uuid

from app.db.neo4j_driver import get_driver

RETURN_FIELDS = """
    g.id AS id, g.name AS name, g.description AS description, g.notes AS notes,
    g.typ AS typ, g.preis AS preis, g.kraft AS kraft,
    g.eigenschaften AS eigenschaften, g.zeigeInGraph AS zeigeInGraph,
    g.einzigartig AS einzigartig, g.hatMenge AS hatMenge, g.menge AS menge,
    g.istVorlage AS istVorlage, g.seltenheit AS seltenheit, g.automatischImShop AS automatischImShop,
    g.bildUrl AS bildUrl, g.sichtbarkeit AS sichtbarkeit, g.sichtbarFuer AS sichtbarFuer
"""


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
    record["einzigartig"] = _or_default(record.get("einzigartig"), True)
    record["hatMenge"] = _or_default(record.get("hatMenge"), False)
    record["menge"] = _or_default(record.get("menge"), 1)
    record["istVorlage"] = _or_default(record.get("istVorlage"), False)
    record["seltenheit"] = _or_default(record.get("seltenheit"), 1)
    record["automatischImShop"] = _or_default(record.get("automatischImShop"), False)
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
            typ: $typ, preis: $preis, kraft: $kraft, eigenschaften: $eigenschaften,
            zeigeInGraph: $zeigeInGraph, einzigartig: $einzigartig, hatMenge: $hatMenge, menge: $menge,
            istVorlage: $istVorlage, seltenheit: $seltenheit, automatischImShop: $automatischImShop, bildUrl: '',
            sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbarFuer
        })
    """
    if owner_person_id:
        query = f"""
            MATCH (p:Person {{id: $owner_id, campaignId: $campaign_id}})
            {create_clause}
            CREATE (p)-[:BESITZT]->(g)
            RETURN {RETURN_FIELDS}
        """
    else:
        query = f"{create_clause}\n        RETURN {RETURN_FIELDS}"

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
        )
        record = await result.single()
        return _decode(dict(record)) if record else None


async def list_gegenstaende(campaign_id: str, owner_person_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (p:Person {{id: $owner_id, campaignId: $campaign_id}})-[:BESITZT]->(g:Gegenstand)
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
        query = f"MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}}) RETURN {RETURN_FIELDS}"
        async with driver.session() as session:
            result = await session.run(query, campaign_id=campaign_id, item_id=item_id)
            record = await result.single()
            return _decode(dict(record)) if record else None

    set_clause = ", ".join(f"g.{k} = ${k}" for k in changed)
    query = f"""
        MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}})
        SET {set_clause}
        RETURN {RETURN_FIELDS}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, item_id=item_id, **changed)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def get_gegenstand(campaign_id: str, item_id: str) -> dict | None:
    driver = get_driver()
    query = f"MATCH (g:Gegenstand {{id: $item_id, campaignId: $campaign_id}}) RETURN {RETURN_FIELDS}"
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
