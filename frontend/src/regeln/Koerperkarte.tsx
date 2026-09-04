import { useEffect, useState } from "react";
import { itemsApi, type Gegenstand } from "../items/api";
import { entitiesApi, type Person } from "../entities/api";
import { Bestaetigung } from "../shell/Bestaetigung";
import {
  ANDOCKPUNKTE,
  SILHOUETTEN,
  ZONEN,
  type Silhouette,
  type ZonenName,
} from "./silhouetten";
import "./koerperkarte.css";

/**
 * Körperkarte: wo sitzt welches Implantat.
 *
 * Aufbau nach Marks Vorbild (Metroid-Ausrüstungsanzeige): Drahtgitter-Figur in
 * der Mitte, Panels aussen, dünne Linien vom Panel zum Körperteil.
 *
 * Die Wahl der Silhouette wird **am Charakter** gespeichert, nicht an der
 * Ansicht: sonst müsste man sie bei jedem Wechsel neu einstellen.
 *
 * Vier Zonen mit je drei Plätzen (`KOERPERZONEN` im Backend).
 */

const PLAETZE = [1, 2, 3];

/* Zeichenfläche. Die Figur steht mittig, links und rechts je eine
   Panelspalte. HTML-Panels werden in Prozent dieser Fläche gesetzt —
   deshalb hat die Hülle dasselbe Seitenverhältnis. */
const BREITE = 900;
const HOEHE = 470;

/* Ausdehnung der Pfade — mit getBBox() **gemessen**, nicht geschätzt.
   Zwei geratene Werte liessen die Beine aus dem Bild laufen. */
const FIGUR_OBEN = 8;
const FIGUR_UNTEN = 213;
const FIGUR_HOEHE = FIGUR_UNTEN - FIGUR_OBEN;
const RAND = 22;
const SKALA = (HOEHE - 2 * RAND) / FIGUR_HOEHE;
const FIG_X = BREITE / 2 - (200 * SKALA) / 2;
const FIG_Y = RAND - FIGUR_OBEN * SKALA;

/** Figurenkoordinate → Zeichenflächenkoordinate. */
function zuFlaeche(p: { x: number; y: number }) {
  return { x: FIG_X + p.x * SKALA, y: FIG_Y + p.y * SKALA };
}

/** Wo welches Panel steht und wo seine Linie ansetzt. */
const PANELS: Record<
  ZonenName,
  { x: number; y: number; breite: number; seite: "links" | "rechts" }
> = {
  Kopf: { x: 636, y: 34, breite: 250, seite: "rechts" },
  Torso: { x: 636, y: 190, breite: 250, seite: "rechts" },
  Beine: { x: 636, y: 342, breite: 250, seite: "rechts" },
  Arme: { x: 14, y: 190, breite: 250, seite: "links" },
};

const proz = (wert: number, gesamt: number) => `${(wert / gesamt) * 100}%`;

