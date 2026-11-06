import { Fenster } from "./Fenster";
import "./bildGross.css";

/**
 * Großansicht eines Bildes als eigenes Popup — z.B. im Tutorial-Shop und
 * normalen Shop, wo die Vorschaubilder in der Detailspalte sehr klein sind
 * (Marks Wunsch, 04.11.2026). Rein zum Anschauen, kein Upload/keine
 * Bearbeitung hier — dafür gibt es die EntitaetsBild-Knöpfe.
 * Klassen `.bild-gross` / `.bild-gross-rahmen`, nicht `.bg-bild` (das ist
 * der Begleiter-Zuschnitt mit object-fit:cover).
 */
export function BildGross({
  offen,
  bildUrl,
  name,
  onSchliessen,
}: {
  offen: boolean;
  bildUrl: string;
  name: string;
  onSchliessen: () => void;
}) {
  return (
    <Fenster offen={offen} titel={name} kennung={`bild-gross:${bildUrl}`} breit onSchliessen={onSchliessen}>
      <div className="bild-gross-rahmen">
        <img src={bildUrl} alt={name} className="bild-gross" />
      </div>
    </Fenster>
  );
}
