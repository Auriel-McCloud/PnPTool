"""Nebenfiguren-Routen (10.11.2026).

Anlegen, Lesen und Bearbeiten laufen über die normalen Personen-Routen
(`POST/PATCH /personen`, `GET /personen?istNebenfigur=true`) — eine
Nebenfigur ist ein `Person`-Knoten mit `istNebenfigur=true`. Hier steht nur,
was es dort nicht gibt: die Einbahnstraße zum vollen NPC.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_campaign_gm
from app.entities.filterung import klartext
from app.entities.repository import PERSON_FIELDS, get_node
from app.entities.schemas import PersonResponse
from app.ki.routes import _idee_anlegen
from app.nebenfiguren.logic import zu_npc_prompt

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/nebenfiguren",
    tags=["nebenfiguren"],
    dependencies=[Depends(require_campaign_gm)],
)


@router.post("/{person_id}/zu-npc", response_model=PersonResponse)
async def zu_npc_machen(campaign_id: str, person_id: str):
    """Macht aus einer Nebenfigur in-place einen vollen NPC — ohne Rückweg.

    Die Charakter-KI baut den Bogen (derselbe regelkonforme Zwei-Stufen-Weg
    wie ✨ Charakter, inkl. Tutorial-Shop-Einkauf); die freien Fähigkeiten
    landen auf der passendsten Katalog-Fertigkeit. Name, Rasse, Beschreibung,
    Notizen, Bilder, Beziehungen und Kontakte bleiben. KI-Fehler → 502, die
    Nebenfigur bleibt dann unverändert.
    """
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nebenfigur nicht gefunden")
    if not person.get("istNebenfigur"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Das ist schon ein voller NPC.")

    prompt = zu_npc_prompt(person, klartext(person.get("description")), klartext(person.get("notes")))
    await _idee_anlegen(campaign_id, "charakter", prompt, nebenfigur=person)

    neu = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if neu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nebenfigur nicht gefunden")
    return neu
