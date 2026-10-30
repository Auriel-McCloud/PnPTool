import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { itemsApi, type Gegenstand } from "./api";
import { ApiError } from "../api/client";

const TASTEN = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ"];

/**
 * Öffnen einer verschlossenen Kiste. Passwort (mit Rätsel drauf), Schlüssel
 * oder die Tastenfolge. Die Folge prüft der Server — hier leuchten nur die
 * Tasten, die er für diese Runde rausgibt.
 */
export function SchlossOeffnen({
  item,
  campaignId,
  offen,
  onSchliessen,
  onGeoeffnet,
  ohneFenster = false,
}: {
  item: Gegenstand;
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
  onGeoeffnet: () => void;
  /** Schon in einem Fachfenster — dann kein zweites Fenster drumherum. */
  ohneFenster?: boolean;
}) {
  const [passwort, setPasswort] = useState("");
  const [hinweis, setHinweis] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [anzeige, setAnzeige] = useState<number[]>([]);
  const [leuchtet, setLeuchtet] = useState<number | null>(null);
  const [eingabe, setEingabe] = useState<number[]>([]);
  const [darfTippen, setDarfTippen] = useState(false);

  async function mitPasswort() {
    setLaeuft(true);
    setHinweis(null);
    try {
      await itemsApi.oeffnen(campaignId, item.id, passwort);
      onGeoeffnet();
      onSchliessen();
    } catch (e) {
      setHinweis(e instanceof ApiError ? e.message : "Geht nicht auf.");
    } finally {
      setLaeuft(false);
    }
  }

  async function mitSchluessel() {
    setLaeuft(true);
    setHinweis(null);
    try {
      await itemsApi.oeffnen(campaignId, item.id);
      onGeoeffnet();
      onSchliessen();
    } catch (e) {
      setHinweis(e instanceof ApiError ? e.message : "Geht nicht auf.");
    } finally {
      setLaeuft(false);
    }
  }

  async function rundeHolen(folge?: number[]) {
    const stand = await itemsApi.schlossSpiel(campaignId, item.id, folge);
    if (stand.geschafft) {
      onGeoeffnet();
      onSchliessen();
      return;
    }
    setAnzeige(stand.anzeige);
    setEingabe([]);
    setDarfTippen(false);
    setHinweis(stand.falsch ? "Daneben. Von vorn." : null);
    await abspielen(stand.anzeige);
    setDarfTippen(true);
  }

  async function abspielen(folge: number[]) {
    for (const taste of folge) {
      setLeuchtet(taste);
      await warten(420);
      setLeuchtet(null);
      await warten(180);
    }
  }

  useEffect(() => {
    if (!offen || item.schlossArt !== "spiel") return;
    let weg = false;
    setHinweis(null);
    rundeHolen().catch((e) => {
      if (!weg) setHinweis(e instanceof ApiError ? e.message : "Das Schloss antwortet nicht.");
    });
    return () => {
      weg = true;
    };
    // Nur beim Öffnen starten. rundeHolen liest den aktuellen Gegenstand.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, item.id]);

  async function taste(index: number) {
    if (!darfTippen || laeuft) return;
    const bisher = [...eingabe, index];
    setEingabe(bisher);
    setLeuchtet(index);
    window.setTimeout(() => setLeuchtet(null), 160);
    if (bisher.length < anzeige.length) return;
    setDarfTippen(false);
    setLaeuft(true);
    try {
      await rundeHolen(bisher);
    } catch (e) {
      setHinweis(e instanceof ApiError ? e.message : "Das Schloss antwortet nicht.");
      setDarfTippen(true);
    } finally {
      setLaeuft(false);
    }
  }

  const titel = item.schlossArt === "spiel" ? "Tasten-Schloss" : item.schlossArt === "schluessel" ? "Schlüssel-Schloss" : "Schloss";

  const inhalt = (
    <>
      {item.schlossArt === "passwort" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void mitPasswort();
          }}
          style={{ display: "flex", flexDirection: "column", gap: 12 }}
        >
          {item.schlossRaetsel && <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{item.schlossRaetsel}</p>}
          <input
            className="cl-roehre"
            value={passwort}
            onChange={(e) => setPasswort(e.target.value)}
            autoComplete="off"
            placeholder={item.schlossRaetsel ? "Lösung" : "Passwort"}
            aria-label="Lösung"
          />
          <button type="submit" disabled={laeuft || !passwort.trim()}>
            Öffnen
          </button>
        </form>
      )}
      {item.schlossArt === "schluessel" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <p style={{ margin: 0, color: "var(--text-leise)" }}>Verschlossen. Dafür brauchst du den passenden Schlüssel.</p>
          <button type="button" onClick={() => void mitSchluessel()} disabled={laeuft}>
            Mit Schlüssel öffnen
          </button>
        </div>
      )}
      {item.schlossArt === "spiel" && (
        <div className="schloss-spiel">
          <p className="schloss-spiel-hinweis">{darfTippen ? "Nachmachen." : "Schau zu."}</p>
          <div className="schloss-tasten">
            {TASTEN.map((zeichen, index) => (
              <button
                key={zeichen}
                type="button"
                className="schloss-taste"
                data-an={leuchtet === index}
                disabled={!darfTippen}
                onClick={() => void taste(index)}
              >
                {zeichen}
              </button>
            ))}
          </div>
        </div>
      )}
      {hinweis && <p style={{ color: "var(--neon-rot, #e55)", margin: "12px 0 0" }}>{hinweis}</p>}
    </>
  );

  if (ohneFenster) return offen ? inhalt : null;
  return (
    <Fenster offen={offen} titel={titel} unterzeile={item.name} kennung={`schloss:${item.id}`} onSchliessen={onSchliessen}>
      {inhalt}
    </Fenster>
  );
}

function warten(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
