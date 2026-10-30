import { useState } from "react";
import type { Gegenstand } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { kampfApi, type Kampf, type Teilnehmer } from "./api";
import { InitiativeSetzen } from "./InitiativeSetzen";
import { Kampfkarte } from "./Kampfkarte";
import "../items/gegenstaende.css";
import "./kampf.css";

/**
 * Wie viele Erfolge eine Beschwörungs-Probe braucht — Spiegelbild von
 * backend/app/items/beschwoerung.py (beschwoerungsstufe/benoetigte_erfolge),
 * rein zur Anzeige VOR dem Würfeln. Serverseitig wird exakt dasselbe erneut
 * geprüft (`kampf/routes.py::item_beschwoeren`) — hier entscheidet also
 * nichts sicherheitsrelevantes, nur die angezeigte Zielzahl.
 */
function benoetigteErfolge(item: Gegenstand): number {
  const markiert = Object.entries(item.ausruestungsfertigkeiten)
    .filter(([name]) => item.kiTamaFertigkeiten[name])
    .map(([, wert]) => wert);
  const stufe = markiert.length ? Math.max(...markiert) : 0;
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
  kampf,
  kiTamas,
  onGeaendert,
}: {
  campaignId: string;
  kampf: Kampf | null;
  /** Eigene Ki-Tama-Gegenstände mit `beschworenerCritterId` gesetzt. */
  kiTamas: Gegenstand[];
  onGeaendert: () => void;
}) {
  const [probeZiel, setProbeZiel] = useState<Gegenstand | null>(null);
  const [erfolgeWert, setErfolgeWert] = useState("");
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenId, setOffenId] = useState<string | null>(null);
  const [initiativeZiel, setInitiativeZiel] = useState<Teilnehmer | null>(null);

  if (kiTamas.length === 0) return null;

  async function beschwoeren() {
    if (!probeZiel) return;
    const zahl = Number(erfolgeWert);
    if (!Number.isInteger(zahl) || zahl < 0) {
      setFehler("Bitte eine ganze Zahl eingeben");
      return;
    }
    setSendet(true);
    setFehler(null);
    try {
      await kampfApi.beschwoeren(campaignId, probeZiel.id, zahl);
      const critterId = probeZiel.beschworenerCritterId;
      setProbeZiel(null);
      setErfolgeWert("");
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
          unterzeile={`Benötigt ${benoetigteErfolge(probeZiel)} Erfolge — Intelligenz + Beschwörungswert würfeln`}
          kennung={`beschwoeren:${probeZiel.id}`}
          onSchliessen={() => setProbeZiel(null)}
        >
          {fehler && <p className="bo-warnung">{fehler}</p>}
          <div className="bo-eingabe">
            <input
              type="number"
              min={0}
              inputMode="numeric"
              value={erfolgeWert}
              onChange={(e) => setErfolgeWert(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void beschwoeren();
              }}
              placeholder="Erzielte Erfolge"
              autoFocus
            />
          </div>
          <div className="bo-knoepfe">
            <button type="button" onClick={beschwoeren} disabled={sendet || erfolgeWert === ""}>
              {sendet ? "…" : "Beschwören"}
            </button>
            <button type="button" className="bo-nein" onClick={() => setProbeZiel(null)}>
              Abbrechen
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
          onSpeichern={async (wert) => {
            await kampfApi.meldeInitiative(campaignId, initiativeZiel.id, wert);
            onGeaendert();
          }}
        />
      )}
    </div>
  );
}
