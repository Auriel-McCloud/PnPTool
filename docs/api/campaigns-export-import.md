# Kampagnen-Export/Import

Eine komplette Kampagne (alle Knoten, Kanten, Bilder und Spieler-Accounts)
als ZIP-Datei sichern und als **neue** Kampagne wiederherstellen — z.B. für
Backups, Umzug auf eine andere Neo4j-Instanz, oder um eine Kampagne mit einer
anderen Spielrunde als Vorlage zu teilen.

## Konzept

**Zwei generische Cypher-Abfragen statt eines Sonderfalls je Entitätstyp.**
Die meisten Knotentypen tragen `campaignId` direkt als Eigenschaft (Person,
Ort, Event, Fraktion, Gegenstand, Party, Begleiter, WikiSeite, Mitteilung,
Verhandlung, Kampf, Nachricht) — ein einziges `WHERE n.campaignId =
$campaign_id` erfasst sie alle. Zwei Ausnahmen ohne dieses Feld werden
explizit nachgezogen: `Spieler` (nur über `GEHOERT_ZU` erreichbar) und
`KampfTeilnehmer` (nur über `Kampf-[:KAEMPFT]->`). Der `Campaign`-Knoten
selbst kommt als drittes Element dazu.

Kanten werden ebenso generisch eingesammelt: alle ausgehenden Kanten jedes
gefundenen Knotens. Das erfasst auch Kanten zu **globalen Katalogknoten**
(`Rasse`, `TraitDef`, `Regelsystem`) — deren IDs werden beim Import bewusst
**nicht** neu vergeben (sie sind kein Teil der Kampagne, sondern ein
gemeinsamer Katalog, der in der Zieldatenbank bereits existieren muss, z.B.
durch `seed_traits`/`seed_rassen`/`seed_neotopia` beim Backend-Start).
Existiert ein solcher Katalogknoten in der Zieldatenbank nicht (z.B. anderes
Regelsystem), fällt die betroffene Kante beim Import kommentarlos weg —
der Import bricht deswegen nicht ab.

**ID-Neuvergabe per Text-Ersetzung statt Feld-für-Feld-Mapping.** Jede
Referenz auf eine kampagnen-eigene ID — als Kanten-Endpunkt, als
`campaignId`-Eigenschaft, aber auch versteckt in einer JSON-als-Text
gespeicherten Liste (`sichtbarFuer`, `empfaengerIds`, `gelesenVon`,
`stammtId` eines Kampfteilnehmers, Bild-URLs mit der Kampagnen-ID im Pfad) —
ist im rohen JSON-Text einfach die UUID als Zeichenkette. Eine einzige
Ersetzungsrunde über den gesamten Rohtext, bevor er wieder geparst wird,
trifft daher jede dieser Stellen auf einmal. Kollisionen sind praktisch
ausgeschlossen (UUIDv4, 122 Zufallsbits).

**Sicherheit gegen manipulierte Importpakete:** `KNOWN_LABELS`/
`KNOWN_REL_TYPES`-Weisslisten in `export_import.py` — Cypher kann Labels und
Beziehungstypen nicht parametrisieren (nur Eigenschaftswerte), ein
unbekanntes Label/ein unbekannter Kantentyp im Importpaket bricht den
Import sofort mit `ValueError` ab, statt den Namen ungeprüft in die Abfrage
einzusetzen.

## Endpunkte

### GET `/api/campaigns/{campaign_id}/export` — **Nur SL dieser Kampagne**

Liefert die ZIP-Datei direkt als Download (`Content-Disposition: attachment`).
Cookie-Auth reicht — ein normaler `<a href>`-Klick im Frontend funktioniert
ohne Umweg über `fetch`/Blob.

Enthält:
- `manifest.json` — Format-Version, Exportzeitpunkt, Kampagnenname/-ID,
  Regelsystem, Anzahl Knoten/Kanten/Bilder (Übersicht ohne die große
  `daten.json` parsen zu müssen)
- `daten.json` — `{"nodes": [...], "edges": [...]}`, jeweils mit
  `labels`/`props` (Knoten) bzw. `fromId`/`relType`/`toId`/`props` (Kanten)
- `bilder/*` — alle Bilddateien aus `uploads/{campaign_id}/`

### POST `/api/campaigns/import` — **jeder eingeloggte SL**

