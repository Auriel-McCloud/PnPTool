# Ereignisprotokoll (Sitzungs-Log)

Sitzungs-Log: eigener Knotentyp je Kategorie, gemeinsame Basis-Felder für
eine UNION-Zeitleiste. Kein generisches `typ`-Feld.

Modul: `backend/app/ereignisprotokoll/` (`schemas.py`, `repository.py`,
`routes.py`, `hooks.py`). Migration: `backend/app/db/migrations/006_ereignisprotokoll.cypher`.
Herleitung: `docs/wiki/entities/ereignisprotokoll.md`.
Frontend: SL-Bereich `Protokoll` in `frontend/src/ereignisprotokoll/`
(Sitzung, Kategoriefilter, Suche, Liste). Korrektur/Papierkorb später.

Commit `233c939` (27.09.2026). Auto-Hooks 29.09.2026.

## Stand

- **Gebaut:** Sitzungen, acht Log-Kategorien, Zeitleiste, SL-Korrektur,
  Papierkorb (`geloescht`-Flag, kein Hard-Delete), `Person.erstelltAm`.
- **Writer** (`log_ki_eintrag`, `log_gegenstandsbewegung`, `log_geldbewegung`,
  `log_aufenthalt`, `log_npc_wissenszuwachs`, `log_kampf_eintrag`,
  `log_verhandlungsausgang`, `log_charakterentwicklung`) liegen im Modul.
  Fachmodule rufen sie über `hooks.py` (aktive Sitzung zentral).
- **Auto-Hooks:** Kampf-Treffer, Verhandlungsausgang, Shop-Kauf + digitale
  Lieferung, Reparatur, Weitergabe/Wegwerfen, Party-Aufenthalt, EP/Steigerung/
  Willenskraft/Rasse, KI-Hauptpfade (Idee, Objekt-Text, Bild, Wiki-Prüfung,
  Auto-Verknüpfung, Erstellungs-Kommentar). Kauf teilt sich `handelId`.
- **Nicht gebaut:** Korrektur/Papierkorb in der UI, Achievements (nur ID-Constraints in der
  Migration; Konzept `docs/wiki/entities/achievements.md`), NPC-Wissens-Hooks,
  KI-Nebenpfade (Sortiment, Alltagswunsch, Zusatzfertigkeiten-Vorschlag,
  Wiki-Import, Spieler-Portrait).

## Kategorien (`LOG_LABELS`)

| Pfad-Key | Neo4j-Label | Inhalt |
|---|---|---|
| `ki` | `KiProtokollEintrag` | KI-Ausgabe, auch wenn nicht übernommen |
| `gegenstand` | `GegenstandsBewegung` | Besitzerkette (gefunden/gekauft/weitergegeben/…) |
| `geld` | `GeldBewegung` | Kapital, optional `handelId` |
| `aufenthalt` | `Aufenthalt` | Party/Person an Ort/Event, Historie |
| `npcwissen` | `NpcWissenszuwachs` | was ein NPC erfahren hat |
| `kampf` | `KampfLogEintrag` | Treffer/kritisch/bewusstlos/tot/Kampfende |
| `verhandlung` | `VerhandlungsAusgang` | angenommen **und** abgelehnt, Positions-Schnappschuss |
| `charakterentwicklung` | `CharakterEntwicklung` | Steigerung, Willenskraft, EP, Rassenwechsel |

Gemeinsame Properties: `zeitpunkt`, `ingameZeitpunkt`, `sitzungId`,
`slNotiz`, `geloescht`. Anker pro Spielabend: `:Sitzung` (echtes `datum`
Pflicht, `ingameDatum` Freitext).

Es gibt **keine POST-Routen zum Anlegen von Log-Einträgen**. Anlegen nur
über die Writer, gedacht als Hooks aus anderen Modulen.

## Basis

`/api/campaigns/{campaign_id}/ereignisprotokoll`

Router: `require_campaign_zugang`. Schreibende Sitzungs- und Korrektur-Routen
zusätzlich `require_campaign_gm`.

## Sitzungen

### GET `/sitzungen`

Alle Sitzungen der Kampagne. Auch Spieler (Filter nach Abend).

### POST `/sitzungen` — nur SL

Body: `datum` (YYYY-MM-DD, Pflicht), `ingameDatum`, `titel`, `notiz`.

### PATCH `/sitzungen/{sitzung_id}` — nur SL

Teilupdate derselben Felder.

## Zeitleiste — nur SL

### GET `/zeitleiste?sitzung_id=`

UNION über alle acht Labels, neueste zuerst. Optional auf eine Sitzung
filtern. Enthält KI-Rohtext und Bewegungen aller Personen — deshalb GM-only.
Felder: `id`, `kategorie`, `zeitpunkt`, `ingameZeitpunkt`, `sitzungId`,
`slNotiz`, `kurz` (Art/Anlass, eine Zeile).

## Kategorie-Listen

| Methode | Pfad | Wer | Filter |
|---|---|---|---|
| GET | `/ki` | nur SL | — |
| GET | `/gegenstandsbewegungen` | Zugang | `gegenstand_id` |
| GET | `/geldbewegungen` | Zugang; Spieler fest auf eigene Person | `person_id` |
| GET | `/aufenthalte` | Zugang | `party_id` |
| GET | `/npc-wissenszuwachs` | nur SL | `npc_person_id` |
| GET | `/kampf` | Zugang | `person_id` |
| GET | `/verhandlungen` | Zugang; Spieler fest auf eigene Person | `person_id` |
| GET | `/charakterentwicklung` | Zugang | `person_id` |

Gelöschte Einträge kommen in den Listen nicht vor (`geloescht = false`).

## Korrektur / Papierkorb — nur SL

Pfad-Key = Spalte „Pfad-Key“ oben (`ki`, `gegenstand`, …). Unbekannt → `404`.

### PATCH `/{kategorie}/{eintrag_id}`

Body `{ "felder": { … } }`. Freies Dict, Feldnamen je Kategorie.

### PUT `/{kategorie}/{eintrag_id}/geloescht`

Body `{ "geloescht": true|false }`. Kein Hard-Delete.
