# Kampf-API

Rundenbasiertes Kampfsystem mit Initiative-Verwaltung.

## Konzept

Wenn es in NeotopiA zur Sache geht, wechselt das Spiel in den **Kampfmodus**:
Rundenbasiert, mit Initiative-Reihenfolge und Zustandsverfolgung.

**Nicht simuliert:** Würfelergebnisse, Regelwerk. Das bleibt am Tisch — das
Tool verwaltet nur *wer wann dran ist* und *was auf dem Feld steht*.
**Ausnahme:** Rüstungsschaden wird sehr wohl gerechnet, siehe
[Rüstung](./ruestung.md) — dort ist die Formel komplex genug (Abnutzung,
Abstufung), dass "am Tisch nachrechnen" fehleranfällig wäre.

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/kampf`

### GET `/`

Aktueller Kampfstatus.

```json
{
  "id": "kampf-uuid",
  "runde": 2,
  "amZug": "person-uuid",
  "begonnen": true,
  "teilnehmer": [
    {
      "personId": "uuid",
      "name": "Ryu Tanaka",
      "initiative": 18,
      "status": "aktiv",
      "position": { "x": 5, "y": 3 }
    }
  ]
}
```

`null` wenn kein Kampf aktiv.

---

### POST `/starten`

Kampf beginnen. **Nur SL.**

```json
{
  "teilnehmer": ["person-uuid-1", "person-uuid-2", "npc-uuid-1"]
}
```

Setzt alle Initiativen auf 0, wartet auf Eingaben.

---

### POST `/initiative`

Initiative für einen Teilnehmer setzen. **Spieler für eigenen PC, SL für alle.**

```json
{
  "personId": "uuid",
  "wert": 18
}
```

---

### POST `/naechster`

Zug beenden, nächster Teilnehmer ist dran. **Nur SL.**

Sortiert nach Initiative (höchste zuerst), setzt `amZug` auf den nächsten.
Am Ende der Runde: `runde++`, wieder von vorne.

---

### POST `/beenden`

Kampf beenden. **Nur SL.**

Löscht den Kampf-Node, alle sind wieder im "Erkunden"-Modus.

---

## Initiative-Eingabe

Wenn die SL eine WARNUNG mit `initiative: true` schickt, erscheint auf den
Spieler-Tablets ein Eingabefeld direkt im Popup:

```
┌─────────────────────────────────────┐
│  ⚠️  WÜRFELT FÜR INITIATIVE!       │
│                                     │
│  Dein Wurf: [____] [Bestätigen]    │
│                                     │
└─────────────────────────────────────┘
```

Der Wert wird via POST `/initiative` gemeldet. Die SL sieht live, wer schon
eingegeben hat.

**Warum im Popup statt separatem Screen?**
> Der Spieler soll nicht wegnavigieren müssen. Die Ansage kommt, er tippt,
> fertig. Ein Klick weniger.

---

## WebSocket (geplant)

Aktuell kein eigener WebSocket für Kampf — Updates kommen über Page-Refresh
oder Polling. Geplant:

```
ws://localhost:8000/api/campaigns/{campaign_id}/kampf/live
```

Events:
- `teilnehmerHinzugefuegt`
- `initiativeGesetzt`
- `zugGewechselt`
- `kampfBeendet`

---

## Datenmodell (Neo4j)

```cypher
(:Kampf {
  id: "uuid",
  campaignId: "uuid",
  runde: 2,
  amZug: "person-uuid",
  begonnen: true
})

// Teilnahme als Beziehung
(:Person)-[:KAEMPFT {
  initiative: 18,
  status: "aktiv",  // aktiv, bewusstlos, geflohen, tot
  position: { x: 5, y: 3 }  // optional, für Battlemap
}]->(:Kampf)
```

---

## Status-Werte

| Status | Beschreibung |
|--------|-------------|
| `aktiv` | Kann handeln |
| `bewusstlos` | Wird übersprungen, kann wiederbelebt werden |
| `geflohen` | Hat den Kampf verlassen |
| `tot` | Permanent aus dem Kampf |

Die SL setzt den Status manuell — keine automatische "0 HP = tot"-Logik.
