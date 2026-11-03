# Rätsel-API

Eine Tafel pro Kampagne. Die SL dreht den Ring, Spieler sehen nur zu.

Zustand als `raetselJson` am `Campaign`-Knoten. Kein eigener Knotentyp, der
Kampagnen-Export nimmt das Property mit.

## Lesen

`GET /api/campaigns/{id}/raetsel`

Spielleitung bekommt den vollen Stand plus `kannZurueck`. Spieler bekommen
denselben Stand nur bei `freigegeben`, sonst nur `{ "freigegeben": false }`.
Der Rückgängig-Stapel geht nie über die Leitung.

## Schreiben (nur SL)

| Methode | Pfad | Wirkung |
|---|---|---|
| POST | `/tuer` | `{raum, seite}` — Leicht: Ring ein Feld gegen den Uhrzeigersinn. Mittel: abwechselnd Ebene wechseln oder beide Ringe drehen. Diese Tür ist die offene. Gesetzte Gruppen müssen neu bestätigt werden, ihre Raum-Nummer bleibt. |
| POST | `/gruppe` | `{index: 0\|1, raum: 0–7 (Leicht) / 0–15 (Mittel) \|null}` — Lage setzen oder Gruppe B weg. Dreht nicht. |
| POST | `/name` | `{raum, name}` — Anzeigename, leer fällt auf die Nummer zurück, Schnitt bei 16. |
| POST | `/ausgang` | `{ring: 0\|1, slot: 0–7\|null}` — fester Ausgang an diesem Feld (nicht Raum), nochmal derselbe Slot nimmt ihn weg. Nur der SL sichtbar. |
| POST | `/modus` | `{modus: "leicht"\|"mittel"}` — Umschalter, setzt Felder auf Start zurück, Namen/Freigabe/Ausgänge bleiben. |
| POST | `/freigabe` | `{an}` — Spieler sehen die Tafel oder nicht. Steht nicht in der Historie. |
| POST | `/zurueck` | Letzten Klick zurück, Freigabe bleibt. |
| POST | `/zuruecksetzen` | Startfelder. Namen, Freigabe, Modus und Ausgänge bleiben. |

`seite` ist `N`, `O`, `S` oder `W`. Antwort enthält zusätzlich `modus`, `takt`,
`naechster` (`"ebene"`\|`"drehen"`, nur im Modus Mittel relevant), `ringe`
(ein oder zwei Arrays mit 8 Raum-Nummern) und `ausgaenge` (SL: `[slot\|null, slot\|null]`,
Spieler immer `[null, null]`).

## Live

`WS /api/campaigns/{id}/raetsel/live`

Beim Verbinden und nach jedem Schreibzugang der komplette Stand, gefiltert
wie beim GET. Nachrichten vom Client werden ignoriert — Klicks laufen über REST,
damit ein Spieler die Leitung nicht drehen kann.
