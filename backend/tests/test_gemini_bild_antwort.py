"""Parser für Gemini-Bildantworten — unabhängig vom HTTP-Transport."""

import base64

import pytest

from app.ki.bildgenerierung import BildgenerierungFehler, bild_aus_gemini_antwort

_PNG = b"\x89PNG\r\n\x1a\n"
_B64 = base64.b64encode(_PNG).decode()


def test_nimmt_inline_data_aus_erstem_part():
    roh, mime = bild_aus_gemini_antwort(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"inlineData": {"mimeType": "image/png", "data": _B64}}
                        ]
                    }
                }
            ]
        }
    )
    assert roh == _PNG
    assert mime == "image/png"


def test_nimmt_bild_auch_nach_text_part():
    roh, mime = bild_aus_gemini_antwort(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "thinking…"},
                            {"inlineData": {"mimeType": "image/jpeg", "data": _B64}},
                        ]
                    }
                }
            ]
        }
    )
    assert roh == _PNG
    assert mime == "image/jpeg"


def test_akzeptiert_snake_case_inline_data():
    roh, mime = bild_aus_gemini_antwort(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"inline_data": {"mime_type": "image/webp", "data": _B64}}
                        ]
                    }
                }
            ]
        }
    )
    assert roh == _PNG
    assert mime == "image/webp"


def test_fehlendes_content_nennt_finish_reason():
    with pytest.raises(BildgenerierungFehler, match="IMAGE_SAFETY") as exc:
        bild_aus_gemini_antwort({"candidates": [{"finishReason": "IMAGE_SAFETY"}]})
    assert "unerwartete Antwort" not in str(exc.value) or "IMAGE_SAFETY" in str(
        exc.value
    )


def test_leere_candidates_nennen_block_reason():
    with pytest.raises(BildgenerierungFehler, match="SAFETY"):
        bild_aus_gemini_antwort(
            {"candidates": [], "promptFeedback": {"blockReason": "SAFETY"}}
        )
