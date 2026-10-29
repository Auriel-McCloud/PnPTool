import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { entitiesApi, type Person } from "../entities/api";
import { itemsApi, type Gegenstand, type GegenstandMitBesitzer } from "../items/api";
import { drohnenApi, type DrohnenEintrag, type MakerProbenErgebnis, type ReparaturProbePool } from "../drohnen/api";
import { verhandlungApi } from "../verhandlung/api";
import "../verhandlung/verhandlung.css";
import "../traits/levelup.css";
import "../items/wegwerfen.css";

export type ReparaturZielTyp = "ruestung" | "drohne" | "fahrzeug";

/** Ein Ziel für das Reparatur-Burgermenü — entweder ein Rüstungs-Gegenstand
 * oder eine Drohne/ein Fahrzeug (Gesundheitsschaden statt Kästchen-Feld). */
export interface ReparaturZiel {
  typ: ReparaturZielTyp;
  id: string;
  name: string;
  /** Nur Rüstung: Besitzer-Person für den Händler-Weg. */
  besitzerId?: string | null;
}

/** Qualitätsstufen-Gruppe mit Gesamtmenge, Repräsentant trägt die konkrete
 * Gegenstands-Id, mit der tatsächlich bezahlt wird (Muster aus
 * DrohnenSteigern.tsx::materialGruppenFuer). */
function materialGruppen(material: Gegenstand[]): { qualitaet: string; menge: number; repraesentant: Gegenstand }[] {
  const nachQualitaet = new Map<string, Gegenstand[]>();
  for (const m of material) {
    if (!m.istMaschinenteil || m.menge <= 0) continue;
    const liste = nachQualitaet.get(m.maschinenteilQualitaet) ?? [];
    liste.push(m);
    nachQualitaet.set(m.maschinenteilQualitaet, liste);
  }
  return [...nachQualitaet.entries()].map(([qualitaet, stuecke]) => ({
    qualitaet,
    menge: stuecke.reduce((s, m) => s + (m.hatMenge ? m.menge : 1), 0),
    repraesentant: stuecke[0],
  }));
}

/**
 * Reparatur-Popup für EIN gewähltes Ziel (Rüstung ODER Drohne/Fahrzeug) —
 * siehe docs/wiki/concepts/drohnen-fahrzeuge.md "Reparatur" für die volle
 * Spec. Zwei Wege:
 *
 * - **Selbst** (Material + selbstberichtete Probe, wie die Maker-Probe beim
 *   Drohnen-Umbau): Qualitätsstufe wählen, Menge wählen, Pool+benötigte
 *   Erfolge anzeigen, danach Erfolg/Misserfolg/Patzer melden.
 * - **Händler** (Nuyen + Verhandlung) — **nur für Rüstung gebaut**, nur
 *   wählbar, wenn ein Händler mit `bietetReparatur` ausgewählt ist. Für
 *   Drohne/Fahrzeug noch nicht gebaut (siehe Wiki, "Noch offen").
 */
