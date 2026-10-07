"""app.ki.client.generiere_text: automatischer Gemini<->Mistral-Fallback.

Mark (07.10.2026): nach dem reinen Retry-Fix in gemini.py (siehe
test_gemini_retry.py) hielt die Gemini-Überlastung trotzdem an — als
nächste Ausbaustufe wollte er, dass die Beratung bei einem dauerhaft
ausfallenden Anbieter automatisch den anderen probiert, UND dass im Chat
sichtbar ist, welcher Anbieter tatsächlich geantwortet hat.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.ki.client import KiFehler, generiere_text
from app.ki.gemini import GeminiFehler
from app.ki.mistral import MistralFehler


def _run(coro):
    return asyncio.run(coro)


def test_primaerer_provider_erfolgreich_kein_fallback_versucht():
    with (
        patch("app.ki.client.gemini.generiere_text", AsyncMock(return_value="Hallo von Gemini")) as g,
        patch("app.ki.client.mistral.generiere_text", AsyncMock()) as m,
    ):
        text, provider = _run(
            generiere_text([{"rolle": "user", "text": "Hi"}], provider="gemini", campaign_id=None)
        )
    assert (text, provider) == ("Hallo von Gemini", "gemini")
    g.assert_awaited_once()
    m.assert_not_called()


def test_gemini_faellt_dauerhaft_aus_mistral_uebernimmt():
    with (
        patch("app.ki.client.gemini.generiere_text", AsyncMock(side_effect=GeminiFehler("HTTP 503: high demand"))),
        patch("app.ki.client.mistral.generiere_text", AsyncMock(return_value="Hallo von Mistral")) as m,
    ):
        text, provider = _run(
            generiere_text([{"rolle": "user", "text": "Hi"}], provider="gemini", campaign_id=None)
        )
    assert (text, provider) == ("Hallo von Mistral", "mistral")
    m.assert_awaited_once()


def test_mistral_faellt_aus_gemini_uebernimmt_umgekehrte_richtung():
    with (
        patch("app.ki.client.mistral.generiere_text", AsyncMock(side_effect=MistralFehler("HTTP 500"))),
        patch("app.ki.client.gemini.generiere_text", AsyncMock(return_value="Hallo von Gemini")) as g,
    ):
        text, provider = _run(
            generiere_text([{"rolle": "user", "text": "Hi"}], provider="mistral", campaign_id=None)
        )
    assert (text, provider) == ("Hallo von Gemini", "gemini")
    g.assert_awaited_once()


def test_beide_anbieter_fallen_aus_lesbarer_kombinierter_fehler():
    with (
        patch("app.ki.client.gemini.generiere_text", AsyncMock(side_effect=GeminiFehler("Gemini kaputt"))),
        patch("app.ki.client.mistral.generiere_text", AsyncMock(side_effect=MistralFehler("Mistral auch kaputt"))),
    ):
        with pytest.raises(KiFehler) as exc:
            _run(generiere_text([{"rolle": "user", "text": "Hi"}], provider="gemini", campaign_id=None))
    assert "Gemini kaputt" in str(exc.value)
    assert "Mistral auch kaputt" in str(exc.value)


def test_unbekannter_provider_wird_sofort_abgelehnt_kein_fallback_versuch(monkeypatch):
    # _aufloesen() faellt bei einem ungueltigen provider-Parameter immer auf
    # settings.ki_provider zurueck (siehe client.py) — die einzig erreichbare
    # Stelle fuer "unbekannter Provider" ist ein falsch konfigurierter
    # Server-Standard selbst.
    from app.ki import client

    monkeypatch.setattr(client.settings, "ki_provider", "chatgpt")
    with (
        patch("app.ki.client.gemini.generiere_text", AsyncMock()) as g,
        patch("app.ki.client.mistral.generiere_text", AsyncMock()) as m,
    ):
        with pytest.raises(KiFehler, match="Unbekannter KI_PROVIDER"):
            _run(generiere_text([{"rolle": "user", "text": "Hi"}], provider=None, campaign_id=None))
    g.assert_not_called()
    m.assert_not_called()
