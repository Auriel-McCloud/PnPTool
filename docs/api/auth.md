# Authentifizierung

Login, Sessions und Rollenmanagement.

## Konzept

PnPTool hat **zwei Benutzertypen**:

1. **Spielleitung (GM):** Ein Account pro Kampagne, voller Zugriff
2. **Spieler (PLAYER):** Ein Account pro Spieler, begrenzter Zugriff

Authentifizierung läuft über **JWT-Tokens** im Cookie `pnptool_session`.

---

## Endpunkte

### POST `/api/auth/gm/login`

SL-Login mit Username/Passwort.

```json
{
  "username": "spielleiter",
  "password": "..."
}
```

**Response:** Setzt Cookie, gibt User-Info zurück.

```json
{
  "id": "user-uuid",
  "username": "spielleiter",
  "role": "GM"
}
```

---

### POST `/api/auth/player/login`

Spieler-Login mit Einladungscode.

```json
{
  "code": "ABC123"
}
```

Der Code ist einmalig und an eine Kampagne + optional einen PC gebunden.

---

### GET `/api/auth/me`

Aktueller Benutzer. **401** wenn nicht eingeloggt.

```json
{
  "id": "user-uuid",
  "role": "GM",
  "username": "spielleiter",
  "campaignId": "uuid"
}
```

Oder für Spieler:
```json
{
  "id": "user-uuid",
  "role": "PLAYER",
  "campaignId": "uuid",
  "personId": "pc-uuid"
}
```

---

### POST `/api/auth/logout`

Löscht den Session-Cookie. **204 No Content.**

---

## JWT-Struktur

```json
{
  "sub": "user-uuid",
  "role": "GM",
  "campaignId": "uuid",
  "personId": "pc-uuid",  // nur bei PLAYER
  "exp": 1725753600
}
```

Token-Lebensdauer: 7 Tage (konfigurierbar).

---

## Einladungscodes

Die SL generiert Codes für Spieler:

```
POST /api/campaigns/{campaign_id}/einladungen
{
  "personId": "pc-uuid"  // optional: direkt an PC binden
}

Response:
{
  "code": "ABC123",
  "url": "https://pnptool.example.com/join/ABC123"
}
```

**Einmalverwendung:** Nach Login ist der Code verbraucht.

---

## Berechtigungsprüfung

Jeder Endpunkt prüft:

1. **Authentifiziert?** — Cookie vorhanden und gültig
2. **Kampagnenzugang?** — User gehört zu dieser Kampagne
3. **Rollenberechtigung?** — GM für Admin-Aktionen, PLAYER für Spieler-Aktionen

FastAPI-Dependencies:
- `get_viewer` — Gibt `Viewer(role, person_id)` zurück
- `require_campaign_zugang` — 403 wenn kein Zugang
- `require_campaign_gm` — 403 wenn nicht SL

---

## Viewer-Objekt

```python
@dataclass
class Viewer:
    role: Literal["GM", "PLAYER"]
    person_id: str | None = None  # PC-ID bei Spielern, None bei SL
```

Wird in allen Endpunkten genutzt um Filterung/Berechtigungen zu steuern.
