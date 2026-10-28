"""Hot-Gehen: Neurolink, eine Drohne pro Runde, Deck nur eingeklinkt.

Mark, 28.10.2026 (docs/wiki/concepts/drohnen-fahrzeuge.md):
Neurolink ist verbaute Cyberware dieses Namens, Bonus 1, keine Extrakennzahl.
Der Decker bekommt die Zusatzaktionen seines Decks erst nach dem Hot-Knopf,
dieselbe Ampel wie der Reflex-Booster. Der Rigger wählt pro Runde eine Drohne;
die teilt seinen Initiative-Slot, ihr Name steht neben seinem.
"""

from app.kampf.hot import (
    anzeige_name,
    bleiben_faellig,
    booster_kandidaten,
    darf_drohne_waehlen,
    falte_hot,
    hat_neurolink,
    ist_neurolink,
    schneller,
    waehle_drohne,
    beantworte_bleiben,
    hot_rueckschlag,
    hot_anpassung,
)


def test_nur_angekreuzte_verbaute_cyberware_ist_ein_neurolink():
    assert ist_neurolink("Cyberware", True, True)
    assert not ist_neurolink("Cyberware", True, False)
    assert not ist_neurolink("Cyberware", False, True)
    assert not ist_neurolink("Bioware", True, True)
    assert hat_neurolink([{"typ": "Cyberware", "verbaut": True, "istNeurolink": False}]) is False
    assert hat_neurolink([{"name": "Datenbuchse", "typ": "Cyberware", "verbaut": True, "istNeurolink": True}]) is True


def test_deck_zusatzaktionen_zaehlen_nur_wenn_hot():
    deck = {"name": "Mikrodeck", "zusatzaktionen": -1}
    assert booster_kandidaten([], deck, matrix_hot=False) == []
    assert booster_kandidaten([], deck, matrix_hot=True) == [deck]
    chrom = [{"name": "Reflex", "zusatzaktionen": 1}]
    kandidaten = booster_kandidaten(chrom, deck, matrix_hot=True)
    assert {k["name"] for k in kandidaten} == {"Reflex", "Mikrodeck"}


def test_pro_runde_nur_eine_drohne():
    assert darf_drohne_waehlen(None, 0, kampf_runde=2) is True
    assert darf_drohne_waehlen("spinne", 2, kampf_runde=2) is False
    # Noch heiß aus der Vorrunde, die Bleiben-Frage ist offen: kein Wechsel.
    assert darf_drohne_waehlen("spinne", 1, kampf_runde=2) is False
    # Außerhalb eines Kampfes kein Runden-Deckel.
    assert darf_drohne_waehlen("spinne", 1, kampf_runde=None) is True


def test_ohne_neurolink_kein_hot():
    ergebnis = waehle_drohne(
        hat_neurolink=False,
        hot_drohne_id=None,
        hot_runde=0,
        kampf_runde=1,
        drohne_id="spinne",
    )
    assert ergebnis.ok is False
    assert ergebnis.hot_drohne_id is None


def test_wahl_merkt_sich_die_runde():
    ergebnis = waehle_drohne(
        hat_neurolink=True,
        hot_drohne_id=None,
        hot_runde=0,
        kampf_runde=3,
        drohne_id="spinne",
    )
    assert ergebnis.ok is True
    assert ergebnis.hot_drohne_id == "spinne"
    assert ergebnis.hot_runde == 3


def test_bleiben_ja_behält_die_drohne_nein_klinkt_aus():
    ja = beantworte_bleiben(True, "spinne", kampf_runde=4)
    assert ja.hot_drohne_id == "spinne"
    assert ja.hot_runde == 4
    nein = beantworte_bleiben(False, "spinne", kampf_runde=4)
    assert nein.hot_drohne_id is None
    assert nein.hot_runde == 4
    assert darf_drohne_waehlen(nein.hot_drohne_id, nein.hot_runde, 4) is False


def test_bleiben_nur_wenn_er_dran_ist_und_die_wahl_aus_der_vorrunde_stammt():
    assert bleiben_faellig("spinne", 1, kampf_runde=2, ist_dran=True) is True
    assert bleiben_faellig("spinne", 2, kampf_runde=2, ist_dran=True) is False
    assert bleiben_faellig("spinne", 1, kampf_runde=2, ist_dran=False) is False
    assert bleiben_faellig(None, 1, kampf_runde=2, ist_dran=True) is False


