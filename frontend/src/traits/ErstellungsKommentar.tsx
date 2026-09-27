import { useState } from "react";
import { bogenApi } from "./bogenApi";
import "./assistent.css";

/**
 * KI-Abschlusskommentar zum fertigen Fertigkeiten-Build (27.09.2026,
 * Marks Idee: "Dungeon Crawler Carl"-artiger Kommentar). Erscheint dort,
 * wo das Fertigkeiten-Fenster geschlossen wurde, direkt über dem
 * "Weiter"-Fußzeilenbereich der Erstellung.
 *
 * Anders als ErstellungsAssistent.tsx (kostenlos, rein regelbasiert, läuft
 * automatisch) ist das hier EIN expliziter Knopf mit echtem KI-Aufruf —
 * Mark ist kostenbewusst beim LLM-Verbrauch, deshalb nie automatisch.
 * Nutzt dieselbe Figur/Optik wie der Live-Assistent (Wiedererkennung),
 * aber eigener Zustand: unbetätigt → lädt → Text oder Fehler.
 */
export function ErstellungsKommentar({
  campaignId,
  werte,
  weg,
  magieFlavor,
}: {
  campaignId: string;
  werte: Record<string, number>;
  weg: string;
  magieFlavor: string;
}) {
  const [zustand, setZustand] = useState<"start" | "laedt" | "fertig" | "fehler">("start");
  const [achievement, setAchievement] = useState("");
  const [text, setText] = useState("");
  const magisch = weg === "MAGIER" || weg === "HAERETIKER";

  async function anfordern() {
    setZustand("laedt");
    try {
      const { achievement, kommentar } = await bogenApi.kommentar(campaignId, werte, weg, magieFlavor);
      setAchievement(achievement);
      setText(kommentar);
      setZustand("fertig");
    } catch (e) {
      setText(e instanceof Error ? e.message : "Der Kommentar ist fehlgeschlagen.");
      setZustand("fehler");
    }
  }

  if (zustand === "start") {
    return (
      <button type="button" className="ak-knopf" onClick={anfordern}>
        🎙️ Wie seh ich aus?
      </button>
    );
  }

  return (
    <div className={`as-box${magisch ? " as-box-magisch" : " as-box-chrom"}`} role="status">
      <div className="as-figur" aria-hidden="true">
        {magisch ? <SigillIcon /> : <KonstruktIcon />}
      </div>
      <div className="as-blase">
        {zustand === "laedt" && <p className="as-text">Moment … die Statistik wird durchgesagt.</p>}
        {zustand === "fertig" && (
          <>
            {achievement && (
              <p className="ak-achievement">
                <span className="ak-achievement-label">New Achievement</span>
                <span className="ak-achievement-titel">{achievement}</span>
              </p>
            )}
            <p className="as-text">{text}</p>
          </>
        )}
        {zustand === "fehler" && (
          <>
            <p className="as-text">{text}</p>
            <button type="button" className="as-weiter" onClick={anfordern}>
              Nochmal versuchen
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/** Dieselben Icons wie ErstellungsAssistent.tsx — Wiedererkennung, eine
 * Figur je Weg, egal ob Live-Hinweis oder Abschlusskommentar. */
function KonstruktIcon() {
  return (
    <svg viewBox="0 0 48 48" width="36" height="36" className="as-svg">
      <g className="as-hyper-links">
        <line x1="24" y1="6" x2="24" y2="15" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="42" y1="24" x2="33" y2="24" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="24" y1="42" x2="24" y2="33" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="6" y1="24" x2="15" y2="24" stroke="currentColor" strokeWidth="1" opacity="0.6" />
      </g>
      <polygon points="24,6 42,24 24,42 6,24" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-aussen" />
      <polygon points="24,15 33,24 24,33 15,24" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-innen" />
      <circle cx="24" cy="24" r="2.5" fill="currentColor" className="as-puls" />
    </svg>
  );
}

function SigillIcon() {
  return (
    <svg viewBox="0 0 48 48" width="36" height="36" className="as-svg">
      <g className="as-hyper-links">
        <line x1="24" y1="4" x2="24" y2="13" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="41" y1="34" x2="33.5" y2="29.5" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="7" y1="34" x2="14.5" y2="29.5" stroke="currentColor" strokeWidth="1" opacity="0.6" />
      </g>
      <polygon points="24,4 41,34 7,34" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-aussen" />
      <polygon points="24,13 33.5,29.5 14.5,29.5" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-innen" />
      <circle cx="24" cy="26" r="2.5" fill="currentColor" className="as-puls" />
    </svg>
  );
}
