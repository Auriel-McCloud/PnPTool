---
title: Drohnen und Fahrzeuge
created: 2026-09-18
updated: 2026-10-25
type: konzept
tags: [drohnen, fahrzeuge, kampf, erfahrung, wirtschaft, inventar, versionsgeschichte, entschieden, offen]
sources: [../../CLAUDE.md, ../../../backend/app/begleiter/, ../../../backend/app/entities/schemas.py, ../../../backend/app/traits/bogen.py, ../../../backend/app/traits/erfahrung.py, ../../../backend/app/kampf/ruestung.py, ../../../backend/app/kampf/initiative.py, ../../../backend/app/items/schemas.py, ../../../backend/app/items/chrom.py]
status: teilweise-umgesetzt
---

# Drohnen und Fahrzeuge

## Definition (Stand 25.10.2026 — komplett neu entschieden, siehe „Entwicklung“)

Mark baute einen Rigger-Charakter und merkte: das bisherige Drohne-Gegenstandsfeld
(Stufe/Widerstand/Angriff/Agilität direkt am `Gegenstand`, siehe „Alte Version“
unten) reicht nicht — eine Drohne soll Rüstung tragen, Waffen ausrüsten, eigene
Fertigkeiten haben und zusammen mit ihrem Rigger an der Initiative teilnehmen.
Das geht mit einem reinen Item nicht (ein Gegenstand kann nicht selbst Besitzer
eines anderen Gegenstands sein, siehe Architekturbegründung unten). Komplette
Neuentscheidung, im Chat mit Mark Punkt für Punkt durchgesprochen.

### Architekturentscheidung: eigener Person-artiger Knotentyp

`Gegenstand`-Besitz läuft im ganzen Projekt ausschließlich über
`(:Person)-[:BESITZT]->(:Gegenstand)` (siehe
[[../entities/neo4j-datenmodell]]). Damit eine Drohne Waffen/Rüstung tragen
kann, muss sie selbst ein `Person`-Knoten sein — alles andere würde das
komplette Besitz-/Ausrüstungssystem für einen zweiten Knotentyp duplizieren.

Neue Flags `istDrohne`/`istFahrzeug` an `Person`, nach demselben Muster wie
`istCritter`/`istKI` (20.09.2026): `sichtbare_kategorien()` tauscht die
Blattstruktur komplett aus, statt eine eigene Blattvariante zu pflegen. Damit
sind Ausrüstungssystem (`BESITZT`/`AUSGERÜSTET`), Initiative-Pool-Mechanismus
und die Rigger-Beziehung (`BEGLEITET` Person→Person, wie bei Critter) **ohne
Parallelimplementierung** mit dabei.

Das alte Begleiter-Sheet (Sprite/Geist, `app/begleiter/`) bleibt für Sprites
und Geister unverändert bestehen — andere Mechanik (kein Körper, kein
Rucksack), bewusst nicht angefasst.

### Die 8 Attribute — zwei Spalten statt drei

Keine dritte (soziale) Spalte, Drohnen/Fahrzeuge haben keine Sozialwerte.

| Körperlich | Technisch |
|---|---|
| Stärke | CPU |
| Geschick | Arbeitsspeicher |
| Geschwindigkeit | Außenhülle (Rüstungsreduktion — teurer, siehe Kosten) |
| Widerstandsfähigkeit | I.C.E. (Matrix-Verteidigung — **eigenes steigerbares Attribut**, nicht abgeleitet wie bei Menschen/Neuroweavern) |

### Initiative

`Geschwindigkeit + CPU` — neuer Formel-Zweig in `bogen.py::initiative()`
neben der bestehenden `Geistesschärfe + Geschicklichkeit + Cyberware-Mod` für
Menschen. Gleiches Muster wie `ice_max()`, das für Neuroweaver schon einen
Sonderzweig hat.

### Fertigkeiten

