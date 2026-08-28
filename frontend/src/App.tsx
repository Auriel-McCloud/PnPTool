import { useState, type FormEvent } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { GmLoginPage } from "./auth/GmLoginPage";
import { useCampaign } from "./campaigns/useCampaign";
import { EntityManager } from "./entities/EntityManager";
import { CampaignGraphView } from "./graph/CampaignGraphView";
import { GegenstaendeUebersicht } from "./items/GegenstaendeUebersicht";

function CreateCampaignForm({ onCreate }: { onCreate: (name: string) => Promise<void> }) {
  const [name, setName] = useState("");
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onCreate(name);
    setName("");
  }
  return (
    <form onSubmit={handleSubmit}>
      <p>Noch keine Kampagne vorhanden.</p>
      <input placeholder="Kampagnenname" value={name} onChange={(e) => setName(e.target.value)} required />
      <button type="submit">Kampagne anlegen</button>
    </form>
  );
}

function Dashboard() {
  const { me, logout } = useAuth();
  const { campaigns, loading, createCampaign } = useCampaign();
  const [tab, setTab] = useState<"liste" | "graph" | "gegenstaende">("liste");

  return (
    <div style={{ maxWidth: 960, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1>PnPTool</h1>
        <div>
          <span>
            Angemeldet als {me?.username} ({me?.role})
          </span>{" "}
          <button type="button" onClick={() => logout()}>
            Abmelden
          </button>
        </div>
      </div>

      {loading && <p>Lade Kampagnen...</p>}
      {!loading && campaigns && campaigns.length === 0 && <CreateCampaignForm onCreate={createCampaign} />}
      {!loading && campaigns && campaigns.length > 0 && (
        <>
          <h2 style={{ color: "#666", fontWeight: "normal" }}>Kampagne: {campaigns[0].name}</h2>
          <div style={{ marginBottom: 16 }}>
            <button
              type="button"
              onClick={() => setTab("liste")}
              style={{ fontWeight: tab === "liste" ? "bold" : "normal", marginRight: 8 }}
            >
              Liste
            </button>
            <button
              type="button"
              onClick={() => setTab("graph")}
              style={{ fontWeight: tab === "graph" ? "bold" : "normal", marginRight: 8 }}
            >
              Beziehungsgraph
            </button>
            <button
              type="button"
              onClick={() => setTab("gegenstaende")}
              style={{ fontWeight: tab === "gegenstaende" ? "bold" : "normal" }}
            >
              Gegenstände
            </button>
          </div>
          {tab === "liste" && <EntityManager campaignId={campaigns[0].id} />}
          {tab === "graph" && <CampaignGraphView campaignId={campaigns[0].id} />}
          {tab === "gegenstaende" && <GegenstaendeUebersicht campaignId={campaigns[0].id} />}
        </>
      )}
    </div>
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
