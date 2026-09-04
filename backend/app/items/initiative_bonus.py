"""Initiative-Modifikator aus getragener Cyberware.

Regelblatt Zeile 57: *Initiative = Geistesschärfe + Geschicklichkeit +
CyberwareMod*. Bis hierher war der Modifikator immer 0 — das Feld existierte
in der Formel, aber nichts füllte es.

Der Reflex-Booster (Neotopia.xlsx, Zeilen 421-444) ist der Hauptfall:
+1 / +3 / +6 je nach Stufe. "Dash" (Zeile 174) gibt +2 für drei Runden.
Deshalb ein **freies Zahlenfeld am Gegenstand** statt einer Sonderregel für
den Reflex-Booster — jedes Implantat, jede Droge, jedes Artefakt kann die
Initiative verschieben.
"""

# Nur was am Körper sitzt, wirkt. Ein Booster im Rucksack beschleunigt
# niemanden.
WIRKSAME_ABLAGE = "AUSGERUESTET"


def initiative_bonus_von(gegenstaende: list[dict]) -> int:
    """Summiert die Initiative-Boni aller ausgerüsteten Gegenstände.

    Fail-closed: fehlende oder unlesbare Angaben zählen als 0. Ein erfundener
    Bonus wäre schlimmer als ein fehlender — er verschöbe die Kampfreihenfolge
    ohne dass jemand nachvollziehen kann, warum.
    """
    summe = 0
    for g in gegenstaende:
        if g.get("ablage") != WIRKSAME_ABLAGE:
            continue
        try:
            summe += int(g.get("initiativeBonus") or 0)
        except (TypeError, ValueError):
            continue
    return summe
