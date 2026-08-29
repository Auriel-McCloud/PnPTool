from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.auth.dependencies import require_gm
from app.campaigns.repository import (
    EINSTELLUNGEN_DEFAULTS,
    create_campaign,
    get_einstellungen,
    list_campaigns_for_gm,
    set_einstellungen,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class CampaignCreateRequest(BaseModel):
    name: str
    ruleset: str = "neotopia"


class CampaignResponse(BaseModel):
    id: str
    name: str
    ruleset: str


@router.post("", response_model=CampaignResponse)
async def create(body: CampaignCreateRequest, claims: dict = Depends(require_gm)):
    return await create_campaign(body.name, body.ruleset, claims["sub"])


@router.get("", response_model=list[CampaignResponse])
async def list_mine(claims: dict = Depends(require_gm)):
    return await list_campaigns_for_gm(claims["sub"])


# Kampagnenweite Spieleinstellungen. Lesen darf jeder mit Zugang — die
# Spieler-Oberfläche braucht z.B. zu wissen, ob Gewicht angezeigt wird.
# Ändern darf nur die Spielleitung.
einstellungen_router = APIRouter(prefix="/api/campaigns/{campaign_id}/einstellungen", tags=["campaigns"])


@einstellungen_router.get("", dependencies=[Depends(require_campaign_zugang)])
async def einstellungen_lesen(campaign_id: str) -> dict:
    return await get_einstellungen(campaign_id)


@einstellungen_router.patch("", dependencies=[Depends(require_campaign_gm)])
async def einstellungen_aendern(campaign_id: str, body: dict) -> dict:
    """Ändert einzelne Einstellungen.

    Bewusst ein offenes dict statt eines festen Schemas: die Sammlung soll
    wachsen können, ohne dass hier und im Frontend jedes Mal ein Feld
    nachgetragen werden muss. Unbekannte Schlüssel verwirft das Repository.
    """
    return await set_einstellungen(campaign_id, body)


@einstellungen_router.get("/standard", dependencies=[Depends(require_campaign_zugang)])
async def einstellungen_standard(campaign_id: str) -> dict:
    """Die Ausgangswerte — damit die Oberfläche weiß, was es überhaupt gibt."""
    return EINSTELLUNGEN_DEFAULTS
