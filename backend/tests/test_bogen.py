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
    "Hexkraft",
}


class TestAbgeleiteteWerte:
    def test_gesundheit_ist_sechs_plus_widerstand(self):
        assert gesundheit_max({"Widerstandsfähigkeit": 3}) == 9

    def test_gesundheit_ohne_gesetztes_attribut(self):
        """Ein frischer Charakter hat trotzdem die Grundgesundheit."""
        assert gesundheit_max({}) == 6

    def test_natuerliches_maximum_ist_zwoelf(self):
        """Widerstandsfähigkeit geht bis 6 (traits/seed.py) — daraus die
        runde 12, wegen der der Grundwert von 5 auf 6 gehoben wurde."""
        assert gesundheit_max({"Widerstandsfähigkeit": 6}) == 12

    def test_personenspezifischer_grundwert_ueberschreibt_global(self):
        """Mark, 10.10.2026: eine Ratte/ein Rattenschwarm soll nicht die
        vollen 6 Standard-LP haben, sondern 2 (1 Grundwert + 1 Widerstand)."""
        assert gesundheit_max({"Widerstandsfähigkeit": 1}, grundwert=1) == 2

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
        assert "Hexkraft" not in sichtbar
        assert "NeuroWeaving" not in sichtbar

    def test_magier_sieht_sphaeren_und_hexkraft_aber_kein_neuroweaving(self):
        sichtbar = sichtbare_kategorien("MAGIER", ALLE_KATEGORIEN)
        assert {"Sphäre", "Hexkraft"} <= sichtbar
        assert "NeuroWeaving" not in sichtbar

    def test_neuroweaver_sieht_neuroweaving_aber_keine_sphaeren(self):
        sichtbar = sichtbare_kategorien("NEUROWEAVER", ALLE_KATEGORIEN)
        assert "NeuroWeaving" in sichtbar
        assert "Sphäre" not in sichtbar
        assert "Hexkraft" not in sichtbar

    def test_attribute_und_fertigkeiten_hat_jeder(self):
        for weg in ("KEINER", "MAGIER", "NEUROWEAVER"):
            sichtbar = sichtbare_kategorien(weg, ALLE_KATEGORIEN)
            assert "Fertigkeit" in sichtbar
            assert "AttributKörperlich" in sichtbar


class TestUebersicht:
    def test_schaden_kann_das_maximum_nicht_ueberschreiten(self):
        """Sinkt ein Attribut, darf der Schaden nicht über die Grenze ragen."""
        person = {"schadenSchlag": 99, "willenskraftVerbraucht": 99}
        u = bogen_uebersicht(person, {"Widerstandsfähigkeit": 2, "Entschlossenheit": 1, "Fassung": 1})
        assert u["gesundheitSchaden"] == u["gesundheitMax"] == 8
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
        assert u["gesundheitMax"] == 6
        assert u["willenskraftMax"] == 0


class TestMatrixVerteidigung:
    """I.C.E. — beim Neuroweaver aus Attributen, sonst vom Gerät."""

    def test_neuroweaver_traegt_seine_abwehr_in_sich(self):
        werte = {"Fassung": 3, "Geistesschärfe": 4}
        # ohne jedes Geraet, trotzdem verteidigt
        assert ice_max("NEUROWEAVER", werte, commlink_cyberwall=0) == 7

    def test_neuroweaver_ignoriert_das_commlink(self):
        werte = {"Fassung": 2, "Geistesschärfe": 2}
        assert ice_max("NEUROWEAVER", werte, commlink_cyberwall=9) == 4

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

    def test_neuroweaver_ist_nie_offline(self):
        u = bogen_uebersicht({"weg": "NEUROWEAVER"}, {"Fassung": 2, "Geistesschärfe": 3}, commlink_cyberwall=0)
        assert u["offline"] is False
        assert u["iceMax"] == 5


class TestSchadensarten:
    """Drei Arten nach World of Darkness, schwerer verdraengt leichteren."""

    def test_arten_werden_getrennt_gezaehlt(self):
        u = bogen_uebersicht(
            {"schadenSchlag": 2, "schadenSchwer": 1, "schadenAggraviert": 1},
            {"Widerstandsfähigkeit": 3},
        )
        assert (u["schadenSchlag"], u["schadenSchwer"], u["schadenAggraviert"]) == (2, 1, 1)
        assert u["gesundheitSchaden"] == 4

    def test_ueberzaehliger_schaden_kuerzt_beim_leichtesten(self):
        """Bei 6 Kaestchen und 4+3+2 bleiben aggravierter und schwerer
        Schaden stehen, gekuerzt wird allein der Schlagschaden (4 -> 1)."""
        u = bogen_uebersicht(
            {"schadenSchlag": 4, "schadenSchwer": 3, "schadenAggraviert": 2},
            {},  # Gesundheit 6
        )
        assert u["gesundheitMax"] == 6
        assert u["schadenAggraviert"] == 2
        assert u["schadenSchwer"] == 3
        assert u["schadenSchlag"] == 1
        assert u["gesundheitSchaden"] == 6

    def test_aggravierter_schaden_allein_kann_voll_ausfuellen(self):
        u = bogen_uebersicht({"schadenAggraviert": 99}, {"Widerstandsfähigkeit": 1})
        assert u["schadenAggraviert"] == u["gesundheitMax"] == 7

    def test_negative_werte_werden_ignoriert(self):
        u = bogen_uebersicht({"schadenSchlag": -3}, {})
        assert u["schadenSchlag"] == 0


