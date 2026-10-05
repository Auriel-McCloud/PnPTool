import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { haendlerApi, type HaendlerGesicht } from "./api";
import { entitiesApi, type Person } from "../entities/api";
import { HaendlerBearbeiten } from "./HaendlerBearbeiten";
import "./shop.css";

/**
 * Ort-seitiger Einstieg ins Shop-System (05.10.2026, Marks Vorgabe: "ich
 * will, dass man einen Ort zu einem Laden machen kann" — die Daten hängen
 * strukturell schon seit 04.10. am Ort und ein Ort kann mehrere Händler
 * haben (siehe haendler/repository.py Docstring), aber es gab dafür nur
 * den Umweg über NPCDetail -> "Zum Händler machen" -> Standort-Dropdown in
 * HaendlerBearbeiten. Dieses Fenster ist der direkte Weg von der Ort-Seite.
 *
 * Verwaltet NUR, welche Personen hier verkaufen (BETREIBT) — Ware/Rabatt
 * bleibt bewusst in der bestehenden HaendlerBearbeiten (verlinkt unten),
 * Spezialisierung/Vertriebsart bleiben bewusst in den bestehenden
 * Händler-Einstellungen (NPCDetail) — keine Parallel-Mechanik, nur der
 * fehlende direkte Einstieg.
 *
 * Der erste hinzugefügte Verkäufer aktiviert den Laden automatisch
 * (istShop=true ist ein Seiteneffekt von haendlerApi.standortSetzen in
 * repository.py). Ein NPC ohne istHaendler=true wird dabei automatisch
 * dazu gemacht — derselbe Schritt, den man sonst einzeln in NPCDetail
 * klicken müsste.
 */
export function OrtLadenFenster({
  campaignId,
  ortId,
  ortName,
  offen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  ortId: string;
  ortName: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Ruft den Ort-Refresh der Eltern auf (istShop kann sich ändern). */
  onGeaendert: () => void;
}) {
  const [verkaeufer, setVerkaeufer] = useState<HaendlerGesicht[]>([]);
  const [npcs, setNpcs] = useState<Person[]>([]);
  const [neuerVerkaeuferId, setNeuerVerkaeuferId] = useState("");
  const [läuft, setLäuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [sortimentOffen, setSortimentOffen] = useState(false);
  const [istAktiv, setIstAktiv] = useState(false);
  const [geladen, setGeladen] = useState(false);

  async function laden() {
    const alleNpcs = await entitiesApi.listPersonen(campaignId, { personType: "NPC" });
    setNpcs(alleNpcs);
    try {
      const shop = await haendlerApi.einzeln(campaignId, ortId);
      setVerkaeufer(shop.haendler);
      setIstAktiv(true);
    } catch {
      // Noch kein Laden — Ort hat istShop=false, es gibt (noch) nichts zu holen.
      setVerkaeufer([]);
      setIstAktiv(false);
    }
    setGeladen(true);
  }

  useEffect(() => {
    if (!offen) return;
    laden().catch(() => setFehler("Laden fehlgeschlagen"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId, ortId]);

  const wählbareNpcs = npcs.filter((p) => !verkaeufer.some((v) => v.id === p.id));

  async function ausfuehren(aktion: () => Promise<unknown>) {
    setLäuft(true);
    setFehler(null);
    try {
      await aktion();
      await laden();
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Aktion fehlgeschlagen");
    } finally {
      setLäuft(false);
    }
  }

  async function verkaeuferHinzufuegen() {
    if (!neuerVerkaeuferId) return;
    const npc = npcs.find((p) => p.id === neuerVerkaeuferId);
    await ausfuehren(async () => {
      if (!npc?.istHaendler) {
        await entitiesApi.updatePerson(campaignId, neuerVerkaeuferId, { istHaendler: true });
      }
      await haendlerApi.standortSetzen(campaignId, neuerVerkaeuferId, ortId);
    });
    setNeuerVerkaeuferId("");
  }

  async function verkaeuferEntfernen(personId: string) {
    await ausfuehren(() => haendlerApi.standortSetzen(campaignId, personId, null));
  }

  return (
    <Fenster
      offen={offen}
      titel={`${ortName} — Laden`}
      unterzeile={
        !geladen ? "Lädt…" : istAktiv ? "Verkäufer & Sortiment" : "Noch kein Laden — ersten Verkäufer hinzufügen"
      }
      kennung={`ort-laden:${ortId}`}
      onSchliessen={onSchliessen}
    >
      <div className="shop-editor">
        {fehler && <p className="shop-ware-fehler">{fehler}</p>}

        <section>
          <h3 className="gg-abschnitt">
            <span>Verkäufer</span>
            <span className="gg-abschnitt-zahl">{verkaeufer.length}</span>
          </h3>

          <div className="shop-editor-liste">
            {verkaeufer.map((v) => (
              <div key={v.id} className="shop-editor-zeile">
                <span className="shop-editor-zeile-name">{v.name}</span>
                <span className="shop-editor-zeile-knoepfe">
                  <button type="button" onClick={() => verkaeuferEntfernen(v.id)} disabled={läuft}>
                    Entfernen
                  </button>
                </span>
              </div>
            ))}
            {verkaeufer.length === 0 && (
              <p className="shop-leer">
                Noch kein Verkäufer — füge einen NPC hinzu, um diesen Ort zu einem Laden zu machen.
              </p>
            )}
          </div>

          <div className="shop-editor-hinzufuegen">
            <select value={neuerVerkaeuferId} onChange={(e) => setNeuerVerkaeuferId(e.target.value)} disabled={läuft}>
              <option value="">— NPC wählen —</option>
              {wählbareNpcs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                  {p.istHaendler ? "" : " (wird zum Händler)"}
                </option>
              ))}
            </select>
            <button type="button" onClick={verkaeuferHinzufuegen} disabled={läuft || !neuerVerkaeuferId}>
              Hinzufügen
            </button>
          </div>
          {geladen && npcs.length === 0 && (
            <p className="shop-ware-hinweis">Noch keine NPCs in dieser Kampagne angelegt.</p>
          )}
          {geladen && npcs.length > 0 && wählbareNpcs.length === 0 && (
            <p className="shop-ware-hinweis">Alle NPCs dieser Kampagne verkaufen hier bereits.</p>
          )}
        </section>

        {istAktiv && (
          <section>
            <button type="button" onClick={() => setSortimentOffen(true)} disabled={läuft}>
              🛒 Sortiment bearbeiten
            </button>
          </section>
        )}
      </div>

      {sortimentOffen && (
        <HaendlerBearbeiten
          campaignId={campaignId}
          haendlerId={ortId}
          offen={sortimentOffen}
          onSchliessen={() => setSortimentOffen(false)}
          onGeaendert={onGeaendert}
        />
      )}
    </Fenster>
  );
}
