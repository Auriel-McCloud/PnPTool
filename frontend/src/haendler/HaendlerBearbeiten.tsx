import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { entitiesApi } from "../entities/api";
import { TypKachelAuswahl } from "../items/TypKachelAuswahl";
import { TYP_KATALOG, symbolFuerTyp } from "../items/typKatalog";
import "./shop.css";

/**
 * SL-Sortiment-Editor. Der Laden ist der Ort: Arten, Tutorial-Flag und
 * neue Ware werden hier gepflegt, nicht am NPC.
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
  onGeaendert: () => void;
}) {
  const [haendler, setHaendler] = useState<HaendlerEintrag | null>(null);
  const [sortiment, setSortiment] = useState<SortimentEintrag[]>([]);
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [läuft, setLäuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [hinweis, setHinweis] = useState<string | null>(null);
  const [kategorie, setKategorie] = useState<string | null>(null);
  const [wunsch, setWunsch] = useState("");
  const [mitBild, setMitBild] = useState(false);

  const [neueWareId, setNeueWareId] = useState("");
  const [neuerPreis, setNeuerPreis] = useState("");
  const [rabattBearbeitet, setRabattBearbeitet] = useState<string | null>(null);
  const [rabattProzent, setRabattProzent] = useState("");
  const [rabattHinweis, setRabattHinweis] = useState("");

  async function laden() {
    const [h, s, g] = await Promise.all([
      haendlerApi.einzeln(campaignId, haendlerId),
      haendlerApi.sortiment(campaignId, haendlerId),
      itemsApi.listAlle(campaignId),
    ]);
    setHaendler(h);
    setSortiment(s);
    setGegenstaende(g);
  }

  useEffect(() => {
    if (!offen) return;
    laden().catch(() => setFehler("Laden fehlgeschlagen"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId, haendlerId]);

  const spezialisierung = haendler?.spezialisierung ?? [];

  const sichtbaresSortiment = sortiment.filter((w) => kategorie === null || w.typ === kategorie);
  const wählbareVorlagen = useMemo(() => {
    const bereitsDrin = new Set(sortiment.map((s) => s.gegenstandId));
    return gegenstaende.filter(
      (g) => g.istVorlage && !bereitsDrin.has(g.id) && (kategorie === null || g.typ === kategorie),
    );
  }, [gegenstaende, sortiment, kategorie]);

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

  async function artenSetzen(neu: string[]) {
    setHinweis(null);
    await ausfuehren(() => entitiesApi.updateOrt(campaignId, haendlerId, { spezialisierung: neu }));
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

  async function mitKiAnlegen() {
    if (!kategorie || !wunsch.trim()) return;
    setHinweis(null);
    setLäuft(true);
    setFehler(null);
    try {
      const antwort = await haendlerApi.wareAnlegen(campaignId, haendlerId, wunsch.trim(), kategorie, mitBild);
      setWunsch("");
      setHinweis(
        antwort.bildHinweis
          ? `„${antwort.name}“ liegt für ${antwort.preis.toLocaleString("de-AT")}¥ im Regal. Bild: ${antwort.bildHinweis}`
          : `„${antwort.name}“ liegt für ${antwort.preis.toLocaleString("de-AT")}¥ im Regal.`,
      );
      await laden();
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Anlegen fehlgeschlagen");
    } finally {
      setLäuft(false);
    }
  }

  if (!haendler) {
    return (
      <Fenster offen={offen} titel="Laden bearbeiten" kennung={`haendler-bearb:${haendlerId}`} onSchliessen={onSchliessen}>
        <p className="shop-ware-hinweis">Lädt…</p>
      </Fenster>
    );
  }

  const istExplizit = (gegenstandId: string) => !sortiment.find((s) => s.gegenstandId === gegenstandId)?.automatisch;

  return (
    <Fenster
      offen={offen}
      titel={`${haendler.name} bearbeiten`}
      unterzeile="Arten und Ware — alles am Ort"
      kennung={`haendler-bearb:${haendlerId}`}
      breit
      onSchliessen={onSchliessen}
    >
      <div className="shop-editor">
        {fehler && <p className="shop-ware-fehler">{fehler}</p>}
        {hinweis && <p className="shop-ware-erfolg">{hinweis}</p>}

        <section>
          <h3 className="gg-abschnitt">
            <span>Führt diese Arten</span>
          </h3>
          <p className="shop-ware-hinweis">
            Keine Kachel = Gemischtwarenladen. Leuchtende Arten beschränken nur den automatischen Katalog — explizit
            angelegte Ware bleibt trotzdem drin.
          </p>
          <TypKachelAuswahl
            gewaehlt={spezialisierung}
            disabled={läuft}
            onWaehlen={(typ) =>
              artenSetzen(
                spezialisierung.includes(typ) ? spezialisierung.filter((t) => t !== typ) : [...spezialisierung, typ],
              )
            }
          />
        </section>

        <section>
          <h3 className="gg-abschnitt">
            <span>Sortiment</span>
            <span className="gg-abschnitt-zahl">{sichtbaresSortiment.length}</span>
          </h3>
          <div className="shop-kategorien-raster">
            <button
              type="button"
              className="shop-kategorie-kachel"
              data-aktiv={kategorie === null}
              onClick={() => setKategorie(null)}
            >
              <span className="shop-kategorie-symbol" aria-hidden="true">
                ✦
              </span>
              <span>Alle</span>
            </button>
            {TYP_KATALOG.map((eintrag) => (
              <button
                key={eintrag.typ}
                type="button"
                className="shop-kategorie-kachel"
                data-aktiv={kategorie === eintrag.typ}
                onClick={() => setKategorie(eintrag.typ)}
              >
                <span className="shop-kategorie-symbol" aria-hidden="true">
                  {eintrag.symbol}
                </span>
                <span>{eintrag.typ}</span>
              </button>
            ))}
          </div>

          {kategorie && (
            <div className="shop-editor-hinzufuegen" style={{ marginTop: 12, flexWrap: "wrap" }}>
              <input
                value={wunsch}
                onChange={(e) => setWunsch(e.target.value)}
                placeholder={`Neu in ${kategorie} — z.B. „billige Taschenlampe“`}
                disabled={läuft}
                onKeyDown={(e) => e.key === "Enter" && mitKiAnlegen()}
              />
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
                <input type="checkbox" checked={mitBild} onChange={(e) => setMitBild(e.target.checked)} disabled={läuft} />
                Bild dazu
              </label>
              <button type="button" onClick={mitKiAnlegen} disabled={läuft || !wunsch.trim()}>
                {läuft ? "Legt an…" : "Mit KI anlegen"}
              </button>
            </div>
          )}
          {!kategorie && (
            <p className="shop-ware-hinweis">Kategorie wählen, dann die Ware dort direkt anlegen — Preis setzt die KI.</p>
          )}

          <div className="shop-editor-liste">
            {sichtbaresSortiment.map((ware) => (
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
                      placeholder="Hinweis (optional)"
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
            {sichtbaresSortiment.length === 0 && <p className="shop-leer">In dieser Ansicht liegt noch nichts.</p>}
          </div>

          <div className="shop-editor-hinzufuegen">
            <select value={neueWareId} onChange={(e) => setNeueWareId(e.target.value)} disabled={läuft}>
              <option value="">— bestehende Vorlage —</option>
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
        </section>
      </div>
    </Fenster>
  );
}
