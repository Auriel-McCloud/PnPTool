"""Reine Matrix-Rechnung fürs Deaktivieren. Kein Neo4j.

Entschieden 01.11.2026, siehe docs/wiki/concepts/neuroweaving-decking.md.
"""

from __future__ import annotations

from app.items.waffenbonus import DEAKTIV_MODI

DECK_EINSTIEG = ("Brute Force", "Schleichen")
NAVIGATION = "Matrix-Navigation"
ELECTRONIC_WARFARE = "Electronic Warfare"
MATRIX_AKTIONEN = DECK_EINSTIEG + (NAVIGATION, ELECTRONIC_WARFARE)

# Eine Navigation-Probe gilt, sobald mindestens ein Erfolg da ist.
# Eine höhere Schwelle hat Mark nicht genannt.
NAVIGATION_MIN = 1


def leerer_stand() -> dict:
    return {"ice": {}, "ew": {}, "gesehen": {}, "aus": [], "offen": {}}


def netto(erfolge: int, ice: int) -> int:
    """Erfolge minus ICE vor dem Treffer, höchstens 3. Unter 1 ist 0."""
    return min(3, ueberschuss(erfolge, ice))


def ueberschuss(erfolge: int, ice: int) -> int:
    """Erfolge minus ICE vor dem Treffer. Kein Deckel. Unter 1 ist 0."""
    return max(0, int(erfolge) - max(0, int(ice)))


def willenskraft_rest(maximum: int, verbraucht: int) -> int:
    """Was der Neuroweaver noch nicht selbst ausgegeben hat. Das ist sein ICE-Deckel."""
    return max(0, int(maximum) - max(0, int(verbraucht)))


def ice_klemmen(gespeichert: int | None, maximum: int) -> int:
    """None heißt voll. Nie über dem aktuellen Maximum — ausgegebene Willenskraft fällt sofort weg."""
    deckel = max(0, int(maximum))
    if gespeichert is None:
        return deckel
    return min(deckel, max(0, int(gespeichert)))


def treffer_art(weg: str, matrix_hot: bool, ist_drohne: bool = False, ist_roboter: bool = False) -> str:
    """Neuroweaver: nur Schaden. Hot oder Roboter: Wahl. Fahrzeug und der Rest: nur schalten.

    Roboter ist eine Drohne, kein Fahrzeug. Die Wahl ist schalten oder der ganze
    Überschuss als Schlagschaden, nicht beides.
    """
    if ist_roboter:
        return "wahl"
    if ist_drohne:
        return "schalten"
    if weg == "NEUROWEAVER":
        return "schaden"
    if matrix_hot:
        return "wahl"
    return "schalten"


def ice_nach_treffer(aktuell: int, erfolge: int) -> int:
    """1 Erfolg nimmt 1 ICE. Unter 0 geht es nicht."""
    return max(0, int(aktuell) - max(0, int(erfolge)))


def ew_bonus(erfolge: int) -> int:
    """+1 je 2 Erfolge. 1 Erfolg gibt 0. Kein Deckel."""
    return max(0, int(erfolge)) // 2


def aufteilung_gueltig(punkte: int, runden: list[int]) -> bool:
    """Jeder Posten ist 1, 2 oder 3 und die Summe frisst höchstens die Punkte.

    Übrige Punkte müssen nicht verbraucht werden. 0 Posten ist erlaubt,
    dann wird nichts geschaltet — der ICE-Schaden bleibt trotzdem.
    """
    if punkte < 1 and runden:
        return False
    if any(r not in (1, 2, 3) for r in runden):
        return False
    return sum(runden) <= min(3, max(0, punkte))


def ice_maximum(basis: int, bonus: int) -> int:
    return max(0, int(basis)) + max(0, int(bonus))


def aktiver_bonus(ew: dict, person_id: str, runde: int) -> int:
    eintrag = ew.get(person_id)
    if not eintrag:
        return 0
    if int(eintrag.get("bisRunde") or 0) < int(runde):
        return 0
    return max(0, int(eintrag.get("bonus") or 0))


