import { useCallback, useEffect, useRef, useState } from "react";
import {
  kontakteApi,
  type KontaktGm,
  type Kontaktstufe,
  type Nachricht,
  STUFEN,
} from "./api";
import type { Person } from "../entities/api";
import { entitiesApi } from "../entities/api";
import { ApiError } from "../api/client";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { NachrichtBlase } from "./Messenger";
import { PersonSuchAuswahl } from "./PersonSuchAuswahl";
import { GruppenGm } from "./GruppenGm";
import { chatZielAbonnieren } from "./chatZiel";
import "./kontakte-gm.css";

interface Props {
  campaignId: string;
}

/**
 * SL-Ansicht: Kontakte zwischen PCs und NPCs verwalten.
 *
 * Trennung zwischen „Stufe" (wie gut kennt man sich) und „Chat offen"
 * (hat man die Nummer ausgetauscht). Man kann jemanden gut kennen,
 * aber trotzdem keine Nummer haben — oder umgekehrt.
 */
export function KontakteGm({ campaignId }: Props) {
  const [kontakte, setKontakte] = useState<KontaktGm[]>([]);
  const [pcs, setPcs] = useState<Person[]>([]);
  const [npcs, setNpcs] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  // Der Messenger ist ein eigener Kampagnen-Schalter (Einstellungen) — ist
  // er aus, antwortet /kontakte komplett mit 403 (siehe backend
  // kontakte/routes.py). Vorher fiel das still unter den Tisch: die
  // Personenliste für die Auswahl-Picker hängt NICHT am Messenger (eigener,
  // unabhängiger Request), bekam aber trotzdem nie eine Chance zu laden,
  // weil beide Requests in einem Promise.all steckten. Jetzt getrennt, mit
  // sichtbarem Hinweis statt stillem console.error (Mark, 07.10.2026: "wie
  // funktioniert dieses Menü?" — weil es aussah, als wäre gar nichts da).
  const [messengerDeaktiviert, setMessengerDeaktiviert] = useState(false);

  // Formular für neuen Kontakt
  const [neuPcId, setNeuPcId] = useState("");
  const [neuNpcId, setNeuNpcId] = useState("");
  const [neuStufe, setNeuStufe] = useState<Kontaktstufe>("GESEHEN");
  const [neuChatOffen, setNeuChatOffen] = useState(false);

  // Löschen
  const [loeschenKontakt, setLoeschenKontakt] = useState<KontaktGm | null>(null);

  // Chat-Viewer
  const [chatKontakt, setChatKontakt] = useState<KontaktGm | null>(null);

  // „Zum Chat“ aus dem Nachrichten-Popup: den Verlauf dieses Kontakts öffnen, sobald die Liste da ist.
  const [zielKontaktId, setZielKontaktId] = useState<string | null>(null);
  useEffect(() => chatZielAbonnieren("KONTAKT", setZielKontaktId), []);

  const laden = useCallback(async () => {
    setLoading(true);
    setMessengerDeaktiviert(false);
    // Zwei unabhängige Requests, bewusst NICHT in einem Promise.all: die
    // Personenliste für die Picker braucht den Messenger nicht und soll
    // auch laden, wenn er aus ist — vorher riss ein 403 auf /kontakte
    // beide mit.
    try {
      const personen = await entitiesApi.listPersonenAlsGm(campaignId);
      setPcs(personen.filter((p) => p.personType === "PC"));
      setNpcs(personen.filter((p) => p.personType === "NPC"));
    } catch (err) {
      console.error("Personenliste laden fehlgeschlagen:", err);
    }
    try {
      const k = await kontakteApi.uebersicht(campaignId);
      setKontakte(k);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setMessengerDeaktiviert(true);
      } else {
        console.error("Kontakte laden fehlgeschlagen:", err);
      }
    }
    setLoading(false);
  }, [campaignId]);

  useEffect(() => {
    laden();
  }, [laden]);

  async function anlegen() {
    if (!neuPcId || !neuNpcId) return;
    await kontakteApi.anlegen(campaignId, neuPcId, neuNpcId, neuStufe, neuChatOffen);
    setNeuPcId("");
    setNeuNpcId("");
    setNeuStufe("GESEHEN");
    setNeuChatOffen(false);
    laden();
  }

  async function stufeAendern(k: KontaktGm, stufe: Kontaktstufe) {
    await kontakteApi.aendern(campaignId, k.id, { stufe });
    laden();
  }

  async function chatOffenToggle(k: KontaktGm) {
    await kontakteApi.aendern(campaignId, k.id, { chatOffen: !k.chatOffen });
    laden();
  }

  async function nameBekanntToggle(k: KontaktGm) {
    await kontakteApi.aendern(campaignId, k.id, { echterNameBekannt: !k.echterNameBekannt });
    laden();
  }

  async function loeschen() {
    if (!loeschenKontakt) return;
    await kontakteApi.loeschen(campaignId, loeschenKontakt.id);
    setLoeschenKontakt(null);
    laden();
  }

  useEffect(() => {
    if (!zielKontaktId || loading) return;
    const k = kontakte.find((x) => x.id === zielKontaktId);
    if (k) setChatKontakt(k);
    setZielKontaktId(null);
  }, [zielKontaktId, kontakte, loading]);

  if (loading && kontakte.length === 0) {
    return <div className="kontakte-gm-loading">Lade Kontakte...</div>;
  }

  // Nach PC gruppiert
  const nachPc = new Map<string, KontaktGm[]>();
  for (const k of kontakte) {
    const liste = nachPc.get(k.pcId) ?? [];
    liste.push(k);
    nachPc.set(k.pcId, liste);
  }

  return (
    <div className="kontakte-gm">
      {messengerDeaktiviert && (
        <p className="kontakte-gm-messenger-hinweis">
          ⚠ Der Messenger ist in dieser Kampagne deaktiviert — deshalb bleiben
          Kontaktliste und Auswahl-Felder leer. Aktivieren in ⚙ Einstellungen
          → „Messenger".
        </p>
      )}

      {/* Neuen Kontakt anlegen */}
      <fieldset className="kontakte-gm-neu">
        <legend>Neuen Kontakt anlegen</legend>
        <div className="kontakte-gm-neu-form">
          <PersonSuchAuswahl
            personen={pcs}
            wert={neuPcId}
            onWaehlen={setNeuPcId}
            platzhalter="PC suchen..."
          />
          <span className="kontakte-gm-pfeil">→</span>
          <PersonSuchAuswahl
            personen={npcs}
            wert={neuNpcId}
            onWaehlen={setNeuNpcId}
            platzhalter="NPC suchen..."
          />
          <select value={neuStufe} onChange={(e) => setNeuStufe(e.target.value as Kontaktstufe)}>
            {STUFEN.map((s) => (
              <option key={s.wert} value={s.wert}>
                {s.name}
              </option>
            ))}
          </select>
          <label className="kontakte-gm-checkbox">
            <input
              type="checkbox"
              checked={neuChatOffen}
              onChange={(e) => setNeuChatOffen(e.target.checked)}
            />
            Chat offen
          </label>
          <button onClick={anlegen} disabled={!neuPcId || !neuNpcId}>
            Anlegen
          </button>
        </div>
      </fieldset>

      {/* Gruppenchats: PCs und NPCs gemischt, nur die SL legt sie an */}
      {!messengerDeaktiviert && <GruppenGm campaignId={campaignId} pcs={pcs} npcs={npcs} />}

      {/* Bestehende Kontakte nach PC */}
      {Array.from(nachPc.entries()).map(([pcId, liste]) => {
        const pc = pcs.find((p) => p.id === pcId);
        return (
          <section key={pcId} className="kontakte-gm-pc">
            <h3>{pc?.name ?? "Unbekannt"}</h3>
            <table className="kontakte-gm-tabelle">
              <thead>
                <tr>
                  <th>NPC</th>
                  <th>Stufe</th>
                  <th>Chat</th>
                  <th>Name bekannt</th>
                  <th>Verlauf</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {liste.map((k) => (
                  <tr key={k.id}>
                    <td className="kontakte-gm-npc">
                      {k.bildUrl && (
                        <img
                          src={k.bildUrl}
                          alt=""
                          className="kontakte-gm-portrait"
                        />
                      )}
                      <span>{k.npcName}</span>
                    </td>
                    <td>
                      <select
                        value={k.stufe}
                        onChange={(e) =>
                          stufeAendern(k, e.target.value as Kontaktstufe)
                        }
                      >
                        {STUFEN.map((s) => (
                          <option key={s.wert} value={s.wert}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <button
                        className={`kontakte-gm-toggle ${k.chatOffen ? "aktiv" : ""}`}
                        onClick={() => chatOffenToggle(k)}
                        title={k.chatOffen ? "Chat schließen" : "Chat öffnen"}
                      >
                        {k.chatOffen ? "📱 offen" : "📵 zu"}
                      </button>
                    </td>
                    <td>
                      <button
                        className={`kontakte-gm-toggle ${k.echterNameBekannt ? "aktiv" : ""}`}
                        onClick={() => nameBekanntToggle(k)}
                        title={k.echterNameBekannt ? "Name verbergen" : "Name zeigen"}
                      >
                        {k.echterNameBekannt ? "✓ bekannt" : "? Alias"}
                      </button>
                    </td>
                    <td>
                      <button
                        className="kontakte-gm-chat-btn"
                        onClick={() => setChatKontakt(k)}
                        title="Chat-Verlauf anzeigen"
                      >
                        💬
                      </button>
                    </td>
                    <td>
                      <button
                        className="kontakte-gm-loeschen"
                        onClick={() => setLoeschenKontakt(k)}
                        title="Kontakt löschen"
                      >
                        🗑
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        );
      })}

      {kontakte.length === 0 && !loading && (
        <p className="kontakte-gm-leer">
          Noch keine Kontakte vorhanden. Lege oben einen an.
        </p>
      )}

      {loeschenKontakt && (
        <Bestaetigung
          titel="Kontakt löschen?"
          text={`${loeschenKontakt.pcName} vergisst ${loeschenKontakt.npcName} komplett.`}
          jaText="Ja, löschen"
          onJa={loeschen}
          onNein={() => setLoeschenKontakt(null)}
        />
      )}

      {/* Chat-Verlauf Popup */}
      {chatKontakt && (
        <ChatPopup
          kontakt={chatKontakt}
          campaignId={campaignId}
          onSchliessen={() => setChatKontakt(null)}
        />
      )}
    </div>
  );
}

/**
 * Chat-Verlauf als Commlink-Fenster — dieselbe Optik wie der Messenger der
 * Spieler (`msg-*`), nur im Fenster. Die SL schreibt als der NPC: dessen
 * Nachrichten stehen rechts („eigen“), die des PC links.
 */
function ChatPopup({
  kontakt,
  campaignId,
  onSchliessen,
}: {
  kontakt: KontaktGm;
  campaignId: string;
  onSchliessen: () => void;
}) {
  const [nachrichten, setNachrichten] = useState<Nachricht[]>([]);
  const [laden, setLaden] = useState(true);
  const [text, setText] = useState("");
  const [senden, setSenden] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const endeRef = useRef<HTMLDivElement>(null);

  const ladeNachrichten = useCallback(async () => {
    try {
      const chat = await kontakteApi.chat(campaignId, kontakt.id);
      setNachrichten(chat.nachrichten);
    } catch (err) {
      console.error("Chat laden fehlgeschlagen:", err);
    } finally {
      setLaden(false);
    }
  }, [campaignId, kontakt.id]);

  useEffect(() => {
    void ladeNachrichten();
    // Neue Spieler-Nachrichten erscheinen von selbst, wie beim Spieler.
    const uhr = setInterval(() => {
      if (!document.hidden) void ladeNachrichten();
    }, 3000);
    return () => clearInterval(uhr);
  }, [ladeNachrichten]);

  useEffect(() => {
    endeRef.current?.scrollIntoView({ behavior: "auto", block: "end" });
  }, [nachrichten.length]);

  async function absenden() {
    const sauber = text.trim();
    if (!sauber || senden) return;
    setSenden(true);
    setFehler(null);
    try {
      await kontakteApi.senden(campaignId, kontakt.id, sauber);
      setText("");
      await ladeNachrichten();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht senden");
    } finally {
      setSenden(false);
    }
  }

  return (
    <Fenster
      offen={true}
      titel={`${kontakt.pcName} ↔ ${kontakt.npcName}`}
      unterzeile="Chatverlauf"
      kennung={`gm-chat:${kontakt.id}`}
      onSchliessen={onSchliessen}
    >
      <div className="msg-huelle msg-gm-chat">
        <div className="msg-chat">
          <div className="msg-verlauf">
            {laden && <p style={{ color: "var(--text-leise)" }}>Lädt…</p>}
            {!laden && nachrichten.length === 0 && (
              <p style={{ color: "var(--text-leise)", textAlign: "center", margin: "auto" }}>
                Noch keine Nachrichten.
              </p>
            )}
            {nachrichten.map((n) => (
              <NachrichtBlase
                key={n.id}
                nachricht={n}
                absender={kontakt.pcName}
                initial={(kontakt.pcName || "?").charAt(0).toUpperCase()}
              />
            ))}
            <div ref={endeRef} />
          </div>

          {kontakt.chatOffen ? (
            <div className="msg-eingabe">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void absenden();
                  }
                }}
                placeholder={`Als ${kontakt.npcName} antworten…`}
                rows={2}
                disabled={senden}
              />
              <button
                type="button"
                className="msg-senden"
                onClick={() => void absenden()}
                disabled={senden || !text.trim()}
              >
                {senden ? "…" : "▶"}
              </button>
            </div>
          ) : (
            <div className="msg-eingabe-gesperrt">Chat ist geschlossen — in der Tabelle öffnen</div>
          )}

          {fehler && (
            <p style={{ color: "var(--warn)", padding: "var(--luft-2)", margin: 0 }}>{fehler}</p>
          )}
        </div>
      </div>
    </Fenster>
  );
}
