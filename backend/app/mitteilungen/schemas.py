"""Schemas der SL-Mitteilungen."""

from typing import Literal

from pydantic import BaseModel, model_validator


class MitteilungCreate(BaseModel):
    art: Literal["TEXT", "BILD", "WARNUNG"] = "TEXT"
    inhalt: str = ""
    bildUrl: str = ""
    # Nur bei WARNUNG: Farbe des pulsierenden Schirms. Waehlbar, weil der
    # Ton am Tisch noch erprobt wird.
    farbe: Literal["rot", "blau", "violett"] = "rot"
    # An alle oder an ausgewählte Charaktere — Mark wollte beides.
    anAlle: bool = True
    empfaengerIds: list[str] = []

    @model_validator(mode="after")
    def pruefe_inhalt(self):
        if self.art == "TEXT" and not self.inhalt.strip():
            raise ValueError("Eine Textmitteilung braucht einen Text")
        if self.art == "WARNUNG" and not self.inhalt.strip():
            # Ein pulsierender Schirm ohne Ansage sagt niemandem, was los ist.
            raise ValueError("Eine Warnung braucht einen Text")
        if self.art == "BILD" and not self.bildUrl.strip():
            raise ValueError("Eine Bildmitteilung braucht ein Bild")
        if not self.anAlle and not self.empfaengerIds:
            raise ValueError("Ohne Rundruf muss mindestens ein Empfänger gewählt sein")
        return self


class MitteilungResponse(BaseModel):
    id: str
    art: str = "TEXT"
    inhalt: str = ""
    bildUrl: str = ""
    farbe: str = "rot"
    anAlle: bool = True
    empfaengerIds: list[str] = []
    gelesenVon: list[str] = []
    erstelltAm: str = ""


class MitteilungenAntwort(BaseModel):
    """Was ein Client beim Verbinden bzw. Abholen bekommt."""

    mitteilungen: list[MitteilungResponse] = []
    ungelesen: int = 0


class SendeAntwort(BaseModel):
    mitteilung: MitteilungResponse
    # Wie viele offene Leitungen es sofort erreicht hat. Der Rest bekommt es
    # beim nächsten Verbinden — nichts geht verloren.
    zugestellt: int = 0
