"""Einmal-Migration (26.10.2026): bestehende Drohnen/Fahrzeuge nachruesten.

Setzt den 3er-Lebenspunkte-Basiswert und legt die automatische
Aussenhuelle-Ruestung nach, fuer Personen, die VOR
entities/routes.py::_drohnen_startausstattung angelegt wurden. Idempotent
(ueberspringt, wer schon ein istNatuerlich-Item hat) -- kann gefahrlos
mehrfach laufen.

Aufruf (im Backend-Container bzw. mit aktiviertem .venv):
    python3 scripts/migrate_drohnen_startausstattung.py
"""

import asyncio

from app.db.neo4j_driver import get_driver
from app.entities.repository import PERSON_FIELDS, update_node
from app.items import repository as items_repository
from app.items.schemas import GegenstandCreate


async def main() -> None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (p:Person) WHERE p.istDrohne = true OR p.istFahrzeug = true "
            "RETURN p.id AS id, p.campaignId AS campaignId, p.name AS name, "
            "p.gesundheitGrundwert AS gesundheitGrundwert"
        )
        rows = [dict(r) async for r in result]

    print(f"Gefunden: {len(rows)} Drohne(n)/Fahrzeug(e)")
    for row in rows:
        cid, pid, name = row["campaignId"], row["id"], row["name"]
        grundwert = row.get("gesundheitGrundwert")
        if grundwert is None or grundwert == -1:
            await update_node("Person", PERSON_FIELDS, cid, pid, {"gesundheitGrundwert": 3})
            print(f"  {name} ({pid}): gesundheitGrundwert -> 3")
        else:
            print(f"  {name} ({pid}): gesundheitGrundwert bereits explizit {grundwert}, unangetastet")

        bestand = await items_repository.list_gegenstaende(cid, pid)
        hat_schon = any(i.get("istNatuerlich") for i in bestand)
        if hat_schon:
            print(f"  {name} ({pid}): hat bereits ein istNatuerlich-Item, uebersprungen")
            continue
        neu = await items_repository.create_gegenstand(
            cid,
            pid,
            GegenstandCreate(
                name="Außenhülle",
                description="Eingebaute Panzerung — Kästchen/Reduktion wachsen automatisch mit "
                "Widerstandsfähigkeit/Außenhülle mit, kein eigenes Item zum An-/Ablegen.",
                typ="Rüstung",
                istNatuerlich=True,
                einzigartig=False,
                ablage="AUSGERUESTET",
                sichtbarkeit="GM",
                sichtbarFuer=[],
            ).model_dump(),
        )
        print(f"  {name} ({pid}): Außenhülle-Item angelegt ({(neu or {}).get('id', 'FEHLER')})")


if __name__ == "__main__":
    asyncio.run(main())
