"""Riggerkonsole-Aktiv-Slot-Logik (25.10.2026) — siehe traits/drohnen.py."""

from app.traits.drohnen import kann_aktivieren


class TestKannAktivieren:
    def test_unter_dem_deckel_erlaubt(self):
        assert kann_aktivieren(aktuell_aktive=1, max_drohnen=2) is True

    def test_am_deckel_nicht_mehr_erlaubt(self):
        assert kann_aktivieren(aktuell_aktive=2, max_drohnen=2) is False

    def test_ohne_konsole_nie_erlaubt(self):
        assert kann_aktivieren(aktuell_aktive=0, max_drohnen=0) is False

    def test_negative_werte_werden_wie_null_behandelt(self):
        assert kann_aktivieren(aktuell_aktive=-3, max_drohnen=1) is True
        assert kann_aktivieren(aktuell_aktive=0, max_drohnen=-1) is False
