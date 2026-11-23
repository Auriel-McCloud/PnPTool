---
title: Konten, Login-Wege und SL-Abo
created: 2026-11-23
updated: 2026-11-23
type: entität
tags: [auth, backend, datenmodell, offen, geplant]
sources: [../../../backend/app/auth/repository.py, ../../../backend/app/players/repository.py, ../../api/auth.md]
status: offen
---

# Konten, Login-Wege und SL-Abo

Zukunftsplanung, kein Bauauftrag. Gehört zu [[entities/skalierung-mehrere-regionen]]
und zur Geschäftsidee in Marks persönlichem Wiki (`concepts/gridmonster.md`:
Software gratis, verkauft wird nur der Service).

## Heute (Code-Stand 23.11.2026)

- SL: `GMUser` mit Benutzername und Passwort.
- Spieler: `Spieler`-Zugang, den die SL anlegt. Er hängt per `GEHOERT_ZU` an genau
  einer Kampagne, das Passwort ist optional. Details: [[entities/auth-und-rollen]].

## Richtung (Mark, 23.11.2026)

- **Jede E-Mail-Adresse** muss ein Konto anlegen können, nicht nur Google/Discord.
- **Login-Wege:** E-Mail plus Passwort, „Mit Google anmelden“, „Mit Discord anmelden“.
- **Spieler-Konten** kann jeder selbst anlegen, kostenlos.
- **SL-Konten kosten monatlich.** Damit sind KI-Tokens, Strom/Hosting und Service
  abgedeckt.
- **Open Source:** Die Software ist gratis, verkauft wird nur der gehostete Service.
  Mark mag den Gedanken. Die Lizenzempfehlung AGPL-3.0 steht schon in
  `gridmonster.md`.
- **Discord-Plugins** als spätere Idee.

## Folge fürs Datenmodell

Damit ist praktisch das **Konto-Modell** gesetzt (Variante B aus dem Chat vom
23.11.): Ein `Konto` mit E-Mail liegt über den Kampagnen. Darunter hängen die
Spieler-Zugänge und die SL-Kampagnen. Google- und Discord-IDs werden mit dem Konto
verknüpft. Gespeichert wird nur die Anbieter-ID (`sub`), keine Profildaten. Die
Variante „nur Google an einen bestehenden Zugang hängen“ ist damit nur noch ein
Zwischenschritt.

Neu nötig: E-Mail-Bestätigung, Passwort-Reset (Mailversand), Schutz gegen
Massenregistrierung, Konto löschen (DSGVO).

## Abo

- Zahlungsanbieter am besten als *Merchant of Record* (Paddle, Lemon Squeezy).
  Der kümmert sich um die EU-Umsatzsteuer, mit Stripe müsste man das selbst machen.
- Die Abrechnung ist im Open-Source-Code abschaltbar (Konfig-Schalter, Standard
  aus). Selbsthoster bekommen alles gratis, der gehostete Dienst verkauft Komfort.
- KI-Kosten: ein Token-Budget je SL-Abo. Selbsthoster könnten ihren eigenen
  API-Key eintragen.

## Vor einer Veröffentlichung als Open Source

- **IP:** NeotopiA nutzt Begriffe aus WoD, Shadowrun und Mage. Das öffentliche
  Repo liefert ein leeres Gerüst oder ein eigenes Standardsystem. NeotopiA bleibt
  Marks Kampagnen-Inhalt.
- **Repo-Historie** (rund 1000 Commits) enthält Referenzmaterial, private Notizen
  und Infrastruktur-Hinweise. Besser ein frisches öffentliches Repo ohne Historie
  plus einen Secret-Scan (z. B. gitleaks). Gekaufte Regelwerk-PDFs nie committen.
- **Sprache:** Code und UI sind deutsch. Für USA/Asien braucht es ohnehin i18n,
  und ein englisches README hilft der Community.
- **Recht:** Gewerbe, Impressum, AGB, Datenschutzerklärung/AVV, AGB des
  KI-Anbieters. Keine Rechtsberatung: vorher WKO-Gründerservice und IP-Anwalt.

## Offen

- Preis und Inhalt des SL-Abos (Token-Budget, Speicher, Anzahl Kampagnen).
- Zeitpunkt der Konto-Umstellung und Migration der Bestandszugänge.
- Was die Discord-Anbindung können soll (Würfelergebnisse, SL-Ansagen,
  Sitzungs-Erinnerung …).
- Ob und wann das Repo öffentlich wird.

## Siehe auch

- [[entities/auth-und-rollen]]
- [[entities/skalierung-mehrere-regionen]]
- [[entities/ki-integration]]

## Entwicklung

- 23.11.2026 — Seite angelegt. Richtung von Mark: Konten per E-Mail, Google und
  Discord, Spieler gratis, SL-Abo, Open Source.
