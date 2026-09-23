---
title: Auth und Rollen
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [auth, backend]
sources: [../../api/auth.md]
status: aktuell
---

# Auth und Rollen

## Konzept

Zwei Benutzertypen: **Spielleitung (GM)** — ein Account pro Kampagne, voller
Zugriff — und **Spieler (PLAYER)** — begrenzter Zugriff. JWT im
httpOnly-Cookie `pnptool_session`, Token-Lebensdauer 7 Tage.

## Login-Wege

- SL: Username/Passwort (`POST /api/auth/gm/login`)
- Spieler: **Einladungscode** (`POST /api/auth/player/login`), einmalig, an
  Kampagne + optional an einen PC gebunden

## Berechtigungsprüfung (FastAPI-Dependencies)

1. Authentifiziert? (Cookie vorhanden/gültig)
2. Kampagnenzugang? (`require_campaign_zugang`)
3. Rollenberechtigung? (`require_campaign_gm` für Admin-Aktionen)

`Viewer(role, person_id)` — `person_id` ist die PC-ID bei Spielern, `None` bei
SL, wird in praktisch allen Endpunkten zur Filterung/Rechteprüfung verwendet
(siehe [[../concepts/rassen]], [[mitteilungen-system]] für Beispiele).

## Siehe auch

- [[neo4j-datenmodell]] — `GEHOERT_ZU`/`SPIELT` für PlayerSession
- [[architektur-drei-ebenen]] — Campaign als Zugangs-Container

## Ersteinstieg für neue Spieler (23.09.2026)

Ein Spieler-Account ohne `SPIELT`-Kante (`personId` fehlt in
`GET /api/spieler/me`) sieht nach dem Login `frontend/src/players/
SpielerEinstieg.tsx` statt der vollen Commlink-Hülle: "Selbst erstellen"
(`POST /api/spieler/charakter-neu`, legt sofort einen leeren PC an,
danach greift die normale Charaktererstellung) oder "Vorgefertigten
Charakter wählen" (`GET /api/spieler/vorgefertigte` listet abgeschlossene,
noch niemandem zugeordnete PCs; `POST /api/spieler/charakter-waehlen`
weist atomar zu — zwei gleichzeitige Zugriffe auf denselben PC können ihn
nicht beide bekommen). Ein "vorgefertigter PC" ist bewusst kein eigenes
Datenfeld, sondern schlicht ein PC ohne `SPIELT`-Kante. Details:
`docs/api/auth.md`, `CLAUDE.md` Punkt 6.

Zusätzlich (gleicher Commit): `AnmeldeFenster.tsx` ersetzt die getrennten
SL-/Spieler-Login-Seiten durch eine gemeinsame Commlink-Karte, Spieler
sehen den Login-Weg zuerst.
