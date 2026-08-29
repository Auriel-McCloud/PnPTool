import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { einstellungenApi, type Einstellungen } from "../campaigns/einstellungen";
import { entitiesApi, type Person } from "../entities/api";
import { playersApi, type SpielerZugang } from "./api";

/**
 * Spielerzugänge verwalten — Namen anlegen, Charaktere zuordnen, entfernen.
 *
 * Ersetzt die frühere Code- und Sitzungsverwaltung. Ein Zugang gehört
 * dauerhaft zu einem Namen, deshalb gibt es hier nichts mehr, das von selbst
 * abläuft oder einen Charakter blockiert.
 */
export function SpielerVerwaltung({ campaignId }: { campaignId: string }) {
  const [zugaenge, setZugaenge] = useState<SpielerZugang[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [einstellungen, setEinstellungen] = useState<Einstellungen | null>(null);
  const [neuName, setNeuName] = useState("");
  const [neuPerson, setNeuPerson] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [laden, setLaden] = useState(true);

  async function neuLaden() {
    const [z, p, e] = await Promise.all([
      playersApi.liste(campaignId),
      entitiesApi.listPersonen(campaignId),
      einstellungenApi.lesen(campaignId),
    ]);
    setZugaenge(z);
    setPersonen(p);
    setEinstellungen(e);
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId]);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Spieler…</p>;

  const pcs = personen.filter((p) => p.personType === "PC");

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    setFehler(null);
    try {
      await playersApi.anlegen(campaignId, neuName.trim(), neuPerson || null);
      setNeuName("");
      setNeuPerson("");
      await neuLaden();
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Anlegen fehlgeschlagen");
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 720 }}>
      <section>
        <h3>Spielerzugang anlegen</h3>
        <form onSubmit={anlegen} style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input
            placeholder="Benutzername"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
            required
            autoCapitalize="none"
            spellCheck={false}
          />
          <select value={neuPerson} onChange={(e) => setNeuPerson(e.target.value)}>
            <option value="">— noch kein Charakter —</option>
            {pcs.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button type="submit">Anlegen</button>
        </form>
        {fehler && <p style={{ color: "var(--signal)", marginTop: 8 }}>{fehler}</p>}
        <p style={{ color: "var(--text-leise)", fontSize: "0.85em", marginTop: 8 }}>
          Zugänge entstehen ohne Passwort — der Name genügt zum Anmelden. Wer möchte, vergibt sich später
          selbst eines. Groß- und Kleinschreibung spielt keine Rolle.
          {pcs.length === 0 &&
            " Es gibt noch keine Spielercharaktere; du kannst den Zugang trotzdem anlegen und später zuordnen."}
        </p>
      </section>

      <section>
        <h3>Zugänge ({zugaenge.length})</h3>
        {zugaenge.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Spieler angelegt.</p>}
        {zugaenge.map((z) => (
          <div
            key={z.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              flexWrap: "wrap",
              borderBottom: "1px solid var(--linie)",
              padding: "8px 0",
            }}
          >
            <strong style={{ minWidth: 110 }}>{z.benutzername}</strong>
            <select
              value={z.personId ?? ""}
              onChange={(e) => playersApi.charakterZuordnen(campaignId, z.id, e.target.value || null).then(setZugaenge)}
            >
              <option value="">— kein Charakter —</option>
              {pcs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <span style={{ color: "var(--text-aus)", fontSize: "0.85em" }}>
              {z.hatPasswort ? "mit Passwort" : "ohne Passwort"}
            </span>
            <button
              type="button"
              onClick={() => playersApi.entfernen(campaignId, z.id).then(neuLaden)}
              style={{ marginLeft: "auto", borderColor: "var(--signal)", color: "var(--signal)" }}
            >
              Entfernen
            </button>
          </div>
        ))}
      </section>

      <section>
        <h3>Spielregeln</h3>
        <label style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <input
            type="checkbox"
            checked={einstellungen?.gewichtAktiv ?? true}
            onChange={(e) => einstellungenApi.aendern(campaignId, { gewichtAktiv: e.target.checked }).then(neuLaden)}
          />
          <span style={{ color: "var(--text)" }}>Gewicht und Traglast anzeigen</span>
        </label>
        <p style={{ color: "var(--text-leise)", fontSize: "0.85em", marginTop: 6 }}>
          Rein informativ — nichts wird dadurch verhindert. Wer über seiner Grenze liegt, erscheint bei den
          Gegenständen als Hinweis. Traglast einer Person ={" "}
          <span className="mono">{einstellungen?.traglastAttribut ?? "Körperkraft"}</span> ×{" "}
          <span className="mono">{einstellungen?.traglastProPunkt ?? 10}</span> kg.
        </p>
      </section>
    </div>
  );
}
