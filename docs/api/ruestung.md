# Rüstung: Kästchen + Schadensreduktion

Wie Rüstung Treffer abschwächt, sich dabei abnutzt und warum die Formel so
aussieht, wie sie aussieht. Das ist das am längsten diskutierte Regelstück im
Tool, mit einem kompletten Umbau nach dem ersten Praxistest am Spieltisch —
deshalb hier ausführlicher begründet als sonst üblich, inklusive der
Sackgassen und der einen Sache, die sich als grundlegend falsch herausstellte.
Code: `backend/app/kampf/ruestung.py` (reine Rechenfunktion, dort auch die
knappe Fassung als Docstring), `backend/tests/test_ruestung.py` (Beispiele
als Tests).

> **Historie:** 10.09.2026 erste Fassung mit einem Wert namens "Durchlass"
> (niedriger = besser — 0 heißt "hermetisch dicht"). 18.09.2026, nachdem Mark
> das System selbst am Spieltisch benutzt hatte: *"Durchlass ist ein dummer
> Wert, sorry... wir ersetzen ihn durch Schadensreduktion"*. Die Grundidee
> (Kästchen + zweiter Wert, Pool aus allen getragenen Teilen, Abstufung statt
> Blocken) blieb, aber der zweite Wert wurde komplett gedreht: **höher ist
> jetzt besser**, wie ein klassischer Soak-Wert. Dieses Dokument beschreibt
> nur noch die aktuelle Fassung; die Durchlass-Version ist Geschichte, siehe
> `docs/wiki/concepts/ruestung-kaestchen-durchlass.md` für die vollständige
> Entwicklung inkl. der alten Formel.

---

## Das Problem mit dem alten (flachen) System

Ursprünglich hatte Rüstung einen flachen `kraft`-Bonus (Regelblatt Zeile
66-67, 76): Waffenschaden + Nettoerfolge **gegen** die Rüstung gerechnet,
fertig. Der Bonus war konstant — eine Weste mit Rüstung 3 blieb Rüstung 3,
egal wie oft sie getroffen wurde. Mark wollte stattdessen, dass sich Rüstung
im Kampf **abnutzt**: sie hält etwas aus, wird dabei schlechter, und
irgendwann bringt sie nichts mehr. Das alte Feld (`kraft`, im Formular
"Rüstungsbonus") existiert weiterhin für Bestandsdaten und einfache Fälle,
wird von den Endpunkten hier unten aber nicht angefasst — ein Gegenstand mit
`ruestungKaestchenMax > 0` nutzt fachlich das neue System, alles andere den
alten flachen Bonus (siehe `frontend/src/kampf/Kampfkarte.tsx`, wo beide
nebeneinander angezeigt werden können).

## Die Grundidee: zwei Werte statt einem

**Kästchen** (`ruestungKaestchenMax` / `ruestungKaestchenAktuell`) — wie viel
Substanz die Rüstung hat, um Treffer zu schlucken, bevor sie reißt. Sinkt mit
Beschädigung, genau wie die Gesundheit einer Person.

**Reduktion** (`ruestungReduktionBasis`) — wie viel Schaden die Rüstung pro
Treffer direkt abfängt. **Höher ist besser**, ein klassischer Soak-Wert:

- Eine **Lederjacke** hat Reduktion 1 — sie ist von Haus aus dünn, hilft aber
  immerhin ein bisschen.
- Eine **Bombenschutzweste** hat Reduktion 6 — sie fängt im Neuzustand einen
  Großteil eines Treffers ab.

**Kein eigener "Aktuell"-Wert für die Reduktion mehr.** Das war beim
Durchlass-System noch nötig (dort stieg der Durchlass mit jedem Treffer) und
war zugleich die Quelle eines echten Bugs: beim nachträglichen Aktivieren
eines Gegenstands über das Bearbeiten-Formular (PATCH) zog der Aktuell-Wert
nicht automatisch mit, wodurch frisch angelegte Rüstung fälschlich als
"zerschossen" galt (Fix vom 18.09.2026 in `items/repository.py::
update_gegenstand`, kurz bevor die Reduktion selbst eingeführt wurde). Die
neue Fassung braucht diesen Fix für die Reduktion gar nicht mehr — die
tatsächlich wirksame Reduktion wird direkt aus dem **Kästchen-Verhältnis**
berechnet, es gibt nichts, was aus dem Tritt geraten könnte.

