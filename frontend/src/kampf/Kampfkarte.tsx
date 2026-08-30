import { useEffect, useMemo, useState } from "react";
import { begleiterApi, type Begleiter } from "../begleiter/api";
import { BegleiterBlatt } from "../begleiter/BegleiterKachel";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { Kaestchen } from "../traits/Kaestchen";
import { WuerfelZehn } from "../traits/WuerfelZehn";
import { bogenApi, type Bogen } from "../traits/bogenApi";
import { Charakterblatt } from "../traits/Charakterblatt";
import { Probe, type ProbeWahl } from "../traits/Probe";
import "./kampfkarte.css";

/**
 * Alles, was im Kampf gebraucht wird — auf einer Karte.
 *
 * Mitten im Gefecht will niemand den ganzen Bogen durchsuchen. Hier stehen
 * die Würfelzahlen fertig ausgerechnet: Treffen, Ausweichen, Parieren,
 * Rüstung, Schaden — und je nach Charakter Arete, NeuroWeaving oder das Deck.
 * Begleiter und Fahrzeuge hängen als Kacheln daran, ihre Blätter gehen als
 * eigenes Fenster auf.
 *
 * Quellen (Regelblatt): Treffen Zeile 62, Ausweichen und Parieren Zeile 62/63,
 * Schaden Zeile 66/67, Rüstung Zeile 130-132.
 */

/** Fertigkeiten, mit denen man zuschlägt oder schießt. */
const KAMPFFERTIGKEITEN = ["Nahkampf", "Handgemenge", "Schusswaffen"];

