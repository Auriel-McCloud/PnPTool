import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { playersApi } from "./api";

/**
 * Einstieg für Spieler: Zugangscode und eigener Name.
 *
 * Bewusst ohne Konto — die Runde bekommt einen Code vom Spielleiter und
 * tippt ihn ein. Der Name dient nur dazu, dass der Spielleiter in seiner
 * Sitzungsliste sieht, wer da ist.
 */
export function BeitrittPage({ onBeigetreten, onZurueck }: { onBeigetreten: () => void; onZurueck: () => void }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  async function absenden(e: FormEvent) {
    e.preventDefault();
    setFehler(null);
    setLaeuft(true);
    try {
      await playersApi.beitreten(code.trim(), name.trim());
      onBeigetreten();
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Beitritt fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "12svh auto", padding: 20 }}>
      <h1>Beitreten</h1>
      <p style={{ color: "var(--text-leise)", marginBottom: 20 }}>
        Gib den Zugangscode ein, den du von deiner Spielleitung bekommen hast.
      </p>
      <form onSubmit={absenden} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          Zugangscode
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
            autoCapitalize="characters"
            autoCorrect="off"
            spellCheck={false}
            placeholder="z.B. FMT26V"
            style={{ fontFamily: "var(--mono)", letterSpacing: "0.22em", fontSize: 20, textTransform: "uppercase" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          Dein Name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Wie heißt du am Tisch?" />
        </label>
        {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
        <button type="submit" disabled={laeuft}>
          {laeuft ? "Verbinde…" : "Beitreten"}
        </button>
        <button type="button" onClick={onZurueck} style={{ background: "none", border: "none", color: "var(--text-leise)" }}>
          Ich bin die Spielleitung
        </button>
      </form>
    </div>
  );
}

/** Auswahl des eigenen Charakters, direkt nach dem Beitritt. */
export function CharakterWahl({ onGewaehlt }: { onGewaehlt: () => void }) {
  const [charaktere, setCharaktere] = useState<{ id: string; name: string }[] | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    playersApi
      .freieCharaktere()
      .then(setCharaktere)
      .catch(() => setCharaktere([]));
  }, []);

  async function waehlen(id: string) {
    setFehler(null);
    try {
      await playersApi.charakterWaehlen(id);
      onGewaehlt();
    } catch {
      // Häufigster Fall: jemand anderes war schneller.
      setFehler("Dieser Charakter ist inzwischen vergeben.");
      playersApi.freieCharaktere().then(setCharaktere);
    }
  }

  if (charaktere === null) {
    return <p style={{ padding: 20, color: "var(--text-leise)" }}>Lade Charaktere…</p>;
  }

  return (
    <div style={{ maxWidth: 420, margin: "12svh auto", padding: 20 }}>
      <h1>Wer bist du?</h1>
      {charaktere.length === 0 ? (
        <p style={{ color: "var(--text-leise)" }}>
          Zurzeit ist kein Charakter frei. Deine Spielleitung muss dir einen anlegen — danach hier neu laden.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
          {charaktere.map((c) => (
            <button key={c.id} type="button" onClick={() => waehlen(c.id)} style={{ justifyContent: "flex-start" }}>
              {c.name}
            </button>
          ))}
        </div>
      )}
      {fehler && <p style={{ color: "var(--signal)", marginTop: 12 }}>{fehler}</p>}
    </div>
  );
}
