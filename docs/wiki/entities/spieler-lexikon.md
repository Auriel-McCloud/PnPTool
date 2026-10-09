---
title: Spieler-Lexikon (Welt/Fauna/Flora/Objekte)
created: 2026-10-09
updated: 2026-10-09
type: entität
tags: [wiki-feature, ui, datenmodell, backend, frontend, geplant]
sources: [../../../CLAUDE.md, ingame-wiki-feature.md, neo4j-datenmodell.md, party-feature.md, ereignisprotokoll.md]
status: entschieden-nicht-umgesetzt
---

# Spieler-Lexikon (Welt/Fauna/Flora/Objekte)

> Nicht zu verwechseln mit dem [[ingame-wiki-feature]] (SL schreibt Seiten,
> die explizit freigegeben werden). Das Lexikon zeigt stattdessen **echte
> Entitäten** (Ort/Gewächs/Critter/story-relevanter Gegenstand) in einer
> eigenen Spieler-Ansicht, gefiltert über einen neuen automatischen
> Entdeckungs-Mechanismus statt manueller Seiten-Freigabe.

## Auslöser

09.10.2026, Mark: ein Spieler legt einen erfolgreichen Wissenswurf über eine
Pflanze/einen Ort ab — wie zeigt man ihm danach dauerhaft ein Objekt mit
Bild+Beschreibung, ohne dass die SL das manuell in einer Mitteilung
nachschicken muss? Daraus entwickelte sich ein größeres Gesamtkonzept
(Lexikon-Burgermenüpunkt, Favoriten, Spieler-Notizen pro Eintrag,
Nähe-Sortierung) und am Ende die eigentlich zentrale Frage: ab wann sieht
ein Spieler ein Objekt/einen Ort/einen Critter überhaupt, wenn er nur
*indirekt* damit verbunden ist (nie dort gewesen, aber sein PC kennt jemanden,
der dort war)?

## Nebenbefund: SL-Geheim-Knopf bei Spielern sinnlos

`richtext/RichTextEditor.tsx` zeigt den 🔒-„SL-geheim"-Knopf unconditional,
auch wenn ein Spieler ihn in seinen eigenen [[../../api/spielernotizen.md|Spieler-Notizen]]
benutzt — dort sieht die SL die Einträge ohnehin nie, der Knopf versteckt
also nur vor dem Spieler selbst beim nächsten Lesen. Rein kosmetischer Bug,
keine Sicherheitslücke (serverseitige Filterung in `entities/visibility.py`
betrifft Spieler-Notizen gar nicht). Fix: neue optionale Prop an
`RichTextEditor` (z. B. `versteckenErlaubt?: boolean`, Default `true`), von
`SpielerNotizen.tsx` auf `false` gesetzt.

## Kernentscheidung 1: zwei unabhängige Sichtbarkeits-Schichten

Bisher kannte das Projekt nur eine Schicht: `sichtbarkeit`
(GM/ALLE/SPEZIFISCH) auf Beschreibung und Notizen getrennt (siehe
[[neo4j-datenmodell]]). Das reicht nicht mehr, sobald es um *Existenz* vs.
*Wissen* geht — ein Spieler kann wissen, dass ein Ort existiert (steht im
Lexikon), ohne die Details zu kennen (Beschreibung bleibt grau/gesperrt, bis
ein Wissenswurf sie freischaltet).

**Entscheidung (Mark, 09.10.2026):** zwei getrennte Mechanismen, die
zusammenspielen, aber unabhängig bleiben:

1. **Entdeckung** (neu, automatisch, siehe unten) — schaltet nur die
   *Existenz* frei: Name + Bild erscheinen im Lexikon.
2. **`sichtbarkeit`** (bestehend, manuell von der SL gesetzt) — schaltet die
   *Beschreibung* frei, weiterhin über den gewohnten Wissenswurf-Reflex der
   SL ("ich flippe das Feld auf ALLE/SPEZIFISCH").

Ein entdeckter, aber inhaltlich noch `GM`-sichtbarer Eintrag erscheint also
im Lexikon als Kachel mit Name+Bild, aber die Beschreibung bleibt gesperrt
("noch nicht erforscht") bis die SL sie freigibt.

## Kernentscheidung 2: automatische Entdeckung durch Erreichbarkeit

