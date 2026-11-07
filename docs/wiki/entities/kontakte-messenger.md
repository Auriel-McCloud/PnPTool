---
title: Kontakte und Messenger
created: 2026-09-18
updated: 2026-11-07
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

## Undefinierter Kontakt (01.11.2026)

Kontakte-Hintergrund legt N Blanko-NPCs an (`istBlankoKontakt`, Chat zu).
Die Spieler-Liste ◍ Kontakte zeigt sie trotzdem, Label „Undefinierter Kontakt“.
Erster Klick: Beschreibung, dann `POST .../generieren`. Danach ist der
Platzhalter weg, der neue NPC hat offenen Chat, und dieser Spieler kennt
den Namen. Ohne die eigene Zeile blieb die Liste leer, weil der Messenger
nur `chatOffen` zeigte.

## Chatverlauf-Regel (07.11.2026)

Lesen (`GET .../chat`) und Senden nutzen dieselbe Regel wie die Liste: `chat_ist_offen` in `kontakte/security.py`. Explizites `chatOffen` zählt; nur ein nie gesetztes Feld fällt auf Stufe ≥ KONTAKT_AUSGETAUSCHT zurück. Vorher lieferte Lesen bei einem von der SL angelegten Kontakt (Stufe GESEHEN, Chat offen) einen leeren Verlauf, obwohl die Nachrichten gespeichert waren.

## SL-Chatfenster (07.11.2026)

Der Verlauf in der SL-Kontaktliste ist ein `Fenster` mit der Messenger-Optik der Spieler (`msg-*`, `NachrichtBlase`). Vorher ein eigenes Overlay mit nicht definierten Theme-Variablen, dadurch durchsichtig. Die SL schreibt als NPC (rechts), der PC steht links.

## Spieler↔Spieler-Chat (07.11.2026)

**Phase 1 gebaut** (PC↔PC, 1:1). Kontakt entsteht per Anfrage zwischen den Spielern, nicht über die SL: Verhandlungsart `SPIELER_KONTAKT` (Zustimmungs-Popup, Muster wie Gegenstands-Weitergabe). Bei Annahme je Seite eine `KENNT`-Kante PC→PC mit Chat offen, Name bekannt, eigenem Alias und eigenen Notizen. Nachrichten (`VON`/`AN`), Liste und Ungelesen-Zähler sind dieselben wie bei NPC-Chats.

**Entscheidungen (Mark):**
1. Kontakt muss erst hergestellt werden, wie bei anderen Kontakten.
2. Die SL wird nicht informiert und liest nicht mit. Verschlüsselt ist es nicht — falls je eine KI/ein Missbrauch einen Blick nötig macht, liegen die Daten in Neo4j. Eine SL-Einsicht ist eine spätere Idee, nicht gebaut.
3. Der Kampagnenschalter `messengerAktiv` gilt auch hier.
4. Gruppenchat ist gewünscht, auch PCs + NPCs gemischt (Phase 2).

**Umsetzung der Privatsphäre:** `security.darf_kontakt_sehen` lässt Spielerkontakte nur den Besitzer der Kante sehen (SL: 404 auf Verlauf und Senden, nicht in `/uebersicht`/`/anfragen`). Die Chat-Mitteilung geht an `empfaengerIds=[Mitspieler]` — eine leere Liste hieße „an die SL“. Die Beschreibung des Mitspielers wird nie ausgeliefert, Anzeigename = eigener Alias, sonst Charaktername. Mitspieler-Liste: nur PCs mit `(:Spieler)-[:SPIELT]->`, also keine unbesetzten Vorgefertigten.

## Gruppenchat (Phase 2, entschieden, nicht gebaut)

- **Wer legt an:** nur die SL. Mitglieder PCs und NPCs gemischt.
- **Modell:** `(:Gruppenchat {id, campaignId, name})-[:TEILNEHMER {gelesenBis}]->(:Person)`; Gruppennachricht `-[:IN]->(:Gruppenchat)` statt `AN`. Ungelesen pro Teilnehmer über `gelesenBis` (ein Gelesen-Häkchen reicht bei mehreren Empfängern nicht). Einzelchats bleiben unverändert, werden nicht in Gruppen umgebaut.
- **NPC in der Gruppe:** die SL schreibt als NPC, bei mehreren NPCs wählt sie per Dropdown, wer spricht — kein sichtbarer Absender „SL“.
- **Anzeige:** Portraits wie im Einzelchat; jeder sieht die anderen unter dem eigenen Alias bzw. „Unbekannter …“.
- **Historie:** neue Mitglieder sehen alles (Mark: was weniger Aufwand ist).
- Neue Beziehungstypen (`TEILNEHMER`, `IN`) und Label `Gruppenchat` müssen in `KNOWN_LABELS`/`KNOWN_REL_TYPES` (`campaigns/export_import.py`).

## Siehe auch

- [[mitteilungen-system]] — Zustellmechanismus für Chat-Benachrichtigungen
- [[neo4j-datenmodell]] — `KENNT`-Beziehung im Gesamtkontext
- [[ui-konzept-commlink]] — Persona-5-Optik-Herkunft
