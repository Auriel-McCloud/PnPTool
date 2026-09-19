# Party-API

Wer gerade zusammen unterwegs ist — Spielergruppen, Gegnergruppen, alles was
gemeinsam auftritt und einem Ort/Event zugeordnet werden soll.

## Konzept

**Ursprüngliche Vision, wiederentdeckt:** Am 28.08.2026 hatte Mark diese Idee
schon einmal skizziert (damals in `CLAUDE.md` festgehalten, beim großen
Verschlankungs-Commit versehentlich verlorengegangen — nur ein toter Verweis
in `docs/ui-konzept.md` blieb übrig). Am 18.09.2026 wieder aufgegriffen und
umgesetzt.

> *"Spieler bilden nicht immer eine einzige feste Gruppe — sie können sich
> aufteilen (2 gehen shoppen, 2 gehen zu einem NPC), wodurch mehrere
> gleichzeitige, temporäre Partys entstehen."* — Mark, 28.08.2026

**Abgrenzung zu Fraktion:** Eine Fraktion ist eine dauerhafte Organisation
mit eigenen Zielen und Ressourcen (Konzern, Gang, Regierung). Eine Party hat
keine eigenen Absichten — sie ist schlicht "wer gerade beisammen ist".
Deshalb ein eigener Bereich statt eine Erweiterung von Fraktionen.

**Design-Entscheidungen (Mark, 18.09.2026):**

1. **Eine Person ist höchstens in einer Party gleichzeitig.** Tritt sie
   einer neuen bei, verlässt sie automatisch die alte — keine
   Doppelmitgliedschaft möglich.
2. **Party ist ein dauerhaftes Objekt**, kein Ad-hoc-Wegwerfobjekt — einmal
   angelegt, bleibt sie bestehen (auch leer), bis sie explizit gelöscht wird.
3. **Gemischte Mitgliedschaft erlaubt** — PCs, NPCs und Begleiter-NPCs
   können in derselben Party stecken.
4. **Höchstens eine Party pro Kampagne ist "aktiv"** — die gerade bespielte.
   Aktivieren einer Party deaktiviert automatisch alle anderen. Die aktive
   Party löst — sobald sie einen Aufenthaltsort mit hinterlegter Playlist
   hat — automatisch die Spotify-Wiedergabe aus (siehe
   `docs/api/spotify.md`).

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/party`

### GET `/`

Alle Partys der Kampagne, mit Mitgliedern und Aufenthaltsort.

```json
[
  {
    "id": "uuid",
    "name": "Hauptgruppe",
    "beschreibung": "...",
    "notizen": "...",
    "aktiv": true,
    "mitglieder": [
      { "id": "person-uuid", "name": "Ryu Tanaka", "personType": "PC" }
    ],
    "aufenthaltsortId": "ort-uuid",
    "aufenthaltsortName": "Die Neon-Katze",
    "aufenthaltsortKind": "Ort",
    "sichtbarkeit": "GM",
    "sichtbarFuer": []
  }
]
```

### GET `/{party_id}`

Einzelne Party.

### POST `/` — **Nur SL**

```json
{ "name": "Hauptgruppe" }
```

### PATCH `/{party_id}` — **Nur SL**

Stammdaten ändern (Name, Beschreibung, Notizen, Sichtbarkeit).

### DELETE `/{party_id}` — **Nur SL**

Löst die Party auf. Mitglieder verlieren nur ihre `MITGLIED_VON`-Kante,
Personen selbst bleiben unangetastet.

### POST `/{party_id}/mitglieder` — **Nur SL**

```json
{ "personId": "uuid" }
```

Nimmt eine Person auf — verlässt dabei automatisch eine etwaige vorherige
Party.

### DELETE `/{party_id}/mitglieder/{person_id}` — **Nur SL**

Entfernt eine Person aus der Party, ohne sie einer neuen zuzuordnen.

### PUT `/{party_id}/aufenthaltsort` — **Nur SL**

```json
{ "zielId": "ort-uuid", "zielKind": "Ort" }
```

`zielKind` ist `"Ort"` oder `"Event"`. Mit `{ "zielId": null }` wird der
Aufenthaltsort gelöst — die Party gilt dann als "unterwegs". Ist diese
Party aktiv, löst der neue Aufenthaltsort automatisch die Spotify-Playlist
aus, die dort hinterlegt ist (siehe `docs/api/spotify.md`); die Antwort
trägt dann ein `musikHinweis`-Feld mit dem Ergebnis.

### POST `/{party_id}/aktivieren` — **Nur SL**

Macht diese Party zur aktiven. **Alle anderen Partys der Kampagne werden
serverseitig automatisch deaktiviert** — dieselbe Exklusivität wie bei einem
laufenden Kampf. Hat die Party bereits einen Aufenthaltsort, startet gleich
dessen Playlist; die Antwort trägt dann `musikHinweis`.

### POST `/{party_id}/deaktivieren` — **Nur SL**

Setzt nur diese Party auf inaktiv, ohne eine andere zu aktivieren (z.B. bei
einer Spielpause, wenn gerade niemand "dran" ist).

---

## Datenmodell (Neo4j)

```cypher
(:Party {
  id: "uuid",
  campaignId: "uuid",
  name: "Hauptgruppe",
  beschreibung: "...",
  notizen: "...",
  aktiv: true,
  sichtbarkeit: "GM",
  sichtbarFuer: []
})

// Mitgliedschaft — höchstens eine ausgehende Kante pro Person
(:Person)-[:MITGLIED_VON]->(:Party)

// Aufenthaltsort — optional, analog zur Gegenstands-Ablage
(:Party)-[:BEFINDET_SICH_AN]->(:Ort | :Event)

// Zugehörigkeit zur Kampagne, wie bei allen anderen Entitäten
(:Campaign)-[:HAT_ENTITAET]->(:Party)
```

**Beide Beziehungen folgen demselben Muster wie
`begleiter/repository.py::besitzer_setzen` und
`items/repository.py::set_ablage`:** vor dem Setzen einer neuen Kante wird
die alte gelöscht — nie zwei gleichzeitig, kein Verwaisen.

---

## Sichtbarkeit

Wie bei Begleitern: wer selbst Mitglied einer Party ist, sieht sie immer —
unabhängig von der gesetzten Sichtbarkeit. Sonst gilt das normale
GM/ALLE/SPEZIFISCH-Modell.

---

## Was noch fehlt (nächste Schritte, nicht Teil dieser ersten Fassung)

- **Inventar-Erweiterung:** Marks Idee, Party-Mitgliedern gegenseitig
  Gegenstände geben zu können (aktuell nur die SL darf Besitzer wechseln).
  Bewusst als Phase 2 zurückgestellt, damit die Grundfunktion nicht ausufert.
- **Party-Anzeige am Ort/Event selbst:** momentan sieht man den
  Aufenthaltsort nur von der Party-Kachel aus, nicht umgekehrt vom
  Ort-Detail-Popup ("welche Party ist gerade hier"). Naheliegende
  Ergänzung, noch nicht gebaut.

## Spotify/MusicCast-Anbindung (19.09.2026, gebaut)

Aktivieren einer Party mit gesetztem Aufenthaltsort — oder das Setzen eines
neuen Aufenthaltsorts an der aktiven Party — startet automatisch die dort
hinterlegte Spotify-Playlist. Details: [[../../docs/api/spotify.md]].
