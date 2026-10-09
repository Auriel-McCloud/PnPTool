"""Auto-Hooks fürs Spieler-Lexikon — Fachmodule rufen diese Funktionen, nicht
die Entdeckungs-Logik direkt (gleiches Prinzip wie
app/ereignisprotokoll/hooks.py).

Recompute läuft additiv (siehe repository.py::neu_berechnen_fuer_person) —
ein zu häufiger Aufruf verschwendet höchstens etwas Rechenzeit, verliert aber
nie bereits entdeckte Einträge. Deshalb bei Unsicherheit lieber zu oft als zu
selten auslösen.
"""

from app.lexikon import repository


async def person_neu_zugeordnet(campaign_id: str, person_id: str) -> None:
    """Ein PC wird frisch an einen Spieler-Zugang gebunden — stellt sicher,
    dass seine Entdeckungs-Historie von Anfang an mitläuft."""
    await repository.neu_berechnen_fuer_person(campaign_id, person_id)


async def party_veraendert(campaign_id: str, party_id: str) -> None:
    """Mitgliedschaft oder Aufenthaltsort einer Party hat sich geändert —
    neu berechnen für alle aktuellen Mitglieder (ein neues Mitglied kann auch
    für die bereits anwesenden PCs neue Pfade öffnen, z.B. über dessen
    Besitz)."""
    from app.db.neo4j_driver import get_driver

    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person)-[:MITGLIED_VON]->(:Party {id: $party_id, campaignId: $campaign_id})
            RETURN p.id AS id
            """,
            campaign_id=campaign_id,
            party_id=party_id,
        )
        mitglieder = [r["id"] async for r in result]
    for person_id in mitglieder:
        await repository.neu_berechnen_fuer_person(campaign_id, person_id)


async def campaign_weit_neu_berechnen(campaign_id: str) -> None:
    """Grobes, aber sicheres Mittel nach Änderungen, die potenziell JEDEN
    PC betreffen können (neue/geänderte VERBINDUNG, LEBT_IN hinzugefügt,
    eine Entität wird sichtbar, ein Gegenstand wird story-relevant). Läuft
    über alle PCs der Kampagne — bei der Projektgröße (ein Spieltisch pro
    Kampagne) unproblematisch, siehe Begründung in repository.py."""
    from app.db.neo4j_driver import get_driver

    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (p:Person {campaignId: $campaign_id, personType: 'PC'}) RETURN p.id AS id",
            campaign_id=campaign_id,
        )
        pcs = [r["id"] async for r in result]
    for person_id in pcs:
        await repository.neu_berechnen_fuer_person(campaign_id, person_id)
