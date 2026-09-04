import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { ChatFenster } from "./ChatFenster";
import { STUFEN, kontakteApi, type Kontakt } from "./api";
import "./kontakte.css";

/**
 * Das Kontaktverzeichnis eines Spielers.
 *
 * Zeigt NPCs unter ihrem Alias. Der echte Name erscheint nur, wenn die
 * Spielleitung ihn freigegeben hat — das entscheidet der Server, nicht diese
 * Ansicht.
 */
export function KontakteAnsicht({ campaignId }: { campaignId: string }) {
  const [kontakte, setKontakte] = useState<Kontakt[]>([]);
  const [offen, setOffen] = useState<Kontakt | null>(null);
  const [laedt, setLaedt] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [aliasEntwurf, setAliasEntwurf] = useState("");

  async function laden() {
    try {
      const liste = await kontakteApi.meine(campaignId);
      setKontakte(liste);
      // Das offene Fenster mitziehen, damit Zähler und Stufe stimmen.
      setOffen((v) => (v ? liste.find((k) => k.id === v.id) ?? null : null));
      setFehler(null);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht laden");
    } finally {
      setLaedt(false);
    }
  }

  useEffect(() => {
    void laden();
    const uhr = setInterval(() => {
      if (!document.hidden) void laden();
    }, 8000);
    return () => clearInterval(uhr);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  async function anfragen(k: Kontakt) {
    await kontakteApi.anfragen_stellen(campaignId, k.id);
    await laden();
  }

  async function aliasSpeichern(k: Kontakt) {
    await kontakteApi.aliasSetzen(campaignId, k.id, aliasEntwurf.trim());
    setAliasEntwurf("");
    await laden();
  }

  if (laedt) return <p className="ko-leise">Lädt…</p>;
  if (fehler) return <p className="ko-fehler">{fehler}</p>;

  if (kontakte.length === 0) {
    return (
      <p className="ko-leise">
        Noch niemand im Verzeichnis. Wer dir begegnet, taucht hier auf.
      </p>
    );
  }

  return (
    <div className="ko-huelle">
      <ul className="ko-liste">
        {kontakte.map((k) => {
          const stufe = STUFEN.find((s) => s.wert === k.stufe);
          return (
            <li key={k.id} className="ko-eintrag" onClick={() => setOffen(k)}>
              {k.bildUrl ? (
                <img className="ko-bild" src={k.bildUrl} alt="" />
              ) : (
                <span className="ko-bild ko-bild-leer" aria-hidden="true">
                  ?
                </span>
              )}

              <span className="ko-namen">
                <span className="ko-alias">
                  {k.alias}
                  {k.ungelesen > 0 && <em className="ko-ungelesen">{k.ungelesen}</em>}
                </span>
                {/* Nur sichtbar, wenn die SL den Namen freigegeben hat. */}
                {k.echterName && <span className="ko-echt">{k.echterName}</span>}
              </span>

              <span className="ko-stufe" title={stufe?.erklaerung}>
                {stufe?.name}
              </span>

              {k.chatOffen && <span className="ko-chatzeichen" title="Chat offen">◍</span>}
            </li>
          );
        })}
      </ul>

      {offen && (
        <Fenster
          titel={offen.alias}
          unterzeile={offen.echterName ?? undefined}
          kennung={`kontakt:${offen.id}`}
          offen={true}
          onSchliessen={() => setOffen(null)}
        >
          {offen.bildUrl && <img className="ko-grossbild" src={offen.bildUrl} alt="" />}

          {offen.beschreibung && <p className="ko-beschreibung">{offen.beschreibung}</p>}

          <div className="ko-aliaszeile">
            <label htmlFor="ko-alias">Dein Name für ihn/sie</label>
            <input
              id="ko-alias"
              value={aliasEntwurf || offen.persoenlicherAlias}
              onChange={(e) => setAliasEntwurf(e.target.value)}
              placeholder={offen.alias}
            />
            <button type="button" onClick={() => aliasSpeichern(offen)}>
              Merken
            </button>
          </div>

          {/* Kontaktanfrage: erst nach einem Gespräch, und nur einmal. */}
          {offen.stufe === "GESPROCHEN" && offen.kontaktAnfrageStatus === "KEINE" && (
            <button type="button" className="ko-anfrage" onClick={() => anfragen(offen)}>
              ◍ Kontakt anfragen
            </button>
          )}
          {offen.kontaktAnfrageStatus === "OFFEN" && (
            <p className="ko-leise">Anfrage gestellt — warte auf Antwort.</p>
          )}
          {offen.kontaktAnfrageStatus === "ABGELEHNT" && (
            <p className="ko-leise">Die Anfrage wurde abgelehnt.</p>
          )}

          <ChatFenster campaignId={campaignId} kontakt={offen} onGeaendert={laden} />
        </Fenster>
      )}
    </div>
  );
}
