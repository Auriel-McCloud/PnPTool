import { useEffect, useRef, useState } from "react";
import { ReactSketchCanvas, type CanvasPath, type ReactSketchCanvasRef } from "react-sketch-canvas";
import { Fenster } from "../shell/Fenster";
import { zeichnungenApi, verbindeZeichnungLive, type Pfad, type ZeichnungLeitung, type Zeichnung } from "./api";
// Teilt sich die Werkzeugleisten-Klassen (.port-*) mit dem Portrait-
// Skizzenblock — direkt importiert statt uns auf eine zufällige Lade-
// Reihenfolge über CharakterportraitAnsicht zu verlassen (CSS-Imports sind
// idempotent, Vite dedupliziert das Stylesheet).
import "../players/portrait.css";

const FARBEN = ["#1a1a1a", "#c0392b", "#e67e22", "#d4a017", "#1e8449", "#2471a3", "#7d3c98", "#f4f4f4"];
const STIFTE = [3, 6, 12];

/**
 * Die eigentliche Zeichenfläche: live mitzeichenbar, mehrere Betrachter
 * gleichzeitig. Jeder abgeschlossene Strich (bzw. Undo/Redo/Leeren) geht als
 * KOMPLETTER Gesamtstand über die Leitung — kein inkrementelles Protokoll,
 * siehe backend/app/zeichnungen/verteiler.py.
 *
 * Programmgesteuerte Übernahmen eines fremden Standes (resetCanvas+loadPaths)
 * lösen denselben onChange-Callback aus wie eigene Striche. Eine kurze
 * Sperrfrist (`sperreBis`) unterscheidet "das war ich selbst, gerade
 * reingekommen" von "das war der Nutzer" — siehe `fernAenderung` unten.
 * Faellt in diese Sperrfrist zufaellig ein echter eigener Strich, wird er
 * erst beim naechsten Strich mitgeschickt (kein Datenverlust, nur verzoegert).
 */
export function WhiteboardPopup({
  offen,
  zeichnung,
  campaignId,
  darfZeichnen,
  istGm,
  onSchliessen,
  onEinstellungenOeffnen,
}: {
  offen: boolean;
  zeichnung: Zeichnung | null;
  campaignId: string;
  darfZeichnen: boolean;
  istGm: boolean;
  onSchliessen: () => void;
  onEinstellungenOeffnen: () => void;
}) {
  const leinwand = useRef<ReactSketchCanvasRef>(null);
  const leitung = useRef<ZeichnungLeitung | null>(null);
  const sperreBis = useRef(0);
  const [farbe, setFarbe] = useState(FARBEN[0]);
  const [stift, setStift] = useState(STIFTE[1]);
  const [radierer, setRadierer] = useState(false);
  const [verbunden, setVerbunden] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    leinwand.current?.eraseMode(radierer);
  }, [radierer, offen]);

  // Übernimmt einen Gesamtstand (vom initialen Laden oder von der Leitung),
  // ohne ihn gleich wieder zurückzuschicken.
  function standUebernehmen(pfade: Pfad[]) {
    sperreBis.current = Date.now() + 150;
    leinwand.current?.resetCanvas();
    if (pfade.length) leinwand.current?.loadPaths(pfade as unknown as CanvasPath[]);
  }

  function lokaleAenderung(updatedPaths: CanvasPath[]) {
    if (Date.now() < sperreBis.current) return;
    leitung.current?.senden(updatedPaths as unknown as Pfad[]);
  }

  // Beim Öffnen: aktuellen Stand frisch laden (nicht auf die Liste
  // verlassen, die könnte veraltet sein) und die Live-Leitung aufbauen.
  useEffect(() => {
    if (!offen || !zeichnung) return;
    let abgebrochen = false;
    setFehler(null);

    zeichnungenApi
      .holen(campaignId, zeichnung.id)
      .then((frisch) => {
        if (!abgebrochen) standUebernehmen(frisch.pfade);
      })
      .catch(() => {
        if (!abgebrochen) setFehler("Board konnte nicht geladen werden");
      });

    leitung.current = verbindeZeichnungLive(
      campaignId,
      zeichnung.id,
      (n) => {
        if (n.typ === "pfade") standUebernehmen(n.daten.pfade);
      },
      setVerbunden,
    );

    return () => {
      abgebrochen = true;
      leitung.current?.trennen();
      leitung.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, zeichnung?.id, campaignId]);

  if (!zeichnung) return null;

  return (
    <Fenster
      offen={offen}
      titel={zeichnung.name}
      kennung={`whiteboard-${zeichnung.id}`}
      breit
      ton="var(--bereich-whiteboard)"
      unterzeile={
        darfZeichnen
          ? verbunden
            ? "Live — jeder Strich geht sofort an alle"
            : "Verbindung wird aufgebaut…"
          : "Nur Zusehen — diese Freigabe hat die Spielleitung nicht erteilt"
      }
      onSchliessen={onSchliessen}
    >
      {darfZeichnen && (
        <div className="port-werkzeug">
          <div className="port-farben" role="group" aria-label="Farbe">
            {FARBEN.map((f) => (
              <button
                key={f}
                type="button"
                className="port-farbe"
                aria-pressed={!radierer && farbe === f}
                style={{ background: f }}
                onClick={() => {
                  setFarbe(f);
                  setRadierer(false);
                }}
              />
            ))}
          </div>
          <div className="port-werkzeug-zeile">
            <div className="port-stifte" role="group" aria-label="Strichstärke">
              {STIFTE.map((s) => (
                <button
                  key={s}
                  type="button"
                  className="port-stift"
                  aria-pressed={stift === s}
                  onClick={() => setStift(s)}
                  title={`${s} px`}
                >
                  <span style={{ width: Math.min(s, 18), height: Math.min(s, 18) }} />
                </button>
              ))}
            </div>
            <button type="button" className="port-mini" aria-pressed={radierer} onClick={() => setRadierer((r) => !r)}>
              {radierer ? "Radierer" : "Stift"}
            </button>
            <button type="button" className="port-mini" onClick={() => leinwand.current?.undo()}>
              Undo
            </button>
            <button type="button" className="port-mini" onClick={() => leinwand.current?.redo()}>
              Redo
            </button>
            {istGm && (
              <button type="button" className="port-mini" onClick={onEinstellungenOeffnen}>
                ⚙ Einstellungen
              </button>
            )}
          </div>
        </div>
      )}

      {!darfZeichnen && istGm && (
        <div className="port-werkzeug">
          <button type="button" className="port-mini" onClick={onEinstellungenOeffnen}>
            ⚙ Einstellungen
          </button>
        </div>
      )}

      <div className="port-leinwand zb-leinwand">
        {offen && (
          <ReactSketchCanvas
            ref={leinwand}
            width="100%"
            height="100%"
            strokeColor={farbe}
            strokeWidth={stift}
            eraserWidth={Math.max(stift * 2, 12)}
            canvasColor="#f7f4ef"
            backgroundImage={zeichnung.bildUrl || ""}
            exportWithBackgroundImage={Boolean(zeichnung.bildUrl)}
            preserveBackgroundImageAspectRatio="xMidYMid meet"
            touchAction="none"
            readOnly={!darfZeichnen}
            onChange={lokaleAenderung}
            style={{ border: "none", borderRadius: 0 }}
          />
        )}
      </div>

      {fehler && <p className="port-fehler">{fehler}</p>}
    </Fenster>
  );
}