**Entschieden (25.10.2026): die volle Fertigkeitenliste, kein Filter.** Mark:
auch soziale Fertigkeiten wie Etiketten/Menschenkenntnis/Darbietung können bei
einem Roboter Sinn ergeben (Benimm-/Gesichtserkennungs-Programme), keine
Kategorie wird grundsätzlich ausgeschlossen. Drohnen/Fahrzeuge nutzen damit
dieselbe `Fertigkeit`-Kategorie wie Menschen, keine eigene
`FertigkeitDrohne`-Kategorie nötig.

**Kuratiert (26.10.2026, Mark nach dem ersten Klicktest — Einzelfall-
Ausnahmen von der Liste oben, keine Rücknahme der Grundsatzentscheidung):**
Schusswaffen/Nahkampf/Wahrnehmung/Sportlichkeit (nur an der Drohne als
"Ausweichen" ANGEZEIGT, der Katalogname bleibt Sportlichkeit — Menschen sehen
weiterhin "Sportlichkeit") plus "Fliegen" stehen im Umbauen-Reiter oben,
alles andere hinter einem "weitere Fertigkeiten"-Umschalter.
**"Riggen" ist komplett aus der Drohnen-Liste entfernt** (serverseitig
UND clientseitig, `traits/drohnen.py::DROHNE_GESPERRTE_FERTIGKEITEN`) — eine
Drohne riggt sich nicht selbst, das beschreibt nur, wie ein MENSCH sie
fernsteuert.

**Neue Fertigkeit „Fliegen" läuft über die bestehenden Zusatzfertigkeiten**
(`app/zusatzfertigkeiten/`, campaign-gebundener SL-Katalog), nicht über den
Kern-Trait-Katalog — Marks eigene, bessere Lösung: keine Katalog-Änderung,
kein Code. `HAT_ZUSATZFERTIGKEIT` hängt generisch an `Person`, ohne
Typ-Ausschluss — sobald Drohne/Fahrzeug ein Person-Knoten ist (siehe oben),
ist „Fliegen" dort automatisch genauso wählbar wie bei einem menschlichen
Piloten. Mark trägt es einfach in die SL-Tabelle „Zusatzfertigkeiten" ein.
**26.10.2026, gebaut:** Zusatzfertigkeiten sind jetzt auch mit Nuyen an der
Drohne kaufbar (`GET`/`POST .../drohnen/{id}/steigern`, Id-Präfix `zf:`,
gleiche Nuyen-Formel wie normale Fertigkeiten) — vorher war nur die Anzeige
im Charakterblatt vorbereitet, keine Möglichkeit, eine Zusatzfertigkeit an
der Drohne überhaupt zu erwerben.

### Lebenspunkte / Struktur

Kein neues System nötig: `bogen.py::gesundheit_max()` ist bereits
`personenspezifischer Grundwert + Widerstandsfähigkeit` (seit dem
Critter-Feature vom 10.10.2026, siehe [[attribute-und-fertigkeiten]]). Ein
Raumschiff bekommt einfach einen hohen Grundwert, das Kästchen-Tracking im
Blatt skaliert automatisch mit — exakt dieselbe Mechanik wie bei einer Ratte
mit Grundwert 1.

### Erschaffung & Steigerung: Nuyen statt XP

Gleiche Formel-Mechanik wie `traits/erfahrung.py` (Preis = aktueller Wert ×
Faktor, Einstieg per `NEU_KOSTEN`), aber in Nuyen statt Erfahrungspunkten:

- **`AttributDrohne`** (Stärke/Geschick/Geschwindigkeit/Widerstandsfähigkeit/
  CPU/Arbeitsspeicher/I.C.E.) — Standard-Attribut-Faktor, wie bei Menschen.
