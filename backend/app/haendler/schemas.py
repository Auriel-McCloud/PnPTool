"""Shop-System: Sortiment und Kauf. Kern-Baustein (22.09.2026), siehe
CLAUDE.md Punkt 1 und docs/api/haendler.md.

Ein Händler ist KEIN eigenes Entitäts-Label — er ist ein `Person`-Knoten mit
`istHaendler=true` (analog `istKI`/`istCritter`, siehe
app/entities/schemas.py). Anlegen/Bearbeiten läuft daher über die
bestehenden `/personen`-Routen (`app/entities/routes.py`); dieses Modul deckt
nur das Shop-spezifische ab: Sortiment (welche Ware zu welchem Preis) und
Kaufen (Guthaben prüfen, Ware übergeben).
"""

from pydantic import BaseModel, Field
from typing import Literal


class SortimentEintrag(BaseModel):
    """Eine Ware im Sortiment eines Händlers — entweder explizit über eine
    VERKAUFT-Kante eingetragen, oder automatisch aus dem globalen Katalog
    (Vorlage mit automatischImShop=true, passend zur Spezialisierung)."""

    gegenstandId: str
    name: str
    bildUrl: str
    typ: str
    preis: int
    # Unendlich verfügbar (Vorlage) oder ein einziges Exemplar, das nach dem
    # Kauf aus dem Sortiment verschwindet.
    istVorlage: bool
    # Ob diese Ware explizit vom SL eingetragen wurde oder automatisch aus
    # dem globalen Katalog stammt (nur zur Anzeige im SL-Editor: automatische
    # Einträge lassen sich nicht direkt entfernen, nur über die Vorlage
    # selbst oder die Spezialisierung des Händlers).
    automatisch: bool
    # Sonderangebot (24.09.2026): nur bei explizit eingetragener Ware
    # möglich (Rabatt braucht eine VERKAUFT-Kante als Träger) — 0 = kein
    # Rabatt. Der tatsächliche Kaufpreis wird serverseitig aus preis und
    # rabattProzent berechnet (repository.py::effektiver_preis), preis oben
    # bleibt der Grundpreis für die Anzeige ("durchgestrichen").
    rabattProzent: int = 0
    rabattHinweis: str = ""


class SortimentHinzufuegenRequest(BaseModel):
    gegenstandId: str
    # None = Grundpreis des Gegenstands übernehmen. Explizit gesetzt erlaubt
    # Auf-/Abschlag (Schwarzmarkt teurer, Kontakt-Rabatt günstiger).
    preis: int | None = None


class KaufRequest(BaseModel):
    gegenstandId: str
    # Nur von der Spielleitung genutzt — ein Spieler kauft immer für den
    # eigenen Charakter, dasselbe Muster wie beim Messenger
    # (kontakte/routes.py::nachricht_senden).
    kaeuferPersonId: str | None = None


class KaufResponse(BaseModel):
    # Bei sofortiger Übergabe (physischer Shop) gesetzt. Bei digitalem Kauf
    # None — die Ware existiert dem Spieler gegenüber noch nicht, siehe
    # bestellung.
    gegenstand: dict | None = None
    kapitalNeu: int
    # Nur bei digitalem Kauf gesetzt (Vertriebsart DIGITAL): die angelegte
    # Bestellung, die SL löst die tatsächliche Lieferung später manuell aus
    # (siehe BestellungResponse, POST .../bestellungen/{id}/liefern).
    bestellung: dict | None = None


class RabattRequest(BaseModel):
    """Sonderangebot auf einen expliziten Sortiment-Eintrag. prozent=0 nimmt
    den Rabatt wieder weg (Normalpreis)."""

    prozent: int = Field(ge=0, le=95)
    hinweis: str = ""


class BestellungResponse(BaseModel):
    """Eine Online-Bestellung bei einem digitalen Händler (Vertriebsart
    DIGITAL) — Ware kommt nicht sofort, die SL gibt die Lieferung manuell
    frei (kein fester Termin, Marks Vorgabe 24.09.2026: "nur ein Knopf
    'jetzt liefern'"). Kapital wird bereits bei der Bestellung abgezogen,
    nicht erst bei Lieferung."""

    id: str
    haendlerId: str
    haendlerName: str
    kaeuferPersonId: str
    gegenstandId: str
    gegenstandName: str
    preis: int
    status: Literal["OFFEN", "GELIEFERT"] = "OFFEN"
    bestelltAm: str = ""
    geliefertAm: str = ""


class HaendlerEintrag(BaseModel):
    """Schlanke Übersicht für Kachel/Kontaktliste — kein Charakterblatt
    (Marks Entscheidung: Händler bleiben bewusst schlank)."""

    id: str
    name: str
    bildUrl: str
    beschreibung: str
    spezialisierung: list[str]
    vertriebsart: str
    shopHintergrundUrl: str = ""
    ortId: str | None = None
    ortName: str | None = None
    sichtbarkeit: str
    sichtbarFuer: list[str]


class StandortRequest(BaseModel):
    ortId: str | None = None


class AlltagswunschRequest(BaseModel):
    """Spieler fragt einen Verkäufer nach einem Alltagsgegenstand, den es im
    Sortiment nicht gibt (Marks Beispiel: Panzerklebeband)."""

    text: str = Field(min_length=1, max_length=300)


class AlltagswunschResponse(BaseModel):
    """Ein KI-bewerteter Alltagsgegenstand-Wunsch, siehe alltagswunsch.py.

    AUTO_ABGELEHNT = die KI hat sofort erkannt, dass es Kampf-/Sicherheits-
    ausrüstung wäre (nie automatisch erzeugt) — die SL sieht diesen Fall gar
    nicht erst, es wird niemand mit unsinnigen Anfragen behelligt."""

    id: str
    haendlerId: str
    haendlerName: str
    spielerPersonId: str
    text: str
    status: Literal["OFFEN", "ANGENOMMEN", "ABGELEHNT", "AUTO_ABGELEHNT"] = "OFFEN"
    vorschlagName: str
    vorschlagTyp: str
    vorschlagBeschreibung: str = ""
    vorschlagPreis: int
    ablehnungsGrund: str = ""
    gegenstandId: str | None = None
    erstelltAm: str = ""
    beantwortetAm: str = ""


class AlltagswunschAntwortRequest(BaseModel):
    """SL-Entscheidung — Name/Beschreibung/Preis lassen sich vor der Annahme
    noch anpassen (die KI schätzt nur, die SL hat das letzte Wort)."""

    angenommen: bool
    name: str = ""
    beschreibung: str = ""
    preis: int = 0
    ablehnungsGrund: str = ""
