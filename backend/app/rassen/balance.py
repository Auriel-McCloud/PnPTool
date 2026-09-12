"""Wie teuer eine Rasse ist — die Rechnung hinter dem Baukasten.

**Die Regel stammt nicht von uns, sie steckte schon in Marks fünf Rassen.**
Beim Nachrechnen (11.09.2026) kam heraus, dass alle fünf exakt derselben
Formel folgen, ohne dass sie je aufgeschrieben worden wäre:

| Rasse  | Freie Punkte | Σ Vorteile | Summe | Σ Nachteile |
|--------|--------------|------------|-------|-------------|
| Mensch | 7+5+3 = 15   | 0          | 15    | 0           |
| Ork    | 6+5+3 = 14   | +1         | 15    | 1           |
| Elf    | 5+5+3 = 13   | +2         | 15    | 1           |
| Zwerg  | 5+5+3 = 13   | +2         | 15    | 1           |
| Troll  | 5+4+3 = 12   | +3         | 15    | 2           |

Daraus die beiden Regeln:

1. **Freie Punkte + Summe der positiven Modifikatoren = 15.** Ein
   Vorteilspunkt kostet also genau einen freien Punkt. Er ist mehr wert als
   ein freier Punkt (er hebt zusätzlich das Maximum), deshalb ist der Tausch
   für die Rasse attraktiv — aber nicht gratis.
2. **Nachteile = aufgerundet die Hälfte der Vorteile.** Sie sind
   **keine Währung**: Nachteile bringen keine freien Punkte ein (Marks
   Entscheidung vom 11.09.2026). Sonst liesse sich ein Min-Max-Volk bauen
   ("−3 Charisma, +3 Körperkraft"), und genau das ist in keiner der fünf
   Rassen passiert.

Die Prüfung **warnt nur** — der Baukasten lässt bewusst auch unrunde Völker
zu (ein übermächtiges NPC-Volk soll möglich sein). Wer abweicht, sieht es,
wird aber nicht gehindert.

Rein rechnend, ohne Datenbank: dieselbe Motivation wie bei `kampf/ruestung.py`
— die Regel steht an einer Stelle, und die Oberfläche zeigt nur an, was hier
herauskommt, statt sie nachzubauen.
"""

import math

# Freie Punkte + positive Modifikatoren, siehe Tabelle oben.
BUDGET = 15

# Das dritte Kontingent ist bei allen fünf Rassen 3 — es ist die Spalte, die
# niemand schwerpunktmässig wählt. Der Baukasten schlägt es als Vorgabe vor,
# erzwingt es aber nicht.
DRITTES_KONTINGENT = 3


def bilanz(modifikatoren: dict[str, int], freie_punkte: list[int]) -> dict:
    """Rechnet eine Rasse durch und sagt, ob sie im Rahmen liegt.

    Gibt alle Zwischenwerte mit zurück, damit der Editor sie einzeln anzeigen
    kann ("13 freie Punkte + 2 Vorteile = 15 ✓") statt nur ein Urteil.
    """
    vorteile = sum(w for w in modifikatoren.values() if w > 0)
    nachteile = sum(-w for w in modifikatoren.values() if w < 0)
    punkte = sum(freie_punkte)
    summe = punkte + vorteile
    # Aufgerundet: 1 Vorteil verlangt 1 Nachteil, 3 Vorteile verlangen 2.
    nachteile_soll = math.ceil(vorteile / 2)

    hinweise: list[str] = []
    if summe > BUDGET:
        hinweise.append(f"{summe - BUDGET} Punkt(e) über dem Budget — diese Rasse ist stärker als die anderen.")
    elif summe < BUDGET:
        hinweise.append(f"{BUDGET - summe} Punkt(e) unter dem Budget — hier ist noch Luft.")
    if nachteile < nachteile_soll:
        hinweise.append(f"Zu wenig Nachteile: {nachteile_soll} erwartet, {nachteile} vergeben.")
    elif nachteile > nachteile_soll:
        hinweise.append(f"Mehr Nachteile als nötig: {nachteile_soll} erwartet, {nachteile} vergeben.")

    return {
        "punkte": punkte,
        "vorteile": vorteile,
        "nachteile": nachteile,
        "summe": summe,
        "budget": BUDGET,
        "nachteileSoll": nachteile_soll,
        "stimmt": summe == BUDGET and nachteile == nachteile_soll,
        "hinweise": hinweise,
    }
