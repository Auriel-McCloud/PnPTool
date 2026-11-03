"""Ring-Rätsel: die SL klickt, Spieler sehen nur zu, und nur nach Freigabe."""

import asyncio
import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.auth.security import decode_access_token
from app.campaigns.repository import campaign_owned_by
from app.raetsel import repository
from app.raetsel.logic import (
    freigabe_setzen,
    fuer_draht,
    gruppe_setzen,
    name_setzen,
    tuer_zu,
    zurueck,
    zuruecksetzen,
)
from app.raetsel.schemas import FreigabeAktion, GruppeAktion, NameAktion, TuerAktion
from app.raetsel.verteiler import Verbindung, verteiler

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/raetsel",
    tags=["raetsel"],
    dependencies=[Depends(require_campaign_zugang)],
)
ws_router = APIRouter(tags=["raetsel"])

# Zwei Klicks hintereinander dürfen sich die Drehung nicht wegoptimieren.
_schloesser: dict[str, asyncio.Lock] = {}


def _schloss(campaign_id: str) -> asyncio.Lock:
    schloss = _schloesser.get(campaign_id)
    if schloss is None:
        schloss = asyncio.Lock()
        _schloesser[campaign_id] = schloss
    return schloss


async def _aendern(campaign_id: str, fn):
    async with _schloss(campaign_id):
        stand = await repository.laden(campaign_id)
        if stand is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
        try:
            neu = fn(stand)
        except ValueError as fehler:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler)) from fehler
        gespeichert = await repository.speichern(campaign_id, neu)
        if gespeichert is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
        await verteiler.rundrufen(campaign_id, gespeichert)
        return fuer_draht(gespeichert, "GM")


@router.get("")
async def stand(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    roh = await repository.laden(campaign_id)
    if roh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return fuer_draht(roh, viewer.role)


@router.post("/tuer", dependencies=[Depends(require_campaign_gm)])
async def tuer(campaign_id: str, body: TuerAktion):
    return await _aendern(campaign_id, lambda z: tuer_zu(z, body.raum, body.seite))


@router.post("/gruppe", dependencies=[Depends(require_campaign_gm)])
async def gruppe(campaign_id: str, body: GruppeAktion):
    return await _aendern(campaign_id, lambda z: gruppe_setzen(z, body.index, body.raum))


@router.post("/name", dependencies=[Depends(require_campaign_gm)])
async def name(campaign_id: str, body: NameAktion):
    return await _aendern(campaign_id, lambda z: name_setzen(z, body.raum, body.name))


@router.post("/freigabe", dependencies=[Depends(require_campaign_gm)])
async def freigabe(campaign_id: str, body: FreigabeAktion):
    return await _aendern(campaign_id, lambda z: freigabe_setzen(z, body.an))


@router.post("/zurueck", dependencies=[Depends(require_campaign_gm)])
async def schritt_zurueck(campaign_id: str):
    return await _aendern(campaign_id, zurueck)


@router.post("/zuruecksetzen", dependencies=[Depends(require_campaign_gm)])
async def neu_aufstellen(campaign_id: str):
    return await _aendern(campaign_id, zuruecksetzen)


async def _viewer_aus_cookie(campaign_id: str, cookie: str | None) -> Viewer | None:
    if not cookie:
        return None
    try:
        claims = decode_access_token(cookie)
    except jwt.PyJWTError:
        return None
    rolle = claims.get("role")
    if rolle == "GM":
        if not await campaign_owned_by(campaign_id, claims["sub"]):
            return None
        return Viewer(role="GM")
    if rolle == "PLAYER":
        from app.players.repository import get_spieler

        spieler = await get_spieler(claims["sub"])
        if spieler is None or spieler["campaignId"] != campaign_id:
            return None
        return Viewer(role="PLAYER", person_id=spieler["personId"])
    return None


@ws_router.websocket("/api/campaigns/{campaign_id}/raetsel/live")
async def live(websocket: WebSocket, campaign_id: str):
    viewer = await _viewer_aus_cookie(campaign_id, websocket.cookies.get("pnptool_session"))
    if viewer is None:
        await websocket.close(code=1008, reason="kein Zugang")
        return
    stand_jetzt = await repository.laden(campaign_id)
    if stand_jetzt is None:
        await websocket.close(code=1008, reason="kein Zugang")
        return
    await websocket.accept()
    await verteiler.anmelden(campaign_id, Verbindung(socket=websocket, rolle=viewer.role))
    try:
        await websocket.send_json({"typ": "stand", "daten": fuer_draht(stand_jetzt, viewer.role)})
        while True:
            # Spieler dürfen nichts schicken, was den Ring dreht. Die Schleife
            # hält die Leitung nur offen, damit ein Abbruch auffällt.
            await websocket.receive_json()
    except WebSocketDisconnect:
        pass
    except Exception:
        log.debug("WebSocket unerwartet beendet", exc_info=True)
    finally:
        await verteiler.abmelden(campaign_id, websocket)
