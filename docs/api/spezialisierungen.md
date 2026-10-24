# Fertigkeiten-Spezialisierung

Code: `backend/app/spezialisierungen/`. Slots an der Person
(`(:Person)-[:HAT_SPEZIALISIERUNG]->(:Spezialisierung)`), nicht als
Property auf `HAS_TRAIT`.

Automatisch bei Fertigkeit/NeuroWeaving 4 und 6, bei Sphären 2/4/6.
Zusätzlich ab der ersten Schwelle für 4 EP kaufbar. **Senken des Ratings
löscht einen Slot nicht.** Wegnehmen kann nur die SL.

## SL räumt auf

- `GET /api/campaigns/{campaign_id}/spezialisierungen` — alle Slots der
  Kampagne, mit Personenname, Fertigkeitsname, Rating und `unterSchwelle`.
  Nur Spielleitung.
- `DELETE /api/campaigns/{campaign_id}/personen/{person_id}/spezialisierungen/{id}`
  — Slot löschen. Nur Spielleitung. Ein gekaufter Slot erstattet 4 EP
  (`erfahrungAusgegeben`). 204.
- `POST /api/campaigns/{campaign_id}/spezialisierungen/leere-unter-schwelle`
  — löscht nur leere automatische Slots unter der ersten Schwelle.
  Benannte und gekaufte bleiben. Antwort: `{ "entfernt": n }`.

Ein gelöschter automatischer Slot kommt erst wieder, wenn die Fertigkeit
die Schwelle erneut überschreitet.
