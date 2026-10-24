from pydantic import BaseModel


class SpezialisierungResponse(BaseModel):
    id: str
    campaignId: str
    personId: str
    traitDefId: str
    # Leer = noch unbenannter Slot.
    text: str
    quelle: str  # "automatisch" | "gekauft"
    benanntVonSpieler: bool
    erstelltAm: str


class SpezialisierungBenennenInput(BaseModel):
    text: str


class SpezialisierungKaufenInput(BaseModel):
    traitDefId: str


class SpezialisierungKampagneResponse(SpezialisierungResponse):
    """Kampagnenliste für die SL: Slot plus wer, welche Fertigkeit, welches Rating."""

    personName: str
    traitName: str
    category: str
    rating: int
    unterSchwelle: bool


class SpezialisierungAufraeumenResponse(BaseModel):
    entfernt: int
