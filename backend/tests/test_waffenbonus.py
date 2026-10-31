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
