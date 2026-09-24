import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { entitiesApi, type Ort } from "../entities/api";
import { symbolFuerTyp } from "../items/typKatalog";
import "./shop.css";

/**
 * SL-Sortiment-Editor (24.09.2026) — Ware eintragen/entfernen/Rabatt setzen
 * und Standort zuweisen, alles Backend-seitig bereits seit 22.09./24.09.
 * fertig (siehe docs/api/haendler.md), hier zum ersten Mal bedienbar.
 *
 * Als eigenes Fenster über der Shop-Seite (Marks Vorgabe: Commlink-Popup
 * statt Inline-Formular), aufrufbar über den "Bearbeiten"-Knopf, den nur
 * die SL sieht.
 */
export function HaendlerBearbeiten({
  campaignId,
  haendlerId,
  offen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  haendlerId: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Ruft die SL-Vorschau auf der Shop-Seite auf, nachdem sich am
   * Sortiment/Standort etwas geändert hat. */
  onGeaendert: () => void;
}) {
  const [haendler, setHaendler] = useState<HaendlerEintrag | null>(null);
  const [sortiment, setSortiment] = useState<SortimentEintrag[]>([]);
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [läuft, setLäuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  // Ware hinzufügen — eigenes kleines Unterformular
  const [neueWareId, setNeueWareId] = useState("");
  const [neuerPreis, setNeuerPreis] = useState("");

  // Rabatt-Bearbeitung: welche Zeile gerade offen ist (nur eine gleichzeitig)
  const [rabattBearbeitet, setRabattBearbeitet] = useState<string | null>(null);
  const [rabattProzent, setRabattProzent] = useState("");
  const [rabattHinweis, setRabattHinweis] = useState("");

  async function laden() {
    const [h, s, g, o] = await Promise.all([
      haendlerApi.einzeln(campaignId, haendlerId),
      haendlerApi.sortiment(campaignId, haendlerId),
      itemsApi.listAlle(campaignId),
      entitiesApi.listOrte(campaignId),
    ]);
    setHaendler(h);
    setSortiment(s);
    setGegenstaende(g);
    setOrte(o);
  }

  useEffect(() => {
    if (!offen) return;
    laden().catch(() => setFehler("Laden fehlgeschlagen"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId, haendlerId]);

  // Nur globale Vorlagen zur Auswahl — Marks Modell: Vorlagen sind
  // unendlich verfügbar, ein Unikat gehört i.d.R. schon jemandem und wird
  // nicht "ins Sortiment gestellt" wie ein Katalogartikel. Bereits
  // eingetragene Ware fällt raus, sonst könnte man sie doppelt hinzufügen.
  const wählbareVorlagen = useMemo(() => {
    const bereitsDrin = new Set(sortiment.map((s) => s.gegenstandId));
    return gegenstaende.filter((g) => g.istVorlage && !bereitsDrin.has(g.id));
  }, [gegenstaende, sortiment]);

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

  async function wareHinzufuegen() {
    if (!neueWareId) return;
    await ausfuehren(() =>
      haendlerApi.sortimentHinzufuegen(
        campaignId,
        haendlerId,
        neueWareId,
        neuerPreis.trim() ? Number(neuerPreis) : undefined,
      ),
    );
    setNeueWareId("");
    setNeuerPreis("");
  }

  async function wareEntfernen(gegenstandId: string) {
    await ausfuehren(() => haendlerApi.sortimentEntfernen(campaignId, haendlerId, gegenstandId));
  }

  function rabattBearbeiten(ware: SortimentEintrag) {
    setRabattBearbeitet(ware.gegenstandId);
    setRabattProzent(ware.rabattProzent ? String(ware.rabattProzent) : "");
    setRabattHinweis(ware.rabattHinweis ?? "");
  }

  async function rabattSpeichern(gegenstandId: string) {
    const prozent = rabattProzent.trim() ? Number(rabattProzent) : 0;
    await ausfuehren(() => haendlerApi.rabattSetzen(campaignId, haendlerId, gegenstandId, prozent, rabattHinweis.trim()));
    setRabattBearbeitet(null);
  }

  async function standortSetzen(ortId: string) {
    await ausfuehren(() => haendlerApi.standortSetzen(campaignId, haendlerId, ortId || null));
  }

  if (!haendler) {
    return (
      <Fenster offen={offen} titel="Händler bearbeiten" kennung={`haendler-bearb:${haendlerId}`} onSchliessen={onSchliessen}>
        <p className="shop-ware-hinweis">Lädt…</p>
      </Fenster>
    );
  }

  // Explizit eingetragene Ware kann entfernt/rabattiert werden, automatisch
  // gelistete Katalog-Vorlagen (automatischImShop) nicht — die hängen an der
  // globalen Vorlage bzw. der Spezialisierung, nicht an einer eigenen Kante
  // (siehe docs/api/haendler.md).
  const istExplizit = (gegenstandId: string) => !sortiment.find((s) => s.gegenstandId === gegenstandId)?.automatisch;

  return (
    <Fenster
      offen={offen}
      titel={`${haendler.name} bearbeiten`}
      unterzeile="Sortiment, Sonderangebote, Standort"
      kennung={`haendler-bearb:${haendlerId}`}
      breit
      onSchliessen={onSchliessen}
    >
      <div className="shop-editor">
        {fehler && <p className="shop-ware-fehler">{fehler}</p>}

        <section>
          <h3 className="gg-abschnitt">
            <span>Standort</span>
          </h3>
          <select
            value={haendler.ortId ?? ""}
            onChange={(e) => standortSetzen(e.target.value)}
            disabled={läuft}
          >
            <option value="">— kein fester Standort (nur per Messenger) —</option>
            {orte.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </section>

        <section>
          <h3 className="gg-abschnitt">
            <span>Sortiment</span>
            <span className="gg-abschnitt-zahl">{sortiment.length}</span>
          </h3>

          <div className="shop-editor-liste">
            {sortiment.map((ware) => (
              <div key={ware.gegenstandId} className="shop-editor-zeile">
                <span className="shop-editor-zeile-name">
                  {symbolFuerTyp(ware.typ)} {ware.name}
                  {ware.automatisch && <span className="shop-editor-marke">automatisch</span>}
                </span>
                <span className="shop-editor-zeile-preis">
                  {ware.rabattProzent > 0 && <s>{ware.preis.toLocaleString("de-AT")}¥</s>}{" "}
                  {Math.round(ware.preis * (1 - (ware.rabattProzent ?? 0) / 100)).toLocaleString("de-AT")}¥
                </span>
                {istExplizit(ware.gegenstandId) && (
                  <span className="shop-editor-zeile-knoepfe">
                    <button type="button" onClick={() => rabattBearbeiten(ware)} disabled={läuft}>
                      Rabatt
                    </button>
                    <button type="button" onClick={() => wareEntfernen(ware.gegenstandId)} disabled={läuft}>
                      Entfernen
                    </button>
                  </span>
                )}

                {rabattBearbeitet === ware.gegenstandId && (
                  <div className="shop-editor-rabatt-form">
                    <input
                      type="number"
                      min={0}
                      max={95}
                      value={rabattProzent}
                      onChange={(e) => setRabattProzent(e.target.value)}
                      placeholder="Prozent (0 = kein Rabatt)"
                    />
                    <input
                      value={rabattHinweis}
                      onChange={(e) => setRabattHinweis(e.target.value)}
                      placeholder="Hinweis (optional, z.B. „Wochenendaktion“)"
                    />
                    <div className="shop-ware-knoepfe">
                      <button type="button" onClick={() => setRabattBearbeitet(null)} disabled={läuft}>
                        Abbrechen
                      </button>
                      <button type="button" onClick={() => rabattSpeichern(ware.gegenstandId)} disabled={läuft}>
                        Speichern
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {sortiment.length === 0 && <p className="shop-leer">Noch keine Ware im Sortiment.</p>}
          </div>

          <div className="shop-editor-hinzufuegen">
            <select value={neueWareId} onChange={(e) => setNeueWareId(e.target.value)} disabled={läuft}>
              <option value="">— Vorlage wählen —</option>
              {wählbareVorlagen.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.preis.toLocaleString("de-AT")}¥)
                </option>
              ))}
            </select>
            <input
              type="number"
              min={0}
              value={neuerPreis}
              onChange={(e) => setNeuerPreis(e.target.value)}
              placeholder="Preis (leer = Grundpreis)"
            />
            <button type="button" onClick={wareHinzufuegen} disabled={läuft || !neueWareId}>
              Hinzufügen
            </button>
          </div>
          {wählbareVorlagen.length === 0 && (
            <p className="shop-ware-hinweis">
              Keine weiteren Vorlagen verfügbar — entweder ist schon alles eingetragen, oder es gibt noch keine
              Gegenstands-Vorlagen in dieser Kampagne.
            </p>
          )}
        </section>
      </div>
    </Fenster>
  );
}
