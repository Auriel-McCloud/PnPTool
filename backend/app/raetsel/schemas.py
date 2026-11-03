from typing import Literal

from pydantic import BaseModel, Field


class TuerAktion(BaseModel):
    raum: int
    seite: Literal["N", "O", "S", "W"]


class GruppeAktion(BaseModel):
    index: int = Field(ge=0, le=1)
    raum: int | None = None


class NameAktion(BaseModel):
    raum: int
    name: str = ""


class FreigabeAktion(BaseModel):
    an: bool


class AusgangAktion(BaseModel):
    ring: int = Field(ge=0, le=1)
    slot: int = Field(ge=0, le=7)


class ModusAktion(BaseModel):
    modus: Literal["leicht", "mittel"]
