"""Protokoll-Zeile für KI: nicht nur der Anlass, sondern was gesagt oder erzeugt wurde."""

from app.ereignisprotokoll.repository import ki_kurz


def test_beratung_zeigt_frage_und_antwort():
    zeile = ki_kurz("beratung", "Was soll der Bösewicht wollen?", "Die Isotope, weil die Stadt ohne sie dunkel wird.")
    assert zeile.startswith("Beratung:")
    assert "Bösewicht" in zeile
    assert "Isotope" in zeile
    assert "→" in zeile


def test_generiert_zeigt_das_ergebnis_nicht_den_wunsch():
    zeile = ki_kurz(
        "idee-charakter",
        "Langes Gespräch\n" * 40,
        "Mira Voss\nRasse Elf, Weg Magier\nKonzept: Diebin im Rosthafen",
    )
    assert zeile.startswith("Charakter generiert:")
    assert "Mira Voss" in zeile
    assert "Langes Gespräch" not in zeile


def test_unbekannter_anlass_bleibt_lesbar():
    assert ki_kurz("shop-sortiment", "", "drei Klingen") == "Shop sortiment: drei Klingen"


def test_leerer_text_bleibt_beim_titel():
    assert ki_kurz("beratung", "  ", "") == "Beratung"


def test_zeitleiste_sortiert_neu_oben():
    from app.ereignisprotokoll.repository import _protokoll_zeile, _zeitleiste_sortieren

    rows = [
        {"zeitpunkt": "2026-10-03T14:00:00+00:00", "kurz": "alt"},
        {"zeitpunkt": "2026-10-26T11:00:00+00:00", "kurz": "neu"},
        {"zeitpunkt": "", "kurz": "ohne"},
        {"zeitpunkt": "2026-10-13T18:00:00+00:00", "kurz": "mitte"},
    ]
    sortiert = _zeitleiste_sortieren(rows)
    assert [r["kurz"] for r in sortiert] == ["neu", "mitte", "alt", "ohne"]


def test_zu_npc_nennt_wen_und_was():
    from app.ereignisprotokoll.repository import _protokoll_zeile

    assert _protokoll_zeile("charakterentwicklung", "ZU_NPC_GEMACHT", "Babybell", "PC → NPC") == (
        "Babybell: zu NPC gemacht (PC → NPC)"
    )


def test_droge_und_matrix_sind_lesbar():
    from app.ereignisprotokoll.repository import _protokoll_zeile

    assert _protokoll_zeile("kampf", "DROGE", "Mira", "Kick") == "Mira: Droge genommen (Kick)"
    assert _protokoll_zeile("kampf", "DROHNE_BEITRITT", "Mira", "Scout") == "Mira: Drohne beigetreten (Scout)"
    assert _protokoll_zeile("kampf", "FAHRZEUG_BEITRITT", "Mira", "Bike") == "Mira: Fahrzeug beigetreten (Bike)"
    assert _protokoll_zeile("kampf", "MATRIX_ANGRIFF", "Wachmann", "von Mira · Brute Force") == (
        "Wachmann: Matrix-Angriff (von Mira · Brute Force)"
    )
    from app.ereignisprotokoll.repository import _protokoll_zeile

    assert _protokoll_zeile(
        "charakterentwicklung", "STEIGERUNG", "Mira", "Schusswaffen 3 → 4 · 8 EP"
    ) == "Mira: Steigerung (Schusswaffen 3 → 4 · 8 EP)"
