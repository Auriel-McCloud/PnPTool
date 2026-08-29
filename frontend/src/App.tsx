import { useEffect, useState, type FormEvent } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { GmLoginPage } from "./auth/GmLoginPage";
import { ViewAsSwitcher } from "./auth/ViewAsSwitcher";
import { useCampaign } from "./campaigns/useCampaign";
import { EntityManager } from "./entities/EntityManager";
import { CampaignGraphView } from "./graph/CampaignGraphView";
import { GegenstaendeUebersicht } from "./items/GegenstaendeUebersicht";
import { BeitrittPage, CharakterWahl } from "./players/BeitrittPage";
import { playersApi } from "./players/api";
import { SpielerAnsicht } from "./players/SpielerAnsicht";
import { ZugangVerwaltung } from "./players/ZugangVerwaltung";
import { CommlinkShell, type Bereich } from "./shell/CommlinkShell";
import { VollbildKnopf } from "./shell/VollbildKnopf";

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
  { id: "welt", name: "Welt", symbol: "◍", farbe: "#00e5ff" },
  // Violett wie die Gegenstands-Knoten im Graphen
  { id: "gegenstaende", name: "Gegenstände", symbol: "◈", farbe: "#a865d8" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "#4d8bd8" },
  { id: "zugang", name: "Zugang", symbol: "⚿", farbe: "#3ddc84" },
  // Rot für den Kampf, Bernstein fürs Regelwerk, Grün für eigene Notizen
  { id: "kampf", name: "Kampfmodus", symbol: "⚔", farbe: "#ff3d5c", bald: true },
  { id: "regeln", name: "Regeln", symbol: "▤", farbe: "#ffb648", bald: true },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "#3ddc84", bald: true },
];

const TITEL: Record<string, string> = {
  welt: "Personen · Orte · Ereignisse",
  gegenstaende: "Gegenstände",
  graph: "Beziehungsgeflecht",
  zugang: "Spielerzugang",
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
      /* Bereiche, die sich selbst einteilen und ohne Scrollen auskommen.
         "Welt" fehlt noch — dort steht dieselbe Frage an wie bei den
         Gegenständen: Kacheln oder Tabelle, Blättern, Suche. */
      statisch={bereich === "gegenstaende" || bereich === "graph"}
    >
      {loading && <p style={{ color: "var(--text-leise)" }}>Lade Kampagnen…</p>}
      {!loading && campaigns && campaigns.length === 0 && <CreateCampaignForm onCreate={createCampaign} />}

      {!loading && kampagne && (
        <>
          <ViewAsSwitcher campaignId={kampagne.id} value={viewAs} onChange={setViewAs} />

          {bereich === "welt" && <EntityManager key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "gegenstaende" && <GegenstaendeUebersicht key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "graph" && <CampaignGraphView key={viewAs ?? "gm"} campaignId={kampagne.id} />}
          {bereich === "zugang" && <ZugangVerwaltung campaignId={kampagne.id} />}
        </>
      )}
    </CommlinkShell>
  );
}

/**
 * Weiche zwischen den drei Zuständen: Spielleitung, Spieler, niemand.
 *
 * Die Rolle kommt aus dem Sitzungs-Cookie (/api/auth/me), Spieler und
 * Spielleitung teilen sich dasselbe Cookie — es kann also immer nur eine
 * Rolle gleichzeitig aktiv sein. Für Marks Aufbau (ein Gerät, eine Rolle)
 * ist das richtig; wer beides zugleich braucht, nimmt ein zweites
 * Browserprofil oder ein privates Fenster.
 */
function Shell() {
  const { me, loading } = useAuth();
  const [zeigeBeitritt, setZeigeBeitritt] = useState(false);
  // Nach dem Beitritt fehlt noch der Charakter; danach die volle Ansicht.
  const [hatCharakter, setHatCharakter] = useState<boolean | null>(null);

  useEffect(() => {
    if (me?.role !== "PLAYER") {
      setHatCharakter(null);
      return;
    }
    playersApi
      .me()
      .then((s) => setHatCharakter(s.personId !== null))
      .catch(() => setHatCharakter(false));
  }, [me]);

  if (loading) return null;

  if (me?.role === "PLAYER") {
    if (hatCharakter === null) return null;
    if (!hatCharakter)
      return (
        <CharakterWahl
          onGewaehlt={() => setHatCharakter(true)}
          onAbmelden={() => playersApi.abmelden().then(() => window.location.reload())}
        />
      );
    return <SpielerAnsicht onAbgemeldet={() => window.location.reload()} />;
  }

  if (me) return <Dashboard />;

  if (zeigeBeitritt) {
    return (
      <BeitrittPage onBeigetreten={() => window.location.reload()} onZurueck={() => setZeigeBeitritt(false)} />
    );
  }

  return <GmLoginPage onBeitreten={() => setZeigeBeitritt(true)} />;
}

function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}

export default App;
