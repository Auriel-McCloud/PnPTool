import { useState, type FormEvent } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { AnmeldeFenster } from "./auth/AnmeldeFenster";
import { ViewAsSwitcher } from "./auth/ViewAsSwitcher";
import { useCampaign } from "./campaigns/useCampaign";
import { KampagnenAuswahl } from "./campaigns/KampagnenAuswahl";
import { Fenster } from "./shell/Fenster";
import { EntityManager, type WeltAnsicht } from "./entities/EntityManager";
import { CampaignGraphView } from "./graph/CampaignGraphView";
import { GegenstaendeUebersicht } from "./items/GegenstaendeUebersicht";
import { ShopUebersicht } from "./haendler/ShopUebersicht";
import { RassenUebersicht } from "./rassen/RassenUebersicht";
import { BegleiterVerwaltung } from "./begleiter/BegleiterVerwaltung";
import { PartyVerwaltung } from "./party/PartyVerwaltung";
import { Kampfmodus } from "./kampf/Kampfmodus";
import { SpielerAnsicht } from "./players/SpielerAnsicht";
import { SpielerVerwaltung } from "./players/SpielerVerwaltung";
import { CommlinkShell, type Bereich } from "./shell/CommlinkShell";
import { WikiAnsicht } from "./wiki/WikiAnsicht";
import { MitteilungenAnbieter } from "./mitteilungen/MitteilungenKontext";
import { MitteilungSenden } from "./mitteilungen/MitteilungSenden";
import { MitteilungenBlitz } from "./mitteilungen/MitteilungenBlitz";
import { MitteilungPopup } from "./mitteilungen/MitteilungPopup";
import { EinstellungenFenster } from "./campaigns/EinstellungenFenster";
import { AugmentsAnsicht } from "./augments/AugmentsAnsicht";
import { KontakteGm } from "./kontakte/KontakteGm";
import { VollbildKnopf } from "./shell/VollbildKnopf";
import { IdeenschmiedeAnsicht } from "./ideenschmiede/IdeenschmiedeAnsicht";

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
  { id: "fraktionen", name: "Fraktionen", symbol: "⬡", farbe: "var(--bereich-fraktionen)" },
  { id: "verbindungen", name: "Verbindungen", symbol: "⬡", farbe: "var(--bereich-verbindungen)" },
  // Violett wie die Gegenstands-Knoten im Graphen
  { id: "gegenstaende", name: "Gegenstände", symbol: "◈", farbe: "var(--bereich-gegenstaende)" },
  // Shop-System (24.09.2026): Händler und ihr Sortiment — eigener Punkt
  // statt Unterreiter bei Gegenständen, weil hier gekauft wird, nicht nur
  // verwaltet. Gedecktes Gold statt der Gegenstandsfarbe: der Shop selbst
  // ist ein Ort des Handelns, kein reiner Datensatz.
  { id: "shop", name: "Shop", symbol: "¥", farbe: "var(--bereich-shop)" },
  // Sprites, Geister und Verbündete — eigener Bereich, weil sie ein eigenes
  // Blatt haben und keine Gegenstände sind.
  { id: "begleiter", name: "Begleiter", symbol: "❊", farbe: "var(--bereich-begleiter)" },
  // Wer gerade zusammen unterwegs ist — eigener Bereich, weil es eine
  // eigene Beziehungslogik ist (Mitgliedschaft + Aufenthaltsort + Aktiv-
  // Exklusivität), keine Fraktion mit Zielen/Ressourcen.
  { id: "party", name: "Party", symbol: "👥", farbe: "var(--bereich-party)" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "var(--bereich-graph)" },
  { id: "zugang", name: "Zugang", symbol: "⚿", farbe: "var(--bereich-zugang)" },
  // SL-Kontaktverwaltung: wer kennt wen, wer kann mit wem chatten
  { id: "kontakte", name: "Kontakte", symbol: "📇", farbe: "var(--bereich-npcs)" },
  // Rot für den Kampf, Bernstein fürs Regelwerk, Grün für eigene Notizen
  { id: "kampf", name: "Kampfmodus", symbol: "⚔", farbe: "var(--bereich-kampf)" },
  // Das Kampagnen-Wiki: Geschichten, Kapitel, Session-Notizen (docs/produktvision-wiki.md)
  { id: "wiki", name: "Wiki", symbol: "❋", farbe: "var(--bereich-wiki)" },
  { id: "augments", name: "Augments", symbol: "⚕", farbe: "var(--bereich-regeln)" },
  // Der Rassen-Baukasten: Völker bauen und je Kampagne freigeben. Wie die
  // Augments ein Regelwerks-Bereich, deshalb dieselbe Leitfarbe.
  { id: "rassen", name: "Rassen", symbol: "🧬", farbe: "var(--bereich-regeln)" },
  // Ideenschmiede: Entwürfe und KI-generierte Ideen sammeln, prüfen, verschieben
  { id: "ideenschmiede", name: "Schmiede", symbol: "🔧", farbe: "var(--bereich-schmiede)" },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "var(--bereich-notizen)", bald: true },
];

