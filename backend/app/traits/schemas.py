from pydantic import BaseModel


class TraitDefResponse(BaseModel):
    id: str
    name: str
    category: str
    defaultMax: int
    sortOrder: int
    description: str = ""
    # Fertigkeiten-Spezialisierung (22.10.2026): GM-vordefinierte
    # Vorschlagstexte für diese Fertigkeit, siehe traits/seed.py::TRAIT_VORSCHLAEGE.
    # Leer, wenn keine hinterlegt sind — der Spieler tippt dann frei.
    vorschlaege: list[str] = []


class TraitRatingUpdate(BaseModel):
    rating: int
    maxOverride: int | None = None


class TraitRatingResponse(BaseModel):
    traitDefId: str
    name: str
    category: str
    rating: int
    max: int
