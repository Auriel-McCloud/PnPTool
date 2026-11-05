import { useEffect, useState } from "react";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Fenster } from "../shell/Fenster";
import { FormelText, formelKlartext } from "../shell/formelText";
import { DotPool } from "../traits/DotPool";
import { StufenBlatt } from "../traits/StufenBlatt";
import type { Ablage, AblageZiel, Gegenstand } from "./api";
import { SCHADEN_MAX, istVerschlossen, itemsApi } from "./api";
import { DROGE_GESCHLUCKT } from "../kampf/BoosterPopup";
import { SchlossOeffnen } from "./SchlossOeffnen";
import { steckbriefKurz } from "./steckbrief";
import { WegwerfenFrage } from "./WegwerfenFrage";
import { WeitergebenPopup } from "./WeitergebenPopup";
import { ZusammenlegenPopup } from "./ZusammenlegenPopup";
import { CredstickPopup } from "./CredstickPopup";
import { ApiError } from "../api/client";
import "./wegwerfen.css";

/**
 * Ein Gegenstand aus Spielersicht: Kachel, die sich zum Fenster öffnet.
 *
 * Bewusst nicht `GegenstandRow` der Spielleitung — die trägt Sichtbarkeit,
 * Besitzerwechsel, Vorlagen und Bild-Upload mit sich, von denen ein Spieler
 * nichts sehen soll und nichts darf.
 *
 * **Das Umlegen sitzt im Fenster, nicht an der Kachel.** Vorher stand unter
 * jedem Eintrag der Liste ein Knopfpaar "→ Rucksack / → Gelagert"; das war
 * die einzige Handlung, die überhaupt hervorstach, und machte die Übersicht
 * zur Knopfwand. Wo etwas liegt, entscheidet man beim Ansehen des Dings.
 */

/** Bekommen ein eigenes Blatt (Neotopia.xlsx, Blatt "Drohne/Fahrzeug"). */
const FAHRZEUGTYPEN = new Set(["Fahrzeug", "Drohne"]);

/**
 * Die beiden festen Ablagen ohne eigenes Ziel — "wo es steckt" jenseits
 * eines konkreten Behälters. Welche(r) Behälter zusätzlich wählbar ist,
 * kommt nicht mehr von hier, sondern live aus `itemsApi.ablageziele`
 * (31.10.2026, Mark: "ich habe einen Charakter der mehr als einen Behälter
 * hat [...] ich habe nicht die Möglichkeit einen anderen Behälter zu
 * wählen" — vorher gab es hartcodiert genau EINEN RUCKSACK-Knopf, benannt
 * nach dem ersten gefundenen getragenen Behälter. Jetzt listet die Kachel
 * jeden eigenen Behälter einzeln, über GELAGERT+Ziel-ID — denselben
 * Mechanismus, den auch `BehaelterHineinlegenPopup` nutzt).
 */
function grundAblagen(): { wert: Ablage; label: string; symbol: string; erklaerung: string }[] {
  return [
    { wert: "AUSGERUESTET", label: "Am Körper", symbol: "⚔", erklaerung: "Griffbereit, ohne etwas aufmachen zu müssen." },
    {
      wert: "RUCKSACK",
      label: "Mitgeführt",
      // 31.10.2026, Mark: die Hand (✋) sah auf den meisten Systemen gelb
      // eingefärbt, genau wie 🤝 beim Weitergeben-Knopf — kaum zu
      // unterscheiden. Das Kastl-Symbol übernimmt jetzt hier die Rolle "kein
      // bestimmter Behälter", während die echten Behälter unten (ziele) das
      // Rucksack-Symbol zurückbekommen, das vorher hier stand.
      symbol: "▣",
      erklaerung: "Dabei, aber in keinem bestimmten Behälter — am Gürtel oder in der Hand.",
    },
  ];
}

