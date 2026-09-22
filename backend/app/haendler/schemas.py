"""Shop-System: Sortiment und Kauf. Kern-Baustein (22.09.2026), siehe
CLAUDE.md Punkt 1 und docs/api/haendler.md.

Ein Händler ist KEIN eigenes Entitäts-Label — er ist ein `Person`-Knoten mit
`istHaendler=true` (analog `istKI`/`istCritter`, siehe
app/entities/schemas.py). Anlegen/Bearbeiten läuft daher über die
bestehenden `/personen`-Routen (`app/entities/routes.py`); dieses Modul deckt
nur das Shop-spezifische ab: Sortiment (welche Ware zu welchem Preis) und
Kaufen (Guthaben prüfen, Ware übergeben).
"""

from pydantic import BaseModel


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
    gegenstand: dict
    kapitalNeu: int


class HaendlerEintrag(BaseModel):
    """Schlanke Übersicht für Kachel/Kontaktliste — kein Charakterblatt
    (Marks Entscheidung: Händler bleiben bewusst schlank)."""

    id: str
    name: str
    bildUrl: str
    beschreibung: str
    spezialisierung: list[str]
    ortId: str | None = None
    ortName: str | None = None
    sichtbarkeit: str
    sichtbarFuer: list[str]


class StandortRequest(BaseModel):
    ortId: str | None = None
