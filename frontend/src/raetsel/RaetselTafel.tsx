import { useEffect, useRef, useState } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { useNachladen } from "../shell/nachladen";
import {
  hatTafel,
  raetselApi,
  verbindeRaetselLive,
  type Modus,
  type RaetselAntwort,
  type RaetselTafel,
  type Seite,
} from "./api";
import "./raetsel.css";

const SEITEN: Seite[] = ["N", "O", "S", "W"];
const SEITEN_NAME: Record<Seite, string> = { N: "Nord", O: "Ost", S: "Süd", W: "West" };
const MODUS_NAME: Record<Modus, string> = { leicht: "Leicht", mittel: "Mittel" };

/** Gleiche Zuordnung wie backend/app/raetsel/logic.py — Feld 0 ist Nord. */
const FELDER = [
  { slot: 7, area: "1 / 1" },
  { slot: 0, area: "1 / 2" },
  { slot: 1, area: "1 / 3" },
  { slot: 6, area: "2 / 1" },
  { slot: 2, area: "2 / 3" },
  { slot: 5, area: "3 / 1" },
  { slot: 4, area: "3 / 2" },
  { slot: 3, area: "3 / 3" },
];

const MITTE: Record<number, Seite[]> = {
  0: ["S"],
  1: ["S", "W"],
  2: ["W"],
  3: ["W", "N"],
  4: ["N"],
  5: ["N", "O"],
  6: ["O"],
  7: ["O", "S"],
};

const EBENEN_NAME = ["Ebene oben", "Ebene unten"];

/**
 * Tafel für einen oder zwei Ringe. Die SL klickt Türen und Räume, Spieler
 * sehen dieselbe Tafel ohne Knöpfe, sobald sie freigegeben ist.
 */
