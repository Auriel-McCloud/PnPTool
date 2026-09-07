# Kontakte & Messenger API

In-Game-Kommunikation zwischen Spielercharakteren und NPCs — ein Cyberpunk-
Messenger im Persona-5-Stil.

## Konzept

Im NeotopiA-Setting hat jeder ein **Commlink** — ein AR-fähiges Smartphone der
Zukunft. Der Messenger ist die In-Game-Darstellung davon: Spieler können mit
NPCs chatten, die sie "kennengelernt" haben.

**Wichtige Design-Entscheidungen:**

1. **Kein sichtbarer Absender bei NPC-Nachrichten** — Die SL tippt, aber der
   Spieler sieht nur den NPC-Namen. Das Spiel bleibt immersiv.

2. **`chatOffen` getrennt von `stufe`** — Ein Spieler kann einen NPC nur
   "gesehen" haben (niedrige Stufe), aber trotzdem dessen Nummer haben, weil
   sie ausgetauscht wurde. Die Stufe bestimmt wie viel man *über* jemanden weiß,
   `chatOffen` ob man mit ihm *reden* kann.

3. **Spieler sehen NPCs nur unter Alias** — Kein echter Name, nur Spitzname
   oder Rassenbeschreibung ("Unbekannter Elf"). Erst wenn die Stufe steigt
   oder ein persönlicher Alias gesetzt wird, ändert sich das.

---

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/kontakte`

### GET `/`

Alle Kontakte für diesen Betrachter.

**Spieler-Response:**
```json
[
  {
    "id": "kontakt-uuid",
    "npcId": "npc-uuid",
    "npcAlias": "Kira",
    "npcRasse": "Mensch",
    "npcBildUrl": "/uploads/.../portrait.jpg",
    "persoenlicherAlias": "Die nette Hackerin",
    "stufe": 3,
    "chatOffen": true,
    "letzteNachricht": "Hey, hast du die Daten?",
    "letzteNachrichtZeit": "2026-09-07T20:00:00.000Z",
    "ungelesen": 2
  }
]
```

**SL-Response:** Zusätzlich `pcId`, `pcName`, `npcName` (echte Namen).

---

### POST `/`

Neuen Kontakt anlegen. **Nur SL.**

```json
{
  "pcId": "spieler-uuid",
  "npcId": "npc-uuid",
  "stufe": 1,
  "chatOffen": false,
  "persoenlicherAlias": ""
}
```

---

### PATCH `/{kontakt_id}`

Kontakt aktualisieren. **Nur SL.**

```json
{
  "stufe": 3,
  "chatOffen": true,
  "persoenlicherAlias": "Mein Fixer"
}
```

---

### GET `/{kontakt_id}/chat`

Chat-Verlauf für diesen Kontakt.

```json
{
  "nachrichten": [
    {
      "id": "nachricht-uuid",
      "inhalt": "Hey, ich brauch Info über Tanaka Corp.",
      "vonPc": true,
      "zeit": "2026-09-07T19:55:00.000Z"
    },
    {
      "id": "nachricht-uuid",
      "inhalt": "Tanaka? Die sind gefährlich. Komm vorbei, ich erzähl dir mehr.",
      "vonPc": false,
      "zeit": "2026-09-07T19:57:00.000Z"
    }
  ]
}
```

`vonPc: true` = Spieler hat geschrieben, `vonPc: false` = NPC hat geschrieben.

---

### POST `/{kontakt_id}/chat`

Nachricht senden. **Spieler und SL.**

```json
{
  "inhalt": "Bin in 10 Minuten da."
}
```

**Response:**
```json
{
  "id": "nachricht-uuid",
  "inhalt": "Bin in 10 Minuten da.",
  "vonPc": true,
  "zeit": "2026-09-07T20:01:00.000Z",
  "absender": "Ryu"
}
```

**Seiteneffekt:** Erstellt automatisch eine NACHRICHT-Mitteilung für den
Empfänger (siehe [Mitteilungen](./mitteilungen.md)).

**Fehler:**
- `409 Conflict` wenn `chatOffen: false` — "Der Chat ist nicht geöffnet"

---

## Stufensystem

Die **Stufe** bestimmt, wie viel ein Spielercharakter über einen NPC weiß:

| Stufe | Was der Spieler sieht | Beschreibung |
|-------|----------------------|--------------|
| 0 | Rasse ("Unbekannter Elf") | Nur flüchtig gesehen |
| 1 | Alias oder Rasse | Kurz getroffen |
| 2 | + Beruf/Rolle | Länger gesprochen |
| 3 | + Hintergrund-Teaser | Vertraut |
| 4 | + Voller Hintergrund | Enger Kontakt |
| 5 | + SL-Notizen | Intim bekannt |

**Stufe beeinflusst NICHT den Chat** — ein Spieler kann Stufe 1 haben (weiß
fast nichts) aber trotzdem `chatOffen: true` (hat die Nummer).

---

## Alias-Logik

Was zeigt der Spieler als Namen?

```python
def effektiver_alias(npc_alias, persoenlicher_alias):
    # Persönlicher Alias überschreibt alles
    if persoenlicher_alias:
        return persoenlicher_alias
    # Sonst NPC-Alias (von SL gepflegt)
    if npc_alias:
        return npc_alias
    # Fallback: Rasse
    return standard_alias(rasse)  # "Unbekannter Mensch"
