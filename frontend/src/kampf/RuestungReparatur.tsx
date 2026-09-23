import { useEffect, useState } from "react";
import { itemsApi, type Gegenstand, type ReparaturWurf } from "../items/api";
import { verhandlungApi } from "../verhandlung/api";
import "../verhandlung/verhandlung.css";

/**
 * SL-seitige Reparatur-UI an einer Rüstung: Selbst reparieren (Hardware-Probe
 * + Material) oder beim Händler (Preisvorschlag über das Verhandlungs-Popup).
 *
 * Sitzt im Bearbeiten-Fenster von `GegenstandRow` (CharacterSheetPanel.tsx),
 * direkt unter dem Kästchen-Feld — nur bei Typ "Rüstung" mit
 * `ruestungKaestchenMax > 0` und nur, wenn tatsächlich etwas fehlt
 * (`ruestungKaestchenAktuell < ruestungKaestchenMax`). Unbeschädigte Rüstung
 * braucht keinen Reparatur-Knopf.
 *
 * **Nur SL** — wie die Routen selbst (`ruestung/reparieren-selbst` und
 * `ruestung/reparatur-preis` + `verhandlungen`-Anbieten sind GM-only, siehe
 * items/routes.py und verhandlung/routes.py).
 */
export function RuestungReparatur({
  campaignId,
  personId,
  item,
  onChanged,
}: {
  campaignId: string;
  /** Besitzer der Rüstung — Empfänger von Probe-Pool bzw. Verhandlungsangebot. */
  personId: string;
  item: Gegenstand;
  /** Nach erfolgreicher Selbst-Reparatur: Gegenstand neu laden. */
  onChanged: () => void;
}) {
  const [weg, setWeg] = useState<"selbst" | "haendler">("selbst");

  // --- Selbst reparieren ------------------------------------------------
  const [material, setMaterial] = useState<Gegenstand[]>([]);
  const [materialLaedt, setMaterialLaedt] = useState(false);
  const [gewaehltesMaterial, setGewaehltesMaterial] = useState<string>("");
  const [wuerfeltLaeuft, setWuerfeltLaeuft] = useState(false);
  const [wurf, setWurf] = useState<ReparaturWurf | null>(null);
  const [selbstFehler, setSelbstFehler] = useState<string | null>(null);

  // --- Beim Händler -------------------------------------------------------
  const [preisLaedt, setPreisLaedt] = useState(false);
  const [preisVorschlag, setPreisVorschlag] = useState<number | null>(null);
  const [deckel, setDeckel] = useState<number | null>(null);
  const [fehlendeKaestchen, setFehlendeKaestchen] = useState(0);
  const [angebotLaeuft, setAngebotLaeuft] = useState(false);
  const [angebotGesendet, setAngebotGesendet] = useState(false);
  const [haendlerFehler, setHaendlerFehler] = useState<string | null>(null);

  useEffect(() => {
    if (weg !== "selbst") return;
    setMaterialLaedt(true);
    itemsApi
      .reparaturmaterialListe(campaignId, item.id)
      .then((liste) => {
        setMaterial(liste);
        // Bereits Ausgewähltes, das nicht mehr existiert (aufgebraucht,
        // umgelegt), fällt automatisch raus.
        setGewaehltesMaterial((alt) => (liste.some((m) => m.id === alt) ? alt : ""));
      })
      .catch(() => setMaterial([]))
      .finally(() => setMaterialLaedt(false));
  }, [weg, campaignId, item.id]);

  useEffect(() => {
    if (weg !== "haendler") return;
    setPreisLaedt(true);
    setHaendlerFehler(null);
    itemsApi
      .ruestungReparaturPreis(campaignId, item.id)
      .then((antwort) => {
        setPreisVorschlag(antwort.preis);
        setDeckel(antwort.deckel);
        setFehlendeKaestchen(antwort.fehlendeKaestchen);
      })
      .catch((e) => setHaendlerFehler(e instanceof Error ? e.message : "Preis konnte nicht berechnet werden"))
      .finally(() => setPreisLaedt(false));
  }, [weg, campaignId, item.id]);

  async function selbstReparieren() {
    if (!gewaehltesMaterial) return;
    setWuerfeltLaeuft(true);
    setSelbstFehler(null);
    try {
      const ergebnis = await itemsApi.ruestungReparierenSelbst(campaignId, item.id, gewaehltesMaterial);
      setWurf(ergebnis);
      onChanged();
    } catch (e) {
      setSelbstFehler(e instanceof Error ? e.message : "Reparatur fehlgeschlagen");
    } finally {
      setWuerfeltLaeuft(false);
    }
  }

  async function angebotSenden() {
    if (preisVorschlag == null) return;
    setAngebotLaeuft(true);
    setHaendlerFehler(null);
    try {
      await verhandlungApi.anbieten(campaignId, {
        empfaengerPersonId: personId,
        art: "RUESTUNG_REPARATUR",
        positionen: [{ bezeichnung: `Reparatur: ${item.name}`, betrag: preisVorschlag }],
        kontext: { gegenstandId: item.id, kaestchen: fehlendeKaestchen },
      });
      setAngebotGesendet(true);
    } catch (e) {
      setHaendlerFehler(e instanceof Error ? e.message : "Angebot konnte nicht gesendet werden");
    } finally {
      setAngebotLaeuft(false);
    }
  }

  return (
    <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8, marginTop: 8 }}>
      <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
        Reparatur — {item.ruestungKaestchenMax - item.ruestungKaestchenAktuell} von{" "}
        {item.ruestungKaestchenMax} Kästchen fehlen
      </label>

      <div className="rr-wahl">
        <button type="button" aria-pressed={weg === "selbst"} onClick={() => setWeg("selbst")}>
          Selbst reparieren
        </button>
        <button type="button" aria-pressed={weg === "haendler"} onClick={() => setWeg("haendler")}>
          Beim Händler
        </button>
      </div>

      {weg === "selbst" && (
        <div className="rr-abschnitt">
          {materialLaedt && <p style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Material wird geladen…</p>}
          {!materialLaedt && material.length === 0 && (
            <p style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
              Kein Reparaturmaterial im Besitz der Trägerin — als Reparaturmaterial markieren lässt sich jeder
              Gegenstand über dessen eigenes Bearbeiten-Formular (Optionen).
            </p>
          )}
          {material.length > 0 && (
            <div className="rr-material-liste">
              {material.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className="rr-material"
                  aria-pressed={gewaehltesMaterial === m.id}
                  onClick={() => setGewaehltesMaterial(m.id)}
                >
                  <span>
                    {m.name}
                    {m.hatMenge ? ` ×${m.menge}` : ""}
                  </span>
                  <span className="rr-material-kapazitaet">bis {m.reparaturKapazitaet} Kästchen</span>
                </button>
              ))}
            </div>
          )}

          <button type="button" disabled={!gewaehltesMaterial || wuerfeltLaeuft} onClick={selbstReparieren}>
            {wuerfeltLaeuft ? "Würfelt…" : "Probe würfeln + reparieren"}
          </button>
          {selbstFehler && <p className="rr-fehler">{selbstFehler}</p>}

          {wurf && (
            <div className="rr-wurf-ergebnis" data-erfolg={wurf.repariert > 0}>
              <span className="rr-wurf-augen">
                Pool {wurf.pool} — Würfe [{wurf.augen.join(", ")}] — {wurf.erfolge} Erfolge
                {wurf.patzer && " — Patzer!"}
              </span>
              <span>
                Schwelle {wurf.schwelle} → Überschuss {wurf.ueberschuss}, gedeckelt durch{" "}
                {wurf.materialName} (max {wurf.materialKapazitaet})
              </span>
              <span className="rr-wurf-repariert" data-erfolg={wurf.repariert > 0}>
                {wurf.repariert} Kästchen repariert — jetzt {wurf.gegenstand.ruestungKaestchenAktuell}/
                {wurf.gegenstand.ruestungKaestchenMax}
              </span>
              <span style={{ fontSize: "0.8em", color: "var(--text-aus)" }}>
                {wurf.materialName} verbraucht — noch {wurf.materialRestmenge} übrig
              </span>
            </div>
          )}
        </div>
      )}

      {weg === "haendler" && (
        <div className="rr-abschnitt">
          {preisLaedt && <p style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Preis wird berechnet…</p>}
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
            <p style={{ fontSize: "0.9em", color: "var(--gut)" }}>
              Angebot über {preisVorschlag?.toLocaleString("de-AT")}¥ gesendet — wartet auf Antwort.
            </p>
          )}
          {haendlerFehler && <p className="rr-fehler">{haendlerFehler}</p>}
        </div>
      )}
    </div>
  );
}
