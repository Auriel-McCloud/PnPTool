import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { bogenApi, type Erstellungsregeln } from "../traits/bogenApi";
import { rassenApi, type Rasse } from "./api";
import "./rassen.css";

/**
 * Der Rassen-Baukasten der Spielleitung.
 *
 * Aufbau wie die Gegenstandsübersicht: Kacheln, die sich zum Fenster öffnen
 * (docs/ui-konzept.md, Leitprinzip "nie scrollen"). Bearbeitet wird immer im
 * Popup, nie inline — sonst reisst das Formular die Übersicht auseinander.
 *
 * **Zwei Ebenen, die man nicht verwechseln darf** und die deshalb sichtbar
 * getrennt sind: der Katalog gilt für das ganze Regelwerk, das Häkchen
 * "in dieser Kampagne" nur für die laufende Runde. Eine neue Rasse ist
 * deshalb erst einmal *nicht* freigegeben — das ist ein bewusster zweiter
 * Schritt, kein vergessenes Kästchen.
 */

/** Spannweite der Modifikatoren im Editor. Reicht für alles, was die fünf
 *  eingebauten Rassen brauchen (Troll +2), ohne zur Rutschbahn zu werden. */
const MOD_MIN = -3;
const MOD_MAX = 3;

function Bilanzstreifen({ rasse }: { rasse: Rasse }) {
  const b = rasse.bilanz;
  return (
    <div className="ra-bilanz" data-stimmt={b.stimmt}>
      <span className="ra-bilanz-rechnung">
        {b.punkte} Punkte + {b.vorteile} Vorteile = <strong>{b.summe}</strong> / {b.budget}
      </span>
      <span className="ra-bilanz-nachteile">
        Nachteile {b.nachteile}/{b.nachteileSoll}
      </span>
      <span className="ra-bilanz-urteil">{b.stimmt ? "✓ ausgewogen" : "⚠ weicht ab"}</span>
    </div>
  );
}

export function RassenUebersicht({ campaignId }: { campaignId: string }) {
  const [rassen, setRassen] = useState<Rasse[]>([]);
  const [regeln, setRegeln] = useState<Erstellungsregeln | null>(null);
  const [laedt, setLaedt] = useState(true);
  const [offeneRasse, setOffeneRasse] = useState<Rasse | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuName, setNeuName] = useState("");

  async function neuLaden() {
    const [katalog, r] = await Promise.all([
      rassenApi.katalog(campaignId),
      bogenApi.regeln(campaignId).catch(() => null),
    ]);
    setRassen(katalog);
    if (r) setRegeln(r);
    // Das offene Fenster mitziehen, sonst zeigt es nach dem Speichern noch
    // den Stand von vorher.
    setOffeneRasse((alt) => (alt ? katalog.find((x) => x.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaedt(true);
    neuLaden().finally(() => setLaedt(false));
  }, [campaignId]);

  /** Die drei Attributspalten — dieselbe Reihenfolge wie im Charakterblatt. */
  const spalten = useMemo(() => regeln?.attributKategorien ?? [], [regeln]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    // Mit dem Budget als Vorgabe starten: eine neue Rasse ist damit sofort
    // ausgewogen, statt den Editor rot zu öffnen.
    const neu = await rassenApi.anlegen(campaignId, { name: neuName.trim(), freiePunkte: [7, 5, 3] });
    setNeuName("");
    setAnlegenOffen(false);
    await neuLaden();
    setOffeneRasse(neu);
  }

  async function freigabeSchalten(rasse: Rasse) {
    const ids = rassen.filter((r) => (r.id === rasse.id ? !r.freigegeben : r.freigegeben)).map((r) => r.id);
    await rassenApi.freigabe(campaignId, ids);
    await neuLaden();
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Rassen…</p>;

  const freigegeben = rassen.filter((r) => r.freigegeben).length;

  return (
    <div className="ra-seite">
      <div className="ra-kopf">
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neue Rasse
        </button>
        <span className="ra-anzahl">
          {freigegeben} von {rassen.length} in dieser Kampagne wählbar
        </span>
      </div>

      {freigegeben === 0 && rassen.length > 0 && (
        <p className="ra-warnung">
          ⚠ In dieser Kampagne ist keine einzige Rasse freigegeben — es lässt sich gerade kein Charakter
          erstellen.
        </p>
      )}

      <div className="ra-raster">
        {rassen.map((rasse) => (
          <div key={rasse.id} className="ra-kachel" data-frei={rasse.freigegeben}>
            <button type="button" className="ra-kachel-flaeche" onClick={() => setOffeneRasse(rasse)}>
              <span className="ra-kachel-bild">
                {rasse.bildUrl ? <img src={rasse.bildUrl} alt="" /> : <span aria-hidden="true">◍</span>}
              </span>
              <span className="ra-kachel-name">{rasse.name}</span>
              <span className="ra-kachel-punkte">{rasse.freiePunkte.join(" / ")}</span>
              <span className="ra-kachel-mods">
                {Object.entries(rasse.modifikatoren).length === 0 ? (
                  <em>keine Modifikatoren</em>
                ) : (
                  Object.entries(rasse.modifikatoren).map(([name, wert]) => (
                    <span key={name} data-vorteil={wert > 0}>
                      {wert > 0 ? "+" : ""}
                      {wert} {name}
                    </span>
                  ))
                )}
              </span>
              {!rasse.bilanz.stimmt && <span className="ra-kachel-warnung">⚠ weicht vom Budget ab</span>}
            </button>
            {/* Das Häkchen sitzt bewusst AUF der Kachel und nicht nur im
                Editor: welche Völker in dieser Runde spielbar sind, will man
                auf einen Blick sehen und schnell umstellen können. */}
            <label className="ra-kachel-freigabe">
              <input type="checkbox" checked={rasse.freigegeben} onChange={() => void freigabeSchalten(rasse)} />
              in dieser Kampagne
            </label>
          </div>
        ))}
      </div>

      {rassen.length === 0 && <p className="ra-leer">Noch keine Rassen im Regelwerk.</p>}

      <Fenster
        offen={anlegenOffen}
        titel="Neue Rasse"
        unterzeile="Erst anlegen, dann im Baukasten ausarbeiten"
        kennung="rasse-neu"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
        }}
      >
        <form onSubmit={anlegen} className="ra-neu-form">
          <input
            type="text"
            placeholder="Name der Rasse"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
            required
            autoFocus
          />
          <p className="ra-hinweis">
            Startet mit 7 / 5 / 3 freien Punkten und ohne Modifikatoren — also genau ausgewogen. Vorteile
            kosten anschliessend freie Punkte.
          </p>
          <button type="submit">Anlegen und bearbeiten</button>
        </form>
      </Fenster>

      {offeneRasse && (
        <RasseEditor
          campaignId={campaignId}
          rasse={offeneRasse}
          spalten={spalten}
          onSchliessen={() => setOffeneRasse(null)}
          onGeaendert={neuLaden}
        />
      )}
    </div>
  );
}

