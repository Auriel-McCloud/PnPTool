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

## Frontend: gemeinsames Anmeldefenster (23.09.2026)

`frontend/src/auth/AnmeldeFenster.tsx` ersetzt die getrennten
`GmLoginPage.tsx`/`SpielerLogin.tsx` — eine Commlink-Karte für beide Rollen,
Spieler sehen das Login-Formular zuerst (deutlich mehr Spieler- als
SL-Logins am Tisch), "Ich bin die Spielleitung" wechselt auf das
SL-Formular. Ein Spieler-Account ohne zugeordneten Charakter (`personId`
fehlt) sieht nach dem Login `frontend/src/players/SpielerEinstieg.tsx`
statt der vollen Commlink-Hülle — siehe `CLAUDE.md` Punkt 6
("PC-Erstellung / Ersteinstieg") für die beiden Wege (selbst erstellen /
vorgefertigten PC wählen).

---

## Eigenes Charakterportrait (Spieler-Router `/api/spieler`)

Drei Wege für den Spieler, sein eigenes zugeordnetes `Person`-Bild zu
setzen — alle bewusst OHNE `require_campaign_gm` (einzige Bild-Upload-Routen
im Projekt, die nicht GM-only sind: der Spieler darf nur sein **eigenes**
Bild setzen, `personId` kommt aus dem JWT-Claim, kein Pfad-Parameter).

### POST `/api/spieler/mein-bild`

Datei-Upload (`multipart/form-data`, Feld `file`, PNG/JPEG/WEBP/GIF, max.
8 MB). Schreibt auf dasselbe `bildUrl`-Feld wie der SL-Upload, gleicher
Ordner (`uploads/<campaign_id>/`), Dateipräfix `portrait-` statt
`personen-`. **Response:** `SpielerMeResponse` (u.a. `personBildUrl`).

### DELETE `/api/spieler/mein-bild`

Setzt `bildUrl` zurück (nicht die Datei selbst — bleibt wie beim SL-Pendant
verwaist auf dem Datenträger liegen).

### POST `/api/spieler/mein-bild-ki-prompt` (gebaut 23.09.2026)

Schritt 1 der KI-Bildgenerierung fürs eigene Portrait — identische Logik
wie `POST /api/campaigns/{id}/ki/bild-prompt` (siehe
[docs/api/ki.md](./ki.md), ruft dieselbe `_bild_prompt_vorschlagen()`
auf), nur ohne Pfadparameter: Objekttyp/-name/-beschreibung kommen aus dem
zugeordneten Charakter selbst, nicht aus dem Body. `400` wenn dem Spieler
noch kein Charakter zugeordnet ist, `404` wenn der Charakter nicht (mehr)
existiert.

**Response:**
```json
{ "prompt": "A grizzled fixer in a rain-soaked alley, neon signage reflecting..." }
```

### POST `/api/spieler/mein-bild-ki` (gebaut 23.09.2026)

Schritt 2 — identisch zu `POST .../ki/bild-generieren`
([docs/api/ki.md](./ki.md)): liefert die rohen Bild-Bytes zur Vorschau
zurück, speichert nichts. Übernehmen läuft über `POST /mein-bild` oben
(Frontend baut aus dem Blob eine `File`).

```json
{ "provider": "lokal" | "cloud", "prompt": "..." }
```

Frontend: `KiBildPopup` in `players/CharakterportraitAnsicht.tsx`, neben
Datei-Upload und Kamera-Aufnahme.

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