def test_hot_drohne_teilt_den_slot_und_verschwindet_als_eigene_zeile():
    rigger = {"id": "t-r", "personId": "rigger", "name": "Kess", "initiative": 4, "zusatzzug": False}
    drohne = {"id": "t-d", "personId": "spinne", "name": "Spinne", "initiative": 9, "zusatzzug": False}
    andere = {"id": "t-a", "personId": "kaefer", "name": "Käfer", "initiative": 3, "zusatzzug": False}
    gefaltet = falte_hot(
        [rigger, drohne, andere],
        {"rigger": ("spinne", "Spinne")},
    )
    ids = [t["id"] for t in gefaltet]
    assert "t-d" not in ids
    assert "t-a" in ids
    zeile = next(t for t in gefaltet if t["id"] == "t-r")
    assert zeile["name"] == anzeige_name("Kess", "Spinne")
    assert zeile["initiative"] == schneller(4, 9)
    assert "magenta" not in zeile


def test_hot_rueckschlag_ist_halber_schlagschaden_aufgerundet():
    assert hot_rueckschlag(0) == 0
    assert hot_rueckschlag(1) == 1
    assert hot_rueckschlag(2) == 1
    assert hot_rueckschlag(3) == 2
    assert hot_rueckschlag(5) == 3


def test_hot_geschick_addiert_riggen_bis_zum_konsolenbonus():
    drohne = {"Geschick": 3, "Fahren": 2, "Stärke": 4}
    rigger = {"Riggen": 6, "Fahren": 5, "Intelligenz": 4, "Geistesschärfe": 3}
    assert hot_anpassung(drohne, rigger, 2)["Geschick"] == 5
    assert hot_anpassung(drohne, rigger, 6)["Geschick"] == 9
    assert hot_anpassung(drohne, rigger, 0).get("Geschick", 3) == 3
    assert hot_anpassung(drohne, rigger, -2).get("Geschick", 3) == 3
    assert hot_anpassung(drohne, rigger, 6)["Stärke"] == 4 if "Stärke" in hot_anpassung(drohne, rigger, 6) else True
    assert "Stärke" not in hot_anpassung(drohne, rigger, 6)


def test_hot_fahren_und_fliegen_nehmen_den_besseren():
    drohne = {"Fahren": 2}
    rigger = {"Fahren": 5, "Riggen": 0}
    assert hot_anpassung(drohne, rigger, 0, rigger_zusatz={"Fliegen": 4}, drohne_zusatz={"Fliegen": 1})["Fahren"] == 5
    assert hot_anpassung(drohne, rigger, 0, rigger_zusatz={"Fliegen": 4}, drohne_zusatz={"Fliegen": 1})["Fliegen"] == 4
    gleich = hot_anpassung({"Fahren": 6}, {"Fahren": 2, "Riggen": 0}, 0)
    assert gleich.get("Fahren", 6) == 6


def test_hot_intelligenz_und_geistesschaerfe_kommen_vom_rigger():
    angepasst = hot_anpassung({}, {"Intelligenz": 4, "Geistesschärfe": 2, "Riggen": 0}, 0)
    assert angepasst["Intelligenz"] == 4
    assert angepasst["Geistesschärfe"] == 2


def test_hot_zusatz_fliegen_nimmt_den_besseren_und_borgt_ihn_wenn_die_drohne_ihn_nicht_hat():
    from app.kampf.hot import zusatz_mit_hot

    gehoben = zusatz_mit_hot(
        [{"id": "d", "name": "Fliegen", "rating": 1}],
        [{"id": "r", "name": "Fliegen", "rating": 4}],
        4,
    )
    assert gehoben[0]["rating"] == 4
    assert gehoben[0]["hotNurAnzeige"] is True
    assert gehoben[0]["id"] == "d"

    geborgt = zusatz_mit_hot(
        [{"id": "d", "name": "Schleichen", "rating": 2}],
        [{"id": "r", "name": "Fliegen", "rating": 4, "kurzbeschreibung": "x"}],
        4,
    )
    assert geborgt[-1]["name"] == "Fliegen"
    assert geborgt[-1]["rating"] == 4
    assert geborgt[0]["rating"] == 2


def test_hot_werte_legen_fahren_drauf_auch_wenn_die_drohne_keinen_eintrag_hat():
    from app.kampf.hot import werte_mit_hot

    katalog = [{"id": "f", "name": "Fahren", "category": "Fertigkeit", "defaultMax": 6}]
    werte, _extra = werte_mit_hot([], katalog, {"Fahren": 5, "Intelligenz": 0, "Geistesschärfe": 0})
    fahren = next(w for w in werte if w["name"] == "Fahren")
    assert fahren["rating"] == 5
    assert fahren["hotNurAnzeige"] is True


def test_dumpshock_nur_wenn_die_hot_drohne_keine_gesundheit_mehr_hat():
    from app.kampf.hot import verbindung_bricht

    assert verbindung_bricht(0) is True
    assert verbindung_bricht(-1) is True
    assert verbindung_bricht(1) is False
