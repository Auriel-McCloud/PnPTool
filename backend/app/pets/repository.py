"""Neo4j-Zugriff der Critter-Pets.

Die Pet-Art steht als `petArt` direkt am Critter-`Person`-Knoten (kein
eigener Knoten). Häufchen sind kleine eigene Knoten, weil sie liegen
bleiben, wenn das Pet weiterzieht — auch über einen Neustart hinweg.
Wo das Pet gerade herumläuft, hält dagegen nur der Server im Speicher
(siehe motor.py): nach einem Neustart fängt es einfach beim Besitzer an.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver
from app.pets.logic import HAEUFCHEN_MAX


async def pets_der_kampagne(campaign_id: str) -> list[dict]:
    """Alle Critter mit Pet-Art, die an einen Spielercharakter gebunden sind.

    `mitglieder` = Spielercharaktere der Party des Besitzers, inklusive
    Besitzer. Ohne Party nur der Besitzer selbst.
    """
    query = """
        MATCH (c:Person {campaignId: $campaign_id, istCritter: true})-[:BEGLEITET]->(b:Person {personType: 'PC'})
        WHERE c.petArt IS NOT NULL AND c.petArt <> ''
        OPTIONAL MATCH (b)-[:MITGLIED_VON]->(:Party)<-[:MITGLIED_VON]-(m:Person {personType: 'PC'})
        RETURN c.id AS id, coalesce(c.alias, c.name) AS name, c.petArt AS art,
               b.id AS besitzerId, b.name AS besitzerName,
               collect(DISTINCT m.id) AS mitglieder
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        pets = []
        async for r in result:
            d = dict(r)
            mitglieder = set(d["mitglieder"] or [])
            mitglieder.add(d["besitzerId"])
            d["mitglieder"] = sorted(mitglieder)
            pets.append(d)
        return pets


async def art_lesen(campaign_id: str, critter_id: str) -> dict | None:
    query = """
        MATCH (c:Person {id: $critter_id, campaignId: $campaign_id, istCritter: true})
        RETURN c.id AS id, c.petArt AS art
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, critter_id=critter_id)
        r = await result.single()
        return dict(r) if r else None


async def art_setzen(campaign_id: str, critter_id: str, art: str | None) -> dict | None:
    query = """
        MATCH (c:Person {id: $critter_id, campaignId: $campaign_id, istCritter: true})
        SET c.petArt = $art
        RETURN c.id AS id, c.petArt AS art
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, critter_id=critter_id, art=art)
        r = await result.single()
        return dict(r) if r else None


async def haeufchen_liste(campaign_id: str, person_id: str) -> list[dict]:
    query = """
        MATCH (h:PetHaeufchen {campaignId: $campaign_id, personId: $person_id})
        RETURN h.id AS id, h.petId AS petId, h.x AS x, h.y AS y, h.erstellt AS erstellt
        ORDER BY h.erstellt
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


async def haeufchen_anlegen(campaign_id: str, person_id: str, pet_id: str, x: float, y: float) -> None:
    """Legt ein Häufchen auf diesen Bildschirm; das älteste fällt bei Überlauf weg."""
    query = """
        CREATE (:PetHaeufchen {id: $id, campaignId: $campaign_id, personId: $person_id,
                               petId: $pet_id, x: $x, y: $y, erstellt: $erstellt})
        WITH 1 AS _
        MATCH (h:PetHaeufchen {campaignId: $campaign_id, personId: $person_id})
        WITH h ORDER BY h.erstellt DESC
        WITH collect(h) AS alle
        UNWIND alle[$max..] AS zuviel
        DETACH DELETE zuviel
    """
    async with get_driver().session() as session:
        await session.run(
            query,
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            person_id=person_id,
            pet_id=pet_id,
            x=x,
            y=y,
            erstellt=datetime.now(timezone.utc).isoformat(),
            max=HAEUFCHEN_MAX,
        )


async def haeufchen_weg(campaign_id: str, person_id: str, haeufchen_id: str) -> None:
    """Nur vom eigenen Bildschirm — fremde Häufchen kann man nicht wegmachen."""
    query = """
        MATCH (h:PetHaeufchen {id: $id, campaignId: $campaign_id, personId: $person_id})
        DETACH DELETE h
    """
    async with get_driver().session() as session:
        await session.run(query, id=haeufchen_id, campaign_id=campaign_id, person_id=person_id)
