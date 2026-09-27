"""Tests für den Charaktererstellungs-Berater (Karl-Klammer-Warnungen).

Reine Regelprüfung, keine Datenbank — wie test_erstellung.py.
"""

from app.traits import berater


def test_leere_werte_geben_keine_falschen_positiven_ausser_den_erwartbaren():
    """Ein komplett leerer Bogen ist der Extremfall aller Warnungen —
    kein Absturz, keine Doppelungen."""
    hinweise = berater.berate({}, weg="KEINER")
    codes = {h["code"] for h in hinweise}
    assert "KEIN_KAMPFWERT" in codes
    assert "KEINE_WAHRNEHMUNG" in codes
    assert "KEIN_SOZIALWERT" in codes
    assert "KEIN_WISSENSWERT" in codes
    assert "MAGIE_UEBERLADEN" not in codes  # kein Magie-Weg


def test_ausgewogener_charakter_bekommt_keine_warnungen():
    werte = {
        "Nahkampf": 2,
        "Wahrnehmung": 2,
        "Überzeugen": 2,
        "Technologie": 2,
        "Körperkraft": 2,
        "Charisma": 2,
        "Intelligenz": 2,
    }
    hinweise = berater.berate(
        werte,
        weg="KEINER",
        attribut_kategorien={
            "AttributKörperlich": ["Körperkraft"],
            "AttributGesellschaftlich": ["Charisma"],
            "AttributGeistig": ["Intelligenz"],
        },
    )
    assert hinweise == []


def test_kein_kampfwert_erkennt_alle_kampfnahen_fertigkeiten():
    # Nur Riggen gesetzt reicht schon, damit die Warnung ausbleibt.
    hinweise = berater.berate({"Riggen": 3}, weg="KEINER")
    assert "KEIN_KAMPFWERT" not in {h["code"] for h in hinweise}


def test_wahrnehmung_null_triggert_eigene_warnung():
    hinweise = berater.berate({"Wahrnehmung": 0, "Nahkampf": 2}, weg="KEINER")
    assert "KEINE_WAHRNEHMUNG" in {h["code"] for h in hinweise}
    hinweise = berater.berate({"Wahrnehmung": 1, "Nahkampf": 2}, weg="KEINER")
    assert "KEINE_WAHRNEHMUNG" not in {h["code"] for h in hinweise}


def test_attribute_schief_braucht_mindestabstand_von_fuenf():
    kategorien = {
        "AttributKörperlich": ["Körperkraft"],
        "AttributGesellschaftlich": ["Charisma"],
        "AttributGeistig": ["Intelligenz"],
    }
    # Abstand 4 — noch keine Warnung.
    knapp = berater.berate(
        {"Körperkraft": 1, "Charisma": 3, "Intelligenz": 5},
        weg="KEINER",
        attribut_kategorien=kategorien,
    )
    assert "ATTRIBUTE_SCHIEF" not in {h["code"] for h in knapp}
    # Abstand 5 — jetzt schon.
    schief = berater.berate(
        {"Körperkraft": 1, "Charisma": 3, "Intelligenz": 6},
        weg="KEINER",
        attribut_kategorien=kategorien,
    )
    assert "ATTRIBUTE_SCHIEF" in {h["code"] for h in schief}


def test_magie_ueberladen_nur_ab_schwelle_und_nur_fuer_magie_wege():
    sphaeren_hoch = {"Kräfte": 6, "Leben": 5}  # Summe 11 > Schwelle 10
    # KEINER hat gar keine Sphären — keine Warnung, unabhängig von der Zahl.
    assert "MAGIE_UEBERLADEN" not in {h["code"] for h in berater.berate(sphaeren_hoch, weg="KEINER")}
    # MAGIER mit derselben Summe: Warnung.
    assert "MAGIE_UEBERLADEN" in {h["code"] for h in berater.berate(sphaeren_hoch, weg="MAGIER")}
    # Knapp unter der Schwelle: keine Warnung.
    knapp = {"Kräfte": 5, "Leben": 5}  # Summe genau 10
    assert "MAGIE_UEBERLADEN" not in {h["code"] for h in berater.berate(knapp, weg="MAGIER")}


def test_magie_ueberladen_gilt_auch_fuer_neuroweaver_mit_eigenem_begriff():
    hoch = {"Brute Force": 6, "Schleichen": 6}  # Summe 12
    hinweise = berater.berate(hoch, weg="NEUROWEAVER")
    treffer = next(h for h in hinweise if h["code"] == "MAGIE_UEBERLADEN")
    assert "NeuroWeaving-Fertigkeiten" in treffer["text"]


# --- kommentar_daten (KI-Abschlussbericht, 27.09.2026) ------------------

_ATTRIBUT_KATEGORIEN = [
    {"name": "Körperlich", "attribute": ["Körperkraft", "Geschicklichkeit"]},
    {"name": "Gesellschaftlich", "attribute": ["Charisma"]},
    {"name": "Geistig", "attribute": ["Intelligenz"]},
]


def test_kommentar_daten_summiert_attribute_und_top_fertigkeiten():
    werte = {
        "Körperkraft": 4, "Geschicklichkeit": 2, "Charisma": 1, "Intelligenz": 3,
        "Nahkampf": 3, "Wahrnehmung": 1,
    }
    daten = berater.kommentar_daten(werte, "KEINER", _ATTRIBUT_KATEGORIEN)
    assert daten["attribut_summen"] == {"Körperlich": 6, "Gesellschaftlich": 1, "Geistig": 3}
    assert "Nahkampf 3" in daten["top_fertigkeiten"]
    assert daten["magie_label"] is None
    assert daten["magie_wert"] is None
    assert daten["weg_anzeige"] == "Weg des Chroms"


def test_kommentar_daten_zeigt_magiewert_und_flavor():
    werte = {"Hexkraft": 4, "Kräfte": 3}
    magier = berater.kommentar_daten(werte, "MAGIER", _ATTRIBUT_KATEGORIEN, magie_flavor="MAGIER")
    assert magier["magie_label"] == "Hexkraft"
    assert magier["magie_wert"] == 4
    assert magier["weg_anzeige"] == "Magier"

    haeretiker = berater.kommentar_daten(werte, "MAGIER", _ATTRIBUT_KATEGORIEN, magie_flavor="HAERETIKER")
    assert haeretiker["magie_label"] == "Glauben"
    assert haeretiker["weg_anzeige"] == "Häretiker"


def test_kommentar_daten_schliesst_magiewerte_aus_den_fertigkeiten_aus():
    """Hexkraft/Sphären tauchen nur in magie_label/magie_wert auf, nicht
    nochmal als normale Fertigkeit in top_fertigkeiten."""
    werte = {"Hexkraft": 4, "Kräfte": 5, "Nahkampf": 2}
    daten = berater.kommentar_daten(werte, "MAGIER", _ATTRIBUT_KATEGORIEN)
    assert "Kräfte" not in daten["top_fertigkeiten"]
    assert "Hexkraft" not in daten["top_fertigkeiten"]
    assert "Nahkampf 2" in daten["top_fertigkeiten"]


def test_kommentar_daten_traegt_dieselben_warnungen_wie_berate():
    werte = {}  # leerer Bogen — alle Standardwarnungen greifen
    daten = berater.kommentar_daten(werte, "KEINER", _ATTRIBUT_KATEGORIEN)
    assert len(daten["warnungen"]) >= 3
