---
title: Ereignisprotokoll (Sitzungs-Log)
created: 2026-09-27
updated: 2026-09-27
type: entität
tags: [ereignisprotokoll, datenmodell, ki-integration, inventar, wirtschaft, party, kampf, verhandlung, erfahrung, rassen, geplant, offen]
sources: [../../../CLAUDE.md, ../../../ideen für später.txt]
status: entschieden-nicht-umgesetzt
---

# Ereignisprotokoll (Sitzungs-Log)

## Auslöser

27.09.2026: Mark verlor eine KI-generierte Nachricht/Kommentar, die nirgends
dauerhaft gespeichert war — Auslöser für ein vollständiges Durchsprechen des
Themas Logging, weit über den ursprünglichen Anlass hinaus. War vorher nur
eine vage Notiz unter "Geplante Features" (`CLAUDE.md`, "Event-Log/Timeline
— niedrige Priorität, erst grob klären was getrackt werden soll"). Jetzt
komplett durchgesprochen: Kategorien, Knoten-vs.-Kante-Entscheidung,
Korrektur-/Löschregel, Zeitstempel-Frage.

**Status dieser Seite: Datenmodell entschieden, noch nicht gebaut.** Reines
Konzept-Dokument — kein Code, keine Migration, keine Routen existieren.

## Grundprinzip: ein eigener Knotentyp pro Kategorie

Kernfrage beim Design: ein generischer `SpielEreignis`-Knoten mit `typ`-Feld,
oder pro Kategorie ein eigener Knotentyp? Mark hat sich für **eigene Knoten
pro Kategorie** entschieden — passt zu einem bestehenden Projektprinzip
("keine allgemeinen Felder für Sonderfälle", siehe auch die separaten
Entitätstypen Person/Ort/Event/Fraktion statt einer generischen "Entity").
Ein gemeinsamer Knoten mit `typ`-Feld hätte pro Kategorie ganz
unterschiedliche Pflichtfelder gebraucht (Gegenstandsbewegung braucht
Gegenstand+Besitzerpaar, Achievement-Verleihung braucht Person+Achievement,
NPC-Wissenszuwachs braucht NPC+Auslöser) — das wäre entweder ein
Optional-Feld-Rattenschwanz oder ein JSON-Blob geworden, beides gegen den
bestehenden Stil.

**Kompromiss für die trotzdem gewünschte gemeinsame Zeitleiste:** jede
Kategorie bekommt ihren eigenen, fachlich sauberen Knotentyp — aber alle
tragen dieselben Basis-Properties (siehe unten), damit eine gemeinsame
Zeitleisten-Abfrage trotzdem mit einer Cypher-`UNION` über alle
Kategorie-Typen möglich ist, ohne dass die einzelnen Typen unsauber werden.

**Knoten statt Kante, wo Historie zählt:** eine reine Kante wie `BESITZT`
oder `BEFINDET_SICH_AN` überschreibt sich beim nächsten Wechsel — für den
aktuellen Stand reicht das, für ein **Log mit voller Historie** (wer hatte
den Gegenstand VORHER, wer war VORHER an diesem Ort) braucht es einen
eigenständigen Log-Knoten pro Ereignis, der sich per Kanten an die
beteiligten Entitäten hängt. Faustregel im Gespräch mit Mark: reicht der
aktuelle Stand → Kante; braucht es die ganze Zeitreihe → eigener Knoten.

## Zeitstempel: real vor allem, In-Game-Datum als Zusatzfeld

Mark: *"vor allem der Reale, aber wir können sehr gerne eine ingame Datums
funktion einbauen... das klingt eigentlich ganz cool... müssen wir dann
schön machen!"* — reales Datum ist Pflicht (beantwortet die eigentliche
Ausgangsfrage: "an welchem Abend ist das passiert"), ein In-Game-Datum ist
gewünscht, aber bewusst erstmal nur ein **Freitext-Platzhalterfeld**
(`ingameDatum: string`) — ein echtes strukturiertes Kalendersystem (eigene
Monats-/Jahreszählung für NeotopiA, Umrechnung, Anzeige) ist ein eigenes,
noch unspezifiziertes Feature, das Mark bewusst *"schön machen"* will, bevor
es gebaut wird. Bis dahin ist es ein reines Textfeld ohne Validierung.

