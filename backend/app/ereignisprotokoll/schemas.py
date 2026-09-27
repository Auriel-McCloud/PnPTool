"""Schemas für das Ereignisprotokoll (Sitzungs-Log).

Siehe docs/wiki/entities/ereignisprotokoll.md für die vollständige Herleitung.
Jede Kategorie ist ein eigener Knotentyp mit gemeinsamen Basis-Feldern
(zeitpunkt, ingameZeitpunkt, sitzungId, slNotiz, geloescht) — kein
generischer "typ"-Knoten, Marks ausdrückliche Entscheidung (passt zum
bestehenden Projektstil: keine allgemeinen Felder für Sonderfälle).
"""

from typing import Literal

from pydantic import BaseModel, Field


class BasisFelder(BaseModel):
    """Gemeinsame Felder jeder Log-Kategorie — nie direkt genutzt, nur geerbt."""

    ingameZeitpunkt: str = ""
    sitzungId: str | None = None
    slNotiz: str = ""


# --- Sitzung -------------------------------------------------------------


class SitzungCreate(BaseModel):
    datum: str  # echtes Kalenderdatum (YYYY-MM-DD), Pflicht
    ingameDatum: str = ""  # Freitext-Platzhalter, echtes Kalendersystem folgt später
    titel: str = ""
    notiz: str = ""


class SitzungUpdate(BaseModel):
    datum: str | None = None
    ingameDatum: str | None = None
    titel: str | None = None
    notiz: str | None = None


class SitzungResponse(BaseModel):
    id: str
    datum: str
    ingameDatum: str = ""
    titel: str = ""
    notiz: str = ""
    erstelltAm: str = ""


# --- KiProtokollEintrag ---------------------------------------------------


class KiProtokollEintragCreate(BasisFelder):
    anlass: str
    prompt: str = ""
    antwortText: str
    uebernommen: bool = False
    betrifftId: str | None = None


class KiProtokollEintragResponse(KiProtokollEintragCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    betrifftName: str | None = None
    betrifftKind: str | None = None


# --- GegenstandsBewegung ---------------------------------------------------

GegenstandsBewegungArt = Literal[
    "GEFUNDEN", "GEKAUFT", "VERKAUFT", "WEITERGEGEBEN",
    "GESTOHLEN", "ZERSTOERT", "REPARIERT", "ENTSORGT", "SONSTIGES",
]


class GegenstandsBewegungCreate(BasisFelder):
    art: GegenstandsBewegungArt
    gegenstandId: str
    alterBesitzerId: str | None = None
    neuerBesitzerId: str | None = None
    ortId: str | None = None
    ortKind: Literal["Ort", "Event"] | None = None
    handelId: str | None = None


class GegenstandsBewegungResponse(GegenstandsBewegungCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    gegenstandName: str | None = None
    alterBesitzerName: str | None = None
    neuerBesitzerName: str | None = None


# --- GeldBewegung -----------------------------------------------------------

GeldBewegungArt = Literal["HANDEL", "WEITERGABE", "NPC_BELOHNUNG", "DIEBSTAHL", "AUSGABE", "SONSTIGES"]


class GeldBewegungCreate(BasisFelder):
    betrag: int
    art: GeldBewegungArt
    vonPersonId: str | None = None
    anPersonId: str | None = None
    handelId: str | None = None


class GeldBewegungResponse(GeldBewegungCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    vonPersonName: str | None = None
    anPersonName: str | None = None


# --- Aufenthalt --------------------------------------------------------------


class AufenthaltCreate(BasisFelder):
    partyId: str | None = None
    personId: str | None = None
    ortId: str
    ortKind: Literal["Ort", "Event"]


class AufenthaltResponse(AufenthaltCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    partyName: str | None = None
    personName: str | None = None
    ortName: str | None = None


# --- NpcWissenszuwachs --------------------------------------------------------


class NpcWissenszuwachsCreate(BasisFelder):
    npcPersonId: str
    wieErfahren: str
    ausloeserId: str | None = None


class NpcWissenszuwachsResponse(NpcWissenszuwachsCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    npcName: str | None = None
    ausloeserName: str | None = None


# --- KampfLogEintrag -----------------------------------------------------------

KampfLogArt = Literal["TREFFER", "KRITISCH", "BEWUSSTLOS", "TOD", "GEFLOHEN", "KAMPFENDE"]
RuestungsArtLog = Literal["schlag", "schwer", "aggraviert"]


class KampfLogEintragCreate(BasisFelder):
    kampfId: str = ""
    runde: int = 0
    art: KampfLogArt
    hpArt: RuestungsArtLog | None = None
    hpMenge: int = 0
    kaestchenSchaden: int = 0
    angreiferPersonId: str | None = None
    zielPersonId: str | None = None


class KampfLogEintragResponse(KampfLogEintragCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    angreiferName: str | None = None
    zielName: str | None = None


# --- VerhandlungsAusgang -----------------------------------------------------


class VerhandlungsAusgangCreate(BasisFelder):
    verhandlungId: str
    art: str
    angenommen: bool
    gesamtbetrag: int = 0
    positionenJson: str = "[]"
    angebotenVonPersonId: str | None = None
    empfaengerPersonId: str


class VerhandlungsAusgangResponse(VerhandlungsAusgangCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    empfaengerName: str | None = None


# --- CharakterEntwicklung ------------------------------------------------------

CharakterEntwicklungArt = Literal["STEIGERUNG", "WILLENSKRAFT", "ERFAHRUNG_VERGEBEN", "RASSE_GEAENDERT"]


class CharakterEntwicklungCreate(BasisFelder):
    personId: str
    art: CharakterEntwicklungArt
    traitDefId: str | None = None
    traitName: str | None = None
    alt: str = ""
    neu: str = ""
    kostenOderMenge: int = 0


class CharakterEntwicklungResponse(CharakterEntwicklungCreate):
    id: str
    zeitpunkt: str
    geloescht: bool = False
    personName: str | None = None


# --- Zeitleiste ---------------------------------------------------------------


class ZeitleisteEintrag(BaseModel):
    """Ein Eintrag beliebiger Kategorie, generisch für die gemeinsame Übersicht."""

    kategorie: str
    id: str
    zeitpunkt: str
    ingameZeitpunkt: str = ""
    sitzungId: str | None = None
    slNotiz: str = ""
    daten: dict = Field(default_factory=dict)


class KorrekturInput(BaseModel):
    """Nachträgliche SL-Korrektur eines Log-Eintrags — Papierkorb-Konvention,
    kein Hard-Delete. Feldnamen sind je Kategorie unterschiedlich, deshalb
    ein freies dict statt eines festen Schemas."""

    felder: dict = Field(default_factory=dict)


class LoeschenInput(BaseModel):
    geloescht: bool = True
