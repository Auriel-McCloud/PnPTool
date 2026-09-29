import json

from app.auth.menue import normalisiere_layouts
from app.db.neo4j_driver import get_driver


async def get_gm_by_username(username: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (g:GMUser) WHERE toLower(g.username) = toLower($username) "
            "RETURN g.id AS id, g.username AS username, g.passwordHash AS passwordHash",
            username=username,
        )
        record = await result.single()
        return dict(record) if record else None


async def get_menue_layouts(gm_id: str) -> dict:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (g:GMUser {id: $gm_id}) RETURN g.menueLayouts AS roh",
            gm_id=gm_id,
        )
        record = await result.single()
        return normalisiere_layouts(record["roh"] if record else None)


async def set_menue_layouts(gm_id: str, layouts: dict) -> dict:
    sauber = normalisiere_layouts(json.dumps(layouts))
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (g:GMUser {id: $gm_id})
            SET g.menueLayouts = $roh
            RETURN g.menueLayouts AS roh
            """,
            gm_id=gm_id,
            roh=json.dumps(sauber, ensure_ascii=False),
        )
        record = await result.single()
        return normalisiere_layouts(record["roh"] if record else None)
