"""Reflex-Booster: Zusatzaktion, Überhitzung, Paralyse.

Der Ablauf am Tisch (Marks Beschreibung vom 04.09.2026):

1. Der Spieler ist dran. Hat er einen Booster verbaut, fragt ein Popup
   **"Reflex Booster aktivieren?"**.
2. Sagt er ja, würfelt das Tool seinen **Standardpool ohne Boosterbonus**
   (Geistesschärfe + Geschicklichkeit). Das Ergebnis ist meist niedriger als
   sein erster Wurf — er handelt also später ein zweites Mal.
   Ist es höher, kommt er direkt zweimal hintereinander dran.
3. Der Zusatzeintrag **verschwindet, sobald er dran war**.
4. Bei Stufe 3 füllt jede Nutzung ein Ampelfeld. Eine ausgesetzte Runde
   nimmt eines weg.
5. Sind alle drei gefüllt, folgt am Ende seiner letzten Runde der
   **Paralyse-Wurf** (Regelblatt Zeile 443: Geistesschärfe + Willenskraft
   gegen 3). Misslingt er, steht die Ampel auf 0 und er setzt die nächste
   Runde aus.
"""

from app.traits.bogen import initiative as _initiative_formel

# Drei Felder wie eine Ampel.
AMPEL_MAX = 3

# Regelblatt Zeile 443: Probe gegen 3.
PARALYSE_SCHWELLE = 3

# Bedeutung von zusatzaktionen_max
UNBEGRENZT = -1


def zweitwurf_pool(werte: dict[str, int], cyberware_mod: int = 0) -> int:
    """Der Pool für den zweiten Initiativwurf.

    **Ohne Boosterbonus** — Marks ausdrückliche Vorgabe: *"mit seinen
    Standard Initiative wert, also Geistes Schärfe + Geschicklichkeit ohne
    Bonus"*. Genau das macht die Zusatzaktion zum Risiko: sie kommt später,
    nicht früher.

    Das Argument `cyberware_mod` wird bewusst **ignoriert** — es steht hier,
    damit niemand später versehentlich den Bonus durchreicht.
    """
    return max(0, _initiative_formel(werte, 0))


def darf_aktivieren(zusatzaktionen_max: int, bereits_genutzt: int) -> bool:
    """Ist noch eine Zusatzaktion übrig?

    `zusatzaktionen_max` kommt vom Gegenstand: 1 (Stufe 1), 2 (Stufe 2) oder
    `UNBEGRENZT` für Stufe 3 ("Jede Runde kannst du eine zusätzliche Aktion
    machen"). 0 bedeutet: kein Booster.
    """
    if zusatzaktionen_max == UNBEGRENZT:
        return True
    return bereits_genutzt < zusatzaktionen_max


def ampel_nach_nutzung(stand: int) -> int:
    """Eine Nutzung füllt ein Ampelfeld."""
    return min(AMPEL_MAX, stand + 1)


def ampel_nach_aussetzen(stand: int) -> int:
    """Eine ausgesetzte Runde kühlt ein Feld ab."""
    return max(0, stand - 1)


def braucht_paralyse_wurf(stand: int) -> bool:
    """Volle Ampel heisst: Überhitzung, Probe fällig."""
    return stand >= AMPEL_MAX


def paralyse_pool(werte: dict[str, int]) -> int:
    """Geistesschärfe + Willenskraft (Regelblatt Zeile 443)."""
    return max(0, int(werte.get("Geistesschärfe", 0)) + int(werte.get("Willenskraft", 0)))


def paralyse_schwelle() -> int:
    """Wie viele Erfolge der Wurf braucht."""
    return PARALYSE_SCHWELLE