export function RaetselTafelAnsicht({
  campaignId,
  istGm,
}: {
  campaignId: string;
  istGm: boolean;
}) {
  const [stand, setStand] = useState<RaetselAntwort | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [gewaehlt, setGewaehlt] = useState(0);
  const [umbenennen, setUmbenennen] = useState<{ raum: number; name: string } | null>(null);
  const [resetOffen, setResetOffen] = useState(false);
  const [modusWechsel, setModusWechsel] = useState<Modus | null>(null);
  const { ungueltig } = useNachladen(
    () => raetselApi.laden(campaignId, istGm),
    (daten) => setStand(daten),
    { quelle: campaignId },
  );
  const ungueltigRef = useRef(ungueltig);
  ungueltigRef.current = ungueltig;

  useEffect(() => {
    const leitung = verbindeRaetselLive(campaignId, (daten) => {
      ungueltigRef.current();
      setStand(daten);
    });
    return () => leitung.trennen();
  }, [campaignId]);

  async function senden(aktion: () => Promise<RaetselTafel>) {
    if (busy) return;
    setBusy(true);
    setFehler(null);
    try {
      const neu = await aktion();
      ungueltig();
      setStand(neu);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Das hat nicht geklappt.");
    } finally {
      setBusy(false);
    }
  }

  if (!stand) {
    return <p className="rr-gesperrt">Lade Rätsel…</p>;
  }
  if (!istGm && !hatTafel(stand)) {
    return (
      <div className="rr">
        <p className="rr-gesperrt">Die SL hat das Rätsel noch nicht freigegeben.</p>
      </div>
    );
  }
  if (!hatTafel(stand)) {
    return <p className="rr-gesperrt">Rätsel nicht erreichbar.</p>;
  }

  const tafel = stand;
  const zweiEbenen = tafel.ringe.length === 2;
  const naechsteOffene = tafel.offen.findIndex(Boolean);
  const klickSetzt = naechsteOffene >= 0 ? naechsteOffene : gewaehlt;
  const gegenueber = !zweiEbenen && tafel.drehung % 8 === 4;

  return (
    <div className="rr">
      <div className="rr-kopf">
        <h2 className="rr-titel">Rätsel</h2>
        <p className="rr-schritt">
          {zweiEbenen ? (
            <>
              Takt {tafel.takt} · nächste Tür: {tafel.naechster === "ebene" ? "Ebene wechseln" : "drehen"}
            </>
          ) : (
            <>
              Schritt {tafel.drehung}
              {gegenueber ? " — gegenüber dem Startfeld" : ""}
            </>
          )}
          {tafel.tuer
            ? ` · offen: ${tafel.namen[tafel.tuer.raum]} ${SEITEN_NAME[tafel.tuer.seite]}`
            : ""}
        </p>
      </div>

      {istGm && (
        <>
          <p className="rr-hinweis">
            {zweiEbenen
              ? "Tür zu wechselt abwechselnd die Ebene (gleiches Feld) oder dreht beide Ringe gegen den Uhrzeigersinn. Danach den Raum klicken, in dem sie sind."
              : "Tür klicken dreht alle acht Räume gegen den Uhrzeigersinn. Danach den Raum klicken, in dem sie sind. Eine offene Tür heißt nicht, dass sie durch sind."}
          </p>
          {(naechsteOffene >= 0 || tafel.gruppen[0] == null) && (
            <p className="rr-banner">
              Wo sind sie? Nächster Klick setzt Gruppe {klickSetzt === 0 ? "A" : "B"}.
            </p>
          )}
          <div className="rr-werkzeuge">
            <button
              type="button"
              data-aktiv={tafel.freigegeben ? "true" : "false"}
              disabled={busy}
              onClick={() => senden(() => raetselApi.freigabe(campaignId, !tafel.freigegeben))}
            >
              {tafel.freigegeben ? "Spieler sehen mit" : "Für Spieler freigeben"}
            </button>
            <button
              type="button"
              disabled={busy || !tafel.kannZurueck}
              onClick={() => senden(() => raetselApi.zurueck(campaignId))}
            >
              Zurück
            </button>
            <button type="button" disabled={busy} onClick={() => setResetOffen(true)}>
              Auf Start
            </button>
          </div>
          <div className="rr-werkzeuge">
            {(["leicht", "mittel"] as Modus[]).map((modus) => (
              <button
                key={modus}
                type="button"
                data-aktiv={tafel.modus === modus ? "true" : "false"}
                disabled={busy}
                onClick={() => tafel.modus !== modus && setModusWechsel(modus)}
              >
                {MODUS_NAME[modus]}
              </button>
            ))}
          </div>
          <div className="rr-gruppen">
            <button
              type="button"
              data-aktiv={klickSetzt === 0 ? "true" : "false"}
              onClick={() => setGewaehlt(0)}
            >
              Gruppe A
            </button>
            <button
              type="button"
              data-aktiv={klickSetzt === 1 ? "true" : "false"}
              onClick={() => setGewaehlt(1)}
            >
              Gruppe B
            </button>
            {tafel.gruppen[1] != null && (
              <button
                type="button"
                disabled={busy}
                onClick={() => senden(() => raetselApi.gruppe(campaignId, 1, null))}
              >
                B weg
              </button>
            )}
          </div>
        </>
      )}

      {fehler && <p className="rr-fehler">{fehler}</p>}

      <div className="rr-bretter">
        {tafel.ringe.map((ring, ringIndex) => (
          <div className="rr-brett-block" key={ringIndex}>
            {zweiEbenen && <p className="rr-ebene-label">{EBENEN_NAME[ringIndex]}</p>}
            <div className="rr-brett">
              <span className="rr-kompass rr-kompass-n">N</span>
              <span className="rr-kompass rr-kompass-o">O</span>
              <span className="rr-kompass rr-kompass-s">S</span>
              <span className="rr-kompass rr-kompass-w">W</span>
              <div className="rr-ring">
                {FELDER.map(({ slot, area }) => (
                  <RaumZelle
                    key={slot}
                    area={area}
                    raum={ring[slot]}
                    feldNummer={zweiEbenen ? (ringIndex === 1 ? 0 : 8) + slot + 1 : slot + 1}
                    tafel={tafel}
                    slot={slot}
                    istGm={istGm}
                    busy={busy}
                    onTuer={(raum, seite) => senden(() => raetselApi.tuer(campaignId, raum, seite))}
                    onRaum={(raum) => senden(() => raetselApi.gruppe(campaignId, klickSetzt, raum))}
                    onUmbenennen={(raum) => setUmbenennen({ raum, name: tafel.namen[raum] })}
                  />
                ))}
                <div className="rr-ziel" style={{ gridArea: "2 / 2" }}>
                  <strong>Ziel</strong>
                  {istGm ? (
                    <AusgangMini
                      werte={tafel.ausgaenge[ringIndex]}
                      busy={busy}
                      onWaehlen={(slot) =>
                        senden(() => raetselApi.ausgang(campaignId, ringIndex, slot))
                      }
                    />
                  ) : (
                    <span>Tür nach innen</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="rr-legende">
        Leuchtende Tür: zuletzt zu. Gestrichelter Rahmen: Lage noch nicht bestätigt.
        {istGm &&
          " Neonkante: diese Tür zeigt zur Mitte, nur für dich sichtbar. Punkte in der Mitte: freie Markierung (aus/blau/rot), reine Notiz ohne eigene Logik. Spieler sehen beides nicht."}
      </p>

      {istGm && umbenennen && (
        <Fenster
          offen
          kennung="raetsel-name"
          titel={`Name: ${umbenennen.name || String(umbenennen.raum + 1)}`}
          onSchliessen={() => setUmbenennen(null)}
        >
          <form
            className="rr-name-fenster"
            onSubmit={(e) => {
              e.preventDefault();
              const { raum, name } = umbenennen;
              setUmbenennen(null);
              void senden(() => raetselApi.name(campaignId, raum, name));
            }}
          >
            <input
              value={umbenennen.name}
              maxLength={16}
              autoFocus
              onChange={(e) => setUmbenennen({ ...umbenennen, name: e.target.value })}
            />
            <button type="submit" disabled={busy}>
              Speichern
            </button>
          </form>
        </Fenster>
      )}

      {resetOffen && (
        <Bestaetigung
          titel="Auf Start zurück?"
          text="Bist du sicher? Die Räume springen auf die Startfelder zurück. Namen und Ausgänge bleiben."
          jaText="Zurücksetzen"
          onNein={() => setResetOffen(false)}
          onJa={() => {
            setResetOffen(false);
            void senden(() => raetselApi.zuruecksetzen(campaignId));
          }}
        />
      )}

      {modusWechsel && (
        <Bestaetigung
          titel={`Auf ${MODUS_NAME[modusWechsel]} umschalten?`}
          text="Bist du sicher? Die Räume springen auf die Startfelder zurück. Namen, Freigabe und Ausgänge bleiben."
          jaText="Umschalten"
          onNein={() => setModusWechsel(null)}
          onJa={() => {
            const ziel = modusWechsel;
            setModusWechsel(null);
            void senden(() => raetselApi.modus(campaignId, ziel));
          }}
        />
      )}
    </div>
  );
}

function AusgangMini({
  werte,
  busy,
  onWaehlen,
}: {
  werte: number[];
  busy: boolean;
  onWaehlen: (slot: number) => void;
}) {
  return (
    <div className="rr-ausgang-mini" title="Freie Markierung für dich, aus/blau/rot">
      {FELDER.map(({ slot, area }) => (
        <button
          key={slot}
          type="button"
          className="rr-ausgang-dot"
          style={{ gridArea: area }}
          data-status={werte[slot] ?? 0}
          disabled={busy}
          aria-label={`Markierung an Feld ${slot + 1}, Klick schaltet weiter`}
          onClick={() => onWaehlen(slot)}
        />
      ))}
    </div>
  );
}

function RaumZelle({
  area,
  raum,
  slot,
  feldNummer,
  tafel,
  istGm,
  busy,
  onTuer,
  onRaum,
  onUmbenennen,
}: {
  area: string;
  raum: number;
  slot: number;
  feldNummer: number;
  tafel: RaetselTafel;
  istGm: boolean;
  busy: boolean;
  onTuer: (raum: number, seite: Seite) => void;
  onRaum: (raum: number) => void;
  onUmbenennen: (raum: number) => void;
}) {
  const mitte = MITTE[slot];
  const marker = tafel.gruppen
    .map((gruppe, index) => (gruppe === raum ? (index === 0 ? "A" : "B") : null))
    .filter(Boolean)
    .join(" ");
  const unbestaetigt = tafel.gruppen.some(
    (gruppe, index) => gruppe === raum && tafel.offen[index],
  );
  const standardname = tafel.namen[raum] === String(raum + 1);
  const anzeigename = standardname ? `${raum + 1}-${feldNummer}` : tafel.namen[raum];
  const kern = (
    <>
      <span className="rr-name">{anzeigename}</span>
      {marker && <span className="rr-marker">{marker}</span>}
    </>
  );

  return (
    <div className="rr-zelle" style={{ gridArea: area }}>
      {SEITEN.map((seite) => {
        const auf = tafel.tuer?.raum === raum && tafel.tuer.seite === seite;
        const zeigtMitte = istGm && mitte.includes(seite);
        const label = SEITEN_NAME[seite];
        const klasse = `rr-tuer rr-tuer-${seite.toLowerCase()}`;
        if (!istGm) {
          return (
            <div key={seite} className={klasse} data-auf={auf ? "true" : "false"} title={label}>
              {seite}
            </div>
          );
        }
        return (
          <button
            key={seite}
            type="button"
            className={klasse}
            data-auf={auf ? "true" : "false"}
            data-mitte={zeigtMitte ? "true" : "false"}
            disabled={busy}
            title={zeigtMitte ? `${label} zu, zeigt zur Mitte` : `${label} zu`}
            onClick={() => onTuer(raum, seite)}
          >
            {seite}
          </button>
        );
      })}
      {istGm ? (
        <button
          type="button"
          className="rr-kern"
          data-offen={unbestaetigt ? "true" : "false"}
          disabled={busy}
          onClick={() => onRaum(raum)}
        >
          {kern}
        </button>
      ) : (
        <div className="rr-kern" data-offen={unbestaetigt ? "true" : "false"}>
          {kern}
        </div>
      )}
      {istGm && (
        <button
          type="button"
          className="rr-umbenennen"
          title="Namen ändern"
          aria-label={`Namen von ${anzeigename} ändern`}
          onClick={() => onUmbenennen(raum)}
        >
          ✎
        </button>
      )}
    </div>
  );
}
