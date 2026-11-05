"""Drogen: Heilung, Umwandeln, Uhren, Gift. Ohne Datenbank."""

from app.items.drogen import (
    crash_auf_person,
    einnahme_aus_vorlage,
    gift_schaden,
    heilen,
    rast_danach,
    rast_vor_heilung,
    reduktion_dazu,
    starte_nebenwirkung,
    szene_wechseln,
    umwandeln,
    willenskraft_anwenden,
)


def test_minderwertig_heilt_nur_schlag():
    assert heilen(5, 2, 1, 3, "minderwertig") == {
        "schadenSchlag": 2, "schadenSchwer": 2, "schadenAggraviert": 1,
    }


def test_normal_toedlich_zuerst_rest_mal_drei():
    assert heilen(10, 2, 1, 4, "normal") == {
        "schadenSchlag": 4, "schadenSchwer": 0, "schadenAggraviert": 1,
    }


def test_normal_ohne_toedlich_ganze_menge_mal_drei():
    assert heilen(10, 0, 1, 2, "normal")["schadenSchlag"] == 4


def test_hochwertig_raeumt_leichte_und_gibt_menge_auf_schwerheilbar():
    assert heilen(4, 3, 5, 2, "hochwertig") == {
        "schadenSchlag": 0, "schadenSchwer": 0, "schadenAggraviert": 3,
    }


def test_umwandeln_verschiebt_ohne_zu_addieren():
    assert umwandeln(3, 1, 0, "schlagZuToedlich") == {
        "schadenSchlag": 0, "schadenSchwer": 4, "schadenAggraviert": 0,
    }
    assert umwandeln(2, 2, 1, "allesZuAggraviert") == {
        "schadenSchlag": 0, "schadenSchwer": 0, "schadenAggraviert": 5,
    }


def test_willenskraft_zurueck_und_weg():
    assert willenskraft_anwenden(3, 8, 2) == 1
    assert willenskraft_anwenden(1, 8, -4) == 5
    assert willenskraft_anwenden(0, 8, 3) == 0


def test_reduktion_addiert_auf_effektiv():
    assert reduktion_dazu(2, 3) == 5
    assert reduktion_dazu(0, 4) == 4


def test_crash_bei_rast_vor_der_heilung_und_rast_zaehlt():
    ein = einnahme_aus_vorlage({
        "name": "Dash",
        "wirkungDauer": "rast",
        "traitBoni": {"Geschicklichkeit": 2},
        "nebenwirkungBoni": {"Geschicklichkeit": -1},
    })
    bleiben, crash = rast_vor_heilung([ein])
    assert crash[0]["phase"] == "nebenwirkung"
    assert crash[0]["modus"] == "weitere-rast"
    person = crash_auf_person({"schadenSchlag": 4, "schadenSchwer": 0, "schadenAggraviert": 0}, {
        **crash[0], "umwandeln": "schlagZuToedlich", "schadenArt": "",
    })
    assert person["schadenSchlag"] == 0
    assert person["schadenSchwer"] == 4
    nach = rast_danach(bleiben)
    assert nach[0]["frisch"] is False
    weg = rast_danach(nach)
    assert weg == []


def test_nebenwirkung_schreibt_normalen_schaden():
    basis = {"schadenSchlag": 1, "schadenSchwer": 2, "schadenAggraviert": 0}
    toedlich = starte_nebenwirkung(einnahme_aus_vorlage({
        "wirkungDauer": "sofort",
        "nebenwirkungSchaden": "toedlich",
        "nebenwirkungSchadenMenge": 3,
    }))
    assert crash_auf_person(basis, toedlich)["schadenSchwer"] == 5
    assert toedlich["modus"] != "zwei-rasten"
    schlag = starte_nebenwirkung(einnahme_aus_vorlage({
        "wirkungDauer": "sofort",
        "nebenwirkungSchaden": "schlag",
        "nebenwirkungSchadenMenge": 2,
    }))
    assert crash_auf_person(basis, schlag)["schadenSchlag"] == 3
    schwerheilbar = starte_nebenwirkung(einnahme_aus_vorlage({
        "wirkungDauer": "sofort",
        "nebenwirkungSchaden": "aggraviert",
        "nebenwirkungSchadenMenge": 4,
    }))
    assert crash_auf_person(basis, schwerheilbar)["schadenAggraviert"] == 4


def test_szene_kippt_ohne_tick():
    ein = einnahme_aus_vorlage({
        "wirkungDauer": "szene",
        "traitBoni": {"Wahrnehmung": 1},
        "nebenwirkungBoni": {"Wahrnehmung": -1},
    })
    bleiben, crash = szene_wechseln([ein])
    assert crash[0]["phase"] == "nebenwirkung"
    assert crash[0]["toedlichTicks"] == 0
    assert bleiben[0]["traitBoni"] == {"Wahrnehmung": -1}


def test_gift_nur_waehrend_der_wirkung():
    ein = einnahme_aus_vorlage({
        "wirkungDauer": "szene",
        "giftMenge": 1,
        "giftArt": "schlag",
        "name": "Nadel",
    })
    assert gift_schaden([ein]) == [{"name": "Nadel", "art": "schlag", "menge": 1}]
    assert gift_schaden([starte_nebenwirkung(ein)]) == []


def test_sofort_schreibt_toedlich_einmal_auf_die_spur():
    ein = starte_nebenwirkung(einnahme_aus_vorlage({
        "wirkungDauer": "sofort",
        "nebenwirkungSchaden": "toedlich",
        "nebenwirkungSchadenMenge": 3,
    }))
    person = crash_auf_person(
        {"schadenSchlag": 1, "schadenSchwer": 2, "schadenAggraviert": 0}, ein,
    )
    assert person["schadenSchwer"] == 5
    assert ein.get("toedlich", 0) == 0
