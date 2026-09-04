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
import { WikiAnsicht } from "./wiki/WikiAnsicht";
import { MitteilungenAnbieter } from "./mitteilungen/MitteilungenKontext";
import { MitteilungSenden } from "./mitteilungen/MitteilungSenden";
import { EinstellungenFenster } from "./campaigns/EinstellungenFenster";
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
  // Die Farben stehen als Tokens in theme/tokens.css (--bereich-*), damit ein
  // Themewechsel sie mitzieht. Hier steht nur noch, WELCHES Token gilt.
  { id: "pcs", name: "PCs", symbol: "◉", farbe: "var(--bereich-pcs)" },
  { id: "npcs", name: "NPCs", symbol: "◌", farbe: "var(--bereich-npcs)" },
  { id: "orte", name: "Orte", symbol: "⌖", farbe: "var(--bereich-orte)" },
  { id: "events", name: "Events", symbol: "◆", farbe: "var(--bereich-events)" },
  { id: "verbindungen", name: "Verbindungen", symbol: "⬡", farbe: "var(--bereich-verbindungen)" },
  // Violett wie die Gegenstands-Knoten im Graphen
  { id: "gegenstaende", name: "Gegenstände", symbol: "◈", farbe: "var(--bereich-gegenstaende)" },
  // Sprites, Geister und Verbündete — eigener Bereich, weil sie ein eigenes
  // Blatt haben und keine Gegenstände sind.
  { id: "begleiter", name: "Begleiter", symbol: "❊", farbe: "var(--bereich-begleiter)" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "var(--bereich-graph)" },
  { id: "zugang", name: "Zugang", symbol: "⚿", farbe: "var(--bereich-zugang)" },
  // Rot für den Kampf, Bernstein fürs Regelwerk, Grün für eigene Notizen
  { id: "kampf", name: "Kampfmodus", symbol: "⚔", farbe: "var(--bereich-kampf)" },
  // Das Kampagnen-Wiki: Geschichten, Kapitel, Session-Notizen (docs/produktvision-wiki.md)
  { id: "wiki", name: "Wiki", symbol: "❋", farbe: "var(--bereich-wiki)" },
  { id: "regeln", name: "Regeln", symbol: "▤", farbe: "var(--bereich-regeln)", bald: true },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "var(--bereich-notizen)", bald: true },
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
  wiki: "Kampagnen-Wiki",
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

  const [einstellungenOffen, setEinstellungenOffen] = useState(false);

  const werkzeuge = (
    <>
      {/* Geplante Werkzeuge (docs/ui-konzept.md): SL-Popups an Spieler und der
          Schalter fürs Tooltip-System. Sichtbar, aber deaktiviert — ein
          Schalter, der nichts tut, wäre irreführender als einer, der sagt,
          dass er noch nicht kann. */}
      {/* War laut docs/ui-konzept.md als "SL-Popups" vorgesehen und bis jetzt
          deaktiviert — hier ist die Funktion dahinter. */}
      {kampagne && <MitteilungSenden campaignId={kampagne.id} />}
      {kampagne && (
        <button
          type="button"
          onClick={() => setEinstellungenOffen(true)}
          title="Kampagnen-Einstellungen"
        >
          ⚙
        </button>
      )}
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

  const shell = (
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
        bereich === "kampf" ||
        bereich === "wiki"
      }
    >
      {loading && <p style={{ color: "var(--text-leise)" }}>Lade Kampagnen…</p>}
      {!loading && campaigns && campaigns.length === 0 && <CreateCampaignForm onCreate={createCampaign} />}

      {!loading && kampagne && (
        <>
          <ViewAsSwitcher campaignId={kampagne.id} value={viewAs} onChange={setViewAs} />

          <EinstellungenFenster
            campaignId={kampagne.id}
            offen={einstellungenOffen}
            onSchliessen={() => setEinstellungenOffen(false)}
          />

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
          {bereich === "wiki" && <WikiAnsicht key={viewAs ?? "gm"} campaignId={kampagne.id} />}
        </>
      )}
    </CommlinkShell>
  );

  // Ohne Kampagne gibt es keine Leitung, die man öffnen könnte.
  if (!kampagne) return shell;

  return (
    <MitteilungenAnbieter campaignId={kampagne.id} personId={null} istSl>
      {shell}
    </MitteilungenAnbieter>
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
