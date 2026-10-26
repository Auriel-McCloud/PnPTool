import { useEffect, useState } from "react";
import { itemsApi, type Gegenstand, type Ablage } from "../items/api";
import { GegenstandKachel } from "../items/GegenstandKachel";
import "../items/gegenstaende.css";

/**
 * Ausrüstung einer Drohne/eines Fahrzeugs (26.10.2026, Mark: "ich habe auch
 * nicht die Möglichkeit Waffen auszurüsten").
 *
 * Technisch ist eine Drohne ein ganz normaler `Person`-Knoten (siehe
 * docs/wiki/concepts/drohnen-fahrzeuge.md, "Ausrüstung") — Waffen/Rüstung
 * laufen 1:1 über das bestehende `BESITZT`/`AUSGERÜSTET`-System, dieselbe
 * `GegenstandKachel` wie im Spieler-Inventar. **Nur GM:** die
 * Besitz-/Ablage-Route (`items/routes.py::ablage_aendern`) prüft bei
 * Nicht-GM strikt `viewer.person_id == Besitzer` — der Rigger selbst ist
 * NICHT der Besitzer der Drohnen-Gegenstände (die Drohne besitzt sie
 * selbst), ein Spieler-Self-Service dafür bräuchte erst eine eigene
 * Freigabe über `_drohne_und_rigger_oder_404` wie bei `aktivSetzen`/
 * `riggerSetzen` — noch nicht gebaut, siehe CLAUDE.md.
 *
 * Neue Gegenstände für die Drohne legt die SL weiterhin über die normale
 * Gegenstände-Verwaltung an (Besitzer auf die Drohne setzen) — kein
 * doppelter Anlegen-Dialog hier.
 */
export function DrohnenAusruestung({ campaignId, drohneId }: { campaignId: string; drohneId: string }) {
  const [items, setItems] = useState<Gegenstand[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);

  function neuLaden() {
    itemsApi
      .list(campaignId, drohneId)
      .then(setItems)
      .catch(() => setFehler("Die Gegenstände konnten nicht geladen werden."))
      .finally(() => setLaden(false));
  }

  useEffect(neuLaden, [campaignId, drohneId]);

  async function umlegen(itemId: string, ablage: Ablage) {
    await itemsApi.setAblage(campaignId, itemId, ablage);
    neuLaden();
  }

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Ausrüstung…</p>;
  if (fehler) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;

  const ausgeruestet = items.filter((i) => i.ablage === "AUSGERUESTET");
  const uebrig = items.filter((i) => i.ablage !== "AUSGERUESTET");

  return (
    <div>
      <p style={{ fontSize: 12, color: "var(--text-leise)", margin: "0 0 10px" }}>
        Waffen, Rüstung und sonstige Ausrüstung dieser Drohne/dieses Fahrzeugs. Neue Gegenstände legt die SL über
        die Gegenstände-Verwaltung an und setzt dort den Besitzer auf diese Drohne — hier wird nur
        ausgerüstet/abgelegt.
      </p>

      {items.length === 0 ? (
        <p style={{ color: "var(--text-leise)" }}>Noch keine Gegenstände im Besitz dieser Drohne.</p>
      ) : (
        <>
          <h3 style={{ margin: "0 0 6px" }}>Ausgerüstet</h3>
          {ausgeruestet.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-leise)", margin: "0 0 10px" }}>Nichts ausgerüstet.</p>
          ) : (
            <div className="gg-raster" style={{ marginBottom: 14 }}>
              {ausgeruestet.map((item) => (
                <GegenstandKachel key={item.id} item={item} onUmlegen={(ablage) => umlegen(item.id, ablage)} />
              ))}
            </div>
          )}

          <h3 style={{ margin: "0 0 6px" }}>Übrige Ausrüstung</h3>
          {uebrig.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-leise)" }}>Alles ist ausgerüstet.</p>
          ) : (
            <div className="gg-raster">
              {uebrig.map((item) => (
                <GegenstandKachel key={item.id} item={item} onUmlegen={(ablage) => umlegen(item.id, ablage)} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
