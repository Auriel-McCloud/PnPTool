import { useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { playersApi } from "./api";

/**
 * Anmeldung für Spieler — Benutzername, Passwort nur falls vergeben.
 *
 * Löst den früheren Beitrittscode ab. Der führte laufend zu Konflikten:
 * wer sich von einem zweiten Gerät anmeldete, fand seinen eigenen Charakter
 * belegt. Ein Zugang gehört jetzt dauerhaft zu einem Namen.
 */
export function SpielerLogin({ onAngemeldet, onZurueck }: { onAngemeldet: () => void; onZurueck: () => void }) {
  const [benutzername, setBenutzername] = useState("");
  const [passwort, setPasswort] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  async function absenden(e: FormEvent) {
    e.preventDefault();
    setFehler(null);
    setLaeuft(true);
    try {
      await playersApi.anmelden(benutzername, passwort);
      onAngemeldet();
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Anmeldung fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "12svh auto", padding: 20 }}>
      <h1>Anmelden</h1>
      <p style={{ color: "var(--text-leise)", marginBottom: 20 }}>
        Melde dich mit dem Namen an, den deine Spielleitung für dich angelegt hat.
      </p>
      <form onSubmit={absenden} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          Benutzername
          <input
            value={benutzername}
            onChange={(e) => setBenutzername(e.target.value)}
            required
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            autoComplete="username"
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          Passwort <span style={{ color: "var(--text-aus)", fontSize: "0.85em" }}>nur falls du eines vergeben hast</span>
          <input
            type="password"
            value={passwort}
            onChange={(e) => setPasswort(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
        <button type="submit" disabled={laeuft}>
          {laeuft ? "Melde an…" : "Anmelden"}
        </button>
        <button type="button" onClick={onZurueck} style={{ background: "none", border: "none", color: "var(--text-leise)" }}>
          Ich bin die Spielleitung
        </button>
      </form>
    </div>
  );
}
