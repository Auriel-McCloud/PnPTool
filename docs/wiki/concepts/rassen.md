---
title: Rassen — Baukasten und Balance
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [rassen, attribute, versionsgeschichte, widerspruch]
sources: [../../api/rassen.md, ../../reference/Neotopia_Charaktererschaffung.md, ../../../CLAUDE.md]
status: aktuell
---

# Rassen — Baukasten und Balance

## Definition (Excel-Ursprung)

5 Rassen mit Startmaximum + freien Punkten je Attributspalte:

| Rasse | Frei | Startmax | Anpassungen |
|---|---|---|---|
| Mensch | 7/5/3 | 4/4/4 | — |
| Ork | 6/5/3 | 3/5/4 | Intelligenz −1, Körperkraft +1 |
| Elf | 5/5/3 | 3/5/5 | Widerstandsfähigkeit −1, Charisma +1, Geschicklichkeit +1 |
| Zwerg | 5/5/3 | 3/5/5 | Charisma −1, Widerstandsfähigkeit +1, Fassung +1 |
| Troll | 5/4/3 | 6/5/3 | Körperkraft +2, Widerstandsfähigkeit +1, Geistesschärfe −1, Geschicklichkeit −1 |

## Entwicklung: vom Fixkatalog zum Baukasten (11.09.2026)

**Vorher:** die 5 Rassen lagen fix im Code/Excel.

**11.09.2026 — Rassen-Baukasten eingeführt** (Marks Vorgabe: „es sollten nicht
automatisch alle zur Verfügung stehen, sondern nur ausgewählte"):

- **Zwei Ebenen:** Katalog global (gehört zum Regelwerk), Freigabe je Kampagne
  über `(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`. Nur freigegebene Rassen
  erscheinen in der Charaktererstellung. Neu gebaute Rassen sind **absichtlich
  noch nicht freigegeben** — Aufnahme ins Regelwerk und Zulassung in einer
  konkreten Runde sind zwei getrennte Entscheidungen.
- **Balance-Regel gefunden, nicht erfunden:** beim Nachrechnen der 5
  gewachsenen Rassen kam heraus, dass sie exakt derselben (nie aufgeschriebenen)
  Formel folgen:
  1. Freie Punkte + Σ positive Modifikatoren = **15**
  2. Nachteile = aufgerundet die **Hälfte** der Vorteile (keine eigene Währung —
     sonst liesse sich Vor- gegen Nachteil frei tauschen)

  | Rasse | Freie Punkte | Σ Vorteile | Summe | Σ Nachteile |
  |---|---|---|---|---|
  | Mensch | 15 | 0 | 15 | 0 |
  | Ork | 14 | +1 | 15 | 1 |
  | Elf | 13 | +2 | 15 | 1 |
  | Zwerg | 13 | +2 | 15 | 1 |
  | Troll | 12 | +3 | 15 | 2 |

  Test: `backend/tests/test_rassen_balance.py`. **Baukasten warnt, blockiert
  nicht** — ein übermächtiges NPC-Volk bleibt bewusst möglich.
- **Zwei Deckel, vorher verwechselt (Bug bis 11.09.2026):**

  | | Formel | Gilt |
  |---|---|---|
  | `startmaxima` | 4 + Modifikator | nur bei der Erstellung |
  | `lebensmaxima` | Katalogmaximum (6) + Modifikator | dauerhaft |

  Vorher wurde `startmaxima` fälschlich als Dauerwert benutzt — ein Troll war
  nach der Erstellung bei Körperkraft für immer auf 4 gefangen, statt auf 8
  zu kommen. Fix zog 12 Attribute rückwirkend nach.
- **Umbenennen ist sicher:** Rassen-Kennung ist eine UUID **ohne** den Namen —
  bewusste Lehre aus dem Arete/Hexkraft-Doppelgänger-Bug (siehe
  [[../entities/neo4j-datenmodell]]). `Person.rasse` hält weiterhin den Namen
  als Text; Umbenennen im Baukasten zieht ihn auf alle betroffenen Charaktere
  nach. Beim Löschen behalten bestehende Charaktere ihren Rassennamen als
  reinen Text.

## Was der Baukasten nicht kann

**Nur Attribute** (Marks Vorgabe: „dabei geht es vor allem nur um die
Attribute"). Fertigkeitsboni oder Sonderfähigkeiten gibt es nicht — sie liessen
sich mit der 15er-Formel auch nicht mehr nachrechnen. **Status: entschieden,
nicht umgesetzt** falls gewünscht — bräuchte zuerst eine erweiterte
Balance-Formel.

## Siehe auch

- [[../entities/rassen-baukasten-feature]] — die UI/Backend-Umsetzung im Detail
- [[attribute-und-fertigkeiten]] — worauf sich die Modifikatoren auswirken
- [[charaktererschaffung]] — wo die Rassenwahl einsortiert ist
