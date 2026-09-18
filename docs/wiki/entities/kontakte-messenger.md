---
title: Kontakte und Messenger
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [kontakte, frontend, ui]
sources: [../../api/kontakte.md, ../../../CLAUDE.md]
status: aktuell
---

# Kontakte und Messenger

## Konzept

In-Game-Kommunikation im Persona-5-Stil. Jeder hat ein **Commlink**; Spieler
chatten mit NPCs, die sie kennengelernt haben.

**Drei Design-Entscheidungen:**
1. Kein sichtbarer Absender bei NPC-Nachrichten — SL tippt, Spieler sieht nur
   den NPC-Namen.
2. **`chatOffen` getrennt von `stufe`** — Nummer haben ≠ jemanden kennen. Die
   Stufe bestimmt *wie viel* man über jemanden weiß, `chatOffen` ob man mit ihm
   *reden* kann.
3. **Spieler sehen NPCs nur unter Alias** — kein echter Name, nur Spitzname
   oder Rassenbeschreibung („Unbekannter Elf"), bis Stufe steigt oder ein
   persönlicher Alias gesetzt wird.

## Stufensystem

| Stufe | Sichtbar | |
|---|---|---|
| 0 | Rasse | „Unbekannter Elf" |
| 1 | Alias oder Rasse | |
| 2 | + Beruf/Rolle | |
| 3 | + Hintergrund-Teaser | |
| 4 | + voller Hintergrund | |
| 5 | + SL-Notizen | intim bekannt |

## Alias-Logik

Persönlicher Alias (eigene Notiz des Spielers) > NPC-Alias (SL-gepflegt) >
Fallback „Unbekannter/Unbekannte [Rasse]".

## Chat → Mitteilung

Jede gesendete Nachricht erzeugt automatisch eine NACHRICHT-Mitteilung (siehe
[[mitteilungen-system]]) statt eines eigenen WebSockets — Begründung: das
Mitteilungen-System hat bereits WebSocket, Reconnect, Popup-Darstellung fertig.
SL→Spieler: `empfaengerIds=[spieler_pc_id]`. Spieler→NPC: `empfaengerIds=[]`
(leer = an SL).

## Geprüft am 07.09.2026

SL→Spieler-Popup ankommt; Spieler→NPC-Popup kommt bei SL an; SL bekommt
**nicht** die Spieler-zu-NPC-Popups anderer (Filterung funktioniert); ✕-Button
blendet einzelne Mitteilungen aus, „Alle ausblenden" leert die Liste, andere
Betrachter sehen sie weiterhin.

## Datenmodell

`(:Person {personType: PC})-[:KENNT {stufe, chatOffen, persoenlicherAlias}]->
(:Person {personType: NPC})`. Nachrichten als **eigene Nodes** (`:Nachricht`),
nicht als Array-Property — Begründung: hunderte Nachrichten pro Chat brauchen
Paging/Indizes, ein Array wäre unhandlich.

## Siehe auch

- [[mitteilungen-system]] — Zustellmechanismus für Chat-Benachrichtigungen
- [[neo4j-datenmodell]] — `KENNT`-Beziehung im Gesamtkontext
- [[ui-konzept-commlink]] — Persona-5-Optik-Herkunft
