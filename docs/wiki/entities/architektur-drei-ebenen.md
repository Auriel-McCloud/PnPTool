---
title: Architektur — Drei Ebenen (Regelsystem → Kampagne → Ideenschmiede)
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [regelsystem-kampagne-ideenschmiede, backend, datenmodell]
sources: [../../../CLAUDE.md]
status: aktuell
---

# Architektur — Drei Ebenen

**Fertig** laut `CLAUDE.md` (12.09.2026 Backend, gleicher Tag Frontend).

## Die drei Ebenen

```
REGELSYSTEM (:Regelsystem)          z.B. "NeotopiA", "D&D 5e", "WoD"
  ├── Regel-Wiki (Kampf, Magie, Proben...)
  ├── Rassen, Sphären, Hexkraft-Stufen
  ├── Preislisten, Standard-Ausrüstung
  └── PC-Vorlagen (vorgefertigte Charaktere)
         │ :NUTZT_REGELSYSTEM
         ▼
KAMPAGNE (:Campaign)                z.B. "Berlin 2087"
  ├── Story-Wiki (istEntwurf: false) → NPCs, Orte, Events dieser Kampagne
  └── Ideenschmiede (istEntwurf: true) → WikiSeiten, NPCs, Orte, Gegenstände
```

- **Regelsystem:** angelegt durch SL oder KI-Import; enthält alles, was für
  **alle** Kampagnen dieses Systems gilt. Mehrere Kampagnen können dasselbe
  Regelsystem nutzen. NeotopiA wird beim Start automatisch angelegt.
- **Kampagne:** verknüpft mit genau einem Regelsystem via
  `(:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)`.
- **Ideenschmiede (pro Kampagne):** Flag `istEntwurf: true` auf WikiSeite,
  Person, Ort, Gegenstand. KI-generierte Inhalte landen hier zur Prüfung.
  „In Kampagne verschieben" = reines Flag-Toggle, **keine Datenmigration**.

## Frontend

Eigener Tab „Schmiede" (🔧) in der Commlink-Shell (siehe
[[ui-konzept-commlink]]): zeigt alle Entwürfe mit Typ-Filter, „Neue Idee" legt
direkt Entwürfe an, „✓ Übernehmen" verschiebt (Flag-Toggle), „✗" löscht den
Entwurf. Backend-Filter für `istEntwurf` in `_aufbereiten()`, eigene
`/entwuerfe`-Route, Wiki-Baum filtert Entwürfe automatisch raus.

## Ein realer Bug aus dem Umbau

**Charakterblatt-Ladefehler (15.09.2026):** nach dem Umbau auf
`(:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)` lieferte `get_campaign` kein
`ruleset`-Feld mehr → `get_bogen` und `regeln/_ruleset` crashten mit
`KeyError: 'ruleset'`. Fix: `get_campaign` liefert jetzt zusätzlich `ruleset`
als Klein-Slug zurück (`toLower(regelsystem-Name)`).

## Offen

- **PC-Vorlagen im Regelsystem** — Spieler soll zwischen „selbst erstellen" und
  „Vorlage wählen" wählen können (Vorlage aus dem Regelsystem kopiert, Spieler
  passt an). **Status: geplant, nicht umgesetzt** (Phase 2).
- KI-Import in die Ideenschmiede — siehe [[ki-integration]].

## Siehe auch

- [[neo4j-datenmodell]] — die zugrundeliegenden Beziehungstypen
- [[ki-integration]] — Ideenschmiede + Gemini
- [[ingame-wiki-feature]] — Story-Wiki vs. dieses Meta-Wiki (nicht verwechseln!)
