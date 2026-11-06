"""Schemas für die Battlemap — eigenes Board, kein Zeichnung-Aufsatz."""

from pydantic import BaseModel

from app.entities.schemas import SichtbarkeitModus


class BattlemapCreate(BaseModel):
    name: str
    bildUrl: str = ""
    spielerDuerfenZeichnen: bool = False
    sichtbarkeit: SichtbarkeitModus = "ALLE"
    sichtbarFuer: list[str] = []


class BattlemapUpdate(BaseModel):
    name: str | None = None
    bildUrl: str | None = None
    spielerDuerfenZeichnen: bool | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    hexGroesse: int | None = None
    originX: float | None = None
    originY: float | None = None
    spawnPcQ: int | None = None
    spawnPcR: int | None = None
    spawnNpcQ: int | None = None
    spawnNpcR: int | None = None
    # Verknüpfung mit Orten/Events (06.11.2026, Mark: Battlemap einem Ort
    # oder Event zuordnen können). Rein organisatorisch — kein
    # automatisches Anhängen beim Kampfbeginn, nur Anzeige/Filter beim
    # Vorbereiten. Leer = keine Verknüpfung.
    ortIds: list[str] | None = None
    eventIds: list[str] | None = None


class BattlemapResponse(BaseModel):
    id: str
    name: str
    pfade: list[dict] = []
    bildUrl: str = ""
    spielerDuerfenZeichnen: bool = False
    sichtbarkeit: SichtbarkeitModus = "ALLE"
    sichtbarFuer: list[str] = []
    geloescht: bool = False
    erstelltAm: str = ""
    hexGroesse: int = 48
    originX: float = 0
    originY: float = 0
    spawnPcQ: int | None = None
    spawnPcR: int | None = None
    spawnNpcQ: int | None = None
    spawnNpcR: int | None = None
    ortIds: list[str] = []
    eventIds: list[str] = []


class PfadeUpdate(BaseModel):
    pfade: list[dict]


class GeloeschtUpdate(BaseModel):
    geloescht: bool = True


class PositionUpdate(BaseModel):
    q: int
    r: int
    drehung: int = 0


class BlickUpdate(BaseModel):
    blickrichtung: int


class VerstecktUpdate(BaseModel):
    versteckt: bool


class KarteAnKampf(BaseModel):
    battlemapId: str | None = None
