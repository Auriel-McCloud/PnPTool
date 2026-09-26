"""Schemas des Verhandlungs-Popups (SL macht einen Preisvorschlag, der
Spieler nimmt an oder lehnt ab).

**Bewusst generisch gehalten** (Marks Vorgabe, 23.09.2026): Der erste
Anwendungsfall ist die Rüstungsreparatur beim Händler, aber dasselbe Popup
soll später auch für Kaufverhandlungen im Shop-System wiederverwendet werden
— potenziell mit **mehreren Positionen gleichzeitig** (Warenkorb-Konzept,
noch nicht gebaut). Deshalb trägt eine Verhandlung von Anfang an eine LISTE
von Positionen statt eines einzelnen Preisfelds, auch wenn heute immer genau
eine Position drinsteht. Das kostet hier nichts (eine Liste mit einem
Eintrag ist so einfach zu handhaben wie ein Skalar) und erspart einen
kompletten Umbau, sobald der Warenkorb kommt.

Was genau bei Annahme passiert, ist **nicht** hier codiert — das steht in
`logic.py`, ausgewählt über `art`. Neue Verhandlungsarten (z.B.
"SHOP_KAUF") brauchen nur einen neuen Eintrag in der Dispatch-Tabelle dort,
keine Schema-Änderung.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Bekannte Verhandlungsarten — bestimmt, welche Nebenwirkung `logic.py` bei
# Annahme auslöst. Weisse Liste statt freiem String, damit ein Tippfehler
# beim Erstellen nicht eine Verhandlung erzeugt, die niemand ausführen kann.
VerhandlungsArt = Literal["RUESTUNG_REPARATUR", "SHOP_KAUF", "GEGENSTAND_WEITERGABE"]


class VerhandlungPosition(BaseModel):
    """Eine Zeile im Angebot: was, wofür wie viel."""

    bezeichnung: str
    betrag: int = Field(ge=0)


class VerhandlungCreate(BaseModel):
    """Vom SL geschickt: an wen, was wird angeboten, wie wird es ausgeführt."""

    empfaengerPersonId: str
    art: VerhandlungsArt
    positionen: list[VerhandlungPosition]
    # Frei nach `art`: für RUESTUNG_REPARATUR z.B. {"gegenstandId": ...,
    # "kaestchen": N} — was `logic.py` bei Annahme braucht, um die
    # eigentliche Handlung (Kästchen reparieren, Kapital abziehen)
    # auszuführen. Kein eigenes Feld je Art, damit neue Arten keine
    # Schema-Änderung brauchen.
    kontext: dict = {}

    @model_validator(mode="after")
    def pruefe_positionen(self):
        if not self.positionen:
            raise ValueError("Eine Verhandlung braucht mindestens eine Position")
        return self


class VerhandlungResponse(BaseModel):
    id: str
    empfaengerPersonId: str
    art: str
    positionen: list[VerhandlungPosition]
    gesamtbetrag: int
    kontext: dict = {}
    status: Literal["OFFEN", "ANGENOMMEN", "ABGELEHNT"] = "OFFEN"
    erstelltAm: str = ""
    # Nur gesetzt, wenn die Annahme tatsächlich etwas verändert hat (z.B.
    # die reparierte Rüstung) — für die Erfolgsmeldung im Popup.
    ergebnis: dict | None = None


class VerhandlungAntwortRequest(BaseModel):
    angenommen: bool


class GegenstandWeitergebenRequest(BaseModel):
    """Spieler-zu-Spieler-Übergabe eines Gegenstands (innerhalb der Party)."""

    gegenstandId: str
    empfaengerPersonId: str
