"""API für GridMonster-Figuren (Grundgerüst 26.11.2026, nur SL)."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import require_campaign_gm
from app.campaigns.repository import get_campaign
from app.gridmonster import katalog, repository

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/gridmonster",
    tags=["gridmonster"],
    dependencies=[Depends(require_campaign_gm)],
)


class FigurCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    istMonster: bool
    personType: Literal["PC", "NPC"] = "NPC"
    description: str = ""


class FigurUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    personType: Literal["PC", "NPC"] | None = None
    description: str | None = None


class WertSetzen(BaseModel):
    wert: int


class Figur(BaseModel):
    id: str
    name: str
    personType: str
    istMonster: bool
    description: str = ""
    werte: dict[str, int] = {}


async def _nur_gridmonster(campaign_id: str) -> None:
    kampagne = await get_campaign(campaign_id)
    if not kampagne or kampagne.get("ruleset") != katalog.RULESET:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Keine GridMonster-Kampagne")


@router.get("/katalog")
async def katalog_lesen(campaign_id: str):
    return katalog.katalog_antwort()


@router.get("/figuren", response_model=list[Figur])
async def figuren(campaign_id: str):
    await _nur_gridmonster(campaign_id)
    return await repository.liste(campaign_id)


@router.post("/figuren", response_model=Figur)
async def figur_anlegen(campaign_id: str, body: FigurCreate):
    await _nur_gridmonster(campaign_id)
    return await repository.anlegen(
        campaign_id, body.name.strip(), body.istMonster, body.personType, body.description,
    )


@router.patch("/figuren/{figur_id}", response_model=Figur)
async def figur_aendern(campaign_id: str, figur_id: str, body: FigurUpdate):
    figur = await repository.aendern(campaign_id, figur_id, body.model_dump(exclude_unset=True))
    if figur is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Figur nicht gefunden")
    return figur


@router.put("/figuren/{figur_id}/werte/{trait_id}", response_model=Figur)
async def wert_setzen(campaign_id: str, figur_id: str, trait_id: str, body: WertSetzen):
    figur = await repository.einzeln(campaign_id, figur_id)
    if figur is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Figur nicht gefunden")
    fehler = katalog.pruefe_wert(trait_id, body.wert, figur["istMonster"])
    if fehler:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, fehler)
    await repository.wert_setzen(campaign_id, figur_id, trait_id, body.wert)
    return await repository.einzeln(campaign_id, figur_id)


@router.delete("/figuren/{figur_id}", status_code=status.HTTP_204_NO_CONTENT)
async def figur_wegwerfen(campaign_id: str, figur_id: str):
    if not await repository.in_papierkorb(campaign_id, figur_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Figur nicht gefunden")
