import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { entitiesApi } from "../entities/api";
import { TypKachelAuswahl } from "../items/TypKachelAuswahl";
import { TYP_KATALOG, symbolFuerTyp } from "../items/typKatalog";
import { VorlagenAuswahlPopup } from "./VorlagenAuswahlPopup";
import { UnikatAnlegenPopup } from "./UnikatAnlegenPopup";
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
  const [nurEinmal, setNurEinmal] = useState(false);

  const [auswahlOffen, setAuswahlOffen] = useState(false);
  const [unikatOffen, setUnikatOffen] = useState(false);
  const [weltOffen, setWeltOffen] = useState(false);
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
      (g) =>
        g.istVorlage &&
        !g.einzigartig &&
        !g.storyRelevant &&
        !bereitsDrin.has(g.id) &&
        (kategorie === null || g.typ === kategorie),
    );
  }, [gegenstaende, sortiment, kategorie]);
  const wählbareUnikate = useMemo(() => {
    const bereitsDrin = new Set(sortiment.map((s) => s.gegenstandId));
    return gegenstaende.filter(
      (g) =>
        !bereitsDrin.has(g.id) &&
        g.ownerPersonType !== "PC" &&
        (!g.istVorlage || g.einzigartig || g.storyRelevant) &&
        (kategorie === null || g.typ === kategorie),
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

  async function unikateHinzufuegen(gegenstandIds: string[], preis?: number) {
    for (const id of gegenstandIds) {
      await haendlerApi.unikatEinhaengen(campaignId, haendlerId, id, preis);
    }
    await laden();
    onGeaendert();
  }

  async function unikatVonHand(name: string, preis: number, description: string) {
    if (!kategorie) return;
    await haendlerApi.unikatAnlegen(campaignId, haendlerId, name, kategorie, preis, description);
    await laden();
    onGeaendert();
  }

  async function vorlagenHinzufuegen(gegenstandIds: string[], preis?: number) {
    for (const id of gegenstandIds) {
      await haendlerApi.sortimentHinzufuegen(campaignId, haendlerId, id, preis);
    }
    await laden();
    onGeaendert();
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
      const antwort = await haendlerApi.wareAnlegen(
        campaignId,
        haendlerId,
        wunsch.trim(),
        kategorie,
        mitBild,
        nurEinmal,
      );
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
              <button type="button" data-aktiv={nurEinmal} onClick={() => setNurEinmal((v) => !v)} disabled={läuft}>
                {nurEinmal ? "Nur einmal" : "Vorlage (unendlich)"}
              </button>
              <button type="button" onClick={mitKiAnlegen} disabled={läuft || !wunsch.trim()}>
                {läuft ? "Legt an…" : "Mit KI anlegen"}
              </button>
              <button type="button" onClick={() => setUnikatOffen(true)} disabled={läuft}>
                Von Hand, nur einmal
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
                  {!ware.istVorlage && <span className="shop-editor-marke">Einzelstück</span>}
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
            <button type="button" onClick={() => setAuswahlOffen(true)} disabled={läuft} style={{ flex: 1 }}>
              Vorlage(n) wählen — unendlich
            </button>
            <button type="button" onClick={() => setWeltOffen(true)} disabled={läuft} style={{ flex: 1 }}>
              Einzelstück aus der Welt
            </button>
          </div>

          <VorlagenAuswahlPopup
            offen={auswahlOffen}
            vorlagen={wählbareVorlagen}
            onHinzufuegen={vorlagenHinzufuegen}
            onSchliessen={() => setAuswahlOffen(false)}
          />
          <VorlagenAuswahlPopup
            offen={weltOffen}
            vorlagen={wählbareUnikate}
            titel="Einzelstück wählen"
            leertext="Kein passendes Einzelstück. Spielerbesitz und kopierbare Vorlagen bleiben draußen."
            kennung="unikat-auswahl"
            onHinzufuegen={unikateHinzufuegen}
            onSchliessen={() => setWeltOffen(false)}
          />
          {kategorie && (
            <UnikatAnlegenPopup
              offen={unikatOffen}
              typ={kategorie}
              onAnlegen={unikatVonHand}
              onSchliessen={() => setUnikatOffen(false)}
            />
          )}
        </section>
      </div>
    </Fenster>
  );
}
