import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";

/**
 * Titel-Abfrage beim Anlegen einer Seite.
 *
 * Ersetzt window.prompt: das sieht nicht nur fremd aus, sondern ist auf
 * Tablets und in eingebetteten Ansichten unzuverlässig — manche Browser
 * unterdrücken es ganz. Dann liesse sich keine Seite mehr anlegen.
 */
export function TitelFenster({
  offen,
  titel,
  vorschlag = "",
  onBestaetigen,
  onSchliessen,
}: {
  offen: boolean;
  titel: string;
  vorschlag?: string;
  onBestaetigen: (wert: string) => void;
  onSchliessen: () => void;
}) {
  const [wert, setWert] = useState(vorschlag);

  useEffect(() => {
    if (offen) setWert(vorschlag);
  }, [offen, vorschlag]);

  function bestaetigen() {
    const sauber = wert.trim();
    if (!sauber) return;
    onBestaetigen(sauber);
    onSchliessen();
  }

  return (
    <Fenster offen={offen} titel={titel} kennung="wiki-titel" onSchliessen={onSchliessen}>
      <input
        autoFocus
        value={wert}
        placeholder="z. B. Kapitel 1 — Die Ankunft"
        onChange={(e) => setWert(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") bestaetigen();
        }}
      />
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
        <button type="button" onClick={onSchliessen}>
          Abbrechen
        </button>
        <button
          type="button"
          onClick={bestaetigen}
          disabled={!wert.trim()}
          style={{ color: "var(--neon)", borderColor: "var(--neon)" }}
        >
          Anlegen
        </button>
      </div>
    </Fenster>
  );
}
