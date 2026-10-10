"""Schulden-Punkte und Kredithai-Auswahl, ohne Datenbank."""

from app.hintergruende.kredithai import (
    bestehenden_kredithai,
    kredithai_rassenkandidaten,
    schulden_punkte,
)
from app.hintergruende.seed import SYSTEM_SCHLUESSEL


def test_kein_kredit_keine_schuldenpunkte():
    assert schulden_punkte(0) == 0


def test_ein_kredit_freebee_ein_schuldenpunkt():
    assert schulden_punkte(1) == 1
    assert schulden_punkte(5) == 5
    assert schulden_punkte(8) == 8


def test_bestehenden_kredithai_nimmt_den_aeltesten():
    npcs = [
        {"id": "b", "istKredithai": True, "erstelltAm": "2026-10-02"},
        {"id": "a", "istKredithai": True, "erstelltAm": "2026-10-01"},
        {"id": "c", "istKredithai": False, "erstelltAm": "2026-09-01"},
    ]
    hai = bestehenden_kredithai(npcs)
    assert hai is not None
    assert hai["id"] == "a"


def test_ohne_markierten_hai_nichts():
    assert bestehenden_kredithai([{"id": "x", "istKredithai": False}]) is None


def test_rassenkandidaten_nur_markierte_wenn_vorhanden():
    rassen = [
        {"name": "Mensch", "kannKredithai": False},
        {"name": "Zorak", "kannKredithai": True},
    ]
    treffer = kredithai_rassenkandidaten(rassen)
    assert [r["name"] for r in treffer] == ["Zorak"]


def test_ohne_haekchen_alle_freigegebenen():
    rassen = [{"name": "Elf"}, {"name": "Ork"}]
    treffer = kredithai_rassenkandidaten(rassen)
    assert [r["name"] for r in treffer] == ["Elf", "Ork"]


def test_systemschluessel_enthaelt_schulden():
    assert "SCHULDEN" in SYSTEM_SCHLUESSEL
