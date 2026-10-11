import { useEffect, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { Bestaetigung } from "../shell/Bestaetigung";
import { bogenApi, type BogenUebersicht } from "./bogenApi";

/**
 * SL-Aktion "Rasten" (11.10.2026, docs/api/rast.md): heilt einen oder
 * mehrere PCs nach fester Formel, kein Würfeln. "Vollständige Heilung"
 * daneben ist der Fallback-Knopf "für den Fall der Fälle" — keine
 * Bedingungen, heilt sofort alles inklusive Rüstung.
 *
 * SL-only (die Route selbst ist per require_campaign_gm abgesichert, das
 * Popup hängt am 🏕️-Werkzeug in App.tsx, das nur die SL-Ansicht zeigt).
 */
export function RastenVerwaltung({ campaignId }: { campaignId: string }) {
  const [personen, setPersonen] = useState<Person[]>([]);
  const [ausgewaehlt, setAusgewaehlt] = useState<Set<string>>(new Set());
  const [laeuft, setLaeuft] = useState(false);
  const [bestaetigung, setBestaetigung] = useState<"rasten" | "heilung" | null>(null);
  const [ergebnis, setErgebnis] = useState<Record<string, BogenUebersicht>>({});
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    entitiesApi
      .listPersonen(campaignId)
      .then((alle) => setPersonen(alle.filter((p) => p.personType === "PC")))
      .catch(() => setPersonen([]));
  }, [campaignId]);

  function schalten(id: string) {
    setAusgewaehlt((alt) => {
      const neu = new Set(alt);
      if (neu.has(id)) neu.delete(id);
      else neu.add(id);
      return neu;
    });
  }

  function alleUmschalten() {
    setAusgewaehlt((alt) => (alt.size === personen.length ? new Set() : new Set(personen.map((p) => p.id))));
  }

  async function ausfuehren(art: "rasten" | "heilung") {
    const ids = [...ausgewaehlt];
    if (ids.length === 0) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const antwort =
        art === "rasten"
          ? await bogenApi.rasten(campaignId, ids)
          : await bogenApi.vollstaendigeHeilung(campaignId, ids);
      setErgebnis((alt) => ({ ...alt, ...antwort }));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Fehlgeschlagen");
    } finally {
      setLaeuft(false);
      setBestaetigung(null);
    }
  }

  const alleAusgewaehlt = personen.length > 0 && ausgewaehlt.size === personen.length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <p style={{ color: "var(--text-leise)", fontSize: "0.9em", margin: 0 }}>
        Ein Klick = eine Rast pro ausgewählter Person: Schlagschaden heilt vollständig, schwerer
        Schaden sinkt um 1 (ein Zähler sammelt bis zum nächsten geheilten Unheilbar-Punkt bei 7),
        natürliche Rüstung heilt bei vollständig gesunder Person +1 Kästchen. „Vollständige
        Heilung" ist der Fallback ohne Bedingungen — auch für die Rüstung.
      </p>

      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
        <input type="checkbox" checked={alleAusgewaehlt} onChange={alleUmschalten} disabled={personen.length === 0} />
        Alle auswählen ({personen.length})
      </label>

      <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 320, overflowY: "auto" }}>
        {personen.map((p) => {
          const u = ergebnis[p.id];
          return (
            <label key={p.id} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.95em" }}>
              <input type="checkbox" checked={ausgewaehlt.has(p.id)} onChange={() => schalten(p.id)} />
              <span>{p.name}</span>
              {u && (
                <span style={{ color: "var(--text-leise)", fontSize: "0.85em" }}>
                  — Schlag {u.schadenSchlag} · Schwer {u.schadenSchwer} · Unheilbar {u.schadenAggraviert} · Heil-Zähler{" "}
                  {u.schwerHeilZaehler}/7
                </span>
              )}
            </label>
          );
        })}
        {personen.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine PCs in dieser Kampagne.</p>}
      </div>

      {fehler && <p style={{ color: "var(--nein)" }}>{fehler}</p>}

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button type="button" onClick={() => setBestaetigung("rasten")} disabled={ausgewaehlt.size === 0 || laeuft}>
          🏕️ Rasten
        </button>
        <button type="button" onClick={() => setBestaetigung("heilung")} disabled={ausgewaehlt.size === 0 || laeuft}>
          ✚ Vollständige Heilung
        </button>
      </div>

      {bestaetigung === "rasten" && (
        <Bestaetigung
          titel="Rasten?"
          text={`${ausgewaehlt.size} Person(en) rasten einmal: Schlagschaden heilt, schwerer Schaden sinkt um 1, natürliche Rüstung heilt ggf. mit.`}
          jaText="Rasten"
          onJa={() => void ausfuehren("rasten")}
          onNein={() => setBestaetigung(null)}
        />
      )}
      {bestaetigung === "heilung" && (
        <Bestaetigung
          titel="Vollständige Heilung?"
          text={`${ausgewaehlt.size} Person(en) werden sofort komplett geheilt (Schaden, Zähler, Rüstung) — keine Bedingungen, kein Würfeln.`}
          jaText="Vollständig heilen"
          onJa={() => void ausfuehren("heilung")}
          onNein={() => setBestaetigung(null)}
        />
      )}
    </div>
  );
}
