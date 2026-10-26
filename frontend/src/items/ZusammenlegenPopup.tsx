import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { itemsApi, type Gegenstand } from "./api";
import "./wegwerfen.css";

/**
 * Zusammenlegen-Popup (26.10.2026): mehrere gleichwertige Gegenstände zu
 * einem Stapel zusammenführen — Mark hatte 3 einzelne Maschinenteile statt
 * eines Stapels mit Anzahl 3.
 *
 * Kandidaten lädt das Popup selbst beim Öffnen (`itemsApi.stapelkandidaten`)
 * — das Backend prüft dieselbe Gleichheit (`stapel_gleich`), mit der die
 * Submit-Route auch wirklich zusammenlegt, das Popup muss sie nicht selbst
 * nachbauen. Mehrfachauswahl nach dem `VorlagenAuswahlPopup`-Muster: Klick
 * toggelt, ein Knopf schickt die ganze Auswahl auf einmal ab.
 *
 * Nur SL — dieselbe Stelle, von der aus auch Zuweisen/Vorlagen-Art bedient
 * werden (`GegenstandRow`, Optionen anzeigen). Die Quellen landen danach im
 * Mülleimer, nicht gelöscht — reversibel, falls die Auswahl falsch war.
 */
export function ZusammenlegenPopup({
  item,
  offen,
  campaignId,
  onZusammengelegt,
  onAbbrechen,
}: {
  item: Gegenstand;
  offen: boolean;
  campaignId: string;
  onZusammengelegt: () => void;
  onAbbrechen: () => void;
}) {
  const [kandidaten, setKandidaten] = useState<Gegenstand[]>([]);
  const [ausgewaehlt, setAusgewaehlt] = useState<Set<string>>(new Set());
  const [ladend, setLadend] = useState(true);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    setLadend(true);
    setFehler(null);
    setAusgewaehlt(new Set());
    itemsApi
      .stapelkandidaten(campaignId, item.id)
      .then(setKandidaten)
      .catch(() => setFehler("Kandidaten konnten nicht geladen werden"))
      .finally(() => setLadend(false));
  }, [offen, campaignId, item.id]);

  function toggeln(id: string) {
    setAusgewaehlt((alt) => {
      const neu = new Set(alt);
      if (neu.has(id)) neu.delete(id);
      else neu.add(id);
      return neu;
    });
  }

  const eigeneMenge = item.hatMenge ? item.menge : 1;
  const neueMenge =
    eigeneMenge + kandidaten.filter((k) => ausgewaehlt.has(k.id)).reduce((s, k) => s + (k.hatMenge ? k.menge : 1), 0);

  async function zusammenlegen() {
    if (ausgewaehlt.size === 0) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await itemsApi.zusammenlegen(campaignId, item.id, [...ausgewaehlt]);
      onZusammengelegt();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Zusammenlegen fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster offen={offen} titel={`${item.name} zusammenlegen`} kennung={`zusammenlegen:${item.id}`} onSchliessen={onAbbrechen}>
      <p className="ww-hinweis">
        Wähle, welche anderen Stücke von {item.name} in dieses hier einfließen sollen.
      </p>
      <p className="ww-beruhigung">
        <strong>Gelöscht wird nichts.</strong> Die ausgewählten Stücke landen im Mülleimer, dieses hier bekommt die
        Summe der Mengen.
      </p>

      {ladend && <p style={{ color: "var(--text-leise)" }}>Lade mögliche Stücke…</p>}
      {!ladend && item.einzigartig && (
        <p className="mu-leer">
          Dieses Stück ist als <strong>einzigartig</strong> markiert — einzigartige Stücke lassen sich nicht
          stapeln. Erst im Umbauen-Formular „Einzigartig" ausschalten, falls es davon mehrere geben soll.
        </p>
      )}
      {!ladend && !item.einzigartig && kandidaten.length === 0 && (
        <p className="mu-leer">Kein anderes Stück passt — gleicher Besitzer und mechanisch identisch nötig.</p>
      )}

      {kandidaten.length > 0 && (
        <div className="mu-liste" style={{ maxHeight: "40vh", overflowY: "auto" }}>
          {kandidaten.map((k) => (
            <label key={k.id} className="mu-zeile" style={{ cursor: "pointer" }}>
              <input type="checkbox" checked={ausgewaehlt.has(k.id)} onChange={() => toggeln(k.id)} />
              <span className="mu-name">
                <strong>{k.name}</strong>
                <span className="mu-herkunft">{k.hatMenge ? `×${k.menge}` : "Einzelstück"}</span>
              </span>
            </label>
          ))}
        </div>
      )}

      {ausgewaehlt.size > 0 && (
        <p className="ww-hinweis" style={{ marginTop: 10 }}>
          Neue Menge danach: <strong>{neueMenge}</strong>
        </p>
      )}

      {fehler && (
        <p className="ww-hinweis" style={{ color: "var(--nein)" }}>
          {fehler}
        </p>
      )}

      <div className="ww-knoepfe">
        <button type="button" className="ww-behalten" disabled={laeuft || ausgewaehlt.size === 0} onClick={zusammenlegen}>
          {laeuft ? "…" : `${ausgewaehlt.size || ""} zusammenlegen`.trim()}
        </button>
        <button type="button" onClick={onAbbrechen} disabled={laeuft}>
          Abbrechen
        </button>
      </div>
    </Fenster>
  );
}
