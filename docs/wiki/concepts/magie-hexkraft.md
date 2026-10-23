---
title: Magie — Hexkraft und Sphären
created: 2026-09-18
updated: 2026-09-24
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
als NeuroWeaving-Fertigkeiten, siehe [[neuroweaving-decking]]). Stufen (seit
23.10.2026 sechs statt fünf, siehe unten): 1 wahrnehmbar · 2 kleines Objekt ·
3 neue Zwischenstufe je Sphäre · 4 Zimmergröße/komplexere Wirkung ·
5 Hausgröße/starke Wirkung · 6 alles / vollständig beherrschen.

Neun Sphären: Korrespondenz, Entropie, Kräfte (*Schaden automatisch +1*), Leben,
Materie, Gedanken, Ursprung, Geister, Zeit. Volltexte in
`docs/reference/Sphären/` (M20-Rohtext, nicht mehr aktuell) und
`docs/reference/Master/` (fertige NeotopiA-Tooltips, Stand 23.10.2026; dort
heißen die Dateien zu zwei Sphären anders als im Code: `Verstand.md` =
Gedanken, `Geist.md` = Geister).

**23.10.2026 — Sphären auf 6 Punkte erweitert (Mark, im Chat durchgesprochen):**
jede Sphäre bekam eine neue Zwischenstufe, „vollständig beherrschen" rutschte
von Stufe 5 auf Stufe 6 (ersetzt die ältere Entscheidung, Sphären blieben
bewusst bei 5 — siehe CLAUDE.md für den vollen Verlauf). `docs/reference/
Master/*.md`, `backend/app/traits/seed.py` (`TRAIT_LANGBESCHREIBUNGEN`,
`HAERETIKER_LANGBESCHREIBUNGEN`, `NEOTOPIA_TRAITS`) und `erstellung.py`
wurden entsprechend aktualisiert. Geister/Izanami zusätzlich inhaltlich
überarbeitet: „Astralebene"/„Todesgürtel" gibt es in NeotopiA nicht mehr,
ersetzt durch **Schattenwelten** (Totenreich, Götterreich u.a.). Charakterblatt-
Anzeige, Charaktererstellungs-UI und eine Sphären-Spezialisierung (analog zur
Fertigkeiten-Spezialisierung) sind zum Zeitpunkt dieses Eintrags noch offen.

## Der exklusive Weg

**„Hexkraft != NeuroWeaving"** steht wörtlich so im Excel — die beiden
schließen sich aus. **Entschieden:** eigenes Feld `weg` am Charakter, nicht aus
`Hexkraft > 0` abgeleitet — sonst wäre ein frisch erstellter Magier mit
Hexkraft 0 fälschlich kein Magier.

## Entwicklung

- **24.09.2026 — Flavor-Option „Häretiker".** Zweite, mechanisch identische
  Alternative zu „Magier" bei der Charaktererstellung: neues Feld
  `magieFlavor` (`MAGIER`/`HAERETIKER`) pro Person, `weg` bleibt
  mechanisch immer `MAGIER` — reine Anzeige-Ebene, keine neue
  Spielmechanik. Hexkraft → **Glauben**, Wilde Magie → **Blasphemie**, die
  neun Sphären bekommen Götternamen aus acht Mythologien (Chronos,
  Shu, Tezcatlipoca, Kali, Donar, Enki, Ogun, Izanagi, Izanami — 27.09.2026:
  Ehecatl→Shu und Atum→Izanagi getauscht, siehe CLAUDE.md Punkt 14 für die
  vollständige Zuordnung samt Begründung).
  Zentrales Vokabular-Mapping in `backend/app/traits/seed.py`
  (`_seed_haeretiker_erklaerungen`) und `frontend/src/traits/magieBegriffe.ts`
  (Single Source of Truth, keine Text-Duplikation über die UI-Komponenten
  verteilt).
- **10.09.2026 — Arete → Hexkraft umbenannt.** Reine Namensänderung für
  Konsistenz (Backend hieß schon Hexkraft, Frontend noch Arete), brachte aber
  einen echten Doppelgänger-Bug mit sich — siehe
  [[../entities/neo4j-datenmodell#TraitDef-Umbenennen]] für die technische
  Ursache (TraitDef-Kennung enthält den Namen).

## Siehe auch

- [[neuroweaving-decking]] — der Gegenweg, gleiche Grundregeln bei Willenskraft
- [[willenskraft]] — Ressource für Wilde Magie
- [[../comparisons/regelwerk-excel-vs-aktuell]] — Umbenennungs-Historie im Kontext
