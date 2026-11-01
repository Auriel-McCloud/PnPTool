"""Reine Matrix-Rechnung fürs Deaktivieren. Kein Neo4j.

Entschieden 01.11.2026, siehe docs/wiki/concepts/neuroweaving-decking.md.
"""

from __future__ import annotations

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
    return min(3, max(0, int(erfolge) - max(0, int(ice))))


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
    """Leer heißt Typ-Default: Schusswaffe komplett, alles andere nur Upgrades."""
    if gespeichert in ("komplett", "upgrades"):
        return gespeichert
    return "komplett" if kampf_fertigkeit == "Schusswaffen" else "upgrades"
