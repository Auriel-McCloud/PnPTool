import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { spotifyApi, type SpotifyPlaylistTreffer } from "./api";
import "./spotify.css";

/**
 * Playlist-Suche für Orte/Events — Popup im selben Stil wie VerweisWaehler
 * (wiki/VerweisWaehler.tsx): Suchfeld oben, Treffer als klickbare Zeilen.
 *
 * Sucht live auf Spotify (kein lokaler Katalog) — die Ergebnisse ändern sich
 * mit jedem Tastenanschlag, deshalb ein kleines Debounce statt bei jedem
 * Zeichen sofort zu suchen.
 */
export function PlaylistWaehler({
  campaignId,
  offen,
  onWaehlen,
  onSchliessen,
}: {
  campaignId: string;
  offen: boolean;
  onWaehlen: (playlist: SpotifyPlaylistTreffer) => void;
  onSchliessen: () => void;
}) {
  const [suche, setSuche] = useState("");
  const [treffer, setTreffer] = useState<SpotifyPlaylistTreffer[]>([]);
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    setSuche("");
    setTreffer([]);
    setFehler(null);
  }, [offen]);

  useEffect(() => {
    if (!offen || !suche.trim()) {
      setTreffer([]);
      return;
    }
    let abgebrochen = false;
    setLaedt(true);
    setFehler(null);
    const timer = window.setTimeout(() => {
      spotifyApi
        .playlistsSuchen(campaignId, suche.trim())
        .then((r) => !abgebrochen && setTreffer(r))
        .catch((e) => !abgebrochen && setFehler(e instanceof Error ? e.message : "Suche fehlgeschlagen"))
        .finally(() => !abgebrochen && setLaedt(false));
    }, 350);
    return () => {
      abgebrochen = true;
      window.clearTimeout(timer);
    };
  }, [campaignId, offen, suche]);

  return (
    <Fenster
      offen={offen}
      titel="Spotify-Playlist verknüpfen"
      unterzeile="Läuft, wenn die aktive Party hier ankommt"
      kennung="spotify-playlist-waehler"
      onSchliessen={onSchliessen}
    >
      <input
        className="sp-suche"
        autoFocus
        type="search"
        placeholder="Playlist suchen…"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
      />

      {laedt && <p style={{ color: "var(--text-leise)" }}>Sucht…</p>}
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      {!laedt && !fehler && suche.trim() && treffer.length === 0 && (
        <p style={{ color: "var(--text-leise)" }}>Nichts gefunden.</p>
      )}
      {!suche.trim() && <p style={{ color: "var(--text-leise)" }}>Tippen, um auf Spotify zu suchen.</p>}

      <div className="sp-treffer">
        {treffer.map((p) => (
          <button key={p.uri} type="button" className="sp-treffer-zeile" onClick={() => onWaehlen(p)}>
            {p.bildUrl ? (
              <img className="sp-treffer-bild" src={p.bildUrl} alt="" />
            ) : (
              <span className="sp-treffer-bild sp-treffer-bild-leer" aria-hidden="true">
                🎵
              </span>
            )}
            <span className="sp-treffer-text">
              <span className="sp-treffer-name">{p.name}</span>
              <span className="sp-treffer-meta">
                {p.besitzer && `${p.besitzer} · `}
                {p.anzahlTracks} Titel
              </span>
            </span>
          </button>
        ))}
      </div>
    </Fenster>
  );
}
