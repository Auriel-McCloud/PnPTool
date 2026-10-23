# Kampagnen-Bündel: Export und Import wiederverwendbarer Welt-Inhalte

Teilt eine Auswahl wiederverwendbarer Welt-Inhalte als ZIP mit anderen
Kampagnen/Runden (z.B. per GitHub-Download) — bewusst getrennt vom
kompletten Kampagnen-Export/-Import (`docs/api/kampagnen.md`), der immer
die GANZE Kampagne inkl. Spielstand sichert/klont. Code:
`backend/app/campaigns/buendel_export.py` (Phase 1),
`backend/app/campaigns/buendel_import.py` (Phase 2),
`frontend/src/buendel/`.

---

## Konzept

**Neun Bündel-Typen, bewusst ohne Spielstand:** Ort, Gegenstand, Fraktion,
Person (NPC + Begleiter/Critter — **nicht** PC), Gewaechs, Event,
WikiSeite, Rasse, Achievement-**Definitionen** (nicht
`AchievementVerleihung`, die ist reine Spielstand-Historie pro PC). PCs,
Kämpfe, Verhandlungen und Spieler-Accounts sind nie Teil eines Bündels —
ein Bündel ist Welt-Material zum Weitergeben, kein Kampagnen-Klon.

**Eigene, kleinere Weisslisten statt die große Kampagnen-Export-Liste.**
`BUENDEL_LABELS`/`BUENDEL_REL_TYPES` in `buendel_export.py` sind bewusst
NICHT dieselben wie `export_import.KNOWN_LABELS`/`KNOWN_REL_TYPES` — eine
künftige Änderung an der großen Weissliste (neuer Spielstand-Knotentyp)
soll dieses Feature nicht stillschweigend mitreißen, und umgekehrt.

**Rasse ist campaign-SCOPELESS** (globaler Ruleset-Katalog, siehe
`docs/api/rassen.md`) — anders als die anderen acht Typen trägt sie kein
`campaignId`. Kandidaten für den Export kommen über die
`(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`-Kante der Quellkampagne, nicht
über einen `campaignId`-Filter.

**Kanten nur zwischen zwei ausgewählten Knoten.** Eine Kante, deren Ziel
nicht selbst Teil der Auswahl ist (z.B. zu einem bewusst ausgeschlossenen
PC), wird beim Export abgeschnitten — beim Re-Import in eine fremde
Kampagne wäre sie ohnehin nicht auflösbar.

**Bündel-Bildschirm ist ein invertierter Picker:** beim Export ist
zunächst alles vorausgewählt, die Spielleitung hakt ab, was NICHT mit
soll (`ausgeschlosseneIds`). Rassen, die nur über den Text
`Person.rasse` referenziert werden (keine eigene Kante), zeigen dort
einen "automatisch, weil von N NPCs benutzt"-Hinweis.

## stammtVonId — die stabile Herkunfts-Kennung

Jeder Knoten der neun Bündel-Typen trägt seit diesem Feature zusätzlich
zu seiner echten `id` ein `stammtVonId`-Feld:

- **Neue Knoten** bekommen `stammtVonId = id` direkt bei der Erstellung
  (`entities/repository.py::create_node` und die Pendants in
  `items/`, `wiki/`, `rassen/`, `achievements/repository.py`).
- **Bestandsknoten** wurden durch die Migration
  `backend/app/db/migrations/013_buendel_stammt_von_id.cypher`
  nachgezogen (`SET n.stammtVonId = n.id WHERE n.stammtVonId IS NULL`,
  idempotent).
- Der Grund für ein zweites Feld statt einfach `id` zu nehmen: `id` wird
  bei jedem Import **neu vergeben** (jede Zielkampagne bekommt ihre
  eigene UUID), `stammtVonId` wandert dagegen unverändert mit — sie ist
  der Anker, über den ein künftiger Re-Import denselben Inhalt
  wiedererkennt, egal wie oft er schon kopiert wurde.

## Import-Abgleich: neu, überspringen oder aktualisieren

Ein eingehender Knoten gilt als "schon vorhanden", wenn die Zielkampagne
(bzw. bei Rasse: **irgendeine** Kampagne, siehe unten) bereits einen
nicht gelöschten Knoten desselben Labels mit derselben `stammtVonId` hat.
Der Modus gilt für den **gesamten Lauf**, nicht pro Knoten:

| Modus | Verhalten bei Treffer |
|---|---|
| `ueberspringen` (Standard) | Bestehender Knoten bleibt komplett unangetastet. |
| `aktualisieren` | Der aktuelle Stand wird zuerst unverändert als neuer, separater Knoten mit `geloescht: true` in den Papierkorb kopiert (eigene frische `id`, sonst identische Properties) — **danach** werden die Properties des echten, bestehenden Knotens mit den Bündel-Werten überschrieben. `id`, `stammtVonId`, `campaignId` und `istEntwurf` des echten Knotens bleiben dabei unverändert (ein Update ist kein neuer Entwurf). |

