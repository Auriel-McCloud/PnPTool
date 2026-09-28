import { useEffect, useState, type FormEvent } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import {
  zusatzfertigkeitenApi,
  type Zusatzfertigkeit,
  type ZusatzfertigkeitVorschlag,
} from "./api";
import "./zusatzfertigkeiten.css";

/**
 * SL-Verwaltung der Zusatzfertigkeiten dieser Kampagne.
 *
 * Marks Vorgabe (28.09.2026): "im Kampagnen Menü eine einfache Tabelle
 * machen in der man Skills eintragen kann [...] nur einen Namen eine Kurz
 * und Detail Beschreibung hinzufügen können." Kein Freigabe-Schalter wie
 * bei Rassen: jeder Eintrag ist sofort für Spieler dieser Kampagne wählbar.
 *
 * Aufbau: schlichte Tabelle (Name/Kurzbeschreibung), Zeile öffnet
 * Detail-Popup mit Bearbeiten/Löschen, "+ Neu" legt einen leeren Eintrag an,
 * "✨ KI-Vorschläge" öffnet ein Popup mit Kandidaten zum Übernehmen.
 */
export function ZusatzfertigkeitenVerwaltung({ campaignId }: { campaignId: string }) {
  const [liste, setListe] = useState<Zusatzfertigkeit[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [offen, setOffen] = useState<Zusatzfertigkeit | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuName, setNeuName] = useState("");
  const [kiOffen, setKiOffen] = useState(false);

  async function neuLaden() {
    const daten = await zusatzfertigkeitenApi.liste(campaignId);
    setListe(daten);
    setOffen((alt) => (alt ? daten.find((z) => z.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaedt(true);
    neuLaden().finally(() => setLaedt(false));
  }, [campaignId]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    const neu = await zusatzfertigkeitenApi.anlegen(campaignId, { name: neuName.trim() });
    setNeuName("");
    setAnlegenOffen(false);
    await neuLaden();
    setOffen(neu);
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Zusatzfertigkeiten…</p>;

  return (
    <div className="zf-seite">
      <div className="zf-kopf">
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neu
        </button>
        <button type="button" className="zf-ki-btn" onClick={() => setKiOffen(true)}>
          ✨ KI-Vorschläge
        </button>
        <span className="zf-anzahl">{liste.length} in dieser Kampagne</span>
      </div>

      {liste.length === 0 && (
        <p className="zf-leer">
          Noch keine Zusatzfertigkeiten in dieser Kampagne. Sie stehen sofort allen Spielern zur Wahl,
          sobald sie hier eingetragen sind.
        </p>
      )}

      {liste.length > 0 && (
        <table className="zf-tabelle">
          <thead>
            <tr>
              <th>Name</th>
              <th>Kurzbeschreibung</th>
            </tr>
          </thead>
          <tbody>
            {liste.map((z) => (
              <tr key={z.id} onClick={() => setOffen(z)} className="zf-zeile">
                <td className="zf-zeile-name">{z.name}</td>
                <td className="zf-zeile-kurz">{z.kurzbeschreibung || <em>—</em>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Fenster
        offen={anlegenOffen}
        titel="Neue Zusatzfertigkeit"
        unterzeile="Erst anlegen, dann Beschreibung ausarbeiten"
        kennung="zusatzfertigkeit-neu"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
        }}
      >
        <form onSubmit={anlegen} className="zf-neu-form">
          <input
            type="text"
            placeholder="Name der Zusatzfertigkeit"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
            required
            autoFocus
          />
          <button type="submit">Anlegen und bearbeiten</button>
        </form>
      </Fenster>

      {offen && (
        <ZusatzfertigkeitEditor
          campaignId={campaignId}
          eintrag={offen}
          onSchliessen={() => setOffen(null)}
          onGeaendert={neuLaden}
        />
      )}

      <KiVorschlaegePopup
        campaignId={campaignId}
        offen={kiOffen}
        onSchliessen={() => setKiOffen(false)}
        onUebernommen={neuLaden}
      />
    </div>
  );
}

/**
 * Bearbeiten-Popup: Textfelder speichern per `onBlur` (Projektkonvention,
 * wie beim Rassen-Editor), kein separater Speichern-Knopf für Name/Kurz —
 * die Detailbeschreibung ist ein längeres Feld, bekommt aber denselben
 * onBlur statt eines eigenen Autosave-Hooks (kein Rich-Text-Editor hier).
 */
function ZusatzfertigkeitEditor({
  campaignId,
  eintrag,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  eintrag: Zusatzfertigkeit;
  onSchliessen: () => void;
  onGeaendert: () => Promise<void>;
}) {
  const [name, setName] = useState(eintrag.name);
  const [kurz, setKurz] = useState(eintrag.kurzbeschreibung);
  const [detail, setDetail] = useState(eintrag.detailbeschreibung);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  useEffect(() => {
    setName(eintrag.name);
    setKurz(eintrag.kurzbeschreibung);
    setDetail(eintrag.detailbeschreibung);
  }, [eintrag.id]);

  async function nameSpeichern() {
    const wert = name.trim();
    if (!wert) {
      // Leerer Name macht den Eintrag in der Tabelle unauffindbar — wie bei
      // Ort/Fraktion/Event zurücksetzen statt speichern.
      setName(eintrag.name);
      return;
    }
    if (wert === eintrag.name) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { name: wert });
    await onGeaendert();
  }

  async function kurzSpeichern() {
    if (kurz === eintrag.kurzbeschreibung) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { kurzbeschreibung: kurz });
    await onGeaendert();
  }

  async function detailSpeichern() {
    if (detail === eintrag.detailbeschreibung) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { detailbeschreibung: detail });
    await onGeaendert();
  }

  async function loeschen() {
    await zusatzfertigkeitenApi.loeschen(campaignId, eintrag.id);
    setLoeschenOffen(false);
    onSchliessen();
    await onGeaendert();
  }

  return (
    <>
      <Fenster
        offen
        titel={eintrag.name}
        unterzeile="Zusatzfertigkeit bearbeiten"
        kennung={`zusatzfertigkeit:${eintrag.id}`}
        onSchliessen={onSchliessen}
      >
        <div className="zf-editor">
          <label className="zf-feld">
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} onBlur={nameSpeichern} />
          </label>

          <label className="zf-feld">
            Kurzbeschreibung
            <textarea
              value={kurz}
              rows={2}
              placeholder="Ein Satz, der die Fertigkeit fassbar macht — erscheint in der Auswahlliste."
              onChange={(e) => setKurz(e.target.value)}
              onBlur={kurzSpeichern}
            />
          </label>

          <label className="zf-feld">
            Detailbeschreibung
            <textarea
              value={detail}
              rows={6}
              placeholder="Ein Absatz — was die Fertigkeit umfasst, wer sie trägt, wofür sie im Spiel nützlich ist."
              onChange={(e) => setDetail(e.target.value)}
              onBlur={detailSpeichern}
            />
          </label>

          <div className="zf-aktionen">
            <button type="button" onClick={() => setLoeschenOffen(true)} className="zf-loeschen">
              🗑 Aus dem Katalog entfernen
            </button>
          </div>
        </div>
      </Fenster>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${eintrag.name} entfernen?`}
          text="Personen, die diese Zusatzfertigkeit bereits gewählt haben, verlieren sie dabei ebenfalls — anders als bei Rassen gibt es hier keinen reinen Textrest auf dem Charakterbogen."
          jaText="Entfernen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}

/**
 * KI-Vorschläge (Marks Wunsch: "Mit einem KI Generierungs Button für
 * Vorschläge"). Zweistufig wie beim Händler-Sortiment: Liste ansehen,
 * jeder Vorschlag einzeln übernehmen (bewusst kein Sammel-Übernehmen) —
 * vor dem Übernehmen editierbar.
 */
function KiVorschlaegePopup({
  campaignId,
  offen,
  onSchliessen,
  onUebernommen,
}: {
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
  onUebernommen: () => Promise<void>;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [vorschlaege, setVorschlaege] = useState<ZusatzfertigkeitVorschlag[]>([]);
  const [uebernommen, setUebernommen] = useState<Set<number>>(new Set());

  async function generieren() {
    setLaedt(true);
    setFehler(null);
    setUebernommen(new Set());
    try {
      const antwort = await zusatzfertigkeitenApi.kiVorschlaege(campaignId, 5);
      setVorschlaege(antwort.vorschlaege);
      if (antwort.vorschlaege.length === 0) {
        setFehler("Die KI hat keine neuen Vorschläge geliefert.");
      }
    } catch (e) {
      setFehler((e as Error).message || "KI-Vorschläge konnten nicht geladen werden.");
    } finally {
      setLaedt(false);
    }
  }

  useEffect(() => {
    if (offen) {
      setVorschlaege([]);
      setFehler(null);
      void generieren();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId]);

  async function uebernehmen(i: number, vorschlag: ZusatzfertigkeitVorschlag) {
    await zusatzfertigkeitenApi.kiVorschlagUebernehmen(campaignId, vorschlag);
    setUebernommen((alt) => new Set(alt).add(i));
    await onUebernommen();
  }

  function editieren(i: number, feld: keyof ZusatzfertigkeitVorschlag, wert: string) {
    setVorschlaege((alt) => alt.map((v, j) => (j === i ? { ...v, [feld]: wert } : v)));
  }

  return (
    <Fenster
      offen={offen}
      breit
      titel="✨ KI-Vorschläge für Zusatzfertigkeiten"
      unterzeile="Vor dem Übernehmen editierbar — jeder Vorschlag einzeln."
      kennung="zusatzfertigkeiten-ki"
      onSchliessen={onSchliessen}
    >
      <div className="zf-ki-popup">
        {laedt && <p style={{ color: "var(--text-leise)" }}>Die KI überlegt…</p>}
        {fehler && <p className="zf-ki-fehler">{fehler}</p>}
        {!laedt && vorschlaege.length > 0 && (
          <button type="button" onClick={generieren} className="zf-ki-neu">
            ↻ Neue Vorschläge
          </button>
        )}

        {vorschlaege.map((v, i) => (
          <div key={i} className="zf-ki-vorschlag" data-uebernommen={uebernommen.has(i)}>
            <label className="zf-feld">
              Name
              <input value={v.name} onChange={(e) => editieren(i, "name", e.target.value)} />
            </label>
            <label className="zf-feld">
              Kurzbeschreibung
              <textarea
                rows={2}
                value={v.kurzbeschreibung}
                onChange={(e) => editieren(i, "kurzbeschreibung", e.target.value)}
              />
            </label>
            <label className="zf-feld">
              Detailbeschreibung
              <textarea
                rows={4}
                value={v.detailbeschreibung}
                onChange={(e) => editieren(i, "detailbeschreibung", e.target.value)}
              />
            </label>
            <button
              type="button"
              className="zf-ki-uebernehmen"
              disabled={uebernommen.has(i)}
              onClick={() => uebernehmen(i, v)}
            >
              {uebernommen.has(i) ? "✓ Übernommen" : "In den Katalog übernehmen"}
            </button>
          </div>
        ))}
      </div>
    </Fenster>
  );
}
