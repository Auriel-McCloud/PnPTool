"""Reflex-Booster: Zusatzaktion, Überhitzung, Paralyse.

Marks Ablauf (04.09.2026), wörtlich:

    "wenn er dran kommt per Pop-up gefragt 'Reflex Booster aktivieren?' Wenn
    er ja sagt wird automatisch mit seinen Standard Initiative wert, also
    Geistes Schärfe + Geschicklichkeit ohne Bonus, gewürfelt, dadurch sollte
    er langsamer sein als bei seinem ersten Wurf und dem entsprechend ein
    2tes Mal in der initive auftauchen, sollte sein wert höher sein als sein
    ursprünglicher, kommt er direkt 2 Mal hintereinander dran."

    "wichtig ist die Logik das der Eintrag verschwindet sobald er dran war,
    und das es einen Zähler für die Stufe 3 gibt, für das überhitzen ... wenn
    er eine Runde aussetzt verschwindet wieder ein Punkt, wenn es riskiert
    und alle 3 Felder der Ampel gefüllt sind muss er am Ende seiner letzten
    Runde ... den Paralyse Wurf machen ... wenn er auf nein drückt sind all
    seine Apel Bällchen auf 0, dafür graut sein eigentlicher initive Eintrag
    aus um zu signalisieren das er die nächste Runde überspringt"

Regelblatt Zeile 443: *"Nach 3 Runden in Folge muss der Träger eine
Geistesschärfe + Willenskraft-Probe gegen 3 machen."*
"""

import pytest

from app.kampf.booster import (
    AMPEL_MAX,
    ampel_nach_aussetzen,
    ampel_nach_nutzung,
    braucht_paralyse_wurf,
    darf_aktivieren,
    paralyse_pool,
    paralyse_schwelle,
    zweitwurf_pool,
)


class TestZweitwurfPool:
    def test_ohne_bonus_gewuerfelt(self):
        # Mark: "mit seinen Standard Initiative wert, also Geistes Schärfe +
        # Geschicklichkeit ohne Bonus".
        werte = {"Geistesschärfe": 4, "Geschicklichkeit": 3}
        assert zweitwurf_pool(werte) == 7

    def test_der_boosterbonus_zaehlt_beim_zweitwurf_nicht(self):
        werte = {"Geistesschärfe": 4, "Geschicklichkeit": 3}
        # Auch wenn ein +6-Booster verbaut ist: der Zweitwurf nutzt 7, nicht 13.
        assert zweitwurf_pool(werte, cyberware_mod=6) == 7

    def test_fehlende_werte_zaehlen_als_null(self):
        assert zweitwurf_pool({}) == 0


class TestAktivierenDuerfen:
    def test_mit_freien_aktionen_erlaubt(self):
        assert darf_aktivieren(zusatzaktionen_max=2, bereits_genutzt=0) is True

    def test_letzte_aktion_noch_erlaubt(self):
        assert darf_aktivieren(zusatzaktionen_max=2, bereits_genutzt=1) is True

    def test_aufgebraucht_nicht_mehr(self):
        assert darf_aktivieren(zusatzaktionen_max=2, bereits_genutzt=2) is False

    def test_ohne_booster_nie(self):
        assert darf_aktivieren(zusatzaktionen_max=0, bereits_genutzt=0) is False

    def test_unbegrenzt_immer(self):
        # Stufe 3: "Jede Runde kannst du eine zusätzliche Aktion machen."
        assert darf_aktivieren(zusatzaktionen_max=-1, bereits_genutzt=99) is True


class TestAmpel:
    def test_nutzung_fuellt_ein_feld(self):
        assert ampel_nach_nutzung(0) == 1

    def test_ampel_steigt_bis_drei(self):
        assert ampel_nach_nutzung(2) == 3

    def test_ampel_geht_nicht_ueber_drei(self):
        assert ampel_nach_nutzung(3) == 3
        assert AMPEL_MAX == 3

    def test_aussetzen_nimmt_ein_feld_weg(self):
        # Mark: "wenn er eine Runde aussetzt verschwindet wieder ein Punkt".
        assert ampel_nach_aussetzen(2) == 1

    def test_ampel_faellt_nicht_unter_null(self):
        assert ampel_nach_aussetzen(0) == 0


class TestParalyse:
    def test_volle_ampel_verlangt_den_wurf(self):
        assert braucht_paralyse_wurf(3) is True

    def test_zwei_felder_reichen_nicht(self):
        assert braucht_paralyse_wurf(2) is False

    def test_pool_ist_geistesschaerfe_plus_willenskraft(self):
        # Regelblatt Zeile 443.
        werte = {"Geistesschärfe": 4, "Willenskraft": 5}
        assert paralyse_pool(werte) == 9

    def test_schwelle_ist_drei(self):
        assert paralyse_schwelle() == 3
