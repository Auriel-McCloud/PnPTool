# Bilder: Uploads und Vorschaubilder

Alle hochgeladenen Bilder (Gegenstände, Personen, Orte, Rassen, Begleiter,
Battlemaps, Zeichnungen, KI-Bilder …) liegen unter
`uploads/<campaignId>/<uuid-dateiname>` und werden ohne Login ausgeliefert.

## `GET /uploads/<campaignId>/<datei>`

Original. Dateinamen sind UUIDs und werden nie überschrieben, deshalb
`Cache-Control: public, max-age=31536000, immutable`.

## `GET /uploads/_vorschau/<breite>/<campaignId>/<datei>`

Verkleinerte Fassung für Übersichten/Kacheln (seit 11.11.2026).

- `breite` = Zielgröße der **kürzeren** Bildseite, nur `128` (Avatare) oder
  `480` (Kacheln); alles andere 404.
- Antwort: WebP, beim ersten Abruf erzeugt und unter
  `uploads/_vorschau/<breite>/<campaignId>/<datei>.webp` abgelegt; ist das
  Original neuer, wird neu gebaut.
- Ist das Original schon klein genug, ein animiertes GIF oder nicht lesbar,
  kommt das Original zurück.
- Gleicher Langzeit-Cache wie das Original. 404, wenn das Original fehlt.

Frontend: `vorschau(url, "kachel" | "klein")` aus `frontend/src/shell/vorschau.ts`
schreibt eine Upload-URL um; Detailansicht, Großbild und Bild-Pushs nutzen
weiter das Original.
