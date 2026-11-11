# Critter-Pets (`/api/campaigns/{campaign_id}/pets`)

Modul `backend/app/pets/`. Wiki: `docs/wiki/entities/critter-pet.md`.

## SL: Pet-Art eines Critters oder Gegenstands

| Methode | Pfad | Wer | Body / Antwort |
|---|---|---|---|
| GET | `/api/campaigns/{cid}/pets/{critterId}` | SL | `{id, art}` — `art` `null` = läuft nicht herum |
| PUT | `/api/campaigns/{cid}/pets/{critterId}` | SL | Body `{art: "drache" \| "baerbel" \| null}`, Antwort wie GET. Gleicht sofort ab (Pet erscheint/verschwindet live). |

`{critterId}` darf auch die id eines `Gegenstand`s sein (Bärbel, 11.11.2026).
Gespeichert als `petArt` am `Person{istCritter:true}`- bzw. `Gegenstand`-Knoten.
Critter: wirksam nur mit `BEGLEITET`-Kante zu einem `personType: "PC"`.
Gegenstand: wirksam, solange ein PC ihn per `BESITZT` hat (ausgerüstet egal),
er nicht `weggeworfen` ist und nicht (auch verschachtelt, `LIEGT_IN`) in einer
verschlossenen Kiste liegt. Mehrere Besitzer → der erste nach id.

## Pause

Keine Pets unterwegs, solange die Kampagneneinstellung `petsAktiv` aus ist oder ein `:Kampf` läuft (`repository.pets_pausiert`). Umschalten und Kampf beginnen/beenden gleichen sofort ab.

## Spieler: Live-Leitung

`WS /api/campaigns/{cid}/pets/live` — Cookie `pnptool_session`, nur Rolle
PLAYER (SL → Close 1008).

Server → Tablet (immer voller Stand dieses Bildschirms):

- `{"typ": "pets", "daten": [{id, name, art, besitzerId, besitzerName, seite, ankunft}]}` — Pets, die gerade hier sind. `seite` = wo es reinkommt, `ankunft` zählt je Auftritt hoch.
- `{"typ": "haeufchen", "daten": [{id, petId, x, y, erstellt, art}]}` — Spuren auf diesem Bildschirm, `x`/`y` als Anteil 0..1, `art` `haeufchen` (antippen), `brand` (Feuerniesen, wegwischen) oder `seite` (Bärbels verlorene Seite, segelt zu Boden, antippen).

Tablet → Server:

- `{"typ": "raus", "petId", "seite": "links"|"rechts"}` — nur vom aktuellen Wirt angenommen.
- `{"typ": "haeufchen", "petId", "x", "y", "art"}` — nur vom aktuellen Wirt; `art` fehlt = Häufchen; über 12 je Art fällt die älteste weg.
- `{"typ": "wegmachen", "id"}` — nur eigene Häufchen.
- `{"typ": "verschieben", "id", "x", "y"}` — Häufchen ist von seinem Element gefallen (Anteile 0..1, begrenzt); nur eigene, nur Art `haeufchen`/`seite` — Brandflecken sitzen am Display und bewegen sich nie.

Wandern: nur zu eingeloggten PCs der Party des Besitzers (ohne Party nur zum
Besitzer), bevorzugt nicht derselbe, Pause 3–12 s, Gegenseite. Pet existiert
nur, solange der Besitzer verbunden ist.
