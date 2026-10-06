import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type CritterEintrag, type Gewaechs, type Person } from "./api";
import type { PersonOption } from "./VisibilitySelector";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Fenster } from "../shell/Fenster";
import { CritterFenster } from "../begleiter/CritterFenster";
import { GewaechsDetail } from "./GewaechsDetail";
import "../items/gegenstaende.css";

/**
 * Flora & Fauna — eigener Burgermenü-Punkt (06.10.2026, Mark: "wir brauchen
 * ein Burgermenü... gleich im neuen Design mit Suchleiste und Neu-Button").
 *
 * Der Ort-Tab (FloraFaunaListe.tsx) zeigt nur, was an EINEM Ort hängt, und
 * zwingt beim Neuanlegen sofort eine Verknüpfung. Diese Übersicht ist der
 * globale Katalog über alle Orte hinweg — Critter (Fauna) und Gewächse
 * (Flora) gemeinsam, frei anlegbar ohne Ort-Zwang. Die Verknüpfung mit
 * einem Ort bleibt Sache des Ort-Tabs, nicht doppelt gebaut.
 *
 * Fauna wird hier BEWUSST nochmal gelistet, obwohl Critter schon unter
 * "❊ Begleiter" eine eigene Suchleiste+Anlegen-Seite haben (Mark hat das
 * explizit so gewollt, 06.10.2026) — beide Seiten greifen auf denselben
 * `entitiesApi.listCritter`/`createPerson`(istCritter)/`CritterFenster`
 * zu, keine zweite Datenquelle oder Bearbeitungslogik.
 *
 * Kachelraster + Anlegen-Popup: dasselbe Muster wie
 * GegenstaendeUebersicht/BegleiterVerwaltung — Suchfeld über Name/Art,
 * "+ Neu" öffnet ein Fenster statt eines Inline-Formulars.
 */
interface KachelEintrag {
  id: string;
  name: string;
  bildUrl: string;
  suchtext: string;
  art: "CRITTER" | "GEWAECHS";
  besitzerName: string | null;
}

export function FloraFaunaUebersicht({ campaignId }: { campaignId: string }) {
  const [critter, setCritter] = useState<CritterEintrag[]>([]);
  const [gewaechse, setGewaechse] = useState<Gewaechs[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [laden, setLaden] = useState(true);
  const [critterOffen, setCritterOffen] = useState<CritterEintrag | null>(null);
  const [gewaechsOffen, setGewaechsOffen] = useState<Gewaechs | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [suche, setSuche] = useState("");
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);

  async function neuLaden() {
    const [c, g, p] = await Promise.all([
      entitiesApi.listCritter(campaignId),
      entitiesApi.listGewaechse(campaignId),
      entitiesApi.listPersonen(campaignId),
    ]);
    setCritter(c);
    setGewaechse(g);
    setPersonen(p);
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId]);

  // Für GewaechsDetail (Sichtbarkeits-Auswahl "für welchen PC freigeben").
  const pcOptions: PersonOption[] = useMemo(
    () => personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name })),
    [personen],
  );
  // Für CritterFenster (Besitzer-Auswahl unter den Menschen der Kampagne).
  const personenNamen = useMemo(
    () => personen.map((p) => ({ id: p.id, label: `${p.name} (${p.personType})` })),
    [personen],
  );

  const kacheln = useMemo<KachelEintrag[]>(() => {
    const c: KachelEintrag[] = critter.map((x) => ({
      id: x.id,
      name: x.name,
      bildUrl: x.bildUrl,
      suchtext: `${x.name} fauna critter ${x.besitzerName ?? ""}`.toLowerCase(),
      art: "CRITTER" as const,
      besitzerName: x.besitzerName,
    }));
    const g: KachelEintrag[] = gewaechse.map((x) => ({
      id: x.id,
      name: x.name,
      bildUrl: x.bildUrl ?? "",
      suchtext: `${x.name} flora gewächs gewaechs`.toLowerCase(),
      art: "GEWAECHS" as const,
      besitzerName: null,
    }));
    return [...c, ...g].sort((a, b) => a.name.localeCompare(b.name, "de"));
  }, [critter, gewaechse]);

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return kacheln;
    return kacheln.filter((k) => k.suchtext.includes(s));
  }, [kacheln, suche]);

  // Nach einer neuen Suche kann die aktuelle Seite hinter dem gefilterten
  // Ende liegen — zurück auf die erste Seite, sonst wirkt die Liste leer.
  useEffect(() => {
    setSeite(0);
  }, [suche]);

  const seiten = Math.max(1, Math.ceil(gefiltert.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = gefiltert.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Flora & Fauna…</p>;

  function kachelOeffnen(k: KachelEintrag) {
    if (k.art === "CRITTER") {
      const gefunden = critter.find((c) => c.id === k.id);
      if (gefunden) setCritterOffen(gefunden);
    } else {
      const gefunden = gewaechse.find((g) => g.id === k.id);
      if (gefunden) setGewaechsOffen(gefunden);
    }
  }

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <div className="gg-kopf">
        <input
          className="gg-suche"
          type="search"
          placeholder="Suchen — Name oder Art"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neu
        </button>
        <span className="gg-anzahl">
          {gefiltert.length} von {kacheln.length}
        </span>
      </div>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((k) => (
          <button
            key={`${k.art}-${k.id}`}
            type="button"
            className="gg-kachel"
            onClick={() => kachelOeffnen(k)}
            title={k.name}
          >
            <span className="gg-kachel-bild">
              {k.bildUrl ? (
                <img src={k.bildUrl} alt="" />
              ) : (
                <span aria-hidden="true">{k.art === "CRITTER" ? "❖" : "🌿"}</span>
              )}
            </span>
            <span className="gg-kachel-name">{k.name}</span>
            <span className="gg-kachel-zeile">{k.art === "CRITTER" ? "Fauna · Critter" : "Flora · Gewächs"}</span>
            {k.art === "CRITTER" && (
              <span className="gg-kachel-marken">
                <span className="gg-marke">{k.besitzerName ?? "ungebunden"}</span>
              </span>
            )}
          </button>
        ))}
      </div>

      {kacheln.length === 0 && <p className="gg-leer">Noch keine Flora oder Fauna in dieser Kampagne.</p>}
      {kacheln.length > 0 && gefiltert.length === 0 && <p className="gg-leer">Nichts gefunden.</p>}

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

      {anlegenOffen && (
        <FloraFaunaAnlegenFenster
          campaignId={campaignId}
          onSchliessen={() => setAnlegenOffen(false)}
          onCritterAngelegt={async (id) => {
            setAnlegenOffen(false);
            const gefunden = await entitiesApi.listCritter(campaignId);
            setCritter(gefunden);
            setCritterOffen(gefunden.find((c) => c.id === id) ?? null);
          }}
          onGewaechsAngelegt={async (id) => {
            setAnlegenOffen(false);
            await neuLaden();
            setGewaechsOffen(await entitiesApi.getGewaechs(campaignId, id));
          }}
        />
      )}

      {critterOffen && (
        <CritterFenster
          campaignId={campaignId}
          critterId={critterOffen.id}
          besitzerId={critterOffen.besitzerId}
          personen={personenNamen}
          onSchliessen={() => setCritterOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setCritterOffen(null);
          }}
        />
      )}

      {gewaechsOffen && (
        <GewaechsDetail
          campaignId={campaignId}
          gewaechs={gewaechsOffen}
          pcOptions={pcOptions}
          onSchliessen={() => setGewaechsOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setGewaechsOffen(await entitiesApi.getGewaechs(campaignId, gewaechsOffen.id));
          }}
        />
      )}
    </div>
  );
}

