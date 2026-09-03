# Produktvision: Kampagnen-Wiki

**Status:** beschlossen als nächste Produkt-Richtung, Implementierung noch nicht begonnen  
**Stand:** 03.09.2026

## Ziel

PnPTool wird zu einem kampagnenbezogenen Planungs- und Wissenswerkzeug für das Schreiben und Organisieren von Geschichten. Es soll sich funktional an OneNote bzw. Google Docs orientieren, bleibt aber in das PnPTool und dessen Neo4j-Weltmodell integriert.

Das Wiki soll Geschichten, Kapitel, Szenen, Session-Notizen und Hintergrundwissen aufnehmen. Inhalte werden mit PCs, NPCs, Orten, Events, Gegenständen und später weiteren Kampagnenobjekten verknüpft.

OneNote oder Google Docs werden nicht als technische Grundlage eingebunden. Dadurch bleiben Daten, Berechtigungen, SL-Geheimnisse und Graph-Verknüpfungen im PnPTool konsistent. Export bzw. Import kann später ergänzt werden.

## Oberflächenidee

Der Wiki-Bereich läuft in der bestehenden `CommlinkShell` und erhält deren kampagnenbezogenes Theme.

- **Oben:** Dokument-Tabs, z.B. Hauptgeschichte, Kapitel, Session-Notizen, Fraktionen.
- **Links:** Seiten- und Kapitelbaum mit verschachtelten Seiten.
- **Mitte:** großer TipTap-Rich-Text-Editor.
- **Rechts:** automatisch erzeugtes Inhaltsverzeichnis und verknüpfte/referenzierende Entitäten.
- **Hauptansicht:** statisch und ohne Seiten-Scrollen, entsprechend dem Commlink-Leitbild; lange Dokumente dürfen innerhalb des Editor-/Dokumentfensters scrollen.

## Inhaltsverzeichnis

Das Inhaltsverzeichnis wird aus den Überschriften des TipTap-Dokuments erzeugt:

- `H1` = Kapitel;
- `H2` = Abschnitt;
- `H3` = Szene bzw. Unterabschnitt.

Es wird nicht separat gespeichert. Klicks springen zur jeweiligen Überschrift. So bleibt es automatisch synchron mit dem Dokument.

## Verknüpfungen

Verknüpfungen werden als echte Referenzen auf Kampagnenobjekte gespeichert und im Text anklickbar dargestellt.

Vorgesehene Eingaben:

- `[[Mr. Chrome]]` als Wiki-Link-Syntax;
- `@`-Autocomplete zur Auswahl einer Entität;
- später typisierte Schreibweise wie `NPC: Mr. Chrome` oder `Ort: Neon Alley Bar`.

Unterstützte Typen:

- PCs;
- NPCs;
- Orte;
- Events;
- Gegenstände;
- Begleiter;
- später weitere Entitätstypen.

Die Suche darf passende Entitäten vorschlagen, legt aber niemals ungefragt neue Objekte an. Überschriften- oder Text-Erkennung darf eine Verknüpfung vorschlagen; das Anlegen eines neuen Objekts benötigt immer eine Bestätigung.

Beim Speichern werden die Dokumentreferenzen zusätzlich als Graphbeziehungen gepflegt:

```text
(:Kampagne)-[:HAT_DOKUMENT]->(:Dokument)
(:Dokument)-[:HAT_SEITE]->(:WikiSeite)
(:WikiSeite)-[:ENTHÄLT]->(:WikiSeite)
(:WikiSeite)-[:VERWEIST_AUF]->(:Person|:Ort|:Event|:Gegenstand)
```

Dadurch können auf einer Entität Rückverweise angezeigt werden, z.B. „Erwähnt in: Hauptgeschichte – Kapitel 1“.

## Datenmodell-MVP

Eine Wiki-Seite enthält mindestens:

- `id`;
- `campaignId`;
- `titel`;
- `inhalt` als TipTap-JSON;
- `parentId` bzw. eine Baumbeziehung;
- `sortierung`;
- `sichtbarkeit` und `sichtbarFuer`;
- `erstelltAm`;
- `aktualisiertAm`.

Dokumente gruppieren Seiten und erhalten Tabs bzw. eine Reihenfolge. Die genaue Trennung zwischen `Dokument` und `WikiSeite` wird vor der Implementierung des Neo4j-Modells noch einmal als kleiner Fachentscheid geprüft; die Oberfläche soll diese Unterscheidung nicht unnötig sichtbar machen.

## Sichtbarkeit

