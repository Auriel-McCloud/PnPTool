"""Einmalige Umstellung: Chrom ist verbaut, nicht ausgerüstet.

Hintergrund (04.09.2026): Cyber-, Bio- und MagWare lag bis dahin als
`ablage=AUSGERUESTET` im selben Topf wie eine Jacke. Das neue Feld `verbaut`
trennt beides.

Marks Entscheidung zu den Bestandsdaten: **alle als nicht verbaut** — er
setzt sie bewusst einzeln ein. 5 der 6 Stücke lagen ohnehin im Rucksack und
wirkten damit gar nicht.

Idempotent: mehrfaches Ausführen ändert nichts.
"""

import asyncio

from app.db.neo4j_driver import get_driver

CHROM_TYPEN = ["Cyberware", "Bioware", "MagWare"]


async def main() -> None:
    driver = get_driver()
    async with driver.session() as session:
        # Vorher zählen, damit die Ausgabe belegt, was passiert ist.
        result = await session.run(
            """
            MATCH (g:Gegenstand)
            WHERE g.typ IN $typen
            RETURN g.typ AS typ, g.ablage AS ablage,
                   coalesce(g.verbaut, false) AS verbaut, count(*) AS n
            ORDER BY typ, ablage
            """,
            typen=CHROM_TYPEN,
        )
        print("Vorher:")
        async for r in result:
            print(f"  {dict(r)}")

        result = await session.run(
            """
            MATCH (g:Gegenstand)
            WHERE g.typ IN $typen AND g.verbaut IS NULL
            SET g.verbaut = false,
                g.entfernungBeantragt = false,
                g.ablage = CASE WHEN g.ablage = 'AUSGERUESTET' THEN 'RUCKSACK' ELSE g.ablage END
            RETURN count(g) AS geaendert
            """,
            typen=CHROM_TYPEN,
        )
        record = await result.single()
        print(f"\nUmgestellt: {record['geaendert'] if record else 0}")

        result = await session.run(
            """
            MATCH (g:Gegenstand)
            WHERE g.typ IN $typen
            RETURN g.typ AS typ, g.ablage AS ablage,
                   coalesce(g.verbaut, false) AS verbaut, count(*) AS n
            ORDER BY typ, ablage
            """,
            typen=CHROM_TYPEN,
        )
        print("\nNachher:")
        async for r in result:
            print(f"  {dict(r)}")

    await driver.close()


if __name__ == "__main__":
    asyncio.run(main())
