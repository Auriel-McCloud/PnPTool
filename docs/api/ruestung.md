# Rüstung: Kästchen + Durchlass

Wie Rüstung Treffer abschwächt, sich dabei abnutzt und warum die Formel so
aussieht, wie sie aussieht. Das ist das jüngste und mit Abstand am längsten
diskutierte Regelstück im Tool (Gespräch Mark/Claude, 10.09.2026) — deshalb
hier ausführlicher begründet als sonst üblich, inklusive der Sackgassen, die
unterwegs korrigiert wurden. Code: `backend/app/kampf/ruestung.py` (reine
Rechenfunktion, dort auch die knappe Fassung als Docstring),
`backend/tests/test_ruestung.py` (Beispiele als Tests).

---

## Das Problem mit dem alten System

Vorher hatte Rüstung einen flachen `kraft`-Bonus (Regelblatt Zeile 66-67, 76):
Waffenschaden + Nettoerfolge **gegen** die Rüstung gerechnet, fertig. Der
Bonus war konstant — eine Weste mit Rüstung 3 blieb Rüstung 3, egal wie oft
sie getroffen wurde. Mark wollte stattdessen, dass sich Rüstung im Kampf
**abnutzt**: sie hält etwas aus, wird dabei schlechter, und irgentwann bringt
sie nichts mehr. Das alte Feld (`kraft`, im Formular "Rüstungsbonus")
existiert weiterhin für Bestandsdaten und einfache Fälle, wird von den
Endpunkten hier unten aber nicht angefasst — ein Gegenstand mit
`ruestungKaestchenMax > 0` nutzt fachlich das neue System, alles andere den
alten flachen Bonus (siehe `frontend/src/kampf/Kampfkarte.tsx`, wo beide
nebeneinander angezeigt werden können).

## Die Grundidee: zwei Werte statt einem

**Kästchen** (`ruestungKaestchenMax` / `ruestungKaestchenAktuell`) — wie viel
Substanz die Rüstung hat, um Treffer zu schlucken, bevor sie reißt. Sinkt mit
Beschädigung, genau wie die Gesundheit einer Person.

**Durchlass** (`ruestungDurchlassBasis` / `ruestungDurchlassAktuell`) — die
Größe der Lücke in der Rüstung: wie viel Schaden *garantiert* ungehindert
durchkommt, bevor die Rüstung überhaupt die Chance hat, etwas abzufangen.

Der entscheidende gedankliche Unterschied zu einem klassischen Rüstungswert:
**niedriger ist besser.** 0 heißt "hermetisch dicht". Das fühlt sich zunächst
falsch an — man ist es gewohnt, dass ein höherer Rüstungswert besser schützt
— aber es macht die Fluff-Seite viel einfacher zu beschreiben:

- Eine **Lederjacke** ist keine "Rüstung 3", sie hat "Durchlass 3": sie ist
  von Haus aus löchrig, weil sie eben nur Leder ist. Selbst ungetragen würde
  ein Nadelstich glatt durchgehen.
- Eine **Bombenschutzweste** startet bei Durchlass 0: im Neuzustand kommt
  nichts automatisch durch, sie muss erst beschädigt werden, bevor überhaupt
  eine Lücke entsteht.

Zwei Unterwerte pro Größe (Basis/Aktuell bzw. Max/Aktuell), weil ein einzelner
Wert für beide Zwecke — "was ist der Ausgangszustand" und "was ist der
aktuelle Zustand" — sich beim Rechnen gegenseitig verfälscht hätte (siehe
nächster Abschnitt).

## Warum Basis UND Aktuell — das ursprüngliche Paradox

Die erste Fassung hatte nur *einen* (steigenden) Durchlass-Wert, der sowohl
für den HP-Schaden als auch für den Kästchenschaden verwendet wurde. Ergebnis
beim Durchrechnen: je kaputter die Rüstung wurde, desto *kleiner* wurde ihr
Überschuss über dem (jetzt höheren) Durchlass — sie nahm also mit jedem
Treffer **weniger** Kästchenschaden, bis irgendwann gar keinen mehr.