**Rasse ist die eine Ausnahme vom "pro Zielkampagne"-Scoping:** der
Abgleich läuft dort campaign-UNABHÄNGIG rein über `stammtVonId` — ein
zweiter GM, der dasselbe Bündel in eine andere Kampagne importiert,
findet die vom ersten Import bereits angelegte Rasse wieder statt sie zu
duplizieren. Eine neu angelegte ODER wiedergefundene Rasse wird
zusätzlich automatisch für die Zielkampagne freigegeben
(`MERGE (:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`, idempotent, unabhängig
vom gewählten Modus).

**Kanten** zwischen zwei importierten Knoten werden per
`MERGE ... ON CREATE SET` angelegt — ein erneuter Import derselben
Kante legt kein Duplikat an und überschreibt auch keine vom GM
inzwischen von Hand geänderte Kanteneigenschaft.

## Ideenschmiede-Umschalter (istEntwurf)

Gilt **nur für brandneu angelegte Knoten**, nicht für Updates. Nur die
sieben Typen, die das Feld laut ihren echten Schemas überhaupt kennen,
werden gesetzt — gegen den realen Code geprüft, nicht angenommen:

- **Kennen `istEntwurf`:** Ort, Gegenstand, Fraktion, Person, Gewaechs,
  Event, WikiSeite.
- **Kennen es NICHT, landen immer live:** Rasse (globaler Katalog, nur
  Freigabe-Mechanik), Achievement (Definition, kein Entwurfs-Konzept).

## Papierkorb-Retrofit (Voraussetzung für die sichere Update-Option)

Damit "aktualisieren" einen alten Stand wirklich sichern kann statt ihn
zu zerstören, nutzen Ort, Fraktion, Event, Gewaechs, NPC
(`entities/repository.py`), WikiSeite, Rasse und Achievement-Definitionen
jetzt `geloescht: true` statt hartem `DETACH DELETE` — wie es bei
Gegenstand (`weggeworfen`) und `AchievementVerleihung` bereits üblich
war. `list_nodes`/`get_node` filtern `geloescht` automatisch heraus.

**PCs sind davon bewusst ausgenommen** (eigener harter Pfad in
`delete_node`, geprüft über `Person.personType`): ein hartes Löschen hat
bisher implizit auch die `(:Spieler)-[:SPIELT]->(:Person)`-Bindung
mitgerissen, wodurch der Spieler nach dem Löschen seines Charakters
wieder im Ersteinstieg landete. Mit reinem `geloescht`-Setzen bliebe diese
Kante stehen und der Spieler schiene weiter an seinen (jetzt im
Papierkorb liegenden) alten Charakter gebunden — ein Verhaltensbruch
außerhalb des Bündel-Scopes. PCs behalten deshalb unverändert den alten
harten `DETACH DELETE`-Pfad.

## Sicherheit beim Import

Ein Bündel-ZIP kann aus einer fremden, nicht vertrauenswürdigen Quelle
stammen (Mark will Bündel auf GitHub veröffentlichen). Deshalb:

- Jedes Knoten-Label und jeder Kantentyp wird vor jeder Cypher-Nutzung
  gegen `BUENDEL_LABELS`/`BUENDEL_REL_TYPES` geprüft. Jede Abweichung
  bricht den **gesamten** Import mit `400` ab — kein stillschweigendes
  Überspringen einzelner Knoten.
- Bild-Dateien aus dem ZIP werden ausbruchsicher entpackt (kein
  Pfadsegment darf den Zielordner verlassen), analog zu
  `export_import.py::import_campaign_zip`.
- Dateigröße ist auf 200 MB begrenzt (`MAX_IMPORT_BYTES`, dieselbe
  Grenze wie beim vollen Kampagnen-Import).

## Bild-Pfade

Anders als bei IDs (die pro Knoten einzeln behandelt werden müssen) gibt
es im ganzen Bündel genau **eine** Kampagnen-ID im Pfad
(`herkunftCampaignId` aus dem Manifest) — die wird vor dem JSON-Parsen
blind per Text-Ersetzung auf die Ziel-Kampagnen-ID umgeschrieben
(`/uploads/{herkunftCampaignId}/...` → `/uploads/{campaignId}/...`),
dieselbe Technik wie bei `remap_ids`, nur für einen Pfad-Baustein statt
für IDs. Referenzierte Bilddateien werden aus dem ZIP nach
`uploads/{campaignId}/` kopiert.

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/buendel` — alle drei nur für die
Spielleitung dieser Kampagne (`require_campaign_gm`).

| Methode | Pfad | Zweck |
|---|---|---|
| POST | `/export` | Baut das ZIP (`manifest.json` + `daten.json` + `bilder/`) aus der Auswahl und liefert es zum Download. Body: `{ name, beschreibung, tags, ausgeschlosseneIds }`. |
| POST | `/import/vorschau` | Liest ein Bündel-ZIP (multipart `datei`) und meldet Inhalt + Abgleich-Status (neu vs. vorhanden, pro Typ), **ohne zu schreiben**. Optionaler Zwischenschritt, kein Pflichtaufruf vor dem eigentlichen Import. |
| POST | `/import` | Importiert ein Bündel-ZIP in **diese** (bestehende) Kampagne. Multipart: `datei`, `modus` (`"ueberspringen"` \| `"aktualisieren"`, Default `ueberspringen`), `ideenschmiede` (bool, Default `false`). Liefert `{ neu, aktualisiert, uebersprungen, proTyp, bundleName, herkunftCampaignName }`. |

Es gibt bewusst **keinen Kampagnen-Picker** beim Import — das Bündel geht
immer in die Kampagne, deren Bündel-Bildschirm die Spielleitung gerade
offen hat (Marks Entscheidung).

Fehlerfälle: `400` bei zu großer Datei (>200 MB), fehlendem/falschem
ZIP-Inhalt (`manifest.json`/`daten.json` fehlt, unbekannte
Format-Version) oder einer Weisslisten-Verletzung (unbekanntes Label/
Kantentyp, Knoten ohne `stammtVonId` — kein gültiges Bündel-Paket).

## Datenmodell (ZIP-Aufbau)

```
buendel-<slug>-<zeitstempel>.zip
├── manifest.json   { formatVersion, exportedAt, name, beschreibung, tags,
│                     herkunftCampaignId, herkunftCampaignName,
│                     anzahlKnoten, anzahlProTyp }
├── daten.json      { nodes: [{ id, labels, props }],
│                     edges: [{ fromId, relType, props, toId, toLabels }] }
└── bilder/
    └── <dateiname>  // nur Bilder, die zu einem exportierten Knoten gehören
