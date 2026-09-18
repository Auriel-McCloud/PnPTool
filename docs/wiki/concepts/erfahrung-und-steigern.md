---
title: Erfahrung und Steigern
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [erfahrung, versionsgeschichte]
sources: [../../regeln-neotopia.md, ../../api/personen.md, ../../../backend/app/traits/erfahrung.py]
status: teilweise-umgesetzt
---

# Erfahrung und Steigern

## Definition — komplett außerhalb des Excels erfunden

**Das Excel beschreibt nur die Erstellung, nichts über spätere Steigerungen.**
Die Preise in `backend/app/traits/erfahrung.py` sind ein Vorschlag, angelehnt an
World of Darkness (Preis = aktueller Wert × Faktor, fünfter Punkt teurer als
zweiter) und an das Freebee-Verhältnis der Erstellung:

| Was | Faktor | Erster Punkt (von 0) |
|---|---|---|
| Attribut | ×4 | — (steht nie auf 0) |
| Fertigkeit | ×2 | 3 |
| Sphäre | ×5 | 7 |
| NeuroWeaving | ×5 | 7 |
| Hexkraft | ×8 | 10 |
| Hintergrund | ×3 | 3 |
| Willenskraft | ×1 | — |

## Zwei EP-Typen (laut `docs/api/personen.md`)

1. **Kampagnen-EP (global):** alle PCs bekommen dieselben EP am Ende einer
   Session — fair, kein Tracking wer „mehr gemacht" hat.
2. **Extra-EP (individuell):** Bonus für herausragendes Rollenspiel, pro PC
   vergeben.

**Nur Plus-Button:** EP können nur hinzugefügt, nicht entfernt werden.
Ausgeben passiert automatisch beim Steigern. Mark: „Irreversibel.
Bestätigungsdialog. Ich will nicht versehentlich 50 EP vergeben."

## Entwicklung

Dieses gesamte System ist eine **Erfindung fürs Tool**, keine Excel-Regel — im
Gegensatz zu den meisten anderen Konzeptseiten hier gibt es also keine
"Excel vs. heute"-Spannung, sondern nur "Vorschlag vs. endgültig". **Status:
teilweise-umgesetzt / vorläufig** — die Faktoren sind laut `regeln-neotopia.md`
ausdrücklich ein Vorschlag, kein von Mark endgültig abgesegnetes Zahlenwerk.

## Siehe auch

- [[charaktererschaffung]] — die Erstellung, von der sich die Faktoren ableiten
- [[attribute-und-fertigkeiten]] — was gesteigert wird
- [[../comparisons/regelwerk-excel-vs-aktuell]] — Einordnung als "nicht aus dem Excel"
