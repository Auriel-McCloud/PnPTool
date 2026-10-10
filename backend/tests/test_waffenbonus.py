from app.items.waffenbonus import SCHADEN_MAX, schaden_klemmen, waffenfelder


def test_handwaffe_nimmt_den_wert():
    assert waffenfelder("Waffe", 4) == {"kraft": 4, "schaden": 4, "istWaffe": True}


def test_fehlende_angabe_wird_stufe_1():
    assert schaden_klemmen(None, typ="Waffe") == 1
    assert schaden_klemmen(0, typ="Waffe") == 1


def test_schiffswaffe_darf_12():
    assert schaden_klemmen(12, typ="Waffe") == 12
    assert SCHADEN_MAX == 12


def test_ueber_12_wird_geklemmt():
    assert schaden_klemmen(13, typ="Waffe") == 12
    assert schaden_klemmen(99, typ="Waffe") == 12


def test_kein_waffenschaden_bei_anderem_typ():
    assert waffenfelder("Sonstiges", 4) == {}
    assert schaden_klemmen(4, typ="Rüstung") == 4


def test_schaden_art_wird_nur_bei_klarer_angabe_gesetzt():
    from app.items.waffenbonus import schaden_art_lesen

    assert schaden_art_lesen("tödlich") == "schwer"
    assert schaden_art_lesen("Schwerheilbar") == "aggraviert"
    assert schaden_art_lesen("giftig") == ""
    assert waffenfelder("Waffe", 3, "schlag")["schadenArt"] == "schlag"
    assert "schadenArt" not in waffenfelder("Waffe", 3)
    assert "schadenArt" not in waffenfelder("Waffe", 3, "irgendwas")
