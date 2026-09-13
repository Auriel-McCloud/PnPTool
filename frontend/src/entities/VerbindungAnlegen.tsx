import { useState } from "react";
import type { EntityKind, SichtbarkeitModus, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { Fenster } from "../shell/Fenster";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import "./pc-detail.css";

/**
 * Legt eine neue Verbindung an, ausgehend von einer festen Entität.
 *
 * Wird im Beziehungs-Tab der Detail-Popups genutzt, damit man dort nicht nur
 * bestehende Kanten *sieht*, sondern auch neue anlegen kann — z.B. den
 * Anführer einer Fraktion oder ihren Einfluss auf einen Ort, ohne dafür in
 * den Verbindungen-Bereich zu wechseln.
 *
 * Die feste Entität ist ein Endpunkt; der andere ist frei wählbar aus `namen`.
 * Die Richtung ist umschaltbar (Subjekt/Predikat), weil „X ist Anführer der
 * Fraktion" und „Die Fraktion hat Einfluss auf X" beide vorkommen.
 */

const KIND_LABEL: Record<EntityKind, string> = {
  Person: "Person",
  Ort: "Ort",
  Event: "Event",
  Fraktion: "Fraktion",
  Gegenstand: "Gegenstand",
};

interface VerbindungAnlegenProps {
  campaignId: string;
  /** Der feste Endpunkt, von dem aus verbunden wird. */
  eigenKind: EntityKind;
  eigenId: string;
  eigenName: string;
  /** Wählbare Gegenseiten — bereits sichtbarkeitsgefiltert geladen. */
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  /** Schnellvorschläge für den Beziehungstyp. */
  typVorschlaege: string[];
  /** Leitfarbe für Rahmen und Bedienelemente (z.B. var(--bereich-pcs)). */
  farbe?: string;
  onGeaendert: () => void;
  onSchliessen: () => void;
}

export function VerbindungAnlegen({
  campaignId,
  eigenKind,
  eigenId,
  eigenName,
  namen,
  pcOptions,
  typVorschlaege,
  farbe = "var(--neon)",
  onGeaendert,
  onSchliessen,
}: VerbindungAnlegenProps) {
  const [zielId, setZielId] = useState("");
  const [zielSuche, setZielSuche] = useState("");
  const [typ, setTyp] = useState("");
  const [richtung, setRichtung] = useState<"aus" | "ein">("aus");
  const [beschreibung, setBeschreibung] = useState("");
  const [sichtbarkeit, setSichtbarkeit] = useState<SichtbarkeitModus>("GM");
  const [sichtbarFuer, setSichtbarFuer] = useState<string[]>([]);
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  // Sortierte Ziel-Liste aus der Namenstabelle; die eigene Entität scheidet
  // aus, damit man sie nicht mit sich selbst verbindet.
  const ziele = Array.from(namen.entries())
    .filter(([id]) => id !== eigenId)
    .map(([id, { name, kind }]) => ({ id, kind, name }))
    .sort((a, b) => {
      const ordnung: Record<EntityKind, number> = {
        Person: 0,
        Ort: 1,
        Event: 2,
        Fraktion: 3,
        Gegenstand: 4,
      };
      if (ordnung[a.kind] !== ordnung[b.kind]) return ordnung[a.kind] - ordnung[b.kind];
      return a.name.localeCompare(b.name, "de");
    });

  // Suche im Ziel-Feld: filtert nach Name und nach Typbezeichnung. Ohne
  // Eingabe bleibt die vollständige, nach Typ sortierte Liste stehen.
  const zielSucheNorm = zielSuche.trim().toLowerCase();
  const gefilterteZiele = zielSucheNorm
    ? ziele.filter(
        (z) =>
          z.name.toLowerCase().includes(zielSucheNorm) ||
          KIND_LABEL[z.kind].toLowerCase().includes(zielSucheNorm),
      )
    : ziele;

  async function speichern() {
    const ziel = ziele.find((z) => z.id === zielId);
    if (!ziel || !typ.trim()) return;
    setSpeichert(true);
    setFehler(null);
    try {
      const basis: Omit<Verbindung, "id"> = {
        vonKind: richtung === "aus" ? eigenKind : ziel.kind,
        vonId: richtung === "aus" ? eigenId : ziel.id,
        zuKind: richtung === "aus" ? ziel.kind : eigenKind,
        zuId: richtung === "aus" ? ziel.id : eigenId,
        typ: typ.trim(),
        beschreibung,
        seit: "",
        bis: "",
        sichtbarkeit,
        sichtbarFuer,
      };
      await entitiesApi.createVerbindung(campaignId, basis);
      onGeaendert();
      onSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verbindung konnte nicht angelegt werden");
      setSpeichert(false);
    }
  }

  return (
    <Fenster
      offen
      titel="Neue Verbindung"
      unterzeile={`Von „${eigenName}" aus`}
      kennung={`verbindung-anlegen:${eigenKind}:${eigenId}`}
      ton={farbe}
      onSchliessen={onSchliessen}
    >
      <div className="pcd-editor-bereich" style={{ padding: 8, "--verbindung-farbe": farbe } as React.CSSProperties}>
        {fehler && <p style={{ color: "var(--signal)", margin: 0 }}>{fehler}</p>}

        <div>
          <label className="pcd-label">Beziehungstyp</label>
          <input
            type="text"
            className="ziel-input"
            placeholder="z.B. Anführer, Einfluss, Verbündeter …"
            value={typ}
            autoFocus
            onChange={(e) => setTyp(e.target.value)}
          />
          {typVorschlaege.length > 0 && (
            <div className="typ-vorschlaege">
              {typVorschlaege.map((v) => (
                <button
                  key={v}
                  type="button"
                  className="typ-vorschlag"
                  onClick={() => setTyp(v)}
                >
                  {v}
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="pcd-label">Mit wem oder was</label>
          <input
            type="text"
            className="ziel-input"
            placeholder="Suchen — Name oder Typ"
            value={zielSuche}
            onChange={(e) => setZielSuche(e.target.value)}
            style={{ marginBottom: 6 }}
          />
          <select
            className="ziel-input"
            value={zielId}
            onChange={(e) => setZielId(e.target.value)}
            required
          >
            <option value="">— wählen —</option>
            {gefilterteZiele.map((z) => (
              <option key={z.id} value={z.id}>
                {KIND_LABEL[z.kind]}: {z.name}
              </option>
            ))}
          </select>
          {zielSucheNorm && gefilterteZiele.length === 0 && (
            <p className="pcd-hinweis" style={{ marginTop: 6 }}>
              Keine Treffer für „{zielSuche.trim()}".
            </p>
          )}
        </div>

        <div>
          <label className="pcd-label">Richtung</label>
          <div className="richtung-auswahl">
            <button
              type="button"
              className={richtung === "aus" ? "richtung-aktiv" : ""}
              onClick={() => setRichtung("aus")}
            >
              {eigenName} → Ziel
            </button>
            <button
              type="button"
              className={richtung === "ein" ? "richtung-aktiv" : ""}
              onClick={() => setRichtung("ein")}
            >
              Ziel → {eigenName}
            </button>
          </div>
        </div>

        <div>
          <label className="pcd-label">Beschreibung (optional)</label>
          <textarea
            className="ziel-textarea"
            placeholder="Worum geht es bei dieser Verbindung?"
            value={beschreibung}
            onChange={(e) => setBeschreibung(e.target.value)}
          />
        </div>

        <VisibilitySelector
          label="Sichtbarkeit der Verbindung"
          modus={sichtbarkeit}
          sichtbarFuer={sichtbarFuer}
          onChange={(m, f) => {
            setSichtbarkeit(m);
            setSichtbarFuer(f);
          }}
          pcOptions={pcOptions}
        />

        <div className="ziel-editor-aktionen">
          <button type="button" className="pcd-abbrechen" onClick={onSchliessen}>
            Abbrechen
          </button>
          <button
            type="button"
            className="pcd-speichern"
            onClick={speichern}
            disabled={speichert || !zielId || !typ.trim()}
          >
            {speichert ? "Legt an…" : "Verbindung anlegen"}
          </button>
        </div>
      </div>
    </Fenster>
  );
}
