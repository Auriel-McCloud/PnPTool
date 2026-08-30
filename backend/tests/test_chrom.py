"""Cyber- und Bioware: Preis und Willenskraftverlust.

Regelblatt Zeilen 112-117. Die Kernaussage: je teurer je Bonuspunkt, desto
weniger reisst es heraus.
"""

import pytest

from app.items.chrom import STUFEN, preis_fuer, stufen_uebersicht, verlust_fuer


@pytest.mark.parametrize(
    "bonus,preis,erwartet",
    [
        # 500¥: Verlust = Bonus × 2
        (1, 500, 2),
        (3, 500, 6),
        # 2.000¥: Verlust = Bonus
        (1, 2_000, 1),
        (4, 2_000, 4),
        # 5.000¥: Bonus / 2, abgerundet
        (2, 5_000, 1),
        (3, 5_000, 1),
        (4, 5_000, 2),
        # 10.000¥: Bonus / 3, abgerundet
        (3, 10_000, 1),
        (5, 10_000, 1),
        (6, 10_000, 2),
        # 20.000¥: Bonus / 4, abgerundet
        (4, 20_000, 1),
        (7, 20_000, 1),
        (8, 20_000, 2),
    ],
)
def test_verlust_je_preisstufe(bonus, preis, erwartet):
    assert verlust_fuer(bonus, preis) == erwartet


def test_teureres_chrom_kostet_nie_mehr_willenskraft():
    """Die eigentliche Aussage der Regel — als Test festgehalten."""
    for bonus in range(1, 9):
        verluste = [verlust_fuer(bonus, s.preis_je_bonus) for s in STUFEN]
        assert verluste == sorted(verluste, reverse=True), f"bei Bonus {bonus}: {verluste}"


def test_kein_bonus_kostet_nichts():
    assert verlust_fuer(0, 500) == 0
    assert verlust_fuer(-2, 500) == 0


def test_unbekannter_preis_faellt_auf_die_haerteste_stufe():
    """Lieber zu teuer veranschlagt als versehentlich gratis."""
    assert verlust_fuer(2, 1_234) == verlust_fuer(2, 500)


def test_preis_ist_bonus_mal_stufe():
    assert preis_fuer(3, 5_000) == 15_000
    assert preis_fuer(0, 5_000) == 0


def test_uebersicht_zeigt_alle_stufen_mit_zahlen():
    liste = stufen_uebersicht(bonus=2)
    assert len(liste) == len(STUFEN)
    assert liste[0]["wVerlust"] > liste[-1]["wVerlust"], "billig muss mehr kosten"
    assert liste[0]["preis"] < liste[-1]["preis"], "und dafür weniger Geld"
