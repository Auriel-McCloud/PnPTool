# Verhandlungen

Generisches Angebot → Annehmen/Ablehnen. Dieselbe Live-Leitung wie
SL-Mitteilungen (`app/mitteilungen/verteiler.py`), Umschlag `_typ: "verhandlung"`.
Kein zweites WebSocket.

Modul: `backend/app/verhandlung/` (`schemas.py`, `repository.py`, `logic.py`,
`routes.py`). Frontend: `frontend/src/verhandlung/VerhandlungPopup.tsx`.

## Konzept

Eine Verhandlung ist ein gespeicherter Knoten mit Status `OFFEN` /
`ANGENOMMEN` / `ABGELEHNT`. Der Empfänger sieht ein Commlink-Popup und
antwortet selbst — die SL antwortet **nicht stellvertretend**.

Was bei Annahme passiert, hängt an `art` (Dispatch-Tabelle in `logic.py`).
Neue Art = neuer Tabelleneintrag, bestehendes Popup bleibt.

## Arten

| `art` | Wer bietet an | Nebenwirkung bei Annahme |
|---|---|---|
| `RUESTUNG_REPARATUR` | nur SL | Kapital abziehen, Rüstungskästchen reparieren. Siehe `docs/api/ruestung.md`. |
| `SHOP_KAUF` | nur SL | Kauf zum verhandelten Preis. Siehe `docs/api/haendler.md`. |
| `GEGENSTAND_WEITERGABE` | nur Spieler | `transfer_owner` auf den Empfänger. Kein Geld. |

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/verhandlungen`

### POST `/` — Angebot erstellen (nur SL)

Body `VerhandlungCreate`: `empfaengerPersonId`, `art`, `positionen`
(`bezeichnung`, `betrag`), `kontext` (artabhängig, z. B. `gegenstandId`).
`201` + Live-Push an den Empfänger.

### POST `/gegenstand-weitergeben` — Spieler gibt weiter

Spieler-zu-Spieler, **ohne** `require_campaign_gm`. Body:

```json
{ "gegenstandId": "...", "empfaengerPersonId": "..." }
```

Prüfungen serverseitig:

- Aufrufer ist Spieler mit `person_id` (GM → `403`)
- nicht an sich selbst (`400`)
- Gegenstand gehört dem Aufrufer (`403` sonst)
- Aufrufer ist in einer Party (`400` sonst)
- Empfänger ist Mitglied derselben Party (`400` sonst)

`kontext` speichert `{gegenstandId, absenderPersonId}`. Positionsliste nur
für die Popup-Bezeichnung (`betrag: 0`). Bei Annahme prüft
`_ausfuehren_gegenstand_weitergabe` den Besitz noch einmal live.

Whitelist: `OHNE_GM_ERLAUBT` in `tests/test_zugriffsschutz.py`.

### GET `/` — offene Angebote für den eigenen Charakter

Aufhol-Liste nach Reconnect. Ohne `person_id` leere Liste.

### GET `/{verhandlung_id}`

Spieler nur das eigene Angebot, sonst `404` (Existenz nicht bestätigen).
SL sieht alle.

### POST `/{verhandlung_id}/antwort`

Body `{ "angenommen": true|false }`. Nur der Empfänger. Schon entschieden →
`409`. Ablehnen setzt Status, Annahme ruft `logic.ausfuehren` auf
(`VerhandlungsFehler` → `409`, z. B. Gegenstand weg).

### DELETE `/{verhandlung_id}` — zurückziehen (nur SL)

Nur offene Angebote / Testdaten. `204`.

## Live-Zustellung

Umschlag ergänzt `empfaengerIds: [empfaengerPersonId]`, damit
`darf_empfangen` greift (Verhandlungen haben intern `empfaengerPersonId`,
Mitteilungen `empfaengerIds`). Frontend: `MitteilungenKontext.tsx` hält eine
eigene Schlange analog zu SL-Mitteilungen.

## Siehe auch

- `docs/wiki/entities/gegenstand-transfer.md` — Party-Transfer, offene Ideen
- `docs/api/ruestung.md` — Reparatur-Verhandlung
- `docs/api/haendler.md` — Shop-Kauf-Verhandlung
- `docs/api/mitteilungen.md` — der geteilte Live-Kanal