const TITEL: Record<string, string> = {
  augments: "Körperkarte: wo sitzt welches Implantat",
  pcs: "Spielercharaktere",
  npcs: "Nichtspielercharaktere",
  orte: "Orte",
  events: "Ereignisse",
  verbindungen: "Beziehungen zwischen Entitäten",
  gegenstaende: "Gegenstände",
  shop: "Shop",
  graph: "Beziehungsgeflecht",
  zugang: "Spielerzugänge",
  wiki: "Kampagnen-Wiki",
  kontakte: "Kontakte: wer kennt wen",
  party: "Party: wer gerade zusammen unterwegs ist",
  rassen: "Rassen: Baukasten und Freigabe",
  ideenschmiede: "Ideenschmiede: Entwürfe und Ideen",
};

const ENTITY_ANSICHT: Partial<Record<string, WeltAnsicht>> = {
  pcs: "pcs",
  npcs: "npcs",
  orte: "orte",
  events: "events",
  fraktionen: "fraktionen",
  verbindungen: "verbindungen",
};

function CreateCampaignForm({
  onCreate,
  hinweis = "Noch keine Kampagne vorhanden.",
  onFertig,
}: {
  onCreate: (name: string) => Promise<unknown>;
  hinweis?: string;
  onFertig?: () => void;
}) {
  const [name, setName] = useState("");
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onCreate(name);
    setName("");
    onFertig?.();
  }
  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
      <p style={{ width: "100%" }}>{hinweis}</p>
      <input placeholder="Kampagnenname" value={name} onChange={(e) => setName(e.target.value)} required />
      <button type="submit">Kampagne anlegen</button>
    </form>
  );
}

