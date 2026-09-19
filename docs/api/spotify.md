# Spotify-API

Musik folgt der aktiven Party: Orte und Events können eine Spotify-Playlist
hinterlegen. Wechselt die aktive Party dorthin (oder wird eine Party mit
bereits gesetztem Aufenthaltsort aktiviert), startet die Wiedergabe
automatisch auf dem gerade aktiven Spotify-Gerät. Ein manueller Knopf
(„▶") daneben spielt sie jederzeit sofort ab, unabhängig von der Party.

## Konzept

**Ein Konto fürs ganze Tool** (Marks Entscheidung, 19.09.2026) — keine
Trennung pro Kampagne. Mark hat ein Premium-Konto, das genügt für den
Spieltisch.

**Kein festes Wiedergabegerät im Tool.** Mark wählt Ziel-Gerät (Yamaha
RX-V4A/MusicCast, Handy, …) und Lautstärke am Handy selbst über Spotify
Connect — das Tool greift dort nicht ein und speichert keine Geräte-ID. Es
ruft `PUT /me/player/play` ohne `device_id` auf, wirkt also auf das gerade
aktive Gerät.

**Automatik + manueller Fallback** (Marks Entscheidung): Wiedergabe startet
automatisch, wenn

1. die aktive Party einen neuen Aufenthaltsort mit hinterlegter Playlist
   bekommt (`PUT .../party/{id}/aufenthaltsort`), oder
2. eine Party mit bereits gesetztem Aufenthaltsort aktiviert wird
   (`POST .../party/{id}/aktivieren`).

Daneben gibt es einen expliziten „▶ Jetzt abspielen"-Knopf an
Ort/Event (z.B. zum Testen ohne Party-Umweg).

**Spotify-Fehler blockieren nie die Party-Aktion.** Kein aktives Gerät,
Konto nicht verbunden, Premium fehlt — die Party wechselt trotzdem den
Aufenthaltsort/wird trotzdem aktiv, nur der Musik-Hinweis erklärt, was
(nicht) passiert ist. Siehe `app/spotify/dienst.py`.

---

## Globale Verbindung (nicht kampagnengebunden)

Basis: `/api/spotify` — **nur die Spielleitung.**

### GET `/status`

```json
{ "verbunden": true, "anzeigename": "Mark" }
```

### GET `/verbinden`

Volle Seitennavigation (kein `fetch`), leitet zum Spotify-Login weiter.
Nach Zustimmung landet der Browser auf `/callback`, das wiederum auf
`FRONTEND_BASE_URL?spotify=verbunden` (oder `?spotify=fehler`) zurückleitet.

### GET `/callback`

Nimmt den Authorization Code entgegen, tauscht ihn gegen Access+Refresh-
Token, speichert Letzteren in Neo4j. **Ohne Auth-Abhängigkeit** — die
Redirect-URI liegt auf `127.0.0.1:8001`, einem anderen Host als
`localhost:5173`, das Sitzungs-Cookie käme dort nicht an. Ein kurzlebiger
`state`-Nonce übernimmt die CSRF-Absicherung (Standard beim
Authorization-Code-Flow).

### POST `/trennen`

Löscht den `SpotifyKonto`-Knoten.

---

## Playlist-Suche & Wiedergabe (kampagnengebunden)

Basis: `/api/campaigns/{campaign_id}/spotify` — **nur die Spielleitung.**

### GET `/suche?q=...`

Durchsucht Spotify nach Playlists (max. 10 Treffer — Spotifys
Development-Mode-Apps lehnen seit dem Februar-2026-Umbau `limit`-Werte
über 10 mit `400 Invalid limit` ab, siehe `client.py::suche_playlists`).

```json
[{ "uri": "spotify:playlist:...", "id": "...", "name": "Neon Nights",
   "besitzer": "Mark", "bildUrl": "https://...", "anzahlTracks": 42 }]
```

### POST `/abspielen`

```json
{ "zielId": "ort-uuid", "zielKind": "Ort" }
```

Startet sofort die am Ziel hinterlegte Playlist. `409`, wenn dort keine
hinterlegt ist.

---

## Playlist an Ort/Event hinterlegen

Kein eigener Endpunkt — einfach drei Felder am bestehenden Ort/Event-PATCH
(`app/entities/schemas.py`, `ORT_FIELDS`/`EVENT_FIELDS`):

```json
{
  "spotifyPlaylistUri": "spotify:playlist:...",
  "spotifyPlaylistName": "Neon Nights",
  "spotifyPlaylistBild": "https://..."
}
```

Leere Strings lösen die Verknüpfung. Das Frontend (`spotify/PlaylistFeld.tsx`)
öffnet dafür ein Such-Popup (`spotify/PlaylistWaehler.tsx`, gleiches Muster
wie `wiki/VerweisWaehler.tsx`) statt die URI manuell eintippen zu lassen.

---

## Datenmodell (Neo4j)

```cypher
(:SpotifyKonto {
  id: "global",
  refreshToken: "...",
  anzeigename: "Mark",
  verbundenAm: datetime()
})
```

Ein einzelner Knoten mit fester ID (`"global"`), kein Verweis auf eine
Kampagne — global im ganzen Tool. Der Access-Token selbst wird NICHT
persistiert, nur prozessweit zwischengehalten (`app/spotify/repository.py`,
`_cache`); er lebt eh nur eine Stunde, ein Neustart holt einfach einen
frischen über den Refresh-Token.

Playlist-Verknüpfung ist keine eigene Kante, sondern drei Properties direkt
am `:Ort`/`:Event`-Knoten (`spotifyPlaylistUri/Name/Bild`) — dieselbe
"Metadaten am Knoten" wie bei `bildUrl`.

---

## Konfiguration (`backend/.env`)

```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8001/api/spotify/callback
```

Die Redirect-URI muss **exakt** so im Spotify-Dashboard
(developer.spotify.com/dashboard) hinterlegt sein. Spotify verlangt seit
2025 eine explizite Loopback-IP (`127.0.0.1`) statt `localhost`.

Scopes: `user-modify-playback-state user-read-playback-state
playlist-read-private user-read-private` (siehe `app/spotify/client.py`).

---

## Was noch fehlt

- **MusicCast-Direktanbindung:** Aktuell läuft alles über Spotify Connect
  (Mark wählt Gerät/Lautstärke am Handy) — eine direkte Ansteuerung des
  Yamaha RX-V4A über die MusicCast-API ist nicht gebaut und aktuell auch
  nicht geplant, weil Spotify Connect den Anwendungsfall schon abdeckt.
- **Ort-Detail zeigt nicht, ob die Party gerade hier ist** — dieselbe Lücke
  wie in `docs/api/party.md` vermerkt.
