"""Cyber-, Bio- und MagWare wird verbaut, nicht ausgerüstet.

Marks Korrektur: *"Das ist keine 'Ausrüstung' die funktioniert nicht wenn die
ausgerüstet ist, die muss 'eingesetzt oder ein operiert werden' wenn die
verbaut ist kann der Spieler die nicht mehr entfernen außer bei speziellen
Events ... Stattdessen gibt es dann chirurgisch entfernen."*

Bis hierher lag Chrom im selben Topf wie eine Jacke: `ablage=AUSGERUESTET`,
per Knopf ablegbar. Das war fachlich falsch.
"""

import pytest

from app.items.chirurgie import (
    ist_chrom,
    ist_wirksam,
    kann_ablegen,
    kann_einsetzen,
    kann_entfernen,
    pruefe_entfernung,
)


def g(**kwargs) -> dict:
    basis = {"name": "Ding", "typ": "Waffe", "ablage": "RUCKSACK", "verbaut": False}
    basis.update(kwargs)
    return basis


class TestWasIstChrom:
    def test_cyberware_ist_chrom(self):
        assert ist_chrom(g(typ="Cyberware")) is True

    def test_bioware_ist_chrom(self):
        assert ist_chrom(g(typ="Bioware")) is True

    def test_magware_ist_chrom(self):
        assert ist_chrom(g(typ="MagWare")) is True

    def test_eine_jacke_ist_kein_chrom(self):
        assert ist_chrom(g(typ="Kleidung")) is False

    def test_fehlender_typ_ist_kein_chrom(self):
        assert ist_chrom({"name": "x"}) is False


class TestWirksamkeit:
    def test_verbautes_chrom_wirkt(self):
        assert ist_wirksam(g(typ="Cyberware", verbaut=True)) is True

    def test_chrom_im_rucksack_wirkt_nicht(self):
        # Ein Implantat in der Tasche ist noch nicht eingesetzt.
        assert ist_wirksam(g(typ="Cyberware", verbaut=False)) is False

    def test_chrom_wirkt_unabhaengig_von_der_ablage(self):
        # Sobald es verbaut ist, spielt die Ablage keine Rolle mehr — es
        # steckt im Körper, nicht im Rucksack.
        assert ist_wirksam(g(typ="Cyberware", verbaut=True, ablage="RUCKSACK")) is True

    def test_normale_ausruestung_wirkt_wenn_ausgeruestet(self):
        assert ist_wirksam(g(typ="Kleidung", ablage="AUSGERUESTET")) is True

    def test_normale_ausruestung_im_rucksack_wirkt_nicht(self):
        assert ist_wirksam(g(typ="Kleidung", ablage="RUCKSACK")) is False


class TestAblegenVerboten:
    def test_verbautes_chrom_kann_man_nicht_ablegen(self):
        # Marks Kern: "da sollten dann auch die Buttons dazu verschwinden".
        assert kann_ablegen(g(typ="Cyberware", verbaut=True)) is False

    def test_nicht_verbautes_chrom_kann_man_umlegen(self):
        # Solange es in der Tasche liegt, ist es ein normaler Gegenstand.
        assert kann_ablegen(g(typ="Cyberware", verbaut=False)) is True

    def test_normale_ausruestung_bleibt_ablegbar(self):
        assert kann_ablegen(g(typ="Waffe", ablage="AUSGERUESTET")) is True


class TestEinsetzen:
    def test_chrom_kann_eingesetzt_werden(self):
        assert kann_einsetzen(g(typ="Cyberware", verbaut=False)) is True

    def test_bereits_verbautes_nicht_nochmal(self):
        assert kann_einsetzen(g(typ="Cyberware", verbaut=True)) is False

    def test_eine_jacke_kann_man_nicht_einsetzen(self):
        assert kann_einsetzen(g(typ="Kleidung")) is False


class TestEntfernen:
    def test_verbautes_chrom_kann_entfernt_werden(self):
        assert kann_entfernen(g(typ="Cyberware", verbaut=True)) is True

    def test_nicht_verbautes_braucht_keine_operation(self):
        assert kann_entfernen(g(typ="Cyberware", verbaut=False)) is False


class TestWerDarfOperieren:
    def test_sl_darf_entfernen(self):
        assert pruefe_entfernung("GM", beantragt=False) == "ENTFERNEN"

    def test_spieler_kann_nur_beantragen(self):
        # Mark: "SL, aber ein Spieler kann 'Entfernung beantragen'".
        assert pruefe_entfernung("PLAYER", beantragt=False) == "ANTRAG"

    def test_spieler_antrag_wird_vermerkt(self):
        assert pruefe_entfernung("PLAYER", beantragt=True) == "ANTRAG_LAEUFT"

    def test_sl_darf_trotz_laufendem_antrag_entfernen(self):
        assert pruefe_entfernung("GM", beantragt=True) == "ENTFERNEN"
