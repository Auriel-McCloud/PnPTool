import { useEffect, useState } from "react";
import { entitiesApi } from "../entities/api";
import type { Gegenstand } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { bogenApi, type Bogen } from "../traits/bogenApi";
import { WuerfelZehn } from "../traits/WuerfelZehn";
import { kampfApi, type Kampf, type Teilnehmer } from "./api";
import { InitiativeSetzen } from "./InitiativeSetzen";
import { Kampfkarte, wert } from "./Kampfkarte";
import "../begleiter/begleiter.css";
import "../items/gegenstaende.css";
import "./kampf.css";
import "./booster.css";
import "./kampfkarte.css";

/**
 * Der Beschwörungswert selbst — Spiegelbild von
 * backend/app/items/beschwoerung.py::beschwoerungsstufe. Zusammen mit der
 * Intelligenz des Beschwörers ergibt das den Würfelpool (siehe Popup unten).
 */
function beschwoerungswert(item: Gegenstand): number {
  const markiert = Object.entries(item.ausruestungsfertigkeiten)
    .filter(([name]) => item.kiTamaFertigkeiten[name])
    .map(([, w]) => w);
  return markiert.length ? Math.max(...markiert) : 0;
}

/**
 * Wie viele Erfolge eine Beschwörungs-Probe braucht — Spiegelbild von
 * backend/app/items/beschwoerung.py::benoetigte_erfolge, rein zur Anzeige
 * VOR dem Würfeln. Serverseitig wird exakt dasselbe erneut geprüft
 * (`kampf/routes.py::item_beschwoeren`) — hier entscheidet also nichts
 * sicherheitsrelevantes, nur die angezeigte Zielzahl.
 */
function benoetigteErfolge(item: Gegenstand): number {
  const stufe = beschwoerungswert(item);
  return Math.max(1, Math.ceil(stufe / 2) + (item.beschwoerungsSchwierigkeit || 0));
}

/**
 * Beschwörungs-Ki-Tama im Kampf (30.10.2026, Marks FF7-Idee direkt im
 * Anschluss ans Ki-Tama-Feature). Die Probe ist ein GATE vor der Initiative
 * — Mark wörtlich: "wir müssen bevor man die initiative eingibt noch die
 * probe im kampf menü einbauen". Nach bestandener Probe exakt dasselbe
 * Fenster + dieselbe Initiative-Eingabe wie bei den eigenen Drohnen
 * (`DeineDrohnenImKampf.tsx`) — Mark wollte das ausdrücklich wiederverwenden
 * statt etwas Neues zu bauen.
 */
