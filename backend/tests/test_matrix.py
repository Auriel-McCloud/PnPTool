from app.kampf.matrix import (
    aktiver_bonus,
    aufteilung_gueltig,
    ew_bonus,
    ew_setzen,
    ice_nach_treffer,
    navigation_trifft,
    netto,
    runde_auffuellen,
    zahl_sichtbar,
)


def test_netto_zieht_ice_ab_und_deckelt_bei_3():
    assert netto(6, 4) == 2
    assert netto(9, 1) == 3
    assert netto(4, 4) == 0
    assert netto(2, 0) == 2


def test_ice_nimmt_1_zu_1_schaden():
    assert ice_nach_treffer(4, 3) == 1
    assert ice_nach_treffer(4, 6) == 0
    assert ice_nach_treffer(0, 2) == 0


def test_ew_plus_1_je_2_erfolge():
    assert ew_bonus(1) == 0
    assert ew_bonus(2) == 1
    assert ew_bonus(5) == 2
    assert ew_bonus(8) == 4


def test_aufteilung_mischt_ziele_und_runden():
    assert aufteilung_gueltig(2, [2])
    assert aufteilung_gueltig(2, [1, 1])
    assert aufteilung_gueltig(3, [2, 1])
    assert not aufteilung_gueltig(2, [2, 1])
    assert not aufteilung_gueltig(3, [4])
    assert aufteilung_gueltig(3, [])


def test_ew_haelt_drei_runden_und_fuellt_mit():
    ew = ew_setzen({}, ["a", "b"], 2, runde=5)
    assert aktiver_bonus(ew, "a", 5) == 2
    assert aktiver_bonus(ew, "a", 7) == 2
    assert aktiver_bonus(ew, "a", 8) == 0
    stand = runde_auffuellen(
        {"ice": {"a": 0}, "ew": ew, "gesehen": {}, "aus": [{"runden": 2, "zielId": "z"}]},
        neue_runde=6,
        maxima={"a": 4},
    )
    assert stand["ice"]["a"] == 6
    assert stand["aus"][0]["runden"] == 1


def test_runde_8_laesst_den_bonus_fallen():
    ew = ew_setzen({}, ["a"], 2, runde=5)
    stand = runde_auffuellen(
        {"ice": {}, "ew": ew, "gesehen": {"ich": ["feind"]}, "aus": [{"runden": 1}]},
        neue_runde=8,
        maxima={"a": 4},
    )
    assert stand["ice"]["a"] == 4
    assert stand["ew"] == {}
    assert stand["aus"] == []
    assert stand["gesehen"]["ich"] == ["feind"]


def test_party_sieht_ice_gegner_nur_nach_probe():
    assert zahl_sichtbar(True, False)
    assert not zahl_sichtbar(False, False)
    assert zahl_sichtbar(False, True)
    assert navigation_trifft(1)
    assert not navigation_trifft(0)
