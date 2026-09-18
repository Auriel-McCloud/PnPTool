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
