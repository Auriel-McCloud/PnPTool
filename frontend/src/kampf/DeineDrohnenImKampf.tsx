import { useEffect, useState } from "react";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { Fenster } from "../shell/Fenster";
import { bogenApi } from "../traits/bogenApi";
import { kampfApi, type HotStatus, type Kampf, type Teilnehmer } from "./api";
import { InitiativeSetzen } from "./InitiativeSetzen";
import { Kampfkarte, kampfKurz } from "./Kampfkarte";
import "../items/gegenstaende.css";
import "./kampf.css";

/**
 * Eigene aktive Drohnen/Fahrzeuge im Kampfbereich (26.10.2026, Mark):
 * kleine Karten mit Name + Gesundheit. Ist die Drohne noch nicht Teilnehmer
 * des laufenden Kampfes, steht hier ein Self-Service-Knopf statt die SL zu
 * bitten — passt sich automatisch an, wie viele die Riggerkonsole gerade
 * aktiv verbunden hat (`drohnenApi.liste` liefert nur `riggerAktiv`).
 * Antippen öffnet den großen Steckbrief, auch wenn die Drohne Hot ist und
 * deshalb keine eigene Zeile in der Initiativliste mehr hat.
 */
export function DeineDrohnenImKampf({
  campaignId,
  eigenePersonId,
  kampf,
  onGeaendert,
  onListeGeladen,
}: {
  campaignId: string;
  eigenePersonId: string;
  kampf: Kampf | null;
  onGeaendert: () => void;
  /** Meldet die IDs der eigenen aktiven Drohnen/Fahrzeuge nach oben — damit
   *  die Initiativliste weiß, wessen Zahl der Rigger anklicken darf. */
  onListeGeladen?: (ids: string[]) => void;
}) {
  const [drohnen, setDrohnen] = useState<DrohnenEintrag[]>([]);
  const [slotsMax, setSlotsMax] = useState(0);
  const [gesundheit, setGesundheit] = useState<Record<string, ReturnType<typeof kampfKurz>>>({});
  const [offenId, setOffenId] = useState<string | null>(null);
  const [beitretend, setBeitretend] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  // Initiative direkt aus dem Drohnen-Steckbrief setzbar (Mark, 26.10.2026) —
  // nicht nur über die Zeile in der Initiativliste außerhalb des Popups.
  const [initiativeZiel, setInitiativeZiel] = useState<Teilnehmer | null>(null);
  const [hot, setHot] = useState<HotStatus | null>(null);
  const [hotSendet, setHotSendet] = useState<string | null>(null);

  useEffect(() => {
    let weg = false;
    drohnenApi
      .liste(campaignId)
      .then((liste) => {
        if (weg) return;
        const eigene = liste.filter((d) => d.riggerId === eigenePersonId);
        const aktiv = eigene.filter((d) => d.riggerAktiv);
        setDrohnen(aktiv);
        onListeGeladen?.(aktiv.map((d) => d.id));
        const slots = eigene.find((d) => d.riggerSlotsMax != null)?.riggerSlotsMax ?? 0;
        setSlotsMax(slots);
      })
      .catch(() => {
        if (!weg) setDrohnen([]);
      });
    return () => {
      weg = true;
    };
    // kampf?.amZug damit der Magenta-Rahmen nach dem Hot-Knopf nachzieht.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, eigenePersonId, kampf?.teilnehmer.length, kampf?.amZug, kampf?.runde]);

  useEffect(() => {
    let weg = false;
    kampfApi
      .hotStatus(campaignId)
      .then((s) => {
        if (!weg) setHot(s);
      })
      .catch(() => {
        if (!weg) setHot(null);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, kampf?.runde, kampf?.amZug, drohnen]);

  useEffect(() => {
    let weg = false;
    Promise.all(
      drohnen.map(async (d) => {
        try {
          const b = await bogenApi.laden(campaignId, d.id);
          return [d.id, kampfKurz(b)] as const;
        } catch {
          return [d.id, []] as const;
        }
      }),
    ).then((paare) => {
      if (!weg) setGesundheit(Object.fromEntries(paare));
    });
    return () => {
      weg = true;
    };
  }, [campaignId, drohnen]);

  if (drohnen.length === 0 && slotsMax === 0) return null;

  async function hotGehen(drohneId: string) {
    setHotSendet(drohneId);
    setFehler(null);
    try {
      setHot(await kampfApi.hotDrohne(campaignId, drohneId));
      setDrohnen((bisher) => bisher.map((d) => ({ ...d, istHot: d.id === drohneId })));
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Hot gerade nicht möglich.");
    } finally {
      setHotSendet(null);
    }
  }

  const kaesten = Math.max(slotsMax, drohnen.length);

  async function beitreten(drohneId: string) {
    setBeitretend(drohneId);
    setFehler(null);
    try {
      await kampfApi.drohneBeitreten(campaignId, drohneId);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht beitreten");
    } finally {
      setBeitretend(null);
    }
  }

  return (
    <div className="ka-drohnen">
      <h3 className="gg-abschnitt">
        <span>⛭ Deine Drohnen</span>
      </h3>
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      <div className="gg-slotboxen">
        {Array.from({ length: kaesten }).map((_, i) => {
          const d = drohnen[i];
          if (!d) {
            return (
              <div className="gg-slotbox-leer" key={i}>
                frei
              </div>
            );
          }
          const teilnahme = kampf?.teilnehmer.find((t) => t.personId === d.id);
          return (
            <div className="gg-slot-spalte" key={d.id}>
              <button
                type="button"
                className={`gg-kachel${d.istHot ? " gg-slot-hot" : ""}`}
                style={d.istHot ? undefined : { borderColor: "var(--ja)", boxShadow: "0 0 8px var(--ja)" }}
                onClick={() => setOffenId(d.id)}
              >
                <span className="gg-kachel-name">{d.name}</span>
                <span className="kk-slot-kurz">
                  {(gesundheit[d.id] ?? []).map((k) => (
                    <span key={k.kuerzel} title={k.titel}>
                      <em>{k.kuerzel}</em>
                      {k.wert}
                    </span>
                  ))}
                  {!gesundheit[d.id] && <span>…</span>}
                </span>
              </button>
              {hot?.hatNeurolink && (
                <button
                  type="button"
                  className="gg-hot-knopf"
                  disabled={d.istHot || hot.darfWaehlen === false || hotSendet === d.id}
                  onClick={() => hotGehen(d.id)}
                >
                  Hot
                </button>
              )}
              {!teilnahme && (
                <button type="button" onClick={() => beitreten(d.id)} disabled={beitretend === d.id || !kampf}>
                  {beitretend === d.id ? "…" : "Dem Kampf beitreten"}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {offenId && (
        <Fenster
          offen
          titel={drohnen.find((d) => d.id === offenId)?.name ?? "Drohne"}
          unterzeile="Kampfwerte"
          kennung={`kampf-drohne:${offenId}`}
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