Mark: *"ab wann bekommen die Spieler das Objekt, den Ort, den Critter
überhaupt angezeigt, sobald sie damit mal indirekt verknüpft waren?"* —
konkretes Beispiel-Kette: PC → Party → Event → Ort → NPC-Party → NPC →
MacGuffin-Gegenstand. Das sind 7 Hops.

**Entschieden:**

- **Reichweite:** maximal **7 Hops** ab dem PC (nicht 5 wie der bestehende
  Beziehungsgraph-Endpunkt `graph/routes.py::_neighborhood`, der nur eine
  Anzeige-Verdichtung um einen Fokusknoten ist, keine Berechtigungslogik).
- **Abbruchregel:** die Traversierung stoppt hart an jeder `VERBINDUNG`-Kante
  mit `sichtbarkeit: GM` (bzw. `SPEZIFISCH` ohne diesen PC) und an jedem noch
  nicht sichtbaren/entdeckten Knoten — auch wenn das innerhalb der 7 Hops
  läge. Ein SL-Geheimnis blockiert die Kette komplett, es "leakt" nichts
  dahinter.
- **Pro PC, nicht campagnenweit:** da Partys sich aufteilen (siehe
  [[party-feature]]), hat jeder PC seine eigene Entdeckungs-Historie. Zwei
  Spieler können unterschiedliche Lexikon-Stände haben.
- **Speicherung:** dauerhafte Kante, nicht live pro Request berechnet
  (gleiches Muster wie [[ereignisprotokoll]] — Hook aktualisiert sie bei
  jeder relevanten Änderung, nicht Live-BFS bei jedem Laden):

  ```cypher
  (:Person {istPC: true})-[:ENTDECKT {seit: datetime}]->(:Ort|Event|Fraktion|Person|Gewaechs|Gegenstand)
  ```

- **Traversal-Regeln:** Strukturkanten sind immer durchlässig (`MITGLIED_VON`,
  `BEFINDET_SICH_AN`, `LEBT_IN`, `BETREIBT`/`VERKAUFT`) — sie tragen selbst
  keine eigene Sichtbarkeit. `VERBINDUNG`-Kanten nur durchlässig, wenn für
  diesen PC laut `entities/visibility.py::is_visible_to` sichtbar.
- **Hook-Auslöser:** Party-Aufenthaltsortwechsel (`BEFINDET_SICH_AN` neu
  gesetzt), neue/geänderte `VERBINDUNG`, `LEBT_IN`-Hinzufügen, Mitgliedschaft
  (`MITGLIED_VON`) ändert sich — jeweils Neuberechnung der Entdeckungs-Kanten
  **ausgehend von den betroffenen PCs**, nicht ein globaler Neulauf.

## Kernentscheidung 3: MacGuffin-Objekte (`storyRelevant`)

Nicht jeder Gegenstand gehört ins Lexikon — eine 08/15-Pistole nicht, das
Beta-Isotop oder die KI-Kristalle schon. Bestehendes Feld
`Gegenstand.zeigeInGraph` (bisher nur „im Beziehungsgraph anzeigen",
`items/schemas.py`/`traits/CharacterSheetPanel.tsx`) wird umgewidmet:

- **Umbenennen zu `storyRelevant`** (Backend-Feld + Frontend-Label „Story
  relevant" statt „Im Beziehungsgraph anzeigen"). Die bisherige
  Graph-Anzeige-Funktion bleibt erhalten — ein story-relevanter Gegenstand
  taucht weiterhin im Cytoscape-Graphen auf (`graph/repository.py` Query
  bleibt unverändert, nur der Feldname wechselt).
- **Gleiche Entdeckungs-Kette wie Orte/Critter**, kein Sonderpfad: ein
  `storyRelevant`-Gegenstand erscheint im Lexikon erst, wenn er über die
  `ENTDECKT`-Kette erreichbar ist (z. B. weil er an einem entdeckten NPC
  oder Ort hängt), nicht automatisch sobald die SL ihn anlegt.
- Gegenstands-`sichtbarkeit` (bestehend) bleibt wie gehabt die Schicht für
  die Beschreibung — exakt dasselbe Zwei-Schichten-Modell wie bei
  Ort/Critter/Gewächs.

## Burgermenü-Struktur (Spieleransicht)

