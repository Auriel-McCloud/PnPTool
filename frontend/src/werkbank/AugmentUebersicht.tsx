import { useEffect, useState } from "react";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { AugmentFenster } from "./AugmentFenster";
import "../items/gegenstaende.css";

/**
 * Augments-Tab im Werkbank-Burgermenü (29.10.2026, siehe
 * docs/wiki/concepts/augments-ausruestung.md): alle Augment-Gegenstände im
 * Umlauf, Klick öffnet `AugmentFenster` (Montieren/Demontieren/Reparieren
 * je nach Zustand). **Nur SL**.
 */
export function AugmentUebersicht({ campaignId }: { campaignId: string }) {
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenesAugment, setOffenesAugment] = useState<GegenstandMitBesitzer | null>(null);

  function neuLaden() {
    setLaden(true);
    itemsApi
      .listAlle(campaignId)
      .then((items) => setGegenstaende(items.filter((g) => g.istAugment && !g.weggeworfen)))
      .catch(() => setFehler("Augments konnten nicht geladen werden."))
      .finally(() => setLaden(false));
  }

  useEffect(neuLaden, [campaignId]);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Augments…</p>;

  const defekte = gegenstaende.filter((g) => g.defekt);
  const montiert = gegenstaende.filter((g) => !g.defekt && g.montiertAnId);
  const frei = gegenstaende.filter((g) => !g.defekt && !g.montiertAnId);

  function kachel(g: GegenstandMitBesitzer) {
    return (
      <button key={g.id} type="button" className="gg-kachel" onClick={() => setOffenesAugment(g)}>
        <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🔩</span>}</span>
        <span className="gg-kachel-name">{g.name}</span>
        <span className="gg-kachel-zeile">
          {g.defekt ? "defekt" : g.montiertAnId ? `montiert an ${g.montiertAnName}` : "frei"} — {g.ownerName ?? "ohne Besitzer"}
        </span>
      </button>
    );
  }

  return (
    <div className="gg-seite">
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      {gegenstaende.length === 0 && (
        <p className="gg-leer">
          Noch kein Augment angelegt — als "Ist selbst ein Augment" markieren lässt sich jeder Gegenstand über dessen
          eigenes Bearbeiten-Formular (Optionen).
        </p>
      )}

      {defekte.length > 0 && (
        <>
          <p className="lu-hinweis" style={{ color: "var(--nein)" }}>Defekt ({defekte.length})</p>
          <div className="gg-raster">{defekte.map(kachel)}</div>
        </>
      )}
      {frei.length > 0 && (
        <>
          <p className="lu-hinweis">Frei, montierbar ({frei.length})</p>
          <div className="gg-raster">{frei.map(kachel)}</div>
        </>
      )}
      {montiert.length > 0 && (
        <>
          <p className="lu-hinweis">Montiert ({montiert.length})</p>
          <div className="gg-raster">{montiert.map(kachel)}</div>
        </>
      )}

      {offenesAugment && (
        <AugmentFenster
          campaignId={campaignId}
          augment={offenesAugment}
          onSchliessen={() => setOffenesAugment(null)}
          onGeaendert={neuLaden}
        />
      )}
    </div>
  );
}
