import { useEffect, useRef, useState } from "react";
import { alsText, kontakteApi, type Chat, type Kontakt } from "./api";
import "./kontakte.css";

/**
 * Der Einzelchat mit einem NPC — im Commlink-Stil.
 *
 * Der Absender ist beim Spieler **immer der Alias des NPC**, nie
 * „Spielleitung“ (docs/phase-5-messenger.md). Das entscheidet der Server;
 * hier wird nur angezeigt, was er liefert.
 *
 * Nur der Verlauf scrollt intern — Hauptansicht und Seitenkörper behalten den
 * „nie scrollen“-Grundsatz.
 */
export function ChatFenster({
  campaignId,
  kontakt,
  alsGm = false,
  onGeaendert,
}: {
  campaignId: string;
  kontakt: Kontakt;
  /** Die SL schreibt als der NPC. */
  alsGm?: boolean;
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
    // Nachladen, solange das Fenster offen ist. Live über WebSocket wäre
    // schöner, ist aber laut Spec bewusst nicht Teil der ersten Runde.
    const uhr = setInterval(() => {
      if (!document.hidden) void laden();
    }, 4000);
    return () => clearInterval(uhr);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, kontakt.id]);

  useEffect(() => {
    endeRef.current?.scrollIntoView({ block: "end" });
  }, [chat?.nachrichten.length]);

  async function senden() {
    const sauber = text.trim();
    if (!sauber) return;
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

  if (!chat) return <p className="ko-leise">Lädt…</p>;

  if (!chat.chatOffen) {
    return (
      <p className="ko-leise">
        Der Chat ist zu. Er öffnet sich, sobald {chat.alias} eure Kontaktanfrage angenommen hat.
      </p>
    );
  }

  return (
    <div className="ko-chat">
      <div className="ko-verlauf">
        {chat.nachrichten.length === 0 && (
          <p className="ko-leise">Noch nichts geschrieben.</p>
        )}
        {chat.nachrichten.map((n) => (
          <div key={n.id} className="ko-blase" data-eigen={n.vonMir}>
            {!n.vonMir && <span className="ko-absender">{n.absender}</span>}
            <span className="ko-text">{alsText(n.inhalt)}</span>
            <span className="ko-zeit">
              {n.erstelltAm
                ? new Date(n.erstelltAm).toLocaleTimeString("de-AT", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : ""}
            </span>
          </div>
        ))}
        <div ref={endeRef} />
      </div>

      <div className="ko-eingabe">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            // Enter sendet, Shift+Enter macht einen Absatz.
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void senden();
            }
          }}
          placeholder={alsGm ? `Als ${chat.alias} schreiben…` : "Nachricht…"}
          rows={2}
        />
        <button type="button" onClick={senden} disabled={sendet || !text.trim()}>
          {sendet ? "…" : "Senden"}
        </button>
      </div>

      {fehler && <p className="ko-fehler">{fehler}</p>}
    </div>
  );
}
