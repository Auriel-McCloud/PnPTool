"""Reihenfolge im Kampf — die Regel, auf die es ankommt.

Regelblatt Zeile 57-58: Initiative = Geistesschärfe + Geschicklichkeit +
Cyberware, und bei Gleichstand handeln **Matrixnutzer vor Nahkämpfern vor
Fernkämpfern**.
"""

from app.kampf.repository import KAMPFART_RANG, sortiere


def t(name, initiative, kampfart="NAHKAMPF"):
    return {"name": name, "initiative": initiative, "kampfart": kampfart}


def namen(liste):
    return [x["name"] for x in sortiere(liste)]


def test_hohe_initiative_handelt_zuerst():
    assert namen([t("Langsam", 3), t("Schnell", 9), t("Mittel", 6)]) == ["Schnell", "Mittel", "Langsam"]


def test_bei_gleichstand_matrix_vor_nahkampf_vor_fernkampf():
    liste = [
        t("Schütze", 7, "FERNKAMPF"),
        t("Decker", 7, "MATRIX"),
        t("Klinge", 7, "NAHKAMPF"),
    ]
    assert namen(liste) == ["Decker", "Klinge", "Schütze"]


def test_initiative_schlaegt_kampfart():
    """Ein schneller Fernkämpfer kommt vor einem langsamen Decker."""
    liste = [t("Decker", 4, "MATRIX"), t("Schütze", 8, "FERNKAMPF")]
    assert namen(liste) == ["Schütze", "Decker"]


def test_gleichstand_in_allem_bleibt_stabil():
    """Sonst springt die Liste bei jedem Nachladen — mitten im Kampf ärgerlich."""
    liste = [t("Bravo", 5), t("Alpha", 5), t("Charlie", 5)]
    assert namen(liste) == ["Alpha", "Bravo", "Charlie"]
    assert namen(list(reversed(liste))) == ["Alpha", "Bravo", "Charlie"]


def test_unbekannte_kampfart_landet_hinten_statt_zu_scheitern():
    liste = [t("Seltsam", 5, "TANZEN"), t("Decker", 5, "MATRIX")]
    assert namen(liste) == ["Decker", "Seltsam"]


def test_rangfolge_ist_die_des_regelblatts():
    assert KAMPFART_RANG["MATRIX"] < KAMPFART_RANG["NAHKAMPF"] < KAMPFART_RANG["FERNKAMPF"]
