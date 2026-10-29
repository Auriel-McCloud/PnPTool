import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { itemsApi, type Gegenstand, type GegenstandMitBesitzer, type AugmentZiel, type AugmentMontagePool, type AugmentReparaturPool } from "../items/api";
import { drohnenApi, type DrohnenEintrag, type MakerProbenErgebnis } from "../drohnen/api";
import "../traits/levelup.css";
import "../items/wegwerfen.css";

const SKILLS = ["Maker (Hardware)", "Handwerk"] as const;

/** Ein montierbares Ziel — Gegenstand (Waffe/Rüstung/Cyberdeck/
 * Riggerkonsole) ODER Person (Drohne/Fahrzeug). */
type ZielAuswahl = { id: string; name: string; kind: "Gegenstand" | "Person" };

/**
 * Montieren/Demontieren/Reparieren-Popup für EIN Augment (29.10.2026, siehe
 * docs/wiki/concepts/augments-ausruestung.md). Drei sich gegenseitig
 * ausschliessende Zustände:
 *
 * - **defekt**: nur Reparatur möglich (Material + selbstberichtete Probe,
 *   dieselbe Mechanik wie die Rüstungs-/Drohnen-Reparatur).
 * - **montiert**: nur Demontieren möglich (dieselbe Probe-Schwelle wie beim
 *   Montieren selbst).
 * - **frei**: Ziel wählen (eigene Waffe/Rüstung/Cyberdeck/Riggerkonsole ODER
 *   beliebige Drohne/Fahrzeug der Kampagne) und montieren.
 *
 * **Nur SL** — wie jede andere Werkbank-Aktion.
 */
