"""Ring-Rätsel: Drehung, Lage der Gruppe, was Spieler sehen dürfen."""

from app.main import app
from app.raetsel.logic import (
    ANZAHL,
    ausgang_setzen,
    fuer_draht,
    freigabe_setzen,
    gruppe_setzen,
    leer,
    modus_setzen,
    name_setzen,
    raum_in_slot,
    slot_von_raum,
    tuer_zu,
    zurueck,
    zuruecksetzen,
)


def test_start_liegt_raum_auf_seinem_feld():
    z = leer()
    for slot in range(ANZAHL):
        assert raum_in_slot(z["drehung"], slot) == slot
        assert slot_von_raum(z["drehung"], slot) == slot


def test_tuer_zu_dreht_alle_gegen_den_uhrzeigersinn_und_laesst_die_gruppe_im_raum():
    z = gruppe_setzen(leer(), 0, 0)
    z = gruppe_setzen(z, 1, 3)
    vorher = list(z["gruppen"])
    neu = tuer_zu(z, 0, "N")
    assert neu["drehung"] == 1
    assert neu["gruppen"] == vorher
    assert neu["offen"] == [True, True]
    assert neu["tuer"] == {"raum": 0, "seite": "N"}
    # Raum 0 lag auf Nord (Feld 0) und steht jetzt auf Nordwest (Feld 7).
    assert slot_von_raum(neu["drehung"], 0) == 7
    assert slot_von_raum(z["drehung"], 0) == 0


def test_tuer_ohne_gesetzte_gruppe_erfindet_keine():
    neu = tuer_zu(leer(), 2, "W")
    assert neu["gruppen"] == [None, None]
    assert neu["offen"] == [False, False]


def test_nur_eine_tuer_bleibt_offen():
    neu = tuer_zu(tuer_zu(leer(), 1, "N"), 4, "S")
    assert neu["tuer"] == {"raum": 4, "seite": "S"}
    assert neu["drehung"] == 2


def test_gruppe_klicken_dreht_nicht_und_bestaetigt():
    gedreht = tuer_zu(gruppe_setzen(leer(), 0, 1), 1, "O")
    assert gedreht["offen"][0] is True
    bestaetigt = gruppe_setzen(gedreht, 0, 1)
    assert bestaetigt["drehung"] == gedreht["drehung"]
    assert bestaetigt["gruppen"][0] == 1
    assert bestaetigt["offen"][0] is False


def test_durchgehen_setzt_die_gruppe_auf_den_anderen_raum_ohne_zweite_drehung():
    gedreht = tuer_zu(gruppe_setzen(leer(), 0, 1), 1, "O")
    weiter = gruppe_setzen(gedreht, 0, 5)
    assert weiter["gruppen"][0] == 5
    assert weiter["drehung"] == 1


def test_vier_schritte_liegen_gegenueber_dem_startfeld():
    z = leer()
    for _ in range(4):
        z = tuer_zu(z, 0, "N")
    assert slot_von_raum(z["drehung"], 0) == 4
    assert slot_von_raum(z["drehung"], 2) == 6


def test_achte_schritt_ist_wieder_das_startfeld():
    z = leer()
    for _ in range(8):
        z = tuer_zu(z, 0, "S")
    assert slot_von_raum(z["drehung"], 3) == 3
    assert z["drehung"] == 8


def test_zurueck_nimmt_drehung_und_bestaetigung_zurueck():
    z = tuer_zu(gruppe_setzen(leer(), 0, 2), 2, "N")
    alt = zurueck(z)
    assert alt["drehung"] == 0
    assert alt["offen"][0] is False
    assert alt["tuer"] is None
    assert alt["gruppen"][0] == 2


def test_zurueck_ohne_historie_aendert_nichts():
    z = leer()
    assert zurueck(z)["drehung"] == 0


def test_freigabe_steht_nicht_in_der_historie():
    z = freigabe_setzen(tuer_zu(leer(), 0, "N"), True)
    alt = zurueck(z)
    assert alt["freigegeben"] is True
    assert alt["drehung"] == 0


def test_zuruecksetzen_behaelt_namen_und_freigabe():
    z = name_setzen(freigabe_setzen(tuer_zu(leer(), 0, "N"), True), 0, "Archiv")
    neu = zuruecksetzen(z)
    assert neu["namen"][0] == "Archiv"
    assert neu["freigegeben"] is True
    assert neu["drehung"] == 0
    assert neu["tuer"] is None
    assert neu["historie"] == []


