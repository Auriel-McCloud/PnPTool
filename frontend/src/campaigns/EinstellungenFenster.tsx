import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { einstellungenApi, kampagnenExportApi, type Einstellungen } from "./einstellungen";
import { spotifyApi, type SpotifyStatus } from "../spotify/api";
import { wikiSweep, wikiVerknuepfungSweep, type SweepErgebnis, type SweepVerknuepfungErgebnis } from "../ideenschmiede/api";
import { PruefungPopup } from "../wiki/PruefungPopup";
import { SweepVerknuepfungPopup } from "../ideenschmiede/SweepVerknuepfungPopup";
import "../spotify/spotify.css";

/**
 * Kampagnenweite Spieleinstellungen.
 *
 * Bisher gab es die Werte nur im Backend — sie waren nicht bedienbar. Mark
 * wollte das digitale Würfeln ausdrücklich *"als Kampagnen weite Option"*,
 * also braucht es einen Ort dafür.
 */

function Schalter({
  an,
  onAendern,
  titel,
  erklaerung,
}: {
  an: boolean;
  onAendern: (neu: boolean) => void;
  titel: string;
  erklaerung: string;
}) {
  return (
    <label
      style={{
        display: "flex",
        gap: 10,
        alignItems: "flex-start",
        padding: "10px 0",
        borderBottom: "1px solid var(--linie)",
        cursor: "pointer",
      }}
    >
      <input
        type="checkbox"
        checked={an}
        onChange={(e) => onAendern(e.target.checked)}
        style={{ marginTop: 3 }}
      />
      <span style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
        <strong style={{ fontSize: 14 }}>{titel}</strong>
        <span style={{ fontSize: 12, color: "var(--text-leise)", overflowWrap: "anywhere" }}>
          {erklaerung}
        </span>
      </span>
    </label>
  );
}

