/**
 * Ergebnis-Popup des Auto-Verknüpfungs-Sweeps über ALLE Wiki-Seiten.
 *
 * Analog zu `wiki/PruefungPopup.tsx` (Rechtschreib-Sweep): eine Gruppe pro
 * Seite mit Treffern, jeder Vorschlag einzeln bestätigt über dieselben
 * Anwenden-Routen wie im einzelnen Wiki-Editor (`AutoVerknuepfungPopup.tsx`).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import {
  verknuepfungAnwenden,
  verknuepfungBeziehungAnwenden,
  type BeziehungsVorschlag,
  type VerknuepfungsVorschlag,
} from "../ki/api";
import type { SweepVerknuepfungSeite } from "./api";
import "../ki/ki.css";
import "../wiki/wiki.css";

const TYP_ICON: Record<string, string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  Fraktion: "⬡",
};

function verweisSchluessel(seitenId: string, v: VerknuepfungsVorschlag) {
  return `${seitenId}:${v.zitat}:${v.typ}:${v.name}`;
}

function beziehungSchluessel(seitenId: string, v: BeziehungsVorschlag) {
  return `${seitenId}:${v.typ1}:${v.name1}:${v.beziehungstyp}:${v.typ2}:${v.name2}`;
}

export function SweepVerknuepfungPopup({
  offen,
  campaignId,
  ergebnisse,
  onSchliessen,
}: {
  offen: boolean;
  campaignId: string;
  ergebnisse: SweepVerknuepfungSeite[];
  onSchliessen: () => void;
}) {
  const [seiten, setSeiten] = useState<SweepVerknuepfungSeite[]>(ergebnisse);
  const [angewandt, setAngewandt] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());

  if (!offen) return null;

  async function verweisAnwenden(seitenId: string, v: VerknuepfungsVorschlag) {
    const key = verweisSchluessel(seitenId, v);
    setAngewandt(key);
    setFehler(null);
    try {
      const ergebnis = await verknuepfungAnwenden(campaignId, seitenId, v);
      if (!ergebnis.ersetzt) {
        setFehler(`„${v.zitat}" wurde im Text nicht mehr gefunden — schon geändert?`);
        return;
      }
      setErledigt((alt) => new Set(alt).add(key));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verknüpfen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  async function beziehungAnwenden(seitenId: string, v: BeziehungsVorschlag) {
    const key = beziehungSchluessel(seitenId, v);
    setAngewandt(key);
    setFehler(null);
    try {
      await verknuepfungBeziehungAnwenden(campaignId, seitenId, v);
      setErledigt((alt) => new Set(alt).add(key));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Beziehung anlegen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  function schliessen() {
    setSeiten(ergebnisse);
    setErledigt(new Set());
    setFehler(null);
    onSchliessen();
  }

  const gesamt = seiten.reduce((n, s) => n + s.verweise.length + s.beziehungen.length, 0);
  const offenGesamt = seiten.reduce((n, s) => {
    const v = s.verweise.filter((x) => !erledigt.has(verweisSchluessel(s.seitenId, x))).length;
    const b = s.beziehungen.filter((x) => !erledigt.has(beziehungSchluessel(s.seitenId, x))).length;
    return n + v + b;
  }, 0);

  return (
    <Fenster
      offen={offen}
      titel="⧉✨ Auto-Verknüpfung — Sweep"
      unterzeile={gesamt === 0 ? "Keine Vorschläge." : `${offenGesamt} von ${gesamt} noch offen`}
      kennung="wiki-verknuepfung-sweep"
      onSchliessen={schliessen}
    >
      {fehler && (
        <p style={{ color: "var(--signal)", fontSize: 12, margin: 0 }}>
          {fehler} <button type="button" className="wk-werkzeug" onClick={() => setFehler(null)}>ok</button>
        </p>
      )}

      {gesamt === 0 && (
        <p style={{ color: "var(--text-leise)", fontSize: 13 }}>
          Keine Erwähnungen oder Beziehungen in den durchsuchten Seiten gefunden.
        </p>
      )}

      {seiten.map((seite) => {
        const offeneVerweise = seite.verweise.filter((v) => !erledigt.has(verweisSchluessel(seite.seitenId, v)));
        const offeneBeziehungen = seite.beziehungen.filter((v) => !erledigt.has(beziehungSchluessel(seite.seitenId, v)));
        if (offeneVerweise.length === 0 && offeneBeziehungen.length === 0) return null;

        return (
          <div key={seite.seitenId} className="wk-pr-seite">
            <h4 className="wk-pr-seitentitel">{seite.titel}</h4>

            {offeneVerweise.length > 0 && (
              <div className="av-gruppe">
                <h4 className="av-gruppentitel">Erwähnungen</h4>
                {offeneVerweise.map((v) => {
                  const key = verweisSchluessel(seite.seitenId, v);
                  const neu = v.zielId === null;
                  return (
                    <div key={key} className="av-vorschlag">
                      <div className="av-vorschlag-kopf">
                        <span className="av-icon">{TYP_ICON[v.typ] ?? "❔"}</span>
                        <span className="av-name">{v.name}</span>
                        <span className="av-typ">{v.typ}</span>
                        {neu && <span className="av-neu">neu</span>}
                      </div>
                      <div className="av-zitat">„{v.zitat}"</div>
                      <button
                        type="button"
                        className="ki-btn-primaer"
                        disabled={angewandt === key}
                        onClick={() => verweisAnwenden(seite.seitenId, v)}
                      >
                        {angewandt === key ? "…" : neu ? "+ Entwurf anlegen & verknüpfen" : "✓ Verknüpfen"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {offeneBeziehungen.length > 0 && (
              <div className="av-gruppe">
                <h4 className="av-gruppentitel">Beziehungen</h4>
                {offeneBeziehungen.map((v) => {
                  const key = beziehungSchluessel(seite.seitenId, v);
                  const neu1 = v.zielId1 === null;
                  const neu2 = v.zielId2 === null;
                  return (
                    <div key={key} className="av-vorschlag">
                      <div className="av-vorschlag-kopf">
                        <span className="av-icon">{TYP_ICON[v.typ1] ?? "❔"}</span>
                        <span className="av-name">
                          {v.name1}
                          {neu1 && <span className="av-neu">neu</span>}
                        </span>
                        <span className="av-beziehungspfeil">— {v.beziehungstyp} →</span>
                        <span className="av-icon">{TYP_ICON[v.typ2] ?? "❔"}</span>
                        <span className="av-name">
                          {v.name2}
                          {neu2 && <span className="av-neu">neu</span>}
                        </span>
                      </div>
                      {v.beschreibung && <div className="av-zitat">{v.beschreibung}</div>}
                      <button
                        type="button"
                        className="ki-btn-primaer"
                        disabled={angewandt === key}
                        onClick={() => beziehungAnwenden(seite.seitenId, v)}
                      >
                        {angewandt === key
                          ? "…"
                          : neu1 || neu2
                            ? "+ Entwurf/Beziehung anlegen"
                            : "✓ Beziehung anlegen"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </Fenster>
  );
}
