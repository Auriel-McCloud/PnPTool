"""Spotify-Anbindung: OAuth-Login, Konto-Status, Playlist-Suche/Wiedergabe.

Global (ein Konto fürs ganze Tool, siehe repository.py) — deshalb zwei
Router: einer ohne Kampagnen-Präfix für die Kontoverbindung selbst (nur die
Spielleitung darf sie herstellen/lösen), einer mit Kampagnen-Präfix für
Playlist-Suche und -Wiedergabe (an Orte/Events gebunden).
"""

import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth.dependencies import require_campaign_gm, require_gm
from app.config import settings
from app.spotify import client, dienst
from app.spotify import repository as spotify_repo
from app.spotify.client import SpotifyFehler

router = APIRouter(prefix="/api/spotify", tags=["spotify"])
campaign_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/spotify",
    tags=["spotify"],
    dependencies=[Depends(require_campaign_gm)],
)

# Kurzlebige State-Nonces gegen CSRF im OAuth-Redirect — kein Neo4j nötig,
# der Handshake dauert Sekunden. Alte Einträge räumt jeder neue Aufruf mit auf.
_PENDING_TTL_SEK = 600
_pending_states: dict[str, float] = {}


def _states_aufraeumen() -> None:
    grenze = time.time() - _PENDING_TTL_SEK
    for s in [s for s, t in _pending_states.items() if t < grenze]:
        _pending_states.pop(s, None)


class SpotifyStatusResponse(BaseModel):
    verbunden: bool
    anzeigename: str | None = None


@router.get("/status", response_model=SpotifyStatusResponse)
async def status_abfragen(claims: dict = Depends(require_gm)):
    return await spotify_repo.status()


@router.get("/verbinden")
async def verbinden(claims: dict = Depends(require_gm)):
    """Leitet zum Spotify-Login weiter — der „Verbinden"-Knopf in den
    Einstellungen ruft das als volle Seitennavigation auf, kein fetch()."""
    if not settings.spotify_client_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein Spotify-Client konfiguriert (backend/.env)")
    _states_aufraeumen()
    state = secrets.token_urlsafe(16)
    _pending_states[state] = time.time()
    return RedirectResponse(client.authorize_url(state))


@router.get("/callback")
async def callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """Rücksprung von Spotify nach Login/Zustimmung.

    Bewusst OHNE Auth-Abhängigkeit: die Redirect-URI liegt auf einem eigenen
    Port (127.0.0.1:8001 — Spotify verlangt seit 2025 eine explizite
    Loopback-Adresse statt "localhost"), die Anfrage trägt deshalb NICHT das
    Sitzungs-Cookie des Frontends (anderer Host als localhost:5173, Cookies
    sind host-gebunden). Der `state`-Nonce übernimmt die CSRF-Absicherung —
    das ist beim Authorization-Code-Flow ohnehin der übliche Schutz, nicht
    eine zusätzliche Cookie-Prüfung.
    """
    ziel = settings.frontend_base_url

    if error or not code or not state or state not in _pending_states:
        return RedirectResponse(f"{ziel}?spotify=fehler")
    _pending_states.pop(state, None)

    try:
        token_antwort = await client.tausche_code_gegen_token(code)
        profil = await client.eigenes_profil(token_antwort["access_token"])
        await spotify_repo.verbinden(
            token_antwort["refresh_token"],
            profil.get("display_name") or profil.get("id") or "Spotify",
        )
    except SpotifyFehler:
        return RedirectResponse(f"{ziel}?spotify=fehler")

    return RedirectResponse(f"{ziel}?spotify=verbunden")


@router.post("/trennen")
async def trennen(claims: dict = Depends(require_gm)):
    await spotify_repo.trennen()
    return {"ok": True}


class PlaylistTreffer(BaseModel):
    uri: str
    id: str
    name: str
    besitzer: str
    bildUrl: str
    anzahlTracks: int


@campaign_router.get("/suche", response_model=list[PlaylistTreffer])
async def playlists_suchen(campaign_id: str, q: str = Query(min_length=1)):
    try:
        access_token = await spotify_repo.gueltiger_access_token()
        return await client.suche_playlists(access_token, q)
    except SpotifyFehler as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))


class AbspielenRequest(BaseModel):
    zielId: str
    zielKind: str  # "Ort" | "Event"


class AbspielenResponse(BaseModel):
    hinweis: str


@campaign_router.post("/abspielen", response_model=AbspielenResponse)
async def abspielen(campaign_id: str, body: AbspielenRequest):
    """Manueller Fallback-Knopf — startet die am Ziel hinterlegte Playlist
    sofort, unabhängig von der aktiven Party (z.B. zum Testen am Tisch)."""
    hinweis = await dienst.playlist_fuer_ziel_abspielen(campaign_id, body.zielId, body.zielKind)
    if hinweis is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An diesem Ziel ist keine Playlist hinterlegt")
    return AbspielenResponse(hinweis=hinweis)
