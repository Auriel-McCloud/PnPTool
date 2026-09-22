import { useRef, useState } from "react";
import { playersApi, type SpielerMe } from "./api";
import "./portrait.css";

/**
 * Charakterportrait als eigener Bereich in der Spieler-Hülle (Mark,
 * 22.09.2026: "damit im Charakterblatt mehr Platz ist" — das Blatt wächst
 * je nach Chartyp mit zusätzlichen Skills/Werten, ein Bild-Verwaltungsknopf
 * dort hätte nur Platz weggenommen). Ursprünglich als Popup über dem Blatt
 * geplant, auf Marks Wunsch zu einem eigenen Burger-Menü-Punkt gemacht.
 *
 * MVP-Scope (mit Mark geklärt): nur Hochladen + Foto per Kamera. Ein
 * Zeichentool und KI-Bildgenerierung sind in CLAUDE.md unter Punkt 11 als
 * offen vermerkt, bewusst nicht Teil dieser ersten Fassung.
 */
export function CharakterportraitAnsicht({
  ich,
  onGeaendert,
}: {
  ich: SpielerMe;
  /** Neuer SpielerMe-Stand nach erfolgreichem Upload. */
  onGeaendert: (frisch: SpielerMe) => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const dateiRef = useRef<HTMLInputElement>(null);
  const kameraRef = useRef<HTMLInputElement>(null);

  async function hochladen(datei: File | undefined) {
    if (!datei) return;
    setLaedt(true);
    setFehler(null);
    try {
      const frisch = await playersApi.meinBildHochladen(datei);
      onGeaendert(frisch);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    } finally {
      setLaedt(false);
      if (dateiRef.current) dateiRef.current.value = "";
      if (kameraRef.current) kameraRef.current.value = "";
    }
  }

  return (
    <div className="port-seite">
      <h3 className="gg-abschnitt">
        <span>◒ Portrait</span>
      </h3>

      <div className="port-popup">
        {ich.personBildUrl && (
          <img src={ich.personBildUrl} alt={ich.personName ?? "Portrait"} className="port-vorschau" />
        )}

        {!ich.personBildUrl && <p className="port-leer">Noch kein Bild gesetzt.</p>}

        <input
          ref={dateiRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          style={{ display: "none" }}
          onChange={(e) => hochladen(e.target.files?.[0])}
        />
        {/* capture="environment" öffnet am Handy direkt die Kamera statt der
            Dateiauswahl — auf dem Desktop ohne Kamera fällt der Browser
            automatisch auf die normale Dateiauswahl zurück. */}
        <input
          ref={kameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={(e) => hochladen(e.target.files?.[0])}
        />

        {fehler && <p className="port-fehler">{fehler}</p>}

        <div className="port-aktionen">
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => dateiRef.current?.click()}>
            {laedt ? "Lädt…" : "📁 Bild hochladen"}
          </button>
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => kameraRef.current?.click()}>
            {laedt ? "Lädt…" : "📷 Foto machen"}
          </button>
        </div>

        <p className="port-hinweis">Zeichentool und KI-generiertes Bild sind noch nicht verfügbar.</p>
      </div>
    </div>
  );
}
