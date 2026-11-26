# GridMonster-API (Grundgerüst 26.11.2026)

Präfix `/api/campaigns/{campaign_id}/gridmonster`, alle Routen **nur SL**
(`require_campaign_gm`). Figuren-Routen antworten mit 400, wenn die Kampagne
kein GridMonster-Regelsystem nutzt.

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/katalog` | Würfelleiter, Stufen (Angriff/Verteidigung), Attribute mit Fertigkeiten, feste Werte (`nurFuer`: `monster`/`mensch`/`null`) |
| GET | `/figuren` | Alle nicht weggeworfenen Figuren der Kampagne mit `werte` (TraitDef-ID → Zahl) |
| POST | `/figuren` | `{name, istMonster, personType: "PC"\|"NPC"}` — legt `Person` mit Startwerten an |
| PATCH | `/figuren/{id}` | `name`, `personType`, `description` ändern |
| PUT | `/figuren/{id}/werte/{traitId}` | `{wert}` — Attribut: 4/6/8/12/20; Fertigkeit zusätzlich 0; feste Werte in ihren Grenzen (Stufe 1–5, Tamer-Level 1–4) |
| DELETE | `/figuren/{id}` | Papierkorb (`geloescht = true`), 204 |

Kampagne anlegen mit Spiel: `POST /api/campaigns {name, ruleset: "GridMonster"}`
(`ruleset` = Regelsystem-ID oder -Name).
