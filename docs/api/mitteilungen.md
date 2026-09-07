# Mitteilungen-API

SL-Broadcasts und Live-Benachrichtigungen — das Popup-System für Ansagen der
Spielleitung.

## Konzept

Eine **Mitteilung** ist ein Popup der Spielleitung an die Spieler. Sie hat
bewusst **keinen sichtbaren Absender** — sie kommt "aus der Spielwelt", nicht
von einer Person. Typische Anwendungen:

- "Würfelt für Initiative!" (WARNUNG mit Initiative-Feld)
- "So sieht er aus" (BILD mit NPC-Portrait)
- "Der Raum bebt, Staub rieselt von der Decke" (TEXT für Atmosphäre)
- "Kira: Hey, hast du Zeit?" (NACHRICHT für Chat-Benachrichtigungen)

Mitteilungen werden **gespeichert**, nicht nur gesendet: Wessen Tablet gerade
im Standby ist, kann die Initiative-Ansage nachlesen.

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/mitteilungen`

### GET `/`

Alle Mitteilungen für diesen Betrachter, neueste zuerst.

**Response:**
```json
{
  "mitteilungen": [
    {
      "id": "uuid",
      "art": "TEXT",
      "inhalt": "Der Regen prasselt gegen die Scheiben.",
      "bildUrl": "",
      "farbe": "rot",
      "initiative": false,
      "anAlle": true,
      "empfaengerIds": [],
      "gelesenVon": ["person-uuid-1"],
      "verstecktVon": [],
      "erstelltAm": "2026-09-07T20:15:00.000Z"
    }
  ],
  "ungelesen": 3
}
```

**Filterung:** Spieler sehen nur:
- Rundrufe (`anAlle: true`)
- Gerichtete Mitteilungen wo ihre `personId` in `empfaengerIds` ist
- NACHRICHT-Mitteilungen wo ihre `personId` in `empfaengerIds` ist

Die SL sieht alle ihre eigenen Broadcasts, aber bei NACHRICHT nur die an sie
gerichteten (wo `empfaengerIds` leer ist).

---

### POST `/`

Neue Mitteilung senden. **Nur SL.**

**Request:**
```json
{
  "art": "WARNUNG",
  "inhalt": "Würfelt für Initiative!",
  "bildUrl": "",
  "farbe": "rot",
  "initiative": true,
  "anAlle": true,
  "empfaengerIds": []
}
```

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `art` | `"TEXT"` \| `"BILD"` \| `"WARNUNG"` \| `"NACHRICHT"` | `"TEXT"` | Art der Mitteilung |
| `inhalt` | string | `""` | Textinhalt (Pflicht bei TEXT/WARNUNG) |
| `bildUrl` | string | `""` | Bild-URL (Pflicht bei BILD) |
| `farbe` | `"rot"` \| `"blau"` \| `"violett"` | `"rot"` | Warnfarbe (nur bei WARNUNG) |
| `initiative` | boolean | `false` | Zeigt Initiative-Eingabefeld (nur WARNUNG) |
| `anAlle` | boolean | `true` | Rundruf an alle |
| `empfaengerIds` | string[] | `[]` | Spezifische Empfänger (nur wenn `anAlle: false`) |

**Response:**
```json
{
  "mitteilung": { ... },
  "zugestellt": 4
}
```

`zugestellt` = wie viele offene WebSocket-Verbindungen es sofort erreicht hat.
Der Rest bekommt es beim nächsten Verbinden.

---

### POST `/{mitteilung_id}/gelesen`

Markiert eine Mitteilung als gelesen für diesen Betrachter. **204 No Content.**

*Gilt pro Person, nicht global — sonst würde das Abhaken eines Spielers die
Meldung bei allen anderen verschwinden lassen.*

---

### POST `/gelesen`

Alle Mitteilungen als gelesen markieren. **204 No Content.**

---

### POST `/{mitteilung_id}/ausblenden`

Blendet eine Mitteilung für diesen Betrachter aus. **204 No Content.**

Die Mitteilung verschwindet aus der eigenen Liste, bleibt aber für andere
sichtbar. Jeder kann seine eigenen Benachrichtigungen aufräumen.

**Warum Ausblenden statt Löschen?**
> Mark: "Ich will dass sie ausblenden, weil die Liste sonst schnell
> unübersichtlich wird."

Ein echter "Löschen"-Button hätte Verwirrung gestiftet — "Lösche ich das
für alle?" Ausblenden ist klar: nur für mich.

---

### POST `/ausblenden`

Alle Mitteilungen für diesen Betrachter ausblenden. **204 No Content.**

---

### DELETE `/{mitteilung_id}`

Mitteilung komplett zurückziehen. **Nur SL. 204 No Content.**

Verschwindet auch auf bereits offenen Bildschirmen (via WebSocket-Push
`zurueckgezogen`).

---

## WebSocket

### Verbinden

```
ws://localhost:8000/api/campaigns/{campaign_id}/mitteilungen/live
```

Authentifizierung via Cookie (`pnptool_session`). Bei fehlendem/ungültigem
Token: Close mit Code `1008` (Policy Violation).

### Nachrichten vom Server

**Initial (nach Verbinden):**
```json
{
  "typ": "stand",
  "daten": {
    "mitteilungen": [...],
    "ungelesen": 3
  }
}
```

**Neue Mitteilung:**
```json
{
  "typ": "mitteilung",
  "daten": {
    "id": "uuid",
    "art": "WARNUNG",
    "inhalt": "Würfelt für Initiative!",
    ...
  }
}
```

**Zurückgezogen:**
```json
{
  "typ": "zurueckgezogen",
  "daten": { "id": "uuid" }
}
```

### Reconnect-Logik

Das Frontend verbindet bei Abbruch automatisch neu mit exponential Backoff
(1s, 2s, 4s, ... max 15s). Wichtig fürs Tablet: Android schläfert
Hintergrund-Tabs ein und trennt dabei die Verbindung.

---

## Mitteilungsarten

### TEXT

Ruhiges Popup. Für Atmosphäre, Hinweise, kleine Ansagen.

### BILD

Zeigt ein Bild (NPC-Portrait, Karte, Gegenstand). Der `inhalt` wird als
Bildunterschrift angezeigt.

### WARNUNG

Der ganze Bildschirm pulsiert in der gewählten `farbe`. Die Ansage steht
groß in der Mitte. Für Initiative-Aufrufe und dramatische Momente.

**Warum wählbare Farben?**
> Mark will am Tisch noch ausprobieren, welcher Ton wirkt — rot für Gefahr,
> blau für Kälte/Magie, violett für Psi/Übernatürliches. Die Entscheidung
> trifft er nach dem Praxistest.

### NACHRICHT

Interne Art für Chat-Benachrichtigungen. Wird vom Messenger automatisch
erstellt, nicht manuell von der SL gesendet.

**Sonderlogik:**
- `empfaengerIds` leer = geht an die SL (Spieler hat an NPC geschrieben)
- `empfaengerIds` gefüllt = geht an diesen Spieler (SL hat als NPC geantwortet)

---

## Filterlogik (logic.py)

### `darf_empfangen(mitteilung, viewer_role, viewer_person_id)`

Entscheidet, ob ein Betrachter eine Mitteilung sehen darf.

```python
# NACHRICHT hat eigene Logik
if art == "NACHRICHT":
    if viewer_role == "GM":
        # SL sieht nur Nachrichten an sie (empfaengerIds leer)
        return len(empfaenger) == 0
    else:
        # Spieler sieht nur wenn seine ID drin ist
        return viewer_person_id in empfaenger

