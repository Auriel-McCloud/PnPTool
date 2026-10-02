"""Spieler-Notizen: privater Schmierzettel, kein Wiki.

Kein Kampagnen-Wissen, keine Freigabe, keine Verknüpfungen. Nur der
Spieler-Zugang sieht seine eigenen Einträge — die Spielleitung hat an
jeder Entität bereits Notizfelder.
"""

from pydantic import BaseModel, field_validator

LEERES_DOKUMENT = '{"type":"doc","content":[]}'


class SpielerNotizCreate(BaseModel):
    titel: str
    inhalt: str = LEERES_DOKUMENT

    @field_validator("titel")
    @classmethod
    def titel_nicht_leer(cls, v: str) -> str:
        sauber = v.strip()
        if not sauber:
            raise ValueError("Titel darf nicht leer sein")
        return sauber


class SpielerNotizUpdate(BaseModel):
    titel: str | None = None
    inhalt: str | None = None

    @field_validator("titel")
    @classmethod
    def titel_nicht_leer(cls, v: str | None) -> str | None:
        if v is None:
            return v
        sauber = v.strip()
        if not sauber:
            raise ValueError("Titel darf nicht leer sein")
        return sauber


class SpielerNotizResponse(BaseModel):
    id: str
    titel: str
    inhalt: str
    erstelltAm: str
    geaendertAm: str
