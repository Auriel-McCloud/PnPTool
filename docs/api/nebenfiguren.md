# Nebenfiguren API

Konzept und Entscheidungen: Wiki `entities/nebenfiguren`.

Eine Nebenfigur ist eine `Person` mit `istNebenfigur=true` (personType `NPC`).
Anlegen, Lesen, Bearbeiten und Löschen laufen über die normalen Personen-Routen.

## Personen-Routen

| Methode | Pfad | Hinweis |
|---|---|---|
| GET | `/api/campaigns/{campaign_id}/personen?istNebenfigur=true` | nur Nebenfiguren; `false` = ohne Nebenfiguren (NPC-Liste); weglassen = alle |
| POST | `/api/campaigns/{campaign_id}/personen` | `{name, personType: "NPC", istNebenfigur: true, erstellungAbgeschlossen: true, ...}` |
| PATCH | `/api/campaigns/{campaign_id}/personen/{id}` | `persoenlichkeit`, `nebenfaehigkeiten`, `rasse`, `alter`, `name`, `description`, `notes`, … — `istNebenfigur` gibt es hier nicht |

Neue Felder an `PersonResponse`:

```json
{
  "istNebenfigur": true,
  "persoenlichkeit": "Leitwolf",
  "nebenfaehigkeiten": [{ "name": "Straßenwissen", "wert": 4 }]
}
```

## Eigene Route

Prefix `/api/campaigns/{campaign_id}/nebenfiguren`, nur SL.

| Methode | Pfad | Zweck |
|---|---|---|
| POST | `/{person_id}/zu-npc` | Einbahnstraße: die Charakter-KI baut in-place einen vollen Bogen (Rasse fix, Fähigkeiten → passendste Fertigkeiten, Tutorial-Shop-Einkauf). Antwort: die Person mit `istNebenfigur=false`. Unbekannt → 404, schon NPC → 409, KI-Fehler → 502 |

## Kampf

`POST /api/campaigns/{campaign_id}/kampf/teilnehmer` mit einer Nebenfigur → 400.
Automatische Kampfkandidaten enthalten keine Nebenfiguren.

## Kontakte

`POST /api/campaigns/{campaign_id}/kontakte/{kontakt_id}/generieren` legt für
einen normalen Blanko-Kontakt seit 10.11.2026 eine Nebenfigur an (ein KI-Aufruf).
Mentoren werden weiter volle NPCs.
