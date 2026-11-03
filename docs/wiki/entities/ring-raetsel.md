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

## Zwei Ebenen, Ausgänge, Umschalter (03.11.2026)

Umschalter oben in der Tafel, nur SL: **Leicht** (eine Ebene, wie oben) oder
**Mittel** (zwei Ebenen). Umschalten setzt Felder auf Start zurück; Namen,
Freigabe und Ausgänge bleiben.

- Mittel hat 16 Räume statt 8, zwei Ringe nebeneinander dargestellt
  („Ebene oben“/„Ebene unten“), nicht übereinander — „hinter“ war nicht
  festgelegt, die Nebeneinander-Anzeige umgeht die Frage.
- Tür zu wechselt abwechselnd: einmal die Ebene (gleiches Feld, anderer Ring),
  einmal drehen beide Ringe gemeinsam gegen den Uhrzeigersinn. Welche der
  beiden Aktionen als Nächstes kommt, zeigt die Kopfzeile an.
- Fester Ausgang: pro Ring ein Feld (nicht ein Raum) lässt sich in der Mitte
  bei „Ziel“ markieren — ein Klick auf einen der acht Punkte setzt ihn, nochmal
  derselbe Punkt nimmt ihn weg. Er bleibt am Feld liegen, während die Räume
  weiterwandern. Nur die SL sieht ihn, auch nach Freigabe nicht die Spieler.
  In Leicht gibt es nur einen Ring, also nur einen Ausgang.
- Dritte Ebene nicht angefangen.

Menüpunkt wie die übrigen Bereiche, siehe [[entities/ui-konzept-commlink]].
Der Stand hängt an der Kampagne und geht mit dem Export mit, siehe
[[entities/kampagnen-export-import]].
