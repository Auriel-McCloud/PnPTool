import { useState } from "react";
import type { EntityKind, SichtbarkeitModus, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { Fenster } from "../shell/Fenster";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import "./pc-detail.css";

/**
 * Korrigiert Typ, Beschreibung und Sichtbarkeit einer bestehenden Kante.
 *
 * Endpunkte bleiben absichtlich unveränderlich — wer die Beteiligten
 * tauschen will, löst die Verbindung und legt neu an.
 */

const KIND_LABEL: Record<EntityKind, string> = {
  Person: "Person",
  Ort: "Ort",
  Event: "Event",
  Fraktion: "Fraktion",
  Gegenstand: "Gegenstand",
};

interface VerbindungBearbeitenProps {
  campaignId: string;
  verbindung: Verbindung;
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  farbe?: string;
  onGeaendert: () => void;
  onSchliessen: () => void;
}

export function VerbindungBearbeiten({
  campaignId,
  verbindung,
  namen,
  pcOptions,
  farbe = "var(--neon)",
  onGeaendert,
  onSchliessen,
}: VerbindungBearbeitenProps) {
  const [typ, setTyp] = useState(verbindung.typ);
  const [letzterTyp, setLetzterTyp] = useState(verbindung.typ);
  const [beschreibung, setBeschreibung] = useState(verbindung.beschreibung);
  const [letzteBeschreibung, setLetzteBeschreibung] = useState(verbindung.beschreibung);
  const [sichtbarkeit, setSichtbarkeit] = useState<SichtbarkeitModus>(verbindung.sichtbarkeit);
  const [sichtbarFuer, setSichtbarFuer] = useState<string[]>(verbindung.sichtbarFuer);
  const [fehler, setFehler] = useState<string | null>(null);

  const von = namen.get(verbindung.vonId);
  const zu = namen.get(verbindung.zuId);
  const vonText = von ? `${KIND_LABEL[von.kind]}: ${von.name}` : "…";
  const zuText = zu ? `${KIND_LABEL[zu.kind]}: ${zu.name}` : "…";

  async function speichere(felder: Partial<Verbindung>) {
    setFehler(null);
    try {
      await entitiesApi.updateVerbindung(campaignId, verbindung.id, felder);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }

  return (
    <Fenster
      offen
      titel="Verbindung bearbeiten"
      unterzeile={`${vonText} → ${zuText}`}
      kennung={`verbindung-bearbeiten:${verbindung.id}`}
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
            onBlur={() => {
              const sauber = typ.trim();
              if (!sauber) {
                setTyp(letzterTyp);
                return;
              }
              if (sauber !== letzterTyp) {
                setLetzterTyp(sauber);
                setTyp(sauber);
                void speichere({ typ: sauber });
              }
            }}
          />
        </div>

        <p className="pcd-hinweis" style={{ margin: 0 }}>
          {vonText} → {zuText}. Die Endpunkte selbst ändert man, indem man die
          Verbindung löst und neu anlegt.
        </p>

        <div>
          <label className="pcd-label">Beschreibung (optional)</label>
          <textarea
            className="ziel-textarea"
            placeholder="Worum geht es bei dieser Verbindung?"
            value={beschreibung}
            onChange={(e) => setBeschreibung(e.target.value)}
            onBlur={() => {
              if (beschreibung !== letzteBeschreibung) {
                setLetzteBeschreibung(beschreibung);
                void speichere({ beschreibung });
              }
            }}
          />
        </div>

        <VisibilitySelector
          label="Sichtbarkeit der Verbindung"
          modus={sichtbarkeit}
          sichtbarFuer={sichtbarFuer}
          onChange={(m, f) => {
            setSichtbarkeit(m);
            setSichtbarFuer(f);
            void speichere({ sichtbarkeit: m, sichtbarFuer: f });
          }}
          pcOptions={pcOptions}
        />
      </div>
    </Fenster>
  );
}