def ew_setzen(ew: dict, person_ids: list[str], bonus: int, runde: int) -> dict:
    """Bonus hält die laufende Runde und zwei weitere, also drei."""
    if bonus <= 0:
        return ew
    neu = dict(ew)
    bis = int(runde) + 2
    for pid in person_ids:
        alt = neu.get(pid) or {}
        neu[pid] = {
            "bonus": max(bonus, int(alt.get("bonus") or 0)),
            "bisRunde": max(bis, int(alt.get("bisRunde") or 0)),
        }
    return neu


def runde_auffuellen(stand: dict, neue_runde: int, maxima: dict[str, int]) -> dict:
    """Kampfrundenwechsel: ICE voll, abgelaufene Boni weg, Schalter ticken."""
    ew = {
        pid: eintrag
        for pid, eintrag in (stand.get("ew") or {}).items()
        if int(eintrag.get("bisRunde") or 0) >= int(neue_runde)
    }
    ice = {}
    for pid, basis in maxima.items():
        ice[pid] = ice_maximum(basis, aktiver_bonus(ew, pid, neue_runde))
    aus = []
    for eintrag in stand.get("aus") or []:
        rest = int(eintrag.get("runden") or 0) - 1
        if rest > 0:
            neu = dict(eintrag)
            neu["runden"] = rest
            aus.append(neu)
    return {
        "ice": ice,
        "ew": ew,
        "gesehen": dict(stand.get("gesehen") or {}),
        "aus": aus,
        "offen": dict(stand.get("offen") or {}),
    }


def zahl_sichtbar(ist_party: bool, gesehen: bool) -> bool:
    return ist_party or gesehen


def navigation_trifft(erfolge: int) -> bool:
    return int(erfolge) >= NAVIGATION_MIN


def abgefallene(vorher: list[dict], nachher: list[dict], art: str) -> list[dict]:
    """Einträge dieser Art, die im neuen Stand nicht mehr stehen."""
    bleibt = {e.get("id") for e in nachher}
    return [e for e in vorher if e.get("art") == art and e.get("id") not in bleibt]


def deaktiv_modus(gespeichert: str, kampf_fertigkeit: str) -> str:
    """Leer heißt Typ-Default: Schusswaffe komplett, alles andere nur Upgrades.

    „nicht“ ist explizit und schlägt den Typ-Default: die Waffe ist kein
    Matrix-Ziel. Klauen an einem Critter haben keinen Grund, hackbar zu sein.
    """
    if gespeichert in DEAKTIV_MODI:
        return gespeichert
    return "komplett" if kampf_fertigkeit == "Schusswaffen" else "upgrades"


def schalt_eintrag(zeile: dict) -> dict | None:
    """Eine Zeile aus der Besitz-Query, oder None wenn sie nicht hackbar ist.

    „nicht“ blendet die Waffe aus und auch Upgrades, die an ihr hängen.
    Cyberware mit demselben Modus (Klaue als Implantat markiert) ebenso.
    """
    if zeile.get("istAugment"):
        if deaktiv_modus(zeile.get("zielDeaktivModus") or "", zeile.get("zielKampfFertigkeit") or "") == "nicht":
            return None
        return {**zeile, "art": "upgrade"}
    modus = deaktiv_modus(zeile.get("deaktivModus") or "", zeile.get("kampfFertigkeit") or "")
    if modus == "nicht":
        return None
    typ = zeile.get("typ") or ""
    if typ == "Waffe":
        if modus == "komplett":
            return {**zeile, "art": "waffe"}
        return None
    if typ == "Cyberware":
        return {**zeile, "art": "cyber"}
    if typ == "Cyberdeck":
        return {**zeile, "art": "deck"}
    if typ == "Riggerkonsole":
        return {**zeile, "art": "konsole"}
    return None
