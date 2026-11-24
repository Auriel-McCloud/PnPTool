---
title: Magie — Hexkraft und Sphären
created: 2026-09-18
updated: 2026-11-24
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

Neun Sphären: Raum, Schicksal, Kräfte (*Schaden automatisch +1*), Leben,
Materie, Gedanken, Ursprung, Schattenwelten, Chronurgie. Volltexte in
`docs/reference/Sphären/` (M20-Rohtext, nicht mehr aktuell) und
`docs/reference/Master/` (fertige NeotopiA-Tooltips; Gedanken ist
`Verstand.md`, Raum `Raum.md`, Chronurgie `Chronurgie.md`, Schicksal
`Schicksal.md`, Schattenwelten `Schattenwelten.md`).

**23.10.2026 — Sphären auf 6 Punkte erweitert (Mark, im Chat durchgesprochen):**
jede Sphäre bekam eine neue Zwischenstufe, „vollständig beherrschen" rutschte
von Stufe 5 auf Stufe 6 (ersetzt die ältere Entscheidung, Sphären blieben
bewusst bei 5 — siehe CLAUDE.md für den vollen Verlauf). `docs/reference/
Master/*.md`, `backend/app/traits/seed.py` (`TRAIT_LANGBESCHREIBUNGEN`,
`HAERETIKER_LANGBESCHREIBUNGEN`, `NEOTOPIA_TRAITS`) und `erstellung.py`
wurden entsprechend aktualisiert. Geister/Izanami zusätzlich inhaltlich
überarbeitet: „Astralebene"/„Todesgürtel" gibt es in NeotopiA nicht mehr,
ersetzt durch **Schattenwelten** (Totenreich, Götterreich u.a.). Charakterblatt-
Anzeige und Charaktererstellung lesen `defaultMax` aus dem Katalog und
zeigen 6 Punkte ohne eigenen Code-Change. Die Sphären-Spezialisierung
(Auto-Slots bei 2/4/6, Zusatzslot 4 EP, kein Würfelbonus) ist seit demselben
Tag gebaut. Die Stufentitel stehen seit 31.10.2026 auch in
`docs/regeln-neotopia.md` — vorher sagte die Regelfassung noch „Sphären
bleiben bei 5“.

## Der exklusive Weg

**„Hexkraft != NeuroWeaving"** steht wörtlich so im Excel — die beiden
schließen sich aus. **Entschieden:** eigenes Feld `weg` am Charakter, nicht aus
`Hexkraft > 0` abgeleitet — sonst wäre ein frisch erstellter Magier mit
Hexkraft 0 fälschlich kein Magier.

## Noch nicht gebaut

**Oberbegriff „Sphären“ heißt künftig „Domänen“** (Mark, 24.11.2026), noch nicht umgestellt. Der Umbau kommt in einem Rutsch mit dem neuen Gedanken-Namen. Nur die Anzeige ändert sich: Der gespeicherte Kategorie-Schlüssel `category = "Sphäre"` bleibt (Filter in `Probe.tsx`, `Kampfkarte.tsx`, `SpezialisierungPopup.tsx` u. a.), sonst wäre eine Migration nötig. Umzustellen sind sichtbare Texte, Seed-Langtexte, `docs/reference/Master/`, live `Erklaerung`-Knoten und `docs/regeln-neotopia.md`.

**Offen (Mark, 24.11.2026): Chronurgie und Schicksal zu einer Domäne zusammenlegen?** Das ergäbe 8 statt 9 Domänen und bräche die 1:1-Entsprechung zu Mage. Vorschlag Neko: Der Name bleibt **Schicksal**, Zeit wird zum Faden des Schicksals. Gott Kali (Kāla = Zeit und Tod), Chronos würde frei. Alternative **Kairos** (der schicksalhafte Augenblick). Live-Stand 24.11.: nur 2 PCs (beide Häretiker) haben Punkte in Schicksal (2 und 3), niemand in Chronurgie. Eine Migration wäre also billig. Wird mit dem Domänen-Umbau zusammen entschieden.

**Gedanken** hat noch keinen neuen Namen. Telepathie ist nur das Lesen. Zuletzt im Rennen: Occultamentis, Persona (keine Entscheidung). Raus: Psyche, Innenwelt, Telepathie, jedes reine ment-Wort.
Kräfte, Leben, Materie bleiben. Ursprung nicht neu entschieden.

## Entwicklung

- **24.11.2026 — Oberbegriff Sphären heißt Domänen (Mark), entschieden, nicht gebaut.** Grund: letzter großer Mage-Fingerabdruck (IP, siehe [[../entities/konten-login-und-abo]]). Passt zu den Häretikern, denn Götter haben Domänen. Verworfen: Gefilde (klingt nach Ort, Konflikt mit Schattenwelten), Siegel (klingt nach Technik), Kreise (so heißen schon die Punkte am Blatt), Arkana (Mage: The Awakening), Disziplinen (Vampire), Gaben (Werwolf), Pfade (Vampire und Awakening), Fäden (NeuroWeaving).
- **09.11.2026 — Korrespondenz heißt Raum, Zeit heißt Chronurgie, Entropie heißt Schicksal (Mark).** Häretiker sehen weiter Shu, Chronos, Kali. Gedanken bleibt. Der Vorschlags-Chip „Schicksal“ heißt jetzt Ordnung, sonst klebt er am Sphärennamen. Punkte hängen per `_migriere_sphaeren_namen` um.
- **09.11.2026 — Sphärennamen Raum, Chronurgie, Schicksal entschieden, nicht gebaut (Mark).** Siehe den Eintrag darüber. Der Umbau ist gelaufen.
- **09.11.2026 — Sphäre Geister heißt Schattenwelten (Mark).** Der Sphärenname
  selbst, nicht nur der Ort in den Stufentexten. Häretiker sehen weiter
  Izanami. Geister rufen und binden in den Stufen bleibt — das sind die
  Wesen, nicht der Name. Bestehende Punkte hängen per Seed-Migration am
  neuen TraitDef (`seed.py::_migriere_geister_zu_schattenwelten`), dieselbe
  Kennungs-Falle wie Arete zu Hexkraft.
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
