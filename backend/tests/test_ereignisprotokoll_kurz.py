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
