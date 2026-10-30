import { useEffect, useMemo, useState } from "react";
import { begleiterApi, type Begleiter } from "../begleiter/api";
import { BegleiterBlatt } from "../begleiter/BegleiterKachel";
import { itemsApi, KAMPF_FERTIGKEIT_LABEL, kampfFertigkeitLesen, schadenArtFuerWaffe, schadenArtLabel, type GegenstandMitBesitzer } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { RuestungsTreffer } from "./RuestungsTreffer";
import { Kaestchen } from "../traits/Kaestchen";
import { WuerfelZehn } from "../traits/WuerfelZehn";
import { bogenApi, type Bogen } from "../traits/bogenApi";
import { anzeigeName } from "../entities/api";
import { Charakterblatt } from "../traits/Charakterblatt";
import { Probe, type ProbeWahl } from "../traits/Probe";
import { WillenskraftFrage } from "../traits/WillenskraftFrage";
import { NEUROWEAVING_POOL_MAX } from "../traits/magie";
import { magieBegriff } from "../traits/magieBegriffe";
import "./kampfkarte.css";

/**
 * Alles, was im Kampf gebraucht wird — auf einer Karte.
 *
 * Mitten im Gefecht will niemand den ganzen Bogen durchsuchen. Hier stehen
 * die Würfelzahlen fertig ausgerechnet: Treffen, Ausweichen, Parieren,
 * Rüstung, Schaden — und je nach Charakter Hexkraft, NeuroWeaving oder das Deck.
 * Begleiter und Fahrzeuge hängen als Kacheln daran, ihre Blätter gehen als
 * eigenes Fenster auf.
 *
 * Quellen (Regelblatt): Treffen Zeile 62, Ausweichen und Parieren Zeile 62/63,
 * Schaden Zeile 66/67, Rüstung Zeile 130-132.
 */

/** Fertigkeiten, mit denen man zuschlägt oder schießt. */
const KAMPFFERTIGKEITEN = ["Nahkampf", "Handgemenge", "Schusswaffen"];

export function wert(bogen: Bogen, name: string) {
  const t = bogen.katalog.find((x) => x.name === name);
  if (!t) return 0;
  return bogen.werte.find((w) => w.traitDefId === t.id)?.rating ?? 0;
}

function ausruestungsBonus(bogen: Bogen, name: string) {
  return bogen.ausruestungsBoni?.[name] ?? 0;
}

/** Geschick der Drohne, Geschicklichkeit beim Menschen. Hot legt den Wert schon auf den Bogen. */
function geschickName(bogen: Bogen) {
  return bogen.person.istDrohne || bogen.person.istFahrzeug ? "Geschick" : "Geschicklichkeit";
}

export function kampfKurz(bogen: Bogen, ruestungKraft = 0) {
  const name = geschickName(bogen);
  const geschick = wert(bogen, name) + ausruestungsBonus(bogen, name);
  const abzug = geschickAbzug(ruestungKraft);
  const effektiv = Math.max(0, geschick - abzug);
  const treffen = (skill: string) => effektiv + wert(bogen, skill) + ausruestungsBonus(bogen, skill);
  const u = bogen.uebersicht;
  const uebrig = u.gesundheitMax - u.schadenSchlag - u.schadenSchwer - u.schadenAggraviert;
  return [
    { kuerzel: "GS", titel: "Gesundheit", wert: `${uebrig}/${u.gesundheitMax}` },
    { kuerzel: "TN", titel: "Treffen Nahkampf", wert: treffen("Nahkampf") },
    { kuerzel: "TS", titel: "Treffen Schusswaffen", wert: treffen("Schusswaffen") },
    { kuerzel: "A", titel: "Ausweichen", wert: effektiv + wert(bogen, "Sportlichkeit") + ausruestungsBonus(bogen, "Sportlichkeit") },
    { kuerzel: "P", titel: "Parieren", wert: treffen("Nahkampf") },
    { kuerzel: "I", titel: "Initiative", wert: u.initiative },
  ];
}

/** Waffenschaden. Bei Chrom ist `kraft` der Implantat-Bonus, nicht die Klinge. */
function waffenSchaden(w: GegenstandMitBesitzer) {
  if (w.typ === "Waffe") return w.schaden || w.kraft;
  return w.schaden;
}

