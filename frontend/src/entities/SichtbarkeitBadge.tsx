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
        background: modus === "GM" ? "#333" : modus === "ALLE" ? "#2a6" : "#a67c00",
        color: "white",
      }}
    >
      {text}
    </span>
  );
}
