from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.dependencies import get_current_claims, require_campaign_gm
from app.auth.security import create_access_token
from app.players import repository
from app.players.schemas import (
    BeitrittRequest,
    CharakterWahlRequest,
    FreierCharakter,
    SitzungResponse,
    SpielerMeResponse,
    ZugangscodeResponse,
)

# Beitritt läuft ohne Anmeldung — der Code ist der Nachweis.
beitritt_router = APIRouter(prefix="/api/beitritt", tags=["players"])
# Alles Weitere setzt eine Spieler-Sitzung voraus.
spieler_router = APIRouter(prefix="/api/spieler", tags=["players"])
# Verwaltung durch den Spielleiter.
gm_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/zugang",
    tags=["players"],
    dependencies=[Depends(require_campaign_gm)],
)

SESSION_COOKIE = "pnptool_session"


async def require_player(claims: dict = Depends(get_current_claims)) -> dict:
    """Sitzungsdaten des angemeldeten Spielers.

    Wirft 401 statt 403, wenn die Sitzung nicht mehr existiert: für den
    Aufrufer ist das gleichbedeutend mit "nicht angemeldet", und er soll sich
    neu verbinden statt es erneut zu versuchen.
    """
    if claims.get("role") != "PLAYER":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "player role required")
    sitzung = await repository.get_session(claims["sub"])
    if sitzung is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session no longer exists")
    return sitzung


@beitritt_router.post("", response_model=SpielerMeResponse)
async def beitreten(body: BeitrittRequest, response: Response):
    kampagne = await repository.finde_kampagne_zu_code(body.code.strip())
    if kampagne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zugangscode ungültig")

    sitzung = await repository.create_session(kampagne["id"], body.name.strip())
    token = create_access_token({"role": "PLAYER", "sub": sitzung["id"], "name": sitzung["name"]})
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return SpielerMeResponse(
        sessionId=sitzung["id"],
        name=sitzung["name"],
        campaignId=kampagne["id"],
        campaignName=kampagne["name"],
    )


@spieler_router.get("/me", response_model=SpielerMeResponse)
async def spieler_me(sitzung: dict = Depends(require_player)):
    return SpielerMeResponse(
        sessionId=sitzung["id"],
        name=sitzung["name"],
        campaignId=sitzung["campaignId"],
        campaignName=sitzung["campaignName"],
        personId=sitzung["personId"],
        personName=sitzung["personName"],
    )


@spieler_router.get("/charaktere", response_model=list[FreierCharakter])
async def waehlbare_charaktere(sitzung: dict = Depends(require_player)):
    return await repository.freie_charaktere(sitzung["campaignId"])


@spieler_router.post("/charakter", response_model=SpielerMeResponse)
async def charakter_beanspruchen(body: CharakterWahlRequest, sitzung: dict = Depends(require_player)):
    if not await repository.claim_charakter(sitzung["id"], body.personId):
        # Entweder schon vergeben oder gar kein Spielercharakter dieser
        # Kampagne — beides ist für den Aufrufer dieselbe Sackgasse.
        raise HTTPException(status.HTTP_409_CONFLICT, "Charakter nicht verfügbar")
    frisch = await repository.get_session(sitzung["id"])
    assert frisch is not None
    return SpielerMeResponse(
        sessionId=frisch["id"],
        name=frisch["name"],
        campaignId=frisch["campaignId"],
        campaignName=frisch["campaignName"],
        personId=frisch["personId"],
        personName=frisch["personName"],
    )


@spieler_router.post("/abmelden")
async def spieler_abmelden(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@gm_router.get("/code", response_model=ZugangscodeResponse)
async def code_lesen(campaign_id: str):
    return ZugangscodeResponse(code=await repository.get_zugangscode(campaign_id))


@gm_router.post("/code", response_model=ZugangscodeResponse)
async def code_erzeugen(campaign_id: str):
    """Erzeugt einen neuen Code. Ein bereits vergebener wird damit ungültig.

    Bestehende Sitzungen bleiben bestehen — der Code regelt nur den Beitritt,
    nicht den weiteren Zugang. Wer draußen bleiben soll, wird über
    DELETE .../sitzungen/{id} entfernt.
    """
    code = repository.erzeuge_code()
    await repository.set_zugangscode(campaign_id, code)
    return ZugangscodeResponse(code=code)


@gm_router.delete("/code", response_model=ZugangscodeResponse)
async def code_entfernen(campaign_id: str):
    """Schließt den Beitritt. Bestehende Sitzungen bleiben gültig."""
    await repository.set_zugangscode(campaign_id, None)
    return ZugangscodeResponse(code=None)


@gm_router.get("/sitzungen", response_model=list[SitzungResponse])
async def sitzungen(campaign_id: str):
    return await repository.list_sessions(campaign_id)


@gm_router.delete("/sitzungen/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def sitzung_entfernen(campaign_id: str, session_id: str):
    if not await repository.delete_session(campaign_id, session_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sitzung nicht gefunden")
