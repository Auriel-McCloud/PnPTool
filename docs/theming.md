# Theming — wie das Aussehen austauschbar wurde

**Stand:** 03.09.2026  
Ergänzt `docs/ui-konzept.md` (das beschreibt das *Warum* der Cyberpunk-Optik, das hier das *Wie* der Austauschbarkeit).

## Die eine Regel

> Außerhalb von `frontend/src/theme/` steht **kein Farbwert** mehr direkt im Code.

Weder `#00e5ff` in CSS noch `farbe: "#4d8bd8"` in TSX. Wer eine Farbe braucht, nimmt ein Token.

Das ist keine Kosmetik: Solange Werte verstreut sind, färbt ein Themewechsel *fast* alles um, und übrig bleiben einzelne Stellen im alten Ton. Genau das war vorher der Zustand — die Graphfarben standen ein zweites Mal in `CampaignGraphView.tsx`, mit dem handschriftlichen Hinweis *"beim Ändern dort nachziehen"*.

## Aufbau

```
frontend/src/theme/
├── tokens.css        Token-Definitionen + Werte des Standardthemes "cyberpunk"
├── hextechpunk.css   Zweites Theme: überschreibt nur Werte, nie Namen
├── theme.ts          Zugriff aus TypeScript (für Canvas), Theme-Umschaltung
└── ThemeSchalter.tsx Durchschalter in der oberen Werkzeugleiste (◐)
```

`index.css` importiert beide CSS-Dateien und beschreibt nur noch Form und Verhalten.

## Die sechs Token-Gruppen

1. **Palette** (`--p-*`) — die rohen Farben. Nur hier stehen Hexwerte.
2. **Rollen** — was eine Farbe *bedeutet*: `--neon` (aktiv/Fokus), `--signal` (SL-geheim), `--ja`/`--nein` (Entscheidungspaar), `--gut`, `--warn`.
3. **Bereiche** (`--bereich-*`) — Leitfarbe je Menüpunkt.
4. **Wertegruppen** (`--wert-*`, `--track-*`) — Charakterblatt.
5. **Kulisse** — Hintergrundbild, Schimmer, Ladebalken, Flackern.
6. **Form** — Radius, Maße, Schrift, Glut-Stärke.

Die Trennung Palette ↔ Rollen ist der Kern: `--signal` heißt durchgehend "SL-geheim". Im Cyberpunk ist das Magenta, im Hextechpunk Gold. Keine einzige Regel muss das wissen.

## Ein neues Theme anlegen

1. Datei `theme/<name>.css` mit `[data-theme="<name>"] { … }`.
2. Nur die **Palette** und einzelne Form-Tokens überschreiben — niemals Rollen-Namen erfinden.
3. `--grund-rgb` / `--flaeche-rgb` mitziehen (für Halbtransparenz).
4. In `theme.ts` bei `THEMES` und `THEME_LABELS` eintragen.
5. Import in `index.css` ergänzen.

Mehr ist nicht nötig. Hextechpunk kam mit ~60 Zeilen aus und färbt die komplette Oberfläche inklusive Graph.

## Canvas: der Sonderfall

Cytoscape zeichnet auf Canvas und kennt keine CSS-Variablen. Statt die Werte zu spiegeln, liest `CampaignGraphView.tsx` sie zur Laufzeit:

```ts
const t = tokens({ person: "--kind-person", ort: "--kind-ort", … });
```

`getComputedStyle` löst dabei auch verkettete Variablen (`--neon: var(--p-cyan)`) bis zum Hexwert auf — verifiziert, nicht angenommen.

Zusätzlich horcht ein `MutationObserver` auf `data-theme` am `<html>` und schreibt das Cytoscape-Stylesheet neu. **Ohne den bliebe der Graph nach einem Themewechsel in den alten Farben stehen.**

## Kampagnenoptik (vorbereitet)

`optikStil()` in `theme.ts` übersetzt eine `KampagnenOptik` in Inline-CSS-Variablen. Damit kann *eine Kampagne* innerhalb eines Themes ein eigenes Hintergrundbild, eine eigene Leitfarbe und einen eigenen Ladebalken bekommen:

```tsx
<div className="cl-shell" style={optikStil(kampagne.optik)}>
```

Der Body legt drei Ebenen übereinander: Schleier (`--hintergrund-schleier`, dunkelt ab, damit Text lesbar bleibt) → Kampagnenbild (`--hintergrund-bild`) → Schimmer.

**Noch nicht angebunden:** Die Felder existieren im Frontend, aber es gibt weder Backend-Feld noch Einstellungs-UI. Das ist der nächste Schritt, wenn kampagnenspezifische Optik gebraucht wird.

## Bewusst global geblieben

Animationsdauern, Übergänge und das Flackern sind **nicht** pro Theme einstellbar. Ein Theme, das die Bewegung umbaut, wird schnell unruhig oder unlesbar. `prefers-reduced-motion` schaltet weiterhin global ab.

## Was der Umbau nebenbei behoben hat

- **`richtext.css` hatte helle Vite-Starter-Farben** (`#fde2e2`, `#ccc`, `#f0f0f0`) — Tabellenränder und die SL-Geheim-Markierung stachen im dunklen Commlink heraus. Die Markierung trägt jetzt `--signal` wie überall sonst.
- **Wertegruppen-Farben lagen dreifach dupliziert** in `Charakterblatt.tsx`, `Charaktererstellung.tsx` und `Probe.tsx`.
- **Das Ja/Nein-Paar der Rückfragen** war in drei CSS-Dateien einzeln kodiert; jetzt `--ja`/`--nein`.
- **`App.css`** war eine nirgends importierte Vite-Starter-Leiche — entfernt.

## Verifikation

Per Chrome DevTools Protocol gegen die laufende App geprüft:

- alle Tokens gesetzt, keine unaufgelösten `var()`-Ketten;
- Themewechsel ändert 14/14 geprüfte Tokens;
- Bereichsfarbe der Hülle zieht mit (`#4d8bd8` → `#5b93e8`);
- Auswahl überlebt den Neuladen (`localStorage`);
- **Canvas-Pixel ausgezählt**: Knotenfarben wechseln tatsächlich (`#2fa96a` → `#38b189`, Signal `#ff2d95` → Gold `#f0c46a`), keine Cyberpunk-Farbe bleibt übrig.
