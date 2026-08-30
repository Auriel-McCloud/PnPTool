from typing import Literal

from pydantic import BaseModel, Field

from app.entities.schemas import SichtbarkeitModus

# Sprite, Geist und Begleiter teilen sich ein Blatt (Neotopia.xlsx, Blatt
# "Drohne/Fahrzeug/Sprite/Geist"). Die Art trennt sie nur in der Anzeige —
# mechanisch sind sie dasselbe.
BegleiterArt = Literal["SPRITE", "GEIST", "BEGLEITER"]


class BegleiterBasis(BaseModel):
    name: str
    art: BegleiterArt = "BEGLEITER"
    # Feld "Beziehnung" auf dem Papierblatt: wie er zu seinem Menschen steht.
    beziehung: str = ""
    beschreibung: str = ""
    notizen: str = ""
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
    stufe: int | None = Field(default=None, ge=0, le=15)
    widerstand: int | None = Field(default=None, ge=0, le=5)
    angriff: int | None = Field(default=None, ge=0, le=5)
    agilitaet: int | None = Field(default=None, ge=0, le=5)
    fertigkeiten: dict[str, int] | None = None
    waffe: str | None = None
    waffenSchaden: int | None = Field(default=None, ge=0, le=7)
    schadensart: str | None = None
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
