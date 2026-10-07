"""Gemini-Client: Wiederholung bei vorübergehender Überlastung (HTTP 503)
und bei Transport-Fehlern (Timeout/Verbindungsabbruch).

Hintergrund (06./07.10.2026): Gemini antwortete stundenlang mit
"This model is currently experiencing high demand... Please try again
later." (HTTP 503) — ca. jeder zweite Aufruf schlug fehl, obwohl weder
Kontingent noch API-Key das Problem waren. `_post_mit_retry` fängt genau
das ab, bevor es als Fehler beim Nutzer landet.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.ki import gemini
from app.ki.gemini import GeminiFehler


def _run(coro):
    return asyncio.run(coro)


def _antwort(status_code: int, **json_body) -> httpx.Response:
    return httpx.Response(status_code, json=json_body or {"ok": True})


def _text_antwort(text: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": text}]}}]},
    )


def _ueberlastet() -> httpx.Response:
    return httpx.Response(
        503,
        json={
            "error": {
                "message": "This model is currently experiencing high demand. "
                "Spikes in demand are usually temporary. Please try again later."
            }
        },
    )


def test_503_wird_wiederholt_und_gelingt_dann(monkeypatch):
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    with (
        patch.object(
            httpx.AsyncClient,
            "post",
            AsyncMock(side_effect=[_ueberlastet(), _ueberlastet(), _text_antwort("Hallo!")]),
        ) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()) as sleep,
    ):
        ergebnis = _run(gemini.generiere_text([{"rolle": "user", "text": "Hi"}]))
    assert ergebnis == "Hallo!"
    assert post.call_count == 3
    assert sleep.call_count == 2
    sleep.assert_any_call(2)
    sleep.assert_any_call(4)


def test_503_dauerhaft_meldet_nach_allen_versuchen_denselben_fehler_wie_vorher(monkeypatch):
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    with (
        patch.object(httpx.AsyncClient, "post", AsyncMock(return_value=_ueberlastet())) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()),
    ):
        with pytest.raises(GeminiFehler) as exc:
            _run(gemini.generiere_text([{"rolle": "user", "text": "Hi"}]))
    assert post.call_count == 3  # 1 Erstversuch + 2 Wiederholungen, dann aufgeben
    assert "HTTP 503" in str(exc.value)
    assert "high demand" in str(exc.value)


def test_transport_fehler_wird_wiederholt_und_gelingt_dann(monkeypatch):
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    with (
        patch.object(
            httpx.AsyncClient,
            "post",
            AsyncMock(side_effect=[httpx.ConnectTimeout("timeout"), _text_antwort("Moin!")]),
        ) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()) as sleep,
    ):
        ergebnis = _run(gemini.generiere_text([{"rolle": "user", "text": "Hi"}]))
    assert ergebnis == "Moin!"
    assert post.call_count == 2
    assert sleep.call_count == 1


def test_transport_fehler_dauerhaft_wird_als_lesbarer_gemini_fehler_gemeldet(monkeypatch):
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    with (
        patch.object(
            httpx.AsyncClient, "post", AsyncMock(side_effect=httpx.ConnectTimeout("timeout"))
        ) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()),
    ):
        with pytest.raises(GeminiFehler) as exc:
            _run(gemini.generiere_text([{"rolle": "user", "text": "Hi"}]))
    assert post.call_count == 3
    assert "nicht erreichbar" in str(exc.value)


def test_sofortiger_erfolg_wiederholt_nicht(monkeypatch):
    """Regression: der Normalfall darf nicht langsamer werden."""
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    with (
        patch.object(httpx.AsyncClient, "post", AsyncMock(return_value=_text_antwort("Hallo!"))) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()) as sleep,
    ):
        ergebnis = _run(gemini.generiere_text([{"rolle": "user", "text": "Hi"}]))
    assert ergebnis == "Hallo!"
    assert post.call_count == 1
    sleep.assert_not_called()


def test_andere_fehlerstatus_werden_nicht_wiederholt(monkeypatch):
    """400/403/etc. sind keine Lastspitzen — kein Grund, Zeit zu verschwenden."""
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    with (
        patch.object(httpx.AsyncClient, "post", AsyncMock(return_value=_antwort(400))) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()) as sleep,
    ):
        with pytest.raises(GeminiFehler) as exc:
            _run(gemini.generiere_text([{"rolle": "user", "text": "Hi"}]))
    assert post.call_count == 1
    sleep.assert_not_called()
    assert "HTTP 400" in str(exc.value)


def test_generiere_json_nutzt_denselben_retry(monkeypatch):
    monkeypatch.setattr(gemini.settings, "gemini_api_key", "test-key")
    json_antwort = httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": '{"name": "Dings"}'}]}}]},
    )
    with (
        patch.object(
            httpx.AsyncClient, "post", AsyncMock(side_effect=[_ueberlastet(), json_antwort])
        ) as post,
        patch("app.ki.gemini.asyncio.sleep", AsyncMock()),
    ):
        ergebnis = _run(gemini.generiere_json("prompt"))
    assert ergebnis == {"name": "Dings"}
    assert post.call_count == 2
