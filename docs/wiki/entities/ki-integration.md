---
title: KI-Integration
created: 2026-09-18
updated: 2026-09-23
type: entität
tags: [ki-integration, backend, geplant]
sources: [../../../CLAUDE.md]
status: teilweise-umgesetzt
---

# KI-Integration

## Erste Iteration (15.09.2026) — umgesetzt

Gemini generiert direkt in der Ideenschmiede (siehe
[[architektur-drei-ebenen]]): „✨ KI"-Knopf öffnet ein Popup mit Typ
(Charakter/Story-Part) und Wunschtext. `story` wird eine Wiki-Seite,
`charakter` ein NPC — beide als Entwurf (`istEntwurf=true`).

Backend: `backend/app/ki/` (dünner Gemini-Client, `POST /ki/idee`), Modell
konfigurierbar (`gemini_model`, Default `gemini-3.6-flash`), API-Key in
`backend/.env` (gitignored, nie im Git-Verlauf — siehe [[tech-stack]] für
Details zur Secrets-Vorlage `.env.example`). Zusätzlich
`backend/app/ki/mistral.py` als Alternativ-Client.

## Bugfix: Kontextlücke im Story-Pfad (22.09.2026) — behoben

Mark meldete: bei einer Story-Generierung erfand Gemini "Proxima Centauri"
als Sternensystem, obwohl die Kampagne bereits "Omikron² Eridiani"
freigegeben hatte. Ursache: `ki_idee()` in `routes.py` rief für `typ=story`
`generiere_json` **ohne** `sammle_kontext()` auf — nur der `charakter`-Pfad
bekam die freigegebene Kampagnenwelt mitgeliefert. Fix: beide Pfade nutzen
jetzt `sammle_kontext()` + `_mit_kontext()`. Zusätzlich die Prompt-Formel in
`_mit_kontext()` verschärft: statt der weichen Bitte „füge das Neue darin
ein" jetzt eine ausdrückliche Vorrang-Regel — bestehende Objekte bevorzugt
wiederverwenden, nur bei echter Lücke etwas komplett Neues erfinden, nie
einen neuen Namen für etwas bereits Freigegebenes erfinden.

## ✨ KI-Knopf an Beschreibung/Notizen (22.09.2026) — umgesetzt

Dritter Anwendungsfall auf derselben Anbindung: neben 🔒 SL-geheim im
`RichTextEditor.tsx` erscheint ein ✨ KI-Knopf, sobald die aufrufende Stelle
die optionale `kiKontext`-Prop setzt (campaignId, Objekttyp, Objektname,
Feldlabel „Beschreibung"/„Notizen"). Betrifft alle Einbettungsstellen:
PC/NPC/Ort/Event/Fraktion-Detail-Popups, Gegenstand-Beschreibung/Notizen
(`CharacterSheetPanel.tsx`), Begleiter/Critter/KI-Fenster.

Ablauf: Klick öffnet `frontend/src/ki/KiTextPopup.tsx` mit freiem
Wunsch-Prompt → `POST /api/campaigns/{id}/ki/objekt-text`
(`backend/app/ki/routes.py::ki_objekt_text`) generiert einen Vorschlag aus
Objektname, bisherigem Feldtext (Anschluss an Vorhandenes) und dem vollen
Kampagnenkontext → **Vorschau im Popup**, erst „✓ Übernehmen" hängt den Text
ans Ende des Editor-Inhalts an (Marks Wunsch, 22.09.2026: keine
Direktschreibung, wie bei der Wiki-Prüfung erst zur Kontrolle anzeigen;
bisheriger Inhalt bleibt erhalten, kein Ersetzen).

## ✨ Auto-Verknüpfung (22.09.2026) — umgesetzt

Vierter Anwendungsfall: „⧉✨ Auto-Verknüpfen"-Knopf im `WikiEditor.tsx`
(neben 🔍 Prüfen, dieselbe Reihe wie ⧉ Verknüpfen manuell). Zweistufig, wie
die Rechtschreib-/Logikprüfung: Klick öffnet
`frontend/src/ki/AutoVerknuepfungPopup.tsx`, „✨ Vorschläge holen" ruft
`POST .../ki/wiki/{id}/verknuepfung/vorschlaege` — die KI bekommt den
Seitentext plus die Namen ALLER freigegebenen Personen/Orte/Events/
Fraktionen (`app/ki/kontext.py::sammle_entitaeten`, neu) und liefert in
EINEM Aufruf zwei Arten von Treffern zurück (Mark ist kostenbewusst — zwei
Requests für denselben Text wären unnötig teuer):

