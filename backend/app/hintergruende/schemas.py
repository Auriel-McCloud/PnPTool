from pydantic import BaseModel, Field


class HintergrundCreate(BaseModel):
    """Narrativer Katalogeintrag — Name plus Beschreibung, keine Mechanik."""

    name: str
    kurzbeschreibung: str = ""
    detailbeschreibung: str = ""


class HintergrundUpdate(BaseModel):
    name: str | None = None
    kurzbeschreibung: str | None = None
    detailbeschreibung: str | None = None


class HintergrundResponse(BaseModel):
    id: str
    campaignId: str
    name: str
    kurzbeschreibung: str
    detailbeschreibung: str


class PersonHintergrund(BaseModel):
    id: str
    name: str
    kurzbeschreibung: str
    detailbeschreibung: str
    rating: int = Field(ge=0)
