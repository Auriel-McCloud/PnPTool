/** Felder einer Droge im Umbauen. Zahlen, keine neue Effekt-Kiste. */

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
  crashBonusName: string;
  crashBonusWert: number;
}

export function DrogenFelder({
  wert,
  onChange,
}: {
  wert: DrogeFelder;
  onChange: (neu: DrogeFelder) => void;
}) {
  function set<K extends keyof DrogeFelder>(key: K, value: DrogeFelder[K]) {
    onChange({ ...wert, [key]: value });
  }
  return (
    <section style={{ marginTop: 16, display: "grid", gap: 8 }}>
      <h4 style={{ margin: 0, letterSpacing: "0.08em", textTransform: "uppercase", fontSize: "0.8em" }}>
        Schlucken
      </h4>
      <label>
        Wirkung hält
        <select value={wert.wirkungDauer} onChange={(e) => set("wirkungDauer", e.target.value)}>
          <option value="sofort">sofort</option>
          <option value="szene">bis die Szene wechselt</option>
          <option value="rast">bis zur Rast</option>
        </select>
      </label>
      <label>
        Heilmenge
        <input type="number" value={wert.heilmenge} onChange={(e) => set("heilmenge", Number(e.target.value))} />
        <select value={wert.heilQualitaet} onChange={(e) => set("heilQualitaet", e.target.value)}>
          <option value="">keine</option>
          <option value="minderwertig">minderwertig, nur Schlag</option>
          <option value="normal">normal, tödlich zuerst</option>
          <option value="hochwertig">hochwertig, auch schwerheilbar</option>
        </select>
      </label>
      <label>
        Willenskraft jetzt
        <input type="number" value={wert.willenskraftWirkung} onChange={(e) => set("willenskraftWirkung", Number(e.target.value))} />
        Crash
        <input type="number" value={wert.willenskraftNebenwirkung} onChange={(e) => set("willenskraftNebenwirkung", Number(e.target.value))} />
      </label>
      <label>
        Crash-Bonus, Name und Würfel
        <input value={wert.crashBonusName} onChange={(e) => set("crashBonusName", e.target.value)} placeholder="Geschicklichkeit" />
        <input type="number" value={wert.crashBonusWert} onChange={(e) => set("crashBonusWert", Number(e.target.value))} />
      </label>
      <label>
        Initiative im Crash
        <input type="number" value={wert.nebenwirkungInitiative} onChange={(e) => set("nebenwirkungInitiative", Number(e.target.value))} />
      </label>
      <label>
        Reduktion, solange die Wirkung läuft
        <input type="number" value={wert.ruestungReduktionBasis} onChange={(e) => set("ruestungReduktionBasis", Number(e.target.value))} />
      </label>
      <label>
        Crash-Schaden
        <select value={wert.umwandeln ? "" : wert.nebenwirkungSchaden} onChange={(e) => set("nebenwirkungSchaden", e.target.value)} disabled={Boolean(wert.umwandeln)}>
          <option value="">keiner</option>
          <option value="schlag">Schlag</option>
          <option value="aggraviert">schwerheilbar</option>
          <option value="toedlich">tödlich, zwei Rasten</option>
        </select>
        <input type="number" value={wert.nebenwirkungSchadenMenge} onChange={(e) => set("nebenwirkungSchadenMenge", Number(e.target.value))} />
      </label>
      <label>
        Oder umwandeln, nichts dazuzählen
        <select value={wert.umwandeln} onChange={(e) => set("umwandeln", e.target.value)}>
          <option value="">nein</option>
          <option value="schlagZuToedlich">aller Schlag wird tödlich</option>
          <option value="allesZuAggraviert">Schlag und tödlich werden schwerheilbar</option>
        </select>
      </label>
      <p style={{ margin: 0, color: "var(--text-leise)", fontSize: "0.8em" }}>
        Plus-Boni sind die Bonuszeilen oben. Der Crash nimmt dieselben Namen mit negativem Vorzeichen,
        sobald du sie unter Nebenwirkung einträgst — hier nur die Initiative des Crashs.
      </p>
    </section>
  );
}
