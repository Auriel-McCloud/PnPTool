"""Schlanker Überblick für die vorgefertigte Charakterwahl.

Kein voller Bogen: nur, wohin die Punkte gefallen sind. Die drei
Fertigkeitsspalten sind dieselben wie auf dem Papierblatt — die ersten zehn
Kernfertigkeiten körperlich, die nächsten zehn gesellschaftlich, der Rest
geistig (`Charakterblatt.tsx` füllt die Fähigkeiten spaltenweise in dieser
Reihenfolge). Sphären und NeuroWeaving-Fertigkeiten bleiben daneben, sonst
sähe ein Magier geistig aus, nur weil er zaubert.
"""

from app.traits.seed import NEOTOPIA_TRAITS

SPALTEN = ("koerperlich", "gesellschaftlich", "geistig")

_ATTRIBUT_SPALTE = {
    "AttributKörperlich": "koerperlich",
    "AttributGesellschaftlich": "gesellschaftlich",
    "AttributGeistig": "geistig",
}

# sortOrder 1–10, 11–20, 21–30 — dieselbe Dreiteilung wie das Blatt.
_FERTIGKEIT_SPALTE = {
    name: SPALTEN[(sortierung - 1) // 10]
    for name, kategorie, _, sortierung in NEOTOPIA_TRAITS
    if kategorie == "Fertigkeit" and 1 <= sortierung <= 30
}


def _leer() -> dict[str, int]:
    return {spalte: 0 for spalte in SPALTEN}


def spalten_summen(werte: list[dict]) -> dict:
    """Summiert HAS_TRAIT-Zeilen zu den drei Spalten plus Weg-Extras.

    `werte`: `{name, category, rating}` — rating 0 oder fehlend zählt nicht,
    unbekannte Namen auch nicht.
    """
    attribute = _leer()
    fertigkeiten = _leer()
    sphaeren = 0
    neuroweaving = 0

    for eintrag in werte:
        name = eintrag.get("name")
        if not name:
            continue
        rating = eintrag.get("rating") or 0
        if rating <= 0:
            continue
        kategorie = eintrag.get("category")
        if kategorie in _ATTRIBUT_SPALTE:
            attribute[_ATTRIBUT_SPALTE[kategorie]] += rating
        elif kategorie == "Fertigkeit":
            spalte = _FERTIGKEIT_SPALTE.get(name)
            if spalte:
                fertigkeiten[spalte] += rating
        elif kategorie == "Sphäre":
            sphaeren += rating
        elif kategorie == "NeuroWeaving":
            neuroweaving += rating

    return {
        "attribute": attribute,
        "fertigkeiten": fertigkeiten,
        "sphaeren": sphaeren,
        "neuroweaving": neuroweaving,
    }
