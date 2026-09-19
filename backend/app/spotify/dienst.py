"""Verknuepft Party-Aufenthaltsort mit Spotify-Wiedergabe.

Eigene Datei statt direkt in party/routes.py: die Party soll nichts ueber
Spotify wissen muessen (Trennung der Fachlichkeit) — sie ruft nur diese eine
Funktion auf und bekommt einen Hinweistext fuer die SL zurueck, nie eine
Exception. Ein Spotify-Ausfall (nicht verbunden, kein Geraet aktiv) darf den
Aufenthaltsort-Wechsel selbst nie verhindern — Musik ist ein Bonus, keine
Voraussetzung zum Weiterspielen.
"""

from app.entities.repository import EVENT_FIELDS, ORT_FIELDS, get_node
from app.spotify import client
from app.spotify import repository as spotify_repo
from app.spotify.client import SpotifyFehler


async def playlist_fuer_ziel_abspielen(campaign_id: str, ziel_id: str, ziel_kind: str) -> str | None:
    """Startet die am Ziel (Ort/Event) hinterlegte Playlist.

    Gibt einen Hinweistext für die Spielleitung zurück (Erfolg oder lesbarer
    Grund, warum nicht), oder `None`, wenn am Ziel gar keine Playlist
    hinterlegt ist — dann gibt es nichts zu vermelden, kein Hinweis nötig.
    """
    label = "Ort" if ziel_kind == "Ort" else "Event"
    felder = ORT_FIELDS if ziel_kind == "Ort" else EVENT_FIELDS
    ziel = await get_node(label, felder, campaign_id, ziel_id)
    if ziel is None or not ziel.get("spotifyPlaylistUri"):
        return None

    try:
        access_token = await spotify_repo.gueltiger_access_token()
        await client.wiedergabe_starten(access_token, ziel["spotifyPlaylistUri"])
        return f"🎵 Wiedergabe gestartet: {ziel.get('spotifyPlaylistName') or 'Playlist'}"
    except SpotifyFehler as e:
        return f"🎵 Playlist hinterlegt, aber nicht gestartet: {e}"
