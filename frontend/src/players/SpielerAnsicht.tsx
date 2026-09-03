import { useEffect, useRef, useState } from "react";
import { entitiesApi, type Event, type Ort, type Person } from "../entities/api";
import { CampaignGraphView } from "../graph/CampaignGraphView";
import { WikiAnsicht } from "../wiki/WikiAnsicht";
import { MitteilungenAnbieter } from "../mitteilungen/MitteilungenKontext";
import { MitteilungenBlitz } from "../mitteilungen/MitteilungenBlitz";
import { MitteilungPopup } from "../mitteilungen/MitteilungPopup";
import { einstellungenApi, formatiereLast, type Einstellungen } from "../campaigns/einstellungen";
import { itemsApi, type Ablage, type Gegenstand, type GegenstandMitBesitzer, type TraglastZeile } from "../items/api";
import {
  ermittleBereiche,
  // "Bereich" heisst in der Hülle bereits der Navigationsbereich links
  type Bereich as Ablagebereich,
} from "../items/aufbewahrung";
import { GegenstandKachel } from "../items/GegenstandKachel";
import { begleiterApi, type Begleiter } from "../begleiter/api";
import { Initiativliste, useKampf } from "../kampf/Initiativliste";
import { Kampfkarte } from "../kampf/Kampfkarte";
import { DranMeldung } from "../kampf/DranMeldung";
import { Verwundung, useZustand } from "../shell/Verwundung";
import { BegleiterKachel } from "../begleiter/BegleiterKachel";
import { Fachfenster } from "../items/Fachfenster";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Charakterblatt } from "../traits/Charakterblatt";
import { CommlinkShell, type Bereich } from "../shell/CommlinkShell";
import { VollbildKnopf } from "../shell/VollbildKnopf";
import "../items/gegenstaende.css";
import { playersApi, type SpielerMe } from "./api";

/**
 * Die Spieler-Ansicht — dieselbe Hülle wie beim Spielleiter, nur mit weniger
 * Bereichen und ohne Bearbeiten (siehe docs/ui-konzept.md, "eine Hülle, zwei
 * Rollen").
 *
 * Gefiltert wird ausschließlich serverseitig: hier kommt nur an, was der
 * Spieler sehen darf. Diese Ansicht versteckt nichts selbst — sie könnte es
 * auch nicht, die Daten sind schlicht nicht da.
 */
const BEREICHE: Bereich[] = [
  // Das Charakterblatt steht vorn und ist die Startansicht — es ist das,
  // worauf ein Spieler während der Runde am häufigsten schaut.
  { id: "blatt", name: "Charakterblatt", symbol: "▤", farbe: "var(--bereich-blatt)" },
  { id: "inventar", name: "Inventar", symbol: "◈", farbe: "var(--bereich-inventar)" },
  // Eigener Bereich, weil ein Rigger sehr viele Drohnen führt und die im
  // Inventar zwischen Munition und Kaugummi untergingen. Beide haben ein
  // eigenes Blatt (Stufe, Widerstand, Angriff, Agilität).
  { id: "fahrzeuge", name: "Fahrzeuge", symbol: "⛭", farbe: "var(--bereich-fahrzeuge)" },
  // Sprites, Geister und Verbündete teilen sich ein Blatt mit den Drohnen —
  // deshalb ein Bereich für alle drei.
  { id: "begleiter", name: "Begleiter", symbol: "❊", farbe: "var(--bereich-begleiter)" },
  // Die Initiativliste sehen alle — darum geht es: jeder weiss, wann er dran
  // ist, ohne zu fragen.
  { id: "kampf", name: "Kampf", symbol: "⚔", farbe: "var(--bereich-kampf)" },
  { id: "kontakte", name: "Kontakte", symbol: "◍", farbe: "var(--bereich-kontakte)" },
  { id: "orte", name: "Orte", symbol: "⌖", farbe: "var(--bereich-orte)" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "var(--bereich-graph)" },
  // Das Kampagnen-Wiki: hier nur lesend, und nur was die SL freigegeben hat.
  { id: "wiki", name: "Wiki", symbol: "❋", farbe: "var(--bereich-wiki)" },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "var(--bereich-notizen)", bald: true },
];

