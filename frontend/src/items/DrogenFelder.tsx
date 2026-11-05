/** Umbauen einer Droge: oben die Wirkung, dicke Linie, darunter dasselbe für die Nebenwirkung. */

import type { ReactNode } from "react";

export interface NebenwirkungZeile {
  key: string;
  value: string;
}

export interface DrogeFelder {
  wirkungDauer: string;
  heilmenge: number;
  heilQualitaet: string;
  willenskraftWirkung: number;
  willenskraftNebenwirkung: number;
  nebenwirkungInitiative: number;
  nebenwirkungSchaden: string;
  nebenwirkungSchadenMenge: number;
  umwandeln: string;
  ruestungReduktionBasis: number;
  nebenwirkungZeilen: NebenwirkungZeile[];
}

type Katalog = { id: string; name: string }[];
type Zeile = { key: string; value: string; spezialisierungen?: string[] };

const ueberschrift: React.CSSProperties = {
  margin: "0 0 8px",
  fontFamily: "var(--mono)",
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  fontSize: "0.8em",
};

const hinweis: React.CSSProperties = {
  margin: "0 0 8px",
  color: "var(--text-leise)",
  fontSize: "0.85em",
};

const feld: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: "0.9em",
  flexWrap: "wrap",
};

const zahl: React.CSSProperties = { width: 70 };

function zeitraumNebenwirkung(dauer: string, schaden: string): string {
  if (schaden === "toedlich") return "Tödlicher Schaden hält zwei Rasten. Die Rast, die ihn startet, zählt mit.";
  if (dauer === "sofort") return "Startet mit dem Schluck.";
  if (dauer === "rast") return "Startet bei der Rast und hält noch eine weitere Rast.";
  return "Startet, wenn die Szene wechselt, und hält bis zur Rast.";
}