Konkret: eine Lederjacke (3 Kästchen, Durchlass 3) verlor bei drei
aufeinanderfolgenden Schlag-6-Treffern erst 1 Kästchen, dann 1, dann **0** —
weil der Durchlass nach jedem Treffer stieg und der Überschuss entsprechend
schrumpfte. **Volle Rüstung war dadurch am leichtesten zu zerstören,
angeschlagene praktisch unzerstörbar** — das genaue Gegenteil von "kaputte
Sachen gehen leichter weiter kaputt".

Der Fix trennt die beiden Rollen:

- Der **Kästchenschaden** rechnet immer gegen die **fixe Basis** — bleibt
  also pro Treffer gleich stark, unabhängig vom Beschädigungszustand.
- Nur der **HP-Durchlass** rechnet gegen die **steigende Aktuell**-Schwelle —
  dadurch sickert trotzdem mehr durch, je kaputter die Rüstung wird, ohne dass
  sich die Rüstung selbst dagegen wehrt.

`backend/tests/test_ruestung.py::TestBombenschutzweste::test_kaestchenschaden_bleibt_konstant_egal_wie_beschaedigt`
belegt das als Regressionstest.

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

**Schritt 1 — was garantiert durchkommt:**

```
garantiert = min(Stärke, Durchlass-Aktuell)
```

**Schritt 2 — was die Rüstung abzufangen versucht** (Berechnungsgrundlage für
den Kästchenschaden, siehe oben):

