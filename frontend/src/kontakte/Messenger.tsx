import { useEffect, useRef, useState, type CSSProperties } from "react";
import { Fenster } from "../shell/Fenster";
import { alsText, kontakteApi, type Chat, type Kontakt, type Nachricht } from "./api";
import "./messenger.css";

/**
 * Messenger im Persona-5-Stil.
 *
 * Persona-inspiriertes Design mit schrägen Kanten, Neon-Cyberpunk-Farben und
 * animiertem Gitter-Hintergrund. Portraits bei jeder Nachricht wie im Spiel.
 *
 * Neu: `nurLesen` — der Spieler kann die Nachricht sehen, aber nicht antworten.
 * Für SL-Broadcasts oder Ankündigungen.
 */

interface MessengerProps {
  campaignId: string;
  kontakte: Kontakt[];
  onKontakteAktualisieren: () => void;
}

export function Messenger({ campaignId, kontakte, onKontakteAktualisieren }: MessengerProps) {
  const [aktiv, setAktiv] = useState<Kontakt | null>(null);
  const [blanko, setBlanko] = useState<Kontakt | null>(null);
  const [wunsch, setWunsch] = useState("");
  const [legtAn, setLegtAn] = useState(false);
  const [anlegenFehler, setAnlegenFehler] = useState<string | null>(null);

  // Offene Chats und noch leere Plätze aus der Charaktererstellung.
  // Die Plätze haben den Chat zu — ohne eigene Zeile sieht der Spieler nichts.
  const plaetze = kontakte.filter((k) => k.istBlankoKontakt);
  const chatKontakte = kontakte.filter((k) => k.chatOffen && !k.istBlankoKontakt);

  async function platzAnlegen() {
    if (!blanko || !wunsch.trim() || legtAn) return;
    setLegtAn(true);
    setAnlegenFehler(null);
    try {
      const neu = await kontakteApi.generieren(campaignId, blanko.id, wunsch.trim());
      setBlanko(null);
      setWunsch("");
      onKontakteAktualisieren();
      setAktiv(neu);
    } catch (e) {
      setAnlegenFehler(e instanceof Error ? e.message : "Konnte nicht angelegt werden");
    } finally {
      setLegtAn(false);
    }
  }

  if (aktiv) {
    return (
      <MessengerChat
        campaignId={campaignId}
        kontakt={aktiv}
        onZurueck={() => setAktiv(null)}
        onGeaendert={onKontakteAktualisieren}
      />
    );
  }

  const listeLeer = chatKontakte.length === 0 && plaetze.length === 0;

  return (
    <div className="msg-huelle">
      {listeLeer ? (
        <div className="msg-leer">
          <span className="msg-leer-icon">◍</span>
          <p>Noch keine Chats.</p>
          <p className="msg-leer-hinweis">
            Tausche Kontaktdaten mit NPCs, um hier zu chatten.
          </p>
        </div>
      ) : (
        <div className="msg-liste">
          {plaetze.map((k) => (
            <button
              key={k.id}
              type="button"
              className="msg-kontakt msg-kontakt-blanko"
              onClick={() => {
                setBlanko(k);
                setWunsch("");
                setAnlegenFehler(null);
              }}
            >
              <span className="msg-portrait">
                <span className="msg-portrait-leer">?</span>
              </span>
              <span className="msg-info">
                <span className="msg-name">{k.istMentor ? "Undefinierter Mentor" : "Undefinierter Kontakt"}</span>
                <span className="msg-vorschau">Tippen und beschreiben</span>
              </span>
            </button>
          ))}
          {chatKontakte.map((k) => (
            <KontaktKarte key={k.id} kontakt={k} onClick={() => setAktiv(k)} />
          ))}
        </div>
      )}

      {blanko && (
        <Fenster
          titel={blanko.istMentor ? "Undefinierter Mentor" : "Undefinierter Kontakt"}
          unterzeile={blanko.istMentor ? "Wer hat dich gelehrt?" : "Wen brauchst du?"}
          kennung={`kontakt-generieren:${blanko.id}`}
          offen={true}
          onSchliessen={() => {
            if (legtAn) return;
            setBlanko(null);
            setWunsch("");
            setAnlegenFehler(null);
          }}
        >
          <div className="msg-generieren">
            <p className="msg-generieren-hinweis">
              {blanko.istMentor
                ? "Beschreib, wer dich gelehrt hat. Daraus wird dein Mentor, stärker je nach deinen Mentor-Punkten. Zurücknehmen geht danach nicht."
                : "Beschreib, wer das sein soll. Daraus wird ein Kontakt, und der Chat geht auf. Zurücknehmen geht danach nicht."}
            </p>
            <textarea
              value={wunsch}
              onChange={(e) => setWunsch(e.target.value)}
              placeholder="z.B. ein Dealer im Nachtmarkt, der an Chrome kommt"
              rows={4}
              disabled={legtAn}
            />
            {anlegenFehler && <p className="msg-generieren-fehler">{anlegenFehler}</p>}
            <button
              type="button"
              className="cl-roehre"
              disabled={legtAn || !wunsch.trim()}
              onClick={() => void platzAnlegen()}
            >
              {legtAn ? "Wird angelegt…" : "Anlegen"}
            </button>
          </div>
        </Fenster>
      )}
    </div>
  );
}

