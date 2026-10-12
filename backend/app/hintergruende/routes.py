"""Narrativer Hintergrund-Katalog: SL-CRUD, Spieler dürfen lesen."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen, set_einstellungen
from app.hintergruende import repository
from app.hintergruende.schemas import HintergrundCreate, HintergrundResponse, HintergrundUpdate
from app.hintergruende.seed import SYSTEM_HINTERGRUENDE

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


@router.get("/system")
async def system_liste(campaign_id: str) -> list[dict]:
    """Mentor/Kontakte/Schulden: Mechanik statt Katalogzeile, aber sichtbar
    und je Kampagne abschaltbar (siehe seed.py::SYSTEM_HINTERGRUENDE)."""
    einstellungen = await get_einstellungen(campaign_id)
    return [
        {
            "schluessel": eintrag["schluessel"],
            "name": eintrag["name"],
            "beschreibung": eintrag["beschreibung"],
            "aktiv": bool(einstellungen.get(eintrag["einstellung"], True)),
        }
        for eintrag in SYSTEM_HINTERGRUENDE
    ]


@router.patch("/system/{schluessel}", dependencies=[Depends(require_campaign_gm)])
async def system_umschalten(campaign_id: str, schluessel: str, body: dict) -> dict:
    """Schaltet einen Mechanik-Hintergrund für diese Kampagne an/aus."""
    eintrag = next((e for e in SYSTEM_HINTERGRUENDE if e["schluessel"] == schluessel), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unbekannter System-Hintergrund")
    aktiv = bool(body.get("aktiv", True))
    await set_einstellungen(campaign_id, {eintrag["einstellung"]: aktiv})
    return {
        "schluessel": schluessel,
        "name": eintrag["name"],
        "beschreibung": eintrag["beschreibung"],
        "aktiv": aktiv,
    }
