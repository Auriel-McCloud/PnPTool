import { useEffect, useState } from "react";
import { type GegenstandMitBesitzer } from "../items/api";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { ReparaturUebersichtSpieler } from "./ReparaturUebersichtSpieler";
import { AugmentUebersichtSpieler } from "./AugmentUebersichtSpieler";

/**
 * Werkbank für Spieler (29.10.2026, Mark: "das war alles für die Spieler
 * gedacht!" — Korrektur, beide Unter-Features waren `require_campaign_gm`).
 * Gegenstück zu `werkbank/WerkbankUebersicht.tsx` (SL-Ansicht, campaignweit):
 * zwei Reiter Reparatur/Augments, aber nur der eigene Besitz — eigene
 * Person ODER eigene gebundene Drohne/eigenes Fahrzeug (`riggerId` statt
 * der fragilen `eigeneDrohnenIds` aus `SpielerAnsicht.tsx`, die nur gefüllt
 * ist, wenn der Kampf-Reiter schon mal offen war — hier deshalb ein
 * eigener, unabhängiger Drohnen-Fetch).
 */
export function WerkbankUebersichtSpieler({
  campaignId,
  personId,
  sachen,
  onGeaendert,
}: {
  campaignId: string;
  personId: string;
  sachen: GegenstandMitBesitzer[];
  onGeaendert: () => void;
}) {
  const [tab, setTab] = useState<"reparatur" | "augments">("reparatur");
  const [meineDrohnen, setMeineDrohnen] = useState<DrohnenEintrag[]>([]);

  useEffect(() => {
    drohnenApi
      .liste(campaignId)
      .then((liste) => setMeineDrohnen(liste.filter((d) => d.riggerId === personId)))
      .catch(() => setMeineDrohnen([]));
  }, [campaignId, personId]);

  const eigenerKreis = new Set([personId, ...meineDrohnen.map((d) => d.id)]);
  const meine = sachen.filter((g) => !g.weggeworfen && eigenerKreis.has(g.ownerId ?? ""));
  const meineAugmente = meine.filter((g) => g.istAugment);
  const meineRuestung = meine.filter(
    (g) => g.typ === "Rüstung" && g.ruestungKaestchenMax > 0 && !g.istNatuerlich && g.ruestungKaestchenAktuell < g.ruestungKaestchenMax,
  );
  const meineDrohnenKaputt = meineDrohnen; // Gesundheitsschaden wird im Popup selbst geprüft/angezeigt

  return (
    <div className="gg-seite">
      <div className="gg-kopf">
        <button type="button" aria-pressed={tab === "reparatur"} onClick={() => setTab("reparatur")}>
          🔧 Reparatur
        </button>
        <button type="button" aria-pressed={tab === "augments"} onClick={() => setTab("augments")}>
          🔩 Upgraden
        </button>
      </div>
      {tab === "reparatur" && (
        <ReparaturUebersichtSpieler
          campaignId={campaignId}
          ruestungsziele={meineRuestung}
          drohnen={meineDrohnenKaputt}
          onGeaendert={onGeaendert}
        />
      )}
      {tab === "augments" && (
        <AugmentUebersichtSpieler campaignId={campaignId} items={meineAugmente} onGeaendert={onGeaendert} />
      )}
    </div>
  );
}
