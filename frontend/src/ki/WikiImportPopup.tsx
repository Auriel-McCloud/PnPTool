/**
 * ⇪✨ Wiki-Import-Popup — SL lädt ein Word/PDF-Dokument hoch, die KI teilt
 * es automatisch anhand seiner Struktur (Überschriften/Kapitel) in eine
 * oder mehrere Wiki-Seiten-Entwürfe auf (istEntwurf=true, Eltern-Kind-
 * Hierarchie wo sinnvoll) und verknüpft sie automatisch (bestehende
 * Auto-Verknüpfungs-Logik läuft pro Seite mit).
 *
 * Ablauf:
 * 1. Datei wählen (.docx oder .pdf).
 * 2. „Importieren" schickt sie an die Route, KI parst + gliedert + legt
 *    Entwürfe an — kann je nach Dokumentlänge einen Moment dauern.
 * 3. Ergebnis-Liste der neu erzeugten Entwürfe mit Link zur Ideenschmiede
 *    (dort läuft die bestehende Prüfung/Freigabe — kein neuer Mechanismus).
 *
 * Entwürfe sind NICHT sofort live: Marks Vorgabe, SL muss jeden Entwurf in
 * der Ideenschmiede noch einzeln prüfen und übernehmen.
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { wikiImportieren, type ImportierteSeite } from "./api";
import "./ki.css";

export function WikiImportPopup({
  offen,
  campaignId,
  onSchliessen,
  onZurIdeenschmiede,
}: {
  offen: boolean;
  campaignId: string;
  onSchliessen: () => void;
  /** Springt in die Ideenschmiede zur Prüfung der neuen Entwürfe. */
  onZurIdeenschmiede: () => void;
}) {
  const [datei, setDatei] = useState<File | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnis, setErgebnis] = useState<ImportierteSeite[] | null>(null);

  function zuruecksetzen() {
    setDatei(null);
    setFehler(null);
    setErgebnis(null);
  }

  function schliessenUndZuruecksetzen() {
    zuruecksetzen();
    onSchliessen();
  }

  async function importieren() {
    if (!datei) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const antwort = await wikiImportieren(campaignId, datei);
      setErgebnis(antwort.seiten);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Import fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  // Baum flach anzeigen, Unterseiten eingerückt — reicht für eine
  // Ergebnis-Liste, ein echter Baum wäre hier Überbau.
  const oberste = (ergebnis ?? []).filter((s) => !s.parentId);
  const kinderVon = (id: string) => (ergebnis ?? []).filter((s) => s.parentId === id);

  function seitenZeile(s: ImportierteSeite, tiefe: number) {
    return (
      <div key={s.id} className="av-vorschlag" style={{ marginLeft: tiefe * 16 }}>
        <div className="av-vorschlag-kopf">
          <span className="av-icon">📄</span>
          <span className="av-name">{s.titel}</span>
          {s.verknuepfungen > 0 && (
            <span className="av-typ" title="Anzahl automatisch angewandter Auto-Verknüpfungen">
              ⧉ {s.verknuepfungen}
            </span>
          )}
        </div>
        {kinderVon(s.id).map((k) => seitenZeile(k, tiefe + 1))}
      </div>
    );
  }

  return (
    <Fenster
      offen={offen}
      titel="⇪✨ Wiki-Import"
      unterzeile="Dokument hochladen — KI teilt es automatisch in Wiki-Seiten-Entwürfe auf"
      kennung="wiki-import"
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {ergebnis === null && (
          <>
            <p className="ki-vorschau-hinweis">
              Word (.docx) oder PDF (.pdf) hochladen. Die KI erkennt Kapitel/Überschriften und
              legt daraus eine oder mehrere Wiki-Seiten als Entwurf an — inklusive automatischer
              Verknüpfung erwähnter Personen, Orte, Ereignisse und Fraktionen. Nichts wird sofort
              veröffentlicht: jeder Entwurf landet in der Ideenschmiede zur Prüfung.
            </p>

            <label className="ki-label">
              Dokument
              <input
                type="file"
                className="ki-input"
                accept=".docx,.pdf"
                disabled={laeuft}
                onChange={(e) => setDatei(e.target.files?.[0] ?? null)}
              />
            </label>

            {fehler && <p className="ki-fehler">{fehler}</p>}

            <div className="ki-aktionen">
              <button
                type="button"
                className="ki-btn-primaer"
                disabled={laeuft || !datei}
                onClick={importieren}
              >
                {laeuft ? "Importiert…" : "⇪ Importieren"}
              </button>
              <button type="button" className="ki-btn-sekundaer" disabled={laeuft} onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {ergebnis !== null && (
          <>
            <p className="ki-vorschau-hinweis">
              {ergebnis.length === 0
                ? "Die KI konnte aus diesem Dokument keine Wiki-Seite ableiten."
                : `${ergebnis.length} Entwurf${ergebnis.length === 1 ? "" : "e"} angelegt — zur Prüfung in der Ideenschmiede:`}
            </p>

            {oberste.map((s) => seitenZeile(s, 0))}

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" onClick={onZurIdeenschmiede}>
                🔧 Zur Ideenschmiede
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
