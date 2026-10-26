import { useEffect, useState } from "react";
import { itemsApi, type Gegenstand, type Ablage } from "../items/api";
import { GegenstandKachel } from "../items/GegenstandKachel";
import { UebergebenPopup } from "./UebergebenPopup";
import "../items/gegenstaende.css";

/**
 * Ausrüstung einer Drohne/eines Fahrzeugs (26.10.2026, Mark: "ich habe auch
 * nicht die Möglichkeit Waffen auszurüsten").
 *
 * Technisch ist eine Drohne ein ganz normaler `Person`-Knoten (siehe
 * docs/wiki/concepts/drohnen-fahrzeuge.md, "Ausrüstung") — Waffen/Rüstung
 * laufen 1:1 über das bestehende `BESITZT`/`AUSGERÜSTET`-System, dieselbe
 * `GegenstandKachel` wie im Spieler-Inventar. **GM und der gebundene Rigger**
 * (26.10.2026, Besitz-Ausnahme in `items/routes.py::ablage_aendern`, analog
 * zu `traits/routes.py::_darf_person_sehen`): beide dürfen ausrüsten/ablegen.
 * Der Rigger sieht dabei trotzdem nur Gegenstände, deren Sichtbarkeit die SL
 * freigegeben hat (normale Sichtbarkeitsprüfung bleibt unverändert, Besitz-
 * Erlaubnis ist eine separate Sache) — neu angelegte Gegenstände sind für
 * einen NPC-Besitzer wie eine Drohne standardmäßig SL-geheim.
 *
 * **Übergeben** (26.10.2026, Mark: "es müsste die Möglichkeit geben, etwas
 * aus dem Inventar des Riggers auszurüsten bzw. zu übergeben" — die Liste
 * zeigte vorher nur, was die Drohne SCHON besitzt, es gab aber keinen Weg,
 * ihr überhaupt etwas zu geben): nur für den Rigger (`eigenePersonId`
 * gesetzt — die GM-Ansicht hat hier kein eigenes Inventar). Nutzt
 * `items/routes.py::besitzer_wechseln`, serverseitig auf den eigenen Kreis
 * begrenzt (`_eigener_kreis`) — sofortige Übertragung, kein Annehmen/
 * Ablehnen wie bei `WeitergebenPopup` unter Spielern. Symmetrisch dazu kann
 * jedes Drohnen-Item genauso wieder zurück an den Rigger wandern.
 *
 * Neue Gegenstände für die Drohne legt die SL weiterhin über die normale
 * Gegenstände-Verwaltung an (Besitzer auf die Drohne setzen) — kein
 * doppelter Anlegen-Dialog hier.
 */
export function DrohnenAusruestung({
  campaignId,
  drohneId,
  eigenePersonId,
}: {
  campaignId: string;
  drohneId: string;
  /** Der Rigger selbst, zum Übergeben aus seinem eigenen Besitz — null/undefined
   *  bei der GM-Ansicht (die SL hat hier kein eigenes Inventar). */
  eigenePersonId?: string | null;
}) {
  const [items, setItems] = useState<Gegenstand[]>([]);
  const [eigene, setEigene] = useState<Gegenstand[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [uebergebenOffen, setUebergebenOffen] = useState(false);
  const [laeuft, setLaeuft] = useState(false);

  function neuLaden() {
    const anfragen: Promise<unknown>[] = [itemsApi.list(campaignId, drohneId).then(setItems)];
    if (eigenePersonId) {
      anfragen.push(itemsApi.list(campaignId, eigenePersonId).then(setEigene));
    }
    Promise.all(anfragen)
      .catch(() => setFehler("Die Gegenstände konnten nicht geladen werden."))
      .finally(() => setLaden(false));
  }

  useEffect(neuLaden, [campaignId, drohneId, eigenePersonId]);

  async function umlegen(itemId: string, ablage: Ablage) {
    await itemsApi.setAblage(campaignId, itemId, ablage);
    neuLaden();
  }

  async function uebergeben(itemId: string) {
    setLaeuft(true);
    try {
      await itemsApi.changeOwner(campaignId, itemId, drohneId);
      setUebergebenOffen(false);
      neuLaden();
    } finally {
      setLaeuft(false);
    }
  }

  async function zurueckgeben(itemId: string) {
    if (!eigenePersonId) return;
    await itemsApi.changeOwner(campaignId, itemId, eigenePersonId);
    neuLaden();
  }

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Ausrüstung…</p>;
  if (fehler) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;

  const ausgeruestet = items.filter((i) => i.ablage === "AUSGERUESTET");
  const uebrig = items.filter((i) => i.ablage !== "AUSGERUESTET");
  // Nichts Körperliches und nichts fest Verbautes lässt sich umverteilen —
  // dieselbe Grenze wie bei `besitzer_wechseln` serverseitig (409 sonst).
  const uebergebbar = eigene.filter((i) => !i.istNatuerlich && !i.verbaut);

  function zeile(item: Gegenstand) {
    return (
      <div key={item.id} style={{ position: "relative" }}>
        <GegenstandKachel item={item} onUmlegen={(ablage) => umlegen(item.id, ablage)} />
        {eigenePersonId && (
          <button
            type="button"
            className="gg-zurueckgeben"
            title="Zurück in deinen eigenen Besitz nehmen"
            onClick={() => zurueckgeben(item.id)}
          >
            ← zu dir
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      <p style={{ fontSize: 12, color: "var(--text-leise)", margin: "0 0 10px" }}>
        Waffen, Rüstung und sonstige Ausrüstung dieser Drohne/dieses Fahrzeugs.
        {eigenePersonId
          ? " Neue Gegenstände dafür legt die SL an — du kannst aber eigene Sachen übergeben oder zurücknehmen."
          : " Neue Gegenstände legt die SL über die Gegenstände-Verwaltung an und setzt dort den Besitzer auf diese Drohne."}
      </p>

      {eigenePersonId && (
        <div className="bg-zeile" style={{ marginBottom: 10 }}>
          <button type="button" onClick={() => setUebergebenOffen(true)}>
            <span aria-hidden="true">🤝</span> Aus eigenem Besitz übergeben
          </button>
        </div>
      )}

      {items.length === 0 ? (
        <p style={{ color: "var(--text-leise)" }}>Noch keine Gegenstände im Besitz dieser Drohne.</p>
      ) : (
        <>
          <h3 style={{ margin: "0 0 6px" }}>Ausgerüstet</h3>
          {ausgeruestet.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-leise)", margin: "0 0 10px" }}>Nichts ausgerüstet.</p>
          ) : (
            <div className="gg-raster" style={{ marginBottom: 14 }}>
              {ausgeruestet.map(zeile)}
            </div>
          )}

          <h3 style={{ margin: "0 0 6px" }}>Übrige Ausrüstung</h3>
          {uebrig.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-leise)" }}>Alles ist ausgerüstet.</p>
          ) : (
            <div className="gg-raster">{uebrig.map(zeile)}</div>
          )}
        </>
      )}

      {eigenePersonId && (
        <UebergebenPopup
          offen={uebergebenOffen}
          gegenstaende={uebergebbar}
          zielName="der Drohne"
          laeuft={laeuft}
          onUebergeben={uebergeben}
          onAbbrechen={() => setUebergebenOffen(false)}
        />
      )}
    </div>
  );
}
