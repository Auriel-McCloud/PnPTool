# Phase 5: Messenger und Kontakte

**Status:** vorgemerkt, noch nicht implementiert  
**Stand:** 02.09.2026

## Zielbild

PnPTool bekommt einen In-World-Messenger im Commlink-Stil. PCs und NPCs sollen
sich Einzelmitteilungen schicken können; PCs sollen auch untereinander
schreiben können. Die Spielleitung kann Nachrichten direkt an Spieler schicken
oder als NPC auftreten. Ein Chatfenster mit Nachrichtenblasen, Zeit-/Tages-
trennern und Portraits darf sich an der Wirkung von *Persona 5* orientieren,
übernimmt aber keine geschützten Grafiken oder konkrete UI-Assets.

Im bestehenden Bereich **Kontakte** bekommt jeder erreichbare Kontakt eine
Aktion **Message**. Die Unterhaltung öffnet sich als eigenes Fenster. Der
Verlauf darf innerhalb dieses Fensters scrollen; die Hauptansicht und der
Seitenkörper dürfen dadurch nicht scrollen.

## Kontaktwissen ist personenbezogen und abgestuft

Das bestehende `VERBINDUNG`-Modell beschreibt das Wissen der Spielleitung über
die Welt. Es ist nicht geeignet, um abzubilden, was *eine bestimmte Figur* über
eine andere weiss. Kontaktwissen muss daher gerichtet sein: A kann B kennen,
während B A noch nicht kennt.

Für den ersten Entwurf sind drei Stufen vorgemerkt:

1. **GESEHEN** — A hat B gesehen. Angezeigt werden ein Bild und eine vom
   Spielleiter gepflegte Beschreibung oder ein Alias, z.B. „Troll aus der
   3-Heavens-Bar“. Der echte Name wird nicht angezeigt. Nachrichten sind noch
   nicht möglich.
2. **GESPROCHEN** — A und B haben miteinander gesprochen. Die Spielleitung
   kann für A einen Namen und eine Beschreibung freigeben oder eintragen.
3. **KONTAKT_AUSGETAUSCHT** — A besitzt die Kontaktdaten von B und darf über
   den Messenger Nachrichten empfangen bzw. senden, soweit die noch offene
   Berechtigungsentscheidung das erlaubt.

Die Namen der Stufen sind Vorschläge und werden vor der Implementierung noch
bestätigt. Entscheidend ist: Anzeigename, Beschreibung und Bild sind Wissen
von A über B und dürfen nicht einfach ungefiltert aus Bs vollständigem
Personenknoten kommen. Ein NPC kann deshalb für verschiedene PCs
unterschiedlich beschrieben sein.

### Vorgeschlagene technische Form

Für die MVP-Version reicht voraussichtlich eine gerichtete Beziehung:

```text
(Person A)-[:KENNT {
  stufe,
  angezeigterName,
  beschreibung,
  bildUrl
}]->(Person B)
```

Das ist einfacher als ein zusätzlicher Kontaktknoten und bildet den häufigsten
Fall — einen aktuellen Wissensstand je Quelle und Ziel — direkt ab. Falls später
Wissensverlauf, mehrere Aliase oder Kontaktaufnahmen als Ereignisse gebraucht
werden, kann daraus ein eigener `Kontaktwissen`-Knoten werden. Diese Entscheidung
ist vor dem Bauen zu bestätigen.

## Nachrichtenmodell

Nachrichten sind unveränderliche `Nachricht`-Knoten in der Kampagne. Sie
verweisen auf Absender und Empfänger; der Absender kann eine Person (PC/NPC)
oder die Spielleitung selbst sein. Für den ersten Schritt sind Einzelchats
vorgesehen, keine Gruppenunterhaltungen.

Vorgemerkte Inhalte einer Nachricht:

- eindeutige ID und Kampagne,
- Absender (Person oder Spielleitung),
- Empfänger-Person,
- Text,
- Erstellungszeitpunkt,
- optionaler Lesezeitpunkt bzw. ungelesen-Status.

