from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.begleiter import repository
from app.begleiter.schemas import (
    BegleiterCreate,
    BegleiterResponse,
    BegleiterUpdate,
    BesitzerRequest,
)
from app.entities.visibility import is_visible_to, redact_rich_text

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/begleiter",
    tags=["begleiter"],
    dependencies=[Depends(require_campaign_zugang)],
)


def _fuer_viewer(begleiter: dict, viewer: Viewer) -> dict | None:
    """Filtert wie bei Entitäten — mit einer Ergänzung.

    Wer einen Begleiter besitzt, sieht ihn immer. Sonst müsste die
    Spielleitung bei jedem Sprite daran denken, ihn für seinen eigenen
    Technomancer freizugeben — und vergisst sie es, steht der Spieler ohne
    sein Sprite da. Gleiches Muster wie bei den Gegenständen.
    """
    if viewer.role == "GM" or begleiter.get("besitzerId") == viewer.person_id:
        sichtbar = True
    else:
        sichtbar = is_visible_to(
            begleiter.get("sichtbarkeit") or "GM",
            begleiter.get("sichtbarFuer") or [],
            viewer.role,
            viewer.person_id,
        )
    if not sichtbar:
        return None

    gefiltert = dict(begleiter)
    gefiltert["beschreibung"] = redact_rich_text(gefiltert.get("beschreibung", ""), viewer.role)
    # Notizen sind Sache der Spielleitung — es gibt dafür keine eigene
    # Freigabestufe, deshalb ganz zurückhalten statt halb zu redigieren
    # (gleiche Entscheidung wie bei den Gegenstandsnotizen).
    if viewer.role != "GM":
        gefiltert["notizen"] = ""
    return gefiltert


@router.get("", response_model=list[BegleiterResponse])
async def alle(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    roh = await repository.liste(campaign_id)
    gefiltert = (_fuer_viewer(b, viewer) for b in roh)
    return [b for b in gefiltert if b is not None]


@router.post("", response_model=BegleiterResponse, dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: BegleiterCreate):
    daten = body.model_dump()
    besitzer = daten.pop("besitzerId")
    # Gehört er einem Spielercharakter, soll dieser ihn auch sehen — ohne
    # dass jemand daran denken muss.
    if besitzer and daten["sichtbarkeit"] == "GM" and not daten["sichtbarFuer"]:
        daten["sichtbarkeit"] = "SPEZIFISCH"
        daten["sichtbarFuer"] = [besitzer]
    ergebnis = await repository.anlegen(campaign_id, besitzer, daten)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne oder Person nicht gefunden")
    return ergebnis


@router.patch("/{begleiter_id}", response_model=BegleiterResponse, dependencies=[Depends(require_campaign_gm)])
async def aendern(campaign_id: str, begleiter_id: str, body: BegleiterUpdate):
    ergebnis = await repository.aendern(campaign_id, begleiter_id, body.model_dump())
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Begleiter nicht gefunden")
    return ergebnis


@router.post("/{begleiter_id}/besitzer", response_model=BegleiterResponse, dependencies=[Depends(require_campaign_gm)])
async def besitzer_setzen(campaign_id: str, begleiter_id: str, body: BesitzerRequest):
    ergebnis = await repository.besitzer_setzen(campaign_id, begleiter_id, body.personId)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Begleiter nicht gefunden")
    return ergebnis


@router.delete("/{begleiter_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def loeschen(campaign_id: str, begleiter_id: str):
    if not await repository.loeschen(campaign_id, begleiter_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Begleiter nicht gefunden")
