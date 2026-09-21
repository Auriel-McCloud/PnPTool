from typing import Literal

from pydantic import BaseModel, Field

from app.entities.schemas import SichtbarkeitModus

# Sprite, Geist und Begleiter teilen sich ein Blatt (Neotopia.xlsx, Blatt
# "Drohne/Fahrzeug/Sprite/Geist"). Die Art trennt sie nur in der Anzeige —
# mechanisch sind sie dasselbe. KI baut auf demselben Blatt auf, bringt aber
# eigene Zusatzfelder mit (siehe unten) — Mark, 19.09.2026: eine Stadt-KI
# (Babel) ist ein besonders mächtiger Sprite, kein neuer Entity-Typ, damit
# Kampf/Zerstören (Brute Force → Kompilieren) automatisch mitläuft.
# CRITTER (Tiere/Haustiere) sind seit 20.09.2026 KEIN Begleiter-Art mehr —
# Mark: "wir machen critter zu richtigen NPCs". Sie leben als `Person`
# (`istCritter=true`) in app/entities/ mit dem vollen NPC-Charakterblatt.
BegleiterArt = Literal["SPRITE", "GEIST", "BEGLEITER", "KI"]

# Ziele, denen eine KI (oder theoretisch jeder Begleiter) Einfluss auf die
# Welt entzogen bzw. zugewiesen bekommen kann — echte Graphkanten statt
# Freitext, damit die Spielleitung ihr im Kampf gezielt einen echten Ort
# wegnehmen kann. Keine Personen: Einfluss auf einen Menschen ist im Tool
# bereits Beziehung/Handlung, kein Ressourcenwert.
EinflussZielKind = Literal["Ort", "Fraktion", "Event", "Gegenstand"]


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

    # --- Zusatzblatt KI (art == "KI") ---------------------------------
    # Dieselbe Skala 1-6 wie bei Personen (Mark, 19.09.2026: "unsere Skala
    # bei Attributen geht von 1-6... verwenden wir wirklich unser system wie
    # bei einer person weiter"). Nur die geistigen/gesellschaftlichen
    # Attribute — eine körperlose KI hat keine Körperlichen.
    charisma: int = Field(default=0, ge=0, le=6)
    manipulation: int = Field(default=0, ge=0, le=6)
    fassung: int = Field(default=0, ge=0, le=6)
    intelligenz: int = Field(default=0, ge=0, le=6)
    geistesschaerfe: int = Field(default=0, ge=0, le=6)
    entschlossenheit: int = Field(default=0, ge=0, le=6)
    # Neu, nur für KIs: wie dominant/sichtbar sie in der Matrix ist.
    matrixPraesenz: int = Field(default=0, ge=0, le=6)

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
    charisma: int | None = Field(default=None, ge=0, le=6)
    manipulation: int | None = Field(default=None, ge=0, le=6)
    fassung: int | None = Field(default=None, ge=0, le=6)
    intelligenz: int | None = Field(default=None, ge=0, le=6)
    geistesschaerfe: int | None = Field(default=None, ge=0, le=6)
    entschlossenheit: int | None = Field(default=None, ge=0, le=6)
    matrixPraesenz: int | None = Field(default=None, ge=0, le=6)
    erfahrung: int | None = Field(default=None, ge=0)
    erfahrungAusgegeben: int | None = Field(default=None, ge=0)
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class BesitzerRequest(BaseModel):
    personId: str | None = None


class EinflussEintrag(BaseModel):
    """Ein Ziel, dem der Begleiter (typischerweise eine KI) Einfluss auf die
    Welt entzogen bzw. zugewiesen hat — echte Graphkante mit Stufe, siehe
    `EinflussZielKind`."""

    zielKind: EinflussZielKind
    zielId: str
    zielName: str
    stufe: int = Field(ge=0, le=6)


class EinflussSetzen(BaseModel):
    zielKind: EinflussZielKind
    zielId: str
    stufe: int = Field(ge=0, le=6)


class BegleiterResponse(BegleiterBasis):
    id: str
    besitzerId: str | None = None
    besitzerName: str | None = None
    einfluss: list[EinflussEintrag] = []
    sichtbarkeit: str
    sichtbarFuer: list[str]
