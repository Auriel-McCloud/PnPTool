/**
 * SL-Beratungschat in der Ideenschmiede.
 *
 * Redet über die freigegebene Kampagne, legt nichts an, bis „Entwurf
 * anlegen“. Entwürfe bleiben istEntwurf — der nächste Chat sieht sie nicht,
 * bis die SL sie freigibt.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import {
  beratungEntwurf,
  beratungLaden,
  beratungListe,
  beratungLoeschen,
  beratungNachricht,
  beratungNeu,
  type Beratung,
  type BeratungNachricht,
} from "./api";
import type { KiTyp } from "../ideenschmiede/api";
import "./ki.css";

export function BeratungPopup({
  offen,
  campaignId,
  onSchliessen,
  onEntwurf,
}: {
  offen: boolean;
  campaignId: string;
  onSchliessen: () => void;
  onEntwurf: () => void;
}) {
  const [liste, setListe] = useState<Beratung[]>([]);
  const [aktiv, setAktiv] = useState<Beratung | null>(null);
  const [eingabe, setEingabe] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [entwurfOffen, setEntwurfOffen] = useState(false);
  const [entwurfTyp, setEntwurfTyp] = useState<KiTyp>("charakter");
  const [entwurfLaeuft, setEntwurfLaeuft] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  // Überschreibt für diese eine Unterhaltung den Kampagnen-Standard — zum
  // direkten Vergleich, ohne die Kampagnen-Einstellung extra umzustellen.
  const [providerOverride, setProviderOverride] = useState<"" | "gemini" | "mistral">("");
  const endeRef = useRef<HTMLDivElement | null>(null);

  const listeLaden = useCallback(async () => {
    const daten = await beratungListe(campaignId);
    setListe(daten);
    return daten;
  }, [campaignId]);

  useEffect(() => {
    if (!offen) return;
    setFehler(null);
    setEingabe("");
    void listeLaden().then((daten) => {
      if (daten[0]) {
        return beratungLaden(campaignId, daten[0].id).then(setAktiv);
      }
      setAktiv(null);
    });
  }, [offen, campaignId, listeLaden]);

  useEffect(() => {
    endeRef.current?.scrollIntoView({ block: "end" });
  }, [aktiv?.nachrichten, laeuft]);

  async function neu() {
    setFehler(null);
    const angelegt = await beratungNeu(campaignId);
    setAktiv(angelegt);
    await listeLaden();
  }

  async function waehlen(id: string) {
    setFehler(null);
    setAktiv(await beratungLaden(campaignId, id));
  }

  async function senden() {
    const text = eingabe.trim();
    if (!text || laeuft) return;
    setLaeuft(true);
    setFehler(null);
    try {
      let thread = aktiv;
      if (!thread) {
        thread = await beratungNeu(campaignId);
        setAktiv(thread);
      }
      const optimistic: BeratungNachricht = {
        id: "tmp-user",
        rolle: "user",
        text,
        zeitpunkt: new Date().toISOString(),
        reihenfolge: (thread.nachrichten?.length ?? 0),
      };
      setAktiv({
        ...thread,
        nachrichten: [...(thread.nachrichten ?? []), optimistic],
      });
      setEingabe("");
      const antwort = await beratungNachricht(campaignId, thread.id, text, providerOverride);
      const frisch = await beratungLaden(campaignId, thread.id);
      setAktiv(frisch);
      void listeLaden();
      void antwort;
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Senden fehlgeschlagen");
      if (aktiv) {
        setAktiv(await beratungLaden(campaignId, aktiv.id).catch(() => aktiv));
      }
    } finally {
      setLaeuft(false);
    }
  }

  async function entwurfAnlegen() {
    if (!aktiv) return;
    setEntwurfLaeuft(true);
    setFehler(null);
    try {
      await beratungEntwurf(campaignId, aktiv.id, entwurfTyp);
      setEntwurfOffen(false);
      onEntwurf();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Entwurf fehlgeschlagen");
    } finally {
      setEntwurfLaeuft(false);
    }
  }

  async function loeschen() {
    if (!aktiv) return;
    await beratungLoeschen(campaignId, aktiv.id);
    setLoeschenOffen(false);
    setAktiv(null);
    const daten = await listeLaden();
    if (daten[0]) setAktiv(await beratungLaden(campaignId, daten[0].id));
  }

  const nachrichten = aktiv?.nachrichten ?? [];
  const hatGespraech = nachrichten.length > 0;

  return (
    <>
      <Fenster
        offen={offen}
        titel="⌬ Beratung"
        unterzeile="Nur Freigegebenes ist Kanon. Entwurf erst auf Knopf."
        kennung="ideenschmiede-beratung"
        onSchliessen={onSchliessen}
      >
        <div className="ki-popup ki-beratung">
          <div className="ki-b-threads">
            <button type="button" className="ki-btn-sekundaer" onClick={() => void neu()}>
              + Neu
            </button>
            {/* Nur für diese Unterhaltung — überschreibt den Kampagnen-Standard
                aus den Einstellungen, zum direkten Vergleich. */}
            <select
              className="ki-input"
              value={providerOverride}
              onChange={(e) => setProviderOverride(e.target.value as "" | "gemini" | "mistral")}
              title="Nur für diese Unterhaltung — Standard ist der Kampagnen-Einstellung überlassen."
              style={{ width: "auto", minWidth: 0 }}
            >
              <option value="">Standard</option>
              <option value="gemini">Gemini</option>
              <option value="mistral">Mistral</option>
            </select>
            {liste.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`ki-b-chip${aktiv?.id === t.id ? " ki-b-chip-aktiv" : ""}`}
                onClick={() => void waehlen(t.id)}
              >
                {t.titel || "Neue Beratung"}
              </button>
            ))}
          </div>

          <div className="ki-b-verlauf">
            {nachrichten.length === 0 && (
              <p className="ki-vorschau-hinweis">
                Frag, skizziere, verwirf. Nichts davon wird Welt, bis du unten
                einen Entwurf anlegst.
              </p>
            )}
            {nachrichten.map((n) => (
              <div
                key={n.id}
                className={n.rolle === "user" ? "ki-b-blase ki-b-user" : "ki-b-blase ki-b-bot"}
              >
                {n.text}
              </div>
            ))}
            {laeuft && <div className="ki-b-blase ki-b-bot ki-b-wartet">denkt…</div>}
            <div ref={endeRef} />
          </div>

          {fehler && <p className="ki-fehler">{fehler}</p>}

          <label className="ki-label">
            Nachricht
            <textarea
              className="ki-input"
              rows={3}
              style={{ resize: "vertical", minHeight: 64, width: "100%" }}
              placeholder="z.B. Passt ein Club im Hafenviertel zu Chrysalis?"
              value={eingabe}
              onChange={(e) => setEingabe(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void senden();
                }
              }}
              disabled={laeuft}
            />
          </label>

          <div className="ki-aktionen">
            <button
              type="button"
              className="ki-btn-primaer"
              disabled={laeuft || !eingabe.trim()}
              onClick={() => void senden()}
            >
              {laeuft ? "…" : "Senden"}
            </button>
            <button
              type="button"
              className="ki-btn-sekundaer"
              disabled={!hatGespraech || laeuft}
              onClick={() => setEntwurfOffen(true)}
            >
              Entwurf anlegen
            </button>
            {aktiv && (
              <button
                type="button"
                className="ki-btn-sekundaer"
                disabled={laeuft}
                onClick={() => setLoeschenOffen(true)}
              >
                Löschen
              </button>
            )}
          </div>
        </div>
      </Fenster>

      <Fenster
        offen={entwurfOffen}
        titel="Entwurf aus Beratung"
        kennung="ideenschmiede-beratung-entwurf"
        onSchliessen={() => setEntwurfOffen(false)}
      >
        <div className="ki-popup">
          <label className="ki-label">
            Was soll entstehen?
            <select
              className="ki-input"
              value={entwurfTyp}
              onChange={(e) => setEntwurfTyp(e.target.value as KiTyp)}
            >
              <option value="charakter">Person / NPC</option>
              <option value="story">Story-Part / Szene</option>
              <option value="gegenstand">Gegenstand</option>
              <option value="ort">Ort</option>
              <option value="event">Ereignis</option>
              <option value="fraktion">Fraktion</option>
              <option value="verbindung">Verbindung</option>
            </select>
          </label>
          <p className="ki-vorschau-hinweis">
            {entwurfTyp === "verbindung"
              ? "Landet als Kante unter Beziehungen. Fehlende Personen/Orte/Events/Fraktionen werden als Entwurf angelegt."
              : "Landet als Entwurf in der Schmiede, nicht in der Kampagne."}
          </p>
          {fehler && <p className="ki-fehler">{fehler}</p>}
          <div className="ki-aktionen">
            <button
              type="button"
              className="ki-btn-primaer"
              disabled={entwurfLaeuft}
              onClick={() => void entwurfAnlegen()}
            >
              {entwurfLaeuft ? "Legt an…" : "Anlegen"}
            </button>
            <button type="button" className="ki-btn-sekundaer" onClick={() => setEntwurfOffen(false)}>
              Abbrechen
            </button>
          </div>
        </div>
      </Fenster>

      {loeschenOffen && (
        <Bestaetigung
          titel="Beratung löschen?"
          text="Das Gespräch ist danach weg. In der Kampagne ändert sich nichts."
          jaText="Löschen"
          onJa={() => void loeschen()}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}
