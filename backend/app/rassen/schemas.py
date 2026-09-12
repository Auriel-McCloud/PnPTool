from pydantic import BaseModel, Field


class RasseCreate(BaseModel):
    """Eine neue Rasse aus dem Baukasten.

    Der Schwerpunkt liegt bewusst allein auf den **Attributen** (Marks
    Vorgabe): Modifikatoren und freie Punkte. Fertigkeiten, Sonderfähigkeiten
    oder Regelvorteile gibt es nicht — sonst wäre die Balance nicht mehr
    nachrechenbar (siehe `balance.py`).
    """

    name: str
    beschreibung: str = ""
    # Attributname -> Modifikator, positiv wie negativ. Wirkt auf Startwert,
    # Erstellungs-Maximum UND Lebensmaximum (Marks Entscheidung 11.09.2026:
    # ein Troll kommt bei Körperkraft dauerhaft auf 6+2=8).
    modifikatoren: dict[str, int] = {}
    # Die drei Kontingente, frei auf die Attributspalten verteilbar.
    freiePunkte: list[int] = []
    sortOrder: int = 0


class RasseUpdate(BaseModel):
    name: str | None = None
    beschreibung: str | None = None
    modifikatoren: dict[str, int] | None = None
    freiePunkte: list[int] | None = None
    sortOrder: int | None = None
    # bildUrl bewusst nicht hier: das Bild kommt über den Upload-Endpunkt,
    # wie bei Gegenständen und Personen auch.


class Bilanz(BaseModel):
    """Was der Baukasten über die Ausgewogenheit sagt — gerechnet in
    `balance.py`, damit die Regel nur an einer Stelle steht."""

    punkte: int
    vorteile: int
    nachteile: int
    summe: int
    budget: int
    nachteileSoll: int
    stimmt: bool
    hinweise: list[str]


class RasseResponse(BaseModel):
    id: str
    name: str
    beschreibung: str
    bildUrl: str
    modifikatoren: dict[str, int]
    freiePunkte: list[int]
    sortOrder: int
    # Kommt vom Server mit, damit Übersicht und Editor dieselbe Bewertung
    # zeigen wie die Prüfung beim Speichern.
    bilanz: Bilanz
    # Nur in der Katalogansicht gefüllt: ob diese Rasse in der aufrufenden
    # Kampagne freigegeben ist.
    freigegeben: bool = False


class FreigabeRequest(BaseModel):
    """Die vollständige Auswahl — nicht ein einzelnes Häkchen. Sonst müsste
    die Oberfläche mitzählen, was sie gerade an- und abgewählt hat."""

    rasseIds: list[str] = Field(default_factory=list)
