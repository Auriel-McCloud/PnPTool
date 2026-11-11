# Critter-Pets (`/api/campaigns/{campaign_id}/pets`)

Modul `backend/app/pets/`. Wiki: `docs/wiki/entities/critter-pet.md`.

## SL: Pet-Art eines Critters

| Methode | Pfad | Wer | Body / Antwort |
|---|---|---|---|
| GET | `/api/campaigns/{cid}/pets/{critterId}` | SL | `{id, art}` — `art` `null` = läuft nicht herum |
| PUT | `/api/campaigns/{cid}/pets/{critterId}` | SL | Body `{art: "drache" \| null}`, Antwort wie GET. Gleicht sofort ab (Pet erscheint/verschwindet live). |

Gespeichert als `petArt` am `Person{istCritter:true}`-Knoten. Wirksam nur mit
`BEGLEITET`-Kante zu einem `personType: "PC"`.

## Spieler: Live-Leitung

`WS /api/campaigns/{cid}/pets/live` — Cookie `pnptool_session`, nur Rolle
PLAYER (SL → Close 1008).

Server → Tablet (immer voller Stand dieses Bildschirms):

- `{"typ": "pets", "daten": [{id, name, art, besitzerId, besitzerName, seite, ankunft}]}` — Pets, die gerade hier sind. `seite` = wo es reinkommt, `ankunft` zählt je Auftritt hoch.
- `{"typ": "haeufchen", "daten": [{id, petId, x, y, erstellt, art}]}` — Spuren auf diesem Bildschirm, `x`/`y` als Anteil 0..1, `art` `haeufchen` (antippen) oder `brand` (Feuerniesen, wegwischen).

Tablet → Server:

- `{"typ": "raus", "petId", "seite": "links"|"rechts"}` — nur vom aktuellen Wirt angenommen.
- `{"typ": "haeufchen", "petId", "x", "y", "art"}` — nur vom aktuellen Wirt; `art` fehlt = Häufchen; über 12 je Art fällt die älteste weg.
- `{"typ": "wegmachen", "id"}` — nur eigene Häufchen.

Wandern: nur zu eingeloggten PCs der Party des Besitzers (ohne Party nur zum
Besitzer), bevorzugt nicht derselbe, Pause 3–12 s, Gegenseite. Pet existiert
nur, solange der Besitzer verbunden ist.
