"""Schemas für Achievements.

Siehe docs/wiki/entities/achievements.md für die vollständige Herleitung
(Meilenstein vs. Rekord, `einzigartig`-Häkchen, Belohnungsmechanik,
Trigger-Katalog). Zwei Knotentypen, analog zum Ereignisprotokoll-Stil:
`Achievement` (die Definition/der Katalogeintrag) und `AchievementVerleihung`
(eine einzelne Vergabe an eine Person, Papierkorb-Prinzip wie überall sonst).
"""

from typing import Literal

from pydantic import BaseModel, Field

AchievementArt = Literal["AUTO", "MANUELL"]

# Fester Code-Katalog, kein Freitext — die KI (oder die SL) kann keinen neuen
# Auslöser erfinden, nur einen der hier gelisteten wählen (siehe
# docs/wiki/entities/achievements.md, Trigger-Katalog).
AUSLOESE_ARTEN: list[str] = [
    "ERSTER_KILL",
    "MOERDER",
    "MEISTE_SCHADEN_GENOMMEN",
    "MEISTE_SCHADEN_VERTEILT",
    "ERSTER_KAUF",
    "ERSTE_VERHANDLUNG",
    "CHARAKTER_ERSTELLT",
    "GEHEIMNISTRAEGER",
    "ERSTER_BESITZ_ZIEL",
    "ERSTE_BESCHREIBUNG_ZIEL",
    "ERSTER_CRITTER",
    "ERSTE_DROHNE",
    "ENDBOSS_BESIEGT",
    "ERSTE_SITZUNG_UEBERLEBT",
]

# Trigger, die einen zielGegenstandId brauchen — die SL wählt beim Anlegen
# EINEN konkreten Gegenstand aus dem Katalog (z.B. β⁺-Isotop).
AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND: set[str] = {"ERSTER_BESITZ_ZIEL", "ERSTE_BESCHREIBUNG_ZIEL"}

BelohnungsArt = Literal["KEINE", "EP", "HINTERGRUND"]


class AchievementCreate(BaseModel):
    name: str
    beschreibung: str = ""
    icon: str = ""
    art: AchievementArt = "MANUELL"
    ausloeseArt: str | None = None
    einzigartig: bool = False
    belohnungsArt: BelohnungsArt = "KEINE"
    belohnungsMenge: int = Field(default=0, ge=0)
    belohnungsHintergrund: str | None = None
    zielGegenstandId: str | None = None


class AchievementUpdate(BaseModel):
    name: str | None = None
    beschreibung: str | None = None
    icon: str | None = None
    art: AchievementArt | None = None
    ausloeseArt: str | None = None
    einzigartig: bool | None = None
    belohnungsArt: BelohnungsArt | None = None
    belohnungsMenge: int | None = Field(default=None, ge=0)
    belohnungsHintergrund: str | None = None
    zielGegenstandId: str | None = None


class AchievementResponse(BaseModel):
    id: str
    name: str
    beschreibung: str = ""
    icon: str = ""
    art: AchievementArt = "MANUELL"
    ausloeseArt: str | None = None
    einzigartig: bool = False
    belohnungsArt: BelohnungsArt = "KEINE"
    belohnungsMenge: int = 0
    belohnungsHintergrund: str | None = None
    zielGegenstandId: str | None = None
    zielGegenstandName: str | None = None


class VerleihungCreate(BaseModel):
    """Manuelle Vergabe — der Auslöser-Kontext fehlt hier bewusst (siehe
    trigger.py für die Auto-Variante), die SL wählt Person + Achievement."""

    personId: str
    text: str = ""
    slNotiz: str = ""


class VerleihungResponse(BaseModel):
    id: str
    personId: str
    personName: str | None = None
    achievementId: str
    achievementName: str | None = None
    achievementIcon: str = ""
    achievementBeschreibung: str = ""
    zeitpunkt: str
    ingameZeitpunkt: str = ""
    sitzungId: str | None = None
    slNotiz: str = ""
    geloescht: bool = False
    text: str = ""
    abgeloest: bool = False


class VorschlagEintrag(BaseModel):
    """Ein offener AUTO-Trigger-Vorschlag — nichts gespeichert, live aus dem
    Ereignisprotokoll berechnet (siehe trigger.py)."""

    achievementId: str
    achievementName: str
    achievementIcon: str = ""
    personId: str
    personName: str
    # Kontext für den KI-Text, falls die SL den Vorschlag bestätigt
    # (sammle_kontext-Erweiterung, siehe trigger.py::kontext_fuer_vorschlag).
    kontextText: str = ""


class VorschlagAnwendenRequest(BaseModel):
    achievementId: str
    personId: str
    text: str = ""
    slNotiz: str = ""


class KiTextRequest(BaseModel):
    achievementId: str
    personId: str
    # Nur bei AUTO-Vorschlägen gefüllt — zusätzlicher Kontext zum Auslöser.
    kontextText: str = ""
