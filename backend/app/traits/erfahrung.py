"""Erfahrungspunkte ausgeben (Level Up).

**Diese Preise stehen nicht im Regelwerk.** `Neotopia.xlsx` beschreibt die
Erstellung samt Freebees, sagt aber nichts darüber, was ein Punkt später
kostet. Die Tabelle unten ist deshalb ein Vorschlag zum Feinschliff und
bewusst an zwei Dinge angelehnt:

* die World of Darkness, an der NeotopiA sich ohnehin orientiert (Steigern
  kostet den *aktuellen* Wert mal einem Faktor — der fünfte Punkt ist teurer
  als der zweite),
* das Preisverhältnis der Freebees (Attribut 5, Fertigkeit 2,
  Willenskraft 1), damit sich Erstellung und Steigern nicht widersprechen.

Ändern heißt: nur `FAKTOR` und `NEU_KOSTEN` anfassen. Die Oberfläche zeigt
die Preise an, statt sie selbst zu kennen.
"""

# Faktor je Kategorie. Preis = aktueller Wert × Faktor.
FAKTOR: dict[str, int] = {
    "AttributKörperlich": 4,
    "AttributGesellschaftlich": 4,
    "AttributGeistig": 4,
    "Fertigkeit": 2,
    # Mark, 30.08.2026: Sphären zählen zu den Fertigkeiten, Arete zu den
    # Attributen — beim Steigern wie bei den Freebees. Arete kostet also
    # wie ein Attribut, eine Sphäre wie eine Fertigkeit.
    "Sphäre": 2,
    "Arete": 4,
    # NeuroWeaving blieb auf Marks Wunsch unverändert ("den Rest lassen wir
    # so"). Es ist beim Technomancer allerdings das Gegenstück zu den
    # Sphären, die jetzt 2 kosten — bei Gelegenheit nachfragen.
    "NeuroWeaving": 5,
    "Hintergrund": 3,
}

# Was der Sprung von 0 auf 1 kostet — die Formel gäbe hier 0 her, und
# geschenkt soll nichts sein. Attribute fehlen bewusst: die stehen nach der
# Erstellung nie auf 0.
NEU_KOSTEN: dict[str, int] = {
    "Fertigkeit": 3,
    "Sphäre": 3,
    # Wie der Freebee-Preis eines Attributpunkts, damit der Einstieg in die
    # Magie nicht teurer ist als bei der Erstellung.
    "Arete": 5,
    "NeuroWeaving": 7,
    "Hintergrund": 3,
}

# Willenskraft ist kein Katalogwert, sondern abgeleitet. Ein Punkt darauf
# wird als Bonus gespeichert und kostet den erreichten Wert mal eins.
FAKTOR_WILLENSKRAFT = 1


def kosten(kategorie: str, von: int) -> int | None:
    """Was der Schritt von `von` auf `von + 1` kostet.

    `None` bedeutet: diese Kategorie lässt sich nicht mit Erfahrung steigern
    (etwa weil sie gar nicht im Katalog steht). Das ist ausdrücklich kein
    Preis von 0 — der Aufrufer muss den Fall trennen behandeln.
    """
    if von <= 0:
        return NEU_KOSTEN.get(kategorie)
    faktor = FAKTOR.get(kategorie)
    return None if faktor is None else von * faktor


def kosten_willenskraft(von: int) -> int:
    """Willenskraft steigern: der erreichte Wert, mindestens 1."""
    return max(1, von) * FAKTOR_WILLENSKRAFT


def preisliste(katalog: list[dict], werte: dict[str, int]) -> list[dict]:
    """Für jeden Katalogwert der Preis des nächsten Punktes.

    Wird so an die Oberfläche gegeben, damit dort niemand die Formel
    nachbauen muss — sonst driften Anzeige und Abrechnung auseinander,
    sobald jemand an der Tabelle oben dreht.
    """
    liste = []
    for eintrag in katalog:
        aktuell = werte.get(eintrag["name"], 0)
        preis = kosten(eintrag["category"], aktuell)
        if preis is None:
            continue
        liste.append(
            {
                "traitDefId": eintrag["id"],
                "name": eintrag["name"],
                "category": eintrag["category"],
                "aktuell": aktuell,
                "max": eintrag["defaultMax"],
                "kosten": preis,
            }
        )
    return liste
