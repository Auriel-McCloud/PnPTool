import { Fenster } from "../shell/Fenster";
import type { Gegenstand } from "../items/api";
import "../items/wegwerfen.css";

/**
 * Auswahl, welcher eigene Gegenstand an die Drohne/das Fahrzeug übergeben
 * wird (26.10.2026, Mark: "es müsste die Möglichkeit geben, etwas aus dem
 * Inventar des Riggers auszurüsten bzw. zu übergeben").
 *
 * Bewusst KEIN Annehmen/Ablehnen wie bei `items/WeitergebenPopup.tsx` — die
 * Drohne trifft keine eigene Entscheidung, die Übergabe ist sofort wirksam
 * (siehe `items/routes.py::besitzer_wechseln`, Rigger-Ausnahme).
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
  return (
    <Fenster offen={offen} titel={`An ${zielName} übergeben`} kennung="drohne-uebergeben" onSchliessen={onAbbrechen}>
      <p className="ww-hinweis">Wähle, was aus deinem eigenen Besitz {zielName} bekommen soll.</p>
      <p className="ww-beruhigung">Die Übergabe wirkt sofort — du kannst es jederzeit zurücknehmen.</p>
      {gegenstaende.length === 0 ? (
        <p style={{ color: "var(--text-leise)" }}>Nichts Übergebbares in deinem eigenen Besitz.</p>
      ) : (
        <div className="ww-knoepfe" style={{ flexWrap: "wrap" }}>
          {gegenstaende.map((item) => (
            <button
              key={item.id}
              type="button"
              className="ww-behalten"
              disabled={laeuft}
              onClick={() => onUebergeben(item.id)}
            >
              {item.name}
            </button>
          ))}
        </div>
      )}
    </Fenster>
  );
}
