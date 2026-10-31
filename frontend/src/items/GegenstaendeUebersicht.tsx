import { useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useAuthFallsVorhanden } from "../auth/AuthContext";
import { einstellungenApi, formatiereLast, type Einstellungen } from "../campaigns/einstellungen";
import { entitiesApi, type Person } from "../entities/api";
import type { PersonOption } from "../entities/VisibilitySelector";
import { Fenster } from "../shell/Fenster";
import { useNachladen } from "../shell/nachladen";
import { GegenstandRow } from "../traits/CharacterSheetPanel";
import { itemsApi, VORLAGE_SENTINEL, type GegenstandMitBesitzer, type TraglastZeile } from "./api";
import { ermittleBereiche, filtereNachBereichen, standardAuswahl } from "./aufbewahrung";
import { KategorienAuswahl, vorhandeneTypenSortiert } from "./KategorienAuswahl";
import { Muelleimer } from "./Muelleimer";
import { TypKachelAuswahl } from "./TypKachelAuswahl";
import { symbolFuerTyp } from "./typKatalog";
import "./gegenstaende.css";

/** Muss zu den Werten in gegenstaende.css passen (Raster-Ausmessung). */
const KACHEL_BREITE = 148;
const KACHEL_HOEHE = 168;
const ABSTAND = 10;

/**
 * Zählt aus, wie viele Kacheln in die tatsächlich vorhandene Fläche passen.
 *
 * Kern des Leitprinzips "nie scrollen": statt die Liste überlaufen zu lassen,
 * wird gemessen und der Rest geblättert. Rechnet bei jeder Größenänderung neu,
 * damit Hoch- und Querformat am Tablet gleichermaßen aufgehen.
 */
function useProSeite(ref: React.RefObject<HTMLDivElement | null>) {
  const [proSeite, setProSeite] = useState(12);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const messen = () => {
      const { width, height } = el.getBoundingClientRect();
      const spalten = Math.max(1, Math.floor((width + ABSTAND) / (KACHEL_BREITE + ABSTAND)));
      const zeilen = Math.max(1, Math.floor((height + ABSTAND) / (KACHEL_HOEHE + ABSTAND)));
      setProSeite(spalten * zeilen);
    };
    messen();
    const beobachter = new ResizeObserver(messen);
    beobachter.observe(el);
    return () => beobachter.disconnect();
  }, [ref]);

  return proSeite;
}

