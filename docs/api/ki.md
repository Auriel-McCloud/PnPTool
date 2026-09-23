# KI-API

Multi-Provider-Anbindung (Gemini/Mistral) für Ideenschmiede-Generierung und
Wiki-Textprüfung. Basis: `/api/campaigns/{campaign_id}/ki`. **Nur SL.**

## Anbieter

`KI_PROVIDER` in `backend/.env` (`gemini` oder `mistral`) wählt den Anbieter
ohne Code-Änderung — siehe `app/ki/client.py`. Fehler jeder Art kommen beim
Aufrufer als `502` an (die KI ist eine externe Abhängigkeit, kein Bug im Tool).

---

## POST `/idee`

Generiert einen Story-Part, einen Charakter oder einen Gegenstand und legt
ihn als Entwurf (`istEntwurf=true`) in der Ideenschmiede ab.

```json
{ "typ": "story" | "charakter" | "gegenstand", "prompt": "Ein misstrauischer Türsteher..." }
```

`story` → neue Wiki-Seite. `charakter` → NPC mit vollem Profil (Konzept,
Ambition, Rasse, Weg, Traits aus dem Katalog). `gegenstand` (**gebaut**
23.09.2026) → Gegenstands-Vorlage (besitzerlos): Name, Beschreibung, Typ,
Preis, Seltenheit. Der Typ MUSS einer aus dem festen Katalog
`GEGENSTAND_TYPEN` (`app/items/schemas.py`, deckungsgleich mit
`frontend/src/items/typKatalog.ts`) sein — als Enum im generierten Schema
erzwungen; erfindet die KI trotzdem etwas Ungültiges, fällt es hart auf
"Sonstiges" zurück (der Typ ist nach dem Anlegen nicht mehr änderbar). Alle
drei beziehen die freigegebene Kampagnenwelt als Kontext ein
(`app/ki/kontext.py`), damit sich das Neue in Bestehendes einfügt statt
isoliert daneben zu stehen — bevorzugt Bestehendes wiederverwenden, nur bei
echter Lücke etwas komplett Neues erfinden.

---

## Bildgenerierung (gebaut 23.09.2026)

Zweistufiger "KI-Bild generieren"-Knopf am jeweils bestehenden
Bild-Upload-Popup (Person/Event/Ort/Fraktion/Gegenstand, Frontend:
`frontend/src/ki/KiBildPopup.tsx`). Spieler-Pendant fürs eigene
Charakterportrait steht unter `/api/spieler/mein-bild-ki-prompt` +
`/mein-bild-ki` in `docs/api/auth.md` (dort dokumentiert, weil es zum
Spieler-Router gehört — gleiche Logik, kein `require_campaign_gm`).

### POST `/bild-prompt`

Schritt 1: schlägt einen Bild-Prompt aus Name + bisheriger Beschreibung vor
(Text-KI, dieselbe `sammle_kontext()`/`generiere_json()`-Infrastruktur wie
oben). Der Nutzer sieht ihn vorausgefüllt und kann ihn vor dem Generieren
noch anpassen.

```json
{ "objektTyp": "Person", "objektName": "Rattenschieber Kez", "bisherigeBeschreibung": "..." }
```

**Response:**
```json
{ "prompt": "A grizzled fixer in a rain-soaked alley, neon signage reflecting..." }
```

`prompt` ist auf Englisch, 2-4 Sätze, für einen SDXL-Bildgenerator formuliert
(Aussehen, Kleidung/Material, Stimmung, Umgebung — keine Namen, keine
Spielmechanik). `502` wenn die KI keinen Vorschlag liefert.

### POST `/bild-generieren`

Schritt 2: generiert das Bild und liefert die **rohen Bild-Bytes als
Vorschau** zurück (`Content-Type` je nach Provider) — **speichert nichts**.
Erst der bestätigte "✓ Übernehmen"-Klick im Popup schickt das Bild als Datei
an die jeweils bestehende Upload-Route der Entität (dieselbe Route wie ein
manueller Upload, kein zweiter Ablage-Mechanismus).

```json
{ "provider": "lokal" | "cloud", "prompt": "A grizzled fixer in a rain-soaked alley..." }
```

- **`cloud`** — Google Gemini `gemini-2.5-flash-image`
  (`generateContent` mit `responseModalities: ["IMAGE"]`), braucht nur den
  bestehenden `gemini_api_key` in `backend/.env`.
- **`lokal`** — spricht `pnptool_server.py` in `C:\DEV\Fooocus` an (eigener
  Wrapper-Prozess, **außerhalb dieses Repos**, nicht eingecheckt — muss
  manuell laufen, z.B. als Autostart). Fooocus 2.5.5/Gradio 3.41.2 hat keine
  eigene REST-API; der Wrapper importiert `modules.async_worker` direkt.
  Settings in `config.py`: `fooocus_url` (Default `http://127.0.0.1:7865`),
  `fooocus_breite`/`fooocus_hoehe` (768×768), `fooocus_performance`
  (`"Speed"`), `fooocus_timeout_sekunden` (300 — eine GTX 1070 kann bei
  SDXL mehrere Minuten brauchen).

