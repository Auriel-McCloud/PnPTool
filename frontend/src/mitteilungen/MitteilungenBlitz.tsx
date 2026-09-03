import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { useMitteilungen } from "./MitteilungenKontext";
import "./mitteilungen.css";

function zeit(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? ""
    : d.toLocaleTimeString("de-AT", { hour: "2-digit", minute: "2-digit" });
}

/**
 * Blitz-Symbol in der oberen Werkzeugleiste (docs/ui-konzept.md).
 *
 * Zeigt ungelesene Ansagen an und öffnet den Verlauf — damit man nachlesen
 * kann, was während einer Pause kam.
 */
export function MitteilungenBlitz({ personId }: { personId: string | null }) {
  const { mitteilungen, ungelesen, verbunden, allesGelesen } = useMitteilungen();
  const [offen, setOffen] = useState(false);

  return (
    <>
      <button
        type="button"
        className="cl-werkzeug mt-blitz"
        data-ungelesen={ungelesen > 0 ? "true" : undefined}
        onClick={() => setOffen(true)}
        title={
          ungelesen > 0
            ? `${ungelesen} ungelesene Ansage${ungelesen === 1 ? "" : "n"} der Spielleitung`
            : "Ansagen der Spielleitung"
        }
        aria-label="Ansagen der Spielleitung"
      >
        ⚡
        {ungelesen > 0 && <span className="mt-zahl">{ungelesen > 9 ? "9+" : ungelesen}</span>}
      </button>

      <Fenster
        offen={offen}
        titel="Ansagen"
        unterzeile={
          <span className="mt-leitung" data-verbunden={verbunden}>
            {verbunden ? "● Live verbunden" : "○ getrennt — versucht neu"}
          </span>
        }
        kennung="mitteilungen-verlauf"
        ton="var(--warn)"
        onSchliessen={() => setOffen(false)}
      >
        {mitteilungen.length === 0 && (
          <p style={{ color: "var(--text-leise)" }}>Noch keine Ansagen.</p>
        )}

        <div className="mt-liste">
          {mitteilungen.map((m) => {
            const ungelesenHier = personId ? !m.gelesenVon.includes(personId) : false;
            return (
              <div key={m.id} className="mt-eintrag" data-ungelesen={ungelesenHier ? "true" : undefined}>
                <div className="mt-eintrag-kopf">
                  <span className="mt-eintrag-zeit">{zeit(m.erstelltAm)}</span>
                  <span className="mt-eintrag-ziel" data-gerichtet={!m.anAlle ? "true" : undefined}>
                    {m.anAlle ? "an alle" : "nur an dich"}
                  </span>
                </div>
                {m.art === "BILD" && m.bildUrl ? (
                  <img src={m.bildUrl} alt={m.inhalt || "Bild"} style={{ maxWidth: "100%", borderRadius: 4 }} />
                ) : null}
                {m.inhalt && <div className="mt-eintrag-text">{m.inhalt}</div>}
              </div>
            );
          })}
        </div>

        {personId && ungelesen > 0 && (
          <button type="button" onClick={allesGelesen} style={{ marginTop: 10 }}>
            Alle als gelesen markieren
          </button>
        )}
      </Fenster>
    </>
  );
}
