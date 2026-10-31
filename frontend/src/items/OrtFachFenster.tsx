import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { GegenstandKachel } from "./GegenstandKachel";
import { itemsApi, type Ablage, type GegenstandMitBesitzer } from "./api";
import "./gegenstaende.css";

/**
 * Was am aktuellen Aufenthaltsort der Party (oder im eigenen Versteck) liegt —
 * campaignweit, nicht nur die eigenen Sachen (31.10.2026, Mark: Rigger legt
 * etwas am gemeinsamen Ort ab, der IT-Sicherheitsmann steht auch dort,
 * "der müsste es jetzt natürlich aufheben können").
 *
 * Anders als `Fachfenster` (ausschließlich eigener Besitz, siehe dort) zeigt
 * dieses Fenster gemischten Besitz: eigene Sachen bekommen die volle
 * `GegenstandKachel` mit Umlegen/Wegwerfen/Weitergeben, fremde nur eine
 * schreibgeschützte Kachel plus den Aufheben-Knopf (gleiche Position/Optik
 * wie `.gg-zurueckgeben` in der Drohnen-Ausrüstung).
 */
export function OrtFachFenster({
  ortName,
  items,
  offen,
  onSchliessen,
  campaignId,
  eigenePersonId,
  onUmlegen,
  onWegwerfen,
  onWeitergeben,
  onZusammengelegt,
  onAufgehoben,
}: {
  ortName: string;
  /** Bereits auf diesen Ort gefiltert (ablageZielId), beliebiger Besitzer. */
  items: GegenstandMitBesitzer[];
  offen: boolean;
  onSchliessen: () => void;
  campaignId: string;
  eigenePersonId: string;
  onUmlegen: (item: GegenstandMitBesitzer, ablage: Ablage, zielId?: string | null) => Promise<void> | void;
  /** Fehlt hier bewusst in der Spielerischen Ansicht genau wie bei den
   * anderen eigenen Fächern dort — Wegwerfen bietet SpielerAnsicht.tsx
   * aktuell an keiner Stelle an. */
  onWegwerfen?: (item: GegenstandMitBesitzer) => Promise<void> | void;
  onWeitergeben: (item: GegenstandMitBesitzer, empfaengerPersonId: string) => Promise<void> | void;
  onZusammengelegt: () => void;
  /** Nach erfolgreichem Aufheben — die Sachen-Liste lädt neu. */
  onAufgehoben: () => void;
}) {
  const [laeuft, setLaeuft] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  async function aufheben(item: GegenstandMitBesitzer) {
    setLaeuft(item.id);
    setFehler(null);
    try {
      await itemsApi.aufheben(campaignId, item.id);
      onAufgehoben();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Aufheben fehlgeschlagen");
    } finally {
      setLaeuft(null);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel={`📍 ${ortName}`}
      unterzeile={`${items.length} ${items.length === 1 ? "Gegenstand" : "Gegenstände"}`}
      kennung={`ort-fach:${ortName}`}
      onSchliessen={onSchliessen}
    >
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      {items.length === 0 ? (
        <p style={{ color: "var(--text-leise)", margin: 0 }}>Hier liegt nichts.</p>
      ) : (
        <div className="gg-fachraster">
          {items.map((g) => {
            const eigenes = g.ownerId === eigenePersonId;
            return (
              <div key={g.id} style={{ position: "relative" }}>
                <GegenstandKachel
                  item={g}
                  campaignId={campaignId}
                  eigenePersonId={eigenePersonId}
                  onUmlegen={eigenes ? (ablage, zielId) => onUmlegen(g, ablage, zielId) : undefined}
                  onWegwerfen={eigenes && onWegwerfen ? () => onWegwerfen(g) : undefined}
                  onWeitergeben={eigenes ? (empfaengerId) => onWeitergeben(g, empfaengerId) : undefined}
                  onZusammengelegt={eigenes ? onZusammengelegt : undefined}
                />
                {!eigenes && (
                  <button
                    type="button"
                    className="gg-zurueckgeben"
                    title={g.ownerName ? `Gehört ${g.ownerName} — an dich nehmen` : "An dich nehmen"}
                    disabled={laeuft === g.id}
                    onClick={() => aufheben(g)}
                  >
                    {laeuft === g.id ? "…" : "📥 Aufheben"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Fenster>
  );
}
