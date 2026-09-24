from typing import Literal

from pydantic import BaseModel

SichtbarkeitModus = Literal["GM", "ALLE", "SPEZIFISCH"]


class BildEintrag(BaseModel):
    """Ein Bild in der Galerie einer Entität."""
    url: str
    istPrimaer: bool = False


class KurzLangEintrag(BaseModel):
    """Ein Listeneintrag mit Kurzbeschreibung und ausformulierter Beschreibung.

    Genutzt für Fraktions-Ziele und -Ressourcen. Kurzbeschreibung (titel) wird
    in der Liste angezeigt, die lange Beschreibung nur auf Abruf — so bleibt
    die Liste kompakt, aber die Spielleitung kann jeden Eintrag ausformulieren.
    """
    titel: str = ""
    beschreibung: str = ""


class SichtbarkeitInput(BaseModel):
    modus: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


VISIBILITY_FIELDS = ["sichtbarkeit", "sichtbarFuer", "notizenSichtbarkeit", "notizenSichtbarFuer"]
VERBINDUNG_VISIBILITY_FIELDS = ["sichtbarkeit", "sichtbarFuer"]


# Ziele, denen eine KI Einfluss auf die Welt entzogen bzw. zugewiesen
# bekommen kann — echte Graphkanten statt Freitext, damit die Spielleitung
# ihr im Kampf gezielt einen echten Ort wegnehmen kann. Keine Personen:
# Einfluss auf einen Menschen ist im Tool bereits Beziehung/Handlung, kein
# Ressourcenwert. Verschoben von `app/begleiter/schemas.py` (20.09.2026,
# revidiert): eine KI ist jetzt eine echte Person (`istKI=true`) statt einer
# Begleiter-Art, das Konzept gehört daher hierher.
EinflussZielKind = Literal["Ort", "Fraktion", "Event", "Gegenstand"]


class EinflussEintrag(BaseModel):
    zielKind: EinflussZielKind
    zielId: str
    zielName: str
    stufe: int


class EinflussSetzen(BaseModel):
    zielKind: EinflussZielKind
    zielId: str
    stufe: int = 0


