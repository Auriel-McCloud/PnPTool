"""Schemas des Gruppenchats (Phase 2 des Messengers).

Eine Gruppe legt nur die Spielleitung an. Mitglieder sind Spielercharaktere
und NPCs gemischt; die SL schreibt als einer der NPC-Mitglieder (kein
sichtbarer Absender „Spielleitung“), die Spieler als ihr eigener Charakter.

**Namen sind pro Betrachter verschieden:** Ein Spieler sieht NPCs unter
seinem eigenen Alias bzw. „Unbekannter …“ (siehe `security.py`), die SL sieht
überall die echten Namen. Deshalb liefert die API keinen Namen, der für alle
gleich wäre.
"""

from pydantic import BaseModel, Field


class TeilnehmerResponse(BaseModel):
    id: str
    # Anzeigename aus Sicht des Betrachters (Spieler: Alias; SL: echter Name).
    name: str
    bildUrl: str = ""
    istNpc: bool = False
    # Der Betrachter selbst (nur Spieleransicht).
    ich: bool = False


class GruppeResponse(BaseModel):
    id: str
    name: str
    # Geschlossen = für Spieler unsichtbar, ohne etwas zu löschen.
    offen: bool = True
    ungelesen: int = 0
    teilnehmer: list[TeilnehmerResponse] = []


class GruppeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    personIds: list[str] = []


class GruppeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    offen: bool | None = None


class TeilnehmerHinzufuegen(BaseModel):
    personId: str


class GruppenNachrichtCreate(BaseModel):
    inhalt: str = Field(min_length=1, max_length=8000)
    # Nur die SL: welcher NPC aus der Gruppe spricht. Spieler schreiben immer
    # als eigener Charakter — das Feld wird bei ihnen abgelehnt.
    alsPersonId: str | None = None


class GruppenNachrichtResponse(BaseModel):
    id: str
    inhalt: str
    erstelltAm: str
    # Spieler: vom eigenen Charakter. SL: von einem NPC (steht rechts).
    vonMir: bool = False
    absender: str = ""
    bildUrl: str = ""
    gelesen: bool = False


class GruppenChatResponse(BaseModel):
    gruppe: GruppeResponse
    nachrichten: list[GruppenNachrichtResponse]
    # Nur SL: die NPC-Mitglieder, als die sie schreiben kann.
    sprecher: list[TeilnehmerResponse] = []
