"""Schemas fürs gemeinsame Whiteboard.

Ein `Zeichnung`-Knoten ist ein eigenständiges Board (nicht Teil der
Entities/Ideenschmiede/Graph-Welt — kein Entitätstyp, keine Beziehungen).
Mehrere Boards pro Kampagne, jedes mit eigenem Namen, optionalem
Hintergrundbild und eigenem Freigabe-Schalter fürs Mitzeichnen.
"""

from pydantic import BaseModel

from app.entities.schemas import SichtbarkeitModus


class ZeichnungCreate(BaseModel):
    name: str
    bildUrl: str = ""
    spielerDuerfenZeichnen: bool = False
    sichtbarkeit: SichtbarkeitModus = "ALLE"
    sichtbarFuer: list[str] = []


class ZeichnungUpdate(BaseModel):
    name: str | None = None
    bildUrl: str | None = None
    spielerDuerfenZeichnen: bool | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class ZeichnungResponse(BaseModel):
    id: str
    name: str
    # Striche aus react-sketch-canvas (exportPaths()/loadPaths()) — eine
    # Liste roher Pfad-Objekte, deren Form uns nicht interessiert (reines
    # Durchreichen zwischen Frontend-Instanzen, siehe entity-types.md-Muster
    # für bilder/ziele: Liste von Maps braucht JSON-Serialisierung in Neo4j).
    pfade: list[dict] = []
    bildUrl: str = ""
    spielerDuerfenZeichnen: bool = False
    sichtbarkeit: SichtbarkeitModus = "ALLE"
    sichtbarFuer: list[str] = []
    geloescht: bool = False
    erstelltAm: str = ""


class PfadeUpdate(BaseModel):
    pfade: list[dict]


class GeloeschtUpdate(BaseModel):
    geloescht: bool = True
