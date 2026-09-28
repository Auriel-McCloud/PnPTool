# Zusatzfertigkeiten: campaign-gebundener Katalog optionaler Fertigkeiten

Sprengstoffe, Esoterik, Gesetzeskunde, Kosmologie, Rätsel und was die
Spielleitung sonst noch einträgt (siehe
`docs/reference/Master/Optionale_Fertigkeiten.md`). Code:
`backend/app/zusatzfertigkeiten/` (Katalog, KI-Vorschlag, Routen),
`frontend/src/zusatzfertigkeiten/` (SL-Tabelle, Spieler-Popup).

---

## Eine Ebene, nicht zwei

Anders als bei [Rassen](./rassen.md) (globaler Katalog + Freigabe je
Kampagne) gibt es hier **keinen zweiten Freigabe-Schritt**. Marks Vorgabe,
wörtlich: *"im Kampagnen Menü eine einfache Tabelle machen in der man
Skills eintragen kann, nach dem diese ja grundsätzlich keine Mechanik mit
sich bringen müsste man nur einen Namen eine Kurz und Detail Beschreibung
hinzufügen können."*

Jeder `Zusatzfertigkeit`-Knoten hängt direkt an einer Kampagne
(`campaignId`-Property, wie die meisten anderen Entitäten) und ist ab dem
Moment des Anlegens für alle Spieler dieser Kampagne wählbar.

## Keine eigene Mechanik

Reiner Name + Kurz-/Detailbeschreibung — wie eine normale Fertigkeit auf
der üblichen 0-6-Skala. Keine Sonderfähigkeiten, Boni oder Formeln am
Eintrag selbst.

## Kosten

Dieselbe Freebee-/EP-Kostentabelle wie eine normale Fertigkeit:

| Kontext | Preis |
|---|---|
| Freebee, neuer Punkt (Erstellung) | 2 pro Stufe (`FREEBEE_KOSTEN_JE_KATEGORIE["Fertigkeit"]`) |
| EP, erster Punkt (0→1) | 3 (`erfahrung.NEU_KOSTEN["Fertigkeit"]`) |
| EP, weitere Punkte | aktueller Wert × 2 (`erfahrung.FAKTOR["Fertigkeit"]`) |

**Eine noch nicht gewählte Zusatzfertigkeit neu erlernen** kostet je nach
Erstellungsphase der Person unterschiedlich:

- **Während der Erstellung** (`Person.erstellungAbgeschlossen == false`):
  zieht aus einem **eigenen, kleinen Freebee-Kontingent**
  (`ZUSATZFERTIGKEIT_FREEBEE_BUDGET = 6`, gespeichert in
  `Person.zusatzfertigkeitenFreebeesAusgegeben`), **nicht** aus dem
  Haupt-Freebee-Pool (`erstellung.FREEBEES_GESAMT`). Grund: der Hauptpool
  wird ausschließlich bei der finalen `POST .../erstellung`-Einreichung aus
  dem eingereichten Body berechnet (kein DB-Zustand) — ein Popup-Knopf, der
  schon während des laufenden Assistenten sofort schreibt, kann dort nicht
  mitrechnen.
- **Nach Erstellungsabschluss**: normaler EP-Kauf, genau wie
  `POST .../steigern` im Haupt-Fertigkeitskatalog.

**Eine bereits gewählte Zusatzfertigkeit steigern** kostet immer EP — auch
während der Erstellungsphase gibt es dafür keine Freebee-Variante (analog
zum Haupt-Fertigkeitskatalog, der ebenfalls nur den Neukauf über Freebees
kennt, nicht das Steigern eines Fertigkeitspunkts über den Erstellungswert
hinaus).

## Löschen

Hartes `DETACH DELETE` — löscht den Katalogeintrag **samt** aller
`HAT_ZUSATZFERTIGKEIT`-Kanten zu Personen, die ihn gewählt haben. Anders
als bei Rassen (`Person.rasse` bleibt als Text bestehen) hat eine
Zusatzfertigkeit kein eigenes Textfeld am Charakter — sie IST die Kante zum
Katalogknoten. Ohne den Knoten bliebe eine kaputte Referenz.

