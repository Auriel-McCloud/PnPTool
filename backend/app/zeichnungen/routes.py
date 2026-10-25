"""HTTP- und WebSocket-Routen fürs gemeinsame Whiteboard.

Board-Verwaltung (anlegen/umbenennen/Hintergrund/Sichtbarkeit/Spieler-
Freigabe/Papierkorb) ist Sache der Spielleitung. Lesen und — falls das Board
es erlaubt — Mitzeichnen darf jeder mit Kampagnenzugang. Der strukturelle
Test in tests/test_zugriffsschutz.py prüft die GM-Pflicht für alles andere
automatisch; `/pfade` steht deshalb bewusst in OHNE_GM_ERLAUBT.
"""

import logging
import mimetypes
import uuid
from pathlib import Path

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
from app.campaigns.repository import campaign_owned_by
from app.entities.visibility import is_visible_to
from app.items.routes import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.zeichnungen import repository
from app.zeichnungen.logic import darf_zeichnen
from app.zeichnungen.schemas import (
    GeloeschtUpdate,
    PfadeUpdate,
    ZeichnungCreate,
    ZeichnungResponse,
    ZeichnungUpdate,
)
from app.zeichnungen.verteiler import Verbindung, verteiler

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/zeichnungen",
    tags=["zeichnungen"],
    dependencies=[Depends(require_campaign_zugang)],
)
ws_router = APIRouter(tags=["zeichnungen"])


def _sichtbar_oder_404(zeichnung: dict | None, viewer: Viewer) -> dict:
    if zeichnung is not None and is_visible_to(
        zeichnung.get("sichtbarkeit") or "GM", zeichnung.get("sichtbarFuer") or [], viewer.role, viewer.person_id
    ):
        return zeichnung
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Zeichnung nicht gefunden")


# Vor /{zeichnung_id} registriert — sonst würde FastAPI "papierkorb" als
# zeichnung_id matchen (Registrierungsreihenfolge, nicht Spezifität).
@router.get("/papierkorb", response_model=list[ZeichnungResponse], dependencies=[Depends(require_campaign_gm)])
async def papierkorb(campaign_id: str):
    """Gelöschte Boards — nur die Spielleitung soll wissen, was noch rückholbar ist."""
    return await repository.liste_papierkorb(campaign_id)


