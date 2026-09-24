import { useEffect, useState } from "react";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { verhandlungApi } from "../verhandlung/api";
import { ShopWare } from "./ShopWare";
import { HaendlerBearbeiten } from "./HaendlerBearbeiten";
import "./shop.css";

/**
 * Die Seite eines einzelnen Shops — Optik hängt komplett an der Vertriebsart
 * (Marks Vorgabe 24.09.2026, siehe docs/api/haendler.md):
 *
 * - PHYSISCH: "Fancy" — eigenes Hintergrundbild als Kulisse, Händlerporträt,
 *   Verhandeln möglich, Ware sofort im Inventar.
 * - DIGITAL: schlichte Online-Shop-Optik, kein Verhandeln, Kauf legt eine
 *   Bestellung an — die SL gibt die Lieferung später manuell frei.
 */
export function ShopSeite({
  campaignId,
  haendlerId,
  eigenePersonId,
  istGm,
  onSchliessen,
}: {
  campaignId: string;
  haendlerId: string;
  /** Für wen gekauft wird — bei der SL kommt das aus der Personenauswahl
   * des Aufrufers, ein Spieler kauft immer für sich selbst (Server ignoriert
   * kaeuferPersonId ohnehin für Spieler, siehe haendler/routes.py). */
  eigenePersonId: string | null;
  istGm: boolean;
  onSchliessen: () => void;
}) {
  const [haendler, setHaendler] = useState<HaendlerEintrag | null>(null);
  const [sortiment, setSortiment] = useState<SortimentEintrag[]>([]);
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [fehler, setFehler] = useState<string | null>(null);
  const [erfolg, setErfolg] = useState<string | null>(null);
  const [bearbeitenOffen, setBearbeitenOffen] = useState(false);

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
    laden();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, haendlerId]);

  if (!haendler) return null;

  const seltenheitVon = (gegenstandId: string) =>
    gegenstaende.find((g) => g.id === gegenstandId)?.seltenheit ?? 1;

  const istDigital = haendler.vertriebsart === "DIGITAL";

  async function kaufen(gegenstandId: string) {
    setFehler(null);
    setErfolg(null);
    try {
      const antwort = await haendlerApi.kaufen(campaignId, haendlerId, gegenstandId, eigenePersonId ?? undefined);
      if (antwort.bestellung) {
        setErfolg(`Bestellt! ${antwort.bestellung.gegenstandName} ist unterwegs — deine Spielleitung gibt Bescheid, wenn es ankommt.`);
      } else {
        setErfolg("Gekauft!");
      }
      await laden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Kauf fehlgeschlagen");
      throw e;
    }
  }

  async function verhandeln(ware: SortimentEintrag, vorgeschlagenerPreis: number) {
    if (!eigenePersonId) return;
    // Der Spieler schlägt vor — Backend/SL-Popup entscheidet über die
    // Annahme. Kontext trägt haendlerId+gegenstandId, damit
    // verhandlung/logic.py::_ausfuehren_shop_kauf den Kauf später ausführen
    // kann (siehe backend/app/verhandlung/logic.py).
    await verhandlungApi.anbieten(campaignId, {
      empfaengerPersonId: eigenePersonId,
      art: "SHOP_KAUF",
      positionen: [{ bezeichnung: ware.name, betrag: vorgeschlagenerPreis }],
      kontext: { haendlerId, gegenstandId: ware.gegenstandId },
    });
  }

  // --- KI-Alltagswunsch (24.09.2026, nur Spieler) ---------------------------
  // Fragt nach etwas, das nicht im Sortiment steht. Kein Warten nötig — die
  // KI antwortet sofort, die Anfrage geht parallel als Popup an die SL
  // (siehe AlltagswunschFreigabePopup). NIE für Waffen/Rüstung, harter
  // Backend-Filter, siehe app/haendler/alltagswunsch.py.
  const [wunschText, setWunschText] = useState("");
  const [wunschLäuft, setWunschLäuft] = useState(false);
  const [wunschRückmeldung, setWunschRückmeldung] = useState<string | null>(null);

  async function wunschStellen() {
    const text = wunschText.trim();
    if (!text) return;
    setWunschLäuft(true);
    setWunschRückmeldung(null);
    try {
      const antwort = await haendlerApi.alltagswunschStellen(campaignId, haendlerId, text);
      if (antwort.status === "AUTO_ABGELEHNT") {
        setWunschRückmeldung(antwort.ablehnungsGrund || "Das führt dieser Verkäufer nicht.");
      } else {
        setWunschRückmeldung(`„${antwort.vorschlagName}“ (${antwort.vorschlagPreis}¥) wartet auf die Freigabe deiner Spielleitung.`);
      }
      setWunschText("");
    } catch (e) {
      setWunschRückmeldung(e instanceof Error ? e.message : "Anfrage fehlgeschlagen");
    } finally {
      setWunschLäuft(false);
    }
  }

  return (
    <div className="shop-seite">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button type="button" onClick={onSchliessen} className="shop-zurueck">
          ← Zurück zur Übersicht
        </button>
        {istGm && (
          <button type="button" onClick={() => setBearbeitenOffen(true)}>
            Bearbeiten
          </button>
        )}
      </div>

      {istDigital ? (
        <div className="shop-kopf-digital">
          <span className="shop-kopf-digital-symbol" aria-hidden="true">▤</span>
          <div>
            <h2>{haendler.name}</h2>
            <p className="shop-kopf-digital-hinweis">Online-Bestellung — Lieferung erfolgt verzögert, sobald deine Spielleitung sie freigibt.</p>
          </div>
        </div>
      ) : (
        <div
          className="shop-kopf-physisch"
          data-hat-bild={Boolean(haendler.shopHintergrundUrl)}
          style={{ "--shop-bild": haendler.shopHintergrundUrl ? `url(${haendler.shopHintergrundUrl})` : "none" } as React.CSSProperties}
        >
          {haendler.bildUrl && <img className="shop-haendler-portrait" src={haendler.bildUrl} alt="" />}
          <div className="shop-kopf-text">
            <h2>{haendler.name}</h2>
            {haendler.beschreibung && <p>{haendler.beschreibung}</p>}
          </div>
        </div>
      )}

      {fehler && <p className="shop-ware-fehler">{fehler}</p>}
      {erfolg && <p className="shop-ware-erfolg">{erfolg}</p>}

      <div className="shop-waren-raster">
        {sortiment.map((ware) => (
          <ShopWare
            key={ware.gegenstandId}
            ware={ware}
            seltenheit={seltenheitVon(ware.gegenstandId)}
            kannVerhandeln={!istDigital && !istGm}
            onKaufen={() => kaufen(ware.gegenstandId)}
            onVerhandelnAnfragen={
              !istDigital && !istGm ? (preis) => verhandeln(ware, preis) : undefined
            }
          />
        ))}
        {sortiment.length === 0 && <p className="shop-leer">Dieser Shop führt gerade nichts.</p>}
      </div>

      {!istGm && (
        <div className="shop-alltagswunsch">
          <p className="shop-alltagswunsch-titel">Etwas Bestimmtes gesucht?</p>
          <p className="shop-ware-hinweis">
            Frag {haendler.name} nach einem Alltagsgegenstand, der nicht im Regal steht — z.B. „Hast du
            Panzerklebeband?“. Waffen und Rüstung führt dieser Weg nie.
          </p>
          <div className="shop-alltagswunsch-zeile">
            <input
              value={wunschText}
              onChange={(e) => setWunschText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && wunschStellen()}
              placeholder="Hast du…?"
              disabled={wunschLäuft}
            />
            <button type="button" onClick={wunschStellen} disabled={wunschLäuft || !wunschText.trim()}>
              Fragen
            </button>
          </div>
          {wunschRückmeldung && <p className="shop-ware-erfolg">{wunschRückmeldung}</p>}
        </div>
      )}

      {istGm && (
        <HaendlerBearbeiten
          campaignId={campaignId}
          haendlerId={haendlerId}
          offen={bearbeitenOffen}
          onSchliessen={() => setBearbeitenOffen(false)}
          onGeaendert={laden}
        />
      )}
    </div>
  );
}
