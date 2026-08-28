from app.entities.schemas import SichtbarkeitModus
from pydantic import BaseModel


class GegenstandCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    typ: str = "Allgemein"
    # Freie Zusatzeigenschaften je nach Typ (Munition, Schaden, Preis, ...),
    # als Key-Value-Paare — bewusst nicht als starres Schema pro Typ, damit
    # neue Gegenstandsarten keine Backend-Änderung brauchen.
    eigenschaften: dict[str, str] = {}
    # MacGuffins/plot-relevante Gegenstände können als eigener Knoten im
    # Beziehungsgraph erscheinen (normale Gegenstände wie ein Hemdknopf nicht).
    zeigeInGraph: bool = False
    # Wird beim Anlegen automatisch gesetzt (PC-Besitzer -> nur für ihn sichtbar,
    # NPC-Besitzer -> SL-geheim), falls hier nicht explizit übersteuert.
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class GegenstandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    typ: str | None = None
    eigenschaften: dict[str, str] | None = None
    zeigeInGraph: bool | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class GegenstandResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    typ: str
    eigenschaften: dict[str, str]
    zeigeInGraph: bool
    bildUrl: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
