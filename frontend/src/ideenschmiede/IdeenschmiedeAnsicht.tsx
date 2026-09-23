/**
 * Ideenschmiede: Entwürfe sammeln, prüfen, bearbeiten, in die Kampagne verschieben.
 *
 * Zeigt alle Entitäten mit istEntwurf=true. Klick auf einen Entwurf öffnet
 * das vollständige Detail-Popup zum Bearbeiten (Bilder, Notizen, Beziehungen).
 * "Übernehmen" setzt istEntwurf=false und verschiebt ihn in die Kampagne.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getEntwuerfe,
  inKampagneVerschieben,
  entwurfLoeschen,
  entwurfAnlegen,
  kiIdee,
  type EntwurfItem,
  type KiTyp,
} from "./api";
import { api } from "../api/client";
import { Fenster } from "../shell/Fenster";
import { OrtDetail } from "../entities/OrtDetail";
import { EventDetail } from "../entities/EventDetail";
import { NPCDetail } from "../entities/NPCDetail";
import { FraktionDetail } from "../entities/FraktionDetail";
import { WikiEditor } from "../wiki/WikiEditor";
import { Bestaetigung } from "../shell/Bestaetigung";
import type { Ort } from "../entities/api";
import type { Event } from "../entities/api";
import type { Person } from "../entities/api";
import type { Fraktion } from "../entities/api";
import type { Verbindung } from "../entities/api";
import type { EntityKind } from "../entities/api";
import type { PersonOption } from "../entities/VisibilitySelector";
import "./ideenschmiede.css";

// Icons für die verschiedenen Typen
const TYP_ICONS: Record<EntwurfItem["typ"], string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  WikiSeite: "📄",
  Gegenstand: "📦",
  Fraktion: "⬡",
};

const TYP_LABELS: Record<EntwurfItem["typ"], string> = {
  Person: "Person",
  Ort: "Ort",
  Event: "Ereignis",
  WikiSeite: "Geschichte",
  Gegenstand: "Gegenstand",
  Fraktion: "Fraktion",
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

  // KI-Popup (Gemini generiert Entwürfe)
  const [kiOffen, setKiOffen] = useState(false);
  const [kiTyp, setKiTyp] = useState<KiTyp>("charakter");
  const [kiPrompt, setKiPrompt] = useState("");
  const [kiLaeuft, setKiLaeuft] = useState(false);
  const [kiFehler, setKiFehler] = useState<string | null>(null);

  // Detail-Popups
  const [ortDetailFuer, setOrtDetailFuer] = useState<Ort | null>(null);
  const [eventDetailFuer, setEventDetailFuer] = useState<Event | null>(null);
  const [personDetailFuer, setPersonDetailFuer] = useState<Person | null>(null);
  const [fraktionDetailFuer, setFraktionDetailFuer] = useState<Fraktion | null>(null);
  const [wikiDetailFuer, setWikiDetailFuer] = useState<{ id: string; titel: string; inhalt: string } | null>(null);
  const [loeschenOffen, setLoeschenOffen] = useState<EntwurfItem | null>(null);

  // Daten für die Detail-Komponenten
  const [allePersonen, setAllePersonen] = useState<Person[]>([]);
  const [alleOrte, setAlleOrte] = useState<Ort[]>([]);
  const [alleEvents, setAlleEvents] = useState<Event[]>([]);
  const [alleFraktionen, setAlleFraktionen] = useState<Fraktion[]>([]);
  const [verbindungen, setVerbindungen] = useState<Verbindung[]>([]);

  const laden = useCallback(async () => {
    setLadend(true);
    setFehler(null);
    try {
      // Entwürfe laden
      const entwuerfeDaten = await getEntwuerfe(campaignId);
      setEntwuerfe(entwuerfeDaten);

      // Alle Entities für die Detail-Popups laden (inkl. Nicht-Entwürfe)
      const [personen, orte, events, fraktionen, verbindungenData] = await Promise.all([
        api.get<Person[]>(`/api/campaigns/${campaignId}/personen`),
        api.get<Ort[]>(`/api/campaigns/${campaignId}/orte`),
        api.get<Event[]>(`/api/campaigns/${campaignId}/events`),
        api.get<Fraktion[]>(`/api/campaigns/${campaignId}/fraktionen`),
        api.get<Verbindung[]>(`/api/campaigns/${campaignId}/verbindungen`),
      ]);
      setAllePersonen(personen);
      setAlleOrte(orte);
      setAlleEvents(events);
      setAlleFraktionen(fraktionen);
      setVerbindungen(verbindungenData);
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

  // PC-Optionen für VisibilitySelector
  const pcOptions: PersonOption[] = useMemo(
    () =>
      allePersonen
        .filter((p) => p.personType === "PC")
        .map((p) => ({ id: p.id, name: p.name })),
    [allePersonen]
  );

  // Namens-Tabelle für Beziehungsanzeige
  const namensTabelle = useMemo(() => {
    const map = new Map<string, { name: string; kind: EntityKind }>();
    for (const p of allePersonen) {
      map.set(p.id, { name: p.name, kind: "Person" });
    }
    for (const o of alleOrte) {
      map.set(o.id, { name: o.name, kind: "Ort" });
    }
    for (const e of alleEvents) {
      map.set(e.id, { name: e.title, kind: "Event" });
    }
    for (const f of alleFraktionen) {
      map.set(f.id, { name: f.name, kind: "Fraktion" });
    }
    return map;
  }, [allePersonen, alleOrte, alleEvents, alleFraktionen]);

  // Wie in EntityManager: nach einer Änderung den frischen Stand statt des
  // einmaligen Snapshots vom Öffnen zeigen — sonst zeigt z.B. die
  // Bildergalerie nach dem Ändern weiter die alten Bilder. Anders als dort
  // kommt der frische Stand nicht aus der Liste (die Entwürfe herausfiltert),
  // sondern per gezieltem Einzel-Abruf derselben Route wie beim Öffnen.
  const detailRefreshen = useCallback(async () => {
    try {
      if (ortDetailFuer) {
        const frisch = await api.get<Ort>(`/api/campaigns/${campaignId}/orte/${ortDetailFuer.id}`);
        setOrtDetailFuer(frisch);
      } else if (eventDetailFuer) {
        const frisch = await api.get<Event>(`/api/campaigns/${campaignId}/events/${eventDetailFuer.id}`);
        setEventDetailFuer(frisch);
      } else if (personDetailFuer) {
        const frisch = await api.get<Person>(`/api/campaigns/${campaignId}/personen/${personDetailFuer.id}`);
        setPersonDetailFuer(frisch);
      } else if (fraktionDetailFuer) {
        const frisch = await api.get<Fraktion>(`/api/campaigns/${campaignId}/fraktionen/${fraktionDetailFuer.id}`);
        setFraktionDetailFuer(frisch);
      }
    } catch (e) {
      console.error("Fehler beim Aktualisieren des Details:", e);
    }
    await laden();
  }, [campaignId, ortDetailFuer, eventDetailFuer, personDetailFuer, fraktionDetailFuer, laden]);

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
    setLoeschenOffen(item);
  };

  const handleLoeschenBestaetigt = async () => {
    if (!loeschenOffen) return;
    const item = loeschenOffen;
    setLoeschenOffen(null);
    
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

  /** Lässt Gemini eine Idee generieren und als Entwurf ablegen. */
  const handleKiGenerieren = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!kiPrompt.trim() || kiLaeuft) return;
    setKiLaeuft(true);
    setKiFehler(null);
    try {
      await kiIdee(campaignId, kiTyp, kiPrompt.trim());
      setKiPrompt("");
      setKiOffen(false);
      await laden();
    } catch (err) {
      // Die Fehlermeldung des Backends (z.B. "Kein API-Key" oder ein
      // Gemini-Fehler) ist lesbarer als ein roher "Fehler beim Generieren".
      setKiFehler(err instanceof Error ? err.message : "Generieren fehlgeschlagen");
    } finally {
      setKiLaeuft(false);
    }
  };

  /** Öffnet das passende Detail-Popup je nach Typ. */
  const handleItemKlick = async (item: EntwurfItem) => {
    try {
      const endpoints: Record<EntwurfItem["typ"], string> = {
        Person: `/api/campaigns/${campaignId}/personen/${item.id}`,
        Ort: `/api/campaigns/${campaignId}/orte/${item.id}`,
        Event: `/api/campaigns/${campaignId}/events/${item.id}`,
        WikiSeite: `/api/campaigns/${campaignId}/wiki/seiten/${item.id}`,
        Gegenstand: `/api/campaigns/${campaignId}/vorlagen/${item.id}`,
        Fraktion: `/api/campaigns/${campaignId}/fraktionen/${item.id}`,
      };

      // Für Gegenstand gibt es noch kein Detail-Popup
      if (item.typ === "Gegenstand") {
        alert(`Gegenstand "${item.name}" — Detail-Ansicht noch nicht implementiert.`);
        return;
      }

      const entity = await api.get<any>(endpoints[item.typ]);

      switch (item.typ) {
        case "Ort":
          setOrtDetailFuer(entity as Ort);
          break;
        case "Event":
          setEventDetailFuer(entity as Event);
          break;
        case "Person":
          setPersonDetailFuer(entity as Person);
          break;
        case "Fraktion":
          setFraktionDetailFuer(entity as Fraktion);
          break;
        case "WikiSeite":
          setWikiDetailFuer({
            id: entity.id,
            titel: entity.titel,
            inhalt: entity.inhalt || '{"type":"doc","content":[]}',
          });
          break;
      }
    } catch (e) {
      console.error("Fehler beim Laden:", e);
      alert("Fehler beim Öffnen des Entwurfs");
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
          <div style={{ display: "flex", gap: 8 }}>
            <button className="is-neu-btn" onClick={() => setAnlegenOffen(true)}>
              + Neue Idee
            </button>
            <button className="is-ki-btn" onClick={() => setKiOffen(true)} title="Mit Gemini eine Idee generieren">
              ✨ KI
            </button>
          </div>
        </div>
        <p className="is-beschreibung">
          Hier landen Entwürfe und KI-generierte Ideen. Klicke auf einen Entwurf
          um ihn zu bearbeiten, oder verschiebe ihn in die Kampagne.
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
              <option value="WikiSeite">📄 Geschichte</option>
              <option value="Person">👤 Person / NPC</option>
              <option value="Ort">📍 Ort</option>
              <option value="Event">📅 Ereignis</option>
              <option value="Gegenstand">📦 Gegenstand</option>
              <option value="Fraktion">⬡ Fraktion</option>
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

      {/* KI-Popup: Gemini generiert einen Entwurf */}
      <Fenster
        offen={kiOffen}
        titel="✨ KI-Idee generieren"
        kennung="ideenschmiede-ki"
        onSchliessen={() => {
          setKiOffen(false);
          setKiFehler(null);
        }}
      >
        <form className="is-anlegen-form" onSubmit={handleKiGenerieren}>
          <label className="is-label">
            Was soll entstehen?
            <select className="is-select" value={kiTyp} onChange={(e) => setKiTyp(e.target.value as KiTyp)}>
              <option value="charakter">👤 Charakter / NPC</option>
              <option value="story">📄 Story-Part / Szene</option>
              <option value="gegenstand">📦 Gegenstand</option>
            </select>
          </label>

          <label className="is-label">
            Wunsch
            <textarea
              className="is-input"
              rows={4}
              style={{ resize: "vertical", minHeight: 80, width: "100%" }}
              placeholder="z.B. Ein mürrischer alter Waffenhändler im Hafenviertel."
              value={kiPrompt}
              onChange={(e) => setKiPrompt(e.target.value)}
              autoFocus
              required
            />
          </label>

          {kiFehler && (
            <p style={{ margin: 0, color: "var(--signal)", fontSize: 12 }}>{kiFehler}</p>
          )}

          <div className="is-anlegen-aktionen">
            <button type="submit" className="is-btn-anlegen" disabled={kiLaeuft || !kiPrompt.trim()}>
              {kiLaeuft ? "Generiert…" : "Generieren"}
            </button>
            <button
              type="button"
              className="is-btn-abbrechen"
              onClick={() => {
                setKiOffen(false);
                setKiFehler(null);
              }}
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
            {(["Person", "Ort", "Event", "WikiSeite", "Gegenstand", "Fraktion"] as const).map((typ) =>
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
              <li
                key={`${item.typ}-${item.id}`}
                className="is-item is-item-klickbar"
                onClick={() => handleItemKlick(item)}
              >
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
                <div className="is-aktionen" onClick={(e) => e.stopPropagation()}>
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

      {/* Vollständige Detail-Popups zum Bearbeiten */}
      {ortDetailFuer && (
        <OrtDetail
          campaignId={campaignId}
          ort={ortDetailFuer}
          verbindungen={verbindungen}
          namen={namensTabelle}
          pcOptions={pcOptions}
          onSchliessen={() => setOrtDetailFuer(null)}
          onGeaendert={detailRefreshen}
        />
      )}
      {eventDetailFuer && (
        <EventDetail
          campaignId={campaignId}
          event={eventDetailFuer}
          verbindungen={verbindungen}
          namen={namensTabelle}
          pcOptions={pcOptions}
          onSchliessen={() => setEventDetailFuer(null)}
          onGeaendert={detailRefreshen}
        />
      )}
      {personDetailFuer && (
        <NPCDetail
          campaignId={campaignId}
          person={personDetailFuer}
          verbindungen={verbindungen}
          namen={namensTabelle}
          pcOptions={pcOptions}
          onSchliessen={() => setPersonDetailFuer(null)}
          onGeaendert={detailRefreshen}
        />
      )}
      {fraktionDetailFuer && (
        <FraktionDetail
          campaignId={campaignId}
          fraktion={fraktionDetailFuer}
          verbindungen={verbindungen}
          namen={namensTabelle}
          pcOptions={pcOptions}
          onSchliessen={() => setFraktionDetailFuer(null)}
          onGeaendert={detailRefreshen}
        />
      )}
      {wikiDetailFuer && (
        <Fenster
          offen={true}
          titel={`📄 ${wikiDetailFuer.titel}`}
          kennung="ideenschmiede-wiki"
          onSchliessen={() => {
            setWikiDetailFuer(null);
            laden();
          }}
        >
          <div className="is-wiki-editor">
            <WikiEditor
              campaignId={campaignId}
              seitenId={wikiDetailFuer.id}
              inhalt={wikiDetailFuer.inhalt}
              nurLesen={false}
              onChange={() => {
                // Auto-Save wird vom WikiEditor selbst gehandhabt
              }}
            />
          </div>
        </Fenster>
      )}

      {/* Bestätigungsdialog für Löschen */}
      {loeschenOffen && (
        <Bestaetigung
          titel="Entwurf löschen?"
          text={`„${loeschenOffen.name}" wird endgültig gelöscht. Das lässt sich nicht rückgängig machen.`}
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={handleLoeschenBestaetigt}
          onNein={() => setLoeschenOffen(null)}
        />
      )}
    </div>
  );
}
