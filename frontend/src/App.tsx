import { useState, type FormEvent } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { GmLoginPage } from "./auth/GmLoginPage";
import { ViewAsSwitcher } from "./auth/ViewAsSwitcher";
import { useCampaign } from "./campaigns/useCampaign";
import { EntityManager, type WeltAnsicht } from "./entities/EntityManager";
import { CampaignGraphView } from "./graph/CampaignGraphView";
import { GegenstaendeUebersicht } from "./items/GegenstaendeUebersicht";
import { BegleiterVerwaltung } from "./begleiter/BegleiterVerwaltung";
import { Kampfmodus } from "./kampf/Kampfmodus";
import { SpielerLogin } from "./players/SpielerLogin";
import { SpielerAnsicht } from "./players/SpielerAnsicht";
import { SpielerVerwaltung } from "./players/SpielerVerwaltung";
import { CommlinkShell, type Bereich } from "./shell/CommlinkShell";
import { VollbildKnopf } from "./shell/VollbildKnopf";

/**
 * Bereiche der SL-Ansicht.
 *
 * PCs, NPCs, Orte, Events und Verbindungen sind eigene Commlink-Bereiche.
 * So bleibt die jeweilige Übersicht fokussiert; die Daten kommen weiterhin
 * aus demselben EntityManager, damit die Verbindungs-Auswahl alle Entitäten
 * kennt.
 */
const BEREICHE: Bereich[] = [
  { id: "pcs", name: "PCs", symbol: "◉", farbe: "#4d8bd8" },
  { id: "npcs", name: "NPCs", symbol: "◌", farbe: "#d4894b" },
  { id: "orte", name: "Orte", symbol: "⌖", farbe: "#2fa96a" },
  { id: "events", name: "Events", symbol: "◆", farbe: "#d4894b" },
  { id: "verbindungen", name: "Verbindungen", symbol: "⬡", farbe: "#7c8fe8" },
  // Violett wie die Gegenstands-Knoten im Graphen
  { id: "gegenstaende", name: "Gegenstände", symbol: "◈", farbe: "#a865d8" },
  // Sprites, Geister und Verbündete — eigener Bereich, weil sie ein eigenes
  // Blatt haben und keine Gegenstände sind.
  { id: "begleiter", name: "Begleiter", symbol: "❊", farbe: "#c76bff" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "#4d8bd8" },
  { id: "zugang", name: "Zugang", symbol: "⚿", farbe: "#3ddc84" },
  // Rot für den Kampf, Bernstein fürs Regelwerk, Grün für eigene Notizen
  { id: "kampf", name: "Kampfmodus", symbol: "⚔", farbe: "#ff3d5c" },
  { id: "regeln", name: "Regeln", symbol: "▤", farbe: "#ffb648", bald: true },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "#3ddc84", bald: true },
];

const TITEL: Record<string, string> = {
  pcs: "Spielercharaktere",
  npcs: "Nichtspielercharaktere",
  orte: "Orte",
  events: "Ereignisse",
  verbindungen: "Beziehungen zwischen Entitäten",
  gegenstaende: "Gegenstände",
  graph: "Beziehungsgeflecht",
  zugang: "Spielerzugänge",
};

const ENTITY_ANSICHT: Partial<Record<string, WeltAnsicht>> = {
  pcs: "pcs",
  npcs: "npcs",
  orte: "orte",
  events: "events",
  verbindungen: "verbindungen",
};

function CreateCampaignForm({ onCreate }: { onCreate: (name: string) => Promise<void> }) {
  const [name, setName] = useState("");
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onCreate(name);
    setName("");
  }
  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
      <p style={{ width: "100%" }}>Noch keine Kampagne vorhanden.</p>
      <input placeholder="Kampagnenname" value={name} onChange={(e) => setName(e.target.value)} required />
      <button type="submit">Kampagne anlegen</button>
    </form>
  );
}

