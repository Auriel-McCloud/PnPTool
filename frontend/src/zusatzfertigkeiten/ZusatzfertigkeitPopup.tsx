import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { zusatzfertigkeitenApi, type Zusatzfertigkeit, type PersonZusatzfertigkeitenAntwort } from "./api";
import "./zusatzfertigkeiten.css";

/**
 * "+ Zusatzfertigkeit"-Popup — an zwei Stellen wiederverwendet
 * (Charaktererstellung UND LevelUp, Marks Vorgabe: derselbe Popup-Button an
 * beiden Stellen, kein Sonderfall). Zeigt die in dieser Kampagne noch nicht
 * gewählten Einträge (Name + Kurzbeschreibung), Klick fügt mit Stufe 1
 * hinzu — mit Kostenanzeige vor der Bestätigung, wie beim normalen Steigern.
 *
 * Suche im Auswahl-Popup (Projektkonvention): sobald der Katalog wächst,
 * soll man nicht durch eine lange ungefilterte Liste scrollen müssen.
 */
export function ZusatzfertigkeitPopup({
  campaignId,
  personId,
  offen,
  onSchliessen,
  onHinzugefuegt,
}: {
  campaignId: string;
  personId: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Damit die aufrufende Ansicht (Erstellung/Blatt) den neuen Stand übernimmt. */
  onHinzugefuegt: (antwort: PersonZusatzfertigkeitenAntwort) => void;
}) {
  const [katalog, setKatalog] = useState<Zusatzfertigkeit[]>([]);
  const [gewaehlteIds, setGewaehlteIds] = useState<Set<string>>(new Set());
  const [kosten, setKosten] = useState<{ freebee: boolean; frei: number } | null>(null);
  const [suche, setSuche] = useState("");
  const [laedt, setLaedt] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [waehltGerade, setWaehltGerade] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    setLaedt(true);
    setFehler(null);
    setSuche("");
    Promise.all([
      zusatzfertigkeitenApi.liste(campaignId),
      zusatzfertigkeitenApi.vonPerson(campaignId, personId),
    ])
      .then(([alle, person]) => {
        setKatalog(alle);
        setGewaehlteIds(new Set(person.gewaehlt.map((z) => z.id)));
        setKosten(
          person.erstellungAbgeschlossen
            ? { freebee: false, frei: person.erfahrungVerfuegbar }
            : { freebee: true, frei: person.freebeesUebrig },
        );
      })
      .catch(() => setFehler("Der Katalog konnte nicht geladen werden."))
      .finally(() => setLaedt(false));
  }, [offen, campaignId, personId]);

  const waehlbar = useMemo(() => {
    const suchtext = suche.trim().toLowerCase();
    return katalog
      .filter((z) => !gewaehlteIds.has(z.id))
      .filter((z) => !suchtext || z.name.toLowerCase().includes(suchtext) || z.kurzbeschreibung.toLowerCase().includes(suchtext));
  }, [katalog, gewaehlteIds, suche]);

  async function waehlen(z: Zusatzfertigkeit) {
    setWaehltGerade(z.id);
    setFehler(null);
    try {
      const antwort = await zusatzfertigkeitenApi.hinzufuegen(campaignId, personId, z.id);
      onHinzugefuegt(antwort);
      setGewaehlteIds(new Set(antwort.gewaehlt.map((g) => g.id)));
      setKosten((alt) =>
        alt
          ? {
              ...alt,
              frei: alt.freebee ? antwort.freebeesUebrig : antwort.erfahrungVerfuegbar,
            }
          : alt,
      );
    } catch (e) {
      setFehler((e as Error).message || "Das Hinzufügen hat nicht geklappt.");
    } finally {
      setWaehltGerade(null);
    }
  }

  return (
    <Fenster
      offen={offen}
      breit
      titel="+ Zusatzfertigkeit"
      unterzeile={
        kosten
          ? kosten.freebee
            ? `${kosten.frei} Freebees übrig für neue Zusatzfertigkeiten`
            : `${kosten.frei} EP frei`
          : undefined
      }
      kennung={`zusatzfertigkeit-popup:${personId}`}
      onSchliessen={onSchliessen}
    >
      <div className="zfp-popup">
        {waehlbar.length > 6 && (
          <input
            type="text"
            className="zfp-suche"
            placeholder="Suchen…"
            value={suche}
            onChange={(e) => setSuche(e.target.value)}
            autoFocus
          />
        )}
        {fehler && <p className="zf-ki-fehler">{fehler}</p>}
        {laedt && <p style={{ color: "var(--text-leise)" }}>Lade Katalog…</p>}
        {!laedt && katalog.length === 0 && (
          <p className="zf-leer">
            In dieser Kampagne sind noch keine Zusatzfertigkeiten eingetragen — die Spielleitung pflegt sie
            im Kampagnen-Menü.
          </p>
        )}
        {!laedt && katalog.length > 0 && waehlbar.length === 0 && (
          <p className="zf-leer">Keine weiteren Zusatzfertigkeiten verfügbar.</p>
        )}
        <div className="zfp-liste">
          {waehlbar.map((z) => (
            <button
              key={z.id}
              type="button"
              className="zfp-eintrag"
              disabled={waehltGerade !== null}
              onClick={() => waehlen(z)}
            >
              <span className="zfp-eintrag-name">{z.name}</span>
              {z.kurzbeschreibung && <span className="zfp-eintrag-kurz">{z.kurzbeschreibung}</span>}
              <span className="zfp-eintrag-knopf">
                {waehltGerade === z.id ? "…" : "+ Wählen"}
              </span>
            </button>
          ))}
        </div>
      </div>
    </Fenster>
  );
}