## Die gestufte Reduktion

Mark: *"könnte sich die Reduktion aufgrund halbieren, wenn die Kästchen
halbiert werden? und dann beim 4tel? somit bleibt eine Lederjacke mit 1
Absorption immer gleich, aber ein Bombenschutzanzug, der stark beschädigt
wird, wird schwächer"*.

```
reduktion_effektiv(Basis, Kästchen-Aktuell, Kästchen-Max):
  Anteil = Kästchen-Aktuell / Kästchen-Max
  > 50 %  → volle Reduktion (Basis)
  > 25 %  → halbe Reduktion (Basis // 2, abgerundet)
  > 0 %   → ein Viertel (Basis // 4, abgerundet)
  = 0     → keine Reduktion (Rüstung wirkt nicht mehr)
```

Das ist genau der gewünschte Effekt: eine Lederjacke mit Reduktion 1 merkt
die Stufen kaum (1 bleibt 1, fällt dann direkt auf 0 — `1 // 2 = 0`), während
eine Bombenschutzweste mit Reduktion 6 spürbar schwächer wird, sobald sie
unter 50 % ihrer Kästchen fällt (6 → 3 → 1).

## Die Rechenformel

Eingabe: Schadensart (`schlag` | `schwer` | `aggraviert` — am Tisch eher
"Schlag/Tödlich/Unheilbar" genannt, siehe Mapping unten) und Stärke (Anzahl
Schadenspunkte, das, was am Tisch als "3× Tödlich" angesagt wird).

| Tischsprache | Feldname im Code |
|---|---|
| Schlag | `schlag` |
| Tödlich | `schwer` |
| Unheilbar | `aggraviert` |

(Dieselben drei Begriffe wie überall sonst im Tool — `schadenSchlag`/
`schadenSchwer`/`schadenAggraviert` an der Person, `Kaestchen.tsx`s
`Schadensart`-Typ. Eine Übersetzung zwischen Regelblatt und Code reicht.)

**Schritt 1 — effektive Reduktion:**

```
reduktion = reduktion_effektiv(Reduktion-Basis, Kästchen-Aktuell, Kästchen-Max)
```

**Schritt 2 — was die Rüstung abfängt, und was durchkommt:**

```
absorbiert = min(Stärke, reduktion)
durchkommend = Stärke - absorbiert
```

**Schritt 3 — Schaden an die Trägerin.** Rüstung *blockt* nicht, sie
*dämpft*: eine Schadensart wird beim Durchdringen eine Stufe leichter.
Schlag ist schon die unterste Stufe — dort gibt es stattdessen eine
Halbierung, weil "eine Stufe leichter als Schlag" nichts mehr wäre:

| Eingehend | Kommt an als |
|---|---|
| Unheilbar | Tödlich, **gleiche Menge** |
| Tödlich | Schlag, **gleiche Menge** |
| Schlag | Schlag, **halbiert** (abgerundet) |

Menge in allen Fällen: `durchkommend` (nicht die volle Stärke — der
absorbierte Anteil wird von der Rüstung geschluckt und wirkt sich nur auf sie
selbst aus, siehe Schritt 4).

**Schritt 4 — Schaden an die Rüstung (Kästchen).** Hier unterscheiden sich
die drei Schadensarten am stärksten:

- **Unheilbar:** immer die volle Stärke, 1:1 — unabhängig von der Reduktion.
  Mark: *"das wäre ja was wie eine Explosion, da kann man froh sein das
  überstanden zu haben"*. Es gibt keine Verhandlung mit einer Bombe.
- **Tödlich:** eine Mischung, weil die Rüstung hier tatsächlich etwas
  leistet:
  ```
  Kästchenschaden = floor(absorbiert / 2) + durchkommend
  ```
  Der absorbierte Anteil beschädigt sie nur zur Hälfte (sie hat ihn ja
  immerhin abgefangen, ohne wirklich zu kämpfen), der durchkommende Anteil
  voll 1:1.
- **Schlag:** nur wenn der Treffer mindestens die Hälfte der *aktuellen*
  Kästchen erreicht — ein laues Klopfen soll wirkungslos abprallen:
  ```
  löst_aus = 2 × Stärke ≥ Kästchen-Aktuell
  Kästchenschaden = durchkommend / 2 (abgerundet), falls löst_aus, sonst 0
  ```
  **Bewusst `Kästchen-Aktuell`, nicht `Kästchen-Max`:** dadurch sinkt die
  Auslöse-Schwelle mit jedem Treffer — eine bereits ramponierte Rüstung
  bricht bei Schlagschaden leichter weiter zusammen.

