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


class VorgefertigterCharakter(BaseModel):
    """Ein vorgebauter PC zur Auswahl beim ersten Einstieg (Ersteinstiegs-

    Fenster, players/SpielerEinstieg.tsx) — bewusst schlank, kein voller
    Bogen. Ergibt sich aus PCs ohne zugeordneten Spieler, kein eigenes
    Markierungsfeld nötig.
    """

    id: str
    name: str
    bildUrl: str = ""
    konzept: str = ""
    rasse: str = ""
    weg: str = "KEINER"


class CharakterWaehlenRequest(BaseModel):
    personId: str


class SpielerMeResponse(BaseModel):
    spielerId: str
    benutzername: str
    campaignId: str
    campaignName: str
    personId: str | None = None
    personName: str | None = None
    hatPasswort: bool = False
    # Charakterportrait des eigenen Charakters — Mark, 22.09.2026: "es gibt
    # keine Möglichkeit ein Bild anzuhängen" für Spieler (analog zu
    # Begleitern/Entitäten, die die SL schon längst per Bild-Upload pflegen
    # kann). Selbstbedienung über /api/spieler/mein-bild.
    personBildUrl: str | None = None


class SpielerResponse(BaseModel):
    """Sicht der Spielleitung auf einen Zugang."""

    id: str
    benutzername: str
    hatPasswort: bool
    personId: str | None = None
    personName: str | None = None
