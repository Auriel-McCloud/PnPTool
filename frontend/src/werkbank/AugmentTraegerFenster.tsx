import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { waffentypPasst, type GegenstandMitBesitzer } from "../items/api";
import { AugmentFenster, type ZielAuswahl } from "./AugmentFenster";
import "../items/gegenstaende.css";

/** Ein Trägergegenstand oder eine Drohne/ein Fahrzeug mit Upgrade-Slots. */
export interface AugmentTraeger {
  id: string;
  name: string;
  kind: "Gegenstand" | "Person";
  upgradeSlots: number;
  /** Nur Gegenstand-Träger — Drohnen/Fahrzeuge (Person) haben kein
   *  `kampfFertigkeit`-Feld, kommt hier leer an (siehe `waffentypPasst`). */
  kampfFertigkeit: string;
}

/**
 * Upgrade-Popup für EINEN Träger (29.10.2026, Mark: "ich will ja einen
 * Gegenstand upgraden, also sollte ich die leichte Pistole sehen, und dort
 * die Slots was bereits in sie verbaut ist, und wenn ich die Pistole
 * anklicke sollte ich sehen was ich in sie verbauen kann"). Gegenstück zum
 * alten augment-zentrierten Einstieg (erst Material wählen, dann Ziel
 * suchen) — hier erst das Ziel, dann das passende freie Upgrade. Öffnet für
 * die eigentliche Montage/Demontage/Reparatur weiterhin `AugmentFenster`
 * unverändert, nur mit vorausgewähltem Ziel bei freien Upgrades.
 */
export function AugmentTraegerFenster({
  campaignId,
  traeger,
  alleGegenstaende,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  traeger: AugmentTraeger;
  /** Alle Gegenstände, aus denen montierte/freie Upgrades ermittelt werden
   *  — beim SL die ganze Kampagne, beim Spieler nur der eigene Besitzkreis
   *  (siehe `AugmentUebersicht(Spieler).tsx`). */
  alleGegenstaende: GegenstandMitBesitzer[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [offenesAugment, setOffenesAugment] = useState<GegenstandMitBesitzer | null>(null);
  const [vorausgewaehlt, setVorausgewaehlt] = useState(false);

  const montiert = alleGegenstaende.filter((g) => g.montiertAnId === traeger.id);
  const frei = alleGegenstaende.filter(
    (g) => g.istAugment && !g.defekt && !g.montiertAnId && waffentypPasst(g.augmentWaffentyp, traeger.kampfFertigkeit),
  );
  const slotsFrei = traeger.upgradeSlots - montiert.length;

  function kachel(g: GegenstandMitBesitzer, zielVorwaehlen: boolean) {
    return (
      <button
        key={g.id}
        type="button"
        className="gg-kachel"
        onClick={() => {
          setVorausgewaehlt(zielVorwaehlen);
          setOffenesAugment(g);
        }}
      >
        <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🔩</span>}</span>
        <span className="gg-kachel-name">{g.name}</span>
        <span className="gg-kachel-zeile">{g.defekt ? "defekt" : "frei, montierbar"}</span>
      </button>
    );
  }

  const ziel: ZielAuswahl = { id: traeger.id, name: traeger.name, kind: traeger.kind };

  return (
    <Fenster offen titel={`Upgraden: ${traeger.name}`} kennung={`augment-traeger:${traeger.id}`} onSchliessen={onSchliessen}>
      <p className="lu-hinweis">
        Slots belegt: <strong>{montiert.length}/{traeger.upgradeSlots}</strong>
      </p>

      {montiert.length > 0 && (
        <>
          <p className="lu-hinweis">Montiert</p>
          <div className="gg-raster">{montiert.map((g) => kachel(g, false))}</div>
        </>
      )}

      {slotsFrei > 0 ? (
        <>
          <p className="lu-hinweis" style={{ marginTop: montiert.length > 0 ? 10 : 0 }}>
            Freie Upgrades zum Einbauen
          </p>
          {frei.length === 0 && (
            <p className="gg-leer">
              Kein passendes freies Upgrade im Besitz — Typ "Upgrade-Material" plus "Ist selbst ein Upgrade" markieren
              lässt sich jeder Gegenstand über dessen eigenes Bearbeiten-Formular.
            </p>
          )}
          <div className="gg-raster">{frei.map((g) => kachel(g, true))}</div>
        </>
      ) : (
        <p className="gg-leer" style={{ marginTop: 10 }}>
          Alle Slots belegt — erst ein montiertes Upgrade demontieren, um Platz zu schaffen.
        </p>
      )}

      {offenesAugment && (
        <AugmentFenster
          campaignId={campaignId}
          augment={offenesAugment}
          vorausgewaehltesZiel={vorausgewaehlt ? ziel : undefined}
          onSchliessen={() => setOffenesAugment(null)}
          onGeaendert={onGeaendert}
        />
      )}
    </Fenster>
  );
}