export function GegenstaendeUebersicht({ campaignId }: { campaignId: string }) {
  const [personen, setPersonen] = useState<Person[]>([]);
  const [items, setItems] = useState<GegenstandMitBesitzer[]>([]);
  const [loading, setLoading] = useState(true);
  const [suche, setSuche] = useState("");
  const [besitzerFilter, setBesitzerFilter] = useState("");
  // Mehrere Bereiche gleichzeitig: in der Praxis will man "Ausgerüstet und
  // Rucksack" sehen, im Auto zusätzlich dessen Inhalt, im Versteck wiederum
  // etwas anderes. Leere Auswahl = alles.
  const [bereichAuswahl, setBereichAuswahl] = useState<Set<string>>(new Set());
  const [auswahlGesetzt, setAuswahlGesetzt] = useState(false);
  // Kategorie-Filter (10.10.2026, Marks Vorgabe): wie im Shop und bei der
  // Erstellung erst den Typ wählen, statt alles auf einmal zu zeigen —
  // bei vielen Gegenständen sonst unübersichtlich. null = "Alle".
  const [kategorie, setKategorie] = useState<string | null>(null);
  const [einstellungen, setEinstellungen] = useState<Einstellungen | null>(null);
  const [traglast, setTraglast] = useState<TraglastZeile[]>([]);
  const [seite, setSeite] = useState(0);
  const [neuName, setNeuName] = useState("");
  // Vorlage ist der mit Abstand häufigste Fall beim Anlegen (Mark, 06.10.2026:
  // "automatisch Vorlage ausgewählt statt 'etwas auswählen'") — die
  // Spielleitung legt meist erst eine Vorlage an und verteilt sie später,
  // statt sofort einen Besitzer zuzuweisen.
  const [neuBesitzer, setNeuBesitzer] = useState(VORLAGE_SENTINEL);
  const [neuTyp, setNeuTyp] = useState<string | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [muelleimerOffen, setMuelleimerOffen] = useState(false);
  // Wie viele Gegenstand-Bearbeiten-Fenster gerade offen sind. Solange
  // eines offen ist, nicht nachladen — sonst kann die Kachel von der
  // Seite rutschen und das Fenster mit sich nehmen.
  const [offeneBearbeitung, setOffeneBearbeitung] = useState(0);
  // Nur die Spielleitung sieht überhaupt, dass es einen Mülleimer gibt —
  // dieselbe Auskunftsregel wie beim Backend (siehe routes.py::liste_weggeworfen).
  const istGm = useAuthFallsVorhanden()?.me?.role === "GM";

  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);

  function anwenden(d: {
    p: Person[];
    i: GegenstandMitBesitzer[];
    e: Einstellungen;
    t: TraglastZeile[];
  }) {
    setPersonen(d.p);
    setItems(d.i);
    setEinstellungen(d.e);
    setTraglast(d.t);
    setLoading(false);
  }

  async function ladeDaten() {
    const [p, i, e, t] = await Promise.all([
      entitiesApi.listPersonen(campaignId),
      itemsApi.listAlle(campaignId),
      einstellungenApi.lesen(campaignId),
      itemsApi.traglast(campaignId),
    ]);
    return { p, i, e, t };
  }

  const { ungueltig } = useNachladen(ladeDaten, anwenden, {
    // Anlegen und Mülleimer sind auch Fenster mit eigenem Stand.
    pausiert: offeneBearbeitung > 0 || anlegenOffen || muelleimerOffen,
    quelle: campaignId,
  });

  async function refresh() {
    ungueltig();
    const d = await ladeDaten();
    ungueltig();
    anwenden(d);
  }

  function meldeBearbeiten(offen: boolean) {
    setOffeneBearbeitung((n) => Math.max(0, n + (offen ? 1 : -1)));
  }

  const pcOptions: PersonOption[] = useMemo(
    () => personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name })),
    [personen],
  );
  const alleOptionen: PersonOption[] = useMemo(
    () => personen.map((p) => ({ id: p.id, name: `${p.name} (${p.personType})` })),
    [personen],
  );

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    return items.filter((i) => {
      if (besitzerFilter === VORLAGE_SENTINEL && i.ownerId !== null) return false;
      if (besitzerFilter && besitzerFilter !== VORLAGE_SENTINEL && i.ownerId !== besitzerFilter) return false;
      if (kategorie !== null && i.typ !== kategorie) return false;
      if (!s) return true;
      // Auch Typ und Besitzer durchsuchen — "alle Waffen von Kira" ist die
      // häufigere Frage als der exakte Gegenstandsname.
      return (
        i.name.toLowerCase().includes(s) ||
        i.typ.toLowerCase().includes(s) ||
        (i.ownerName ?? "").toLowerCase().includes(s)
      );
    });
  }, [items, suche, besitzerFilter, kategorie]);

  // Welche Kategorien überhaupt vorkommen — gemessen am Besitzerfilter,
  // nicht an der schon kategorie-gefilterten Liste, sonst verschwänden die
  // übrigen Kacheln, sobald man eine anklickt.
  const vorhandeneTypen = useMemo(() => {
    const basis = items.filter((i) => {
      if (besitzerFilter === VORLAGE_SENTINEL) return i.ownerId === null;
      if (besitzerFilter) return i.ownerId === besitzerFilter;
      return true;
    });
    return vorhandeneTypenSortiert(basis.map((i) => i.typ));
  }, [items, besitzerFilter]);

  // Der Behältername passt nur, wenn genau eine Person gefiltert ist —
  // sonst stünde der Rucksack eines Spielers über den Sachen aller.
  const bereiche = useMemo(
    () => ermittleBereiche(items, Boolean(besitzerFilter) && besitzerFilter !== VORLAGE_SENTINEL),
    [items, besitzerFilter],
  );

  // Beim ersten Laden auf "am Körper" vorwählen — aber nur einmal, sonst
  // liesse sich die Auswahl nie wieder leeren.
  useEffect(() => {
    // Erst wenn Gegenstände geladen sind — vorher kennt ermittleBereiche nur
    // "Ausgerüstet" und die Vorauswahl bliebe unvollständig stehen.
    if (!auswahlGesetzt && items.length > 0) {
      setBereichAuswahl(standardAuswahl(bereiche));
      setAuswahlGesetzt(true);
    }
  }, [bereiche, items.length, auswahlGesetzt]);

  const sichtbareItems = filtereNachBereichen(gefiltert, bereiche, bereichAuswahl);

  // Wie viele Gegenstände in jedem Behälter liegen — dieselbe Grundlage wie
  // die Reiter-Zahl (gefiltert, nicht die ganze Kampagne), damit Kachel-Badge
  // und Reiter nie widersprüchlich wirken (31.10.2026, Mark: "sehen was
  // darin ist, eventuell direkt in der Übersicht").
  const inhaltProBehaelter = useMemo(() => {
    const zaehler = new Map<string, number>();
    for (const g of gefiltert) {
      if (!g.ablageZielId) continue;
      zaehler.set(g.ablageZielId, (zaehler.get(g.ablageZielId) ?? 0) + 1);
    }
    return zaehler;
  }, [gefiltert]);

  function schalteBereich(id: string) {
    setBereichAuswahl((alt) => {
      const neu = new Set(alt);
      if (neu.has(id)) neu.delete(id);
      else neu.add(id);
      return neu;
    });
  }

  // Nach dem Filtern kann die aktuelle Seite hinter dem Ende liegen
  const seiten = Math.max(1, Math.ceil(sichtbareItems.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = sichtbareItems.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  useEffect(() => {
    setSeite(0);
  }, [suche, besitzerFilter, bereichAuswahl, kategorie]);

  // Wer über seiner Grenze liegt — die Spielleitung soll es auf einen Blick
  // sehen und selbst entscheiden, was daraus folgt.
  const ueberladen = traglast.filter((z) => z.kapazitaet > 0 && z.last > z.kapazitaet);

  async function removeItem(itemId: string) {
    await itemsApi.remove(campaignId, itemId);
    await refresh();
  }

  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim() || !neuBesitzer || !neuTyp) return;
    if (neuBesitzer === VORLAGE_SENTINEL) {
      await itemsApi.createVorlage(campaignId, { name: neuName, typ: neuTyp });
    } else {
      await itemsApi.create(campaignId, neuBesitzer, { name: neuName, typ: neuTyp });
    }
    setNeuName("");
    setNeuBesitzer(VORLAGE_SENTINEL);
    setNeuTyp(null);
    setAnlegenOffen(false);
    await refresh();
  }

  if (loading) return <p style={{ color: "var(--text-leise)" }}>Lade Gegenstände…</p>;

  return (
    <div
      className="gg-seite"
      style={
        {
          "--gg-kachel-breite": `${KACHEL_BREITE}px`,
          "--gg-kachel-hoehe": `${KACHEL_HOEHE}px`,
          "--gg-abstand": `${ABSTAND}px`,
        } as React.CSSProperties
      }
    >
      <div className="gg-kopf">
        <input
          className="gg-suche"
          type="search"
          placeholder="Suchen — Name, Typ oder Besitzer"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
        <select value={besitzerFilter} onChange={(e) => setBesitzerFilter(e.target.value)}>
          <option value="">Alle Besitzer</option>
          <option value={VORLAGE_SENTINEL}>Nur Vorlagen</option>
          {alleOptionen.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neuer Gegenstand
        </button>
        {istGm && (
          <button type="button" onClick={() => setMuelleimerOffen(true)} title="Weggeworfene Gegenstände">
            🗑 Mülleimer
          </button>
        )}
        <span className="gg-anzahl">
          {sichtbareItems.length} von {items.length}
        </span>
      </div>

      {/* Neuer Gegenstand Popup */}
      <Fenster
        offen={anlegenOffen}
        titel="Neuer Gegenstand"
        unterzeile={neuTyp ? `Typ: ${neuTyp}` : "Zuerst den Typ wählen"}
        kennung="neuer-gegenstand"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
          setNeuBesitzer(VORLAGE_SENTINEL);
          setNeuTyp(null);
        }}
      >
        {!neuTyp ? (
          <TypKachelAuswahl onWaehlen={setNeuTyp} />
        ) : (
          <form onSubmit={addItem} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
            <span className="gg-typ-gewaehlt">
              {symbolFuerTyp(neuTyp)} {neuTyp}
              <button type="button" onClick={() => setNeuTyp(null)}>
                ändern
              </button>
            </span>
            <select
              value={neuBesitzer}
              onChange={(e) => setNeuBesitzer(e.target.value)}
              required
              style={{ fontSize: "1rem", padding: "10px 12px" }}
            >
              <option value="">Besitzer wählen…</option>
              <option value={VORLAGE_SENTINEL}>— Vorlage (kein Besitzer) —</option>
              {alleOptionen.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Name des Gegenstands"
              value={neuName}
              onChange={(e) => setNeuName(e.target.value)}
              required
              autoFocus
              style={{ fontSize: "1.1rem", padding: "12px 14px" }}
            />
            <button
              type="submit"
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
              Gegenstand erstellen
            </button>
          </form>
        )}
      </Fenster>

      {einstellungen?.gewichtAktiv && ueberladen.length > 0 && (
        <div className="gg-ueberladen">
          <strong>⚠ Überladen:</strong>
          {ueberladen.map((z) => (
            <span key={z.id}>
              {z.name} <span className="mono">{formatiereLast(z.last, z.kapazitaet)}</span>
            </span>
          ))}
        </div>
      )}

      <KategorienAuswahl vorhandeneTypen={vorhandeneTypen} gewaehlt={kategorie} onWaehlen={setKategorie} />

      <div className="gg-reiter">
        {bereiche.map((b) => (
          <button
            key={b.id}
            type="button"
            data-aktiv={bereichAuswahl.has(b.id)}
            onClick={() => schalteBereich(b.id)}
            title="Mehrere Bereiche lassen sich gleichzeitig anzeigen"
          >
            {b.symbol} {b.name} <span className="gg-reiter-zahl">{gefiltert.filter(b.passt).length}</span>
          </button>
        ))}
        {bereichAuswahl.size > 0 && (
          <button type="button" onClick={() => setBereichAuswahl(new Set())} title="Auswahl aufheben">
            alle zeigen
          </button>
        )}
      </div>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((item) => (
          <GegenstandRow
            key={item.id}
            kachel
            campaignId={campaignId}
            personId={item.ownerId ?? undefined}
            item={item}
            pcOptions={pcOptions}
            alleOptionen={alleOptionen}
            onChanged={refresh}
            onRemoved={() => removeItem(item.id)}
            onBearbeiten={meldeBearbeiten}
            inhaltAnzahl={item.istBehaelter ? inhaltProBehaelter.get(item.id) ?? 0 : undefined}
          />
        ))}
      </div>

      {gefiltert.length === 0 && (
        <p className="gg-leer">
          {items.length === 0 ? "Noch keine Gegenstände in dieser Kampagne." : "Nichts gefunden."}
        </p>
      )}

      {seiten > 1 && (
        <div className="gg-blaettern">
          <button type="button" onClick={() => setSeite(aktuelleSeite - 1)} disabled={aktuelleSeite === 0}>
            ‹
          </button>
          <span>
            Seite {aktuelleSeite + 1} / {seiten}
          </span>
          <button type="button" onClick={() => setSeite(aktuelleSeite + 1)} disabled={aktuelleSeite >= seiten - 1}>
            ›
          </button>
        </div>
      )}

      {istGm && (
        <Muelleimer
          campaignId={campaignId}
          offen={muelleimerOffen}
          onSchliessen={() => setMuelleimerOffen(false)}
          onGeaendert={refresh}
        />
      )}
    </div>
  );
}
