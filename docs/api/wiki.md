# Wiki-API

Weltenbau-System mit Seitenfreigabe für Spieler.

## Konzept

Das Wiki ist das **Gedächtnis der Spielwelt**: Orte, Personen, Fraktionen,
Geschichte — alles was die Spieler (und die SL) nachschlagen wollen.

**Kern-Idee:** Die SL schreibt, die Spieler lesen — aber nur das, was sie
In-Game wissen dürfen.

**Design-Entscheidungen:**

1. **Nur Seiten, kein Dokumenttyp** — Ursprünglich waren "Wiki-Artikel" und
   "Wiki-Dokumente" getrennt. Unnötig: Eine Seite ist eine Seite.

2. **SL-only als Standard** — Neue Seiten sind erstmal nur für die SL sichtbar.
   Explizit freigeben statt versehentlich spoilern.

3. **Entitätsverknüpfungen als echte Graphreferenzen** — "Diese Seite beschreibt
   den NPC Viktor" ist eine Kante im Graph, keine Textsuche. Ermöglicht
   automatische Backlinks und Konsistenzprüfungen.

4. **Freigabe ohne Vererbung** — Wenn eine Seite über einen Ort erzählt und
   einen NPC erwähnt, heißt das NICHT dass der NPC auch freigegeben ist. Jede
   Entität hat ihre eigene Sichtbarkeit.

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/wiki`

### GET `/seiten`

Alle Wiki-Seiten für diesen Betrachter.

**Response:**
```json
[
  {
    "id": "seite-uuid",
    "titel": "Die Neon-Katze",
    "kategorie": "Orte",
    "zusammenfassung": "Eine heruntergekommene Bar im Hafen...",
    "inhalt": "# Die Neon-Katze\n\nDie Bar liegt...",
    "sichtbarFuerSpieler": true,
    "verknuepfteEntitaeten": [
      { "id": "ort-uuid", "typ": "Ort", "name": "Hafenviertel" }
    ],
    "erstelltAm": "2026-08-15T...",
    "geaendertAm": "2026-09-01T..."
  }
]
```

**Spieler sehen nur Seiten mit `sichtbarFuerSpieler: true`.**

---

### POST `/seiten`

Neue Seite anlegen. **Nur SL.**

```json
{
  "titel": "Tanaka Corporation",
  "kategorie": "Fraktionen",
  "inhalt": "# Tanaka Corporation\n\nEiner der größten Megakonzerne...",
  "sichtbarFuerSpieler": false,
  "verknuepfteEntitaeten": ["fraktion-uuid"]
}
```

---

### PATCH `/seiten/{seite_id}`

Seite bearbeiten. **Nur SL.**

---

### DELETE `/seiten/{seite_id}`

Seite löschen. **Nur SL.**

---

### POST `/seiten/{seite_id}/freigeben`

Seite für Spieler freigeben. **Nur SL.**

**"Bis hierher"-Funktion:** Optional mit `{ "bisHierher": true }` — gibt diese
Seite UND alle verlinkten Seiten frei, die bereits `sichtbarFuerSpieler: true`
vorbereitet haben.

> Mark: "Ich will einen Knopf der 'diese Seite und alles was sie erwähnt'
> freigibt, aber nur was ich vorher schon als 'darf man sehen' markiert habe."

---

### POST `/bilder`

Bild für Wiki-Seiten hochladen. **Nur SL.**

Multipart-FormData mit `file`. Gibt `{ "url": "/uploads/.../bild.jpg" }` zurück.

*Wird auch für Mitteilungen-Bilder genutzt (gleicher Upload-Ordner).*

---

## Kategorien

Vordefiniert, nicht frei erweiterbar:

- Orte
- Personen (NPCs, wichtige Figuren)
- Fraktionen (Konzerne, Gangs, Organisationen)
- Geschichte (Ereignisse, Timeline)
- Regeln (Hausregeln, Setting-Besonderheiten)
- Sonstiges

---

## Verknüpfungslogik

Eine Wiki-Seite kann mit **Entitäten** verknüpft sein:

```cypher
(:WikiSeite)-[:BESCHREIBT]->(:Person|Ort|Fraktion|...)
```

Das ermöglicht:
- **Backlinks:** "Diese Person wird erwähnt in: [Seite A], [Seite B]"
- **Konsistenz:** "Diese Seite beschreibt Viktor" — wenn Viktor gelöscht wird,
  wird die Verknüpfung entfernt (nicht die Seite)
- **Freigabe-Check:** "Ist der erwähnte NPC für Spieler sichtbar?"

**Sichtbarkeit ist NICHT transitiv:**
> Wenn Seite "Die Neon-Katze" freigegeben ist und NPC "Viktor" erwähnt,
> heißt das nicht dass Viktor freigegeben ist. Der Spieler sieht den Namen,
> aber kein Portrait, keine Details — es sei denn Viktor selbst ist auch
> freigegeben.

---

## Datenmodell (Neo4j)

```cypher
(:WikiSeite {
  id: "uuid",
  campaignId: "uuid",
  titel: "Die Neon-Katze",
  kategorie: "Orte",
  zusammenfassung: "...",
  inhalt: "# Markdown...",
  sichtbarFuerSpieler: true,
  erstelltAm: "...",
  geaendertAm: "..."
})

// Verknüpfung zu beschriebener Entität
(:WikiSeite)-[:BESCHREIBT]->(:Ort)
(:WikiSeite)-[:BESCHREIBT]->(:Person)
```

---

## Markdown-Unterstützung

Wiki-Inhalte sind **Markdown** mit:
- Standard-Formatierung (Überschriften, Listen, Fett/Kursiv)
- Interne Links: `[[Seite:Die Neon-Katze]]` oder `[[Person:Viktor]]`
- Bilder: `![Alt](/uploads/.../bild.jpg)`
- Tabellen (GitHub-Flavored Markdown)

**Kein HTML** — wird beim Rendern escaped (XSS-Schutz).
