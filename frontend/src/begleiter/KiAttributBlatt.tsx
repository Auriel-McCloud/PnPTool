import { DotPool } from "../traits/DotPool";
import type { Begleiter } from "./api";

/** Die sieben KI-Attribute als eigener Typ — überall dort brauchbar, wo nur
 * diese Werte vorliegen (Bearbeiten-Formular hält sie einzeln in useState,
 * nicht als ganzes Begleiter-Objekt). */
export type KiAttribute = Pick<
  Begleiter,
  "charisma" | "manipulation" | "fassung" | "intelligenz" | "geistesschaerfe" | "entschlossenheit" | "matrixPraesenz"
>;

/**
 * Die sieben KI-Attribute — dieselbe Skala 1-6 wie bei Personen (Mark,
 * 19.09.2026: "unsere Skala bei Attributen geht von 1-6... verwenden wir
 * wirklich unser system wie bei einer person weiter"). Nur die
 * geistigen/gesellschaftlichen Attribute, eine körperlose KI hat keine
 * körperlichen — dazu neu Matrix-Präsenz.
 */
export const KI_ATTRIBUTE: { feld: keyof KiAttribute; name: string; erklaerung: string }[] = [
  { feld: "charisma", name: "Charisma", erklaerung: "Wie sympathisch/einschüchternd sie auf Menschen wirkt." },
  { feld: "manipulation", name: "Manipulation", erklaerung: "Wie gut sie Menschen digital beeinflussen kann." },
  { feld: "fassung", name: "Fassung", erklaerung: "Stabilität gegen Überlastung, Viren, Gegenangriffe." },
  { feld: "intelligenz", name: "Intelligenz", erklaerung: "Rechenleistung, Datenverarbeitung, logisches Denken." },
  { feld: "geistesschaerfe", name: "Geistesschärfe", erklaerung: "Reaktionsgeschwindigkeit in der Matrix." },
  { feld: "entschlossenheit", name: "Entschlossenheit", erklaerung: "Durchhalten, sich nicht abschalten lassen." },
  { feld: "matrixPraesenz", name: "Matrix-Präsenz", erklaerung: "Wie dominant/sichtbar sie in der Matrix ist." },
];

/** Anzeige- und Bearbeitungs-Grid für die KI-Attribute. */
export function KiAttributBlatt({
  werte,
  onAendern,
}: {
  werte: KiAttribute;
  /** Fehlt sie, ist das Blatt nur zum Ansehen. */
  onAendern?: (feld: keyof KiAttribute, wert: number) => void;
}) {
  return (
    <section className="bg-werte" style={{ "--cb-ton": "var(--bereich-begleiter)" } as React.CSSProperties}>
      {KI_ATTRIBUTE.map(({ feld, name, erklaerung }) => (
        <div key={feld} className="bg-wert" title={erklaerung}>
          <span>{name}</span>
          <DotPool
            value={werte[feld]}
            max={6}
            onChange={onAendern ? (w) => onAendern(feld, w) : undefined}
          />
        </div>
      ))}
    </section>
  );
}
