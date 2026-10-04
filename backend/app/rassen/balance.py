"""Wie teuer eine Rasse ist — die Rechnung hinter dem Baukasten.

**Die Regel stammt nicht von uns, sie steckte schon in Marks fünf Rassen.**
Beim Nachrechnen (11.09.2026) kam heraus, dass alle fünf exakt derselben
Formel folgen, ohne dass sie je aufgeschrieben worden wäre. Mark empfand
diese erste Fassung dann als unfair (04.10.2026: "ich glaube es wird nur
der erste - Wert gerechnet, aber alle + Werte... Und das führt zu einem
Ungleichgewicht") — nachgerechnet stimmte das nicht (jeder Nachteil wurde
schon immer korrekt mitgezählt), aber das eigentliche Problem war real:
Nachteile brachten keine freien Punkte ein, also kam bei Rassen mit
Schwächen am Ende **weniger** als bei Mensch heraus (24 − Σ Nachteile statt
immer 24). Mark wollte stattdessen (05.10.2026): "ein Minus Punkt gibt
einen Punkt zurück, es soll also immer 24 rauskommen" — seitdem gilt:

| Rasse  | Freie Punkte | Σ Vorteile | Σ Nachteile | Summe | Gesamt (9 + Summe) |
|--------|--------------|------------|-------------|-------|--------------------|
| Mensch | 7+5+3 = 15   | 0          | 0           | 15    | 24                 |
| Ork    | 6+6+3 = 15   | +1         | 1           | 15    | 24                 |
| Elf    | 5+6+3 = 14   | +2         | 1           | 15    | 24                 |
| Zwerg  | 5+6+3 = 14   | +2         | 1           | 15    | 24                 |
| Troll  | 5+6+3 = 14   | +3         | 2           | 15    | 24                 |

Daraus die beiden Regeln:

1. **Freie Punkte + Σ Vorteile − Σ Nachteile = 15.** Ein Vorteilspunkt
   kostet einen freien Punkt (er ist trotzdem mehr wert, weil er zusätzlich
   das Maximum hebt), ein Nachteilspunkt bringt umgekehrt einen freien
   Punkt zurück. Damit landet **jede** Rasse rechnerisch bei genau 9
   (Grundwert über 9 Attribute) + 15 = **24** Gesamtpunkten, unabhängig
   davon, wie viele Vor-/Nachteile sie hat.
2. **Nachteile = aufgerundet die Hälfte der Vorteile.** Diese Mindestzahl
   bleibt bestehen — sie ist kein Budget-Mechanismus mehr (den erledigt
   Regel 1 jetzt von selbst), sondern verhindert weiterhin ein reines
   Vorteils-Volk ohne jede erzählerische Schwäche. Ohne sie liesse sich ein
   Min-Max-Volk bauen ("−3 Charisma, +3 Körperkraft") mit noch immer exakt
   24 Punkten, aber ohne echten Nachteil dafür.

Die Prüfung **warnt nur** — der Baukasten lässt bewusst auch unrunde Völker
zu (ein übermächtiges NPC-Volk soll möglich sein). Wer abweicht, sieht es,
wird aber nicht gehindert.

Rein rechnend, ohne Datenbank: dieselbe Motivation wie bei `kampf/ruestung.py`
— die Regel steht an einer Stelle, und die Oberfläche zeigt nur an, was hier
herauskommt, statt sie nachzubauen.
"""

import math

# Freie Punkte + Vorteile − Nachteile, siehe Tabelle oben. Ergibt zusammen
# mit dem Attribut-Grundwert (9 × 1) immer 24 Gesamtpunkte.
BUDGET = 15

# Das dritte Kontingent ist bei allen fünf Rassen 3 — es ist die Spalte, die
# niemand schwerpunktmässig wählt. Der Baukasten schlägt es als Vorgabe vor,
# erzwingt es aber nicht.
DRITTES_KONTINGENT = 3


def bilanz(modifikatoren: dict[str, int], freie_punkte: list[int]) -> dict:
    """Rechnet eine Rasse durch und sagt, ob sie im Rahmen liegt.

    Gibt alle Zwischenwerte mit zurück, damit der Editor sie einzeln anzeigen
    kann ("14 freie Punkte + 2 Vorteile − 1 Nachteil = 15 ✓") statt nur ein
    Urteil.
    """
    vorteile = sum(w for w in modifikatoren.values() if w > 0)
    nachteile = sum(-w for w in modifikatoren.values() if w < 0)
    punkte = sum(freie_punkte)
    # Nachteile geben seit 05.10.2026 einen Punkt zurück (Marks Fairness-
    # Wunsch: am Ende soll unabhängig von der Rasse immer 24 herauskommen).
    summe = punkte + vorteile - nachteile
    # Aufgerundet: 1 Vorteil verlangt 1 Nachteil, 3 Vorteile verlangen 2.
    # Reine Flavor-/Vielfalts-Regel jetzt, kein Budget-Posten mehr (Regel 1
    # oben macht die Summe unabhängig davon immer 24).
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
