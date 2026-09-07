# Entitäten-API

Orte, Gegenstände, Fraktionen und andere Weltenbau-Elemente.

## Konzept

**Entitäten** sind die Bausteine der Spielwelt — alles was kein Charakter ist:

- **Orte:** Bars, Stadtteile, Gebäude, Räume
- **Gegenstände:** Waffen, Ausrüstung, Cyberdecks, Schlüssel
- **Fraktionen:** Konzerne, Gangs, Regierungen, Geheimgesellschaften
- **Fahrzeuge:** Motorräder, Autos, Drohnen

Als Graph modelliert: Orte enthalten Orte, Fraktionen kontrollieren Orte,
Gegenstände befinden sich an Orten.

---

## Gemeinsame Struktur

Alle Entitäten haben:

```json
{
  "id": "uuid",
  "campaignId": "uuid",
  "name": "Die Neon-Katze",
  "beschreibung": "Eine heruntergekommene Bar...",
  "bildUrl": "/uploads/.../bar.jpg",
  "sichtbarFuerSpieler": false,
  "tags": ["bar", "hafen", "treffpunkt"],
  "notizen": "Hier trifft sich die Crew von Session 3"
}
```

`notizen` ist SL-only, `beschreibung` ist für Spieler (wenn freigegeben).

---

## Orte

### Zusätzliche Felder

```json
{
  "ortTyp": "gebaeude",  // stadteil, gebaeude, raum, wildnis
  "enthaelt": ["raum-uuid-1", "raum-uuid-2"],
  "liegtIn": "stadtteil-uuid"
}
```

### Hierarchie

Orte sind hierarchisch: Stadtteil → Gebäude → Räume.

```cypher
(:Ort {ortTyp: "stadtteil", name: "Hafenviertel"})
  <-[:LIEGT_IN]-
(:Ort {ortTyp: "gebaeude", name: "Die Neon-Katze"})
  <-[:LIEGT_IN]-
(:Ort {ortTyp: "raum", name: "Hinterzimmer"})
```

### Szenen & Musik (geplant)

> Mark plant: Orte/Szenen bekommen eine Spotify-Playlist. Beim Wechsel zu
> diesem Ort startet die Musik automatisch auf dem Yamaha RX-V4A (MusicCast).

---

## Gegenstände

### Zusätzliche Felder

```json
{
  "gegenstandTyp": "waffe",  // waffe, ruestung, werkzeug, verbrauch, sonstiges
  "wert": 500,  // in Nuyen
  "gewicht": 2.5,  // in kg
  "seltenheit": "selten",  // gewoehnlich, ungewoehnlich, selten, einzigartig
  "eigenschaften": {
    "schaden": "3W6",
    "reichweite": "nah"
  }
}
```

### Besitz

```cypher
(:Person)-[:BESITZT { anzahl: 2, ausgeruestet: false }]->(:Gegenstand)
(:Ort)-[:ENTHAELT]->(:Gegenstand)  // Liegt herum
(:Haendler)-[:VERKAUFT { preis: 600 }]->(:Gegenstand)  // Im Shop
```

### Inventar-Aktionen

- **Aufheben:** `POST /personen/{id}/inventar` mit `{ gegenstandId, anzahl }`
- **Ablegen:** `DELETE /personen/{id}/inventar/{item_id}`
- **Ausrüsten:** `PATCH /personen/{id}/inventar/{item_id}` mit `{ ausgeruestet: true }`

**Wegwerfen geht in den SL-Papierkorb:**
> Mark: "Ich will nicht dass versehentlich gelöschte Gegenstände weg sind.
> Ein Papierkorb, den nur die SL sieht."

---

## Fraktionen

### Zusätzliche Felder

```json
{
  "fraktionTyp": "konzern",  // konzern, gang, regierung, geheim, sonstige
  "hauptquartier": "ort-uuid",
  "territorien": ["ort-uuid-1", "ort-uuid-2"],
  "feinde": ["fraktion-uuid"],
  "verbuendete": ["fraktion-uuid"],
  "ressourcen": "hoch"  // niedrig, mittel, hoch, enorm
}
```

### Beziehungen

```cypher
(:Fraktion)-[:KONTROLLIERT]->(:Ort)
(:Fraktion)-[:VERFEINDET_MIT]->(:Fraktion)
(:Fraktion)-[:VERBUENDET_MIT]->(:Fraktion)
(:Person)-[:MITGLIED_VON { rang: "Lieutenant" }]->(:Fraktion)
```

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/entitaeten`

### GET `/{typ}`

Alle Entitäten eines Typs (`orte`, `gegenstaende`, `fraktionen`, `fahrzeuge`).

### POST `/{typ}`

Neue Entität anlegen. **Nur SL.**

### GET `/{typ}/{id}`

Einzelne Entität.

### PATCH `/{typ}/{id}`

Bearbeiten. **Nur SL.**

### DELETE `/{typ}/{id}`

Löschen. **Nur SL. Geht in Papierkorb.**

---

## Sichtbarkeit

Wie bei Personen: `sichtbarFuerSpieler` steuert ob Spieler die Entität sehen.

**Separate Freigabe:** Wenn ein Ort freigegeben ist, sind die Gegenstände darin
NICHT automatisch freigegeben. Jede Entität hat eigene Sichtbarkeit.

---

## Graph-Visualisierung

Das Frontend kann Entitäten als **Cytoscape-Graph** darstellen:
- Nodes = Entitäten
- Edges = Beziehungen (LIEGT_IN, KONTROLLIERT, VERFEINDET_MIT, ...)

Farben kommen aus dem Kampagnen-Theme via CSS-Variablen.
