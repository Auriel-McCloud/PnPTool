---
title: Veraltete API-Docs vs. tatsächlicher Code
created: 2026-09-18
updated: 2026-09-18
type: vergleich
tags: [widerspruch, offen, attribute, cyberware]
sources: [../../api/personen.md, ../../api/entitaeten.md, ../../../backend/app/traits/erstellung.py, ../../regeln-neotopia.md]
status: offen
---

# Veraltete API-Docs vs. tatsächlicher Code

**Für Mark zur Prüfung markiert — kein Blocker, aber eine echte Diskrepanz, die
bei der nächsten Bearbeitung von `docs/api/personen.md` bzw. `docs/api/entitaeten.md`
aufgelöst werden sollte.**

## Der Fund

`docs/api/personen.md` (Abschnitt „Attribut-System") beschreibt ein **anderes**
Attributsystem als das, was laut `docs/regeln-neotopia.md` und dem restlichen
Projekt tatsächlich gilt:

| | `docs/api/personen.md` (Stand: undatiert) | Tatsächliches NeotopiA-System |
|---|---|---|
| Attribute | Stärke, Geschick, Ausdauer, Charisma, Intelligenz, **Willenskraft** (6, generisch) | Körperkraft, Geschicklichkeit, Widerstandsfähigkeit, Charisma, Manipulation, Fassung, Intelligenz, Geistesschärfe, Entschlossenheit (9, drei Spalten) |
| Skala | 1–5 | 1–6 (siehe [[../concepts/attribute-und-fertigkeiten]]) |
| Ressource für Cyberware | **Essenz** (startet bei 6.0, Cyberpsychose bei 0) | **Willenskraftverlust** (siehe [[../concepts/cyberware-bioware]]) — komplett anderes Konzept |
| Beispiel-JSON | `essenzKosten: 0.5` | Existiert im echten Datenmodell nicht |

`docs/api/entitaeten.md` hat ebenfalls Beispiel-Strukturen (`gegenstandTyp`,
`eigenschaften: { schaden: "3W6" }`, `(:Haendler)-[:VERKAUFT]`), die nirgends im
tatsächlichen Backend (`backend/app/items/`) vorkommen — kein Würfelnotation-Feld,
kein `Haendler`-Node-Typ existiert laut Code-Suche.

## Wahrscheinliche Erklärung

Diese beiden Dateien wirken wie **früh geschriebene Platzhalter-Docs** (vielleicht
aus einer generischen Cyberpunk-RPG-Vorlage oder einem ersten Entwurf vor der
Festlegung auf NeotopiAs tatsächliches WoD-Attributsystem), die nie an den
späteren, echten Regelstand angepasst wurden — während andere `docs/api/*.md`
(`ruestung.md`, `rassen.md`, `kampf.md`) sichtlich mit dem Code mitgewachsen sind
und genaue Feldnamen wie `ruestungKaestchenMax` oder `schadenSchlag` verwenden.

`docs/api/kampf.md` selbst zeigt ebenfalls Reste des generischen Systems
(`"staerke": 3, "geschick": 4, ...` im Beispiel-JSON) statt der neun tatsächlichen
NeotopiA-Attribute — dasselbe Muster.

## Was zu tun wäre (nicht von diesem Wiki entschieden)

- `docs/api/personen.md`: Attribut-Tabelle und Cyberware-Beispiele auf die
  echten 9 Attribute und das Willenskraftverlust-System umstellen
- `docs/api/entitaeten.md`: Gegenstand-Beispiele an `backend/app/items/schemas.py`
  angleichen (Rüstung, Waffenschaden-Bonus, Cyberware-Felder statt generischem
  `eigenschaften`-Objekt)
- `docs/api/kampf.md`: Beispiel-JSON der Attribute korrigieren

## Siehe auch

- [[regelwerk-excel-vs-aktuell]] — der andere große Diskrepanz-Fund, aber zeitlich
  erklärt (Excel vs. Weiterentwicklung); dieser hier ist eher ein Doku-Rückstand
- [[../concepts/attribute-und-fertigkeiten]] — das tatsächliche Attributsystem
- [[../concepts/cyberware-bioware]] — das tatsächliche Willenskraftverlust-System
