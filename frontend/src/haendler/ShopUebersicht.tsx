import { useEffect, useState } from "react";
import { haendlerApi, type HaendlerEintrag, type BestellungResponse } from "./api";
import { ShopSeite } from "./ShopSeite";
import "./shop.css";

/**
 * Der Shop-Bereich (eigener Burgermenü-Punkt, Marks Vorgabe 24.09.2026):
 * Kachelraster aller sichtbaren Händler, Klick öffnet die jeweilige
 * Shop-Seite (ShopSeite.tsx, dort physisch/digital verzweigt).
 *
 * Bei Spielern zeigt sie zusätzlich die eigenen offenen Bestellungen
 * (verzögerte Online-Käufe); die SL sieht stattdessen alle offenen
 * Bestellungen der Kampagne mit dem "Jetzt liefern"-Knopf.
 */
export function ShopUebersicht({
  campaignId,
  eigenePersonId,
  istGm,
}: {
  campaignId: string;
  eigenePersonId: string | null;
  istGm: boolean;
}) {
  const [haendler, setHaendler] = useState<HaendlerEintrag[]>([]);
  const [bestellungen, setBestellungen] = useState<BestellungResponse[]>([]);
  const [offenerHaendler, setOffenerHaendler] = useState<string | null>(null);

  async function laden() {
    const [h, b] = await Promise.all([
      haendlerApi.alle(campaignId),
      istGm ? haendlerApi.bestellungenOffen(campaignId) : haendlerApi.bestellungenEigene(campaignId),
    ]);
    setHaendler(h);
    setBestellungen(b);
  }

  useEffect(() => {
    laden();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, istGm]);

  async function liefern(bestellungId: string) {
    await haendlerApi.bestellungLiefern(campaignId, bestellungId);
    await laden();
  }

  if (offenerHaendler) {
    return (
      <ShopSeite
        campaignId={campaignId}
        haendlerId={offenerHaendler}
        eigenePersonId={eigenePersonId}
        istGm={istGm}
        onSchliessen={() => {
          setOffenerHaendler(null);
          laden();
        }}
      />
    );
  }

  return (
    <div className="shop-seite">
      <div className="shop-haendler-raster">
        {haendler.map((h) => (
          <button
            key={h.id}
            type="button"
            className="shop-haendler-kachel"
            data-hat-bild={Boolean(h.shopHintergrundUrl)}
            style={{ "--shop-bild": h.shopHintergrundUrl ? `url(${h.shopHintergrundUrl})` : "none" } as React.CSSProperties}
            onClick={() => setOffenerHaendler(h.id)}
          >
            <span className="shop-haendler-name">{h.name}</span>
            <span className="shop-haendler-art" data-art={h.vertriebsart}>
              {h.vertriebsart === "DIGITAL" ? "Online" : "Vor Ort"}
            </span>
            {h.spezialisierung.length > 0 && (
              <span className="shop-haendler-spez">
                {h.spezialisierung.map((s) => (
                  <span key={s} className="gg-marke">{s}</span>
                ))}
              </span>
            )}
          </button>
        ))}
        {haendler.length === 0 && <p className="shop-leer">Noch keine Händler bekannt.</p>}
      </div>

      {/* Bestellungen: SL sieht alle offenen, Spieler nur die eigenen. */}
      {bestellungen.length > 0 && (
        <section>
          <h3 className="gg-abschnitt">
            <span>{istGm ? "Offene Online-Bestellungen" : "Deine Bestellungen"}</span>
            <span className="gg-abschnitt-zahl">{bestellungen.length}</span>
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {bestellungen.map((b) => (
              <div key={b.id} className="shop-bestellung-zeile">
                <span>
                  {b.gegenstandName} — <span style={{ color: "var(--text-leise)" }}>{b.haendlerName}</span>
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="shop-bestellung-status" data-status={b.status}>
                    {b.status === "OFFEN" ? "unterwegs" : "geliefert"}
                  </span>
                  {istGm && b.status === "OFFEN" && (
                    <button type="button" onClick={() => liefern(b.id)}>
                      Jetzt liefern
                    </button>
                  )}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