**Sonderfall — 0 Kästchen:** Eine komplett zerstörte Rüstung wirkt gar nicht
mehr. Sie kann dann auch nichts mehr abstufen: der Treffer geht unverändert
und in voller Höhe durch (Mark: *"wirkt gar nicht mehr"*).

**Kein separater Schritt zum "Reduktion erhöhen" mehr** — anders als beim
alten Durchlass-System, wo der Durchlass-Aktuell-Wert nach jedem Treffer
stieg, braucht die neue Fassung das nicht: die effektive Reduktion sinkt
automatisch mit den Kästchen, weil sie direkt aus ihnen berechnet wird.

## Mehrere Rüstungsteile: ein Pool

Marks Vorgabe: *"ich hätte schon gerne dass alle Rüstungen zu einem Pool
addiert werden, ich will keine Körper Zonen, das ist zu kompliziert"*. Alles
Getragene wirkt deshalb als **eine** virtuelle Rüstung
(`kampf/ruestung.py::pool`):

- **Kästchen** = Summe aller getragenen Teile. Ein gemeinsamer Vorrat, wie
  eine zweite Gesundheitsleiste. Das ist auch die Zahl, gegen die der
  Schlag-Trigger prüft.
- **Reduktion** = die **beste** Basis-Reduktion unter den getragenen Teilen.
  Ausdrücklich *nicht* summiert und kein Mittelwert: die stärkste Schicht
  bestimmt die Basis. Die tatsächlich wirksame Reduktion des Pools wird dann
  aus dieser Basis **und dem Kästchen-Verhältnis des gesamten Pools**
  berechnet — der Pool wird schlechter, wenn seine Gesamtsubstanz sinkt,
  nicht nur wenn ausgerechnet das beste Einzelteil beschädigt wird.

`berechne_treffer` wird also mit den Poolwerten aufgerufen. Von seiner
Rückgabe gelten dann nur `hpArt`, `hpMenge` und `kaestchenSchaden`; das Feld
`kaestchenNeu` bezieht sich auf die virtuelle Gesamtrüstung und wird
verworfen. Was die einzelnen Teile abbekommen, rechnet
`verteile_kaestchenschaden`.

**Keine Körperzonen, kein Zielen.** Eine Verteilungsregel "welcher Anteil
geht auf Helm, welcher auf die Weste" gibt es bewusst nicht — sie bräuchte
Körperzonen für Rüstung (die es, anders als bei Cyberware, nicht gibt) und
war Mark ausdrücklich zu kompliziert. Die Treffer-Route nimmt deshalb nur
Art und Stärke, kein Ziel.

## Verbrauchsreihenfolge: die beste Reduktion zuerst

Aus der Durchlass-Fassung übernommen, nur mit gedrehter Sortierung (weil
"hoch=gut" jetzt gilt): der Kästchenschaden frisst sich absteigend nach
`ruestungReduktionBasis` durch die Teile, mit Überlauf ins nächste
(`kampf/ruestung.py::reihenfolge` + `verteile_kaestchenschaden`). Die beste
Schicht hält den Treffer auf und wird dabei verbraucht; ist sie hin,
übernimmt die nächstbeste.

Daraus ergibt sich von selbst die gewünschte Kurve: die gute Weste hält den
Schaden auf und wird dabei verbraucht; ist sie hin, fällt der Pool auf das
nächstbeste Teil zurück.

**Diese Reihenfolge schließt außerdem einen sonst offenen Missbrauch.** Ein
winziges Teil mit sehr hoher Reduktion würde dem Pool sonst dauerhaft seine
Stärke leihen, während eine schwache Jacke die Masse der Kästchen stellt.
Weil aber genau dieses Teil zuerst aufgebraucht wird, ist es nach wenigen
Treffern weg und der Pool fällt auf die Jacke zurück (Test:
`test_ruestung.py::TestSuspensoriumMissbrauch` — der Name ist aus der
Durchlass-Ära stehengeblieben, die Regel gilt unverändert).

