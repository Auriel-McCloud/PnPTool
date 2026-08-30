import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import { ART_NAMEN, ART_SYMBOLE, begleiterApi, type Begleiter, type BegleiterArt } from "./api";
import "../items/gegenstaende.css";
import "./begleiter.css";

/**
 * Begleiter anlegen und pflegen — Sprites, Geister, Verbündete.
 *
 * Sie hängen an einer Person und teilen sich das Blatt mit Drohnen und
 * Fahrzeugen. Wer einem Spielercharakter zugeordnet ist, wird beim Anlegen
 * automatisch für ihn sichtbar; sonst müsste die Spielleitung bei jedem
 * Sprite daran denken, und vergässe sie es, stünde der Technomancer ohne da.
 */

const ARTEN: BegleiterArt[] = ["SPRITE", "GEIST", "BEGLEITER"];

export function BegleiterVerwaltung({ campaignId }: { campaignId: string }) {
  const [alle, setAlle] = useState<Begleiter[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [laden, setLaden] = useState(true);
  const [offen, setOffen] = useState<Begleiter | null>(null);
  const [neuName, setNeuName] = useState("");
  const [neuArt, setNeuArt] = useState<BegleiterArt>("SPRITE");
  const [neuBesitzer, setNeuBesitzer] = useState("");
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);

  async function neuLaden() {
    const [b, p] = await Promise.all([
      begleiterApi.liste(campaignId),
      entitiesApi.listPersonen(campaignId),
    ]);
    setAlle(b);
    setPersonen(p);
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId]);

  const personenNamen = useMemo(
    () => personen.map((p) => ({ id: p.id, label: `${p.name} (${p.personType})` })),
    [personen],
  );

  const seiten = Math.max(1, Math.ceil(alle.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = alle.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    await begleiterApi.anlegen(campaignId, {
      name: neuName.trim(),
      art: neuArt,
      besitzerId: neuBesitzer || null,
    });
    setNeuName("");
    await neuLaden();
  }

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Begleiter…</p>;

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <form onSubmit={anlegen} className="bg-zeile" style={{ marginBottom: 10 }}>
        <input
          placeholder="Name"
          value={neuName}
          onChange={(e) => setNeuName(e.target.value)}
          style={{ flex: "1 1 200px", minWidth: 0 }}
        />
        <select value={neuArt} onChange={(e) => setNeuArt(e.target.value as BegleiterArt)}>
          {ARTEN.map((a) => (
            <option key={a} value={a}>
              {ART_NAMEN[a]}
            </option>
          ))}
        </select>
        <select value={neuBesitzer} onChange={(e) => setNeuBesitzer(e.target.value)}>
          <option value="">— ungebunden —</option>
          {personenNamen.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <button type="submit">Anlegen</button>
      </form>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((b) => (
          <button key={b.id} type="button" className="gg-kachel" onClick={() => setOffen(b)} title={b.name}>
            <span className="gg-kachel-bild">
              <span aria-hidden="true">{ART_SYMBOLE[b.art]}</span>
            </span>
            <span className="gg-kachel-name">{b.name}</span>
            <span className="gg-kachel-zeile">
              {ART_NAMEN[b.art]}
              {b.stufe > 0 && ` · Stufe ${b.stufe}`}
            </span>
            <span className="gg-kachel-marken">
              {b.besitzerName ? (
                <span className="gg-marke">{b.besitzerName}</span>
              ) : (
                <span className="gg-marke">ungebunden</span>
              )}
            </span>
          </button>
        ))}
      </div>

      {alle.length === 0 && <p className="gg-leer">Noch keine Begleiter in dieser Kampagne.</p>}

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

      {offen && (
        <BegleiterFenster
          campaignId={campaignId}
          begleiter={offen}
          personen={personenNamen}
          onSchliessen={() => setOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setOffen(null);
          }}
        />
      )}
    </div>
  );
}

