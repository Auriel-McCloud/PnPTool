import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { Bestaetigung } from "../shell/Bestaetigung";
import { playersApi, type SpielerMe, type VorgefertigterCharakter } from "./api";
import "./einstieg.css";

const WEG_TITEL: Record<string, string> = {
  KEINER: "",
  MAGIER: "Magier",
  NEUROWEAVER: "Neuroweaver",
};

/**
 * Ersteinstieg für Spieler ohne zugeordneten Charakter.
 *
 * Zwei Wege (Mark, 22.09.2026): selbst bauen — führt in die bestehende
 * Charaktererstellung (`Charaktererstellung.tsx`, hängt bereits automatisch
 * ans Charakterblatt, sobald `erstellungAbgeschlossen=false` ist, siehe
 * `Charakterblatt.tsx`) — oder einen vorgefertigten PC fix übernehmen.
 *
 * "Vorgefertigt" ist bewusst kein eigenes Datenfeld: ein PC ohne
 * zugeordneten Spieler *ist* schon ein vorgefertigter Charakter — das war
 * Marks eigener Gedanke ("das macht am meisten Sinn?") und stimmt. Die
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
  const [gewaehlt, setGewaehlt] = useState<VorgefertigterCharakter | null>(null);
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
    if (!gewaehlt) return;
    setFehler(null);
    setLaeuft(true);
    try {
      onZugewiesen(await playersApi.charakterWaehlen(gewaehlt.id));
    } catch (err) {
      setFehler(err instanceof ApiError ? err.message : "Wählen fehlgeschlagen");
      // War der Charakter inzwischen doch vergeben, ist die Liste veraltet —
      // neu laden, damit er nicht nochmal antippbar bleibt.
      setVorgefertigte(null);
      setLaeuft(false);
    } finally {
      setGewaehlt(null);
    }
  }

  return (
    <div className="ei-buehne">
      <div className="ei-kasten cl-roehre">
        <header className="ei-kopf">
          <h1>Willkommen, {benutzername}</h1>
          <p className="ei-unter">{campaignName}</p>
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
                  Ein fertiger PC deiner Spielleitung — sofort spielbereit, gehört danach fix dir.
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
                    onClick={() => setGewaehlt(p)}
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

      {gewaehlt && (
        <Bestaetigung
          titel="Charakter fix wählen"
          text={`„${gewaehlt.name}" gehört danach dauerhaft dir — kein anderer Spieler kann ihn mehr wählen.`}
          jaText="Diesen Charakter wählen"
          onJa={bestaetigeWahl}
          onNein={() => setGewaehlt(null)}
        />
      )}
    </div>
  );
}