Multipart-Upload (`datei`, max. 200 MB). Legt **immer** eine neue Kampagne
mit neuer ID an, die ausschliesslich dem importierenden SL gehört
(`OWNS`-Kante) — es wird nie eine bestehende Kampagne überschrieben (Marks
Entscheidung, um versehentlichen Datenverlust auszuschliessen). Antwort:
`{"id": "uuid", "name": "...", ...}` (`CampaignResponse`).

Muss vor `/{campaign_id}/export` registriert sein (FastAPI matcht nach
Registrierungsreihenfolge, nicht Spezifität — sonst würde `campaign_id`
fälschlich auf `"import"` matchen).

Fehlerfälle (alle `400 Bad Request` mit Klartext-`detail`):
- ZIP ohne `manifest.json`/`daten.json`
- unbekannte `formatVersion`
- Kampagnen-ID aus `manifest.json` fehlt in `daten.json`
- unbekanntes Knoten-Label / unbekannter Kantentyp im Paket

## Datenmodell / Ablauf

```
export_campaign_zip(campaign_id)
  → collect_campaign_graph()      # generische Cypher-Sammlung, s.o.
  → manifest.json + daten.json + bilder/ ins ZIP (in-memory, io.BytesIO)

import_campaign_zip(zip_bytes, gm_id)
  → ZIP lesen, Format-Version prüfen
  → remap_ids(daten.json-Text, alte_campaign_id)   # reine Funktion, keine DB
      - prüft alle Labels/Kantentypen gegen die Weisslisten
      - vergibt jeder kampagnen-eigenen ID eine frische UUID (Text-Ersetzung)
  → Bilder nach uploads/{neue_campaign_id}/ entpacken (pfad-ausbruchsicher:
    Dateiname darf kein "/" oder "\" enthalten)
  → Knoten per CREATE (n:Label1:Label2) SET n = $props anlegen
  → Kanten per MATCH+MATCH+CREATE anlegen (fehlt ein Zielknoten — z.B. ein
    globaler Katalogknoten, der in dieser DB nicht existiert — fällt nur
    diese eine Kante weg, der Import läuft weiter)
  → (:GMUser)-[:OWNS]->(:Campaign) für den importierenden SL anlegen
```

`remap_ids` ist bewusst von der Datenbank getrennt (reine Funktion über
Text/JSON) — dadurch ohne laufende Neo4j-Instanz testbar
(`backend/tests/test_campaign_export_import.py`).

## Frontend

`frontend/src/campaigns/einstellungen.ts` (`kampagnenExportApi`) +
`EinstellungenFenster.tsx` (neue Sektion „KAMPAGNE“ nach „MUSIK“):

- **Export:** Knopf „⬇ Kampagne exportieren“ — erzeugt einen unsichtbaren
  `<a href="/api/campaigns/{id}/export" download="...">`-Anker und klickt
  ihn programmatisch (Cookie-Auth läuft automatisch mit).
- **Import:** `<label class="cl-roehre">` mit verstecktem
  `<input type="file" accept=".zip">` — Multipart-Upload per `fetch`.
  Nach Erfolg: `useCampaign().nachImportUebernehmen(neueId)` lädt die
  Kampagnenliste neu und wechselt automatisch zur frisch importierten
  Kampagne (Dropdown in der Kopfleiste).

## Verifiziert (24.09.2026, nachts)

- 6 Unit-Tests für `remap_ids`/Weisslisten (`test_campaign_export_import.py`)
- Echter End-to-End-Lauf gegen laufendes Backend + echte Neo4j: Kampagne mit
  PC, NPC, Ort, Gegenstand, Wiki-Seite, Spieler-Account angelegt → exportiert
  → importiert → alle Entitäten mit neuen IDs, referenzielle Integrität
  (Kanten zeigen auf die neuen IDs), globale Katalogdaten (Regelsystem,
  TraitDefs, Rassen) unverändert. **Alle Prüfungen bestanden.**
- Beide Testkampagnen (Original + Import) danach aus der echten Neo4j
  wieder entfernt — keine Testdaten zurückgeblieben.
- `tsc -b` fehlerfrei, Backend-Import + Routen im OpenAPI-Schema geprüft.
- **Offen:** kein Klicktest von Export-Knopf/Import-Upload im laufenden
  Frontend (nur `tsc -b` + Backend-E2E). Mark sollte am Dev-Server einmal
  echt klicken, v.a. ob der Download-Dateiname stimmt und die
  Erfolgsmeldung nach Import erscheint.