function Dashboard() {
  const { me, logout } = useAuth();
  const { campaigns, loading, aktive, waehleKampagne, createCampaign, nachImportUebernehmen } = useCampaign();
  const [bereich, setBereich] = useState("pcs");
  // Person-ID der SL-Vorschau, null = normale SL-Sicht. Dient zugleich als
  // React-key der Ansichten: bei einem Wechsel werden sie neu aufgebaut und
  // laden ihre Daten frisch gefiltert.
  const [viewAs, setViewAs] = useState<string | null>(null);

  const kampagne = aktive;

  const [einstellungenOffen, setEinstellungenOffen] = useState(false);
  const [neueKampagneOffen, setNeueKampagneOffen] = useState(false);

  // Kennung, mit der jede Ansicht neu aufgebaut wird: Wechsel der Kampagne
  // oder der Rollen-Sicht (viewAs) muss die Ansicht frisch laden lassen.
  const ansichtKennung = `${kampagne?.id ?? "keine"}:${viewAs ?? "gm"}:${bereich}`;

  const werkzeuge = (
    <>
      {/* Aktive Kampagne wechseln bzw. neu anlegen. */}
      <KampagnenAuswahl
        kampagnen={campaigns ?? []}
        aktiveId={kampagne?.id ?? null}
        onWaehlen={waehleKampagne}
        onNeu={() => setNeueKampagneOffen(true)}
      />
      {/* Geplante Werkzeuge (docs/ui-konzept.md): SL-Popups an Spieler und der
          Schalter fürs Tooltip-System. Sichtbar, aber deaktiviert — ein
          Schalter, der nichts tut, wäre irreführender als einer, der sagt,
          dass er noch nicht kann. */}
      {/* War laut docs/ui-konzept.md als "SL-Popups" vorgesehen und bis jetzt
          deaktiviert — hier ist die Funktion dahinter. */}
      {kampagne && <MitteilungSenden campaignId={kampagne.id} />}
      {/* Blitz-Symbol für die SL, um Nachrichten zu sehen (Chat-Benachrichtigungen). */}
      {kampagne && <MitteilungenBlitz personId={null} />}
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
    <>
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
        bereich === "shop" ||
        bereich === "graph" ||
        bereich === "begleiter" ||
        bereich === "kampf" ||
        bereich === "wiki" ||
        bereich === "augments"
      }
    >
      {loading && <p style={{ color: "var(--text-leise)" }}>Lade Kampagnen…</p>}
      {!loading && campaigns && campaigns.length === 0 && <CreateCampaignForm onCreate={createCampaign} />}

      {!loading && kampagne && (
        <>
          <ViewAsSwitcher campaignId={kampagne.id} value={viewAs} onChange={setViewAs} />

          <EinstellungenFenster
            campaignId={kampagne.id}
            campaignName={kampagne.name}
            offen={einstellungenOffen}
            onSchliessen={() => setEinstellungenOffen(false)}
            onImportiert={(neu) => nachImportUebernehmen(neu.id)}
          />

          {ENTITY_ANSICHT[bereich] && (
            <EntityManager
              key={ansichtKennung}
              campaignId={kampagne.id}
              ansicht={ENTITY_ANSICHT[bereich]!}
            />
          )}
          {bereich === "gegenstaende" && <GegenstaendeUebersicht key={ansichtKennung} campaignId={kampagne.id} />}
          {bereich === "shop" && <ShopUebersicht key={ansichtKennung} campaignId={kampagne.id} eigenePersonId={null} istGm />}
          {bereich === "begleiter" && <BegleiterVerwaltung key={ansichtKennung} campaignId={kampagne.id} />}
          {bereich === "party" && <PartyVerwaltung key={ansichtKennung} campaignId={kampagne.id} />}
          {bereich === "rassen" && <RassenUebersicht key={ansichtKennung} campaignId={kampagne.id} />}
          {bereich === "kampf" && <Kampfmodus key={ansichtKennung} campaignId={kampagne.id} />}
          {bereich === "graph" && <CampaignGraphView key={ansichtKennung} campaignId={kampagne.id} />}
          {bereich === "zugang" && <SpielerVerwaltung campaignId={kampagne.id} />}
          {bereich === "wiki" && (
            <WikiAnsicht
              key={ansichtKennung}
              campaignId={kampagne.id}
              onNavigateToIdeenschmiede={() => setBereich("ideenschmiede")}
            />
          )}

          {/* Augments: Koerperkarte (wo sitzt welches Implantat). */}
          {bereich === "augments" && <AugmentsAnsicht key={ansichtKennung} campaignId={kampagne.id} />}

          {/* Kontakte: SL verwaltet wer wen kennt und wer mit wem chatten kann. */}
          {bereich === "kontakte" && <KontakteGm key={ansichtKennung} campaignId={kampagne.id} />}

          {/* Ideenschmiede: Entwürfe und KI-Ideen sammeln, prüfen, verschieben. */}
          {bereich === "ideenschmiede" && <IdeenschmiedeAnsicht key={ansichtKennung} campaignId={kampagne.id} />}
        </>
      )}
    </CommlinkShell>

      {/* Neue Kampagne anlegen — über das Dropdown in der Kopfleiste erreichbar. */}
      <Fenster
        offen={neueKampagneOffen}
        titel="Neue Kampagne"
        kennung="neue-kampagne"
        onSchliessen={() => setNeueKampagneOffen(false)}
      >
        <CreateCampaignForm
          hinweis="Name der neuen Kampagne:"
          onCreate={createCampaign}
          onFertig={() => setNeueKampagneOffen(false)}
        />
      </Fenster>
    </>
  );

  // Ohne Kampagne gibt es keine Leitung, die man öffnen könnte.
  if (!kampagne) return shell;

  return (
      <MitteilungenAnbieter campaignId={kampagne.id} personId={null} istSl>
        {shell}
        {/* Popup für Chat-Benachrichtigungen (NACHRICHT-Art) von Spielern. */}
        <MitteilungPopup />
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

  if (loading) return null;

  // Der Charakter haengt fest am Zugang, es gibt also nichts mehr zu waehlen.
  if (me?.role === "PLAYER") {
    return <SpielerAnsicht onAbgemeldet={() => window.location.reload()} />;
  }

  if (me) return <Dashboard />;

  // Gemeinsames Anmeldefenster (Mark, 22.09.2026): Spieler sehen den
  // Anmelde-Weg zuerst, die SL muss extra klicken — deutlich mehr
  // Spieler- als SL-Logins am Tisch, das vermeidet Verwechslungen.
  return <AnmeldeFenster />;
}

function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}

export default App;
