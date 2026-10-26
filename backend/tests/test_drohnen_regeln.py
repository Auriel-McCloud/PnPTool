"""Riggerkonsole-Slots + Nuyen-Kauf an Drohnen/Fahrzeugen.

Siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
"""

from app.traits.drohnen import benoetigte_erfolge_maker_probe, kann_aktivieren, kann_bezahlen


class TestKannAktivieren:
    def test_slot_frei(self):
        assert kann_aktivieren(aktuell_aktive=1, max_drohnen=2) is True

    def test_kein_slot_frei(self):
        assert kann_aktivieren(aktuell_aktive=2, max_drohnen=2) is False

    def test_keine_konsole_kein_slot(self):
        assert kann_aktivieren(aktuell_aktive=0, max_drohnen=0) is False


class TestKannBezahlen:
    """Mark, 25.10.2026: 'Der Rigger zahlt es aus seinem Kapitel, die Drohne
    hat keins!' — geprüft wird immer das Kapital des RIGGERS."""

    def test_kapital_reicht_genau(self):
        assert kann_bezahlen(preis=600, rigger_kapital=600) is True

    def test_kapital_reicht_nicht(self):
        assert kann_bezahlen(preis=600, rigger_kapital=599) is False

    def test_ueberschuessiges_kapital_reicht_erst_recht(self):
        assert kann_bezahlen(preis=100, rigger_kapital=100_000) is True

    def test_negatives_kapital_wird_wie_null_behandelt(self):
        assert kann_bezahlen(preis=0, rigger_kapital=-100) is True
        assert kann_bezahlen(preis=1, rigger_kapital=-100) is False


class TestBenoetigteErfolgeMakerProbe:
    """Mark, 26.10.2026: 'die Anzahl der Erfolge die er benötigt ist die
    Anzahl der vorhandenen Punkte in dem Skill/Attribut +1'."""

    def test_frischer_wert_braucht_einen_erfolg(self):
        assert benoetigte_erfolge_maker_probe(0) == 1

    def test_hoher_wert_braucht_entsprechend_mehr(self):
        assert benoetigte_erfolge_maker_probe(4) == 5

    def test_negativer_wert_wie_null_behandelt(self):
        assert benoetigte_erfolge_maker_probe(-3) == 1
