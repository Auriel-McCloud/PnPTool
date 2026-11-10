---
title: Nebenfiguren
created: 2026-11-10
updated: 2026-11-10
type: entität
tags: [personen, kontakte, ki, frontend]
sources: [../../api/nebenfiguren.md, ../../../CLAUDE.md]
status: aktuell
---

# Nebenfiguren

## Herkunft (10.11.2026)

Mark: Kontakte, die Familie eines NPCs und ähnliche Figuren brauchen weder
Charakterblatt noch Inventar und sollen die NPC-Liste nicht mit Figuren
überfluten, die er nie ausspielt. Trotzdem brauchen sie Rasse, Name, Alter,
Beschreibung, Notiz, mehrere Bilder, Beziehungen und ein paar feste Werte.

## Entscheidungen

- **Kein eigener Knotentyp.** `Person` mit `istNebenfigur=true`
  (personType bleibt `NPC`). Dadurch funktionieren Beziehungen, Graph,
  Kontakte, Chat, Gruppenchat und Bildergalerie ohne neuen Code.
- **Eigenes Burgermenü** „Nebenfiguren“ (SL). Die NPC-Liste fragt mit
  `istNebenfigur=false` und zeigt sie nicht.
- **Felder:** Name, Rasse, Alter, Persönlichkeit (kurzes Stichwort wie
  „Leitwolf“, „Angsthase“, max. 60 Zeichen), Beschreibung, Notizen, Bilder,
  Beziehungen. Dazu freie **Fähigkeiten**: Name ist Freitext, Wert eine feste
  Zahl (z. B. Straßenwissen 4). Kein Bezug auf den Fertigkeitenkatalog.
  Von Hand ohne Deckel; die KI vergibt höchstens drei, Wert 1–5.
- **Kein Kampf.** `POST .../kampf/teilnehmer` lehnt mit 400 ab,
  `kampf_kandidaten` lässt sie weg, die Kampfmodus-Auswahl zeigt sie nicht.
- **Sichtbarkeit:** dieselben Regeln wie bei NPCs.
- **Einbahnstraße zum NPC:** `POST .../nebenfiguren/{id}/zu-npc`. Die
  Charakter-KI (derselbe Zwei-Stufen-Weg wie ✨ Charakter, inkl.
  Tutorial-Shop-Einkauf) baut den Bogen in-place. Rasse ist fix, die freien
  Fähigkeiten stehen im Stufe-2-Prompt und landen auf der inhaltlich
  passendsten Katalog-Fertigkeit (Mark: „das Äquivalent oder etwas
  Ähnliches“). Name, Beschreibung, Notizen, Bilder, Beziehungen und Kontakte
  bleiben. Zurück zur Nebenfigur geht nicht. KI-Fehler → 502, Nebenfigur
  bleibt unverändert.
- **Kontakte-Hintergrund:** Ein leerer Kontakt-Platz, den der Spieler
  beschreibt, wird seit 10.11. als Nebenfigur angelegt (ein KI-Aufruf statt
  zwei plus Einkauf). **Nur Mentoren** werden weiter volle NPCs, weil die KI
  ihnen EP verteilt. Die neue Nebenfigur ist kein Ideenschmiede-Entwurf, sie
  steht direkt im Nebenfiguren-Menü (SL-geheim wie vorher).

- **Leere Kontakt-/Mentor-Plätze sind schon als Platzhalter Nebenfiguren**
  (10.11., Mark: Platzhalter sollen nicht in der NPC-Liste stehen).
  `spawn.py` setzt `istNebenfigur`, Migration 014 zieht den Altbestand nach.
  Kachel zeigt „Platzhalter“, „Zu NPC machen“ ist dort gesperrt (409) — den
  Platz füllt der Spieler. Der Mentor-Platz wird bei der Befüllung weiter ein
  voller NPC.
- **Ideenschmiede (10.11.):** ✨ KI kennt den Typ „Nebenfigur“ mit Anzahl
  (1–12) und optionaler Verbindung zu Person/Ort/Ereignis/Fraktion. Ohne
  feste Beziehung schlägt die KI je Figur eine vor (Feld `beziehung` im
  Schema, z. B. „Mutter von“), sonst gilt der Standard. Läuft über den
  Massen-Job, landet als Entwurf; „Übernehmen“ schiebt sie ins
  Nebenfiguren-Menü. „+ Neue Idee“ kann eine leere Nebenfigur anlegen,
  Beratung kennt den Typ auch (auch als Massen-Entwurf).

## Datenmodell

`Person`-Felder: `istNebenfigur: bool`, `persoenlichkeit: str`,
`nebenfaehigkeiten: [{name, wert}]` (in Neo4j als JSON-String wie `bilder`).
`istNebenfigur` steht bewusst nicht im `PersonUpdate` — umschalten nur über
die Zu-NPC-Route.

## Code

- Backend: `app/nebenfiguren/` (`logic.py` rein, `ki.py` Erzeugung,
  `routes.py` Zu-NPC), `ki/routes.py::_idee_anlegen(..., nebenfigur=)`,
  `kontakte/routes.py::kontakt_generieren`.
- Frontend: `entities/NebenfigurKacheln.tsx`, `entities/NebenfigurDetail.tsx`,
  Ansicht `nebenfiguren` in `EntityManager.tsx`, Bereich in `App.tsx`,
  Graph-Rechtsklick öffnet das Nebenfigur-Detail (`GraphOeffnen.tsx`).

## Entwicklung

- **10.11.2026 — gebaut.** Tests `tests/test_nebenfiguren.py` (Logik,
  Zu-NPC-Route, In-place-Bogen mit fixer Rasse). Anlegen/Patchen/Filtern
  einmal gegen die lokale Neo4j durchgespielt. Nebenbei: `EntityManager`
  hält jetzt eine ungefilterte Personenliste für Namen in Beziehungen — vorher
  fehlten in der NPC-Ansicht Beziehungen zu PCs. **Kein Klicktest, kein
  echter KI-Lauf.**
- **10.11.2026 — Platzhalter + Ideenschmiede.** Live gab es fünf leere
  Kontakt-Plätze („Unbekannter Kontakt“, einer ohne PC) und einen schon
  befüllten Kontakt als vollen NPC (Evelyn Sterling, Test Charakter) — der
  bleibt NPC. Tests in `test_nebenfiguren.py` (KI-Entwurf, Beziehungs-
  vorschlag, Massen-Kante, Spawn, Platzhalter-409). **Kein Klicktest.**