def test_leerer_name_faellt_auf_die_nummer_zurueck():
    assert name_setzen(leer(), 3, "   ")["namen"][3] == "4"


def test_name_wird_gekuerzt():
    assert len(name_setzen(leer(), 0, "a" * 40)["namen"][0]) == 16


def test_ungueltige_seite_und_raum():
    try:
        tuer_zu(leer(), 0, "X")
        raise AssertionError("seite")
    except ValueError:
        pass
    try:
        gruppe_setzen(leer(), 0, 8)
        raise AssertionError("raum")
    except ValueError:
        pass
    try:
        gruppe_setzen(leer(), 2, 0)
        raise AssertionError("index")
    except ValueError:
        pass


def test_spieler_sehen_ungefreigt_nichts_von_der_tafel():
    z = tuer_zu(name_setzen(leer(), 0, "Geheim"), 0, "N")
    assert fuer_draht(z, "PLAYER") == {"freigegeben": False}
    frei = freigabe_setzen(z, True)
    sicht = fuer_draht(frei, "PLAYER")
    assert sicht["namen"][0] == "Geheim"
    assert sicht["drehung"] == 1
    assert "historie" not in sicht
    assert sicht["kannZurueck"] is False


def test_sl_sieht_ob_zurueck_geht():
    assert fuer_draht(leer(), "GM")["kannZurueck"] is False
    assert fuer_draht(tuer_zu(leer(), 0, "N"), "GM")["kannZurueck"] is True


def test_raetsel_routen_sind_registriert():
    pfade = app.openapi()["paths"]
    basis = "/api/campaigns/{campaign_id}/raetsel"
    assert "get" in pfade[basis]
    assert "post" in pfade[basis + "/tuer"]
    assert "post" in pfade[basis + "/gruppe"]
    assert "post" in pfade[basis + "/name"]
    assert "post" in pfade[basis + "/freigabe"]
    assert "post" in pfade[basis + "/zurueck"]
    assert "post" in pfade[basis + "/zuruecksetzen"]
    assert "post" in pfade[basis + "/ausgang"]
    assert "post" in pfade[basis + "/modus"]


def test_ausgang_schaltet_aus_blau_rot_im_kreis_und_dreht_nicht():
    z = ausgang_setzen(leer(), 0, 0)
    assert z["ausgaenge"][0][0] == 1
    assert z["drehung"] == 0
    rot = ausgang_setzen(z, 0, 0)
    assert rot["ausgaenge"][0][0] == 2
    aus = ausgang_setzen(rot, 0, 0)
    assert aus["ausgaenge"][0][0] == 0


def test_ausgang_erlaubt_mehrere_markierungen_gleichzeitig():
    z = ausgang_setzen(ausgang_setzen(leer(), 0, 1), 0, 5)
    assert z["ausgaenge"][0][1] == 1
    assert z["ausgaenge"][0][5] == 1


def test_spieler_sehen_den_ausgang_nicht():
    z = freigabe_setzen(ausgang_setzen(leer(), 0, 4), True)
    assert fuer_draht(z, "PLAYER")["ausgaenge"] == [[0] * ANZAHL, [0] * ANZAHL]
    assert fuer_draht(z, "GM")["ausgaenge"][0][4] == 1


def test_mittel_wechselt_zuerst_die_ebene_dann_dreht():
    z = modus_setzen(leer(), "mittel")
    assert z["ringe"][0][0] == 0
    assert z["ringe"][1][0] == 8
    hoch = tuer_zu(z, 0, "N")
    assert hoch["ringe"][1][0] == 0
    assert hoch["ringe"][0][0] == 8
    assert hoch["takt"] == 1
    gedreht = tuer_zu(hoch, 0, "S")
    assert gedreht["ringe"][1][7] == 0
    assert gedreht["takt"] == 2
    assert fuer_draht(gedreht, "GM")["naechster"] == "ebene"


def test_modus_behaelt_namen_und_stellt_felder_neu():
    z = freigabe_setzen(name_setzen(tuer_zu(leer(), 0, "N"), 0, "Archiv"), True)
    z = ausgang_setzen(z, 0, 2)
    neu = modus_setzen(z, "mittel")
    assert neu["modus"] == "mittel"
    assert neu["namen"][0] == "Archiv"
    assert neu["freigegeben"] is True
    assert neu["ausgaenge"][0][2] == 1
    assert neu["drehung"] == 0
    assert neu["takt"] == 0
    assert neu["ringe"][0][0] == 0
    assert name_setzen(neu, 8, "Oben")["namen"][8] == "Oben"
