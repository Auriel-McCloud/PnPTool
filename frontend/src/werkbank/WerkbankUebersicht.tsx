import { useState } from "react";
import { ReparaturUebersicht } from "../reparatur/ReparaturUebersicht";
import { AugmentUebersicht } from "./AugmentUebersicht";

/**
 * Burgermenü "Werkbank" (29.10.2026, Mark: "was ist wenn wir das Menü nicht
 * nur Reparatur, sondern einfach Werkbank nennen" — siehe
 * docs/wiki/concepts/augments-ausruestung.md): Oberbegriff für alles, was
 * an Waffe/Rüstung/Drohne/Fahrzeug herumgeschraubt wird. Zwei Reiter:
 *
 * - **Reparatur** (29.10.2026, zuerst gebaut): Material-Stufen +
 *   selbstberichtete Probe, siehe `reparatur/ReparaturUebersicht.tsx`.
 * - **Augments** (29.10.2026, zweiter Baustein): Zielfernrohr & Co. an
 *   Waffe/Rüstung/Cyberdeck/Riggerkonsole/Drohne/Fahrzeug montieren.
 *
 * Ersetzt das vorherige, enger benannte Burgermenü "Reparatur" 1:1 — gleiche
 * Bereich-Position in `App.tsx`, nur umbenannt plus erweitert.
 */
export function WerkbankUebersicht({ campaignId }: { campaignId: string }) {
  const [tab, setTab] = useState<"reparatur" | "augments">("reparatur");

  return (
    <div>
      <div className="gg-kopf">
        <button type="button" aria-pressed={tab === "reparatur"} onClick={() => setTab("reparatur")}>
          🔧 Reparatur
        </button>
        <button type="button" aria-pressed={tab === "augments"} onClick={() => setTab("augments")}>
          🔩 Upgraden
        </button>
      </div>
      {tab === "reparatur" && <ReparaturUebersicht campaignId={campaignId} />}
      {tab === "augments" && <AugmentUebersicht campaignId={campaignId} />}
    </div>
  );
}
