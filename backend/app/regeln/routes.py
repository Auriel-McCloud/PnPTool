from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign
from app.regeln import repository

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/erklaerungen",
    tags=["regeln"],
    dependencies=[Depends(require_campaign_zugang)],
)


class ErklaerungResponse(BaseModel):
    schluessel: str
    titel: str
    text: str
    quelle: str


class ErklaerungInput(BaseModel):
    titel: str = ""
    text: str = ""
    # HAND = jemand hat es geschrieben, KI = ein Modell hat es erzeugt und
    # niemand hat es bisher gegengelesen.
    quelle: str = Field(default="HAND", pattern="^(HAND|KI)$")


async def _ruleset(campaign_id: str) -> str:
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return campaign["ruleset"]


@router.get("", response_model=list[ErklaerungResponse])
async def alle_erklaerungen(campaign_id: str):
    """Alle Erklärungen auf einmal.

    Einzeln nachzuladen wäre bei jedem Antippen eine Anfrage — und die
    Oberfläche muss vorher wissen, zu welchen Begriffen überhaupt etwas da
    ist, um nur dort ein Zeichen zu setzen. Es sind wenige Kilobyte.

    Auch für Spieler lesbar: Erklärungen sind Regelwissen, nichts Geheimes.
    Was die Spielleitung verborgen halten will, gehört in die Notizen.
    """
    return await repository.list_erklaerungen(await _ruleset(campaign_id))


@router.put(
    "/{schluessel:path}",
    response_model=ErklaerungResponse,
    dependencies=[Depends(require_campaign_gm)],
)
async def erklaerung_setzen(campaign_id: str, schluessel: str, body: ErklaerungInput):
    """Erklärung schreiben oder ändern. Leerer Text entfernt sie wieder.

    `:path` im Pfad, weil Schlüssel einen Doppelpunkt enthalten
    (`trait:Körperkraft`) — ohne das schneidet Starlette am Trennzeichen ab.
    """
    return await repository.setze_erklaerung(
        await _ruleset(campaign_id), schluessel, body.titel, body.text, body.quelle
    )
