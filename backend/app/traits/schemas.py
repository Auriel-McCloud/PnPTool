from pydantic import BaseModel


class TraitDefResponse(BaseModel):
    id: str
    name: str
    category: str
    defaultMax: int
    sortOrder: int


class TraitRatingUpdate(BaseModel):
    rating: int
    maxOverride: int | None = None


class TraitRatingResponse(BaseModel):
    traitDefId: str
    name: str
    category: str
    rating: int
    max: int
