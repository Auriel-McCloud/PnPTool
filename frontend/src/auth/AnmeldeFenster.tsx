import { useState, type FormEvent } from "react";
import { ApiError, useAuth } from "./AuthContext";
import { playersApi } from "../players/api";
import "./anmelde.css";

/**
 * Gemeinsames Anmeldefenster für Spieler und Spielleitung.
 *
 * Mark, 22.09.2026: Spieler sollen als Erstes den Anmelde-Weg sehen, die SL
 * muss extra klicken — "das führt zu weniger Problemen" (deutlich mehr
 * Spieler- als SL-Logins am Tisch). Beide Formulare teilen sich dieselbe
 * Commlink-Karte, nur der Inhalt tauscht — kein Seitenwechsel, kein zweites
 * Layout zum Pflegen.
 */
export function AnmeldeFenster() {
  const [rolle, setRolle] = useState<"spieler" | "sl">("spieler");

  return (
    <div className="an-buehne">
      <div className="an-kasten cl-roehre">
        {rolle === "spieler" ? (
          <SpielerFormular onZurWahlSl={() => setRolle("sl")} />
        ) : (
          <SlFormular onZurueck={() => setRolle("spieler")} />
        )}
      </div>
    </div>
  );
}

function SpielerFormular({ onZurWahlSl }: { onZurWahlSl: () => void }) {
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
      window.location.reload();
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Anmeldung fehlgeschlagen");
      setLaeuft(false);
    }
  }

  return (
    <>
      <h1 className="an-titel">Anmelden</h1>
      <p className="an-hinweis">Melde dich mit dem Namen an, den deine Spielleitung für dich angelegt hat.</p>
      <form onSubmit={absenden} className="an-form">
        <label className="an-feld">
          <span>Benutzername</span>
          <input
            value={benutzername}
            onChange={(e) => setBenutzername(e.target.value)}
            required
            autoFocus
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            autoComplete="username"
          />
        </label>
        <label className="an-feld">
          <span>
            Passwort <em>nur falls du eines vergeben hast</em>
          </span>
          <input
            type="password"
            value={passwort}
            onChange={(e) => setPasswort(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {fehler && <p className="an-fehler">{fehler}</p>}
        <button type="submit" disabled={laeuft} className="an-absenden">
          {laeuft ? "Melde an…" : "Anmelden"}
        </button>
        <button type="button" onClick={onZurWahlSl} className="an-wechsel">
          Ich bin die Spielleitung
        </button>
      </form>
    </>
  );
}

function SlFormular({ onZurueck }: { onZurueck: () => void }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  async function absenden(e: FormEvent) {
    e.preventDefault();
    setFehler(null);
    setLaeuft(true);
    try {
      await login(username, password);
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Login fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <>
      <h1 className="an-titel">Spielleitung — Login</h1>
      <p className="an-hinweis">Anmeldung für die Spielleitung mit Benutzername und Passwort.</p>
      <form onSubmit={absenden} className="an-form">
        <label className="an-feld">
          <span>Benutzername</span>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
        </label>
        <label className="an-feld">
          <span>Passwort</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {fehler && <p className="an-fehler">{fehler}</p>}
        <button type="submit" disabled={laeuft} className="an-absenden">
          {laeuft ? "…" : "Anmelden"}
        </button>
        <button type="button" onClick={onZurueck} className="an-wechsel">
          Ich bin Spieler
        </button>
      </form>
    </>
  );
}
