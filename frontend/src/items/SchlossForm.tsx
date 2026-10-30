import { useEffect, useState } from "react";
import { itemsApi, type Gegenstand, type GegenstandMitBesitzer } from "./api";
import { ApiError } from "../api/client";

type Art = "" | "passwort" | "schluessel" | "spiel";

/**
 * SL setzt das Schloss an einem Behälter, bevor die Kiste rausgeht.
 * Spieler sehen das hier nicht — der PATCH ist sowieso nur für die SL.
 */
export function SchlossForm({
  campaignId,
  item,
  onGeaendert,
}: {
  campaignId: string;
  item: Gegenstand;
  onGeaendert: () => void;
}) {
  const [art, setArt] = useState<Art>((item.schlossArt as Art) || "");
  const [raetsel, setRaetsel] = useState(item.schlossRaetsel || "");
  const [passwort, setPasswort] = useState(item.schlossPasswort || "");
  const [schluesselId, setSchluesselId] = useState(item.schluesselId || "");
  const [laenge, setLaenge] = useState(item.spielLaenge || 4);
  const [kandidaten, setKandidaten] = useState<GegenstandMitBesitzer[]>([]);
  const [suche, setSuche] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  useEffect(() => {
    setArt((item.schlossArt as Art) || "");
    setRaetsel(item.schlossRaetsel || "");
    setPasswort(item.schlossPasswort || "");
    setSchluesselId(item.schluesselId || "");
    setLaenge(item.spielLaenge || 4);
  }, [item]);

  useEffect(() => {
    if (art !== "schluessel") return;
    itemsApi.listAlle(campaignId).then(setKandidaten).catch(() => setKandidaten([]));
  }, [art, campaignId]);

  const treffer = kandidaten
    .filter((g) => g.id !== item.id && !g.weggeworfen)
    .filter((g) => !suche.trim() || g.name.toLowerCase().includes(suche.trim().toLowerCase()))
    .slice(0, 8);

  async function setzen(extra: { aufgeschlossen?: boolean; schlossArt?: Art } = {}) {
    setLaeuft(true);
    setFehler(null);
    const zielArt = extra.schlossArt ?? art;
    try {
      await itemsApi.update(campaignId, item.id, {
        schlossArt: zielArt,
        schlossRaetsel: zielArt === "passwort" ? raetsel : "",
        schlossPasswort: zielArt === "passwort" ? passwort : "",
        schluesselId: zielArt === "schluessel" ? schluesselId : "",
        spielLaenge: zielArt === "spiel" ? Math.max(1, laenge) : 0,
        istBehaelter: true,
        ...extra,
      });
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof ApiError ? e.message : "Schloss nicht gespeichert.");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
      <label style={{ fontSize: "0.9em", display: "flex", flexDirection: "column", gap: 4 }}>
        Schloss
        <select value={art} onChange={(e) => setArt(e.target.value as Art)}>
          <option value="">keins</option>
          <option value="passwort">Passwort / Rätsel</option>
          <option value="schluessel">ein bestimmter Schlüssel</option>
          <option value="spiel">Tastenfolge</option>
        </select>
      </label>
      {item.aufgeschlossen && item.schlossArt && (
        <p style={{ margin: 0, fontSize: "0.8em", color: "var(--text-leise)" }}>
          Auf. Bleibt auf, bis du wieder zusperrst.
        </p>
      )}
      {art === "passwort" && (
        <>
          <label style={{ fontSize: "0.9em", display: "flex", flexDirection: "column", gap: 4 }}>
            Rätsel auf dem Schloss
            <textarea value={raetsel} onChange={(e) => setRaetsel(e.target.value)} rows={3} placeholder="Leer = nur ein Code, kein Rätsel." />
          </label>
          <label style={{ fontSize: "0.9em", display: "flex", flexDirection: "column", gap: 4 }}>
            Lösung
            <input value={passwort} onChange={(e) => setPasswort(e.target.value)} autoComplete="off" />
          </label>
        </>
      )}
      {art === "schluessel" && (
        <>
          <input value={suche} onChange={(e) => setSuche(e.target.value)} placeholder="Schlüssel suchen" />
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {treffer.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => setSchluesselId(g.id)}
                style={{ textAlign: "left", fontWeight: g.id === schluesselId ? 700 : 400 }}
              >
                {g.name}
              </button>
            ))}
            {treffer.length === 0 && <span style={{ fontSize: "0.8em", color: "var(--text-leise)" }}>Nichts gefunden.</span>}
          </div>
        </>
      )}
      {art === "spiel" && (
        <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 8 }}>
          Länge bis auf
          <input
            type="number"
            min={1}
            value={laenge}
            onChange={(e) => setLaenge(Math.max(1, Number(e.target.value) || 1))}
            style={{ width: 70 }}
          />
        </label>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" disabled={laeuft} onClick={() => void setzen({ aufgeschlossen: false })}>
          Schloss setzen
        </button>
        {item.schlossArt && item.aufgeschlossen && (
          <button type="button" disabled={laeuft} onClick={() => void setzen({ aufgeschlossen: false })}>
            Wieder zusperren
          </button>
        )}
        {item.schlossArt && (
          <button type="button" disabled={laeuft} onClick={() => void setzen({ schlossArt: "", aufgeschlossen: false })}>
            Schloss abnehmen
          </button>
        )}
      </div>
      {fehler && <p style={{ margin: 0, fontSize: "0.8em", color: "var(--neon-rot, #e55)" }}>{fehler}</p>}
    </div>
  );
}
