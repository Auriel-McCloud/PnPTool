import cytoscape from "cytoscape";
import { useEffect, useRef, useState } from "react";
import { getGraph } from "./api";

const KIND_SHAPE: Record<string, string> = {
  Person: "ellipse",
  Ort: "round-rectangle",
  Event: "diamond",
  Gegenstand: "star",
};

// Cytoscape zeichnet auf Canvas und kennt keine CSS-Variablen — diese Werte
// müssen die Entsprechungen aus index.css (--kind-*) von Hand spiegeln.
// Beim Ändern dort also auch hier nachziehen.
const KIND_COLOR: Record<string, string> = {
  Person: "#4d8bd8",
  Ort: "#2fa96a",
  Event: "#d4894b",
  Gegenstand: "#a865d8",
};

const FARBE_GEHEIM = "#ff2d95"; // --signal
const FARBE_LINIE = "#3a3a52"; // --linie-hell, gedämpft für Kanten
const FARBE_NEON = "#00e5ff"; // --neon, Auswahl
const FARBE_TEXT_LEISE = "#9a9ab2"; // --text-leise, Kantenbeschriftung

const stylesheet = [
  {
    selector: "node",
    style: {
      "background-color": (ele: cytoscape.NodeSingular) => KIND_COLOR[ele.data("kind")] ?? "#888",
      shape: (ele: cytoscape.NodeSingular) => KIND_SHAPE[ele.data("kind")] ?? "ellipse",
      label: "data(label)",
      color: "#fff",
      "text-outline-width": 2,
      "text-outline-color": (ele: cytoscape.NodeSingular) => KIND_COLOR[ele.data("kind")] ?? "#888",
      "font-size": 12,
      "text-valign": "center",
      "text-halign": "center",
      width: 56,
      height: 56,
      "border-width": 3,
      "border-color": (ele: cytoscape.NodeSingular) =>
        ele.data("sichtbarkeit") === "GM" ? FARBE_GEHEIM : FARBE_LINIE,
    } as cytoscape.Css.Node,
  },
  {
    selector: "node:selected",
    style: { "border-width": 5, "border-color": FARBE_NEON } as cytoscape.Css.Node,
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": (ele: cytoscape.EdgeSingular) =>
        ele.data("sichtbarkeit") === "GM" ? FARBE_GEHEIM : FARBE_LINIE,
      "target-arrow-color": (ele: cytoscape.EdgeSingular) =>
        ele.data("sichtbarkeit") === "GM" ? FARBE_GEHEIM : FARBE_LINIE,
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(typ)",
      "font-size": 10,
      color: FARBE_TEXT_LEISE,
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

  // Create the Cytoscape instance exactly once and tear it down on unmount.
  // Driving cytoscape imperatively (instead of the react-cytoscapejs wrapper)
  // avoids the wrapper re-running the layout / losing event handlers on
  // every unrelated re-render.
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      style: stylesheet as cytoscape.StylesheetStyle[],
      elements: [],
      minZoom: 0.2,
      maxZoom: 2.5,
    });

    cy.on("tap", "node", (evt) => {
      setFocus(evt.target.data("id"));
      setFocusLabel(evt.target.data("label"));
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

    return () => {
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

        cy.resize();
        cy.elements().remove();
        cy.add([...graph.nodes, ...graph.edges]);
        cy.layout({ name: "cose", animate: false, padding: 30 }).run();
        cy.fit(undefined, 30);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unbekannter Fehler beim Laden des Graphen");
      });

    return () => {
      cancelled = true;
    };
  }, [campaignId, focus, depth]);

  return (
    <div>
      <div style={{ marginBottom: 8, display: "flex", gap: 12, alignItems: "center" }}>
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
          </>
        ) : (
          <span>Gesamtübersicht — klick auf eine Person/Ort/Event für die Nachbarschaftsansicht</span>
        )}
      </div>

      {error && (
        <p style={{ color: "var(--signal)", border: "1px solid var(--signal)", padding: 8, borderRadius: 4 }}>
          Fehler beim Laden des Graphen: {error}
        </p>
      )}
      {isEmpty && !error && <p>Noch keine Personen/Orte/Events angelegt.</p>}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: 520,
          border: "1px solid var(--linie)",
          borderRadius: 6,
          display: isEmpty ? "none" : "block",
          position: "relative",
          overflow: "hidden",
          // Absicherung, siehe Stolperstein 8 in CLAUDE.md: Cytoscapes
          // Canvas-Layer sind position:absolute mit left/right:auto und erben
          // damit text-align — bei "center" rutscht die gesamte Zeichenfläche
          // zur Seite (linke Hälfte leer, Klicks versetzt). Die Ursache von
          // damals (#root { text-align: center }) ist mit dem Commlink-Theme
          // entfallen, das hier bleibt als Schutz falls es wiederkehrt.
          textAlign: "left",
        }}
      />
    </div>
  );
}