`502` bei jedem Fehler (Fooocus nicht erreichbar, Timeout, Gemini lehnt ab
z.B. per Sicherheitsfilter) mit einer für den jeweiligen Provider
verständlichen Fehlermeldung; `422` wenn `prompt` leer ist.

**Provider ist pro Aufruf wählbar** (Dropdown im Popup), anders als der
Text-Provider `KI_PROVIDER` in `.env`, der global für alle Text-Endpunkte
oben gilt.

### Datenmodell

Kein neues Feld — das generierte Bild landet über die bestehende
Upload-Route im selben `bildUrl`-Feld (Person/Ort/Event/Fraktion) bzw.
`gegenstand.bildUrl`, genau wie ein manuell hochgeladenes Bild.

---

## POST `/wiki/{seiten_id}/pruefen`

Prüft **eine** Wiki-Seite auf Rechtschreib-, Grammatik- und Logikfehler.
Der "🔍 Prüfen"-Knopf direkt im Wiki-Editor (Story-Wiki und
Ideenschmiede-Wiki-Popup teilen sich dieselbe `WikiEditor`-Komponente).

**Response:**
```json
{
  "befunde": [
    {
      "art": "rechtschreibung" | "grammatik" | "logik",
      "zitat": "Haendler",
      "vorschlag": "Händler",
      "begruendung": "Falsche Schreibweise."
    }
  ]
}
```

`zitat` ist wörtlich und zusammenhängend im geprüften Text enthalten (Vorgabe
im Prompt) — Grundlage für `POST .../pruefung/uebernehmen`, das genau diese
Zeichenfolge im Dokument sucht und ersetzt. Ein Logikfehler ist NUR ein
direkter Widerspruch zu einer bereits freigegebenen Tatsache der Kampagne
(z.B. eine Person gilt dort als tot, handelt hier aber) — ein Name/Ort, der
in der freigegebenen Welt schlicht noch nicht vorkommt, ist kein Fehler,
sondern neuer Inhalt, und wird bewusst nicht gemeldet.

Merkt sich nach dem Lauf den geprüften Textstand (`s.pruefHash`) — taucht die
Seite später im Sweep (`/wiki/pruefen-alle`) auf und hat sich seither nichts
geändert, wird sie dort übersprungen.

---

## POST `/wiki/pruefen-alle`

Prüft **alle** Wiki-Seiten der Kampagne in einem Lauf, überspringt jede Seite,
deren Inhalt sich seit der letzten Prüfung nicht geändert hat (Hash-Vergleich,
`app/ki/wiki_pruefung.py::sweep`). Marks "Fließtext prüfen"-Knopf in den
Kampagnen-Einstellungen — bewusst ein manueller Sweep statt einer
Dauerprüfung: er will das gezielt ab und zu anstoßen, nicht bei jeder
Kleinigkeit KI-Kosten verursachen.

**Response:**
```json
{
  "geprueft": 3,
  "uebersprungen": 12,
  "ergebnisse": [
    { "seitenId": "uuid", "titel": "Kapitel 1", "befunde": [ /* wie oben */ ] }
  ]
}
```

Nur Seiten mit tatsächlichen Befunden landen in `ergebnisse` — eine geprüfte,
fehlerfreie Seite zählt in `geprueft` mit, taucht aber nicht in der Liste auf.

---

## POST `/wiki/{seiten_id}/pruefung/uebernehmen`

Übernimmt einen Korrekturvorschlag: ersetzt `zitat` durch `vorschlag` direkt
im gespeicherten TipTap-Dokument der Seite.

```json
{ "zitat": "Haendler", "vorschlag": "Händler" }
```

Funktioniert unabhängig davon, ob die Seite gerade im Editor offen ist — die
Sweep-Ergebnisse können viele nicht-offene Seiten gleichzeitig betreffen.
Findet sich das Zitat nicht mehr im Dokument (z.B. weil die Seite inzwischen
von Hand geändert wurde), bleibt sie unverändert und `ersetzt` ist `false`:

```json
{ "ersetzt": true, "inhalt": "{\"type\":\"doc\", ...}" }
```

---

## Datenmodell

Ein Feld am `WikiSeite`-Knoten: `pruefHash` (SHA-256 des zuletzt geprüften
Fließtexts, leer wenn noch nie geprüft). Kein eigener Node-Typ — die Prüfung
braucht keine Historie, nur den letzten Stand.

## Siehe auch

- [Wiki](./wiki.md) — Seitenmodell, Freigabesystem
- [Händler](./haendler.md) — KI-Sortiment-Vorschlag baut auf dem
  KI-Gegenstandsgenerator auf (`app/haendler/ki_vorschlag.py`)
- [Auth](./auth.md) — Spieler-Pendant der Bildgenerierung
  (`/api/spieler/mein-bild-ki-prompt` + `/mein-bild-ki`) fürs eigene
  Charakterportrait, dort dokumentiert weil zum Spieler-Router gehörend
- `CLAUDE.md`, Punkt 3 ("KI-Integration") — offene Punkte: Auto-Verknüpfung
  (Entwürfe für unbekannte erwähnte Entitäten anlegen) folgt als nächster
  Schritt auf derselben Baustelle