```
überschuss = max(0, Stärke - Durchlass-Basis)
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

Menge in allen Fällen: `garantiert` (nicht die volle Stärke — der Überschuss
wird von der Rüstung geschluckt und wirkt sich nur auf sie selbst aus, siehe
Schritt 4. Es gibt also **keinen** zusätzlichen HP-Schaden aus dem
Überschuss).

**Schritt 4 — Schaden an die Rüstung (Kästchen).** Hier unterscheiden sich
die drei Schadensarten am stärksten:

- **Unheilbar:** immer die volle Stärke, 1:1 — unabhängig vom Durchlass.
  Mark: *"das wäre ja was wie eine Explosion, da kann man froh sein das
  überstanden zu haben"*. Es gibt keine Verhandlung mit einer Bombe.
- **Tödlich:** eine Mischung, weil die Rüstung hier tatsächlich etwas
  leistet — auch wenn der Treffer gar nicht über die Basis hinausgeht:
  ```
  Kästchenschaden = floor(min(Stärke, Durchlass-Basis) / 2) + überschuss
  ```
  Der Anteil bis zur Basis-Schwelle beschädigt sie nur zur Hälfte (sie hat
  ihn ja immerhin durchgelassen, ohne wirklich zu kämpfen — Mark bestand
  darauf, dass ein Treffer genau an der Schwelle nicht spurlos bleibt), der
  Anteil darüber voll 1:1.
- **Schlag:** nur wenn der Treffer mindestens die Hälfte der *aktuellen*
  Kästchen erreicht — ein laues Klopfen soll wirkungslos abprallen:
  ```
  löst_aus = 2 × Stärke ≥ Kästchen-Aktuell
  Kästchenschaden = überschuss / 2 (abgerundet), falls löst_aus, sonst 0
  ```
  **Bewusst `Kästchen-Aktuell`, nicht `Kästchen-Max`:** dadurch sinkt die
  Auslöse-Schwelle mit jedem Treffer — eine bereits ramponierte Rüstung
  bricht bei Schlagschaden leichter weiter zusammen. Das ist ein zweiter,
  von Schritt 3 unabhängiger "wird schlechter"-Mechanismus.

  Diese Regel klärte ursprünglich die Frage, warum eine Bombenschutzweste
  (Durchlass 0) überhaupt Schaden von einem Faustschlag nehmen sollte: mit
  der alten Formel (`Stärke ≥ 2×Durchlass`) war die Bedingung bei Durchlass 0
  *immer* erfüllt, jeder noch so schwache Treffer hätte genagt. Mit dem
  Bezug auf die Kästchen statt den Durchlass braucht ein 9-Kästchen-Stück
  erst einen Treffer der Stärke 5, um überhaupt etwas auszurichten — kleine
  Treffer prallen wirkungslos ab (siehe `floor()`: bei geringem Überschuss
  rundet die Division ohnehin auf 0).

**Schritt 5 — Durchlass-Aktuell steigt** um genau den in Schritt 4
entstandenen Kästchenschaden:

```
Durchlass-Aktuell = min(Kästchen-Max, Durchlass-Aktuell + Kästchenschaden)
```

Gedeckelt auf **Kästchen-Max**, nicht auf die (sinkenden) aktuellen
Kästchen — sonst würde der Deckel selbst mit jedem Treffer fallen, und die
Rüstung könnte nie so schlecht werden, wie ihre Größe es eigentlich zuließe.

**Sonderfall — 0 Kästchen:** Eine komplett zerstörte Rüstung wirkt gar nicht
mehr. Sie kann dann auch nichts mehr abstufen: der Treffer geht unverändert
und in voller Höhe durch (Mark: *"wirkt gar nicht mehr"*).

## Mehrere Rüstungsteile: ein Pool

Marks Vorgabe: *"ich hätte schon gerne dass alle Rüstungen zu einem Pool
addiert werden, ich will keine Körper Zonen, das ist zu kompliziert"*. Alles
Getragene wirkt deshalb als **eine** virtuelle Rüstung
(`kampf/ruestung.py::pool`):

- **Kästchen** = Summe aller getragenen Teile. Ein gemeinsamer Vorrat, wie
  eine zweite Gesundheitsleiste. Das ist auch die Zahl, gegen die der
  Schlag-Trigger prüft — ein Ganzkörper-Kit lässt sich mit einem Faustschlag
  schwerer eindellen als eine einzelne Weste.
- **Durchlass** = der des **dichtesten** Teils. Ausdrücklich *nicht*
  summiert und kein Mittelwert: die engste Schicht bestimmt, was
  durchsickert. Von diesem Teil kommt auch die **Basis** — beide
  Durchlasswerte müssen aus derselben Schicht stammen, sonst könnten
  Kästchenschaden und HP-Durchlass gegeneinander laufen.

`berechne_treffer` wird also mit den Poolwerten aufgerufen. Von seiner
Rückgabe gelten dann nur `hpArt`, `hpMenge` und `kaestchenSchaden`; die
Felder `kaestchenNeu`/`durchlassNeu` beziehen sich auf die virtuelle
Gesamtrüstung und werden verworfen. Was die einzelnen Teile abbekommen,
rechnet `verteile_kaestchenschaden`.

**Keine Körperzonen, kein Zielen.** Eine Verteilungsregel "welcher Anteil
geht auf Helm, welcher auf die Weste" gibt es bewusst nicht — sie bräuchte
Körperzonen für Rüstung (die es, anders als bei Cyberware, nicht gibt) und
war Mark ausdrücklich zu kompliziert. Die Treffer-Route nimmt deshalb nur
Art und Stärke, kein Ziel.

## Verbrauchsreihenfolge: das dichteste Teil zuerst

Marks Vorgabe: *"zuerst wird das mit dem niedrigsten Durchlasswert
zerstört... dann der nächste"*. Der Kästchenschaden frisst sich aufsteigend
nach `ruestungDurchlassAktuell` durch die Teile, mit Überlauf ins nächste
(`kampf/ruestung.py::reihenfolge` + `verteile_kaestchenschaden`). Jedes
betroffene Teil bekommt seinen **eigenen** Durchlass um seinen **eigenen**
Verlust erhöht, gedeckelt auf sein eigenes Kästchen-Max — dieselbe Regel wie
bei einer Einzelrüstung, nur pro Stück angewandt.

Daraus ergibt sich von selbst die gewünschte Kurve: die gute Weste hält den
Schaden auf und wird dabei verbraucht; ist sie hin, springt der Pool-Durchlass
auf das nächstbeste Teil. *"Erst geht die Bombenweste kaputt, dann bist du nur
noch in der Lederjacke."*

**Diese Reihenfolge schließt außerdem einen sonst offenen Missbrauch.**
Weil der Pool-Durchlass vom besten Teil kommt, könnte man sich ein winziges
Teil mit Durchlass 0 anziehen — das "kugelsichere Suspensorium" — und wäre
dicht, während eine löchrige Jacke die Masse der Kästchen stellt. Weil aber
genau dieses Teil zuerst aufgebraucht wird, ist es nach einem Kästchen weg
und der Durchlass springt sofort auf die Jacke. Das korrigiert sich also von
selbst, ohne Sonderregel (Test:
`test_ruestung.py::TestSuspensoriumMissbrauch`).

**Bei gleichem Durchlass zuerst das kleinere Teil** (weniger Kästchen): so
wird es fertig aufgebraucht, statt dass mehrere Teile halb angeknackst
herumliegen. Danach die Kennung, damit die Reihenfolge bei völligem
Gleichstand reproduzierbar bleibt und nicht von der Sortierung der
Datenbankabfrage abhängt.

## Zerstörte Rüstung gilt nicht mehr als ausgerüstet

Fällt ein Teil auf 0 Kästchen, wird es **ins Mitgeführte zurückgelegt**
(`ablage = RUCKSACK`) und zählt damit nicht mehr zum Pool — weder mit
Kästchen noch mit seinem Durchlass. Wichtig für den zweiten Punkt: eine
zerschossene Weste mit Durchlass 0 darf den Pool nicht weiter dicht
*aussehen* lassen.

Ins Mitgeführte und nicht in den Mülleimer, weil sie reparierbar bleiben
soll — dasselbe Muster wie bei chirurgisch entferntem Chrom, das auch in den
Rucksack zurückwandert (`items/repository.py::setze_verbaut`).

> **Zum Namen:** `RUCKSACK` ist kein Rucksack, sondern der Zustand "am
> Körper, aber nicht griffbereit" — er setzt keinen Behälter voraus. Die
> Oberfläche nennt ihn **"Mitgeführt"**, und nur wenn tatsächlich ein
> Behälter getragen wird, heißt der Bereich nach ihm (siehe
> `items/aufbewahrung.ts::ermittleBereiche`). Ein Platzhalter-Behälter ist
> dafür also nicht nötig.

**Wieder anlegen ist gesperrt**, solange die Kästchen bei 0 stehen:
`.../ablage` antwortet mit `409 Conflict` und *"Zerschossene Rüstung schützt
nicht — sie muss erst repariert werden"*. Ohne diese Sperre könnte man sie
endlos wieder anziehen und würde rätseln, warum der Rüstungsbalken nicht
steigt.

**Ohne wirksame Rüstung** (nichts angelegt, oder alles zerstört) trifft der
Schaden ungebremst und unverändert in seiner Art. Das ist kein Fehlerfall,
sondern erlaubt, dasselbe Popup auch für ungerüstete Charaktere zu benutzen —
die Rechnung "was geht an die Gesundheit" spart man sich trotzdem.

## Reparatur

Mark: *"es muss dann auch eine Möglichkeit geben die Rüstung zu reparieren,
entweder mit dem Hardware Skill, oder bei einem Händler und es kostet
Geld"* — und: *"Reparatur senkt auch die Schwelle"*.

Die reine Rechnung ist gebaut (`kampf/ruestung.py::repariere`,
`POST .../ruestung/reparieren`, nur SL): sie stellt eine angegebene Menge
Kästchen wieder her und senkt den Durchlass **symmetrisch** um denselben
Betrag, nach unten gedeckelt auf die Basis — eine Reparatur macht eine
Rüstung nie besser als neu.

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
neben `zustand`: es ist dieselbe Art von Zustandsänderung, nur mit
vorgeschalteter Rechnung.

**SL für alle, Spieler:innen nur für den eigenen Charakter** (404 bei fremden,
damit deren Existenz nicht bestätigt wird — wie bei `zustand`).

```json
// Request — mehr als Art und Stärke gibt es nicht anzugeben
{ "art": "schwer", "staerke": 6 }

