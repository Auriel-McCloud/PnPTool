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
    # Cyberwall eines Commlinks: bestimmt die Matrix-Verteidigung (I.C.E.)
    # seines Trägers. Nur bei typ "Commlink" von Belang. 200¥ je Punkt bis 5,
    # darüber 500¥ (siehe docs/regeln-neotopia.md).
    cyberwall: int = 0
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
    # Invariante: istVorlage <=> kein Besitzer. Wird beim Anlegen serverseitig
    # anhand dessen erzwungen, ob ein owner_person_id übergeben wurde — dieser
    # Wert hier wird für die person-gescopte Route ignoriert.
    istVorlage: bool = False
    # Seltenheit 1 (überall verfügbar) bis 5 (nur Speziallabor/Schwarzmarkt).
    # Wird später für automatische Shop-Bestückung genutzt (noch nicht gebaut).
    seltenheit: int = 1
    # Soll dieser Gegenstand automatisch im Angebot von Shops (Orten mit
    # passender Seltenheitsstufe) auftauchen, sobald es Shops gibt? Reines
    # Datenfeld ohne Logik — die automatische Shop-Bestückung selbst ist noch
    # nicht gebaut (Phase 5), siehe CLAUDE.md.
    automatischImShop: bool = False
    # Wo der Gegenstand steckt: AUSGERUESTET (angelegt/getragen), RUCKSACK
    # (mitgeführt) oder GELAGERT (an einem Ort oder in einem Fahrzeug — dann
    # zeigt eine :LIEGT_IN-Beziehung auf das Ziel). Das meiste, was man
    # besitzt, trägt man mit sich, daher RUCKSACK als Ausgangswert.
    ablage: str = "RUCKSACK"
    # Ob etwas anderes hineinpasst. **Nicht** aus dem Typ abgeleitet: ein
    # Motorrad ist ein Fahrzeug ohne Stauraum, eine Kiste hat Stauraum ohne
    # Räder. Ohne Angabe entscheidet das Repository nach dem Typ.
    istBehaelter: bool | None = None
    # Blatt für Drohne/Fahrzeug/Sprite/Geist (Neotopia.xlsx). Die Stufe wird
    # beim Kauf frei auf diese Werte und die Fertigkeiten verteilt.
    stufe: int = 0
    widerstand: int = 0
    angriff: int = 0
    agilitaet: int = 0
    fahrzeugFertigkeiten: dict[str, int] = {}
    # Eigengewicht in kg. 0 = vernachlässigbar (Ausweis, Datenchip).
    gewicht: float = 0.0
    # Wie viel dieser Gegenstand aufnehmen kann, in kg. 0 = kein Behälter.
    # Bei Personen ergibt sich die Traglast stattdessen aus einem Attribut,
    # siehe campaigns/repository.py (EINSTELLUNGEN_DEFAULTS).
    kapazitaet: float = 0.0
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
    cyberwall: int | None = None
    eigenschaften: dict[str, str] | None = None
    zeigeInGraph: bool | None = None
    einzigartig: bool | None = None
    hatMenge: bool | None = None
    menge: int | None = None
    # istVorlage bewusst NICHT hier: ob ein Gegenstand eine Vorlage ist, ergibt
    # sich ausschließlich daraus, ob er einen Besitzer hat (siehe Besitzer
    # wechseln/Vorlage machen/Zuweisen-Endpoints) — kein direktes Umschalten
    # per PATCH, sonst könnten owned+istVorlage-Widersprüche entstehen.
    seltenheit: int | None = None
    automatischImShop: bool | None = None
    gewicht: float | None = None
    kapazitaet: float | None = None
    istBehaelter: bool | None = None
    stufe: int | None = None
    widerstand: int | None = None
    angriff: int | None = None
    agilitaet: int | None = None
    fahrzeugFertigkeiten: dict[str, int] | None = None
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
    cyberwall: int
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
    ablage: str
    gewicht: float
    kapazitaet: float
    istBehaelter: bool = False
    stufe: int = 0
    widerstand: int = 0
    angriff: int = 0
    agilitaet: int = 0
    fahrzeugFertigkeiten: dict[str, int] = {}
    # Nur bei GELAGERT gesetzt: worin bzw. wo der Gegenstand liegt.
    ablageZielId: str | None = None
    ablageZielName: str | None = None
    ablageZielKind: str | None = None


class GegenstandMitBesitzer(GegenstandResponse):
    # Vorlagen haben keinen Besitzer (siehe istVorlage-Kommentar in
    # GegenstandUpdate) — daher optional statt Pflichtfeld.
    ownerId: str | None = None
    ownerName: str | None = None
    ownerPersonType: str | None = None


class AblageRequest(BaseModel):
    """Umlegen eines Gegenstands.

    `zielId` ist nur bei ablage="GELAGERT" von Belang und wird sonst
    ignoriert; ohne Ziel gilt der Gegenstand als unbestimmt gelagert.
    """

    ablage: str
    zielId: str | None = None


class AblageZiel(BaseModel):
    id: str
    name: str
    # "Ort" oder "Gegenstand" — bestimmt nur die Darstellung
    kind: str
