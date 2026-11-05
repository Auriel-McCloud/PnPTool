from app.kampf.matrix import (
    aktiver_bonus,
    aufteilung_gueltig,
    ew_bonus,
    ew_setzen,
    ice_klemmen,
    ice_nach_treffer,
    navigation_trifft,
    netto,
    runde_auffuellen,
    treffer_art,
    ueberschuss,
    willenskraft_rest,
    zahl_sichtbar,
)


def test_netto_zieht_ice_ab_und_deckelt_bei_3():
    assert netto(6, 4) == 2
    assert netto(9, 1) == 3
    assert netto(4, 4) == 0
    assert netto(2, 0) == 2


def test_ueberschuss_ist_nicht_auf_3_gedeckelt():
    assert ueberschuss(9, 1) == 8
    assert ueberschuss(6, 4) == 2
    assert ueberschuss(4, 4) == 0
    assert willenskraft_rest(6, 2) == 4
    assert willenskraft_rest(3, 5) == 0


def test_ice_faellt_sofort_auf_das_maximum():
    assert ice_klemmen(None, 4) == 4
    assert ice_klemmen(6, 4) == 4
    assert ice_klemmen(2, 4) == 2
    assert ice_klemmen(0, 4) == 0


def test_neuroweaver_nimmt_schaden_hot_decker_hat_die_wahl():
    assert treffer_art("NEUROWEAVER", True) == "schaden"
    assert treffer_art("NEUROWEAVER", False) == "schaden"
    assert treffer_art("KEINER", True) == "wahl"
    assert treffer_art("KEINER", False) == "schalten"
    assert treffer_art("NEUROWEAVER", False, ist_drohne=True) == "schalten"
    assert treffer_art("KEINER", False, ist_drohne=True, ist_roboter=True) == "wahl"
    assert treffer_art("NEUROWEAVER", False, ist_roboter=True) == "wahl"
    assert treffer_art("KEINER", False, ist_drohne=True) == "schalten"


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


def test_konsole_gilt_als_abgefallen_wenn_der_eintrag_weg_ist():
    from app.kampf.matrix import abgefallene
    vorher = [{"id": "a", "art": "konsole", "gesprungeneIds": ["d1"]}, {"id": "b", "art": "waffe"}]
    assert abgefallene(vorher, [], "konsole") == [vorher[0]]
    assert abgefallene(vorher, vorher, "konsole") == []


def test_deaktiv_modus_default_nach_typ():
    from app.kampf.matrix import deaktiv_modus
    assert deaktiv_modus("", "Schusswaffen") == "komplett"
    assert deaktiv_modus("", "Nahkampf") == "upgrades"
    assert deaktiv_modus("upgrades", "Schusswaffen") == "upgrades"
    assert deaktiv_modus("komplett", "Handgemenge") == "komplett"
    assert deaktiv_modus("nicht", "Schusswaffen") == "nicht"
    assert deaktiv_modus("nicht", "Handgemenge") == "nicht"
    assert zahl_sichtbar(True, False)
    assert not zahl_sichtbar(False, False)
    assert zahl_sichtbar(False, True)
    assert navigation_trifft(1)
    assert not navigation_trifft(0)


def test_nicht_hackbar_faellt_aus_der_liste():
    from app.kampf.matrix import schalt_eintrag
    klaue = {"id": "k", "typ": "Waffe", "deaktivModus": "nicht", "kampfFertigkeit": "Handgemenge", "istAugment": False}
    assert schalt_eintrag(klaue) is None
    schuss = {"id": "s", "typ": "Waffe", "deaktivModus": "", "kampfFertigkeit": "Schusswaffen", "istAugment": False}
    assert schalt_eintrag(schuss)["art"] == "waffe"
    scope = {
        "id": "u", "typ": "Upgrade-Material", "istAugment": True,
        "zielDeaktivModus": "nicht", "zielKampfFertigkeit": "Handgemenge",
    }
    assert schalt_eintrag(scope) is None
    chip = {"id": "c", "typ": "Cyberware", "deaktivModus": "nicht", "kampfFertigkeit": "", "istAugment": False}
    assert schalt_eintrag(chip) is None
    arm = {"id": "a", "typ": "Cyberware", "deaktivModus": "", "kampfFertigkeit": "", "istAugment": False}
    assert schalt_eintrag(arm)["art"] == "cyber"
