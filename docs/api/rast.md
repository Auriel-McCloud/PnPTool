# Rast: Heilung über Zeit

SL-Aktion, die einen oder mehrere PCs nach einer festen, nicht gewürfelten
Formel heilt — Mark: ein Werkzeug für "zwischen den Szenen", kein
Probenwurf. Ergänzt die bisherige (Würfel-basierte) Heilung nirgends, sie
läuft komplett separat über zwei neue SL-only-Endpunkte.

## Die Formel ("Rasten")

Pro ausgewählter Person ist **ein Klick = eine Rast**. Reihenfolge ist
bindend, weil Schritt 3 vom Ergebnis von Schritt 2 abhängt und Schritt 4 vom
Ergebnis der Schritte 1-3:

1. `schadenSchlag` → `0` (vollständig geheilt, immer, unabhängig vom Rest).
2. Ist `schadenSchwer > 0` ("Tödlich" in der Anzeige): `schadenSchwer -= 1`,
   **sofort, jede Rast** — kein Zähler, kein Warten.
3. Erst wenn `schadenSchwer` NACH Schritt 2 bei `0` steht **und** noch
   `schadenAggraviert > 0` ("Unheilbar") da ist, läuft der persistente
   Zähler `schwerHeilZaehler` mit: `+= 1` pro Rast.
   - Steht der Zähler danach bei `>= 7`: Wraparound — `schwerHeilZaehler -= 7`
     **und** `schadenAggraviert -= 1`. Sieben Rasten OHNE offenen
     Tödlich-Schaden heilen also einen Unheilbar-Punkt.
   - Solange noch Tödlich-Schaden offen ist, bleibt der Zähler stehen —
     Unheilbar heilt erst, wenn der PC vom tödlichen Schaden runter ist.
     **Korrektur 12.10.2026** (Mark, nach Praxistest am Spieltisch): die
     ursprüngliche Formel hatte das verkehrt herum — der Zähler lief nur
     MIT offenem Tödlich-Schaden und fror ein, sobald der bei 0 stand,
     sodass reiner Unheilbar-Schaden (ohne gleichzeitigen Tödlich-Schaden)
     nie heilte, egal wie oft geklickt wurde.
4. Ist die Person **nach** Schritt 1-3 vollständig gesund (`schadenSchlag ==
   0 AND schadenSchwer == 0 AND schadenAggraviert == 0`): jedes getragene
   Rüstungsteil mit `istNatuerlich=true` **und** Kästchen-Defizit
   (`ruestungKaestchenAktuell < ruestungKaestchenMax`, Max dabei live aus der
   Widerstandsfähigkeit berechnet, siehe `docs/api/ruestung.md`) heilt `+1`
   Kästchen, gecappt auf dieses Max. Das gilt **schon in genau der Rast, in
   der die Person gerade vollständig gesund geworden ist** — nicht erst ab
   der nächsten.

Reine Funktionen in `app/traits/rast.py`:

- `person_aenderung(person) -> dict` — Schritte 1-3, liefert die vier zu
  schreibenden Felder (`schadenSchlag`, `schadenSchwer`, `schadenAggraviert`,
  `schwerHeilZaehler`).
- `ist_vollstaendig_gesund(aenderung) -> bool` — Schritt-4-Bedingung.
- `ruestung_heilung(teile) -> list[dict]` — welche Rüstungsteile (mit
  Live-Max bereits angewendet, siehe unten) +1 heilen; liefert nur die
  tatsächlich betroffenen (`id`, neues `ruestungKaestchenAktuell`).

## Fallback: "Vollständige Heilung"

Mark: "für den Fall der Fälle" — keine Bedingungen, kein Würfeln, kein
Schritt-für-Schritt. Setzt pro ausgewählter Person:

- `schadenSchlag = 0`, `schadenSchwer = 0`, `schadenAggraviert = 0`,
  `schwerHeilZaehler = 0`
- **jedes** getragene Rüstungsteil (auch nicht-natürliches, anders als beim
  normalen Rasten) sofort auf den vollen (live berechneten) Max.

Funktionen: `vollheilung_person() -> dict`, `vollheilung_ruestung(teile) ->
list[dict]` (identische Rückgabeform wie `ruestung_heilung`, aber ohne
`istNatuerlich`/Defizit-Bedingung).

## Endpunkte

