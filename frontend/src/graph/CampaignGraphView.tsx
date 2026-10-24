import cytoscape from "cytoscape";
import { useCallback, useEffect, useRef, useState } from "react";
import type { EntityKind } from "../entities/api";
import { getGraph, type GraphEdge, type GraphNode } from "./api";
import { GraphOeffnen, type GraphZiel } from "./GraphOeffnen";
import { GraphFilterPanel, type KantenFilterOption, type KnotenFilterOption } from "./GraphFilterPanel";
import { KantentypenNormalisierenPopup } from "./KantentypenNormalisierenPopup";
import { tokens } from "../theme/theme";

const KIND_SHAPE: Record<string, string> = {
  Person: "ellipse",
  Ort: "round-rectangle",
  Event: "diamond",
  Gegenstand: "star",
  Fraktion: "hexagon",
  Party: "tag",
};

// Objekttyp-Filter: Personen werden in PC/NPC aufgesplittet, alles andere
// bleibt bei seiner Art — Mark will NSCs/Gegenstände/etc. unabhängig
// voneinander ausblenden können (24.10.2026).
function knotenKategorie(n: { kind: string; personType?: string | null }): string {
  if (n.kind === "Person") return n.personType === "PC" ? "Person:PC" : "Person:NPC";
  return n.kind;
}

const KATEGORIE_LABEL: Record<string, string> = {
  "Person:PC": "◌ Spielercharaktere",
  "Person:NPC": "◌ NSCs",
  Ort: "⌖ Orte",
  Event: "◆ Events",
  Fraktion: "⬡ Fraktionen",
  Gegenstand: "◈ Gegenstände",
  Party: "👥 Partys",
};

// Lokale Merkung je Kampagne — reiner Anzeige-Filter, keine Serverdaten
// betroffen. Eigener Präfix, damit eine spätere Suche nach dem Schlüssel
// nicht mit anderen localStorage-Einträgen kollidiert.
const LS_PRAEFIX = "pnptool:graph-filter:";

function filterAusStorage(schluessel: string): Set<string> {
  try {
    const roh = window.localStorage.getItem(LS_PRAEFIX + schluessel);
    if (!roh) return new Set();
    const arr = JSON.parse(roh);
    return new Set(Array.isArray(arr) ? arr.filter((x): x is string => typeof x === "string") : []);
  } catch {
    return new Set();
  }
}

function filterInStorage(schluessel: string, werte: Set<string>): void {
  try {
    window.localStorage.setItem(LS_PRAEFIX + schluessel, JSON.stringify([...werte]));
  } catch {
    // Privater Modus o.ä. — der Filter funktioniert dann nur für die Sitzung.
  }
}

// Cytoscape zeichnet auf Canvas und kennt keine CSS-Variablen. Frueher standen
// die Farben deshalb ein zweites Mal als Hexwerte hier — mit dem Hinweis "beim
// Aendern dort nachziehen". Das haelt keinen Themewechsel aus.
// Jetzt werden die Tokens zur Laufzeit aus dem aktiven Theme gelesen
// (theme/theme.ts), es gibt also weiterhin nur eine Quelle der Wahrheit.
function graphFarben() {
  const t = tokens({
    person: "--kind-person",
    ort: "--kind-ort",
    event: "--kind-event",
    gegenstand: "--kind-gegenstand",
    fraktion: "--kind-fraktion",
    party: "--kind-party",
    geheim: "--signal",
    linie: "--linie-hell",
    neon: "--neon",
    textLeise: "--text-leise",
    knotenText: "--text",
  });
  return {
    kind: {
      Person: t.person,
      Ort: t.ort,
      Event: t.event,
      Gegenstand: t.gegenstand,
      Fraktion: t.fraktion,
      Party: t.party,
    } as Record<string, string>,
    geheim: t.geheim,
    linie: t.linie,
    neon: t.neon,
    textLeise: t.textLeise,
    knotenText: t.knotenText,
  };
}

type GraphFarben = ReturnType<typeof graphFarben>;

