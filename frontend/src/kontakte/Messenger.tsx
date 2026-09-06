import { useEffect, useRef, useState } from "react";
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

  // Nur Kontakte mit offenem Chat zeigen
  const chatKontakte = kontakte.filter((k) => k.chatOffen);

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

  return (
    <div className="msg-huelle">
      {chatKontakte.length === 0 ? (
        <div className="msg-leer">
          <span className="msg-leer-icon">◍</span>
          <p>Noch keine Chats.</p>
          <p style={{ fontSize: "0.8rem" }}>
            Tausche Kontaktdaten mit NPCs, um hier zu chatten.
          </p>
        </div>
      ) : (
        <div className="msg-liste">
          {chatKontakte.map((k) => (
            <KontaktKarte key={k.id} kontakt={k} onClick={() => setAktiv(k)} />
          ))}
        </div>
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

  useEffect(() => {
    endeRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
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

      <div className="msg-blase">
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
