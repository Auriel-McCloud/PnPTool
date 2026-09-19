from pydantic import BaseModel

from app.entities.schemas import SichtbarkeitModus


class PartyCreate(BaseModel):
    """Eine Gruppe, die gerade gemeinsam unterwegs ist.

    Bewusst schlank — keine Ziele/Ressourcen wie bei Fraktionen (Neotopia-
    Wiki, 28.08.2026: "eine Party ist wer gerade zusammen unterwegs ist",
    keine dauerhafte Organisation mit eigenen Absichten). Mitgliedschaft und
    Aufenthaltsort sind eigene Beziehungen (siehe repository.py), keine
    Felder hier.
    """

    name: str
    beschreibung: str = ""
    notizen: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


class PartyUpdate(BaseModel):
    name: str | None = None
    beschreibung: str | None = None
    notizen: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class MitgliedRequest(BaseModel):
    personId: str


class AufenthaltsortRequest(BaseModel):
    """Wo die Party gerade ist — ein Ort oder ein Event, oder keins (unterwegs).

    `zielKind` steuert, gegen welches Label gematcht wird (analog zu
    Verbindungen in entities/repository.py, wo vonKind/zuKind ebenfalls den
    Knotentyp angeben). Nur bei gesetztem `zielId` von Belang.
    """

    zielId: str | None = None
    zielKind: str | None = None  # "Ort" | "Event"


class Mitglied(BaseModel):
    id: str
    name: str
    personType: str


class PartyResponse(BaseModel):
    id: str
    name: str
    beschreibung: str
    notizen: str
    # Nur EINE Party pro Kampagne kann aktiv sein (siehe repository.py::
    # aktivieren) — die aktive Party ist die, deren Aufenthaltsort später die
    # Musik auslöst (Spotify/MusicCast-Anbindung, noch nicht gebaut).
    aktiv: bool = False
    mitglieder: list[Mitglied] = []
    aufenthaltsortId: str | None = None
    aufenthaltsortName: str | None = None
    aufenthaltsortKind: str | None = None
    sichtbarkeit: str
    sichtbarFuer: list[str]
