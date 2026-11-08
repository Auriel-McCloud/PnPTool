import { useEffect, useRef, useState, type CSSProperties } from "react";
import { Fenster } from "../shell/Fenster";
import { alsText, kontakteApi, type Chat, type Kontakt, type Nachricht } from "./api";
import { chatZielAbonnieren } from "./chatZiel";
import { GruppenChat } from "./GruppenChat";
import { gruppenApi, type Gruppe } from "./gruppenApi";
import { MitspielerFenster } from "./MitspielerFenster";
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
  const [mitspielerOffen, setMitspielerOffen] = useState(false);
  const [gruppen, setGruppen] = useState<Gruppe[]>([]);
  // Der offene Chat steht als Popup über der Liste (wie bei der SL). Nur einer zugleich.
  const [aktiveGruppeId, setAktiveGruppeId] = useState<string | null>(null);

  // „Zum Chat“ aus dem Nachrichten-Popup. Eine Gruppe kennt der Chat selbst (Name lädt er mit);
  // ein Einzelchat braucht den Eintrag aus der Kontaktliste — die kann noch fehlen, dann nachladen.
  const [zielKontaktId, setZielKontaktId] = useState<string | null>(null);
  const zielVersuche = useRef(0);
  useEffect(
    () =>
      chatZielAbonnieren("KONTAKT", (id) => {
        zielVersuche.current = 0;
        setZielKontaktId(id);
      }),
    [],
  );
  useEffect(
    () =>
      chatZielAbonnieren("GRUPPE", (id) => {
        setAktiv(null);
        setMitspielerOffen(false);
        setBlanko(null);
        setAktiveGruppeId(id);
      }),
    [],
  );
  useEffect(() => {
    if (!zielKontaktId) return;
    const k = kontakte.find((x) => x.id === zielKontaktId);
    if (k) {
      setAktiveGruppeId(null);
      setMitspielerOffen(false);
      setBlanko(null);
      setAktiv(k);
      setZielKontaktId(null);
    } else if (zielVersuche.current < 3) {
      zielVersuche.current += 1;
      onKontakteAktualisieren();
    } else {
      setZielKontaktId(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zielKontaktId, kontakte]);

  async function gruppenLaden() {
    try {
      setGruppen(await gruppenApi.liste(campaignId));
    } catch {
      // Messenger aus (403) oder Netz weg — dann gibt es einfach keine Gruppen.
      setGruppen([]);
    }
  }

  // Eine Zusage eines Mitspielers, eine neue Gruppe oder neue Nachrichten kommen
  // ohne eigene Aktion an — die Liste still nachladen (auch hinter einem offenen Chat-
  // Popup: Reihenfolge und Zähler bleiben so aktuell).
  const aktualisierenRef = useRef(onKontakteAktualisieren);
  aktualisierenRef.current = onKontakteAktualisieren;
  const gruppenLadenRef = useRef(gruppenLaden);
  gruppenLadenRef.current = gruppenLaden;
  useEffect(() => {
    void gruppenLadenRef.current();
    const uhr = setInterval(() => {
      if (document.hidden) return;
      aktualisierenRef.current();
      void gruppenLadenRef.current();
    }, 5000);
    return () => clearInterval(uhr);
  }, []);

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

  // Einzelchats und Gruppen in EINER Liste: der Chat mit der neuesten Nachricht steht oben.
  // Ohne Nachricht zählt die Anlage; Altbestand ohne Zeit sinkt nach unten (stabile Sortierung).
  const eintraege = [
    ...gruppen.map((gruppe) => ({ gruppe, kontakt: null as Kontakt | null, zeit: gruppe.letzteAktivitaet || "" })),
    ...chatKontakte.map((kontakt) => ({ gruppe: null as Gruppe | null, kontakt, zeit: kontakt.letzteAktivitaet || "" })),
  ].sort((a, b) => (a.zeit < b.zeit ? 1 : a.zeit > b.zeit ? -1 : 0));

  function chatSchliessen() {
    setAktiv(null);
    setAktiveGruppeId(null);
    // Zähler und Reihenfolge sofort frisch, nicht erst nach dem nächsten Takt.
    onKontakteAktualisieren();
    void gruppenLaden();
  }

  const listeLeer = chatKontakte.length === 0 && plaetze.length === 0 && gruppen.length === 0;

  return (
    <div className="msg-huelle">
      <div className="msg-werkzeug">
        <button type="button" className="cl-roehre" onClick={() => setMitspielerOffen(true)}>
          ＋ Mitspieler
        </button>
      </div>
      {listeLeer ? (
        <div className="msg-leer">
          <span className="msg-leer-icon">◍</span>
          <p>Noch keine Chats.</p>
          <p className="msg-leer-hinweis">
            Tausche Kontaktdaten mit NPCs oder biete einem Mitspieler Kontakt an, um hier zu chatten.
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
          {eintraege.map((e) =>
            e.gruppe ? (
              <GruppenKarte
                key={`g:${e.gruppe.id}`}
                gruppe={e.gruppe}
                onClick={() => {
                  const g = e.gruppe;
                  if (!g) return;
                  setAktiv(null);
                  setAktiveGruppeId(g.id);
                }}
              />
            ) : e.kontakt ? (
              <KontaktKarte
                key={`k:${e.kontakt.id}`}
                kontakt={e.kontakt}
                onClick={() => {
                  const k = e.kontakt;
                  if (!k) return;
                  setAktiveGruppeId(null);
                  setAktiv(k);
                }}
              />
            ) : null,
          )}
        </div>
      )}

      {aktiv && (
        <Fenster
          titel={aktiv.alias}
          unterzeile={aktiv.echterName && aktiv.echterName !== aktiv.alias ? aktiv.echterName : undefined}
          kennung={`chat:${aktiv.id}`}
          offen={true}
          onSchliessen={chatSchliessen}
        >
          <div className="msg-huelle msg-gm-chat">
            <MessengerChat
              campaignId={campaignId}
              kontakt={aktiv}
              imFenster
              onZurueck={chatSchliessen}
              onGeaendert={onKontakteAktualisieren}
            />
          </div>
        </Fenster>
      )}

      {aktiveGruppeId && (
        <Fenster
          titel={gruppen.find((g) => g.id === aktiveGruppeId)?.name || "Gruppenchat"}
          unterzeile="Gruppenchat"
          kennung={`gruppe:${aktiveGruppeId}`}
          offen={true}
          onSchliessen={chatSchliessen}
        >
          <div className="msg-huelle msg-gm-chat">
            <GruppenChat campaignId={campaignId} gruppeId={aktiveGruppeId} onGeaendert={() => void gruppenLaden()} />
          </div>
        </Fenster>
      )}

      {mitspielerOffen && (
        <MitspielerFenster campaignId={campaignId} onSchliessen={() => setMitspielerOffen(false)} />
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

/** Eine Gruppe in der Liste: Name, wer drin ist, Ungelesen-Zähler. */
function GruppenKarte({ gruppe, onClick }: { gruppe: Gruppe; onClick: () => void }) {
  const andere = gruppe.teilnehmer.filter((t) => !t.ich);
  return (
    <div className="msg-kontakt msg-kontakt-gruppe" onClick={onClick}>
      <div className="msg-portrait">
        <span className="msg-portrait-leer">◍◍</span>
        {gruppe.ungelesen > 0 && <span className="msg-badge">{gruppe.ungelesen}</span>}
      </div>
      <div className="msg-info">
        <span className="msg-name">{gruppe.name}</span>
        <span className="msg-vorschau">{andere.map((t) => t.name).join(" · ")}</span>
      </div>
      <span className="msg-zeit">▶</span>
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
        {kontakt.echterName && kontakt.echterName !== kontakt.alias && (
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
  imFenster = false,
  onZurueck,
  onGeaendert,
}: {
  campaignId: string;
  kontakt: Kontakt;
  /** Wenn true, kann der Spieler nicht antworten. */
  nurLesen?: boolean;
  /** Im Popup (`Fenster`): Name und Schließen stecken schon in der Fensterleiste — keine eigene Kopfzeile. */
  imFenster?: boolean;
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

  const inhalt = (
      <div className="msg-chat">
        {/* Header */}
        {!imFenster && (
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
        )}

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
  );

  // Im Popup liefert der Aufrufer die Hülle (`msg-huelle msg-gm-chat`); sonst bringt der Chat seine mit.
  return imFenster ? inhalt : <div className="msg-huelle">{inhalt}</div>;
}

/**
 * Einzelne Nachricht im Persona-5-Stil.
 *
 * `absender` überschreibt den Namen über der Blase, `initial` den Buchstaben
 * im Portrait-Platzhalter — die SL-Ansicht braucht beides, weil dort die
 * Gegenseite der PC ist (die API liefert für die SL den NPC-Alias).
 */
export function NachrichtBlase({
  nachricht,
  bildUrl,
  absender,
  initial = "?",
  absenderImmer = false,
}: {
  nachricht: Nachricht;
  bildUrl?: string;
  absender?: string;
  initial?: string;
  /** Den Namen auch über eigenen (rechten) Blasen zeigen — SL im Gruppenchat. */
  absenderImmer?: boolean;
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
          {initial}
        </span>
      )}

      <div className="msg-blase" style={{ "--msg-schraeg": `${schraeg}px` } as CSSProperties}>
        {(!nachricht.vonMir || absenderImmer) && (absender ?? nachricht.absender) && (
          <span className="msg-absender">{absender ?? nachricht.absender}</span>
        )}
        <span className="msg-text">{alsText(nachricht.inhalt)}</span>
        <span className="msg-uhrzeit">{zeit}</span>
      </div>
    </div>
  );
}

export { MessengerChat };
