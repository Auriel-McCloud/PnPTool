import { useState } from "react";
import type { EntityKind, Fraktion, Verbindung, ZielEintrag } from "./api";
import { entitiesApi } from "./api";
import { BildGalerie } from "./BildGalerie";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { parseRichText, serializeRichText } from "../richtext/content";
import { BeziehungsListe, beziehungsZeilen } from "./BeziehungsListe";
import type { JSONContent } from "@tiptap/react";
import "./pc-detail.css"; // Selbes Popup-Gerüst wie bei PCs und NPCs

/**
 * Detail-Popup für eine Fraktion.
 *
 * Gleiches Bedienkonzept wie PCDetail/NPCDetail/OrtDetail: Navigation oben,
 * Übersicht mit Bild und Schnellzugriff, dann die einzelnen Bereiche.
 * Fraktionen haben zusätzlich Ziele und Ressourcen als eigene Felder.
 */

type Unteransicht = "uebersicht" | "beschreibung" | "ziele" | "ressourcen" | "notizen" | "beziehungen";

interface FraktionDetailProps {
  campaignId: string;
  fraktion: Fraktion;
  /** Alle sichtbaren Verbindungen der Kampagne — gefiltert wird hier. */
  verbindungen: Verbindung[];
  /** ID → Name/Art für die Gegenseiten; muss sichtbarkeitsgefiltert sein. */
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}

