import { waffentypPasst, type GegenstandMitBesitzer } from "../items/api";
import { steckbriefKurz } from "../items/steckbrief";

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
 * Rechte Spalte der zweigeteilten Werkbank-Upgraden-Ansicht (29.10.2026,
 * Mark: "können wir es vielleicht in der Mitte aufteilen, so dass man auf
 * einer Seite die Items und auf der anderen die Upgrade-Materialien
 * sieht?" — Nachbesserung zum trägerzentrierten Umbau: statt eines
 * Popups pro Klick jetzt ein feststehendes zweites Panel neben der
 * Träger-Liste). Zeigt für den LINKS gewählten Träger die montierten
 * Upgrades (Klick → `AugmentFenster` zum Demontieren/Reparieren) und die
 * passenden freien Upgrades zum Einbauen (Klick → `AugmentFenster` mit
 * vorausgewähltem Ziel, kein Ziel-Chooser mehr nötig).
 */
export function AugmentTraegerPanel({
  traeger,
  alleGegenstaende,
  onUpgradeKlick,
}: {
  traeger: AugmentTraeger | null;
  /** Alle Gegenstände, aus denen montierte/freie Upgrades ermittelt werden
   *  — beim SL die ganze Kampagne, beim Spieler nur der eigene Besitzkreis
   *  (siehe `AugmentUebersicht(Spieler).tsx`). */
  alleGegenstaende: GegenstandMitBesitzer[];
  /** Öffnet das Montieren/Demontieren/Reparieren-Popup — `vorausgewaehlt`
   *  true heisst: Ziel ist der gerade angezeigte Träger (freie Upgrades). */
  onUpgradeKlick: (g: GegenstandMitBesitzer, vorausgewaehlt: boolean) => void;
}) {
  if (!traeger) {
    return <p className="gg-leer">Links einen Gegenstand oder eine Drohne/ein Fahrzeug wählen.</p>;
  }

  const montiert = alleGegenstaende.filter((g) => g.montiertAnId === traeger.id);
  const frei = alleGegenstaende.filter(
    (g) => g.istAugment && !g.defekt && !g.montiertAnId && waffentypPasst(g.augmentWaffentyp, traeger.kampfFertigkeit),
  );
  const slotsFrei = traeger.upgradeSlots - montiert.length;

  function kachel(g: GegenstandMitBesitzer, zielVorwaehlen: boolean) {
    return (
      <button key={g.id} type="button" className="gg-kachel" onClick={() => onUpgradeKlick(g, zielVorwaehlen)}>
        <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🔩</span>}</span>
        <span className="gg-kachel-name">{g.name}</span>
        <span className="gg-kachel-zeile">{g.defekt ? "defekt" : "frei, montierbar"}</span>
        {/* Was das Upgrade bewirkt (29.10.2026, Mark: "es wäre gut wenn das
            Material einen Steckbrief hätte, also man sieht was es tut") —
            liest traitBoni generisch, dieselbe Funktion wie bei jeder
            anderen Gegenstands-Kachel im Tool. */}
        {steckbriefKurz(g).length > 0 && (
          <span className="gg-kachel-steckbrief">{steckbriefKurz(g).join(" · ")}</span>
        )}
      </button>
    );
  }

  return (
    <div className="gg-seite">
      <p className="lu-hinweis">
        <strong>{traeger.name}</strong> — Slots belegt: <strong>{montiert.length}/{traeger.upgradeSlots}</strong>
      </p>

      {montiert.length > 0 && (
        <>
          <p className="lu-hinweis">Montiert</p>
          <div className="wb-kachelraster">{montiert.map((g) => kachel(g, false))}</div>
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
          <div className="wb-kachelraster">{frei.map((g) => kachel(g, true))}</div>
        </>
      ) : (
        <p className="gg-leer" style={{ marginTop: 10 }}>
          Alle Slots belegt — erst ein montiertes Upgrade demontieren, um Platz zu schaffen.
        </p>
      )}
    </div>
  );
}
