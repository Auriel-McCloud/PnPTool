"""Tests für Waffen-/Rüstungs-/Drohnen-Augments (siehe app/items/augments.py
und docs/wiki/concepts/augments-ausruestung.md für die volle Herleitung)."""

from app.items.augments import (
    AUGMENT_TRAEGER_TYPEN,
    augment_level,
    benoetigte_erfolge_montage,
    kombiniere_zusatzaktionen,
    waffentyp_passt,
    wende_augment_boni_an,
    zieltyp_passt,
)
from app.kampf.ruestung import reparatur_benoetigte_erfolge, reparatur_heilung_material


class TestAugmentLevel:
    def test_summe_der_bonuspunkte(self):
        assert augment_level({"Schusswaffen": 1}) == 1
        assert augment_level({"Schusswaffen": 2, "Initiative": 1}) == 3

    def test_leeres_traitboni_ist_level_null(self):
        assert augment_level({}) == 0

    def test_negative_werte_zaehlen_nicht_negativ(self):
        # Sollte nie vorkommen (traitBoni sind Bonuswürfel), aber die Formel
        # bleibt robust statt einen negativen Level zuzulassen.
        assert augment_level({"X": -3}) == 0


class TestBenoetigteErfolgeMontage:
    """Mark, 29.10.2026: Level + 1 — Gegenstück zur Reparatur (Level - 1)."""

    def test_level_plus_eins(self):
        assert benoetigte_erfolge_montage(0) == 1
        assert benoetigte_erfolge_montage(3) == 4

    def test_marks_beispiel_zielfernrohr_plus_eins(self):
        assert benoetigte_erfolge_montage(1) == 2


class TestWaffentypPasst:
    def test_leerer_waffentyp_passt_auf_alles(self):
        assert waffentyp_passt("", "Schusswaffen") is True
        assert waffentyp_passt("", "") is True  # Rüstung/Drohne/Cyberdeck/Riggerkonsole

    def test_gesetzter_waffentyp_nur_bei_match(self):
        assert waffentyp_passt("Schusswaffen", "Schusswaffen") is True
        assert waffentyp_passt("Schusswaffen", "Nahkampf") is False
        assert waffentyp_passt("Schusswaffen", "") is False  # fällt an Rüstung/Drohne heraus


class TestAugmentReparaturWiederverwendetReparaturFormeln:
    """Mark, 29.10.2026: "die probe ist Level des Gegenstandes -1 zum
    reparieren" — dieselbe Funktion wie bei der normalen Werkbank-Reparatur,
    nur mit `level` statt Materialmenge aufgerufen."""

    def test_benoetigte_erfolge_ist_level_minus_eins(self):
        assert reparatur_benoetigte_erfolge(5) == 4  # Level 5 -> Probe gegen 4
        assert reparatur_benoetigte_erfolge(1) == 1  # Minimum bleibt 1

    def test_heilung_nutzt_level_als_fehlende_kaestchen(self):
        # Level 5 defektes Augment: 5 minderwertige Stücke reichen genau.
        assert reparatur_heilung_material("minderwertig", menge=5, fehlende_kaestchen=5) == 5
        # 1 hochwertiges Stück repariert immer vollständig.
        assert reparatur_heilung_material("hochwertig", menge=1, fehlende_kaestchen=5) == 5
        # 1 normales Stück deckt 5 Einheiten — reicht für Level <= 5 genau.
        assert reparatur_heilung_material("normal", menge=1, fehlende_kaestchen=5) == 5
        # Zu wenig Material: Level 6 mit nur 1 minderwertigem Stück reicht nicht.
        assert reparatur_heilung_material("minderwertig", menge=1, fehlende_kaestchen=6) == 1


class TestAugmentTraegerTypen:
    def test_enthaelt_waffe_ruestung_cyberdeck_riggerkonsole(self):
        assert AUGMENT_TRAEGER_TYPEN == {"Waffe", "Rüstung", "Cyberdeck", "Riggerkonsole"}


