from typing import Literal

from pydantic import BaseModel

LexikonKategorie = Literal["welt", "fauna", "flora", "objekte"]


class LexikonEintrag(BaseModel):
    id: str
    kategorie: LexikonKategorie
    name: str
    bildUrl: str
    # Platzhaltertext statt echter Beschreibung, solange sichtbarkeit noch
    # GM ist — Existenz (Name+Bild) ist entdeckt, Inhalt noch nicht
    # freigegeben (siehe docs/wiki/entities/spieler-lexikon.md).
    beschreibung: str
    beschreibungSichtbar: bool
    favorisiert: bool
    entdecktSeit: str
    # Rang fuer "In meiner Naehe"-Sortierung: 0 = aktueller Aufenthaltsort,
    # steigend mit struktureller Entfernung, 9999 = kein Pfad/Party nirgendwo.
    naehe: int


class FavorisierenRequest(BaseModel):
    zielId: str
