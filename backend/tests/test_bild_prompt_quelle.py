"""Bild-Prompt-Quelle: Name, Beschreibung und Notizen."""

from app.ki.routes import _bild_prompt_quelle


def test_notizen_landen_in_der_prompt_quelle():
    text = _bild_prompt_quelle(
        "Person", "Aria", "eine Deckerin", "rote Haare, Cyberauge links"
    )
    assert "Aria" in text
    assert "eine Deckerin" in text
    assert "rote Haare" in text
    assert "Cyberauge links" in text


def test_leere_notizen_erscheinen_nicht():
    text = _bild_prompt_quelle("Person", "Aria", "eine Deckerin", "   ")
    assert "Notizen" not in text
    assert "eine Deckerin" in text


def test_nur_notizen_ohne_beschreibung():
    text = _bild_prompt_quelle("Ort", "Nachtmarkt", "", "neonrot, nass, Dampf")
    assert "Nachtmarkt" in text
    assert "neonrot" in text
    assert "Bisherige Beschreibung" not in text
