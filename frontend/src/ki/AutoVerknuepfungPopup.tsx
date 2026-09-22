/**
 * ⧉✨ Auto-Verknüpfung — Popup mit den von der KI erkannten Erwähnungen UND
 * Beziehungen einer Wiki-Seite.
 *
 * Zweistufig wie die Rechtschreib-/Logikprüfung: „Vorschläge holen" listet
 * Treffer, jeder einzeln bestätigt. Zwei Arten von Treffern:
 *
 * - **Verweise** (Person/Ort/Event/Fraktion im Text erwähnt): „✓ Verknüpfen"
 *   fügt einen Verweis-Chip an der Textstelle ein.
 * - **Beziehungen** (der Text drückt eine konkrete Beziehung zwischen zwei
 *   erwähnten Entitäten aus, z.B. "arbeitet für"): „✓ Beziehung anlegen"
 *   erzeugt eine echte VERBINDUNG-Kante zwischen den beiden — dieselbe Art
 *   Kante wie der "+ Neue Verbindung"-Knopf im Beziehungen-Tab.
 *
 * Ein Treffer ohne passende bestehende Entität zeigt „neu" — Klick legt
 * zuerst einen SL-geheimen Entwurf in der Ideenschmiede an (Marks Vorgabe:
 * Entwurf zur Prüfung, kein Autocommit in die Kampagne).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import {
  verknuepfungAnwenden,
  verknuepfungBeziehungAnwenden,
  verknuepfungsVorschlaege,
  type BeziehungsVorschlag,
  type VerknuepfungsVorschlag,
} from "./api";

const TYP_ICON: Record<string, string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  Fraktion: "⬡",
};

function verweisSchluessel(v: VerknuepfungsVorschlag) {
  return `${v.zitat}:${v.typ}:${v.name}`;
}

function beziehungSchluessel(v: BeziehungsVorschlag) {
  return `${v.typ1}:${v.name1}:${v.beziehungstyp}:${v.typ2}:${v.name2}`;
}

export function AutoVerknuepfungPopup({
  offen,
  campaignId,
  seitenId,
  onSchliessen,
  onUebernommen,
}: {
  offen: boolean;
  campaignId: string;
  seitenId: string;
  onSchliessen: () => void;
  /** Nach jeder angewandten Verweis-Verknüpfung — Aufrufer aktualisiert den Editor mit dem neuen Inhalt. */
  onUebernommen: (neuerInhalt: string) => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [angewandt, setAngewandt] = useState<string | null>(null); // Schlüssel des gerade laufenden Vorschlags
  const [fehler, setFehler] = useState<string | null>(null);
  const [verweise, setVerweise] = useState<VerknuepfungsVorschlag[] | null>(null);
  const [beziehungen, setBeziehungen] = useState<BeziehungsVorschlag[]>([]);
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());

  if (!offen) return null;

  async function holen() {
    setLaedt(true);
    setFehler(null);
    try {
      const antwort = await verknuepfungsVorschlaege(campaignId, seitenId);
      setVerweise(antwort.verweise);
      setBeziehungen(antwort.beziehungen);
      setErledigt(new Set());
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Erkennung fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  async function verweisAnwenden(v: VerknuepfungsVorschlag) {
    const key = verweisSchluessel(v);
    setAngewandt(key);
    setFehler(null);
    try {
      const ergebnis = await verknuepfungAnwenden(campaignId, seitenId, v);
      if (!ergebnis.ersetzt) {
        setFehler(`„${v.zitat}" wurde im Text nicht mehr gefunden — schon geändert?`);
        return;
      }
      setErledigt((alt) => new Set(alt).add(key));
      onUebernommen(ergebnis.inhalt);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verknüpfen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  async function beziehungAnwenden(v: BeziehungsVorschlag) {
    const key = beziehungSchluessel(v);
    setAngewandt(key);
    setFehler(null);
    try {
      await verknuepfungBeziehungAnwenden(campaignId, seitenId, v);
      setErledigt((alt) => new Set(alt).add(key));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Beziehung anlegen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  function schliessenUndZuruecksetzen() {
    setVerweise(null);
    setBeziehungen([]);
    setErledigt(new Set());
    setFehler(null);
    onSchliessen();
  }

  const offeneVerweise = (verweise ?? []).filter((v) => !erledigt.has(verweisSchluessel(v)));
  const offeneBeziehungen = beziehungen.filter((v) => !erledigt.has(beziehungSchluessel(v)));
  const gesamtGefunden = (verweise?.length ?? 0) + beziehungen.length;

  return (
    <Fenster
      offen={offen}
      titel="⧉✨ Auto-Verknüpfung"
      unterzeile="Erkennt erwähnte Personen/Orte/Events/Fraktionen und ihre Beziehungen"
      kennung={`auto-verknuepfung:${seitenId}`}
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {verweise === null && (
          <>
            <p className="ki-vorschau-hinweis">
              Durchsucht den Text dieser Seite nach Personen, Orten, Ereignissen und Fraktionen sowie
              konkreten Beziehungen zwischen ihnen (z.B. „arbeitet für"). Bekannte werden direkt verknüpft,
              unbekannte als Entwurf zur Prüfung angelegt.
            </p>
            {fehler && <p className="ki-fehler">{fehler}</p>}
            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" disabled={laedt} onClick={holen}>
                {laedt ? "Erkennt…" : "✨ Vorschläge holen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {verweise !== null && (
          <>
            {fehler && <p className="ki-fehler">{fehler}</p>}

            {offeneVerweise.length === 0 && offeneBeziehungen.length === 0 && (
              <p className="ki-vorschau-hinweis">
                {gesamtGefunden === 0 ? "Keine Erwähnungen oder Beziehungen gefunden." : "Alles verknüpft."}
              </p>
            )}

            {offeneVerweise.length > 0 && (
              <div className="av-gruppe">
                <h4 className="av-gruppentitel">Erwähnungen</h4>
                {offeneVerweise.map((v) => {
                  const key = verweisSchluessel(v);
                  const neu = v.zielId === null;
                  return (
                    <div key={key} className="av-vorschlag">
                      <div className="av-vorschlag-kopf">
                        <span className="av-icon">{TYP_ICON[v.typ] ?? "❔"}</span>
                        <span className="av-name">{v.name}</span>
                        <span className="av-typ">{v.typ}</span>
                        {neu && <span className="av-neu">neu</span>}
                      </div>
                      <div className="av-zitat">„{v.zitat}"</div>
                      <button
                        type="button"
                        className="ki-btn-primaer"
                        disabled={angewandt === key}
                        onClick={() => verweisAnwenden(v)}
                      >
                        {angewandt === key ? "…" : neu ? "+ Entwurf anlegen & verknüpfen" : "✓ Verknüpfen"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {offeneBeziehungen.length > 0 && (
              <div className="av-gruppe">
                <h4 className="av-gruppentitel">Beziehungen</h4>
                {offeneBeziehungen.map((v) => {
                  const key = beziehungSchluessel(v);
                  const neu1 = v.zielId1 === null;
                  const neu2 = v.zielId2 === null;
                  return (
                    <div key={key} className="av-vorschlag">
                      <div className="av-vorschlag-kopf">
                        <span className="av-icon">{TYP_ICON[v.typ1] ?? "❔"}</span>
                        <span className="av-name">
                          {v.name1}
                          {neu1 && <span className="av-neu">neu</span>}
                        </span>
                        <span className="av-beziehungspfeil">— {v.beziehungstyp} →</span>
                        <span className="av-icon">{TYP_ICON[v.typ2] ?? "❔"}</span>
                        <span className="av-name">
                          {v.name2}
                          {neu2 && <span className="av-neu">neu</span>}
                        </span>
                      </div>
                      {v.beschreibung && <div className="av-zitat">{v.beschreibung}</div>}
                      <button
                        type="button"
                        className="ki-btn-primaer"
                        disabled={angewandt === key}
                        onClick={() => beziehungAnwenden(v)}
                      >
                        {angewandt === key
                          ? "…"
                          : neu1 || neu2
                            ? "+ Entwurf/Beziehung anlegen"
                            : "✓ Beziehung anlegen"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-sekundaer" disabled={laedt} onClick={holen}>
                {laedt ? "Erkennt…" : "↺ Erneut prüfen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Schließen
              </button>
            </div>
          </>
        )}
      </div>
    </Fenster>
  );
}
