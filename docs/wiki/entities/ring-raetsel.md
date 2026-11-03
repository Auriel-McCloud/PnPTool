---
title: Ring-Rätsel
created: 2026-11-03
updated: 2026-11-03
type: entität
tags: [frontend, backend, ui, live]
sources: [../../../backend/app/raetsel/logic.py, ../../../frontend/src/raetsel/RaetselTafel.tsx, ../../api/raetsel.md]
status: aktuell
---

# Ring-Rätsel

Tafel für die SL, damit sie am Tisch nicht den Kopf als Ring benutzen muss.
Kein Regelwerk-Rätsel und keine Lösungsmaschine.

## Eine Ebene, gebaut 03.11.2026

Acht Räume um ein festes Ziel. Feld 0 ist Nord, dann im Uhrzeigersinn.
Gegen den Uhrzeigersinn wandert der Raum aus Nord nach Nordwest.

- Tür zu dreht **alle acht Räume** ein Feld. Es bleibt immer nur eine Tür offen.
- Die Gruppe hängt am Raum, nicht am Feld. Sie wandert also optisch mit.
- Tür auf ist nicht durchgehen. Nach der Drehung muss die SL den Raum klicken,
  in dem die Spieler wirklich sind. Bis dahin pulsiert die letzte Lage.
- Zweite Markierung für einen Split. Egal wer die Tür zumacht, der ganze Ring dreht.
- Die Tür, die am aktuellen Feld zur Mitte zeigt, bekommt eine Neonkante.
  Ob das die richtige Stelle ist, rechnet das Tool nicht aus. Nach vier Schritten
  liegt jeder Raum gegenüber seinem Startfeld — das ist Geometrie, nicht die Lösung.
- Namen sind Kosmetik, höchstens 16 Zeichen. Zurücknehmen lässt die Freigabe stehen.

Spieler sehen dieselbe Tafel ohne Knöpfe, sobald die SL freigibt, und live mit.
Vorher kommt nur „noch nicht freigegeben“, auch auf der Leitung. Der Menüpunkt
selbst ist sichtbar; ausblenden geht über das normale Burgermenü.

Zustand liegt als `raetselJson` am Kampagnen-Knoten, kein eigener Knotentyp.
Der Kampagnen-Export nimmt das Property mit.

## Nicht gebaut

Zwei Ringe übereinander, Räume wechseln die Ebene (rauf, rechts, hinter, rechts).
„Hinter“ ist nicht festgelegt. Anzeige wäre zwei Ringe nebeneinander, nicht übereinander.
Dritte Ebene nicht anfangen.

Menüpunkt wie die übrigen Bereiche, siehe [[entities/ui-konzept-commlink]].
Der Stand hängt an der Kampagne und geht mit dem Export mit, siehe
[[entities/kampagnen-export-import]].