## Korrektur statt Unveränderlichkeit

Mark: *"SL darf nachträglich Einträge korrigieren, ergänzen usw."* — kein
striktes Audit-Log. Löschen folgt derselben Regel wie überall sonst im
Projekt (`docs/wiki/SCHEMA.md`, Abschnitt "Allgemein" in `CLAUDE.md`:
"Papierkorb statt echtem Löschen (SL-sichtbar)"): jeder Log-Eintrag trägt
`geloescht: bool` statt hart entfernt zu werden — ein SL-Papierkorb kann
später alle als gelöscht markierten Einträge zeigen, falls sich jemand doch
vertan hat.

## Gemeinsame Basis-Properties (jede Kategorie unten)

```
zeitpunkt: datetime       # echter Zeitpunkt (Pflicht)
ingameZeitpunkt: string   # Freitext, optional (siehe oben)
sitzungId: uuid           # Bezug zur Sitzung, optional (s.u.)
slNotiz: string           # freie SL-Anmerkung, optional
geloescht: bool           # Papierkorb, default false
campaignId: uuid          # wie überall im Projekt
```

## `Sitzung` — der Anker-Knoten

```cypher
(:Sitzung {
  id: uuid,
  campaignId: uuid,
  datum: "2026-09-27",          # echtes Kalenderdatum, Pflicht
  ingameDatum: "12. Regen, 2087", # Freitext-Platzhalter, s.o.
  titel: "Session 14",          # optional
  notiz: "...",                 # optional, SL-Freitext zum Abend allgemein
  erstelltAm: datetime
})
```

Jede Kategorie unten verknüpft sich per `-[:WAEHREND]->(:Sitzung)` **oder**
trägt nur die `sitzungId`-Property (analog zum bestehenden
`campaignId`-Muster: Kante für Navigierbarkeit, Property für schnelle
Filterung — beides parallel, wie es das Projekt schon bei `campaignId`
macht). `sitzungId` ist optional, weil manche Log-Kategorien (z. B. ein
KI-Aufruf mitten in der Woche, außerhalb eines Spielabends) keiner Sitzung
zugeordnet sein müssen.

## Kategorien

### 1. `KiProtokollEintrag` — der eigentliche Auslöser

Aktuell verschwinden KI-Ausgaben (Vorschau in `KiTextPopup`, Prüfergebnisse,
Bild-Prompt-Vorschläge, Auto-Verknüpfungs-Vorschläge...) spurlos, wenn
niemand aktiv "Übernehmen" klickt — genau das hat Mark am 27.09.2026
verloren. Diese Kategorie loggt **jede KI-Ausgabe dauerhaft**, unabhängig
vom Übernahme-Status:

```cypher
(:KiProtokollEintrag {
  ...Basis,
  anlass: string,        # z.B. "objekt-text", "wiki-pruefung",
                          # "auto-verknuepfung", "bild-prompt", "npc-chat"
  prompt: string,        # Nutzer-/Auslöser-Eingabe, falls vorhanden
  antwortText: string,   # volle KI-Rohausgabe
  uebernommen: bool       # wurde der Vorschlag ins Spiel übernommen?
})-[:BETRIFFT]->(beliebige Entität)   # optional, Bezug (Person/Ort/Event/...)
```

### 2. `GegenstandsBewegung`

Volle Besitzerkette + Ereignisart eines Gegenstands (Marks MacGuffin-Beispiel
im Gespräch: gefunden → weitergegeben → gestohlen, jede Station geloggt statt
nur den aktuellen Besitz zu zeigen):

