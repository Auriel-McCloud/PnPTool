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
