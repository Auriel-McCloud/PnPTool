"""Initiative: Pool berechnen, Wert melden, wer darf das.

Marks Ablauf am Tisch:

1. Die Spielleitung schickt die Warnung *"Würfelt für Initiative!"*.
2. Jeder Spieler sieht **seinen** Pool (Geistesschärfe + Geschicklichkeit +
   Cyberware) und würfelt **physisch**.
3. Er tippt die **Anzahl Erfolge** ein.
4. Der Wert erscheint sofort in der Initiativliste der Spielleitung.

Die Spielleitung kann die Initiative ihrer NPCs digital würfeln lassen
(`digitalesWuerfelnSL`) — das ist die ausdrückliche Ausnahme.
"""

from app.traits.bogen import initiative as _initiative_formel
from app.wuerfel.logic import MAX_POOL

# Höchster meldbarer Wert. Selbst bei lauter Zehnen gibt ein Pool höchstens
# das Doppelte an Erfolgen — mehr ist ein Tippfehler.
MAX_ERFOLGE = MAX_POOL * 2


def initiative_pool(werte: dict[str, int], cyberware_mod: int = 0) -> int:
    """Wie viele Würfel dieser Charakter für die Initiative wirft.

    Nutzt dieselbe Formel wie der Charakterbogen (`traits/bogen.py`), damit
    die Zahl im Kampf nicht von der auf dem Blatt abweicht.
    """
    return max(0, _initiative_formel(werte, cyberware_mod))


def darf_melden(rolle: str, eigene_person_id: str | None, ziel_person_id: str | None) -> bool:
    """Nur für den eigenen Charakter — die Spielleitung für alle.

    Ohne diese Prüfung trüge ein Spieler dem Nachbarn eine 0 ein. Ein
    Teilnehmer ohne Person ("Wachmann 1") gehört niemandem und bleibt für
    Spieler tabu.
    """
    if rolle == "GM":
        return True
    if not eigene_person_id or not ziel_person_id:
        return False
    return eigene_person_id == ziel_person_id


def melde_wert(erfolge: int) -> int:
    """Prüft einen von Hand gemeldeten Initiativwert."""
    if erfolge < 0:
        raise ValueError("Initiative kann nicht negativ sein")
    if erfolge > MAX_ERFOLGE:
        raise ValueError(f"Initiative unglaubwürdig hoch (höchstens {MAX_ERFOLGE})")
    return erfolge