## Endpunkte

Katalog-Basis: `/api/campaigns/{campaign_id}/zusatzfertigkeiten`
Personen-Basis: `/api/campaigns/{campaign_id}/personen/{person_id}/zusatzfertigkeiten`

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `` (Katalog) | alle mit Zugang | Der ganze Katalog dieser Kampagne |
| POST | `` (Katalog) | nur SL | Neuen Eintrag anlegen — sofort wählbar |
| PATCH | `/{id}` (Katalog) | nur SL | Name/Kurz-/Detailbeschreibung ändern |
| DELETE | `/{id}` (Katalog) | nur SL | Entfernen, inkl. Personen-Kanten |
| GET | `/ki-vorschlaege?anzahl=5` | nur SL | 3-5 KI-Kandidaten (speichert nichts) |
| POST | `/ki-vorschlaege/uebernehmen` | nur SL | Einen bestätigten Vorschlag anlegen |
| GET | `` (Personen) | SL / eigener Spieler | Gewählte Zusatzfertigkeiten samt Kontingent |
| POST | `` (Personen) | SL / eigener Spieler | Eine noch nicht gewählte hinzufügen (Stufe 1) |
| POST | `/{id}/steigern` (Personen) | SL / eigener Spieler | Eine gewählte um einen Punkt steigern |

Spieler dürfen die Personen-Routen nur am eigenen Charakter (404 statt 403
bei fremden Personen, wie überall sonst im Tool) — Zugriffsschutz-Test in
`backend/tests/test_zugriffsschutz.py::OHNE_GM_ERLAUBT`.

### Antwortformat der Personen-Routen

```json
{
  "gewaehlt": [
    {"id": "uuid", "name": "Sprengstoffe", "kurzbeschreibung": "...", "detailbeschreibung": "...", "rating": 2}
  ],
  "erstellungAbgeschlossen": true,
  "freebeesUebrig": 4,
  "erfahrungVerfuegbar": 45
}
```

`freebeesUebrig` ist nur vor Erstellungsabschluss relevant,
`erfahrungVerfuegbar` nur danach — beide werden trotzdem immer mitgeliefert,
damit das Frontend nicht zwei unterschiedliche Antwortformen behandeln muss.

## KI-Vorschlag

Zweistufig wie beim [Händler-Sortiment-Vorschlag](./haendler.md):
`vorschlaege()` generiert Kandidaten zur Ansicht, nichts wird gespeichert.
Die SL übernimmt jeden Vorschlag **einzeln** (bewusst kein
Sammel-Übernehmen). Der Prompt bekommt die bereits existierenden
Zusatzfertigkeiten dieser Kampagne mit (keine Duplikate) sowie den
NeotopiA-Cyberpunk-Kontext; Ton/Umfang orientiert sich an
`Optionale_Fertigkeiten.md` (Kurzbeschreibung ein Satz, Detailbeschreibung
ein Absatz).

## Datenmodell (Neo4j)

```cypher
(:Zusatzfertigkeit {
  id: "uuid",
  campaignId: "uuid",   // campaign-gebunden, KEIN ruleset-weiter Katalog
  name: "Sprengstoffe",
  kurzbeschreibung: "Herstellung, Handhabung und Entschärfung von Sprengstoffen.",
  detailbeschreibung: "..."
})

(:Campaign)-[:HAT_ENTITAET]->(:Zusatzfertigkeit)
(:Person)-[:HAT_ZUSATZFERTIGKEIT {rating: 2}]->(:Zusatzfertigkeit)
```

`Person.zusatzfertigkeitenFreebeesAusgegeben` (int, Default 0) — zusätzliches
Bogenfeld für das eigene Freebee-Kontingent, siehe Kosten-Abschnitt oben.

## Was noch fehlt

- Kein eigener UI-Weg für die SL, einem NPC/Begleiter eine Zusatzfertigkeit
  zu geben (die Personen-Route würde es technisch erlauben, aber die
  Popups hängen nur an Spieler-Flows).
- `ZUSATZFERTIGKEIT_FREEBEE_BUDGET = 6` ist eine Schätzung, nicht mit Mark
  abgestimmt.
