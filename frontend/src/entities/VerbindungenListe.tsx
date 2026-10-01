import { useState } from "react";
import type { EntityKind, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { Bestaetigung } from "../shell/Bestaetigung";
import { VerbindungBearbeiten } from "./VerbindungBearbeiten";
import type { PersonOption } from "./VisibilitySelector";
import "./filterleiste.css";

/**
 * Eigenständige Verbindungen-Übersicht: Suchleiste über allen Kanten,
 * darunter die Liste mit Bearbeiten/Lösen. Anlegen läuft über den
 * "+ Neue Verbindung"-Knopf im Kopf der Ansicht (siehe EntityManager),
 * der das Auswahl-Popup VerbindungAnlegenGlobal öffnet.
 *
 * Gleiches Bedienkonzept wie Filterleiste.tsx, aber ohne Backend-Rundreise:
 * die Verbindungen sind ohnehin schon alle geladen, Suche filtert nur lokal.
 */

const ART_SYMBOL: Record<string, string> = {
  Person: "◌",
  Ort: "⌖",
  Event: "◆",
  Gegenstand: "◈",
  Fraktion: "⬡",
};

interface VerbindungsZeile {
  verbindung: Verbindung;
  von: { name: string; kind: EntityKind };
  zu: { name: string; kind: EntityKind };
}

export function VerbindungenListe({
  campaignId,
  verbindungen,
  namen,
  pcOptions,
  onGeaendert,
  farbe = "var(--bereich-verbindungen)",
}: {
  campaignId: string;
  verbindungen: Verbindung[];
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onGeaendert: () => void;
  farbe?: string;
}) {
  const [suche, setSuche] = useState("");
  const [loeschKandidat, setLoeschKandidat] = useState<VerbindungsZeile | null>(null);
  const [bearbeiten, setBearbeiten] = useState<Verbindung | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  const zeilen: VerbindungsZeile[] = [];
  for (const v of verbindungen) {
    const von = namen.get(v.vonId);
    const zu = namen.get(v.zuId);
    // Ohne beide Namen nicht anzeigen: eine Seite ist dann für diesen
    // Blickwinkel unsichtbar, eine Zeile mit roher ID verriete ihre Existenz.
    if (!von || !zu) continue;
    zeilen.push({ verbindung: v, von, zu });
  }
  zeilen.sort(
    (a, b) => a.verbindung.typ.localeCompare(b.verbindung.typ, "de") || a.von.name.localeCompare(b.von.name, "de"),
  );

  const sucheNorm = suche.trim().toLowerCase();
  const gefiltert = sucheNorm
    ? zeilen.filter((z) =>
        [z.von.name, z.zu.name, z.verbindung.typ, z.verbindung.beschreibung].join(" ").toLowerCase().includes(sucheNorm),
      )
    : zeilen;

  async function loesen() {
    if (!loeschKandidat) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await entitiesApi.deleteVerbindung(campaignId, loeschKandidat.verbindung.id);
      setLoeschKandidat(null);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verbindung konnte nicht gelöst werden");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div className="fl-leiste" style={{ ["--fl-farbe" as string]: farbe }}>
        <div className="fl-zeile">
          <div className="fl-suchfeld">
            <span className="fl-lupe" aria-hidden="true">
              ⌕
            </span>
            <input
              type="search"
              value={suche}
              onChange={(e) => setSuche(e.target.value)}
              placeholder="Suchen — Name, Typ, Beschreibung…"
              aria-label="Verbindungen durchsuchen"
            />
            {suche && (
              <button type="button" className="fl-loeschen" onClick={() => setSuche("")} title="Suche leeren">
                ✕
              </button>
            )}
          </div>
        </div>
        <div className="fl-fuss">
          <span className="fl-treffer mono">
            {gefiltert.length} {gefiltert.length === 1 ? "Verbindung" : "Verbindungen"}
            {sucheNorm && ` (gefiltert von ${zeilen.length})`}
          </span>
          {sucheNorm && (
            <button type="button" className="fl-zuruecksetzen" onClick={() => setSuche("")}>
              Suche zurücksetzen
            </button>
          )}
        </div>
      </div>

      {gefiltert.length === 0 && (
        <p style={{ color: "var(--text-leise)", fontStyle: "italic" }}>
          {zeilen.length === 0
            ? "Noch keine Verbindungen angelegt. Oben rechts anlegen."
            : `Keine Verbindung passt zu „${suche.trim()}".`}
        </p>
      )}

      {gefiltert.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 }}>
          {gefiltert.map((z) => (
            <li
              key={z.verbindung.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                flexWrap: "wrap",
                padding: "8px 10px",
                background: "var(--flaeche)",
                border: "1px solid var(--linie)",
                borderRadius: "var(--radius)",
              }}
            >
              <span style={{ minWidth: 0, overflowWrap: "break-word" }}>
                {ART_SYMBOL[z.von.kind] ?? "·"} {z.von.name}
              </span>
              <strong style={{ color: farbe }}>— {z.verbindung.typ} →</strong>
              <span style={{ minWidth: 0, overflowWrap: "break-word" }}>
                {ART_SYMBOL[z.zu.kind] ?? "·"} {z.zu.name}
              </span>
              {z.verbindung.sichtbarkeit === "GM" && (
                <span title="Nur für die Spielleitung sichtbar" style={{ fontSize: "0.8rem", color: "var(--text-leise)" }}>
                  SL
                </span>
              )}
              <button
                type="button"
                onClick={() => setBearbeiten(z.verbindung)}
                title="Verbindung bearbeiten"
                style={{ marginLeft: "auto", minHeight: 0, padding: "4px 10px", fontSize: 12 }}
              >
                Bearbeiten
              </button>
              <button
                type="button"
                onClick={() => setLoeschKandidat(z)}
                title="Verbindung lösen"
                style={{ minHeight: 0, padding: "4px 10px", fontSize: 12, color: "var(--signal)" }}
              >
                Lösen
              </button>
            </li>
          ))}
        </ul>
      )}

      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

      {bearbeiten && (
        <VerbindungBearbeiten
          campaignId={campaignId}
          verbindung={bearbeiten}
          namen={namen}
          pcOptions={pcOptions}
          farbe={farbe}
          onGeaendert={onGeaendert}
          onSchliessen={() => setBearbeiten(null)}
        />
      )}

      {/* Rückfrage wie überall im Werkzeug — eine gelöste Verbindung ist
          nicht wiederherstellbar. */}
      {loeschKandidat && (
        <Bestaetigung
          titel="Verbindung lösen?"
          text={`„${loeschKandidat.verbindung.typ}" zwischen ${loeschKandidat.von.name} und ${loeschKandidat.zu.name} wird entfernt. Die Entitäten selbst bleiben bestehen.`}
          jaText={laeuft ? "Löst…" : "Ja, lösen"}
          neinText="Abbrechen"
          onJa={loesen}
          onNein={() => setLoeschKandidat(null)}
        />
      )}
    </div>
  );
}
