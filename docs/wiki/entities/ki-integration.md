---
title: KI-Integration
created: 2026-09-18
updated: 2026-09-20
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
- Bildgenerierung (Portraits, Item-Bilder, Maps) — **nicht umgesetzt**
- Wiki-Import aus Word-Dokumenten — **nicht umgesetzt**
- Auto-Verknüpfung (KI durchsucht Wiki/Ideenschmiede, verknüpft erwähnte
  Personen/Orte/Events als echte Graphkanten; existiert eine Entität noch
  nicht, legt die KI dafür einen Entwurf in der Ideenschmiede an und trägt
  die Beziehung gleich mit ein — präzisiert 20.09.2026, Marks Wunsch) —
  **nicht umgesetzt**, als NÄCHSTES angekündigt ("machen wir danach")
- Rechtschreib-/Grammatik-/Logikprüfung im Wiki-Editor und in der
  Ideenschmiede — **umgesetzt** (siehe oben). Dieselbe Prüfung für die
  `RichTextEditor`-Felder an Personen/Orten/Events/Fraktionen ist noch
  offen, war bewusst nicht Teil von Schritt 1.
- Chatbot-Gegenstände (Decker redet mit Deck, Priester mit Bibel) —
  **nicht umgesetzt**, siehe `CLAUDE.md` Punkt 10 für den vollen Entwurf
  inkl. geplanter TTS-Hybrid-Lösung (Edge TTS + ElevenLabs)

## Siehe auch

- [[architektur-drei-ebenen]] — wo generierte Inhalte landen (Ideenschmiede)
- [[tech-stack]] — `.env`-Konfiguration, Secrets-Handling
- [[../../../CLAUDE.md]] — vollständige Feature-Liste unter „Geplante Features"
