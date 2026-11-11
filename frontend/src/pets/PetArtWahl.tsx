import { useEffect, useState } from "react";
import { PET_ARTEN, petsApi, type PetArt } from "./api";

/**
 * SL-Auswahl „Pet auf den Tablets“ — am Critter (Tiere) und am Gegenstand
 * (Bärbel, 11.11.2026: „Bärbel wäre ja ein Gegenstand und kein Critter“).
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
  const [art, setArt] = useState<PetArt | null | undefined>(undefined);
  useEffect(() => {
    petsApi.artLesen(campaignId, zielId).then((d) => setArt(d.art)).catch(() => setArt(null));
  }, [campaignId, zielId]);
  if (art === undefined) return null;
  // Eine schon gesetzte Art bleibt wählbar, auch wenn sie eigentlich zur anderen Sorte gehört.
  const arten = PET_ARTEN.filter((a) => a.fuer === fuer || a.wert === art);
  return (
    <div className="bg-zeile" style={{ marginTop: 10, flexDirection: "column", alignItems: "stretch", gap: 4 }}>
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
        Pet auf den Tablets
        <select
          value={art ?? ""}
          onChange={async (e) => {
            const neu = (e.target.value || null) as PetArt | null;
            const d = await petsApi.artSetzen(campaignId, zielId, neu);
            setArt(d.art);
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
      <span style={{ fontSize: 11, color: "var(--text-leise)" }}>{hinweis}</span>
    </div>
  );
}
