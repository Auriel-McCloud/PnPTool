/**
 * Ideenschmiede: Entwürfe sammeln, prüfen, in die Kampagne verschieben.
 *
 * Zeigt alle Entitäten mit istEntwurf=true. Das können manuell angelegte
 * Ideen sein oder KI-generierte Inhalte, die noch geprüft werden müssen.
 */

import { useCallback, useEffect, useState } from "react";
import {
  getEntwuerfe,
  inKampagneVerschieben,
  entwurfLoeschen,
  type EntwurfItem,
} from "./api";
import "./ideenschmiede.css";

// Icons für die verschiedenen Typen
const TYP_ICONS: Record<EntwurfItem["typ"], string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  WikiSeite: "📄",
  Gegenstand: "📦",
};

const TYP_LABELS: Record<EntwurfItem["typ"], string> = {
  Person: "Person",
  Ort: "Ort",
  Event: "Ereignis",
  WikiSeite: "Wiki-Seite",
  Gegenstand: "Gegenstand",
};

interface Props {
  campaignId: string;
}

export function IdeenschmiedeAnsicht({ campaignId }: Props) {
  const [entwuerfe, setEntwuerfe] = useState<EntwurfItem[]>([]);
  const [ladend, setLadend] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [filter, setFilter] = useState<EntwurfItem["typ"] | "alle">("alle");

  const laden = useCallback(async () => {
    setLadend(true);
    setFehler(null);
    try {
      const daten = await getEntwuerfe(campaignId);
      setEntwuerfe(daten);
    } catch (e) {
      setFehler("Fehler beim Laden der Entwürfe");
      console.error(e);
    } finally {
      setLadend(false);
    }
  }, [campaignId]);

  useEffect(() => {
    laden();
  }, [laden]);

  const handleVerschieben = async (item: EntwurfItem) => {
    if (!confirm(`„${item.name}" wirklich in die Kampagne verschieben?`)) return;
    try {
      await inKampagneVerschieben(campaignId, item.typ, item.id);
      setEntwuerfe((prev) => prev.filter((e) => e.id !== item.id));
    } catch (e) {
      alert("Fehler beim Verschieben");
      console.error(e);
    }
  };

  const handleLoeschen = async (item: EntwurfItem) => {
    if (!confirm(`„${item.name}" wirklich löschen? Das kann nicht rückgängig gemacht werden.`)) return;
    try {
      await entwurfLoeschen(campaignId, item.typ, item.id);
      setEntwuerfe((prev) => prev.filter((e) => e.id !== item.id));
    } catch (e) {
      alert("Fehler beim Löschen");
      console.error(e);
    }
  };

  const gefiltert = filter === "alle"
    ? entwuerfe
    : entwuerfe.filter((e) => e.typ === filter);

  // Zähle pro Typ
  const anzahlProTyp: Record<string, number> = { alle: entwuerfe.length };
  for (const e of entwuerfe) {
    anzahlProTyp[e.typ] = (anzahlProTyp[e.typ] || 0) + 1;
  }

  if (ladend) {
    return <div className="is-leer">Lade Entwürfe...</div>;
  }

  if (fehler) {
    return <div className="is-fehler">{fehler}</div>;
  }

  return (
    <div className="ideenschmiede">
      <header className="is-header">
        <h2>🔧 Ideenschmiede</h2>
        <p className="is-beschreibung">
          Hier landen Entwürfe und KI-generierte Ideen. Prüfe sie und verschiebe
          sie in die Kampagne, wenn sie bereit sind.
        </p>
      </header>

      {entwuerfe.length === 0 ? (
        <div className="is-leer">
          <p>🎨 Die Schmiede ist leer!</p>
          <p>
            Erstelle neue Entwürfe über die anderen Bereiche (Personen, Orte, Wiki...)
            und markiere sie als "Entwurf", oder lass die KI Ideen generieren.
          </p>
        </div>
      ) : (
        <>
          {/* Filter-Tabs */}
          <div className="is-filter">
            <button
              className={filter === "alle" ? "aktiv" : ""}
              onClick={() => setFilter("alle")}
            >
              Alle ({anzahlProTyp.alle})
            </button>
            {(["Person", "Ort", "Event", "WikiSeite", "Gegenstand"] as const).map((typ) =>
              anzahlProTyp[typ] ? (
                <button
                  key={typ}
                  className={filter === typ ? "aktiv" : ""}
                  onClick={() => setFilter(typ)}
                >
                  {TYP_ICONS[typ]} {TYP_LABELS[typ]} ({anzahlProTyp[typ]})
                </button>
              ) : null
            )}
          </div>

          {/* Liste */}
          <ul className="is-liste">
            {gefiltert.map((item) => (
              <li key={`${item.typ}-${item.id}`} className="is-item">
                <span className="is-icon">{TYP_ICONS[item.typ]}</span>
                <div className="is-inhalt">
                  <strong>{item.name}</strong>
                  <span className="is-typ">{TYP_LABELS[item.typ]}</span>
                  {item.beschreibung && (
                    <p className="is-beschreibung-kurz">
                      {item.beschreibung.slice(0, 120)}
                      {item.beschreibung.length > 120 ? "..." : ""}
                    </p>
                  )}
                </div>
                <div className="is-aktionen">
                  <button
                    className="is-verschieben"
                    onClick={() => handleVerschieben(item)}
                    title="In die Kampagne verschieben"
                  >
                    ✓ Übernehmen
                  </button>
                  <button
                    className="is-loeschen"
                    onClick={() => handleLoeschen(item)}
                    title="Entwurf löschen"
                  >
                    ✗
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