/**
 * Abzug auf Geschicklichkeit durch schwere Rüstung (Zeilen 131-132):
 * Wert 3 kostet 1, Wert 4 kostet 2.
 *
 * Das Blatt sagt nicht, ob der Wert je Stück oder in Summe gilt. Hier gilt
 * die **Summe** — sonst bliebe der Abzug bei drei leichten Westen aus, die
 * zusammen mehr schützen als ein schwerer Anzug.
 */
function geschickAbzug(ruestung: number) {
  if (ruestung >= 4) return 2;
  if (ruestung >= 3) return 1;
  return 0;
}

export function Kampfkarte({
  campaignId,
  personId,
  aenderbar = false,
  kompaktStart = false,
  onInitiativeKlick,
}: {
  campaignId: string;
  personId: string;
  /** Schaden und Willenskraft eintragen — der eigene Charakter, oder die SL. */
  aenderbar?: boolean;
  /** Startet eingeklappt: nur eine kleine Kopfzeile mit Gesundheit/TN/TS/
   *  A/P/I in Kurzform, antippen zeigt den Rest ausgeschrieben (Mark,
   *  26.10.2026 — für die Drohnen-Steckbriefe im Kampfmenü). */
  kompaktStart?: boolean;
  /** Macht die Initiative-Zahl antippbar (Mark, 26.10.2026: kein eigener
   *  Knopf — genau wie in der Initiativliste reicht ein Klick auf den
   *  Wert). Nur für Drohnen-Steckbriefe gesetzt. */
  onInitiativeKlick?: () => void;
}) {
  const [bogen, setBogen] = useState<Bogen | null>(null);
  const [sachen, setSachen] = useState<GegenstandMitBesitzer[]>([]);
  const [begleiter, setBegleiter] = useState<Begleiter[]>([]);
  const [vollerBogen, setVollerBogen] = useState(false);
  const [offenerBegleiter, setOffenerBegleiter] = useState<Begleiter | null>(null);
  // Angetippter Wert — für Hexkraft heisst das: Willenskraft dazugeben.
  const [probe, setProbe] = useState<ProbeWahl | null>(null);
  const [fragtWillenskraft, setFragtWillenskraft] = useState(false);
  const [erklaertRuestung, setErklaertRuestung] = useState(false);
  const [trefferOffen, setTrefferOffen] = useState(false);
  // Kompakt-Kopfzeile (Drohnen-Steckbrief): eingeklappt zeigt nur TN/TS/A/P/I
  // in Kurzform, Antippen klappt den Rest auf wie gehabt.
  const [aufgeklappt, setAufgeklappt] = useState(!kompaktStart);
  // Kampf/Cyberkampf-Umschalter (Mark, 30.10.2026): bei einem Decker kommen
  // sonst Nahkampf-Würfel UND Cyberdeck-Werte untereinander — genau das
  // zwang zum Scrollen vorbei an Gesundheit/Rüstung/Willenskraft. Nur einer
  // der beiden Blöcke ist gleichzeitig sichtbar, umschaltbar per Knopf.
  const [kampfModus, setKampfModus] = useState<"kampf" | "cyberkampf">("kampf");

  async function laden() {
    const [b, s, bg] = await Promise.all([
      bogenApi.laden(campaignId, personId),
      itemsApi.listAlle(campaignId),
      begleiterApi.liste(campaignId).catch(() => []),
    ]);
    setBogen(b);
    setSachen(s.filter((g) => g.ownerId === personId));
    setBegleiter(bg.filter((x) => x.besitzerId === personId));
  }

  useEffect(() => {
    void laden();
  }, [campaignId, personId]);

  const ausgeruestet = useMemo(() => sachen.filter((g) => g.ablage === "AUSGERUESTET"), [sachen]);
  const waffen = ausgeruestet.filter((g) => g.typ === "Waffe" || g.istWaffe);
  const ruestungsteile = ausgeruestet.filter((g) => g.typ === "Rüstung");
  const ruestung = ruestungsteile.reduce((summe, g) => summe + g.kraft, 0);
  const fahrzeuge = sachen.filter((g) => g.typ === "Fahrzeug" || g.typ === "Drohne");
  // Ki-Tama-Attacken (30.10.2026, Marks Idee): ausruestungsfertigkeiten, die
  // als "Attacke" markiert sind, erscheinen zusätzlich zu den Waffen oben —
  // mit eigener Formel. KEIN Ausrüstungsbonus und KEINE Geschicklichkeit wie
  // bei Waffen: Mark, 30.10.2026 — "genau Intelligenz + Fertigkeitswert,
  // keine weiteren Boni". Schaden ist bewusst kein fixer Wert, sondern wie
  // bei Waffen die Nettoerfolge — siehe items/schemas.py::attackenFertigkeiten.
  const attacken = ausgeruestet.flatMap((g) =>
    Object.entries(g.ausruestungsfertigkeiten || {})
      .filter(([name]) => g.attackenFertigkeiten?.[name])
      .map(([name, w]) => ({
        key: `${g.id}:${name}`,
        name: Object.keys(g.ausruestungsfertigkeiten).length > 1 ? `${name} (${g.name})` : name,
        wert: Number(w) || 0,
        schadenArt: schadenArtFuerWaffe(g.attackenSchadensart?.[name]),
      })),
  );

  if (!bogen) return <p style={{ color: "var(--text-leise)" }}>Lade Kampfwerte…</p>;

  const u = bogen.uebersicht;
  const geschick = wert(bogen, geschickName(bogen)) + ausruestungsBonus(bogen, geschickName(bogen));
  const abzug = geschickAbzug(ruestung);
  const geschickEffektiv = Math.max(0, geschick - abzug);
  const treffenPool = (skill: string) => geschickEffektiv + wert(bogen, skill) + ausruestungsBonus(bogen, skill);
  // Intelligenz-Attribut ohne jeden weiteren Bonus — Ki-Tama-Attacken rechnen
  // bewusst anders als Waffen (keine Ausrüstungsboni, kein Rüstungsabzug).
  const intelligenz = wert(bogen, "Intelligenz");
  // Was noch da ist — verbrauchte Willenskraft steht für Zauber nicht mehr
  // zur Verfügung.
  const uebrigeWillenskraft = Math.max(0, u.willenskraftMax - u.willenskraftVerbraucht);

  // --- Kompakt-Kopfzeile: Gesundheit + TN/TS/A/P/I in Kurzform ---------
  // Mark, 26.10.2026: "möglichst alles in klein ... dann sieht er alles in
  // klein, kann aber drauf klicken und sieht es dann ausgeschrieben und
  // schöner" — dieselben Zahlen wie unten, nur knapp beschriftet.
  const kompaktWerte = kampfKurz(bogen, ruestung);
  // Der Umschalter erscheint nur, wenn überhaupt ein Cyberdeck ausgerüstet
  // ist — sonst gibt es nichts zum Umschalten, und die Karte bleibt wie
  // gehabt (ein Block, keine Knöpfe).
  const hatDeck = Object.keys(bogen.deckBoni ?? {}).length > 0;

  return (
    <div className="kk-karte">
      {/* Kompakt-Kopfzeile NUR für Drohnen-Steckbriefe (kompaktStart) — der
          eigene Charakter zeigt seine Werte immer groß und ausgeschrieben,
          kein Einklapp-Knopf über den eigenen Werten (Mark, 26.10.2026: das
          ist Webseiten-Optik, nicht Programm-Gefühl). */}
      {kompaktStart && (
        <button type="button" className="kk-kompakt" onClick={() => setAufgeklappt((a) => !a)}>
          {kompaktWerte.map((k) => (
            <span key={k.kuerzel} className="kk-kompakt-wert" title={k.titel}>
              <em>{k.kuerzel}</em>
              {k.wert}
            </span>
          ))}
          <span className="kk-kompakt-pfeil" aria-hidden="true">
            {aufgeklappt ? "▲" : "▼"}
          </span>
        </button>
      )}

      {(aufgeklappt || !kompaktStart) && (
        <>
      {/* --- Zustand ---------------------------------------------------- */}
      <section className="kk-zustand">
        <div className="kk-spur">
          <span className="kk-titel">Gesundheit</span>
          <Kaestchen
            max={u.gesundheitMax}
            schaden={{
              schlag: u.schadenSchlag,
              schwer: u.schadenSchwer,
              aggraviert: u.schadenAggraviert,
            }}
            ton="var(--track-gesundheit)"
            onKlick={
              aenderbar
                ? async (index) => {
                    const { schadenAggraviert: a, schadenSchwer: sw, schadenSchlag: sl } = u;
                    let neu = { schadenAggraviert: a, schadenSchwer: sw, schadenSchlag: sl };
                    if (index < a) neu = { ...neu, schadenAggraviert: a - 1 };
                    else if (index < a + sw) neu = { ...neu, schadenSchwer: sw - 1, schadenAggraviert: a + 1 };
                    else if (index < a + sw + sl) neu = { ...neu, schadenSchlag: sl - 1, schadenSchwer: sw + 1 };
                    else neu = { ...neu, schadenSchlag: sl + 1 };
                    await bogenApi.zustand(campaignId, personId, neu);
                    await laden();
                  }
                : undefined
            }
          />
        </div>
        {/* Dieselbe Rüstungsübersicht wie im Charakterblatt (Kästchen +
            Reduktion, server-gerechnet über bogen.ruestung) — zwischen
            Gesundheit und Willenskraft, weil Rüstung genau das ist, was
            zwischen einem Treffer und der Gesundheit liegt (siehe
            Charakterblatt.tsx). Nicht mehr lokal aus den Gegenständen
            nachgerechnet, sonst laufen beide Anzeigen auseinander. */}
        {bogen.ruestung.kaestchenMax > 0 && (
          <div className="kk-spur">
            <span className="kk-titel">
              Rüstung
              {bogen.ruestung.teile.length > 1 && (
                <span className="kk-hinweis"> · {bogen.ruestung.teile.length} Teile, zuerst {bogen.ruestung.teile[0].name}</span>
              )}
            </span>
            <Kaestchen
              max={bogen.ruestung.kaestchenMax}
              verbraucht={bogen.ruestung.kaestchenMax - bogen.ruestung.kaestchenAktuell}
              ton="var(--track-ruestung)"
            />
            <span className="kk-hinweis">
              Reduktion {bogen.ruestung.reduktionEffektiv}
              {bogen.ruestung.reduktionEffektiv < bogen.ruestung.reduktionBasis &&
                ` / ${bogen.ruestung.reduktionBasis}`}{" "}
              — wie viel Schaden pro Treffer abgefangen wird
            </span>
          </div>
        )}
        <div className="kk-spur">
          <span className="kk-titel">Willenskraft</span>
          <Kaestchen
            max={u.willenskraftMax}
            verbraucht={u.willenskraftVerbraucht}
            ton="var(--wert-gesellschaftlich)"
            onKlick={
              aenderbar
                ? (index) => {
                    // Ausgeben ja, zurückholen nur als Spielleitung. Und erst
                    // nach Rückfrage — versehentlich getroffen ist der Punkt
                    // sonst weg, und zurückholen kann ihn nur die SL.
                    // Verbraucht füllt von links (Puffer zuerst, siehe
                    // Kaestchen.tsx) — ein Klick auf ein bereits verbrauchtes
                    // Feld tut hier nichts (kein Rückgabe-Weg in der Kampfkarte).
                    if (index < u.willenskraftVerbraucht) return;
                    setFragtWillenskraft(true);
                  }
                : undefined
            }
          />
          <span className="kk-hinweis">
            {uebrigeWillenskraft} übrig — für erzwungene Erfolge oder wilde Magie
          </span>
        </div>
        <Zahl titel="Initiative" wert={u.initiative} wuerfel onKlick={onInitiativeKlick} />
        {/* Mark, 30.10.2026: direkt neben die Initiative statt weiter unten
            bei Rüstung/Waffen vergraben — im Gefecht trifft man zuerst auf
            die Initiative, der Treffer gehört in denselben Blick. */}
        {aenderbar && (
          <button
            type="button"
            className="kk-treffer-knopf"
            style={{ alignSelf: "center" }}
            onClick={() => setTrefferOffen(true)}
          >
            ⚡ Treffer eintragen
          </button>
        )}
      </section>

      {/* --- Was man würfelt -------------------------------------------- */}
      <section className="kk-block">
        <div className="kk-block-kopf">
          <h3>{hatDeck && kampfModus === "cyberkampf" ? "Cyberdeck" : "Würfeln"}</h3>
          {hatDeck && (
            <div className="kk-modus-schalter">
              <button
                type="button"
                className="kk-modus-knopf"
                data-aktiv={kampfModus === "kampf"}
                onClick={() => setKampfModus("kampf")}
              >
                Kampf
              </button>
              <button
                type="button"
                className="kk-modus-knopf"
                data-aktiv={kampfModus === "cyberkampf"}
                onClick={() => setKampfModus("cyberkampf")}
              >
                Cyberkampf
              </button>
            </div>
          )}
        </div>
        {kampfModus === "kampf" && (
          <div className="kk-werte">
            {KAMPFFERTIGKEITEN.map((name) => {
              const f = wert(bogen, name) + ausruestungsBonus(bogen, name);
              if (f === 0 && name !== "Nahkampf") return null;
              return <Zahl key={name} titel={`Treffen · ${name}`} wert={geschickEffektiv + f} wuerfel />;
            })}
            <Zahl
              titel="Ausweichen"
              wert={geschickEffektiv + wert(bogen, "Sportlichkeit") + ausruestungsBonus(bogen, "Sportlichkeit")}
              hinweis="Geschicklichkeit + Sportlichkeit, plus Ausrüstung. Jeder weitere Einsatz in derselben Runde: −1."
              wuerfel
            />
            <Zahl
              titel="Parieren"
              wert={treffenPool("Nahkampf")}
              hinweis="Geschicklichkeit + Nahkampf, plus Ausrüstung. Gegen Fernkampf nur mit Cyberware oder Magie. Jeder weitere Einsatz: −1."
              wuerfel
            />
          </div>
        )}
        {hatDeck && kampfModus === "cyberkampf" && (
          <div className="kk-werte">
            {Object.entries(bogen.deckBoni).map(([name, w]) => (
              <Zahl
                key={name}
                titel={name}
                // Pool wie überall sonst: Deck-Wert + Matrix-Fertigkeit —
                // NICHT der rohe Deck-Bonus allein (siehe Probe.tsx::
                // CYBERDECK_PARTNER_FERTIGKEIT, Charakterblatt.tsx).
                wert={w + wert(bogen, "Matrix") + ausruestungsBonus(bogen, "Matrix")}
                hinweis="Cyberdeck-Aktion + Matrix. Antippen für die Würfelrechnung."
                wuerfel
                onKlick={() => setProbe({ name, wert: w, kategorie: "Cyberdeck" })}
              />
            ))}
          </div>
        )}
      </section>

      {/* --- Rüstung und Waffen ----------------------------------------- */}
      {/* Im Cyberkampf-Modus ausgeblendet (Mark, 30.10.2026): wer gerade im
          Deck steckt, braucht die Waffenliste nicht — weniger zu scrollen. */}
      {(!hatDeck || kampfModus === "kampf") && (
        <section className="kk-block">
          <h3>Schutz und Schaden</h3>
          <div className="kk-werte">
            {ruestung > 0 && (
              <Zahl
                titel="Rüstungsbonus"
                wert={ruestung}
                hinweis="Antippen: wie Schaden abgefangen wird (alter, flacher Bonus)"
                onKlick={() => setErklaertRuestung(true)}
              />
            )}
          </div>
          {/* Dieselbe Rüstungsübersicht wie im Charakterblatt steht jetzt oben
              zwischen Gesundheit und Willenskraft, nicht mehr hier. */}
          {waffen.length === 0 && attacken.length === 0 ? (
            <p className="kk-leer">Nichts ausgerüstet.</p>
          ) : (
            <ul className="kk-waffen">
              {waffen.map((w) => {
                const skill = kampfFertigkeitLesen(w.kampfFertigkeit);
                const schaden = waffenSchaden(w);
                return (
                  <li key={w.id}>
                    <span className="kk-waffe-name">{w.name}</span>
                    {skill && (
                      <span
                        className="kk-waffe-pool"
                        title={`Geschicklichkeit + ${skill}, Ausrüstung schon drin`}
                      >
                        {KAMPF_FERTIGKEIT_LABEL[skill]} {treffenPool(skill)}
                        <WuerfelZehn groesse={14} />
                      </span>
                    )}
                    <span className="kk-waffe-schaden">
                      Schaden {schaden}
                      <em>+ Nettoerfolge</em>
                    </span>
                  </li>
                );
              })}
              {attacken.map((a) => (
                <li key={a.key}>
                  <span className="kk-waffe-name">{a.name}</span>
                  <span className="kk-waffe-pool" title="Intelligenz + Fertigkeitswert, keine weiteren Boni">
                    INT {intelligenz + a.wert}
                    <WuerfelZehn groesse={14} />
                  </span>
                  <span className="kk-waffe-schaden">
                    {schadenArtLabel(a.schadenArt)}
                    <em>Nettoerfolge</em>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {/* --- Was diesen Charakter besonders macht ------------------------ */}
      {u.weg === "MAGIER" && (
        <section className="kk-block">
          <h3>Magie</h3>
          <div className="kk-werte">
            <Zahl
              titel={magieBegriff(u.magieFlavor, "Hexkraft")}
              wert={wert(bogen, "Hexkraft")}
              hinweis={`Antippen, um Willenskraft dazuzugeben — noch ${uebrigeWillenskraft} übrig.`}
              wuerfel
              onKlick={() => setProbe({ name: "Hexkraft", wert: wert(bogen, "Hexkraft"), kategorie: "Hexkraft" })}
            />
          </div>
          <div className="kk-sphaeren">
            {bogen.katalog
              .filter((t) => t.category === "Sphäre")
              .map((t) => {
                const w = bogen.werte.find((x) => x.traitDefId === t.id)?.rating ?? 0;
                return (
                  <span key={t.id} data-leer={w === 0}>
                    {magieBegriff(u.magieFlavor, t.name)} <strong>{w}</strong>
                  </span>
                );
              })}
          </div>
        </section>
      )}

      {u.weg === "NEUROWEAVER" && (
        <section className="kk-block">
          <h3>NeuroWeaving</h3>
          <div className="kk-werte">
            {bogen.katalog
              .filter((t) => t.category === "NeuroWeaving")
              .map((t) => {
                const f = bogen.werte.find((x) => x.traitDefId === t.id)?.rating ?? 0;
                return (
                  <Zahl
                    key={t.id}
                    titel={t.name}
                    wert={Math.min(NEUROWEAVING_POOL_MAX, wert(bogen, "NeuroWeaving") + f)}
                    hinweis={`NeuroWeaving + Fertigkeit, höchstens ${NEUROWEAVING_POOL_MAX}. Antippen für Willenskraft — noch ${uebrigeWillenskraft} übrig.`}
                    wuerfel
                    onKlick={() => setProbe({ name: t.name, wert: f, kategorie: "NeuroWeaving" })}
                  />
                );
              })}
          </div>
        </section>
      )}

      {/* --- Wer sonst noch mitkämpft ------------------------------------ */}
      {(begleiter.length > 0 || fahrzeuge.length > 0) && (
        <section className="kk-block">
          <h3>Dabei</h3>
          <div className="kk-dabei">
            {begleiter.map((b) => (
              <button key={b.id} type="button" onClick={() => setOffenerBegleiter(b)}>
                <span>{b.name}</span>
                <em>Stufe {b.stufe}</em>
              </button>
            ))}
            {fahrzeuge.map((g) => (
              <span key={g.id} className="kk-fahrzeug">
                <span>{g.name}</span>
                <em>
                  {g.stufe > 0 ? `Stufe ${g.stufe}` : g.typ}
                  {g.angriff > 0 && ` · Angriff ${g.angriff}`}
                </em>
              </span>
            ))}
          </div>
        </section>
      )}

      <button type="button" className="kk-ganzer" onClick={() => setVollerBogen(true)}>
        Ganzer Bogen
      </button>
        </>
      )}

      <Fenster
        offen={vollerBogen}
        breit
        titel={anzeigeName(bogen.person.name, bogen.uebersicht.alias)}
        unterzeile="Charakterbogen"
        kennung={`kampfkarte-bogen:${personId}`}
        onSchliessen={() => {
          setVollerBogen(false);
          void laden();
        }}
      >
        <Charakterblatt campaignId={campaignId} personId={personId} aenderbar={aenderbar} />
      </Fenster>

      <Fenster
        offen={erklaertRuestung}
        titel={`Rüstung ${ruestung}`}
        unterzeile="Wie Schaden abgefangen wird"
        kennung="ruestung-erklaerung"
        onSchliessen={() => setErklaertRuestung(false)}
      >
        <p className="kk-erklaerung">
          Der <strong>Rüstungsbonus</strong> aller getragenen Stücke wird zusammengezählt und dem
          eingehenden Schaden entgegengesetzt (Regelblatt Zeile 66-67, 76).
        </p>
        <ul className="kk-rechenweg">
          <li>
            <span>Fernkampf</span> Waffenschaden + Nettoerfolge des Treffers <em>gegen</em> deine
            Rüstung
          </li>
          <li>
            <span>Nahkampf</span> Waffenschaden + Körperkraft des Angreifers + Nettoerfolge{" "}
            <em>gegen</em> deine Rüstung
          </li>
        </ul>
        {ruestung === 0 ? (
          <p className="kk-erklaerung kk-warnend">
            Du trägst nichts. Jeder Treffer kommt ungebremst durch.
          </p>
        ) : (
          <p className="kk-erklaerung">
            Du fängst derzeit <strong>{ruestung}</strong> ab.
            {abzug > 0 && (
              <>
                {" "}
                Ab Rüstung 3 wird es unbequem: <strong>−{abzug}</strong> auf Geschicklichkeit, schon
                eingerechnet in Treffen, Ausweichen und Parieren.
              </>
            )}
          </p>
        )}
        <p className="kk-erklaerung kk-leise">
          Ein Widerstandswurf steht nicht im Regelblatt — dort fängt allein die Rüstung ab. Falls
          Widerstandsfähigkeit doch mitspielen soll, fehlt die Zahl hier noch.
        </p>
      </Fenster>

      <RuestungsTreffer
        campaignId={campaignId}
        personId={personId}
        offen={trefferOffen}
        onSchliessen={() => setTrefferOffen(false)}
        onAngewendet={laden}
      />

      <WillenskraftFrage
        offen={fragtWillenskraft}
        uebrig={uebrigeWillenskraft}
        weg={u.weg}
        magieFlavor={u.magieFlavor}
        onNein={() => setFragtWillenskraft(false)}
        onJa={async () => {
          setFragtWillenskraft(false);
          await bogenApi.zustand(campaignId, personId, {
            willenskraftVerbraucht: u.willenskraftVerbraucht + 1,
          });
          await laden();
        }}
      />

      <Probe
        wahl={probe}
        katalog={bogen.katalog}
        werte={new Map(bogen.werte.map((w) => [w.traitDefId, w.rating]))}
        willenskraft={uebrigeWillenskraft}
        deckBoni={bogen.deckBoni}
        ausruestungsBoni={bogen.ausruestungsBoni}
        magieFlavor={u.magieFlavor}
        onSchliessen={() => setProbe(null)}
      />

      <Fenster
        offen={offenerBegleiter !== null}
        titel={offenerBegleiter?.name ?? ""}
        unterzeile="Begleiter"
        kennung={`kampfkarte-begleiter:${offenerBegleiter?.id ?? ""}`}
        onSchliessen={() => setOffenerBegleiter(null)}
      >
        {offenerBegleiter && <BegleiterBlatt begleiter={offenerBegleiter} />}
      </Fenster>
    </div>
  );
}

function Zahl({
  titel,
  wert,
  hinweis,
  wuerfel = false,
  onKlick,
}: {
  titel: string;
  wert: number;
  hinweis?: string;
  /** Steht die Zahl für Würfel? Dann das W10-Zeichen daneben. */
  wuerfel?: boolean;
  /** Macht die Kachel antippbar — etwa um Willenskraft dazuzugeben. */
  onKlick?: () => void;
}) {
  const inhalt = (
    <>
      <span className="kk-titel">{titel}</span>
      <span className="kk-ziffer">
        {wert}
        {wuerfel && <WuerfelZehn groesse={15} />}
      </span>
    </>
  );
  if (!onKlick) {
    return (
      <div className="kk-zahl" title={hinweis}>
        {inhalt}
      </div>
    );
  }
  return (
    <button type="button" className="kk-zahl kk-zahl-knopf" title={hinweis} onClick={onKlick}>
      {inhalt}
    </button>
  );
}
