---
title: KI-Integration
created: 2026-09-18
updated: 2026-09-19
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

## Geplante Anwendungsfälle (`CLAUDE.md` Punkt 3, größtenteils noch offen)

- NPC-Generator aus Kurzbeschreibung — **teilweise umgesetzt** (siehe oben)
- Bildgenerierung (Portraits, Item-Bilder, Maps) — **nicht umgesetzt**
- Wiki-Import aus Word-Dokumenten — **nicht umgesetzt**
- Auto-Verknüpfung (KI durchsucht Wiki/Ideenschmiede, verknüpft erwähnte
  Personen/Orte/Events als echte Graphkanten; existiert eine Entität noch
  nicht, legt die KI dafür einen Entwurf in der Ideenschmiede an und trägt
  die Beziehung gleich mit ein — präzisiert 20.09.2026, Marks Wunsch) —
  **nicht umgesetzt**
- Rechtschreib-/Grammatik-/Logikprüfung im Wiki-Editor und in der
  Ideenschmiede (erweitert 20.09.2026 um Logik-/Konsistenzfehler, nicht nur
  Rechtschreibung) — **nicht umgesetzt**
- Chatbot-Gegenstände (Decker redet mit Deck, Priester mit Bibel) —
  **nicht umgesetzt**, siehe `CLAUDE.md` Punkt 10 für den vollen Entwurf
  inkl. geplanter TTS-Hybrid-Lösung (Edge TTS + ElevenLabs)

## Siehe auch

- [[architektur-drei-ebenen]] — wo generierte Inhalte landen (Ideenschmiede)
- [[tech-stack]] — `.env`-Konfiguration, Secrets-Handling
- [[../../../CLAUDE.md]] — vollständige Feature-Liste unter „Geplante Features"