const stylesheetFuer = (f: GraphFarben) => [
  {
    selector: "node",
    style: {
      "background-color": (ele: cytoscape.NodeSingular) => f.kind[ele.data("kind")] ?? f.linie,
      shape: (ele: cytoscape.NodeSingular) => KIND_SHAPE[ele.data("kind")] ?? "ellipse",
      label: "data(label)",
      color: f.knotenText,
      "text-outline-width": 2,
      "text-outline-color": (ele: cytoscape.NodeSingular) => f.kind[ele.data("kind")] ?? f.linie,
      "font-size": 12,
      "text-valign": "center",
      "text-halign": "center",
      width: 56,
      height: 56,
      "border-width": 3,
      "border-color": (ele: cytoscape.NodeSingular) =>
        ele.data("sichtbarkeit") === "GM" ? f.geheim : f.linie,
    } as cytoscape.Css.Node,
  },
  {
    selector: "node:selected",
    style: { "border-width": 5, "border-color": f.neon } as cytoscape.Css.Node,
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": (ele: cytoscape.EdgeSingular) =>
        ele.data("sichtbarkeit") === "GM" ? f.geheim : f.linie,
      "target-arrow-color": (ele: cytoscape.EdgeSingular) =>
        ele.data("sichtbarkeit") === "GM" ? f.geheim : f.linie,
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(typ)",
      "font-size": 10,
      color: f.textLeise,
      "text-rotation": "autorotate",
    } as cytoscape.Css.Edge,
  },
];

