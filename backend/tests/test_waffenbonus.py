from app.items.waffenbonus import (
    SCHADEN_MAX,
    kampf_fertigkeit_lesen,
    ki_schaden_roh,
    schaden_klemmen,
    waffenfelder,
)


def test_handwaffe_nimmt_den_wert():
    assert waffenfelder("Waffe", 4) == {
        "kraft": 4,
        "schaden": 4,
        "istWaffe": True,
        "schadenArt": "schwer",
        "paradeBonus": 0,
    }


def test_fehlende_angabe_wird_stufe_1():
    assert schaden_klemmen(None, typ="Waffe") == 1
    assert schaden_klemmen(0, typ="Waffe") == 1


def test_schiffswaffe_darf_12():
    assert schaden_klemmen(12, typ="Waffe") == 12
    assert SCHADEN_MAX == 12
    assert waffenfelder("Waffe", 12)["schaden"] == 12


def test_ueber_12_wird_geklemmt():
    assert schaden_klemmen(13, typ="Waffe") == 12
    assert schaden_klemmen(99, typ="Waffe") == 12


def test_kein_waffenschaden_bei_anderem_typ():
    assert waffenfelder("Sonstiges", 4) == {}
    assert schaden_klemmen(4, typ="Rüstung") == 4


def test_fehlende_schadensart_ist_toedlich():
    assert waffenfelder("Waffe", 3)["schadenArt"] == "schwer"
    assert waffenfelder("Waffe", 3, "schlag")["schadenArt"] == "schlag"
    assert waffenfelder("Waffe", 3, "unheilbar")["schadenArt"] == "aggraviert"


def test_alter_schluessel_schadensbonus_gilt_noch():
    assert ki_schaden_roh({"schaden": 5}) == 5
    assert ki_schaden_roh({"schadensbonus": 3}) == 3
    assert ki_schaden_roh({"schaden": 8, "schadensbonus": 2}) == 8


def test_kampf_fertigkeit_nur_die_drei_skills():
    assert kampf_fertigkeit_lesen("Schusswaffen") == "Schusswaffen"
    assert kampf_fertigkeit_lesen("Nahkampf") == "Nahkampf"
    assert kampf_fertigkeit_lesen("Handgemenge") == "Handgemenge"
    assert kampf_fertigkeit_lesen("Fernkampf") == ""
    assert kampf_fertigkeit_lesen(None) == ""
    assert kampf_fertigkeit_lesen("") == ""


def test_schild_behaelt_schaden_null_wenn_parade_gesetzt():
    felder = waffenfelder("Waffe", 0, "schlag", 2)
    assert felder["schaden"] == 0
    assert felder["paradeBonus"] == 2
    assert felder["schadenArt"] == "schlag"


def test_fehlender_schaden_ohne_parade_bleibt_stufe_1():
    assert waffenfelder("Waffe", 0)["schaden"] == 1
    assert waffenfelder("Waffe", None)["paradeBonus"] == 0


def test_parade_bonus_hebt_nur_das_parieren():
    from app.items.waffenbonus import parade_mit_waffe

    basis = 5
    assert parade_mit_waffe(basis, 2) == 7
    assert parade_mit_waffe(basis, 0) == basis
    assert parade_mit_waffe(basis, -1) == 4


def test_grosse_parier_zahl_nimmt_die_nahkampfwaffe():
    """Fernkampf kann nicht parieren — die große Kachel zeigt die Schwert-Parade."""
    from app.items.waffenbonus import parier_pool

    basis = 6
    assert parier_pool(basis, []) == 6
    assert parier_pool(basis, [2]) == 8
    assert parier_pool(basis, [2, 0]) == 8
    assert parier_pool(basis, [1, 3]) == 9


def test_nahkampf_schaden_addiert_koerperkraft():
    """Waffenschaden 3 + Körperkraft 3 = 6 auf der Zeile, Fernkampf bleibt 3."""
    from app.items.waffenbonus import waffen_schaden_anzeige

    assert waffen_schaden_anzeige(3, 3, "Nahkampf") == 6
    assert waffen_schaden_anzeige(3, 3, "Handgemenge") == 6
    assert waffen_schaden_anzeige(3, 3, "Schusswaffen") == 3
    assert waffen_schaden_anzeige(3, 3, "") == 3


def test_pistole_zaehlt_nicht_als_paradewaffe():
    from app.items.waffenbonus import ist_parade_waffe

    assert ist_parade_waffe("Nahkampf", 2) is True
    assert ist_parade_waffe("Handgemenge", 0) is True
    assert ist_parade_waffe("Schusswaffen", 2) is False
    assert ist_parade_waffe("", 2) is True
    assert ist_parade_waffe("", 0) is False
