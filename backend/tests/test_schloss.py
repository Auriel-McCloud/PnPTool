"""Schloss-Logik ohne Datenbank: Lösung, Folge, PATCH-Regeln."""

from app.items.schloss import (
    anzeige_fuer,
    ist_verschlossen,
    neue_folge,
    passwort_passt,
    schloss_patch_anpassen,
    zug_passt,
)


def test_passwort_ignoriert_grossschreibung_und_leerzeichen():
    assert passwort_passt("  Ratte ", "ratte")
    assert not passwort_passt("maus", "ratte")
    assert not passwort_passt("", "ratte")


def test_verschlossen_nur_mit_art_und_noch_zu():
    assert ist_verschlossen({"schlossArt": "passwort", "aufgeschlossen": False})
    assert not ist_verschlossen({"schlossArt": "passwort", "aufgeschlossen": True})
    assert not ist_verschlossen({"schlossArt": "", "aufgeschlossen": False})


def test_folge_hat_die_gesetzte_laenge_und_fuenf_tasten():
    folge = neue_folge(6)
    assert len(folge) == 6
    assert all(0 <= taste <= 4 for taste in folge)
    assert len(neue_folge(0)) == 1


def test_runde_waechst_um_eine_taste():
    folge = [0, 1, 2, 3]
    assert anzeige_fuer(folge, 0) == [0]
    assert anzeige_fuer(folge, 2) == [0, 1, 2]
    assert zug_passt([0, 1], folge, 1)
    assert not zug_passt([0, 2], folge, 1)


def test_patch_ohne_loesung_wird_abgelehnt():
    fehler = schloss_patch_anpassen({"id": "kiste", "schlossArt": ""}, {"schlossArt": "passwort", "schlossPasswort": "  "})
    assert fehler


def test_wechsel_der_art_setzt_das_spiel_zurueck():
    daten = {"schlossArt": "spiel", "spielLaenge": 5}
    assert schloss_patch_anpassen({"id": "kiste", "schlossArt": "passwort", "aufgeschlossen": True}, daten) is None
    assert daten["aufgeschlossen"] is False
    assert daten["spielRunde"] == 0
    assert daten["spielFolge"] == "[]"


def test_spiel_ohne_laenge_startet_bei_vier():
    daten = {"schlossArt": "spiel"}
    assert schloss_patch_anpassen({"id": "kiste", "schlossArt": ""}, daten) is None
    assert daten["spielLaenge"] == 4
