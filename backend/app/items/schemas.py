from app.entities.schemas import SichtbarkeitModus
from pydantic import BaseModel


class GegenstandCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    # Wird beim Anlegen automatisch gesetzt (PC-Besitzer -> nur für ihn sichtbar,
    # NPC-Besitzer -> SL-geheim), falls hier nicht explizit übersteuert.
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class GegenstandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class GegenstandResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
