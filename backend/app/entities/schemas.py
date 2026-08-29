from typing import Literal

from pydantic import BaseModel

SichtbarkeitModus = Literal["GM", "ALLE", "SPEZIFISCH"]


class SichtbarkeitInput(BaseModel):
    modus: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


VISIBILITY_FIELDS = ["sichtbarkeit", "sichtbarFuer", "notizenSichtbarkeit", "notizenSichtbarFuer"]
VERBINDUNG_VISIBILITY_FIELDS = ["sichtbarkeit", "sichtbarFuer"]


class PersonCreate(BaseModel):
    name: str
    personType: Literal["PC", "NPC"] = "NPC"
    description: str = ""
    notes: str = ""
    # --- Charakterbogen ---------------------------------------------------
    # Der eingeschlagene Weg entscheidet, was auf dem Blatt überhaupt
    # erscheint: Sphären und Arete nur für Magier, NeuroWeaving nur für
    # Technomancer. Auf dem Blatt steht ausdrücklich "Arete != NeuroWeaving",
    # beides zugleich geht also nicht. Ein eigenes Feld statt aus Arete > 0
    # abzuleiten — sonst wäre ein frisch erstellter Magier mit Arete 0 keiner.
    weg: Literal["KEINER", "MAGIER", "TECHNOMANCER"] = "KEINER"
    # Bestimmt Startwerte und Maxima bei der Erstellung (Mensch, Ork, Elf,
    # Zwerg, Troll). Frei als Text, weil Rassen dazukommen können.
    rasse: str = ""
    # Zustand: abgehakte Kästchen. Die Obergrenze ist abgeleitet
    # (Gesundheit = 5 + Widerstandsfähigkeit, Willenskraft = Entschlossenheit
    # + Fassung) und wird berechnet, nicht gespeichert.
    gesundheitSchaden: int = 0
    willenskraftVerbraucht: int = 0
    iceSchaden: int = 0
    # I.C.E. kommt vom Commlink und ist deshalb nicht ableitbar.
    iceMax: int = 0
    # Erfahrung: gesamt vergeben und davon ausgegeben.
    erfahrung: int = 0
    erfahrungAusgegeben: int = 0

    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class PersonUpdate(BaseModel):
    name: str | None = None
    weg: Literal["KEINER", "MAGIER", "TECHNOMANCER"] | None = None
    rasse: str | None = None
    gesundheitSchaden: int | None = None
    willenskraftVerbraucht: int | None = None
    iceSchaden: int | None = None
    iceMax: int | None = None
    erfahrung: int | None = None
    erfahrungAusgegeben: int | None = None
    personType: Literal["PC", "NPC"] | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class PersonResponse(BaseModel):
    id: str
    name: str
    personType: str
    description: str
    notes: str
    # Charakterbogen — Ausgangswerte greifen für Bestandsdaten, die diese
    # Felder noch nicht haben (Ersatz kommt aus dem Repository).
    weg: str = "KEINER"
    rasse: str = ""
    gesundheitSchaden: int = 0
    willenskraftVerbraucht: int = 0
    iceSchaden: int = 0
    iceMax: int = 0
    erfahrung: int = 0
    erfahrungAusgegeben: int = 0
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


class OrtCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class OrtUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class OrtResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


class EventCreate(BaseModel):
    title: str
    timestamp: str = ""
    description: str = ""
    notes: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class EventUpdate(BaseModel):
    title: str | None = None
    timestamp: str | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class EventResponse(BaseModel):
    id: str
    title: str
    timestamp: str
    description: str
    notes: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


EntityKind = Literal["Person", "Ort", "Event", "Gegenstand"]


class VerbindungCreate(BaseModel):
    vonKind: EntityKind
    vonId: str
    zuKind: EntityKind
    zuId: str
    typ: str
    beschreibung: str = ""
    seit: str = ""
    bis: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


class VerbindungResponse(BaseModel):
    id: str
    vonKind: str
    vonId: str
    zuKind: str
    zuId: str
    typ: str
    beschreibung: str
    seit: str
    bis: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
