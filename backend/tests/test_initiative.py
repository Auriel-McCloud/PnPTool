"""Der Spieler meldet seine eigene Initiative.

Marks Kernwunsch: *"das bei würfelt Initiative, bereits bei dem jeweiligen
Spielern seine Initiative angezeigt wird, er die Möglichkeit hat seinen
manuell gewürfelten wert einzugeben, damit das bei mir in der Initiative
reinfolge automatisch angezeigt wird"*.
"""

import pytest

from app.kampf.initiative import (
    darf_melden,
    initiative_pool,
    melde_wert,
)


class TestPool:
    def test_pool_ist_geistesschaerfe_plus_geschicklichkeit(self):
        # Regelblatt Zeile 27: Initiative = Geistesschärfe + Geschicklichkeit
        # + Cyberware-Modifikator.
        werte = {"Geistesschärfe": 4, "Geschicklichkeit": 3}
        assert initiative_pool(werte) == 7

    def test_cyberware_erhoeht_den_pool(self):
        werte = {"Geistesschärfe": 4, "Geschicklichkeit": 3}
        assert initiative_pool(werte, cyberware_mod=2) == 9

    def test_fehlende_werte_zaehlen_als_null(self):
        assert initiative_pool({}) == 0

    def test_pool_wird_nicht_negativ(self):
        werte = {"Geistesschärfe": 1, "Geschicklichkeit": 1}
        assert initiative_pool(werte, cyberware_mod=-5) == 0


class TestMeldenDuerfen:
    def test_spieler_darf_fuer_seinen_charakter_melden(self):
        assert darf_melden(rolle="PLAYER", eigene_person_id="p-1", ziel_person_id="p-1") is True

    def test_spieler_darf_nicht_fuer_andere_melden(self):
        # Sonst trägt jemand dem Nachbarn eine 0 ein.
        assert darf_melden(rolle="PLAYER", eigene_person_id="p-1", ziel_person_id="p-2") is False

    def test_sl_darf_fuer_alle_melden(self):
        assert darf_melden(rolle="GM", eigene_person_id=None, ziel_person_id="p-9") is True

    def test_spieler_ohne_charakter_darf_nicht_melden(self):
        assert darf_melden(rolle="PLAYER", eigene_person_id=None, ziel_person_id="p-1") is False

    def test_teilnehmer_ohne_person_ist_fuer_spieler_tabu(self):
        # "Wachmann 1" gehört niemandem — daran darf kein Spieler drehen.
        assert darf_melden(rolle="PLAYER", eigene_person_id="p-1", ziel_person_id=None) is False


class TestWertMelden:
    def test_gemeldeter_wert_landet_als_initiative(self):
        assert melde_wert(3) == 3

    def test_null_ist_erlaubt(self):
        # Alle Würfel danebengegangen — das ist ein gültiges Ergebnis.
        assert melde_wert(0) == 0

    def test_negativer_wert_wird_abgelehnt(self):
        with pytest.raises(ValueError):
            melde_wert(-1)

    def test_unsinnig_hoher_wert_wird_abgelehnt(self):
        # Erfolge können den Pool nie um mehr als das Doppelte übersteigen
        # (lauter Zehnen), und der Pool ist selbst begrenzt.
        with pytest.raises(ValueError):
            melde_wert(999)
