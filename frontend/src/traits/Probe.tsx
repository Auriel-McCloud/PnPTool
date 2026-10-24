import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { WuerfelZehn } from "./WuerfelZehn";
import type { TraitDef } from "./api";
import type { Spezialisierung } from "../spezialisierungen/api";
import { SpezialisierungVerwaltung } from "./SpezialisierungPopup";
import { MAGIE_HINWEISE, NEUROWEAVING_POOL_MAX, SPHAEREN, SPHAEREN_STUFEN } from "./magie";
import { magieBegriff, type MagieFlavor } from "./magieBegriffe";
import "./probe.css";

/**
 * Wieviele Würfel? — die Rechenhilfe zur Probe.
 *
 * **Das Werkzeug würfelt nicht.** Gewürfelt wird am Tisch, mit echten Würfeln;
 * hier steht nur, wie viele man nehmen darf. Marks Vorgabe: eine Erleichterung,
 * kein Ersatz. (Ein Schalter, der das Würfeln doch erlaubt, ist als Idee
 * notiert — er zöge nach sich, dass Spielleitung und Mitspieler die Ergebnisse
 * sehen müssten, und das ist eine eigene Runde wert.)
 *
 * Zwei Fenster übereinander, wie im UI-Konzept: antippen → womit kombinieren?
 * → so viele Würfel. Von welcher Seite man kommt, entscheidet nur die Liste:
 * Fähigkeit antippen fragt nach dem Attribut, Attribut antippen nach der
 * Fähigkeit. Beides ist derselbe Pool.
 */

/** Reihenfolge und Beschriftung wie auf dem Blatt. */
const SPALTEN: { titel: string; kategorie: string; ton: string }[] = [
  { titel: "Körperlich", kategorie: "AttributKörperlich", ton: "var(--wert-koerperlich)" },
  { titel: "Gesellschaftlich", kategorie: "AttributGesellschaftlich", ton: "var(--wert-gesellschaftlich)" },
  { titel: "Geistig", kategorie: "AttributGeistig", ton: "var(--wert-geistig)" },
];

/** Klick auf so eine Zeile fragt nach der Fähigkeit, nicht nach einem zweiten Attribut. */
const ATTRIBUT_KATEGORIEN = new Set([
  "AttributKörperlich",
  "AttributGesellschaftlich",
  "AttributGeistig",
  "AttributMatrix",
]);

/**
 * Fähigkeiten stehen auf dem Blatt in drei Zehnerblöcken, passend zu den
 * Attributspalten (sortOrder 1–10 / 11–20 / 21–30). Dieselbe Schnitte hier,
 * sonst sucht man die Fertigkeit an einer anderen Stelle als auf dem Blatt.
 */
const FERTIGKEIT_SPALTEN: { titel: string; von: number; bis: number; ton: string }[] = [
  { titel: "Körperlich", von: 1, bis: 10, ton: "var(--wert-koerperlich)" },
  { titel: "Gesellschaftlich", von: 11, bis: 20, ton: "var(--wert-gesellschaftlich)" },
  { titel: "Geistig", von: 21, bis: 30, ton: "var(--wert-geistig)" },
];

/**
 * Hexkraft geht **nicht** mit Attributen zusammen (Zeilen 81-86). Ein
 * kontrollierter Zauber ist nur der Hexkraft-Wert; dazunehmen lässt sich allein
 * Willenskraft, und das mit Folgen — siehe `magie.ts`.
 */
const NUR_WILLENSKRAFT = new Set(["Hexkraft", "NeuroWeavingWert", "NeuroWeaving"]);

/**
 * Beim NeuroWeaving treffen zwei Werte aufeinander: der NeuroWeaving-Wert
 * selbst und eine der vier Fertigkeiten (Regelblatt Zeile 45/96 — anders als
 * Sphären zählen sie **mit**). Von welcher Seite man kommt, entscheidet nur,
 * was die Auswahl zeigt.
 */
const NEURO_PARTNER: Record<string, string> = {
  NeuroWeavingWert: "NeuroWeaving",
  NeuroWeaving: "NeuroWeavingWert",
};

export interface ProbeWahl {
  name: string;
  wert: number;
  kategorie: string;
}

