import { useEffect, useState, type FormEvent } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { hintergruendeApi, type Hintergrund } from "./api";
import "../zusatzfertigkeiten/zusatzfertigkeiten.css";

/**
 * SL-Baukasten für narrative Hintergründe (Name, Kurz, Detail).
 * Mentor/Kontakte sind Mechanik und stehen nicht in dieser Tabelle.
 */
export function HintergruendeVerwaltung({ campaignId }: { campaignId: string }) {
  const [liste, setListe] = useState<Hintergrund[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [offen, setOffen] = useState<Hintergrund | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuName, setNeuName] = useState("");

  async function neuLaden() {
    const daten = await hintergruendeApi.liste(campaignId);
    setListe(daten);
    setOffen((alt) => (alt ? daten.find((h) => h.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaedt(true);
    neuLaden().finally(() => setLaedt(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    const neu = await hintergruendeApi.anlegen(campaignId, { name: neuName.trim() });
    setNeuName("");
    setAnlegenOffen(false);
    await neuLaden();
    setOffen(neu);
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Hintergründe…</p>;

  return (
    <div className="zf-seite">
      <div className="zf-kopf">
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neu
        </button>
        <span className="zf-anzahl">{liste.length} in dieser Kampagne</span>
      </div>

      {liste.length === 0 && (
        <p className="zf-leer">
          Noch keine narrativen Hintergründe. Mentor und Kontakte sind Mechanik und stehen
          nicht in dieser Liste.
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
            {liste.map((h) => (
              <tr key={h.id} onClick={() => setOffen(h)} className="zf-zeile">
                <td className="zf-zeile-name">{h.name}</td>
                <td className="zf-zeile-kurz">{h.kurzbeschreibung || <em>—</em>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Fenster
        offen={anlegenOffen}
        titel="Neuer Hintergrund"
        unterzeile="Erst anlegen, dann Beschreibung ausarbeiten"
        kennung="hintergrund-neu"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
        }}
      >
        <form onSubmit={anlegen} className="zf-neu-form">
          <input
            type="text"
            placeholder="Name des Hintergrunds"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
            required
            autoFocus
          />
          <button type="submit">Anlegen und bearbeiten</button>
        </form>
      </Fenster>

      {offen && (
        <HintergrundEditor
          campaignId={campaignId}
          eintrag={offen}
          onSchliessen={() => setOffen(null)}
          onGeaendert={neuLaden}
        />
      )}
    </div>
  );
}

function HintergrundEditor({
  campaignId,
  eintrag,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  eintrag: Hintergrund;
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
      setName(eintrag.name);
      return;
    }
    if (wert === eintrag.name) return;
    await hintergruendeApi.aendern(campaignId, eintrag.id, { name: wert });
    await onGeaendert();
  }

  async function kurzSpeichern() {
    if (kurz === eintrag.kurzbeschreibung) return;
    await hintergruendeApi.aendern(campaignId, eintrag.id, { kurzbeschreibung: kurz });
    await onGeaendert();
  }

  async function detailSpeichern() {
    if (detail === eintrag.detailbeschreibung) return;
    await hintergruendeApi.aendern(campaignId, eintrag.id, { detailbeschreibung: detail });
    await onGeaendert();
  }

  async function loeschen() {
    await hintergruendeApi.loeschen(campaignId, eintrag.id);
    setLoeschenOffen(false);
    onSchliessen();
    await onGeaendert();
  }

  return (
    <>
      <Fenster
        offen
        titel={eintrag.name}
        unterzeile="Hintergrund bearbeiten"
        kennung={`hintergrund:${eintrag.id}`}
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
              placeholder="Ein Satz — erscheint in der Erstellung."
              onChange={(e) => setKurz(e.target.value)}
              onBlur={kurzSpeichern}
            />
          </label>
          <label className="zf-feld">
            Detailbeschreibung
            <textarea
              value={detail}
              rows={6}
              placeholder="Was der Hintergrund im Spiel bedeutet."
              onChange={(e) => setDetail(e.target.value)}
              onBlur={detailSpeichern}
            />
          </label>
          <button type="button" className="zf-loeschen" onClick={() => setLoeschenOffen(true)}>
            Löschen
          </button>
        </div>
      </Fenster>
      {loeschenOffen && (
        <Bestaetigung
          titel="Hintergrund löschen?"
          text="Einträge auf Charakteren, die darauf zeigen, gehen mit weg."
          jaText="Löschen"
          onNein={() => setLoeschenOffen(false)}
          onJa={loeschen}
        />
      )}
    </>
  );
}
