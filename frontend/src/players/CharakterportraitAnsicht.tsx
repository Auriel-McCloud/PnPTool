import { useRef, useState } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { KiBildPopup } from "../ki/KiBildPopup";
import { playersApi, type SpielerMe } from "./api";
import "./portrait.css";

/**
 * Charakterportrait als eigener Bereich in der Spieler-Hülle (Mark,
 * 22.09.2026: "damit im Charakterblatt mehr Platz ist" — das Blatt wächst
 * je nach Chartyp mit zusätzlichen Skills/Werten, ein Bild-Verwaltungsknopf
 * dort hätte nur Platz weggenommen). Ursprünglich als Popup über dem Blatt
 * geplant, auf Marks Wunsch zu einem eigenen Burger-Menü-Punkt gemacht.
 *
 * MVP-Scope (mit Mark geklärt): Hochladen, Foto per Kamera, KI-generiertes
 * Bild. Ein Zeichentool ist in CLAUDE.md unter Punkt 11 als offen vermerkt,
 * bewusst nicht Teil dieser Fassung.
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
  const [loeschenFrage, setLoeschenFrage] = useState(false);
  const [kiOffen, setKiOffen] = useState(false);
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

  async function loeschen() {
    setLoeschenFrage(false);
    setLaedt(true);
    setFehler(null);
    try {
      const frisch = await playersApi.meinBildEntfernen();
      onGeaendert(frisch);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
    } finally {
      setLaedt(false);
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
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => setKiOffen(true)}>
            ✨ KI-Bild generieren
          </button>
          {ich.personBildUrl && (
            <button
              type="button"
              className="port-btn-loeschen"
              disabled={laedt}
              onClick={() => setLoeschenFrage(true)}
            >
              ✕ Entfernen
            </button>
          )}
        </div>

        <p className="port-hinweis">Ein Zeichentool ist noch nicht verfügbar.</p>
      </div>

      {loeschenFrage && (
        <Bestaetigung
          titel="Portrait entfernen"
          text="Bist du sicher? Dein Charakterportrait wird entfernt."
          jaText="Entfernen"
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenFrage(false)}
        />
      )}

      <KiBildPopup
        offen={kiOffen}
        objektTyp="Person"
        objektName={ich.personName ?? "Charakter"}
        onSchliessen={() => setKiOffen(false)}
        onPromptVorschlagen={() => playersApi.meinBildKiPrompt()}
        onGenerieren={(provider, prompt) => playersApi.meinBildKiGenerieren(provider, prompt)}
        onUebernehmen={async (blob) => {
          const datei = new File([blob], "portrait-ki.png", { type: blob.type || "image/png" });
          const frisch = await playersApi.meinBildHochladen(datei);
          onGeaendert(frisch);
        }}
      />
    </div>
  );
}