/** Einzelne Kontakt-Karte in der Liste. */
function KontaktKarte({ kontakt, onClick }: { kontakt: Kontakt; onClick: () => void }) {
  return (
    <div className="msg-kontakt" onClick={onClick}>
      <div className="msg-portrait">
        {kontakt.bildUrl ? (
          <img src={kontakt.bildUrl} alt="" />
        ) : (
          <span className="msg-portrait-leer">?</span>
        )}
        {kontakt.ungelesen > 0 && <span className="msg-badge">{kontakt.ungelesen}</span>}
      </div>
      <div className="msg-info">
        <span className="msg-name">{kontakt.alias}</span>
        {kontakt.echterName && (
          <span className="msg-vorschau" style={{ color: "var(--neon)" }}>
            {kontakt.echterName}
          </span>
        )}
      </div>
      <span className="msg-zeit">▶</span>
    </div>
  );
}

/** Der eigentliche Chat. */
function MessengerChat({
  campaignId,
  kontakt,
  nurLesen = false,
  onZurueck,
  onGeaendert,
}: {
  campaignId: string;
  kontakt: Kontakt;
  /** Wenn true, kann der Spieler nicht antworten. */
  nurLesen?: boolean;
  onZurueck: () => void;
  onGeaendert?: () => void;
}) {
  const [chat, setChat] = useState<Chat | null>(null);
  const [text, setText] = useState("");
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const endeRef = useRef<HTMLDivElement>(null);

  async function laden() {
    try {
      const c = await kontakteApi.chat(campaignId, kontakt.id);
      setChat(c);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht laden");
    }
  }

  useEffect(() => {
    void laden();
    // Polling für neue Nachrichten
    const uhr = setInterval(() => {
      if (!document.hidden) void laden();
    }, 3000);
    return () => clearInterval(uhr);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, kontakt.id]);

  // Mobil (< 600px, gleicher Breakpoint wie messenger.css) wird beim Öffnen
  // UND bei jeder neuen Nachricht immer hart ans Ende gescrollt — auf dem
  // Handy will man den Chat nie manuell runterziehen. Am Desktop lief das
  // "smooth"-Scrollen schon zuverlässig, bleibt also unangetastet.
  useEffect(() => {
    const mobil = window.matchMedia("(max-width: 600px)").matches;
    if (mobil) {
      endeRef.current?.scrollIntoView({ behavior: "auto", block: "end" });
    } else {
      endeRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [chat?.nachrichten.length]);

  async function senden() {
    const sauber = text.trim();
    if (!sauber || nurLesen) return;
    setSendet(true);
    setFehler(null);
    try {
      await kontakteApi.senden(campaignId, kontakt.id, sauber);
      setText("");
      await laden();
      onGeaendert?.();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht senden");
    } finally {
      setSendet(false);
    }
  }

  return (
    <div className="msg-huelle">
      <div className="msg-chat">
        {/* Header */}
        <header className="msg-header">
          <button type="button" className="msg-zurueck" onClick={onZurueck}>
            ◀
          </button>
          <div className="msg-partner">
            {kontakt.bildUrl && (
              <img className="msg-partner-bild" src={kontakt.bildUrl} alt="" />
            )}
            <span className="msg-partner-name">{kontakt.alias}</span>
          </div>
          {nurLesen && <span className="msg-readonly">Nur Empfang</span>}
        </header>

        {/* Nachrichten */}
        <div className="msg-verlauf">
          {!chat && <p style={{ color: "var(--text-leise)" }}>Lädt…</p>}
          {chat?.nachrichten.length === 0 && (
            <p style={{ color: "var(--text-leise)", textAlign: "center", margin: "auto" }}>
              Schreib die erste Nachricht!
            </p>
          )}
          {chat?.nachrichten.map((n) => (
            <NachrichtBlase
              key={n.id}
              nachricht={n}
              bildUrl={n.vonMir ? undefined : kontakt.bildUrl}
            />
          ))}
          <div ref={endeRef} />
        </div>

        {/* Eingabe */}
        {nurLesen ? (
          <div className="msg-eingabe-gesperrt">
            ⚠ Du kannst hier nicht antworten
          </div>
        ) : (
          <div className="msg-eingabe">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void senden();
                }
              }}
              placeholder="Nachricht schreiben…"
              rows={2}
            />
            <button
              type="button"
              className="msg-senden"
              onClick={senden}
              disabled={sendet || !text.trim()}
            >
              {sendet ? "…" : "▶"}
            </button>
          </div>
        )}

        {fehler && (
          <p style={{ color: "var(--warn)", padding: "var(--luft-2)", margin: 0 }}>
            {fehler}
          </p>
        )}
      </div>
    </div>
  );
}