class TestZieltypPasst:
    """29.10.2026 Nachbesserung, Mark: 'ein zusätzliches Feld dafür, wenn es
    leer ist gilt es für alle, bei Auswahl z.B. nur für Decks'."""

    def test_leerer_zieltyp_passt_auf_alles(self):
        assert zieltyp_passt("", "Cyberdeck") is True
        assert zieltyp_passt("", "Waffe") is True
        assert zieltyp_passt("", "") is True  # Drohne/Fahrzeug (Person-Ziel, kein typ)

    def test_gesetzter_zieltyp_nur_bei_match(self):
        assert zieltyp_passt("Cyberdeck", "Cyberdeck") is True
        assert zieltyp_passt("Cyberdeck", "Riggerkonsole") is False
        assert zieltyp_passt("Cyberdeck", "") is False  # fällt an Drohne/Fahrzeug heraus


class TestKombiniereZusatzaktionen:
    """-1 ('jede Runde', Reflex-Booster Stufe 3) schlägt jede endliche Zahl."""

    def test_addiert_endliche_werte(self):
        assert kombiniere_zusatzaktionen(1, 1) == 2
        assert kombiniere_zusatzaktionen(0, 2) == 2

    def test_minus_eins_gewinnt_immer(self):
        assert kombiniere_zusatzaktionen(-1, 2) == -1
        assert kombiniere_zusatzaktionen(2, -1) == -1
        assert kombiniere_zusatzaktionen(-1, -1) == -1

    def test_negative_eingaben_ausser_sentinel_zaehlen_als_null(self):
        assert kombiniere_zusatzaktionen(0, 0) == 0


class TestWendeAugmentBoniAn:
    """items/repository.py::augment_boni_fuer_ziel liefert `boni` genau in
    dieser Form — hier nur die reine Anwendung auf ein geladenes Ziel."""

    def test_ohne_augment_bleibt_alles_gleich(self):
        basis = {"schaden": 3, "schadenArt": "schwer", "zusatzaktionen": 0}
        assert wende_augment_boni_an(basis, {}) == {
            "schaden": 3,
            "schadenArt": "schwer",
            "zusatzaktionen": 0,
            "ruestungReduktionBasis": 0,
            "ruestungKaestchenMax": 0,
            "initiativeBonus": 0,
        }

    def test_addiert_schaden_reduktion_kaestchen_initiative(self):
        basis = {"schaden": 3, "ruestungReduktionBasis": 2, "ruestungKaestchenMax": 5, "initiativeBonus": 0}
        boni = {"schaden": 2, "ruestungReduktionBasis": 1, "ruestungKaestchenMax": 3, "initiativeBonus": 3}
        ergebnis = wende_augment_boni_an(basis, boni)
        assert ergebnis["schaden"] == 5
        assert ergebnis["ruestungReduktionBasis"] == 3
        assert ergebnis["ruestungKaestchenMax"] == 8
        assert ergebnis["initiativeBonus"] == 3

    def test_schadenart_override_nur_wenn_gesetzt(self):
        basis = {"schadenArt": "schwer"}
        assert wende_augment_boni_an(basis, {"schadenArt": "aggraviert"})["schadenArt"] == "aggraviert"
        assert wende_augment_boni_an(basis, {"schadenArt": ""})["schadenArt"] == "schwer"
        assert wende_augment_boni_an(basis, {})["schadenArt"] == "schwer"

    def test_mutiert_basis_nicht(self):
        basis = {"schaden": 3}
        wende_augment_boni_an(basis, {"schaden": 5})
        assert basis["schaden"] == 3

    def test_reflexbooster_auf_deck_kombiniert_zusatzaktionen_mit_sentinel(self):
        # Deck hat selbst 1 Zusatzaktion, montiertes Reflexbooster-Stufe-3-
        # Augment gibt "jede Runde" (-1) — das Sentinel gewinnt.
        basis = {"zusatzaktionen": 1, "initiativeBonus": 0}
        ergebnis = wende_augment_boni_an(basis, {"zusatzaktionen": -1, "initiativeBonus": 6})
        assert ergebnis["zusatzaktionen"] == -1
        assert ergebnis["initiativeBonus"] == 6
