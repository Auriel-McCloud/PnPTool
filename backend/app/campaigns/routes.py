from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import require_gm
from app.campaigns.repository import create_campaign, list_campaigns_for_gm

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class CampaignCreateRequest(BaseModel):
    name: str


class CampaignResponse(BaseModel):
    id: str
    name: str


@router.post("", response_model=CampaignResponse)
async def create(body: CampaignCreateRequest, claims: dict = Depends(require_gm)):
    return await create_campaign(body.name, claims["sub"])


@router.get("", response_model=list[CampaignResponse])
async def list_mine(claims: dict = Depends(require_gm)):
    return await list_campaigns_for_gm(claims["sub"])
