from app.entities.schemas import SichtbarkeitModus
from pydantic import BaseModel


class GegenstandCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    typ: str = "Sonstiges"
    preis: int = 0
    # Punkte-Bonus (0-7, wie Waffenschaden/Rüstungsbonus im Regeln-Sheet),
    # nur relevant wenn typ Waffe/Rüstung ist, aber generisch gespeichert.
    kraft: int = 0
    # Freie Zusatzeigenschaften für alles, was kein eigenes Feld hat (Munition,
    # Schadensart, ...) — bewusst nicht als starres Schema pro Typ, damit neue
    # Gegenstandsarten keine Backend-Änderung brauchen.
    eigenschaften: dict[str, str] = {}
    # MacGuffins/plot-relevante Gegenstände können als eigener Knoten im
    # Beziehungsgraph erscheinen (normale Gegenstände wie ein Hemdknopf nicht).
    zeigeInGraph: bool = False
    # Einzigartig = genau ein Exemplar in der Welt (z.B. "Das Amulett von
    # Neotopia"), rein thematisch/für die Lore. Unabhängig davon: hatMenge
    # steuert, ob überhaupt eine Stückzahl geführt wird — z.B. ist ein Seil
    # nicht einzigartig, aber trotzdem muss niemand zählen wie viele man hat.
    # Erst wenn hatMenge=true UND nicht einzigartig ergibt "menge" wirklich
    # Sinn (z.B. Munition: jede besitzende Person führt ihre eigene Menge,
    # bewusst noch keine geteilte Vorlage über Personen hinweg — das wäre erst
    # für einen echten Shop-Katalog nötig).
    einzigartig: bool = True
    hatMenge: bool = False
    menge: int = 1
    # Markiert diesen Gegenstand als Vorlage: kann per "Zuweisen" beliebig oft
    # als unabhängige, individualisierbare Kopie an eine Person vergeben werden
    # (z.B. ein Pistolenmodell, das zwei Spieler kaufen und dann unterschiedlich
    # aufrüsten). Die Vorlage selbst bleibt dabei unverändert bestehen.
    istVorlage: bool = False
    # Seltenheit 1 (überall verfügbar) bis 5 (nur Speziallabor/Schwarzmarkt).
    # Wird später für automatische Shop-Bestückung genutzt (noch nicht gebaut).
    seltenheit: int = 1
    # Soll dieser Gegenstand automatisch im Angebot von Shops (Orten mit
    # passender Seltenheitsstufe) auftauchen, sobald es Shops gibt? Reines
    # Datenfeld ohne Logik — die automatische Shop-Bestückung selbst ist noch
    # nicht gebaut (Phase 5), siehe CLAUDE.md.
    automatischImShop: bool = False
    # Wird beim Anlegen automatisch gesetzt (PC-Besitzer -> nur für ihn sichtbar,
    # NPC-Besitzer -> SL-geheim), falls hier nicht explizit übersteuert.
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class GegenstandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    typ: str | None = None
    preis: int | None = None
    kraft: int | None = None
    eigenschaften: dict[str, str] | None = None
    zeigeInGraph: bool | None = None
    einzigartig: bool | None = None
    hatMenge: bool | None = None
    menge: int | None = None
    istVorlage: bool | None = None
    seltenheit: int | None = None
    automatischImShop: bool | None = None
    bildUrl: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None


class ZuweisenRequest(BaseModel):
    zielPersonId: str


class GegenstandResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    typ: str
    preis: int
    kraft: int
    eigenschaften: dict[str, str]
    zeigeInGraph: bool
    einzigartig: bool
    hatMenge: bool
    menge: int
    istVorlage: bool
    seltenheit: int
    automatischImShop: bool
    bildUrl: str
    sichtbarkeit: str
    sichtbarFuer: list[str]


class GegenstandMitBesitzer(GegenstandResponse):
    ownerId: str
    ownerName: str
    ownerPersonType: str
