import { useEffect, useState } from "react";
import { PET_ARTEN, WACHSTUM_STUFEN, petsApi, type PetArt, type PetStand } from "./api";

/**
 * SL-Auswahl „Pet auf den Tablets“ — am Critter (Tiere) und am Gegenstand
 * (Bärbel, 11.11.2026: „Bärbel wäre ja ein Gegenstand und kein Critter“).
 * Bei Drachen am Critter dazu die Wachstumsstufe (Mark, 13.11.2026: SL-Knopf
 * zum Korrigieren) — er wächst von dort mit seinen EP normal weiter.
 */
export function PetArtWahl({
  campaignId,
  zielId,
  fuer,
  hinweis,
}: {
  campaignId: string;
  zielId: string;
  fuer: "critter" | "gegenstand";
  hinweis: string;
}) {
  const [stand, setStand] = useState<PetStand | null | undefined>(undefined);
  useEffect(() => {
    petsApi.artLesen(campaignId, zielId).then(setStand).catch(() => setStand(null));
  }, [campaignId, zielId]);
  if (stand === undefined) return null;
  const art = stand?.art ?? null;
  // Eine schon gesetzte Art bleibt wählbar, auch wenn sie eigentlich zur anderen Sorte gehört.
  const arten = PET_ARTEN.filter((a) => a.fuer === fuer || a.wert === art);
  const leise = { fontSize: 11, color: "var(--text-leise)" };
  return (
    <div className="bg-zeile" style={{ marginTop: 10, flexDirection: "column", alignItems: "stretch", gap: 4 }}>
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
        Pet auf den Tablets
        <select
          value={art ?? ""}
          onChange={async (e) => {
            const neu = (e.target.value || null) as PetArt | null;
            setStand(await petsApi.artSetzen(campaignId, zielId, neu));
          }}
        >
          <option value="">aus</option>
          {arten.map((a) => (
            <option key={a.wert} value={a.wert}>
              {a.name}
            </option>
          ))}
        </select>
      </label>
      <span style={leise}>{hinweis}</span>
      {stand?.waechst && stand.stufe && (
        <>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em", marginTop: 4 }}>
            Wachstum
            <select
              value={stand.gewachsen === null && stand.stufe !== "ei" ? "" : stand.stufe}
              onChange={async (e) => {
                if (e.target.value) setStand(await petsApi.wachstumSetzen(campaignId, zielId, e.target.value));
              }}
            >
              {/* Bestandsdrache von vor dem Wachstum: eigener Eintrag, damit auch „Junger Drache“ wählbar ist. */}
              {stand.gewachsen === null && stand.stufe !== "ei" && <option value="">Junger Drache (wächst nicht)</option>}
              {WACHSTUM_STUFEN.map((s) => (
                <option key={s.wert} value={s.wert}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <span style={leise}>
            {stand.stufe === "ei"
              ? "Liegt als Ei beim Besitzer, bis es oft genug angetippt wurde."
              : stand.gewachsen === null
                ? "Dieser Drache wächst noch nicht mit. Wähle eine Stufe, dann wächst er ab dort mit den EP seines Critters."
                : `${stand.gewachsen} EP seit dem Schlüpfen. Stufe wählen setzt ihn dorthin, danach wächst er normal weiter.`}
          </span>
        </>
      )}
    </div>
  );
}