# Normale Mitteilungen (TEXT, BILD, WARNUNG)
if viewer_role == "GM":
    return True  # SL sieht alles
if anAlle:
    return True  # Rundruf
return viewer_person_id in empfaengerIds  # Gerichtet
```

### `ist_versteckt(mitteilung, viewer_role, viewer_person_id)`

Prüft ob der Betrachter diese Mitteilung ausgeblendet hat.

```python
viewer_id = viewer_person_id or f"gm:{viewer_role}"
return viewer_id in verstecktVon
```

### `fuer_viewer(mitteilungen, viewer_role, viewer_person_id)`

Filtert eine Liste: nur was der Betrachter sehen darf UND nicht ausgeblendet hat.

---

## Datenmodell (Neo4j)

```cypher
(:Mitteilung {
  id: "uuid",
  campaignId: "uuid",
  art: "TEXT",
  inhalt: "...",
  bildUrl: "",
  farbe: "rot",
  initiative: false,
  anAlle: true,
  empfaengerIds: ["uuid", ...],
  gelesenVon: ["uuid", ...],
  verstecktVon: ["uuid", ...],
  erstelltAm: "2026-09-07T20:15:00.000Z"
})
```

Keine Beziehungen zu anderen Nodes — Mitteilungen sind "Broadcast-Pakete",
keine vernetzten Entitäten.