// Response
{
  "hpArt": "schlag",
  "hpMenge": 3,
  "kaestchenSchaden": 4,
  "betroffen": [
    { "id": "…", "name": "Kevlarweste", "verlust": 3, "kaestchenNeu": 0, "durchlassNeu": 3, "zerstoert": true },
    { "id": "…", "name": "Lederjacke", "verlust": 1, "kaestchenNeu": 4, "durchlassNeu": 5, "zerstoert": false }
  ],
  "uebersicht": { "...": "aktualisierte Bogen-Übersicht der Person" }
}
```

Schreibt in einem Rutsch: Kästchen und Durchlass **jedes betroffenen**
Rüstungsteils, die Ablage zerstörter Teile (zurück ins Mitgeführte) UND den
`schadenSchlag`/`schadenSchwer`/`schadenAggraviert`-Zähler der Person — der
HP-Schaden wird **addiert**, nicht gesetzt, damit ein Treffer bereits
vorhandenen Schaden nicht überschreibt.

`betroffen: []` heißt: keine wirksame Rüstung, der Schaden kam ungebremst
und unverändert an. Teile, die nichts abbekommen haben, stehen nicht in der
Liste.

### POST `/api/campaigns/{campaign_id}/gegenstaende/{item_id}/ruestung/reparieren`

**Nur SL.** Bleibt am Gegenstand — reparieren betrifft immer ein bestimmtes
Stück, da gibt es nichts zu entscheiden. Siehe Abschnitt Reparatur oben.

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
  "durchlass": 0,
  "teile": [
    { "id": "…", "name": "Kevlarweste", "kaestchenAktuell": 2, "kaestchenMax": 3, "durchlass": 0 },
    { "id": "…", "name": "Lederjacke", "kaestchenAktuell": 5, "kaestchenMax": 5, "durchlass": 4 }
  ]
}
```

