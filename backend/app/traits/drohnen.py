"""Riggerkonsole & aktive Slots (25.10.2026).

Siehe docs/wiki/concepts/drohnen-fahrzeuge.md. Eine Riggerkonsole
(`app/items/schemas.py::maxDrohnen`) begrenzt, wie viele Drohnen/Fahrzeuge
ihr Besitzer gleichzeitig aktiv verbunden haben kann. Reine Zählregel — wer
schon verbunden ist, bleibt verbunden, auch wenn die Konsole später
ausgetauscht wird und der neue Deckel niedriger ausfällt (kein nachträgliches
Zwangs-Deaktivieren, siehe `kann_aktivieren`).
"""


def kann_aktivieren(aktuell_aktive: int, max_drohnen: int) -> bool:
    """Darf eine weitere Drohne/ein weiteres Fahrzeug aktiviert werden?

    `aktuell_aktive` zählt NICHT die Drohne, die gerade aktiviert werden
    soll (die ist ja noch inaktiv) — ein Aufrufer mit z.B. 2 von 2 aktiven
    Slots bekommt hier `False`, mit 1 von 2 `True`.
    """
    return max(0, aktuell_aktive) < max(0, max_drohnen)