@router.get("", response_model=list[ZeichnungResponse])
async def liste(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    alle = await repository.liste(campaign_id)
    return [
        z
        for z in alle
        if is_visible_to(z.get("sichtbarkeit") or "GM", z.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]


@router.post("", response_model=ZeichnungResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: ZeichnungCreate):
    return await repository.erstellen(campaign_id, body.model_dump())


@router.get("/{zeichnung_id}", response_model=ZeichnungResponse)
async def holen(campaign_id: str, zeichnung_id: str, viewer: Viewer = Depends(get_viewer)):
    zeichnung = await repository.holen(campaign_id, zeichnung_id)
    return _sichtbar_oder_404(zeichnung, viewer)


@router.patch("/{zeichnung_id}", response_model=ZeichnungResponse, dependencies=[Depends(require_campaign_gm)])
async def aktualisieren(campaign_id: str, zeichnung_id: str, body: ZeichnungUpdate):
    zeichnung = await repository.aktualisieren(campaign_id, zeichnung_id, body.model_dump())
    if zeichnung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zeichnung nicht gefunden")
    return zeichnung


@router.patch("/{zeichnung_id}/pfade", response_model=ZeichnungResponse)
async def pfade_speichern(campaign_id: str, zeichnung_id: str, body: PfadeUpdate, viewer: Viewer = Depends(get_viewer)):
    """Persistiert den aktuellen Gesamtstand. Wer zeichnen darf, darf auch
    speichern — dieselbe Prüfung wie für die Live-Leitung (logic.darf_zeichnen).
    404 statt 403 bei fehlender Sicht: ein Spieler soll nicht erfahren, ob es
    das Board überhaupt gibt."""
    zeichnung = await repository.holen(campaign_id, zeichnung_id)
    zeichnung = _sichtbar_oder_404(zeichnung, viewer)
    if not darf_zeichnen(zeichnung, viewer.role, viewer.person_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Auf diesem Board nicht freigegeben")
    aktualisiert = await repository.pfade_speichern(campaign_id, zeichnung_id, body.pfade)
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zeichnung nicht gefunden")
    return aktualisiert


@router.put("/{zeichnung_id}/geloescht", response_model=ZeichnungResponse, dependencies=[Depends(require_campaign_gm)])
async def geloescht_setzen(campaign_id: str, zeichnung_id: str, body: GeloeschtUpdate):
    """Papierkorb-Prinzip wie überall sonst — kein Hard-Delete."""
    zeichnung = await repository.setze_geloescht(campaign_id, zeichnung_id, body.geloescht)
    if zeichnung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zeichnung nicht gefunden")
    return zeichnung


@router.post("/{zeichnung_id}/bild", response_model=ZeichnungResponse, dependencies=[Depends(require_campaign_gm)])
async def bild_hochladen(campaign_id: str, zeichnung_id: str, file: UploadFile = File(...)):
    """Optionales Hintergrundbild (z.B. eine Karte, über die gezeichnet wird)."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")
    inhalt = await file.read()
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    name = f"zeichnung-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    zeichnung = await repository.aktualisieren(
        campaign_id, zeichnung_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"}
    )
    if zeichnung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zeichnung nicht gefunden")
    return zeichnung


async def _viewer_aus_cookie(campaign_id: str, cookie: str | None) -> Viewer | None:
    """Blickwinkel für eine WebSocket-Verbindung aus dem Sitzungs-Cookie.

    Eigener Weg statt der HTTP-Abhängigkeit: die wirft HTTPException, worauf
    ein WebSocket nicht antworten kann (dasselbe Muster wie bei den
    Mitteilungen, app/mitteilungen/routes.py::_viewer_aus_cookie).
    """
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


@ws_router.websocket("/api/campaigns/{campaign_id}/zeichnungen/{zeichnung_id}/live")
async def live(websocket: WebSocket, campaign_id: str, zeichnung_id: str):
    """Live-Leitung für ein einzelnes Board.

    Der Client lädt den aktuellen Stand vorher per GET — hier kommen nur
    noch NEUE Striche/Änderungen rein, jede als kompletter Gesamtstand
    (kein inkrementelles Protokoll, siehe verteiler.py). Wer nicht zeichnen
    darf, bleibt trotzdem verbunden und sieht live zu; seine gesendeten
    Nachrichten werden nur ignoriert, nicht mit einem Fehler beantwortet —
    ein veralteter/manipulierter Client soll nicht die Leitung für alle
    anderen kappen.
    """
    viewer = await _viewer_aus_cookie(campaign_id, websocket.cookies.get("pnptool_session"))
    if viewer is None:
        await websocket.close(code=1008, reason="kein Zugang")
        return

    zeichnung = await repository.holen(campaign_id, zeichnung_id)
    if zeichnung is None or not is_visible_to(
        zeichnung.get("sichtbarkeit") or "GM", zeichnung.get("sichtbarFuer") or [], viewer.role, viewer.person_id
    ):
        await websocket.close(code=1008, reason="kein Zugang")
        return

    await websocket.accept()
    verbindung = Verbindung(socket=websocket, rolle=viewer.role, person_id=viewer.person_id)
    await verteiler.anmelden(zeichnung_id, verbindung)

    try:
        while True:
            nachricht = await websocket.receive_json()
            pfade = nachricht.get("pfade")
            if not isinstance(pfade, list):
                continue
            # Stand neu holen statt den eingangs geladenen zu cachen — eine
            # SL kann die Freigabe mitten in der Sitzung umschalten.
            aktuell = await repository.holen(campaign_id, zeichnung_id)
            if aktuell is None or not darf_zeichnen(aktuell, viewer.role, viewer.person_id):
                continue
            await repository.pfade_speichern(campaign_id, zeichnung_id, pfade)
            await verteiler.rundrufen(zeichnung_id, pfade, ausser=websocket)
    except WebSocketDisconnect:
        pass
    except Exception:
        log.debug("WebSocket unerwartet beendet", exc_info=True)
    finally:
        await verteiler.abmelden(zeichnung_id, websocket)
