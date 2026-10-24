import { useEffect, useRef, useState } from "react";
import { ReactSketchCanvas, type ReactSketchCanvasRef } from "react-sketch-canvas";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";

/**
 * Einfacher Skizzenblock fürs Charakterportrait. Kein Malprogramm —
 * Strich, Radierer, Undo. Das PNG geht über denselben Upload wie
 * Datei, Kamera und KI. Ebenen und Pinsel sitzen im Zeichentisch (Klecks).
 */

const FARBEN: { name: string; wert: string }[] = [
  { name: "Schwarz", wert: "#1a1a1a" },
  { name: "Grau", wert: "#8a8a8a" },
  { name: "Weiss", wert: "#f4f4f4" },
  { name: "Haut hell", wert: "#e0b090" },
  { name: "Haut", wert: "#c68642" },
  { name: "Haut dunkel", wert: "#6b3e26" },
  { name: "Braun", wert: "#5c3317" },
  { name: "Rot", wert: "#c0392b" },
  { name: "Orange", wert: "#e67e22" },
  { name: "Gelb", wert: "#d4a017" },
  { name: "Grün", wert: "#1e8449" },
  { name: "Blau", wert: "#2471a3" },
  { name: "Violett", wert: "#7d3c98" },
  { name: "Rosa", wert: "#d63384" },
];

const STIFTE = [3, 8, 16, 32];

export function ZeichenblockPopup({
  offen,
  bildUrl,
  onSchliessen,
  onUebernehmen,
}: {
  offen: boolean;
  /** Liegt schon ein Portrait, liegt es unter der Skizze. */
  bildUrl?: string | null;
  onSchliessen: () => void;
  onUebernehmen: (blob: Blob) => Promise<void>;
}) {
  const leinwand = useRef<ReactSketchCanvasRef>(null);
  const [farbe, setFarbe] = useState(FARBEN[0].wert);
  const [stift, setStift] = useState(STIFTE[1]);
  const [radierer, setRadierer] = useState(false);
  const [loeschenFrage, setLoeschenFrage] = useState(false);
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    leinwand.current?.eraseMode(radierer);
  }, [radierer, offen]);

  async function speichern() {
    if (!leinwand.current) return;
    setSpeichert(true);
    setFehler(null);
    try {
      const dataUrl = await leinwand.current.exportImage("png");
      const blob = await (await fetch(dataUrl)).blob();
      await onUebernehmen(blob);
      onSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="Zeichnen"
      kennung="zeichenblock"
      breit
      unterzeile="Skizze — wird als Portrait gespeichert"
      onSchliessen={onSchliessen}
    >
      <div className="port-werkzeug">
        <div className="port-farben" role="group" aria-label="Farbe">
          {FARBEN.map((f) => (
            <button
              key={f.wert}
              type="button"
              className="port-farbe"
              title={f.name}
              aria-label={f.name}
              aria-pressed={!radierer && farbe === f.wert}
              disabled={speichert}
              style={{ background: f.wert }}
              onClick={() => {
                setFarbe(f.wert);
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
                disabled={speichert}
                onClick={() => setStift(s)}
                title={`${s} px`}
              >
                <span style={{ width: Math.min(s, 18), height: Math.min(s, 18) }} />
              </button>
            ))}
          </div>
          <button
            type="button"
            className="port-mini"
            aria-pressed={radierer}
            disabled={speichert}
            onClick={() => setRadierer((r) => !r)}
          >
            {radierer ? "Radierer" : "Stift"}
          </button>
          <button type="button" className="port-mini" disabled={speichert} onClick={() => leinwand.current?.undo()}>
            Undo
          </button>
          <button type="button" className="port-mini" disabled={speichert} onClick={() => leinwand.current?.redo()}>
            Redo
          </button>
          <button type="button" className="port-mini" disabled={speichert} onClick={() => setLoeschenFrage(true)}>
            Leeren
          </button>
        </div>
      </div>

      <div className="port-leinwand">
        {offen && (
          <ReactSketchCanvas
            ref={leinwand}
            width="100%"
            height="100%"
            strokeColor={farbe}
            strokeWidth={stift}
            eraserWidth={Math.max(stift * 2, 12)}
            canvasColor="#f7f4ef"
            backgroundImage={bildUrl || ""}
            exportWithBackgroundImage={Boolean(bildUrl)}
            preserveBackgroundImageAspectRatio="xMidYMid meet"
            touchAction="none"
            style={{ border: "none", borderRadius: 0 }}
          />
        )}
      </div>

      {fehler && <p className="port-fehler">{fehler}</p>}

      <button type="button" className="port-btn-primaer" disabled={speichert} onClick={speichern}>
        {speichert ? "Speichert…" : "Als Portrait speichern"}
      </button>

      {loeschenFrage && (
        <Bestaetigung
          titel="Skizze leeren"
          text="Bist du sicher? Die Striche auf der Skizze werden entfernt. Das bisherige Portrait bleibt, bis du speicherst."
          jaText="Leeren"
          neinText="Abbrechen"
          onJa={() => {
            leinwand.current?.clearCanvas();
            setLoeschenFrage(false);
          }}
          onNein={() => setLoeschenFrage(false)}
        />
      )}
    </Fenster>
  );
}
