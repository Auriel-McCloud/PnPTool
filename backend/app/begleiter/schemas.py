from typing import Literal

from pydantic import BaseModel, Field

from app.entities.schemas import SichtbarkeitModus

# Sprite, Geist und Begleiter teilen sich ein Blatt (Neotopia.xlsx, Blatt
# "Drohne/Fahrzeug/Sprite/Geist"). Die Art trennt sie nur in der Anzeige —
# mechanisch sind sie dasselbe.
#
# **KI und CRITTER sind seit 20.09.2026 KEINE Begleiter-Arten mehr** — Mark:
# erst "wir machen critter zu richtigen NPCs", dann "mach jetzt das Gleiche
# für die KI". Beide leben als echte `Person`-Knoten in `app/entities/`
# (`istCritter`/`istKI`) mit dem vollen Charakterblatt statt dieses
# Drohne/Fahrzeug-Blatts — Einfluss-Kanten, KI-Attribute (inkl.
# Matrix-Präsenz als 4. Attribut-Kategorie) liegen entsprechend in
# `app/entities/schemas.py`/`repository.py`/`routes.py`.
BegleiterArt = Literal["SPRITE", "GEIST", "BEGLEITER"]


class BegleiterBasis(BaseModel):
    name: str
    art: BegleiterArt = "BEGLEITER"
    # Feld "Beziehnung" auf dem Papierblatt: wie er zu seinem Menschen steht.
    beziehung: str = ""
    beschreibung: str = ""
    notizen: str = ""
    # Aussehen; per Blitz an alle Spieler zeigbar — dasselbe Muster wie bei
    # Personen/Orten (EntitaetsBild), 20.09.2026 nachgezogen (Mark: "es gibt
    # keine Möglichkeit ein Bild anzuhängen").
    bildUrl: str = ""
    # Die Stufe wird beim Erschaffen frei auf die drei Werte und die
    # Fertigkeiten verteilt; Gesundheit = Stufe.
    stufe: int = Field(default=0, ge=0, le=15)
    widerstand: int = Field(default=0, ge=0, le=5)
    angriff: int = Field(default=0, ge=0, le=5)
    agilitaet: int = Field(default=0, ge=0, le=5)
    # Freie Fertigkeiten mit Wert — auf dem Blatt vier leere Zeilen.
    fertigkeiten: dict[str, int] = {}
    # Der Gegenstand am unteren Rand des Blatts.
    waffe: str = ""
    waffenSchaden: int = Field(default=0, ge=0, le=7)
    schadensart: str = ""

    # --- Erfahrung -----------------------------------------------------
    # Reine Budget-Anzeige, keine Kostenrechnung wie bei Personen (Mark,
    # 19.09.2026: Werte bleiben frei einstellbar, das ist nur Erinnerung/
    # Übersicht für die SL, wie viel schon "verdient" wurde).
    erfahrung: int = Field(default=0, ge=0)
    erfahrungAusgegeben: int = Field(default=0, ge=0)


class BegleiterCreate(BegleiterBasis):
    # Wem er zur Seite steht. Ohne Angabe ungebunden.
    besitzerId: str | None = None
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


class BegleiterUpdate(BaseModel):
    name: str | None = None
    art: BegleiterArt | None = None
    beziehung: str | None = None
    beschreibung: str | None = None
    notizen: str | None = None
    bildUrl: str | None = None
    stufe: int | None = Field(default=None, ge=0, le=15)
    widerstand: int | None = Field(default=None, ge=0, le=5)
    angriff: int | None = Field(default=None, ge=0, le=5)
    agilitaet: int | None = Field(default=None, ge=0, le=5)
    fertigkeiten: dict[str, int] | None = None
    waffe: str | None = None
    waffenSchaden: int | None = Field(default=None, ge=0, le=7)
    schadensart: str | None = None
    erfahrung: int | None = Field(default=None, ge=0)
    erfahrungAusgegeben: int | None = Field(default=None, ge=0)
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class BesitzerRequest(BaseModel):
    personId: str | None = None


class BegleiterResponse(BegleiterBasis):
    id: str
    besitzerId: str | None = None
    besitzerName: str | None = None
    sichtbarkeit: str
    sichtbarFuer: list[str]
