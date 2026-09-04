"""HTTP- und WebSocket-Routen der SL-Mitteilungen.

Senden ist Sache der Spielleitung, Lesen darf jeder mit Kampagnenzugang.
Der strukturelle Test in tests/test_zugriffsschutz.py prüft das automatisch.
"""

import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.auth.security import decode_access_token
from app.campaigns.repository import campaign_owned_by
from app.entities.repository import PERSON_FIELDS, list_nodes
from app.mitteilungen import repository
from app.mitteilungen.logic import empfaenger_aufloesen, fuer_viewer, zaehle_ungelesen
from app.mitteilungen.schemas import (
    MitteilungCreate,
    MitteilungenAntwort,
    MitteilungResponse,
    SendeAntwort,
)
from app.mitteilungen.verteiler import Verbindung, verteiler

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/mitteilungen",
    tags=["mitteilungen"],
    dependencies=[Depends(require_campaign_zugang)],
)

# Der WebSocket hängt bewusst NICHT am Router mit require_campaign_zugang:
# Diese Abhängigkeit wirft HTTPException, und ein WebSocket kann darauf nicht
# antworten — der Client sähe nur einen wortlosen Abbruch. Die Prüfung
# passiert deshalb von Hand, mit sauberem Schliessgrund.
ws_router = APIRouter(tags=["mitteilungen"])


async def _alle_pc_ids(campaign_id: str) -> list[str]:
    personen = await list_nodes("Person", PERSON_FIELDS, campaign_id)
    return [p["id"] for p in personen if p.get("personType") == "PC"]


@router.get("", response_model=MitteilungenAntwort)
async def liste(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Was dieser Betrachter sehen darf, neueste zuerst."""
    alle = await repository.list_mitteilungen(campaign_id)
    sichtbar = fuer_viewer(alle, viewer.role, viewer.person_id)
    return {
        "mitteilungen": sichtbar,
        "ungelesen": zaehle_ungelesen(alle, viewer.role, viewer.person_id),
    }


@router.post("", response_model=SendeAntwort, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_campaign_gm)])
async def senden(campaign_id: str, body: MitteilungCreate):
    """Popup an alle oder an ausgewählte Charaktere.

    Erst speichern, dann verteilen: Wessen Gerät gerade schläft, soll die
    Ansage nachlesen können statt sie zu verpassen.
    """
    empfaenger = empfaenger_aufloesen(body.anAlle, body.empfaengerIds, await _alle_pc_ids(campaign_id))
    if not body.anAlle and not empfaenger:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein gültiger Empfänger")

    mitteilung = await repository.create_mitteilung(
        campaign_id,
        art=body.art,
        inhalt=body.inhalt,
        an_alle=body.anAlle,
        empfaenger_ids=empfaenger,
        bild_url=body.bildUrl,
        farbe=body.farbe,
    )
    zugestellt = await verteiler.verteilen(campaign_id, mitteilung)
    return {"mitteilung": mitteilung, "zugestellt": zugestellt}


@router.post("/{mitteilung_id}/gelesen", status_code=status.HTTP_204_NO_CONTENT)
async def gelesen(campaign_id: str, mitteilung_id: str, viewer: Viewer = Depends(get_viewer)):
    """Abhaken. Gilt pro Person, nicht global."""
    if viewer.person_id is None:
        # Die Spielleitung hat nichts abzuhaken — sie hat es geschrieben.
        return
    await repository.als_gelesen(campaign_id, mitteilung_id, viewer.person_id)


@router.post("/gelesen", status_code=status.HTTP_204_NO_CONTENT)
async def alles_gelesen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    if viewer.person_id is None:
        return
    await repository.alles_gelesen(campaign_id, viewer.person_id)


@router.delete("/{mitteilung_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_campaign_gm)])
async def zurueckziehen(campaign_id: str, mitteilung_id: str):
    """Ein versehentlich gesendetes Popup wieder einsammeln.

    Verschwindet auch auf bereits offenen Bildschirmen.
    """
    if not await repository.delete_mitteilung(campaign_id, mitteilung_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mitteilung nicht gefunden")
    await verteiler.zurueckziehen(campaign_id, mitteilung_id)


async def _viewer_aus_cookie(campaign_id: str, cookie: str | None) -> Viewer | None:
    """Blickwinkel für eine WebSocket-Verbindung aus dem Sitzungs-Cookie.

    Bewusst eigener Weg statt der HTTP-Abhängigkeit: Die wirft
    HTTPException, worauf ein WebSocket nicht antworten kann.
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


@ws_router.websocket("/api/campaigns/{campaign_id}/mitteilungen/live")
async def live(websocket: WebSocket, campaign_id: str):
    """Live-Leitung für Popups.

    Nach dem Verbinden kommt einmal der aktuelle Stand (was der Betrachter
    sehen darf und wie viel davon ungelesen ist), danach jede neue Mitteilung
    einzeln.
    """
    viewer = await _viewer_aus_cookie(campaign_id, websocket.cookies.get("pnptool_session"))
    if viewer is None:
        # 1008 = policy violation. Ein Ablehnen VOR accept() käme beim Client
        # nur als anonymer Verbindungsfehler an.
        await websocket.close(code=1008, reason="kein Zugang")
        return

    await websocket.accept()
    verbindung = Verbindung(socket=websocket, rolle=viewer.role, person_id=viewer.person_id)
    await verteiler.anmelden(campaign_id, verbindung)

    try:
        alle = await repository.list_mitteilungen(campaign_id)
        await websocket.send_json(
            {
                "typ": "stand",
                "daten": {
                    "mitteilungen": fuer_viewer(alle, viewer.role, viewer.person_id),
                    "ungelesen": zaehle_ungelesen(alle, viewer.role, viewer.person_id),
                },
            }
        )

        # Die Leitung offen halten. Der Client schickt nichts Fachliches —
        # empfangen wird trotzdem, weil erst dadurch ein Verbindungsabbruch
        # bemerkt wird.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        log.debug("WebSocket unerwartet beendet", exc_info=True)
    finally:
        await verteiler.abmelden(campaign_id, websocket)
