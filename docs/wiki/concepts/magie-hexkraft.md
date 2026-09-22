---
title: Magie — Hexkraft und Sphären
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [magie, versionsgeschichte]
sources: [../../reference/Neotopia_Regeln.md, ../../regeln-neotopia.md, ../../../backend/app/traits/seed.py]
status: aktuell
---

# Magie — Hexkraft und Sphären

## Definition

**Hexkraft** ist der Magiewert (im Excel noch „Arete" genannt, siehe
„Entwicklung"). Ein **kontrollierter** Zauber würfelt nur den Hexkraft-Wert.

**Wilde Magie:** Bonuswürfel bis zur Höhe der Willenskraft dazunehmen; vorher
muss ein **Zielwert** festgelegt werden — wird er unterschritten, ist die Probe
gescheitert. Nach einem gelungenen wilden Zauber: Willenskraftwurf gegen die
Erfolgszahl (entfällt bei exakter Übereinstimmung mit dem Zielwert); die
Differenz wird als Schaden abgezogen. Kritische Treffer zählen beim Zielwert
**nicht** als zusätzliche Erfolge. Bewusst **kein Pool-Deckel** — anders als
beim NeuroWeaving-Gegenstück "Overclock" (siehe [[neuroweaving-decking]]),
weil Hexkraft allein gewürfelt wird und nicht mit einem zweiten Wert
kombiniert.

**Sphären beschreiben, was möglich ist — sie geben keine Bonuswürfel** (anders
als NeuroWeaving-Fertigkeiten, siehe [[neuroweaving-decking]]). Stufen:
1 wahrnehmbar · 2 bis ~50cm³ · 3 bis ~4m³ · 4 bis Hausgröße · 5 alles.

Neun Sphären: Korrespondenz, Entropie, Kräfte (*Schaden automatisch +1*), Leben,
Materie, Gedanken, Ursprung, Geister, Zeit. Volltexte in
`docs/reference/Sphären/` (M20-Rohtext) und `docs/reference/Master/`
(fertige NeotopiA-Tooltips).

## Der exklusive Weg

**„Hexkraft != NeuroWeaving"** steht wörtlich so im Excel — die beiden
schließen sich aus. **Entschieden:** eigenes Feld `weg` am Charakter, nicht aus
`Hexkraft > 0` abgeleitet — sonst wäre ein frisch erstellter Magier mit
Hexkraft 0 fälschlich kein Magier.

## Entwicklung

- **10.09.2026 — Arete → Hexkraft umbenannt.** Reine Namensänderung für
  Konsistenz (Backend hieß schon Hexkraft, Frontend noch Arete), brachte aber
  einen echten Doppelgänger-Bug mit sich — siehe
  [[../entities/neo4j-datenmodell#TraitDef-Umbenennen]] für die technische
  Ursache (TraitDef-Kennung enthält den Namen).

## Siehe auch

- [[neuroweaving-decking]] — der Gegenweg, gleiche Grundregeln bei Willenskraft
- [[willenskraft]] — Ressource für Wilde Magie
- [[../comparisons/regelwerk-excel-vs-aktuell]] — Umbenennungs-Historie im Kontext
