import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Fenster } from "../shell/Fenster";
import { drohnenApi, type DrohnenEintrag } from "./api";
import { DrohnenFenster } from "./DrohnenFenster";
import { kampfApi, type HotStatus } from "../kampf/api";
import "../items/gegenstaende.css";

/**
 * Burgermenü "Fahrzeuge & Drohnen" (25.10.2026, Phase 3) — für SL und
 * Spieler sichtbar, siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
 *
 * Aktiv verbundene (riggerAktiv=true) Boards stehen oben, optisch
 * hervorgehoben (Rahmenfarbe) — sie sind die, die gerade am Kampf
 * teilnehmen. Alle übrigen darunter mit Aktivieren-Knopf. Anlegen und
 * Rigger-Zuweisung bleibt SL-Sache (siehe `DrohnenFenster`), Spieler sehen
 * hier nur, was sichtbar freigegeben ist (Server filtert, siehe
 * `entities/routes.py::list_drohnen`).
 */
export function DrohnenUebersicht({
  campaignId,
  istGm,
  eigenePersonId = null,
}: {
  campaignId: string;
  istGm: boolean;
  eigenePersonId?: string | null;
}) {
  const [liste, setListe] = useState<DrohnenEintrag[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenFuer, setOffenFuer] = useState<DrohnenEintrag | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [suche, setSuche] = useState("");
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);
  const [hot, setHot] = useState<HotStatus | null>(null);

  async function neuLaden() {
    const [d, p, h] = await Promise.all([
      drohnenApi.liste(campaignId),
      istGm ? entitiesApi.listPersonen(campaignId) : Promise.resolve([]),
      eigenePersonId ? kampfApi.hotStatus(campaignId).catch(() => null) : Promise.resolve(null),
    ]);
    setListe(d);
    setPersonen(p);
    setHot(h);
  }

  async function hotGehen(drohneId: string) {
    setFehler(null);
    try {
      setHot(await kampfApi.hotDrohne(campaignId, drohneId));
      await neuLaden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Hot gerade nicht möglich.");
    }
  }

  useEffect(() => {
    setLaden(true);
    neuLaden()
      .catch(() => setFehler("Drohnen/Fahrzeuge konnten nicht geladen werden."))
      .finally(() => setLaden(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  const personenNamen = useMemo(
    () => personen.map((p) => ({ id: p.id, label: `${p.name} (${p.personType})` })),
    [personen],
  );

  // Für den Sichtbarkeits-Auswahlknopf im Detail-Fenster (SPEZIFISCH-Modus):
  // nur PCs sind sinnvolle Ziele, ein NPC-Rigger kann das Fenster eh nicht
  // selbst öffnen.
  const pcOptions = useMemo(
    () => personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name })),
    [personen],
  );

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return liste;
    return liste.filter((d) => `${d.name} ${d.riggerName ?? ""}`.toLowerCase().includes(s));
  }, [liste, suche]);

  const aktive = gefiltert.filter((d) => d.riggerAktiv);
  const uebrige = gefiltert.filter((d) => !d.riggerAktiv);

  // Riggerkonsole-Slots als echte Kästchen statt nur als Text-Badge
  // (26.10.2026, Mark: "leere Kästchen, simultan zur Menge an zu
  // kontrollierenden Drohnen durch die Riggerkonsole" — eine Reihe pro
  // Rigger, so viele Boxen wie `riggerSlotsMax`, aktive Drohnen wandern
  // optisch rein (blau), der Rest bleibt eine leere Box. Nur die BESTE
  // ausgerüstete Konsole zählt serverseitig (`riggerkonsole_max_drohnen`
  // nimmt `max()`, keine Summe) — "man kann nicht 10 billige kaufen" gilt
  // also schon. Die Hot-Drohne (28.10., noch nicht gebaut) ist magenta
  // pulsierend umrandet (`--p-magenta`), hier und im Kampf — nicht nur die
  // linke Slot-Box. Aktive-aber-nicht-Hot bleibt blau.
  const riggerSlotGruppen = useMemo(() => {
    const map = new Map<string, { name: string; slotsMax: number; aktiv: DrohnenEintrag[] }>();
    for (const d of gefiltert) {
      if (!d.riggerId) continue;
      if (!map.has(d.riggerId)) {
        map.set(d.riggerId, { name: d.riggerName ?? "Rigger", slotsMax: d.riggerSlotsMax ?? 0, aktiv: [] });
      }
      if (d.riggerAktiv) map.get(d.riggerId)!.aktiv.push(d);
    }
    return [...map.entries()].filter(([, g]) => g.slotsMax > 0 || g.aktiv.length > 0);
  }, [gefiltert]);

  useEffect(() => setSeite(0), [suche]);
  const seiten = Math.max(1, Math.ceil(uebrige.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbarUebrige = uebrige.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  async function aktivieren(d: DrohnenEintrag) {
    setFehler(null);
    try {
      await drohnenApi.aktivSetzen(campaignId, d.id, true);
      await neuLaden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht aktiviert werden.");
    }
  }

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Fahrzeuge & Drohnen…</p>;

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <div className="gg-kopf">
        <input
          className="gg-suche"
          type="search"
          placeholder="Suchen — Name oder Rigger"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
        {istGm && (
          <button type="button" onClick={() => setAnlegenOffen(true)}>
            + Neu
          </button>
        )}
        <span className="gg-anzahl">
          {gefiltert.length} von {liste.length}
        </span>
      </div>

      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

      {riggerSlotGruppen.map(([riggerId, gruppe]) => (
        <div className="gg-slotreihe" key={riggerId}>
          <h3 style={{ margin: "4px 0", fontSize: 12, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--ja)" }}>
            {gruppe.name} — Riggerkonsole ({gruppe.aktiv.length}/{gruppe.slotsMax || gruppe.aktiv.length})
          </h3>
          <div className="gg-slotboxen">
            {Array.from({ length: Math.max(gruppe.slotsMax, gruppe.aktiv.length) }).map((_, i) => {
              const d = gruppe.aktiv[i];
              if (!d) {
                return (
                  <div className="gg-slotbox-leer" key={i}>
                    frei
                  </div>
                );
              }
              return (
                <div className="gg-slot-spalte" key={d.id}>
                  <button
                    type="button"
                    className={`gg-kachel${d.istHot ? " gg-slot-hot" : ""}`}
                    style={d.istHot ? undefined : { borderColor: "var(--ja)", boxShadow: "0 0 8px var(--ja)" }}
                    onClick={() => setOffenFuer(d)}
                    title={d.name}
                  >
                    <span className="gg-kachel-bild">
                      {d.bildUrl ? <img src={d.bildUrl} alt="" /> : <span aria-hidden="true">⛭</span>}
                    </span>
                    <span className="gg-kachel-name">{d.name}</span>
                    <span className="gg-kachel-zeile">{d.istFahrzeug ? "Fahrzeug" : "Drohne"}</span>
                  </button>
                  {eigenePersonId && d.riggerId === eigenePersonId && hot?.hatNeurolink && (
                    <button
                      type="button"
                      className="gg-hot-knopf"
                      disabled={d.istHot || hot.darfWaehlen === false}
                      onClick={() => hotGehen(d.id)}
                    >
                      Hot
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <h3 style={{ margin: "10px 0 4px", fontSize: 12, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-leise)" }}>
        {aktive.length > 0 ? "Alle übrigen" : "Fahrzeuge & Drohnen"}
      </h3>
      <div className="gg-raster" ref={rasterRef}>
        {sichtbarUebrige.map((d) => (
          <div key={d.id} className="gg-kachel" style={{ display: "flex", flexDirection: "column" }}>
            <button type="button" style={{ all: "unset", cursor: "pointer", display: "contents" }} onClick={() => setOffenFuer(d)}>
              <span className="gg-kachel-bild">
                {d.bildUrl ? <img src={d.bildUrl} alt="" /> : <span aria-hidden="true">⛭</span>}
              </span>
              <span className="gg-kachel-name">{d.name}</span>
              <span className="gg-kachel-zeile">{d.istFahrzeug ? "Fahrzeug" : "Drohne"}</span>
              <span className="gg-kachel-marken">
                <span className="gg-marke">{d.riggerName ?? "ungebunden"}</span>
                {d.riggerSlotsMax != null && (
                  <span className="gg-marke" title="Aktive Slots der Riggerkonsole">
                    {d.riggerSlotsBelegt}/{d.riggerSlotsMax} Slots
                  </span>
                )}
              </span>
            </button>
            {d.riggerId && (
              <button type="button" style={{ marginTop: 6 }} onClick={() => aktivieren(d)}>
                Aktivieren
              </button>
            )}
          </div>
        ))}
      </div>

      {liste.length === 0 && (
        <p className="gg-leer">
          {istGm ? "Noch keine Drohne/kein Fahrzeug angelegt." : "Die Spielleitung hat noch keine Drohne/kein Fahrzeug freigegeben."}
        </p>
      )}
      {liste.length > 0 && gefiltert.length === 0 && <p className="gg-leer">Nichts gefunden.</p>}

      {seiten > 1 && (
        <div className="gg-blaettern">
          <button type="button" onClick={() => setSeite((n) => Math.max(0, n - 1))} disabled={aktuelleSeite === 0}>
            ‹
          </button>
          <span>
            {aktuelleSeite + 1} / {seiten}
          </span>
          <button type="button" onClick={() => setSeite((n) => Math.min(seiten - 1, n + 1))} disabled={aktuelleSeite >= seiten - 1}>
            ›
          </button>
        </div>
      )}

      {istGm && anlegenOffen && (
        <DrohnenAnlegenFenster
          campaignId={campaignId}
          onSchliessen={() => setAnlegenOffen(false)}
          onAngelegt={async (id) => {
            setAnlegenOffen(false);
            await neuLaden();
            const frisch = await drohnenApi.liste(campaignId);
            setOffenFuer(frisch.find((d) => d.id === id) ?? null);
          }}
        />
      )}

      {offenFuer && (
        <DrohnenFenster
          campaignId={campaignId}
          drohneId={offenFuer.id}
          riggerId={offenFuer.riggerId}
          riggerAktiv={offenFuer.riggerAktiv}
          riggerSlotsBelegt={offenFuer.riggerSlotsBelegt}
          riggerSlotsMax={offenFuer.riggerSlotsMax}
          personen={personenNamen}
          pcOptions={pcOptions}
          sichtbarkeit={offenFuer.sichtbarkeit}
          sichtbarFuer={offenFuer.sichtbarFuer}
          istGm={istGm}
          onSchliessen={() => setOffenFuer(null)}
          onGeaendert={async () => {
            await neuLaden();
            const frisch = await drohnenApi.liste(campaignId);
            setOffenFuer(frisch.find((d) => d.id === offenFuer.id) ?? null);
          }}
        />
      )}
    </div>
  );
}

/** Anlegen-Popup: Name + Art (Drohne/Fahrzeug) — Rest (Rigger, Werte) folgt
 * im Detail-Fenster, genau wie bei Critter/KI in BegleiterVerwaltung. */
function DrohnenAnlegenFenster({
  campaignId,
  onSchliessen,
  onAngelegt,
}: {
  campaignId: string;
  onSchliessen: () => void;
  onAngelegt: (id: string) => void;
}) {
  const [name, setName] = useState("");
  const [art, setArt] = useState<"DROHNE" | "FAHRZEUG">("DROHNE");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || laeuft) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const neu = await entitiesApi.createPerson(campaignId, {
        name: name.trim(),
        personType: "NPC",
        description: "",
        notes: "",
        istDrohne: art === "DROHNE",
        istFahrzeug: art === "FAHRZEUG",
        // Keine Chargen-Wizard-Odyssee für eine Drohne — das Blatt steht
        // sofort fertig da, genau wie beim Kredithai-/Blanko-Kontakt-Stub
        // (hintergruende/spawn.py). Ohne das bleibt Charakterblatt.tsx im
        // PC-Ersterstellungsmodus hängen (Stolperstein, 25.10.2026).
        erstellungAbgeschlossen: true,
        sichtbarkeit: "ALLE",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      onAngelegt(neu.id);
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Anlegen fehlgeschlagen");
      setLaeuft(false);
    }
  }

  return (
    <Fenster offen titel="Neu: Drohne oder Fahrzeug" kennung="drohne-neu" ton="var(--bereich-begleiter)" onSchliessen={onSchliessen}>
      <form onSubmit={anlegen} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
        {fehler && <p style={{ color: "var(--signal)", margin: 0 }}>{fehler}</p>}

        <div className="bg-zeile">
          <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--neon)" }}>Art</span>
          <select value={art} onChange={(e) => setArt(e.target.value as "DROHNE" | "FAHRZEUG")}>
            <option value="DROHNE">⛭ Drohne</option>
            <option value="FAHRZEUG">🚗 Fahrzeug</option>
          </select>
        </div>

        <input
          type="text"
          placeholder="Name"
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
