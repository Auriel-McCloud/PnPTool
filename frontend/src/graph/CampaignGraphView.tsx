import cytoscape from "cytoscape";
import { useEffect, useRef, useState } from "react";
import { getGraph } from "./api";
import { tokens } from "../theme/theme";

const KIND_SHAPE: Record<string, string> = {
  Person: "ellipse",
  Ort: "round-rectangle",
  Event: "diamond",
  Gegenstand: "star",
};

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
    </div>
  );
}
