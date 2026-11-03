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
| POST | `/tuer` | `{raum, seite}` — Ring ein Feld gegen den Uhrzeigersinn, diese Tür ist die offene. Gesetzte Gruppen müssen neu bestätigt werden, ihre Raum-Nummer bleibt. |
| POST | `/gruppe` | `{index: 0\|1, raum: 0–7\|null}` — Lage setzen oder Gruppe B weg. Dreht nicht. |
| POST | `/name` | `{raum, name}` — Anzeigename, leer fällt auf die Nummer zurück, Schnitt bei 16. |
| POST | `/freigabe` | `{an}` — Spieler sehen die Tafel oder nicht. Steht nicht in der Historie. |
| POST | `/zurueck` | Letzten Klick zurück, Freigabe bleibt. |
| POST | `/zuruecksetzen` | Startfelder. Namen und Freigabe bleiben. |

`seite` ist `N`, `O`, `S` oder `W`.

## Live

`WS /api/campaigns/{id}/raetsel/live`

Beim Verbinden und nach jedem Schreibzugang der komplette Stand, gefiltert
wie beim GET. Nachrichten vom Client werden ignoriert — Klicks laufen über REST,
damit ein Spieler die Leitung nicht drehen kann.
