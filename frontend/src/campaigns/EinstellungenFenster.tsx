import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { einstellungenApi, type Einstellungen } from "./einstellungen";

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
  offen,
  onSchliessen,
}: {
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
}) {
  const [werte, setWerte] = useState<Einstellungen | null>(null);
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    einstellungenApi
      .lesen(campaignId)
      .then(setWerte)
      .catch((e) => setFehler(e instanceof Error ? e.message : "Konnte nicht laden"));
  }, [campaignId, offen]);

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

          {speichert && (
            <p style={{ fontSize: 11, color: "var(--text-aus)", marginTop: 10 }}>speichert…</p>
          )}
        </>
      )}

      {fehler && <p style={{ color: "var(--signal)", fontSize: 13 }}>{fehler}</p>}
    </Fenster>
  );
}
