import { useCallback, useEffect, useState } from "react";
import {
  alsText,
  kontakteApi,
  type KontaktGm,
  type Kontaktstufe,
  type Nachricht,
  STUFEN,
} from "./api";
import type { Person } from "../entities/api";
import { entitiesApi } from "../entities/api";
import { Bestaetigung } from "../shell/Bestaetigung";
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

  // Formular für neuen Kontakt
  const [neuPcId, setNeuPcId] = useState("");
  const [neuNpcId, setNeuNpcId] = useState("");
  const [neuStufe, setNeuStufe] = useState<Kontaktstufe>("GESEHEN");
  const [neuChatOffen, setNeuChatOffen] = useState(false);

  // Löschen
  const [loeschenKontakt, setLoeschenKontakt] = useState<KontaktGm | null>(null);

  // Chat-Viewer
  const [chatKontakt, setChatKontakt] = useState<KontaktGm | null>(null);
  const [chatNachrichten, setChatNachrichten] = useState<Nachricht[]>([]);
  const [chatLaden, setChatLaden] = useState(false);

  const laden = useCallback(async () => {
    setLoading(true);
    try {
      const [k, personen] = await Promise.all([
        kontakteApi.uebersicht(campaignId),
        entitiesApi.listPersonenAlsGm(campaignId),
      ]);
      setKontakte(k);
      setPcs(personen.filter((p) => p.personType === "PC"));
      setNpcs(personen.filter((p) => p.personType === "NPC"));
    } catch (err) {
      console.error("Kontakte laden fehlgeschlagen:", err);
    } finally {
      setLoading(false);
    }
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

  async function chatOeffnen(k: KontaktGm) {
    setChatKontakt(k);
    setChatLaden(true);
    try {
      const chat = await kontakteApi.chat(campaignId, k.id);
      setChatNachrichten(chat.nachrichten);
    } catch (err) {
      console.error("Chat laden fehlgeschlagen:", err);
      setChatNachrichten([]);
    } finally {
      setChatLaden(false);
    }
  }

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
      {/* Neuen Kontakt anlegen */}
      <fieldset className="kontakte-gm-neu">
        <legend>Neuen Kontakt anlegen</legend>
        <div className="kontakte-gm-neu-form">
          <select value={neuPcId} onChange={(e) => setNeuPcId(e.target.value)}>
            <option value="">PC wählen...</option>
            {pcs.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <span className="kontakte-gm-pfeil">→</span>
          <select value={neuNpcId} onChange={(e) => setNeuNpcId(e.target.value)}>
            <option value="">NPC wählen...</option>
            {npcs.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
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
                        onClick={() => chatOeffnen(k)}
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
          nachrichten={chatNachrichten}
          laden={chatLaden}
          onSchliessen={() => setChatKontakt(null)}
          onGesendet={() => chatOeffnen(chatKontakt)}
        />
      )}
    </div>
  );
}

/** Chat-Popup als eigene Komponente für State-Isolation */
function ChatPopup({
  kontakt,
  campaignId,
  nachrichten,
  laden,
  onSchliessen,
  onGesendet,
}: {
  kontakt: KontaktGm;
  campaignId: string;
  nachrichten: Nachricht[];
  laden: boolean;
  onSchliessen: () => void;
  onGesendet: () => void;
}) {
  const [text, setText] = useState("");
  const [senden, setSenden] = useState(false);

  async function absenden(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || senden) return;
    setSenden(true);
    try {
      await kontakteApi.senden(campaignId, kontakt.id, text.trim());
      setText("");
      onGesendet();
    } finally {
      setSenden(false);
    }
  }

  return (
    <div className="kontakte-gm-chat-overlay" onClick={onSchliessen}>
      <div className="kontakte-gm-chat-popup" onClick={(e) => e.stopPropagation()}>
        <header className="kontakte-gm-chat-header">
          <h3>💬 {kontakt.pcName} ↔ {kontakt.npcName}</h3>
          <button onClick={onSchliessen}>✕</button>
        </header>
        <div className="kontakte-gm-chat-verlauf">
          {laden && <p className="kontakte-gm-chat-laden">Lade...</p>}
          {!laden && nachrichten.length === 0 && (
            <p className="kontakte-gm-chat-leer">Noch keine Nachrichten.</p>
          )}
          {nachrichten.map((n) => (
            <div
              key={n.id}
              className={`kontakte-gm-chat-msg ${n.vonMir ? "von-npc" : "von-pc"}`}
            >
              <span className="kontakte-gm-chat-absender">
                {n.vonMir ? kontakt.npcName : kontakt.pcName}:
              </span>
              <span className="kontakte-gm-chat-text">{alsText(n.inhalt)}</span>
              <span className="kontakte-gm-chat-zeit">
                {new Date(n.erstelltAm).toLocaleString("de-AT", {
                  day: "2-digit",
                  month: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          ))}
        </div>
        {kontakt.chatOffen && (
          <form className="kontakte-gm-chat-eingabe" onSubmit={absenden}>
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={`Als ${kontakt.npcName} antworten...`}
              disabled={senden}
              autoFocus
            />
            <button type="submit" disabled={!text.trim() || senden}>
              Senden
            </button>
          </form>
        )}
        {!kontakt.chatOffen && (
          <p className="kontakte-gm-chat-gesperrt">
            Chat ist geschlossen. Öffne ihn in der Tabelle.
          </p>
        )}
      </div>
    </div>
  );
}
