"""Verknuepft Party-Aufenthaltsort mit Spotify-Wiedergabe.

Eigene Datei statt direkt in party/routes.py: die Party soll nichts ueber
Spotify wissen muessen (Trennung der Fachlichkeit) — sie ruft nur diese eine
Funktion auf und bekommt einen Hinweistext fuer die SL zurueck, nie eine
Exception. Ein Spotify-Ausfall (nicht verbunden, kein Geraet aktiv) darf den
Aufenthaltsort-Wechsel selbst nie verhindern — Musik ist ein Bonus, keine
Voraussetzung zum Weiterspielen.
"""

from app.entities.repository import EVENT_FIELDS, ORT_FIELDS, get_node, get_verbundener_ort_mit_playlist
from app.spotify import client
from app.spotify import repository as spotify_repo
from app.spotify.client import SpotifyFehler


async def playlist_fuer_ziel_abspielen(campaign_id: str, ziel_id: str, ziel_kind: str) -> str | None:
    """Startet die am Ziel (Ort/Event) hinterlegte Playlist.

    Fallback (Mark, 23.10.2026): hat das Ziel ein Event OHNE eigene Playlist,
    wird die Playlist des per VERBINDUNG-Kante verknüpften Orts genommen,
    falls vorhanden — ein Event ist so gut wie immer an einen Ort gebunden,
    der die eigentliche Stimmungsmusik trägt (siehe
    get_verbundener_ort_mit_playlist).

    Gibt einen Hinweistext für die Spielleitung zurück (Erfolg oder lesbarer
    Grund, warum nicht), oder `None`, wenn weder am Ziel noch (bei einem
    Event) an einem verknüpften Ort eine Playlist hinterlegt ist — dann gibt
    es nichts zu vermelden, kein Hinweis nötig.
    """
    label = "Ort" if ziel_kind == "Ort" else "Event"
    felder = ORT_FIELDS if ziel_kind == "Ort" else EVENT_FIELDS
    ziel = await get_node(label, felder, campaign_id, ziel_id)
    if ziel is None:
        return None

    quelle = ziel
    fallback_ort_name: str | None = None
    if ziel_kind == "Event" and not ziel.get("spotifyPlaylistUri"):
        verbundener_ort = await get_verbundener_ort_mit_playlist(campaign_id, ziel_id)
        if verbundener_ort is None:
            return None
        quelle = verbundener_ort
        fallback_ort_name = verbundener_ort.get("name")
    elif not ziel.get("spotifyPlaylistUri"):
        return None

    try:
        access_token = await spotify_repo.gueltiger_access_token()
        await client.wiedergabe_starten(access_token, quelle["spotifyPlaylistUri"])
        name = quelle.get("spotifyPlaylistName") or "Playlist"
        if fallback_ort_name:
            return f"🎵 Wiedergabe gestartet: {name} (Playlist von Ort „{fallback_ort_name}\")"
        return f"🎵 Wiedergabe gestartet: {name}"
    except SpotifyFehler as e:
        return f"🎵 Playlist hinterlegt, aber nicht gestartet: {e}"