**Bei gleicher Reduktion zuerst das kleinere Teil** (weniger Kästchen): so
wird es fertig aufgebraucht, statt dass mehrere Teile halb angeknackst
herumliegen. Danach die Kennung, damit die Reihenfolge bei völligem
Gleichstand reproduzierbar bleibt.

## Zerstörte Rüstung gilt nicht mehr als ausgerüstet

Fällt ein Teil auf 0 Kästchen, wird es **ins Mitgeführte zurückgelegt**
(`ablage = RUCKSACK`) und zählt damit nicht mehr zum Pool.

Ins Mitgeführte und nicht in den Mülleimer, weil sie reparierbar bleiben
soll — dasselbe Muster wie bei chirurgisch entferntem Chrom, das auch in den
Rucksack zurückwandert (`items/repository.py::setze_verbaut`).

> **Zum Namen:** `RUCKSACK` ist kein Rucksack, sondern der Zustand "am
> Körper, aber nicht griffbereit" — er setzt keinen Behälter voraus. Die
> Oberfläche nennt ihn **"Mitgeführt"**, und nur wenn tatsächlich ein
> Behälter getragen wird, heißt der Bereich nach ihm (siehe
> `items/aufbewahrung.ts::ermittleBereiche`).

**Wieder anlegen ist gesperrt**, solange die Kästchen bei 0 stehen:
`.../ablage` antwortet mit `409 Conflict` und *"Zerschossene Rüstung schützt
nicht — sie muss erst repariert werden"*. Ohne diese Sperre könnte man sie
endlos wieder anziehen und würde rätseln, warum der Rüstungsbalken nicht
steigt.

**Ohne wirksame Rüstung** (nichts angelegt, oder alles zerstört) trifft der
Schaden ungebremst und unverändert in seiner Art. Das ist kein Fehlerfall,
sondern erlaubt, dasselbe Popup auch für ungerüstete Charaktere zu benutzen.

## Reparatur

Mark: *"es muss dann auch eine Möglichkeit geben die Rüstung zu reparieren,
entweder mit dem Hardware Skill, oder bei einem Händler und es kostet
Geld"*.

