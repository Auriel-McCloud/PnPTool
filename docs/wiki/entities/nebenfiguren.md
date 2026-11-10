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
