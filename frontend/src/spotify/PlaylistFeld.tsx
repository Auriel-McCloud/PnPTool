import { useState } from "react";
import { spotifyApi, type SpotifyPlaylistTreffer } from "./api";
import { PlaylistWaehler } from "./PlaylistWaehler";
import "./spotify.css";

/**
 * Spotify-Playlist-Feld für Orte/Events: zeigt die verknüpfte Playlist,
 * bietet Suche/Ändern/Entfernen und einen manuellen "Jetzt abspielen"-Knopf
 * (Fallback neben der Automatik, die beim Party-Aufenthaltsort greift).
 */
export function PlaylistFeld({
  campaignId,
  zielId,
  zielKind,
  playlistUri,
  playlistName,
  playlistBild,
  onGeaendert,
}: {
  campaignId: string;
  zielId: string;
  zielKind: "Ort" | "Event";
  playlistUri: string;
  playlistName: string;
  playlistBild: string;
  onGeaendert: (felder: { spotifyPlaylistUri: string; spotifyPlaylistName: string; spotifyPlaylistBild: string }) => void;
}) {
  const [waehlerOffen, setWaehlerOffen] = useState(false);
  const [spielt, setSpielt] = useState(false);
  const [hinweis, setHinweis] = useState<string | null>(null);

  function gewaehlt(p: SpotifyPlaylistTreffer) {
    setWaehlerOffen(false);
    onGeaendert({ spotifyPlaylistUri: p.uri, spotifyPlaylistName: p.name, spotifyPlaylistBild: p.bildUrl });
  }

  function entfernen() {
    onGeaendert({ spotifyPlaylistUri: "", spotifyPlaylistName: "", spotifyPlaylistBild: "" });
  }

  async function jetztAbspielen() {
    setSpielt(true);
    setHinweis(null);
    try {
      const r = await spotifyApi.abspielen(campaignId, zielId, zielKind);
      setHinweis(r.hinweis);
    } catch (e) {
      setHinweis(e instanceof Error ? e.message : "Abspielen fehlgeschlagen");
    } finally {
      setSpielt(false);
      window.setTimeout(() => setHinweis(null), 5000);
    }
  }

  return (
    <div>
      {playlistUri ? (
        <div className="sp-verknuepft">
          {playlistBild ? (
            <img className="sp-verknuepft-bild" src={playlistBild} alt="" />
          ) : (
            <span aria-hidden="true">🎵</span>
          )}
          <span className="sp-verknuepft-name">{playlistName || "Playlist"}</span>
          <button type="button" onClick={jetztAbspielen} disabled={spielt} title="Jetzt abspielen">
            {spielt ? "…" : "▶"}
          </button>
          <button type="button" onClick={() => setWaehlerOffen(true)} title="Andere Playlist wählen">
            ✎
          </button>
          <button
            type="button"
            onClick={entfernen}
            style={{ color: "var(--signal)" }}
            title="Verknüpfung entfernen"
          >
            ✕
          </button>
        </div>
      ) : (
        <button type="button" onClick={() => setWaehlerOffen(true)}>
          🎵 Spotify-Playlist verknüpfen
        </button>
      )}

      {hinweis && <p className="sp-hinweis">{hinweis}</p>}

      <PlaylistWaehler
        campaignId={campaignId}
        offen={waehlerOffen}
        onWaehlen={gewaehlt}
        onSchliessen={() => setWaehlerOffen(false)}
      />
    </div>
  );
}
