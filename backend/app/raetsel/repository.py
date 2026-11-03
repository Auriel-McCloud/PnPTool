"""Ein Ring pro Kampagne, als JSON am Kampagnen-Knoten.

Kein eigener Knotentyp: der Export nimmt die Kampagne samt Properties mit,
eine Weisslisten-Zeile wäre hier nur eine zweite Stelle, die vergessen wird.
"""

import json

from app.db.neo4j_driver import get_driver
from app.raetsel.logic import normalisiere


async def laden(campaign_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign {id: $id}) RETURN c.raetselJson AS roh",
            id=campaign_id,
        )
        record = await result.single()
    if record is None:
        return None
    roh = record["roh"]
    if not roh:
        return normalisiere(None)
    try:
        return normalisiere(json.loads(roh))
    except json.JSONDecodeError:
        return normalisiere(None)


async def speichern(campaign_id: str, zustand: dict) -> dict | None:
    driver = get_driver()
    text = json.dumps(zustand, ensure_ascii=False)
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $id})
            SET c.raetselJson = $text
            RETURN c.id AS id
            """,
            id=campaign_id,
            text=text,
        )
        record = await result.single()
    if record is None:
        return None
    return zustand
