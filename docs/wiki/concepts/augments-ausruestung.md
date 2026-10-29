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

## Korrektur 3: Gesundheit/Außenhülle sichtbar, "Augments" in der Werkbank-UI zu "Upgraden" umbenannt, Typ-Bugfix (29.10.2026, Marks dritter Klicktest)

Drei Befunde vom ersten echten Durchklicken am Spieltisch:

1. **"Ich sehe bei der Reparatur nicht den Gesundheitszustand der
   Drohnen/Rüstungen"**: Die Reparatur-Kacheln für Drohnen/Fahrzeuge zeigten
   nur Name + Typ, keinen Schadenszustand — und das Reparatur-Popup selbst
   zeigte überhaupt keinen aktuellen Zustand (weder für Rüstung noch für
   Drohne/Fahrzeug). `GET /drohnen` liefert jetzt zusätzlich
   `gesundheitAktuell`/`gesundheitMax` (live wie am Charakterblatt) sowie
   `aussenhuelleAktuell`/`aussenhuelleMax` — die Außenhülle ist das
   `istNatuerlich`-Rüstungsteil der Drohne selbst (identischer Mechanismus
   wie Dug'Rahs natürliche Rüstung, siehe `anwende_natuerliche_ruestung`).
   `ReparaturZiel` trägt diese Werte jetzt mit, `ReparaturFenster` zeigt sie
   als Kopfzeile.
   - **Offen/ungelöst:** Eine Drohne kann bisher nicht rasten (ihr einziger
     Heilweg ist die Werkbank-Material-Reparatur, die nur Gesundheit
     heilt). Die Außenhülle wird dadurch sichtbar, aber NICHT repariert —
     und die normale Rüstungs-Reparatur schließt `istNatuerlich`-Teile
     bewusst aus (sie heilen bei Personen über Rast). Für Drohnen gibt es
     also aktuell **keinen Weg**, eine beschädigte Außenhülle wieder
     aufzufüllen. Entscheidung von Mark noch offen: Außenhülle in die
     bestehende Gesundheits-Material-Reparatur mit aufnehmen, oder einen
     eigenen Reparaturschritt dafür bauen?
2. **Benennung**: Mark, 29.10.2026: "das verbessern von Waffen ... heißt
   noch Augments, das muss bitte Upgraden heißen" — alle user-sichtbaren
   Texte im Werkbank-Augments-Reiter umbenannt (Tab-Button, Fenstertitel,
   Leer-/Fehlertexte, die Checkbox "Ist selbst ein Augment" am
   Gegenstands-Formular). Interne Namen (`istAugment`, `AugmentFenster.tsx`,
   `items/augments.py`, API-Routen) bleiben unverändert — reine
   Display-Umbenennung. Die KÖRPERKARTE (Cyberware-Implantate,
   `augments/AugmentsAnsicht.tsx`, Burgermenü "Augments" mit Symbol ⚕) ist
   ein eigenes, unverwandtes Feature und bleibt unverändert.
3. **Bugfix "Spieler sieht sein Upgrade-Material nicht"**: Mark hatte ein
   Zielfernrohr mit Typ "Upgrade-Material" angelegt, aber die separate
   Checkbox "Ist selbst ein Augment" nicht gesetzt — laut Datenmodell zwei
   unabhängige Felder (Typ ist nur die Kachel-Optik), in der Praxis aber
   genau die Verwechslung, die zum Typ "Upgrade-Material" erst geführt
   hatte. Jetzt erzwingen `create_item`/`update_item` serverseitig
   `istAugment=true`, sobald `typ == "Upgrade-Material"` ist — die Checkbox
   bleibt im Formular sichtbar (und für andere Typen weiter frei wählbar),
   wird für diesen einen Typ aber nicht mehr vergessen.

`pytest` (887 passed, 55 vorbestehende Fehlschläge unverändert — identisch
zur Baseline), `tsc -b`/`vite build` sauber, Live-Deploy auf bebop.

## Korrektur 4: Werkbank-Upgraden träger-zentriert statt Upgrade-zentriert (29.10.2026, Marks vierter Klicktest)

Mark: "ich will ja einen Gegenstand upgraden, also sollte ich die leichte
Pistole sehen, und dort die Slots was bereits in sie verbaut ist, und wenn
ich die Pistole anklicke sollte ich sehen was ich in sie verbauen kann." —
der bisherige Einstieg lief umgekehrt (erst das Upgrade-Material wählen,
dann ein Ziel dafür suchen), das fühlte sich falsch herum an.

**Frontend, keine Backend-Änderung nötig** (alle `/augment/...`-Routen
waren schon immer Upgrade-zentriert per `item_id`, das reicht für beide
Browse-Richtungen):

- `AugmentUebersicht(Spieler).tsx` listen jetzt **Träger** (Gegenstände mit
  `AUGMENT_TRAEGER_TYPEN` + `upgradeSlots > 0`, sowie Drohnen/Fahrzeuge mit
  `upgradeSlots > 0`) statt Upgrade-Gegenstände. Kachel zeigt
  `belegteSlots/upgradeSlots`. Eine kleine separate Liste "Defekt, ohne
  Träger" bleibt oben stehen — ein beim Montieren/Demontieren
  kaputtgegangenes, gerade unmontiertes Upgrade hat keinen Träger mehr, dem
  es zugeordnet werden könnte.
- Neu: `AugmentTraegerFenster.tsx` — Popup für EINEN Träger, zeigt die
  montierten Upgrades (Klick → bestehendes `AugmentFenster`,
  Demontieren/Reparieren unverändert) und die **passenden freien** eigenen
  Upgrades zum Einbauen (gefiltert über das neue
  `items/api.ts::waffentypPasst`, TS-Pendant zu
  `items/augments.py::waffentyp_passt`).
- `AugmentFenster.tsx` bekommt ein optionales `vorausgewaehltesZiel`-Prop:
  wird es von der Trägeransicht mit bereits feststehendem Ziel geöffnet,
  entfällt der alte "Ziel wählen"-Schritt komplett, es geht direkt zu
  Skill/Probe. Vom alten Einstieg (SL-Übersicht "Defekt, ohne Träger")
  weiterhin ohne Preset nutzbar, Ziel-Chooser erscheint dann wie bisher.
- `AugmentUebersichtSpieler.tsx` bekommt dafür ein geändertes Props-Schema:
  statt der vorgefilterten `items` (nur eigene Upgrades) jetzt `meine`
  (ALLE eigenen Gegenstände — Träger UND Upgrades gemeinsam, damit sich
  montierte/freie Upgrades pro Träger clientseitig ohne Zusatzabfrage
  ermitteln lassen) plus `meineDrohnen`. `WerkbankUebersichtSpieler.tsx`
  reicht beides durch.

`tsc -b`/`vite build` sauber, Live-Deploy auf bebop. Kein Backend-Test
betroffen (reiner Frontend-Umbau).

## Korrektur 5: Zweigeteilte Ansicht statt Popup pro Träger (29.10.2026, Mark direkt im Anschluss)

Mark: "können wir es vielleicht in der Mitte aufteilen, so dass man auf
einer Seite die Items und auf der anderen die Upgrade-Materialien sieht?"
— Korrektur 4 löste noch jeden Träger als eigenes Popup auf
(`AugmentTraegerFenster.tsx`), Mark wollte stattdessen beide Seiten
gleichzeitig sichtbar, ohne Klick-Umweg.

- `AugmentTraegerFenster.tsx` → `AugmentTraegerPanel.tsx` umbenannt: kein
  `Fenster`-Wrapper mehr, reine Inhaltskomponente (Prop `traeger: ... | null`
  — `null` zeigt den Hinweis "Links … wählen"). Montiert/Freie-Listen
  unverändert, Klick auf ein Upgrade öffnet weiterhin das modale
  `AugmentFenster` (Skill/Probe bleibt ein eigener Schritt, macht als
  Popup mehr Sinn als inline).
- `AugmentUebersicht(Spieler).tsx`: neues `wb-split`-Grid
  (`werkbank/werkbank.css`, gleiches Muster wie `haendler/shop.css::
  .ts-layout`) — links die Träger-Kacheln (Klick setzt nur noch
  `gewaehlterTraeger`-State, markiert sich selbst `data-aktiv`), rechts
  fest das `AugmentTraegerPanel` für den gewählten Träger.
- Kein Backend betroffen, `tsc -b`/`vite build` sauber, Live-Deploy auf
  bebop.

## Korrektur 6: Kachelhöhe fehlte (Text abgeschnitten) + Steckbrief auf der Upgrade-Kachel (29.10.2026)

Zwei Folgefehler direkt nach Korrektur 5, beide Mark beim Testen
aufgefallen:

1. **"Man kann leider den Namen des Upgrade-Materials nicht richtig
   lesen"**: Das `.gg-kachel`-Raster braucht die CSS-Variablen
   `--gg-kachel-breite`/`-hoehe`/`--gg-abstand` (`items/kachelraster.ts::
   KACHEL_STIL`) — ohne sie wird `grid-auto-rows`/`grid-template-columns`
   ungültig, die Kachel bekommt keine feste Höhe und der Text läuft über
   den sichtbaren Rand hinaus (`overflow: hidden` schneidet ab, statt zu
   wachsen). Andere Kachelraster im Tool (`DrohnenUebersicht.tsx`,
   `BegleiterVerwaltung.tsx` etc.) setzen `style={KACHEL_STIL}` IMMER auf
   das äußere `.gg-seite` — beim ursprünglichen Augments-Build am
   29.10.2026 wurde das übersehen. Jetzt an beiden Werkbank-Upgraden-
   Wurzeln (`AugmentUebersicht(Spieler).tsx`) ergänzt; die CSS-Variable
   vererbt sich an alle Kinder, auch ins rechts eingebettete
   `AugmentTraegerPanel`, ohne dass dieses selbst etwas setzen muss.
   **Merke:** jedes neue `.gg-raster` braucht `style={KACHEL_STIL}` am
   nächsten `.gg-seite`-Vorfahren, sonst droht genau dieser Bug.
2. **"Es wäre gut wenn das Material einen Steckbrief hätte, also man
   sieht was es tut"**: `items/steckbrief.ts::steckbriefKurz` las
   `traitBoni` schon immer generisch (unabhängig vom Typ) — fehlte nur die
   Anzeige. Jetzt zeigt jede Upgrade-Kachel (`AugmentTraegerPanel.tsx`,
   plus die "Defekt, ohne Träger"-Liste in beiden Übersichten) zusätzlich
   `<span className="gg-kachel-steckbrief">`, dieselbe Zeile wie bei jeder
   anderen Gegenstands-Kachel im Tool (`GegenstandKachel.tsx`-Vorbild).

`tsc -b`/`vite build` sauber, Live-Deploy auf bebop. Kein Backend
betroffen.

## Materia-Fertigkeiten: Upgrade-Material-Skills steigerbar (29.10.2026)

Marks Idee, wörtlich: "wir könnten bei gewissen Skills die Möglichkeit
ergänzen sie zu leveln, so daß wir ein Material z.B. die Fähigkeit bzw. den
Zauber 'Blitz' geben, der dann das Lvl Skill Level 1 hat, ich würde dem
Spieler gerne die Möglichkeit geben XP in diesen Skill zu stecken und ihn
hoch zu leveln, ebenfalls bis auf Stufe 6, das Besondere wäre das die XP
dann auf den Gegenstand übertragen werden... auch für z.B. Endbosse die man
dann looten kann, und man dann sein Upgrade-Material auf dem Level bekommt
das er hatte" — offen aus FF7 geklaut, wie er selbst sagt.

Eine `ausruestungsfertigkeiten`-Fertigkeit (NEUE Fertigkeit NUR durch einen
Gegenstand) lässt sich jetzt per Häkchen als **Materia** markieren
(`materiaFertigkeiten: dict[str, bool]`). Markierte Fertigkeiten erscheinen
im normalen EP-Sheet neben den Skills (Mark: "am besten einfach im
XP-Steigerungssheet mit angezeigt… ich habe vor dass das grundsätzlich nur
Skills sind") und kosten exakt wie eine normale Fertigkeit. Die Stufe steht
NICHT auf der Person, sondern bleibt im `ausruestungsfertigkeiten`-Dict des
Gegenstands — wandert der Gegenstand per Besitzerwechsel weiter (Loot vom
Endboss), kommt die hochgelevelte Stufe automatisch mit, ganz ohne
Sondercode. Technischer Clou: ein synthetischer `traitDefId`
(`"materia::<gegenstandId>::<name>"`, `traits/erfahrung.py::
materia_schluessel`/`materia_entschluesseln`), den das bestehende generische
Steigern-Popup (`frontend/src/traits/LevelUp.tsx`) für einen ganz normalen
Skill hält — dadurch **keine einzige Codeänderung** an diesem Popup nötig.
Details: `items/repository.py::materia_fertigkeiten_liste`/
`steigere_materia_fertigkeit`, `traits/routes.py::_materia_preise` + Zweig
in `steigere_wert`. Verifiziert über 7 reine Funktionstests
(`test_materia.py`), volle Backend-Suite ohne Regression, `tsc -b` sauber,
Live-Deploy auf bebop. Kein Klicktest am Spieltisch.

### Ideen für später: Materia kombinieren (Crisis Core)

Mark, direkt im Anschluss, noch unentschieden: "ich überlege ob ich die
Funktion von Crisis Core noch irgendwie implementieren kann, dass man die
aufgelevelten Materialien noch kombinieren kann." Gemeint ist das
Crisis-Core-Feature, zwei gleich hochgelevelte Materia zu einer stärkeren
zu verschmelzen. **Bewusst noch nicht spezifiziert** — weder Datenmodell
noch Regel stehen fest (was genau kombiniert werden darf, was dabei
entsteht, ob es ein Materia-Level-6-Cap sprengt). Erst mit Mark das
Datenmodell besprechen, bevor hier irgendetwas gebaut wird.

### Ideen für später: Beschwörungs-Materia (Critter beschwören)

Mark, 29.10.2026, neue Idee direkt im Anschluss ans Materia-Feature:

> "Wir könnten Beschwörungen-Materias machen, hinter denen gewisse Critter
> stecken, die man im Kampf beschwören kann. Der Beschwörer bekommt den
> Critter dann wie eine Drohne angezeigt und kann ihn steuern. Das Level der
> Beschwörung (wieder 1-6) gibt an, wie viele Runden der Critter am Kampf
> teilnimmt — wir nehmen die Logik von den Zusatzrunden, er muss dann gleich
> die Initiative eingeben. Was neu wäre: der Critter heilt jedes Mal mit,
> wenn die Gruppe rastet, also wie ein spezielles Pet."

**Bewusst noch nicht spezifiziert, Datenmodell erst morgen besprechen.**
Vorläufige Einordnung für den Einstieg in die Diskussion:

- Eine neue Art Materia (eigenes `materiaFertigkeiten`-Flag? eigener Typ?),
  die statt einer Fertigkeits-Stufe einen **Critter-Link** trägt — Critter
  sind seit 20.09.2026 echte `Person`-Knoten (`istCritter=true`, siehe
  `entities/schemas.py`), kein eigener Begleiter-Typ mehr. Offene Frage: ist
  die Beschwörung ein TEMPLATE-Critter (eine Vorlage, die bei jeder
  Beschwörung frisch instanziiert wird) oder immer derselbe, fest gebundene
  Critter-Knoten?
- "Wird wie eine Drohne angezeigt und steuerbar" — vermutlich dasselbe
  Rigger/Drohne-Muster wie bei `drohne_rigger`/Hot (`kampf/hot.py`,
  `entities/repository.py::drohne_rigger`): der Beschwörer bekommt dieselbe
  Steuer-Sicht wie ein Rigger auf seine Drohne, nur für den beschworenen
  Critter.
- "Level 1-6 = wie viele Runden der Critter teilnimmt, Logik von den
  Zusatzrunden" — unklar, ob Mark damit die Hot-Ampel-Rundenlogik
  (`kampf/booster.py::AMPEL_MAX`/`ampel_nach_nutzung`) meint oder einfach
  das Zählmuster von `zusatzaktionen` (Sentinel -1 = "jede Runde", siehe
  `items/augments.py::kombiniere_zusatzaktionen`) — morgen konkret
  nachfragen, welche der beiden Mark meint.
- "Er muss dann gleich die Initiative eingeben" — analog zum
  Reflex-Booster-Zusatzzug (`kampf/repository.py`: zweiter Initiative-
  Eintrag derselben Person), nur für den neu erschienenen Critter statt für
  eine Zusatzaktion derselben Person.
- "Heilt mit, wenn die Gruppe rastet, wie ein spezielles Pet" — neu
  gegenüber der normalen Rast-Mechanik (`traits/rast.py`): bisher rasten nur
  tatsächlich anwesende `Person`-Knoten, die explizit ausgewählt werden
  (`RastInput.personIds`). Ein beschworener Critter müsste entweder
  automatisch mitgewählt werden, sobald sein Beschwörer rastet, oder einen
  eigenen Rast-Pfad bekommen.

**Beschwörungs-Probe — ENTSCHIEDEN (30.10.2026):** Mark: "das ist ja wie
Magie... also muss er Intelligenz + den Wert der Beschwörung würfeln."
Benötigte Erfolge = **Beschwörungswert ÷ 2, aufgerundet** (Stufe 1→1, 2→1,
3→2, 4→2, 5→3, 6→3) — Variante "Wert − 2, Minimum 1" (dieselbe Formel-Form
wie `kampf/ruestung.py::reparatur_benoetigte_erfolge`) wurde bewusst
verworfen: die Erfolgsschwelle muss mit dem Pool mitwachsen, sonst sind
Stufe 1-3 alle gleich trivial, obwohl der Critter bei Stufe 3 schon dreimal
so lange mitkämpft.
**Plus Schwierigkeitsgrad:** die SL legt beim **Anlegen** der Beschwörungs-
Materia (nicht pro Wurf) einen festen Aufschlag von **+0/+1/+2** auf die
benötigten Erfolge fest, damit besonders starke Beschwörungen nicht
automatisch so leicht sind wie schwache. Noch offen: ob der Aufschlag ein
neues Zahlenfeld am Gegenstand wird (z.B. `beschwoerungsSchwierigkeit: int`)
oder anders modelliert wird — Datenmodell dafür noch nicht gebaut.

## Korrektur 7: Diagnose aus Korrektur 6 war falsch — richtiger Fix mit Flex-Wrap statt Grid (29.10.2026)

Mark direkt nach Korrektur 6: **"ist jetzt sogar noch schlimmer... ich
kann jetzt garnichts mehr lesen"** — der `KACHEL_STIL`-Fix hat die Karten
nicht repariert, sondern komplett leergeräumt (nur noch das Icon sichtbar,
Name/Zeile/Steckbrief vollständig weg, nicht mal mehr abgeschnitten).

**Die Diagnose aus Korrektur 6 ("`.gg-raster` braucht `KACHEL_STIL` am
`.gg-seite`-Vorfahren, sonst bleibt die Zeilenhöhe ungültig") war falsch.**
Das `.gg-raster`/`KACHEL_STIL`-System ist für das globale "nie
scrollen"-Leitprinzip gebaut: eine Seite misst ihre volle, garantiert
definite Höhe aus einer lückenlosen Kette aus `flex:1; min-height:0` vom
App-Grundgerüst bis zur Kachel herab, und `grid-auto-rows: 168px` verlangt
genau diese definite Höhe, um sich korrekt zu strecken. Die
Werkbank-Upgraden-Ansicht ist aber *keine* solche Seite — sie splittet
sich in zwei unabhängig scrollende Spalten (`.wb-split` → zwei
`.wb-spalte` mit `overflow-y: auto`, zusätzlich verschachtelt mit einem
weiteren `.gg-seite` für `AugmentTraegerPanel`). Diese Mischung aus
Scroll-Container und gemessenem Grid bricht die Höhen-Kette irgendwo in
der Mitte (welche Zwischenebene genau, bleibt unklar — mehrere
verschachtelte `flex:1`-Ebenen ohne definite Außenhöhe). Ohne
`KACHEL_STIL` fiel `grid-auto-rows` auf `auto` zurück und die Karte nahm
ihre natürliche (kleine) Content-Höhe an — dadurch nur leicht
abgeschnitten durch `.gg-raster`s eigenes `overflow: hidden`. Mit
`KACHEL_STIL` forderte jede Karte plötzlich 168px an, aber der tatsächlich
zugeteilte Platz blieb genauso klein wie vorher — das Overflow-Fenster
zeigte dann nur noch zufällig den Bereich, in dem das (jetzt mittig in
einer großen, unsichtbaren Box zentrierte) Icon lag, der Text lag
komplett außerhalb.

**Richtiger Fix:** kein `.gg-raster`/`KACHEL_STIL` mehr in der Werkbank-
Upgraden-Ansicht. Neue, einfache Klasse `.wb-kachelraster`
(`werkbank.css`) — `display: flex; flex-wrap: wrap;` ohne jede
Höhenmessung, Kacheln bekommen darin eine FESTE `width`/`height` (148×168px)
direkt per CSS statt per Grid-Variable. Ein Flex-Wrap-Raster kann nie
kleiner werden als seine Kacheln und hat kein `overflow: hidden`, das
etwas abschneiden könnte — `.wb-spalte`s eigenes `overflow-y: auto`
übernimmt das Scrollen, falls der Inhalt den sichtbaren Bereich sprengt.
Betroffen: `AugmentUebersicht(Spieler).tsx`, `AugmentTraegerPanel.tsx`
(alle `gg-raster` → `wb-kachelraster`), `KACHEL_STIL`-Imports entfernt.

**Merke für zukünftige Instanzen:** das `.gg-raster`/`KACHEL_STIL`-System
NUR in Ansichten verwenden, die als alleiniger Seiteninhalt direkt unter
dem App-Grundgerüst hängen (ein `.gg-seite` pro Burgermenü-Eintrag, siehe
`DrohnenUebersicht.tsx` als Vorbild). Sobald eine Ansicht selbst scrollen
soll (`overflow-y: auto` irgendwo in der Kette) oder mehrere `.gg-seite`
ineinander verschachtelt sind, lieber ein eigenes, einfaches
Flex-Wrap-Raster mit fester Kachelgröße bauen statt das Grid-Messsystem zu
erzwingen — die Fehlerbilder dabei (abgeschnittener Text, leere Karten)
sehen täuschend nach "fehlende CSS-Variable" aus, sind aber tatsächlich
ein strukturelles Scroll-vs-Messung-Problem.

**Außerdem (Mark, gleiche Nachricht): "frage ich mich ob ich von außen
sehen werde welche Upgrades in der Waffe verbaut sind"** — vorher nein,
montierte Upgrades waren nur in der Werkbank sichtbar. Jetzt zeigt
`GegenstandKachel.tsx` optional `montierteUpgrades?: string[]` als
zusätzliche `gg-marke`-Badges ("🔩 Zielfernrohr"); `PCInventar.tsx`
übergibt das, aus der eigenen Gegenstandsliste berechnet
(`items.filter(i => i.montiertAnId === g.id)`). Andere Aufrufer von
`GegenstandKachel` (SL-Ansicht, NPC-Inventar) bekommen die Badges noch
nicht — Prop ist optional, kein Zwang, das überall nachzuziehen, aber bei
Bedarf einfach dieselbe Berechnung übernehmen.

`tsc -b`/`vite build` sauber, Live-Deploy auf bebop. Kein Backend
betroffen.