Beide nur SL (`Depends(require_campaign_gm)`), liegen in
`app/traits/routes.py` (neben `zustand`/`steckbrief`, kein eigenes Modul —
sie brauchen dieselben Bogen-Bausteine wie die bestehenden Trait-Routen und
es gibt noch keine eigenständige "Rast"-Domäne im Datenmodell).

### POST `/api/campaigns/{campaign_id}/personen/rasten`

```json
{ "personIds": ["<id1>", "<id2>"] }
```

Wendet die Rast-Formel auf jede Person an (eine Rast pro ID in der Liste).
Unbekannte/gelöschte IDs werden übersprungen, nicht als Fehler gemeldet —
eine Mehrfachauswahl soll nicht an einem einzelnen ungültigen Eintrag
scheitern. Antwort: `{ personId: BogenUebersicht }` — dieselbe Form wie die
`zustand`-Route liefert, einmal pro betroffener Person, direkt fürs
Charakterblatt verwendbar.

### POST `/api/campaigns/{campaign_id}/personen/vollstaendige-heilung`

```json
{ "personIds": ["<id1>", "<id2>"] }
```

Gleiche Response-Form, wendet statt der Rast-Formel die bedingungslose
Vollheilung an.

## Datenmodell (Neo4j)

Eine neue Property an `(:Person)`, analog zu `rassenFeatureGenutzt`:

```cypher
(:Person { schwerHeilZaehler: 0, ... })
```

**Default nicht vergessen** — dieses Projekt hatte an exakt dieser Stelle
schon einen echten Bug (fehlender Default an einem neuen Person-Feld →
`GET /personen` crasht für die ganze Kampagne, siehe `CLAUDE.md`,
"Ideenschmiede lädt Entwürfe wieder", 10.10.2026). Decode-Default sitzt in
`entities/repository.py::_BOGEN_DEFAULTS["schwerHeilZaehler"] = 0`, Feld in
`_BOGEN_FELDER`/`PERSON_FIELDS`. Schemas (`entities/schemas.py`):
`PersonCreate`/`PersonResponse` mit `schwerHeilZaehler: int = 0`,
`PersonUpdate` mit `schwerHeilZaehler: int | None = None`.

`schwerHeilZaehler` erscheint zusätzlich informativ im Bogen-Output
(`traits/bogen.py`), damit die SL sieht, wie weit der nächste geheilte
Unheilbar-Punkt noch entfernt ist (0–6, wrapt bei 7).

## Frontend

Neues SL-only Popup `frontend/src/traits/RastenVerwaltung.tsx`, erreichbar
über ein neues Werkzeugleisten-Symbol 🏕️ in `App.tsx` (neben 🏆
Achievements). Inhalt: Liste aller PCs der Kampagne mit Checkboxen + "Alle
auswählen", zwei Buttons "🏕️ Rasten" und "✚ Vollständige Heilung" — beide
hinter der bestehenden `Bestaetigung`-Komponente (`shell/Bestaetigung.tsx`),
weil beide Aktionen folgenreich und nicht rückgängig zu machen sind. Zeigt
nach einem Aufruf pro Person kompakt Schlag/Schwer/Unheilbar/Heil-Zähler an.

## Verifiziert

- `backend/tests/test_rast.py` (pytest, 20 Fälle): Schlag immer voll,
  Schwer -1 + Zähler-Inkrement 0→6, Wraparound bei genau 7 (inkl.
  End-to-End-Lauf über 7 Rasten), "gesund in genau dieser Rast zählt schon",
  Rüstungsheilung nur bei `istNatuerlich` + Defizit, Vollheilung
  bedingungslos, Zusammenspiel mit `anwende_natuerliche_ruestung` (Live-Max
  bestimmt das Defizit, nicht der gespeicherte Wert).
- Echtes E2E-Skript gegen laufendes Backend+Neo4j (disposable GM, Kampagne,
  PC, natürliche Rüstung, disposable Spieler-Account — alles danach wieder
  gelöscht): beide Rast-Szenarien (kein Vollheil-Trigger vs. Wraparound +
  Sofortheilung der Rüstung in derselben Rast) und die Vollheilung
  Zahl-für-Zahl über die echten HTTP-Endpunkte bestätigt. Kein Klicktest im
  Browser für Feature B — siehe Abschlussbericht/CLAUDE.md für den
  aktuellen Verifikationsstand.
