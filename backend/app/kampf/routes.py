from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.kampf import repository
from app.kampf.sichtbarkeit import fuer_spieler

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/kampf",
    tags=["kampf"],
    dependencies=[Depends(require_campaign_zugang)],
)

Kampfart = str  # MATRIX | NAHKAMPF | FERNKAMPF — bewusst offen, siehe unten


def _ohne_hilfsfelder(kampf: dict | None) -> dict | None:
    """Entfernt die nur zur Filterung mitgelieferten Felder.

    Schreibrouten sind der Spielleitung vorbehalten, dort ist nichts zu
    verbergen — die Felder gehören aber trotzdem nicht in die Antwort.
    """
    if kampf is None:
        return None
    for feld in ("_rassen", "_npcIds", "_begleiterBesitzer"):
        kampf.pop(feld, None)
    return kampf


class TeilnehmerResponse(BaseModel):
    id: str
    name: str
    initiative: int
    # Entscheidet die Reihenfolge bei Gleichstand (Zeile 58). Kein Enum, damit
    # sich weitere Arten ergänzen lassen, ohne das Schema anzufassen.
    kampfart: str
    notiz: str
    erledigt: bool
    personId: str | None = None
    personType: str | None = None
    begleiterId: str | None = None


class KampfResponse(BaseModel):
    id: str
    runde: int
    amZug: str | None = None
    teilnehmer: list[TeilnehmerResponse]


class TeilnehmerInput(BaseModel):
    name: str
    initiative: int = Field(default=0, ge=0)
    kampfart: str = "NAHKAMPF"
    notiz: str = ""
    personId: str | None = None
    begleiterId: str | None = None


class TeilnehmerUpdate(BaseModel):
    name: str | None = None
    initiative: int | None = Field(default=None, ge=0)
    kampfart: str | None = None
    notiz: str | None = None
    erledigt: bool | None = None


class AmZugInput(BaseModel):
    teilnehmerId: str | None = None


@router.get("", response_model=KampfResponse | None)
async def laufender_kampf(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Die Initiativliste.

    **Für alle mit Zugang lesbar** — das ist der Sinn der Sache: jeder am Tisch
    soll sehen, wann er dran ist, ohne fragen zu müssen.

    **Aber:** Spieler sehen NPCs nur unter Alias. Mark: *"die Spieler dürfen
    nur die Alias Namen der NPCs sehen nicht ihre richtigen Namen!"* Gefiltert
    wird hier serverseitig, nicht im Browser — im Netzwerkverkehr stünde der
    echte Name sonst trotzdem.
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        return None

    rassen = kampf.pop("_rassen", {})
    npc_ids = kampf.pop("_npcIds", set())
    begleiter_besitzer = kampf.pop("_begleiterBesitzer", {})

    if viewer.role != "GM":
        kampf["teilnehmer"] = fuer_spieler(
            kampf["teilnehmer"],
            rassen=rassen,
            eigene_person_id=viewer.person_id,
            begleiter_besitzer=begleiter_besitzer,
            npc_ids=npc_ids,
        )
    return kampf


@router.post("", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def beginne(campaign_id: str):
    return _ohne_hilfsfelder(await repository.beginne(campaign_id))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def beende(campaign_id: str):
    await repository.beende(campaign_id)


@router.post("/teilnehmer", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_hinzu(campaign_id: str, body: TeilnehmerInput):
    kampf = await repository.teilnehmer_hinzu(campaign_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.patch("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_aendern(campaign_id: str, teilnehmer_id: str, body: TeilnehmerUpdate):
    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.delete("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_entfernen(campaign_id: str, teilnehmer_id: str):
    kampf = await repository.teilnehmer_entfernen(campaign_id, teilnehmer_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.post("/weiter", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def weiter(campaign_id: str):
    """Einen Zug weiter. Am Ende der Liste beginnt die nächste Runde."""
    kampf = await repository.weiter(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.post("/amzug", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def am_zug(campaign_id: str, body: AmZugInput):
    """Direkt jemanden ans Ruder setzen — für den Fall, dass es durcheinander ging."""
    kampf = await repository.setze_am_zug(campaign_id, body.teilnehmerId)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)