- **Verweise** — Zitat + Typ + Name. „✓ Verknüpfen" fügt einen
  `entitaetsverweis`-Chip an der Textstelle ein — die klassische "Erwähnt
  in"-Kante zur Wiki-Seite.
- **Beziehungen** (22.09.2026, Marks Nachfrage) — wo der Text eine
  KONKRETE Beziehung zwischen zwei erwähnten Entitäten ausdrückt (z.B.
  "arbeitet für", nicht nur zufällige Nähe im selben Absatz), schlägt die
  KI Beziehungstyp + Kurzbeschreibung vor. „✓ Beziehung anlegen" erzeugt
  eine echte `VERBINDUNG`-Kante zwischen den beiden Entitäten selbst —
  dieselbe Art Kante wie der „+ Neue Verbindung"-Knopf im Beziehungen-Tab,
  fachlich etwas ANDERES als der Verweis zur Wiki-Seite.

Der Namensabgleich gegen bestehende IDs passiert bewusst in Python
(`auto_verknuepfung.py::vorschlaege`, normalisierter Stringvergleich), nie
durch die KI selbst — eine leicht abweichende Schreibweise der KI darf nie
eine falsche ID erfinden.

Jeder Treffer einzeln bestätigt: bekannte Entität → direkt verknüpft;
unbekannte → legt zuerst einen SL-geheimen Entwurf in der Ideenschmiede an
(Marks Vorgabe: Vorschlag zur Prüfung, kein Autocommit). **Dedup-Schutz**
(`_finde_oder_lege_an`/`_bestehende_id`): taucht dieselbe neue Person
sowohl in einem Verweis- als auch in einem Beziehungs-Vorschlag auf,
entsteht sie nur EINMAL — wird zuerst der Verweis angewandt, findet die
Beziehung danach dieselbe frisch angelegte Person wieder statt eine zweite
zu erzeugen.

`anwenden()` fügt an der zitierten Textstelle den Chip ein
(`_verweis_einfuegen`, splittet den Textknoten, erhält Marks wie 🔒
SL-geheim auf beiden Seiten) und speichert die Seite — dieselbe
`_verweise_schreiben()`-Pipeline wie ein von Hand eingefügter Verweis
erzeugt danach die echte `VERWEIST_AUF`-Kante. `beziehung_anwenden()` ruft
dieselbe `entities/repository.py::create_verbindung` wie der manuelle
"+ Neue Verbindung"-Knopf.

**Nebenbei-Fix:** `ERLAUBTE_ZIELTYPEN` in `wiki/repository.py` kannte
`"Fraktion"` bisher nicht — ein Fraktions-Chip blieb im Text sichtbar,
erzeugte aber nie eine echte Graphkante (betraf auch manuelle
Verknüpfungen, nicht nur die neue Auto-Verknüpfung). Jetzt ergänzt.

Backend end-to-end verifiziert: Server startet fehlerfrei, alle drei neuen
Routen im OpenAPI-Schema, `_verweis_einfuegen` isoliert getestet (Text wird
korrekt gesplittet, SL-geheim-Marks bleiben auf beiden Textteilen erhalten,
Namens-Normalisierung funktioniert). `tsc --noEmit` fehlerfrei.

Sweep über alle Seiten auf einmal (wie bei der Rechtschreibprüfung) bewusst
NICHT gebaut — Mark wollte erstmal nur den Einzelseiten-Knopf, Sweep bei
Bedarf später.

## Wiki-Rechtschreib-/Grammatik-/Logikprüfung (20.09.2026) — umgesetzt

Zweites Feature auf derselben KI-Anbindung, eigenes Modul
`backend/app/ki/wiki_pruefung.py`. Zwei Einstiege:

- **Eine Seite**: "🔍 Prüfen"-Knopf direkt im `WikiEditor.tsx` (Story-Wiki
  und Ideenschmiede-Wiki-Popup teilen sich diese Komponente).
