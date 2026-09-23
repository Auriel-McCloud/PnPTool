/**
 * ✨ KI-Bild-Popup — der "KI-Bild generieren"-Knopf neben dem normalen
 * Datei-Upload an Charakterportrait, Gegenstands-Bild und Ort-Bild.
 *
 * Ablauf (Marks Entscheidung, siehe Aufgabenbeschreibung):
 * 1. Beim Öffnen schlägt die KI (Gemini Text) automatisch einen Bild-Prompt
 *    vor, basierend auf Name + vorhandener Beschreibung der Entität.
 * 2. Der Prompt steht editierbar im Textfeld — der Nutzer kann ihn vor dem
 *    Generieren anpassen.
 * 3. Provider wählen (lokal Fooocus / cloud Gemini), dann "Generieren".
 * 4. Vorschau des generierten Bildes; erst "✓ Übernehmen" speichert es
 *    tatsächlich — über denselben Upload-Weg wie ein manuell hochgeladenes
 *    Bild (der Aufrufer übergibt eine `hochladen`-Funktion, die dieselbe
 *    Route wie den bestehenden Datei-Upload trifft).
 *
 * Generisch für alle drei Entitätstypen (Person/Ort/Gegenstand) gebaut,
 * damit es nur eine Komponente statt drei Kopien gibt — der Aufrufer bringt
 * nur objektTyp/objektName/bisherigeBeschreibung und die Upload-Funktion mit.
 */
import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import "./ki.css";

export function KiBildPopup({
  offen,
  objektTyp,
  objektName,
  onSchliessen,
  onPromptVorschlagen,
  onGenerieren,
  onUebernehmen,
}: {
  offen: boolean;
  objektTyp: string;
  objektName: string;
  onSchliessen: () => void;
  /** Liefert den Prompt-Vorschlag (Schritt 1). */
  onPromptVorschlagen: () => Promise<string>;
  /** Generiert das Bild (Schritt 2) — liefert den Blob zur Vorschau. */
  onGenerieren: (provider: "lokal" | "cloud", prompt: string) => Promise<Blob>;
  /** Übernimmt den Blob als Datei über die bestehende Upload-Route. */
  onUebernehmen: (blob: Blob) => Promise<void>;
}) {
  const [provider, setProvider] = useState<"lokal" | "cloud">("cloud");
  const [prompt, setPrompt] = useState("");
  const [ladePrompt, setLadePrompt] = useState(false);
  const [generiert, setGeneriert] = useState(false);
  const [uebernimmt, setUebernimmt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [vorschauUrl, setVorschauUrl] = useState<string | null>(null);
  const [vorschauBlob, setVorschauBlob] = useState<Blob | null>(null);

  // Beim Öffnen automatisch einen Prompt vorschlagen (Marks Wunsch: "schlägt
  // die KI ... automatisch einen Bild-Prompt vor"). Nur einmal pro Öffnen,
  // nicht bei jedem Tastendruck im Textfeld.
  useEffect(() => {
    if (!offen) return;
    let abgebrochen = false;
    setLadePrompt(true);
    setFehler(null);
    onPromptVorschlagen()
      .then((p) => {
        if (!abgebrochen) setPrompt(p);
      })
      .catch((e) => {
        if (!abgebrochen) setFehler(e instanceof Error ? e.message : "Prompt-Vorschlag fehlgeschlagen");
      })
      .finally(() => {
        if (!abgebrochen) setLadePrompt(false);
      });
    return () => {
      abgebrochen = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen]);

  function zuruecksetzen() {
    setPrompt("");
    setFehler(null);
    setGeneriert(false);
    if (vorschauUrl) URL.revokeObjectURL(vorschauUrl);
    setVorschauUrl(null);
    setVorschauBlob(null);
  }

  function schliessenUndZuruecksetzen() {
    zuruecksetzen();
    onSchliessen();
  }

  async function generieren() {
    if (!prompt.trim()) return;
    setGeneriert(false);
    setFehler(null);
    try {
      const blob = await onGenerieren(provider, prompt.trim());
      if (vorschauUrl) URL.revokeObjectURL(vorschauUrl);
      setVorschauBlob(blob);
      setVorschauUrl(URL.createObjectURL(blob));
      setGeneriert(true);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Generieren fehlgeschlagen");
    }
  }

  async function uebernehmen() {
    if (!vorschauBlob) return;
    setUebernimmt(true);
    setFehler(null);
    try {
      await onUebernehmen(vorschauBlob);
      schliessenUndZuruecksetzen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Übernehmen fehlgeschlagen");
    } finally {
      setUebernimmt(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="✨ KI-Bild generieren"
      unterzeile={`${objektTyp} „${objektName}"`}
      kennung={`ki-bild:${objektTyp}:${objektName}`}
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {!generiert && (
          <>
            <label className="ki-label">
              Generator
              <div className="ki-bild-provider">
                <button
                  type="button"
                  className={provider === "cloud" ? "ki-btn-primaer" : "ki-btn-sekundaer"}
                  onClick={() => setProvider("cloud")}
                >
                  ☁ Cloud (Gemini)
                </button>
                <button
                  type="button"
                  className={provider === "lokal" ? "ki-btn-primaer" : "ki-btn-sekundaer"}
                  onClick={() => setProvider("lokal")}
                >
                  ▣ Lokal (Fooocus)
                </button>
              </div>
            </label>

            <label className="ki-label">
              Bild-Prompt {ladePrompt && "— wird vorgeschlagen…"}
              <textarea
                className="ki-input"
                rows={5}
                style={{ resize: "vertical", minHeight: 100, width: "100%" }}
                placeholder="Beschreibung des gewünschten Bildes…"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={ladePrompt}
              />
            </label>

            {fehler && <p className="ki-fehler">{fehler}</p>}

            <div className="ki-aktionen">
              <button
                type="button"
                className="ki-btn-primaer"
                disabled={ladePrompt || !prompt.trim()}
                onClick={generieren}
              >
                ✨ Generieren
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {generiert && vorschauUrl && (
          <>
            <p className="ki-vorschau-hinweis">Vorschau — erst „Übernehmen" speichert das Bild:</p>
            <img src={vorschauUrl} alt="" className="ki-bild-vorschau" />

            {fehler && <p className="ki-fehler">{fehler}</p>}

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" disabled={uebernimmt} onClick={uebernehmen}>
                {uebernimmt ? "Übernimmt…" : "✓ Übernehmen"}
              </button>
              <button
                type="button"
                className="ki-btn-sekundaer"
                disabled={uebernimmt}
                onClick={() => {
                  setGeneriert(false);
                  if (vorschauUrl) URL.revokeObjectURL(vorschauUrl);
                  setVorschauUrl(null);
                  setVorschauBlob(null);
                }}
              >
                ↺ Neu versuchen
              </button>
              <button type="button" className="ki-btn-sekundaer" disabled={uebernimmt} onClick={schliessenUndZuruecksetzen}>
                Verwerfen
              </button>
            </div>
          </>
        )}
      </div>
    </Fenster>
  );
}