- Standard für neue Dokumente und Seiten: nur Spielleitung.
- Später können Dokumente bzw. Seiten auf `ALLE` oder `SPEZIFISCH` freigegeben werden.
- Die vorhandene TipTap-Markierung `gmSecret` bleibt für geheime Textabschnitte nutzbar.
- Der Server redigiert bzw. filtert Inhalte vor der Auslieferung, nicht nur die Oberfläche.

## Kampagnenbezogenes Theme

Die bestehende Optik wird nicht als vollständig austauschbares Stylesheet behandelt. Sie besteht aktuell aus einem guten zentralen CSS-Fundament plus einigen fest eingetragenen/dynamischen Werten:

- `frontend/src/index.css`: globale CSS-Variablen, Flächen, Grundfarben, Akzente, Typografie, Formulare und globale Bewegung;
- `frontend/src/shell/commlink.css`: Commlink-Hülle, Neonröhren, responsive Navigation, Übergangsbalken, fliegender Bereichsname und Flackern;
- `CommlinkShell.tsx`/`App.tsx`: Bereichsfarben und einige dynamische Inline-Werte;
- `CampaignGraphView.tsx`: Cytoscape-Canvas-Farben separat, weil Canvas keine CSS-Variablen liest.

Daraus folgt: Ein globales Redesign wäre bereits relativ einfach, ein pro Kampagne konfigurierbares Theme benötigt aber einen gezielten Umbau. Es soll **kein eigenes CSS-Bundle pro Kampagne** erzeugt werden.

Vorgesehen ist ein gemeinsames Struktur-Stylesheet mit kampagnenbezogenen CSS-Variablen. Ein Theme kann zunächst enthalten:

- Grund-/Hintergrundfarbe;
- Panel-/Fensterfarbe;
- Textfarbe;
- Hauptakzentfarbe;
- Signal-/Geheimfarbe;
- Ladebalkenfarbe;
- Hintergrundbild;
- Hintergrundposition;
- Hintergrunddeckkraft;
- später optional Schrift- und Rahmenstil.

Animationen bleiben zunächst global, damit Themes lesbar und ruhig bleiben. Optional abschaltbare Störeffekte bzw. reduzierte Bewegung bleiben aus Gründen der Barrierefreiheit erhalten.

Beispielhafte Anwendung:

```tsx
<div
  className="cl-shell"
  style={{
    "--grund": theme.grundfarbe,
    "--flaeche": theme.flaechenfarbe,
    "--neon": theme.akzentfarbe,
    "--signal": theme.signalfarbe,
    "--kampagnen-hintergrund": theme.hintergrundbild
      ? `url(${theme.hintergrundbild})`
      : "none",
  } as React.CSSProperties}
>
```

Der bunte Seitenwechsel-Balken verwendet weiterhin dieselbe Animation, bezieht seine Farbe aber aus `--ladebalkenfarbe` bzw. dem Akzent des Zielbereichs. Das Hintergrundbild wird hinter einer konfigurierbaren Abdunklung gelegt, damit Text und Neonränder lesbar bleiben.

Der Graph erhält die aufgelösten Theme-Farben zusätzlich als Props oder über einen gemeinsamen Theme-Resolver; die Werte werden nicht mehr unabhängig von der Oberfläche gepflegt.

## Umsetzungsreihenfolge

1. Theme-Vertrag und Anwendung in der `CommlinkShell` zentralisieren.
2. Kampagnen-Wiki-MVP mit Dokumenten, Seitenbaum und TipTap-Inhalt.
3. Automatisches Inhaltsverzeichnis aus Überschriften.
4. Dokument-Tabs und interne Navigation.
5. Explizite Entitätsverknüpfungen mit `[[...]]`/`@`-Autocomplete.
6. Backlinks auf Entitätsseiten.
7. Suche über Dokumente und Seiten.
8. Überschriften-/Text-Erkennung als bestätigungspflichtiger Vorschlag.
9. Import/Export, Versionierung und Echtzeit-Kollaboration erst danach.

Echtzeit-Kollaboration wie bei Google Docs ist kein MVP-Ziel. TipTap-JSON wird zunächst zuverlässig per Autosave gespeichert; Yjs/WebSockets können später ergänzt werden.

## Bewusste Grenzen

- Keine externe OneNote-/Google-Docs-Abhängigkeit als Kern.
- Keine ungefragte Erstellung neuer Entitäten durch automatische Erkennung.
- Keine Spielerfreigabe standardmäßig.
- Keine eigene CSS-Datei oder Build-Variante pro Kampagne.
- Keine Entscheidung für ein komplexes Dokument-/Versionsmodell, bevor der Wiki-MVP mit Seitenbaum und Verknüpfungen funktioniert.
