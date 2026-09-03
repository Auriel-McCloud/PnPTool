"""Schemas des Kampagnen-Wikis."""

from typing import Literal

from pydantic import BaseModel

SichtbarkeitModus = Literal["GM", "ALLE", "SPEZIFISCH"]


class SeiteCreate(BaseModel):
    titel: str
    # Leer anlegen ist der Normalfall: Titel eintippen, dann schreiben.
    inhalt: str = '{"type":"doc","content":[]}'
    parentId: str | None = None
    symbol: str = ""
    # Standard SL-geheim — eine Planungsseite, die versehentlich offen steht,
    # verrät den Plot.
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


class SeiteUpdate(BaseModel):
    titel: str | None = None
    inhalt: str | None = None
    symbol: str | None = None
    sortierung: int | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    # Bewusst nicht optional-mit-None-Bedeutung: siehe VerschiebeRequest.
    # Zum Verschieben gibt es eine eigene Route, damit "None" hier nicht
    # zweideutig ist (nicht gesetzt vs. auf oberste Ebene holen).


class VerschiebeRequest(BaseModel):
    """Seite umhängen. `parentId: null` heisst ausdrücklich: oberste Ebene."""

    parentId: str | None = None
    sortierung: int | None = None


class SeiteResponse(BaseModel):
    id: str
    titel: str
    inhalt: str
    parentId: str | None = None
    symbol: str = ""
    sortierung: int = 0
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    erstelltAm: str = ""
    aktualisiertAm: str = ""


class InhaltsverzeichnisEintrag(BaseModel):
    stufe: int
    text: str
    anker: str


class SeiteMitVerzeichnis(SeiteResponse):
    """Einzelabruf: Seite plus das aus ihren Überschriften erzeugte Verzeichnis."""

    inhaltsverzeichnis: list[InhaltsverzeichnisEintrag] = []


class BaumKnoten(BaseModel):
    """Seitenbaum ohne Inhalt — für Tabs und Seitenleiste.

    Ohne `inhalt`, weil der Baum bei jedem Seitenwechsel geladen wird und die
    Dokumente beliebig gross werden können.
    """

    id: str
    titel: str
    symbol: str = ""
    sortierung: int = 0
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    kinder: list["BaumKnoten"] = []


class FreigabeRequest(BaseModel):
    """Freigabe mehrerer Seiten auf einmal.

    `bisSeiteId` ist Marks "was bisher geschah": alle Seiten in Lesereihenfolge
    bis einschliesslich dieser freigeben. Alternativ `seitenIds` für eine
    ausdrückliche Auswahl.
    """

    bisSeiteId: str | None = None
    seitenIds: list[str] | None = None
    sichtbarkeit: SichtbarkeitModus = "ALLE"
    sichtbarFuer: list[str] = []


class FreigabeAntwort(BaseModel):
    freigegeben: int
    seitenIds: list[str] = []


class Rueckverweis(BaseModel):
    id: str
    titel: str


class BildAntwort(BaseModel):
    url: str
