"""Sichtbarkeitsfilter für Wiki-Seiten.

Baut auf app/entities/visibility.py auf statt eigene Regeln zu erfinden —
GM/ALLE/SPEZIFISCH und die 🔒-Inline-Redaktion gelten im Wiki genauso wie
bei Personen, Orten und Events.

Wie dort gilt: Gefiltert wird serverseitig. Ein Spieler bekommt geheime
Inhalte gar nicht erst geschickt, statt dass die Oberfläche sie versteckt.
"""

from app.entities.visibility import is_visible_to, redact_rich_text


def filter_seite_for_viewer(seite: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    """Eine Wiki-Seite aus Sicht des Betrachters, oder None wenn unsichtbar.

    Fehlt die Sichtbarkeit, gilt sie als GM-geheim (fail closed) — wie bei den
    Entitäten. Für ein Planungswerkzeug ist das die einzig vertretbare
    Voreinstellung: eine Seite, die versehentlich offen steht, verrät den Plot.
    """
    if not is_visible_to(
        seite.get("sichtbarkeit") or "GM",
        seite.get("sichtbarFuer") or [],
        viewer_role,
        viewer_person_id,
    ):
        return None

    ergebnis = dict(seite)
    ergebnis["inhalt"] = redact_rich_text(ergebnis.get("inhalt", ""), viewer_role)
    return ergebnis


def filter_seiten_for_viewer(seiten: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    gefiltert = (filter_seite_for_viewer(s, viewer_role, viewer_person_id) for s in seiten)
    return [s for s in gefiltert if s is not None]
