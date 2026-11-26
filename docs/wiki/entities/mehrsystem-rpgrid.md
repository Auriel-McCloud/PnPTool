---
title: Mehrsystem-Kern (RPGrid) — NeotopiA und GridMonster umschalten
created: 2026-11-26
updated: 2026-11-26
type: entität
tags: [regelsystem-kampagne-ideenschmiede, datenmodell, gridmonster]
sources: [Gespräch 2026-11-26]
status: offen
---

# Mehrsystem-Kern (RPGrid)

**Mark (26.11.2026):** „Wollen wir das Grundgerüst für den RPGrid bauen, so
dass wir ein wenig an GridMonster basteln können? Und zwischen NeotopiA und
GridMonster umschalten können?“

RPGrid = Arbeitsname der Plattform („Role Play Grid“, alle Systeme darin),
siehe Marks persönliches Wiki `entities/pnptool.md`. GridMonster-Regelstand
(Attribute, Fertigkeiten, Stufen/Würfel, Partnerschaft) steht in Marks
persönlichem Wiki `concepts/gridmonster.md` — dort nachlesen, nicht hierher
kopieren.

## Befund im Code (26.11.2026)

- Backend hat die Ebene schon: `(:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)`,
  CRUD unter `/api/regelsysteme`, `seed_neotopia()` beim Start
  (siehe [[architektur-drei-ebenen]]).
- `get_campaign` liefert `ruleset` als Klein-Slug (`toLower(Name)`) →
  GridMonster würde automatisch `gridmonster`.
- `TraitDef` (Attribute/Fertigkeiten), `Erklaerung` (Regeltexte) sind schon
  nach `ruleset` getrennt → GridMonster-Katalog kann daneben liegen.
- Frontend nutzt das Regelsystem nirgends; Kampagnen anlegen ohne Systemwahl.
- Rund 50 Stellen im Backend setzen `"neotopia"` fest (Fallbacks,
  `hintergruende`, `kampf/repository.py` Rassen-Match, `wuerfel/logic.py`,
  `traits/bogen.py` …) — die müssen beim Umbau einzeln geprüft werden.

## Entschieden: Startseite mit Spiele-Kacheln (Mark, 26.11.2026)

> „Ich logge mich in den RPGrid ein, und dann sehe ich Kacheln von Spielen,
> die ich spielen kann, im Moment NeotopiA und GridMonster, und dann klicke ich
> auf das, das ich spielen möchte. … Ein SL sieht alle Spiele, ein Spieler nur
> die, in denen er mitspielt.“

- Nach dem Login kommt eine Kachel-Startseite **über** den Kampagnen: eine
  Kachel je Regelsystem (Spiel).
- SL sieht alle Spiele; Spieler nur die, in denen er einen Zugang hat.
- Datenmodell bleibt `Kampagne -NUTZT_REGELSYSTEM-> Regelsystem`; die Kacheln
  gruppieren nur.
- **Mark (26.11.2026):** Ein Spiel kann mehrere Kampagnen haben, auch unter
  derselben SL.
- **Annahme Neko:** Hat das Spiel genau eine Kampagne, führt der Klick direkt
  hinein; bei mehreren kommt die Kampagnen-Auswahl dieses Spiels. Ein Knopf
  „Spiel wechseln“ führt zurück zu den Kacheln.
- Spieler-Seite der Kacheln braucht das `Konto` über mehreren Kampagnen
  ([[konten-login-und-abo]]); heute hängt ein Spieler-Zugang an genau einer
  Kampagne und geht weiter direkt hinein.

## Offene Achsen

1. ~~Umschalten~~ → entschieden, siehe oben.
2. **Umfang erstes Gerüst:** nur Schalter (GridMonster-Kampagne, NeotopiA-
   Bereiche ausgeblendet) / + Monster & Mensch mit Attributen, Fertigkeiten,
   Würfelstufen, LP/Energie / + Partnerschaft Mensch↔Monster und Spieler mit
   zwei Charakteren.
3. **Monster im Datenmodell:** Person mit Flag `istMonster` (Kampf, Graph,
   Zugang, Listen spielen sofort mit; Standardweg laut Projektregel) **oder**
   eigenes Label `Monster`.

## Vorschlag Neko (nicht entschieden)

- Achse 3: Flag an `Person`. Achse 2: mittlere Stufe,
  Partnerschaft als zweiter Schritt (Graph-Idee aus Marks Wiki:
  Zugang -SPIELT-> Mensch/Monster fix, Mensch -PARTNER-> Monster SL-änderbar).
- In einer GridMonster-Kampagne ausblenden (Annahme, reversibel): Augments,
  Rassen, Zusatzfertigkeiten, Hintergründe, Begleiter, Shop.
- Würfelstufen als eigene GridMonster-Würfellogik (W4–W20, explodierend,
  höherer von Attribut-/Fertigkeitswürfel), nicht in den NeotopiA-W10-Pool
  hineinbiegen.
- IP: Stufennamen (Rookie/Champion/…) und private Digimon-Daten gehören nicht
  ins Repo (`C:\DEV\GridMonster-privat\` bleibt getrennt); im Code neutrale
  Stufen 1–5 mit Anzeigenamen als Einstellung.