```

```cypher
// stammtVonId an jedem der neun Bündel-Typen, zusätzlich zur echten id:
(:Ort|:Gegenstand|:Fraktion|:Person|:Gewaechs|:Event|:WikiSeite|:Rasse|:Achievement {
  id: "uuid",            // bei jedem Import neu vergeben
  stammtVonId: "uuid",   // wandert unverändert mit, Anker für Re-Import-Abgleich
  ...
})
```

## Verifiziert

**Phase 1 (Export, 23.10.2026):** `backend/tests/test_buendel_export.py`
(13 Fälle inkl. Regressionstest für den PC/`SPIELT`-Fix beim
Papierkorb-Retrofit), `test_achievements.py` an das neue
Papierkorb-Verhalten angepasst, volle Suite gegen `main`-Baseline
gegengeprüft — keine neuen Fehlschläge gegenüber der Baseline. `tsc -b`
sauber.

**Phase 2 (Import, 23.10.2026):** `backend/tests/test_buendel_import.py`
(7 Fälle gegen echtes Neo4j: Neuanlage in leere Zielkampagne, globaler
Rasse-Re-Fund statt Duplikat, Re-Import im Skip-Modus ohne Duplikate,
Re-Import im Aktualisieren-Modus mit Papierkorb-Sicherung einer lokalen
Änderung, Weisslisten-Ablehnung, `istEntwurf`-Scope, Vorschau-Funktion),
`tsc -b`/`vite build` sauber. **Echter Browser-Rundlauf** über eine
Wegwerf-SL mit zwei frischen Testkampagnen: Export A → Import B neu →
Re-Import Skip ohne Duplikate → lokale Bearbeitung + Re-Import
Aktualisieren mit belegtem Papierkorb-Eintrag.

**Merge in `main` + Live-Deploy (23.10.2026):** Merge mit
`origin/main` (3 zwischenzeitliche Commits, u.a. "Aktive Party von
Ort/Event aus verknüpfbar") sauber automatisch aufgelöst — die
Änderungen lagen an denselben Dateien (`entities/repository.py`,
`EventDetail.tsx`, `OrtDetail.tsx`), aber in nicht überlappenden
Bereichen, keine Konfliktmarker. Volle Backend-Suite auf dem gemergten
Stand erneut laufen lassen: 44 Fehlschläge, aber **identisch** reproduzierbar
auf vanilla `main` vor diesem Feature und auf dem ungemergten Feature-
Branch selbst — derselbe vorbestehende `asyncio.run()`-pro-Test +
Treiber-Singleton-Lauf-Flake wie bei `test_shop_am_ort.py`
(Stolperstein 8), kein durch den Merge verursachter Regressionsfehler.
Nach dem Deploy: Migration `013_buendel_stammt_von_id` lief beim
Backend-Neustart automatisch (bestätigt per Live-Datenabgleich, nicht
per Logzeile — `apply_migrations()` loggt grundsätzlich keine
Migrationsnamen, das gilt für alle 13 Migrationen gleich, nicht nur
diese); alle Bestandsknoten der neun Typen tragen jetzt `stammtVonId`
(stichprobenartig gegen live Neo4j geprüft, 100% Abdeckung über alle
acht geprüften Typen mit Bestandsdaten).

## Noch offen

- Kein Kampagnen-Picker beim Import ist eine bewusste Phase-2-Grenze
  (siehe oben) — ein künftiger "in eine NEUE Kampagne importieren"-Weg
  wäre eine eigene, kleine Erweiterung auf derselben `buendel_import.py`.
- Bündel-Veröffentlichung/-Katalog auf GitHub (Marks Idee, Teilen mit
  anderen Runden) ist reiner Datei-Download/-Upload — kein eigener
  Hosting-/Katalog-Mechanismus im Tool selbst.
