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
    # Rassengebundene Zusatzfertigkeit (10.10.2026, Vaet-Transformation):
    # leer = für alle wählbar (Normalfall). Gesetzt (Rassenname als Text,
    # wie Person.rasse — kein eigener Katalog-Fremdschlüssel nötig) = nur
    # Charaktere dieser Rasse sehen/wählen sie in der Erstellung/im LevelUp.
    # Analog zum bereits bestehenden Freigabe-Häkchen bei Rassen.
    nurFuerRasse: str = ""


class ZusatzfertigkeitUpdate(BaseModel):
    name: str | None = None
    kurzbeschreibung: str | None = None
    detailbeschreibung: str | None = None
    nurFuerRasse: str | None = None


class ZusatzfertigkeitResponse(BaseModel):
    id: str
    campaignId: str
    name: str
    kurzbeschreibung: str
    detailbeschreibung: str
    nurFuerRasse: str = ""


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