class PersonCreate(BaseModel):
    name: str
    personType: Literal["PC", "NPC"] = "NPC"
    description: str = ""
    notes: str = ""
    # Aussehen. Die Spielleitung kann es per Blitz an alle schicken.
    bildUrl: str = ""  # Legacy: einzelnes Bild (abwärtskompatibel)
    bilder: list[BildEintrag] = []  # NEU: Bildergalerie mit Primär-Flag
    # Ideenschmiede: Entwürfe sind noch nicht Teil der aktiven Kampagne
    istEntwurf: bool = False
    # --- Charakterbogen ---------------------------------------------------
    # Der eingeschlagene Weg entscheidet, was auf dem Blatt überhaupt
    # erscheint: Sphären und Hexkraft nur für Magier, NeuroWeaving nur für
    # Neuroweaver. Auf dem Blatt steht ausdrücklich "Hexkraft != NeuroWeaving",
    # beides zugleich geht also nicht. Ein eigenes Feld statt aus Hexkraft > 0
    # abzuleiten — sonst wäre ein frisch erstellter Magier mit Hexkraft 0 keiner.
    weg: Literal["KEINER", "MAGIER", "NEUROWEAVER"] = "KEINER"
    # Häretiker (24.09.2026, Marks Konzept): reines Flavor-Reskin für Magier,
    # gleichberechtigt bei der Erstellung wählbar — mechanisch 100% identisch
    # (gleiche Werte, gleiche Formeln, gleiche Sphären-Stufen). Technisch
    # bleibt `weg` dafür auf "MAGIER" stehen (keine Code-Verdopplung der
    # Magie-Mechanik in bogen.py/items/routes.py/ki/routes.py); dieses Feld
    # trägt nur, WELCHE Begriffe die Oberfläche zeigt: Hexkraft→Glauben,
    # Wilde Magie→Blasphemie, die 9 Sphären→Götternamen (siehe
    # traits/seed.py::HAERETIKER_LABELS, CLAUDE.md Punkt 14).
    magieFlavor: Literal["MAGIER", "HAERETIKER"] = "MAGIER"
    # Bestimmt Startwerte und Maxima bei der Erstellung (Mensch, Ork, Elf,
    # Zwerg, Troll). Frei als Text, weil Rassen dazukommen können.
    rasse: str = ""
    # Critter (20.09.2026, Marks Entscheidung): Tiere/Haustiere sind echte
    # NPCs mit dem vollen Charakterblatt statt eines eigenen Begleiter-Typs —
    # "wir machen critter zu richtigen NPCs". Die Verbindung zu ihrem Menschen
    # läuft über dieselbe BEGLEITET-Kante wie bei Sprite/Geist/KI, nur von
    # Person zu Person statt von Begleiter zu Person (siehe
    # app/entities/repository.py::critter_besitzer_setzen). Reines
    # Markierungsfeld, damit die Begleiter-Übersicht sie herausfiltern kann,
    # ohne jeden NPC nach einer BEGLEITET-Kante abzufragen.
    istCritter: bool = False
    # KI (20.09.2026, revidiert — Mark: "mach jetzt das Gleiche für die KI"):
    # eine Stadt-KI wie Babel ist wie Critter eine echte Person statt einer
    # eigenen Begleiter-Art, mit dem vollen Charakterblatt. Körperliche
    # Attribute ergeben für eine körperlose KI keinen Sinn — bei istKI=true
    # ersetzt die eigene Kategorie "AttributMatrix" (nur Matrix-Präsenz) die
    # Körperlich-Spalte auf dem Blatt (siehe traits/bogen.py::
    # sichtbare_kategorien, Charakterblatt.tsx). Einfluss auf Orte/Fraktionen/
    # Events/Gegenstände läuft über echte Graphkanten von der Person aus
    # (siehe entities/repository.py::person_einfluss_setzen).
    istKI: bool = False
    # Shop-System (22.09.2026, Kern-Baustein): ein Händler ist wie KI/Critter
    # eine echte Person, aber bewusst SCHLANK — kein Charakterblatt (Marks
    # Entscheidung), nur Name/Bild/Beschreibung + Sortiment (siehe
    # app/haendler/). Kontakt/Messenger läuft über das bestehende
    # KENNT-System, der Standort über dieselbe BEFINDET_SICH_AN-Kante wie bei
    # Party (app/haendler/repository.py).
    istHaendler: bool = False
    # Nur relevant bei istHaendler=true: auf welche Gegenstandstypen sich der
    # AUTOMATISCHE Shop-Bestand (Vorlagen mit automatischImShop=true) dieses
    # Händlers beschränkt. Leer = Gemischtwarenladen, zeigt alle passenden
    # Vorlagen. Gesetzt (z.B. ["Waffe"]) = nur diese Typen, egal wie
    # generisch die Vorlage sonst automatisch verteilt würde — Mark:
    # "bei einem Waffenladen sollte es schließlich keinen Brokkoli geben".
    # Explizit im Sortiment eingetragene Ware (VERKAUFT-Kante,
    # app/haendler/repository.py) ist davon unabhängig immer sichtbar.
    spezialisierung: list[str] = []
    # Shop-Frontend (24.09.2026, Marks Konzept): PHYSISCH zeigt Laden-Bild +
    # Händler-Portrait, Verhandeln ist möglich, Ware wird bei Kauf sofort
    # übergeben. DIGITAL zeigt eine schlichte Online-Shop-Ansicht (kein
    # Verhandeln, kein Laden-Bild), Kauf legt stattdessen eine Bestellung
    # an — die SL löst die Lieferung manuell per Knopf aus (kein fester
    # Termin), siehe app/haendler/repository.py::Bestellung.
    vertriebsart: Literal["PHYSISCH", "DIGITAL"] = "PHYSISCH"
    # Shop-Frontend (24.09.2026): eigenes Hintergrundbild je (physischem) Shop.
    shopHintergrundUrl: str = ""
    silhouette: str = "maennlich"
    # Zustand: abgehakte Kästchen. Die Obergrenze ist abgeleitet
    # (Gesundheit = 6 + Widerstandsfähigkeit, Willenskraft = Entschlossenheit
    # + Fassung) und wird berechnet, nicht gespeichert.
    # Schaden nach Art getrennt — Schlagschaden "/", schwerer "X",
    # aggravierter als durchgestrichenes X.
    schadenSchlag: int = 0
    schadenSchwer: int = 0
    schadenAggraviert: int = 0
    willenskraftVerbraucht: int = 0
    iceSchaden: int = 0
    # Erfahrung: gesamt vergeben und davon ausgegeben.
    erfahrung: int = 0
    erfahrungAusgegeben: int = 0
    # Extra-EP für diesen PC (individuelle Bonus-Punkte, zusätzlich zu
    # den kampagnenweiten EP). Nur erhöhbar, nicht senkbar.
    extraEP: int = 0
    willenskraftBonus: int = 0
    # Kopfzeile des Papierblatts: Konzept, Alter, Ambition, Verlangen, Ziel,
    # Kapital/Schulden. Reiner Text bzw. Zahlen, keine Regelmechanik.
    konzept: str = ""
    alter: str = ""
    ambition: str = ""
    verlangen: str = ""
    ziel: str = ""
    kapital: int = 0
    schulden: int = 0
    erstellungAbgeschlossen: bool = False

    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class PersonUpdate(BaseModel):
    name: str | None = None
    bildUrl: str | None = None
    bilder: list[BildEintrag] | None = None  # Bildergalerie
    istEntwurf: bool | None = None  # Verschieben zwischen Ideenschmiede und Kampagne
    weg: Literal["KEINER", "MAGIER", "NEUROWEAVER"] | None = None
    magieFlavor: Literal["MAGIER", "HAERETIKER"] | None = None
    rasse: str | None = None
    istCritter: bool | None = None
    istKI: bool | None = None
    istHaendler: bool | None = None
    spezialisierung: list[str] | None = None
    vertriebsart: Literal["PHYSISCH", "DIGITAL"] | None = None
    shopHintergrundUrl: str | None = None
    silhouette: str | None = None
    schadenSchlag: int | None = None
    schadenSchwer: int | None = None
    schadenAggraviert: int | None = None
    willenskraftVerbraucht: int | None = None
    iceSchaden: int | None = None
    erfahrung: int | None = None
    erfahrungAusgegeben: int | None = None
    extraEP: int | None = None
    willenskraftBonus: int | None = None
    konzept: str | None = None
    alter: str | None = None
    ambition: str | None = None
    verlangen: str | None = None
    ziel: str | None = None
    kapital: int | None = None
    schulden: int | None = None
    erstellungAbgeschlossen: bool | None = None
    personType: Literal["PC", "NPC"] | None = None
    description: str | None = None
    notes: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class PersonResponse(BaseModel):
    id: str
    name: str
    personType: str
    description: str
    notes: str
    bildUrl: str = ""
    bilder: list[BildEintrag] = []  # Bildergalerie
    # Ideenschmiede: Entwürfe sind noch nicht Teil der aktiven Kampagne
    istEntwurf: bool = False
    # Charakterbogen — Ausgangswerte greifen für Bestandsdaten, die diese
    # Felder noch nicht haben (Ersatz kommt aus dem Repository).
    weg: str = "KEINER"
    magieFlavor: str = "MAGIER"
    rasse: str = ""
    istCritter: bool = False
    istKI: bool = False
    istHaendler: bool = False
    spezialisierung: list[str] = []
    vertriebsart: str = "PHYSISCH"
    shopHintergrundUrl: str = ""
    silhouette: str = "maennlich"
    schadenSchlag: int = 0
    schadenSchwer: int = 0
    schadenAggraviert: int = 0
    willenskraftVerbraucht: int = 0
    iceSchaden: int = 0
    erfahrung: int = 0
    erfahrungAusgegeben: int = 0
    extraEP: int = 0
    willenskraftBonus: int = 0
    konzept: str = ""
    alter: str = ""
    ambition: str = ""
    verlangen: str = ""
    ziel: str = ""
    kapital: int = 0
    schulden: int = 0
    erstellungAbgeschlossen: bool = False
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


class OrtCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    bildUrl: str = ""  # Legacy
    bilder: list[BildEintrag] = []  # Bildergalerie
    istEntwurf: bool = False  # Ideenschmiede
    # Spotify-Playlist dieses Ortes/dieser Szene — startet automatisch, wenn
    # die aktive Party hierher wechselt (siehe app/spotify/).
    spotifyPlaylistUri: str = ""
    spotifyPlaylistName: str = ""
    spotifyPlaylistBild: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class OrtUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    bildUrl: str | None = None
    bilder: list[BildEintrag] | None = None  # Bildergalerie
    istEntwurf: bool | None = None  # Verschieben zwischen Ideenschmiede und Kampagne
    spotifyPlaylistUri: str | None = None
    spotifyPlaylistName: str | None = None
    spotifyPlaylistBild: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class OrtResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    bildUrl: str = ""
    bilder: list[BildEintrag] = []  # Bildergalerie
    istEntwurf: bool = False
    spotifyPlaylistUri: str = ""
    spotifyPlaylistName: str = ""
    spotifyPlaylistBild: str = ""
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


class EventCreate(BaseModel):
    title: str
    timestamp: str = ""
    description: str = ""
    notes: str = ""
    bildUrl: str = ""  # Legacy
    bilder: list[BildEintrag] = []  # Bildergalerie
    istEntwurf: bool = False  # Ideenschmiede
    spotifyPlaylistUri: str = ""
    spotifyPlaylistName: str = ""
    spotifyPlaylistBild: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class EventUpdate(BaseModel):
    title: str | None = None
    timestamp: str | None = None
    description: str | None = None
    notes: str | None = None
    bildUrl: str | None = None
    bilder: list[BildEintrag] | None = None  # Bildergalerie
    istEntwurf: bool | None = None  # Verschieben zwischen Ideenschmiede und Kampagne
    spotifyPlaylistUri: str | None = None
    spotifyPlaylistName: str | None = None
    spotifyPlaylistBild: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class EventResponse(BaseModel):
    id: str
    title: str
    timestamp: str
    description: str
    notes: str
    bildUrl: str = ""
    bilder: list[BildEintrag] = []  # Bildergalerie
    istEntwurf: bool = False
    spotifyPlaylistUri: str = ""
    spotifyPlaylistName: str = ""
    spotifyPlaylistBild: str = ""
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


