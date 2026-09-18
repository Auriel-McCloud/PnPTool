---
title: KI-Integration
created: 2026-09-18
updated: 2026-09-18
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
`backend/.env` (gitignored). Zusätzlich `backend/app/ki/mistral.py` als
Alternativ-Client.

## Geplante Anwendungsfälle (`CLAUDE.md` Punkt 3, größtenteils noch offen)

- NPC-Generator aus Kurzbeschreibung — **teilweise umgesetzt** (siehe oben)
- Bildgenerierung (Portraits, Item-Bilder, Maps) — **nicht umgesetzt**
- Wiki-Import aus Word-Dokumenten — **nicht umgesetzt**
- Auto-Verknüpfung (KI durchsucht Wiki, verknüpft Entitäten) — **nicht umgesetzt**
- Rechtschreib-/Grammatikprüfung im Editor — **nicht umgesetzt**
- Chatbot-Gegenstände (Decker redet mit Deck, Priester mit Bibel) —
  **nicht umgesetzt**, siehe `CLAUDE.md` Punkt 10 für den vollen Entwurf
  inkl. geplanter TTS-Hybrid-Lösung (Edge TTS + ElevenLabs)

## Siehe auch

- [[architektur-drei-ebenen]] — wo generierte Inhalte landen (Ideenschmiede)
- [[../../../CLAUDE.md]] — vollständige Feature-Liste unter „Geplante Features"
