from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    benutzername: str = Field(min_length=1, max_length=60)
    # Leer lassen, solange kein Passwort gesetzt ist.
    passwort: str = ""


class PasswortRequest(BaseModel):
    """Leerer Wert entfernt das Passwort wieder."""

    passwort: str = ""


class SpielerAnlegenRequest(BaseModel):
    benutzername: str = Field(min_length=1, max_length=60)
    personId: str | None = None
    passwort: str = ""


class CharakterZuordnenRequest(BaseModel):
    personId: str | None = None


class SpielerMeResponse(BaseModel):
    spielerId: str
    benutzername: str
    campaignId: str
    campaignName: str
    personId: str | None = None
    personName: str | None = None
    hatPasswort: bool = False


class SpielerResponse(BaseModel):
    """Sicht der Spielleitung auf einen Zugang."""

    id: str
    benutzername: str
    hatPasswort: bool
    personId: str | None = None
    personName: str | None = None
