"""Reine Funktionen rund um Nebenfiguren — ohne Datenbank testbar."""

from typing import Any

# Kurz halten: der Wert ist ein Stichwort, kein Absatz.
PERSOENLICHKEIT_MAX_ZEICHEN = 60
# KI-Werte bleiben im üblichen 1–5-Rahmen. Von Hand darf die SL jede Zahl
# eintragen (Marks Hausregel: keine harten Caps).
KI_WERT_MIN = 1
KI_WERT_MAX = 5


def nebenfaehigkeiten_saeubern(roh: Any, *, ki: bool = False) -> list[dict]:
    """Liste von {name, wert}: leere Namen fliegen raus, Werte werden Ganzzahlen ≥ 0.

    Mit ``ki=True`` zusätzlich auf 1–5 geklemmt und höchstens drei Einträge —
    die KI soll eine Nebenfigur nicht zum Alleskönner machen.
    """
    if not isinstance(roh, list):
        return []
    sauber: list[dict] = []
    gesehen: set[str] = set()
    for eintrag in roh:
        if isinstance(eintrag, dict):
            name = str(eintrag.get("name") or "").strip()
            wert_roh = eintrag.get("wert")
        else:
            name = str(getattr(eintrag, "name", "") or "").strip()
            wert_roh = getattr(eintrag, "wert", 0)
        if not name or name.casefold() in gesehen:
            continue
        try:
            wert = int(wert_roh or 0)
        except (TypeError, ValueError):
            wert = 0
        wert = max(0, wert)
        if ki:
            wert = max(KI_WERT_MIN, min(wert, KI_WERT_MAX))
        gesehen.add(name.casefold())
        sauber.append({"name": name, "wert": wert})
    return sauber[:3] if ki else sauber


def nebenfaehigkeiten_text(roh: Any) -> str:
    """„Straßenwissen 4, Feilschen 3“ — für Prompts und Anzeigen."""
    return ", ".join(f"{e['name']} {e['wert']}" for e in nebenfaehigkeiten_saeubern(roh))


def persoenlichkeit_saeubern(roh: Any) -> str:
    text = " ".join(str(roh or "").split())
    return text[:PERSOENLICHKEIT_MAX_ZEICHEN]


def zu_npc_prompt(person: dict, beschreibung_text: str, notizen_text: str) -> str:
    """Auftrag an die Charakter-KI, wenn eine Nebenfigur ein voller NPC wird."""
    teile = [
        f"Baue einen vollständigen Charakterbogen für die bestehende Figur „{person.get('name') or 'Unbenannt'}“. "
        "Name, Rasse und Hintergrund stehen fest — erfinde keine andere Person.",
    ]
    if person.get("rasse"):
        teile.append(f"Rasse: {person['rasse']}.")
    if person.get("alter"):
        teile.append(f"Alter: {person['alter']}.")
    if person.get("persoenlichkeit"):
        teile.append(f"Persönlichkeit in einem Wort: {person['persoenlichkeit']}.")
    faehigkeiten = nebenfaehigkeiten_text(person.get("nebenfaehigkeiten"))
    if faehigkeiten:
        teile.append(
            f"Bisherige feste Fähigkeiten (frei benannt): {faehigkeiten}. "
            "Diese Stärken sollen sich im Bogen wiederfinden."
        )
    if beschreibung_text:
        teile.append(f"Beschreibung: {beschreibung_text}")
    if notizen_text:
        teile.append(f"SL-Notizen: {notizen_text}")
    return "\n".join(teile)
