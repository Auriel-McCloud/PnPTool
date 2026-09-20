---
title: Regelwerk — Excel (Version 1) vs. aktueller Stand im Tool
created: 2026-09-18
updated: 2026-09-18
type: vergleich
tags: [versionsgeschichte, wuerfelsystem, attribute, magie, neuroweaving, kampf, ruestung, cyberware]
sources: [../../reference/Neotopia_Regeln.md, ../../reference/Neotopia_Charaktererschaffung.md, ../../regeln-neotopia.md, ../../../CLAUDE.md, ../../ENTWICKLUNGSHISTORIE.md]
status: aktuell
---

# Regelwerk: Excel (Version 1) vs. aktueller Stand

**Die wichtigste Seite für die Frage "was hat sich seit dem Excel geändert".**
`Neotopia.xlsx` (zuletzt bearbeitet 29.08.2026, siehe [[../../reference/Neotopia_Regeln.md]]
für die vollständige Transkription) ist der Regelstand **kurz vor bzw. bei
Projektstart**. PnPTool begann am 28.08.2026. Seither wurde das Regelwerk beim
Umsetzen an etlichen Stellen bewusst weiterentwickelt — **das Tool, nicht das
Excel, gilt jetzt**, aber das Excel wurde absichtlich nicht nachgezogen (eigene
Datenquelle, siehe [[../../reference/INDEX.md]]).

## Überblick: was sich geändert hat

| Regel | Excel (Version 1) | Aktuell im Tool | Seit wann |
|---|---|---|---|
| Magiewert-Name | „Arete" | „Hexkraft" | 10.09.2026 |
| Technomancer-Name | „Technomancer" | „Neuroweaver" | 10.09.2026 |
| Gesundheit-Formel | 5 + Widerstandskraft | **6** + Widerstandsfähigkeit | 10.09.2026 |
| Neuroweaver-Verteidigung | Willenskraft (Excel Zeile 99) | Fassung + Geistesschärfe | 29.08.2026 (Tag 1!) |
| Rüstung | Flacher Bonus, addiert | Kästchen + Durchlass, nutzt sich ab | 10.09.2026 |
| Chrom-Willenskraftverlust-Rundung | Nicht spezifiziert | Rohwerte summieren, erst am Ende runden (Minimum 1) | 31.08.2026 |
| Rassen | Fixe Tabelle im Excel | Baukasten (Katalog + Freigabe je Kampagne), Balance-Formel nachträglich gefunden | 11.09.2026 |
| Erfahrung/Steigern nach Erstellung | Nicht im Excel enthalten | Erfunden, WoD-artige Faktor-Formel | siehe [[../concepts/erfahrung-und-steigern]] |
| Hintergründe (Kontakte, Ressourcen, ...) | Nicht im Excel enthalten | Vorschlag, zum Umbau frei | siehe [[../concepts/charaktererschaffung]] |
| Fahrzeug/Drohnen-Preisformel | Wie im Excel | Wie im Excel, aber **von Mark als fraglich markiert** (Motorrad zu teuer) | 30.08.2026 (Notiz, nicht behoben) |
| Fertigkeitsmaximum | 5 | **6** (gleichgezogen mit Attributmaximum; Sphären bleiben bei 5) | 20.09.2026 |

Jede Zeile hat eine ausführlichere Behandlung auf der jeweiligen Konzeptseite
unter „Entwicklung" — hier nur der schnelle Überblick.

## Warum diese Abweichungen entstanden sind

**Nicht willkürlich** — jede Änderung hat einen dokumentierten Auslöser:

- **Arete → Hexkraft, Technomancer → Neuroweaver**: reine Umbenennungen für
  Konsistenz zwischen Backend und Frontend (die Werte hießen im Code teils
  schon anders als im Excel/UI). Brachte einen echten Bug mit sich, siehe
  [[../entities/neo4j-datenmodell#TraitDef-Umbenennen]].
- **Neuroweaver-Verteidigung**: Willenskraft wird beim NeuroWeaving selbst
  verbraucht — hätte den Neuroweaver nach jeder eigenen Aktion verwundbarer
  gemacht. Fassung+Geistesschärfe bleibt stabil. Mark hat das laut
  [[../../regeln-neotopia.md]] bereits am **29.08.2026**, also praktisch am
  ersten Projekttag, geändert — das Excel war zu diesem Zeitpunkt schon nicht
  mehr ganz aktuell.
- **Rüstung Kästchen+Durchlass**: Mark wollte, dass Rüstung sich im Kampf
  abnutzt statt konstant zu bleiben. Ausführlichste Regeldiskussion des
  gesamten Projekts, siehe [[../concepts/ruestung-kaestchen-durchlass]].
- **Gesundheit 5→6**: Widerstandsfähigkeit geht bis 6 (Attributmaximum);
  mit Grundwert 6 macht das 12 statt 11 Kästchen als natürliches Maximum.
- **Rassen-Baukasten**: Mark wollte nicht mehr nur die 5 Excel-Rassen fix im
  Code, sondern selbst welche bauen können, mit Kampagnen-Freigabe.
- **Fertigkeitsmaximum 5→6**: Mark fand die Asymmetrie zum Attributmaximum
  (6) unbegründet und wollte Einheitlichkeit. Sphären blieben bewusst bei 5,
  weil ihre Stufen fest definiert sind (5 = „alles").

## Was NICHT geändert wurde (Excel gilt weiterhin 1:1)

- Würfelsystem (10-seitig, 1-5 Fehlschlag, 6-10 Erfolg, Kritisch/Patzer) —
  siehe [[../concepts/wuerfelsystem]]
- Attribute (9 Werte in 3 Spalten), Fertigkeiten (30 Stück, aber Maximum seit
  20.09.2026 auf 6 angehoben, siehe oben) — siehe
  [[../concepts/attribute-und-fertigkeiten]]
- Freebee-Kosten, Fertigkeitspakete, Startkapital 10.000¥ — siehe
  [[../concepts/charaktererschaffung]]
- Sphären-Definitionen und -Stufen — siehe [[../concepts/magie-hexkraft]]
- Cyber/Bioware-Grundformel (Preis→Willenskraftverlust-Tabelle) — siehe
  [[../concepts/cyberware-bioware]]

## Offene Fragen, die weder Excel noch Tool klären

Aus `docs/regeln-neotopia.md` „Offen / noch zu klären" (Stand der Doku, nicht
notwendigerweise noch aktuell — bei nächstem Ingest prüfen):

- Rüstungsmaxima je Zone (Kopf 2, Torso 4, Beine 2 laut Blatt) — feste Grenze
  oder nur Vorlage?
- Sphären beim Freebee-Kauf: Zeile 39 des Excels nennt nur „Attribut / Hexkraft
  NeuroWeaving 5", Zeile 27 stellt Sphären aber zu den Fertigkeiten. Umgesetzt
  ist vorerst der Fertigkeitspreis.
- Hintergründe und Erfahrungspreise bleiben erfunden statt belegt (siehe oben).

## Siehe auch

- [[../../../CLAUDE.md]] — laufender Projektstand, hier NICHT dupliziert
- [[veraltete-docs-vs-code]] — ein zweiter, ungeklärter Widerspruch (API-Docs vs. Code)
- [[../entities/architektur-drei-ebenen]] — wie Regelsystem/Kampagne heute strukturell getrennt sind
