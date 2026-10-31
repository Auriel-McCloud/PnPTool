"""Tests für Beschwörungs-Ki-Tama: Probe-Formel und Beschwörungswert, siehe
app/items/beschwoerung.py und docs/wiki/concepts/augments-ausruestung.md."""

from app.items.beschwoerung import benoetigte_erfolge, beschwoerungsstufe, ruf_entscheidung


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

    def test_null_stufe_hat_trotzdem_mindestens_einen_erfolg(self):
        assert benoetigte_erfolge(0, 0) == 1

    def test_negative_eingaben_zaehlen_als_null_mit_mindestens_einem_erfolg(self):
        assert benoetigte_erfolge(-3, -2) == 1


class TestRufEinmalProKampf:
    def test_patzer_verbraucht_auch_wenn_die_erfolge_reichen_wuerden(self):
        assert ruf_entscheidung("patzer", False, 6, 1) == "verbraucht"

    def test_fehlwurf_verbraucht_nicht(self):
        assert ruf_entscheidung("nein", False, 0, 1) == "offen"

    def test_null_erfolge_ohne_patzer_flag_ist_kein_patzer(self):
        assert ruf_entscheidung("ja", False, 0, 1) == "zu-wenig"

    def test_gelungener_ruf_verbraucht_und_holt_den_critter(self):
        assert ruf_entscheidung("ja", False, 1, 1) == "gerufen"

    def test_schon_gerufen_blockiert_auch_einen_weiteren_patzer(self):
        assert ruf_entscheidung("patzer", True, 0, 1) == "blockiert"
        assert ruf_entscheidung("ja", True, 4, 1) == "blockiert"

    def test_stufe_aendert_das_limit_nicht(self):
        # Dieselbe Entscheidung bei Schwelle 1 (Stufe 1) und Schwelle 3.
        assert ruf_entscheidung("ja", False, 1, 1) == "gerufen"
        assert ruf_entscheidung("ja", True, 3, 3) == "blockiert"
