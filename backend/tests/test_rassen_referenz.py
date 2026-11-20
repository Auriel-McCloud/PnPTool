"""Reiner Referenzpool: Schalter-Start, Prompt-Hinweis, URL-Grenze."""

from app.rassen.referenz import (
    gemini_parts,
    ist_eigene_url,
    name_startet_mit_referenz,
    prompt_mit_referenz,
    waehle_url,
)


def test_startnamen_nur_die_drei_und_apostroph():
    assert name_startet_mit_referenz("Dug'Rah")
    assert name_startet_mit_referenz("Sephari")
    assert name_startet_mit_referenz("quill")
    assert not name_startet_mit_referenz("Mensch")
    assert not name_startet_mit_referenz("Dugrah")


def test_prompt_haengt_hinweis_nur_bei_referenz_an():
    teile = gemini_parts("a portrait", (b"png", "image/png"))
    assert teile[0]["text"].startswith("a portrait")
    assert "different individual" in teile[0]["text"]
    assert teile[1]["inlineData"]["mimeType"] == "image/png"
    assert gemini_parts("nur text", None) == [{"text": "nur text"}]
    assert "different individual" in prompt_mit_referenz("x")


def test_url_bleibt_im_rassenordner():
    assert ist_eigene_url("abc", "/uploads/rassen/abc/bild.png")
    assert not ist_eigene_url("abc", "/uploads/rassen/fremd/bild.png")
    assert not ist_eigene_url("abc", "/uploads/rassen/abc/../geheim.png")
    assert not ist_eigene_url("abc", "/uploads/kampagne/bild.png")


def test_waehle_url_leer():
    assert waehle_url([]) is None
    assert waehle_url(["", ""]) is None
    assert waehle_url(["/a.png"]) == "/a.png"
