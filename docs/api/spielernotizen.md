# Spieler-Notizen

Privater Schmierzettel des Spielers. **Kein Wiki** (keine Seiten, keine
Freigabe, keine Verknüpfungen). Die Spielleitung sieht diese Einträge
nicht — sie hat an jeder Entität bereits Notizfelder.

Hängt am Spieler-Zugang (`(:Spieler)-[:HAT_NOTIZ]->(:SpielerNotiz)`),
nicht am Charakter: wechselt der PC, bleiben die Notizen.

---

## Endpunkte

Alle unter `/api/spieler/notizen`. Sitzung: Spieler-Cookie.
Fremde IDs → **404** (Existenz nicht verraten). GM ohne Spieler-Cookie → **403**.

### GET `/api/spieler/notizen`

Liste der eigenen Notizen, neueste Änderung zuerst.

```json
[
  {
    "id": "uuid",
    "titel": "Der Typ aus der Bar",
    "inhalt": "{\"type\":\"doc\",\"content\":[]}",
    "erstelltAm": "2026-10-02T08:00:00+00:00",
    "geaendertAm": "2026-10-02T08:15:00+00:00"
  }
]
```

`inhalt` ist TipTap-JSON als String.

### POST `/api/spieler/notizen`

```json
{ "titel": "Neue Notiz", "inhalt": "{\"type\":\"doc\",\"content\":[]}" }
```

Leerer Titel → 422.

### PATCH `/api/spieler/notizen/{notiz_id}`

```json
{ "titel": "Umbenannt", "inhalt": "…" }
```

Felder optional. Leerer Titel → 422. Fremde ID → 404.

### DELETE `/api/spieler/notizen/{notiz_id}`

**204**. Fremde ID → 404.
