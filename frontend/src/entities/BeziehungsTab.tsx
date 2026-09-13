import { useState } from "react";
import type { EntityKind, Verbindung } from "./api";
import { beziehungsZeilen, BeziehungsListe } from "./BeziehungsListe";
import { VerbindungAnlegen } from "./VerbindungAnlegen";
import type { PersonOption } from "./VisibilitySelector";
import "./pc-detail.css";

/**
 * Beziehungs-Tab eines Detail-Popups: bestehende Verbindungen sehen UND neue
 * anlegen — beides an einem Ort, statt nur auf den Verbindungen-Bereich zu
 * verweisen.
 *
 * Gemeinsame Komponente für PCs, NPCs und Fraktionen: dieselbe Bedienlogik,
 * nur Eigenentität und Vorschläge unterscheiden sich.
 */

/** Schnellvorschläge für Personen — kein Anführer, dafür Geld und Bekannte. */
export const PERSON_TYP_VORSCHLAEGE = [
  "Schulden bei",
  "Gläubiger",
  "Freund",
  "Feind",
  "Kontakt",
  "Verwandt mit",
  "Arbeitet für",
  "Arbeitgeber",
  "Mitglied von",
];

interface BeziehungsTabProps {
  campaignId: string;
  /** Der feste Endpunkt, von dem aus verbunden wird. */
  eigenKind: EntityKind;
  eigenId: string;
  eigenName: string;
  verbindungen: Verbindung[];
  /** ID → Name/Art für die Gegenseiten; muss sichtbarkeitsgefiltert sein. */
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  typVorschlaege: string[];
  /** Leitfarbe für Button und Dialog. */
  farbe?: string;
  onGeaendert: () => void;
}

export function BeziehungsTab({
  campaignId,
  eigenKind,
  eigenId,
  eigenName,
  verbindungen,
  namen,
  pcOptions,
  typVorschlaege,
  farbe = "var(--neon)",
  onGeaendert,
}: BeziehungsTabProps) {
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const zeilen = beziehungsZeilen(eigenId, verbindungen, namen);

  return (
    <div
      className="pcd-editor-bereich"
      style={{ "--verbindung-farbe": farbe } as React.CSSProperties}
    >
      <BeziehungsListe campaignId={campaignId} zeilen={zeilen} onGeaendert={onGeaendert} farbe={farbe} />

      <button type="button" className="verbindung-neu" onClick={() => setAnlegenOffen(true)}>
        + Neue Verbindung
      </button>

      {anlegenOffen && (
        <VerbindungAnlegen
          campaignId={campaignId}
          eigenKind={eigenKind}
          eigenId={eigenId}
          eigenName={eigenName}
          namen={namen}
          pcOptions={pcOptions}
          typVorschlaege={typVorschlaege}
          farbe={farbe}
          onGeaendert={onGeaendert}
          onSchliessen={() => setAnlegenOffen(false)}
        />
      )}
    </div>
  );
}
