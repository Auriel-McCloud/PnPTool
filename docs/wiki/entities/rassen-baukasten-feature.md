---
title: Rassen-Baukasten (Feature)
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [rassen-baukasten, frontend, backend]
sources: [../../api/rassen.md, ../../../CLAUDE.md]
status: aktuell
---

# Rassen-Baukasten (Feature)

Die technische Umsetzung des in [[../concepts/rassen]] beschriebenen
Regelkonzepts. Eigener SL-Bereich (Kacheln + Editor-Fenster), gebaut
11.09.2026: Völker bauen, Live-Bilanz gegen die 15er-Regel, Bild-Upload,
Freigabe je Kampagne. Infobox mit Beschreibung + Bild in der
Charaktererstellung.

## Endpunkte

Basis `/api/campaigns/{campaign_id}/rassen`:

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `` | alle mit Zugang | wählbare Rassen dieser Kampagne |
| GET | `/katalog` | nur SL | alle Rassen des Regelwerks + Freigabe-Häkchen |
| POST | `` | nur SL | neue Rasse (noch nicht freigegeben) |
| PATCH | `/{id}` | nur SL | bearbeiten, Umbenennen wird nachgezogen |
| DELETE | `/{id}` | nur SL | aus dem Regelwerk entfernen |
| PUT | `/freigabe` | nur SL | vollständige Auswahl für diese Kampagne |
| POST | `/{id}/bild` | nur SL | Bild für Infobox |

Pfade hängen an einer Kampagne, die Daten nicht — derselbe Zuschnitt wie bei
`/chromstufen`.

## Bild-Upload-Fix (15.09.2026)

Die generische `/{art}/{node_id}/bild`-Route fing `/rassen/...` fälschlich ab.
Fix: vier explizite Bild-Routen statt einer generischen.

## Siehe auch

- [[../concepts/rassen]] — das Regelkonzept (Balance-Formel, Baukasten-Idee)
- [[neo4j-datenmodell]] — `ERLAUBT_RASSE`-Beziehung
