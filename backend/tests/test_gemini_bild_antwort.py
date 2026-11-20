"""Parser für Gemini-Bildantworten — unabhängig vom HTTP-Transport."""

import base64

import pytest

from app.ki.bildgenerierung import BildgenerierungFehler, _BildgenerierungKeinBildFehler, bild_aus_gemini_antwort

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


def test_no_image_ist_retrybar_und_kein_block():
    """NO_IMAGE (Mark, 20.11.2026: 'Gemini liefert kein Bild (Grund: No
    Image)') ist Modell-Unzuverlässigkeit, kein bewusster Inhalts-Block —
    muss die retrybare Unterklasse auslösen, damit _generiere_gemini
    automatisch nochmal versucht."""
    with pytest.raises(_BildgenerierungKeinBildFehler, match="NO_IMAGE"):
        bild_aus_gemini_antwort({"candidates": [{"finishReason": "NO_IMAGE"}]})


def test_image_other_ist_retrybar():
    with pytest.raises(_BildgenerierungKeinBildFehler, match="IMAGE_OTHER"):
        bild_aus_gemini_antwort({"candidates": [{"finishReason": "IMAGE_OTHER"}]})


def test_image_safety_ist_nicht_retrybar():
    """Ein bewusster Sicherheits-Block bleibt bei Wiederholung derselbe —
    darf NICHT die retrybare Unterklasse auslösen, sonst verschwendet
    _generiere_gemini 2 weitere Versuche umsonst."""
    with pytest.raises(BildgenerierungFehler, match="IMAGE_SAFETY") as exc:
        bild_aus_gemini_antwort({"candidates": [{"finishReason": "IMAGE_SAFETY"}]})
    assert not isinstance(exc.value, _BildgenerierungKeinBildFehler)


def test_no_image_mit_block_reason_ist_nicht_retrybar():
    """Ein promptFeedback.blockReason entscheidet VOR der Generierung — auch
    wenn der Text zufällig 'NO_IMAGE' wäre, zählt der explizite Block."""
    with pytest.raises(BildgenerierungFehler) as exc:
        bild_aus_gemini_antwort({"candidates": [], "promptFeedback": {"blockReason": "NO_IMAGE"}})
    assert not isinstance(exc.value, _BildgenerierungKeinBildFehler)