- **`AttributDrohneAussenhuelle`** — gleicher Einstiegspreis wie die anderen
  Drohnen-Attribute, aber **doppelter Faktor** (Marks Vorgabe: „der erste ist
  noch günstig, aber ab dem zweiten wird's rapide teurer“) — reiner
  Zahlendreh in derselben Formel, kein neuer Mechanismus.
- Fertigkeiten laufen über die normale **`Fertigkeit`**-Kategorie, dieselbe
  wie bei Menschen (siehe oben — keine eigene Kategorie nötig).
- Neue Kampagnen-Einstellung **`nuyenProXp`** (Default **200¥**, Mark kann sie
  jederzeit im Einstellungen-Popup ändern — Startwert zum Playtesten, keine
  endgültige Zahl). Rechnet den XP-Formel-Preis in Nuyen um. Der Kauf läuft
  über den bestehenden `VerhandlungPopup`-Mechanismus (Spieler bietet,
  Mark bestätigt/ändert) — gleiches Muster wie Rüstungsreparatur beim Händler.
- **Anzeige-Deckel:** Punkte werden als Kreise angezeigt bis zu einer
  Obergrenze (Vorschlag: 10, analog zur Waffenschaden-Skala 1–12, wo ab 8 nur
  noch Schiffswaffen stehen), darüber nur die nackte Zahl — sonst hätte ein
  Raumschiff-Attribut 30+ Kreise. **Exakte Zahl noch offen.**

### Riggerkonsole & aktive Slots

- `riggerBonus` und `maxDrohnen` existieren bereits als Felder am
  Riggerkonsole-`Gegenstand` (`items/schemas.py`) — bisher nur Datenablage,
  nirgends ausgewertet. Werden jetzt zum Slot-Limit.
- Neues Feld `riggerAktiv` am Drohnen/Fahrzeug-Knoten. Aktivieren/Deaktivieren
  serverseitig gegen `maxDrohnen` der ausgerüsteten Konsole gedeckelt.
- Neues Burgermenü **„Fahrzeuge & Drohnen“**, auch für Spieler sichtbar:
  - **Ohne Riggerkonsole:** eine einzelne Steckbrief-Kachel (Bild, Zustand,
    Werte), Klick öffnet das Detail-„Charakterblatt“-Popup.
  - **Mit Riggerkonsole:** oben visuell umrandete **aktive Slots** (Bild +
    Kurz-Steckbrief je Drohne), darunter eine Liste aller übrigen
    Drohnen/Fahrzeuge mit Aktivieren/Deaktivieren-Knopf.
- **Inaktive Drohnen erscheinen NICHT im Kampf** — die
  Teilnehmer-Hinzufügen-Liste filtert auf `riggerAktiv=true`.

### Hot-Gehen / Neurolink (28.10.2026, entschieden, noch nicht gebaut)

Mark hat die bisher brachliegende Bedeutung von `riggerBonus` festgelegt: er
ist die Voraussetzung, mit der Riggerkonsole (später auch dem Cyberdeck) in
den Modus **„Hot“** zu gehen — direktes Einklinken in eine Drohne bzw. (beim
Deck) direkt in die Matrix, statt nur normaler Fernsteuerung.

- **Neues Chrom „Neurolink“** (typ Cyberware, normales
  `koerperzone`/`slot`-Chirurgie-Schema wie jedes andere Implantat):
  **Pflichtvoraussetzung** fürs Hot-Gehen. Ohne Neurolink bleibt nur normales
  Fernsteuern ohne den Hot-Bonus — Konsole/Deck allein reichen nicht.
- Neuer Wert **„Einklinken“** am Neurolink: reines **Ja/Nein-Flag**
  (schaltet die Fähigkeit frei), kein eigener Zahlenwert.
- **Proben:** solange Hot verbunden, läuft **jede Probe der Drohne** als
  Skill(Drohne) + **Riggen(Rigger)** — pauschal, nicht nur die zum jeweiligen
  Attribut passende Probe. Der Rigger-Fertigkeitswert ersetzt das
  Drohnen-Attribut komplett für die Dauer der Hot-Verbindung.
- **Initiative:** die Drohne übernimmt den Initiative-Slot des Riggers
  (**das jeweils schnellere/bessere** der beiden Werte), der Rigger steuert
  nicht mehr sich selbst. Die Drohne läuft NICHT zusätzlich in ihrem
  eigenen, ursprünglichen Slot.
- **Verbindungsabbruch im Kampf** (z. B. Drohne zerstört): der Rigger
  erleidet Dumpshock und fällt für den Rest der laufenden Runde aus. Sobald
  sein ursprünglicher Initiative-Slot wieder dran ist, fragt das Tool ihn,
  ob er die Drohne weiterhin Hot steuert — **Ja:** er bleibt ausgefallen,
  die Drohne handelt stattdessen in genau diesem Slot (ihr eigener Slot
  bleibt ungenutzt). Das ist die generelle Mechanik für jede Runde, nicht
  nur beim Verbindungsabbruch.
- **Noch offen:** exakte Nuyen-/Chirurgie-Kosten des Neurolink-Chroms.

### Drohnen-Augments (28.10.2026, entschieden, noch nicht gebaut)

Gleiches System wie bei menschlichem Chrom (Cyberware/Bioware/Hexware, siehe
[[cyberware-bioware]]), aber als eigene, 4.-Kategorie-artige Variante rein
über ein Flag statt eines neuen `typ`:

- Neues Feld **`istDrohnenAugment`** am Gegenstand (wie `istWaffe`/
  `istMaschinenteil`) — kein neuer Eintrag in `GEGENSTAND_TYPEN` nötig.
  Filterbar im Shop (eigene Warenkategorie bei Händlern) und im
  Umbauen-Dialog der Drohne.
- **Eigenes Körperzonen-Schema für Drohnen statt der menschlichen
  Kopf/Arme/Beine/Torso-Zonen** — Mark: z. B. Chassis/Sensorik/Antrieb.
  Genaue Zonen/Slot-Zahl je Zone noch offen, aber das 3-Slot-Prinzip
  (`items/repository.py::slot_konflikt`) wird wiederverwendet, nur mit
  drohnenspezifischen Zonennamen.

### Ausrüstung

Da `Person`-Knoten: Waffen und Rüstung laufen 1:1 über das bestehende
`BESITZT`/`AUSGERÜSTET`-System, keine Parallelimplementierung.
**26.10.2026, gebaut:** eigener Reiter „Ausrüstung" im `DrohnenFenster.tsx`
(**nur SL**) zeigt die Gegenstände der Drohne als `GegenstandKachel` und
erlaubt Ausrüsten/Ablegen. Neue Gegenstände legt die SL weiterhin über die
normale Gegenstände-Verwaltung an (Besitzer auf die Drohne setzen) — kein
zweiter Anlegen-Dialog. **Nicht für Spieler freigegeben:**
`items/routes.py::ablage_aendern` prüft bei Nicht-GM
  `viewer.person_id == Besitzer`, und Besitzer der Ausrüstung ist die Drohne,
  nicht der gebundene Rigger — ein Spieler-Self-Service bräuchte erst eine
  eigene, über `_drohne_und_rigger_oder_404` geprüfte Route (Muster wie
  `aktivSetzen`/`riggerSetzen`), noch nicht gebaut.

**28.10.2026, gebaut:** Übergeben/Zurücknehmen zwischen Rigger- und
Drohnen-Inventar lief schon (26.10.2026). Neu: Typ-/Textfilter
(`KategorienAuswahl`, gleiche Komponente wie in `GegenstaendeUebersicht.tsx`)
in `DrohnenAusruestung.tsx` UND im `UebergebenPopup.tsx` — letzteres zeigte
bisher nur nackte Namensknöpfe ohne Steckbrief, jetzt mit Typ +
Steckbrief-Kurzzeile je Eintrag (Mark: "damit ich weiß, welche Waffe ich der
Drohne zuweise"). Reiner Frontend-Job, kein Backend/Schema geändert.

### Material statt Nuyen (26.10.2026, Minimal-Scope)

Mark wollte beim Umbau wählen können, ob ein Punkt mit ¥ oder mit einem
Material-Gegenstand bezahlt wird — bewusst NUR die Zahlung selbst, ohne
Shop-/Händler-Integration oder das größere Reparatur-Feature unten.

- Neuer Gegenstands-Flag `istMaschinenteil`/`maschinenteilQualitaet`
  (`"" | "minderwertig" | "normal" | "hochwertig"`), dasselbe Muster wie
  `istReparaturmaterial`/`reparaturKapazitaet` — Checkbox+Dropdown im
  normalen Gegenstands-Bearbeiten-Popup (`CharacterSheetPanel.tsx`).
- `traits/drohnen.py::maschinenteil_reicht(qualitaet, category)`: hochwertig
  deckt Attribute UND Fertigkeiten/Zusatzfertigkeiten, normal nur
  Fertigkeiten/Zusatzfertigkeiten, minderwertig deckt beim Umbau NICHTS
  (für die Reparatur unten reserviert).
- `GET .../drohnen/{id}/maschinenteile` listet Maschinenteile DES RIGGERS
  (nicht der Drohne — die besitzt nichts eigenes Kapital-/Material-mäßig,
  siehe oben). `POST .../drohnen/{id}/steigern` nimmt optional
  `materialGegenstandId`: verbraucht 1 Stück (Menge −1) statt ¥ vom
  Rigger-Kapital abzuziehen.
- **Bewusst draußen gelassen:** Shop-Sortiment/Händlerverkauf von
  Maschinenteilen, das Burgermenü „Reparatur" und die Hardware-Probe aus
  dem Abschnitt „Reparatur" unten — eigenständiges, größeres Folge-Feature.

### Maker-Probe beim Material-Umbau (26.10.2026, Folge-Feature)

Mark, nachdem er die ersten drei Maschinenteile im echten Einsatz probiert
hat: "es sollte nicht einfach nur möglich sein ein Maschinenteil zu
verwenden, sondern der Spieler muss dann eine Probe auf Maker machen." Der
Material-Pfad aus dem Abschnitt oben kaufte den Punkt bisher instant —
jetzt hängt er an einer selbstberichteten Maker-Probe, genau wie
Paralysewurf/Booster-Aktivierung: der Spieler würfelt physisch am Tisch,
das Tool rechnet nur den Pool vor und nimmt das Ergebnis entgegen.

- `traits/drohnen.py::benoetigte_erfolge_maker_probe(aktuell)` = `aktuell + 1`
  — je höher der Zielwert schon steht, desto mehr Erfolge nötig.
- `GET .../drohnen/{id}/maker-probe-pool?traitDefId=…`: liefert Maker
  (Hardware)-Wert DES RIGGERS, alle seine Attribute zur freien Partnerwahl
  (Mark: "den er dann mit einem Attribut kombinieren darf" — kein fester
  Pflicht-Partner wie bei der normalen Hardware-Reparatur-Probe) und die
  benötigten Erfolge. Reine Leseabfrage, würfelt nichts selbst.
- `POST .../drohnen/{id}/steigern` verlangt beim Material-Pfad jetzt
  zusätzlich `probenErgebnis: "ja" | "nein" | "patzer"` (400 ohne). "ja"
  erhöht den Wert UND verbraucht das Material, "patzer" verbraucht NUR das
  Material (kein Fortschritt), "nein" lässt beides unangetastet — der
  Rigger darf später erneut versuchen.
- Frontend (`DrohnenSteigern.tsx`/`MakerProbePopup.tsx`): Materialzahlungen
  laufen deshalb NICHT mehr über den Sammel-Warenkorb (`kaeufe`) wie die
  ¥-Käufe — ein Würfelwurf ist ein Einzelereignis am Tisch. Klick auf die
  Hauptkarte bei gewählter Material-Zahlart öffnet das Popup sofort statt
  den Kauf vorzumerken; "Speichern"/"Zurücksetzen" bleiben reine ¥-Sache.
- Gleichzeitig: die Zahlart-Knöpfe zeigen pro Qualitätsstufe jetzt EINEN
  Knopf mit Gesamtmenge (`materialGruppenFuer`) statt einen pro einzelnem,
  noch nicht zusammengelegtem Gegenstand (Mark: "nur ein Stück mit der
  Menge dort stehen, und nicht alle einzelt aufgeführt werden").
- **Weiterhin draußen gelassen:** das eigenständige Burgermenü „Reparatur"
  unten bleibt ein eigenes, noch nicht gebautes Feature — diese Maker-Probe
  gilt nur für den Umbau-Kauf (Attribut/Fertigkeit per Material steigern),
  nicht für Schadensreparatur.

### Zwei Bugfixes nach dem ersten echten Klicktest (26.10.2026)

- **Zusatzfertigkeiten ungefiltert im Drohnen-Umbau:** Mark: "ich seh das
  Mimikry und das dürfen nur Vael haben" — der Umbau zeigte bisher den
  KOMPLETTEN campaign-weiten Zusatzfertigkeiten-Katalog, auch
  rassengebundene (`nurFuerRasse`), die für eine Maschine keinen Sinn
  ergeben. Neues Feld `ZusatzfertigkeitCreate.fuerDrohnenFreigegeben`
  (Default `false`, unabhängig von `nurFuerRasse` — eine Drohne hat keine
  Rasse): `drohne_steigerungspreise`/`drohne_steigern` zeigen/erlauben nur
  noch explizit freigegebene Einträge. GM-Checkbox „Für Drohnen/Fahrzeuge
  freigeben" im Zusatzfertigkeiten-Editor (`ZusatzfertigkeitenVerwaltung.tsx`).
  **Achtung Migrationslücke:** bereits existierende Einträge wie „Fliegen"
  (siehe `WICHTIGE_FERTIGKEITEN` in `DrohnenSteigern.tsx`) verschwinden aus
  dem Umbau, bis die SL sie einmal manuell freischaltet — reiner Default,
  keine automatische Rückwärtskompatibilität.
- **Maker-Probe-Pool zeigte Drohnen-Attribute statt Rigger-Attribute:**
  Mark: "da müssen natürlich auch die Attribute des Riggers stehen." Der
  Filter `category.startswith("Attribut")` erwischte auch
  `AttributDrohne`/`AttributDrohneAussenhuelle` (Drohnen-eigene Werte wie
  Sensoren/Panzerung, andere Namen als menschliche Attribute) — die
  WERTE kamen zwar schon korrekt vom Rigger, aber als Optionsliste standen
  Drohnen-Attributnamen drin. Fix: explizite Filterliste
  `erstellung.ATTRIBUT_KATEGORIEN` (Körperlich/Gesellschaftlich/Geistig)
  plus `AttributMatrix` (KI-Rigger).

### Reparatur (neues eigenständiges Feature, gilt für Rüstung UND Drohne/Fahrzeug)

`kampf/ruestung.py` hat die komplette Formel schon fertig, bisher nur an
Rüstung gebunden — wird generisch auf jedes „Kästchen“-tragende Ziel
ausgeweitet:

- `hardware_probe_pool()` = **Maker (Hardware) + Intelligenz** (Würfelpool
  für die technische Reparatur-Probe).
- `reparatur_schwelle()`/`selbstreparatur_ergebnis()` — Erfolgs-Überschuss
  über die halbe Kästchen-Max wird zu reparierten Kästchen, gedeckelt vom
  eingesetzten Material.
- `haendler_reparatur_preis()` — fertige quadratisch-progressive Preisformel
  mit 75 %-Totalschaden-Deckel, schon generisch (`fehlende_kaestchen`/
  `kaestchen_max`/`neuwert`, kennt „Rüstung“ gar nicht explizit).
- **Ein Skill reicht am Fahrzeug** (Mark: Handwerk *oder* Maker (Hardware)
  können ein Fahrzeug reparieren, kein getrennter Struktur-/
  Elektronik-Schadenspool).
- Neues eigenständiges Burgermenü **„Reparatur“**: ein Slot für das Ziel
  (Rüstung/Drohne/Fahrzeug), ein Slot für das Verbrauchsmaterial — statt wie
  bisher im Bearbeiten-Popup des einzelnen Gegenstands versteckt
  (`RuestungReparatur.tsx`).
- Neuer Verbrauchsgegenstand **„Maschinenteil“**, analog zu
  `istReparaturmaterial`/`reparaturKapazitaet`: Qualitätsstufen
  minderwertig/normal/hochwertig — hochwertig für Attribute, normal für
  Fertigkeiten, minderwertig nur für Reparatur.
- Neues Händler-Flag **`bietetReparatur`** (analog `istTutorialHaendler`) —
  nicht jeder Laden repariert gegen Geld.

## Entwicklung

- **28.10.2026 (Hot-Gehen/Neurolink + Drohnen-Augments + Inventar-Filter,
  Besprechung mit Mark, noch nicht gebaut):** Bedeutung von `riggerBonus`
  festgelegt (Hot-Gehen-Voraussetzung), neues Chrom „Neurolink“ geplant,
  Initiative-Übernahme-Regel inkl. Dumpshock-Verhalten entschieden.
  Drohnen-Augments als `istDrohnenAugment`-Flag mit eigenem
  Körperzonen-Schema geplant. Fehlender Inventar-Filter identifiziert. Siehe
  „Hot-Gehen / Neurolink“, „Drohnen-Augments“ und „Ausrüstung“ oben.
- **18.09.2026 (Version 1):** Begleiter-Sheet-basiertes Konzept, siehe „Alte
  Version“ unten.
- **25.10.2026 (komplette Neuentscheidung):** im Chat mit Mark Punkt für
  Punkt durchgesprochen (Architektur, 8 Attribute, Initiative, I.C.E.,
  Nuyen-Kosten, Riggerkonsole-Slots, Reparatursystem) — siehe „Definition“
  oben. Auslöser: Mark baute einen Rigger-Charakter, das alte
  Drohne-Gegenstandsfeld reichte nicht mehr.
- **25.10.2026 (Phase 1 — Datenmodell-Fundament gebaut, direkt im Anschluss):**
  `istDrohne`/`istFahrzeug`/`riggerAktiv` an `Person`, acht TraitDef-Attribute
  (`AttributDrohne`×7, `AttributDrohneAussenhuelle`×1), `sichtbare_kategorien()`/
  `initiative()`/`ice_max()` mit `ist_drohne`-Zweig, neue Kosten-Kategorien in
  `erfahrung.py`. `gesundheit_max()` brauchte keine Änderung. **Verifiziert:**
  `pytest tests/test_bogen.py tests/test_drohnen_kosten.py` grün, volle Suite
  ohne Regression. Details siehe `CLAUDE.md`.
- **25.10.2026 (Phase 2 — Riggerkonsole-Slots, Nuyen-Formel, Kampf-Filter,
  direkt im Anschluss):** `nuyenProXp`-Kampagneneinstellung (Start 200¥),
  `erfahrung.nuyen_kosten()`. Riggerkonsole-`maxDrohnen` jetzt durchgesetzt
  (`items/repository.py::riggerkonsole_max_drohnen`, `entities/repository.py::
  aktive_drohnen_zahl`, reine Regel in `traits/drohnen.py::kann_aktivieren`),
  neue Routen `.../drohnen`, `.../drohnen/{id}/rigger`, `.../drohnen/{id}/aktiv`
  (Spieler-Selbstbedienung für die eigene Drohne, in
  `test_zugriffsschutz.py::OHNE_GM_ERLAUBT` eingetragen). Kampf lehnt inaktive
  Drohnen/Fahrzeuge als Teilnehmer jetzt mit 400 ab. **Verifiziert:** 52 Tests
  grün, echter E2E-Test gegen laufende Neo4j (Wegwerf-Kampagne, Slot-Deckel
  korrekt durchgesetzt, danach aufgeräumt), volle Suite ohne Regression (800
  statt 783 bestanden gegenüber unverändertem Stand, dieselben
  vorbestehenden Windows-Flakes).
- **25.10.2026 (Phase 2.5 — Nuyen-Kauf-Endpoint, direkt im Anschluss):**
  Mark beantwortete die offene Frage: „Der Rigger zahlt es aus seinem
  Kapitel, die Drohne hat keins!" Neue Routen `GET`/`POST
  .../drohnen/{id}/steigern`, Zahlung ausschließlich aus `kapitalBasis` des
  Riggers (`traits/drohnen.py::kann_bezahlen`). **Fund:** die
  Phase-1-TraitDefs waren im lokalen Dev-Neo4j noch nicht gemerged —
  `seed_traits()` läuft nur beim App-Start, ein laufender `--reload`-Prozess
  zieht neue Katalogeinträge nicht automatisch nach. Durch expliziten
  `seed_traits()`-Aufruf dauerhaft behoben. **Verifiziert:** 15/15 neue
  Tests grün, Zugriffsschutz ohne Regression, echter E2E-Kauf gegen Neo4j.
  **Phase 3 (Frontend: Burgermenü, Reparatur-Menü, Maschinenteil) noch nicht
  gebaut.**

## Alte Version (bis 25.10.2026, status: veraltet — abgelöst durch obige Neuentscheidung)

Beim Kauf wurde die **Stufe** festgelegt und frei auf Werte/Fertigkeiten
verteilt:
- Gesundheit = Stufe
- Widerstand = Schadensreduktion
- Angriff = Treffen und Schaden
- Agilität = Geschwindigkeit

**Riggen:** nutzte eigene Werte, aber höchstens bis zur Stufe der Drohne.
Charakterblatt und eigenes `DrohneFahrzeug`-Sheet enthielten je bis zu 4 Slots
für „Drohne/Fahrzeug/Sprite/Geist“ (`Neotopia.xlsx`) — siehe
[[../../reference/Neotopia_Drohnen_Fahrzeuge.md]].

**Preisformel (Excel, abgelöst durch das neue Nuyen-pro-Attribut-System):**

| Typ | Formel |
|---|---|
| Fahrzeug | Stufe×5.000¥ bis Stufe 5, ab 5×20.000¥, ab 10×40.000¥ |
| Drohne | Stufe×500¥ bis Stufe 5, ab 5×1.000¥, ab 10×5.000¥ |

Mark hatte diese Formel schon am 30.08.2026 selbst infrage gestellt (Motorrad
Stufe 3 = 15.000¥, kaum leistbar) — das war mit ein Auslöser für die
Neuentscheidung vom 25.10.2026.

## Offene Fragen (vor dem Bauen noch zu klären)

- **Punkte-Anzeige-Deckel:** Vorschlag 10 Kreise, dann nur Zahl — exakte
  Zahl noch offen.
- **Start-Faktoren für `AttributDrohne`:**
  Stufe×500¥/5.000¥-Tabelle angelehnt, oder komplett neu kalibrieren?
- **`nuyenProXp` = 200¥** ist ein bewusster Startwert zum Playtesten am
  Spieltisch, keine endgültige Zahl.

## Siehe auch

- [[../entities/neo4j-datenmodell]] — `BESITZT`/`BEGLEITET`-Kanten, Grund für
  die Person-Knoten-Entscheidung
- [[erfahrung-und-steigern]] — Faktor-Formel, die für Nuyen-Kosten wiederverwendet wird
- [[kampf-und-initiative]] — Initiative-Formel-Erweiterung
- [[cyberware-bioware]] — Vorbild für Qualitätsstufen-Preislogik (Chrom)
- [[ruestung-kaestchen-durchlass]] — Vorbild für die wiederverwendete Reparaturformel
- [[attribute-und-fertigkeiten]] — Grundwert-pro-Entität-Mechanismus (Critter-Feature)
- [[../../CLAUDE.md]]
