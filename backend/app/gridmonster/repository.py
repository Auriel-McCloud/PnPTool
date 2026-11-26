"""Neo4j-Zugriff für GridMonster-Figuren (Grundgerüst 26.11.2026).

Datenmodell (Mark, 26.11.2026):
    Mensch und Monster sind je eine eigene Figur = `Person`-Knoten mit
    `istMonster` (false = Mensch) und `personType` 'PC'/'NPC' wie bei
    NeotopiA. Die Werte hängen per `HAS_TRAIT {rating}` an den
    GridMonster-`TraitDef`s (ruleset 'gridmonster', siehe katalog.py).
    Attribute/Fertigkeiten speichern die Würfelgröße (4/6/8/12/20, 0 = nicht
    gelernt), feste Werte (LP, Energie, Stufe …) die Zahl selbst.

Noch nicht gebaut (nächster Schritt): Partnerschaft Mensch↔Monster,
Spieler-Zugang mit zwei Figuren, Inventar je Figur.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver
from app.gridmonster import katalog


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


async def seed() -> None:
    """Regelsystem 'GridMonster' und seinen Katalog anlegen/aktualisieren (idempotent)."""
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MERGE (r:Regelsystem {name: $name})
            ON CREATE SET r.id = $id, r.beschreibung = $beschreibung,
                          r.erstelltAm = $jetzt, r.aktualisiertAm = $jetzt
            """,
            name=katalog.REGELSYSTEM_NAME,
            id=str(uuid.uuid4()),
            beschreibung="Partner-Monster-Rollenspiel: jeder spielt einen Menschen und ein Monster.",
            jetzt=_jetzt(),
        )
        await session.run(
            """
            UNWIND $eintraege AS e
            MERGE (t:TraitDef {id: e.id})
            SET t.ruleset = $ruleset, t.name = e.name, t.category = e.category,
                t.sortOrder = e.sortOrder, t.defaultMax = e.defaultMax,
                t.attribut = e.attribut, t.nurFuer = e.nurFuer
            """,
            eintraege=katalog.katalog_eintraege(),
            ruleset=katalog.RULESET,
        )


_FIGUR = """
    n.id AS id, n.name AS name, n.personType AS personType,
    coalesce(n.istMonster, false) AS istMonster,
    coalesce(n.description, '') AS description
"""


async def liste(campaign_id: str) -> list[dict]:
    driver = get_driver()
    query = f"""
        MATCH (n:Person {{campaignId: $campaign_id}})
        WHERE NOT coalesce(n.geloescht, false)
        OPTIONAL MATCH (n)-[r:HAS_TRAIT]->(t:TraitDef {{ruleset: $ruleset}})
        WITH n, collect([t.id, r.rating]) AS paare
        RETURN {_FIGUR}, paare
        ORDER BY toLower(n.name)
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, ruleset=katalog.RULESET)
        figuren = []
        async for record in result:
            figur = dict(record)
            paare = figur.pop("paare")
            figur["werte"] = {tid: rating for tid, rating in paare if tid is not None}
            figuren.append(figur)
        return figuren


async def einzeln(campaign_id: str, figur_id: str) -> dict | None:
    for figur in await liste(campaign_id):
        if figur["id"] == figur_id:
            return figur
    return None


async def anlegen(campaign_id: str, name: str, ist_monster: bool, person_type: str, beschreibung: str) -> dict:
    driver = get_driver()
    figur_id = str(uuid.uuid4())
    werte = [{"id": tid, "rating": r} for tid, r in katalog.startwerte(ist_monster).items()]
    query = """
        MATCH (c:Campaign {id: $campaign_id})
        CREATE (n:Person {id: $id, campaignId: $campaign_id, stammtVonId: $id,
                          name: $name, personType: $person_type, istMonster: $ist_monster,
                          description: $beschreibung, istEntwurf: false})
        CREATE (c)-[:HAT_ENTITAET]->(n)
        WITH n
        UNWIND $werte AS w
        MATCH (t:TraitDef {id: w.id})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = w.rating
    """
    async with driver.session() as session:
        await session.run(
            query, campaign_id=campaign_id, id=figur_id, name=name, person_type=person_type,
            ist_monster=ist_monster, beschreibung=beschreibung, werte=werte,
        )
    figur = await einzeln(campaign_id, figur_id)
    assert figur is not None
    return figur


async def aendern(campaign_id: str, figur_id: str, daten: dict) -> dict | None:
    erlaubt = {k: v for k, v in daten.items() if k in ("name", "personType", "description") and v is not None}
    if erlaubt:
        driver = get_driver()
        sets = ", ".join(f"n.{k} = ${k}" for k in erlaubt)
        async with driver.session() as session:
            await session.run(
                f"MATCH (n:Person {{id: $figur_id, campaignId: $campaign_id}}) SET {sets}",
                figur_id=figur_id, campaign_id=campaign_id, **erlaubt,
            )
    return await einzeln(campaign_id, figur_id)


async def wert_setzen(campaign_id: str, figur_id: str, trait: str, wert: int) -> None:
    driver = get_driver()
    query = """
        MATCH (n:Person {id: $figur_id, campaignId: $campaign_id})
        MATCH (t:TraitDef {id: $trait, ruleset: $ruleset})
        MERGE (n)-[r:HAS_TRAIT]->(t)
        SET r.rating = $wert
    """
    async with driver.session() as session:
        await session.run(
            query, figur_id=figur_id, campaign_id=campaign_id, trait=trait,
            ruleset=katalog.RULESET, wert=wert,
        )


async def in_papierkorb(campaign_id: str, figur_id: str) -> bool:
    """Papierkorb statt Löschen — auch für PCs, weil GridMonster-Figuren noch
    keine SPIELT-Kante haben (anders als `entities.delete_node`)."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (n:Person {id: $figur_id, campaignId: $campaign_id})
            WHERE NOT coalesce(n.geloescht, false)
            SET n.geloescht = true
            RETURN count(n) AS anzahl
            """,
            figur_id=figur_id, campaign_id=campaign_id,
        )
        record = await result.single()
        return bool(record and record["anzahl"])
