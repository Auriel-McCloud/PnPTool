import type { SichtbarkeitModus } from "./api";

export function SichtbarkeitBadge({
  modus,
  sichtbarFuer,
  personenById,
  label,
}: {
  modus: SichtbarkeitModus;
  sichtbarFuer: string[];
  personenById: Map<string, string>;
  label: string;
}) {
  const text =
    modus === "GM"
      ? `${label}: SL-geheim`
      : modus === "ALLE"
        ? `${label}: alle Spieler`
        : `${label}: ${sichtbarFuer.map((id) => personenById.get(id) ?? "?").join(", ") || "niemand ausgewählt"}`;
  return (
    <span
      style={{
        marginRight: 8,
        fontSize: "0.75em",
        padding: "2px 8px",
        borderRadius: 4,
        // Magenta trägt in der Oberfläche durchgehend die Bedeutung
        // "SL-geheim" (siehe index.css), deshalb hier ebenso.
        background:
          modus === "GM" ? "var(--signal-schwach)" : modus === "ALLE" ? "color-mix(in srgb, var(--gut) 14%, transparent)" : "color-mix(in srgb, var(--warn) 14%, transparent)",
        color: modus === "GM" ? "var(--signal)" : modus === "ALLE" ? "var(--gut)" : "var(--warn)",
        border: `1px solid ${modus === "GM" ? "var(--signal)" : modus === "ALLE" ? "var(--gut)" : "var(--warn)"}`,
      }}
    >
      {text}
    </span>
  );
}
