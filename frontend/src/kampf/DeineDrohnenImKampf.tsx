import { useEffect, useState } from "react";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { Fenster } from "../shell/Fenster";
import { bogenApi } from "../traits/bogenApi";
import { kampfApi, type HotStatus, type Kampf, type Teilnehmer } from "./api";
import { InitiativeSetzen, initiativePlatzhalter } from "./InitiativeSetzen";
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
    async function hol() {
      if (document.hidden) return;
      try {
        const liste = await drohnenApi.liste(campaignId);
        if (weg) return;
        const eigene = liste.filter((d) => d.riggerId === eigenePersonId);
        const aktiv = eigene.filter((d) => d.riggerAktiv);
        setDrohnen(aktiv);
        onListeGeladen?.(aktiv.map((d) => d.id));
        setSlotsMax(eigene.find((d) => d.riggerSlotsMax != null)?.riggerSlotsMax ?? 0);
      } catch {
        if (!weg) setDrohnen([]);
      }
    }
    void hol();
    const uhr = window.setInterval(() => void hol(), 3000);
    return () => {
      weg = true;
      window.clearInterval(uhr);
    };
    // kampf-Takt stößt sofort an, der Intervall fängt das Aus der Konsole.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, eigenePersonId, kampf?.teilnehmer.length, kampf?.amZug, kampf?.runde]);

  useEffect(() => {
    let weg = false;
    kampfApi
      .hotStatus(campaignId, eigenePersonId)
      .then((s) => {
        if (!weg) setHot(s);
      })
      .catch(() => {
        if (!weg) setHot(null);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, eigenePersonId, kampf?.runde, kampf?.amZug, drohnen]);

  // Gesundheit wird separat vom Bogen geladen, nicht aus `kampf` — der
  // Kampf-Takt (useKampf, alle 3s) weiß nichts von Schaden. Ohne eigenen
  // Takt blieb die Anzeige hier stehen, bis sich die Drohnenliste selbst
  // änderte (neue Runde/neuer Zug), und Mark musste manuell neu laden,
  // nachdem er einer Drohne Schaden gegeben hatte (29.10.2026).
  useEffect(() => {
    if (drohnen.length === 0) return;
    let weg = false;
    async function ladenGesundheit() {
      if (document.hidden) return;
      const paare = await Promise.all(
        drohnen.map(async (d) => {
          try {
            const b = await bogenApi.laden(campaignId, d.id);
            return [d.id, kampfKurz(b)] as const;
          } catch {
            return [d.id, []] as const;
          }
        }),
      );
      if (!weg) setGesundheit(Object.fromEntries(paare));
    }
    void ladenGesundheit();
    const uhr = setInterval(ladenGesundheit, 3000);
    document.addEventListener("visibilitychange", ladenGesundheit);
    return () => {
      weg = true;
      clearInterval(uhr);
      document.removeEventListener("visibilitychange", ladenGesundheit);
    };
  }, [campaignId, drohnen]);

  if (drohnen.length === 0 && slotsMax === 0) return null;

  async function hotGehen(drohneId: string) {
    setHotSendet(drohneId);
    setFehler(null);
    try {
      setHot(await kampfApi.hotDrohne(campaignId, drohneId, eigenePersonId));
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
              <div
                className={`gg-kachel${d.istHot ? " gg-slot-hot" : ""}`}
                style={d.istHot ? undefined : { borderColor: "var(--ja)", boxShadow: "0 0 8px var(--ja)" }}
                role="button"
                tabIndex={0}
                onClick={() => setOffenId(d.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") setOffenId(d.id);
                }}
              >
                <span className="gg-kachel-name">{d.name}</span>
                <span className="kk-slot-kurz">
                  {(gesundheit[d.id] ?? []).map((k) =>
                    k.kuerzel === "I" ? (
                      <button
                        key={k.kuerzel}
                        type="button"
                        className="kk-init-tipp"
                        title="Initiative eintragen"
                        onClick={(e) => {
                          e.stopPropagation();
                          setInitiativeZiel(teilnahme ?? initiativePlatzhalter(d.name, d.id, Number(k.wert) || 0));
                        }}
                      >
                        <em>{k.kuerzel}</em>
                        {k.wert}
                      </button>
                    ) : (
                      <span key={k.kuerzel} title={k.titel}>
                        <em>{k.kuerzel}</em>
                        {k.wert}
                      </span>
                    ),
                  )}
                  {!gesundheit[d.id] && <span>…</span>}
                </span>
              </div>
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
              {!teilnahme && !d.istHot && hot?.hotDrohneId !== d.id && (
                <button
                  type="button"
                  title="Nimmt diese Drohne in die Initiative auf, wenn sie selbstständig kämpft — nicht nötig, solange du Hot in ihr bist."
                  onClick={() => beitreten(d.id)}
                  disabled={beitretend === d.id || !kampf}
                >
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
            onInitiativeKlick={() => {
              const dabei = kampf?.teilnehmer.find((t) => t.personId === offenId);
              const name = drohnen.find((d) => d.id === offenId)?.name ?? "Drohne";
              setInitiativeZiel(dabei ?? initiativePlatzhalter(name, offenId));
            }}
          />
        </Fenster>
      )}

      {initiativeZiel && (
        <InitiativeSetzen
          teilnehmer={initiativeZiel}
          onSchliessen={() => setInitiativeZiel(null)}
          onSpeichern={async (wert) => {
            if (initiativeZiel.id) {
              await kampfApi.meldeInitiative(campaignId, initiativeZiel.id, wert);
            } else if (initiativeZiel.personId) {
              const aufgenommen = await kampfApi.drohneBeitreten(campaignId, initiativeZiel.personId);
              const dabei = aufgenommen.teilnehmer.find(
                (t) => t.personId === initiativeZiel.personId && !t.zusatzzug,
              );
              if (!dabei) throw new Error("Drohne nicht im Kampf");
              await kampfApi.meldeInitiative(campaignId, dabei.id, wert);
            }
            onGeaendert();
          }}
        />
      )}
    </div>
  );
}