- **Alle Seiten**: "🔍 Fließtext prüfen"-Knopf in den Kampagnen-
  Einstellungen (`EinstellungenFenster.tsx`) — ein manueller Sweep, kein
  Hintergrundlauf. Überspringt jede Seite, deren Inhalt sich seit der
  letzten Prüfung nicht geändert hat (SHA-256-Hash `pruefHash` am
  `WikiSeite`-Knoten) — Mark will das gezielt ab und zu anstoßen, nicht bei
  jeder Kleinigkeit KI-Kosten verursachen.

Logikfehler beziehen den freigegebenen Kampagnenkontext ein (dieselbe
`sammle_kontext()`-Quelle wie beim NPC-Generator oben) — aber NUR echte
Widersprüche zu bestehenden Fakten gelten als Fehler; ein neuer Name/Ort,
der in der Welt schlicht noch nicht vorkommt, wird bewusst NICHT gemeldet
(erste Version tat das fälschlich, Prompt wurde nachgeschärft — siehe
`references/ki-gemini-integration.md` in der Skill für den vollen Verlauf).

Jeder Befund hat ein wörtliches Zitat + Vorschlag; "✓ Übernehmen" ersetzt
die Textstelle automatisch im TipTap-Dokument, auch wenn die Seite gerade
nicht offen ist. `docs/api/ki.md` dokumentiert die drei neuen Endpunkte.

## Geplante Anwendungsfälle (`CLAUDE.md` Punkt 3)

- NPC-Generator aus Kurzbeschreibung — **umgesetzt** (siehe oben)
- ✨ Freier KI-Text-Zusatz an Beschreibung/Notizen jeder Entität —
  **umgesetzt** (siehe oben)
- Bildgenerierung (Portraits, Item-Bilder, Maps) — **nicht umgesetzt**
- Wiki-Import aus Word-Dokumenten — **nicht umgesetzt**
- Auto-Verknüpfung (KI durchsucht Wiki/Ideenschmiede, verknüpft erwähnte
  Personen/Orte/Events als echte Graphkanten; existiert eine Entität noch
  nicht, legt die KI dafür einen Entwurf in der Ideenschmiede an und trägt
  die Beziehung gleich mit ein — präzisiert 20.09.2026, Marks Wunsch) —
  **umgesetzt** (22.09.2026, siehe oben). Bisher nur im Wiki-Editor
  (Einzelseite); Ideenschmiede-Texte und ein Sweep über alle Seiten sind
  noch offen.
- Rechtschreib-/Grammatik-/Logikprüfung im Wiki-Editor und in der
  Ideenschmiede — **umgesetzt** (siehe oben). Dieselbe Prüfung für die
  `RichTextEditor`-Felder an Personen/Orten/Events/Fraktionen ist noch
  offen, war bewusst nicht Teil von Schritt 1.
- Chatbot-Gegenstände (Decker redet mit Deck, Priester mit Bibel) —
  **nicht umgesetzt**, siehe `CLAUDE.md` Punkt 10 für den vollen Entwurf
  inkl. geplanter TTS-Hybrid-Lösung (Edge TTS + ElevenLabs)

## KI-Gegenstandsgenerator + KI-Sortiment-Vorschlag (23.09.2026) — umgesetzt

Fünfter Anwendungsfall: dritter Ideenschmiede-Typ `gegenstand` neben
`story`/`charakter` (`typ: "gegenstand"` in `ki/routes.py::ki_idee`). Der Typ
ist seit dem Typwechsel-Verbot (22.09.2026, siehe [[architektur-drei-ebenen]]
für den Bezug) nach dem Anlegen fix — deshalb erzwingt das generierte JSON-
Schema den festen Katalog `GEGENSTAND_TYPEN` (`items/schemas.py`) als Enum;
erfindet die KI trotzdem etwas Ungültiges, fällt der Wert hart auf
"Sonstiges" zurück. Entsteht wie Charakter/Story als besitzerloser,
SL-geheimer Entwurf.

Darauf aufbauend: **KI-Sortiment-Vorschlag für Händler**, neues Modul
`backend/app/haendler/ki_vorschlag.py`. Bevorzugt bestehende, bereits
freigegebene Gegenstands-Vorlagen der Kampagne wiederzuverwenden (Abgleich
über echte IDs, nicht per KI-Text — dieselbe Regel wie bei der
Auto-Verknüpfung oben), erfindet nur bei einer echten Lücke etwas Neues
(landet dann zuerst als Ideenschmiede-Entwurf, kein Autocommit). Zweistufig
wie die Auto-Verknüpfung: `GET .../ki-vorschlaege` liefert eine
Vorschauliste, `POST .../ki-vorschlaege/anwenden` übernimmt EINEN
bestätigten Vorschlag. Details: `docs/api/haendler.md`.

