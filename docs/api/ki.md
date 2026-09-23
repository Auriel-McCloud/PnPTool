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
- `CLAUDE.md`, Punkt 3 ("KI-Integration") — offene Punkte: Auto-Verknüpfung
  (Entwürfe für unbekannte erwähnte Entitäten anlegen) folgt als nächster
  Schritt auf derselben Baustelle
