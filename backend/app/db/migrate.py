from pathlib import Path

from app.db.neo4j_driver import get_driver

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def apply_migrations() -> None:
    driver = get_driver()
    async with driver.session() as session:
        for path in sorted(MIGRATIONS_DIR.glob("*.cypher")):
            statements = [s.strip() for s in path.read_text(encoding="utf-8").split(";") if s.strip()]
            for statement in statements:
                await session.run(statement)
