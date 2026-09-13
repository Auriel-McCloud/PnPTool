/**
 * Ideenschmiede: Entwürfe sammeln, prüfen, in die Kampagne verschieben.
 *
 * Zeigt alle Entitäten mit istEntwurf=true. Das können manuell angelegte
 * Ideen sein oder KI-generierte Inhalte, die noch geprüft werden müssen.
 *
 * Klick auf einen Entwurf öffnet ihn im Editor (je nach Typ).
 * "Übernehmen" setzt istEntwurf=false und verschiebt ihn in die Kampagne.
 */

import { useCallback, useEffect, useState } from "react";
import {
  getEntwuerfe,
  inKampagneVerschieben,
  entwurfLoeschen,
  entwurfAnlegen,
  type EntwurfItem,
} from "./api";
import { Fenster } from "../shell/Fenster";
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

  // Anlegen-Popup
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuerName, setNeuerName] = useState("");
  const [neuerTyp, setNeuerTyp] = useState<EntwurfItem["typ"]>("WikiSeite");
  const [anlegenLaeuft, setAnlegenLaeuft] = useState(false);

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
    if (!confirm(`„${item.name}" wirklich in die Kampagne übernehmen?`)) return;
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

  const handleAnlegen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!neuerName.trim() || anlegenLaeuft) return;
    setAnlegenLaeuft(true);
    try {
      await entwurfAnlegen(campaignId, neuerTyp, neuerName.trim());
      setNeuerName("");
      setAnlegenOffen(false);
      await laden();
    } catch (err) {
      alert("Fehler beim Anlegen");
      console.error(err);
    } finally {
      setAnlegenLaeuft(false);
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
        <div className="is-header-zeile">
          <h2>🔧 Ideenschmiede</h2>
          <button className="is-neu-btn" onClick={() => setAnlegenOffen(true)}>
            + Neue Idee
          </button>
        </div>
        <p className="is-beschreibung">
          Hier landen Entwürfe und KI-generierte Ideen. Prüfe sie und verschiebe
          sie in die Kampagne, wenn sie bereit sind.
        </p>
      </header>

      {/* Anlegen-Popup im Commlink-Stil */}
      <Fenster
        offen={anlegenOffen}
        titel="Neue Idee anlegen"
        kennung="ideenschmiede-anlegen"
        onSchliessen={() => setAnlegenOffen(false)}
      >
        <form className="is-anlegen-form" onSubmit={handleAnlegen}>
          <label className="is-label">
            Typ
            <select
              className="is-select"
              value={neuerTyp}
              onChange={(e) => setNeuerTyp(e.target.value as EntwurfItem["typ"])}
            >
              <option value="WikiSeite">📄 Wiki-Seite</option>
              <option value="Person">👤 Person / NPC</option>
              <option value="Ort">📍 Ort</option>
              <option value="Event">📅 Ereignis</option>
              <option value="Gegenstand">📦 Gegenstand</option>
            </select>
          </label>

          <label className="is-label">
            Name
            <input
              type="text"
              className="is-input"
              placeholder="Name oder Titel der Idee"
              value={neuerName}
              onChange={(e) => setNeuerName(e.target.value)}
              autoFocus
              required
            />
          </label>

          <div className="is-anlegen-aktionen">
            <button type="submit" className="is-btn-anlegen" disabled={anlegenLaeuft}>
              {anlegenLaeuft ? "Wird angelegt..." : "Anlegen"}
            </button>
            <button
              type="button"
              className="is-btn-abbrechen"
              onClick={() => setAnlegenOffen(false)}
            >
              Abbrechen
            </button>
          </div>
        </form>
      </Fenster>

      {entwuerfe.length === 0 ? (
        <div className="is-leer">
          <p>🎨 Die Schmiede ist leer!</p>
          <p>
            Klicke auf „+ Neue Idee" um einen Entwurf anzulegen, oder lass später
            die KI Ideen generieren.
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
