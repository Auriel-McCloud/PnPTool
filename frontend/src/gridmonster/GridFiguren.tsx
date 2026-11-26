import { useEffect, useMemo, useState } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { giltFuer, gridApi, wertVon, type GmFigur, type GmKatalog } from "./api";
import "./gridmonster.css";

/**
 * GridMonster-Grundgerüst (26.11.2026): SL-Liste der Menschen bzw. Monster.
 *
 * Eine Komponente für beide Bereiche — `art` entscheidet, welche Figuren
 * gezeigt und angelegt werden. Mensch und Monster sind je eine eigene
 * Figur mit eigenem Blatt (Mark, 26.11.2026). Partnerschaft, Spieler mit
 * zwei Figuren und Inventar kommen im nächsten Schritt.
 */
export function GridFiguren({ campaignId, art }: { campaignId: string; art: "mensch" | "monster" }) {
  const istMonster = art === "monster";
  const [katalog, setKatalog] = useState<GmKatalog | null>(null);
  const [figuren, setFiguren] = useState<GmFigur[] | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [filter, setFilter] = useState<"alle" | "PC" | "NPC">("alle");
  const [offenId, setOffenId] = useState<string | null>(null);
  const [neuOffen, setNeuOffen] = useState(false);

  useEffect(() => {
    Promise.all([gridApi.katalog(campaignId), gridApi.figuren(campaignId)])
      .then(([k, f]) => {
        setKatalog(k);
        setFiguren(f);
      })
      .catch((e: Error) => setFehler(e.message));
  }, [campaignId]);

  const sichtbar = useMemo(
    () =>
      (figuren ?? []).filter(
        (f) => f.istMonster === istMonster && (filter === "alle" || f.personType === filter),
      ),
    [figuren, istMonster, filter],
  );

  function ersetzen(neu: GmFigur) {
    setFiguren((alt) => (alt ?? []).map((f) => (f.id === neu.id ? neu : f)));
  }

  const offen = figuren?.find((f) => f.id === offenId) ?? null;
  const ton = istMonster ? "var(--bereich-begleiter)" : "var(--bereich-pcs)";

  return (
    <div className="gm-ansicht" data-art={art}>
      <div className="gm-kopf">
        <div className="gm-filter" role="group" aria-label="Filter">
          {(["alle", "PC", "NPC"] as const).map((f) => (
            <button key={f} type="button" data-aktiv={filter === f ? "true" : undefined} onClick={() => setFilter(f)}>
              {f === "alle" ? "Alle" : f}
            </button>
          ))}
        </div>
        <button type="button" className="gm-neu" onClick={() => setNeuOffen(true)}>
          + {istMonster ? "Neues Monster" : "Neuer Mensch"}
        </button>
      </div>

      {fehler && <p className="gm-fehler">{fehler}</p>}
      {!figuren && !fehler && <p className="gm-leise">Lade…</p>}
      {figuren && sichtbar.length === 0 && (
        <p className="gm-leise">{istMonster ? "Noch keine Monster." : "Noch keine Menschen."}</p>
      )}

      <div className="gm-kacheln">
        {katalog &&
          sichtbar.map((f) => (
            <button key={f.id} type="button" className="gm-kachel cl-roehre" onClick={() => setOffenId(f.id)}>
              <span className="gm-kachel-symbol" aria-hidden="true">
                {istMonster ? "✦" : "◉"}
              </span>
              <span className="gm-kachel-name">{f.name}</span>
              <span className="gm-kachel-typ">{f.personType}</span>
              <span className="gm-kachel-werte">{kurzWerte(f, katalog)}</span>
            </button>
          ))}
      </div>

      {katalog && offen && (
        <Fenster
          offen
          breit
          ton={ton}
          titel={offen.name}
          unterzeile={`${istMonster ? "Monster" : "Mensch"} · ${offen.personType}`}
          kennung={`gm-figur-${offen.id}`}
          onSchliessen={() => setOffenId(null)}
        >
          <GridBlatt
            campaignId={campaignId}
            katalog={katalog}
            figur={offen}
            onGeaendert={ersetzen}
            onWeg={() => {
              setFiguren((alt) => (alt ?? []).filter((f) => f.id !== offen.id));
              setOffenId(null);
            }}
          />
        </Fenster>
      )}

      <NeueFigur
        offen={neuOffen}
        istMonster={istMonster}
        ton={ton}
        onSchliessen={() => setNeuOffen(false)}
        onAnlegen={async (name, personType) => {
          const neu = await gridApi.anlegen(campaignId, { name, istMonster, personType });
          setFiguren((alt) => [...(alt ?? []), neu].sort((a, b) => a.name.localeCompare(b.name)));
          setNeuOffen(false);
          setOffenId(neu.id);
        }}
      />
    </div>
  );
}

