"""Was ein Spieler an seinem eigenen Zustand ändern darf.

Marks Regel vom 30.08.2026: Willenskraft ausgeben ja, zurückholen nein — sie
kehrt zurück, wenn die Spielleitung es sagt.
"""

from app.traits.bogen import zustand_verboten


def test_spieler_darf_willenskraft_ausgeben():
    assert zustand_verboten("PLAYER", {"willenskraftVerbraucht": 1}, {"willenskraftVerbraucht": 3}) is None


def test_spieler_darf_willenskraft_nicht_zurueckholen():
    grund = zustand_verboten("PLAYER", {"willenskraftVerbraucht": 3}, {"willenskraftVerbraucht": 1})
    assert grund and "Spielleitung" in grund


def test_gleich_bleibt_erlaubt():
    """Ein Formular schickt oft alle Felder mit, auch unveränderte."""
    assert zustand_verboten("PLAYER", {"willenskraftVerbraucht": 2}, {"willenskraftVerbraucht": 2}) is None


def test_spielleitung_darf_alles():
    assert zustand_verboten("GM", {"willenskraftVerbraucht": 5}, {"willenskraftVerbraucht": 0}) is None


def test_schaden_bleibt_in_beide_richtungen_offen():
    """Verletzungen heilen nach eigenen Regeln; Vertipper soll man richten können."""
    assert zustand_verboten("PLAYER", {"schadenSchlag": 4}, {"schadenSchlag": 0}) is None


def test_bestandsdaten_ohne_feld_stolpern_nicht():
    """Alte Personen kennen willenskraftVerbraucht nicht — dann gilt 0."""
    assert zustand_verboten("PLAYER", {}, {"willenskraftVerbraucht": 2}) is None
    assert zustand_verboten("PLAYER", {"willenskraftVerbraucht": None}, {"willenskraftVerbraucht": 1}) is None


def test_nicht_gesetzte_willenskraft_wird_ignoriert():
    assert zustand_verboten("PLAYER", {"willenskraftVerbraucht": 3}, {"schadenSchlag": 1}) is None