EntityKind = Literal["Person", "Ort", "Event", "Gegenstand", "Fraktion"]


class FraktionCreate(BaseModel):
    name: str
    description: str = ""  # Was die Spielwelt über die Fraktion weiß/wahrnimmt
    # Ziele als Liste: jedes Vorhaben hat eine Kurzbeschreibung (titel) und
    # eine ausformulierte Beschreibung. Die Liste bleibt damit flexibel statt
    # ein einziger Freitext-Block.
    ziele: list[KurzLangEintrag] = []
    # Ressourcen als Liste, wie die Ziele: Miliz, Kapital, Zugang — jeder
    # Eintrag mit Kurzbeschreibung und, bei Bedarf, Ausführung.
    ressourcen: list[KurzLangEintrag] = []
    notes: str = ""
    bildUrl: str = ""  # Legacy
    bilder: list[BildEintrag] = []  # Bildergalerie
    istEntwurf: bool = False  # Ideenschmiede
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []
    # Gilt gemeinsam für notes, ziele und ressourcen — SL-Innenperspektive,
    # dieselbe Aufteilung wie bei Person/Ort/Event (zwei Sichtbarkeitsebenen,
    # nicht vier getrennte).
    notizenSichtbarkeit: SichtbarkeitModus = "GM"
    notizenSichtbarFuer: list[str] = []


class FraktionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    ziele: list[KurzLangEintrag] | None = None
    ressourcen: list[KurzLangEintrag] | None = None
    notes: str | None = None
    bildUrl: str | None = None
    bilder: list[BildEintrag] | None = None
    istEntwurf: bool | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    notizenSichtbarkeit: SichtbarkeitModus | None = None
    notizenSichtbarFuer: list[str] | None = None


class FraktionResponse(BaseModel):
    id: str
    name: str
    description: str
    ziele: list[KurzLangEintrag] = []
    ressourcen: list[KurzLangEintrag] = []
    notes: str
    bildUrl: str = ""
    bilder: list[BildEintrag] = []
    istEntwurf: bool = False
    sichtbarkeit: str
    sichtbarFuer: list[str]
    notizenSichtbarkeit: str
    notizenSichtbarFuer: list[str]


class VerbindungCreate(BaseModel):
    vonKind: EntityKind
    vonId: str
    zuKind: EntityKind
    zuId: str
    typ: str
    beschreibung: str = ""
    seit: str = ""
    bis: str = ""
    sichtbarkeit: SichtbarkeitModus = "GM"
    sichtbarFuer: list[str] = []


class VerbindungResponse(BaseModel):
    id: str
    vonKind: str
    vonId: str
    zuKind: str
    zuId: str
    typ: str
    beschreibung: str
    seit: str
    bis: str
    sichtbarkeit: str
    sichtbarFuer: list[str]


class FilterZiel(BaseModel):
    """Eine Entität, mit der tatsächlich mindestens eine Verbindung besteht."""

    id: str
    kind: str
    label: str
    anzahl: int


class FilterOptionen(BaseModel):
    """Womit sich eine Liste sinnvoll filtern lässt — aus dem echten Graphen.

    Bewusst kein fester Katalog von Beziehungsarten: die Spielleitung tippt
    den Typ frei ein ("Gegner", "Stammgast", "gehört zu"), und der Filter darf
    nur anbieten, was auch wirklich angelegt ist. Ein Dropdown mit erfundenen
    Vorschlägen führte sonst zu leeren Ergebnissen.
    """

    typen: list[str] = []
    ziele: list[FilterZiel] = []
