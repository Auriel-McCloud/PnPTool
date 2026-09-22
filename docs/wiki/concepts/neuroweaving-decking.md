---
title: NeuroWeaving und Decking
created: 2026-09-18
updated: 2026-09-22
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
  begrenzen). **Sechs Fertigkeiten** (seit 22.09.2026, siehe „Entwicklung"):
  Brute Force, Schleichen, Daten Verarbeiten, Kompilieren, Electronic Warfare,
  Matrix-Navigation.
- Ein Neuroweaver darf NeuroWeaving-Fertigkeiten auch nutzen, in denen er
  keine Punkte hat.

**Cyberwall/I.C.E.** wird für Decker (Hacker) mit Geräten benötigt. Decking
nutzt i. d. R. Intelligenz + Matrix zum Hacken; Cyberdeck-Fertigkeiten
(B/S/D/K/EW/N — sechs Werte, seit 22.09.2026) geben Bonuswürfel je Aktion.
**KI nutzt dieselben sechs Fertigkeiten wie ein Neuroweaver** — kein eigenes
Gerät nötig, dieselbe Matrix-Präsenz wie beim NeuroWeaving.

## Die sechs Fertigkeiten im Detail

| Fertigkeit | Was sie tut |
|---|---|
| Brute Force | Aggressiver Frontalangriff auf Sicherheitssysteme — laut, riskant, effektiv gegen stark gepanzerte Hosts |
| Schleichen | Unbemerktes Eindringen, kaum Spuren, umgeht ICE |
| Daten Verarbeiten | Große Datenmengen in Echtzeit durchsuchen/filtern/auswerten |
| Kompilieren | Spontan eigene Programme/Effekte erschaffen |
| **Electronic Warfare** | „Rauschen" — sinnbildlich eine Rauchgranate im Netz. **Rein tarnend**, senkt NICHT gegnerische Verteidigung, sondern erschwert Ortung/Erkennung der eigenen Gruppe. Eine Probe bestimmt Radius UND Dauer zugleich; Dauer ist kontextabhängig (Szene bis Sekunden), im Kampf immer nur ein einmaliger Soforteffekt. Auffälliger als Schleichen. |
| **Matrix-Navigation** | Dinge im Netz aufspüren, auch Verstecktes. Erfolgsstufen bestimmen die Tiefe des Fundes — genug Erfolge finden sogar Backdoors in Host-Architekturen. Bewusst getrennt von Schleichen: Navigation findet den Weg, Schleichen hält unentdeckt, keine Überschneidung. |

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
- **22.09.2026 — Erweiterung auf 6 Skills umgesetzt** (`CLAUDE.md` Punkt 9).
  Vorschlag vom 20.09.2026 (Electronic Warfare + Matrix-Navigation) mit Mark
  durchgesprochen und in den Katalog übernommen: `backend/app/traits/seed.py`
  (Katalogeinträge + Beschreibungen), Cyberdeck-Werte in `items/schemas.py`/
  `repository.py`/`routes.py` (`deckElectronicWarfare`/`deckMatrixNavigation`,
  analog zu B/S/D/K). Frontend braucht keine Änderung — Probe/Kampfkarte/
  LevelUp iterieren generisch über Katalog/`deckBoni`, keine hartkodierten
  Skill-Namen. Gilt für NeuroWeaver, Decker UND KI. **Cyberdecks als echte
  Gegenstände im System (statt nur Referenztabelle im Wiki) bleibt bewusst
  offen** — Mark macht das separat, nicht Teil dieser Erweiterung.

## Siehe auch

- [[magie-hexkraft]] — der exklusive Gegenweg
- [[willenskraft]] — gemeinsame Ressource beider Wege
- [[../entities/neo4j-datenmodell]] — TraitDef-Umbenennungs-Fallstrick im Detail
