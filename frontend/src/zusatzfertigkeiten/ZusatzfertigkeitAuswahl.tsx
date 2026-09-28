import { useEffect, useMemo, useState } from "react";
import { zusatzfertigkeitenApi, type Zusatzfertigkeit } from "./api";
import "./zusatzfertigkeiten.css";

/**
 * Rein clientseitige Zusatzfertigkeiten-Auswahl für den Fertigkeiten-Schritt
 * der Charaktererstellung (28.09.2026, Marks Korrektur — siehe
 * `traits/Charaktererstellung.tsx`).
 *
 * Anders als `ZusatzfertigkeitPopup.tsx` (LevelUp, sofortiger Server-Write
 * mit EP-/eigenem-Freebee-Abzug) schreibt diese Komponente NICHTS an den
 * Server: sie lädt nur den Katalog dieser Kampagne und meldet gewählte/
 * abgewählte IDs über `onWaehlen`/`onAbwaehlen` an den Erstellungs-State
 * zurück — genau wie die Auswahl eines Fertigkeitspakets oder eines
 * Hintergrunds. Bezahlt wird erst im Freebees-Schritt aus dem gemeinsamen
 * Hauptpool, gespeichert erst beim finalen `bogenApi.erstellen(...)`-Submit.
 */
export function ZusatzfertigkeitAuswahl({
  campaignId,
  gewaehlteIds,
  onWaehlen,
  onAbwaehlen,
}: {
  campaignId: string;
  /** IDs der bereits in diesem Erstellungs-Durchlauf gewählten Einträge. */
  gewaehlteIds: string[];
  onWaehlen: (z: Zusatzfertigkeit) => void;
  onAbwaehlen: (id: string) => void;
}) {
  const [katalog, setKatalog] = useState<Zusatzfertigkeit[]>([]);
  const [suche, setSuche] = useState("");
  const [laedt, setLaedt] = useState(true);

  useEffect(() => {
    setLaedt(true);
    zusatzfertigkeitenApi
      .liste(campaignId)
      .then(setKatalog)
      .catch(() => setKatalog([]))
      .finally(() => setLaedt(false));
  }, [campaignId]);

  const gewaehlteSet = useMemo(() => new Set(gewaehlteIds), [gewaehlteIds]);

  const gefiltert = useMemo(() => {
    const suchtext = suche.trim().toLowerCase();
    if (!suchtext) return katalog;
    return katalog.filter(
      (z) => z.name.toLowerCase().includes(suchtext) || z.kurzbeschreibung.toLowerCase().includes(suchtext),
    );
  }, [katalog, suche]);

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Zusatzfertigkeiten…</p>;

  if (katalog.length === 0) {
    return (
      <p className="zf-leer">
        In dieser Kampagne sind noch keine Zusatzfertigkeiten eingetragen — die Spielleitung pflegt sie
        im Kampagnen-Menü.
      </p>
    );
  }

  return (
    <div className="zfp-popup">
      {katalog.length > 6 && (
        <input
          type="text"
          className="zfp-suche"
          placeholder="Suchen…"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
      )}
      <div className="zfp-liste">
        {gefiltert.map((z) => {
          const gewaehlt = gewaehlteSet.has(z.id);
          return (
            <button
              key={z.id}
              type="button"
              className={`zfp-eintrag${gewaehlt ? " zfp-eintrag-aktiv" : ""}`}
              onClick={() => (gewaehlt ? onAbwaehlen(z.id) : onWaehlen(z))}
            >
              <span className="zfp-eintrag-name">{z.name}</span>
              {z.kurzbeschreibung && <span className="zfp-eintrag-kurz">{z.kurzbeschreibung}</span>}
              <span className="zfp-eintrag-knopf">{gewaehlt ? "✓ Gewählt" : "+ Wählen"}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
