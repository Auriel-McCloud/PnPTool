"""Schulden nach der Charaktererstellung: Hai wiederverwenden oder Stub.

KI-Füllung wie bei Kontakten kommt später — Erstellung soll nicht auf
einen LLM-Call warten und nicht extra kosten, wenn schon ein Hai da ist.
"""

from app.entities.repository import PERSON_FIELDS, create_node, list_nodes
from app.entities.schemas import PersonCreate
from app.hintergruende import repository
from app.hintergruende.kredithai import (
    bestehenden_kredithai,
    kredithai_rasse,
    schulden_beschreibung,
    schulden_punkte,
)
from app.kontakte import repository as kontakte_repository
from app.rassen import repository as rassen_repository


async def nach_erstellung(campaign_id: str, person_id: str, kredit_freebees: int) -> dict | None:
    """No-Op ohne Kredit. Sonst HAT_KREDITHAI + Schuldet + KENNT (Chat zu)."""
    rating = schulden_punkte(kredit_freebees)
    if rating <= 0:
        return None

    bestehend = await repository.hole_kredithai(campaign_id, person_id)
    hai_id = bestehend["haiId"] if bestehend else None
    if not hai_id:
        personen = await list_nodes("Person", PERSON_FIELDS, campaign_id)
        npcs = [n for n in personen if n.get("personType") == "NPC"]
        hai = bestehenden_kredithai(npcs)
        if hai:
            hai_id = hai["id"]
        else:
            rassen = await rassen_repository.liste_fuer_kampagne(campaign_id)
            stub = await create_node(
                "Person",
                PERSON_FIELDS,
                campaign_id,
                PersonCreate(
                    name="Kredithai",
                    personType="NPC",
                    description="Zwielichtiger Geldverleiher. Noch nicht ausgearbeitet.",
                    istKredithai=True,
                    istEntwurf=True,
                    sichtbarkeit="GM",
                    rasse=kredithai_rasse(rassen),
                    erstellungAbgeschlossen=True,
                ).model_dump(),
            )
            hai_id = stub["id"]

    await repository.setze_kredithai(campaign_id, person_id, hai_id, rating)
    await repository.setze_schuldet_verbindung(
        campaign_id, person_id, hai_id, schulden_beschreibung(kredit_freebees)
    )
    await kontakte_repository.anlegen(
        campaign_id, person_id, hai_id, stufe="GESEHEN", chat_offen=False
    )
    return {"haiId": hai_id, "rating": rating}
