"""Reine Berechtigungslogik fürs Whiteboard, ohne Datenbank.

Mark hat festgelegt: pro Board entscheidet die SL, ob Spieler mitzeichnen
dürfen (`spielerDuerfenZeichnen`). Sichtbarkeit bleibt dabei die äußere
Grenze — eine Freigabe zum Zeichnen hebt nicht auf, dass ein Spieler das
Board überhaupt sehen darf (dieselbe Logik wie überall sonst im Projekt,
siehe app/entities/visibility.py::is_visible_to).
"""

from app.entities.visibility import is_visible_to


def darf_zeichnen(zeichnung: dict, viewer_role: str, viewer_person_id: str | None) -> bool:
    """Ob dieser Betrachter auf diesem Board live mitzeichnen darf."""
    if viewer_role == "GM":
        return True
    if not zeichnung.get("spielerDuerfenZeichnen"):
        return False
    return is_visible_to(
        zeichnung.get("sichtbarkeit") or "GM",
        zeichnung.get("sichtbarFuer") or [],
        viewer_role,
        viewer_person_id,
    )
