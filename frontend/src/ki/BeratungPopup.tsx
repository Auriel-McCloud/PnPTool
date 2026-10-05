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
import { entitiesApi } from "../entities/api";
import {
  beratungEntwurf,
  beratungLaden,
  beratungListe,
  beratungLoeschen,
  beratungMassenentwurf,
  beratungNachricht,
  beratungNeu,
  massenjobStatus,
  type Beratung,
  type BeratungNachricht,
  type MassenErgebnis,
  type MassenTyp,
  type MassenZielTyp,
} from "./api";
import type { KiTyp } from "../ideenschmiede/api";
import "./ki.css";

/** Typen, für die die Massen-Anlage angeboten wird — deckungsgleich mit
 * MassenTyp im Backend (Mark: Gegenstände/NPCs/Orte zuerst, 03.10.2026). */
const MASSEN_TYPEN: readonly string[] = ["gegenstand", "charakter", "ort"];

interface ZielOption {
  id: string;
  label: string;
}

async function ladeZielOptionen(campaignId: string, zielTyp: MassenZielTyp): Promise<ZielOption[]> {
  if (zielTyp === "Person") {
    const liste = await entitiesApi.listPersonen(campaignId);
    return liste.map((p) => ({ id: p.id, label: p.istHaendler ? `${p.name} (Händler)` : p.name }));
  }
  if (zielTyp === "Ort") {
    const liste = await entitiesApi.listOrte(campaignId);
    return liste.map((o) => ({ id: o.id, label: o.name }));
  }
  if (zielTyp === "Event") {
    const liste = await entitiesApi.listEvents(campaignId);
    return liste.map((e) => ({ id: e.id, label: e.title }));
  }
  const liste = await entitiesApi.listFraktionen(campaignId);
  return liste.map((f) => ({ id: f.id, label: f.name }));
}

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
  // Massen-Anlage (03.10.2026): "N unterschiedliche Entwürfe statt einem",
  // nur für MASSEN_TYPEN anbieten — siehe ladeZielOptionen/massenAnlegen unten.
  const [massenModus, setMassenModus] = useState(false);
  // Anzahl-Feld (05.10.2026, Mark-Bug): nicht direkt als number führen, sonst
  // clamped onChange bei JEDER Eingabe sofort auf den Min-/Max-Wert zurück —
  // ein geleertes Feld wird augenblicklich wieder zu "1", man kann die
  // führende Ziffer nie ersetzen, nur noch Ziffern anhängen (1, 10, 11, 12…).
  // Rohtext separat halten, der echte (geclampte) Wert ist abgeleitet; erst
  // beim Verlassen des Feldes (onBlur) wird der Rohtext normalisiert.
  const [massenAnzahlEingabe, setMassenAnzahlEingabe] = useState("5");
  const massenAnzahl = Math.max(1, Math.min(12, parseInt(massenAnzahlEingabe, 10) || 1));
  const [massenZielTyp, setMassenZielTyp] = useState<"" | MassenZielTyp>("");
  const [massenZielId, setMassenZielId] = useState("");
  const [massenBeziehungstyp, setMassenBeziehungstyp] = useState("");
  const [zielOptionen, setZielOptionen] = useState<ZielOption[]>([]);
  const [massenErgebnis, setMassenErgebnis] = useState<MassenErgebnis | null>(null);
  // Fortschritt des Hintergrund-Jobs (05.10.2026, siehe massenAnlegen unten)
  // — null solange kein Job läuft, sonst "X von Y" fürs Knopf-Label.
  const [massenFortschritt, setMassenFortschritt] = useState<{ erstellt: number; gesamt: number } | null>(null);
  // Zählt bei jedem massenAnlegen()-Aufruf UND beim Abbrechen/Unmount hoch —
  // eine laufende Polling-Schleife prüft das vor jedem setState und bricht
  // sich selbst ab, sobald ihre eigene Generation nicht mehr die aktuelle
  // ist. Der Hintergrund-Job selbst läuft davon unberührt weiter (das ist ja
  // der Witz); es geht nur darum, keine veralteten Zustände mehr anzuzeigen.
  const massenJobGeneration = useRef(0);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  // Überschreibt für diese eine Unterhaltung den Kampagnen-Standard — zum
  // direkten Vergleich, ohne die Kampagnen-Einstellung extra umzustellen.
  const [providerOverride, setProviderOverride] = useState<"" | "gemini" | "mistral">("");
  const endeRef = useRef<HTMLDivElement | null>(null);

  // Stoppt eine laufende Fortschritts-Abfrage beim Schließen des Popups oder
  // Verlassen der Seite — der Hintergrund-Job selbst läuft serverseitig
  // unbeeindruckt weiter, das hier verhindert nur sinnlose weitere Polls.
  useEffect(() => {
    return () => {
      massenJobGeneration.current++;
    };
  }, []);

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

  // Zurücksetzen, sobald das Popup zugeht oder der Typ wechselt — sonst
  // hängt ein Ziel aus "Gegenstand" noch an, wenn man auf "Ort" wechselt.
  useEffect(() => {
    if (!entwurfOffen) {
      setMassenModus(false);
      setMassenErgebnis(null);
    }
  }, [entwurfOffen]);

  useEffect(() => {
    setMassenZielTyp("");
    setMassenZielId("");
    setMassenBeziehungstyp("");
    setMassenErgebnis(null);
    if (!MASSEN_TYPEN.includes(entwurfTyp)) setMassenModus(false);
  }, [entwurfTyp]);

  useEffect(() => {
    setMassenZielId("");
    if (!massenZielTyp) {
      setZielOptionen([]);
      return;
    }
    let aktuelleAnfrage = true;
    void ladeZielOptionen(campaignId, massenZielTyp).then((optionen) => {
      if (aktuelleAnfrage) setZielOptionen(optionen);
    });
    return () => {
      aktuelleAnfrage = false;
    };
  }, [campaignId, massenZielTyp]);

  async function massenAnlegen() {
    if (!aktiv) return;
    const generation = ++massenJobGeneration.current;
    setEntwurfLaeuft(true);
    setFehler(null);
    setMassenErgebnis(null);
    setMassenFortschritt(null);
    try {
      const ziel =
        massenZielTyp && massenZielId
          ? { zielTyp: massenZielTyp, zielId: massenZielId, beziehungstyp: massenBeziehungstyp }
          : undefined;
      const gestartet = await beratungMassenentwurf(
        campaignId,
        aktiv.id,
        entwurfTyp as MassenTyp,
        massenAnzahl,
        ziel,
      );
      if (massenJobGeneration.current !== generation) return; // abgebrochen/weitergeklickt
      setMassenFortschritt({ erstellt: 0, gesamt: gestartet.gesamt });

      // Die eigentliche Erzeugung läuft jetzt serverseitig weiter, komplett
      // unabhängig von dieser Browser-Verbindung (05.10.2026, Mark: "Failed
      // to fetch" auf Mobilfunk bei größeren Massen-Anlagen — vorher hing
      // die ganze Arbeit an genau dieser einen Anfrage, siehe massenjobs.py).
      // Hier wird nur noch der Fortschritt abgefragt, bis er fertig ist.
      while (massenJobGeneration.current === generation) {
        await new Promise((r) => setTimeout(r, 1500));
        if (massenJobGeneration.current !== generation) return;
        const stand = await massenjobStatus(campaignId, gestartet.jobId);
        if (massenJobGeneration.current !== generation) return;
        setMassenFortschritt({ erstellt: stand.erstellt, gesamt: stand.gesamt });
        if (stand.fertig) {
          if (stand.fehler) {
            setFehler(stand.fehler);
          } else if (stand.ergebnis) {
            setMassenErgebnis(stand.ergebnis);
            onEntwurf();
          }
          break;
        }
      }
    } catch (e) {
      if (massenJobGeneration.current === generation) {
        setFehler(e instanceof Error ? e.message : "Massen-Anlage fehlgeschlagen");
      }
    } finally {
      if (massenJobGeneration.current === generation) {
        setEntwurfLaeuft(false);
        setMassenFortschritt(null);
      }
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

          {MASSEN_TYPEN.includes(entwurfTyp) && !massenErgebnis && (
            <label className="ki-label" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={massenModus}
                onChange={(e) => setMassenModus(e.target.checked)}
              />
              Mehrere auf einmal anlegen (z.B. "5 Gegenstände von Händler X")
            </label>
          )}

          {massenModus && !massenErgebnis && (
            <>
              <label className="ki-label">
                Anzahl
                <input
                  type="number"
                  className="ki-input"
                  min={1}
                  max={12}
                  value={massenAnzahlEingabe}
                  onChange={(e) => setMassenAnzahlEingabe(e.target.value)}
                  onBlur={() => setMassenAnzahlEingabe(String(massenAnzahl))}
                />
              </label>
              <label className="ki-label">
                Verknüpfen mit (optional)
                <select
                  className="ki-input"
                  value={massenZielTyp}
                  onChange={(e) => setMassenZielTyp(e.target.value as "" | MassenZielTyp)}
                >
                  <option value="">Keine Verknüpfung</option>
                  <option value="Person">Person</option>
                  <option value="Ort">Ort</option>
                  <option value="Event">Ereignis</option>
                  <option value="Fraktion">Fraktion</option>
                </select>
              </label>
              {massenZielTyp && (
                <label className="ki-label">
                  Ziel
                  <select
                    className="ki-input"
                    value={massenZielId}
                    onChange={(e) => setMassenZielId(e.target.value)}
                  >
                    <option value="">— auswählen —</option>
                    {zielOptionen.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {massenZielTyp && massenZielId && entwurfTyp !== "gegenstand" && (
                <label className="ki-label">
                  Beziehung (optional, z.B. "arbeitet in")
                  <input
                    className="ki-input"
                    value={massenBeziehungstyp}
                    onChange={(e) => setMassenBeziehungstyp(e.target.value)}
                    placeholder="leer = sinnvoller Standard"
                  />
                </label>
              )}
              <p className="ki-vorschau-hinweis">
                {entwurfTyp === "gegenstand" && massenZielTyp === "Person"
                  ? "Landet im Sortiment, wenn das Ziel ein Händler ist — sonst wird die Ware direkt zugewiesen."
                  : entwurfTyp === "gegenstand" && massenZielTyp
                    ? "Für Orte/Ereignisse/Fraktionen gibt es noch keine automatische Verknüpfung für Gegenstände — sie landen trotzdem als Entwürfe."
                    : "Jeder Eintrag unterscheidet sich bewusst vom vorigen, keine Wiederholung."}
              </p>
            </>
          )}

          <p className="ki-vorschau-hinweis">
            {entwurfTyp === "verbindung"
              ? "Landet als Kante unter Beziehungen. Fehlende Personen/Orte/Events/Fraktionen werden als Entwurf angelegt."
              : "Landet als Entwurf in der Schmiede, nicht in der Kampagne."}
          </p>
          {massenModus && entwurfLaeuft && (
            <p className="ki-vorschau-hinweis">
              Läuft jetzt am Server weiter — auch wenn die Verbindung zwischendurch abbricht (z.B. Mobilfunk), geht
              nichts verloren. Einfach später nochmal reinschauen.
            </p>
          )}
          {fehler && <p className="ki-fehler">{fehler}</p>}

          {massenErgebnis && (
            <div className="ki-vorschau-hinweis">
              <strong>{massenErgebnis.eintraege.length} Entwürfe angelegt:</strong>
              <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>
                {massenErgebnis.eintraege.map((e) => (
                  <li key={e.id}>
                    {e.name}
                    {e.verknuepft ? " — verknüpft" : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="ki-aktionen">
            {massenErgebnis ? (
              <button type="button" className="ki-btn-primaer" onClick={() => setEntwurfOffen(false)}>
                Fertig
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="ki-btn-primaer"
                  disabled={entwurfLaeuft || (massenModus && !!massenZielTyp && !massenZielId)}
                  onClick={() => void (massenModus ? massenAnlegen() : entwurfAnlegen())}
                >
                  {entwurfLaeuft
                    ? massenFortschritt
                      ? `${massenFortschritt.erstellt} von ${massenFortschritt.gesamt}…`
                      : "Startet…"
                    : massenModus
                      ? `${massenAnzahl} anlegen`
                      : "Anlegen"}
                </button>
                <button
                  type="button"
                  className="ki-btn-sekundaer"
                  onClick={() => {
                    // Beendet nur das Mitverfolgen hier — ein bereits
                    // gestarteter Hintergrund-Job legt seine Einträge trotzdem
                    // fertig an (siehe massenAnlegen/massenjobs.py).
                    massenJobGeneration.current++;
                    setEntwurfOffen(false);
                  }}
                >
                  Abbrechen
                </button>
              </>
            )}
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
