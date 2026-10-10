---
title: Hintergrund-Baukasten
created: 2026-10-10
updated: 2026-10-10
type: entität
tags: [charaktererschaffung, hintergrund, erfahrung, achievements, ki-integration, kontakte, geplant]
sources: [../../../CLAUDE.md, ../../../backend/app/traits/erstellung.py, ../../../backend/app/ki/routes.py, zusatzfertigkeiten.md, achievements.md, ki-integration.md, kontakte-messenger.md]
status: entschieden-nicht-umgesetzt
---

# Hintergrund-Baukasten

Entschieden 10.10.2026. **Kein generisches `mechanikTyp`-Feld** am Katalog
(keine allgemeinen Felder für Sonderfälle). Narrativ ist Baukasten,
Mechanik ist eigener Code.

## Ist-Zustand (vor dem Umbau)

- `HINTERGRUENDE` in `backend/app/traits/erstellung.py` — zehn feste
  Einträge, nur `name` + `beschreibung`, ruleset-weiter `TraitDef`,
  `HAS_TRAIT`. Keine UI.
- `HINTERGRUND_MAX = 5`, `HINTERGRUND_PUNKTE_GESAMT = 5`, Freebee 1 je Punkt.
- Nach der Erstellung nicht spielerseitig steigerbar; Achievements mit
  `belohnungsArt: "HINTERGRUND"` sind der einzige Aufstieg
  (siehe [[achievements]]).
- `Achievement.belohnungsHintergrund` speichert den **Namen**, keine ID —
  Umbenennen/Löschen bricht still. Mit dem Baukasten auf ID umstellen.
- Der ✨-Charaktergenerator (`ki/routes.py::_setze_traits`) schreibt
  Roh-Ratings, geklemmt nur auf `defaultMax`. **Keine** `pruefe()` —
  deshalb wirken KI-Attribute oft zu hoch. Das ist der Bug, den
  Hintergrund-NPCs nicht erben dürfen.

## Zwei Schichten

### 1. Narrativ — SL-Baukasten

Wie [[zusatzfertigkeiten]]: campaign-gebunden, sofort wählbar, kein
Freigabe-Schalter. Eine Zeile im Katalog = ein ankreuzbarer Hintergrund
(`Pilotenschein`, nicht generisches „Lizenz“ plus Freitext).

```
(:Hintergrund {id, campaignId, name, kurzbeschreibung, detailbeschreibung})
(:Person)-[:HAT_HINTERGRUND {rating: 1–5}]->(:Hintergrund)
```

Alte Liste ohne Mentor/Kontakte (Ressourcen, Straßenruf, Verbündete,
Unterschlupf, Schwarzmarkt, Konzernzugang, Ausrüstung, Geheimwissen)
wird als **editierbarer Seed** in jede Kampagne kopiert. SL löscht oder
überschreibt.

### 2. Mechanik — fest im Code, nicht im Baukasten erfindbar

| Hintergrund | Wirkung |
|---|---|
| **Mentor** | genau ein NPC, Paket Profi, `20×N` EP, Plan-Autosteigerung, Bild, Welt-Verbindungen |
| **Kontakte** | `N` NPCs bei Rating N, voller KI-Charakter **ohne** Profi-Zwang und **ohne** EP-Leiter |

```
(:Person)-[:HAT_MENTOR {rating}]->(:Person {personType: NPC})
(:Person)-[:HAT_KONTAKT]->(:Person {personType: NPC})
(:Person)-[:KENNT {stufe, chatOffen}]->(:Person)   # Messenger, s. [[kontakte-messenger]]
```

Gegenstände am Mentor: bewusst nicht in v1.

## KI-Charaktere = Spieler-Erstellung

Die KI füllt **dasselbe Formular** wie ein Spieler (`ErstellungInput`:
Rasse, Weg, Schwerpunkte, Attributpunkte, Fertigkeitspaket,
Fertigkeitspunkte, Freebees). Ergebnis muss `erstellung.pruefe()`
überstehen, Werte kommen aus `endwerte()`, nicht aus Roh-Ratings.

Gilt für Mentor, Kontakte **und** den ✨-Charakterpfad in der
Ideenschmiede (derselbe Generator, derselbe Attribut-Bug).

Unbekannte Rasse / nicht in der Kampagne freigegeben → verworfen.
Erlaubte Rassen kommen aus dem Rassen-Baukasten (`ERLAUBT_RASSE`),
nicht aus der hart verdrahteten Fünferliste im alten Prompt.

## Mentor-Pipeline

Spieler schreibt eine Beschreibung (Erstellungs-Schritt, sobald Punkte
drauf liegen; Nachreichen im Hintergründe-Popup erlaubt). Leer → kein
KI-Call, Slot bleibt.

1. KI bekommt Beschreibung + PC-Kontext (Rasse, Weg, Flavor) +
   freigegebene Rassen + Trait-Katalog.
2. **Rasse:** aus der Beschreibung, nur wenn in der Kampagne
   freigegeben („Mentor war eine Ratte“ + Ratte existiert → Ratte).
   Sonst Fallback: Rasse des PC.
3. **Weg:** Vorschlag = Weg des PC (Häretiker-Flavor inklusive).
   Die Beschreibung **darf das verbiegen**. Nur wenn nichts dazu steht,
   bleibt der PC-Weg.
4. **Paket:** immer Profi. KI liefert die acht Fertigkeiten und die
   legale Attributverteilung, nicht die Endzahlen.
