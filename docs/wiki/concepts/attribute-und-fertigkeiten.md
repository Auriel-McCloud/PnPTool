---
title: Attribute und Fertigkeiten
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [attribute, fertigkeiten, versionsgeschichte]
sources: [../../reference/Neotopia_Charakterblatt.md, ../../regeln-neotopia.md, ../../../backend/app/traits/]
status: aktuell
---

# Attribute und Fertigkeiten

## Definition

**9 Attribute in 3 Spalten**, Maximum 6:

| Körperlich | Gesellschaftlich | Geistig |
|---|---|---|
| Körperkraft | Charisma | Intelligenz |
| Geschicklichkeit | Manipulation | Geistesschärfe |
| Widerstandsfähigkeit | Fassung | Entschlossenheit |

**30 Fertigkeiten**, Maximum 5, in drei Zehnerspalten (siehe
[[../../reference/Neotopia_Charakterblatt.md]] für die vollständige Liste). Dazu
kommen bei entsprechendem Weg: **Sphären** (siehe [[magie-hexkraft]]) oder
**NeuroWeaving-Fertigkeiten** (siehe [[neuroweaving-decking]]) — beide zählen
technisch als Fertigkeit, werden aber meist ohne Attribut gewürfelt.

Tooltip-Texte für alle Attribute/Fertigkeiten liegen fertig ausformuliert in
`docs/reference/Master/` (siehe [[../../reference/INDEX.md]]).

## Abgeleitete Werte

- **Gesundheit = 6 + Widerstandsfähigkeit** (siehe „Entwicklung" unten — Excel
  sagt noch 5)
- **Willenskraft = Entschlossenheit + Fassung** — siehe [[willenskraft]]
- **Initiative = Geistesschärfe + Geschicklichkeit + Cyberware-Modifikator** —
  nur während eines laufenden Kampfs auf dem Blatt sichtbar (siehe
  [[kampf-und-initiative]])

Gesundheit, I.C.E., Hexkraft/NeuroWeaving und Willenskraft sind auf dem Blatt
**Kästchenreihen** (Fünfergruppen), keine reinen Punktwerte — der abgeleitete
Wert bestimmt, wie viele Kästchen zählen.

## Schadensarten (auf der Gesundheitsleiste)

Drei Arten, WoD-Stil, in derselben Kästchenreihe:

| Zeichen | Art | Heilt |
|---|---|---|
| `/` | Schlagschaden | schnell (Widerstandsfähigkeit über Nacht) |
| `X` | Tödlicher Schaden | langsam (½ Widerstandsfähigkeit, nur behandelt) |
| durchgestrichenes `X` | Unheilbarer Schaden | sehr langsam ((7−Widerstandsfähigkeit) Wochen, nur behandelt) |

Schwererer Schaden steht links; im Tool schaltet ein Klick durch
unbeschädigt → `/` → `X` → durchgestrichen → frei.

## Entwicklung

- **10.09.2026 — Gesundheit 5→6:** Widerstandsfähigkeit geht bis 6 (Maximum);
  mit Grundwert 6 macht das **12 statt 11 Kästchen** als natürliches Maximum
  (mit Chrom bis 18 statt 17). Keine Datenmigration nötig — der Wert ist
  abgeleitet, jeder Charakter hat einfach automatisch ein Kästchen mehr.
- **10.09.2026 — Rüstung als vierte Zustandsleiste** eingeführt, Reihenfolge auf
  dem Blatt jetzt Gesundheit → Willenskraft → Rüstung → I.C.E. Siehe
  [[ruestung-kaestchen-durchlass]].
- **Kästchen-Overflow noch ungelöst:** Bei Werten über 10 (durch Chrom o. Ä.)
  ist die Darstellung (>10 Kästchen) noch offen — siehe `CLAUDE.md` Punkt 9.
  Soll für Gesundheit, Willenskraft UND Rüstung gleich gelöst werden, muss
  „cyberpunkig" aussehen (keine Herzen). Status: **offen**.

## Widerspruch mit veralteten Docs

`docs/api/personen.md` und `docs/api/kampf.md` beschreiben noch ein generisches
6-Attribut-System (Stärke/Geschick/Ausdauer/Charisma/Intelligenz/Willenskraft,
1–5). Das ist **nicht** das tatsächliche System — siehe
[[../comparisons/veraltete-docs-vs-code]].

## Siehe auch

- [[charaktererschaffung]] — wie Attribute/Fertigkeiten bei der Erstellung verteilt werden
- [[rassen]] — Rassenmodifikatoren auf Attribute
- [[erfahrung-und-steigern]] — spätere Steigerung
