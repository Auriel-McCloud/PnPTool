import { useEffect, useState } from "react";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { Fenster } from "../shell/Fenster";
import { bogenApi } from "../traits/bogenApi";
import { kampfApi, type Kampf, type Teilnehmer } from "./api";
import { InitiativeSetzen } from "./InitiativeSetzen";
import { Kampfkarte } from "./Kampfkarte";
import "./kampf.css";

/**
 * Eigene aktive Drohnen/Fahrzeuge im Kampfbereich (26.10.2026, Mark):
 * kleine Karten mit Name + Gesundheit. Ist die Drohne noch nicht Teilnehmer
 * des laufenden Kampfes, steht hier ein Self-Service-Knopf statt die SL zu
 * bitten — passt sich automatisch an, wie viele die Riggerkonsole gerade
 * aktiv verbunden hat (`drohnenApi.liste` liefert nur `riggerAktiv`).
 * Antippen einer schon teilnehmenden Drohne öffnet ihren Steckbrief
 * (Kampfkarte, kompaktStart — Gesundheit/TN/TS/A/P/I in Kurzform, Klick
 * klappt die ausgeschriebene Fassung auf).
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
  const [gesundheit, setGesundheit] = useState<Record<string, string>>({});
  const [offenId, setOffenId] = useState<string | null>(null);
  const [beitretend, setBeitretend] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  // Initiative direkt aus dem Drohnen-Steckbrief setzbar (Mark, 26.10.2026) —
  // nicht nur über die Zeile in der Initiativliste außerhalb des Popups.
  const [initiativeZiel, setInitiativeZiel] = useState<Teilnehmer | null>(null);

  useEffect(() => {
    let weg = false;
    drohnenApi
      .liste(campaignId)
      .then((liste) => {
        if (weg) return;
        const eigene = liste.filter((d) => d.riggerId === eigenePersonId && d.riggerAktiv);
        setDrohnen(eigene);
        onListeGeladen?.(eigene.map((d) => d.id));
      })
      .catch(() => {
        if (!weg) setDrohnen([]);
      });
    return () => {
      weg = true;
    };
    // kampf?.teilnehmer.length als Signal zum Nachladen (beigetreten/entfernt).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, eigenePersonId, kampf?.teilnehmer.length]);

  useEffect(() => {
    let weg = false;
    Promise.all(
      drohnen.map(async (d) => {
        try {
          const b = await bogenApi.laden(campaignId, d.id);
          const u = b.uebersicht;
          const uebrig = u.gesundheitMax - u.schadenSchlag - u.schadenSchwer - u.schadenAggraviert;
          return [d.id, `${uebrig}/${u.gesundheitMax}`] as const;
        } catch {
          return [d.id, "?"] as const;
        }
      }),
    ).then((paare) => {
      if (!weg) setGesundheit(Object.fromEntries(paare));
    });
    return () => {
      weg = true;
    };
  }, [campaignId, drohnen]);

  if (drohnen.length === 0) return null;

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
      <div className="ka-drohnen-raster">
        {drohnen.map((d) => {
          const teilnahme = kampf?.teilnehmer.find((t) => t.personId === d.id);
          return (
            <div key={d.id} className="ka-drohnen-karte" data-dabei={Boolean(teilnahme)}>
              {teilnahme ? (
                <button type="button" onClick={() => setOffenId(d.id)}>
                  <span className="ka-drohnen-name">{teilnahme.name}</span>
                  <span className="ka-drohnen-gs">{gesundheit[d.id] ?? "…"}</span>
                </button>
              ) : (
                <>
                  <span className="ka-drohnen-name">{d.name}</span>
                  <button type="button" onClick={() => beitreten(d.id)} disabled={beitretend === d.id || !kampf}>
                    {beitretend === d.id ? "…" : "Dem Kampf beitreten"}
                  </button>
                </>
              )}
            </div>
          );
        })}
      </div>

      {offenId && (
        <Fenster
          offen
          titel={kampf?.teilnehmer.find((t) => t.personId === offenId)?.name ?? ""}
          unterzeile="Kampfwerte"
          kennung={`kampf-drohne:${offenId}`}
          onSchliessen={() => setOffenId(null)}
        >
          {(() => {
            const teilnahme = kampf?.teilnehmer.find((t) => t.personId === offenId);
            return (
              <>
                {teilnahme && (
                  <button
                    type="button"
                    className="kk-ganzer"
                    style={{ marginBottom: 10 }}
                    onClick={() => setInitiativeZiel(teilnahme)}
                  >
                    Initiative setzen ({teilnahme.initiative})
                  </button>
                )}
                <Kampfkarte campaignId={campaignId} personId={offenId} kompaktStart />
              </>
            );
          })()}
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
