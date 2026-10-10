"""Waffenschaden auf die Felder, die Kachel und Kampf lesen.

Die Ideenschmiede hat Gegenstände lange nur mit Name, Typ und Preis angelegt.
`kraft` (Kachel) und `schaden` (Steckbrief) blieben dadurch 0. Beide Felder
tragen bei Typ Waffe denselben Wert — das Label heißt überall „Schaden“,
nicht Schadensbonus.

Skala 1–12: 1–7 Handwaffen laut Regelwerk, 8–12 Schiffswaffen (Raumschiff).
"""

SCHADEN_MAX = 12


def schaden_klemmen(roh, *, typ: str) -> int:
    """1–12 für eine Waffe, 0–12 sonst. Fehlend oder 0 bei einer Waffe wird 1.

    Lieber Schlagring-Stufe als eine Waffe ohne Wert: die Kachel blendet
    kraft 0 aus, und der Kampf rechnet dann mit 0.
    """
    try:
        wert = int(roh)
    except (TypeError, ValueError):
        wert = 0
    if typ == "Waffe" and wert <= 0:
        return 1
    return max(0, min(wert, SCHADEN_MAX))


def waffenfelder(typ: str, roh, art=None) -> dict:
    """Nur typ Waffe. Andere Typen bleiben unangetastet (Cyberklinge ist istWaffe).

    schadenArt nur, wenn eine der drei Arten lesbar ist. Fehlende oder
    wirre Angabe bleibt leer — nicht tödlich raten.
    """
    if typ != "Waffe":
        return {}
    wert = schaden_klemmen(roh, typ=typ)
    felder = {"kraft": wert, "schaden": wert, "istWaffe": True}
    gelesen = schaden_art_lesen(art)
    if gelesen:
        felder["schadenArt"] = gelesen
    return felder


_ART_ALIAS = {
    "schlag": "schlag",
    "schlagschaden": "schlag",
    "schwer": "schwer",
    "toedlich": "schwer",
    "tödlich": "schwer",
    "letal": "schwer",
    "aggraviert": "aggraviert",
    "unheilbar": "aggraviert",
    "schwerheilbar": "aggraviert",
}


def schaden_art_lesen(roh) -> str:
    """Tischsprache und die drei Codes auf schlag/schwer/aggraviert. Sonst leer."""
    text = str(roh or "").strip().lower()
    return _ART_ALIAS.get(text, "")