export function CampaignGraphView({ campaignId }: { campaignId: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [focus, setFocus] = useState<string | null>(null);
  const [focusLabel, setFocusLabel] = useState<string | null>(null);
  const [depth, setDepth] = useState(2);
  const [isEmpty, setIsEmpty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ziel, setZiel] = useState<GraphZiel | null>(null);
  const [oeffnet, setOeffnet] = useState(false);
  // Hochzählen schließt das Fenster und zeichnet den Graphen neu — Labels
  // und Kantenfarben sollen den Stand zeigen, den man gerade bearbeitet hat.
  // Nicht bei jedem Feld-Speichern: ein Layout-Sprung hinter dem offenen
  // Fenster wäre nur Ruckeln.
  const [graphStand, setGraphStand] = useState(0);
  const oeffneRef = useRef<(ziel: GraphZiel) => void>(() => {});
  oeffneRef.current = (naechstes) => {
    setError(null);
    setZiel(naechstes);
  };

  // --- Objekt-/Kantentyp-Filter (24.10.2026, Marks Wunsch) -----------------
  // Rein clientseitig: welche Objekt- und Kantentypen im Canvas ausgeblendet
  // sind. Gemerkt in localStorage je Kampagne, damit die Auswahl einen
  // Neuladen übersteht. Die rohen Knoten/Kanten der letzten Antwort stehen
  // in Refs, damit das Umschalten eines Filters ohne Serverfahrt neu
  // anwendbar ist (siehe wendeFilterAn unten).
  const [versteckteKnoten, setVersteckteKnoten] = useState<Set<string>>(() =>
    filterAusStorage(`${campaignId}:knoten`),
  );
  const [versteckteKanten, setVersteckteKanten] = useState<Set<string>>(() =>
    filterAusStorage(`${campaignId}:kanten`),
  );
  const [knotenOptionen, setKnotenOptionen] = useState<KnotenFilterOption[]>([]);
  const [kantenOptionen, setKantenOptionen] = useState<KantenFilterOption[]>([]);
  const [normalisierenOffen, setNormalisierenOffen] = useState(false);
  const letzteKnotenRef = useRef<GraphNode[]>([]);
  const letzteKantenRef = useRef<GraphEdge[]>([]);

  // Kampagnenwechsel (derselbe View bleibt eingehängt): Filter der neuen
  // Kampagne laden statt die der alten weiterzuverwenden.
  useEffect(() => {
    setVersteckteKnoten(filterAusStorage(`${campaignId}:knoten`));
    setVersteckteKanten(filterAusStorage(`${campaignId}:kanten`));
  }, [campaignId]);

  useEffect(() => {
    filterInStorage(`${campaignId}:knoten`, versteckteKnoten);
  }, [campaignId, versteckteKnoten]);

  useEffect(() => {
    filterInStorage(`${campaignId}:kanten`, versteckteKanten);
  }, [campaignId, versteckteKanten]);

  function knotenUmschalten(schluessel: string) {
    setVersteckteKnoten((alt) => {
      const neu = new Set(alt);
      if (neu.has(schluessel)) neu.delete(schluessel);
      else neu.add(schluessel);
      return neu;
    });
  }

  function kanteUmschalten(typ: string) {
    setVersteckteKanten((alt) => {
      const neu = new Set(alt);
      if (neu.has(typ)) neu.delete(typ);
      else neu.add(typ);
      return neu;
    });
  }

  function alleAnzeigen() {
    setVersteckteKnoten(new Set());
    setVersteckteKanten(new Set());
  }

  // Wendet die aktuelle Filterauswahl auf die bereits gezeichneten Elemente
  // an — ohne Serverfahrt und ohne das cose-Layout neu laufen zu lassen
  // (sonst würde jedes Umschalten einer Checkbox den ganzen Graphen
  // umsortieren). Ein ausgeblendeter Knoten blendet automatisch auch seine
  // Kanten aus, nicht nur umgekehrt — Cytoscape macht das nicht von sich aus.
  const wendeFilterAn = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const versteckteKnotenIds = new Set(
      letzteKnotenRef.current.filter((n) => versteckteKnoten.has(knotenKategorie(n.data))).map((n) => n.data.id),
    );
    cy.batch(() => {
      cy.nodes().forEach((ele) => {
        ele.style("display", versteckteKnotenIds.has(ele.data("id")) ? "none" : "element");
      });
      cy.edges().forEach((ele) => {
        const ausgeblendet =
          versteckteKanten.has(ele.data("typ")) ||
          versteckteKnotenIds.has(ele.data("source")) ||
          versteckteKnotenIds.has(ele.data("target"));
        ele.style("display", ausgeblendet ? "none" : "element");
      });
    });
  }, [versteckteKnoten, versteckteKanten]);

  // Neu anwenden, sobald sich die Auswahl ändert (z.B. Checkbox geklickt) —
  // unabhängig vom Dateneffekt unten, der nur bei echtem Neuladen läuft.
  useEffect(() => {
    wendeFilterAn();
  }, [wendeFilterAn]);

  // Create the Cytoscape instance exactly once and tear it down on unmount.
  // Driving cytoscape imperatively (instead of the react-cytoscapejs wrapper)
  // avoids the wrapper re-running the layout / losing event handlers on
  // every unrelated re-render.
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      style: stylesheetFuer(graphFarben()) as cytoscape.StylesheetStyle[],
      elements: [],
      minZoom: 0.2,
      maxZoom: 2.5,
    });

    cy.on("tap", "node", (evt) => {
      setFocus(evt.target.data("id"));
      setFocusLabel(evt.target.data("label"));
    });

    // Rechtsklick öffnet, Linksklick zoomt. Das Browser-Menü bleibt aus —
    // sonst liegt es über dem Fenster, das gerade aufgehen soll.
    const oeffne = (evt: cytoscape.EventObject, naechstes: GraphZiel) => {
      const original = evt.originalEvent;
      if (original && "preventDefault" in original) original.preventDefault();
      oeffneRef.current(naechstes);
    };
    cy.on("cxttap", "node", (evt) => {
      oeffne(evt, {
        art: "knoten",
        id: evt.target.data("id"),
        kind: evt.target.data("kind") as EntityKind,
      });
    });
    cy.on("cxttap", "edge", (evt) => {
      oeffne(evt, { art: "kante", id: evt.target.data("id") });
    });

    cyRef.current = cy;

    // Falls der Container beim cytoscape()-Aufruf noch nicht final gelayoutet ist
    // (z.B. direkt nach Tab-Wechsel oder auf schmalen/mobilen Viewports), kann die
    // interne Erstmessung zu klein/falsch ausfallen und bleibt es auch (Canvas nur
    // "halb" befüllt, Klick-Koordinaten verschoben). Doppeltes rAF erzwingt eine
    // Nachmessung, nachdem der Browser das Layout tatsächlich committed hat.
    const forceResize = () => {
      cy.resize();
      cy.fit(undefined, 30);
    };
    requestAnimationFrame(() => requestAnimationFrame(forceResize));

    window.addEventListener("resize", forceResize);
    const beobachter = new ResizeObserver(forceResize);
    beobachter.observe(containerRef.current);

    return () => {
      beobachter.disconnect();
      window.removeEventListener("resize", forceResize);
      cy.destroy();
      cyRef.current = null;
    };
  }, []);

  // Load data whenever the campaign, focus node, or neighborhood depth changes.
  useEffect(() => {
    let cancelled = false;

    getGraph(campaignId, focus ?? undefined, depth)
      .then((graph) => {
        const cy = cyRef.current;
        if (cancelled || !cy) return;

        setIsEmpty(graph.nodes.length === 0);
        setError(null);

        letzteKnotenRef.current = graph.nodes;
        letzteKantenRef.current = graph.edges;

        // Verfügbare Filteroptionen aus den tatsächlich geladenen Daten —
        // ein Filter für einen Typ, den es gar nicht gibt, wäre Rauschen
        // (dasselbe Prinzip wie Filterleiste.tsx bei den Entitätslisten).
        const knotenZaehlung = new Map<string, number>();
        for (const n of graph.nodes) {
          const schluessel = knotenKategorie(n.data);
          knotenZaehlung.set(schluessel, (knotenZaehlung.get(schluessel) ?? 0) + 1);
        }
        setKnotenOptionen(
          [...knotenZaehlung.entries()]
            .map(([schluessel, anzahl]) => ({
              schluessel,
              label: KATEGORIE_LABEL[schluessel] ?? schluessel,
              anzahl,
            }))
            .sort((a, b) => a.label.localeCompare(b.label, "de")),
        );

        const kantenZaehlung = new Map<string, number>();
        for (const e of graph.edges) {
          kantenZaehlung.set(e.data.typ, (kantenZaehlung.get(e.data.typ) ?? 0) + 1);
        }
        setKantenOptionen(
          [...kantenZaehlung.entries()]
            .map(([typ, anzahl]) => ({ typ, anzahl }))
            .sort((a, b) => a.typ.localeCompare(b.typ, "de")),
        );

        cy.resize();
        cy.elements().remove();
        cy.add([...graph.nodes, ...graph.edges]);
        cy.layout({ name: "cose", animate: false, padding: 30 }).run();
        cy.fit(undefined, 30);
        wendeFilterAn();
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unbekannter Fehler beim Laden des Graphen");
      });

    return () => {
      cancelled = true;
    };
    // wendeFilterAn bewusst nicht in der Liste: dieser Effekt soll nur bei
    // echtem Neuladen laufen, nicht bei jedem Checkbox-Klick (dafür gibt es
    // den eigenen Effekt oben, der dieselbe Funktion aufruft).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, focus, depth, graphStand]);

  // Themewechsel: Cytoscape zeichnet auf Canvas, ein Wechsel der CSS-Tokens
  // erreicht es also nicht von selbst. Der MutationObserver horcht auf
  // data-theme am <html> und schreibt das Stylesheet mit den neuen Tokens neu.
  // Ohne das bliebe der Graph nach einem Themewechsel in den alten Farben
  // stehen — genau der Fehler, den die frueher gespiegelten Hexwerte
  // unvermeidlich gemacht haetten.
  useEffect(() => {
    const beobachter = new MutationObserver(() => {
      cyRef.current?.style(stylesheetFuer(graphFarben()) as cytoscape.StylesheetStyle[]);
    });
    beobachter.observe(document.documentElement, { attributeFilter: ["data-theme"] });
    return () => beobachter.disconnect();
  }, []);

  return (
    // Fuellt die Flaeche des Bereichs (Leitprinzip "nie scrollen") statt einer
    // festen Hoehe; die Kopfzeile behaelt ihre, der Graph bekommt den Rest.
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ marginBottom: 8, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", flexShrink: 0 }}>
        {focus ? (
          <>
            <strong>Fokus: {focusLabel}</strong>
            <label>
              Tiefe:{" "}
              <select value={depth} onChange={(e) => setDepth(Number(e.target.value))}>
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
              </select>
            </label>
            <button type="button" onClick={() => setFocus(null)}>
              Zurück zur Gesamtübersicht
            </button>
            <span style={{ color: "var(--text-leise)" }}>Rechtsklick öffnet Objekt oder Kante</span>
          </>
        ) : (
          <span>
            Gesamtübersicht — Linksklick zoomt in die Nachbarschaft, Rechtsklick öffnet das Objekt oder die Kante
          </span>
        )}
        {oeffnet && <span style={{ color: "var(--text-leise)" }}>Öffne…</span>}
        <div style={{ marginLeft: "auto" }}>
          <GraphFilterPanel
            knotenOptionen={knotenOptionen}
            kantenOptionen={kantenOptionen}
            versteckteKnoten={versteckteKnoten}
            versteckteKanten={versteckteKanten}
            onKnotenUmschalten={knotenUmschalten}
            onKanteUmschalten={kanteUmschalten}
            onAlleAnzeigen={alleAnzeigen}
            onNormalisieren={() => setNormalisierenOffen(true)}
          />
        </div>
      </div>

      {error && (
        <p style={{ color: "var(--signal)", border: "1px solid var(--signal)", padding: 8, borderRadius: 4 }}>
          Fehler beim Laden des Graphen: {error}
        </p>
      )}
      {isEmpty && !error && <p>Noch keine Personen/Orte/Events angelegt.</p>}
      <div
        ref={containerRef}
        onContextMenu={(e) => e.preventDefault()}
        style={{
          width: "100%",
          flex: 1,
          minHeight: 0,
          // Neonröhre als Begrenzung, siehe .cl-roehre in shell/commlink.css.
          // --bereich-farbe kommt aus der Hülle (hier das Blau der Beziehungen).
          border: "1px solid var(--bereich-farbe, var(--neon))",
          boxShadow:
            "0 0 10px -4px var(--bereich-farbe, var(--neon)), inset 0 0 20px -12px var(--bereich-farbe, var(--neon))",
          borderRadius: 6,
          display: isEmpty ? "none" : "block",
          position: "relative",
          overflow: "hidden",
          // Die Hülle unterbindet Zoom-Gesten (touch-action: pan-x pan-y),
          // hier werden sie aber gebraucht. "none" heisst: der Browser fasst
          // die Gesten gar nicht an, Cytoscape wertet sie selbst aus.
          // Cytoscape setzt das NICHT selbst — es tut das nur auf alten
          // Microsoft-Browsern, sonst steht dort "auto".
          touchAction: "none",
          // Absicherung, siehe Stolperstein 8 in CLAUDE.md: Cytoscapes
          // Canvas-Layer sind position:absolute mit left/right:auto und erben
          // damit text-align — bei "center" rutscht die gesamte Zeichenfläche
          // zur Seite (linke Hälfte leer, Klicks versetzt). Die Ursache von
          // damals (#root { text-align: center }) ist mit dem Commlink-Theme
          // entfallen, das hier bleibt als Schutz falls es wiederkehrt.
          textAlign: "left",
        }}
      />
      {ziel && (
        <GraphOeffnen
          key={`${ziel.art}:${ziel.id}`}
          campaignId={campaignId}
          ziel={ziel}
          onLadend={setOeffnet}
          onFehler={(meldung) => {
            setError(meldung);
            setOeffnet(false);
            setZiel(null);
          }}
          onSchliessen={() => {
            setOeffnet(false);
            setZiel(null);
            setGraphStand((n) => n + 1);
          }}
        />
      )}
      <KantentypenNormalisierenPopup
        offen={normalisierenOffen}
        campaignId={campaignId}
        onSchliessen={() => setNormalisierenOffen(false)}
        onUebernommen={() => setGraphStand((n) => n + 1)}
      />
    </div>
  );
}
