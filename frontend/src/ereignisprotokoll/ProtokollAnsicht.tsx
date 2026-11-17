import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Fenster } from "../shell/Fenster";
import { KATEGORIE_TITEL, protokollApi, sitzungName, type Sitzung, type ZeitleisteEintrag } from "./api";
import "./protokoll.css";

function uhr(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
}

const ANLASS_TITEL: Record<string, string> = {
  beratung: "Beratung",
  "idee-story": "Story generiert",
  "idee-gegenstand": "Gegenstand generiert",
  "idee-ort": "Ort generiert",
  "idee-event": "Ereignis generiert",
  "idee-fraktion": "Fraktion generiert",
  "idee-verbindung": "Verbindung generiert",
  "idee-charakter": "Charakter generiert",
  nebenfigur: "Nebenfigur generiert",
  "nebenfigur-zu-npc": "Nebenfigur zum NPC",
  "objekt-text": "Objekttext",
  "bild-prompt": "Bild-Prompt",
  "bild-generieren": "Bild generiert",
  "wiki-pruefung": "Wiki-Prüfung",
  "auto-verknuepfung": "Verknüpfung",
  "beziehungen-aus-beschreibungen": "Beziehungen",
  achievement_text: "Achievement-Text",
  "erstellung-kommentar": "Erstellungs-Kommentar",
};

function detailLabels(anlass: string): { titel: string; links: string; rechts: string } {
  const titel = ANLASS_TITEL[anlass] ?? (anlass ? anlass.replace(/[-_]/g, " ") : "KI");
  if (anlass === "beratung") return { titel, links: "Frage", rechts: "Antwort" };
  if (anlass.startsWith("idee-") || anlass === "nebenfigur" || anlass === "nebenfigur-zu-npc") {
    return { titel, links: "Wunsch", rechts: "Generiert" };
  }
  return { titel, links: "Eingabe", rechts: "Ausgabe" };
}

