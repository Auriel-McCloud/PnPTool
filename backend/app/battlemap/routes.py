"""HTTP- und WebSocket-Routen für die Battlemap."""

import logging
import mimetypes
import uuid

import jwt
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.auth.security import decode_access_token
from app.battlemap import repository
from app.battlemap.logic import darf_zeichnen
from app.battlemap.schemas import (
    BattlemapCreate,
    BattlemapResponse,
    BattlemapUpdate,
    GeloeschtUpdate,
    PfadeUpdate,
)
from app.battlemap.verteiler import Verbindung, verteiler
from app.campaigns.repository import campaign_owned_by
from app.entities.visibility import is_visible_to
from app.items.routes import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/battlemaps",
    tags=["battlemap"],
    dependencies=[Depends(require_campaign_zugang)],
)
ws_router = APIRouter(tags=["battlemap"])


def _sichtbar_oder_404(karte: dict | None, viewer: Viewer) -> dict:
    if karte is not None and is_visible_to(
        karte.get("sichtbarkeit") or "GM", karte.get("sichtbarFuer") or [], viewer.role, viewer.person_id
    ):
        return karte
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Karte nicht gefunden")


@router.get("/papierkorb", response_model=list[BattlemapResponse], dependencies=[Depends(require_campaign_gm)])
async def papierkorb(campaign_id: str):
    return await repository.liste_papierkorb(campaign_id)


@router.get("", response_model=list[BattlemapResponse])
async def liste(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    alle = await repository.liste(campaign_id)
    return [
        z
        for z in alle
        if is_visible_to(z.get("sichtbarkeit") or "GM", z.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]


@router.post("", response_model=BattlemapResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: BattlemapCreate):
    return await repository.erstellen(campaign_id, body.model_dump())


@router.get("/{karte_id}", response_model=BattlemapResponse)
async def holen(campaign_id: str, karte_id: str, viewer: Viewer = Depends(get_viewer)):
    karte = await repository.holen(campaign_id, karte_id)
    return _sichtbar_oder_404(karte, viewer)


@router.patch("/{karte_id}", response_model=BattlemapResponse, dependencies=[Depends(require_campaign_gm)])
async def aktualisieren(campaign_id: str, karte_id: str, body: BattlemapUpdate):
    daten = body.model_dump(exclude_unset=True)
    karte = await repository.aktualisieren(campaign_id, karte_id, daten)
    if karte is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Karte nicht gefunden")
    await verteiler.rundrufen(karte_id, {"typ": "karte", "daten": karte})
    if any(feld.startswith("spawn") for feld in daten):
        from app.battlemap.logic import token_stand
        from app.kampf import repository as kampf_repo

        kampf = await kampf_repo.hole(campaign_id)
        if kampf:
            if not kampf.get("battlemapId"):
                kampf = await kampf_repo.setze_karte(campaign_id, karte_id)
            elif kampf.get("battlemapId") == karte_id:
                await kampf_repo.platziere_unplatzierte(campaign_id)
                kampf = await kampf_repo.hole(campaign_id)
            if kampf:
                await verteiler.rundrufen(karte_id, {"typ": "tokens", "daten": token_stand(kampf)})
    return karte


@router.patch("/{karte_id}/pfade", response_model=BattlemapResponse)
async def pfade_speichern(campaign_id: str, karte_id: str, body: PfadeUpdate, viewer: Viewer = Depends(get_viewer)):
    karte = await repository.holen(campaign_id, karte_id)
    karte = _sichtbar_oder_404(karte, viewer)
    if not darf_zeichnen(karte, viewer.role, viewer.person_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Auf dieser Karte nicht freigegeben")
    aktualisiert = await repository.pfade_speichern(campaign_id, karte_id, body.pfade)
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Karte nicht gefunden")
    return aktualisiert


@router.put("/{karte_id}/geloescht", response_model=BattlemapResponse, dependencies=[Depends(require_campaign_gm)])
async def geloescht_setzen(campaign_id: str, karte_id: str, body: GeloeschtUpdate):
    karte = await repository.setze_geloescht(campaign_id, karte_id, body.geloescht)
    if karte is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Karte nicht gefunden")
    return karte


@router.post("/{karte_id}/bild", response_model=BattlemapResponse, dependencies=[Depends(require_campaign_gm)])
async def bild_hochladen(campaign_id: str, karte_id: str, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")
    inhalt = await file.read()
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    name = f"battlemap-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    karte = await repository.aktualisieren(
        campaign_id, karte_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"}
    )
    if karte is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Karte nicht gefunden")
    await verteiler.rundrufen(karte_id, {"typ": "karte", "daten": karte})
    return karte


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


@ws_router.websocket("/api/campaigns/{campaign_id}/battlemaps/{karte_id}/live")
async def live(websocket: WebSocket, campaign_id: str, karte_id: str):
    viewer = await _viewer_aus_cookie(campaign_id, websocket.cookies.get("pnptool_session"))
    if viewer is None:
        await websocket.close(code=1008, reason="kein Zugang")
        return

    karte = await repository.holen(campaign_id, karte_id)
    if karte is None or not is_visible_to(
        karte.get("sichtbarkeit") or "GM", karte.get("sichtbarFuer") or [], viewer.role, viewer.person_id
    ):
        await websocket.close(code=1008, reason="kein Zugang")
        return

    await websocket.accept()
    verbindung = Verbindung(socket=websocket, rolle=viewer.role, person_id=viewer.person_id)
    await verteiler.anmelden(karte_id, verbindung)

    try:
        while True:
            nachricht = await websocket.receive_json()
            pfade = nachricht.get("pfade")
            if not isinstance(pfade, list):
                continue
            aktuell = await repository.holen(campaign_id, karte_id)
            if aktuell is None or not darf_zeichnen(aktuell, viewer.role, viewer.person_id):
                continue
            await repository.pfade_speichern(campaign_id, karte_id, pfade)
            await verteiler.rundrufen(karte_id, {"typ": "pfade", "daten": {"pfade": pfade}}, ausser=websocket)
    except WebSocketDisconnect:
        pass
    except Exception:
        log.debug("WebSocket unerwartet beendet", exc_info=True)
    finally:
        await verteiler.abmelden(karte_id, websocket)
