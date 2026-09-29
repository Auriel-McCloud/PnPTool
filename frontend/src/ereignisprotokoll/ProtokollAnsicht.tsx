import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Fenster } from "../shell/Fenster";
import { KATEGORIE_TITEL, protokollApi, type Sitzung, type ZeitleisteEintrag } from "./api";
import "./protokoll.css";

function uhr(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
}

export function ProtokollAnsicht({ campaignId }: { campaignId: string }) {
  const [sitzungen, setSitzungen] = useState<Sitzung[]>([]);
  const [sitzungId, setSitzungId] = useState<string>("");
  const [eintraege, setEintraege] = useState<ZeitleisteEintrag[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [kategorie, setKategorie] = useState<string>("");
  const [suche, setSuche] = useState("");
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuDatum, setNeuDatum] = useState(() => new Date().toISOString().slice(0, 10));
  const [neuTitel, setNeuTitel] = useState("");

  async function laden(sid: string) {
    const liste = await protokollApi.sitzungen(campaignId);
    setSitzungen(liste);
    const zeit = await protokollApi.zeitleiste(campaignId, sid || undefined);
    setEintraege(zeit);
  }

  useEffect(() => {
    setLaedt(true);
    laden(sitzungId).finally(() => setLaedt(false));
  }, [campaignId, sitzungId]);

  const gefiltert = useMemo(() => {
    const nadel = suche.trim().toLowerCase();
    return eintraege.filter((e) => {
      if (kategorie && e.kategorie !== kategorie) return false;
      if (!nadel) return true;
      const hay = `${KATEGORIE_TITEL[e.kategorie] ?? e.kategorie} ${e.kurz} ${e.slNotiz}`.toLowerCase();
      return hay.includes(nadel);
    });
  }, [eintraege, kategorie, suche]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuDatum) return;
    const neu = await protokollApi.anlegen(campaignId, { datum: neuDatum, titel: neuTitel.trim() });
    setAnlegenOffen(false);
    setNeuTitel("");
    setSitzungId(neu.id);
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Protokoll…</p>;

  return (
    <div className="ep-seite">
      <div className="ep-kopf">
        <select value={sitzungId} onChange={(ev) => setSitzungId(ev.target.value)} aria-label="Sitzung">
          <option value="">Alle Sitzungen</option>
          {sitzungen.map((s) => (
            <option key={s.id} value={s.id}>
              {s.datum}
              {s.titel ? ` — ${s.titel}` : ""}
            </option>
          ))}
        </select>
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Sitzung
        </button>
        <input
          className="ep-suche"
          type="search"
          placeholder="Suche…"
          value={suche}
          onChange={(ev) => setSuche(ev.target.value)}
        />
        <span className="ep-anzahl">{gefiltert.length} Einträge</span>
      </div>

      <div className="ep-filter">
        <button type="button" data-an={kategorie === "" ? "true" : undefined} onClick={() => setKategorie("")}>
          Alle
        </button>
        {Object.entries(KATEGORIE_TITEL).map(([id, name]) => (
          <button
            key={id}
            type="button"
            data-an={kategorie === id ? "true" : undefined}
            onClick={() => setKategorie(kategorie === id ? "" : id)}
          >
            {name}
          </button>
        ))}
      </div>

      {gefiltert.length === 0 && (
        <p className="ep-leer">
          Noch keine Einträge
          {sitzungId ? " in dieser Sitzung" : ""}. Spielzüge mit Auto-Hooks erscheinen hier von selbst.
        </p>
      )}

      {gefiltert.length > 0 && (
        <ol className="ep-liste">
          {gefiltert.map((e) => (
            <li key={e.id} className="ep-zeile cl-roehre">
              <span className="ep-zeit">{uhr(e.zeitpunkt)}</span>
              <span className="ep-kat">{KATEGORIE_TITEL[e.kategorie] ?? e.kategorie}</span>
              <span className="ep-kurz">{e.kurz || "—"}</span>
              {e.slNotiz && <span className="ep-notiz">{e.slNotiz}</span>}
            </li>
          ))}
        </ol>
      )}

      <Fenster
        offen={anlegenOffen}
        titel="Neue Sitzung"
        kennung="sitzung-anlegen"
        onSchliessen={() => setAnlegenOffen(false)}
      >
        <form className="ep-form" onSubmit={anlegen}>
          <label>
            Datum
            <input type="date" value={neuDatum} onChange={(ev) => setNeuDatum(ev.target.value)} required />
          </label>
          <label>
            Titel
            <input value={neuTitel} onChange={(ev) => setNeuTitel(ev.target.value)} placeholder="Session 14" />
          </label>
          <button type="submit">Anlegen</button>
        </form>
      </Fenster>
    </div>
  );
}