export function Koerperkarte({
  campaignId,
  personId,
  aenderbar = false,
}: {
  campaignId: string;
  personId: string;
  /** Nur die SL darf die Silhouette umstellen. */
  aenderbar?: boolean;
}) {
  const [person, setPerson] = useState<Person | null>(null);
  const [chrom, setChrom] = useState<Gegenstand[]>([]);
  const [gewaehlt, setGewaehlt] = useState<ZonenName | null>(null);
  const [popupZone, setPopupZone] = useState<ZonenName | null>(null);
  const [popupAugment, setPopupAugment] = useState<Gegenstand | null>(null);
  const [laedt, setLaedt] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  // Chirurgie-Modus: SL kann Augments entfernen.
  const [chirurgieModus, setChirurgieModus] = useState(false);
  const [zuEntfernen, setZuEntfernen] = useState<Gegenstand | null>(null);

  const silhouette: Silhouette =
    (person?.silhouette as Silhouette) === "weiblich" ? "weiblich" : "maennlich";
  const pfade = SILHOUETTEN[silhouette];

  useEffect(() => {
    let weg = false;
    setLaedt(true);
    setFehler(null);
    Promise.all([
      entitiesApi.getPerson(campaignId, personId),
      itemsApi.verbautes(campaignId, personId),
    ])
      .then(([p, verbaut]) => {
        if (weg) return;
        setPerson(p);
        setChrom(verbaut);
      })
      .catch((e) => {
        if (!weg) setFehler(e instanceof Error ? e.message : "Konnte nicht laden");
      })
      .finally(() => {
        if (!weg) setLaedt(false);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, personId]);

  async function silhouetteWechseln() {
    if (!aenderbar || !person) return;
    const neu: Silhouette = silhouette === "maennlich" ? "weiblich" : "maennlich";
    const vorher = person;
    // Sofort umschalten, damit der Knopf nicht träge wirkt.
    setPerson({ ...person, silhouette: neu });
    try {
      await entitiesApi.updatePerson(campaignId, personId, { silhouette: neu });
    } catch {
      setPerson(vorher); // zurückdrehen, sonst lügt die Anzeige
    }
  }

  const inZone = (zone: ZonenName) => chrom.filter((g) => g.koerperzone === zone);
  const ohneZone = chrom.filter((g) => !g.koerperzone);
  const belegt = chrom.length;
  const plaetzeGesamt = ZONEN.length * PLAETZE.length;

  async function augmentEntfernen(item: Gegenstand) {
    try {
      await itemsApi.chirurgie(campaignId, item.id, false);
      setChrom(chrom.filter((g) => g.id !== item.id));
    } catch (e) {
      console.error("Chirurgie fehlgeschlagen", e);
    }
    setZuEntfernen(null);
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lädt…</p>;
  if (fehler) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;

  /** Ein Panel — im Grossbild absolut gesetzt, auf schmalen Geräten gestapelt. */
  function Panel({ zone }: { zone: ZonenName }) {
    const stuecke = inZone(zone);
    const platz = PANELS[zone];
    // Augments ohne Slot: der erste freie Platz, oder ans Ende.
    const mitSlot = (nr: number) => stuecke.find((g) => g.slot === nr);
    const ohneSlot = stuecke.filter((g) => g.slot == null);
    let ohneSlotIdx = 0;
    const fuerPlatz = (nr: number) => {
      const direkt = mitSlot(nr);
      if (direkt) return direkt;
      // Nächstes Augment ohne Slot hier einfügen
      if (ohneSlotIdx < ohneSlot.length) {
        return ohneSlot[ohneSlotIdx++];
      }
      return null;
    };
    return (
      <section
        className="kk-panel"
        data-zone={zone}
        data-gewaehlt={gewaehlt === zone}
        data-seite={platz.seite}
        style={{
          left: proz(platz.x, BREITE),
          top: proz(platz.y, HOEHE),
          width: proz(platz.breite, BREITE),
        }}
        onClick={() => {
          if (gewaehlt === zone) {
            // Zweiter Klick: Popup öffnen wenn Augments vorhanden
            if (stuecke.length > 0) setPopupZone(zone);
          } else {
            setGewaehlt(zone);
          }
        }}
      >
        <h4 className="kk-panelkopf">
          {zone}
          <em>
            {stuecke.length}/{PLAETZE.length}
          </em>
        </h4>
        <ul className="kk-panelliste">
          {PLAETZE.map((nr) => {
            const stueck = fuerPlatz(nr);
            return (
              <li
                key={nr}
                data-frei={!stueck}
                data-chirurgie={chirurgieModus && Boolean(stueck)}
                onClick={(e) => {
                  if (chirurgieModus && stueck) {
                    e.stopPropagation();
                    setZuEntfernen(stueck);
                  }
                }}
              >
                <span className="kk-punkt" data-an={Boolean(stueck)} aria-hidden="true" />
                {stueck ? (
                  <span className="kk-eintrag">
                    <span className="kk-name">{stueck.name}</span>
                    <span className="kk-werte">
                      {stueck.wVerlust > 0 && `${stueck.wVerlust} WK`}
                      {stueck.entfernungBeantragt && (
                        <span className="kk-antrag" title="Der Spieler bittet um die Ausbau-Operation">
                          {" "}
                          ⚕ beantragt
                        </span>
                      )}
                    </span>
                  </span>
                ) : (
                  <span className="kk-frei">frei</span>
                )}
              </li>
            );
          })}
        </ul>
      </section>
    );
  }

  return (
    <div className="kk-huelle">
      <div className="kk-kopfzeile">
        <span className="kk-titel">
          {person?.name}
          <em>
            {belegt} von {plaetzeGesamt} Plätzen belegt
          </em>
        </span>
        {aenderbar && (
          <button
            type="button"
            className="kk-schalter"
            onClick={silhouetteWechseln}
            title="Zwischen männlicher und weiblicher Silhouette wechseln"
          >
            {silhouette === "maennlich" ? "♂ männlich" : "♀ weiblich"}
          </button>
        )}
      </div>

      <div className="kk-buehne">
        {/* Figur, Verbindungslinien und Andockpunkte in einer Ebene — so
            können sie nicht auseinanderlaufen. */}
        <svg
          className="kk-zeichnung"
          viewBox={`0 0 ${BREITE} ${HOEHE}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label="Körperkarte"
        >
          {/* Verbindungslinien: waagerecht vom Panel weg, dann zum Körperteil. */}
          {ZONEN.map((zone) => {
            const ziel = zuFlaeche(ANDOCKPUNKTE[zone]);
            const panel = PANELS[zone];
            const vonX = panel.seite === "rechts" ? panel.x : panel.x + panel.breite;
            const vonY = panel.y + 34;
            const knick = panel.seite === "rechts" ? vonX - 26 : vonX + 26;
            return (
              <polyline
                key={`l-${zone}`}
                className="kk-leitung"
                data-gewaehlt={gewaehlt === zone}
                points={`${vonX},${vonY} ${knick},${vonY} ${ziel.x},${ziel.y}`}
              />
            );
          })}

          <g transform={`translate(${FIG_X} ${FIG_Y}) scale(${SKALA})`}>
            {ZONEN.map((zone) => {
              const anzahl = inZone(zone).length;
              return (
                <g key={zone} className="kk-zonengruppe">
                  <path
                    d={pfade[zone].umriss}
                    className="kk-zone"
                    data-belegt={anzahl > 0}
                    data-voll={anzahl >= PLAETZE.length}
                    data-gewaehlt={gewaehlt === zone}
                    onClick={() => {
                      if (gewaehlt === zone) {
                        if (anzahl > 0) setPopupZone(zone);
                      } else {
                        setGewaehlt(zone);
                      }
                    }}
                  >
                    <title>
                      {zone}: {anzahl} von {PLAETZE.length} belegt
                    </title>
                  </path>
                  {/* Binnenzeichnung — rein optisch, faengt keine Klicks. */}
                  <path d={pfade[zone].linien} className="kk-detail" data-belegt={anzahl > 0} />
                </g>
              );
            })}
          </g>

          {/* Andockpunkte zuletzt, damit sie ueber der Figur liegen. */}
          {ZONEN.map((zone) => {
            const ziel = zuFlaeche(ANDOCKPUNKTE[zone]);
            return (
              <rect
                key={`p-${zone}`}
                className="kk-anker"
                data-gewaehlt={gewaehlt === zone}
                x={ziel.x - 5}
                y={ziel.y - 5}
                width={10}
                height={10}
              />
            );
          })}
        </svg>

        {ZONEN.map((zone) => (
          <Panel key={zone} zone={zone} />
        ))}
      </div>

      {ohneZone.length > 0 && (
        <section className="kk-ohnezone">
          <h4>Ohne feste Zone</h4>
          <ul>
            {ohneZone.map((g) => (
              <li key={g.id}>
                <span className="kk-punkt" data-an="true" aria-hidden="true" />
                <span className="kk-name">{g.name}</span>
                <span className="kk-werte">{g.typ}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {belegt === 0 && (
        <p className="kk-leer">
          Nichts verbaut. Implantate werden im Charakterbogen eingesetzt — bis dahin liegen sie
          nur herum und wirken nicht.
        </p>
      )}

      {/* Chirurgie-Symbol: nur SL sieht es, links unten in der Silhouette. */}
      {aenderbar && belegt > 0 && (
        <button
          type="button"
          className="kk-chirurgie"
          data-aktiv={chirurgieModus}
          onClick={() => setChirurgieModus(!chirurgieModus)}
          title={chirurgieModus ? "Chirurgie-Modus beenden" : "Augments entfernen"}
        >
          ⚕
        </button>
      )}

      {chirurgieModus && (
        <p className="kk-chirurgie-hinweis">
          Klicke auf ein Augment, um es zu entfernen.
        </p>
      )}

      {/* Zonen-Popup: zeigt Augments der Zone, klickbar für Details */}
      {popupZone && (
        <div className="kk-popup-huelle" onClick={() => setPopupZone(null)}>
          <div className="kk-popup" onClick={(e) => e.stopPropagation()}>
            <h3>{popupZone}</h3>
            <ul className="kk-popup-liste">
              {inZone(popupZone).map((aug) => (
                <li
                  key={aug.id}
                  onClick={() => setPopupAugment(aug)}
                  className="kk-popup-eintrag"
                >
                  <span className="kk-punkt" data-an="true" aria-hidden="true" />
                  <span className="kk-name">{aug.name}</span>
                  <span className="kk-werte">
                    {aug.typ}
                    {aug.wVerlust > 0 && ` · ${aug.wVerlust} WK`}
                  </span>
                </li>
              ))}
            </ul>
            <button
              type="button"
              className="kk-popup-schliessen"
              onClick={() => setPopupZone(null)}
            >
              Schließen
            </button>
          </div>
        </div>
      )}

      {/* Augment-Detail-Popup */}
      {popupAugment && (
        <div className="kk-popup-huelle" onClick={() => setPopupAugment(null)}>
          <div className="kk-popup kk-popup-detail" onClick={(e) => e.stopPropagation()}>
            <h3>{popupAugment.name}</h3>
            <dl className="kk-popup-daten">
              <dt>Typ</dt>
              <dd>{popupAugment.typ}</dd>
              {popupAugment.koerperzone && (
                <>
                  <dt>Zone</dt>
                  <dd>{popupAugment.koerperzone}{popupAugment.slot ? `, Platz ${popupAugment.slot}` : ""}</dd>
                </>
              )}
              {popupAugment.wVerlust > 0 && (
                <>
                  <dt>Willenskraftverlust</dt>
                  <dd>{popupAugment.wVerlust}</dd>
                </>
              )}
            </dl>
            <div className="kk-popup-knoepfe">
              <button
                type="button"
                onClick={() => setPopupAugment(null)}
              >
                Zurück
              </button>
              {aenderbar && (
                <button
                  type="button"
                  className="kk-popup-entfernen"
                  onClick={() => {
                    setZuEntfernen(popupAugment);
                    setPopupAugment(null);
                    setPopupZone(null);
                  }}
                >
                  ⚕ Entfernen
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bestätigungsdialog */}
      {zuEntfernen && (
        <Bestaetigung
          titel="Augment entfernen"
          text={`Sicher, dass du „${zuEntfernen.name}" entfernen willst?

Das Augment wandert zurück ins Inventar und muss neu eingesetzt werden.`}
          jaText="Entfernen"
          neinText="Abbrechen"
          onJa={() => augmentEntfernen(zuEntfernen)}
          onNein={() => setZuEntfernen(null)}
        />
      )}
    </div>
  );
}
