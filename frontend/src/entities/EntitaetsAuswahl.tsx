import { useState } from "react";
import type { EntityKind } from "./api";

const KIND_LABEL: Record<EntityKind, string> = {
  Person: "Person",
  Ort: "Ort",
  Event: "Event",
  Fraktion: "Fraktion",
  Gegenstand: "Gegenstand",
};

const KIND_ORDNUNG: Record<EntityKind, number> = {
  Person: 0,
  Ort: 1,
  Event: 2,
  Fraktion: 3,
  Gegenstand: 4,
};

interface EntitaetsOption {
  id: string;
  kind: EntityKind;
  name: string;
}

/**
 * Durchsuchbare Endpunkt-Wahl für Verbindungen: eigenes Suchfeld über einer
 * nach Art sortierten Auswahlliste.
 *
 * Eigene Komponente statt ein natives <select> allein, weil in größeren
 * Kampagnen "wirklich alles" zur Auswahl steht — Personen, Orte, Events,
 * Fraktionen, Gegenstände. Ohne Suche müsste man ein sehr langes Dropdown
 * durchscrollen, um die eine gesuchte Entität zu finden.
 */
export function EntitaetsAuswahl({
  label,
  namen,
  value,
  onChange,
  ausschluss,
}: {
  label: string;
  /** Wählbare Entitäten — bereits sichtbarkeitsgefiltert geladen. */
  namen: Map<string, { name: string; kind: EntityKind }>;
  value: string;
  onChange: (id: string) => void;
  /** ID, die aus der Auswahl ausscheidet (z.B. die bereits gewählte Gegenseite). */
  ausschluss?: string;
}) {
  const [suche, setSuche] = useState("");

  const optionen: EntitaetsOption[] = Array.from(namen.entries())
    .filter(([id]) => id !== ausschluss)
    .map(([id, { name, kind }]) => ({ id, kind, name }))
    .sort((a, b) => {
      if (KIND_ORDNUNG[a.kind] !== KIND_ORDNUNG[b.kind]) return KIND_ORDNUNG[a.kind] - KIND_ORDNUNG[b.kind];
      return a.name.localeCompare(b.name, "de");
    });

  const sucheNorm = suche.trim().toLowerCase();
  const gefiltert = sucheNorm
    ? optionen.filter(
        (o) => o.name.toLowerCase().includes(sucheNorm) || KIND_LABEL[o.kind].toLowerCase().includes(sucheNorm),
      )
    : optionen;

  return (
    <div>
      <label className="pcd-label">{label}</label>
      <input
        type="text"
        className="ziel-input"
        placeholder="Suchen — Name oder Typ"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
        style={{ marginBottom: 6 }}
      />
      <select className="ziel-input" value={value} onChange={(e) => onChange(e.target.value)} required>
        <option value="">— wählen —</option>
        {gefiltert.map((o) => (
          <option key={o.id} value={o.id}>
            {KIND_LABEL[o.kind]}: {o.name}
          </option>
        ))}
      </select>
      {sucheNorm && gefiltert.length === 0 && (
        <p className="pcd-hinweis" style={{ marginTop: 6 }}>
          Keine Treffer für „{suche.trim()}".
        </p>
      )}
    </div>
  );
}
