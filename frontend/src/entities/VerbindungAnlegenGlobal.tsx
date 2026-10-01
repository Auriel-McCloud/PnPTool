import { useState } from "react";
import type { EntityKind, SichtbarkeitModus, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { Fenster } from "../shell/Fenster";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { EntitaetsAuswahl } from "./EntitaetsAuswahl";
import "./pc-detail.css";

/**
 * Legt eine neue Verbindung zwischen zwei frei wählbaren Entitäten an.
 *
 * Gegenstück zu VerbindungAnlegen.tsx: dort ist ein Endpunkt fest (man kommt
 * aus einem Detail-Popup), hier sind beide frei wählbar — für die
 * eigenständige Verbindungen-Übersicht, wo man nicht erst ein Detail-Popup
 * öffnen will, nur um zwei Dinge miteinander zu verknüpfen. Beide Endpunkte
 * nutzen dieselbe durchsuchbare Auswahl wie dort, denn auch hier kommt
 * "wirklich alles" infrage.
 */
export function VerbindungAnlegenGlobal({
  campaignId,
  namen,
  pcOptions,
  farbe = "var(--bereich-verbindungen)",
  onGeaendert,
  onSchliessen,
}: {
  campaignId: string;
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  farbe?: string;
  onGeaendert: () => void;
  onSchliessen: () => void;
}) {
  const [vonId, setVonId] = useState("");
  const [zuId, setZuId] = useState("");
  const [typ, setTyp] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [sichtbarkeit, setSichtbarkeit] = useState<SichtbarkeitModus>("GM");
  const [sichtbarFuer, setSichtbarFuer] = useState<string[]>([]);
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function speichern() {
    const von = namen.get(vonId);
    const zu = namen.get(zuId);
    if (!von || !zu || !typ.trim()) return;
    setSpeichert(true);
    setFehler(null);
    try {
      const basis: Omit<Verbindung, "id"> = {
        vonKind: von.kind,
        vonId,
        zuKind: zu.kind,
        zuId,
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
      unterzeile="Zwei Entitäten miteinander verknüpfen"
      kennung="verbindung-anlegen-global"
      ton={farbe}
      onSchliessen={onSchliessen}
    >
      <div className="pcd-editor-bereich" style={{ padding: 8, "--verbindung-farbe": farbe } as React.CSSProperties}>
        {fehler && <p style={{ color: "var(--signal)", margin: 0 }}>{fehler}</p>}

        <EntitaetsAuswahl label="Von" namen={namen} value={vonId} onChange={setVonId} ausschluss={zuId || undefined} />

        <div>
          <label className="pcd-label">Beziehungstyp</label>
          <input
            type="text"
            className="ziel-input"
            placeholder="z.B. Anführer, Einfluss, Verbündeter …"
            value={typ}
            onChange={(e) => setTyp(e.target.value)}
          />
        </div>

        <EntitaetsAuswahl label="Zu" namen={namen} value={zuId} onChange={setZuId} ausschluss={vonId || undefined} />

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
            disabled={speichert || !vonId || !zuId || vonId === zuId || !typ.trim()}
          >
            {speichert ? "Legt an…" : "Verbindung anlegen"}
          </button>
        </div>
      </div>
    </Fenster>
  );
}