export function ReparaturFenster({
  campaignId,
  ziel,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  ziel: ReparaturZiel;
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const istRuestung = ziel.typ === "ruestung";
  const [weg, setWeg] = useState<"selbst" | "haendler">("selbst");

  // --- Selbst reparieren ---------------------------------------------
  const [material, setMaterial] = useState<Gegenstand[]>([]);
  const [materialLaedt, setMaterialLaedt] = useState(true);
  const [qualitaet, setQualitaet] = useState<string | null>(null);
  const [menge, setMenge] = useState(1);
  const [skill, setSkill] = useState<string>(ziel.typ === "fahrzeug" ? "Handwerk" : istRuestung ? "Handwerk" : "Maker (Hardware)");
  const [pool, setPool] = useState<ReparaturProbePool | null>(null);
  const [poolLaedt, setPoolLaedt] = useState(false);
  const [gewaehltesAttribut, setGewaehltesAttribut] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnisText, setErgebnisText] = useState<string | null>(null);

  // --- Beim Händler (nur Rüstung) --------------------------------------
  const [haendlerListe, setHaendlerListe] = useState<Person[]>([]);
  const [gewaehlterHaendler, setGewaehlterHaendler] = useState<string>("");
  const [preisLaedt, setPreisLaedt] = useState(false);
  const [preisVorschlag, setPreisVorschlag] = useState<number | null>(null);
  const [deckel, setDeckel] = useState<number | null>(null);
  const [fehlendeKaestchenHaendler, setFehlendeKaestchenHaendler] = useState(0);
  const [angebotLaeuft, setAngebotLaeuft] = useState(false);
  const [angebotGesendet, setAngebotGesendet] = useState(false);
  const [haendlerFehler, setHaendlerFehler] = useState<string | null>(null);

  const gruppen = useMemo(() => materialGruppen(material), [material]);
  const gewaehlteGruppe = gruppen.find((g) => g.qualitaet === qualitaet) ?? null;
  const skillOptionen = ziel.typ === "fahrzeug" ? ["Handwerk", "Maker (Hardware)"] : null;

  function ladeMaterial() {
    setMaterialLaedt(true);
    const anfrage =
      ziel.typ === "ruestung"
        ? itemsApi.ruestungMaschinenteile(campaignId, ziel.id)
        : drohnenApi.maschinenteile(campaignId, ziel.id);
    anfrage
      .then((liste) => {
        setMaterial(liste);
        setQualitaet((alt) => (alt && liste.some((m) => m.maschinenteilQualitaet === alt && m.menge > 0) ? alt : null));
      })
      .catch(() => setMaterial([]))
      .finally(() => setMaterialLaedt(false));
  }

  useEffect(() => {
    if (weg !== "selbst") return;
    ladeMaterial();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weg, campaignId, ziel.id]);

  useEffect(() => {
    if (weg !== "selbst" || !gewaehlteGruppe) {
      setPool(null);
      return;
    }
    setPoolLaedt(true);
    setFehler(null);
    const anfrage =
      ziel.typ === "ruestung"
        ? itemsApi.ruestungReparaturPool(campaignId, ziel.id, gewaehlteGruppe.repraesentant.id, menge)
        : drohnenApi.reparaturPool(campaignId, ziel.id, skill, gewaehlteGruppe.repraesentant.id, menge);
    anfrage
      .then((p) => {
        setPool(p);
        setGewaehltesAttribut((alt) => (alt && p.attribute.some((a) => a.name === alt) ? alt : null));
      })
      .catch((e) => setFehler(e instanceof Error ? e.message : "Pool konnte nicht geladen werden"))
      .finally(() => setPoolLaedt(false));
  }, [weg, campaignId, ziel.id, ziel.typ, gewaehlteGruppe, menge, skill]);

  useEffect(() => {
    if (weg !== "haendler" || !istRuestung) return;
    entitiesApi
      .listPersonen(campaignId)
      .then((liste) => setHaendlerListe(liste.filter((p) => p.istHaendler && p.bietetReparatur)))
      .catch(() => setHaendlerListe([]));
  }, [weg, campaignId, istRuestung]);

  useEffect(() => {
    if (weg !== "haendler" || !gewaehlterHaendler || !istRuestung) return;
    setPreisLaedt(true);
    setHaendlerFehler(null);
    itemsApi
      .ruestungReparaturPreis(campaignId, ziel.id)
      .then((antwort) => {
        setPreisVorschlag(antwort.preis);
        setDeckel(antwort.deckel);
        setFehlendeKaestchenHaendler(antwort.fehlendeKaestchen);
      })
      .catch((e) => setHaendlerFehler(e instanceof Error ? e.message : "Preis konnte nicht berechnet werden"))
      .finally(() => setPreisLaedt(false));
  }, [weg, campaignId, ziel.id, gewaehlterHaendler, istRuestung]);

  const attributWert = gewaehltesAttribut ? (pool?.attribute.find((a) => a.name === gewaehltesAttribut)?.wert ?? 0) : null;
  const poolGroesse = pool && attributWert != null ? pool.skillWert + attributWert : null;

  async function melden(ergebnis: MakerProbenErgebnis) {
    if (!gewaehlteGruppe) return;
    setLaeuft(true);
    setFehler(null);
    try {
      if (ziel.typ === "ruestung") {
        const r = await itemsApi.ruestungReparierenMaterial(campaignId, ziel.id, gewaehlteGruppe.repraesentant.id, menge, ergebnis);
        setErgebnisText(ergebnisMeldung(ergebnis, r.repariert, r.materialName));
      } else {
        const r = await drohnenApi.reparierenMaterial(campaignId, ziel.id, gewaehlteGruppe.repraesentant.id, menge, ergebnis);
        setErgebnisText(ergebnisMeldung(ergebnis, r.repariert, r.materialName));
      }
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Reparatur fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  function ergebnisMeldung(ergebnis: MakerProbenErgebnis, repariert: number, materialName: string): string {
    if (ergebnis === "ja") return `Geschafft! ${repariert} Kästchen repariert, ${materialName} verbraucht.`;
    if (ergebnis === "patzer") return `Patzer — ${materialName} ist verbraucht, keine Reparatur.`;
    return `Nicht geschafft — ${materialName} bleibt, keine Reparatur. Später erneut versuchen.`;
  }

  async function angebotSenden() {
    if (preisVorschlag == null || !ziel.besitzerId) return;
    setAngebotLaeuft(true);
    setHaendlerFehler(null);
    try {
      await verhandlungApi.anbieten(campaignId, {
        empfaengerPersonId: ziel.besitzerId,
        art: "RUESTUNG_REPARATUR",
        positionen: [{ bezeichnung: `Reparatur: ${ziel.name}`, betrag: preisVorschlag }],
        kontext: { gegenstandId: ziel.id, kaestchen: fehlendeKaestchenHaendler },
      });
      setAngebotGesendet(true);
    } catch (e) {
      setHaendlerFehler(e instanceof Error ? e.message : "Angebot konnte nicht gesendet werden");
    } finally {
      setAngebotLaeuft(false);
    }
  }

  return (
    <Fenster offen titel={`Reparatur: ${ziel.name}`} kennung={`reparatur:${ziel.id}`} onSchliessen={onSchliessen}>
      <div className="rr-wahl">
        <button type="button" aria-pressed={weg === "selbst"} onClick={() => setWeg("selbst")}>
          Selbst reparieren
        </button>
        {istRuestung && (
          <button type="button" aria-pressed={weg === "haendler"} onClick={() => setWeg("haendler")}>
            Beim Händler
          </button>
        )}
      </div>

      {weg === "selbst" && (
        <div className="rr-abschnitt">
          {materialLaedt && <p style={{ color: "var(--text-leise)" }}>Maschinenteile werden geladen…</p>}
          {!materialLaedt && gruppen.length === 0 && (
            <p style={{ color: "var(--text-leise)" }}>
              Kein Maschinenteil im Besitz — als "Maschinenteil" markieren lässt sich jeder Gegenstand über dessen
              eigenes Bearbeiten-Formular (Optionen).
            </p>
          )}
          {gruppen.length > 0 && (
            <div className="lu-zahlart" style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
              {gruppen.map((g) => (
                <button
                  key={g.qualitaet}
                  type="button"
                  className="lu-zahlart-knopf"
                  data-aktiv={qualitaet === g.qualitaet}
                  onClick={() => {
                    setQualitaet(g.qualitaet);
                    setMenge(1);
                    setErgebnisText(null);
                  }}
                >
                  {g.qualitaet || "unbekannt"} ×{g.menge}
                </button>
              ))}
            </div>
          )}

          {gewaehlteGruppe && (
            <div className="lu-hinweis" style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <label>Menge einsetzen</label>
              <input
                type="number"
                min={1}
                max={gewaehlteGruppe.menge}
                value={menge}
                onChange={(e) => setMenge(Math.max(1, Math.min(gewaehlteGruppe.menge, Number(e.target.value))))}
                style={{ width: 70 }}
              />
              {gewaehlteGruppe.qualitaet === "hochwertig" && (
                <span style={{ fontSize: "0.8em", color: "var(--text-leise)" }}>1 Stück repariert vollständig</span>
              )}
            </div>
          )}

          {skillOptionen && gewaehlteGruppe && (
            <div className="lu-zahlart" style={{ display: "flex", gap: 4, marginBottom: 10 }}>
              {skillOptionen.map((s) => (
                <button key={s} type="button" className="lu-zahlart-knopf" data-aktiv={skill === s} onClick={() => setSkill(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {poolLaedt && <p style={{ color: "var(--text-leise)" }}>Pool wird berechnet…</p>}

          {!poolLaedt && pool && !ergebnisText && (
            <>
              <p className="lu-hinweis">
                {pool.skill}: <strong>{pool.skillWert}</strong> — wähle dazu ein Attribut, mit dem du würfelst.
                {pool.fehlendeKaestchen > 0 && ` Es fehlen ${pool.fehlendeKaestchen} Kästchen.`}
              </p>
              <div className="lu-zahlart" style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
                {pool.attribute.map((a) => (
                  <button
                    key={a.name}
                    type="button"
                    className="lu-zahlart-knopf"
                    data-aktiv={gewaehltesAttribut === a.name}
                    onClick={() => setGewaehltesAttribut(a.name)}
                  >
                    {a.name} {a.wert}
                  </button>
                ))}
              </div>

              {poolGroesse != null && (
                <p className="lu-hinweis">
                  Pool: <strong>{pool.skillWert} + {attributWert}</strong> = <strong>{poolGroesse}</strong> Würfel. Du
                  brauchst <strong>{pool.benoetigteErfolge}</strong> Erfolge, Heilung bei Erfolg:{" "}
                  <strong>{pool.heilungBeiErfolg}</strong> Kästchen.
                </p>
              )}

              {fehler && <p className="rr-fehler">{fehler}</p>}

              <p className="lu-hinweis" style={{ marginTop: 10 }}>Am Tisch gewürfelt — geschafft?</p>
              <div className="ww-knoepfe">
                <button type="button" className="ww-behalten" disabled={laeuft || !gewaehltesAttribut} onClick={() => melden("ja")}>
                  ✓ Ja
                </button>
                <button type="button" disabled={laeuft || !gewaehltesAttribut} onClick={() => melden("nein")}>
                  ✗ Nein
                </button>
                <button
                  type="button"
                  style={{ color: "var(--nein)", borderColor: "var(--nein)" }}
                  disabled={laeuft || !gewaehltesAttribut}
                  onClick={() => melden("patzer")}
                >
                  ⚡ Patzer
                </button>
              </div>
            </>
          )}

          {ergebnisText && (
            <>
              <p className="ww-beruhigung">{ergebnisText}</p>
              <div className="ww-knoepfe">
                <button type="button" className="ww-behalten" onClick={() => { setErgebnisText(null); setQualitaet(null); ladeMaterial(); }}>
                  Weiter
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {weg === "haendler" && istRuestung && (
        <div className="rr-abschnitt">
          {haendlerListe.length === 0 && (
            <p style={{ color: "var(--text-leise)" }}>
              Kein Händler mit "Bietet Reparatur" markiert — Flag am NPC im Händler-Steckbrief setzen.
            </p>
          )}
          {haendlerListe.length > 0 && (
            <div className="lu-zahlart" style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
              {haendlerListe.map((h) => (
                <button
                  key={h.id}
                  type="button"
                  className="lu-zahlart-knopf"
                  data-aktiv={gewaehlterHaendler === h.id}
                  onClick={() => setGewaehlterHaendler(h.id)}
                >
                  {h.name}
                </button>
              ))}
            </div>
          )}

          {gewaehlterHaendler && (
            <>
              {preisLaedt && <p style={{ color: "var(--text-leise)" }}>Preis wird berechnet…</p>}
              {!preisLaedt && preisVorschlag != null && !angebotGesendet && (
                <>
                  <div className="rr-preis-zeile">
                    <label style={{ fontSize: "0.9em" }}>Vorschlag</label>
                    <input
                      type="number"
                      min={0}
                      className="rr-preis-eingabe"
                      value={preisVorschlag}
                      onChange={(e) => setPreisVorschlag(Math.max(0, Number(e.target.value)))}
                    />
                    <span>¥</span>
                  </div>
                  {deckel != null && (
                    <p className="rr-preis-deckel-hinweis">
                      Deckel bei Totalschaden: {deckel.toLocaleString("de-AT")}¥ (75 % vom Neuwert)
                    </p>
                  )}
                  <button type="button" disabled={angebotLaeuft} onClick={angebotSenden}>
                    {angebotLaeuft ? "Sendet…" : "Angebot an Spieler senden"}
                  </button>
                </>
              )}
              {angebotGesendet && (
                <p style={{ color: "var(--gut)" }}>
                  Angebot über {preisVorschlag?.toLocaleString("de-AT")}¥ gesendet — wartet auf Antwort.
                </p>
              )}
              {haendlerFehler && <p className="rr-fehler">{haendlerFehler}</p>}
            </>
          )}
        </div>
      )}

      {weg === "haendler" && !istRuestung && (
        <p style={{ color: "var(--text-leise)" }}>
          Der Händler-Weg (Nuyen + Verhandlung) ist für Drohnen/Fahrzeuge noch nicht gebaut — bisher nur Selbst-Reparieren.
        </p>
      )}
    </Fenster>
  );
}

export type { Gegenstand, GegenstandMitBesitzer, DrohnenEintrag };
