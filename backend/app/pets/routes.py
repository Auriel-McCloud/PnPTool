"""Routen der Critter-Pets.

SL: legt am Critter — oder an einem Gegenstand (Bärbel, 11.11.2026) — fest,
ob und als was er herumläuft (`petArt`). `{critter_id}` ist dann die
Gegenstands-id.
Spieler: eine Live-Leitung, über die das Pet kommt und geht.
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.mitteilungen.routes import _viewer_aus_cookie
from app.pets import repository
from app.pets.logic import PET_ARTEN
from app.pets.motor import motor

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/pets",
    tags=["pets"],
    dependencies=[Depends(require_campaign_zugang)],
)
ws_router = APIRouter(tags=["pets"])


class PetArt(BaseModel):
    # None = läuft nicht herum.
    art: Literal[PET_ARTEN] | None = None  # type: ignore[valid-type]


class PetArtAntwort(BaseModel):
    id: str
    art: str | None = None


@router.get("/{critter_id}", response_model=PetArtAntwort, dependencies=[Depends(require_campaign_gm)])
async def art_lesen(campaign_id: str, critter_id: str):
    d = await repository.art_lesen(campaign_id, critter_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Critter oder Gegenstand nicht gefunden")
    return d


@router.put("/{critter_id}", response_model=PetArtAntwort, dependencies=[Depends(require_campaign_gm)])
async def art_setzen(campaign_id: str, critter_id: str, body: PetArt):
    d = await repository.art_setzen(campaign_id, critter_id, body.art)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Critter oder Gegenstand nicht gefunden")
    # Sofort sichtbar machen, nicht erst im nächsten Takt.
    await motor.abgleich(campaign_id)
    return d


@router.post("/fuettern/{item_id}")
async def fuettern(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)) -> dict:
    """Tierfutter verfüttern (Mark, 12.11.2026): ein Stück vom eigenen Futter,
    dafür steht ein Napf unten auf dem eigenen Bildschirm, bis ein Drache ihn
    leer frisst. Nur Spieler — die SL hat keine Pets auf dem Schirm. Prüft
    den Besitz selbst (Ausnahmeliste in tests/test_zugriffsschutz.py)."""
    if viewer.role != "PLAYER" or not viewer.person_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Füttern geht nur am eigenen Spieler-Tablet.")
    fehler = await repository.napf_futter_verbrauchen(campaign_id, viewer.person_id, item_id)
    if fehler:
        raise HTTPException(status.HTTP_404_NOT_FOUND, fehler)
    await motor.napf_hinstellen(campaign_id, viewer.person_id)
    return {"text": "Der Napf steht auf deinem Bildschirm — jetzt muss nur noch ein Drache vorbeikommen."}


@ws_router.websocket("/api/campaigns/{campaign_id}/pets/live")
async def live(websocket: WebSocket, campaign_id: str):
    """Live-Leitung eines Spieler-Tablets. Die SL bekommt keine Pets (Mark, 11.11.2026)."""
    viewer = await _viewer_aus_cookie(campaign_id, websocket.cookies.get("pnptool_session"))
    if viewer is None or viewer.role != "PLAYER" or not viewer.person_id:
        await websocket.close(code=1008, reason="kein Zugang")
        return

    await websocket.accept()
    person_id = viewer.person_id
    await motor.anmelden(campaign_id, person_id, websocket)
    try:
        while True:
            n = await websocket.receive_json()
            if not isinstance(n, dict):
                continue
            typ = n.get("typ")
            try:
                if typ == "raus":
                    await motor.raus(campaign_id, person_id, str(n.get("petId")), str(n.get("seite")))
                elif typ == "haeufchen":
                    await motor.haeufchen(campaign_id, person_id, str(n.get("petId")),
                                          float(n.get("x", 0)), float(n.get("y", 1)),
                                          str(n.get("art") or "haeufchen"))
                elif typ == "wegmachen":
                    await motor.wegmachen(campaign_id, person_id, str(n.get("id")),
                                          str(n.get("petId")) if n.get("petId") else None)
                elif typ == "streicheln":
                    await motor.streicheln(campaign_id, person_id, str(n.get("petId")))
                elif typ == "verschieben":
                    await motor.verschieben(campaign_id, person_id, str(n.get("id")),
                                            float(n.get("x", 0)), float(n.get("y", 1)))
                elif typ == "gelesen":
                    await motor.gelesen(campaign_id, person_id, str(n.get("petId")))
                elif typ == "tippen":
                    await motor.tippen(campaign_id, person_id, str(n.get("petId")))
            except (TypeError, ValueError):
                continue
    except WebSocketDisconnect:
        pass
    except Exception:
        log.debug("Pet-Leitung unerwartet beendet", exc_info=True)
    finally:
        await motor.abmelden(campaign_id, person_id, websocket)
