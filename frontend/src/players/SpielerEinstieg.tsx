import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { playersApi, type SpielerMe, type SpaltenSumme, type VorgefertigterCharakter } from "./api";
import "./einstieg.css";

const WEG_TITEL: Record<string, string> = {
  KEINER: "",
  MAGIER: "Magier",
  NEUROWEAVER: "Neuroweaver",
};

const LEERE_SPALTEN: SpaltenSumme = { koerperlich: 0, gesellschaftlich: 0, geistig: 0 };

const SPALTEN: { key: keyof SpaltenSumme; titel: string; ton: string }[] = [
  { key: "koerperlich", titel: "Körperlich", ton: "var(--wert-koerperlich)" },
  { key: "gesellschaftlich", titel: "Gesellschaftlich", ton: "var(--wert-gesellschaftlich)" },
  { key: "geistig", titel: "Geistig", ton: "var(--wert-geistig)" },
];

/**
 * Ersteinstieg für Spieler ohne zugeordneten Charakter.
 *
 * Zwei Wege (Mark, 22.09.2026): selbst bauen — führt in die bestehende
 * Charaktererstellung (`Charaktererstellung.tsx`, hängt bereits automatisch
 * ans Charakterblatt, sobald `erstellungAbgeschlossen=false` ist, siehe
 * `Charakterblatt.tsx`) — oder einen vorgefertigten PC dauerhaft übernehmen.
 * Vor der Übernahme zeigt ein Steckbrief Bild, Spaltenbalance und die
 * kurzen Texte — nicht den vollen Bogen.
 *
 * "Vorgefertigt" ist seit 08.10.2026 ein echtes Feld (`istVorgefertigt`,
 * von der SL bewusst im PC-Detail-Popup gesetzt) — vorher galt jeder
 * abgeschlossene PC ohne Spieler automatisch als vorgefertigt. Die
 * Zuweisung läuft serverseitig atomar (`repository.charakter_waehlen`),
 * damit zwei Spieler nicht denselben Charakter ergattern können.
 */