function Dashboard() {
  const { me, logout } = useAuth();
  const { campaigns, loading, createCampaign } = useCampaign();
  const [bereich, setBereich] = useState("pcs");
  // Person-ID der SL-Vorschau, null = normale SL-Sicht. Dient zugleich als
  // React-key der Ansichten: bei einem Wechsel werden sie neu aufgebaut und
  // laden ihre Daten frisch gefiltert.
  const [viewAs, setViewAs] = useState<string | null>(null);

  const kampagne = campaigns?.[0];

  const werkzeuge = (
    <>
      {/* Geplante Werkzeuge (docs/ui-konzept.md): SL-Popups an Spieler und der
          Schalter fürs Tooltip-System. Sichtbar, aber deaktiviert — ein
          Schalter, der nichts tut, wäre irreführender als einer, der sagt,
          dass er noch nicht kann. */}
      <button type="button" className="cl-werkzeug" disabled title="Pop-ups an Spieler — kommt noch">
        ◎
      </button>
      <button type="button" className="cl-werkzeug" disabled title="Erklärungen einblenden — kommt noch">
        ?
      </button>
      <VollbildKnopf />
      <button type="button" className="cl-werkzeug" onClick={() => logout()} title="Abmelden">
        ⏻
      </button>
    </>
  );

  const fuss = (
    <>
      <div style={{ color: "var(--text-leise)" }}>{me?.username}</div>
      <div>{me?.role === "GM" ? "Spielleitung" : me?.role}</div>
    </>
  );

  return (
    <CommlinkShell
      bereiche={BEREICHE}
      aktiv={bereich}
      onBereichWechsel={setBereich}
      titel={kampagne ? `${kampagne.name} — ${TITEL[bereich] ?? ""}` : "Keine Kampagne"}
      werkzeuge={werkzeuge}
      fuss={fuss}
      /* Jede fokussierte Weltansicht teilt sich ihre Fläche selbst ein;
         lange Detailinhalte öffnen weiterhin im Fenster. */
      statisch={
        bereich === "pcs" ||
        bereich === "npcs" ||
        bereich === "orte" ||
        bereich === "events" ||
        bereich === "verbindungen" ||
        bereich === "gegenstaende" ||
        bereich === "graph" ||
        bereich === "begleiter" ||
        bereich === "kampf"
      }
    >
      {loading && <p style={{ color: "var(--text-leise)" }}>Lade Kampagnen…</p>}
      {!loading && campaigns && campaigns.length === 0 && <CreateCampaignForm onCreate={createCampaign} />}

      {!loading && kampagne && (
        <>
          <ViewAsSwitcher campaignId={kampagne.id} value={viewAs} onChange={setViewAs} />

          {ENTITY_ANSICHT[bereich] && (
            <EntityManager
              key={`${viewAs ?? "gm"}:${bereich}`}
              campaignId={kampagne.id}
              ansicht={ENTITY_ANSICHT[bereich]!}
            />
          )}
          {bereich === "gegenstaende" && <GegenstaendeUebersicht key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "begleiter" && <BegleiterVerwaltung key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "kampf" && <Kampfmodus key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "graph" && <CampaignGraphView key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "zugang" && <SpielerVerwaltung campaignId={kampagne.id} />}
        </>
      )}
    </CommlinkShell>
  );
}

/**
 * Weiche zwischen den drei Zuständen: Spielleitung, Spieler, niemand.
 *
 * Die Rolle kommt aus dem Sitzungs-Cookie (/api/auth/me). Spieler und
 * Spielleitung teilen sich dasselbe Cookie — es kann also immer nur eine
 * Rolle gleichzeitig aktiv sein. Für Marks Aufbau (ein Gerät, eine Rolle)
 * ist das richtig; wer beides zugleich braucht, nimmt ein zweites
 * Browserprofil oder ein privates Fenster.
 */
function Shell() {
  const { me, loading } = useAuth();
  const [zeigeSpielerLogin, setZeigeSpielerLogin] = useState(false);

  if (loading) return null;

  // Der Charakter haengt fest am Zugang, es gibt also nichts mehr zu waehlen.
  if (me?.role === "PLAYER") {
    return <SpielerAnsicht onAbgemeldet={() => window.location.reload()} />;
  }

  if (me) return <Dashboard />;

  if (zeigeSpielerLogin) {
    return <SpielerLogin onAngemeldet={() => window.location.reload()} onZurueck={() => setZeigeSpielerLogin(false)} />;
  }

  return <GmLoginPage onBeitreten={() => setZeigeSpielerLogin(true)} />;
}

function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}

export default App;
