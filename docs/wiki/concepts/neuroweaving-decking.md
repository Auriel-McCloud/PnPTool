---
title: NeuroWeaving und Decking
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [neuroweaving, versionsgeschichte, widerspruch]
sources: [../../reference/Neotopia_Regeln.md, ../../regeln-neotopia.md, ../../../backend/app/traits/seed.py]
status: aktuell
---

# NeuroWeaving und Decking

## Definition

Der Gegenweg zu Hexkraft (siehe [[magie-hexkraft]] — „Hexkraft != NeuroWeaving",
schließt sich aus). Gleiche Grundregeln wie Hexkraft/Arete beim
Willenskrafteinsatz und dessen Folgen, **aber**:

- **NeuroWeaving-Fertigkeiten geben Bonuswürfel** (anders als Sphären, die nur
  begrenzen). Vier Fertigkeiten: Brute Force, Schleichen, Daten Verarbeiten,
  Kompilieren.
- Ein Neuroweaver darf NeuroWeaving-Fertigkeiten auch nutzen, in denen er
  keine Punkte hat.

**Cyberwall/I.C.E.** wird für Decker (Hacker) mit Geräten benötigt. Decking
nutzt i. d. R. Intelligenz + Matrix zum Hacken; Cyberdeck-Fertigkeiten
(B/S/D/K = Brute Force/Schleichen/Daten verarbeiten/Kompilieren) geben
Bonuswürfel je Aktion.

## Matrix-Verteidigung (I.C.E.)

**Wer kein Neuroweaver ist, bezieht I.C.E. vom Commlink.** Ohne Commlink ist
der Wert 0 — dann ist man aber auch offline und nicht angreifbar. Bei mehreren
Geräten gilt der **beste** Wert, nicht die Summe. **Cyberdecks addieren ihren
Bonus obendrauf** (Cywall+1 bis +4) — hier wird summiert, weil Zusatzausrüstung,
kein Zugangsgerät; ein Deck allein nützt aber nichts ohne Commlink.

**Neuroweaver: Fassung + Geistesschärfe** — siehe „Entwicklung", weicht bewusst
vom Excel ab.

## Entwicklung

- **29.08.2026 (Tag 1 des Projekts!) — Neuroweaver-Verteidigung geändert.**
  Excel Zeile 99 sagt „Willenskraft". Mark hat das noch am ersten Projekttag
  auf Fassung+Geistesschärfe umgestellt: die Willenskraft wird beim NeuroWeaving
  selbst verbraucht — dieselbe Größe als Verteidigung hätte den Neuroweaver
  nach jeder eigenen Aktion verwundbarer gemacht. **Das Excel ist an dieser
  Stelle nie nachgezogen worden** und bleibt es auch bewusst (siehe
  [[../../reference/INDEX.md]] — Excel ist reine Rohdaten-Quelle).
- **10.09.2026 — Technomancer → Neuroweaver umbenannt.** Reine Namensänderung,
  gleicher Anlass wie Arete→Hexkraft.
- **Vorschlag, noch nicht entschieden (`CLAUDE.md` Punkt 7):** Erweiterung auf
  6 Skills (zusätzlich Electronic Warfare, Matrix-Navigation) für ein
  ausgewogeneres Schere-Stein-Papier-System. **Status: offen**, nur notiert.

## Siehe auch

- [[magie-hexkraft]] — der exklusive Gegenweg
- [[willenskraft]] — gemeinsame Ressource beider Wege
- [[../entities/neo4j-datenmodell]] — TraitDef-Umbenennungs-Fallstrick im Detail