```

**Warum persönlicher Alias?**
> Der Spieler kann sich eigene Notizen machen: "Der Typ aus der Bar" statt
> dem offiziellen Alias "Viktor". Das ist sein Adressbuch.

---

## Chat-Benachrichtigungen

Wenn eine Nachricht gesendet wird, passiert:

1. Nachricht wird in Neo4j gespeichert
2. Eine NACHRICHT-Mitteilung wird erstellt:
   - SL → Spieler: `empfaengerIds = [spieler_pc_id]`
   - Spieler → NPC: `empfaengerIds = []` (leer = an SL)
3. Mitteilung wird via WebSocket gepusht
4. Empfänger sieht Popup: "💬 Kira: Hey, hast du..."

**Warum über Mitteilungen statt eigenen WebSocket?**
> Das Mitteilungen-System hat schon WebSocket-Support, Reconnect-Logik,
> Popup-Darstellung. Warum das Rad neu erfinden?

---

## Datenmodell (Neo4j)

```cypher
// Kontakt-Beziehung zwischen PC und NPC
(:Person {id: "pc-uuid", personType: "PC"})
  -[:KENNT {
    id: "kontakt-uuid",
    campaignId: "uuid",
    stufe: 3,
    chatOffen: true,
    persoenlicherAlias: "Mein Fixer"
  }]->
(:Person {id: "npc-uuid", personType: "NPC"})

// Nachrichten als eigene Nodes
(:Nachricht {
  id: "uuid",
  campaignId: "uuid",
  inhalt: "...",
  vonId: "sender-uuid",
  anId: "empfaenger-uuid",
  zeit: "2026-09-07T20:00:00.000Z"
})
```

**Warum Nachrichten als Nodes statt Properties?**
> Ein Chat kann hunderte Nachrichten haben. Als Array-Property wäre das
> unhandlich (kein Paging, keine Indizes). Separate Nodes erlauben effiziente
> Queries: "Die letzten 50 Nachrichten zwischen A und B".

---

## UI-Design

Der Messenger ist im **Persona-5-Stil** gestaltet:
- Schräge Sprechblasen mit harten Kanten
- Portraits links/rechts je nach Absender
- Neon-Cyberpunk-Farbpalette (via CSS-Tokens)
- Glitch-Effekte bei neuen Nachrichten

**CSS-Struktur:**
- `frontend/src/kontakte/messenger.css` — Spieler-Messenger (517 Zeilen)
- `frontend/src/kontakte/kontakte-gm.css` — SL-Ansicht mit Chat-Popup