function kurzWerte(f: GmFigur, k: GmKatalog): string {
  const lp = wertVon(f, k, "Lebenspunkte");
  if (f.istMonster) {
    return `Stufe ${wertVon(f, k, "Stufe") ?? "?"} · LP ${lp ?? "?"} · EN ${wertVon(f, k, "Energie") ?? "?"}`;
  }
  return `Tamer ${wertVon(f, k, "Tamer-Level") ?? "?"} · LP ${lp ?? "?"}`;
}

function NeueFigur({
  offen,
  istMonster,
  ton,
  onSchliessen,
  onAnlegen,
}: {
  offen: boolean;
  istMonster: boolean;
  ton: string;
  onSchliessen: () => void;
  onAnlegen: (name: string, personType: "PC" | "NPC") => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [typ, setTyp] = useState<"PC" | "NPC">("NPC");
  const [fehler, setFehler] = useState<string | null>(null);
  useEffect(() => {
    if (offen) {
      setName("");
      setFehler(null);
    }
  }, [offen]);
  return (
    <Fenster
      offen={offen}
      schmal
      ton={ton}
      titel={istMonster ? "Neues Monster" : "Neuer Mensch"}
      kennung="gm-neue-figur"
      onSchliessen={onSchliessen}
    >
      <form
        className="gm-neu-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim()) return;
          onAnlegen(name.trim(), typ).catch((err: Error) => setFehler(err.message));
        }}
      >
        <label>
          Name
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <div className="gm-filter" role="group" aria-label="PC oder NPC">
          {(["PC", "NPC"] as const).map((t) => (
            <button key={t} type="button" data-aktiv={typ === t ? "true" : undefined} onClick={() => setTyp(t)}>
              {t}
            </button>
          ))}
        </div>
        {fehler && <p className="gm-fehler">{fehler}</p>}
        <button type="submit" className="gm-neu" disabled={!name.trim()}>
          Anlegen
        </button>
      </form>
    </Fenster>
  );
}

