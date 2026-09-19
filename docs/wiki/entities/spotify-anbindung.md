---
title: Spotify-Anbindung
created: 2026-09-19
updated: 2026-09-19
type: entität
tags: [spotify, musik, party, backend, frontend]
sources: [../../api/spotify.md, ../../../backend/app/spotify/]
status: aktuell
---

# Spotify-Anbindung

Musik folgt der aktiven Party — die am 18.09.2026 wieder aufgegriffene
Vision aus dem Party-Feature ([[party-feature]]) ist jetzt umgesetzt.

## Design-Entscheidungen (Mark, 19.09.2026)

1. **Ein Konto fürs ganze Tool**, nicht pro Kampagne — Mark hat ein
   Premium-Konto, das reicht für seinen Spieltisch.
2. **Automatik + manueller Fallback-Knopf.** Wiedergabe startet
   automatisch, wenn die aktive Party einen neuen Aufenthaltsort mit
   hinterlegter Playlist bekommt, oder eine Party mit bereits gesetztem
   Ort aktiviert wird. Ein „▶"-Knopf am Ort/Event startet sie daneben
   jederzeit manuell.
3. **Kein festes Wiedergabegerät im Tool.** Ursprünglich stand zur
   Diskussion, ein Zielgerät (Yamaha RX-V4A) in den Einstellungen fest zu
   verdrahten. Mark entschied sich dagegen: er kann am Handy ohnehin
   auswählen, wohin Spotify Connect gerade spielt, und die Lautstärke
   dort regeln — das Tool ruft `PUT /me/player/play` **ohne** `device_id`
   auf und wirkt so auf das gerade aktive Gerät, unabhängig davon welches
   das ist.
4. **Kein Spotify-Fehler blockiert je die Party-Aktion.** Aufenthaltsort
   setzen oder Party aktivieren gelingt immer; ein `musikHinweis`-Text in
   der Antwort erklärt nur, ob/was Spotify getan hat ("nicht verbunden",
   "kein aktives Gerät", "Wiedergabe gestartet: ...").

## Warum Client Credentials NICHT reichen

Erste Überlegung war der einfachere Client-Credentials-Flow (kein
Nutzerlogin nötig). Scheitert aber an `PUT /me/player/play` — Wiedergabe
steuern verlangt einen **User-Access-Token** mit
`user-modify-playback-state`-Scope, den es nur über den vollen
Authorization-Code-Flow gibt. Deshalb der OAuth-Login-Knopf in den
Kampagnen-Einstellungen statt einer reinen Server-zu-Server-Anbindung.

## Redirect-URI-Eigenheit

Spotify verlangt seit 2025 eine explizite Loopback-IP (`127.0.0.1:PORT`)
statt `localhost` als Redirect-URI. Die Callback-Route liegt deshalb auf
`127.0.0.1:8001` — einem anderen Host als das Frontend
(`localhost:5173`) — und bekommt dadurch **nicht** das Sitzungs-Cookie
mitgeschickt (Cookies sind host-gebunden, `127.0.0.1` ≠ `localhost`). Die
Callback-Route läuft deshalb bewusst ohne Auth-Abhängigkeit; ein
kurzlebiger `state`-Nonce übernimmt die CSRF-Absicherung, wie beim
Authorization-Code-Flow ohnehin üblich.

## Datenmodell

Ein einzelner `:SpotifyKonto`-Knoten mit fester ID (`"global"`), kein
Kampagnenbezug. Playlist-Verknüpfung ist keine eigene Kante, sondern drei
Properties direkt am `:Ort`/`:Event`-Knoten
(`spotifyPlaylistUri/Name/Bild`) — dasselbe Muster wie `bildUrl`.

Vollständige API-Referenz: [[../../api/spotify.md]].

## Frontend

Playlist-Suche als Popup (`spotify/PlaylistWaehler.tsx`), gleiches Muster
wie `wiki/VerweisWaehler.tsx`: Suchfeld oben, klickbare Trefferzeilen mit
Cover-Bild. Eingebaut in `OrtDetail`/`EventDetail` über die gemeinsame
Komponente `spotify/PlaylistFeld.tsx` (Anzeige der verknüpften Playlist +
Ändern/Entfernen + manueller Abspiel-Knopf).

Verbinden/Trennen sitzt in den Kampagnen-Einstellungen
(`EinstellungenFenster.tsx`, neue Sektion „MUSIK") — Verbinden ist ein
echter `<a href>`-Link (volle Seitennavigation für den OAuth-Redirect),
kein `fetch()`.

## Offen

- MusicCast-Direktanbindung ist nicht geplant — Spotify Connect deckt den
  Anwendungsfall (Gerätewahl, Lautstärke) bereits ab.
- Party-Anzeige am Ort/Event-Popup fehlt weiterhin (siehe
  [[party-feature]], "Offen").

## Siehe auch

- [[../../api/spotify.md]] — vollständige Endpunkt-Referenz
- [[party-feature]] — aktive Party als Auslöser