export function Probe({
  wahl,
  katalog,
  werte,
  willenskraft,
  deckBoni,
  ausruestungsBoni,
  zusatzfertigkeiten,
  ausruestungsfertigkeiten,
  magieFlavor,
  spezialisierungen,
  campaignId,
  personId,
  erfahrungVerfuegbar = 0,
  istGM = false,
  onSpezialisierungAenderung,
  onSchliessen,
}: {
  wahl: ProbeWahl | null;
  /** Attribut- und Fertigkeitsnamen, Reihenfolge und sortOrder. */
  katalog: TraitDef[];
  /**
   * Aktuelle Werte, verschlüsselt nach **TraitDef-Kennung** — so liefert sie
   * das Charakterblatt. Nach Namen zu suchen ginge schief: die Karte hätte
   * dann für jeden Eintrag `undefined` und alle Attribute stünden auf 0.
   */
  werte: Map<string, number>;
  /** Obergrenze für Wilde Magie — so viele Bonuswürfel sind erlaubt. */
  willenskraft: number;
  /** Bonuswürfel aus dem ausgerüsteten Cyberdeck, je Matrix-Aktion. */
  deckBoni?: Record<string, number>;
  /**
   * Bonuswürfel aus Ausrüstung, Schlüssel ist der Trait-Name. Der angeklickte
   * Wert bringt seinen Bonus schon mit (`wahl.wert`); der Partner wird hier
   * nachgeschlagen und muss denselben Bonus dazubekommen, sonst weicht der Pool
   * davon ab, was auf dem Blatt steht.
   */
  ausruestungsBoni?: Record<string, number>;
  /**
   * Zusatz- und Ausrüstungsfertigkeiten gehören nicht zum Trait-Katalog,
   * kombinieren sich aber genauso mit einem Attribut. Nur die Attribut-Seite
   * zeigt sie — von der Fertigkeit aus fragt das Fenster weiter nach dem Attribut.
   */
  zusatzfertigkeiten?: { name: string; wert: number }[];
  ausruestungsfertigkeiten?: { name: string; wert: number }[];
  /** Häretiker-Flavor (24.09.2026): nur Anzeige, siehe magieBegriffe.ts. */
  magieFlavor?: MagieFlavor;
  /** Fertigkeiten-Spezialisierung (22.10.2026): ALLE Slots dieser Person
   * (benannt wie unbenannt) — nur die BENANNTEN werden als Chip angeboten,
   * und nur für die plain Fertigkeit+Attribut-Kombination unten, nie für
   * Attribute/Sphären/Hexkraft/NeuroWeaving (siehe istSphaere/nurWillenskraft).
   * Benennen und Kaufen sitzt nicht hier, sondern im ersten Fenster
   * (SpezialisierungVerwaltung) — dieser Chip ist nur der +1 für die Probe. */
  spezialisierungen?: Spezialisierung[];
  /** Fürs Einbetten der Slot-Verwaltung. Fehlt das, bleibt das Fenster
   * eine reine Rechenhilfe (Kampfkarte). */
  campaignId?: string;
  personId?: string;
  erfahrungVerfuegbar?: number;
  istGM?: boolean;
  onSpezialisierungAenderung?: () => void | Promise<void>;
  onSchliessen: () => void;
}) {
  const [attribut, setAttribut] = useState<{ name: string; wert: number; traitDefId?: string } | null>(null);
  // Bonuswürfel aus Willenskraft — nur bei Hexkraft und NeuroWeaving.
  const [wild, setWild] = useState(0);
  // Genau eine Deck-Aktion — man tut ja eines nach dem anderen.
  const [deck, setDeck] = useState<{ name: string; wert: number } | null>(null);
  // Gewählte Spezialisierung — EINE, kein Stapeln mehrerer Boni auf eine
  // Probe (Mark hat das nie besprochen, siehe Berichtstext/Assumption).
  const [spezialisierung, setSpezialisierung] = useState<Spezialisierung | null>(null);

  // Beim NeuroWeaving gibt es genau EINEN Grundwert (Kategorie
  // "NeuroWeavingWert") — klickt man auf eine der sechs Fertigkeiten, bleibt
  // als Partner keine echte Wahl übrig, nur ein Pflichtklick auf den
  // einzigen Kandidaten. Den übernehmen wir automatisch (Mark, 22.09.2026:
  // "ich habe ja garkeine Wahl"). Der umgekehrte Fall — Klick auf den
  // Grundwert selbst, sechs mögliche Fertigkeiten — bleibt bewusst offen.
  useEffect(() => {
    if (!wahl) return;
    const partner = NEURO_PARTNER[wahl.kategorie];
    if (!partner) return;
    const kandidaten = katalog.filter((t) => t.category === partner);
    if (kandidaten.length === 1) {
      const [t] = kandidaten;
      setAttribut({
        name: t.name,
        wert: (werte.get(t.id) ?? 0) + (ausruestungsBoni?.[t.name] ?? 0),
      });
    }
  }, [wahl, katalog, werte, ausruestungsBoni]);

  if (!wahl) return null;

  const istSphaere = wahl.kategorie === "Sphäre";
  const nurWillenskraft = NUR_WILLENSKRAFT.has(wahl.kategorie);
  const partnerKategorie = NEURO_PARTNER[wahl.kategorie];
  // Nur für die plaine Fertigkeit+Attribut-Kombination unten relevant —
  // istSphaere/nurWillenskraft geben vorher eigene Fenster zurück und
  // erreichen diesen Zweig nie. `katalog` enthält je Ruleset+Kategorie
  // eindeutige Namen (dieselbe Annahme wie bei SPALTEN/NEURO_PARTNER oben).
  const fertigkeitTrait =
    wahl.kategorie === "Fertigkeit" || wahl.kategorie === "NeuroWeaving"
      ? katalog.find((t) => t.name === wahl.name && t.category === wahl.kategorie)
      : undefined;
  // Attribut antippen: die Spezialisierung hängt an der gewählten Fähigkeit,
  // nicht am Attribut. Sonst gäbe es den +1 nur, wenn man von der Fähigkeit kommt.
  const istAttributWahl = ATTRIBUT_KATEGORIEN.has(wahl.kategorie);
  const spezialisierungsTraitId = istAttributWahl ? attribut?.traitDefId : fertigkeitTrait?.id;
  const spezialisierungenFuerTrait = spezialisierungsTraitId
    ? (spezialisierungen ?? []).filter((s) => s.traitDefId === spezialisierungsTraitId && s.text)
    : [];
  const roh =
    wahl.wert +
    (attribut?.wert ?? 0) +
    (nurWillenskraft ? wild : 0) +
    (deck?.wert ?? 0) +
    (spezialisierung ? 1 : 0);
  // Der Deckel gilt nur fürs NeuroWeaving; Hexkraft allein geht bis 10 und
  // sammelt darüber hinaus nur wilde Würfel.
  const gedeckelt = Boolean(partnerKategorie) && roh > NEUROWEAVING_POOL_MAX;
  const pool = gedeckelt ? NEUROWEAVING_POOL_MAX : roh;
  // Häretiker-Flavor: übersetzt "Hexkraft"/Sphärennamen/"Wilde Magie", sonst
  // unverändert. Zentrale Stelle statt an jeder Textausgabe einzeln.
  const wahlName = magieBegriff(magieFlavor, wahl.name);
  const wildeMagieName = magieBegriff(magieFlavor, "Wilde Magie");

  const deckAktionen = Object.entries(deckBoni ?? {});

  function schliesseAlles() {
    setAttribut(null);
    setWild(0);
    setDeck(null);
    setSpezialisierung(null);
    onSchliessen();
  }

  // Slots benennen und kaufen — im selben Fenster wie die Attributwahl,
  // nicht als Badge neben den Punkten. Nur wenn die Fertigkeit eine
  // Spezialisierung haben kann (oder schon Slots hat).
  function spezialisierungsBlock(aktuell: ProbeWahl) {
    if (!campaignId || !personId || !onSpezialisierungAenderung) return null;
    if (aktuell.kategorie !== "Fertigkeit" && aktuell.kategorie !== "NeuroWeaving" && aktuell.kategorie !== "Sphäre") {
      return null;
    }
    const trait = katalog.find((t) => t.name === aktuell.name && t.category === aktuell.kategorie);
    if (!trait) return null;
    const rating = werte.get(trait.id) ?? 0;
    const slots = (spezialisierungen ?? []).filter((s) => s.traitDefId === trait.id);
    const mindest = aktuell.kategorie === "Sphäre" ? 2 : 4;
    if (rating < mindest && slots.length === 0) return null;
    return (
      <section className="pr-spezialisierung">
        <h3 className="pr-spalte-titel" style={{ "--cb-ton": "var(--neon)" } as React.CSSProperties}>
          Spezialisierungen
        </h3>
        <SpezialisierungVerwaltung
          campaignId={campaignId}
          personId={personId}
          trait={trait}
          rating={rating}
          erfahrungVerfuegbar={erfahrungVerfuegbar}
          slots={slots}
          istGM={istGM}
          onAenderung={onSpezialisierungAenderung}
        />
      </section>
    );
  }

  // --- Sphären: hier wird nicht gewürfelt (Zeile 87) --------------------
  if (istSphaere) {
    return (
      <Fenster
        offen
        titel={`${wahlName} ${wahl.wert}`}
        unterzeile="Sphäre — was damit geht"
        kennung={`sphaere:${wahl.name}`}
        onSchliessen={schliesseAlles}
      >
        <p className="pr-regel pr-hinweis">{MAGIE_HINWEISE.sphaereNichtWuerfeln}</p>
        {SPHAEREN[wahl.name] && <p className="pr-sphaerentext">{SPHAEREN[wahl.name]}</p>}
        <ol className="pr-stufen">
          {SPHAEREN_STUFEN.slice(1).map((text, i) => {
            const stufe = i + 1;
            return (
              <li key={stufe} data-erreicht={stufe <= wahl.wert} data-aktuell={stufe === wahl.wert}>
                <span className="pr-stufe-zahl">{stufe}</span>
                <span>{text}</span>
              </li>
            );
          })}
        </ol>
        {wahl.wert === 0 && <p className="pr-regel">Diese Sphäre steht dir noch nicht offen.</p>}
        {spezialisierungsBlock(wahl)}
      </Fenster>
    );
  }

  // --- Hexkraft und NeuroWeaving: nur Willenskraft dazu --------------------
  if (nurWillenskraft) {
    return (
      <>
        <Fenster
          offen
          titel={`${wahlName} ${wahl.wert}`}
          unterzeile={wahl.kategorie === "Hexkraft" ? "Kontrolliert oder wild?" : "NeuroWeaving"}
          kennung={`probe:${wahl.name}`}
          onSchliessen={schliesseAlles}
        >
          <p className="pr-regel pr-hinweis">
            {wahl.kategorie === "Hexkraft" ? MAGIE_HINWEISE.hexkraftKontrolliert : MAGIE_HINWEISE.neuroWeaving}
          </p>

          {partnerKategorie && (
            <section>
              <h3 className="pr-spalte-titel" style={{ "--cb-ton": "var(--wert-neuroweaving)" } as React.CSSProperties}>
                {wahl.kategorie === "NeuroWeavingWert" ? "Womit?" : "NeuroWeaving-Wert"}
              </h3>
              {katalog
                .filter((t) => t.category === partnerKategorie)
                .map((t) => {
                  const wert = (werte.get(t.id) ?? 0) + (ausruestungsBoni?.[t.name] ?? 0);
                  const gewaehlt = attribut?.name === t.name;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      className="pr-attribut"
                      data-gewaehlt={gewaehlt}
                      style={{ "--cb-ton": "var(--wert-neuroweaving)" } as React.CSSProperties}
                      onClick={() => setAttribut(gewaehlt ? null : { name: t.name, wert })}
                    >
                      <span className="pr-attribut-name">{t.name}</span>
                      <span className="pr-attribut-summe">
                        {Math.min(NEUROWEAVING_POOL_MAX, wahl.wert + wert + wild)}
                      </span>
                    </button>
                  );
                })}
            </section>
          )}

          <div className="pr-pool">
            <span className="pr-zahl">{pool}</span>
            <WuerfelZehn groesse={54} />
          </div>
          <p className="pr-rechnung">
            {wahlName} {wahl.wert}
            {attribut && ` + ${attribut.name} ${attribut.wert}`}
            {wild > 0 && ` + ${wild} aus Willenskraft`}
            {gedeckelt && ` — gedeckelt auf ${NEUROWEAVING_POOL_MAX}`}
          </p>

          {willenskraft > 0 ? (
            <section className="pr-wild">
              <h3>{wahl.kategorie === "Hexkraft" ? wildeMagieName : "Overclock"}</h3>
              <p className="pr-regel">
                {wahl.kategorie === "Hexkraft" ? MAGIE_HINWEISE.hexkraftWild : MAGIE_HINWEISE.overclock}
              </p>
              <div className="pr-wild-reihe">
                <button type="button" onClick={() => setWild((w) => Math.max(0, w - 1))} disabled={wild === 0}>
                  −
                </button>
                <span className="pr-wild-zahl">
                  {wild} <em>von {willenskraft}</em>
                </span>
                <button
                  type="button"
                  onClick={() => setWild((w) => Math.min(willenskraft, w + 1))}
                  disabled={wild >= willenskraft}
                >
                  +
                </button>
              </div>
              {wild > 0 && (
                <p className="pr-warnung">
                  {wahl.kategorie === "Hexkraft" ? MAGIE_HINWEISE.hexkraftRueckstoss : MAGIE_HINWEISE.overclockRueckstoss}
                </p>
              )}
            </section>
          ) : (
            <p className="pr-regel">
              {wahl.kategorie === "Hexkraft" ? `Ohne Willenskraft keine ${wildeMagieName}.` : "Ohne Willenskraft kein Overclock."}
            </p>
          )}
          {spezialisierungsBlock(wahl)}
        </Fenster>
      </>
    );
  }

  return (
    <>
      <Fenster
        offen
        breit={istAttributWahl}
        titel={`${wahlName} ${wahl.wert}`}
        unterzeile={istAttributWahl ? "Mit welcher Fähigkeit?" : "Womit kombinierst du?"}
        kennung={`probe:${wahl.name}`}
        onSchliessen={schliesseAlles}
      >
        {istAttributWahl ? (
          <FertigkeitsWahl
            katalog={katalog}
            werte={werte}
            ausruestungsBoni={ausruestungsBoni}
            zusatzfertigkeiten={zusatzfertigkeiten}
            ausruestungsfertigkeiten={ausruestungsfertigkeiten}
            basis={wahl.wert}
            onWaehlen={(partner) => {
              setAttribut(partner);
              setSpezialisierung((aktuell) =>
                aktuell && partner.traitDefId && aktuell.traitDefId === partner.traitDefId ? aktuell : null,
              );
            }}
          />
        ) : (
          <div className="pr-spalten">
            {attributSpalten(katalog).map((spalte) => (
              <section key={spalte.kategorie} style={{ "--cb-ton": spalte.ton } as React.CSSProperties}>
                <h3 className="pr-spalte-titel">{spalte.titel}</h3>
                {katalog
                  .filter((t) => t.category === spalte.kategorie)
                  .map((t) => {
                    const wert = (werte.get(t.id) ?? 0) + (ausruestungsBoni?.[t.name] ?? 0);
                    return (
                      <button
                        key={t.id}
                        type="button"
                        className="pr-attribut"
                        onClick={() => setAttribut({ name: t.name, wert })}
                      >
                        <span className="pr-attribut-name">{t.name}</span>
                        <span className="pr-attribut-summe">{wahl.wert + wert}</span>
                      </button>
                    );
                  })}
              </section>
            ))}
          </div>
        )}
        {spezialisierungsBlock(wahl)}
      </Fenster>

      {/* Zweites Fenster über dem ersten — die Zahl ist die ganze Auskunft. */}
      <Fenster
        offen={attribut !== null}
        titel={attribut ? `${wahlName} + ${attribut.name}` : ""}
        kennung="probe-pool"
        onSchliessen={() => setAttribut(null)}
      >
        <div className="pr-pool">
          <span className="pr-zahl">{pool}</span>
          <WuerfelZehn groesse={54} />
        </div>
        <p className="pr-rechnung">
          {wahlName} {wahl.wert}
          {attribut && attribut.wert > 0 && ` + ${attribut.name} ${attribut.wert}`}
          {deck && ` + ${deck.name} ${deck.wert}`}
          {spezialisierung && ` + 1 (Spezialisierung: ${spezialisierung.text})`}
        </p>

        {/* Das Deck gibt Bonuswürfel je Aktion (Zeile 157). Nur anbieten,
            wenn eines ausgerüstet ist — sonst steht hier eine leere Reihe. */}
        {deckAktionen.length > 0 && (
          <section className="pr-deck">
            <h3>Cyberdeck</h3>
            <div className="pr-deck-reihe">
              {deckAktionen.map(([name, wert]) => (
                <button
                  key={name}
                  type="button"
                  data-gewaehlt={deck?.name === name}
                  onClick={() => setDeck(deck?.name === name ? null : { name, wert })}
                >
                  {name} <strong>+{wert}</strong>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Spezialisierung: +1, EIN Chip wählbar (Klick auf den bereits
            gewählten deselektiert — kein Stapeln, siehe Props-Doku oben).
            Selbe Bauweise wie Cyberdeck direkt darüber — keine neue CSS. */}
        {spezialisierungenFuerTrait.length > 0 && (
          <section className="pr-deck">
            <h3>Spezialisierung</h3>
            <div className="pr-deck-reihe">
              {spezialisierungenFuerTrait.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  data-gewaehlt={spezialisierung?.id === s.id}
                  onClick={() => setSpezialisierung(spezialisierung?.id === s.id ? null : s)}
                >
                  {s.text}
                </button>
              ))}
            </div>
          </section>
        )}
        <p className="pr-regel">
          <strong>1–5</strong> Misserfolg · <strong>6–10</strong> Erfolg. Zwei Zehner zählen wie vier Erfolge.
        </p>
      </Fenster>
    </>
  );
}

/** KI hat Matrix statt Körperlich — dieselbe Ersetzung wie auf dem Blatt. */
function attributSpalten(katalog: TraitDef[]) {
  const hatMatrix = katalog.some((t) => t.category === "AttributMatrix");
  const hatKoerper = katalog.some((t) => t.category === "AttributKörperlich");
  const erste =
    hatMatrix && !hatKoerper
      ? { titel: "Matrix", kategorie: "AttributMatrix", ton: "var(--bereich-begleiter)" }
      : SPALTEN[0];
  return [erste, SPALTEN[1], SPALTEN[2]].filter((spalte) =>
    katalog.some((t) => t.category === spalte.kategorie),
  );
}

function FertigkeitsWahl({
  katalog,
  werte,
  ausruestungsBoni,
  zusatzfertigkeiten,
  ausruestungsfertigkeiten,
  basis,
  onWaehlen,
}: {
  katalog: TraitDef[];
  werte: Map<string, number>;
  ausruestungsBoni?: Record<string, number>;
  zusatzfertigkeiten?: { name: string; wert: number }[];
  ausruestungsfertigkeiten?: { name: string; wert: number }[];
  basis: number;
  onWaehlen: (partner: { name: string; wert: number; traitDefId?: string }) => void;
}) {
  const fertigkeiten = katalog.filter((t) => t.category === "Fertigkeit");
  const spalten = FERTIGKEIT_SPALTEN.map((spalte) => ({
    ...spalte,
    eintraege: fertigkeiten.filter((t) => t.sortOrder >= spalte.von && t.sortOrder <= spalte.bis),
  })).filter((spalte) => spalte.eintraege.length > 0);
  const ohneSpalte = fertigkeiten.filter((t) => t.sortOrder < 1 || t.sortOrder > 30);

  function knopf(key: string, name: string, wert: number, traitDefId?: string) {
    return (
      <button key={key} type="button" className="pr-attribut" onClick={() => onWaehlen({ name, wert, traitDefId })}>
        <span className="pr-attribut-name">{name}</span>
        <span className="pr-attribut-summe">{basis + wert}</span>
      </button>
    );
  }

  return (
    <>
      <div className="pr-spalten">
        {spalten.map((spalte) => (
          <section key={spalte.titel} style={{ "--cb-ton": spalte.ton } as React.CSSProperties}>
            <h3 className="pr-spalte-titel">{spalte.titel}</h3>
            {spalte.eintraege.map((t) =>
              knopf(t.id, t.name, (werte.get(t.id) ?? 0) + (ausruestungsBoni?.[t.name] ?? 0), t.id),
            )}
          </section>
        ))}
      </div>
      {ohneSpalte.length > 0 && (
        <section>
          <h3 className="pr-spalte-titel" style={{ "--cb-ton": "var(--wert-fertigkeit)" } as React.CSSProperties}>
            Weitere
          </h3>
          {ohneSpalte.map((t) =>
            knopf(t.id, t.name, (werte.get(t.id) ?? 0) + (ausruestungsBoni?.[t.name] ?? 0), t.id),
          )}
        </section>
      )}
      {(zusatzfertigkeiten?.length ?? 0) > 0 && (
        <section>
          <h3 className="pr-spalte-titel" style={{ "--cb-ton": "var(--p-violett, var(--neon))" } as React.CSSProperties}>
            Zusatzfertigkeiten
          </h3>
          {zusatzfertigkeiten!.map((z) => knopf(`zusatz:${z.name}`, z.name, z.wert))}
        </section>
      )}
      {(ausruestungsfertigkeiten?.length ?? 0) > 0 && (
        <section>
          <h3 className="pr-spalte-titel" style={{ "--cb-ton": "var(--wert-hexkraft)" } as React.CSSProperties}>
            Ausrüstung
          </h3>
          {ausruestungsfertigkeiten!.map((f) => knopf(`ausruestung:${f.name}`, f.name, f.wert))}
        </section>
      )}
    </>
  );
}
