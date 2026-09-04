"""Initiative-Boni aus Cyberware (Reflex-Booster & Co.).

Regelblatt Zeile 57: *Initiative = Geistesschärfe + Geschicklichkeit +
CyberwareMod*. Der Reflex-Booster (Neotopia.xlsx, Blatt "Regeln", Zeilen
421-444) liefert diesen Modifikator:

* Stufe 1 (günstig, 5.000¥) — **Initiative +1**
* Stufe 2 (militärisch, 20.000¥) — **Initiative +3**
* Stufe 3 (Prototyp, 50.000¥) — **Initiative +6**

Zeile 174 kennt ausserdem "Dash" (Combat Speed): **Initiative +2 für 3
Runden** — deshalb ist der Bonus ein freies Feld am Gegenstand und keine
Reflex-Booster-Sonderregel.
"""

from app.items.initiative_bonus import initiative_bonus_von


def g(**kwargs) -> dict:
    """Ein Gegenstand mit sinnvollen Vorgaben."""
    basis = {
        "name": "Ding",
        "ablage": "AUSGERUESTET",
        "initiativeBonus": 0,
        "menge": 1,
    }
    basis.update(kwargs)
    return basis


class TestBonusSummieren:
    def test_ohne_gegenstaende_kein_bonus(self):
        assert initiative_bonus_von([]) == 0

    def test_gegenstand_ohne_bonus_zaehlt_nicht(self):
        assert initiative_bonus_von([g(name="Kaffeebecher")]) == 0

    def test_reflex_booster_stufe_eins(self):
        assert initiative_bonus_von([g(name="Reflex Booster", initiativeBonus=1)]) == 1

    def test_reflex_booster_stufe_drei(self):
        assert initiative_bonus_von([g(name="Reflex Booster", initiativeBonus=6)]) == 6

    def test_mehrere_boni_addieren_sich(self):
        # Reflex-Booster plus ein anderes Implantat.
        werte = [g(initiativeBonus=3), g(initiativeBonus=1)]
        assert initiative_bonus_von(werte) == 4

    def test_negativer_bonus_ist_moeglich(self):
        # Ein schlecht eingesetztes Implantat kann bremsen.
        assert initiative_bonus_von([g(initiativeBonus=-2)]) == -2


class TestNurAusgeruestet:
    def test_im_rucksack_wirkt_nicht(self):
        # Ein Booster in der Tasche beschleunigt niemanden.
        assert initiative_bonus_von([g(initiativeBonus=6, ablage="RUCKSACK")]) == 0

    def test_gelagert_wirkt_nicht(self):
        assert initiative_bonus_von([g(initiativeBonus=6, ablage="LAGER")]) == 0

    def test_nur_der_ausgeruestete_zaehlt(self):
        werte = [
            g(name="getragen", initiativeBonus=3, ablage="AUSGERUESTET"),
            g(name="dabei", initiativeBonus=6, ablage="RUCKSACK"),
        ]
        assert initiative_bonus_von(werte) == 3


class TestRobustheit:
    def test_fehlendes_feld_zaehlt_als_null(self):
        # Bestandsdaten kennen initiativeBonus nicht.
        assert initiative_bonus_von([{"name": "alt", "ablage": "AUSGERUESTET"}]) == 0

    def test_none_zaehlt_als_null(self):
        assert initiative_bonus_von([g(initiativeBonus=None)]) == 0

    def test_fehlende_ablage_gilt_nicht_als_ausgeruestet(self):
        # Fail-closed: lieber kein Bonus als ein erfundener.
        assert initiative_bonus_von([{"name": "x", "initiativeBonus": 5}]) == 0