export function SpielerEinstieg({
  campaignName,
  benutzername,
  onZugewiesen,
  onAbmelden,
}: {
  campaignName: string;
  benutzername: string;
  onZugewiesen: (frisch: SpielerMe) => void;
  onAbmelden: () => void;
}) {
  const [ansicht, setAnsicht] = useState<"wahl" | "vorgefertigt">("wahl");
  const [vorgefertigte, setVorgefertigte] = useState<VorgefertigterCharakter[] | null>(null);
  const [steckbrief, setSteckbrief] = useState<VorgefertigterCharakter | null>(null);
  const [uebernehmenOffen, setUebernehmenOffen] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  useEffect(() => {
    if (ansicht !== "vorgefertigt" || vorgefertigte !== null) return;
    playersApi
      .vorgefertigteListe()
      .then(setVorgefertigte)
      .catch(() => setVorgefertigte([]));
  }, [ansicht, vorgefertigte]);

  async function selbstErstellen() {
    setFehler(null);
    setLaeuft(true);
    try {
      onZugewiesen(await playersApi.charakterNeu());
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Anlegen fehlgeschlagen");
      setLaeuft(false);
    }
  }

  async function bestaetigeWahl() {
    if (!steckbrief) return;
    setFehler(null);
    setLaeuft(true);
    try {
      onZugewiesen(await playersApi.charakterWaehlen(steckbrief.id));
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Wählen fehlgeschlagen");
      // War der Charakter inzwischen doch vergeben, ist die Liste veraltet —
      // neu laden, damit er nicht nochmal antippbar bleibt.
      setVorgefertigte(null);
      setLaeuft(false);
    } finally {
      setSteckbrief(null);
      setUebernehmenOffen(false);
    }
  }

  return (
    <div className="ei-buehne">
      <div className="ei-kasten cl-roehre">
        <header className="ei-kopf">
          <h1>
            Willkommen in der Kampagne {campaignName}, {benutzername}
          </h1>
        </header>

        {ansicht === "wahl" && (
          <div className="ei-wahl">
            <p className="ei-hinweis">Dir ist noch kein Charakter zugeordnet. Wie möchtest du starten?</p>
            <div className="ei-karten">
              <button type="button" className="ei-karte" onClick={selbstErstellen} disabled={laeuft}>
                <span className="ei-karte-symbol" aria-hidden="true">
                  ✦
                </span>
                <span className="ei-karte-titel">Charakter selbst erstellen</span>
                <span className="ei-karte-text">
                  Führt dich durch Weg, Rasse, Attribute, Fertigkeiten und Hintergrund.
                </span>
              </button>
              <button
                type="button"
                className="ei-karte"
                onClick={() => setAnsicht("vorgefertigt")}
                disabled={laeuft}
              >
                <span className="ei-karte-symbol" aria-hidden="true">
                  ▤
                </span>
                <span className="ei-karte-titel">Vorgefertigten Charakter wählen</span>
                <span className="ei-karte-text">
                  Ein fertiger PC deiner Spielleitung — sofort spielbereit, gehört danach dauerhaft dir.
                </span>
              </button>
            </div>
          </div>
        )}

        {ansicht === "vorgefertigt" && (
          <div className="ei-vorgefertigt">
            <button type="button" className="ei-zurueck" onClick={() => setAnsicht("wahl")} disabled={laeuft}>
              ← Zurück
            </button>

            {vorgefertigte === null && <p className="ei-hinweis">Lade Charaktere…</p>}
            {vorgefertigte?.length === 0 && (
              <p className="ei-hinweis">
                Es steht gerade kein vorgebauter Charakter zur Verfügung — erstelle dir stattdessen selbst
                einen.
              </p>
            )}

            {vorgefertigte && vorgefertigte.length > 0 && (
              <div className="ei-raster">
                {vorgefertigte.map((p) => (
                  <button
                    type="button"
                    key={p.id}
                    className="ei-pc-karte"
                    onClick={() => {
                      setSteckbrief(p);
                      setUebernehmenOffen(false);
                    }}
                    disabled={laeuft}
                  >
                    <div className="ei-pc-bild-bereich">
                      {p.bildUrl ? (
                        <img src={p.bildUrl} alt={p.name} />
                      ) : (
                        <span className="ei-pc-bild-leer" aria-hidden="true">
                          ◉
                        </span>
                      )}
                    </div>
                    <div className="ei-pc-info">
                      <strong>{p.name}</strong>
                      {p.konzept && <span className="ei-pc-konzept">{p.konzept}</span>}
                      {(p.rasse || (p.weg && p.weg !== "KEINER")) && (
                        <span className="ei-pc-tags">
                          {[p.rasse, WEG_TITEL[p.weg ?? "KEINER"]].filter(Boolean).join(" · ")}
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {fehler && <p className="ei-fehler">{fehler}</p>}

        <button type="button" className="ei-abmelden" onClick={onAbmelden}>
          Abmelden
        </button>
      </div>

      {steckbrief && (
        <AuswahlSteckbrief
          person={steckbrief}
          laeuft={laeuft}
          onSchliessen={() => {
            if (uebernehmenOffen) {
              setUebernehmenOffen(false);
              return;
            }
            setSteckbrief(null);
          }}
          onWaehlen={() => setUebernehmenOffen(true)}
        />
      )}

      {uebernehmenOffen && steckbrief && (
        <Bestaetigung
          titel="Charakter dauerhaft übernehmen"
          text={`„${steckbrief.name}“ gehört danach dir — kein anderer Spieler kann ihn mehr wählen.`}
          jaText="Übernehmen"
          onJa={bestaetigeWahl}
          onNein={() => setUebernehmenOffen(false)}
        />
      )}
    </div>
  );
}

function AuswahlSteckbrief({
  person,
  laeuft,
  onSchliessen,
  onWaehlen,
}: {
  person: VorgefertigterCharakter;
  laeuft: boolean;
  onSchliessen: () => void;
  onWaehlen: () => void;
}) {
  const unterzeile = [person.rasse, WEG_TITEL[person.weg ?? "KEINER"]].filter(Boolean).join(" · ");
  const texte = [
    { titel: "Konzept", text: person.konzept },
    { titel: "Ambition", text: person.ambition },
    { titel: "Verlangen", text: person.verlangen },
    { titel: "Ziel", text: person.ziel },
  ].filter((eintrag) => eintrag.text?.trim());

  return (
    <Fenster
      offen
      titel={person.name}
      unterzeile={unterzeile || undefined}
      kennung={`auswahl:${person.id}`}
      onSchliessen={onSchliessen}
    >
      <div className="ei-steck-bild-rahmen">
        {person.bildUrl ? (
          <img src={person.bildUrl} alt={person.name} />
        ) : (
          <span className="ei-pc-bild-leer" aria-hidden="true">
            ◉
          </span>
        )}
      </div>

      <Spalten titel="Attribute" summen={person.attribute ?? LEERE_SPALTEN} />
      <Spalten titel="Fähigkeiten" summen={person.fertigkeiten ?? LEERE_SPALTEN} />
      {(person.sphaeren ?? 0) > 0 && <p className="ei-steck-extra">Sphären · {person.sphaeren}</p>}
      {(person.neuroweaving ?? 0) > 0 && <p className="ei-steck-extra">NeuroWeaving · {person.neuroweaving}</p>}

      {texte.map((eintrag) => (
        <section className="ei-steck-block" key={eintrag.titel}>
          <h3 className="ei-steck-rubrik">{eintrag.titel}</h3>
          <p className="ei-steck-text">{eintrag.text}</p>
        </section>
      ))}

      <button type="button" className="ei-steck-waehlen" onClick={onWaehlen} disabled={laeuft}>
        Charakter wählen
      </button>
    </Fenster>
  );
}

function Spalten({ titel, summen }: { titel: string; summen: SpaltenSumme }) {
  const max = Math.max(summen.koerperlich, summen.gesellschaftlich, summen.geistig, 1);
  return (
    <section className="ei-steck-block">
      <h3 className="ei-steck-rubrik">{titel}</h3>
      {SPALTEN.map((spalte) => (
        <div className="ei-balken" key={spalte.key}>
          <span className="ei-balken-titel">{spalte.titel}</span>
          <span className="ei-balken-spur" aria-hidden="true">
            <span
              className="ei-balken-fuellung"
              style={{ width: `${(summen[spalte.key] / max) * 100}%`, background: spalte.ton }}
            />
          </span>
          <span className="ei-balken-zahl">{summen[spalte.key]}</span>
        </div>
      ))}
    </section>
  );
}
