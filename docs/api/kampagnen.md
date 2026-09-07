# Kampagnen-API

Kampagnenverwaltung — der Container für alles andere.

## Konzept

Eine **Kampagne** ist ein Spieluniversum: alle Charaktere, Orte, NPCs, Wiki-
Einträge, Kämpfe gehören zu genau einer Kampagne.

Ein GM kann mehrere Kampagnen haben (Montags NeotopiA, Donnerstags Shadowrun).
Spieler haben Zugang zu einer Kampagne.

---

## Endpunkte

### GET `/api/campaigns`

Alle Kampagnen des eingeloggten GMs.

```json
[
  {
    "id": "uuid",
    "name": "NeotopiA: Neonlichter",
    "beschreibung": "Cyberpunk in Neo-Tokyo, 2089",
    "theme": "cyberpunk-neon",
    "erstelltAm": "2026-01-15T...",
    "spielerAnzahl": 4
  }
]
```

---

### POST `/api/campaigns`

Neue Kampagne anlegen. **Nur GM.**

```json
{
  "name": "NeotopiA: Neonlichter",
  "beschreibung": "Cyberpunk in Neo-Tokyo, 2089",
  "theme": "cyberpunk-neon"
}
```

---

### GET `/api/campaigns/{campaign_id}`

Kampagnen-Details.

---

### PATCH `/api/campaigns/{campaign_id}`

Kampagne bearbeiten. **Nur besitzender GM.**

---

### DELETE `/api/campaigns/{campaign_id}`

Kampagne löschen. **Nur besitzender GM. Bestätigungsdialog.**

⚠️ Löscht ALLES: Personen, Orte, Wiki, Kämpfe, Nachrichten.

---

## Themes

Kampagnen haben ein **Theme** das die Farbpalette bestimmt:

| Theme | Beschreibung |
|-------|-------------|
| `cyberpunk-neon` | Neon-Pink/Cyan auf Schwarz (Default für NeotopiA) |
| `fantasy-gold` | Warme Goldtöne, Pergament-Feeling |
| `horror-blood` | Rot/Schwarz, düster |
| `scifi-blue` | Kühl, technisch, blau-weiß |

Themes sind CSS-Variablen in `frontend/src/theme/`:

```css
/* themes/cyberpunk-neon.css */
:root {
  --accent: #ff00ff;
  --accent-2: #00ffff;
  --grund: #0a0a0a;
  --warn: #ff3366;
  /* ... */
}
```

**Cytoscape-Farben** (für Graph-Visualisierungen) werden per Token nachgezogen —
keine harten Farbwerte außerhalb der Theme-Dateien.

---

## Datenmodell (Neo4j)

```cypher
(:Kampagne {
  id: "uuid",
  name: "NeotopiA: Neonlichter",
  beschreibung: "...",
  theme: "cyberpunk-neon",
  besitzerId: "gm-user-uuid",
  erstelltAm: "..."
})

// Alles andere hängt an campaignId
(:Person { campaignId: "uuid", ... })
(:Ort { campaignId: "uuid", ... })
(:WikiSeite { campaignId: "uuid", ... })
```

Keine expliziten Kanten zur Kampagne — `campaignId` als Property reicht und
ist schneller für Queries.
