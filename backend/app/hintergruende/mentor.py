"""Mentor — Mechanik-Hintergrund wie Schulden/Kredithai, eigener NPC statt
Katalogzeile (siehe seed.py::SYSTEM_SCHLUESSEL).

Punkte auf "Mentor" (0-5) legen einen leeren Platz in der Chatliste an.
Der Spieler beschreibt ihn, dann erzeugt die KI den NPC und gibt 20 EP
je Punkt auf vorhandene Werte aus.
"""


def bestehenden_mentor(npcs: list[dict]) -> dict | None:
    """Den ältesten markierten Mentor, sonst None (dann neu generieren)."""
    kandidaten = [n for n in npcs if n.get("istMentor")]
    if not kandidaten:
        return None
    return sorted(kandidaten, key=lambda n: (n.get("erstelltAm") or "", n.get("id") or ""))[0]
