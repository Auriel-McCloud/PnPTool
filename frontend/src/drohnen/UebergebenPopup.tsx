import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import type { Gegenstand } from "../items/api";
import { KategorienAuswahl, vorhandeneTypenSortiert } from "../items/KategorienAuswahl";
import { steckbriefKurz } from "../items/steckbrief";
import "../items/wegwerfen.css";
import "../items/gegenstaende.css";

/**
 * Auswahl, welcher eigene Gegenstand an die Drohne/das Fahrzeug übergeben
 * wird (26.10.2026, Mark: "es müsste die Möglichkeit geben, etwas aus dem
 * Inventar des Riggers auszurüsten bzw. zu übergeben").
 *
 * Bewusst KEIN Annehmen/Ablehnen wie bei `items/WeitergebenPopup.tsx` — die
 * Drohne trifft keine eigene Entscheidung, die Übergabe ist sofort wirksam
 * (siehe `items/routes.py::besitzer_wechseln`, Rigger-Ausnahme).
 *
 * **28.10.2026, Mark: "ich brauche den Steckbrief des Gegenstands, damit ich
 * weiß welche Waffe ich der Drohne zuweise"** — vorher ein nackter
 * Name-Knopf ohne Typ/Werte. Jetzt Typ-Filter (gleiche `KategorienAuswahl`
 * wie in der Gegenstandsübersicht) + Textsuche + Steckbrief-Kurzzeile pro
 * Zeile, nach dem Muster von `items/Muelleimer.tsx` (mu-liste/mu-zeile).
 */
export function UebergebenPopup({
  offen,
  gegenstaende,
  zielName,
  laeuft,
  onUebergeben,
  onAbbrechen,
}: {
  offen: boolean;
  /** Eigene Gegenstände, aus denen gewählt werden kann (schon vorgefiltert:
   *  keine natürliche Rüstung, keine verbauten Implantate, keine Vorlagen). */
  gegenstaende: Gegenstand[];
  zielName: string;
  laeuft?: boolean;
  onUebergeben: (itemId: string) => void;
  onAbbrechen: () => void;
}) {
  const [suche, setSuche] = useState("");
  const [kategorie, setKategorie] = useState<string | null>(null);

  // Frischer Filter bei jedem neuen Öffnen — sonst wirkt die Liste beim
  // nächsten Mal leer, weil noch ein alter Treffer von zuvor steht.
  useEffect(() => {
    if (offen) {
      setSuche("");
      setKategorie(null);
    }
  }, [offen]);

  const vorhandeneTypen = useMemo(() => vorhandeneTypenSortiert(gegenstaende.map((g) => g.typ)), [gegenstaende]);

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    return gegenstaende.filter((g) => {
      if (kategorie !== null && g.typ !== kategorie) return false;
      if (!s) return true;
      return g.name.toLowerCase().includes(s) || g.typ.toLowerCase().includes(s);
    });
  }, [gegenstaende, suche, kategorie]);

  return (
    <Fenster offen={offen} titel={`An ${zielName} übergeben`} kennung="drohne-uebergeben" onSchliessen={onAbbrechen}>
      <p className="ww-hinweis">Wähle, was aus deinem eigenen Besitz {zielName} bekommen soll.</p>
      <p className="ww-beruhigung">Die Übergabe wirkt sofort — du kannst es jederzeit zurücknehmen.</p>
      {gegenstaende.length === 0 ? (
        <p style={{ color: "var(--text-leise)" }}>Nichts Übergebbares in deinem eigenen Besitz.</p>
      ) : (
        <>
          {gegenstaende.length > 3 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, margin: "10px 0" }}>
              <input
                className="gg-suche"
                type="search"
                placeholder="Suchen — Name oder Typ"
                value={suche}
                onChange={(e) => setSuche(e.target.value)}
              />
              <KategorienAuswahl vorhandeneTypen={vorhandeneTypen} gewaehlt={kategorie} onWaehlen={setKategorie} />
            </div>
          )}

          {gefiltert.length === 0 ? (
            <p style={{ color: "var(--text-leise)" }}>Nichts gefunden.</p>
          ) : (
            <div className="mu-liste" style={{ marginTop: 10 }}>
              {gefiltert.map((item) => {
                const steckbrief = steckbriefKurz(item);
                return (
                  <div key={item.id} className="mu-zeile">
                    <span className="mu-name">
                      <strong>{item.name}</strong>
                      <span className="mu-herkunft">
                        {item.typ}
                        {steckbrief.length > 0 && ` · ${steckbrief.join(" · ")}`}
                      </span>
                    </span>
                    <button
                      type="button"
                      className="ww-behalten"
                      disabled={laeuft}
                      onClick={() => onUebergeben(item.id)}
                    >
                      Übergeben
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </Fenster>
  );
}
