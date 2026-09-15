import { useEffect, useRef, useState } from "react";
import type { Campaign } from "./useCampaign";
import "./kampagnenauswahl.css";

/**
 * Auswahl der aktiven Kampagne — ein Dropdown in der Kopfleiste.
 *
 * Zeigt immer, welche Kampagne gerade aktiv ist; wer mehrere Kampagnen leitet,
 * wechselt hier. Ganz unten „+ Neue Kampagne" öffnet das Anlege-Fenster.
 */
export function KampagnenAuswahl({
  kampagnen,
  aktiveId,
  onWaehlen,
  onNeu,
}: {
  kampagnen: Campaign[];
  aktiveId: string | null;
  onWaehlen: (id: string) => void;
  onNeu: () => void;
}) {
  const [offen, setOffen] = useState(false);
  const wurzel = useRef<HTMLDivElement>(null);

  // Klick außerhalb schließt das Menü wieder.
  useEffect(() => {
    if (!offen) return;
    function schliessen(e: MouseEvent) {
      if (wurzel.current && !wurzel.current.contains(e.target as Node)) {
        setOffen(false);
      }
    }
    document.addEventListener("mousedown", schliessen);
    return () => document.removeEventListener("mousedown", schliessen);
  }, [offen]);

  const aktive = kampagnen.find((k) => k.id === aktiveId);

  return (
    <div className="ka-auswahl" ref={wurzel}>
      <button
        type="button"
        className="ka-knopf"
        onClick={() => setOffen((o) => !o)}
        title="Kampagne wechseln"
        aria-haspopup="listbox"
        aria-expanded={offen}
      >
        <span className="ka-symbol" aria-hidden="true">
          ▤
        </span>
        <span className="ka-name">{aktive?.name ?? "Keine Kampagne"}</span>
        <span className="ka-pfeil" aria-hidden="true">
          ▾
        </span>
      </button>

      {offen && (
        <div className="ka-menue" role="listbox">
          {kampagnen.map((k) => (
            <button
              key={k.id}
              type="button"
              role="option"
              aria-selected={k.id === aktiveId}
              className="ka-eintrag"
              data-aktiv={k.id === aktiveId ? "true" : undefined}
              onClick={() => {
                onWaehlen(k.id);
                setOffen(false);
              }}
            >
              {k.name}
            </button>
          ))}
          <div className="ka-trenner" />
          <button
            type="button"
            className="ka-eintrag ka-neu"
            onClick={() => {
              setOffen(false);
              onNeu();
            }}
          >
            + Neue Kampagne
          </button>
        </div>
      )}
    </div>
  );
}
