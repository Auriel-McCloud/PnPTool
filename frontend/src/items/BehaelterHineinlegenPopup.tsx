import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { itemsApi, type GegenstandMitBesitzer } from "./api";
import "./wegwerfen.css";

/**
 * Vom Behälter aus nach einem Gegenstand suchen und ihn hineinlegen
 * (31.10.2026, Mark: der Workflow war bisher umgekehrt — man musste am
 * Gegenstand ein Ziel suchen, siehe `ablageziele` in CharacterSheetPanel.
 * "ich gehe auf den Behälter, und dann kann ich nach einem Gegenstand
 * suchen den ich dann hineinlege").
 *
 * Lädt dieselbe campaignweite Liste wie die Gegenstände-Übersicht
 * (`itemsApi.listAlle`) und filtert clientseitig — kein eigener Such-
 * Endpunkt nötig. Vorlage vs. Einzelstück entscheidet ausschließlich der
 * Server (`POST .../hineinlegen`), hier nur eine Anzeige-Auskunft, welche
 * der beiden Varianten gleich passiert.
 */
export function BehaelterHineinlegenPopup({
  behaelterId,
  behaelterName,
  campaignId,
  offen,
  onSchliessen,
  onHineingelegt,
}: {
  behaelterId: string;
  behaelterName: string;
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Nach jedem erfolgreichen Hineinlegen — die Übersicht dahinter lädt neu. */
  onHineingelegt: () => void;
}) {
  const [alle, setAlle] = useState<GegenstandMitBesitzer[]>([]);
  const [suche, setSuche] = useState("");
  const [ladend, setLadend] = useState(true);
  const [laeuft, setLaeuft] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [erledigt, setErledigt] = useState<string | null>(null);

  async function laden() {
    setLadend(true);
    try {
      setAlle(await itemsApi.listAlle(campaignId));
    } catch {
      setFehler("Gegenstände konnten nicht geladen werden");
    } finally {
      setLadend(false);
    }
  }

  useEffect(() => {
    if (!offen) return;
    setSuche("");
    setFehler(null);
    setErledigt(null);
    void laden();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId]);

  const treffer = useMemo(() => {
    const s = suche.trim().toLowerCase();
    return alle
      .filter((g) => g.id !== behaelterId)
      // Schon drin — kein Grund, es nochmal anzubieten.
      .filter((g) => g.ablageZielId !== behaelterId)
      .filter(
        (g) =>
          !s ||
          g.name.toLowerCase().includes(s) ||
          g.typ.toLowerCase().includes(s) ||
          (g.ownerName ?? "").toLowerCase().includes(s),
      )
      .slice(0, 40);
  }, [alle, suche, behaelterId]);

  async function hineinlegen(g: GegenstandMitBesitzer) {
    setLaeuft(g.id);
    setFehler(null);
    setErledigt(null);
    try {
      await itemsApi.hineinlegen(campaignId, behaelterId, g.id);
      setErledigt(g.istVorlage ? `Kopie von „${g.name}“ liegt jetzt drin.` : `„${g.name}“ liegt jetzt drin.`);
      await laden();
      onHineingelegt();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Hineinlegen fehlgeschlagen");
    } finally {
      setLaeuft(null);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel={`In ${behaelterName} hineinlegen`}
      kennung={`hineinlegen:${behaelterId}`}
      onSchliessen={onSchliessen}
    >
      <p className="ww-hinweis">
        Eine Vorlage wird dabei automatisch als Kopie hineingelegt — die Vorlage selbst bleibt bestehen.
        Ein Einzelstück wandert direkt um, egal wem es gerade gehört.
      </p>
      <input
        type="search"
        placeholder="Suchen — Name, Typ oder Besitzer"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
        autoFocus
        style={{ width: "100%", marginBottom: 10 }}
      />
      {ladend && <p className="mu-leer">Lade Gegenstände…</p>}
      {erledigt && <p className="ww-beruhigung">{erledigt}</p>}
      {fehler && (
        <p className="ww-hinweis" style={{ color: "var(--signal)" }}>
          {fehler}
        </p>
      )}
      {!ladend && treffer.length === 0 && <p className="mu-leer">Nichts gefunden.</p>}
      {treffer.length > 0 && (
        <div className="mu-liste" style={{ maxHeight: "45vh", overflowY: "auto" }}>
          {treffer.map((g) => (
            <div key={g.id} className="mu-zeile">
              <span className="mu-name">
                <strong>{g.name}</strong>
                <span className="mu-herkunft">
                  {g.typ}
                  {g.istVorlage ? " · Vorlage" : g.ownerName ? ` · ${g.ownerName}` : " · ohne Besitzer"}
                </span>
              </span>
              <button type="button" disabled={laeuft === g.id} onClick={() => hineinlegen(g)}>
                {laeuft === g.id ? "…" : g.istVorlage ? "Kopie hineinlegen" : "Hineinlegen"}
              </button>
            </div>
          ))}
        </div>
      )}
    </Fenster>
  );
}
