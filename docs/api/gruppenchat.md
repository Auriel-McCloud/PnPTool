# Gruppenchat API

Prefix: `/api/campaigns/{campaign_id}/gruppenchats`. Hängt wie der Einzelchat am
Kampagnenschalter `messengerAktiv` (aus → 403). Konzept und Entscheidungen: Wiki
`entities/kontakte-messenger`.

## Rechte

- **Nur SL:** Anlegen, Umbenennen, Schließen/Öffnen, Löschen, Mitglieder.
- **Spieler:** sehen und beschreiben nur **offene** Gruppen, in denen ihr Charakter
  Mitglied ist. Alles andere ist 404 (sie sollen nicht erfahren, dass es die Gruppe gibt).
- **SL** sieht alle Gruppen und schreibt als eines der NPC-Mitglieder.

## Namen pro Betrachter

Der Server liefert fertige Namen: Spieler sehen NPCs unter eigenem Alias bzw.
„Unbekannter …“ (nie den echten Namen), Mitspieler unter eigenem Alias oder Charaktername;
die SL sieht echte Namen.

## Endpunkte

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `` | alle | Spieler: eigene offene Gruppen mit `ungelesen`. SL: alle Gruppen |
| POST | `` | SL | `{name, personIds[]}` anlegen (unbekannte Person → 404, nichts wird angelegt) |
| PATCH | `/{gruppe_id}` | SL | `{name?, offen?}` — `offen=false` versteckt die Gruppe für Spieler, löscht nichts |
| DELETE | `/{gruppe_id}` | SL | Gruppe samt Verlauf löschen (204) |
| POST | `/{gruppe_id}/teilnehmer` | SL | `{personId}` aufnehmen (PC oder NPC) |
| DELETE | `/{gruppe_id}/teilnehmer/{person_id}` | SL | entfernen; er verliert den Zugriff |
| GET | `/{gruppe_id}/chat` | Mitglied / SL | Verlauf. Für Spieler gilt er damit als gelesen. Antwort: `{gruppe, nachrichten, sprecher}`; `sprecher` nur für die SL (NPC-Mitglieder) |
| POST | `/{gruppe_id}/chat` | Mitglied / SL | `{inhalt, alsPersonId?}`. Spieler: immer als eigener Charakter (`alsPersonId` → 403). SL: `alsPersonId` muss ein NPC-Mitglied sein (sonst 400). Geschlossene Gruppe → 409 |

Neue Mitglieder sehen den ganzen Verlauf. Ihr `gelesenBis` startet beim Beitritt, die alte
Historie zählt also nicht als ungelesen.

## Datenmodell

```
(:Gruppenchat {id, campaignId, name, offen, erstelltAm})-[:TEILNEHMER {gelesenBis, beigetretenAm}]->(:Person)
(:Nachricht)-[:VON]->(:Person)
(:Nachricht)-[:IN]->(:Gruppenchat)
```

Gruppennachrichten haben kein `AN` und erscheinen deshalb in keiner Einzelchat-Abfrage.

## Benachrichtigung

Über das Mitteilungen-System (`art=NACHRICHT`). Der Text enthält nur den Gruppennamen, keinen
Absender. Spieler schreibt → die anderen PC-Mitglieder, und die SL, wenn mindestens ein NPC in
der Gruppe sitzt. SL schreibt → die PC-Mitglieder.
