"""Schadensbonus einer Waffe auf die Felder, die Kachel und Kampf lesen.

Die Ideenschmiede hat Gegenstände lange nur mit Name, Typ und Preis angelegt.
`kraft` (Label „Schadensbonus“, Kampfkarte und Kachel) und `schaden` (Zeile
„Schaden“ im Detail, sobald typ Waffe oder istWaffe) blieben dadurch 0.
Die Skala ist das Regelwerk, 1–7 — kein Würfelausdruck aus dem Chat.
"""

SCHADENSBONUS_MAX = 7


def schadensbonus_klemmen(roh, *, typ: str) -> int:
    """1–7 für eine Waffe, 0–7 sonst. Fehlend oder 0 bei einer Waffe wird 1.

    Lieber Schlagring-Stufe als eine Waffe ohne Wert: die Kachel blendet
    kraft 0 aus, und der Kampf rechnet dann mit 0.
    """
    try:
        wert = int(roh)
    except (TypeError, ValueError):
        wert = 0
    if typ == "Waffe" and wert <= 0:
        return 1
    return max(0, min(wert, SCHADENSBONUS_MAX))


def waffenfelder(typ: str, roh) -> dict:
    """Nur typ Waffe. Andere Typen bleiben unangetastet (Cyberklinge ist istWaffe)."""
    if typ != "Waffe":
        return {}
    bonus = schadensbonus_klemmen(roh, typ=typ)
    return {"kraft": bonus, "schaden": bonus, "istWaffe": True}
