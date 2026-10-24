"""Rassen-Feature gratisErsterKaufTyp: Typ-Treffer, inkl. Sentinel „alle Typen“.

Das Einmal-Flag (`rassenFeatureGenutzt`) sitzt in der Kauf-Route, nicht hier.
Diese Funktion sagt nur, ob DIESER Gegenstand den Gratis-Kauf auslösen würde.
"""

from app.items.schemas import GEGENSTAND_TYPEN
from app.rassen.gratis_kauf import ALLE_TYPEN, trifft


def test_leeres_feature_trifft_nicht():
    assert not trifft("", "Hexware")
    assert not trifft(None, "Waffe")


def test_passender_typ():
    assert trifft("Hexware", "Hexware")


def test_fremder_typ():
    assert not trifft("Hexware", "Waffe")


def test_alle_typen_trifft_jeden_typ_genau_einmal_pro_aufruf():
    assert trifft(ALLE_TYPEN, "Waffe")
    assert trifft(ALLE_TYPEN, "Hexware")
    assert trifft(ALLE_TYPEN, "Sonstiges")
    # Auch ohne gesetzten Typ — der Sentinel meint jeden Kauf, nicht jede Kategorie.
    assert trifft(ALLE_TYPEN, "")
    assert trifft(ALLE_TYPEN, None)


def test_sentinel_kollidiert_nicht_mit_einem_echten_typ():
    assert ALLE_TYPEN not in GEGENSTAND_TYPEN
