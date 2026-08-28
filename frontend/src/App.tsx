import { useState, type FormEvent } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { GmLoginPage } from "./auth/GmLoginPage";
import { ViewAsSwitcher } from "./auth/ViewAsSwitcher";
import { useCampaign } from "./campaigns/useCampaign";
import { EntityManager } from "./entities/EntityManager";
import { CampaignGraphView } from "./graph/CampaignGraphView";
import { GegenstaendeUebersicht } from "./items/GegenstaendeUebersicht";
import { CommlinkShell, type Bereich } from "./shell/CommlinkShell";

/**
 * Bereiche der SL-Ansicht.
 *
 * Zielbild laut docs/ui-konzept.md ist ein feinerer Schnitt — Spieler-
 * charaktere und NPCs getrennt, dazu Orte und Events einzeln. Solange
 * EntityManager das alles in einer Ansicht hält, steht hier ein
 * gemeinsamer Bereich "Welt". Die noch nicht gebauten Bereiche sind
 * bewusst schon sichtbar (ausgegraut), damit die Richtung erkennbar ist.
 */
const BEREICHE: Bereich[] = [
  { id: "welt", name: "Welt", symbol: "◍" },
  { id: "gegenstaende", name: "Gegenstände", symbol: "◈" },
  { id: "graph", name: "Beziehungen", symbol: "⬡" },
  { id: "kampf", name: "Kampfmodus", symbol: "⚔", bald: true },
  { id: "regeln", name: "Regeln", symbol: "▤", bald: true },
  { id: "notizen", name: "Notizen", symbol: "✎", bald: true },
];

const TITEL: Record<string, string> = {
  welt: "Personen · Orte · Ereignisse",
  gegenstaende: "Gegenstände",
  graph: "Beziehungsgeflecht",
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
  const [bereich, setBereich] = useState("welt");
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
    >
      {loading && <p style={{ color: "var(--text-leise)" }}>Lade Kampagnen…</p>}
      {!loading && campaigns && campaigns.length === 0 && <CreateCampaignForm onCreate={createCampaign} />}

      {!loading && kampagne && (
        <>
          <ViewAsSwitcher campaignId={kampagne.id} value={viewAs} onChange={setViewAs} />

          {bereich === "welt" && <EntityManager key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "gegenstaende" && <GegenstaendeUebersicht key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "graph" && <CampaignGraphView key={viewAs ?? "gm"} campaignId={kampagne.id} />}
        </>
      )}
    </CommlinkShell>
  );
}

function Shell() {
  const { me, loading } = useAuth();
  if (loading) {
    return null;
  }
  return me ? <Dashboard /> : <GmLoginPage />;
}

function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}

export default App;
