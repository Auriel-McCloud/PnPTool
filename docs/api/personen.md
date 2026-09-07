# Personen-API

Spielercharaktere (PCs) und Nichtspielercharaktere (NPCs).

## Konzept

**Personen** sind das Herzstück von NeotopiA — die Charaktere, die die
Geschichte bevölkern. Zwei Typen:

- **PC (Player Character):** Spielercharakter, von einem Spieler gesteuert
- **NPC (Non-Player Character):** Von der SL gesteuert, vom Barkeeper bis zum Endgegner

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/personen`

### GET `/`

Alle Personen der Kampagne.

**Spieler sehen:** Nur freigegebene NPCs + alle PCs (reduziert).
**SL sieht:** Alles.

```json
[
  {
    "id": "uuid",
    "personType": "PC",
    "name": "Ryu Tanaka",
    "alias": "",
    "rasse": "Mensch",
    "beruf": "Street Samurai",
    "bildUrl": "/uploads/.../portrait.jpg",
    "sichtbarFuerSpieler": true
  }
]
```

---

### GET `/{person_id}`

Einzelne Person mit allen Details.

**Für NPCs:** Spieler sehen nur wenn `sichtbarFuerSpieler: true`, und dann
nur die Felder die ihrer Kontakt-Stufe entsprechen (siehe [Kontakte](./kontakte.md)).

---

### GET `/{person_id}/bogen`

Vollständiger Charakterbogen. **PC: Eigentümer oder SL. NPC: Nur SL.**

```json
{
  "id": "uuid",
  "name": "Ryu Tanaka",
  "attribute": {
    "staerke": 3,
    "geschick": 4,
    "ausdauer": 3,
    "charisma": 2,
    "intelligenz": 3,
    "willenskraft": 3
  },
  "fertigkeiten": [
    { "name": "Nahkampf", "wert": 4 },
    { "name": "Schusswaffen", "wert": 3 }
  ],
  "cyberware": [
    { "name": "Reflexbooster", "stufe": 2, "essenzKosten": 0.5 }
  ],
  "ausruestung": [
    { "id": "item-uuid", "name": "Katana", "anzahl": 1 }
  ],
  "hintergrund": "Geboren in den Sprawls von Neo-Tokyo...",
  "notizen": "Sucht seinen vermissten Bruder",
  "erfahrungspunkte": {
    "gesamt": 150,
    "ausgegeben": 120,
    "verfuegbar": 30
  }
}
```

---

### POST `/`

Person anlegen. **Nur SL.**

---

### PATCH `/{person_id}`

Person bearbeiten. **SL oder Eigentümer (nur bestimmte Felder).**

---

### DELETE `/{person_id}`

Person löschen. **Nur SL. Bestätigungsdialog im Frontend.**

---

## Attribut-System

NeotopiA nutzt ein **WoD-inspiriertes** Attributsystem (1-5 Punkte):

| Attribut | Beschreibung |
|----------|-------------|
| Stärke | Körperkraft, Nahkampfschaden |
| Geschick | Reflexe, Feinmotorik, Ausweichen |
| Ausdauer | Zähigkeit, Gesundheit, Resistenz |
| Charisma | Ausstrahlung, Überzeugung |
| Intelligenz | Wissen, Analyse, Technik |
| Willenskraft | Mentale Stärke, Magie-Resistenz |

---

## Erfahrungspunkte

**Zwei EP-Typen:**

1. **Kampagnen-EP (global):** Alle PCs bekommen dieselben EP am Ende einer
   Session. Fair, kein Tracking wer "mehr gemacht" hat.

2. **Extra-EP (individuell):** Bonus für herausragendes Rollenspiel, clevere
   Lösungen. Pro PC vergeben.

**Nur Plus-Button:** EP können nur hinzugefügt, nicht entfernt werden.
Ausgeben passiert beim Steigern (automatisch abgezogen).

> Mark: "Irreversibel. Bestätigungsdialog. Ich will nicht versehentlich
> 50 EP vergeben."

---

## Cyberware & Essenz

Cyberware kostet **Essenz** — je mehr Chrom, desto weniger Menschlichkeit.

```json
{
  "name": "Reflexbooster",
  "stufe": 2,
  "essenzKosten": 0.5,
  "effekt": "+2 Initiative"
}
```

**Essenz startet bei 6.0**, jedes Implantat zieht ab. Bei 0: Cyberpsychose
(SL-Entscheidung, keine automatische Regel).

**Kein generisches `bonus`-Feld:**
> Mark: "Ich will keine allgemeinen Felder für spezifische Sonderfälle.
> Initiative-Bonus nur für Reflexbooster, nicht für jedes Item."

---

## Datenmodell (Neo4j)

```cypher
(:Person {
  id: "uuid",
  campaignId: "uuid",
  personType: "PC",
  name: "Ryu Tanaka",
  alias: "",
  rasse: "Mensch",
  beruf: "Street Samurai",
  bildUrl: "...",
  sichtbarFuerSpieler: true,
  // Attribute
  staerke: 3,
  geschick: 4,
  // ... etc
})

// Besitz
(:Person)-[:BESITZT { anzahl: 1, ausgeruestet: true }]->(:Gegenstand)

// Cyberware als eigene Nodes
(:Person)-[:HAT_IMPLANTIERT]->(:Cyberware { name: "...", stufe: 2, essenzKosten: 0.5 })
```

---

## Sichtbarkeit für Spieler

NPCs haben `sichtbarFuerSpieler`:

- `false`: Existiert für Spieler nicht (geheimer Antagonist)
- `true`: Erscheint in Listen, Kontakten, Kampf

**Die Kontakt-Stufe regelt WIE VIEL man sieht**, nicht OB.