function Karte({ titel, unter, text }: { titel: string; unter?: string; text?: string }) {
  return (
    <article style={{ borderBottom: "1px solid var(--linie)", padding: "10px 0" }}>
      <h3 style={{ margin: 0, color: "var(--text)", textTransform: "none", letterSpacing: 0 }}>
        {titel}
        {unter && <span style={{ color: "var(--text-leise)", fontWeight: "normal" }}> · {unter}</span>}
      </h3>
      {text && (
        <div style={{ marginTop: 4, color: "var(--text-leise)" }}>
          <RichTextView content={parseRichText(text)} />
        </div>
      )}
    </article>
  );
}

export function SpielerAnsicht({ onAbgemeldet }: { onAbgemeldet: () => void }) {
  const [ich, setIch] = useState<SpielerMe | null>(null);
  const [bereich, setBereich] = useState("blatt");
  // Welches Fach gerade offensteht (null = nur die Ausrüstung). Abgelöst hat
  // das die frühere Mehrfachauswahl über Reiter: was man am Körper trägt,
  // liegt offen, alles andere macht man auf — und sieht schon daran, dass
  // man nicht gleich schnell drankommt.
  // Ein *Stapel* offener Fächer, keine einzelne Auswahl: aus dem Rucksack
  // heraus soll sich der Behälter darin öffnen lassen, und darin wieder einer.
  // Genau das meinte Mark mit "Pop-ups die zu Pop-ups führen".
  const [fachStapel, setFachStapel] = useState<string[]>([]);
  // Kachelraster wie beim Spielleiter: gemessen statt gescrollt.
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  // Eigenes Raster: es steht in einem anderen Bereich und misst eine andere
  // Fläche aus. Ein geteiltes ref zeigte je nach Bereich ins Leere.
  const fahrzeugRasterRef = useRef<HTMLDivElement>(null);
  const begleiterRasterRef = useRef<HTMLDivElement>(null);
  // Läuft dauerhaft mit, nicht nur im Kampfbereich: so kann später eine
  // Meldung "du bist dran" von überall aufgehen.
  const { kampf, geladen: kampfGeladen } = useKampf(ich?.campaignId ?? null);
  // Der eigene Zustand, damit der Bildschirm mitblutet — auch wenn die
  // Spielleitung den Schaden einträgt und nicht man selbst.
  const zustand = useZustand(ich?.campaignId ?? null, ich?.personId ?? null);
  const [seite, setSeite] = useState(0);
  const [einstellungen, setEinstellungen] = useState<Einstellungen | null>(null);
  const [traglast, setTraglast] = useState<TraglastZeile[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [sachen, setSachen] = useState<GegenstandMitBesitzer[]>([]);
  const [begleiter, setBegleiter] = useState<Begleiter[]>([]);

  useEffect(() => {
    playersApi.me().then(setIch).catch(() => setIch(null));
  }, []);

  useEffect(() => {
    if (!ich) return;
    const cid = ich.campaignId;
    entitiesApi.listPersonen(cid).then(setPersonen).catch(() => setPersonen([]));
    entitiesApi.listOrte(cid).then(setOrte).catch(() => setOrte([]));
    entitiesApi.listEvents(cid).then(setEvents).catch(() => setEvents([]));
    itemsApi.listAlle(cid).then(setSachen).catch(() => setSachen([]));
    einstellungenApi.lesen(cid).then(setEinstellungen).catch(() => setEinstellungen(null));
    itemsApi.traglast(cid).then(setTraglast).catch(() => setTraglast([]));
    begleiterApi.liste(cid).then(setBegleiter).catch(() => setBegleiter([]));
  }, [ich]);

  // Bereiche nur aus den eigenen Sachen — fremde Verstecke gehen einen nichts an
  const meineRoh = sachen.filter((g) => g.ownerId === ich?.personId);
  const fremdeRoh = sachen.filter((g) => g.ownerId !== ich?.personId);
  // Was anderen gehört, ist ein Reiter wie jeder andere statt eines
  // angehängten zweiten Blocks: dann gibt es genau ein Raster, das sich
  // ausmessen lässt, und die Auswahl bleibt eine einzige Entscheidung.
  // Ein Bereich prüft laut Schnittstelle einen `Gegenstand`; den Besitzer
  // trägt erst die kampagnenweite Liste nach. Deshalb hier die einzige
  // Stelle, an der das nachgeschlagen wird.
  const gehoertMir = (g: Gegenstand) => (g as GegenstandMitBesitzer).ownerId === ich?.personId;
  const fahrzeuge = meineRoh.filter((g) => g.typ === "Fahrzeug" || g.typ === "Drohne");
  const bereiche: Ablagebereich[] = [
    // Die eigenen Bereiche dürfen nur eigene Sachen einsammeln — sonst
    // fischte "Mitgeführt" auch den Rucksackinhalt anderer heraus.
    ...ermittleBereiche(meineRoh).map((b) => ({
      ...b,
      passt: (g: Gegenstand) => gehoertMir(g) && b.passt(g),
    })),
    ...(fremdeRoh.length > 0
      ? [
          {
            id: "FREMD",
            name: "Anderswo gesehen",
            symbol: "◇",
            greifbar: false,
            passt: (g: Gegenstand) => !gehoertMir(g),
          },
        ]
      : []),
  ];

  // Muss vor der Abbruchbedingung stehen: Hooks müssen bei jedem Aufbau in
  // derselben Reihenfolge laufen, sonst bricht React ab ("Rendered more
  // hooks than during the previous render").
  useEffect(() => {
    setSeite(0);
  }, [bereich]);

  if (!ich) return null;

  const amKoerper = bereiche.find((b) => b.greifbar);
  const faecher = bereiche.filter((b) => !b.greifbar);
  const getragen = amKoerper ? sachen.filter(amKoerper.passt) : [];
  const seiten = Math.max(1, Math.ceil(getragen.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const aufDieserSeite = getragen.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  // Der getragene Behälter gibt dem mittleren Ablageplatz seinen Namen.
  const getragenesFach = faecher.find((f) => f.id === "MITGEFUEHRT");
  const getragenerBehaelter = getragenesFach?.name;
  const getragenerBehaelterId = sachen.find(
    (g) => g.ablage === "AUSGERUESTET" && (g.typ === "Behälter" || g.typ === "Fahrzeug"),
  )?.id;

  /**
   * Zu welchem Fach ein Behälter-Gegenstand gehört. Der getragene Rucksack
   * sammelt unter "MITGEFUEHRT" ein, jeder andere Behälter unter seiner
   * eigenen Kennung.
   */
  function fachIdFuer(item: Gegenstand) {
    if (item.id === getragenerBehaelterId) return getragenesFach?.id;
    return faecher.find((f) => f.id === item.id)?.id;
  }

  function inhaltVon(item: Gegenstand) {
    const fachId = fachIdFuer(item);
    if (!fachId) return undefined;
    const fach = faecher.find((f) => f.id === fachId);
    if (!fach) return undefined;
    return {
      anzahl: sachen.filter(fach.passt).length,
      oeffnen: () => setFachStapel((alt) => [...alt, fachId]),
    };
  }

  async function umlegen(itemId: string, ziel: Ablage) {
    if (!ich) return;
    // Ohne festes Ziel: der Spieler legt nur die Art fest, das genaue Wohin
    // (welches Fahrzeug, welcher Ort) bleibt Sache der Spielleitung.
    await itemsApi.setAblage(ich.campaignId, itemId, ziel, null);
    const [frisch, last] = await Promise.all([
      itemsApi.listAlle(ich.campaignId),
      itemsApi.traglast(ich.campaignId),
    ]);
    setSachen(frisch);
    setTraglast(last);
  }

  async function abmelden() {
    await playersApi.abmelden();
    onAbgemeldet();
  }

  return (
    <MitteilungenAnbieter campaignId={ich.campaignId} personId={ich.personId}>
    {/* Liegt ueber allem, auch ueber offenen Fenstern: eine Ansage der
        Spielleitung darf nicht dahinter verschwinden. */}
    <MitteilungPopup />
    <Verwundung zustand={zustand} />
    <DranMeldung
      kampf={kampf}
      eigenePersonId={ich.personId}
      imKampfbereich={bereich === "kampf"}
      onHin={() => setBereich("kampf")}
    />
    <CommlinkShell
      bereiche={BEREICHE}
      aktiv={bereich}
      onBereichWechsel={setBereich}
      titel={`${ich.campaignName} — ${BEREICHE.find((b) => b.id === bereich)?.name ?? ""}`}
      // Nur das Inventar teilt sich die Fläche selbst ein; die übrigen
      // Bereiche sind noch Listen und dürfen scrollen.
      statisch={
        bereich === "inventar" ||
        bereich === "fahrzeuge" ||
        bereich === "begleiter" ||
        bereich === "kampf" ||
        bereich === "wiki"
      }
      werkzeuge={
        <>
          {/* Blitz rechts in der oberen Leiste — docs/ui-konzept.md */}
          <MitteilungenBlitz personId={ich.personId} />
          <VollbildKnopf />
          <button type="button" className="cl-werkzeug" onClick={abmelden} title="Abmelden">
            ⏻
          </button>
        </>
      }
      fuss={
        <>
          <div style={{ color: "var(--text-leise)" }}>{ich.benutzername}</div>
          <div>{ich.personName ?? "kein Charakter"}</div>
        </>
      }
    >
      {bereich === "blatt" &&
        (ich.personId ? (
          <Charakterblatt campaignId={ich.campaignId} personId={ich.personId} />
        ) : (
          <p style={{ color: "var(--text-leise)" }}>
            Dir ist noch kein Charakter zugeordnet — deine Spielleitung muss dir einen zuweisen.
          </p>
        ))}

      {bereich === "fahrzeuge" && (
        <div className="gg-seite" style={KACHEL_STIL}>
          <h3 className="gg-abschnitt">
            <span>⛭ Fahrzeuge und Drohnen</span>
            <span className="gg-abschnitt-zahl">{fahrzeuge.length}</span>
          </h3>
          <div className="gg-raster" ref={fahrzeugRasterRef}>
            {fahrzeuge.map((g) => (
              <GegenstandKachel
                key={g.id}
                item={g}
                behaelterName={getragenerBehaelter}
                behaelterId={getragenerBehaelterId}
                inhalt={inhaltVon(g)}
                onUmlegen={(ziel) => umlegen(g.id, ziel)}
              />
            ))}
          </div>
          {fahrzeuge.length === 0 && <p className="gg-leer">Du besitzt kein Fahrzeug und keine Drohne.</p>}
        </div>
      )}

      {bereich === "kampf" && (
        <div className="ka-seite">
          {!kampfGeladen && <p style={{ color: "var(--text-leise)" }}>Lade…</p>}
          {kampfGeladen && !kampf && (
            <p style={{ color: "var(--text-leise)" }}>Gerade wird nicht gekämpft.</p>
          )}
          {kampf && (
            <>
              <header className="ka-kopf">
                <span className="ka-runde">
                  Runde <strong>{kampf.runde}</strong>
                </span>
              </header>
              <Initiativliste kampf={kampf} eigenePersonId={ich.personId} />
              {/* Die eigenen Kampfwerte gleich darunter — im Gefecht will man
                  nicht erst in den Bogen wechseln. */}
              {ich.personId && (
                <div className="ka-eigene">
                  <h3 className="gg-abschnitt">
                    <span>⚔ Deine Werte</span>
                  </h3>
                  <Kampfkarte campaignId={ich.campaignId} personId={ich.personId} aenderbar />
                </div>
              )}
              {kampf.teilnehmer.length > 1 && (
                <p className="ka-ansage">
                  <span>Ansage von hinten:</span>{" "}
                  {[...kampf.teilnehmer].reverse().map((t) => t.name).join(" → ")}
                </p>
              )}
            </>
          )}
        </div>
      )}

      {bereich === "begleiter" && (
        <div className="gg-seite" style={KACHEL_STIL}>
          <h3 className="gg-abschnitt">
            <span>❊ Sprites, Geister und Verbündete</span>
            <span className="gg-abschnitt-zahl">{begleiter.length}</span>
          </h3>
          <div className="gg-raster" ref={begleiterRasterRef}>
            {begleiter.map((b) => (
              <BegleiterKachel key={b.id} begleiter={b} />
            ))}
          </div>
          {begleiter.length === 0 && <p className="gg-leer">Dir steht noch niemand zur Seite.</p>}
        </div>
      )}

      {bereich === "kontakte" && (
        <>
          {personen.length === 0 && <p style={{ color: "var(--text-leise)" }}>Du kennst noch niemanden.</p>}
          {personen.map((p) => (
            <Karte
              key={p.id}
              titel={p.name}
              unter={p.id === ich.personId ? "du" : undefined}
              text={p.description}
            />
          ))}
        </>
      )}

      {bereich === "inventar" && (
        // Feste Fläche, gemessenes Raster: die Hauptansicht scrollt nicht.
        // In den Fächern darf sie es — dort bricht es die Illusion nicht.
        <div className="gg-seite" style={KACHEL_STIL}>
          {einstellungen?.gewichtAktiv &&
            (() => {
              const meineLast = traglast.find((z) => z.id === ich.personId);
              if (!meineLast) return null;
              const voll = meineLast.kapazitaet > 0 && meineLast.last > meineLast.kapazitaet;
              return (
                <p className="gg-kachel-last" data-voll={voll} style={{ marginBottom: 8, fontSize: 13 }}>
                  Getragen: {formatiereLast(meineLast.last, meineLast.kapazitaet)}
                  {voll && " — überladen"}
                </p>
              );
            })()}

          <h3 className="gg-abschnitt">
            <span>⚔ Am Körper</span>
            <span className="gg-abschnitt-zahl">{getragen.length}</span>
          </h3>

          <div className="gg-raster" ref={rasterRef}>
            {aufDieserSeite.map((g) => (
              <GegenstandKachel
                key={g.id}
                item={g}
                behaelterName={getragenerBehaelter}
                behaelterId={getragenerBehaelterId}
                inhalt={inhaltVon(g)}
                onUmlegen={(ziel) => umlegen(g.id, ziel)}
              />
            ))}
          </div>

          {getragen.length === 0 && <p className="gg-leer">Du trägst nichts bei dir.</p>}

          {seiten > 1 && (
            <div className="gg-blaettern">
              <button type="button" onClick={() => setSeite((n) => Math.max(0, n - 1))} disabled={aktuelleSeite === 0}>
                ‹
              </button>
              <span>
                {aktuelleSeite + 1} / {seiten}
              </span>
              <button
                type="button"
                onClick={() => setSeite((n) => Math.min(seiten - 1, n + 1))}
                disabled={aktuelleSeite >= seiten - 1}
              >
                ›
              </button>
            </div>
          )}

          {/* Die Fächer unten wie eine Werkzeugleiste: Rucksack, Fahrzeug,
              Versteck. Jedes geht als Fenster auf — das ist zugleich die
              Handlung "aufmachen" und zeigt, dass man da nicht so schnell
              drankommt wie an das, was man am Körper trägt. */}
          {faecher.length > 0 && (
            <div className="gg-faecher">
              {faecher.map((f) => {
                const anzahl = sachen.filter(f.passt).length;
                return (
                  <button
                    key={f.id}
                    type="button"
                    className="gg-fach"
                    onClick={() => setFachStapel([f.id])}
                    // Auch leere Fächer lassen sich öffnen — man will
                    // nachsehen können, statt zu rätseln.
                    title={`${f.name} öffnen`}
                  >
                    <span className="gg-fach-symbol" aria-hidden="true">
                      {f.symbol}
                    </span>
                    <span className="gg-fach-name">{f.name}</span>
                    <span className="gg-fach-zahl">{anzahl}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Ein Fenster je Stufe des Stapels. Schliessen räumt alles darüber
              mit ab — sonst bliebe ein Fenster stehen, dessen Fach gar nicht
              mehr offen ist. */}
          {fachStapel.map((fachId, stufe) => {
            const fach = faecher.find((f) => f.id === fachId);
            if (!fach) return null;
            return (
              <Fachfenster
                key={`${fachId}:${stufe}`}
                fach={fach}
                offen
                items={sachen.filter(fach.passt)}
                behaelterName={getragenerBehaelter}
                behaelterId={getragenerBehaelterId}
                inhaltVon={inhaltVon}
                onSchliessen={() => setFachStapel((alt) => alt.slice(0, stufe))}
                // Fremdes lässt sich ansehen, aber nicht umlegen
                onUmlegen={fach.id === "FREMD" ? undefined : (item, ziel) => umlegen(item.id, ziel)}
              />
            );
          })}
        </div>
      )}

      {bereich === "orte" && (
        <>
          {orte.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Orte bekannt.</p>}
          {orte.map((o) => (
            <Karte key={o.id} titel={o.name} text={o.description} />
          ))}
          {events.length > 0 && (
            <>
              <h3 style={{ marginTop: 20 }}>Was geschehen ist</h3>
              {events.map((e) => (
                <Karte key={e.id} titel={e.title} unter={e.timestamp || undefined} text={e.description} />
              ))}
            </>
          )}
        </>
      )}

      {bereich === "graph" && <CampaignGraphView campaignId={ich.campaignId} />}

      {/* Nur lesend: Anlegen, Aendern und Freigeben bleibt Sache der Spielleitung.
          Was hier ankommt, hat der Server bereits gefiltert. */}
      {bereich === "wiki" && <WikiAnsicht campaignId={ich.campaignId} nurLesen />}
    </CommlinkShell>
    </MitteilungenAnbieter>
  );
}
