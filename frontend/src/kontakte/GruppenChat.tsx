import { useCallback, useEffect, useRef, useState } from "react";
import { gruppenApi, type GruppenChat as ChatDaten } from "./gruppenApi";
import { NachrichtBlase } from "./Messenger";

/**
 * Der Verlauf einer Gruppe — gemeinsam für Spieler (Vollbild im Messenger) und
 * Spielleitung (im Fenster).
 *
 * Spieler schreiben als ihr eigener Charakter. Die SL schreibt als eines der
 * NPC-Mitglieder und wählt über das Auswahlfeld, welcher NPC spricht — ihr
 * eigener Name taucht nirgends auf. Die Bilder hängen an jeder Nachricht, wie
 * im Einzelchat.
 */
export function GruppenChat({
  campaignId,
  gruppeId,
  alsGm = false,
  onZurueck,
  onGeaendert,
}: {
  campaignId: string;
  gruppeId: string;
  /** SL-Ansicht: NPC-Auswahl statt eigenem Charakter, echte Namen. */
  alsGm?: boolean;
  /** Nur Spieleransicht: Pfeil zurück zur Liste (Vollbild mit Kopfzeile). */
  onZurueck?: () => void;
  onGeaendert?: () => void;
}) {
  const [chat, setChat] = useState<ChatDaten | null>(null);
  const [text, setText] = useState("");
  const [sprecherId, setSprecherId] = useState("");
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const endeRef = useRef<HTMLDivElement>(null);

  const laden = useCallback(async () => {
    try {
      setChat(await gruppenApi.chat(campaignId, gruppeId));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht laden");
    }
  }, [campaignId, gruppeId]);

  useEffect(() => {
    void laden();
    // Neue Nachrichten erscheinen von selbst, wie im Einzelchat.
    const uhr = setInterval(() => {
      if (!document.hidden) void laden();
    }, 3000);
    return () => clearInterval(uhr);
  }, [laden]);

  // Erster NPC als Sprecher vorbelegen; fällt er aus der Gruppe, den nächsten nehmen.
  const sprecher = chat?.sprecher ?? [];
  useEffect(() => {
    if (!alsGm) return;
    if (!sprecher.some((s) => s.id === sprecherId)) setSprecherId(sprecher[0]?.id ?? "");
  }, [alsGm, sprecher, sprecherId]);

  // Mobil immer hart ans Ende, am Desktop weich (wie MessengerChat).
  useEffect(() => {
    const mobil = window.matchMedia("(max-width: 600px)").matches;
    endeRef.current?.scrollIntoView({ behavior: mobil ? "auto" : "smooth", block: "end" });
  }, [chat?.nachrichten.length]);

  async function senden() {
    const sauber = text.trim();
    if (!sauber || sendet || (alsGm && !sprecherId)) return;
    setSendet(true);
    setFehler(null);
    try {
      await gruppenApi.senden(campaignId, gruppeId, sauber, alsGm ? sprecherId : undefined);
      setText("");
      await laden();
      onGeaendert?.();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht senden");
    } finally {
      setSendet(false);
    }
  }

  const gruppe = chat?.gruppe;
  const andere = (gruppe?.teilnehmer ?? []).filter((t) => !t.ich);
  const geschlossen = gruppe ? !gruppe.offen : false;
  const kannSenden = !geschlossen && (!alsGm || sprecher.length > 0);

  const inhalt = (
    <div className="msg-chat">
      {onZurueck && (
        <header className="msg-header">
          <button type="button" className="msg-zurueck" onClick={onZurueck}>
            ◀
          </button>
          <div className="msg-partner">
            <span className="msg-partner-name">{gruppe?.name ?? "Gruppe"}</span>
          </div>
        </header>
      )}

      {andere.length > 0 && (
        <div className="msg-gruppe-mitglieder">{andere.map((t) => t.name).join(" · ")}</div>
      )}

      <div className="msg-verlauf">
        {!chat && !fehler && <p style={{ color: "var(--text-leise)" }}>Lädt…</p>}
        {chat?.nachrichten.length === 0 && (
          <p style={{ color: "var(--text-leise)", textAlign: "center", margin: "auto" }}>
            Noch keine Nachrichten.
          </p>
        )}
        {chat?.nachrichten.map((n) => (
          <NachrichtBlase
            key={n.id}
            nachricht={n}
            bildUrl={n.bildUrl || undefined}
            initial={(n.absender || "?").charAt(0).toUpperCase()}
            // Die SL schreibt als mehrere NPCs — dort muss auch bei „eigenen“ Nachrichten
            // der Sprecher über der Blase stehen.
            absenderImmer={alsGm}
          />
        ))}
        <div ref={endeRef} />
      </div>

      {geschlossen ? (
        <div className="msg-eingabe-gesperrt">Diese Gruppe ist geschlossen</div>
      ) : !kannSenden ? (
        <div className="msg-eingabe-gesperrt">Kein NPC in der Gruppe — füge einen hinzu, um zu schreiben</div>
      ) : (
        <div className="msg-eingabe-block">
          {alsGm && (
            <label className="msg-sprecher">
              <span>Spricht:</span>
              <select value={sprecherId} onChange={(e) => setSprecherId(e.target.value)}>
                {sprecher.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </label>
          )}
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
              disabled={sendet}
            />
            <button type="button" className="msg-senden" onClick={() => void senden()} disabled={sendet || !text.trim()}>
              {sendet ? "…" : "▶"}
            </button>
          </div>
        </div>
      )}

      {fehler && <p style={{ color: "var(--warn)", padding: "var(--luft-2)", margin: 0 }}>{fehler}</p>}
    </div>
  );

  // Spieler: eigene Hülle wie MessengerChat. SL: kommt schon in einer Hülle im Fenster.
  return onZurueck ? <div className="msg-huelle">{inhalt}</div> : inhalt;
}
