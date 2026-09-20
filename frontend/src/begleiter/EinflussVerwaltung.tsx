import { useMemo, useState } from "react";
import { entitiesApi } from "../entities/api";
import { itemsApi } from "../items/api";
import { DotPool } from "../traits/DotPool";
import { begleiterApi, type Begleiter, type EinflussZielKind } from "./api";

/** Anzeigesymbol je Zielart — dieselben Symbole wie in den jeweiligen
 * Commlink-Bereichen (App.tsx/ZielAuswahl in PartyVerwaltung.tsx). */
const ZIEL_SYMBOLE: Record<EinflussZielKind, string> = {
  Ort: "⌖",
  Fraktion: "⬡",
  Event: "◆",
  Gegenstand: "◈",
};

const ZIEL_NAMEN: Record<EinflussZielKind, string> = {
  Ort: "Ort",
  Fraktion: "Fraktion",
  Event: "Event",
  Gegenstand: "Gegenstand",
};

interface WaehlbaresZiel {
  kind: EinflussZielKind;
  id: string;
  name: string;
}

/**
 * Einfluss-Verwaltung einer KI: welche Orte/Fraktionen/Events/Gegenstände sie
 * kontrolliert, mit Stufe je Ziel — echte Graphkanten statt Freitext (Mark,
 * 19.09.2026: "damit kann die SL ihr im Kampf gezielt einen echten Ort
 * wegnehmen"). Nur die Spielleitung bearbeitet das; Spieler sehen die Liste
 * nur an, siehe `EinflussAnzeige` weiter unten.
 */