/**
 * Popup zum freien Neuanlegen: Art wählen (Critter/Gewächs), Name eingeben,
 * anlegen — OHNE Ort-Zwang. Die Verknüpfung mit einem Ort passiert optional
 * später über den "Flora & Fauna"-Tab am Ort selbst
 * (FloraFaunaListe.tsx::FloraFaunaHinzufuegenFenster), nicht hier.
 */
function FloraFaunaAnlegenFenster({
  campaignId,
  onSchliessen,
  onCritterAngelegt,
  onGewaechsAngelegt,
}: {
  campaignId: string;
  onSchliessen: () => void;
  onCritterAngelegt: (id: string) => void;
  onGewaechsAngelegt: (id: string) => void;
}) {
  const [art, setArt] = useState<"CRITTER" | "GEWAECHS">("CRITTER");
  const [name, setName] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || laeuft) return;
    setLaeuft(true);
    setFehler(null);
    try {
      if (art === "CRITTER") {
        const neu = await entitiesApi.createPerson(campaignId, {
          name: name.trim(),
          personType: "NPC",
          description: "",
          notes: "",
          istCritter: true,
          sichtbarkeit: "GM",
          sichtbarFuer: [],
          notizenSichtbarkeit: "GM",
          notizenSichtbarFuer: [],
        });
        onCritterAngelegt(neu.id);
      } else {
        const neu = await entitiesApi.createGewaechs(campaignId, {
          name: name.trim(),
          description: "",
          notes: "",
          sichtbarkeit: "GM",
          sichtbarFuer: [],
          notizenSichtbarkeit: "GM",
          notizenSichtbarFuer: [],
        });
        onGewaechsAngelegt(neu.id);
      }
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Anlegen fehlgeschlagen");
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen
      titel="Neu: Flora oder Fauna"
      unterzeile="Ohne Ort — Verknüpfung geht später über den Ort selbst"
      kennung="flora-fauna-neu"
      onSchliessen={onSchliessen}
    >
      <form onSubmit={anlegen} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
        {fehler && <p style={{ color: "var(--signal)", margin: 0 }}>{fehler}</p>}

        <div className="bg-zeile">
          <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--neon)" }}>
            Art
          </span>
          <select value={art} onChange={(e) => setArt(e.target.value as "CRITTER" | "GEWAECHS")}>
            <option value="CRITTER">❖ Fauna (Critter)</option>
            <option value="GEWAECHS">🌿 Flora (Gewächs)</option>
          </select>
        </div>

        <input
          type="text"
          placeholder={art === "CRITTER" ? "Name des Critters" : "Name des Gewächses"}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
          style={{ fontSize: "1.1rem", padding: "12px 14px" }}
        />

        <button
          type="submit"
          disabled={laeuft || !name.trim()}
          style={{
            padding: "12px 20px",
            background: "color-mix(in srgb, var(--ja) 20%, transparent)",
            border: "1px solid var(--ja)",
            borderRadius: "var(--radius)",
            color: "var(--ja)",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "1rem",
          }}
        >
          {laeuft ? "Legt an…" : "Anlegen"}
        </button>
      </form>
    </Fenster>
  );
}
