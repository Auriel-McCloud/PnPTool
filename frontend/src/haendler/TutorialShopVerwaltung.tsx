import { useEffect, useState } from "react";
import { haendlerApi, type HaendlerEintrag } from "./api";
import { entitiesApi } from "../entities/api";
import "../zusatzfertigkeiten/zusatzfertigkeiten.css";
import "./shop.css";

/**
 * Kampagnen-Einstellungen (⚙): welcher Laden der Tutorial-Shop ist.
 * Ein Laden pro Kampagne, Flag bleibt am Ort. Nicht im Sortiment-Editor,
 * dort zerreißt das Label-Layout den Haken. Eingebettet in
 * campaigns/EinstellungenFenster.tsx, Sektion TUTORIAL-SHOP — kein eigener
 * Burgermenü-Punkt (11.10.2026, Mark: das war ein Missverständnis).
 */
export function TutorialShopVerwaltung({ campaignId }: { campaignId: string }) {
  const [laeden, setLaeden] = useState<HaendlerEintrag[]>([]);
  const [aktuellId, setAktuellId] = useState<string | null>(null);
  const [laedt, setLaedt] = useState(true);
  const [läuft, setLäuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function laden() {
    const [normal, tutorial] = await Promise.all([
      haendlerApi.alle(campaignId),
      haendlerApi.tutorial(campaignId),
    ]);
    const nachId = new Map(normal.map((s) => [s.id, s]));
    if (tutorial) nachId.set(tutorial.id, { ...tutorial, istTutorialShop: true });
    setLaeden([...nachId.values()].sort((a, b) => a.name.localeCompare(b.name, "de")));
    setAktuellId(tutorial?.id ?? null);
  }

  useEffect(() => {
    setLaedt(true);
    laden()
      .catch(() => setFehler("Läden konnten nicht geladen werden"))
      .finally(() => setLaedt(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  async function waehlen(id: string | null) {
    if (id === aktuellId || läuft) return;
    setLäuft(true);
    setFehler(null);
    try {
      if (aktuellId) {
        await entitiesApi.updateOrt(campaignId, aktuellId, { istTutorialShop: false });
      }
      if (id) {
        await entitiesApi.updateOrt(campaignId, id, { istTutorialShop: true });
      }
      await laden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte den Tutorial-Shop nicht setzen");
    } finally {
      setLäuft(false);
    }
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Läden…</p>;

  return (
    <div className="zf-seite">
      <p className="zf-hinweis">
        Ein Laden pro Kampagne — hier nur einer wählbar. Spieler sehen ihn nur im Freebees-Schritt, nicht in der Shop-Übersicht. Ware pflegst
        du am Ort unter Laden verwalten.
      </p>
      {fehler && <p className="shop-ware-fehler">{fehler}</p>}

      {laeden.length === 0 && (
        <p className="zf-leer">Noch kein Laden. Unter Orte einen Ort anlegen und zum Laden machen.</p>
      )}

      {laeden.length > 0 && (
        <label style={{ display: "flex", flexDirection: "column", gap: 4, padding: "6px 0" }}>
          <span style={{ fontSize: 12, color: "var(--text-leise)" }}>Welcher Laden</span>
          <select
            value={aktuellId ?? ""}
            disabled={läuft}
            onChange={(e) => waehlen(e.target.value || null)}
            style={{ maxWidth: 360 }}
          >
            <option value="">Keiner</option>
            {laeden.map((laden) => (
              <option key={laden.id} value={laden.id}>
                {laden.name}
                {laden.vertriebsart === "DIGITAL" ? " (Online)" : ""}
              </option>
            ))}
          </select>
        </label>
      )}
    </div>
  );
}
