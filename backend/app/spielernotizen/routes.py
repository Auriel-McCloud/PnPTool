"""Spieler-Notizen: nur der eigene Zugang, nie die Spielleitung."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.players.routes import require_spieler
from app.spielernotizen import repository
from app.spielernotizen.schemas import SpielerNotizCreate, SpielerNotizResponse, SpielerNotizUpdate

router = APIRouter(prefix="/api/spieler/notizen", tags=["spielernotizen"])


@router.get("", response_model=list[SpielerNotizResponse])
async def liste(spieler: dict = Depends(require_spieler)):
    return await repository.liste(spieler["id"], spieler["campaignId"])


@router.post("", response_model=SpielerNotizResponse)
async def anlegen(body: SpielerNotizCreate, spieler: dict = Depends(require_spieler)):
    return await repository.anlegen(spieler["id"], spieler["campaignId"], body.model_dump())


@router.patch("/{notiz_id}", response_model=SpielerNotizResponse)
async def aendern(notiz_id: str, body: SpielerNotizUpdate, spieler: dict = Depends(require_spieler)):
    eintrag = await repository.aendern(
        spieler["id"], spieler["campaignId"], notiz_id, body.model_dump(exclude_unset=True)
    )
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notiz nicht gefunden")
    return eintrag


@router.delete("/{notiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def loeschen(notiz_id: str, spieler: dict = Depends(require_spieler)):
    if not await repository.loeschen(spieler["id"], spieler["campaignId"], notiz_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notiz nicht gefunden")
