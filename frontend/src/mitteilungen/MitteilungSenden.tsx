import { useEffect, useRef, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { entitiesApi, type Person } from "../entities/api";
import { bildFuerAnsage, sendeMitteilung, ziehZurueck, type Warnfarbe } from "./api";
import { useMitteilungen } from "./MitteilungenKontext";
import "./mitteilungen.css";

/** Was am Tisch am häufigsten gebraucht wird — mitten im Kampf tippt niemand. */
/** Ansagen, die als Warnung sinnvoll sind — der Schirm pulsiert dabei. */
const SCHNELL_WARNUNG = ["Würfelt für Initiative!", "Gefahr!", "Hinterhalt!"];

const SCHNELL = [
  "Würfelt für Initiative!",
  "Wahrnehmungsprobe, bitte.",
  "Ihr hört Schritte im Nebenraum.",
  "Kurze Pause.",
];

/**
 * Sendefenster der Spielleitung: Popup an alle oder an einzelne Charaktere.
 *
 * Sitzt hinter dem ◎-Symbol in der Werkzeugleiste, das im UI-Konzept schon
 * als "SL-Popups" vorgesehen war (bis jetzt deaktiviert).
 */
export function MitteilungSenden({ campaignId }: { campaignId: string }) {
  const [offen, setOffen] = useState(false);
  const [pcs, setPcs] = useState<Person[]>([]);
  const [text, setText] = useState("");
  const [anAlle, setAnAlle] = useState(true);
  const [ziele, setZiele] = useState<string[]>([]);
  const [sendet, setSendet] = useState(false);
  // Hochgeladenes Bild, das mitgeschickt wird (leer = reine Textansage).
  const [bildUrl, setBildUrl] = useState("");
  // Warnung: ganzer Schirm pulsiert. Bewusst eigener Schalter statt einer
  // dritten Art im Dropdown — man greift im Kampf danach, nicht im Menue.
  const [alsWarnung, setAlsWarnung] = useState(false);
  const [warnfarbe, setWarnfarbe] = useState<Warnfarbe>("rot");
  const [laedtBild, setLaedtBild] = useState(false);
  const dateiRef = useRef<HTMLInputElement>(null);
  const [rueckmeldung, setRueckmeldung] = useState<string | null>(null);
  const { mitteilungen, verbunden, neuLaden } = useMitteilungen();

  useEffect(() => {
    if (!offen) return;
    // Ungefiltert: die SL soll alle ihre Charaktere als Ziel wählen können.
    entitiesApi
      .listPersonenAlsGm(campaignId)
      .then((alle) => setPcs(alle.filter((p) => p.personType === "PC")))
      .catch(() => setPcs([]));
  }, [campaignId, offen]);

  async function senden(inhalt: string) {
    const sauber = inhalt.trim();
    // Ein Bild spricht fuer sich — dann ist der Text freiwillig.
    // Eine Warnung nicht: ein pulsierender Schirm ohne Ansage sagt nichts.
    if (!sauber && (!bildUrl || alsWarnung)) return;
    if (sendet) return;
    if (!anAlle && ziele.length === 0) {
      setRueckmeldung("Kein Empfänger gewählt.");
      return;
    }
    setSendet(true);
    setRueckmeldung(null);
    try {
      const { zugestellt } = await sendeMitteilung(campaignId, {
        // Warnung schlaegt Bild: ein pulsierender Schirm mit Bild waere
        // beides halb. Bild bleibt dem ruhigen Popup vorbehalten.
        art: alsWarnung ? "WARNUNG" : bildUrl ? "BILD" : "TEXT",
        inhalt: sauber,
        bildUrl: alsWarnung ? "" : bildUrl,
        farbe: warnfarbe,
        anAlle,
        empfaengerIds: anAlle ? [] : ziele,
      });
      setText("");
      setBildUrl("");
      neuLaden();
      setRueckmeldung(
        zugestellt > 0
          ? `Zugestellt an ${zugestellt} offene Verbindung${zugestellt === 1 ? "" : "en"}.`
          : "Gespeichert — niemand ist gerade verbunden, es wird beim nächsten Öffnen gezeigt.",
      );
    } catch (e) {
      setRueckmeldung(e instanceof Error ? e.message : "Senden fehlgeschlagen");
    } finally {
      setSendet(false);
    }
  }

  async function bildWaehlen(datei: File | undefined) {
    if (!datei) return;
    setLaedtBild(true);
    setRueckmeldung(null);
    try {
      const { url } = await bildFuerAnsage(campaignId, datei);
      setBildUrl(url);
    } catch (e) {
      setRueckmeldung(e instanceof Error ? e.message : "Bild konnte nicht hochgeladen werden");
    } finally {
      setLaedtBild(false);
      if (dateiRef.current) dateiRef.current.value = "";
    }
  }

  function zielUmschalten(id: string) {
    setZiele((alt) => (alt.includes(id) ? alt.filter((x) => x !== id) : [...alt, id]));
  }

  const letzte = mitteilungen.slice(0, 5);

  return (
    <>
      <button
        type="button"
        className="cl-werkzeug"
        onClick={() => setOffen(true)}
        title="Ansage an die Spieler senden"
      >
        ◎
      </button>

      <Fenster
        offen={offen}
        titel="Ansage an die Spieler"
        unterzeile={
          <span className="mt-leitung" data-verbunden={verbunden}>
            {verbunden ? "● Live verbunden" : "○ getrennt"}
          </span>
        }
        kennung="mitteilung-senden"
        ton="var(--warn)"
        onSchliessen={() => setOffen(false)}
      >
        <div className="mt-senden">
          <div className="mt-schnell">
            {(alsWarnung ? SCHNELL_WARNUNG : SCHNELL).map((s) => (
              <button key={s} type="button" onClick={() => senden(s)} disabled={sendet}>
                {s}
              </button>
            ))}
          </div>

          {!alsWarnung && (
          <div className="mt-schnell">
            <button type="button" onClick={() => dateiRef.current?.click()} disabled={laedtBild}>
              {laedtBild ? "lädt…" : "▣ Bild wählen"}
            </button>
            {bildUrl && (
              <button type="button" onClick={() => setBildUrl("")} style={{ color: "var(--signal)" }}>
                Bild entfernen
              </button>
            )}
          </div>
          )}

          <input
            ref={dateiRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            style={{ display: "none" }}
            onChange={(e) => bildWaehlen(e.target.files?.[0])}
          />

          {bildUrl && (
            <div className="mt-vorschau">
              <img src={bildUrl} alt="Vorschau" />
              <span style={{ fontSize: 12, color: "var(--text-leise)" }}>
                Wird als Bild gesendet. Der Text darunter ist die Bildunterschrift und darf leer bleiben.
              </span>
            </div>
          )}

          <textarea
            placeholder={
              alsWarnung ? "Warntext — steht gross in der Mitte…" : bildUrl ? "Bildunterschrift (freiwillig)…" : "Eigene Ansage…"
            }
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              // Strg+Enter sendet — Enter bleibt Zeilenumbruch.
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) senden(text);
            }}
            style={{ minHeight: 80 }}
          />

          <div className="mt-ziel-wahl">
            <button
              type="button"
              className="mt-pc"
              aria-pressed={alsWarnung}
              onClick={() => setAlsWarnung((w) => !w)}
              title="Der ganze Bildschirm pulsiert, die Ansage steht gross in der Mitte"
              style={alsWarnung ? { color: "var(--signal)", borderColor: "var(--signal)" } : undefined}
            >
              ⚠ Als Warnung
            </button>

            {alsWarnung && (
              <span className="wn-farbwahl">
                {(["rot", "blau", "violett"] as const).map((f) => (
                  <button
                    key={f}
                    type="button"
                    className="wn-farbknopf"
                    aria-pressed={warnfarbe === f}
                    onClick={() => setWarnfarbe(f)}
                    style={{ "--wn-probe": `var(--warnung-${f})` } as React.CSSProperties}
                  >
                    {f}
                  </button>
                ))}
              </span>
            )}
          </div>

          <div className="mt-ziel-wahl">
            <button
              type="button"
              className="mt-pc"
              aria-pressed={anAlle}
              onClick={() => setAnAlle(true)}
            >
              An alle
            </button>
            <button
              type="button"
              className="mt-pc"
              aria-pressed={!anAlle}
              onClick={() => setAnAlle(false)}
            >
              An einzelne
            </button>
          </div>

          {!anAlle && (
            <div className="mt-ziel-wahl">
              {pcs.length === 0 && (
                <span style={{ color: "var(--text-leise)", fontSize: 12 }}>
                  Keine Spielercharaktere vorhanden.
                </span>
              )}
              {pcs.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="mt-pc"
                  aria-pressed={ziele.includes(p.id)}
                  onClick={() => zielUmschalten(p.id)}
                >
                  {p.name}
                </button>
              ))}
            </div>
          )}

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              type="button"
              onClick={() => senden(text)}
              disabled={sendet || (!text.trim() && (!bildUrl || alsWarnung))}
              style={
                alsWarnung
                  ? { color: "var(--signal)", borderColor: "var(--signal)" }
                  : { color: "var(--warn)", borderColor: "var(--warn)" }
              }
            >
              {sendet ? "sendet…" : alsWarnung ? "⚠ Warnung senden" : "Senden"}
            </button>
            <span style={{ fontSize: 11, color: "var(--text-aus)" }}>Strg+Enter</span>
          </div>

          {rueckmeldung && (
            <p style={{ fontSize: 12, color: "var(--text-leise)", margin: 0 }}>{rueckmeldung}</p>
          )}

          {letzte.length > 0 && (
            <>
              <hr />
              <div style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-aus)" }}>
                Zuletzt gesendet
              </div>
              <div className="mt-liste">
                {letzte.map((m) => (
                  <div key={m.id} className="mt-eintrag">
                    <div className="mt-eintrag-kopf">
                      <span className="mt-eintrag-ziel" data-gerichtet={!m.anAlle ? "true" : undefined}>
                        {m.anAlle ? "an alle" : `an ${m.empfaengerIds.length}`}
                      </span>
                      <button
                        type="button"
                        className="mt-pc"
                        style={{ marginLeft: "auto", color: "var(--signal)" }}
                        title="Zurückziehen — verschwindet auch auf offenen Bildschirmen"
                        onClick={async () => {
                          await ziehZurueck(campaignId, m.id).catch(() => {});
                          neuLaden();
                        }}
                      >
                        ✕
                      </button>
                    </div>
                    {m.art === "BILD" && m.bildUrl && (
                      <img src={m.bildUrl} alt="" style={{ maxWidth: 120, borderRadius: 4, marginBottom: 4 }} />
                    )}
                    {m.inhalt && <div className="mt-eintrag-text">{m.inhalt}</div>}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </Fenster>
    </>
  );
}
