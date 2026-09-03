# Phase 5: Messenger und Kontakte

**Status:** Regeln beschlossen, Implementierung läuft  
**Stand:** 03.09.2026

## Zielbild

PnPTool bekommt einen In-World-Messenger im Commlink-Stil. PCs können mit NPCs
schreiben, sobald die SL eine Kontaktanfrage als dieser NPC angenommen hat. Die
SL schreibt im Messenger immer als ausgewählter NPC. Eine direkte Mitteilung der
SL hat keinen Absender und wird später als Popup/Benachrichtigung umgesetzt
(z.B. „Würfelt für Initiative“, Warnung, Bild oder Map).

Der Chat ist ein eigenes Fenster. Nur der Nachrichtenverlauf darf darin intern
scrollen; Hauptansicht und Seitenkörper behalten den bestehenden „nie scrollen“-
Grundsatz.

## Kontaktwissen und Neo4j-Modell

Kontaktwissen betrifft ein PC-NPC-Paar. Da das Wissen in diesem MVP vom PC über
den NPC geführt wird, gibt es genau **eine kanonische Beziehung**:

```text
(:Person {personType: "PC"})-[:KENNT {
  id: "...",
  stufe: "GESEHEN" | "GESPROCHEN" | "KONTAKT_AUSGETAUSCHT",
  echterNameBekannt: false,
  kontaktAnfrageStatus: "KEINE" | "AUSSTEHEND" | "ANGENOMMEN" | "ABGELEHNT",
  alias: "<persönlicher Alias oder leer>",
  persoenlicheNotizen: "<TipTap-JSON>",
  erstelltAm: "...",
  aktualisiertAm: "..."
}]->(:Person {personType: "NPC"})
```

Die Beziehung wird nicht gespiegelt. „Beidseitig“ beschreibt die Berechtigung,
nach angenommener Anfrage in demselben Chat in beide Richtungen zu schreiben;
es bedeutet keine zweite Graphkante und kein zweites Wissensobjekt.

Die Stufen bedeuten:

1. **GESEHEN** — automatisch aus einem sichtbaren Graphweg oder bewusst durch
   die SL angelegt. Der Spieler sieht Alias, Bild und freigegebene
   Erscheinungsbeschreibung, aber nicht den echten Namen.
2. **GESPROCHEN** — die SL markiert, dass das Gespräch stattgefunden hat.
   Freigegebene allgemeine NPC-Notizen werden sichtbar.
3. **KONTAKT_AUSGETAUSCHT** — die SL nimmt die Kontaktanfrage des Spielers als
   den ausgewählten NPC an. Der Einzelchat ist für beide Seiten freigeschaltet.

`echterNameBekannt` ist unabhängig von der Stufe eine eigene SL-Checkbox. Ist
sie aus, wird der echte Name serverseitig nicht in eine Spielerantwort
aufgenommen.

## NPC-Standard und persönlicher Alias

Der NPC-Knoten enthält die gemeinsamen Fakten:

- `name`: echter Name, ausschließlich serverseitig nach der Namensfreigabe;
- `alias`: gemeinsamer Standardalias;
- `bildUrl`: gemeinsames Bild/Aussehen;
- `description`: gemeinsame Erscheinungsbeschreibung und allgemeine Daten;
- `rasse`: Grundlage für einen Startwert wie „Unbekannter Ork“ oder
  „Unbekannte Person“.

Beim Anlegen eines NPCs wird ein Standardalias erzeugt, wenn die SL keinen
Alias angibt. Die SL kann diesen Standard ändern. Jeder PC kann zusätzlich auf
seiner `KENNT`-Beziehung einen persönlichen Alias setzen; die SL kann den Alias
für genau diesen PC ebenfalls ändern. Ist kein persönlicher Alias gesetzt,
gilt der NPC-Standard. Der persönliche Alias bleibt auch nach Bekanntwerden des
echten Namens erhalten. Die Antwort liefert den echten Namen getrennt und nur,
wenn er sichtbar sein darf, damit die Oberfläche Alias und echten Namen
nebeneinander darstellen kann.

Spieler ändern nur ihren eigenen persönlichen Alias. Die Änderung des
NPC-Standards bleibt eine SL-Aktion, weil sie alle Kontakte ohne persönlichen
Override betrifft.

## Allgemeine und persönliche Notizen

Allgemeine Notizen hängen als eigene Knoten am NPC, damit mehrere Beiträge,
Autoren und Freigaben möglich sind:

