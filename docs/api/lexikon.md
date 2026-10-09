# Spieler-Lexikon

Automatisch gefüllter Katalog — "Welt"/"Fauna"/"Flora"/"Objekte" — aus der
Sicht eines einzelnen PCs. Siehe `docs/wiki/entities/spieler-lexikon.md` für
die vollständige Design-Begründung.

**Zwei unabhängige Sichtbarkeits-Schichten:**
1. Existenz (Name+Bild) — automatisch über die `ENTDECKT`-Kante, berechnet
   per Erreichbarkeits-BFS ab dem eigenen PC (max. 7 Hops, bricht an
   SL-geheimen Verbindungen/unsichtbaren Knoten hart ab).
2. Beschreibung — weiterhin das bestehende `sichtbarkeit`-Feld (GM/ALLE/
   SPEZIFISCH), von der SL nach einem Wissenswurf von Hand freigegeben.

---

## Endpunkte

Alle unter `/api/spieler/lexikon`. Sitzung: Spieler-Cookie, braucht
zugeordneten Charakter (`personId`), sonst leere Liste statt Fehler.

### GET `/api/spieler/lexikon`

```json
[
  {
    "id": "uuid",
    "kategorie": "welt",
    "name": "Unterschlupf",
    "bildUrl": "",
    "beschreibung": "Noch nicht erforscht — die Spielleitung hat dies noch nicht freigegeben.",
    "beschreibungSichtbar": false,
    "favorisiert": false,
    "entdecktSeit": "2026-10-09T12:00:00+00:00",
    "naehe": 0
  }
]
```

`kategorie` ist `welt` (Ort/Event/Fraktion), `fauna` (Critter), `flora`
(Gewächs) oder `objekte` (story-relevanter Gegenstand). `naehe` ist der
strukturelle Abstand zum aktuellen Party-Aufenthaltsort (0 = genau dort,
9999 = kein Pfad/keine Party-Zuordnung) — Grundlage der "In meiner
Nähe"-Standardsortierung, die das Frontend übernimmt.

### POST `/api/spieler/lexikon/favoriten`

```json
{ "zielId": "uuid" }
```

**204**. Nur für bereits entdeckte Einträge — fremde/unentdeckte ID → 404.

### DELETE `/api/spieler/lexikon/favoriten/{ziel_id}`

**204**, auch wenn nicht favorisiert (idempotent).

---

## Hooks (serverseitig, nicht per API)

`app/lexikon/hooks.py` wird von Fachmodulen aufgerufen, wenn sich etwas
ändert, das Erreichbarkeit beeinflussen kann: Party-Mitgliedschaft/
Aufenthaltsort, neue/geänderte `VERBINDUNG`, `LEBT_IN` hinzugefügt,
Sichtbarkeit von Ort/Event/Fraktion/Person/Gewächs/Gegenstand geändert,
PC neu einem Spieler-Zugang zugeordnet. Berechnung ist additiv — einmal
entdeckt bleibt entdeckt, auch wenn der Pfad später wegfällt.