```cypher
(:GegenstandsBewegung {
  ...Basis,
  art: "GEFUNDEN" | "GEKAUFT" | "VERKAUFT" | "WEITERGEGEBEN" |
       "GESTOHLEN" | "ZERSTOERT" | "REPARIERT" | "ENTSORGT" | "SONSTIGES",
  handelId: uuid          # optional, verknüpft mit passender GeldBewegung (s.u.)
})-[:BETRIFFT]->(:Gegenstand)
  -[:ALTER_BESITZER]->(:Person)   # optional (z.B. bei "GEFUNDEN" leer)
  -[:NEUER_BESITZER]->(:Person)   # optional (z.B. bei "ENTSORGT" leer)
  -[:ORT]->(:Ort|:Event)          # optional
```

### 3. `GeldBewegung`

Kapitalbewegungen unabhängig vom betroffenen Gegenstand (Mark: *"das Geld
müssen wir auch tracken"*), an `Person.kapital` gebunden, nicht an einem
Item — siehe [[../concepts/waehrung-und-preise]]:

```cypher
(:GeldBewegung {
  ...Basis,
  betrag: number,
  art: "HANDEL" | "WEITERGABE" | "NPC_BELOHNUNG" | "DIEBSTAHL" |
       "AUSGABE" | "SONSTIGES",
  handelId: uuid           # optional, verknüpft mit passender GegenstandsBewegung
})-[:VON]->(:Person)        # optional (Quelle, z.B. NPC oder Spieler)
  -[:AN]->(:Person)         # optional (Empfänger)
```

**Handel ist bewusst kein dritter Knotentyp** — Marks eigene Erkenntnis im
Gespräch: *"da sind wir eh wieder bei den Gegenständen"*. Ein abgeschlossener
Kauf/Tausch erzeugt einfach EINE `GegenstandsBewegung` + EINE `GeldBewegung`
mit gemeinsamer `handelId` — verknüpft mit dem bestehenden
Verhandlungs-System (`app/verhandlung/`, siehe [[gegenstand-transfer]]),
keine Parallelstruktur.

### 4. `Aufenthalt` — Party-/Personenbewegung

Wer war wann mit welchem Event/Ort verknüpft — historisiert, im Gegensatz
zur bestehenden `BEFINDET_SICH_AN`-Kante, die sich beim Ortswechsel
überschreibt (siehe [[party-feature]]):

```cypher
(:Aufenthalt {
  ...Basis
})-[:PARTY]->(:Party)        # optional, alternativ zu PERSON
  -[:PERSON]->(:Person)      # optional, falls jemand einzeln unterwegs war
  -[:ORT]->(:Ort|:Event)
```

**Löst nebenbei einen bereits notierten Blocker:** `CLAUDE.md` Punkt 8 nennt
als Voraussetzung für die geplante KI-Auto-Steigerung von NPCs/Begleitern
ausdrücklich ein *"Party-Besuchs-Log (`WAR_AN`-Kante mit Zeitstempel), weil
`BEFINDET_SICH_AN` beim Ortswechsel überschrieben statt historisiert wird
und 'hat die Party das Event schon erlebt' sonst nicht beantwortbar ist"* —
`Aufenthalt` ist genau diese fehlende Grundlage, nur als Knoten statt reiner
Kante (wegen `slNotiz`/Korrigierbarkeit).

### 5. `Achievement` + `AchievementVerleihung`

Katalog-Knoten + Verleihungs-Log. **Vollständig ausspezifiziert (27.09.2026,
Mark: "beides" — automatisch erkannt UND spontan von Hand vergebbar).**
Details, Beispiele und Trigger-Katalog: [[achievements]] (eigene Seite,
weil das Thema eigenständig genug für mehr Tiefe ist).

### 6. `NpcWissenszuwachs`

Wann ein NPC wodurch von etwas erfahren hat (Mark: *"natürlich interessieren
uns auch NPCs, und wann diese z.B. Informationen oder Wissen dazu bekommen
haben wegen anderen Events"*):

```cypher
(:NpcWissenszuwachs {
  ...Basis,
  wieErfahren: string     # Freitext: "Gerücht", "Verhör", "beobachtet", ...
})-[:NPC]->(:Person)
  -[:AUSLOESER]->(beliebige Entität)   # optional: Event/Gegenstand/Person/Ort
```

## Zeitleisten-Abfrage (Konzept, noch nicht gebaut)

Ziel: "was ist am Abend X passiert" aus einer Abfrage, trotz getrennter
Knotentypen — Cypher-`UNION` über alle Kategorien mit derselben
`sitzungId`, sortiert nach `zeitpunkt`. Skizze (Feinheiten beim Bauen
klären, insbesondere wie unterschiedliche Rückgabeformen einheitlich
gemappt werden):

```cypher
MATCH (g:GegenstandsBewegung {sitzungId: $sitzungId, geloescht: false})
RETURN g.zeitpunkt AS zeitpunkt, "GegenstandsBewegung" AS kategorie, g AS eintrag
UNION
MATCH (a:Aufenthalt {sitzungId: $sitzungId, geloescht: false})
RETURN a.zeitpunkt AS zeitpunkt, "Aufenthalt" AS kategorie, a AS eintrag
UNION
// ... eine UNION-Zeile pro Kategorie
ORDER BY zeitpunkt
```

### 7. `KampfLogEintrag`

Runde für Runde: wer hat wen getroffen, kritische Treffer, Bewusstlosigkeit/
Tod, Kampfausgang. Für Session-Recaps vermutlich der interessanteste Teil.

```cypher
(:KampfLogEintrag {
  ...Basis,
  kampfId: string,        # Bezug zum Kampf (auch wenn der später gelöscht wird)
  runde: int,
  art: "TREFFER" | "KRITISCH" | "BEWUSSTLOS" | "TOD" | "GEFLOHEN" | "KAMPFENDE",
  hpArt: "schlag" | "schwer" | "aggraviert",  # nur bei TREFFER/KRITISCH
  hpMenge: int,
  kaestchenSchaden: int
})-[:ANGREIFER]->(:Person)   # optional, siehe Auto-Zuordnung unten
  -[:ZIEL]->(:Person)        # die Person, an der der Treffer eingetragen wurde
```

**Automatische Angreifer-Zuordnung** (Mark, 27.09.2026: *"wenn mein Spieler
dran ist, und ein NPC leben verliert, der Spieler diesen NPC verletzt hat,
und umgekehrt natürlich auch!"*) — beim Eintragen eines Treffers
(`POST .../personen/{id}/ruestung/treffer`, siehe [[../../api/ruestung.md]])
während eines laufenden Kampfs wird automatisch die Person nachgeschlagen,
die laut `Kampf.amZug` gerade am Zug ist (`KampfTeilnehmer-[:IST]->Person`,
siehe `backend/app/kampf/repository.py::hole`), und als `ANGREIFER` gesetzt
— **kein manuelles Zusatzfeld im Regelfall nötig**, die bestehende
Zugreihenfolge trägt die Information schon in sich. Neues optionales
Override-Feld `angreiferPersonId` in `RuestungTrefferInput`
(`backend/app/traits/routes.py`) für Ausnahmefälle: Treffer außerhalb der
Zugreihenfolge, Umwelt-/Fallenschaden ohne Angreifer, nachträgliche
SL-Korrektur. Außerhalb eines laufenden Kampfs bleibt `ANGREIFER` leer,
sofern nicht manuell gesetzt.

### 8. `VerhandlungsAusgang`

Ergebnis einer abgeschlossenen Verhandlung (Shop-Kauf, Rüstungsreparatur,
Gegenstands-Weitergabe, siehe [[gegenstand-transfer]] und
[[../../api/verhandlung.md]]) — bisher trägt der `Verhandlung`-Knoten nur den
aktuellen Status (`OFFEN`/`ANGENOMMEN`/`ABGELEHNT`), keine dauerhafte
Historie über mehrere Verhandlungen hinweg:

```cypher
(:VerhandlungsAusgang {
  ...Basis,
  verhandlungId: string,
  art: "RUESTUNG_REPARATUR" | "SHOP_KAUF" | "GEGENSTAND_WEITERGABE",
  angenommen: bool,
  gesamtbetrag: int,
  positionenJson: string   # Schnappschuss der Positionen zum Entscheidungs-
                            # zeitpunkt — ein später geänderter Händlerpreis
                            # darf die Historie nicht rückwirkend verfälschen
})-[:ANGEBOTEN_VON]->(:Person)   # optional (meist SL, nur bei Spieler-zu-Spieler gesetzt)
  -[:EMPFAENGER]->(:Person)
```

Entsteht automatisch bei `POST .../verhandlungen/{id}/antwort`
(`backend/app/verhandlung/logic.py`), unabhängig davon ob angenommen oder
abgelehnt — Ablehnungen sind für einen Rückblick genauso interessant
("die Party hat das Angebot des Fixers ausgeschlagen").

### 9. `CharakterEntwicklung`

Wer wurde wann wie stark — Punkt-Käufe (`POST .../personen/{id}/steigern`)
und EP-Vergaben (`POST .../personen/{id}/erfahrung`) sind aktuell komplett
ungeloggt, nur der jeweils aktuelle Wert steht am Charakterblatt.

```cypher
(:CharakterEntwicklung {
  ...Basis,
  art: "STEIGERUNG" | "WILLENSKRAFT" | "ERFAHRUNG_VERGEBEN" | "RASSE_GEAENDERT",
  traitDefId: string,   # nur bei STEIGERUNG
  traitName: string,    # Anzeige-Snapshot — überlebt eine spätere Umbenennung
                          # des TraitDef (siehe Stolperstein 6, neo4j-datenmodell.md)
  alt: string,           # bei RASSE_GEAENDERT: alte Rasse (Text). Sonst: alter Wert als String
  neu: string,           # neue Rasse bzw. neuer Wert
  kostenOderMenge: int   # EP-Kosten bei STEIGERUNG/WILLENSKRAFT, vergebene
                          # Menge bei ERFAHRUNG_VERGEBEN, leer bei RASSE_GEAENDERT
})-[:PERSON]->(:Person)
```

**Begründung nutzt das bereits vorhandene `slNotiz`-Basisfeld** — kein
zusätzliches Feld nötig. Mark, 27.09.2026: *"ja ich finde das gut wenn es
die Option einer Begründung gibt! vor allem bei den extra XP macht das
Sinn"* — `ErfahrungInput` (`traits/schemas.py`/`routes.py`) bekommt dafür ein
neues optionales Feld `begruendung: str = \"\"`, das direkt in `slNotiz`
landet. Bei `STEIGERUNG`/`WILLENSKRAFT` bleibt `slNotiz` meist leer (der
Spieler kauft selbst, ohne Begründungstext), ist aber technisch genauso
nutzbar, falls die SL nachträglich kommentieren will.

**Charaktererstellung selbst wird NICHT geloggt** (Mark, 27.09.2026,
ausdrücklich entschieden: *"nein die Charaktererstellung selbst muss nicht
mitgeloggt werden, es reicht wann der Charakter erstellt wurde"*) — die
anfängliche Freebee-Verteilung läuft über einen eigenen Codepfad
(`traits/erstellung.py`), keine `CharakterEntwicklung`-Einträge dafür.

**Voraussetzung, aktuell eine echte Lücke:** `Person` trägt bisher **kein
`erstelltAm`-Feld** (`entities/repository.py::PERSON_FIELDS`/`_BOGEN_FELDER`)
— jede Person entsteht ohne Zeitstempel, "wann wurde X erstellt" ist damit
für JEDEN bestehenden und neuen Charakter unbeantwortbar, bis das Feld
ergänzt wird. Muss beim Bauen zuerst nachgezogen werden (neues Feld in
`PERSON_FIELDS`, gesetzt in `create_node()`/an der Charaktererstellungs-Route,
kein Log-Knoten nötig — ein einfaches Property reicht für diesen einen Zweck).
Bestehende Personen bekommen dabei kein rückwirkendes Datum (kann niemand
mehr wissen) — Feld bleibt bei denen leer, erst ab Einführung gefüllt.

**Rasse nachträglich geändert** (Mark, 27.09.2026: *"nehmen wir das mit, das
kann ja auch storytechnisch begründet passieren... Body Swap oder sowas"*)
— `rasse` ist bereits ein generisches PATCH-Feld (`PersonUpdate.rasse`,
`entities/schemas.py`), es gibt keinen eigenen Endpunkt dafür. Der
allgemeine Personen-Update-Pfad muss beim Bauen einen Vergleich alt/neu
einbauen: ändert sich `rasse` gegenüber dem bisherigen Wert, entsteht
automatisch ein `CharakterEntwicklung`-Eintrag mit `art: "RASSE_GEAENDERT"`
— unabhängig davon, ob der Rassenwechsel spielmechanisch etwas nach sich
zieht (Maxima, Attributmodifikatoren — siehe [[../concepts/rassen]]) oder
rein erzählerisch ist.

## Vorgemerkt für später, gleiches Muster (noch nicht durchgesprochen)

- **Verwundungs-/Todesmeilensteine** — schwer verwundet, Rüstung
  zerschossen, Tod, als dramatische Marker fürs Recap. Teilweise deckt
  `KampfLogEintrag` (`art: "BEWUSSTLOS"|"TOD"`) das schon ab — prüfen, ob ein
  separater Meilenstein-Knoten wirklich zusätzlich nötig ist.
- **Beziehungsänderungen** — eventuell reicht hier die bestehende
  `VERBINDUNG`-Kante samt Erstellungszeitpunkt aus (siehe
  [[neo4j-datenmodell]]), statt einen weiteren Log-Knoten zu bauen —
  gegenprüfen, sobald diese Kategorie konkret angegangen wird.
- **Freies SL-Ereignis** — Freitext-Eintrag ohne feste Entität dahinter
  ("Party hat die Bar abgefackelt"), nur `-[:WAEHREND]->(:Sitzung)` nötig.

## Warum Neo4j auch fürs Logging die richtige Wahl bleibt

Mark fragte (27.09.2026), ob ein anderes Tool (Zeitreihen-/Log-Datenbank)
besser geeignet wäre. **Antwort: nein, Neo4j bleibt richtig, ein Zusatztool
wäre Overkill in die andere Richtung.** Fast jeder Log-Eintrag hängt sich per
Kante direkt an bestehende Knoten (Person, Gegenstand, Ort) — in einer
separaten Zeitreihen-DB bräuchte jede Abfrage wie "zeig mir alles, was Fred
betrifft" einen Join zurück in den Graph, also zwei Datenbanken statt einer
Cypher-Abfrage. Bei diesem Datenvolumen (ein Homebrew-Spieltisch, keine
Industrie-Telemetrie) macht Neo4j das mühelos mit; ein zweites System wäre
nur zusätzlicher Betriebsaufwand ohne echten Nutzen.

## Offene Fragen

- Was ein Achievement inhaltlich ist/bewirkt — **bewusst zurückgestellt**,
  Mark klärt das separat.
- UI/Ansicht der Zeitleiste (wo im Commlink? eigener Bereich? nur SL oder
  auch Spieler-Rückblick?) — **noch nicht entworfen**.
- Genaue Feldliste je Kategorie kann sich beim tatsächlichen Bauen noch
  verschieben (dies ist ein Konzept-Dokument, kein fertiges Schema).
- Ob `Aufenthalt` das bestehende `BEFINDET_SICH_AN` ersetzt oder nur
  zusätzlich mitläuft (aktueller Stand weiter per Kante, Historie separat
  per Log) — **naheliegend ist "zusätzlich"**, nicht entschieden.

## Entwicklung

- **27.09.2026** — Ausgelöst durch eine verlorene KI-Nachricht. Komplettes
  Datenmodell im Gespräch durchgesprochen: Knoten-vs.-Kante-Grundprinzip
  geklärt (an Marks MacGuffin-Beispiel), sechs Kategorien konkret
  spezifiziert (KI-Protokoll, Gegenstandsbewegung, Geldbewegung, Aufenthalt,
  Achievement-Verleihung, NPC-Wissenszuwachs), reales Datum als Pflicht +
  In-Game-Datum als späteres Zusatzfeature, SL-Korrektur statt starrem
  Audit-Log (Papierkorb-Konvention). Reines Konzept — noch kein Code.
- **27.09.2026, gleicher Tag** — Zwei weitere Kategorien aus der
  "Vorgemerkt"-Liste konkret ausspezifiziert, auf Marks Wunsch: `KampfLogEintrag`
  (mit automatischer Angreifer-Zuordnung aus `Kampf.amZug` — Mark: "wenn mein
  Spieler dran ist, und ein NPC leben verliert, hat der Spieler diesen NPC
  verletzt, und umgekehrt") und `VerhandlungsAusgang` (Ergebnis jeder
  beantworteten Verhandlung, egal ob angenommen oder abgelehnt). Zusätzlich
  Marks Frage beantwortet, ob Neo4j fürs Logging die richtige Wahl ist
  (ja — siehe eigener Abschnitt oben).

- **27.09.2026, dritte Runde** — `CharakterEntwicklung` ausspezifiziert:
  Steigerungs-/Willenskraft-/EP-Vergabe-Log mit optionaler Begründung (nutzt
  das bestehende `slNotiz`-Basisfeld, kein Zusatzfeld nötig), plus
  `RASSE_GEAENDERT` für nachträgliche Rassenwechsel (Mark: "kann ja auch
  storytechnisch begründet passieren... Body Swap oder sowas"). Explizit
  NICHT geloggt: die Charaktererstellung selbst. Dabei eine echte Lücke im
  bestehenden Code gefunden: `Person` hat aktuell gar kein `erstelltAm`-Feld
  — muss beim Bauen zuerst ergänzt werden, sonst bleibt "wann wurde X
  erstellt" für jeden Charakter unbeantwortbar.

## Siehe auch

- [[neo4j-datenmodell]] — Node-/Beziehungstypen im Gesamtkontext, Papierkorb-Konvention
- [[gegenstand-transfer]] — bestehendes Verhandlungs-/Transfer-System, das `handelId` verknüpft
- [[party-feature]] — `MITGLIED_VON`/`BEFINDET_SICH_AN`, Vorlage für `Aufenthalt`
- [[../concepts/waehrung-und-preise]] — `Person.kapital`, geplante Geld-Weitergabe
- [[ki-integration]] — alle KI-Anwendungsfälle, die `KiProtokollEintrag` erfassen soll
- [[mitteilungen-system]] — bereits dauerhaft gespeicherte Broadcasts (Abgrenzung: die sind schon geloggt, KI-Vorschauen bisher nicht)
- [[../../../CLAUDE.md]] — Punkt 17 unter "Geplante Features"
- [[../../api/kampf.md]] — laufende Kampf-/Initiative-Verwaltung, `Kampf.amZug`
- [[kampf-und-initiative]] — Regelkonzept Kampf, Grundlage für `KampfLogEintrag`
- [[../concepts/erfahrung-und-steigern]] — EP-Preisformel, Grundlage für `CharakterEntwicklung`
- [[../concepts/rassen]] — Rassen-Baukasten, Grundlage für `RASSE_GEAENDERT`
- [[achievements]] — vollständiges Achievement-Konzept (Katalog, Auto-Erkennung, KI-Text)
