/**
 * ⧉✨ Auto-Verknüpfung für ein freies Beschreibungs-/Notizen-Feld ohne
 * Wiki-Seitenbezug — der Knopf neben "🔍 Prüfen" im generischen
 * `RichTextEditor` (Personen/Orte/Events/Fraktionen/Gegenstände/Begleiter,
 * inkl. Ideenschmiede-Entwürfe dieser Typen).
 *
 * Anders als `AutoVerknuepfungPopup.tsx` (Wiki-Seite) gibt es hier keinen
 * Ort, an dem ein Verweis-Chip eingefügt werden könnte — Verweise erscheinen
 * deshalb nur informativ (ohne Aktions-Knopf). Nur **Beziehungen** sind
 * wirklich anwendbar: eine echte VERBINDUNG-Kante zwischen den zwei
 * Entitäten, unabhängig vom aktuell bearbeiteten Feld.
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import {
  objektTextVerknuepfung,
  verknuepfungBeziehungAnwenden,
  type BeziehungsVorschlag,
  type VerknuepfungsVorschlag,
} from "./api";
import "./ki.css";

const TYP_ICON: Record<string, string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  Fraktion: "⬡",
};

function beziehungSchluessel(v: BeziehungsVorschlag) {
  return `${v.typ1}:${v.name1}:${v.beziehungstyp}:${v.typ2}:${v.name2}`;
}

export function ObjektVerknuepfungPopup({
  offen,
  campaignId,
  text,
  onSchliessen,
}: {
  offen: boolean;
  campaignId: string;
  /** Aktueller Fließtext des Feldes (`editor.getText()` des Aufrufers). */
  text: string;
  onSchliessen: () => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [angewandt, setAngewandt] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [verweise, setVerweise] = useState<VerknuepfungsVorschlag[] | null>(null);
  const [beziehungen, setBeziehungen] = useState<BeziehungsVorschlag[]>([]);
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());

  if (!offen) return null;

  async function holen() {
    setLaedt(true);
    setFehler(null);
    try {
      const antwort = await objektTextVerknuepfung(campaignId, text);
      setVerweise(antwort.verweise);
      setBeziehungen(antwort.beziehungen);
      setErledigt(new Set());
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Erkennung fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  async function beziehungAnwenden(v: BeziehungsVorschlag) {
    const key = beziehungSchluessel(v);
    setAngewandt(key);
    setFehler(null);
    try {
      // seitenId ist bei dieser Route nur Teil des URL-Pfads (die Kante hängt
      // an den zwei Entitäten, nicht an einer Wiki-Seite) — Platzhalter reicht.
      await verknuepfungBeziehungAnwenden(campaignId, "objekt-text", v);
      setErledigt((alt) => new Set(alt).add(key));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Beziehung anlegen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  function schliessenUndZuruecksetzen() {
    setVerweise(null);
    setBeziehungen([]);
    setErledigt(new Set());
    setFehler(null);
    onSchliessen();
  }

  const offeneBeziehungen = beziehungen.filter((v) => !erledigt.has(beziehungSchluessel(v)));

  return (
    <Fenster
      offen={offen}
      titel="⧉✨ Auto-Verknüpfung"
      unterzeile="Erkennt erwähnte Personen/Orte/Events/Fraktionen und ihre Beziehungen"
      kennung="objekt-verknuepfung"
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {verweise === null && (
          <>
            <p className="ki-vorschau-hinweis">
              Durchsucht diesen Text nach Personen, Orten, Ereignissen und Fraktionen sowie
              konkreten Beziehungen zwischen ihnen (z.B. „arbeitet für"). Ohne Wiki-Seite lässt
              sich nur eine erkannte Beziehung wirklich anlegen — Erwähnungen werden nur zur
              Information angezeigt.
            </p>
            {fehler && <p className="ki-fehler">{fehler}</p>}
            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" disabled={laedt} onClick={holen}>
                {laedt ? "Erkennt…" : "✨ Vorschläge holen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {verweise !== null && (
          <>
            {fehler && <p className="ki-fehler">{fehler}</p>}

            {verweise.length === 0 && offeneBeziehungen.length === 0 && (
              <p className="ki-vorschau-hinweis">Keine Erwähnungen oder Beziehungen gefunden.</p>
            )}

            {verweise.length > 0 && (
              <div className="av-gruppe">
                <h4 className="av-gruppentitel">Erwähnungen (nur informativ)</h4>
                {verweise.map((v) => (
                  <div key={`${v.zitat}:${v.typ}:${v.name}`} className="av-vorschlag">
                    <div className="av-vorschlag-kopf">
                      <span className="av-icon">{TYP_ICON[v.typ] ?? "❔"}</span>
                      <span className="av-name">{v.name}</span>
                      <span className="av-typ">{v.typ}</span>
                      {v.zielId === null && <span className="av-neu">neu</span>}
                    </div>
                    <div className="av-zitat">„{v.zitat}"</div>
                  </div>
                ))}
              </div>
            )}

            {offeneBeziehungen.length > 0 && (
              <div className="av-gruppe">
                <h4 className="av-gruppentitel">Beziehungen</h4>
                {offeneBeziehungen.map((v) => {
                  const key = beziehungSchluessel(v);
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
                        onClick={() => beziehungAnwenden(v)}
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

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-sekundaer" disabled={laedt} onClick={holen}>
                {laedt ? "Erkennt…" : "↺ Erneut prüfen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Schließen
              </button>
            </div>
          </>
        )}
      </div>
    </Fenster>
  );
}
