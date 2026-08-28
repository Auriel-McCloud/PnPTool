from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_campaign_gm
from app.entities.repository import PERSON_FIELDS, get_node
from app.items import repository
from app.items.schemas import GegenstandCreate, GegenstandResponse

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/personen/{person_id}/gegenstaende",
    tags=["items"],
    dependencies=[Depends(require_campaign_gm)],
)


@router.post("", response_model=GegenstandResponse)
async def create_item(campaign_id: str, person_id: str, body: GegenstandCreate):
    owner = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if owner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    sichtbarkeit = body.sichtbarkeit
    sichtbar_fuer = body.sichtbarFuer
    if sichtbarkeit is None:
        # Standard: Gegenstände von Spielercharakteren sind automatisch nur für
        # diesen Spieler sichtbar, bei NPCs bleiben sie SL-geheim. Der SL kann
        # das beim Anlegen jederzeit explizit übersteuern.
        if owner["personType"] == "PC":
            sichtbarkeit, sichtbar_fuer = "SPEZIFISCH", [person_id]
        else:
            sichtbarkeit, sichtbar_fuer = "GM", []

    item = await repository.create_gegenstand(
        campaign_id,
        person_id,
        {
            "name": body.name,
            "description": body.description,
            "notes": body.notes,
            "sichtbarkeit": sichtbarkeit,
            "sichtbarFuer": sichtbar_fuer or [],
        },
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return item


@router.get("", response_model=list[GegenstandResponse])
async def list_items(campaign_id: str, person_id: str):
    return await repository.list_gegenstaende(campaign_id, person_id)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(campaign_id: str, person_id: str, item_id: str):
    if not await repository.delete_gegenstand(campaign_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