function GridBlatt({
  campaignId,
  katalog,
  figur,
  onGeaendert,
  onWeg,
}: {
  campaignId: string;
  katalog: GmKatalog;
  figur: GmFigur;
  onGeaendert: (f: GmFigur) => void;
  onWeg: () => void;
}) {
  const [fehler, setFehler] = useState<string | null>(null);
  const [name, setName] = useState(figur.name);
  const [wegFragen, setWegFragen] = useState(false);

  async function setzen(traitId: string, wert: number) {
    setFehler(null);
    try {
      onGeaendert(await gridApi.wertSetzen(campaignId, figur.id, traitId, wert));
    } catch (e) {
      setFehler((e as Error).message);
    }
  }

  async function aendern(daten: Partial<Pick<GmFigur, "name" | "personType">>) {
    setFehler(null);
    try {
      onGeaendert(await gridApi.aendern(campaignId, figur.id, daten));
    } catch (e) {
      setFehler((e as Error).message);
    }
  }

  const stufe = wertVon(figur, katalog, "Stufe");
  const stufeDaten = katalog.stufen.find((s) => s.stufe === stufe);
  const tamer = wertVon(figur, katalog, "Tamer-Level");

  return (
    <div className="gm-blatt" data-art={figur.istMonster ? "monster" : "mensch"}>
      <div className="gm-blatt-kopf">
        <label>
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => name.trim() && name.trim() !== figur.name && aendern({ name: name.trim() })}
          />
        </label>
        <div className="gm-filter" role="group" aria-label="PC oder NPC">
          {(["PC", "NPC"] as const).map((t) => (
            <button
              key={t}
              type="button"
              data-aktiv={figur.personType === t ? "true" : undefined}
              onClick={() => figur.personType !== t && aendern({ personType: t })}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {fehler && <p className="gm-fehler">{fehler}</p>}

      <section className="gm-werte">
        {katalog.werte
          .filter((w) => giltFuer(w.nurFuer, figur.istMonster))
          .map((w) => (
            <ZahlFeld
              key={w.id}
              name={w.name}
              wert={figur.werte[w.id] ?? 0}
              min={w.min}
              max={w.max}
              onSetzen={(v) => setzen(w.id, v)}
            />
          ))}
      </section>

      <p className="gm-abgeleitet">
        {figur.istMonster
          ? stufeDaten
            ? `Angriff W${stufeDaten.angriff} · Verteidigung ${stufeDaten.verteidigung}`
            : "Stufe setzen für Angriff/Verteidigung"
          : `Karten pro Zug: ${Math.min(tamer ?? 1, 3)}${tamer === 4 ? " · Verschmelzung möglich" : ""}`}
      </p>

      <section className="gm-attribute">
        {katalog.attribute.map((a) => (
          <div key={a.id} className="gm-attribut cl-roehre">
            <div className="gm-zeile gm-zeile-attribut">
              <span className="gm-zeile-name">{a.name}</span>
              <WuerfelWahl
                wuerfel={katalog.wuerfel}
                wert={figur.werte[a.id] ?? 0}
                onSetzen={(v) => setzen(a.id, v)}
              />
            </div>
            {a.fertigkeiten
              .filter((f) => giltFuer(f.nurFuer, figur.istMonster))
              .map((f) => (
                <div key={f.id} className="gm-zeile">
                  <span className="gm-zeile-name" title={f.name}>
                    {f.name}
                  </span>
                  <WuerfelWahl
                    wuerfel={katalog.wuerfel}
                    mitLeer
                    wert={figur.werte[f.id] ?? 0}
                    onSetzen={(v) => setzen(f.id, v)}
                  />
                </div>
              ))}
          </div>
        ))}
      </section>

      <div className="gm-blatt-fuss">
        <button type="button" className="gm-weg" onClick={() => setWegFragen(true)}>
          In den Papierkorb
        </button>
      </div>

      {wegFragen && (
        <Bestaetigung
          titel="In den Papierkorb?"
          text={`${figur.name} verschwindet aus der Liste. Die Figur wird nicht gelöscht, sondern nur als gelöscht markiert.`}
          jaText="Wegwerfen"
          onNein={() => setWegFragen(false)}
          onJa={async () => {
            setWegFragen(false);
            try {
              await gridApi.wegwerfen(campaignId, figur.id);
              onWeg();
            } catch (e) {
              setFehler((e as Error).message);
            }
          }}
        />
      )}
    </div>
  );
}

function WuerfelWahl({
  wuerfel,
  wert,
  mitLeer = false,
  onSetzen,
}: {
  wuerfel: number[];
  wert: number;
  mitLeer?: boolean;
  onSetzen: (w: number) => void;
}) {
  const stufen = mitLeer ? [0, ...wuerfel] : wuerfel;
  return (
    <div className="gm-wuerfel" role="group">
      {stufen.map((w) => (
        <button
          key={w}
          type="button"
          data-aktiv={wert === w ? "true" : undefined}
          onClick={() => wert !== w && onSetzen(w)}
          title={w === 0 ? "nicht gelernt" : `W${w}`}
        >
          {w === 0 ? "–" : `W${w}`}
        </button>
      ))}
    </div>
  );
}

function ZahlFeld({
  name,
  wert,
  min,
  max,
  onSetzen,
}: {
  name: string;
  wert: number;
  min: number;
  max: number | null;
  onSetzen: (w: number) => void;
}) {
  const [text, setText] = useState(String(wert));
  useEffect(() => setText(String(wert)), [wert]);
  const grenze = (v: number) => Math.max(min, max === null ? v : Math.min(max, v));
  function uebernehmen() {
    const v = Number.parseInt(text, 10);
    if (Number.isNaN(v)) return setText(String(wert));
    const g = grenze(v);
    if (g !== wert) onSetzen(g);
    else setText(String(wert));
  }
  return (
    <div className="gm-zahl cl-roehre">
      <span className="gm-zahl-name">{name}</span>
      <div className="gm-zahl-regler">
        <button type="button" disabled={wert <= min} onClick={() => onSetzen(grenze(wert - 1))}>
          −
        </button>
        <input
          inputMode="numeric"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={uebernehmen}
          onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
        />
        <button type="button" disabled={max !== null && wert >= max} onClick={() => onSetzen(grenze(wert + 1))}>
          +
        </button>
      </div>
    </div>
  );
}
