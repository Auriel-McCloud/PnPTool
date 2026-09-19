"""Duenner Spotify-Web-API-Client — nur der Transport.

Authorization-Code-Flow (Login), Token-Refresh und die paar Endpunkte, die
das Tool braucht (Playlist-Suche, Wiedergabe starten). Nimmt den
Access-Token immer als Parameter entgegen statt ihn selbst zu verwalten —
das Verwalten (holen, cachen, erneuern) liegt in repository.py, damit hier
kein Kreisimport entsteht.

Gleiches Muster wie app/ki/gemini.py: ein eigener Fehlertyp, damit das
Frontend eine lesbare Meldung zeigt statt einer rohen HTTP-Exception.
"""

import base64

import httpx

from app.config import settings

_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"

# user-modify-playback-state: Wiedergabe starten.
# user-read-playback-state: ob/wo gerade etwas aktiv ist (fuer Fehlermeldungen).
# playlist-read-private: auch private Playlists durchsuchen/anzeigen koennen.
# user-read-private: fuer "verbunden als <Name>" in der Oberflaeche.
SCOPES = "user-modify-playback-state user-read-playback-state playlist-read-private user-read-private"


class SpotifyFehler(Exception):
    """Lesbare Fehlermeldung fuer die Spotify-Anbindung."""


def _basic_auth_header() -> dict:
    roh = f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()
    return {"Authorization": f"Basic {base64.b64encode(roh).decode()}"}


def _fehlertext(resp: httpx.Response) -> str:
    try:
        fehler = resp.json().get("error", {})
        if isinstance(fehler, dict):
            return fehler.get("message") or f"Spotify-Fehler (HTTP {resp.status_code})"
        return str(fehler) or f"Spotify-Fehler (HTTP {resp.status_code})"
    except Exception:
        return f"Spotify-Fehler (HTTP {resp.status_code})"


def authorize_url(state: str) -> str:
    """Die URL, zu der der Browser fuer den Login geschickt wird."""
    query = httpx.QueryParams(
        {
            "client_id": settings.spotify_client_id,
            "response_type": "code",
            "redirect_uri": settings.spotify_redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
    )
    return f"{_AUTHORIZE_URL}?{query}"


async def tausche_code_gegen_token(code: str) -> dict:
    """Erster Schritt nach der Zustimmung: Code gegen Access+Refresh-Token."""
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise SpotifyFehler("Kein Spotify-Client konfiguriert (backend/.env)")

    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.post(
            _TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            headers={**_basic_auth_header(), "Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise SpotifyFehler(f"Spotify-Login fehlgeschlagen: {_fehlertext(resp)}")
    return resp.json()


async def token_erneuern(refresh_token: str) -> dict:
    """Frischen Access-Token holen — der alte ist nach einer Stunde abgelaufen."""
    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.post(
            _TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers={**_basic_auth_header(), "Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise SpotifyFehler("Spotify-Token konnte nicht erneuert werden — bitte neu verbinden")
    return resp.json()


async def eigenes_profil(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.get(f"{_API_BASE}/me", headers={"Authorization": f"Bearer {access_token}"})
    if resp.status_code != 200:
        raise SpotifyFehler(_fehlertext(resp))
    return resp.json()


async def suche_playlists(access_token: str, suchtext: str, limit: int = 12) -> list[dict]:
    """Durchsucht Spotify nach Playlists — fuer das Auswahl-Popup an Orten/Events."""
    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.get(
            f"{_API_BASE}/search",
            params={"q": suchtext, "type": "playlist", "limit": limit},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise SpotifyFehler(_fehlertext(resp))

    treffer = ((resp.json().get("playlists") or {}).get("items")) or []
    return [
        {
            "uri": p["uri"],
            "id": p["id"],
            "name": p["name"],
            "besitzer": (p.get("owner") or {}).get("display_name", ""),
            "bildUrl": (p["images"][0]["url"] if p.get("images") else ""),
            "anzahlTracks": (p.get("tracks") or {}).get("total", 0),
        }
        # Spotify liefert in der Trefferliste vereinzelt null-Eintraege
        # (entfernte/regional gesperrte Playlists) — die einfach uebergehen.
        for p in treffer
        if p is not None
    ]


async def wiedergabe_starten(access_token: str, context_uri: str) -> None:
    """Startet die Playlist auf dem Geraet, das gerade aktiv ist.

    Bewusst ohne device_id: Mark waehlt Ziel-Geraet und Lautstaerke selbst an
    seinem Handy per Spotify Connect, das Tool greift da nicht ein. Ohne ein
    bereits aktives Geraet lehnt Spotify mit 404 ab — das ist die erwartete
    Ansage "erst am Handy irgendwo verbinden", kein Fehler im Tool.
    """
    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.put(
            f"{_API_BASE}/me/player/play",
            json={"context_uri": context_uri},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code == 404:
        raise SpotifyFehler("Kein aktives Spotify-Geraet — am Handy zuerst irgendwo verbinden/abspielen")
    if resp.status_code == 403:
        raise SpotifyFehler("Wiedergabe verweigert — dafuer wird Spotify Premium benoetigt")
    if resp.status_code not in (200, 204):
        raise SpotifyFehler(_fehlertext(resp))
