"""Cyber- und Bioware: Preis und Willenskraftverlust.

Regelblatt Zeilen 112-117. Die Kernaussage: je teurer je Bonuspunkt, desto
weniger reisst es heraus.
"""

import pytest

from app.items.chrom import (
    STUFEN,
    preis_fuer,
    stufen_uebersicht,
    verlust_fuer,
    verlust_genau,
    verlust_gesamt,
)


@pytest.mark.parametrize(
    "bonus,preis,erwartet",
    [
        # 500¥: Verlust = Bonus × 2
        (1, 500, 2),
        (3, 500, 6),
        # 2.000¥: Verlust = Bonus
        (1, 2_000, 1),
        (4, 2_000, 4),
        # 5.000¥: Bonus / 2
        (4, 5_000, 2),
        # 10.000¥: Bonus / 3
        (6, 10_000, 2),
        # 20.000¥: Bonus / 4
        (8, 20_000, 2),
    ],
)
def test_verlust_je_preisstufe(bonus, preis, erwartet):
    assert verlust_fuer(bonus, preis) == erwartet


@pytest.mark.parametrize(
    "bonus,preis,erwartet",
    [
        (2, 5_000, 1.0),
        (3, 5_000, 1.5),
        (2, 10_000, pytest.approx(0.667, abs=0.001)),
        (2, 20_000, 0.5),
        (3, 500, 6.0),
    ],
)
def test_einzelverlust_bleibt_ungerundet(bonus, preis, erwartet):
    """Ungerundet gespeichert, damit sich die Brüche später summieren können."""
    assert verlust_genau(bonus, preis) == erwartet


# --- Marks Regel vom 31.08.2026 ---------------------------------------


def test_ein_stueck_kostet_mindestens_einen_punkt():
    """0,67 allein ist trotzdem 1 — Chrom ist nie gratis."""
    assert verlust_gesamt([0.667]) == 1
    assert verlust_gesamt([0.25]) == 1


def test_zwei_teure_stuecke_kosten_zusammen_weiterhin_eins():
    """Marks Beispiel: 0,67 + 0,67 = 1,33 — abgerundet 1, nicht 2.

    Genau das macht teure Arbeit lohnend: würde jedes Stück für sich
    aufgerundet, käme zweimal 1 zusammen.
    """
    assert verlust_gesamt([0.667, 0.667]) == 1


def test_erst_die_summe_wird_abgerundet():
    assert verlust_gesamt([0.667, 0.667, 0.667]) == 2  # 2,0
    assert verlust_gesamt([0.5, 0.5, 0.5]) == 1  # 1,5 -> 1
    assert verlust_gesamt([0.5, 0.5, 0.5, 0.5]) == 2  # 2,0


def test_einzeln_gerundet_waere_teurer():
    """Der Vergleich, um den es Mark ging — als Test festgehalten."""
    stuecke = [0.667, 0.667]
    einzeln_gerundet = sum(max(1, int(w)) if w > 0 else 0 for w in stuecke)
    assert verlust_gesamt(stuecke) < einzeln_gerundet


def test_billiges_chrom_bleibt_teuer():
    """Die Regel schont nur, wo Brüche entstehen — 6 bleibt 6."""
    assert verlust_gesamt([6.0]) == 6
    assert verlust_gesamt([6.0, 0.667]) == 6


def test_ohne_chrom_kostet_nichts():
    assert verlust_gesamt([]) == 0
    assert verlust_gesamt([0.0, 0.0]) == 0


def test_bewusst_kostenloses_implantat_bleibt_kostenlos():
    """Ein rein kosmetisches Stück, das die Spielleitung auf 0 setzt."""
    assert verlust_gesamt([0.0]) == 0


def test_teureres_chrom_kostet_nie_mehr_willenskraft():
    """Die eigentliche Aussage der Regel — als Test festgehalten."""
    for bonus in range(1, 9):
        verluste = [verlust_genau(bonus, s.preis_je_bonus) for s in STUFEN]
        assert verluste == sorted(verluste, reverse=True), f"bei Bonus {bonus}: {verluste}"


def test_kein_bonus_kostet_nichts():
    assert verlust_fuer(0, 500) == 0
    assert verlust_fuer(-2, 500) == 0


def test_unbekannter_preis_faellt_auf_die_haerteste_stufe():
    """Lieber zu teuer veranschlagt als versehentlich gratis."""
    assert verlust_genau(2, 1_234) == verlust_genau(2, 500)


def test_preis_ist_bonus_mal_stufe():
    assert preis_fuer(3, 5_000) == 15_000
    assert preis_fuer(0, 5_000) == 0


def test_uebersicht_zeigt_alle_stufen_mit_zahlen():
    liste = stufen_uebersicht(bonus=2)
    assert len(liste) == len(STUFEN)
    assert liste[0]["wVerlustGenau"] > liste[-1]["wVerlustGenau"], "billig muss mehr kosten"
    assert liste[0]["preis"] < liste[-1]["preis"], "und dafür weniger Geld"