/**
 * Der Baukasten für eine einzelne Rasse.
 *
 * Rechnet **nichts** selbst: nach jeder Änderung antwortet der Server mit der
 * neuen Bilanz, und die wird angezeigt. Damit gilt beim Bearbeiten dieselbe
 * Regel wie beim Speichern, und es gibt keine zweite Stelle, an der die
 * Formel gepflegt werden müsste.
 */
function RasseEditor({
  campaignId,
  rasse,
  spalten,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  rasse: Rasse;
  spalten: { id: string; name: string; attribute: string[] }[];
  onSchliessen: () => void;
  onGeaendert: () => Promise<void>;
}) {
  const [name, setName] = useState(rasse.name);
  const [beschreibung, setBeschreibung] = useState(rasse.beschreibung);
  const [punkte, setPunkte] = useState<number[]>(rasse.freiePunkte);
  const [mods, setMods] = useState<Record<string, number>>(rasse.modifikatoren);
  const [laeuft, setLaeuft] = useState(false);
  const [laedtBild, setLaedtBild] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  // Wechselt die Auswahl auf eine andere Rasse, muss das Formular mitziehen.
  useEffect(() => {
    setName(rasse.name);
    setBeschreibung(rasse.beschreibung);
    setPunkte(rasse.freiePunkte);
    setMods(rasse.modifikatoren);
  }, [rasse.id]);

  function modSetzen(attribut: string, wert: number) {
    setMods((alt) => {
      const neu = { ...alt };
      // 0 heisst "kein Modifikator" — dann raus aus der Liste, sonst stünde
      // in der Übersicht "+0 Charisma".
      if (wert === 0) delete neu[attribut];
      else neu[attribut] = wert;
      return neu;
    });
  }

  async function speichern() {
    setLaeuft(true);
    try {
      await rassenApi.aendern(campaignId, rasse.id, {
        name,
        beschreibung,
        freiePunkte: punkte,
        modifikatoren: mods,
      });
      await onGeaendert();
    } finally {
      setLaeuft(false);
    }
  }

  async function bildWaehlen(e: React.ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    if (!datei) return;
    setLaedtBild(true);
    try {
      await rassenApi.bildHochladen(campaignId, rasse.id, datei);
      await onGeaendert();
    } finally {
      setLaedtBild(false);
    }
  }

  async function loeschen() {
    await rassenApi.loeschen(campaignId, rasse.id);
    setLoeschenOffen(false);
    onSchliessen();
    await onGeaendert();
  }

  return (
    <>
      <Fenster
        offen
        breit
        titel={rasse.name}
        unterzeile="Rassen-Baukasten"
        kennung={`rasse:${rasse.id}`}
        onSchliessen={onSchliessen}
      >
        <div className="ra-editor">
          <Bilanzstreifen rasse={rasse} />
          {rasse.bilanz.hinweise.length > 0 && (
            <ul className="ra-hinweise">
              {rasse.bilanz.hinweise.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          )}

          <label className="ra-feld">
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>

          <label className="ra-feld">
            Kurzbeschreibung
            <textarea
              value={beschreibung}
              rows={2}
              placeholder="Ein Satz, der die Rasse fassbar macht — erscheint bei der Charaktererstellung."
              onChange={(e) => setBeschreibung(e.target.value)}
            />
          </label>

          <div className="ra-feld">
            <span>Freie Attributpunkte je Spalte</span>
            <div className="ra-punkte">
              {punkte.map((p, i) => (
                <label key={i}>
                  <em>{i + 1}. Kontingent</em>
                  <input
                    type="number"
                    min={0}
                    value={p}
                    onChange={(e) =>
                      setPunkte(punkte.map((alt, j) => (j === i ? Math.max(0, Number(e.target.value)) : alt)))
                    }
                  />
                </label>
              ))}
              <span className="ra-punkte-summe">= {punkte.reduce((s, p) => s + p, 0)} Punkte</span>
            </div>
            <p className="ra-hinweis">
              Der Spieler verteilt diese drei Kontingente frei auf die drei Attributspalten — welches
              Kontingent auf welche Spalte fällt, entscheidet er selbst.
            </p>
          </div>

          <div className="ra-feld">
            <span>Modifikatoren</span>
            <p className="ra-hinweis">
              Wirken auf Startwert, Erstellungsgrenze <strong>und</strong> das dauerhafte Maximum: +2
              Körperkraft heisst, dieses Volk kommt bis 8 statt 6. Jeder Vorteilspunkt kostet einen freien
              Punkt; Nachteile bringen keine Punkte, gehören aber dazu.
            </p>
            {spalten.map((spalte) => (
              <div key={spalte.id} className="ra-spalte">
                <h4>{spalte.name}</h4>
                {spalte.attribute.map((attribut) => {
                  const wert = mods[attribut] ?? 0;
                  return (
                    <div key={attribut} className="ra-mod" data-gesetzt={wert !== 0}>
                      <span className="ra-mod-name">{attribut}</span>
                      <div className="ra-mod-regler">
                        <button
                          type="button"
                          onClick={() => modSetzen(attribut, Math.max(MOD_MIN, wert - 1))}
                          disabled={wert <= MOD_MIN}
                          aria-label={`${attribut} senken`}
                        >
                          −
                        </button>
                        <span className="ra-mod-wert" data-vorteil={wert > 0} data-nachteil={wert < 0}>
                          {wert > 0 ? "+" : ""}
                          {wert}
                        </span>
                        <button
                          type="button"
                          onClick={() => modSetzen(attribut, Math.min(MOD_MAX, wert + 1))}
                          disabled={wert >= MOD_MAX}
                          aria-label={`${attribut} heben`}
                        >
                          +
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          <div className="ra-feld">
            <span>Bild für die Infobox</span>
            <div className="ra-bild">
              {rasse.bildUrl && <img src={rasse.bildUrl} alt="" />}
              <input type="file" accept="image/*" onChange={bildWaehlen} disabled={laedtBild} />
              {laedtBild && <span className="ra-hinweis">lädt hoch…</span>}
            </div>
          </div>

          <div className="ra-aktionen">
            <button type="button" onClick={speichern} disabled={laeuft} className="ra-speichern">
              Speichern
            </button>
            <button type="button" onClick={() => setLoeschenOffen(true)} className="ra-loeschen">
              🗑 Aus dem Regelwerk entfernen
            </button>
          </div>
        </div>
      </Fenster>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${rasse.name} entfernen?`}
          text="Bestehende Charaktere behalten ihren Rassennamen und bleiben spielbar — die Rasse lässt sich nur nicht mehr neu wählen."
          jaText="Entfernen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}
