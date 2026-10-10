"""Narrativer Hintergrund-Katalog: SL-CRUD, Spieler dürfen lesen."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.hintergruende import repository
from app.hintergruende.schemas import HintergrundCreate, HintergrundResponse, HintergrundUpdate

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/hintergruende",
    tags=["hintergruende"],
    dependencies=[Depends(require_campaign_zugang)],
)


@router.get("", response_model=list[HintergrundResponse])
async def liste(campaign_id: str):
    """Katalog dieser Kampagne — SL-Tabelle und Spieler-Erstellung."""
    return await repository.liste(campaign_id)


@router.post("", response_model=HintergrundResponse, dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: HintergrundCreate):
    return await repository.anlegen(campaign_id, body.model_dump())


@router.patch("/{hintergrund_id}", response_model=HintergrundResponse, dependencies=[Depends(require_campaign_gm)])
async def aendern(campaign_id: str, hintergrund_id: str, body: HintergrundUpdate):
    eintrag = await repository.aendern(campaign_id, hintergrund_id, body.model_dump())
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hintergrund nicht gefunden")
    return eintrag


@router.delete("/{hintergrund_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def loeschen(campaign_id: str, hintergrund_id: str):
    if not await repository.loeschen(campaign_id, hintergrund_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hintergrund nicht gefunden")