```text
(:Person {personType: "NPC"})-[:HAT_NOTIZ]->(:NpcNotiz {
  id: "...",
  inhalt: "<TipTap-JSON>",
  autorPersonId: "<PC-ID>" | null,
  autorRolle: "PLAYER" | "GM",
  freigegeben: false | true,
  erstelltAm: "...",
  aktualisiertAm: "..."
})
```

Spieler dürfen eigene allgemeine Notizen anlegen und bearbeiten. Die SL kann
alle Notizen bearbeiten und jede einzeln freigeben oder zurücknehmen. Ein
Spieler sieht eigene Entwürfe sofort; fremde Beiträge erst nach Freigabe und
ab `GESPROCHEN`. Die SL sieht alle Beiträge.

Persönliche Notizen liegen auf der eigenen `KENNT`-Beziehung. Sie sind nur für
den zugehörigen Spieler und die SL sichtbar und editierbar. Sie werden nie als
allgemeine NPC-Notiz veröffentlicht.

## Automatisches GESEHEN aus dem Beziehungsgraphen

Für jeden PC können **sichtbare** `VERBINDUNG`-Kanten einen ungerichteten Weg
bilden. Sichtbar bedeutet: Die Kante und beide Endpunkte wären für diesen PC
sichtbar (`ALLE` oder passende `SPEZIFISCH`-Freigabe). Der Beziehungstyp bleibt
rein beschreibend; auch Feindschaft oder Besitz kann Teil des Weges sein.

Die Suche läuft maximal über **sieben Kanten**. Orte und Events erhalten das
zusätzliche Feld `kontaktwissenWeitergeben` (Standard `true`). Wird es bei einem
Ort oder Event deaktiviert, darf der Weg diesen Knoten zwar erreichen, dort aber
nicht weiterlaufen. Das gilt auch für Bestandsdaten ohne dieses Feld, die aus
Kompatibilitätsgründen als `true` behandelt werden.

Beim ersten gültigen Weg wird genau eine PC→NPC-`KENNT`-Beziehung mit `GESEHEN`
angelegt. Eine vorhandene Beziehung wird durch die Automatik niemals
hochgestuft, zurückgesetzt oder gelöscht. `GESPROCHEN`, Namenskenntnis und
`KONTAKT_AUSGETAUSCHT` bleiben bewusste Aktionen der SL bzw. der
Kontaktanfrage.

Temporäre Parties werden noch nicht modelliert. Wenn sie später existieren,
können sie als eigene Graphknoten in dieselbe Wegsuche einbezogen werden.

## Kontaktanfrage und Messenger

Ein Spieler kann ab `GESPROCHEN` eine Kontaktanfrage an einen NPC senden. Die
SL sieht ausstehende Anfragen und nimmt sie als ausgewählter NPC an oder lehnt
sie ab. Annahme setzt die bestehende Beziehung auf
`KONTAKT_AUSGETAUSCHT` und schaltet den Einzelchat in beide Richtungen frei.

Nachrichten sind eigene, unveränderliche `Nachricht`-Knoten:

```text
(:Nachricht {
  id: "...",
  campaignId: "...",
  inhalt: "<TipTap-JSON>",
  inhaltFormat: "tiptap-json",
  erstelltAm: "...",
  gelesenAm: null | "...",
  erstelltVonRolle: "PLAYER" | "GM"
})-[:VON]->(:Person)
(:Nachricht)-[:AN]->(:Person)
```

Eine SL-Nachricht zeigt niemals „Spielleitung“ als Absender: Beim Schreiben
als NPC zeigt `VON` auf den ausgewählten NPC. Absenderlose SL-Popups bleiben
eine spätere Funktion außerhalb dieses Nachrichtenmodells.

Nachrichteninhalt wird als TipTap-JSON gespeichert. Klartext ist für Tests als
einzelner Absatz kompatibel. Android-Smileys bleiben echte Unicode-Zeichen,
auch zusammengesetzte Emoji-Sequenzen und Hautfarben; sie werden nicht in
Bilddateien oder `:codes:` umgewandelt.

## Bewusste Nicht-Ziele der ersten Runde

- temporäre Parties und deren eigenes Datenmodell,
- direkte SL-Popups, Bilder und Maps als Benachrichtigung,
- WebSocket-Live-Zustellung,
- Gruppen-Chats, Anhänge, Bearbeiten/Löschen gesendeter Nachrichten,
- öffentliche Kontaktsuche.