Neuer Bereich „Lexikon" ersetzt den bisherigen schlichten `orte`-Tab in
`players/SpielerAnsicht.tsx` (der zeigt aktuell nur eine flache Karten-Liste
ohne Bild/Kategorien). Unterkategorien als Reiter, analog zum bestehenden
Kachelraster-Muster aus [[ingame-wiki-feature]]s Schwester-Feature
`entities/FloraFaunaUebersicht.tsx`:

- **Welt** (entdeckte Orte + Events)
- **Fauna** (entdeckte Critter)
- **Flora** (entdeckte Gewächse)
- **Objekte** (entdeckte `storyRelevant`-Gegenstände)

Jede Kachel öffnet ein Detail-Popup (Bild + Beschreibung, gesperrt-Hinweis
falls `sichtbarkeit` noch `GM`) im bestehenden Commlink-Popup-Stil — nie
Inline oder natives Dialog-Element.

### Sortierung

- **Default: „In meiner Nähe"** — Critter/Gewächse/Objekte, die über
  `LEBT_IN`/Besitz-Kanten am aktuellen Party-Aufenthaltsort hängen, zuerst;
  danach Einträge an direkt verbundenen Orten (`VERBINDUNG`); Rest
  alphabetisch als Fallback.
- Alphabetisch, Suche (Name/Art), Favoriten-Ansicht als weitere Reiter/Filter.

### Favoriten

Neue Kante `(:Person {istPC: true})-[:FAVORISIERT]->(:Ort|Event|Fraktion|Person|Gewaechs|Gegenstand)`,
rein spielerseitig gesetzt/entfernt, keine SL-Sicht nötig.

## Kernentscheidung 4: Spieler-Notizen pro Lexikon-Eintrag

Bestehendes [[../../api/spielernotizen.md|SpielerNotiz]] ist aktuell ein
freier Schmierzettel ohne Objektbezug. Erweiterung um ein optionales
Bezugs-Paar:

```
SpielerNotiz { ..., bezugTyp: "Ort"|"Event"|"Fraktion"|"Person"|"Gewaechs"|"Gegenstand" | null,
                    bezugId: string | null }
```

- **Genau eine laufende Notiz pro Objekt und Spieler** (wird beim ersten
  Tippen im Lexikon-Detail-Popup automatisch angelegt, danach wie die
  bestehenden Notizen autosave-editiert) — keine Mehrfach-Notizen pro
  Objekt, das hält es einfach.
- Die bestehende „Notizen"-Seite (`spielernotizen/SpielerNotizen.tsx`) zeigt
  neu zwei Gruppen: **Objekt-Notizen** (mit Objektnamen, Klick springt direkt
  ins Lexikon-Detail-Popup zum zugehörigen Eintrag, dort als eigener
  Unterpunkt "Meine Notizen" sichtbar) und die bisherigen freien Notizen
  unverändert darunter.

## Offene technische Reihenfolge (noch nicht entschieden, beim Bauen klären)

- Reihenfolge der Bausteine: vermutlich zuerst `ENTDECKT`-Datenmodell +
  Hook-Grundgerüst (kleinster, isoliert testbarer Baustein), dann
  `storyRelevant`-Umbenennung, dann Frontend-Lexikon, dann Favoriten +
  Notizen-Bezug zuletzt (hängen an den vorherigen Schichten).
- Migration für Bestandsdaten: bestehende Partys/PCs haben noch keine
  `ENTDECKT`-Kanten — braucht einen einmaligen Nachlauf-Job, der die
  Hook-Logik einmal über den aktuellen Stand laufen lässt, sonst zeigt das
  Lexikon für laufende Kampagnen erstmal gähnende Leere.

## Siehe auch

- [[ingame-wiki-feature]] — Schwester-Feature, manuelle SL-Seiten statt
  automatischer Entdeckung
- [[neo4j-datenmodell]] — `VERBINDUNG`, `LEBT_IN`, `MITGLIED_VON`,
  `BEFINDET_SICH_AN`, neu: `ENTDECKT`/`FAVORISIERT`
- [[party-feature]] — Aufenthaltsort/Mitgliedschaft als Grundlage der
  Traversierung
- [[ereignisprotokoll]] — Hook-Muster, das `ENTDECKT` übernimmt
- [[../../../CLAUDE.md]] — laufender Projektstand
