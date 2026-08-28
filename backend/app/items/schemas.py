from app.entities.schemas import SichtbarkeitModus
from pydantic import BaseModel


class GegenstandCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    typ: str = "Sonstiges"
    preis: int = 0
    # Punkte-Bonus (0-7, wie Waffenschaden/Rüstungsbonus im Regeln-Sheet),
    # nur relevant wenn typ Waffe/Rüstung ist, aber generisch gespeichert.
    kraft: int = 0
    # Freie Zusatzeigenschaften für alles, was kein eigenes Feld hat (Munition,
    # Schadensart, ...) — bewusst nicht als starres Schema pro Typ, damit neue
    # Gegenstandsarten keine Backend-Änderung brauchen.
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
    preis: int | None = None
    kraft: int | None = None
    eigenschaften: dict[str, str] | None = None
    zeigeInGraph: bool | None = None
    bildUrl: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class GegenstandResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    typ: str
    preis: int
    kraft: int
    eigenschaften: dict[str, str]
    zeigeInGraph: bool
    bildUrl: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