function BegleiterFenster({
  campaignId,
  begleiter,
  personen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  begleiter: Begleiter;
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [name, setName] = useState(begleiter.name);
  const [art, setArt] = useState(begleiter.art);
  const [beziehung, setBeziehung] = useState(begleiter.beziehung);
  const [stufe, setStufe] = useState(begleiter.stufe);
  const [widerstand, setWiderstand] = useState(begleiter.widerstand);
  const [angriff, setAngriff] = useState(begleiter.angriff);
  const [agilitaet, setAgilitaet] = useState(begleiter.agilitaet);
  const [waffe, setWaffe] = useState(begleiter.waffe);
  const [waffenSchaden, setWaffenSchaden] = useState(begleiter.waffenSchaden);
  const [schadensart, setSchadensart] = useState(begleiter.schadensart);
  // Freie Fertigkeiten als Paare, damit sich Namen ändern lassen — ein
  // Objekt liesse den Schlüssel nicht umbenennen, ohne den Wert zu verlieren.
  const [fertigkeiten, setFertigkeiten] = useState<[string, number][]>(
    Object.entries(begleiter.fertigkeiten ?? {}),
  );
  const [besitzer, setBesitzer] = useState(begleiter.besitzerId ?? "");
  const [sendet, setSendet] = useState(false);

  const verteilt = widerstand + angriff + agilitaet + fertigkeiten.reduce((s, [, w]) => s + w, 0);

  async function sichern() {
    setSendet(true);
    try {
      await begleiterApi.aendern(campaignId, begleiter.id, {
        name,
        art,
        beziehung,
        stufe,
        widerstand,
        angriff,
        agilitaet,
        waffe,
        waffenSchaden,
        schadensart,
        fertigkeiten: Object.fromEntries(fertigkeiten.filter(([n]) => n.trim())),
      });
      if (besitzer !== (begleiter.besitzerId ?? "")) {
        await begleiterApi.besitzer(campaignId, begleiter.id, besitzer || null);
      }
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  return (
    <Fenster
      offen
      titel={`${ART_SYMBOLE[art]} ${begleiter.name}`}
      unterzeile="Blatt wie bei Drohne und Fahrzeug"
      kennung={`begleiter-bearbeiten:${begleiter.id}`}
      onSchliessen={onSchliessen}
    >
      <div className="bg-formular">
        <div className="bg-zeile">
          <input value={name} onChange={(e) => setName(e.target.value)} style={{ flex: "1 1 200px" }} />
          <select value={art} onChange={(e) => setArt(e.target.value as BegleiterArt)}>
            {ARTEN.map((a) => (
              <option key={a} value={a}>
                {ART_NAMEN[a]}
              </option>
            ))}
          </select>
        </div>

        <label className="bg-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3 }}>
          <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--neon)" }}>
            Beziehung
          </span>
          <input
            value={beziehung}
            onChange={(e) => setBeziehung(e.target.value)}
            placeholder="Wie steht er zu seinem Menschen?"
          />
        </label>

        <div className="bg-zeile">
          <select value={besitzer} onChange={(e) => setBesitzer(e.target.value)}>
            <option value="">— ungebunden —</option>
            {personen.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <section className="bg-stufe">
          <span className="bg-stufe-titel">Stufe</span>
          <DotPool value={stufe} max={15} onChange={setStufe} />
          <span className="bg-stufe-hinweis">
            Das Budget für die Werte darunter — und zugleich die Gesundheit.
          </span>
        </section>

        <section className="bg-werte">
          {(
            [
              ["Widerstand", widerstand, setWiderstand, 5],
              ["Angriff", angriff, setAngriff, 5],
              ["Agilität", agilitaet, setAgilitaet, 5],
            ] as const
          ).map(([beschriftung, wert, setzen, maximum]) => (
            <div key={beschriftung} className="bg-wert">
              <span>{beschriftung}</span>
              <DotPool value={wert} max={maximum} onChange={setzen} />
            </div>
          ))}
        </section>

        {stufe > 0 && verteilt > stufe && (
          <p style={{ color: "var(--warn)", fontSize: 13, margin: 0 }}>
            {verteilt} Punkte verteilt, die Stufe gibt {stufe} her.
          </p>
        )}

        <section>
          <h3 style={{ margin: "0 0 6px" }}>Fertigkeiten</h3>
          {fertigkeiten.map(([fName, fWert], i) => (
            <div key={i} className="bg-zeile" style={{ marginBottom: 4 }}>
              <input
                value={fName}
                onChange={(e) =>
                  setFertigkeiten((alt) => alt.map((p, j) => (j === i ? [e.target.value, p[1]] : p)))
                }
                placeholder="Name"
                style={{ flex: "1 1 160px" }}
              />
              <DotPool
                value={fWert}
                max={5}
                onChange={(w) => setFertigkeiten((alt) => alt.map((p, j) => (j === i ? [p[0], w] : p)))}
              />
              <button type="button" onClick={() => setFertigkeiten((alt) => alt.filter((_, j) => j !== i))}>
                −
              </button>
            </div>
          ))}
          <button type="button" onClick={() => setFertigkeiten((alt) => [...alt, ["", 0]])}>
            Fertigkeit hinzufügen
          </button>
        </section>

        <section>
          <h3 style={{ margin: "0 0 6px" }}>Gegenstand</h3>
          <div className="bg-zeile">
            <input
              value={waffe}
              onChange={(e) => setWaffe(e.target.value)}
              placeholder="Waffe oder Gerät"
              style={{ flex: "1 1 180px" }}
            />
            <input
              value={schadensart}
              onChange={(e) => setSchadensart(e.target.value)}
              placeholder="Schadensart"
              style={{ flex: "1 1 140px" }}
            />
          </div>
          <div className="bg-wert" style={{ marginTop: 4 }}>
            <span>Schadensbonus</span>
            <DotPool value={waffenSchaden} max={7} onChange={setWaffenSchaden} />
          </div>
        </section>

        <div className="bg-zeile">
          <button type="button" onClick={sichern} disabled={sendet}>
            {sendet ? "Wird gespeichert…" : "Speichern"}
          </button>
          <button
            type="button"
            style={{ borderColor: "var(--signal)", color: "var(--signal)", marginLeft: "auto" }}
            onClick={async () => {
              await begleiterApi.entfernen(campaignId, begleiter.id);
              onGeaendert();
            }}
          >
            Entfernen
          </button>
        </div>
      </div>
    </Fenster>
  );
}
