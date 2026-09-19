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
- **Kästchen-Overflow gelöst** (`frontend/src/traits/Kaestchen.tsx`): ab 10
  Kästchen kippt die Leiste in eine Puffer+Enden-Form — schmale Zellen mit
  Füllhöhe (⅓/⅔/voll für Schlag/Tödlich/Unheilbar) für den vorderen Teil,
  die letzten 5 Kästchen bleiben groß mit den gewohnten Zeichen. **18.09.2026
  drei Fehler behoben** (Mark hat die Implementierung selbst am Spieltisch
  geprüft und für nicht ganz stimmig befunden):
  - Füllrichtung war zwischen Gesundheit (Puffer zuerst) und Willenskraft/
    I.C.E. (Enden zuerst) uneinheitlich — jetzt beide von vorne (Puffer
    zuerst), wie von Mark gewünscht: "die Schmalen zuerst, die Großen erst
    wenn's kritisch wird"
  - Die Gesundheitsleiste im Charakterblatt hatte einen zweiten, direkten
    Schaden-Weg (Zahlenpad im `ZustandFenster`), der die Rüstung komplett
    umging — im Kampfmodus gab es dafür schon den korrekten Weg über
    `RuestungsTreffer`. Der direkte Weg ist jetzt für Gesundheit gesperrt.
  - Ab 11 Kästchen wurde die Willenskraft-Leiste zum reinen Öffnen-Knopf,
    und das dortige Zahlenpad kannte die Willenskraft-Sonderregeln (nur 1
    auf einmal, Pflicht-Rückfrage, Spieler kann nicht heilen) nicht — ein
    Charakter mit hoher Willenskraft bekam die Rückfrage nie, einer mit
    niedriger schon. Jetzt läuft auch die Vollansicht über den echten
    Klick-Handler mit Rückfrage.
  - **Nachtrag (von Mark selbst am System gefunden):** der separate
    „⚡ Treffer eintragen"-Knopf (Rüstungsrechnung, `RuestungsTreffer.tsx`)
    hatte noch ein rohes `<input type="number">` für die Stärke — eigene
    Optik, Systemtastatur statt Zahlenpad. Jetzt gemeinsame Komponente
    `frontend/src/shell/Zahlenpad.tsx`, aus `ZustandFenster` extrahiert und
    in beiden Fenstern verwendet.
  - **Zweiter Nachtrag:** die Zahlenpad-Vorgabe „1" bei der Stärke wurde
    beim ersten Tastendruck angehängt statt ersetzt — „4" getippt ergab
    „14". Fix: der erste Tastendruck ersetzt die Vorgabe komplett, danach
    verhält sich das Pad wie überall sonst.

## Widerspruch mit veralteten Docs

`docs/api/personen.md` und `docs/api/kampf.md` beschreiben noch ein generisches
6-Attribut-System (Stärke/Geschick/Ausdauer/Charisma/Intelligenz/Willenskraft,
1–5). Das ist **nicht** das tatsächliche System — siehe
[[../comparisons/veraltete-docs-vs-code]].

## Siehe auch

- [[charaktererschaffung]] — wie Attribute/Fertigkeiten bei der Erstellung verteilt werden
- [[rassen]] — Rassenmodifikatoren auf Attribute
- [[erfahrung-und-steigern]] — spätere Steigerung