export function GegenstandKachel({
  item,
  onUmlegen,
  onChirurgie,
  onWegwerfen,
  onWeitergeben,
  campaignId,
  eigenePersonId,
  inhalt,
  onZusammengelegt,
  montierteUpgrades,
  onGeoeffnet,
  istSpielleitung = false,
}: {
  item: Gegenstand;
  /** Nur bei Behältern und Fahrzeugen: hineinsehen, in einem weiteren Fenster. */
  inhalt?: { anzahl: number; oeffnen: () => void };
  /**
   * Die einzige Änderung, die ein Spieler an einem Gegenstand vornehmen darf.
   * Fehlt sie, ist der Gegenstand nur anzusehen — so bei fremdem Besitz.
   */
  onUmlegen?: (ablage: Ablage, zielId?: string | null) => Promise<void> | void;
  /** Nur SL: einsetzen (true) oder chirurgisch entfernen (false). */
  onChirurgie?: (einsetzen: boolean) => Promise<void> | void;
  /**
   * Wegwerfen. Fehlt sie, erscheint der Mistkübel gar nicht — bei fremdem
   * Besitz soll man nichts entsorgen können, was einem nicht gehört.
   * Löscht nichts; die Rückfrage davor stellt diese Komponente selbst.
   */
  onWegwerfen?: () => Promise<void> | void;
  /**
   * Weitergeben an ein Party-Mitglied. Fehlt sie, erscheint der Knopf gar
   * nicht — genau wie beim Wegwerfen nur am eigenen Besitz sinnvoll.
   * Zusammen mit `campaignId`/`eigenePersonId` nötig, weil das Popup selbst
   * die Party-Mitglieder nachlädt (verhandlung/routes.py::gegenstand_weitergeben
   * prüft serverseitig ohnehin noch einmal, wer wirklich in derselben
   * Party ist — das hier ist nur die Auswahl-Anzeige).
   */
  onWeitergeben?: (empfaengerPersonId: string) => Promise<void> | void;
  campaignId?: string;
  eigenePersonId?: string;
  /**
   * Mehrere gleiche Stücke zu einem Stapel zusammenlegen (26.10.2026, Mark:
   * "das müssen unbedingt auch die Spieler können"). Fehlt sie, erscheint
   * der Knopf gar nicht — genau wie bei Wegwerfen/Weitergeben nur am eigenen
   * Besitz sinnvoll. Das Popup spricht selbst mit der API (Backend prüft den
   * Besitz ohnehin nochmal serverseitig); diese Funktion ruft nur nach.
   */
  onZusammengelegt?: () => void;
  /**
   * Namen der Upgrades, die aktuell in diesem Gegenstand verbaut sind
   * (29.10.2026, Mark: "frage ich mich ob ich von außen sehen werde welche
   * Upgrades in der Waffe verbaut sind" — vorher nur in der Werkbank sichtbar).
   * Der Aufrufer ermittelt das aus der eigenen Gegenstandsliste
   * (`andere.filter(g => g.montiertAnId === item.id)`), diese Kachel kennt
   * die Liste der Geschwister-Gegenstände selbst nicht.
   */
  montierteUpgrades?: string[];
  /** Nach erfolgreichem Öffnen die Liste neu holen. */
  onGeoeffnet?: () => void;
  /**
   * Credstick (05.11.2026): nur die SL bekommt den Knopf "Geld erzeugen"
   * (ohne Kapitalabzug, für NPC-Belohnungen/Fundstücke). Laden/Entladen
   * selbst sind kein SL-Privileg — die erscheinen für jeden, der den
   * Credstick bearbeiten darf (siehe `onUmlegen`).
   */
  istSpielleitung?: boolean;
}) {
  // Cyber-, Bio- und Hexware sind Implantate, keine Ausrüstung.
  const CHROM = ["Cyberware", "Bioware", "Hexware"];
  const istChrom = CHROM.includes(item.typ);

  const [offen, setOffen] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [schluckText, setSchluckText] = useState<string | null>(null);
  const [frageOffen, setFrageOffen] = useState(false);
  const [weitergebenOffen, setWeitergebenOffen] = useState(false);
  const [weitergebenFehler, setWeitergebenFehler] = useState<string | null>(null);
  const [zusammenlegenOffen, setZusammenlegenOffen] = useState(false);
  const [schlossOffen, setSchlossOffen] = useState(false);
  const [ziele, setZiele] = useState<AblageZiel[]>([]);
  const [zusperrenFehler, setZusperrenFehler] = useState<string | null>(null);
  const [umlegenFehler, setUmlegenFehler] = useState<string | null>(null);
  const [credstickModus, setCredstickModus] = useState<"laden" | "entladen" | "sl-laden" | null>(null);
  const [credstickFehler, setCredstickFehler] = useState<string | null>(null);

  const eigenschaften = Object.entries(item.eigenschaften ?? {});
  const beschreibung = parseRichText(item.description);

  // Eigene Behälter (und Orte) live holen, sobald das Fenster offen ist —
  // genau wie CharacterSheetPanel es für die Spielleitung schon tut. Nicht
  // im Voraus für jede Kachel: das wäre eine Abfrage pro Gegenstand in der
  // Liste, nur damit ein paar Knöpfe gefüllt sind.
  useEffect(() => {
    if (!offen || !onUmlegen || !campaignId) {
      setZiele([]);
      return;
    }
    let abgebrochen = false;
    itemsApi
      .ablageziele(campaignId, item.id)
      .then((z) => {
        if (!abgebrochen) setZiele(z);
      })
      .catch(() => {
        if (!abgebrochen) setZiele([]);
      });
    return () => {
      abgebrochen = true;
    };
  }, [offen, onUmlegen, campaignId, item.id]);

  async function umlegen(ablage: Ablage, zielId?: string | null) {
    if (!onUmlegen) return;
    setLaeuft(true);
    setUmlegenFehler(null);
    try {
      await onUmlegen(ablage, zielId);
    } catch (e) {
      // Vorher verschluckt: 409 (natürliche Rüstung, verbautes Implantat)
      // liess den Knopf tot aussehen.
      setUmlegenFehler(e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Umlegen fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  async function wegwerfen() {
    if (!onWegwerfen) return;
    setLaeuft(true);
    try {
      await onWegwerfen();
      // Beide Fenster zu: der Gegenstand ist aus der Liste verschwunden, ein
      // offenes Fenster darüber stünde ohne Bezug da.
      setFrageOffen(false);
      setOffen(false);
    } finally {
      setLaeuft(false);
    }
  }

  /** Eine offene Kiste wieder zusperren — Spieler dürfen das selbst
   * (Mark, 31.10.2026). Setzt beim Tasten-Schloss zugleich Runde/Folge
   * zurück, siehe backend/app/items/routes.py::kiste_zusperren. */
  async function zusperren() {
    if (!campaignId) return;
    setLaeuft(true);
    setZusperrenFehler(null);
    try {
      await itemsApi.zusperren(campaignId, item.id);
      onGeoeffnet?.();
    } catch (e) {
      setZusperrenFehler(e instanceof ApiError ? e.message : "Geht nicht zu.");
    } finally {
      setLaeuft(false);
    }
  }

  async function weitergeben(empfaengerPersonId: string) {
    if (!onWeitergeben) return;
    setLaeuft(true);
    setWeitergebenFehler(null);
    try {
      await onWeitergeben(empfaengerPersonId);
      // Nicht die Kachel schließen: der Gegenstand gehört bis zur Annahme
      // noch dem Absender, er bleibt also in der Liste stehen — anders als
      // beim Wegwerfen, das sofort wirkt.
      setWeitergebenOffen(false);
    } catch (e) {
      // Vorher verschluckt: schlug die Anfrage fehl (z.B. Empfänger nicht in
      // derselben Party, oder ein SL-Schreibversuch während der Spieler-
      // Vorschau — siehe api/client.ts, Schreibzugriffe laufen dort immer
      // als die eigene Rolle, nie als der vorgeschaute Spieler), passierte
      // äusserlich gar nichts: das Fenster blieb offen, kein Hinweis. Jetzt
      // zeigt das Popup die Fehlermeldung vom Server an.
      setWeitergebenFehler(e instanceof Error ? e.message : "Weitergeben fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  /** Credstick auf-/entladen oder (SL) Geld erzeugen — siehe CredstickPopup.tsx.
   * Ruft die API direkt auf (gleiches Muster wie `zusperren` oben), weil
   * nur `campaignId`/`item.id` gebraucht werden, kein eigener Handler-Prop
   * pro Aufrufer nötig. */
  async function credstickAktion(betrag: number) {
    if (!campaignId || !credstickModus) return;
    setLaeuft(true);
    setCredstickFehler(null);
    try {
      if (credstickModus === "laden") {
        await itemsApi.credstickLaden(campaignId, item.id, betrag);
      } else if (credstickModus === "entladen") {
        await itemsApi.credstickEntladen(campaignId, item.id, betrag);
      } else {
        await itemsApi.credstickSlLaden(campaignId, item.id, betrag);
      }
      setCredstickModus(null);
      onGeoeffnet?.();
    } catch (e) {
      setCredstickFehler(e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Hat nicht geklappt.");
    } finally {
      setLaeuft(false);
    }
  }


  return (
    <>
      <button type="button" className="gg-kachel" onClick={() => setOffen(true)} title={formelKlartext(item.name)}>
        <span className="gg-kachel-bild">
          {item.bildUrl ? <img src={item.bildUrl} alt="" /> : <span aria-hidden="true">◈</span>}
          {item.hatMenge && <span className="gg-kachel-menge">×{item.menge}</span>}
        </span>
        <span className="gg-kachel-name">
          <FormelText text={item.name} />
        </span>
        <span className="gg-kachel-zeile">
          {item.typ}
          {item.gewicht > 0 && ` · ${item.gewicht} kg`}
        </span>
        {steckbriefKurz(item).length > 0 && (
          <span className="gg-kachel-steckbrief">{steckbriefKurz(item).join(" · ")}</span>
        )}
        <span className="gg-kachel-marken">
          {/* Kein "getragen"-Zeichen: im Abschnitt "Am Körper" wäre es an
              jeder Kachel dasselbe, und in einem Fach kann nichts getragen
              sein. Wo etwas liegt, sagt der Ort — das ist die Auskunft, die
              man beim Durchsehen eines Fachs braucht. */}
          {istVerschlossen(item) && (
            <span className="gg-marke" data-ton="signal" title="Verschlossen">
              verschlossen
            </span>
          )}
          {/* Nur am Körper von Belang: im Rucksack sieht es ohnehin niemand. */}
          {item.immerSichtbar && item.ablage === "AUSGERUESTET" && (
            <span className="gg-marke" data-ton="signal" title="Das sieht jeder">
              sichtbar
            </span>
          )}
          {item.hatMenge && item.menge === 0 && (
            <span className="gg-marke" data-ton="signal">leer</span>
          )}
          {montierteUpgrades?.map((name) => (
            <span className="gg-marke" key={name} title="Verbautes Upgrade">
              🔩 {name}
            </span>
          ))}
          {/* Das Stück selbst ist montiert (31.10.2026, Mark: "als SL kann
              ich Ki-Tamas/Waffen-Upgrades nicht mehr sehen, wenn sie
              verbaut sind") — die Kachel bleibt wie gewohnt klickbar und
              anzeigbar, bekommt aber zusätzlich ein Fähnchen, wo sie sitzt. */}
          {item.montiertAnId && (
            <span className="gg-marke" title={`Montiert an ${item.montiertAnName ?? "?"}`}>
              🔩 an {item.montiertAnName ?? "?"}
            </span>
          )}
        </span>
      </button>

      <Fenster
        offen={offen}
        titel={item.hatMenge ? `${formelKlartext(item.name)} ×${item.menge}` : item.name}
        unterzeile={[item.typ, item.preis > 0 ? `${item.preis.toLocaleString("de-AT")}¥` : null, item.gewicht > 0 ? `${item.gewicht} kg` : null]
          .filter(Boolean)
          .join(" · ")}
        kennung={`gegenstand:${item.id}`}
        onSchliessen={() => setOffen(false)}
      >
        {item.bildUrl && (
          <img
            src={item.bildUrl}
            alt=""
            style={{ width: "100%", maxHeight: 240, objectFit: "contain", borderRadius: "var(--radius)" }}
          />
        )}

        {item.immerSichtbar && (
          <p className="gg-sichtbar-hinweis">
            {item.ablage === "AUSGERUESTET"
              ? "Am Körper nicht zu übersehen — wer dich ansieht, sieht das hier."
              : "Trägst du es offen, sieht es jeder."}
          </p>
        )}

        {beschreibung && <RichTextView content={beschreibung} />}

        {inhalt && (
          <button type="button" className="gg-hineinsehen" onClick={inhalt.oeffnen}>
            <span aria-hidden="true">{item.typ === "Fahrzeug" ? "⛭" : "▣"}</span>
            Hineinsehen
            <span className="gg-fach-zahl">{inhalt.anzahl}</span>
          </button>
        )}

        {/* Blatt für Drohne und Fahrzeug (Neotopia.xlsx). Erscheint bei
            diesen Typen **immer** — auch ungepflegt: dass noch nichts
            eingetragen ist, ist selbst eine Auskunft. Vorher blieb ein
            Fahrzeug ohne Werte völlig stumm, und man rätselte, ob es kein
            Blatt hat oder ob die Anzeige fehlt. */}
        {(FAHRZEUGTYPEN.has(item.typ) ||
          item.stufe > 0 ||
          item.widerstand > 0 ||
          item.angriff > 0 ||
          item.agilitaet > 0) && (
          <>
            <StufenBlatt
              titel={item.typ === "Drohne" ? "Drohnenwerte" : "Fahrzeugwerte"}
              werte={item}
              stufenHinweis={
                item.stufe === 0
                  ? "Noch keine Stufe festgelegt — das trägt die Spielleitung ein."
                  : undefined
              }
            />
            {Object.keys(item.fahrzeugFertigkeiten ?? {}).length > 0 && (
              <div className="gg-fahrzeugwerte">
                {Object.entries(item.fahrzeugFertigkeiten).map(([name, wert]) => (
                  <div key={name} className="gg-fahrzeugwert">
                    <span>{name}</span>
                    <DotPool value={wert} max={5} />
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Chrom: kraft ist die Stufe (Preis-/WK-Bonus), nicht der Waffenschaden.
            Echte Klingen sitzen in schaden, und nur wenn das Stück auch Waffe ist. */}
        {istChrom && item.kraft > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ color: "var(--text-leise)", fontSize: 13 }}>Stufe</span>
            <DotPool value={item.kraft} max={SCHADEN_MAX} />
          </div>
        )}
        {istChrom && item.istWaffe && item.schaden > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ color: "var(--text-leise)", fontSize: 13 }}>Schaden</span>
            <DotPool value={item.schaden} max={SCHADEN_MAX} />
          </div>
        )}
        {!istChrom && item.kraft > 0 && item.typ !== "Rüstung" && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ color: "var(--text-leise)", fontSize: 13 }}>Schaden</span>
            <DotPool value={item.kraft} max={SCHADEN_MAX} />
          </div>
        )}

        {item.typ === "Commlink" && (
          <p style={{ color: "var(--text-leise)", fontSize: 13, margin: 0 }}>I.C.E. {item.cyberwall}</p>
        )}

        {item.typ === "Credstick" && campaignId && (
          <section className="gg-ablage-wahl">
            <h3>Credstick</h3>
            <p className="gg-ablage-ort">Geladen: {item.geladenesGeld.toLocaleString("de-AT")}¥</p>
            <div className="gg-ablage-knoepfe">
              {onUmlegen && (
                <button
                  type="button"
                  onClick={() => {
                    setCredstickFehler(null);
                    setCredstickModus("laden");
                  }}
                  disabled={laeuft}
                >
                  <span aria-hidden="true">⬆</span> Aufladen
                </button>
              )}
              {onUmlegen && (
                <button
                  type="button"
                  onClick={() => {
                    setCredstickFehler(null);
                    setCredstickModus("entladen");
                  }}
                  disabled={laeuft}
                >
                  <span aria-hidden="true">⬇</span> Abheben
                </button>
              )}
              {istSpielleitung && (
                <button
                  type="button"
                  onClick={() => {
                    setCredstickFehler(null);
                    setCredstickModus("sl-laden");
                  }}
                  disabled={laeuft}
                >
                  <span aria-hidden="true">✨</span> Geld erzeugen
                </button>
              )}
            </div>
          </section>
        )}

        {item.typ === "Cyberdeck" && (
          <p style={{ color: "var(--text-leise)", fontSize: 13, margin: 0 }}>
            B {item.deckBruteForce} · S {item.deckSchleichen} · D {item.deckDaten} · K {item.deckKompilieren} · EW{" "}
            {item.deckElectronicWarfare} · N {item.deckMatrixNavigation}
            {item.cyberwall > 0 && ` · Cyberwall +${item.cyberwall}`}
          </p>
        )}

        {istChrom && (item.koerperzone || item.wVerlust > 0 || item.initiativeBonus !== 0 || item.zusatzaktionen !== 0) && (
          <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text-leise)", fontSize: 13 }}>
            {item.koerperzone && (
              <li>
                {item.koerperzone}
                {item.slot ? `, Platz ${item.slot}` : ""}
              </li>
            )}
            {item.wVerlust > 0 && <li>−{item.wVerlust.toLocaleString("de-AT")} Willenskraft</li>}
            {item.initiativeBonus !== 0 && (
              <li>
                Initiative {item.initiativeBonus > 0 ? "+" : ""}
                {item.initiativeBonus}
              </li>
            )}
            {item.zusatzaktionen !== 0 && (
              <li>
                Zusatzaktion: {item.zusatzaktionen === -1 ? "jede Runde" : `${item.zusatzaktionen}× pro Kampf`}
              </li>
            )}
          </ul>
        )}

        {eigenschaften.length > 0 && (
          <dl className="gg-eigenschaften">
            {eigenschaften.map(([schluessel, wert]) => (
              <div key={schluessel}>
                <dt>{schluessel}</dt>
                <dd>{wert}</dd>
              </div>
            ))}
          </dl>
        )}

                {/* Noch nicht eingesetztes Chrom: der Weg hinein. */}
        {istChrom && !item.verbaut && onChirurgie && (
          <section className="gg-ablage-wahl">
            <h3>Noch nicht eingesetzt</h3>
            <p className="gg-ablage-ort">
              Liegt herum und wirkt nicht. Erst eingesetzt zählt es — mit allem, was dazugehört
              (Willenskraftverlust, Körperplatz).
            </p>
            <div className="gg-ablage-knoepfe">
              <button type="button" onClick={() => void onChirurgie(true)} disabled={laeuft}>
                <span aria-hidden="true">⚕</span> Einsetzen
              </button>
            </div>
          </section>
        )}

        {/* Hierher gehört das Umlegen: man sieht sich das Ding an und
            entscheidet dabei, wo es hin soll. Bei verbautem Chrom entfällt
            es vollständig. */}
        {istVerschlossen(item) && campaignId && onGeoeffnet && (
          <section className="gg-ablage-wahl">
            <h3>Verschlossen</h3>
            <p className="gg-ablage-ort">
              {item.schlossArt === "spiel"
                ? "Ein Runen-Schloss. Die Folge wird länger, bis es aufgeht."
                : item.schlossArt === "schluessel"
                  ? "Dafür brauchst du den passenden Schlüssel."
                  : item.schlossRaetsel || "Dafür brauchst du die Lösung."}
            </p>
            <div className="gg-ablage-knoepfe">
              <button type="button" onClick={() => setSchlossOffen(true)}>
                Öffnen
              </button>
            </div>
          </section>
        )}
        {item.aufgeschlossen && item.schlossArt && campaignId && onGeoeffnet && (
          <section className="gg-ablage-wahl">
            <h3>Aufgeschlossen</h3>
            <p className="gg-ablage-ort">Bleibt offen, bis es wieder zugesperrt wird.</p>
            <div className="gg-ablage-knoepfe">
              <button type="button" onClick={() => void zusperren()} disabled={laeuft}>
                Verschließen
              </button>
            </div>
            {zusperrenFehler && <p style={{ margin: 0, fontSize: "0.85em", color: "var(--nein)" }}>{zusperrenFehler}</p>}
          </section>
        )}
        {onUmlegen && !(istChrom && item.verbaut) && (
        <section className="gg-ablage-wahl">
          <h3>Wo ist es?</h3>
          {item.ablage === "GELAGERT" && item.ablageZielName && (
            <p className="gg-ablage-ort">
              Liegt in <strong>{item.ablageZielName}</strong>.
            </p>
          )}
          <div className="gg-ablage-knoepfe">
            {grundAblagen().map((a) => (
              <button
                key={a.wert}
                type="button"
                data-aktiv={item.ablage === a.wert}
                disabled={laeuft || item.ablage === a.wert}
                onClick={() => umlegen(a.wert, null)}
                title={a.erklaerung}
              >
                <span aria-hidden="true">{a.symbol}</span> {a.label}
              </button>
            ))}
            {/* Jeder eigene Behälter (und jeder Ort der Kampagne) einzeln —
                live aus itemsApi.ablageziele, siehe grundAblagen() oben.
                Nichts kann in sich selbst liegen. */}
            {ziele
              .filter((z) => z.id !== item.id)
              .map((z) => (
                <button
                  key={z.id}
                  type="button"
                  data-aktiv={item.ablage === "GELAGERT" && item.ablageZielId === z.id}
                  disabled={laeuft || (item.ablage === "GELAGERT" && item.ablageZielId === z.id)}
                  onClick={() => umlegen("GELAGERT", z.id)}
                  title={z.kind === "Ort" ? `Liegt am Ort „${z.name}".` : `Verstaut in „${z.name}".`}
                >
                  <span aria-hidden="true">{z.kind === "Ort" ? "⌂" : "🎒"}</span> {z.name}
                </button>
              ))}
            <button
              type="button"
              data-aktiv={item.ablage === "GELAGERT" && !item.ablageZielId}
              disabled={laeuft || (item.ablage === "GELAGERT" && !item.ablageZielId)}
              onClick={() => umlegen("GELAGERT", null)}
              title="Liegt anderswo, ohne festen Platz — die Spielleitung legt die Details fest."
            >
              <span aria-hidden="true">⌷</span> Weggelegt
            </button>
          </div>
          {umlegenFehler && <p style={{ margin: "8px 0 0", fontSize: "0.85em", color: "var(--nein)" }}>{umlegenFehler}</p>}
        </section>
        )}

        {/* Abgesetzt und leise: erst der Griff danach ist eine Entscheidung,
            die die Rückfrage stellt. Siehe wegwerfen.css. */}
        {(item.typ === "Droge" && campaignId && onUmlegen) && (
          <div className="gg-wegwerfen">
            <button
              type="button"
              disabled={laeuft}
              onClick={async () => {
                setLaeuft(true);
                setSchluckText(null);
                try {
                  const antwort = await itemsApi.schlucken(campaignId, item.id);
                  setSchluckText(antwort.text);
                  onGeoeffnet?.();
                  window.dispatchEvent(new CustomEvent(DROGE_GESCHLUCKT));
                } catch (e) {
                  setSchluckText(e instanceof ApiError ? e.message : "Schlucken ging nicht.");
                } finally {
                  setLaeuft(false);
                }
              }}
            >
              Schlucken
            </button>
            {schluckText && <p style={{ margin: "8px 0 0" }}>{schluckText}</p>}
          </div>
        )}

        {(onWegwerfen || onWeitergeben) && (
          <div className="gg-wegwerfen">
            {onWeitergeben && (
              <button
                type="button"
                onClick={() => {
                  setWeitergebenFehler(null);
                  setWeitergebenOffen(true);
                }}
                disabled={laeuft}
              >
                <span aria-hidden="true">🤝</span> Weitergeben
              </button>
            )}
            {/* Zusammenlegen braucht nicht zwingend onWegwerfen/onWeitergeben,
                aber beide Marker heißen "das ist mein eigener Gegenstand" —
                onUmlegen ist das zuverlässigste Signal dafür (auch an
                Stellen, die (noch) kein Wegwerfen anbieten). Absichtlich OHNE
                einzigartig-Filter hier: einzigartig ist der Schema-Default
                (true) für praktisch jeden neu angelegten Gegenstand, ein
                Filter davor würde den Knopf fast überall unsichtbar machen.
                Das Popup selbst erklärt es, wenn es wirklich zutrifft. */}
            {onZusammengelegt && onUmlegen && campaignId && (
              <button type="button" onClick={() => setZusammenlegenOffen(true)} disabled={laeuft}>
                <span aria-hidden="true">⧉</span> Zusammenlegen
              </button>
            )}
            {onWegwerfen && (
              <button type="button" onClick={() => setFrageOffen(true)} disabled={laeuft}>
                <span aria-hidden="true">🗑</span> Wegwerfen
              </button>
            )}
          </div>
        )}
        {/* Zusammenlegen ohne Wegwerfen/Weitergeben an derselben Stelle (z.B.
            Fahrzeuge/Ausrüstung-Reiter, die bisher keinen Fußzeilen-Bereich
            hatten) bekommt die Fußzeile trotzdem, sonst gibt es den Knopf hier nie. */}
        {!(onWegwerfen || onWeitergeben) && onZusammengelegt && onUmlegen && campaignId && (
          <div className="gg-wegwerfen">
            <button type="button" onClick={() => setZusammenlegenOffen(true)} disabled={laeuft}>
              <span aria-hidden="true">⧉</span> Zusammenlegen
            </button>
          </div>
        )}
      </Fenster>

      {onWegwerfen && (
        <WegwerfenFrage
          item={item}
          offen={frageOffen}
          laeuft={laeuft}
          onWegwerfen={wegwerfen}
          onAbbrechen={() => setFrageOffen(false)}
        />
      )}

      {onWeitergeben && campaignId && eigenePersonId && (
        <WeitergebenPopup
          item={item}
          offen={weitergebenOffen}
          campaignId={campaignId}
          eigenePersonId={eigenePersonId}
          onWeitergeben={weitergeben}
          laeuft={laeuft}
          fehler={weitergebenFehler}
          onAbbrechen={() => setWeitergebenOffen(false)}
        />
      )}

      {onZusammengelegt && campaignId && (
        <ZusammenlegenPopup
          item={item}
          offen={zusammenlegenOffen}
          campaignId={campaignId}
          onZusammengelegt={() => {
            setZusammenlegenOffen(false);
            onZusammengelegt();
          }}
          onAbbrechen={() => setZusammenlegenOffen(false)}
        />
      )}
      {credstickModus && campaignId && (
        <CredstickPopup
          item={item}
          modus={credstickModus}
          offen
          onBestaetigen={credstickAktion}
          onAbbrechen={() => setCredstickModus(null)}
          laeuft={laeuft}
          fehler={credstickFehler}
        />
      )}
      {schlossOffen && campaignId && onGeoeffnet && (
        <SchlossOeffnen
          item={item}
          campaignId={campaignId}
          offen
          onSchliessen={() => setSchlossOffen(false)}
          onGeoeffnet={() => {
            setSchlossOffen(false);
            setOffen(false);
            onGeoeffnet();
          }}
        />
      )}
    </>
  );
}
