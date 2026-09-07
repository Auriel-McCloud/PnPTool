# PnPTool API-Dokumentation

Technische Referenz der Backend-APIs für das NeotopiA PnP-Werkzeug.

## Übersicht

PnPTool ist ein FastAPI-Backend mit Neo4j-Graphdatenbank. Die API ist REST-basiert
mit WebSocket-Erweiterungen für Echtzeit-Features.

### Basis-URL

- Entwicklung: `http://localhost:8000/api`
- Alle Endpunkte erfordern Authentifizierung (Cookie `pnptool_session`)

### Rollen

| Rolle | Beschreibung |
|-------|--------------|
| `GM` | Spielleitung — voller Zugriff auf alle Kampagnendaten |
| `PLAYER` | Spieler — sieht nur freigegebene Inhalte und eigenen Charakter |

### Module

| Modul | Beschreibung | Docs |
|-------|--------------|------|
| [Authentifizierung](./auth.md) | Login, Session, Rollen | |
| [Kampagnen](./kampagnen.md) | Kampagnenverwaltung | |
| [Personen](./personen.md) | PCs, NPCs, Charakterbögen | |
| [Kontakte & Messenger](./kontakte.md) | In-Game-Kommunikation | ⭐ |
| [Mitteilungen](./mitteilungen.md) | SL-Broadcasts, Live-Popups | ⭐ |
| [Kampf](./kampf.md) | Rundenbasierter Kampf, Initiative | |
| [Wiki](./wiki.md) | Weltenbau, Freigabesystem | |
| [Entitäten](./entitaeten.md) | Orte, Gegenstände, Fraktionen | |

⭐ = Komplexe Systeme mit WebSocket-Integration

---

## Architektur-Entscheidungen

### Warum Neo4j?

Ein Pen-and-Paper-Spiel ist ein Netz aus Beziehungen: NPCs kennen sich, Orte
sind verbunden, Gegenstände gehören Charakteren, Fraktionen haben Hierarchien.
Eine Graphdatenbank bildet das natürlich ab — keine JOIN-Orgien, keine
künstlichen Zwischentabellen.

### Warum kein GraphQL?

REST reicht für unser UI. Die Abfragen sind vorhersehbar (Charakterbogen,
Kontaktliste, Wiki-Seite), nicht explorative Graphtraversierungen. GraphQL
hätte Overhead gebracht ohne echten Nutzen.

### Warum WebSockets statt Polling?

Am Spieltisch sitzt jeder mit einem Gerät. Wenn die SL "Würfelt Initiative!"
ruft, muss das *sofort* auf allen Tablets erscheinen — nicht "in 5 Sekunden
beim nächsten Poll". WebSockets liefern echte Echtzeit.

---

## Konventionen

### Fehler-Responses

```json
{
  "detail": "Menschenlesbare Fehlermeldung"
}
```

HTTP-Statuscodes:
- `400` — Ungültige Anfrage (fehlende Felder, Validierungsfehler)
- `401` — Nicht authentifiziert
- `403` — Keine Berechtigung (z.B. Spieler versucht SL-Aktion)
- `404` — Ressource nicht gefunden
- `409` — Konflikt (z.B. Chat nicht geöffnet)

### IDs

Alle Entitäten haben UUIDs als IDs (`uuid4`). Keine sequenziellen IDs —
die verraten Informationen (wie viele NPCs gibt es?) und kollidieren beim
späteren Zusammenführen von Kampagnen.

### Zeitstempel

ISO 8601 in UTC: `2026-09-07T22:15:00.000Z`

### Sprache

- Code, Variablennamen, Kommentare: **Deutsch**
- API-Feldnamen: **camelCase** (für JS-Frontend)
- Dokumentation: **Deutsch**
