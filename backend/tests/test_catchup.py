"""Tests der deterministischen NPC-Catch-up-Rechnung (reine Funktionen aus
app/traits/catchup.py — der KI-Teil (Werteverteilung, Einkauf) ist nicht
sinnvoll ohne laufende KI/DB testbar, siehe ki_einkauf.py, das denselben
Grundsatz verfolgt)."""

from app.traits.catchup import berechne_budget, erfahrung_gesamt_person, vermoegen_person, ziel_erfahrung


class TestErfahrungGesamt:
    def test_addiert_individuelle_kampagnen_und_extra_ep(self):
        person = {"erfahrung": 10, "extraEP": 2}
        assert erfahrung_gesamt_person(person, kampagnen_ep=5) == 17

    def test_fehlende_felder_zaehlen_als_null(self):
        assert erfahrung_gesamt_person({}, kampagnen_ep=3) == 3


class TestVermoegen:
    def test_kapital_plus_warenwert(self):
        person = {"kapital": 500}
        gegenstaende = [{"preis": 1000}, {"preis": 250}]
        assert vermoegen_person(person, gegenstaende) == 1750

    def test_ohne_gegenstaende_nur_kapital(self):
        assert vermoegen_person({"kapital": 300}, []) == 300

    def test_fehlender_preis_zaehlt_als_null(self):
        assert vermoegen_person({"kapital": 0}, [{"preis": None}]) == 0


class TestBerechneBudget:
    def test_hundert_prozent_ist_unveraendert(self):
        assert berechne_budget(1000, 100) == 1000

    def test_zwanzig_prozent_boss_aufschlag(self):
        assert berechne_budget(1000, 120) == 1200

    def test_rundet_kaufmaennisch(self):
        assert berechne_budget(100, 125) == 125
        assert berechne_budget(99, 50) == round(49.5)

    def test_nie_negativ(self):
        assert berechne_budget(100, 0) == 0


class TestZielErfahrung:
    def test_rechnet_laufende_kampagnen_ep_heraus(self):
        """Der NPC bekommt kampagnenEP ohnehin automatisch (bogen.py) -- das
        individuelle Feld darf es nicht nochmal draufpacken."""
        assert ziel_erfahrung(budget_ep=100, kampagnen_ep=20, npc_extra_ep=0) == 80

    def test_zieht_auch_extra_ep_ab(self):
        assert ziel_erfahrung(budget_ep=100, kampagnen_ep=20, npc_extra_ep=5) == 75

    def test_nie_negativ_wenn_kampagnen_ep_schon_das_ganze_budget_deckt(self):
        assert ziel_erfahrung(budget_ep=10, kampagnen_ep=50, npc_extra_ep=0) == 0