export function ProtokollAnsicht({ campaignId }: { campaignId: string }) {
  const [sitzungen, setSitzungen] = useState<Sitzung[]>([]);
  const [sitzungId, setSitzungId] = useState<string>("");
  const [eintraege, setEintraege] = useState<ZeitleisteEintrag[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [kategorie, setKategorie] = useState<string>("");
  const [eventId, setEventId] = useState("");
  const [suche, setSuche] = useState("");
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuDatum, setNeuDatum] = useState(() => new Date().toISOString().slice(0, 10));
  const [neuTitel, setNeuTitel] = useState("");
  const [neuNummer, setNeuNummer] = useState("");
  const [schaltet, setSchaltet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [detail, setDetail] = useState<ZeitleisteEintrag | null>(null);

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
    const treffer = eintraege.filter((e) => {
      if (kategorie && e.kategorie !== kategorie) return false;
      if (eventId && !(e.eventIds ?? []).includes(eventId)) return false;
      if (!nadel) return true;
      const hay = `${KATEGORIE_TITEL[e.kategorie] ?? e.kategorie} ${e.kurz} ${e.slNotiz} ${e.prompt ?? ""} ${e.antwort ?? ""} ${(e.eventNamen ?? []).join(" ")}`.toLowerCase();
      return hay.includes(nadel);
    });
    // Neu oben, alt unten. Die API liefert das schon so; hier nochmal, falls
    // eine alte Antwort ungeordnet ankommt.
    return [...treffer].sort((a, b) => (b.zeitpunkt || "").localeCompare(a.zeitpunkt || ""));
  }, [eintraege, kategorie, eventId, suche]);

  const events = useMemo(() => {
    const map = new Map<string, string>();
    for (const e of eintraege) {
      (e.eventIds ?? []).forEach((id, i) => {
        if (!map.has(id)) map.set(id, e.eventNamen?.[i] || id);
      });
    }
    return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1], "de"));
  }, [eintraege]);

  // Starten/Beenden (Mark, 16.11.2026: „einen Session aktiv und deaktiviert
  // Button, wo ich die Nummer eintragen kann“). Aktiv ist höchstens eine.
  const aktive = sitzungen.find((s) => s.aktiv) ?? null;
  const gewaehlt = sitzungen.find((s) => s.id === sitzungId) ?? null;

  function startenOeffnen() {
    const hoechste = Math.max(0, ...sitzungen.map((s) => s.nummer ?? 0));
    setNeuNummer(String(hoechste + 1));
    setNeuDatum(new Date().toISOString().slice(0, 10));
    setNeuTitel("");
    setFehler(null);
    setAnlegenOffen(true);
  }

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuDatum) return;
    const nummer = neuNummer.trim() ? Number(neuNummer) : null;
    try {
      const neu = await protokollApi.anlegen(campaignId, {
        datum: neuDatum,
        titel: neuTitel.trim(),
        nummer: nummer != null && Number.isFinite(nummer) ? nummer : null,
      });
      setAnlegenOffen(false);
      setNeuTitel("");
      setSitzungId(neu.id);
      if (neu.id === sitzungId) await laden(neu.id);
    } catch {
      setFehler("Starten ging nicht.");
    }
  }

  async function aktivSetzen(s: Sitzung, aktiv: boolean) {
    setSchaltet(true);
    setFehler(null);
    try {
      await protokollApi.aktivSetzen(campaignId, s.id, aktiv);
      await laden(sitzungId);
    } catch {
      setFehler(aktiv ? "Fortsetzen ging nicht." : "Beenden ging nicht.");
    } finally {
      setSchaltet(false);
    }
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Protokoll…</p>;

  return (
    <div className="ep-seite">
      <div className="ep-status cl-roehre" data-aktiv={aktive ? "true" : undefined}>
        <span className="ep-status-text">
          {aktive ? `${sitzungName(aktive)} läuft` : "Keine Session aktiv"}
        </span>
        {aktive ? (
          <button type="button" disabled={schaltet} onClick={() => aktivSetzen(aktive, false)}>
            {schaltet ? "…" : "Session beenden"}
          </button>
        ) : (
          <button type="button" onClick={startenOeffnen}>
            Session starten
          </button>
        )}
        {gewaehlt && !gewaehlt.aktiv && (
          <button type="button" disabled={schaltet} onClick={() => aktivSetzen(gewaehlt, true)}>
            {sitzungName(gewaehlt)} fortsetzen
          </button>
        )}
        {aktive && (
          <button type="button" onClick={startenOeffnen}>
            Nächste Session
          </button>
        )}
        {fehler && <span className="ep-status-fehler">{fehler}</span>}
      </div>

      <div className="ep-kopf">
        <select value={sitzungId} onChange={(ev) => setSitzungId(ev.target.value)} aria-label="Sitzung">
          <option value="">Alle Sitzungen</option>
          {sitzungen.map((s) => (
            <option key={s.id} value={s.id}>
              {sitzungName(s)}
              {s.nummer != null && s.titel ? ` — ${s.titel}` : ""}
              {` · ${s.datum}`}
              {s.aktiv ? " · läuft" : ""}
            </option>
          ))}
        </select>
        <select value={eventId} onChange={(ev) => setEventId(ev.target.value)} aria-label="Event">
          <option value="">Alle Events</option>
          {events.map(([id, name]) => (
            <option key={id} value={id}>
              {name}
            </option>
          ))}
        </select>
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
          {gefiltert.map((e) => {
            const hatText = Boolean((e.prompt || "").trim() || (e.antwort || "").trim());
            const labels = detailLabels(e.anlass || "");
            return (
              <li key={e.id}>
                <div
                  className="ep-zeile cl-roehre"
                  data-klick={hatText ? "true" : undefined}
                  role={hatText ? "button" : undefined}
                  tabIndex={hatText ? 0 : undefined}
                  onClick={() => hatText && setDetail(e)}
                  onKeyDown={(ev) => {
                    if (!hatText) return;
                    if (ev.key === "Enter" || ev.key === " ") {
                      ev.preventDefault();
                      setDetail(e);
                    }
                  }}
                >
                  <span className="ep-zeit">{uhr(e.zeitpunkt)}</span>
                  <span className="ep-kat">{KATEGORIE_TITEL[e.kategorie] ?? e.kategorie}</span>
                  <span className="ep-kurz">{e.kurz || "—"}</span>
                  {e.slNotiz && <span className="ep-notiz">{e.slNotiz}</span>}
                </div>
                {detail?.id === e.id && (
                  <Fenster
                    offen
                    titel={labels.titel}
                    kennung={`protokoll-${e.id}`}
                    onSchliessen={() => setDetail(null)}
                  >
                    <div className="ep-detail">
                      {e.prompt?.trim() && (
                        <section>
                          <p className="ep-detail-label">{labels.links}</p>
                          <p className="ep-detail-text">{e.prompt}</p>
                        </section>
                      )}
                      {e.antwort?.trim() && (
                        <section>
                          <p className="ep-detail-label">{labels.rechts}</p>
                          <p className="ep-detail-text">{e.antwort}</p>
                        </section>
                      )}
                    </div>
                  </Fenster>
                )}
              </li>
            );
          })}
        </ol>
      )}

      <Fenster
        offen={anlegenOffen}
        titel="Session starten"
        kennung="sitzung-anlegen"
        onSchliessen={() => setAnlegenOffen(false)}
      >
        <form className="ep-form" onSubmit={anlegen}>
          {aktive && <p className="ep-hinweis">{sitzungName(aktive)} wird dabei beendet.</p>}
          <label>
            Nummer
            <input
              type="number"
              min={0}
              inputMode="numeric"
              value={neuNummer}
              onChange={(ev) => setNeuNummer(ev.target.value)}
            />
          </label>
          <label>
            Datum
            <input type="date" value={neuDatum} onChange={(ev) => setNeuDatum(ev.target.value)} required />
          </label>
          <label>
            Titel (optional)
            <input value={neuTitel} onChange={(ev) => setNeuTitel(ev.target.value)} placeholder="Der Überfall" />
          </label>
          {fehler && <p className="ep-status-fehler">{fehler}</p>}
          <button type="submit">Starten</button>
        </form>
      </Fenster>
    </div>
  );
}