function BonusZeilen({
  zeilen,
  onChange,
  katalog,
  spez,
  neuWert,
}: {
  zeilen: Zeile[];
  onChange: (neu: Zeile[]) => void;
  katalog: Katalog;
  spez?: (texte: string[], onChange: (neu: string[]) => void) => ReactNode;
  neuWert: string;
}) {
  return (
    <>
      {zeilen.map((p, i) => (
        <div key={i} style={{ marginTop: 4 }}>
          <div style={{ display: "flex", gap: 6 }}>
            <select
              value={p.key}
              onChange={(e) => onChange(zeilen.map((x, idx) => (idx === i ? { ...x, key: e.target.value } : x)))}
              style={{ flex: 1 }}
            >
              <option value="">— Wert wählen —</option>
              {katalog.map((t) => (
                <option key={t.id} value={t.name}>
                  {t.name}
                </option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Würfel"
              value={p.value}
              onChange={(e) => onChange(zeilen.map((x, idx) => (idx === i ? { ...x, value: e.target.value } : x)))}
              style={{ width: 70 }}
            />
            <button type="button" onClick={() => onChange(zeilen.filter((_, idx) => idx !== i))}>
              ×
            </button>
          </div>
          {spez?.(p.spezialisierungen ?? [], (neu) =>
            onChange(zeilen.map((x, idx) => (idx === i ? { ...x, spezialisierungen: neu } : x))),
          )}
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...zeilen, { key: "", value: neuWert }])}
        style={{ marginTop: 4, fontSize: "0.85em" }}
      >
        + Bonus
      </button>
    </>
  );
}

export function DrogenFelder({
  wert,
  onChange,
  katalog,
  wirkungBoni,
  onWirkungBoni,
  initiative,
  onInitiative,
  zusatzaktionen,
  onZusatzaktionen,
  spez,
}: {
  wert: DrogeFelder;
  onChange: (neu: DrogeFelder) => void;
  katalog: Katalog;
  wirkungBoni: Zeile[];
  onWirkungBoni: (neu: Zeile[]) => void;
  initiative: number;
  onInitiative: (neu: number) => void;
  zusatzaktionen: number;
  onZusatzaktionen: (neu: number) => void;
  spez: (texte: string[], onChange: (neu: string[]) => void) => ReactNode;
}) {
  function set<K extends keyof DrogeFelder>(key: K, value: DrogeFelder[K]) {
    onChange({ ...wert, [key]: value });
  }

  return (
    <>
      <section>
        <h4 style={ueberschrift}>Wirkung</h4>
        <label style={feld}>
          Zeitraum
          <select value={wert.wirkungDauer} onChange={(e) => set("wirkungDauer", e.target.value)}>
            <option value="sofort">sofort</option>
            <option value="szene">bis die Szene wechselt</option>
            <option value="rast">bis zur Rast</option>
          </select>
        </label>
        <p style={{ ...hinweis, marginTop: 10 }}>
          Würfel, solange die Wirkung läuft. Spezialisierungen darunter sind von der SL fix vergeben, +1 in der Probe.
        </p>
        <BonusZeilen zeilen={wirkungBoni} onChange={onWirkungBoni} katalog={katalog} spez={spez} neuWert="1" />
        <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
          <label style={feld}>
            Initiative
            <input type="number" value={initiative} onChange={(e) => onInitiative(Number(e.target.value))} style={zahl} />
          </label>
          <label style={feld}>
            Zusatzaktionen
            <select value={zusatzaktionen} onChange={(e) => onZusatzaktionen(Number(e.target.value))}>
              <option value={0}>keine</option>
              <option value={1}>1× pro Kampf</option>
              <option value={2}>2× pro Kampf</option>
              <option value={-1}>jede Runde</option>
            </select>
          </label>
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
          <label style={feld}>
            Heilmenge
            <input type="number" value={wert.heilmenge} onChange={(e) => set("heilmenge", Number(e.target.value))} style={zahl} />
            <select value={wert.heilQualitaet} onChange={(e) => set("heilQualitaet", e.target.value)}>
              <option value="">keine</option>
              <option value="minderwertig">minderwertig, nur Schlag</option>
              <option value="normal">normal, tödlich zuerst</option>
              <option value="hochwertig">hochwertig, auch schwerheilbar</option>
            </select>
          </label>
          <label style={feld} title="Plus gibt ausgegebene Willenskraft zurück, Minus verbraucht sie.">
            Willenskraft
            <input
              type="number"
              value={wert.willenskraftWirkung}
              onChange={(e) => set("willenskraftWirkung", Number(e.target.value))}
              style={zahl}
            />
          </label>
          <label style={feld} title="Addiert auf die Reduktion der aktiven Rüstung, solange die Wirkung läuft.">
            Reduktion
            <input
              type="number"
              value={wert.ruestungReduktionBasis}
              onChange={(e) => set("ruestungReduktionBasis", Number(e.target.value))}
              style={zahl}
            />
          </label>
        </div>
      </section>

      <div role="separator" style={{ borderTop: "4px solid var(--text)", margin: "22px 0 14px" }} />

      <section>
        <h4 style={ueberschrift}>Nebenwirkung</h4>
        <p style={hinweis}>
          Zeitraum: {zeitraumNebenwirkung(wert.wirkungDauer, wert.umwandeln ? "" : wert.nebenwirkungSchaden)}
        </p>
        <p style={hinweis}>Dieselben Würfel noch einmal. Minus ist der Abzug.</p>
        <BonusZeilen
          zeilen={wert.nebenwirkungZeilen}
          onChange={(neu) => set("nebenwirkungZeilen", neu)}
          katalog={katalog}
          neuWert="-1"
        />
        <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
          <label style={feld}>
            Initiative
            <input
              type="number"
              value={wert.nebenwirkungInitiative}
              onChange={(e) => set("nebenwirkungInitiative", Number(e.target.value))}
              style={zahl}
            />
          </label>
          <label style={feld} title="Plus gibt ausgegebene Willenskraft zurück, Minus verbraucht sie.">
            Willenskraft
            <input
              type="number"
              value={wert.willenskraftNebenwirkung}
              onChange={(e) => set("willenskraftNebenwirkung", Number(e.target.value))}
              style={zahl}
            />
          </label>
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
          <label style={feld}>
            Schaden
            <select
              value={wert.umwandeln ? "" : wert.nebenwirkungSchaden}
              onChange={(e) => set("nebenwirkungSchaden", e.target.value)}
              disabled={Boolean(wert.umwandeln)}
            >
              <option value="">keiner</option>
              <option value="schlag">Schlag</option>
              <option value="aggraviert">schwerheilbar</option>
              <option value="toedlich">tödlich, zwei Rasten</option>
            </select>
            <input
              type="number"
              value={wert.nebenwirkungSchadenMenge}
              onChange={(e) => set("nebenwirkungSchadenMenge", Number(e.target.value))}
              style={zahl}
              disabled={Boolean(wert.umwandeln)}
            />
          </label>
          <label style={feld}>
            Oder umwandeln, nichts dazuzählen
            <select value={wert.umwandeln} onChange={(e) => set("umwandeln", e.target.value)}>
              <option value="">nein</option>
              <option value="schlagZuToedlich">aller Schlag wird tödlich</option>
              <option value="allesZuAggraviert">Schlag und tödlich werden schwerheilbar</option>
            </select>
          </label>
        </div>
      </section>
    </>
  );
}