5. System legt NPC an (`istEntwurf=true`, `sichtbarkeit=GM`), wendet
   `pruefe`/`endwerte` an, schreibt `20×N` EP, führt die Autosteigerung
   aus (siehe unten).
6. Bis zu **N** `VERBINDUNG`-Kanten auf **bestehende** Orte/Fraktionen/
   Personen (Muster Auto-Verknüpfung). Leere Welt → 0, kein NPC-Spam.
7. Bild automatisch erzeugen und am Entwurf speichern (kein Extra-Popup;
   die Prüfung ist die Schmiede). Bildfehler lässt den Entwurf ohne
   Portrait stehen.
8. `HAT_MENTOR` + `KENNT` (`chatOffen=true`) sofort. Spieler sieht
   Name/Bild/Messenger **erst nach „✓ Übernehmen“**.

EP-Soll ist immer `20×N` (1→20 … 5→100). Achievement oder späteres +1
→ +20 EP, Plan weiter abarbeiten. Kein Umwürfeln; SL-Edits bleiben.

## Kontakte-Pipeline

Eine Beschreibung pro Punkt. Voller KI-Charakter über denselben
legalen Erstellungspfad. KI wählt Rasse aus dem Freigabe-Katalog und
das Fertigkeitspaket (kein Profi-Zwang). **Kein** `20×N`-EP.

Kanten `HAT_KONTAKT` + `KENNT` sofort, Sichtbarkeit wie Mentor erst
nach Übernehmen. Mehrere Kontakte nacheinander (Massenjob), damit sich
Namen nicht doppelklicken.

## Autosteigerung — Plan, nicht Resteverwertung

**Nicht** „EP ausgeben weil sie da sind“ (kein Round-Robin auf die
höchste Fertigkeit, kein Rest in Billigskills — sonst wird aus der
Ninja-Ratte ein Finanzamt).

**Sondern:** die KI liefert in **demselben** Generierungs-Call einen
geordneten Plan einzelner +1-Schritte, passend zu Konzept und den
schon gewählten Profi-Skills. Attribute gehören dazu — sie sind teuer,
deshalb gerade sparenswert.

Executor (reine Funktion, ohne KI, ohne DB):

1. Nimm `Plan[0]`.
2. Reicht das unausgegebene EP für genau diesen Schritt? Kaufen, Plan
   vorn verkürzen.
3. Reicht es nicht? **Stopp, EP bleibt liegen.** Nicht den Plan
   überspringen, nicht etwas Billigeres hinterher kaufen.
4. Nur Werte, die nach der Erstellung schon > 0 sind, plus
   Willenskraft. Kein Neu-Erlernen (keine Finanzen-5 auf der Ninja-Ratte).
5. Nicht über Lebensmax.

Dieselbe Funktion hängt als SL-Knopf „EP automatisch ausgeben“ am
NPC-Blatt (gespeicherter Plan, sonst unangetastet). Mentor ruft sie
nach der Erstellung auf.

Plan leer und EP übrig: liegen lassen (SL oder späterer Replan). Bei
Mentor-Rating-Plus: Delta gutschreiben, Restplan weiter.

Das ist **nicht** die geplante KI-Auto-Steigerung aus Events
([[ereignisprotokoll]], CLAUDE.md Punkt 8). Hier: Erstellung + EP-Soll,
deterministischer Executor.

## Sichtbarkeit

„Freigabe“ = Ideenschmiede-Übernehmen (`istEntwurf=false`), nicht
weltöffentlich. Beim Übernehmen eines Hintergrund-NPCs: sichtbar
**für diesen PC**, nicht für die ganze Gruppe. Spieler-Listen
(Messenger, Hintergründe-Popup) filtern `istEntwurf`. Bis dahin sieht
der Spieler nur die eigene Beschreibung und „SL prüft noch“.

## Spieler-UI

Button auf dem Charakterblatt → Commlink-Popup: narrative Hintergründe
mit Name/Punkte/Text; Mentor und Kontakte als Karten (nach Freigabe
Name+Bild, klickbar in den Messenger). Kein natives Browser-Dialog,
kein Inline-Akkordeon.

## Kosten

1 Mentor + N Kontakte = `(1+N)` Text-KI + `(1+N)` Bild-KI. Bild-Provider
wie bisher (Cloud/lokal). Leerlassen der Beschreibung = kein Call.

## Migration

Bestehende `HAS_TRAIT` auf alte Hintergrund-Namen: Seed-Einträge
bekommen `HAT_HINTERGRUND`; Mentor/Kontakte-Punkte erzeugen noch keine
NPCs nachträglich (SL stößt die KI an, wenn gewünscht). Achievement-
Bezug von Name auf Katalog-ID bzw. Systemschlüssel `MENTOR`/`KONTAKTE`.

## Siehe auch

- [[zusatzfertigkeiten]] — Vorbild campaign-Katalog ohne Freigabe-Schalter
- [[achievements]] — Hintergrund-Belohnung, ID-Umstellung
- [[ki-integration]] — Charaktergenerator, Bild, Auto-Verknüpfung, Ideenschmiede
- [[kontakte-messenger]] — `KENNT` / `chatOffen`
- [[../concepts/charaktererschaffung]] — Pakete, Freebees, `pruefe()`
- [[../concepts/erfahrung-und-steigern]] — EP-Tarif, den der Executor benutzt
- [[rassen-baukasten-feature]] — `ERLAUBT_RASSE`, Ratte/Schildkröte nur wenn freigegeben
- [[architektur-drei-ebenen]] — `istEntwurf` vs. Kampagne
