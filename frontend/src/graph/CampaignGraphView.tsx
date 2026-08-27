import cytoscape from "cytoscape";
import { useEffect, useRef, useState } from "react";
import { getGraph } from "./api";

const KIND_SHAPE: Record<string, string> = {
  Person: "ellipse",
  Ort: "round-rectangle",
  Event: "diamond",
};

const KIND_COLOR: Record<string, string> = {
  Person: "#3f6fb4",
  Ort: "#2a8f5a",
  Event: "#b4703f",
};

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
      "border-color": (ele: cytoscape.NodeSingular) => (ele.data("sichtbarkeit") === "GM" ? "#a11" : "#ccc"),
    } as cytoscape.Css.Node,
  },
  {
    selector: "node:selected",
    style: { "border-width": 5, "border-color": "#ffd23f" } as cytoscape.Css.Node,
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": (ele: cytoscape.EdgeSingular) => (ele.data("sichtbarkeit") === "GM" ? "#a11" : "#999"),
      "target-arrow-color": (ele: cytoscape.EdgeSingular) => (ele.data("sichtbarkeit") === "GM" ? "#a11" : "#999"),
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(typ)",
      "font-size": 10,
      color: "#555",
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

    return () => {
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
        <p style={{ color: "crimson", border: "1px solid crimson", padding: 8, borderRadius: 4 }}>
          Fehler beim Laden des Graphen: {error}
        </p>
      )}
      {isEmpty && !error && <p>Noch keine Personen/Orte/Events angelegt.</p>}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: 520,
          border: "1px solid #ddd",
          borderRadius: 6,
          display: isEmpty ? "none" : "block",
        }}
      />
    </div>
  );
}
