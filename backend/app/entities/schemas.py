from typing import Literal

from pydantic import BaseModel

Sichtbarkeit = Literal["GM", "SPIELER"]


class PersonCreate(BaseModel):
    name: str
    personType: Literal["PC", "NPC"] = "NPC"
    description: str = ""
    notes: str = ""
    sichtbarkeit: Sichtbarkeit = "GM"


class PersonUpdate(BaseModel):
    name: str | None = None
    personType: Literal["PC", "NPC"] | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: Sichtbarkeit | None = None


class PersonResponse(BaseModel):
    id: str
    name: str
    personType: str
    description: str
    notes: str
    sichtbarkeit: str


class OrtCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    sichtbarkeit: Sichtbarkeit = "GM"


class OrtUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: Sichtbarkeit | None = None


class OrtResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    sichtbarkeit: str


class EventCreate(BaseModel):
    title: str
    timestamp: str = ""
    description: str = ""
    notes: str = ""
    sichtbarkeit: Sichtbarkeit = "GM"


class EventUpdate(BaseModel):
    title: str | None = None
    timestamp: str | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: Sichtbarkeit | None = None


class EventResponse(BaseModel):
    id: str
    title: str
    timestamp: str
    description: str
    notes: str
    sichtbarkeit: str


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
    sichtbarkeit: Sichtbarkeit = "GM"


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
