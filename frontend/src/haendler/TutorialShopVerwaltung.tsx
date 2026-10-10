import { useEffect, useState } from "react";
import { haendlerApi, type HaendlerEintrag } from "./api";
import { entitiesApi } from "../entities/api";
import "../zusatzfertigkeiten/zusatzfertigkeiten.css";
import "./shop.css";

/**
 * Kampagnenmenü: welcher Laden der Tutorial-Shop ist.
 * Ein Laden pro Kampagne, Flag bleibt am Ort. Nicht im Sortiment-Editor,
 * dort zerreißt das Label-Layout den Haken.
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
        Ein Laden pro Kampagne. Spieler sehen ihn nur im Freebees-Schritt, nicht in der Shop-Übersicht. Ware pflegst
        du am Ort unter Laden verwalten.
      </p>
      {fehler && <p className="shop-ware-fehler">{fehler}</p>}

      {laeden.length === 0 && (
        <p className="zf-leer">Noch kein Laden. Unter Orte einen Ort anlegen und zum Laden machen.</p>
      )}

      {laeden.length > 0 && (
        <table className="zf-tabelle">
          <thead>
            <tr>
              <th>Laden</th>
              <th>Art</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {laeden.map((laden) => {
              const istEs = laden.id === aktuellId;
              return (
                <tr key={laden.id} className="zf-zeile" onClick={() => waehlen(istEs ? null : laden.id)}>
                  <td className="zf-zeile-name">{laden.name}</td>
                  <td>{laden.vertriebsart === "DIGITAL" ? "Online" : "Vor Ort"}</td>
                  <td>{istEs ? "Tutorial-Shop" : läuft ? "…" : "wählen"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      {aktuellId && (
        <button type="button" disabled={läuft} onClick={() => waehlen(null)}>
          Keiner
        </button>
      )}
    </div>
  );
}
