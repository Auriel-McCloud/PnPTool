import { useEffect, useState } from "react";
import { entitiesApi, type KiEintrag } from "../entities/api";
import { KI_STUFEN, petsApi, type PetStand } from "./api";

/**
 * SL: KI-Begleiter an einen Gegenstand koppeln (Mark, 15.11.2026: „die KI an
 * einen Gegenstand koppeln, und im Gegenstand für den Spieler einen
 * aktivieren/deaktivieren-Button“). Die KI bleibt eine eigene KI-Person mit
 * Blatt (Begleiter-Verwaltung) und wächst mit ihren EP; der Gegenstand sagt
 * nur, wo sie läuft und ob ihr Desktop-Pet gerade wach ist.
 * KI-Liste erst beim Öffnen des Formulars holen (wie die Critter-Liste
 * der Ki-Tamas).
 */
export function KiKopplungWahl({
  campaignId,
  itemId,
  kiPersonId: kiVorher,
  kiAktiv: aktivVorher,
}: {
  campaignId: string;
  itemId: string;
  kiPersonId: string;
  kiAktiv: boolean;
}) {
  const [kis, setKis] = useState<KiEintrag[]>([]);
  const [kiId, setKiId] = useState(kiVorher);
  const [aktiv, setAktiv] = useState(aktivVorher);
  const [stand, setStand] = useState<PetStand | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    entitiesApi.listKi(campaignId).then(setKis).catch(() => setKis([]));
  }, [campaignId]);

  useEffect(() => {
    if (!kiId) {
      setStand(null);
      return;
    }
    petsApi.artLesen(campaignId, kiId).then(setStand).catch(() => setStand(null));
  }, [campaignId, kiId]);

  async function koppeln(neu: string) {
    setFehler(null);
    try {
      const k = await petsApi.kiKoppeln(campaignId, itemId, neu || null);
      setKiId(k.kiPersonId);
      setAktiv(k.kiAktiv);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Koppeln ging nicht.");
    }
  }

  const leise = { fontSize: 11, color: "var(--text-leise)" };
  return (
    <div className="bg-zeile" style={{ marginTop: 10, flexDirection: "column", alignItems: "stretch", gap: 4 }}>
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
        KI-Begleiter
        <select value={kiId} onChange={(e) => koppeln(e.target.value)}>
          <option value="">keine</option>
          {kis.map((k) => (
            <option key={k.id} value={k.id}>
              {k.alias || k.name}
              {k.besitzerName ? ` (${k.besitzerName})` : ""}
            </option>
          ))}
        </select>
      </label>
      <span style={leise}>
        Die KI läuft auf diesem Gegenstand. Ist sie wach, schwebt sie als Pet über die Tablets der Party dessen,
        der ihn besitzt — er kann sie im Gegenstand selbst an- und ausschalten.
      </span>
      {kiId && (
        <>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em", marginTop: 4 }}>
            <input
              type="checkbox"
              checked={aktiv}
              onChange={async (e) => {
                setFehler(null);
                try {
                  setAktiv((await petsApi.kiAktiv(campaignId, itemId, e.target.checked)).kiAktiv);
                } catch (err) {
                  setFehler(err instanceof Error ? err.message : "Umschalten ging nicht.");
                }
              }}
            />{" "}
            KI wach (Desktop-Pet an)
          </label>
          {stand?.waechst && stand.stufe && (
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em", marginTop: 4 }}>
              Wachstum
              <select
                value={stand.stufe}
                onChange={async (e) => {
                  if (e.target.value) setStand(await petsApi.wachstumSetzen(campaignId, kiId, e.target.value));
                }}
              >
                {KI_STUFEN.map((s) => (
                  <option key={s.wert} value={s.wert}>
                    {s.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {stand?.gewachsen !== null && stand?.gewachsen !== undefined && (
            <span style={leise}>{stand.gewachsen} EP seit dem ersten Funken — sie wächst mit den EP der KI weiter.</span>
          )}
        </>
      )}
      {fehler && <span style={leise}>{fehler}</span>}
    </div>
  );
}