class TestPflanzenVokabular:
    """Flora & Fauna (06.10.2026): rein kosmetisches Flag, siehe schemas.py."""

    def test_default_ist_false_fuer_bestandscharaktere(self):
        u = bogen_uebersicht({}, {})
        assert u["istPflanzenCritter"] is False

    def test_wird_aus_der_person_uebernommen(self):
        u = bogen_uebersicht({"istPflanzenCritter": True}, {})
        assert u["istPflanzenCritter"] is True


class TestLebenspunkteGrundwert:
    """Personenspezifischer Grundwert (10.10.2026) — siehe Marks Ratten-Beispiel."""

    def test_ohne_override_gilt_der_globale_standard(self):
        u = bogen_uebersicht({}, {"Widerstandsfähigkeit": 2})
        assert u["gesundheitGrundwert"] == 6
        assert u["gesundheitMax"] == 8

    def test_sentinel_minus_eins_gilt_als_kein_override(self):
        """-1 kommt aus entities/repository.py::_BOGEN_DEFAULTS für
        Bestandsdaten ohne das Feld — muss wie None behandelt werden."""
        u = bogen_uebersicht({"gesundheitGrundwert": -1}, {"Widerstandsfähigkeit": 2})
        assert u["gesundheitGrundwert"] == 6
        assert u["gesundheitMax"] == 8

    def test_rattenschwarm_hat_nur_zwei_lebenspunkte(self):
        u = bogen_uebersicht(
            {"gesundheitGrundwert": 1},
            {"Widerstandsfähigkeit": 1},
        )
        assert u["gesundheitGrundwert"] == 1
        assert u["gesundheitMax"] == 2

    def test_grundwert_null_ist_gueltig_und_wird_nicht_ersetzt(self):
        u = bogen_uebersicht({"gesundheitGrundwert": 0}, {"Widerstandsfähigkeit": 1})
        assert u["gesundheitGrundwert"] == 0
        assert u["gesundheitMax"] == 1


class TestDrohneFahrzeug:
    """Eigenes Blatt (25.10.2026) — siehe docs/wiki/concepts/drohnen-fahrzeuge.md."""

    ALLE_MIT_DROHNE = ALLE_KATEGORIEN | {"AttributDrohne", "AttributDrohneAussenhuelle"}

    def test_sichtbare_kategorien_nur_drohne_und_fertigkeit(self):
        sichtbar = sichtbare_kategorien("KEINER", self.ALLE_MIT_DROHNE, ist_drohne=True)
        assert sichtbar == {"AttributDrohne", "AttributDrohneAussenhuelle", "Fertigkeit"}

    def test_mensch_sieht_keine_drohnen_attribute(self):
        sichtbar = sichtbare_kategorien("KEINER", self.ALLE_MIT_DROHNE)
        assert "AttributDrohne" not in sichtbar
        assert "AttributDrohneAussenhuelle" not in sichtbar
        assert "AttributKörperlich" in sichtbar

    def test_initiative_ist_geschwindigkeit_plus_cpu(self):
        werte = {"Geschwindigkeit": 3, "CPU": 2, "Geistesschärfe": 99, "Geschicklichkeit": 99}
        assert initiative(werte, ist_drohne=True) == 5
        assert initiative(werte, cyberware_mod=1, ist_drohne=True) == 6

    def test_ice_ist_eigenes_attribut_nicht_abgeleitet(self):
        werte = {"I.C.E.": 4, "Fassung": 99, "Geistesschärfe": 99}
        assert ice_max("KEINER", werte, commlink_cyberwall=0, ist_drohne=True) == 4
        # Commlink/Neuroweaver-Formel darf nicht mitspielen, selbst wenn
        # beide Felder zufällig gesetzt wären.
        assert ice_max("NEUROWEAVER", werte, commlink_cyberwall=9, ist_drohne=True) == 4

    def test_bogen_uebersicht_erkennt_istdrohne_und_istfahrzeug(self):
        u_drohne = bogen_uebersicht(
            {"istDrohne": True}, {"Geschwindigkeit": 2, "CPU": 3, "I.C.E.": 1}
        )
        assert u_drohne["initiative"] == 5
        assert u_drohne["iceMax"] == 1
        assert u_drohne["istDrohne"] is True

        u_fahrzeug = bogen_uebersicht(
            {"istFahrzeug": True}, {"Geschwindigkeit": 4, "CPU": 1, "I.C.E.": 2}
        )
        assert u_fahrzeug["initiative"] == 5
        assert u_fahrzeug["istFahrzeug"] is True

    def test_drohne_ist_nie_offline_auch_ohne_commlink(self):
        """Bugfix (26.10.2026): Mark meldete, I.C.E. werde trotz gesetzter
        Punkte nicht angezeigt. Ursache: `offline` prüfte unabhängig von
        `ist_drohne` nur `commlink_cyberwall` — eine Drohne hat aber nie ein
        Commlink (ihr I.C.E. ist ein direkt gekauftes Attribut, siehe
        `ice_max`), zeigte also IMMER "offline" statt der Kästchenreihe."""
        u = bogen_uebersicht({"istDrohne": True}, {"I.C.E.": 3}, commlink_cyberwall=0)
        assert u["iceMax"] == 3
        assert u["offline"] is False

    def test_mensch_ohne_commlink_bleibt_offline(self):
        """Gegenprobe: die Drohnen-Ausnahme darf Menschen nicht mitreissen."""
        u = bogen_uebersicht({}, {}, commlink_cyberwall=0)
        assert u["offline"] is True

    def test_gesundheit_nutzt_denselben_grundwert_mechanismus(self):
        """Kein neues System nötig — ein Raumschiff bekommt einfach einen
        hohen Grundwert, siehe Wiki-Seite."""
        u = bogen_uebersicht(
            {"istFahrzeug": True, "gesundheitGrundwert": 40},
            {"Widerstandsfähigkeit": 5},
        )
        assert u["gesundheitMax"] == 45