Die reine Rechnung ist gebaut (`kampf/ruestung.py::repariere`,
`POST .../ruestung/reparieren`, nur SL): sie stellt eine angegebene Menge
Kästchen wieder her. **Seit dem Umbau auf Schadensreduktion braucht das
keinen zweiten Schritt mehr** — vorher musste die Reparatur auch den
Durchlass symmetrisch senken (Mark damals: *"Reparatur senkt auch die
Schwelle"*); jetzt folgt die Reduktion automatisch aus dem
wiederhergestellten Kästchen-Verhältnis.

**Was noch fehlt:** die Hardware-Skill-Probe und der Händler-Preis dahinter.
Der Endpunkt nimmt aktuell nur das *Ergebnis* entgegen (wie viele Kästchen),
die SL trägt es von Hand ein — genau wie Erfahrung vergeben. Eine echte Probe
bräuchte einen Fertigkeitswurf gegen eine Schwierigkeit (analog zum
Paralysewurf beim Reflex-Booster, `kampf/booster.py`), ein Preis pro Kästchen
bräuchte das noch nicht existierende Shop-System (siehe CLAUDE.md, Punkt 1).
Beides ist bewusst zurückgestellt, bis diese Systeme stehen.

## Endpunkte

### POST `/api/campaigns/{campaign_id}/personen/{person_id}/ruestung/treffer`

Ein erlittener Treffer. **An der Person, nicht am Gegenstand** — getroffen
wird eine Person, welche ihrer Rüstungsteile der Kästchenschaden aufbraucht,
entscheidet die Regel (siehe oben). Implementiert in `traits/routes.py`,
neben `zustand`.

**SL für alle, Spieler:innen nur für den eigenen Charakter** (404 bei fremden,
damit deren Existenz nicht bestätigt wird — wie bei `zustand`).

```json
// Request — mehr als Art und Stärke gibt es nicht anzugeben
{ "art": "schwer", "staerke": 10 }

// Response
{
  "hpArt": "schlag",
  "hpMenge": 4,
  "kaestchenSchaden": 7,
  "betroffen": [
    { "id": "…", "name": "Bombenschutzweste", "verlust": 7, "kaestchenNeu": 2, "zerstoert": false }
  ],
  "uebersicht": { "...": "aktualisierte Bogen-Übersicht der Person" }
}
```

Schreibt in einem Rutsch: Kästchen **jedes betroffenen** Rüstungsteils, die
Ablage zerstörter Teile (zurück ins Mitgeführte) UND den
`schadenSchlag`/`schadenSchwer`/`schadenAggraviert`-Zähler der Person — der
HP-Schaden wird **addiert**, nicht gesetzt.

`betroffen: []` heißt: keine wirksame Rüstung, der Schaden kam ungebremst
und unverändert an.

### POST `/api/campaigns/{campaign_id}/gegenstaende/{item_id}/ruestung/reparieren`

**Nur SL.** Bleibt am Gegenstand — reparieren betrifft immer ein bestimmtes
Stück. Siehe Abschnitt Reparatur oben.

```json
// Request
{ "kaestchen": 3 }
// Response: der aktualisierte Gegenstand
```

### GET `/api/campaigns/{campaign_id}/personen/{person_id}/bogen`

Der Charakterbogen liefert die Rüstung als **fertig gerechneten Pool** mit —
das Blatt zeigt sie als vierte Zustandsleiste (Gesundheit → Willenskraft →
Rüstung → I.C.E.):

```json
"ruestung": {
  "kaestchenAktuell": 7,
  "kaestchenMax": 8,
  "reduktionBasis": 4,
  "reduktionEffektiv": 4,
  "teile": [
    { "id": "…", "name": "Kevlarweste", "kaestchenAktuell": 2, "kaestchenMax": 3, "reduktion": 4 },
    { "id": "…", "name": "Lederjacke", "kaestchenAktuell": 5, "kaestchenMax": 5, "reduktion": 1 }
  ]
}
```

`teile` steht in Verbrauchsreihenfolge (beste Reduktion zuerst).
`reduktionBasis` ist der volle Wert bei intakter Rüstung, `reduktionEffektiv`
der aktuell wirksame (gestuft nach Kästchen-Anteil). Bewusst serverseitig
gerechnet (`kampf/ruestung.py::uebersicht`).

### GET `.../gegenstaende/{person_id}` (Feld an jedem Gegenstand)

Jede `GegenstandResponse` trägt drei Felder mit (0, wenn ungenutzt):
`ruestungKaestchenMax`, `ruestungKaestchenAktuell`, `ruestungReduktionBasis`.

## Datenmodell (Neo4j)

Keine neuen Knoten oder Beziehungen — drei zusätzliche Properties am
bestehenden `(:Gegenstand)`-Knoten, analog zu `kraft`:

```cypher
(:Gegenstand {
  typ: "Rüstung",
  ruestungKaestchenMax: 9,
  ruestungKaestchenAktuell: 6,
  ruestungReduktionBasis: 6
})
```

Beim Anlegen defaultet `Aktuell` auf `Max`, wenn nicht ausdrücklich etwas
anderes mitgegeben wird (ein frisches Stück ist unbeschädigt) — siehe
`items/repository.py::create_gegenstand`. Beim nachträglichen Aktivieren über
PATCH (Bearbeiten-Formular) zieht `update_gegenstand` denselben Nachzug
nach, sofern das Stück vorher `Max == 0` hatte.

## Durchgerechnete Beispiele

**Lederjacke** (5 Kästchen, Reduktion 1 — "schützt kaum, aber immerhin ein
bisschen"):

| Treffer | An die Trägerin | An die Jacke |
|---|---|---|
| Schlag 6 | 2 Schlag (5 durchkommend, halbiert) | 2 Kästchen → 3/5 |
| Tödlich 6 | 5 Schlag (abgestuft, nicht halbiert) | 5 → gedeckelt auf verbleibende Kästchen |

**Bombenschutzweste** (9 Kästchen, Reduktion 6 — im Neuzustand fängt sie
viel ab):

| Treffer | An die Trägerin | An die Weste |
|---|---|---|
| Schlag 6 (intakt) | 0 (absorbiert vollständig) | 0 — `2×6=12≥9` löst aus, aber `durchkommend=0` |
| Tödlich 10 (intakt) | 4 Schlag (10−6 durchkommend, abgestuft) | 7 Kästchen → 2/9 (3 halbe Reduktion + 4 voll) |
| Schlag 6 (bei 4/9 Kästchen, unter 50%) | 3 Schlag (Reduktion jetzt nur noch 3) | je nach Trigger |

Beide Tabellen als ausführbare Tests in `backend/tests/test_ruestung.py`.
