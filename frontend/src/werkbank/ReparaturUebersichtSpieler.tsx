import { useState } from "react";
import { type Gegenstand } from "../items/api";
import { type DrohnenEintrag } from "../drohnen/api";
import { type ReparaturFreigabeEintrag } from "../party/api";
import { ReparaturFenster, type ReparaturZiel } from "../reparatur/ReparaturFenster";
import "../items/gegenstaende.css";
import "./werkbank.css";

/** Eine Gruppe reparierbarer Gegenstände einer Person — die eigene
 * Ausrüstung, oder (05.11.2026, Party-Reparatur-Freigabe) die eines
 * Party-Mitglieds, das dem Fixer Zugriff erteilt hat. */
export interface ReparaturGruppe {
  label: string;
  personId: string;
  items: Gegenstand[];
}

/**
 * Werkbank-Reparatur für Spieler (29.10.2026, Mark: "das war alles für die
 * Spieler gedacht!" — Korrektur, war vorher `require_campaign_gm`).
 * Gegenstück zu `reparatur/ReparaturUebersicht.tsx` (SL-Ansicht,
 * campaignweit) — hier nur die eigene Rüstung + eigene gebundene Drohnen/
 * Fahrzeuge, Vorauswahl übernimmt `SpielerAnsicht.tsx`. Kein Händler-Reiter
 * (`ReparaturFenster erlaubeHaendler={false}`) — der Weg läuft über eine
 * SL-initiierte Verhandlung, nicht über Spieler-Self-Service.
 */
