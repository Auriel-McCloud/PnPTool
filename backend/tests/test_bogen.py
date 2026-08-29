"""Tests der abgeleiteten Bogenwerte (docs/regeln-neotopia.md)."""

from app.traits.bogen import (
    bogen_uebersicht,
    gesundheit_max,
    ice_max,
    initiative,
    sichtbare_kategorien,
    willenskraft_max,
)

ALLE_KATEGORIEN = {
    "AttributKörperlich",
    "AttributGesellschaftlich",
    "AttributGeistig",
    "Fertigkeit",
    "NeuroWeaving",
    "Sphäre",
    "Arete",
}


class TestAbgeleiteteWerte:
    def test_gesundheit_ist_fuenf_plus_widerstand(self):
        assert gesundheit_max({"Widerstandsfähigkeit": 3}) == 8

    def test_gesundheit_ohne_gesetztes_attribut(self):
        """Ein frischer Charakter hat trotzdem die Grundgesundheit."""
        assert gesundheit_max({}) == 5

    def test_willenskraft_ist_entschlossenheit_plus_fassung(self):
        assert willenskraft_max({"Entschlossenheit": 3, "Fassung": 2}) == 5

    def test_initiative_zaehlt_cyberware_mit(self):
        werte = {"Geistesschärfe": 3, "Geschicklichkeit": 2}
        assert initiative(werte) == 5
        assert initiative(werte, cyberware_mod=2) == 7


class TestSichtbareBereiche:
    def test_ohne_weg_weder_sphaeren_noch_neuroweaving(self):
        sichtbar = sichtbare_kategorien("KEINER", ALLE_KATEGORIEN)
        assert "Sphäre" not in sichtbar
        assert "Arete" not in sichtbar
        assert "NeuroWeaving" not in sichtbar

    def test_magier_sieht_sphaeren_und_arete_aber_kein_neuroweaving(self):
        sichtbar = sichtbare_kategorien("MAGIER", ALLE_KATEGORIEN)
        assert {"Sphäre", "Arete"} <= sichtbar
        assert "NeuroWeaving" not in sichtbar

    def test_technomancer_sieht_neuroweaving_aber_keine_sphaeren(self):
        sichtbar = sichtbare_kategorien("TECHNOMANCER", ALLE_KATEGORIEN)
        assert "NeuroWeaving" in sichtbar
        assert "Sphäre" not in sichtbar
        assert "Arete" not in sichtbar

    def test_attribute_und_fertigkeiten_hat_jeder(self):
        for weg in ("KEINER", "MAGIER", "TECHNOMANCER"):
            sichtbar = sichtbare_kategorien(weg, ALLE_KATEGORIEN)
            assert "Fertigkeit" in sichtbar
            assert "AttributKörperlich" in sichtbar


class TestUebersicht:
    def test_schaden_kann_das_maximum_nicht_ueberschreiten(self):
        """Sinkt ein Attribut, darf der Schaden nicht über die Grenze ragen."""
        person = {"gesundheitSchaden": 99, "willenskraftVerbraucht": 99}
        u = bogen_uebersicht(person, {"Widerstandsfähigkeit": 2, "Entschlossenheit": 1, "Fassung": 1})
        assert u["gesundheitSchaden"] == u["gesundheitMax"] == 7
        assert u["willenskraftVerbraucht"] == u["willenskraftMax"] == 2

    def test_verfuegbare_erfahrung_ist_gesamt_minus_ausgegeben(self):
        u = bogen_uebersicht({"erfahrung": 20, "erfahrungAusgegeben": 8}, {})
        assert u["erfahrungGesamt"] == 20
        assert u["erfahrungVerfuegbar"] == 12

    def test_ueberzogene_erfahrung_wird_nicht_negativ(self):
        u = bogen_uebersicht({"erfahrung": 5, "erfahrungAusgegeben": 9}, {})
        assert u["erfahrungVerfuegbar"] == 0

    def test_leere_person_ergibt_brauchbare_werte(self):
        u = bogen_uebersicht({}, {})
        assert u["weg"] == "KEINER"
        assert u["gesundheitMax"] == 5
        assert u["willenskraftMax"] == 0


class TestMatrixVerteidigung:
    """I.C.E. — beim Technomancer aus Attributen, sonst vom Gerät."""

    def test_technomancer_traegt_seine_abwehr_in_sich(self):
        werte = {"Fassung": 3, "Geistesschärfe": 4}
        # ohne jedes Geraet, trotzdem verteidigt
        assert ice_max("TECHNOMANCER", werte, commlink_cyberwall=0) == 7

    def test_technomancer_ignoriert_das_commlink(self):
        werte = {"Fassung": 2, "Geistesschärfe": 2}
        assert ice_max("TECHNOMANCER", werte, commlink_cyberwall=9) == 4

    def test_andere_bekommen_den_wert_vom_commlink(self):
        werte = {"Fassung": 5, "Geistesschärfe": 5}
        # Attribute helfen hier nicht — es zaehlt allein das Geraet
        assert ice_max("MAGIER", werte, commlink_cyberwall=3) == 3
        assert ice_max("KEINER", werte, commlink_cyberwall=0) == 0

    def test_ohne_commlink_gilt_man_als_offline(self):
        u = bogen_uebersicht({"weg": "KEINER"}, {}, commlink_cyberwall=0)
        assert u["offline"] is True
        assert u["iceMax"] == 0

    def test_mit_commlink_nicht_offline(self):
        u = bogen_uebersicht({"weg": "KEINER"}, {}, commlink_cyberwall=4)
        assert u["offline"] is False
        assert u["iceMax"] == 4

    def test_technomancer_ist_nie_offline(self):
        u = bogen_uebersicht({"weg": "TECHNOMANCER"}, {"Fassung": 2, "Geistesschärfe": 3}, commlink_cyberwall=0)
        assert u["offline"] is False
        assert u["iceMax"] == 5