export function AugmentFenster({
  campaignId,
  augment,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  augment: GegenstandMitBesitzer;
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [skill, setSkill] = useState<string>(SKILLS[0]);
  const [gewaehltesAttribut, setGewaehltesAttribut] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnisText, setErgebnisText] = useState<string | null>(null);

  // --- Montieren: Ziel-Auswahl -----------------------------------------
  const [gegenstandZiele, setGegenstandZiele] = useState<AugmentZiel[]>([]);
  const [drohnenZiele, setDrohnenZiele] = useState<DrohnenEintrag[]>([]);
  const [gewaehltesZiel, setGewaehltesZiel] = useState<ZielAuswahl | null>(null);
  const [montagePool, setMontagePool] = useState<AugmentMontagePool | null>(null);
  const [poolLaedt, setPoolLaedt] = useState(false);

  // --- Reparieren -------------------------------------------------------
  const [material, setMaterial] = useState<Gegenstand[]>([]);
  const [qualitaet, setQualitaet] = useState<string | null>(null);
  const [menge, setMenge] = useState(1);
  const [reparaturPool, setReparaturPool] = useState<AugmentReparaturPool | null>(null);

  const istDefekt = augment.defekt;
  const istMontiert = !istDefekt && Boolean(augment.montiertAnId);
  const istFrei = !istDefekt && !istMontiert;

  const gruppen = useMemo(() => {
    const nachQualitaet = new Map<string, Gegenstand[]>();
    for (const m of material) {
      if (!m.istMaschinenteil || m.menge <= 0) continue;
      const liste = nachQualitaet.get(m.maschinenteilQualitaet) ?? [];
      liste.push(m);
      nachQualitaet.set(m.maschinenteilQualitaet, liste);
    }
    return [...nachQualitaet.entries()].map(([q, stuecke]) => ({
      qualitaet: q,
      menge: stuecke.reduce((s, m) => s + (m.hatMenge ? m.menge : 1), 0),
      repraesentant: stuecke[0],
    }));
  }, [material]);
  const gewaehlteGruppe = gruppen.find((g) => g.qualitaet === qualitaet) ?? null;

  // Ziele laden (Montieren)
  useEffect(() => {
    if (!istFrei) return;
    itemsApi.augmentZiele(campaignId, augment.id).then(setGegenstandZiele).catch(() => setGegenstandZiele([]));
    // Nur Drohnen/Fahrzeuge DESSELBEN Besitzers als Ziel anbieten (29.10.2026,
    // Self-Service für Spieler) — sonst könnte man fremde Ausrüstung in der
    // Liste sehen, auch wenn der Server das Montieren ohnehin ablehnen würde.
    drohnenApi
      .liste(campaignId)
      .then((liste) => setDrohnenZiele(liste.filter((d) => d.upgradeSlots > 0 && (!augment.ownerId || d.riggerId === augment.ownerId))))
      .catch(() => setDrohnenZiele([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [istFrei, campaignId, augment.id, augment.ownerId]);

  // Material laden (Reparieren)
  useEffect(() => {
    if (!istDefekt) return;
    itemsApi.augmentMaterial(campaignId, augment.id).then(setMaterial).catch(() => setMaterial([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [istDefekt, campaignId, augment.id]);

  // Montage-Pool (Montieren UND Demontieren teilen sich dieselbe Schwelle)
  useEffect(() => {
    if (istDefekt) return;
    if (istFrei && !gewaehltesZiel) {
      setMontagePool(null);
      return;
    }
    setPoolLaedt(true);
    setFehler(null);
    itemsApi
      .augmentMontagePool(campaignId, augment.id, skill)
      .then((p) => {
        setMontagePool(p);
        setGewaehltesAttribut((alt) => (alt && p.attribute.some((a) => a.name === alt) ? alt : null));
      })
      .catch((e) => setFehler(e instanceof Error ? e.message : "Pool konnte nicht geladen werden"))
      .finally(() => setPoolLaedt(false));
  }, [istDefekt, istFrei, gewaehltesZiel, campaignId, augment.id, skill]);

  // Reparatur-Pool
  useEffect(() => {
    if (!istDefekt || !gewaehlteGruppe) {
      setReparaturPool(null);
      return;
    }
    setPoolLaedt(true);
    setFehler(null);
    itemsApi
      .augmentReparaturPool(campaignId, augment.id, skill, gewaehlteGruppe.repraesentant.id, menge)
      .then((p) => {
        setReparaturPool(p);
        setGewaehltesAttribut((alt) => (alt && p.attribute.some((a) => a.name === alt) ? alt : null));
      })
      .catch((e) => setFehler(e instanceof Error ? e.message : "Pool konnte nicht geladen werden"))
      .finally(() => setPoolLaedt(false));
  }, [istDefekt, gewaehlteGruppe, menge, campaignId, augment.id, skill]);

  const pool = istDefekt ? reparaturPool : montagePool;
  const attributWert = gewaehltesAttribut ? (pool?.attribute.find((a) => a.name === gewaehltesAttribut)?.wert ?? 0) : null;
  const poolGroesse = pool && attributWert != null ? pool.skillWert + attributWert : null;

  async function montierenMelden(ergebnis: MakerProbenErgebnis) {
    if (!gewaehltesZiel) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const r = await itemsApi.augmentMontieren(campaignId, augment.id, gewaehltesZiel.id, skill, ergebnis);
      setErgebnisText(
        ergebnis === "ja"
          ? `Montiert an ${gewaehltesZiel.name}.`
          : ergebnis === "patzer"
            ? "Patzer — das Upgrade ist jetzt defekt."
            : "Nicht geschafft — später erneut versuchen.",
      );
      void r;
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Montage fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  async function demontierenMelden(ergebnis: MakerProbenErgebnis) {
    setLaeuft(true);
    setFehler(null);
    try {
      await itemsApi.augmentDemontieren(campaignId, augment.id, skill, ergebnis);
      setErgebnisText(
        ergebnis === "ja"
          ? "Demontiert."
          : ergebnis === "patzer"
            ? "Patzer — das Upgrade ist jetzt defekt, bleibt aber montiert."
            : "Nicht geschafft — später erneut versuchen.",
      );
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Demontage fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  async function reparierenMelden(ergebnis: MakerProbenErgebnis) {
    if (!gewaehlteGruppe) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const r = await itemsApi.augmentReparierenMaterial(campaignId, augment.id, gewaehlteGruppe.repraesentant.id, menge, ergebnis);
      setErgebnisText(
        ergebnis === "ja"
          ? r.repariert
            ? `Repariert! ${r.materialName} verbraucht.`
            : `${r.materialName} verbraucht, aber noch nicht genug — weiteres Material nötig.`
          : ergebnis === "patzer"
            ? `Patzer — ${r.materialName} ist verbraucht, keine Reparatur.`
            : "Nicht geschafft — Material bleibt, später erneut versuchen.",
      );
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Reparatur fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster offen titel={`Upgrade: ${augment.name}`} kennung={`augment:${augment.id}`} onSchliessen={onSchliessen}>
      {ergebnisText ? (
        <>
          <p className="ww-beruhigung">{ergebnisText}</p>
          <div className="ww-knoepfe">
            <button type="button" className="ww-behalten" onClick={onSchliessen}>
              Schliessen
            </button>
          </div>
        </>
      ) : (
        <div className="rr-abschnitt">
          {istMontiert && (
            <p className="lu-hinweis">
              Montiert an <strong>{augment.montiertAnName}</strong>.
            </p>
          )}

          {istFrei && (
            <>
              <p className="lu-hinweis">Ziel wählen:</p>
              {gegenstandZiele.length === 0 && drohnenZiele.length === 0 && (
                <p style={{ color: "var(--text-leise)" }}>
                  Kein passendes Ziel gefunden — braucht freie Upgrade-Slots und (falls eingeschränkt) den richtigen
                  Waffentyp.
                </p>
              )}
              <div className="lu-zahlart" style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
                {gegenstandZiele.map((z) => (
                  <button
                    key={z.id}
                    type="button"
                    className="lu-zahlart-knopf"
                    data-aktiv={gewaehltesZiel?.id === z.id}
                    onClick={() => setGewaehltesZiel({ id: z.id, name: z.name, kind: "Gegenstand" })}
                  >
                    {z.name} ({z.belegteSlots}/{z.upgradeSlots})
                  </button>
                ))}
                {drohnenZiele.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    className="lu-zahlart-knopf"
                    data-aktiv={gewaehltesZiel?.id === d.id}
                    onClick={() => setGewaehltesZiel({ id: d.id, name: d.name, kind: "Person" })}
                  >
                    {d.name} ({d.istFahrzeug ? "Fahrzeug" : "Drohne"}, {d.upgradeSlots} Slots)
                  </button>
                ))}
              </div>
            </>
          )}

          {istDefekt && (
            <>
              <p className="lu-hinweis" style={{ color: "var(--nein)" }}>
                Defekt — erst reparieren, bevor es wieder montiert werden kann.
              </p>
              {gruppen.length === 0 && (
                <p style={{ color: "var(--text-leise)" }}>Kein Maschinenteil im Besitz der Besitzerin.</p>
              )}
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
                    }}
                  >
                    {g.qualitaet || "unbekannt"} ×{g.menge}
                  </button>
                ))}
              </div>
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
                </div>
              )}
            </>
          )}

          {(istMontiert || (istFrei && gewaehltesZiel) || (istDefekt && gewaehlteGruppe)) && (
            <>
              <div className="lu-zahlart" style={{ display: "flex", gap: 4, marginBottom: 10 }}>
                {SKILLS.map((s) => (
                  <button key={s} type="button" className="lu-zahlart-knopf" data-aktiv={skill === s} onClick={() => setSkill(s)}>
                    {s}
                  </button>
                ))}
              </div>

              {poolLaedt && <p style={{ color: "var(--text-leise)" }}>Pool wird berechnet…</p>}

              {!poolLaedt && pool && (
                <>
                  <p className="lu-hinweis">
                    {pool.skill}: <strong>{pool.skillWert}</strong> — wähle dazu ein Attribut, mit dem du würfelst.
                    {" "}Level {pool.level}, benötigte Erfolge: <strong>{pool.benoetigteErfolge}</strong>.
                    {istDefekt && reparaturPool && (
                      <> Heilung bei Erfolg: <strong>{reparaturPool.heilungBeiErfolg}</strong>{" "}
                        {reparaturPool.vollstaendigRepariert ? "(vollständig repariert)" : "(reicht noch nicht ganz)"}.</>
                    )}
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
                      Pool: <strong>{pool.skillWert} + {attributWert}</strong> = <strong>{poolGroesse}</strong> Würfel.
                    </p>
                  )}

                  {fehler && <p className="rr-fehler">{fehler}</p>}

                  <p className="lu-hinweis" style={{ marginTop: 10 }}>Am Tisch gewürfelt — geschafft?</p>
                  <div className="ww-knoepfe">
                    <button
                      type="button"
                      className="ww-behalten"
                      disabled={laeuft || !gewaehltesAttribut}
                      onClick={() => (istDefekt ? reparierenMelden("ja") : istMontiert ? demontierenMelden("ja") : montierenMelden("ja"))}
                    >
                      ✓ Ja
                    </button>
                    <button
                      type="button"
                      disabled={laeuft || !gewaehltesAttribut}
                      onClick={() => (istDefekt ? reparierenMelden("nein") : istMontiert ? demontierenMelden("nein") : montierenMelden("nein"))}
                    >
                      ✗ Nein
                    </button>
                    <button
                      type="button"
                      style={{ color: "var(--nein)", borderColor: "var(--nein)" }}
                      disabled={laeuft || !gewaehltesAttribut}
                      onClick={() => (istDefekt ? reparierenMelden("patzer") : istMontiert ? demontierenMelden("patzer") : montierenMelden("patzer"))}
                    >
                      ⚡ Patzer
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </Fenster>
  );
}