export function DeineBeschwoerungen({
  campaignId,
  eigenePersonId,
  kampf,
  kiTamas,
  onGeaendert,
}: {
  campaignId: string;
  /** Der Beschwörer selbst — für seine Intelligenz, die in den Würfelpool
   *  der Probe eingeht (siehe Popup unten). */
  eigenePersonId: string;
  kampf: Kampf | null;
  /** Eigene Ki-Tama-Gegenstände mit `beschworenerCritterId` gesetzt. */
  kiTamas: Gegenstand[];
  onGeaendert: () => void;
}) {
  const [probeZiel, setProbeZiel] = useState<Gegenstand | null>(null);
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenId, setOffenId] = useState<string | null>(null);
  const [initiativeZiel, setInitiativeZiel] = useState<Teilnehmer | null>(null);
  // Nur für die Intelligenz gebraucht — kein Fach für Waffen/Items, deshalb
  // ein eigener, schlanker Ladevorgang statt den vollen Bogen hochzureichen.
  const [eigenerBogen, setEigenerBogen] = useState<Bogen | null>(null);
  // Critter-Bild für die Probe (30.10.2026, Mark: "wäre cool wenn du das
  // bild der beschwörung in dem fenster anzeigen würdest") — Critter sind
  // standardmäßig ALLE-sichtbar (siehe BegleiterVerwaltung.tsx), der
  // normale Spieler-lesbare Personen-Endpunkt reicht deshalb.
  const [critterBild, setCritterBild] = useState<string | null>(null);

  useEffect(() => {
    let weg = false;
    bogenApi
      .laden(campaignId, eigenePersonId)
      .then((b) => {
        if (!weg) setEigenerBogen(b);
      })
      .catch(() => {
        if (!weg) setEigenerBogen(null);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, eigenePersonId]);

  useEffect(() => {
    const critterId = probeZiel?.beschworenerCritterId;
    if (!critterId) {
      setCritterBild(null);
      return;
    }
    let weg = false;
    entitiesApi
      .getPerson(campaignId, critterId)
      .then((p) => {
        if (!weg) setCritterBild(p.bildUrl || null);
      })
      .catch(() => {
        if (!weg) setCritterBild(null);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, probeZiel?.beschworenerCritterId]);

  if (kiTamas.length === 0) return null;

  const intelligenz = eigenerBogen ? wert(eigenerBogen, "Intelligenz") : null;
  // Würfelpool der Probe — Intelligenz des Beschwörers + Beschwörungswert
  // des Ki-Tama, exakt wie bei jedem anderen Pool im Tool (Mark, 30.10.2026:
  // "die würfel anzahl anzeigen die der spieler hat", nicht nur die
  // Einzelzahlen nebeneinander ohne Summe).
  const wuerfelpool =
    intelligenz !== null && probeZiel ? intelligenz + beschwoerungswert(probeZiel) : null;

  /** Erfolgreiche Probe (Spieler hat selbst am Tisch genug gewürfelt) —
   *  schickt serverseitig exakt die benötigte Zahl, die Probe selbst läuft
   *  ja physisch am Tisch, keine Eingabe nötig (Mark, 30.10.2026: "eigentlich
   *  gibts keinen Grund die Nummer hier einzugeben, hier muss man nur
   *  Beschwören oder Fehlschlag anklicken können"). */
  async function beschwoeren() {
    if (!probeZiel) return;
    setSendet(true);
    setFehler(null);
    try {
      await kampfApi.beschwoeren(campaignId, probeZiel.id, benoetigteErfolge(probeZiel));
      const critterId = probeZiel.beschworenerCritterId;
      setProbeZiel(null);
      onGeaendert();
      // Direkt weiter zur Initiative, genau wie Mark es wollte — kein
      // zweiter Klick nötig, das Fenster zeigt gleich die Kampfwerte.
      if (critterId) setOffenId(critterId);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Beschwörung fehlgeschlagen");
    } finally {
      setSendet(false);
    }
  }

  /** Probe misslungen — nichts zu melden, der Critter bleibt draußen. */
  function fehlschlag() {
    setProbeZiel(null);
    setFehler(null);
  }

  return (
    <div className="ka-drohnen">
      <h3 className="gg-abschnitt">
        <span>🔮 Deine Beschwörungen</span>
      </h3>
      <div className="gg-slotboxen">
        {kiTamas.map((item) => {
          const critterId = item.beschworenerCritterId;
          const teilnahme = kampf?.teilnehmer.find((t) => t.personId === critterId);
          return (
            <div className="gg-slot-spalte" key={item.id}>
              <button
                type="button"
                className="gg-kachel"
                style={teilnahme ? { borderColor: "var(--ja)", boxShadow: "0 0 8px var(--ja)" } : undefined}
                onClick={() => (teilnahme && critterId ? setOffenId(critterId) : undefined)}
                disabled={!teilnahme}
              >
                <span className="gg-kachel-name">{item.name}</span>
                {teilnahme && (
                  <span className="kk-slot-kurz">
                    <em>Runden</em>
                    {teilnahme.rundenVerbleibend ?? "–"}
                  </span>
                )}
              </button>
              {!teilnahme && (
                <button type="button" onClick={() => setProbeZiel(item)} disabled={!kampf}>
                  Beschwören
                </button>
              )}
            </div>
          );
        })}
      </div>

      {probeZiel && (
        <Fenster
          offen
          titel={`Beschwörung: ${probeZiel.name}`}
          unterzeile="Probe vor der Beschwörung"
          kennung={`beschwoeren:${probeZiel.id}`}
          onSchliessen={() => setProbeZiel(null)}
        >
          {fehler && <p className="bo-warnung">{fehler}</p>}
          {critterBild && <img src={critterBild} alt={probeZiel.name} className="bo-critter-bild" />}
          <div className="bo-pool">
            <span className="bo-poolzahl">{benoetigteErfolge(probeZiel)}</span>
            <span className="bo-poolinfo">
              <span>Erfolge nötig</span>
              <em>
                Intelligenz {intelligenz ?? "…"} + Beschwörungswert {beschwoerungswert(probeZiel)}
              </em>
            </span>
            {wuerfelpool !== null && (
              <span className="kk-ziffer" title="Intelligenz + Beschwörungswert — so viele W10 würfeln">
                {wuerfelpool}
                <WuerfelZehn groesse={20} />
              </span>
            )}
          </div>
          <div className="bo-knoepfe">
            <button type="button" onClick={beschwoeren} disabled={sendet}>
              {sendet ? "…" : "Beschwören"}
            </button>
            <button type="button" className="bo-nein" onClick={fehlschlag} disabled={sendet}>
              Fehlschlag
            </button>
          </div>
        </Fenster>
      )}

      {offenId && (
        <Fenster
          offen
          titel="Beschworener Critter"
          unterzeile="Kampfwerte"
          kennung={`kampf-critter:${offenId}`}
          onSchliessen={() => setOffenId(null)}
        >
          <Kampfkarte
            campaignId={campaignId}
            personId={offenId}
            aenderbar
            onInitiativeKlick={(() => {
              const teilnahme = kampf?.teilnehmer.find((t) => t.personId === offenId);
              return teilnahme ? () => setInitiativeZiel(teilnahme) : undefined;
            })()}
          />
        </Fenster>
      )}

      {initiativeZiel && (
        <InitiativeSetzen
          teilnehmer={initiativeZiel}
          onSchliessen={() => setInitiativeZiel(null)}
          onSpeichern={async (initiativeWert) => {
            await kampfApi.meldeInitiative(campaignId, initiativeZiel.id, initiativeWert);
            onGeaendert();
          }}
        />
      )}
    </div>
  );
}
