from pydantic import BaseModel


class ZusatzfertigkeitCreate(BaseModel):
    """Ein neuer Katalogeintrag — reiner Name plus Beschreibung.

    Keine Mechanik, keine Boni (Marks Vorgabe): eine Zusatzfertigkeit ist
    eine normale Fertigkeit auf der üblichen 0-6-Skala, nur nicht im
    festen Ruleset-Katalog (TraitDef), sondern campaign-gebunden.
    """

    name: str
    kurzbeschreibung: str = ""
    detailbeschreibung: str = ""


class ZusatzfertigkeitUpdate(BaseModel):
    name: str | None = None
    kurzbeschreibung: str | None = None
    detailbeschreibung: str | None = None


class ZusatzfertigkeitResponse(BaseModel):
    id: str
    campaignId: str
    name: str
    kurzbeschreibung: str
    detailbeschreibung: str


class PersonZusatzfertigkeit(BaseModel):
    """Eine von einer Person gewählte Zusatzfertigkeit samt Stufe.

    Trägt Kurz- und Detailbeschreibung mit, damit das Charakterblatt und
    das Auswahl-Popup nicht für jede Anzeige extra den Katalog nachladen
    müssen — dieselbe Antwort reicht für beides.
    """

    id: str
    name: str
    kurzbeschreibung: str
    detailbeschreibung: str
    rating: int


class ZusatzfertigkeitHinzufuegenInput(BaseModel):
    zusatzfertigkeitId: str
