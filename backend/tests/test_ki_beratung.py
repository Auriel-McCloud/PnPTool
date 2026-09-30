"""Invarianten der SL-Beratung: Kanon bleibt Freigegebenes."""

from pathlib import Path

from app.ki.beratung import _titel_aus, fuer_modell, gespraech_als_prompt


def test_sammle_kontext_kennt_beratung_nicht():
    """KiBeratung darf nie in den Kampagnenkontext rutschen."""
    text = Path("app/ki/kontext.py").read_text(encoding="utf-8")
    assert "KiBeratung" not in text
    assert "WikiSeite" in text


def test_titel_kuerzt_lange_erste_nachricht():
    assert _titel_aus("kurz") == "kurz"
    assert _titel_aus("") == "Neue Beratung"
    lang = "x" * 80
    titel = _titel_aus(lang)
    assert titel.endswith("…")
    assert len(titel) <= 48


def test_fuer_modell_nimmt_nur_die_letzten_turns():
    msgs = [{"rolle": "user", "text": str(i), "id": str(i)} for i in range(40)]
    out = fuer_modell(msgs)
    assert len(out) == 30
    assert out[0]["text"] == "10"
    assert "id" not in out[0]


def test_gespraech_als_prompt_trennt_rollen():
    text = gespraech_als_prompt(
        [
            {"rolle": "user", "text": "Club im Hafen?"},
            {"rolle": "assistant", "text": "Passt zu Chrysalis."},
        ]
    )
    assert "Spielleitung: Club im Hafen?" in text
    assert "Beratung: Passt zu Chrysalis." in text
    assert "Verworfene Ideen weglassen" in text
