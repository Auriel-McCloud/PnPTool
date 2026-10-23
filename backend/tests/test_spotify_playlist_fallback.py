"""Event ohne eigene Playlist übernimmt die des verbundenen Orts (23.10.2026)."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.spotify import dienst


def _run(coro):
    return asyncio.run(coro)


def test_ort_mit_eigener_playlist_bleibt_unveraendert():
    """Normalfall (Ort, keine VERBINDUNG-Logik beteiligt) bleibt wie bisher."""
    ort = {"id": "o1", "spotifyPlaylistUri": "spotify:playlist:abc", "spotifyPlaylistName": "Neon Nights"}

    async def run():
        with patch("app.spotify.dienst.get_node", AsyncMock(return_value=ort)), \
             patch("app.spotify.dienst.get_verbundener_ort_mit_playlist", AsyncMock()) as fallback, \
             patch("app.spotify.dienst.spotify_repo.gueltiger_access_token", AsyncMock(return_value="tok")), \
             patch("app.spotify.dienst.client.wiedergabe_starten", AsyncMock()) as starten:
            hinweis = await dienst.playlist_fuer_ziel_abspielen("c1", "o1", "Ort")
        fallback.assert_not_called()
        starten.assert_awaited_once_with("tok", "spotify:playlist:abc")
        assert hinweis == "🎵 Wiedergabe gestartet: Neon Nights"

    _run(run())


def test_event_mit_eigener_playlist_nutzt_kein_fallback():
    event = {"id": "e1", "spotifyPlaylistUri": "spotify:playlist:event", "spotifyPlaylistName": "Eventmusik"}

    async def run():
        with patch("app.spotify.dienst.get_node", AsyncMock(return_value=event)), \
             patch("app.spotify.dienst.get_verbundener_ort_mit_playlist", AsyncMock()) as fallback, \
             patch("app.spotify.dienst.spotify_repo.gueltiger_access_token", AsyncMock(return_value="tok")), \
             patch("app.spotify.dienst.client.wiedergabe_starten", AsyncMock()):
            hinweis = await dienst.playlist_fuer_ziel_abspielen("c1", "e1", "Event")
        fallback.assert_not_called()
        assert hinweis == "🎵 Wiedergabe gestartet: Eventmusik"

    _run(run())


def test_event_ohne_playlist_faellt_auf_verbundenen_ort_zurueck():
    event = {"id": "e1", "spotifyPlaylistUri": ""}
    verbundener_ort = {
        "id": "o1", "name": "Die Neon-Katze",
        "spotifyPlaylistUri": "spotify:playlist:ort", "spotifyPlaylistName": "Bar-Sound",
    }

    async def run():
        with patch("app.spotify.dienst.get_node", AsyncMock(return_value=event)), \
             patch("app.spotify.dienst.get_verbundener_ort_mit_playlist", AsyncMock(return_value=verbundener_ort)) as fallback, \
             patch("app.spotify.dienst.spotify_repo.gueltiger_access_token", AsyncMock(return_value="tok")), \
             patch("app.spotify.dienst.client.wiedergabe_starten", AsyncMock()) as starten:
            hinweis = await dienst.playlist_fuer_ziel_abspielen("c1", "e1", "Event")
        fallback.assert_awaited_once_with("c1", "e1")
        starten.assert_awaited_once_with("tok", "spotify:playlist:ort")
        assert hinweis == "🎵 Wiedergabe gestartet: Bar-Sound (Playlist von Ort „Die Neon-Katze\")"

    _run(run())


def test_event_ohne_playlist_und_ohne_verbundenen_ort_gibt_none():
    event = {"id": "e1", "spotifyPlaylistUri": ""}

    async def run():
        with patch("app.spotify.dienst.get_node", AsyncMock(return_value=event)), \
             patch("app.spotify.dienst.get_verbundener_ort_mit_playlist", AsyncMock(return_value=None)), \
             patch("app.spotify.dienst.client.wiedergabe_starten", AsyncMock()) as starten:
            hinweis = await dienst.playlist_fuer_ziel_abspielen("c1", "e1", "Event")
        starten.assert_not_called()
        assert hinweis is None

    _run(run())


def test_ziel_nicht_gefunden_gibt_none():
    async def run():
        with patch("app.spotify.dienst.get_node", AsyncMock(return_value=None)):
            hinweis = await dienst.playlist_fuer_ziel_abspielen("c1", "fehlt", "Ort")
        assert hinweis is None

    _run(run())
