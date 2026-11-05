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


def eigener_haupteintrag(teilnehmer: list[dict], person_id: str) -> dict | None:
    """Der eigene Kampf-Eintrag, nicht der Zusatzzug aus dem Reflex-Booster.

    Der Zusatzzug hat dieselbe personId, darf aber nicht die gemeldete
    Initiative überschreiben.
    """
    return next(
        (t for t in teilnehmer if t.get("personId") == person_id and not t.get("zusatzzug")),
        None,
    )


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


# Fehlercodes für Booster- und Hot-Aktionen. Die Route mappt sie auf HTTP.
FEHLER_KEIN_CHARAKTER = "kein_charakter"
FEHLER_KEINE_PERSON = "keine_person"
FEHLER_UNBEKANNT = "unbekannt"
FEHLER_NUR_SPIELER = "nur_spieler"


def waehle_person(
    rolle: str,
    eigene_person_id: str | None,
    ziel_person_id: str | None,
    ziel_person_type: str | None,
    *,
    schreiben: bool,
) -> tuple[str | None, str | None]:
    """Wen Booster und Hot ansprechen: (person_id, fehlercode).

    Der Spieler handelt immer für sich — eine fremde Angabe wird ignoriert,
    sonst könnte er den Nachbarn zünden. Die Spielleitung hat keinen eigenen
    Charakter und steuert die NPCs. Spielercharaktere entscheiden selbst;
    die SL bekommt deren Popups nicht und kann sie auch nicht beantworten.

    ``ziel_person_type is None`` heißt: die SL hat eine Id genannt, der
    Knoten fehlt. Ein leerer Typ am vorhandenen Knoten ist kein PC.
    Lesen ohne Ziel liefert (None, None) — leerer Status, kein Fehler.
    """
    if rolle != "GM":
        if not eigene_person_id:
            return None, FEHLER_KEIN_CHARAKTER
        return eigene_person_id, None
    if not ziel_person_id:
        if schreiben:
            return None, FEHLER_KEINE_PERSON
        return None, None
    if ziel_person_type is None:
        return None, FEHLER_UNBEKANNT
    if ziel_person_type == "PC":
        return None, FEHLER_NUR_SPIELER
    return ziel_person_id, None


def person_fehler_http(code: str) -> tuple[int, str]:
    """HTTP-Status und Text zu einem Fehlercode aus ``waehle_person``."""
    return {
        FEHLER_KEIN_CHARAKTER: (400, "Kein eigener Charakter"),
        FEHLER_KEINE_PERSON: (400, "Keine Person angegeben"),
        FEHLER_UNBEKANNT: (404, "Person nicht gefunden"),
        FEHLER_NUR_SPIELER: (403, "Spielercharaktere entscheiden das selbst"),
    }[code]


def melde_wert(erfolge: int) -> int:
    """Prüft einen von Hand gemeldeten Initiativwert."""
    if erfolge < 0:
        raise ValueError("Initiative kann nicht negativ sein")
    if erfolge > MAX_ERFOLGE:
        raise ValueError(f"Initiative unglaubwürdig hoch (höchstens {MAX_ERFOLGE})")
    return erfolge
