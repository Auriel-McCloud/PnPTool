"""Wer darf auf der Battlemap schieben und zeichnen, ohne Datenbank."""

from app.entities.visibility import is_visible_to


def darf_zeichnen(karte: dict, viewer_role: str, viewer_person_id: str | None) -> bool:
    """Wie Whiteboard: SL immer, Spieler nur mit Freigabe und Sicht."""
    if viewer_role == "GM":
        return True
    if not karte.get("spielerDuerfenZeichnen"):
        return False
    return is_visible_to(
        karte.get("sichtbarkeit") or "GM",
        karte.get("sichtbarFuer") or [],
        viewer_role,
        viewer_person_id,
    )


def darf_schieben(
    *,
    rolle: str,
    person_id: str | None,
    token_person_id: str | None,
    besitzer_id: str | None,
    am_zug: bool,
) -> bool:
    """SL immer. Spieler nur eigenen Token (oder eigene Drohne/Beschwörung) am Zug."""
    if rolle == "GM":
        return True
    if not am_zug or not person_id:
        return False
    if besitzer_id:
        return besitzer_id == person_id
    return token_person_id == person_id


TOKEN_FELDER = (
    "id",
    "name",
    "personId",
    "personType",
    "begleiterId",
    "hexQ",
    "hexR",
    "hexDrehung",
    "zugStartQ",
    "zugStartR",
    "bildUrl",
    "istGross",
    "istDrohne",
    "istFahrzeug",
    "istCritter",
    "besitzerId",
    "blickrichtung",
    "versteckt",
    "rundumsicht",
    "veraltet",
)


def token_stand(kampf: dict) -> dict:
    """Vollständiger Token-Stand für den Battlemap-Rundruf — inklusive neuer Teilnehmer."""
    return {
        "amZug": kampf.get("amZug"),
        "battlemapId": kampf.get("battlemapId"),
        "teilnehmer": [
            {feld: t.get(feld) for feld in TOKEN_FELDER}
            for t in kampf.get("teilnehmer") or []
            if not t.get("zusatzzug")
        ],
    }

