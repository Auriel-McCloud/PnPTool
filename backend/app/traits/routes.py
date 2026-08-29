from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign
from app.traits import repository
from app.traits.schemas import TraitDefResponse, TraitRatingResponse, TraitRatingUpdate

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["traits"], dependencies=[Depends(require_campaign_zugang)])


@router.get("/traitkatalog", response_model=list[TraitDefResponse])
async def get_catalog(campaign_id: str):
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return await repository.list_catalog(campaign["ruleset"])


@router.get("/personen/{person_id}/werte", response_model=list[TraitRatingResponse])
async def get_werte(campaign_id: str, person_id: str):
    return await repository.get_ratings_for_entity(campaign_id, person_id)


@router.put("/personen/{person_id}/werte/{trait_def_id}", response_model=TraitRatingResponse, dependencies=[Depends(require_campaign_gm)])
async def set_wert(campaign_id: str, person_id: str, trait_def_id: str, body: TraitRatingUpdate):
    result = await repository.set_rating(campaign_id, person_id, trait_def_id, body.rating, body.maxOverride)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Fähigkeit nicht gefunden")
    return result