function wert(bogen: Bogen, name: string) {
  const t = bogen.katalog.find((x) => x.name === name);
  if (!t) return 0;
  return bogen.werte.find((w) => w.traitDefId === t.id)?.rating ?? 0;
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
}: {
  campaignId: string;
  personId: string;
  /** Schaden und Willenskraft eintragen — der eigene Charakter, oder die SL. */
  aenderbar?: boolean;
}) {
  const [bogen, setBogen] = useState<Bogen | null>(null);
  const [sachen, setSachen] = useState<GegenstandMitBesitzer[]>([]);
  const [begleiter, setBegleiter] = useState<Begleiter[]>([]);
  const [vollerBogen, setVollerBogen] = useState(false);
  const [offenerBegleiter, setOffenerBegleiter] = useState<Begleiter | null>(null);
  // Angetippter Wert — für Arete heisst das: Willenskraft dazugeben.
  const [probe, setProbe] = useState<ProbeWahl | null>(null);

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
  const waffen = ausgeruestet.filter((g) => g.typ === "Waffe");
  const ruestung = ausgeruestet
    .filter((g) => g.typ === "Rüstung")
    .reduce((summe, g) => summe + g.kraft, 0);
  const fahrzeuge = sachen.filter((g) => g.typ === "Fahrzeug" || g.typ === "Drohne");

  if (!bogen) return <p style={{ color: "var(--text-leise)" }}>Lade Kampfwerte…</p>;

  const u = bogen.uebersicht;
  const geschick = wert(bogen, "Geschicklichkeit");
  const kraft = wert(bogen, "Körperkraft");
  const abzug = geschickAbzug(ruestung);
  const geschickEffektiv = Math.max(0, geschick - abzug);
  // Was noch da ist — verbrauchte Willenskraft steht für Zauber nicht mehr
  // zur Verfügung.
  const uebrigeWillenskraft = Math.max(0, u.willenskraftMax - u.willenskraftVerbraucht);

  return (
    <div className="kk-karte">
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
            ton="#ff4d6b"
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
        <div className="kk-spur">
          <span className="kk-titel">Willenskraft</span>
          <Kaestchen
            max={u.willenskraftMax}
            verbraucht={u.willenskraftVerbraucht}
            ton="#ffb648"
            onKlick={
              aenderbar
                ? async (index) => {
                    // Ausgeben ja, zurückholen nur als Spielleitung — dafür
                    // gibt es den eigenen Bogen (siehe Charakterblatt).
                    const frei = u.willenskraftMax - u.willenskraftVerbraucht;
                    if (index >= frei) return;
                    await bogenApi.zustand(campaignId, personId, {
                      willenskraftVerbraucht: u.willenskraftVerbraucht + 1,
                    });
                    await laden();
                  }
                : undefined
            }
          />
          <span className="kk-hinweis">
            {uebrigeWillenskraft} übrig — für erzwungene Erfolge oder wilde Magie
          </span>
        </div>
        <Zahl titel="Initiative" wert={u.initiative} wuerfel />
      </section>

      {/* --- Was man würfelt -------------------------------------------- */}
      <section className="kk-block">
        <h3>Würfeln</h3>
        <div className="kk-werte">
          {KAMPFFERTIGKEITEN.map((name) => {
            const f = wert(bogen, name);
            if (f === 0 && name !== "Nahkampf") return null;
            return <Zahl key={name} titel={`Treffen · ${name}`} wert={geschickEffektiv + f} wuerfel />;
          })}
          <Zahl
            titel="Ausweichen"
            wert={geschickEffektiv + wert(bogen, "Sportlichkeit")}
            hinweis="Geschicklichkeit + Sportlichkeit. Jeder weitere Einsatz in derselben Runde: −1."
            wuerfel
          />
          <Zahl
            titel="Parieren"
            wert={geschickEffektiv + wert(bogen, "Nahkampf")}
            hinweis="Geschicklichkeit + Waffenfertigkeit. Gegen Fernkampf nur mit Cyberware oder Magie. Jeder weitere Einsatz: −1."
            wuerfel
          />
        </div>
      </section>

      {/* --- Rüstung und Waffen ----------------------------------------- */}
      <section className="kk-block">
        <h3>Schutz und Schaden</h3>
        <div className="kk-werte">
          <Zahl
            titel="Rüstung"
            wert={ruestung}
            hinweis={
              abzug > 0
                ? `Wird vom Schaden abgezogen. Schwer genug für −${abzug} auf Geschicklichkeit — ist schon eingerechnet.`
                : "Wird vom erlittenen Schaden abgezogen."
            }
          />
        </div>
        {waffen.length === 0 ? (
          <p className="kk-leer">Nichts ausgerüstet.</p>
        ) : (
          <ul className="kk-waffen">
            {waffen.map((w) => (
              <li key={w.id}>
                <span className="kk-waffe-name">{w.name}</span>
                <span className="kk-waffe-schaden">
                  {w.kraft}
                  <em>+ Nettoerfolge</em>
                </span>
                <span className="kk-waffe-nah">
                  im Nahkampf {w.kraft + kraft}
                  <em>+ Körperkraft</em>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* --- Was diesen Charakter besonders macht ------------------------ */}
      {u.weg === "MAGIER" && (
        <section className="kk-block">
          <h3>Magie</h3>
          <div className="kk-werte">
            <Zahl
              titel="Arete"
              wert={wert(bogen, "Arete")}
              hinweis={`Antippen, um Willenskraft dazuzugeben — noch ${uebrigeWillenskraft} übrig.`}
              wuerfel
              onKlick={() => setProbe({ name: "Arete", wert: wert(bogen, "Arete"), kategorie: "Arete" })}
            />
          </div>
          <div className="kk-sphaeren">
            {bogen.katalog
              .filter((t) => t.category === "Sphäre")
              .map((t) => {
                const w = bogen.werte.find((x) => x.traitDefId === t.id)?.rating ?? 0;
                return (
                  <span key={t.id} data-leer={w === 0}>
                    {t.name} <strong>{w}</strong>
                  </span>
                );
              })}
          </div>
        </section>
      )}

      {u.weg === "TECHNOMANCER" && (
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
                    wert={Math.min(10, wert(bogen, "NeuroWeaving") + f)}
                    hinweis={`NeuroWeaving + Fertigkeit, höchstens 10. Antippen für Willenskraft — noch ${uebrigeWillenskraft} übrig.`}
                    wuerfel
                    onKlick={() => setProbe({ name: t.name, wert: f, kategorie: "NeuroWeaving" })}
                  />
                );
              })}
          </div>
        </section>
      )}

      {Object.keys(bogen.deckBoni ?? {}).length > 0 && (
        <section className="kk-block">
          <h3>Cyberdeck</h3>
          <div className="kk-werte">
            {Object.entries(bogen.deckBoni).map(([name, w]) => (
              <Zahl key={name} titel={name} wert={w} hinweis="Bonuswürfel für diese Aktion." />
            ))}
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

      <Fenster
        offen={vollerBogen}
        breit
        titel={bogen.person.name}
        unterzeile="Charakterbogen"
        kennung={`kampfkarte-bogen:${personId}`}
        onSchliessen={() => {
          setVollerBogen(false);
          void laden();
        }}
      >
        <Charakterblatt campaignId={campaignId} personId={personId} aenderbar={aenderbar} />
      </Fenster>

      <Probe
        wahl={probe}
        katalog={bogen.katalog}
        werte={new Map(bogen.werte.map((w) => [w.traitDefId, w.rating]))}
        willenskraft={uebrigeWillenskraft}
        deckBoni={bogen.deckBoni}
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
