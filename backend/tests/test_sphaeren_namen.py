"""Sphärennamen auf dem Blatt. Ohne Datenbank.

09.11.2026: Korrespondenz→Raum, Zeit→Chronurgie, Entropie→Schicksal.
Gedanken bleibt, bis der Name steht. Die Götter bleiben.
"""

from app.traits.seed import HAERETIKER_LABELS, NEOTOPIA_TRAITS, TRAIT_VORSCHLAEGE


def test_blatt_zeigt_die_entschiedenen_namen():
    namen = [name for name, kategorie, *_ in NEOTOPIA_TRAITS if kategorie == "Sphäre"]
    assert namen == [
        "Raum",
        "Schicksal",
        "Kräfte",
        "Leben",
        "Materie",
        "Gedanken",
        "Ursprung",
        "Schattenwelten",
        "Chronurgie",
    ]


def test_goetter_bleiben_an_den_neuen_namen():
    assert HAERETIKER_LABELS["Raum"] == "Shu"
    assert HAERETIKER_LABELS["Chronurgie"] == "Chronos"
    assert HAERETIKER_LABELS["Schicksal"] == "Kali"
    assert HAERETIKER_LABELS["Gedanken"] == "Tezcatlipoca"


def test_schicksal_chip_heisst_nicht_wie_die_sphaere():
    assert "Schicksal" not in TRAIT_VORSCHLAEGE["Schicksal"]
    assert "Ordnung" in TRAIT_VORSCHLAEGE["Schicksal"]