Backend end-to-end gegen echte Neo4j-DB verifiziert (Wiederverwendung UND
Neuerfindung getestet). Frontend für den Sortiment-Vorschlag noch offen
(SL-Popup mit Vorschlagsliste).

## Bildgenerierung (23.09.2026) — umgesetzt

Sechster Anwendungsfall, eigenes Modul `backend/app/ki/bildgenerierung.py`:
`generiere_bild(provider, prompt) -> (bytes, content_type)` mit zwei
**pro Aufruf** wählbaren Providern (Commlink-Popup-Dropdown, anders als der
global per `.env` gesetzte Text-Provider `KI_PROVIDER`):

- **cloud** — Google Gemini `gemini-2.5-flash-image` (`generateContent` mit
  `responseModalities: ["IMAGE"]`, gleicher REST-Stil wie der Text-Client,
  kein SDK).
- **lokal** — `pnptool_server.py` in `C:\DEV\Fooocus`, ein eigener
  Wrapper-Prozess **außerhalb dieses Repos** (nicht eingecheckt, eigenes
  venv). Fooocus 2.5.5/Gradio 3.41.2 hat keine eigene REST-API; der Wrapper
  importiert `modules.async_worker` direkt. Muss von Mark manuell separat
  gestartet werden (z.B. Autostart) — läuft er nicht, meldet die Route eine
  klare Verbindungsfehlermeldung statt eines rohen Timeouts.

Zweistufiges Popup, wie schon bei der Wiki-Prüfung/Auto-Verknüpfung erst
zur Kontrolle anzeigen statt sofort zu speichern: `POST .../ki/bild-prompt`
schlägt einen editierbaren Bild-Prompt aus Name+Beschreibung vor (Text-KI,
dieselbe `sammle_kontext()`-Infrastruktur), `POST .../ki/bild-generieren`
liefert die rohen Bild-Bytes als Vorschau — **speichert nichts**. Erst
"✓ Übernehmen" im Frontend-Popup (`frontend/src/ki/KiBildPopup.tsx`) schickt
das Bild über die jeweils bestehende Datei-Upload-Route der Entität, kein
zweiter Ablage-Mechanismus (ein erster Versuch mit eigenen
Byte-Speicher-Helfern in `entities/routes.py`/`items/routes.py` wurde noch
am selben Tag wieder verworfen zugunsten dieses einfacheren Wegs).

Eingebunden an Person/Event (`EntitaetsBild.tsx`), Ort/Fraktion
(`BildGalerie.tsx`), Gegenstand (`CharacterSheetPanel.tsx`) für die SL sowie
am eigenen Charakterportrait für den Spieler
(`players/CharakterportraitAnsicht.tsx`, eigene Routen
`/api/spieler/mein-bild-ki-prompt` + `/mein-bild-ki`, siehe
`docs/api/auth.md`). Details zu Request/Response: `docs/api/ki.md`.

**Verifiziert:** Backend-Import ok, alle Routen im OpenAPI-Schema, `tsc -b`
fehlerfrei, ein echter E2E-Call gegen laufendes Backend + echte Neo4j-Daten
+ echten Gemini-Key lieferte einen funktionierenden Bild-Prompt-Vorschlag.
Bildgenerierung selbst für beide Provider (Cloud UND lokal) je einmal live
getestet. **Zwei offene Punkte:** `KiBildPopup.tsx` wurde nur gegen `tsc -b`
geprüft, kein echter Klicktest im laufenden Frontend — Mark muss das selbst
gegenprüfen; der Fooocus-Wrapper muss manuell als Hintergrundprozess
eingerichtet sein, sonst schlägt der "lokal"-Provider fehl.

## Siehe auch

- [[architektur-drei-ebenen]] — wo generierte Inhalte landen (Ideenschmiede)
- [[tech-stack]] — `.env`-Konfiguration, Secrets-Handling
- [[../../../CLAUDE.md]] — vollständige Feature-Liste unter „Geplante Features"
