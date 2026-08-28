import type { SichtbarkeitModus } from "./api";

export interface PersonOption {
  id: string;
  name: string;
}

export function VisibilitySelector({
  label,
  modus,
  sichtbarFuer,
  onChange,
  pcOptions,
}: {
  label: string;
  modus: SichtbarkeitModus;
  sichtbarFuer: string[];
  onChange: (modus: SichtbarkeitModus, sichtbarFuer: string[]) => void;
  pcOptions: PersonOption[];
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>{label}</label>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <select value={modus} onChange={(e) => onChange(e.target.value as SichtbarkeitModus, sichtbarFuer)}>
          <option value="GM">SL-geheim</option>
          <option value="ALLE">Für alle Spieler sichtbar</option>
          <option value="SPEZIFISCH">Nur für bestimmte Spieler</option>
        </select>
        {modus === "SPEZIFISCH" && (
          <select
            multiple
            value={sichtbarFuer}
            onChange={(e) => onChange(modus, Array.from(e.target.selectedOptions, (o) => o.value))}
            style={{ minWidth: 180, minHeight: 60 }}
          >
            {pcOptions.length === 0 && <option disabled>Noch keine PCs angelegt</option>}
            {pcOptions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