export function ReparaturUebersichtSpieler({
  campaignId,
  reparaturgruppen,
  drohnen,
  onGeaendert,
  inEigenerParty,
  partyAnfragbar,
  anfrageLaeuft,
  onFreigabeAnfragen,
  erteilteFreigaben,
  onFreigabeWiderrufen,
}: {
  campaignId: string;
  reparaturgruppen: ReparaturGruppe[];
  drohnen: DrohnenEintrag[];
  onGeaendert: () => void;
  /** Ist der Spieler gerade überhaupt Mitglied einer Party? Steuert, welchen
   * Leer-Hinweis der Freigaben-Abschnitt zeigt (05.11.2026). */
  inEigenerParty: boolean;
  partyAnfragbar: { id: string; name: string }[];
  anfrageLaeuft: Set<string>;
  onFreigabeAnfragen: (zielPersonId: string) => void;
  erteilteFreigaben: ReparaturFreigabeEintrag[];
  onFreigabeWiderrufen: (fixerPersonId: string) => void;
}) {
  const [offenesZiel, setOffenesZiel] = useState<ReparaturZiel | null>(null);
  const gesamtRuestung = reparaturgruppen.reduce((n, g) => n + g.items.length, 0);

  return (
    <div className="gg-seite">
      {gesamtRuestung === 0 && drohnen.length === 0 && (
        <p className="gg-leer">Keine reparierbare Ausrüstung oder Drohne/Fahrzeug im Zugriff.</p>
      )}

      {reparaturgruppen.map(
        (gruppe) =>
          gruppe.items.length > 0 && (
            <div key={gruppe.personId}>
              <p className="lu-hinweis">
                {gruppe.label} ({gruppe.items.length})
              </p>
              <div className="wb-kachelraster">
                {gruppe.items.map((g) => (
                  <button
                    key={g.id}
                    type="button"
                    className="gg-kachel"
                    onClick={() =>
                      setOffenesZiel({
                        typ: "ruestung",
                        id: g.id,
                        name: g.name,
                        besitzerId: gruppe.personId,
                        ruestungKaestchenAktuell: g.ruestungKaestchenAktuell,
                        ruestungKaestchenMax: g.ruestungKaestchenMax,
                      })
                    }
                  >
                    <span className="gg-kachel-bild">
                      {g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🛡</span>}
                    </span>
                    <span className="gg-kachel-name">{g.name}</span>
                    <span className="gg-kachel-zeile">
                      <span style={g.ruestungKaestchenAktuell < g.ruestungKaestchenMax ? { color: "var(--nein)" } : undefined}>
                        {g.ruestungKaestchenAktuell}/{g.ruestungKaestchenMax} Kästchen
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ),
      )}


      {drohnen.length > 0 && (
        <>
          <p className="lu-hinweis">Drohnen &amp; Fahrzeuge ({drohnen.length})</p>
          <div className="wb-kachelraster">
            {drohnen.map((d) => (
              <button
                key={d.id}
                type="button"
                className="gg-kachel"
                onClick={() =>
                  setOffenesZiel({
                    typ: d.istFahrzeug ? "fahrzeug" : "drohne",
                    id: d.id,
                    name: d.name,
                    gesundheitAktuell: d.gesundheitAktuell,
                    gesundheitMax: d.gesundheitMax,
                    aussenhuelleAktuell: d.aussenhuelleAktuell,
                    aussenhuelleMax: d.aussenhuelleMax,
                  })
                }
              >
                <span className="gg-kachel-bild">
                  {d.bildUrl ? <img src={d.bildUrl} alt="" /> : <span aria-hidden="true">⛭</span>}
                </span>
                <span className="gg-kachel-name">{d.name}</span>
                <span className="gg-kachel-zeile">{d.istFahrzeug ? "Fahrzeug" : "Drohne"}</span>
                <span className="gg-kachel-zeile">
                  Gesundheit {d.gesundheitAktuell}/{d.gesundheitMax}
                  {d.aussenhuelleMax != null && d.aussenhuelleMax > 0 && (
                    <>
                      {" — "}Außenhülle{" "}
                      <span style={d.aussenhuelleAktuell! < d.aussenhuelleMax ? { color: "var(--nein)" } : undefined}>
                        {d.aussenhuelleAktuell}/{d.aussenhuelleMax}
                      </span>
                    </>
                  )}
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {/* Party-Reparatur-Freigabe (05.11.2026): wen darf ich noch fragen, und
          wem habe ich selbst schon Zugriff erteilt (zum Widerrufen). Immer
          sichtbar (nicht nur bei vorhandenen Einträgen) — Mark, nach dem
          ersten Klicktest: "ich sehe nirgendwo etwas wo ich einen Spieler
          meiner Party sehen würde", weil der Abschnitt bei leeren Listen
          komplett verschwand, statt den Grund zu erklären. */}
      <div className="wb-freigaben">
        <p className="lu-hinweis">Reparatur unter Party-Mitgliedern</p>
        {!inEigenerParty && (
          <p className="gg-leer">Du bist aktuell in keiner Party — die Spielleitung muss dich erst einer zuordnen.</p>
        )}
        {inEigenerParty && partyAnfragbar.length === 0 && erteilteFreigaben.length === 0 && (
          <p className="gg-leer">Niemand sonst in deiner Party, dem du Zugriff geben oder den du fragen könntest.</p>
        )}
        {partyAnfragbar.length > 0 && (
          <>
            <p className="lu-hinweis">Reparatur-Zugriff anfragen</p>
            <div className="wb-freigaben-liste">
              {partyAnfragbar.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className="wb-freigabe-knopf"
                  disabled={anfrageLaeuft.has(m.id)}
                  onClick={() => onFreigabeAnfragen(m.id)}
                >
                  {anfrageLaeuft.has(m.id) ? `Angefragt bei ${m.name}…` : `🔧 Bei ${m.name} anfragen`}
                </button>
              ))}
            </div>
          </>
        )}
        {erteilteFreigaben.length > 0 && (
          <>
            <p className="lu-hinweis">Du hast Reparatur-Zugriff erteilt an</p>
            <div className="wb-freigaben-liste">
              {erteilteFreigaben.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className="wb-freigabe-knopf wb-freigabe-widerrufen"
                  onClick={() => onFreigabeWiderrufen(f.id)}
                >
                  {f.name} — widerrufen ✕
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {offenesZiel && (
        <ReparaturFenster
          campaignId={campaignId}
          ziel={offenesZiel}
          onSchliessen={() => setOffenesZiel(null)}
          onGeaendert={onGeaendert}
          erlaubeHaendler={false}
        />
      )}
    </div>
  );
}

export type { Gegenstand };
