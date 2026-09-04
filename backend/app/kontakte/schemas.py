"""Schemas für Kontakte und Messenger.

Fachliche Grundlage: `docs/phase-5-messenger.md`.

**Der echte NPC-Name taucht in keiner Spielerantwort auf** — auch nicht in
einem ungenutzten Feld. Deshalb hat `KontaktResponse` gar kein `npcName`,
sondern nur `echterName`, das die Sicherheitsschicht bewusst füllt oder auf
`None` lässt (`security.kontakt_fuer_viewer`).
"""

from typing import Literal

from pydantic import BaseModel, Field

Kontaktstufe = Literal["GESEHEN", "GESPROCHEN", "KONTAKT_AUSGETAUSCHT"]
AnfrageStatus = Literal["KEINE", "OFFEN", "ANGENOMMEN", "ABGELEHNT"]


class KontaktResponse(BaseModel):
    """Ein Kontakt aus Sicht des Betrachters.

    Kein `npcName`: der echte Name darf nur über `echterName` und nur nach
    Freigabe herausgehen.
    """

    id: str
    npcId: str
    # Was angezeigt wird: persönlicher Alias, sonst NPC-Standard, sonst
    # "Unbekannte Person".
    alias: str
    # Nur gesetzt, wenn `echterNameBekannt` gilt — sonst None.
    echterName: str | None = None
    # Der eigene Alias dieses Spielers, damit die Oberfläche ihn zum
    # Bearbeiten anbieten kann.
    persoenlicherAlias: str = ""
    bildUrl: str = ""
    beschreibung: str = ""
    stufe: Kontaktstufe = "GESEHEN"
    echterNameBekannt: bool = False
    kontaktAnfrageStatus: AnfrageStatus = "KEINE"
    persoenlicheNotizen: str = ""
    # Darf dieser Betrachter mit dem NPC schreiben?
    chatOffen: bool = False
    ungelesen: int = 0


class KontaktGmResponse(KontaktResponse):
    """Zusätzlich für die Spielleitung: wer kennt wen.

    Die SL sieht den echten Namen immer — sie hat den NPC angelegt.
    """

    pcId: str
    pcName: str = ""
    npcName: str = ""


class AliasUpdate(BaseModel):
    """Der persönliche Alias eines Spielers für diesen NPC."""

    alias: str = Field(max_length=120)


class NotizenUpdate(BaseModel):
    """Persönliche Notizen auf der eigenen KENNT-Beziehung."""

    inhalt: str = ""


class KontaktGmUpdate(BaseModel):
    """Was die Spielleitung an einem Kontakt ändern darf."""

    stufe: Kontaktstufe | None = None
    echterNameBekannt: bool | None = None
    # Der für diesen einen PC gesetzte Alias.
    alias: str | None = None


class KontaktCreate(BaseModel):
    """Die SL legt ein Kontaktwissen von Hand an."""

    pcId: str
    npcId: str
    stufe: Kontaktstufe = "GESEHEN"


class AnfrageEntscheidung(BaseModel):
    """Annehmen oder ablehnen — die SL antwortet als der NPC."""

    annehmen: bool


class NachrichtCreate(BaseModel):
    """Eine Nachricht im Einzelchat.

    Der Inhalt wird als TipTap-JSON gespeichert; Klartext wird beim Speichern
    umgewandelt (`logic.normalisiere_nachrichteninhalt`). Emojis bleiben echte
    Unicode-Zeichen — auch zusammengesetzte Sequenzen mit Hautfarbe.
    """

    inhalt: str = Field(min_length=1, max_length=8000)


class NachrichtResponse(BaseModel):
    id: str
    inhalt: str
    erstelltAm: str
    # True = vom Betrachter selbst geschrieben. Die Oberfläche stellt eigene
    # Nachrichten rechts dar, fremde links.
    vonMir: bool = False
    # Wer geschrieben hat — beim Spieler immer der Alias des NPC, nie
    # "Spielleitung" (Spec: SL-Nachrichten haben keinen sichtbaren Absender).
    absender: str = ""
    gelesen: bool = False


class ChatResponse(BaseModel):
    kontaktId: str
    npcId: str
    alias: str
    chatOffen: bool
    nachrichten: list[NachrichtResponse]
