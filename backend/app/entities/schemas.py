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
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class PersonUpdate(BaseModel):
    name: str | None = None
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


EntityKind = Literal["Person", "Ort", "Event"]


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
