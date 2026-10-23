"""Lokale Archetyp-Vorlagen für Ambition und Verlangen.

Dieselbe Datei wie der Vorschläge-Knopf in der Charaktererstellung. Die Texte
stammen aus fremdem Regelwerk und sind gitignored — sie dürfen den Prompt
einer Cloud-KI nicht erreichen. Die KI-Charaktererstellung bekommt nur die
Namen und muss einen davon wählen.
"""

import json
from pathlib import Path

VORLAGEN_DATEI = Path(__file__).resolve().parents[2] / "data" / "vorlagen.local.json"


def ambition_eintraege() -> list:
    """Roh-Einträge (name/text) oder leere Liste, wenn die Datei fehlt."""
    try:
        inhalt = json.loads(VORLAGEN_DATEI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(inhalt, dict):
        return []
    roh = inhalt.get("ambition", [])
    return roh if isinstance(roh, list) else []


def archetyp_namen() -> list[str]:
    """Kanonische Namen, Dateireihenfolge, ohne Duplikate."""
    namen: list[str] = []
    gesehen: set[str] = set()
    for eintrag in ambition_eintraege():
        if not isinstance(eintrag, dict):
            continue
        name = (eintrag.get("name") or "").strip()
        if not name:
            continue
        schluessel = name.casefold()
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        namen.append(name)
    return namen


def nur_archetyp(wert: str | None, namen: list[str]) -> str:
    """Nur ein exakter Vorlagen-Name, sonst leer. Nie umformulieren."""
    text = (wert or "").strip()
    if not text or not namen:
        return ""
    for name in namen:
        if text.casefold() == name.casefold():
            return name
    return ""