export function EinstellungenFenster({
  campaignId,
  campaignName,
  offen,
  onSchliessen,
  onImportiert,
}: {
  campaignId: string;
  campaignName: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Nach erfolgreichem Import: neue Kampagne (id/name) an die Auswahl melden. */
  onImportiert: (kampagne: { id: string; name: string }) => void;
}) {
  const [werte, setWerte] = useState<Einstellungen | null>(null);
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [spotifyStatus, setSpotifyStatus] = useState<SpotifyStatus | null>(null);
  const [spotifyHinweis, setSpotifyHinweis] = useState<string | null>(null);

  // Wiki-Fließtextprüfung: kampagnenweiter Sweep (Rechtschreibung/Grammatik/
  // Logik), überspringt Seiten, die seit der letzten Prüfung unverändert
  // sind. Bewusst nur auf Knopfdruck — Mark will das gezielt ab und zu
  // anstoßen, nicht bei jeder Kleinigkeit KI-Kosten verursachen.
  const [pruefLaeuft, setPruefLaeuft] = useState(false);
  const [pruefFehler, setPruefFehler] = useState<string | null>(null);
  const [sweepErgebnis, setSweepErgebnis] = useState<SweepErgebnis | null>(null);
  const [pruefStamp, setPruefStamp] = useState(0);

  // Auto-Verknüpfung: kampagnenweiter Sweep über alle Wiki-Seiten, erkennt
  // erwähnte Personen/Orte/Events/Fraktionen und ihre Beziehungen — für
  // Altbestand, der vor Einführung der Funktion angelegt wurde. Läuft
  // unabhängig vom Fließtext-Sweep oben (eigener Hash, eigener Knopf).
  const [verknuepfLaeuft, setVerknuepfLaeuft] = useState(false);
  const [verknuepfFehler, setVerknuepfFehler] = useState<string | null>(null);
  const [verknuepfErgebnis, setVerknuepfErgebnis] = useState<SweepVerknuepfungErgebnis | null>(null);
  const [verknuepfStamp, setVerknuepfStamp] = useState(0);

  // Kampagnen-Export/Import: kompletter Datentransfer als ZIP (siehe
  // docs/api/campaigns-export-import.md). Export ist ein simpler Download,
  // Import läuft asynchron über einen Datei-Upload.
  const [importLaeuft, setImportLaeuft] = useState(false);
  const [importFehler, setImportFehler] = useState<string | null>(null);
  const [importErfolg, setImportErfolg] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    einstellungenApi
      .lesen(campaignId)
      .then(setWerte)
      .catch((e) => setFehler(e instanceof Error ? e.message : "Konnte nicht laden"));
    spotifyApi.status().then(setSpotifyStatus).catch(() => setSpotifyStatus(null));

    // Rücksprung vom Spotify-Login trägt ?spotify=verbunden|fehler in der
    // Adresse — hier abfangen und die URL wieder säubern, sonst bliebe der
    // Parameter beim nächsten Neuladen stehen.
    const params = new URLSearchParams(window.location.search);
    const ergebnis = params.get("spotify");
    if (ergebnis) {
      setSpotifyHinweis(ergebnis === "verbunden" ? "Mit Spotify verbunden." : "Verbindung fehlgeschlagen.");
      params.delete("spotify");
      const rest = params.toString();
      window.history.replaceState({}, "", window.location.pathname + (rest ? `?${rest}` : ""));
    }
  }, [campaignId, offen]);

  async function spotifyTrennen() {
    await spotifyApi.trennen();
    setSpotifyStatus({ verbunden: false, anzeigename: null });
  }

  async function pruefFliesstext() {
    setPruefLaeuft(true);
    setPruefFehler(null);
    try {
      const ergebnis = await wikiSweep(campaignId);
      setSweepErgebnis(ergebnis);
      setPruefStamp((n) => n + 1);
    } catch (e) {
      setPruefFehler(e instanceof Error ? e.message : "Prüfung fehlgeschlagen");
    } finally {
      setPruefLaeuft(false);
    }
  }

  async function verknuepfungSweep() {
    setVerknuepfLaeuft(true);
    setVerknuepfFehler(null);
    try {
      const ergebnis = await wikiVerknuepfungSweep(campaignId);
      setVerknuepfErgebnis(ergebnis);
      setVerknuepfStamp((n) => n + 1);
    } catch (e) {
      setVerknuepfFehler(e instanceof Error ? e.message : "Verknüpfung fehlgeschlagen");
    } finally {
      setVerknuepfLaeuft(false);
    }
  }

  async function kampagneImportieren(datei: File) {
    setImportLaeuft(true);
    setImportFehler(null);
    setImportErfolg(null);
    try {
      const neu = await kampagnenExportApi.importieren(datei);
      setImportErfolg(`„${neu.name}" wurde als neue Kampagne angelegt.`);
      onImportiert(neu);
    } catch (e) {
      setImportFehler(e instanceof Error ? e.message : "Import fehlgeschlagen");
    } finally {
      setImportLaeuft(false);
    }
  }

  async function aendern(feld: string, wert: unknown) {
    if (!werte) return;
    // Sofort anzeigen, dann speichern — sonst wirkt der Schalter träge.
    setWerte({ ...werte, [feld]: wert });
    setSpeichert(true);
    setFehler(null);
    try {
      const neu = await einstellungenApi.aendern(campaignId, { [feld]: wert });
      setWerte(neu);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht speichern");
      // Zurückdrehen, damit der Schalter nicht lügt.
      setWerte(werte);
    } finally {
      setSpeichert(false);
    }
  }

  if (!offen) return null;

  return (
    <>
    <Fenster titel="Einstellungen" kennung="einstellungen" offen={offen} onSchliessen={onSchliessen}>
      {!werte && !fehler && <p style={{ color: "var(--text-leise)" }}>Lädt…</p>}

      {werte && (
        <>
          <h4 style={{ margin: "4px 0 2px", fontSize: 12, color: "var(--text-aus)", letterSpacing: "0.08em" }}>
            WÜRFELN
          </h4>

          <Schalter
            an={Boolean(werte.digitalesWuerfeln)}
            onAendern={(n) => aendern("digitalesWuerfeln", n)}
            titel="Digitales Würfeln"
            erklaerung="Spieler können im Tool würfeln statt am Tisch. Aus, wenn ihr echte Würfel benutzt — sie melden dann nur ihre Erfolge."
          />

          <Schalter
            an={Boolean(werte.digitalesWuerfelnSL)}
            onAendern={(n) => aendern("digitalesWuerfelnSL", n)}
            titel="Digitales Würfeln (Spielleitung)"
            erklaerung="Die Initiative der NPCs und Begleiter würfelt das Tool auf Knopfdruck — auch wenn die Spieler physisch würfeln."
          />

          <h4 style={{ margin: "16px 0 2px", fontSize: 12, color: "var(--text-aus)", letterSpacing: "0.08em" }}>
            WEITERE
          </h4>

          <Schalter
            an={Boolean(werte.gewichtAktiv)}
            onAendern={(n) => aendern("gewichtAktiv", n)}
            titel="Gewicht und Traglast"
            erklaerung="Zeigt Auslastung an. Rein informativ — nichts wird verhindert, der Balken färbt sich nur rot."
          />

          <Schalter
            an={Boolean(werte.messengerAktiv)}
            onAendern={(n) => aendern("messengerAktiv", n)}
            titel="Messenger"
            erklaerung="In-World-Chat zwischen Charakteren. Noch im Bau."
          />

          <h4 style={{ margin: "16px 0 2px", fontSize: 12, color: "var(--text-aus)", letterSpacing: "0.08em" }}>
            WIKI
          </h4>

          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0" }}>
            <button
              type="button"
              onClick={pruefFliesstext}
              disabled={pruefLaeuft}
              title="Prüft alle Wiki-Seiten auf Rechtschreibung, Grammatik und Logikfehler — überspringt Seiten, die sich seit der letzten Prüfung nicht geändert haben."
            >
              {pruefLaeuft ? "prüft…" : "🔍 Fließtext prüfen"}
            </button>
            {sweepErgebnis && (
              <span style={{ fontSize: 12, color: "var(--text-leise)" }}>
                {sweepErgebnis.geprueft} geprüft, {sweepErgebnis.uebersprungen} unverändert übersprungen
              </span>
            )}
          </div>
          {pruefFehler && <p style={{ fontSize: 12, color: "var(--signal)" }}>{pruefFehler}</p>}

          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0" }}>
            <button
              type="button"
              onClick={verknuepfungSweep}
              disabled={verknuepfLaeuft}
              title="Durchsucht alle Wiki-Seiten nach erwähnten Personen/Orten/Events/Fraktionen und ihren Beziehungen — überspringt Seiten, die sich seit dem letzten Sweep nicht geändert haben."
            >
              {verknuepfLaeuft ? "sucht…" : "⧉✨ Auto-Verknüpfung — alle Seiten"}
            </button>
            {verknuepfErgebnis && (
              <span style={{ fontSize: 12, color: "var(--text-leise)" }}>
                {verknuepfErgebnis.geprueft} geprüft, {verknuepfErgebnis.uebersprungen} unverändert übersprungen
              </span>
            )}
          </div>
          {verknuepfFehler && <p style={{ fontSize: 12, color: "var(--signal)" }}>{verknuepfFehler}</p>}

          <h4 style={{ margin: "16px 0 2px", fontSize: 12, color: "var(--text-aus)", letterSpacing: "0.08em" }}>
            MUSIK
          </h4>

          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0" }}>
            {spotifyStatus === null && <span style={{ color: "var(--text-leise)", fontSize: 12 }}>Lädt…</span>}
            {spotifyStatus && !spotifyStatus.verbunden && (
              <a href="/api/spotify/verbinden" role="button" className="sp-verbinden">
                🎵 Mit Spotify verbinden
              </a>
            )}
            {spotifyStatus?.verbunden && (
              <>
                <span style={{ fontSize: 13 }}>
                  Verbunden als <strong>{spotifyStatus.anzeigename}</strong>
                </span>
                <button type="button" onClick={spotifyTrennen} style={{ color: "var(--signal)" }}>
                  Trennen
                </button>
              </>
            )}
          </div>
          {spotifyHinweis && <p style={{ fontSize: 12, color: "var(--text-leise)" }}>{spotifyHinweis}</p>}
          <p style={{ fontSize: 11, color: "var(--text-aus)" }}>
            Ein Konto fürs ganze Tool. Playlists werden an Orten/Events hinterlegt — läuft die aktive Party
            dort ein, startet die Wiedergabe automatisch auf deinem gerade verbundenen Spotify-Gerät.
          </p>

          <h4 style={{ margin: "16px 0 2px", fontSize: 12, color: "var(--text-aus)", letterSpacing: "0.08em" }}>
            KAMPAGNE
          </h4>

          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={() => kampagnenExportApi.exportieren(campaignId, campaignName)}
              title="Lädt die komplette Kampagne (alle Daten, Bilder und Spieler-Zugänge) als ZIP-Datei herunter."
            >
              ⬇ Kampagne exportieren
            </button>

            <label
              className="cl-roehre"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                fontSize: 13,
                fontFamily: "var(--mono)",
                cursor: importLaeuft ? "wait" : "pointer",
              }}
            >
              {importLaeuft ? "importiert…" : "⬆ Kampagne importieren"}
              <input
                type="file"
                accept=".zip,application/zip"
                disabled={importLaeuft}
                style={{ display: "none" }}
                onChange={(e) => {
                  const datei = e.target.files?.[0];
                  e.target.value = "";
                  if (datei) kampagneImportieren(datei);
                }}
              />
            </label>
          </div>
          <p style={{ fontSize: 11, color: "var(--text-aus)" }}>
            Import legt immer eine <strong>neue</strong> Kampagne an, nie eine bestehende wird überschrieben.
            Enthält die ZIP-Datei Spieler-Zugänge, gelten deren bisherige Passwörter unverändert weiter.
          </p>
          {importFehler && <p style={{ fontSize: 12, color: "var(--signal)" }}>{importFehler}</p>}
          {importErfolg && <p style={{ fontSize: 12, color: "var(--text-leise)" }}>{importErfolg}</p>}

          {speichert && (
            <p style={{ fontSize: 11, color: "var(--text-aus)", marginTop: 10 }}>speichert…</p>
          )}
        </>
      )}

      {fehler && <p style={{ color: "var(--signal)", fontSize: 13 }}>{fehler}</p>}
    </Fenster>

    {/* Popup im Popup ("Pop-ups die zu Pop-ups führen") — Fenster.tsx trägt
        das über ein Portal, unabhängig von der Verschachtelungstiefe hier. */}
    <PruefungPopup
      key={pruefStamp}
      offen={sweepErgebnis !== null && sweepErgebnis.ergebnisse.length > 0}
      campaignId={campaignId}
      ergebnisse={sweepErgebnis?.ergebnisse ?? []}
      onSchliessen={() => setSweepErgebnis(null)}
    />
    <SweepVerknuepfungPopup
      key={verknuepfStamp}
      offen={verknuepfErgebnis !== null}
      campaignId={campaignId}
      ergebnisse={verknuepfErgebnis?.ergebnisse ?? []}
      onSchliessen={() => setVerknuepfErgebnis(null)}
    />
    </>
  );
}
