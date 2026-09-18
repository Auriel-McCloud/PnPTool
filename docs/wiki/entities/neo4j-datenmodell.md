---
title: Neo4j-Datenmodell
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [datenmodell, backend, versionsgeschichte]
sources: [../../../backend/app/db/migrations/, ../../../CLAUDE.md, ../../api/README.md]
status: aktuell
---

# Neo4j-Datenmodell

## Warum Neo4j

Ein PnP-Spiel ist ein Netz aus Beziehungen: NPCs kennen sich, Orte sind
verbunden, Gegenstände gehören Charakteren, Fraktionen haben Hierarchien. Eine
Graphdatenbank bildet das natürlich ab — keine JOIN-Orgien, keine künstlichen
Zwischentabellen (siehe [[../../api/README.md]]).

## Node-Typen (Constraints, `backend/app/db/migrations/`)

`GMUser`, `Campaign`, `Person`, `Ort`, `Event`, `TraitDef`, `PlayerSession`,
`Gegenstand`, `Rasse` — jeweils mit eindeutiger `id`-Constraint. Weitere Typen
ohne expliziten Constraint (laut Code-Suche in den Repositories):
`Mitteilung`, `WikiSeite`, `Kampf`, `Nachricht`, `Kontakt`/`KENNT`-Beziehung,
`Fraktion`, `Regelsystem`, `Erklaerung`.

## Zentrale Beziehungstypen (aus `repository.py`-Dateien)

| Beziehung | Zwischen | Bedeutung |
|---|---|---|
| `HAS_TRAIT` | Person/Rasse → TraitDef | Attribut-/Fertigkeitswert (`rating`, `maxOverride`) |
| `BESITZT` | Person → Gegenstand | Inventar |
| `LIEGT_IN` | Gegenstand/Ort → Ort | Hierarchie |
| `VERBINDUNG` | beliebig → beliebig | generische Graph-Kante (`typ`, `beschreibung`, Sichtbarkeit) |
| `BEGLEITET` | Person → Begleiter | Drohne/Fahrzeug/Sprite/Geist, siehe [[../concepts/drohnen-fahrzeuge]] |
| `HAT_ENTITAET` | Campaign → * | Zugehörigkeit zur Kampagne |
| `HAT_KAMPF` / `KAEMPFT` / `IST` | Campaign/Person → Kampf | siehe [[../concepts/kampf-und-initiative]] |
| `HAT_MITTEILUNG` | Campaign → Mitteilung | siehe [[mitteilungen-system]] |
| `HAT_SEITE` / `UNTERSEITE_VON` / `VERWEIST_AUF` | Campaign/WikiSeite | siehe [[ingame-wiki-feature]] |
| `NUTZT_REGELSYSTEM` | Campaign → Regelsystem | siehe [[architektur-drei-ebenen]] |
| `ERLAUBT_RASSE` | Campaign → Rasse | siehe [[../concepts/rassen]] |
| `GEHOERT_ZU` / `SPIELT` | PlayerSession → Campaign/Person | Spielerzugang |
| `VON` (im Kontext `kontakte/`) | Nachricht → Person | siehe [[kontakte-messenger]] |

**Fast alles trägt zusätzlich `campaignId` als Property** statt (oder zusätzlich
zu) expliziten Kanten zur Kampagne — schneller für Queries, laut
`docs/api/kampagnen.md`.

## TraitDef-Umbenennen — der wichtigste Stolperstein

**Die TraitDef-Kennung ist `ruleset:category:name`** (`backend/app/traits/seed.py`).
Wer einen Wert umbenennt, ändert damit die Kennung — `MERGE` legt dann einen
**neuen, leeren** Knoten an, während der alte samt aller Charakterwerte
(`HAS_TRAIT`, dort sitzt `rating`) stehen bleibt.

**So entstand der Arete/Hexkraft-Doppelgänger** (10.09.2026, siehe
[[../concepts/magie-hexkraft]]): das Charakterblatt zeigte die alten Punkte,
die Kampfkarte den neuen leeren Wert; weil die alte Kategorie keine
Magie-Kategorie mehr war, sah plötzlich **jeder** Charakter die Zeile. Fix-Muster:
`seed.py::_migriere_arete_zu_hexkraft` (Werte umhängen, alten Knoten erst löschen
wenn nichts mehr dranhängt).

**Lehre daraus umgesetzt bei Rassen** (siehe [[../concepts/rassen]]): die
Rassen-Kennung ist bewusst eine **namenlose UUID**, damit Umbenennen im
Baukasten nichts zerreißt.

## Weitere dokumentierte Stolpersteine (Auszug, vollständig in `CLAUDE.md`)

- **6-Schichten-Check bei neuen Feldern:** DB-Property → Repository FIELDS+DEFAULTS
  → Create-Schema → Update-Schema → **Response-Schema (oft vergessen!)** →
  Frontend-Interface.
- **Neo4j NIE mit `docker run` starten** — anonymes Volume, wirkt wie
  Datenverlust. Immer `docker compose up -d neo4j` (benanntes Volume
  `pnptool_neo4j_data`). Am 15.09.2026 real passiert und behoben.
- **`WITH` zwischen schreibender Klausel und `MATCH`** — Neo4j verlangt das
  nach `CREATE`/`SET`/`DELETE` vor erneutem `MATCH`.
- Pydantic-Response-Felder ohne Fallback → `null` → Validierung schlägt fehl
  auf der **ganzen Liste**, nicht nur beim betroffenen Datensatz. Lösung:
  `coalesce`-Fallback in `_decode()` bei jeder neuen Property.

## Siehe auch

- [[architektur-drei-ebenen]] — wie Regelsystem/Campaign/Ideenschmiede sich im Graph verschachteln
- [[../concepts/rassen]] — konkretes Beispiel für saubere Kennungs-Gestaltung
- [[../../../CLAUDE.md]] — vollständige Stolperstein-Liste
