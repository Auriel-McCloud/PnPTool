"""Tests für Beschwörungs-Ki-Tama: Probe-Formel und Beschwörungswert, siehe
app/items/beschwoerung.py und docs/wiki/concepts/augments-ausruestung.md."""

from app.items.beschwoerung import benoetigte_erfolge, beschwoerungsstufe


class TestBeschwoerungsstufe:
    def test_hoechste_markierte_fertigkeit_zaehlt(self):
        fertigkeiten = {"Feuersalamander": 4, "Blitz": 6}
        markiert = {"Feuersalamander": True, "Blitz": False}
        assert beschwoerungsstufe(fertigkeiten, markiert) == 4

    def test_unmarkierte_fertigkeiten_zaehlen_nicht(self):
        fertigkeiten = {"Blitz": 6}
        markiert = {"Blitz": False}
        assert beschwoerungsstufe(fertigkeiten, markiert) == 0

    def test_ohne_markierung_ueberhaupt_null(self):
        assert beschwoerungsstufe({}, {}) == 0

    def test_mehrere_markierte_nimmt_das_maximum(self):
        fertigkeiten = {"A": 2, "B": 5}
        markiert = {"A": True, "B": True}
        assert beschwoerungsstufe(fertigkeiten, markiert) == 5


class TestBenoetigteErfolge:
    def test_stufe_aufgerundet_ohne_schwierigkeit(self):
        # Mark, ENTSCHIEDEN: Stufe 1->1, 2->1, 3->2, 4->2, 5->3, 6->3.
        erwartet = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3}
        for stufe, erfolge in erwartet.items():
            assert benoetigte_erfolge(stufe, 0) == erfolge

    def test_schwierigkeit_kommt_additiv_oben_drauf(self):
        assert benoetigte_erfolge(3, 2) == 4
        assert benoetigte_erfolge(6, 1) == 4

    def test_null_stufe_ist_nicht_negativ(self):
        assert benoetigte_erfolge(0, 0) == 0

    def test_negative_eingaben_zaehlen_als_null(self):
        assert benoetigte_erfolge(-3, -2) == 0
