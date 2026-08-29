import { useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { einstellungenApi, formatiereLast, type Einstellungen } from "../campaigns/einstellungen";
import { entitiesApi, type Person } from "../entities/api";
import type { PersonOption } from "../entities/VisibilitySelector";
import { GegenstandRow } from "../traits/CharacterSheetPanel";
import { itemsApi, VORLAGE_SENTINEL, type GegenstandMitBesitzer, type TraglastZeile } from "./api";
import { ermittleBereiche, filtereNachBereichen, standardAuswahl } from "./aufbewahrung";
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
  const [einstellungen, setEinstellungen] = useState<Einstellungen | null>(null);
  const [traglast, setTraglast] = useState<TraglastZeile[]>([]);
  const [seite, setSeite] = useState(0);
  const [neuName, setNeuName] = useState("");
  const [neuBesitzer, setNeuBesitzer] = useState("");
  const [anlegenOffen, setAnlegenOffen] = useState(false);

  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);

  async function refresh() {
    const [p, i, e, t] = await Promise.all([
      entitiesApi.listPersonen(campaignId),
      itemsApi.listAlle(campaignId),
      einstellungenApi.lesen(campaignId),
      itemsApi.traglast(campaignId),
    ]);
    setPersonen(p);
    setItems(i);
    setEinstellungen(e);
    setTraglast(t);
  }

  useEffect(() => {
    setLoading(true);
    refresh().finally(() => setLoading(false));
  }, [campaignId]);

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
      if (!s) return true;
      // Auch Typ und Besitzer durchsuchen — "alle Waffen von Kira" ist die
      // häufigere Frage als der exakte Gegenstandsname.
      return (
        i.name.toLowerCase().includes(s) ||
        i.typ.toLowerCase().includes(s) ||
        (i.ownerName ?? "").toLowerCase().includes(s)
      );
    });
  }, [items, suche, besitzerFilter]);

  const bereiche = useMemo(() => ermittleBereiche(items), [items]);

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
  }, [suche, besitzerFilter, bereichAuswahl]);

  // Wer über seiner Grenze liegt — die Spielleitung soll es auf einen Blick
  // sehen und selbst entscheiden, was daraus folgt.
  const ueberladen = traglast.filter((z) => z.kapazitaet > 0 && z.last > z.kapazitaet);

  async function removeItem(itemId: string) {
    await itemsApi.remove(campaignId, itemId);
    await refresh();
  }

  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim() || !neuBesitzer) return;
    if (neuBesitzer === VORLAGE_SENTINEL) {
      await itemsApi.createVorlage(campaignId, { name: neuName });
    } else {
      await itemsApi.create(campaignId, neuBesitzer, { name: neuName });
    }
    setNeuName("");
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
        <button type="button" onClick={() => setAnlegenOffen((o) => !o)}>
          {anlegenOffen ? "Abbrechen" : "+ Neu"}
        </button>
        <span className="gg-anzahl">
          {sichtbareItems.length} von {items.length}
        </span>
      </div>

      {anlegenOffen && (
        <form onSubmit={addItem} className="gg-kopf">
          <select value={neuBesitzer} onChange={(e) => setNeuBesitzer(e.target.value)} required>
            <option value="">Besitzer wählen…</option>
            <option value={VORLAGE_SENTINEL}>— Vorlage (kein Besitzer) —</option>
            {alleOptionen.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            className="gg-suche"
            placeholder="Name des Gegenstands"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
          />
          <button type="submit">Hinzufügen</button>
        </form>
      )}

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
    </div>
  );
}
