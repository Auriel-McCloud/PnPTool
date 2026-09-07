# PnPTool — Entwicklungshistorie

Ausgelagerte Details aus CLAUDE.md. Bei Problemen hier nachschlagen.

## Stolpersteine (vollständige Liste)

### 1. `passlib` + neueres `bcrypt`
Inkompatibel (passlib ist unmaintained, `bcrypt>=4.1` hat `__about__` entfernt).
**Lösung:** `bcrypt`-Paket direkt nutzen, kein passlib. Bereits in `auth/security.py`.

### 2. `uvicorn --reload` auf Windows
Der Reloader-Parent kann sterben während der Worker weiterläuft und alten Code serviert.
**Lösung:** Beide PIDs killen (`netstat -ano | grep :8000` → `taskkill /F /PID X`), ohne `--reload` starten.

### 3. `react-cytoscapejs`-Wrapper
Bug: rief bei jedem Re-Render ein Re-Layout auf, verlor Klick-Handler.
**Lösung:** Komplett entfernt, Cytoscape direkt via `useRef` in `CampaignGraphView.tsx`.

### 4. Cytoscape + `box-sizing`
Ohne globales `box-sizing: border-box` entsteht minimaler Overflow → ResizeObserver-Endlosschleife.
**Lösung:** Globales `box-sizing: border-box` in `index.css`.

### 5. Cytoscape Initial-Messung zu früh
Container beim `cytoscape()`-Aufruf noch nicht gelayoutet → Canvas "halb" befüllt.
**Lösung:** Doppeltes `requestAnimationFrame` + `cy.resize()` + `cy.fit()`.

### 6. TypeScript + `verbatimModuleSyntax` + `@types/cytoscape`
`type Stylesheet` lässt sich nicht als `cytoscape.Stylesheet` referenzieren.
**Lösung:** `interface StylesheetStyle` statt des Union-`type Stylesheet` verwenden.

### 7. Vite Hot-Reload + Cytoscape
HMR kann alte Instanzen hinterlassen.
**Lösung:** Dev-Server komplett neu starten, `node_modules/.vite` löschen.

### 8. Cytoscape-Canvas verschoben durch `text-align: center`
`index.css` setzt `#root { text-align: center }` → Canvas um halbe Breite verschoben.
**Lösung:** `textAlign: "left"` explizit auf dem Graph-Container.

### 8b. Blindes Ersetzen kurzer CSS-Selektoren
`.cb-wert {` traf die falsche Fundstelle → Layout kaputt.
**Lösung:** Genug Kontext mitnehmen oder eindeutigen Anker verwenden.

### 8c. Browser-Prüfungen verändern echte Daten
Testlauf der "ersten freien Ablage-Knopf" drückt, verschiebt tatsächlich Gegenstände.
**Lösung:** Auf Testdaten arbeiten oder Ausgangszustand wiederherstellen.

### 9. Neue Pydantic-Response-Felder + Bestandsdaten ohne Property
Ein Feld ohne Fallback → `null` → Pydantic-Validierung schlägt fehl → 500 auf ganzer Liste.
**Lösung:** Bei jeder neuen Property IMMER `coalesce`-Fallback in `_decode()`.

### 9b. Cypher: `WITH` zwischen schreibender Klausel und `MATCH`
Nach `CREATE`, `SET`, `DELETE` verlangt Neo4j ein `WITH` vor erneutem `MATCH`.
**Lösung:** `LIEGT_IN_NACH_CREATE`-Variante mit `WITH g` nur wo keine weitere Variable nötig.

### 10. WebSocket nicht an `require_campaign_zugang`
Dependency wirft `HTTPException` → Client sieht wortlosen Abbruch.
**Lösung:** Prüfung von Hand (`_viewer_aus_cookie`) mit `close(code=1008)`.

### 11. 6-Schichten-Check bei neuen Feldern
Vergessene Schicht → Feld fehlt still. Prüfen:
1. DB-Property
2. Repository FIELDS + DEFAULTS
3. Create-Schema
4. Update-Schema
5. **Response-Schema** (oft vergessen!)
6. Frontend-Interface

### 12. `_create_data` zählt Felder einzeln auf
Was dort fehlt, geht beim Anlegen still verloren.
**Lösung:** `test_gegenstand_felder.py` vergleicht Schema mit Übergabe.

## Geprüfte Features (historisch)

### SL-Popups (03.09.2026)
- 198 Backend-Tests (17 neue)
- End-to-End mit zwei Browser-Kontexten
- Rundruf kam live beim Spieler an
- Gerichtete Ansage an anderen PC erschien nicht (LEAK: false)
- Zurückziehen ließ offenes Popup verschwinden

### Warnung (03.09.2026)
- Drei Farben einzeln geprüft (rot/blau/violett)
- Aufgelöste CSS-Werte ausgelesen (220 30 60, etc.)
- Puls läuft, Text steht mittig
- prefers-reduced-motion: kein Puls, Ansage bleibt

### Bilder (03.09.2026)
- PNG an Test-NPC hochgeladen (200, content-type: image/png)
- Per Blitz an alle geschickt
- Beim Spieler im Popup gerendert (naturalWidth > 0)

### Initiative (03.09.2026)
- Warnung mit Initiative-Schalter kam an
- Popup zeigte Pool und Herkunft
- Spieler tippte Wert über Oberfläche → bei SL in Liste
- NPC-Initiative automatisch gewürfelt
- NPC weiterhin als Alias sichtbar (leak: false)

### Reflex-Booster (04.09.2026)
- Nicht verbaut: Initiative 7, Mod 0
- Eingesetzt: Initiative 13, Mod 6
- Ablegen bei verbautem Chrom → 409
- Zweitwurf-Pool ohne Bonus
- Paralyse "nicht geschafft" → Ampel 0, setztAus=true

### Chat-Benachrichtigungen (07.09.2026)
- SL → Spieler: Spieler bekommt Popup
- Spieler → NPC: SL bekommt Popup
- SL bekommt NICHT Spieler-zu-NPC-Popups (Filterung funktioniert)

### Mitteilungen ausblenden (07.09.2026)
- ✕ Button blendet einzelne aus
- "Alle ausblenden" leert Liste
- Andere Benutzer sehen Mitteilung noch

## Testkampagne & Testdaten

- **Kampagne:** `71dc452c-6c45-4a18-aec5-24815d161053` ("Neotopia Testkampagne")
- **Test-PC:** Ryu Tanaka `22fabda9-c1b8-4ace-bed4-b0083091ebb8`
- **Test-NPC:** Kira Voss `a7999dae-e236-47ca-9121-ef66ddd8186c`
- **Kontakt:** `1e997a42-a274-4909-acc8-552460353417` (chatOffen: true)

Demo-Daten: Kira Voss (spieler-sichtbar), Mr. Chrome (SL-geheim), Neon Alley Bar, "Der Deal geht schief", 3 Verbindungen.
