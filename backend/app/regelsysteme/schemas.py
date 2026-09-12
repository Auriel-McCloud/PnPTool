"""Schemas für Regelsysteme."""

from pydantic import BaseModel, Field


class RegelsystemCreate(BaseModel):
    """Ein neues Regelsystem anlegen."""

    name: str = Field(..., min_length=1, max_length=100)
    beschreibung: str = ""


class RegelsystemUpdate(BaseModel):
    """Ein Regelsystem bearbeiten."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    beschreibung: str | None = None


class RegelsystemResponse(BaseModel):
    """Regelsystem in der API-Antwort."""

    id: str
    name: str
    beschreibung: str
    # Anzahl der Kampagnen die dieses System nutzen
    kampagnenAnzahl: int = 0