export function FraktionDetail({
  campaignId,
  fraktion,
  verbindungen,
  namen,
  pcOptions,
  onSchliessen,
  onGeaendert,
}: FraktionDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [name, setName] = useState(fraktion.name);
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(fraktion.description));
  const [ziele, setZiele] = useState<ZielEintrag[]>(fraktion.ziele ?? []);
  const [offenesZiel, setOffenesZiel] = useState<number | null>(null);
  const [ressourcenDoc, setRessourcenDoc] = useState<JSONContent>(parseRichText(fraktion.ressourcen));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(fraktion.notes));
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  const zeilen = beziehungsZeilen(fraktion.id, verbindungen, namen);

  async function speichere(felder: Partial<Fraktion>) {
    setSpeichert(true);
    setFehler(null);
    try {
      await entitiesApi.updateFraktion(campaignId, fraktion.id, felder);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setSpeichert(false);
    }
  }

  async function loeschen() {
    setSpeichert(true);
    try {
      await entitiesApi.deleteFraktion(campaignId, fraktion.id);
      setLoeschenOffen(false);
      onGeaendert();
      onSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
      setLoeschenOffen(false);
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <Fenster
      offen
      breit={unteransicht === "beziehungen"}
      titel={fraktion.name}
      unterzeile="Fraktion"
      kennung={`fraktion-detail:${fraktion.id}`}
      ton="var(--bereich-fraktionen)"
      onSchliessen={onSchliessen}
    >
      <div className="pcd-inhalt">
        <nav className="pcd-nav pcd-nav-fraktionen">
          {(
            [
              ["uebersicht", "Übersicht"],
              ["beschreibung", "Beschreibung"],
              ["ziele", "Ziele"],
              ["ressourcen", "Ressourcen"],
              ["notizen", "Notizen"],
              ["beziehungen", `Beziehungen (${zeilen.length})`],
            ] as [Unteransicht, string][]
          ).map(([wert, text]) => (
            <button
              key={wert}
              type="button"
              className={unteransicht === wert ? "pcd-nav-aktiv" : ""}
              onClick={() => setUnteransicht(wert)}
            >
              {text}
            </button>
          ))}
        </nav>

        <div className="pcd-bereich">
          {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

          {unteransicht === "uebersicht" && (
            <div className="pcd-uebersicht">
              <div className="pcd-bild-bereich">
                <BildGalerie
                  campaignId={campaignId}
                  art="fraktionen"
                  id={fraktion.id}
                  name={fraktion.name}
                  bilder={fraktion.bilder || []}
                  bildUrl={fraktion.bildUrl}
                  onGeaendert={onGeaendert}
                />
              </div>
              <div className="pcd-schnellzugriff">
                <div className="pcd-feld">
                  <label htmlFor={`fraktion-name-${fraktion.id}`}>Name</label>
                  <input
                    id={`fraktion-name-${fraktion.id}`}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onBlur={() => {
                      const sauber = name.trim();
                      // Leerer Name würde die Fraktion in jeder Liste unauffindbar
                      // machen — dann lieber den alten behalten.
                      if (!sauber) {
                        setName(fraktion.name);
                        return;
                      }
                      if (sauber !== fraktion.name) speichere({ name: sauber });
                    }}
                  />
                </div>

                <VisibilitySelector
                  label="Sichtbarkeit der Beschreibung"
                  modus={fraktion.sichtbarkeit}
                  sichtbarFuer={fraktion.sichtbarFuer}
                  onChange={(m, f) => speichere({ sichtbarkeit: m, sichtbarFuer: f })}
                  pcOptions={pcOptions}
                />
                <VisibilitySelector
                  label="Sichtbarkeit der Notizen"
                  modus={fraktion.notizenSichtbarkeit}
                  sichtbarFuer={fraktion.notizenSichtbarFuer}
                  onChange={(m, f) => speichere({ notizenSichtbarkeit: m, notizenSichtbarFuer: f })}
                  pcOptions={pcOptions}
                />

                <div className="pcd-buttons" style={{ marginTop: 12 }}>
                  <button type="button" onClick={() => setUnteransicht("beschreibung")}>
                    📝 Beschreibung bearbeiten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("ziele")}>
                    🎯 Ziele bearbeiten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("ressourcen")}>
                    💎 Ressourcen bearbeiten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("beziehungen")}>
                    ⬡ Beziehungen ansehen ({zeilen.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setLoeschenOffen(true)}
                    style={{ color: "var(--signal)", borderColor: "var(--signal)" }}
                  >
                    🗑 Fraktion löschen
                  </button>
                </div>
              </div>
            </div>
          )}

          {unteransicht === "beschreibung" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor content={beschreibungDoc} onChange={setBeschreibungDoc} minHeight={200} />
              <button
                type="button"
                className="pcd-speichern"
                onClick={() => speichere({ description: serializeRichText(beschreibungDoc) })}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Beschreibung speichern"}
              </button>
            </div>
          )}

          {unteransicht === "ziele" && (
            <div className="pcd-editor-bereich">
              <p className="pcd-hinweis">
                Was die Fraktion vorhat — freundliche Übernahme, Putsch, Expansion, Marktdominanz.
              </p>

              <div className="ziel-liste">
                {ziele.length === 0 && (
                  <p style={{ color: "var(--text-leise)", fontStyle: "italic" }}>
                    Noch keine Ziele. Leg eins an — jedes Ziel hat eine Kurzbeschreibung und,
                    bei Bedarf, eine ausformulierte Beschreibung.
                  </p>
                )}

                {ziele.map((ziel, i) => (
                  <div key={i} className="ziel-eintrag">
                    <button
                      type="button"
                      className="ziel-titel-zeile"
                      onClick={() => setOffenesZiel(offenesZiel === i ? null : i)}
                    >
                      <span className="ziel-aufklapp">{offenesZiel === i ? "▾" : "▸"}</span>
                      <span className="ziel-titel">{ziel.titel.trim() || "Unbenanntes Ziel"}</span>
                      <span
                        className="ziel-wegwerfen"
                        title="Ziel entfernen"
                        onClick={(e) => {
                          e.stopPropagation();
                          const neue = ziele.filter((_, k) => k !== i);
                          setZiele(neue);
                          if (offenesZiel === i) setOffenesZiel(null);
                          speichere({ ziele: neue });
                        }}
                      >
                        ✕
                      </span>
                    </button>

                    {offenesZiel === i && (
                      <div className="ziel-detail">
                        <label className="pcd-label">Kurzbeschreibung</label>
                        <input
                          type="text"
                          className="ziel-input"
                          placeholder="z.B. Freundliche Übernahme der Hafenlogistik"
                          value={ziel.titel}
                          onChange={(e) => {
                            const neue = [...ziele];
                            neue[i] = { ...ziel, titel: e.target.value };
                            setZiele(neue);
                          }}
                          onBlur={() => speichere({ ziele })}
                        />
                        <label className="pcd-label">Beschreibung</label>
                        <textarea
                          className="ziel-textarea"
                          placeholder="Ausführlich: warum, wie, womit, bis wann …"
                          value={ziel.beschreibung}
                          onChange={(e) => {
                            const neue = [...ziele];
                            neue[i] = { ...ziel, beschreibung: e.target.value };
                            setZiele(neue);
                          }}
                          onBlur={() => speichere({ ziele })}
                        />
                      </div>
                    )}
                  </div>
                ))}

                <button
                  type="button"
                  className="ziel-neu"
                  onClick={() => {
                    const neue = [...ziele, { titel: "", beschreibung: "" }];
                    setZiele(neue);
                    setOffenesZiel(neue.length - 1);
                  }}
                >
                  + Neues Ziel
                </button>
              </div>

              <button
                type="button"
                className="pcd-speichern"
                onClick={() => speichere({ ziele })}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Ziele speichern"}
              </button>
            </div>
          )}

          {unteransicht === "ressourcen" && (
            <div className="pcd-editor-bereich">
              <p className="pcd-hinweis">
                Miliz, Kapital, Zugang, Technologie — was die Fraktion einsetzen kann.
              </p>
              <RichTextEditor content={ressourcenDoc} onChange={setRessourcenDoc} minHeight={200} />
              <button
                type="button"
                className="pcd-speichern"
                onClick={() => speichere({ ressourcen: serializeRichText(ressourcenDoc) })}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Ressourcen speichern"}
              </button>
            </div>
          )}

          {unteransicht === "notizen" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor content={notizenDoc} onChange={setNotizenDoc} minHeight={200} />
              <button
                type="button"
                className="pcd-speichern"
                onClick={() => speichere({ notes: serializeRichText(notizenDoc) })}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Notizen speichern"}
              </button>
            </div>
          )}

          {unteransicht === "beziehungen" && (
            <BeziehungsListe
              campaignId={campaignId}
              zeilen={zeilen}
              onGeaendert={onGeaendert}
              farbe="var(--bereich-fraktionen, var(--neon))"
            />
          )}
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel="Fraktion löschen?"
          text={`„${fraktion.name}" wird endgültig entfernt, samt aller ${zeilen.length} Verbindungen. Das lässt sich nicht rückgängig machen.`}
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
