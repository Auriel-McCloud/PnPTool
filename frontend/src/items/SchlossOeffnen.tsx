import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { itemsApi, type Gegenstand } from "./api";
import { ApiError } from "../api/client";
import { KonstruktIcon } from "../traits/ErstellungsAssistent";
import "../traits/assistent.css";

/** Muss mit TASTEN in backend/app/items/schloss.py übereinstimmen. */
const TASTEN_ANZAHL = 10;

/** Unicode-Runenblock (Elder Futhark) — keine eigene Schriftart nötig,
 * Windows bringt mit "Segoe UI Historic"/"Segoe UI Symbol" eine Darstellung
 * dafür mit (siehe schloss-taste-Regel in gegenstaende.css). */
const RUNEN_POOL = [
  "ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ",
  "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ", "ᛏ", "ᛒ", "ᛖ", "ᛗ",
  "ᛚ", "ᛜ", "ᛟ", "ᛞ",
];

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/** 10 Runen für genau dieses Schloss — zufällig gemischt, aber pro
 * Gegenstand immer dieselben (sonst müsste man sich bei jeder Runde neu
 * einprägen, welche Taste welches Zeichen trägt). */
function runenFuer(itemId: string): string[] {
  const pool = [...RUNEN_POOL];
  const ausgewaehlt: string[] = [];
  let same = hashString(itemId) || 1;
  for (let i = 0; i < TASTEN_ANZAHL && pool.length > 0; i++) {
    same = (same * 1103515245 + 12345) & 0x7fffffff;
    const idx = same % pool.length;
    ausgewaehlt.push(pool[idx]);
    pool.splice(idx, 1);
  }
  return ausgewaehlt;
}

/** Radius des Tastenkreises in Pixeln — siehe .schloss-kreis in gegenstaende.css. */
const KREIS_RADIUS = 104;

/**
 * Öffnen einer verschlossenen Kiste. Passwort (mit Rätsel drauf), Schlüssel
 * oder die Tastenfolge. Die Folge prüft der Server — hier leuchten nur die
 * Tasten, die er für diese Runde rausgibt.
 *
 * Das Tasten-Spiel zeigt keinen Fehlertext: ein Fehlversuch lässt stattdessen
 * das ganze Fenster rot aufblitzen und beginnt stumm von vorn (Mark,
 * 31.10.2026 — "einfach von vorne", kein "Daneben"-Text).
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
  const [blitzt, setBlitzt] = useState(false);

  const tasten = useMemo(() => runenFuer(item.id), [item.id]);

  function blitzen() {
    setBlitzt(false);
    // Eigener Tick, damit die CSS-Animation auch bei zwei Fehlversuchen
    // kurz hintereinander jedes Mal neu von vorn beginnt.
    window.setTimeout(() => setBlitzt(true), 10);
  }

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
    setHinweis(null);
    if (stand.falsch) blitzen();
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
          {!darfTippen && <p className="schloss-spiel-hinweis">Schau zu.</p>}
          <div className="schloss-kreis">
            <div className="schloss-kreis-mitte" aria-hidden="true">
              <KonstruktIcon />
            </div>
            {tasten.map((zeichen, index) => {
              const winkel = (Math.PI * 2 * index) / TASTEN_ANZAHL - Math.PI / 2;
              const x = Math.cos(winkel) * KREIS_RADIUS;
              const y = Math.sin(winkel) * KREIS_RADIUS;
              return (
                <button
                  key={index}
                  type="button"
                  className="schloss-taste"
                  style={{ left: `calc(50% + ${x}px)`, top: `calc(50% + ${y}px)` }}
                  data-an={leuchtet === index}
                  disabled={!darfTippen}
                  onClick={() => void taste(index)}
                >
                  {zeichen}
                </button>
              );
            })}
          </div>
        </div>
      )}
      {hinweis && <p style={{ color: "var(--nein)", margin: "12px 0 0" }}>{hinweis}</p>}
    </>
  );

  if (ohneFenster) return offen ? inhalt : null;
  return (
    <Fenster offen={offen} titel={titel} unterzeile={item.name} kennung={`schloss:${item.id}`} blitzt={blitzt} onSchliessen={onSchliessen}>
      {inhalt}
    </Fenster>
  );
}

function warten(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