Die Anzeige einer Unterhaltung wird zunächst aus den Nachrichten zweier
Teilnehmer abgeleitet. Ein eigener `Konversation`-Knoten ist erst nötig, wenn
Gruppenchats, archivierte Threads oder zusätzliche Chat-Metadaten dazukommen.

## Berechtigungen

Die Regeln müssen serverseitig gelten; die Oberfläche darf nur zusätzlich
Buttons ausblenden:

- Die Spielleitung sieht alle Kontakte und Nachrichten der Kampagne und darf
  direkt an einen PC schreiben oder als NPC senden.
- Ein Spieler sieht nur sein eigenes Kontaktwissen und Nachrichten, an denen
  seine zugeordnete Person beteiligt ist.
- Ein Spieler darf nicht über `alsSpieler` oder eine fremde Personen-ID in
  andere Unterhaltungen wechseln.
- Das Senden an eine Person soll an die Kontaktstufe gekoppelt sein. Ob dafür
  nur der sendende Charakter `KONTAKT_AUSGETAUSCHT` haben muss oder beide Seiten
den Kontakt bestätigt haben müssen, ist eine offene Regelentscheidung.
- Die SL-Vorschau bleibt lesend. Ein Vorschauwechsel darf keine Nachrichten
  erzeugen oder den Kontaktstatus verändern.

## UI-Vorgaben

- Der Kontaktbereich bleibt eine eigene Commlink-Ansicht und darf eine interne
  Liste mit `overflow-y: auto` haben.
- Beim Öffnen einer Unterhaltung erscheint ein Fenster mit fester Fläche und
  internem Chatverlauf. Nur dieser Verlauf scrollt; Kopfzeile und Eingabefeld
  bleiben erreichbar.
- Die Seite bzw. der gesamte Shell-Körper erhält für diesen Bereich keinen
  zusätzlichen Gesamt-Scrollbalken. Das folgt dem bestehenden Grundsatz:
  Übersichten teilen sich die Bildschirmfläche ein, lange Inhalte liegen in
  Fenstern.
- Nachrichtenblasen unterscheiden Absender und Empfänger klar. Portrait,
  Alias und unbekannte Identität müssen zur jeweiligen Kontaktstufe passen.
- Neue Nachrichten werden über das bereits vorgesehene Blitz-/Popup-Symbol
  angekündigt. Das Popup soll von diesem Symbol aus aufgehen und minimierbar
  sein — das verbindet den Messenger mit der allgemeinen Phase-5-Live-
  Infrastruktur.

## Reihenfolge der Umsetzung

1. Kontaktstufen, gerichtete Freigabe und die Frage „einseitiger oder
   beidseitiger Kontakt“ gemeinsam festlegen.
2. Kontaktwissen als lesbare und für die Spielleitung bearbeitbare Daten
   anlegen; Sichtbarkeit und Fremdcharakter-Schutz mit Tests absichern.
3. Nachrichten-API für Einzelchats bauen: lesen, senden, ungelesen markieren;
   GM/NPC-Absender und Spielerberechtigungen getrennt testen.
4. Kontaktansicht und das intern scrollende Chatfenster bauen.
5. WebSocket-Zustellung, ungelesene Zähler und minimierbare Live-Popups in die
   vorhandene Phase-5-Infrastruktur einhängen.

Nicht Teil des ersten Messenger-Schritts sind Gruppen-Chats, Anhänge,
Nachrichtenbearbeitung, Löschen und eine öffentliche Kontakt-Suche.

## Offene Entscheidungen vor dem Bauen

- Endgültige Namen und genaue Bedeutung der drei Kontaktstufen.
- Muss ein Kontakt nur beim Sender oder auf beiden Seiten bestätigt sein?
- Darf ein PC einem NPC schreiben, sobald der PC den Kontakt hat, oder muss der
  SL den NPC-Kontakt zusätzlich freigeben?
- Schreibt die Spielleitung im Chat als „Spielleitung“, als ausgewählter NPC
  oder beides?
- Sind Nachrichten zunächst Klartext oder Rich-Text?
- Gehört ein Portrait zum Personenknoten oder zur jeweiligen
  Kontaktwissen-Beziehung?
