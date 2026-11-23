---
title: Skalierung — mehrere Server und Regionen
created: 2026-11-23
updated: 2026-11-23
type: entität
tags: [backend, websocket, auth, offen, geplant]
sources: [../../../backend/app/auth/security.py, ../../../backend/app/mitteilungen/verteiler.py, ../../../backend/app/battlemap/verteiler.py, ../../../backend/app/ki/massenjobs.py, ../../../backend/app/main.py]
status: offen
---

# Skalierung — mehrere Server und Regionen

Zukunftsplanung, kein Bauauftrag. Anlass: ein befreundeter Programmierer hat Mark
gefragt, was passiert, wenn PnPTool über einen Server hinaus wächst (USA, Asien,
Cloud-Anbieter). Grundsatz von Mark (23.11.2026): **„Wir beginnen klein, verbauen uns
nichts und planen für Erfolg.“**

## Entschieden (Mark, 23.11.2026)

- **Start daheim:** Solange es geht, läuft PnPTool auf Marks eigenem Server (bebop).
  Über Cloud wird erst bei Erfolg entschieden.
- **Regionswahl beim Login:** Auf der Anmeldeseite wählt man „Europa / USA / Asien“.
  Jede Region ist ein vollständig eigener Stack (Backend, Neo4j, Uploads).
- **Kein Anbieter-Lock-in:** Weiter mit Docker Compose und Standardbausteinen
  (Redis, S3-kompatibler Speicher), damit jeder Anbieter infrage kommt.

## Wo es heute an genau einem Server hängt (Code-Stand 23.11.2026)

| Baustein | Heute | Bei mehreren Servern |
|---|---|---|
| Login | JWT-Cookie `pnptool_session`, zustandslos (`auth/security.py`) | Funktioniert, solange alle Server einer Region dasselbe `jwt_secret` haben |
| Live-Leitungen | `Verteiler` je Modul im Prozess-Speicher (`mitteilungen`, `battlemap`, `raetsel`, `zeichnungen`) | SL auf Server A erreicht Spieler auf B nicht → Redis Pub/Sub dazwischen |
| Uploads | Lokaler Ordner `uploads/` (`main.py`) | Andere Server sehen die Dateien nicht → Object Storage (S3/Blob) + CDN |
| KI-Massenjobs | `_JOBS`-Dict im Speicher (`ki/massenjobs.py`) | Polling landet auf anderem Server → Job-Stand in DB oder Redis |
| Neo4j | Eine Instanz | Mit Kampagne-je-Region kein Cluster nötig; Ausfallsicherheit wäre Enterprise/Aura |

## Modell „eine Region = ein eigenständiger Stack“

- Eine Kampagne lebt komplett in einer Region. Es gibt keine weltweite Datenbank und
  keine Synchronisation zwischen den Kontinenten.
- Die Regionswahl beim Login spart einen globalen Login-Dienst. Konto und Kampagne
  liegen in derselben Region.
- Einladungslinks tragen die Region (z. B. eigene Subdomain je Region), damit ein
  Mitspieler im richtigen Stack landet, auch wenn er auf einem anderen Kontinent sitzt.
  Etwa 250 ms Verzögerung über den Globus sind für ein Tabletop-Werkzeug unkritisch.
- Datenschutz-Nebeneffekt: EU-Gruppen bleiben auf EU-Servern.

## Leitplanken ab jetzt („nichts verbauen“)

- Neuer Zustand, der eine Anfrage überdauert, gehört in die DB, nicht in
  modulweite Dicts/Listen im Prozess.
- Neue Live-Funktionen nutzen das bestehende `Verteiler`-Muster. Später wird dann
  nur der Verteiler auf Redis umgestellt, nicht jedes Feature einzeln.
- Dateien nur über den bestehenden Upload-Pfad ablegen, keine neuen Sonderordner.
- Adressen, Domains und Geheimnisse kommen aus der Konfiguration (`config.py`/env),
  nie fest im Code.
- Abfragen bleiben innerhalb einer Kampagne, nichts kampagnenübergreifend
  Globales voraussetzen.

## Offen

- **Anbieter**, falls es aus dem Heimbetrieb herauswächst. Kandidaten: Hetzner
  (günstig, DE/FI/US/Singapur), OVH, DigitalOcean, Azure/AWS/GCP (teurer, nur bei
  Bedarf an deren Spezialdiensten). Entscheidung erst bei Bedarf.
- **Ein Konto für mehrere Regionen?** Heute pro Region getrennt. Wer in einer EU-
  und einer US-Kampagne spielt, bräuchte zwei Konten. Alternative wäre ein globaler
  Login (eigener Dienst oder externer Anbieter wie Microsoft/Google/Discord).
- **Umzug einer Kampagne** zwischen Regionen: denkbar über
  [[entities/kampagnen-export-import]].
- **Konten und Login über Google/Discord/E-Mail:** siehe [[entities/konten-login-und-abo]].
- **Zeitpunkt** für Stufe 1 (zweiter Server in derselben Region: Redis + Object
  Storage + Jobs in DB, grob einige Tage Arbeit).

## Siehe auch

- [[entities/tech-stack]]
- [[entities/auth-und-rollen]]
- [[entities/mitteilungen-system]]
- [[entities/kampagnen-export-import]]

## Entwicklung

- 23.11.2026 — Seite angelegt nach Gespräch mit Neko. Code-Stand analysiert,
  Grundsatzentscheidungen von Mark (Start daheim, Regionswahl beim Login, kein Lock-in).
