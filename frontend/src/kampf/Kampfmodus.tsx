import { useEffect, useMemo, useState, type FormEvent } from "react";
import { begleiterApi, type Begleiter } from "../begleiter/api";
import { BegleiterBlatt } from "../begleiter/BegleiterKachel";
import { entitiesApi, type Person } from "../entities/api";
import { Fenster } from "../shell/Fenster";
import { bogenApi } from "../traits/bogenApi";
import { Charakterblatt } from "../traits/Charakterblatt";
import { KAMPFARTEN, kampfApi, type Kampfart, type Teilnehmer } from "./api";
import { Initiativliste, useKampf } from "./Initiativliste";
import "./kampf.css";

/**
 * Kampfmodus für die Spielleitung.
 *
 * Sie führt die Liste, alle anderen sehen sie. Der Knopf ▤ je Zeile öffnet den
 * Bogen des Betreffenden — egal ob Spielercharakter, NPC oder Begleiter; wer
 * einen Kampf leitet, will nachsehen können, ohne die Ansicht zu verlassen.
 *
 * **Initiative wird vorgeschlagen, nicht verordnet**: Geistesschärfe +
 * Geschicklichkeit (Zeile 57) steht beim Hinzufügen im Feld, überschreiben
 * kann man sie jederzeit — Cyberware und Drogen kennt das Werkzeug noch nicht.
 */
export function Kampfmodus({ campaignId }: { campaignId: string }) {
  const { kampf, geladen, neuLaden } = useKampf(campaignId);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [begleiter, setBegleiter] = useState<Begleiter[]>([]);
  const [wer, setWer] = useState("");
  const [name, setName] = useState("");
  const [initiative, setInitiative] = useState(0);
  const [kampfart, setKampfart] = useState<Kampfart>("NAHKAMPF");
  const [bogenFuer, setBogenFuer] = useState<Teilnehmer | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  useEffect(() => {
    entitiesApi.listPersonen(campaignId).then(setPersonen).catch(() => setPersonen([]));
    begleiterApi.liste(campaignId).then(setBegleiter).catch(() => setBegleiter([]));
  }, [campaignId]);

  /** Auswahl: erst die Charaktere, dann die Begleiter, dann "frei benannt". */
  const auswahl = useMemo(
    () => [
      ...personen.map((p) => ({ wert: `person:${p.id}`, label: `${p.name} (${p.personType})` })),
      ...begleiter.map((b) => ({ wert: `begleiter:${b.id}`, label: `${b.name} (Begleiter)` })),
    ],
    [personen, begleiter],
  );

  /**
   * Initiative vorschlagen. Nur für Personen — Begleiter haben keine
   * Attribute, ihre Agilität steht auf dem eigenen Blatt und ist etwas anderes.
   */
  async function uebernehmen(schluessel: string) {
    setWer(schluessel);
    const [art, id] = schluessel.split(":");
    if (art === "person") {
      const p = personen.find((x) => x.id === id);
      setName(p?.name ?? "");
      try {
        const bogen = await bogenApi.laden(campaignId, id);
        setInitiative(bogen.uebersicht.initiative);
      } catch {
        setInitiative(0);
      }
    } else if (art === "begleiter") {
      const b = begleiter.find((x) => x.id === id);
      setName(b?.name ?? "");
      setInitiative(b?.agilitaet ?? 0);
    }
  }

  async function hinzufuegen(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || !kampf) return;
    const [art, id] = wer ? wer.split(":") : ["", ""];
    neuLaden(
      await kampfApi.hinzu(campaignId, {
        name: name.trim(),
        initiative,
        kampfart,
        personId: art === "person" ? id : null,
        begleiterId: art === "begleiter" ? id : null,
      }),
    );
    setWer("");
    setName("");
    setInitiative(0);
  }

  async function mit<T>(aktion: Promise<T>) {
    setLaeuft(true);
    try {
      neuLaden((await aktion) as never);
    } finally {
      setLaeuft(false);
    }
  }

  if (!geladen) return <p style={{ color: "var(--text-leise)" }}>Lade Kampf…</p>;

  if (!kampf) {
    return (
      <div className="ka-leer">
        <p>Gerade wird nicht gekämpft.</p>
        <button type="button" onClick={() => mit(kampfApi.beginnen(campaignId))}>
          Kampf beginnen
        </button>
      </div>
    );
  }

  return (
    <div className="ka-seite">
      <header className="ka-kopf">
        <span className="ka-runde">
          Runde <strong>{kampf.runde}</strong>
        </span>
        <button type="button" className="ka-weiter" onClick={() => mit(kampfApi.weiter(campaignId))} disabled={laeuft}>
          Nächster ›
        </button>
        <button
          type="button"
          className="ka-ende"
          onClick={() => mit(kampfApi.beenden(campaignId).then(() => null))}
        >
          Kampf beenden
        </button>
      </header>

      <Initiativliste
        kampf={kampf}
        onAmZug={(id) => mit(kampfApi.amZug(campaignId, id))}
        onBogen={setBogenFuer}
        onEntfernen={(id) => mit(kampfApi.entfernen(campaignId, id))}
        onErledigt={(t) => mit(kampfApi.aendern(campaignId, t.id, { erledigt: !t.erledigt }))}
      />

      {/* Zeile 59: angesagt wird von hinten nach vorn, damit die schnellste
          Person auf alles reagieren kann. Deshalb sichtbar dabei. */}
      {kampf.teilnehmer.length > 1 && (
        <p className="ka-ansage">
          <span>Ansage von hinten:</span>{" "}
          {[...kampf.teilnehmer].reverse().map((t) => t.name).join(" → ")}
        </p>
      )}

      <form onSubmit={hinzufuegen} className="ka-form">
        <select value={wer} onChange={(e) => uebernehmen(e.target.value)}>
          <option value="">— frei benannt —</option>
          {auswahl.map((a) => (
            <option key={a.wert} value={a.wert}>
              {a.label}
            </option>
          ))}
        </select>
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ flex: "1 1 160px", minWidth: 0 }}
        />
        <input
          type="number"
          min={0}
          value={initiative}
          onChange={(e) => setInitiative(Number(e.target.value))}
          title="Initiative — Geistesschärfe + Geschicklichkeit + Cyberware"
          style={{ width: 76 }}
        />
        <select value={kampfart} onChange={(e) => setKampfart(e.target.value as Kampfart)}>
          {KAMPFARTEN.map((a) => (
            <option key={a.wert} value={a.wert}>
              {a.symbol} {a.name}
            </option>
          ))}
        </select>
        <button type="submit">Aufnehmen</button>
      </form>

      <Fenster
        offen={bogenFuer !== null}
        breit
        titel={bogenFuer?.name ?? ""}
        unterzeile="Charakterbogen"
        kennung={`kampfbogen:${bogenFuer?.id ?? ""}`}
        onSchliessen={() => setBogenFuer(null)}
      >
        {bogenFuer?.personId ? (
          <Charakterblatt campaignId={campaignId} personId={bogenFuer.personId} bearbeitbar />
        ) : (
          <BegleiterImKampf begleiter={begleiter.find((b) => b.id === bogenFuer?.begleiterId)} />
        )}
      </Fenster>
    </div>
  );
}

function BegleiterImKampf({ begleiter }: { begleiter?: Begleiter }) {
  if (!begleiter) return <p style={{ color: "var(--text-leise)" }}>Kein Bogen hinterlegt.</p>;
  // Dasselbe Blatt wie in der Begleiterverwaltung — nicht nachgebaut.
  return <BegleiterBlatt begleiter={begleiter} />;
}