`teile` steht in Verbrauchsreihenfolge (dichtestes zuerst). Bewusst
serverseitig gerechnet (`kampf/ruestung.py::uebersicht`): würde das Blatt
die Pool-Regel nachbauen, liefe die Anzeige irgendwann mit dem auseinander,
was ein Treffer tatsächlich anrichtet. Ohne getragene Rüstung stehen überall
Nullen, und die Leiste bleibt weg.

### GET `.../gegenstaende/{person_id}` (Feld an jedem Gegenstand)

Jede `GegenstandResponse` trägt die vier Felder mit (0, wenn ungenutzt):
`ruestungKaestchenMax`, `ruestungKaestchenAktuell`, `ruestungDurchlassBasis`,
`ruestungDurchlassAktuell`.

## Datenmodell (Neo4j)

Keine neuen Knoten oder Beziehungen — vier zusätzliche Properties am
bestehenden `(:Gegenstand)`-Knoten, analog zu `kraft`:

```cypher
(:Gegenstand {
  typ: "Rüstung",
  ruestungKaestchenMax: 9,
  ruestungKaestchenAktuell: 6,
  ruestungDurchlassBasis: 0,
  ruestungDurchlassAktuell: 3
})
```

Beim Anlegen defaultet `Aktuell` jeweils auf `Max`/`Basis`, wenn nicht
ausdrücklich etwas anderes mitgegeben wird (ein frisches Stück ist
unbeschädigt) — siehe `items/repository.py::create_gegenstand`.

## Durchgerechnete Beispiele

**Lederjacke** (3 Kästchen, Durchlass-Basis 3 — "schützt vor Schlägen, nicht
vor Schüssen"):

| Treffer | An die Trägerin | An die Jacke |
|---|---|---|
| Schlag 6 | 1 Schlag (halbiert von 3) | 1 Kästchen → 2/3 |
| Tödlich 6 | 3 Schlag (abgestuft, nicht halbiert) | 4 → gedeckelt auf 3, Jacke komplett hin |
| Tödlich 3 (genau an der Schwelle) | 3 Schlag | 1 Kästchen (auch ein Treffer, der nicht über die Basis geht, kostet was) |

**Bombenschutzweste** (9 Kästchen, Durchlass-Basis 0 — im Neuzustand
hermetisch dicht):

| Treffer | An die Trägerin | An die Weste |
|---|---|---|
| 1. Schlag 6 | 0 (Durchlass startet bei 0) | 3 Kästchen → 6/9, Durchlass → 3 |
| 2. Schlag 6 (danach) | 1 Schlag (Durchlass jetzt 3, halbiert) | 3 Kästchen → 3/9, Durchlass → 6 |
| Schlag 4 (auf frische Weste) | 0 | 0 — `2×4=8 < 9`, löst gar nicht erst aus |

Beide Tabellen als ausführbare Tests in `backend/tests/test_ruestung.py`.
