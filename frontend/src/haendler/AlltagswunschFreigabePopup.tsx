import { useState } from "react";
import { createPortal } from "react-dom";
import { useMitteilungen } from "../mitteilungen/MitteilungenKontext";
import "../shell/bestaetigung.css";
import "../haendler/shop.css";

/**
 * SL-Popup (24.09.2026): ein Spieler hat einen Verkäufer nach einem
 * Alltagsgegenstand gefragt, die KI hat schon einen Vorschlag samt Preis
 * gemacht — die SL entscheidet, ohne dass der Spieler warten muss (der
 * bekommt die Antwort separat als Ergebnis-Popup, siehe
 * AlltagswunschErgebnisPopup). Liegt wie VerhandlungPopup über allem.
 */
export function AlltagswunschFreigabePopup() {
  const { alltagswunschAktuell: w, alltagswunschWartend, alltagswunschEntscheiden } = useMitteilungen();
  const [name, setName] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [preis, setPreis] = useState("");
  const [grund, setGrund] = useState("");
  const [ablehnenModus, setAblehnenModus] = useState(false);
  const [läuft, setLäuft] = useState(false);

  if (!w) return null;

  // Formularfelder erst befüllen, wenn ein neuer Wunsch reinkommt (sonst
  // würde jedes Neu-Rendern die Eingabe der SL überschreiben) — einfachster
  // Weg ohne useEffect: key auf dem Wurzel-Element unten per w.id.

  async function entscheiden(angenommen: boolean) {
    setLäuft(true);
    try {
      if (angenommen) {
        await alltagswunschEntscheiden(true, {
          name: name.trim() || undefined,
          beschreibung: beschreibung.trim() || undefined,
          preis: preis.trim() ? Number(preis) : undefined,
        });
      } else {
        await alltagswunschEntscheiden(false, undefined, grund.trim() || undefined);
      }
      setName("");
      setBeschreibung("");
      setPreis("");
      setGrund("");
      setAblehnenModus(false);
    } finally {
      setLäuft(false);
    }
  }

  return createPortal(
    <div className="best-huelle" key={w!.id}>
      <div className="best-kasten shop-ware-verhandel-form" style={{ maxWidth: 420 }}>
        <h2 className="best-titel">⚡ Alltagswunsch: {w!.spielerName}</h2>
        <p className="shop-ware-hinweis">
          fragt <strong>{w!.haendlerName}</strong>: „{w!.wunschText}“
        </p>
        <p className="shop-ware-hinweis">
          KI-Vorschlag: <strong>{w!.vorschlagName}</strong> ({w!.vorschlagTyp}) — {w!.vorschlagPreis}¥
        </p>
        {w!.vorschlagBeschreibung && (
          <p className="shop-ware-hinweis" style={{ fontStyle: "italic" }}>
            {w!.vorschlagBeschreibung}
          </p>
        )}

        {!ablehnenModus ? (
          <>
            <label style={{ display: "block", fontSize: 12, marginBottom: 4 }}>
              Name (leer = KI-Vorschlag übernehmen)
            </label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder={w!.vorschlagName} />
            <label style={{ display: "block", fontSize: 12, margin: "8px 0 4px" }}>Beschreibung (optional)</label>
            <input
              value={beschreibung}
              onChange={(e) => setBeschreibung(e.target.value)}
              placeholder={w!.vorschlagBeschreibung}
            />
            <label style={{ display: "block", fontSize: 12, margin: "8px 0 4px" }}>Preis in ¥ (optional)</label>
            <input
              type="number"
              min={0}
              value={preis}
              onChange={(e) => setPreis(e.target.value)}
              placeholder={String(w!.vorschlagPreis)}
            />
          </>
        ) : (
          <>
            <label style={{ display: "block", fontSize: 12, marginBottom: 4 }}>
              Ablehnungsgrund (optional, Spieler sieht ihn)
            </label>
            <input value={grund} onChange={(e) => setGrund(e.target.value)} placeholder="z.B. nicht hier erhältlich" />
          </>
        )}

        <div className="shop-ware-knoepfe" style={{ marginTop: 12 }}>
          {!ablehnenModus ? (
            <>
              <button type="button" className="best-nein" onClick={() => setAblehnenModus(true)} disabled={läuft}>
                Ablehnen
              </button>
              <button type="button" className="best-ja shop-ware-kaufen-btn" onClick={() => entscheiden(true)} disabled={läuft}>
                Annehmen
              </button>
            </>
          ) : (
            <>
              <button type="button" className="best-nein" onClick={() => setAblehnenModus(false)} disabled={läuft}>
                Zurück
              </button>
              <button type="button" className="best-ja" onClick={() => entscheiden(false)} disabled={läuft}>
                Endgültig ablehnen
              </button>
            </>
          )}
        </div>
        {alltagswunschWartend > 0 && (
          <p className="shop-ware-hinweis" style={{ marginTop: 8 }}>
            +{alltagswunschWartend} weitere{alltagswunschWartend === 1 ? "r" : ""} Wunsch{alltagswunschWartend === 1 ? "" : "wünsche"} in der Warteschlange
          </p>
        )}
      </div>
    </div>,
    document.body,
  );
}
