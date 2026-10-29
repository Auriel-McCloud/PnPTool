---
title: Waffen-/Rüstungs-/Drohnen-Augments (Werkbank)
created: 2026-10-29
updated: 2026-10-29
type: konzept
---

# Waffen-/Rüstungs-/Drohnen-Augments (Werkbank)

Zweiter Baustein des Burgermenüs **Werkbank** (erster Baustein:
[[concepts/drohnen-fahrzeuge#Reparatur]]). Mark, 29.10.2026: "was ist wenn
wir das Menü nicht nur Reparatur, sondern einfach Werkbank nennen, und
Reparieren nur eine Option ist". Dieses Dokument beschreibt den zweiten
Reiter: **Augments** — montierbare Verbesserungen für Waffe, Rüstung,
Cyberdeck, Riggerkonsole UND Drohne/Fahrzeug.

## Idee

Ein Verbrauchsgegenstand wie ein "Zielfernrohr" lässt sich an einer Waffe
montieren und gibt einen Bonus (z. B. +1 auf Schusswaffen) — im Kern
Chrom/Cyberware, nur für Ausrüstung statt für den Körper. Ersetzt den alten,
nie gebauten Plan vom 28.10.2026 für ein eigenes Körperzonen-Schema bei
Drohnen-Augments komplett: Waffen, Rüstung, Cyberdeck, Riggerkonsole UND
Drohne/Fahrzeug tragen stattdessen alle nur ein `upgradeSlots`-Feld
(0–6, SL legt es pro Stück individuell fest — Mark: "ich würde das gerne
variabel halten").

Mark (29.10.2026, zweite Idee im selben Chat): "nimm Riggerkonsolen und
Decks bitte mit" — Augments sind also nicht auf Waffen/Rüstung beschränkt,
sondern auf **jeden Gegenstand**, bei dem ein Upgrade-Slot inhaltlich Sinn
ergibt.

## Datenmodell

Neue Felder am Gegenstand (`items/schemas.py`, `items/augments.py`):

| Feld | Bedeutung |
|---|---|
| `upgradeSlots` (int, 0–6) | Wie viele Augments hier hineinpassen. Nur bei `AUGMENT_TRAEGER_TYPEN = {"Waffe", "Rüstung", "Cyberdeck", "Riggerkonsole"}` im Bearbeiten-Formular sichtbar. |
| `istAugment` (bool) | Dieser Gegenstand IST ein Augment. |
| `traitBoni` | Wiederverwendet — **kein neues Bonus-Feld**. Mark: "genau wie traitBoni heute". Der Bonus eines Augments steckt in seinem eigenen `traitBoni`-Dict. |
| `augmentWaffentyp` | `""` (passt auf alles: jede Waffe, Rüstung, Cyberdeck, Riggerkonsole, Drohne/Fahrzeug) oder `Schusswaffen`/`Nahkampf`/`Handgemenge` (nur Waffen dieses Typs). |
| `defekt` (bool) | Ein Patzer beim Montieren/Demontieren hat das Augment beschädigt — der Bonus zählt nicht, bis es repariert ist. |
| `montiertAnId`/`Name`/`Kind` | Response-only (wie `ablageZielId`), Montage-Kante `:MONTIERT_AN`. |

Drohne/Fahrzeug (Person-Knoten) bekommen ebenfalls `upgradeSlots`
(`entities/schemas.py`), da sie keine Gegenstand-Knoten sind. Die
Montage-Kante `(:Gegenstand)-[:MONTIERT_AN]->(z)` zeigt deshalb auf einen
Knoten **beliebigen Typs** (kein Label im Cypher-Pattern) — selbe Idee wie
`:LIEGT_IN`, nur zusätzlich auf Person erweitert.

**Wichtig — bewusst nicht gebaut:** `traitBoni` fliesst aktuell (Stand
29.10.2026) im ganzen Tool noch in KEINE Würfelpool-Berechnung ein, auch
nicht bei normalen Waffen-Boni. Das Augment-Bonus-Feld ist also konsistent
mit dem Rest des Systems, aber genau wie dort bisher reine Datenhaltung —
die tatsächliche Pool-Anwendung müsste an derselben Stelle nachgezogen
werden wie bei jedem anderen `traitBoni`.

## Montieren / Demontieren

Mark, 29.10.2026 wörtlich: "es geht jederzeit, benötigt einen Maker oder
Handwerk Wurf der 1+Level des Gegenstandes ist."

- **Level** eines Augments = Summe seiner `traitBoni`-Werte
  (`items/augments.py::augment_level`).
- **Benötigte Erfolge** = Level + 1, für Montieren UND Demontieren gleich
  (`benoetigte_erfolge_montage`).
- Skill **frei wählbar**: Maker (Hardware) ODER Handwerk (anders als bei
  der Haupt-Reparatur, die je Zieltyp fest zugeordnet ist).
- Attribut-Partner **frei wählbar** — Mark: "machen wir's wieder frei
  wählbar", gleiche Linie wie bei der Reparatur.
- **Kein Chirurgie-Risiko** wie bei Personen-Cyberware — jederzeit möglich.
- **Patzer** beim Montieren ODER Demontieren beschädigt das Augment
  (`defekt=true`) statt die Aktion nur scheitern zu lassen:
  - Patzer beim Montieren: Montage schlägt fehl, Augment bleibt unmontiert
    UND defekt.
  - Patzer beim Demontieren: Demontage schlägt fehl, Augment bleibt
    montiert UND wird defekt (Annahme des Assistenten, von Mark nicht
    widersprochen — am Spieltisch anpassbar).

## Reparatur eines defekten Augments

Mark, 29.10.2026 wörtlich: "es braucht so viele minderwertige Materialien
wie sein Level ist zum reparieren, (normale Materialien zählen wieder für
5 minderwertige, und ein hochwertiges repariert es vollständig) und die
Probe ist Level des Gegenstandes -1 zum reparieren."

Wiederverwendet exakt dieselben Funktionen wie die Haupt-Werkbank-Reparatur
(`kampf/ruestung.py::reparatur_benoetigte_erfolge`/
`reparatur_heilung_material`), nur mit **Level statt Materialmenge bzw.
fehlenden Kästchen** als Eingabe:

- Benötigte Erfolge = Level − 1 (Minimum 1).
- Heilung: 1 hochwertiges Stück repariert immer vollständig, 1 normales
  Stück deckt 5 "Einheiten", 1 minderwertiges Stück deckt 1 Einheit.
- Ein Augment ist erst wieder einsatzbereit (`defekt=false`), wenn die
  Heilung ≥ Level ist — Teilreparatur in einem Versuch bleibt wirkungslos,
  bis genug Material in EINEM Versuch eingesetzt wird (keine
  Fortschritts-Speicherung über mehrere Versuche).

## Drohnen/Fahrzeuge im selben System

Mark, 29.10.2026: "wir wollten das ja auch mit Drohnen machen, aber
Drohnen sind keine richtigen Objekte, oder? können wir Drohnen auch gleich
in dieses System mit rein nehmen?" — Antwort: ja, über dieselbe
`:MONTIERT_AN`-Kante (Ziel kann Gegenstand ODER Person sein). Ersetzt den
alten, nie umgesetzten Plan vom 28.10.2026 für ein separates
Körperzonen-Schema (Chassis/Sensorik/Antrieb) komplett.

## Backend

- `items/augments.py` — reine Formeln: `augment_level`,
  `benoetigte_erfolge_montage`, `waffentyp_passt`, Konstante
  `AUGMENT_TRAEGER_TYPEN`.
- `items/repository.py` — `MONTIERT_AN`-Pattern fest in `LIEGT_IN`
  eingebaut (immer beide OPTIONAL MATCHes zusammen, damit nicht an jeder
  der ~20 Fundstellen einzeln ergänzt werden musste), neue Funktionen
  `ziel_fuer_augment`, `belegte_slots`, `montiere_augment`,
  `demontiere_augment`, `list_montierbare_ziele`, `list_augmente_von`.
- `items/routes.py` — Routen unter `/{item_id}/augment/...`:
  `montage-pool` (GET), `ziele` (GET, nur Gegenstand-Ziele — Drohnen/
  Fahrzeuge laufen frontendseitig über `drohnenApi.liste`),
  `montieren`/`demontieren` (POST, GM-only), `reparatur-pool` (GET),
  `reparieren-material` (POST, GM-only), `material` (GET).
- `entities/schemas.py`/`repository.py` — `upgradeSlots` an Person
  (`PERSON_FIELDS`, `_BOGEN_DEFAULTS`), `list_drohnen`-Query erweitert.

## Frontend

- `items/api.ts` — neue Gegenstand-Felder, `AugmentMontagePool`/
  `AugmentZiel`/`AugmentAktionsErgebnis`/`AugmentReparaturPool`/
  `AugmentReparaturErgebnis`, `itemsApi.augment*`-Funktionen,
  `AUGMENT_TRAEGER_TYPEN`-Set.
- `traits/CharacterSheetPanel.tsx` — Upgrade-Slots-Feld (nur bei
  passendem Typ) + "Ist selbst ein Augment"-Checkbox + Waffentyp-Dropdown.
- `werkbank/WerkbankUebersicht.tsx` (NEU) — ersetzt
  `reparatur/ReparaturUebersicht.tsx` als Burgermenü-Einstieg, zwei Reiter.
- `werkbank/AugmentUebersicht.tsx` (NEU) — Liste aller Augments (defekt/
  frei/montiert), Klick öffnet `AugmentFenster`.
- `werkbank/AugmentFenster.tsx` (NEU) — Montieren/Demontieren/Reparieren
  je nach Zustand, 3-Buttons-Muster wie die Haupt-Reparatur.

Bereich-Id in `App.tsx` bewusst `"reparatur"` **unverändert gelassen**
(nur Name/Komponente getauscht), damit ein eventuell schon gespeichertes
Menü-Layout (`MenueAnpassen`) nicht verwaist.

## Noch offen

- `pytest`/`tsc -b` grün, **kein Klicktest** (wie beim Reparatur-Feature
  schon immer gehandhabt — Mark testet am Spieltisch).
- Kein UI, um `upgradeSlots` an einer Drohne/einem Fahrzeug selbst zu
  setzen (Backend-Feld + generisches `entitiesApi.updatePerson` sind da,
  aber keine eigene Eingabe in der Drohnen-Detailansicht — bisher nur über
  die API direkt setzbar).
- `traitBoni`-Wirkung auf echte Würfelpools fehlt systemweit, siehe oben.

## Nachbesserung (29.10.2026, Marks erster Klicktest)

- **Eigener Typ "Upgrade-Material"** (`items/typKatalog.ts`, Symbol 🔩) —
  Mark: "ich wäre mehr für den Typ Upgrade Material das klingt
  sprechende". Reiner Frontend-Katalogeintrag, `typ` ist im Backend ein
  freies `str`-Feld, keine Migration nötig. Ersetzt NICHT das
  `istAugment`-Flag (das bleibt Pflicht, damit es in der Werkbank als
  Augment erscheint) — der Typ ist nur die sprechendere Kachel beim
  Anlegen, analog zu "Werkzeug"/"Verbrauchsgegenstand" davor.
- **Bugfix Sichtbarkeit:** Das Upgrade-Slots-Feld sass hinter dem
  eingeklappten "Optionen anzeigen"-Schalter und war damit faktisch
  unauffindbar — Mark: "ich finde weder in Waffen noch in Rüstungen die
  Möglichkeit unter der Seltenheit einzustellen". Jetzt direkt neben dem
  Seltenheit-Feld platziert (immer sichtbar für `AUGMENT_TRAEGER_TYPEN`,
  keine Optionen-Klapp-Notwendigkeit mehr). Die "Ist selbst ein
  Augment"-Checkbox + Waffentyp-Dropdown bleiben in den Optionen (weniger
  zeitkritisch).

## Korrektur: Self-Service statt GM-only (29.10.2026, Marks zweiter Klicktest)

Mark meldete, dass Spieler die Werkbank gar nicht sehen — **by design**
(alle Augment-Routen waren `require_campaign_gm`), aber **falsch gedacht**:
Mark: "natürlich war das für die Spieler gedacht, deswegen haben wir ja
bestimmt was sie würfeln müssen, damit das für sie dann auch angezeigt
wird, und ihre Materialien verwendet werden." Die Self-Report-Probe-Mechanik
(Spieler würfelt am Tisch, Tool nimmt Ergebnis entgegen) ergibt nur Sinn,
wenn Spieler die Aktion auch selbst auslösen — sonst bräuchte es keinen
Probe-Pool, der GM könnte das Ergebnis genauso gut direkt eintragen.

**Backend:** `montieren`/`demontieren`/`reparieren-material` verlieren
`require_campaign_gm`, bekommen stattdessen dieselbe Besitzprüfung wie
`ablage_aendern`/`besitzer_wechseln` (`_augment_oder_404` prüft jetzt via
`_eigener_kreis`: eigene Person ODER eigene gebundene Drohne/eigenes
Fahrzeug, GM immer). Zusätzlich geprüft: das **Ziel** beim Montieren
(Gegenstand-Besitzer ODER Drohne/Fahrzeug muss im selben Besitzkreis
sein) und das **Material** bei der Reparatur — sonst könnte ein Spieler
sein Augment an fremde Ausrüstung montieren oder mit fremdem Material
reparieren. `tests/test_zugriffsschutz.py::OHNE_GM_ERLAUBT` um die drei
Routen ergänzt.

**Frontend:** Neue Spieler-Bereich "Werkbank" (`players/SpielerAnsicht.tsx`)
— nur der Augments-Teil, kein Reparatur-Reiter (für Rüstung/Drohne/
Fahrzeug-Reparatur gibt es bis heute KEINE Spieler-UI, unabhängig von
diesem Feature). Neue `werkbank/AugmentUebersichtSpieler.tsx` zeigt nur
eigene Augments (eigene Person + eigene gebundene Drohnen/Fahrzeuge),
reutiliert das bestehende `AugmentFenster.tsx` unverändert. `AugmentFenster`
bekam dafür `augment: GegenstandMitBesitzer` (statt `Gegenstand`) und
filtert die Drohnen-Ziel-Liste jetzt auf denselben Rigger wie der
Augment-Besitzer — sowohl in der SL- als auch der Spieler-Ansicht, bisher
wurden dort ausnahmslos ALLE Drohnen der Kampagne angeboten.

`pytest` (887 passed, 55 vorbestehende Fehlschläge unverändert), `tsc -b`
sauber, kein Klicktest.

## Korrektur 2: Rüstungs-Reparatur ebenfalls Self-Service, Spieler-Werkbank bekommt Reparatur-Reiter (29.10.2026)

Mark bestätigte explizit: "ja bitte unbedingt! das war alles für die
Spieler gedacht!" — die Korrektur oben deckte nur Augments ab, aber
`ruestung/reparieren-material` (Selbst-Reparieren mit Maschinenteil +
Probe) war ebenfalls `require_campaign_gm`, obwohl das Drohnen-/
Fahrzeug-Pendant (`entities/routes.py::drohne_reparieren_material`) schon
immer Self-Service war — eine Inkonsistenz aus der ursprünglichen
Reparatur-Implementierung, nicht aus den Augments.

**Backend:** `ruestung_reparieren_material` verliert `require_campaign_gm`,
bekommt dieselbe `_eigener_kreis`-Prüfung wie die Augment-Routen. Der
Händler-Weg (`ruestung/reparatur-preis` + `POST /verhandlungen`) bleibt
bewusst SL-only — das ist kein Versehen, sondern das grundsätzliche
Verhandlungs-Modell dieses Tools ("SL macht ein Angebot, Spieler
antwortet", `verhandlung/routes.py::anbieten` ist überall
`require_campaign_gm`, nicht nur hier). Die manuelle Kästchen-Eintragung
ohne Probe (`ruestung/reparieren`) bleibt ebenfalls SL-only — das ist der
Sonderfall-Weg für Questbelohnungen/Improvisation, kein Self-Service-Pfad.
`tests/test_zugriffsschutz.py::OHNE_GM_ERLAUBT` entsprechend ergänzt.

**Frontend:** `reparatur/ReparaturFenster.tsx` bekommt ein optionales
`erlaubeHaendler`-Prop (Default `true`, blendet bei `false` den
Händler-Reiter komplett aus — SL-Ansicht bleibt unverändert). Neue
`werkbank/ReparaturUebersichtSpieler.tsx` (eigene Rüstung + eigene
Drohnen/Fahrzeuge, kein Händler-Weg) und `werkbank/
WerkbankUebersichtSpieler.tsx` (Wrapper mit zwei Reitern Reparatur/
Augments, ersetzt die direkte `AugmentUebersichtSpieler`-Einbindung von
Korrektur 1). Eigener, unabhängiger Drohnen-Fetch in
`WerkbankUebersichtSpieler` statt der fragilen `eigeneDrohnenIds` aus
`SpielerAnsicht.tsx` (die nur gefüllt ist, wenn der Kampf-Reiter schon
mal offen war).

`pytest` (887 passed, 55 vorbestehende Fehlschläge unverändert), `tsc -b`
sauber, kein Klicktest.
