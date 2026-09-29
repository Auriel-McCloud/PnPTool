"""Menü-Layouts der Spielleitung — PC und Tablet getrennt, Handy scrollt.

Gespeichert als JSON-String an GMUser.menueLayouts. Leere Ordnung heißt:
Default-Reihenfolge aus dem Frontend. Unbekannte IDs ignoriert das Frontend,
neue Bereiche hängen sich hinten an.
"""

from __future__ import annotations

import json

LEER_LAYOUT = {"ordnung": [], "ausgeblendet": []}
LEER_LAYOUTS = {"pc": LEER_LAYOUT, "tablet": LEER_LAYOUT}


def _slot(wert: object) -> dict:
    if not isinstance(wert, dict):
        return dict(LEER_LAYOUT)
    ordnung = wert.get("ordnung")
    ausgeblendet = wert.get("ausgeblendet")
    return {
        "ordnung": [x for x in ordnung if isinstance(x, str)] if isinstance(ordnung, list) else [],
        "ausgeblendet": [x for x in ausgeblendet if isinstance(x, str)] if isinstance(ausgeblendet, list) else [],
    }


def normalisiere_layouts(roh: str | None) -> dict:
    if not roh:
        return {"pc": dict(LEER_LAYOUT), "tablet": dict(LEER_LAYOUT)}
    try:
        gelesen = json.loads(roh)
    except (TypeError, ValueError):
        return {"pc": dict(LEER_LAYOUT), "tablet": dict(LEER_LAYOUT)}
    if not isinstance(gelesen, dict):
        return {"pc": dict(LEER_LAYOUT), "tablet": dict(LEER_LAYOUT)}
    return {"pc": _slot(gelesen.get("pc")), "tablet": _slot(gelesen.get("tablet"))}