/** Einzelne Nachricht im Persona-5-Stil. */
function NachrichtBlase({
  nachricht,
  bildUrl,
}: {
  nachricht: Nachricht;
  bildUrl?: string;
}) {
  const zeit = nachricht.erstelltAm
    ? new Date(nachricht.erstelltAm).toLocaleTimeString("de-AT", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  // Persona 5 wirkt lebendig, weil keine zwei Sprechblasen exakt gleich
  // geschnitten sind. Statt einer starren Form pro Seite (eigen/fremd)
  // streuen wir die Schräg-Ecke leicht — deterministisch aus der
  // Nachrichten-ID gehasht, damit dieselbe Nachricht beim Neuladen nicht
  // "hüpft". Reine Formvariation, Farben/Ausrichtung bleiben unverändert.
  let hash = 0;
  for (let i = 0; i < nachricht.id.length; i++) {
    hash = (hash * 31 + nachricht.id.charCodeAt(i)) >>> 0;
  }
  const schraeg = 6 + (hash % 10); // 6–15px Eckenschnitt

  return (
    <div className="msg-nachricht" data-eigen={nachricht.vonMir}>
      {/* Portrait nur bei fremden Nachrichten */}
      {!nachricht.vonMir && bildUrl && (
        <img className="msg-mini-portrait" src={bildUrl} alt="" />
      )}
      {!nachricht.vonMir && !bildUrl && (
        <span
          className="msg-mini-portrait"
          style={{
            display: "grid",
            placeItems: "center",
            background: "color-mix(in srgb, var(--neon) 20%, var(--grund))",
            color: "var(--text-leise)",
          }}
        >
          ?
        </span>
      )}

      <div className="msg-blase" style={{ "--msg-schraeg": `${schraeg}px` } as CSSProperties}>
        {!nachricht.vonMir && nachricht.absender && (
          <span className="msg-absender">{nachricht.absender}</span>
        )}
        <span className="msg-text">{alsText(nachricht.inhalt)}</span>
        <span className="msg-uhrzeit">{zeit}</span>
      </div>
    </div>
  );
}

export { MessengerChat };
