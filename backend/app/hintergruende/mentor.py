"""Mentor — Mechanik-Hintergrund wie Schulden/Kredithai, eigener NPC statt
Katalogzeile (siehe seed.py::SYSTEM_SCHLUESSEL).

Punkte auf "Mentor" (0-5, Teil des gemeinsamen Hintergrund-Pools, siehe
traits/erstellung.py::HINTERGRUENDE) erzeugen bei Erstellungs-Abschluss EINEN
NPC — bestehenden markierten wiederverwenden, sonst per KI frisch generiert
(voller Charakter inkl. Tutorial-Shop-Einkauf, siehe spawn.py::
mentor_nach_erstellung), genau wie Kredithai für Schulden.
"""


def bestehenden_mentor(npcs: list[dict]) -> dict | None:
    """Den ältesten markierten Mentor, sonst None (dann neu generieren)."""
    kandidaten = [n for n in npcs if n.get("istMentor")]
    if not kandidaten:
        return None
    return sorted(kandidaten, key=lambda n: (n.get("erstelltAm") or "", n.get("id") or ""))[0]
