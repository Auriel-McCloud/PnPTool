import { useEffect, useRef, useState } from "react";
import { haendlerApi, type HaendlerEintrag, type PetSortimentEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { entitiesApi, type CritterEintrag } from "../entities/api";
import { rassenApi, type Rasse } from "../rassen/api";
import { ShopWarenkorb } from "./ShopWarenkorb";
import { abgleichen, postenBerechnen, useWarenkorb, type WarenkorbZeile } from "./warenkorb";
import { useNachladen } from "../shell/nachladen";
import { verhandlungApi } from "../verhandlung/api";
import { ShopWare } from "./ShopWare";
import { ShopPet } from "./ShopPet";
import { ShopKategorien } from "./ShopKategorien";
import { ShopSortierleiste, gueltigesFeld, sortimentSortieren, type SortierRichtung } from "./ShopSortierung";
import { HaendlerBearbeiten } from "./HaendlerBearbeiten";
import { extrahiereReinenText } from "../richtext/content";
import "./shop.css";
import { vorschau } from "../shell/vorschau";

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
  const [pets, setPets] = useState<PetSortimentEintrag[]>([]);
  const [meineCritter, setMeineCritter] = useState<CritterEintrag[]>([]);
  const [fehler, setFehler] = useState<string | null>(null);
  const [erfolg, setErfolg] = useState<string | null>(null);
  const [bearbeitenOffen, setBearbeitenOffen] = useState(false);
  // Reiter (18.11.2026, Tierladen): "pets" nur wählbar, wenn es überhaupt
  // etwas zu kaufen gibt UND der Käufer noch keinen Begleiter hat (Mark:
  // sonst ist der Reiter für ihn irrelevant) — siehe `zeigePetsReiter` unten.
  const [ansicht, setAnsicht] = useState<"waren" | "pets">("waren");
  // Kategorie-Filter (10.10.2026, Marks Vorgabe): erst Kategorie wählen,
  // dann das Sortiment dieser Kategorie. null = "Alle".
  const [kategorie, setKategorie] = useState<string | null>(null);
  // Sortierung (24.10.2026, Marks Wunsch): Basis-Felder + je Kategorie
  // zusätzlich die passenden Steckbrief-Werte, siehe ShopSortierung.tsx.
  const [sortierFeld, setSortierFeld] = useState("preis");
  const [sortierRichtung, setSortierRichtung] = useState<SortierRichtung>("auf");

  // Fällt auf "Preis" zurück, wenn ein Kategoriewechsel das bisher gewählte
  // Feld ungültig macht (z.B. "Schaden" beim Wechsel von Waffe auf Rüstung).
  useEffect(() => {
    setSortierFeld((f) => gueltigesFeld(f, kategorie, sortiment));
  }, [kategorie, sortiment]);
  // Kapital des Käufers (20.11.2026) + Rassen-Feature „erster Kauf gratis“
  // für die Warenkorb-Rechnung. null = unbekannt/kein Käufer.
  const [kaeufer, setKaeufer] = useState<KaeuferInfo | null>(null);
  const rassenCache = useRef<Rasse[] | null>(null);

  // Warenkorb (20.11.2026): Client-Stand pro Kampagne + Laden + Käufer in
  // localStorage, siehe warenkorb.ts. Bezahlt wird erst an der Kasse.
  const warenkorb = useWarenkorb(campaignId, haendlerId, eigenePersonId);
  const zeilenRef = useRef<WarenkorbZeile[]>(warenkorb.zeilen);
  zeilenRef.current = warenkorb.zeilen;
  const [korbHinweis, setKorbHinweis] = useState<string | null>(null);
  const [korbFehler, setKorbFehler] = useState<string | null>(null);
  const [korbLaeuft, setKorbLaeuft] = useState(false);

  /** Eigener try/catch, NICHT im Promise.all unten: scheitert das Kapital
   * (Rechte, Netz), darf der Laden trotzdem nicht leer bleiben. */
  async function kaeuferHolen(): Promise<KaeuferInfo | null> {
    if (!eigenePersonId) return null;
    try {
      const person = await entitiesApi.getPerson(campaignId, eigenePersonId);
      let gratisTyp = "";
      if (person.rasse && !person.rassenFeatureGenutzt) {
        try {
          if (!rassenCache.current) rassenCache.current = await rassenApi.verfuegbar(campaignId);
          gratisTyp = rassenCache.current.find((r) => r.name === person.rasse)?.gratisErsterKaufTyp ?? "";
        } catch {
          gratisTyp = "";
        }
      }
      return { kapital: person.kapital ?? 0, name: person.name, gratisTyp };
    } catch {
      return null;
    }
  }

  async function holen() {
    const kaeuferInfo = kaeuferHolen();
    const [h, s, g, p, mc] = await Promise.all([
      haendlerApi.einzeln(campaignId, haendlerId),
      haendlerApi.sortiment(campaignId, haendlerId),
      itemsApi.listAlle(campaignId),
      haendlerApi.petsSortiment(campaignId, haendlerId),
      entitiesApi.meineCritter(campaignId),
    ]);
    return { h, s, g, p, mc, k: await kaeuferInfo };
  }

  function anwenden(d: {
    h: HaendlerEintrag;
    s: SortimentEintrag[];
    g: GegenstandMitBesitzer[];
    p: PetSortimentEintrag[];
    mc: CritterEintrag[];
    k: KaeuferInfo | null;
  }) {
    setHaendler(d.h);
    setSortiment(d.s);
    setGegenstaende(d.g);
    setPets(d.p);
    setMeineCritter(d.mc);
    // Nur überschreiben, wenn das Nachladen geklappt hat — ein Netz-
    // aussetzer soll das zuletzt bekannte Kapital nicht wegwischen.
    if (d.k) setKaeufer(d.k);
    // Verschwundene Ware fliegt aus dem Korb, mit kurzem Hinweis.
    const { entfernt } = abgleichen(zeilenRef.current, d.s);
    if (entfernt.length > 0) {
      const namen = entfernt.map((n) => `„${n}“`).join(", ");
      setKorbHinweis(`${namen} gibt es hier nicht mehr — aus dem Warenkorb genommen.`);
    }
    warenkorb.aendern((z) => abgleichen(z, d.s).zeilen);
  }

  // Pause, solange die SL das Sortiment bearbeitet — das Fenster hat
  // eigenen Stand und darf nicht unter ihr neu aufgehen.
  const { ungueltig } = useNachladen(holen, anwenden, {
    pausiert: bearbeitenOffen,
    quelle: `${campaignId}:${haendlerId}:${eigenePersonId ?? ""}`,
  });

  async function laden() {
    ungueltig();
    const d = await holen();
    ungueltig();
    anwenden(d);
  }

  if (!haendler) return null;

  const seltenheitVon = (gegenstandId: string) =>
    gegenstaende.find((g) => g.id === gegenstandId)?.seltenheit ?? 1;

  const istDigital = haendler.vertriebsart === "DIGITAL";
  // Reiter nur zeigen, wenn es wirklich etwas zu kaufen gibt UND der
  // Käufer noch keinen Begleiter hat (Mark, 18.11.2026) — sonst ist der
  // Reiter irrelevant. meineCritter ist für die SL ohne eigenen Charakter
  // immer leer, der Reiter zeigt sich ihr also schon bei leerem Angebot nicht.
  const zeigePetsReiter = pets.length > 0 && meineCritter.length === 0;

  const posten = postenBerechnen(warenkorb.zeilen, sortiment, kaeufer?.gratisTyp ?? "");
  const warenkorbSumme = posten.reduce((s, p) => s + p.summe, 0);

  async function bezahlen() {
    if (warenkorb.zeilen.length === 0) return;
    setFehler(null);
    setErfolg(null);
    setKorbFehler(null);
    setKorbHinweis(null);
    setKorbLaeuft(true);
    ungueltig();
    try {
      const antwort = await haendlerApi.kaufenWarenkorb(
        campaignId,
        haendlerId,
        warenkorb.zeilen.map((z) => ({ gegenstandId: z.gegenstandId, anzahl: z.anzahl })),
        eigenePersonId ?? undefined,
      );
      setKaeufer((k) => (k ? { ...k, kapital: antwort.kapitalNeu } : k));
      const bezahlt = new Set(antwort.gekauft.map((z) => z.gegenstandId));
      warenkorb.aendern((z) => z.filter((x) => !bezahlt.has(x.gegenstandId)));
      const liste = antwort.gekauft.map((z) => `${z.anzahl}× ${z.name}`).join(", ");
      let text = istDigital
        ? `Bestellt und bezahlt (${antwort.bezahlt.toLocaleString("de-AT")}¥): ${liste} — deine Spielleitung gibt Bescheid, wenn es ankommt.`
        : `Gekauft für ${antwort.bezahlt.toLocaleString("de-AT")}¥: ${liste} — liegt in deinem Inventar.`;
      if (antwort.fehlgeschlagen.length > 0) {
        text += ` Nicht geklappt (Geld zurück, bleibt im Warenkorb): ${antwort.fehlgeschlagen
          .map((z) => `${z.anzahl}× ${z.name}`)
          .join(", ")}.`;
      }
      setErfolg(text);
      await laden();
    } catch (e) {
      setKorbFehler(e instanceof Error ? e.message : "Bezahlen fehlgeschlagen");
    } finally {
      setKorbLaeuft(false);
    }
  }

  async function kaufenPet(critterId: string) {
    setFehler(null);
    setErfolg(null);
    ungueltig();
    try {
      await haendlerApi.petKaufen(campaignId, haendlerId, critterId, eigenePersonId ?? undefined);
      setErfolg("Gekauft! Dein neuer Begleiter wartet in der Begleiter-Übersicht.");
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
          {(haendler.haendler ?? []).filter((g) => g.bildUrl).map((g) => (
            <img key={g.id} className="shop-haendler-portrait" src={vorschau(g.bildUrl)} loading="lazy" decoding="async" alt={g.name} />
          ))}
          {!(haendler.haendler ?? []).some((g) => g.bildUrl) && haendler.bildUrl && (
            <img className="shop-haendler-portrait" src={vorschau(haendler.bildUrl)} loading="lazy" decoding="async" alt="" />
          )}
          <div className="shop-kopf-text">
            <h2>{haendler.name}</h2>
            {haendler.beschreibung && <p>{extrahiereReinenText(haendler.beschreibung)}</p>}
          </div>
        </div>
      )}

      {eigenePersonId && (
        <div className="shop-kasse">
          {kaeufer && (
            <p className="shop-kapital">
              <span>{istGm ? `Kapital von ${kaeufer.name}` : "Dein Kapital"}</span>
              <strong>{kaeufer.kapital.toLocaleString("de-AT")}¥</strong>
            </p>
          )}
          <ShopWarenkorb
            posten={posten}
            kapital={kaeufer ? kaeufer.kapital : null}
            digital={istDigital}
            laeuft={korbLaeuft}
            fehler={korbFehler}
            hinweis={korbHinweis}
            onAnzahl={(id, n) => {
              setKorbFehler(null);
              warenkorb.anzahlSetzen(id, n);
            }}
            onEntfernen={(id) => {
              setKorbFehler(null);
              warenkorb.entfernen(id);
            }}
            onLeeren={() => {
              setKorbFehler(null);
              warenkorb.leeren();
            }}
            onBezahlen={bezahlen}
          />
        </div>
      )}

      {fehler && <p className="shop-ware-fehler">{fehler}</p>}
      {erfolg && <p className="shop-ware-erfolg">{erfolg}</p>}

      {zeigePetsReiter && (
        <div className="shop-kategorien-raster" style={{ marginBottom: 4 }}>
          <button type="button" className="shop-kategorie-kachel" data-aktiv={ansicht === "waren"} onClick={() => setAnsicht("waren")}>
            <span>Waren</span>
          </button>
          <button type="button" className="shop-kategorie-kachel" data-aktiv={ansicht === "pets"} onClick={() => setAnsicht("pets")}>
            <span>Pets</span>
            <span className="gg-abschnitt-zahl">{pets.length}</span>
          </button>
        </div>
      )}

      {ansicht === "pets" && zeigePetsReiter ? (
        <div className="shop-waren-raster">
          {pets.map((pet) => (
            <ShopPet key={pet.critterId} pet={pet} onKaufen={() => kaufenPet(pet.critterId)} />
          ))}
          {pets.length === 0 && <p className="shop-leer">Dieser Laden führt gerade kein Pet.</p>}
        </div>
      ) : (
        <div className="shop-waren-raster">
          <ShopKategorien sortiment={sortiment} gewaehlt={kategorie} onWaehlen={setKategorie} />
          <ShopSortierleiste
            sortiment={sortiment}
            kategorie={kategorie}
            feld={sortierFeld}
            richtung={sortierRichtung}
            onAendern={(f, r) => {
              setSortierFeld(f);
              setSortierRichtung(r);
            }}
          />
          {sortimentSortieren(
            sortiment.filter((ware) => kategorie === null || ware.typ === kategorie),
            sortierFeld,
            sortierRichtung,
          ).map((ware) => (
            <ShopWare
              key={ware.gegenstandId}
              ware={ware}
              seltenheit={seltenheitVon(ware.gegenstandId)}
              kannVerhandeln={!istDigital && !istGm}
              imWarenkorb={warenkorb.zeilen.find((z) => z.gegenstandId === ware.gegenstandId)?.anzahl ?? 0}
              warenkorbAktiv={warenkorb.aktiv}
              kapital={kaeufer ? kaeufer.kapital : null}
              warenkorbSumme={warenkorbSumme}
              onInDenWarenkorb={(anzahl) => {
                setErfolg(null);
                setKorbFehler(null);
                setKorbHinweis(null);
                warenkorb.hinzufuegen(ware, anzahl);
              }}
              onVerhandelnAnfragen={
                !istDigital && !istGm ? (preis) => verhandeln(ware, preis) : undefined
              }
            />
          ))}
          {sortiment.length === 0 && <p className="shop-leer">Dieser Shop führt gerade nichts.</p>}
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

interface KaeuferInfo {
  kapital: number;
  name: string;
  /** gratisErsterKaufTyp der Rasse, solange das Feature unverbraucht ist. */
  gratisTyp: string;
}
