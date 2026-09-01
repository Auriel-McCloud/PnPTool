import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { itemsApi, type GegenstandMitBesitzer } from "./api";
import "./wegwerfen.css";

/**
 * Der Mülleimer der Spielleitung: alles, was Spieler oder SL weggeworfen
 * haben, landet hier statt endgültig gelöscht zu werden (siehe
 * WegwerfenFrage.tsx). Von hier aus geht es zurück ins Spiel oder — als
 * bewusst zweiter, eigener Schritt — endgültig weg.
 *
 * "Endgültig löschen" nutzt die schon vorhandene generische Löschroute
 * (DELETE .../{item_id} → itemsApi.remove): die kennt keinen Unterschied
 * zwischen weggeworfen und nicht, sie löscht den Knoten, egal woher man
 * kommt. Eine eigene Route dafür wäre doppelte Arbeit.
 */
export function Muelleimer({
  campaignId,
  offen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Nach Zurückholen/Löschen — die Übersicht dahinter muss neu laden. */
  onGeaendert: () => void;
}) {
  const [items, setItems] = useState<GegenstandMitBesitzer[]>([]);
  const [laedt, setLaedt] = useState(false);
  // Welche Zeile grad eine Aktion laufen hat — sperrt nur diese Zeile,
  // nicht den ganzen Mülleimer.
  const [laeuft, setLaeuft] = useState<string | null>(null);

  async function laden() {
    setLaedt(true);
    try {
      setItems(await itemsApi.listWeggeworfen(campaignId));
    } finally {
      setLaedt(false);
    }
  }

  useEffect(() => {
    if (offen) void laden();
  }, [offen, campaignId]);

  async function zurueckholen(itemId: string) {
    setLaeuft(itemId);
    try {
      await itemsApi.zurueckholen(campaignId, itemId);
      await laden();
      onGeaendert();
    } finally {
      setLaeuft(null);
    }
  }

  async function endgueltigLoeschen(item: GegenstandMitBesitzer) {
    // Rückfrage per window.confirm statt eigenem Fenster: das ist der
    // zweite, seltenere Schritt hinter der Wegwerfen-Rückfrage, und hier
    // ist die Konsequenz wirklich endgültig — knapp und unmissverständlich.
    if (!window.confirm(`"${item.name}" endgültig löschen? Das lässt sich nicht mehr zurückholen.`)) {
      return;
    }
    setLaeuft(item.id);
    try {
      await itemsApi.remove(campaignId, item.id);
      await laden();
      onGeaendert();
    } finally {
      setLaeuft(null);
    }
  }

  return (
    <Fenster offen={offen} titel="Mülleimer" kennung="muelleimer" onSchliessen={onSchliessen}>
      {laedt && <p className="mu-leer">Lade…</p>}
      {!laedt && items.length === 0 && <p className="mu-leer">Der Mülleimer ist leer.</p>}
      {!laedt && items.length > 0 && (
        <div className="mu-liste">
          {items.map((item) => (
            <div key={item.id} className="mu-zeile">
              <span className="mu-name">
                <strong>{item.name}</strong>
                <span className="mu-herkunft">
                  {item.ownerName ? `von ${item.ownerName}` : "ohne Besitzer"}
                  {item.weggeworfenVon && ` · weggeworfen von ${item.weggeworfenVon}`}
                </span>
              </span>
              <button type="button" disabled={laeuft === item.id} onClick={() => zurueckholen(item.id)}>
                Zurückholen
              </button>
              <button
                type="button"
                className="mu-endgueltig"
                disabled={laeuft === item.id}
                onClick={() => endgueltigLoeschen(item)}
              >
                Endgültig löschen
              </button>
            </div>
          ))}
        </div>
      )}
    </Fenster>
  );
}