export function EinflussVerwaltung({
  campaignId,
  begleiter,
  onGeaendert,
}: {
  campaignId: string;
  begleiter: Begleiter;
  onGeaendert: (neu: Begleiter) => void;
}) {
  const [ziele, setZiele] = useState<WaehlbaresZiel[] | null>(null);
  const [suche, setSuche] = useState("");
  const [ladeFehler, setLadeFehler] = useState<string | null>(null);

  // Erst beim Aufklappen laden — die vier Listen zusammen können in einer
  // großen Kampagne beträchtlich sein, und die meisten Begleiter sind keine
  // KI und brauchen das nie.
  async function ladenFallsNoetig() {
    if (ziele !== null) return;
    try {
      const [orte, fraktionen, events, gegenstaende] = await Promise.all([
        entitiesApi.listOrte(campaignId),
        entitiesApi.listFraktionen(campaignId),
        entitiesApi.listEvents(campaignId),
        itemsApi.listAlle(campaignId),
      ]);
      setZiele([
        ...orte.map((o) => ({ kind: "Ort" as const, id: o.id, name: o.name })),
        ...fraktionen.map((f) => ({ kind: "Fraktion" as const, id: f.id, name: f.name })),
        ...events.map((e) => ({ kind: "Event" as const, id: e.id, name: e.title })),
        ...gegenstaende.map((g) => ({ kind: "Gegenstand" as const, id: g.id, name: g.name })),
      ]);
    } catch {
      setLadeFehler("Ziele konnten nicht geladen werden.");
    }
  }

  const bereitsVerknuepft = new Set(begleiter.einfluss.map((e) => `${e.zielKind}:${e.zielId}`));
  const suchNorm = suche.trim().toLowerCase();
  const waehlbar = useMemo(() => {
    if (!ziele) return [];
    return ziele.filter((z) => {
      if (bereitsVerknuepft.has(`${z.kind}:${z.id}`)) return false;
      if (!suchNorm) return true;
      return z.name.toLowerCase().includes(suchNorm) || ZIEL_NAMEN[z.kind].toLowerCase().includes(suchNorm);
    });
  }, [ziele, suchNorm, begleiter.einfluss]);

  async function hinzufuegen(ziel: WaehlbaresZiel) {
    const neu = await begleiterApi.einflussSetzen(campaignId, begleiter.id, ziel.kind, ziel.id, 1);
    onGeaendert(neu);
  }

  async function stufeAendern(zielKind: EinflussZielKind, zielId: string, stufe: number) {
    if (stufe <= 0) {
      const neu = await begleiterApi.einflussEntfernen(campaignId, begleiter.id, zielKind, zielId);
      onGeaendert(neu);
      return;
    }
    const neu = await begleiterApi.einflussSetzen(campaignId, begleiter.id, zielKind, zielId, stufe);
    onGeaendert(neu);
  }

  async function entfernen(zielKind: EinflussZielKind, zielId: string) {
    const neu = await begleiterApi.einflussEntfernen(campaignId, begleiter.id, zielKind, zielId);
    onGeaendert(neu);
  }

  return (
    <section>
      <h3 style={{ margin: "0 0 6px" }}>Einfluss</h3>
      <p className="pcd-hinweis" style={{ marginBottom: 8 }}>
        Echte Verknüpfungen zu Orten, Fraktionen, Events und Gegenständen — im Kampf gezielt entziehbar.
      </p>

      {begleiter.einfluss.length === 0 && (
        <p className="gg-leer" style={{ marginBottom: 8 }}>
          Kontrolliert noch nichts.
        </p>
      )}

      {begleiter.einfluss.map((e) => (
        <div key={`${e.zielKind}:${e.zielId}`} className="bg-wert" style={{ marginBottom: 4 }}>
          <span>
            {ZIEL_SYMBOLE[e.zielKind]} {e.zielName}{" "}
            <em style={{ color: "var(--text-leise)", fontStyle: "normal", fontSize: 12 }}>
              {ZIEL_NAMEN[e.zielKind]}
            </em>
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <DotPool value={e.stufe} max={6} onChange={(w) => stufeAendern(e.zielKind, e.zielId, w)} />
            <button
              type="button"
              className="ziel-wegwerfen"
              title="Einfluss ganz entziehen"
              onClick={() => entfernen(e.zielKind, e.zielId)}
            >
              ✕
            </button>
          </span>
        </div>
      ))}

      <details style={{ marginTop: 8 }} onToggle={(e) => e.currentTarget.open && ladenFallsNoetig()}>
        <summary className="ziel-neu" style={{ display: "inline-block", cursor: "pointer" }}>
          + Einfluss hinzufügen
        </summary>
        <div style={{ marginTop: 8 }}>
          {ladeFehler && <p style={{ color: "var(--signal)" }}>{ladeFehler}</p>}
          {ziele === null && !ladeFehler && <p className="pcd-hinweis">Lädt…</p>}
          {ziele !== null && (
            <>
              <input
                type="search"
                className="pt-suchfeld"
                placeholder="Suchen — Name oder Art…"
                value={suche}
                onChange={(e) => setSuche(e.target.value)}
                style={{ marginBottom: 6 }}
              />
              <div className="pt-auswahl-liste">
                {waehlbar.length === 0 && <p className="pt-hinweis">Nichts gefunden.</p>}
                {waehlbar.map((z) => (
                  <button
                    key={`${z.kind}:${z.id}`}
                    type="button"
                    className="pt-auswahl-zeile pt-auswahl-hinzufuegen"
                    onClick={() => hinzufuegen(z)}
                  >
                    <span>
                      {ZIEL_SYMBOLE[z.kind]} {z.name}
                    </span>
                    <em className="pt-typ">{ZIEL_NAMEN[z.kind]}</em>
                    <span className="pt-plus" aria-hidden="true">
                      +
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </details>
    </section>
  );
}

/** Reine Anzeige für Spieler/Nicht-Bearbeiten-Kontexte — keine Aktionen. */
export function EinflussAnzeige({ begleiter }: { begleiter: Begleiter }) {
  if (begleiter.einfluss.length === 0) return null;
  return (
    <section>
      <h3 style={{ margin: "0 0 6px" }}>Einfluss</h3>
      {begleiter.einfluss.map((e) => (
        <div key={`${e.zielKind}:${e.zielId}`} className="bg-wert">
          <span>
            {ZIEL_SYMBOLE[e.zielKind]} {e.zielName}
          </span>
          <DotPool value={e.stufe} max={6} />
        </div>
      ))}
    </section>
  );
}
