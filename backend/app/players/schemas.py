from pydantic import BaseModel, Field


class BeitrittRequest(BaseModel):
    code: str
    # Damit der Spielleiter in der Sitzungsliste sieht, wer beigetreten ist.
    name: str = Field(min_length=1, max_length=60)


class CharakterWahlRequest(BaseModel):
    personId: str


class FreierCharakter(BaseModel):
    id: str
    name: str


class SpielerMeResponse(BaseModel):
    sessionId: str
    name: str
    campaignId: str
    campaignName: str
    # Erst nach dem Beanspruchen gesetzt
    personId: str | None = None
    personName: str | None = None


class ZugangscodeResponse(BaseModel):
    # None, wenn der Spielleiter den Zugang geschlossen hat
    code: str | None = None


class SitzungResponse(BaseModel):
    id: str
    name: str
    createdAt: str | None = None
    personId: str | None = None
    personName: str | None = None
