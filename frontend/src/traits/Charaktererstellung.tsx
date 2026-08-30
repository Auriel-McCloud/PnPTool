import { useEffect, useMemo, useState } from "react";
import { DotPool } from "./DotPool";
import { api } from "../api/client";
import { traitsApi, type TraitDef } from "./api";
import { Fenster } from "../shell/Fenster";
import {
  bogenApi,
  KATEGORIE_TITEL,
  type Erstellungsregeln,
  type ErstellungEingabe,
  type FertigkeitsPaket,
  type Rasse,
} from "./bogenApi";
import "./erstellung.css";

/**
 * Charaktererstellung — Prototyp.
 *
 * Führt in sieben Schritten durch das, was `Neotopia.xlsx` (Blatt *Regeln*,
 * Zeilen 1-42) beschreibt. Die Regeln selbst stehen **nicht hier**, sondern
 * kommen von `/erstellung/regeln`; diese Ansicht rechnet nur mit, was noch
 * offen ist, und lässt weiterklicken, wenn ein Schritt aufgeht.
 *
 * Endgültig entscheidet immer der Server: `traits/erstellung.pruefe` sieht
 * dieselbe Einreichung noch einmal an und lehnt ab, was nicht passt. Die
 * Rechnerei hier ist Bequemlichkeit, keine Absicherung.
 */

const SCHRITTE = [
  { id: "weg", titel: "Weg" },
  { id: "rasse", titel: "Rasse" },
  { id: "attribute", titel: "Attribute" },
  { id: "fertigkeiten", titel: "Fertigkeiten" },
  { id: "hintergrund", titel: "Hintergrund" },
  { id: "freebees", titel: "Freebees" },
  { id: "person", titel: "Person" },
] as const;

/** Farben wie auf dem fertigen Blatt, damit man sich sofort zurechtfindet. */
const TON: Record<string, string> = {
  AttributKörperlich: "#ff6b4d",
  AttributGesellschaftlich: "#ffb648",
  AttributGeistig: "#4d8bd8",
  Fertigkeit: "#00e5ff",
  Arete: "#c76bff",
  Sphäre: "#a865d8",
  NeuroWeaving: "#3ddc84",
  Hintergrund: "#8a8aa0",
};

function summe(werte: Record<string, number>) {
  return Object.values(werte).reduce((a, b) => a + (b || 0), 0);
}

export function Charaktererstellung({
  campaignId,
  personId,
  name,
  onFertig,
}: {
  campaignId: string;
  personId: string;
  name: string;
  onFertig: () => void;
}) {
  const [regeln, setRegeln] = useState<Erstellungsregeln | null>(null);
  const [katalog, setKatalog] = useState<TraitDef[]>([]);
  const [schritt, setSchritt] = useState(0);
  const [fehler, setFehler] = useState<string[]>([]);
  const [sendet, setSendet] = useState(false);

  const [weg, setWeg] = useState("KEINER");
  const [rasse, setRasse] = useState("");
  const [schwerpunkte, setSchwerpunkte] = useState<Record<string, number>>({});
  const [attributPunkte, setAttributPunkte] = useState<Record<string, number>>({});
  const [paket, setPaket] = useState("");
  const [fertigkeitPunkte, setFertigkeitPunkte] = useState<Record<string, number>>({});
  const [hintergrundPunkte, setHintergrundPunkte] = useState<Record<string, number>>({});
  const [freebeePunkte, setFreebeePunkte] = useState<Record<string, number>>({});
  const [freebeeWillenskraft, setFreebeeWillenskraft] = useState(0);
  const [freebeeKredit, setFreebeeKredit] = useState(0);
  const [freebeeEigenkapital, setFreebeeEigenkapital] = useState(0);
  const [konzept, setKonzept] = useState("");
  const [alter, setAlter] = useState("");
  const [ambition, setAmbition] = useState("");
  const [verlangen, setVerlangen] = useState("");
  const [ziel, setZiel] = useState("");

  useEffect(() => {
    Promise.all([bogenApi.regeln(campaignId), traitsApi.getKatalog(campaignId)])
      .then(([r, k]) => {
        setRegeln(r);
        setKatalog(k);
      })
      .catch(() => setFehler(["Die Erstellungsregeln konnten nicht geladen werden."]));
  }, [campaignId]);

  const gewaehlteRasse: Rasse | undefined = regeln?.rassen.find((r) => r.name === rasse);
  const gewaehltesPaket: FertigkeitsPaket | undefined = regeln?.fertigkeitsPakete.find((p) => p.id === paket);

  /** Welche Kategorien dieser Weg mitbringt — bestimmt die Fertigkeitsauswahl. */
  const wegKategorien = useMemo(() => {
    if (weg === "MAGIER") return new Set(["Fertigkeit", "Arete", "Sphäre"]);
    if (weg === "TECHNOMANCER") return new Set(["Fertigkeit", "NeuroWeaving"]);
    return new Set(["Fertigkeit"]);
  }, [weg]);

  const waehlbareFertigkeiten = useMemo(
    () => katalog.filter((t) => wegKategorien.has(t.category)),
    [katalog, wegKategorien],
  );

  /**
   * Worauf sich Freebees setzen lassen: alles, was dieser Charakter haben
   * kann — nicht nur, was schon einen Wert trägt. Vorher standen nur die
   * bereits gewählten Fertigkeiten zur Verfügung, damit war eine neue
   * Fertigkeit per Freebee gar nicht erreichbar.
   */
  const freebeeKandidaten = useMemo(
    () =>
      katalog.filter(
        (t) => t.category.startsWith("Attribut") || wegKategorien.has(t.category) || t.category === "Hintergrund",
      ),
    [katalog, wegKategorien],
  );

  /** Wechselt die Rasse und wirft die daran hängende Verteilung weg. */
  function rasseWaehlen(neu: string) {
    setRasse(neu);
    const r = regeln?.rassen.find((x) => x.name === neu);
    if (!r) return;
    // Kontingente in der Reihenfolge der Spalten vorbelegen — umstellen kann
    // man sie im nächsten Schritt, aber irgendwo muss man anfangen.
    const kategorien = regeln!.attributKategorien.map((k) => k.id);
    setSchwerpunkte(Object.fromEntries(kategorien.map((k, i) => [k, r.freiePunkte[i]])));
    setAttributPunkte({});
    setFreebeePunkte({});
  }

  /** Tauscht ein Kontingent zwischen zwei Spalten. */
  function kontingentSetzen(kategorie: string, wert: number) {
    setSchwerpunkte((alt) => {
      const bisher = alt[kategorie];
      const andere = Object.keys(alt).find((k) => k !== kategorie && alt[k] === wert);
      if (andere === undefined) return { ...alt, [kategorie]: wert };
      return { ...alt, [kategorie]: wert, [andere]: bisher };
    });
    // Die Verteilung passt jetzt womöglich nicht mehr — lieber zurücksetzen,
    // als den Leuten eine stille Überschreitung zu hinterlassen.
    setAttributPunkte({});
  }

  const offeneAttributPunkte = useMemo(() => {
    if (!regeln) return {} as Record<string, number>;
    const offen: Record<string, number> = {};
    for (const kategorie of regeln.attributKategorien) {
      const verteilt = kategorie.attribute.reduce((a, n) => a + (attributPunkte[n] || 0), 0);
      offen[kategorie.id] = (schwerpunkte[kategorie.id] || 0) - verteilt;
    }
    return offen;
  }, [regeln, schwerpunkte, attributPunkte]);

  /** Wieviele Fertigkeiten je Wert noch zu vergeben sind. */
  const offeneFertigkeiten = useMemo(() => {
    const offen: Record<number, number> = {};
    if (!gewaehltesPaket) return offen;
    for (const { wert, anzahl } of gewaehltesPaket.verteilung) offen[wert] = anzahl;
    for (const wert of Object.values(fertigkeitPunkte)) {
      if (wert > 0) offen[wert] = (offen[wert] ?? 0) - 1;
    }
    return offen;
  }, [gewaehltesPaket, fertigkeitPunkte]);

  const kategorieVon = useMemo(
    () => Object.fromEntries(katalog.map((t) => [t.name, t.category])),
    [katalog],
  );

  const freebeesVerbraucht = useMemo(() => {
    if (!regeln) return 0;
    const preise = regeln.freebees.kostenJeKategorie;
    let s = 0;
    for (const [name, punkte] of Object.entries(freebeePunkte)) {
      s += (preise[kategorieVon[name] ?? ""] ?? 0) * Math.max(0, punkte);
    }
    s += regeln.freebees.kostenWillenskraft * freebeeWillenskraft;
    s += regeln.freebees.kostenKredit * freebeeKredit;
    s += regeln.freebees.kostenEigenkapital * freebeeEigenkapital;
    return s;
  }, [regeln, freebeePunkte, kategorieVon, freebeeWillenskraft, freebeeKredit, freebeeEigenkapital]);

  const freebeesFrei = (regeln?.freebees.gesamt ?? 0) - freebeesVerbraucht;

  /** Grundwert eines Wertes vor Freebees — für die Anzeige im Freebee-Schritt. */
  function grundwert(name: string) {
    if (gewaehlteRasse?.startwerte[name] !== undefined) {
      return gewaehlteRasse.startwerte[name] + (attributPunkte[name] || 0);
    }
    return (fertigkeitPunkte[name] || 0) + (hintergrundPunkte[name] || 0);
  }

  /** Ob der aktuelle Schritt abgeschlossen ist — steuert nur den Weiter-Knopf. */
  const schrittFertig = useMemo(() => {
    switch (SCHRITTE[schritt].id) {
      case "weg":
        return true; // "Normal" ist eine gültige Wahl
      case "rasse":
        return Boolean(rasse);
      case "attribute":
        return Object.values(offeneAttributPunkte).every((n) => n === 0);
      case "fertigkeiten":
        return Boolean(paket) && Object.values(offeneFertigkeiten).every((n) => n === 0);
      case "hintergrund":
        return summe(hintergrundPunkte) <= (regeln?.hintergrundPunkteGesamt ?? 5);
      case "freebees":
        return freebeesFrei >= 0;
      default:
        return true;
    }
  }, [schritt, rasse, offeneAttributPunkte, paket, offeneFertigkeiten, hintergrundPunkte, regeln, freebeesFrei]);

  async function abschliessen() {
    setSendet(true);
    setFehler([]);
    const eingabe: ErstellungEingabe = {
      weg,
      rasse,
      schwerpunkte,
      attributPunkte,
      fertigkeitsPaket: paket,
      fertigkeitPunkte,
      hintergrundPunkte,
      freebeePunkte,
      freebeeWillenskraft,
      freebeeKredit,
      freebeeEigenkapital,
      konzept,
      alter,
      ambition,
      verlangen,
      ziel,
    };
    try {
      await bogenApi.erstellen(campaignId, personId, eingabe);
      onFertig();
    } catch (e) {
      // Der Server schickt seine Regelverstöße als Liste — sie sind
      // aussagekräftiger als alles, was hier stünde.
      const inhalt = (e as { data?: { detail?: { fehler?: string[] } }; message?: string })?.data?.detail?.fehler;
      setFehler(inhalt ?? [(e as Error).message || "Die Erstellung wurde abgelehnt."]);
    } finally {
      setSendet(false);
    }
  }

  if (!regeln) {
    return (
      <div className="er-blatt">
        <p style={{ color: fehler.length ? "var(--signal)" : "var(--text-leise)" }}>
          {fehler[0] ?? "Lade Erstellungsregeln…"}
        </p>
      </div>
    );
  }

  const aktuell = SCHRITTE[schritt];

  return (
    <div className="er-blatt">
      <header className="er-kopf">
        <div>
          <h2 className="er-name">{name}</h2>
          <div className="er-untertitel">Charaktererstellung</div>
        </div>
        <ol className="er-schritte">
          {SCHRITTE.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                className={`er-schritt${i === schritt ? " er-schritt-aktiv" : ""}${i < schritt ? " er-schritt-fertig" : ""}`}
                // Zurückspringen ist immer erlaubt, vorspringen nicht —
                // sonst stünde man in einem Schritt, dessen Grundlage fehlt.
                onClick={() => i <= schritt && setSchritt(i)}
                disabled={i > schritt}
              >
                <span className="er-schritt-zahl">{i + 1}</span>
                <span className="er-schritt-titel">{s.titel}</span>
              </button>
            </li>
          ))}
        </ol>
      </header>

      <div className="er-buehne">
        {aktuell.id === "weg" && (
          <SchrittWeg regeln={regeln} weg={weg} onWaehlen={setWeg} />
        )}

        {aktuell.id === "rasse" && (
          <SchrittRasse regeln={regeln} rasse={rasse} onWaehlen={rasseWaehlen} />
        )}

        {aktuell.id === "attribute" && gewaehlteRasse && (
          <SchrittAttribute
            regeln={regeln}
            rasse={gewaehlteRasse}
            schwerpunkte={schwerpunkte}
            offen={offeneAttributPunkte}
            punkte={attributPunkte}
            onKontingent={kontingentSetzen}
            onPunkte={setAttributPunkte}
          />
        )}

        {aktuell.id === "fertigkeiten" && (
          <SchrittFertigkeiten
            regeln={regeln}
            fertigkeiten={waehlbareFertigkeiten}
            paket={paket}
            onPaket={(p) => {
              setPaket(p);
              setFertigkeitPunkte({});
            }}
            werte={fertigkeitPunkte}
            offen={offeneFertigkeiten}
            onWert={setFertigkeitPunkte}
          />
        )}

        {aktuell.id === "hintergrund" && (
          <SchrittHintergrund
            regeln={regeln}
            werte={hintergrundPunkte}
            onWert={setHintergrundPunkte}
          />
        )}

        {aktuell.id === "freebees" && (
          <SchrittFreebees
            regeln={regeln}
            frei={freebeesFrei}
            punkte={freebeePunkte}
            grundwert={grundwert}
            waehlbar={freebeeKandidaten}
            onPunkte={setFreebeePunkte}
            willenskraft={freebeeWillenskraft}
            onWillenskraft={setFreebeeWillenskraft}
            kredit={freebeeKredit}
            onKredit={setFreebeeKredit}
            eigenkapital={freebeeEigenkapital}
            onEigenkapital={setFreebeeEigenkapital}
          />
        )}

        {aktuell.id === "person" && (
          <SchrittPerson
            campaignId={campaignId}
            felder={{ konzept, alter, ambition, verlangen, ziel }}
            setzen={{ setKonzept, setAlter, setAmbition, setVerlangen, setZiel }}
          />
        )}
      </div>

      {fehler.length > 0 && (
        <ul className="er-fehler">
          {fehler.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}

      <footer className="er-fuss">
        <button type="button" onClick={() => setSchritt((s) => Math.max(0, s - 1))} disabled={schritt === 0}>
          Zurück
        </button>
        <span className="er-fuss-hinweis">
          {aktuell.id === "attribute" &&
            regeln.attributKategorien
              .map((k) => `${k.name}: ${offeneAttributPunkte[k.id] ?? 0}`)
              .join(" · ") + " offen"}
          {aktuell.id === "fertigkeiten" &&
            gewaehltesPaket &&
            (Object.entries(offeneFertigkeiten)
              .filter(([, anzahl]) => anzahl > 0)
              .map(([wert, anzahl]) => `${anzahl}× auf ${wert}`)
              .join(" · ") || "alles vergeben")}
          {aktuell.id === "hintergrund" &&
            `${regeln.hintergrundPunkteGesamt - summe(hintergrundPunkte)} von ${regeln.hintergrundPunkteGesamt} Punkten frei`}
          {aktuell.id === "freebees" && `${freebeesFrei} von ${regeln.freebees.gesamt} Freebees frei`}
        </span>
        {schritt < SCHRITTE.length - 1 ? (
          <button
            type="button"
            className="er-weiter"
            onClick={() => setSchritt((s) => s + 1)}
            disabled={!schrittFertig}
          >
            Weiter
          </button>
        ) : (
          <button type="button" className="er-weiter" onClick={abschliessen} disabled={sendet}>
            {sendet ? "Wird angelegt…" : "Charakter anlegen"}
          </button>
        )}
      </footer>
    </div>
  );
}

// =====================================================================
// Schritte
// =====================================================================

function SchrittWeg({
  regeln,
  weg,
  onWaehlen,
}: {
  regeln: Erstellungsregeln;
  weg: string;
  onWaehlen: (id: string) => void;
}) {
  return (
    <div className="er-karten">
      {regeln.wege.map((w) => (
        <button
          key={w.id}
          type="button"
          className={`er-karte${weg === w.id ? " er-karte-aktiv" : ""}`}
          onClick={() => onWaehlen(w.id)}
        >
          <span className="er-karte-titel">{w.name}</span>
          <span className="er-karte-text">{w.beschreibung}</span>
        </button>
      ))}
    </div>
  );
}

function SchrittRasse({
  regeln,
  rasse,
  onWaehlen,
}: {
  regeln: Erstellungsregeln;
  rasse: string;
  onWaehlen: (name: string) => void;
}) {
  return (
    <div className="er-karten er-karten-schmal">
      {regeln.rassen.map((r) => {
        const mods = Object.entries(r.modifikatoren);
        return (
          <button
            key={r.name}
            type="button"
            className={`er-karte${rasse === r.name ? " er-karte-aktiv" : ""}`}
            onClick={() => onWaehlen(r.name)}
          >
            <span className="er-karte-titel">{r.name}</span>
            <span className="er-karte-text">{r.beschreibung}</span>
            <span className="er-karte-zahlen">
              <span className="er-marke">{r.freiePunkte.join(" / ")} Punkte</span>
              {mods.length === 0 ? (
                <span className="er-marke er-marke-leise">keine Anlagen</span>
              ) : (
                mods.map(([name, wert]) => (
                  <span key={name} className={`er-marke ${wert > 0 ? "er-marke-plus" : "er-marke-minus"}`}>
                    {name} {wert > 0 ? `+${wert}` : wert}
                  </span>
                ))
              )}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function SchrittAttribute({
  regeln,
  rasse,
  schwerpunkte,
  offen,
  punkte,
  onKontingent,
  onPunkte,
}: {
  regeln: Erstellungsregeln;
  rasse: Rasse;
  schwerpunkte: Record<string, number>;
  offen: Record<string, number>;
  punkte: Record<string, number>;
  onKontingent: (kategorie: string, wert: number) => void;
  onPunkte: (werte: Record<string, number>) => void;
}) {
  // Gleiche Zahlen können mehrfach vorkommen (Elf 5/5/3) — dann ist die
  // Auswahl an dieser Stelle ohnehin eindeutig.
  const kontingente = [...new Set(rasse.freiePunkte)];

  return (
    <div>
      <p className="er-hinweis">
        Jeder startet mit einem Punkt je Attribut, verändert durch die Anlagen deiner Rasse.
        Die drei Kontingente <strong>{rasse.freiePunkte.join(" / ")}</strong> verteilst du frei auf die
        Spalten — und darin auf die einzelnen Attribute. Wie weit ein Attribut bei der Erstellung gehen
        darf, zeigt die Länge seiner Punktreihe; sie richtet sich nach deinen Anlagen. Nur Freebees
        dürfen darüber hinaus.
      </p>
      <div className="er-spalten">
        {regeln.attributKategorien.map((kategorie) => (
          <section key={kategorie.id} style={{ "--cb-ton": TON[kategorie.id] } as React.CSSProperties}>
            <h3 className="er-spalte-titel">{kategorie.name}</h3>
            <div className="er-kontingent">
              {kontingente.map((wert) => (
                <button
                  key={wert}
                  type="button"
                  className={`er-kontingent-knopf${schwerpunkte[kategorie.id] === wert ? " er-kontingent-aktiv" : ""}`}
                  onClick={() => onKontingent(kategorie.id, wert)}
                >
                  {wert}
                </button>
              ))}
              <span className="er-kontingent-rest">{offen[kategorie.id] ?? 0} offen</span>
            </div>
            {kategorie.attribute.map((name) => {
              const start = rasse.startwerte[name];
              const wert = start + (punkte[name] || 0);
              return (
                // Name darüber, Punkte darunter linksbündig: nebeneinander
                // stehen die Punktreihen unterschiedlich weit rechts, weil
                // die Namen verschieden lang sind — das sah unruhig aus.
                <div key={name} className="er-wert er-wert-gestapelt">
                  <span className="er-wert-name">{name}</span>
                  <DotPool
                    value={wert}
                    max={rasse.startmaxima[name]}
                    onChange={(neu) => {
                      // Unter den rassenbedingten Startwert geht es nicht.
                      const punkteNeu = Math.max(0, neu - start);
                      const andere = kategorie.attribute
                        .filter((n) => n !== name)
                        .reduce((a, n) => a + (punkte[n] || 0), 0);
                      if (andere + punkteNeu > (schwerpunkte[kategorie.id] || 0)) return;
                      onPunkte({ ...punkte, [name]: punkteNeu });
                    }}
                  />
                </div>
              );
            })}
          </section>
        ))}
      </div>
    </div>
  );
}

function SchrittFertigkeiten({
  regeln,
  fertigkeiten,
  paket,
  onPaket,
  werte,
  offen,
  onWert,
}: {
  regeln: Erstellungsregeln;
  fertigkeiten: TraitDef[];
  paket: string;
  onPaket: (id: string) => void;
  werte: Record<string, number>;
  offen: Record<number, number>;
  onWert: (werte: Record<string, number>) => void;
}) {
  // Die Auswahl selbst steht in einem Fenster: dreissig Fertigkeiten unter
  // die Paketkarten zu hängen zwang zum Scrollen, und die Spalten gerieten
  // durcheinander. Im Fenster ist Scrollen erlaubt (docs/ui-konzept.md), und
  // die Aufteilung ist dieselbe wie auf dem fertigen Blatt.
  const [auswahlOffen, setAuswahlOffen] = useState(false);
  const gewaehlt = regeln.fertigkeitsPakete.find((p) => p.id === paket);
  const hoechster = gewaehlt ? Math.max(...gewaehlt.verteilung.map((v) => v.wert)) : 0;
  const vergeben = Object.values(werte).filter((w) => w > 0).length;

  const gruppen = fertigkeiten.reduce<Record<string, TraitDef[]>>((acc, t) => {
    (acc[t.category] ??= []).push(t);
    return acc;
  }, {});
  const gruppenFolge = ["Fertigkeit", "Arete", "Sphäre", "NeuroWeaving"].filter((k) => gruppen[k]?.length);

  return (
    <div>
      <div className="er-karten er-karten-schmal">
        {regeln.fertigkeitsPakete.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`er-karte${paket === p.id ? " er-karte-aktiv" : ""}`}
            onClick={() => {
              onPaket(p.id);
              setAuswahlOffen(true);
            }}
          >
            <span className="er-karte-titel">{p.name}</span>
            <span className="er-karte-text">{p.beschreibung}</span>
            <span className="er-karte-zahlen">
              {p.verteilung.map((v) => (
                <span key={v.wert} className="er-marke">
                  {v.anzahl}× auf {v.wert}
                </span>
              ))}
            </span>
          </button>
        ))}
      </div>

      {gewaehlt && (
        <>
          <div className="er-offen">
            {gewaehlt.verteilung.map((v) => (
              <span key={v.wert} className={`er-offen-marke${(offen[v.wert] ?? 0) === 0 ? " er-offen-leer" : ""}`}>
                <strong>{offen[v.wert] ?? 0}</strong>× auf {v.wert}
              </span>
            ))}
          </div>
          <p className="er-hinweis">
            {vergeben} von {gewaehlt.anzahl} Fertigkeiten gesetzt.
            {(gruppen.Arete || gruppen.Sphäre || gruppen.NeuroWeaving) &&
              " Arete, Sphären und NeuroWeaving zählen dabei mit."}
          </p>
          <button type="button" className="er-weiter" onClick={() => setAuswahlOffen(true)}>
            Fertigkeiten wählen
          </button>

          <Fenster
            offen={auswahlOffen}
            titel={`Fertigkeiten — ${gewaehlt.name}`}
            unterzeile={
              Object.entries(offen)
                .filter(([, anzahl]) => anzahl > 0)
                .map(([wert, anzahl]) => `${anzahl}× auf ${wert}`)
                .join(" · ") || "alles vergeben"
            }
            kennung="fertigkeitswahl"
            onSchliessen={() => setAuswahlOffen(false)}
          >
            <p className="er-hinweis">
              Ein Wert lässt sich nur vergeben, solange davon noch einer frei ist — nochmal antippen
              nimmt ihn zurück.
            </p>
            {gruppenFolge.map((kategorie) => (
              <section key={kategorie} style={{ "--cb-ton": TON[kategorie] } as React.CSSProperties}>
                <h3 className="er-spalte-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
                <div
                  className="er-spaltenraster"
                  // Spaltenweise füllen wie auf dem Blatt: die ersten zehn
                  // untereinander, dann die nächsten — nicht zeilenweise, sonst
                  // steht dieselbe Fertigkeit hier woanders als dort.
                  style={{ "--er-zeilen": Math.ceil(gruppen[kategorie].length / 3) } as React.CSSProperties}
                >
                  {gruppen[kategorie].map((t) => {
                    const wert = werte[t.name] || 0;
                    return (
                      <div key={t.id} className="er-wert">
                        <span className="er-wert-name">{t.name}</span>
                        <DotPool
                          value={wert}
                          max={hoechster}
                          onChange={(neu) => {
                            const ziel = neu === wert ? 0 : neu;
                            if (ziel > 0 && (offen[ziel] ?? 0) <= 0) return;
                            onWert({ ...werte, [t.name]: ziel });
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
              </section>
            ))}
          </Fenster>
        </>
      )}
    </div>
  );
}

function SchrittHintergrund({
  regeln,
  werte,
  onWert,
}: {
  regeln: Erstellungsregeln;
  werte: Record<string, number>;
  onWert: (werte: Record<string, number>) => void;
}) {
  const vergeben = summe(werte);
  return (
    <div style={{ "--cb-ton": TON.Hintergrund } as React.CSSProperties}>
      <p className="er-hinweis">
        Was dein Charakter mitbringt, das nicht in ihm selbst steckt: Leute, Geld, Ruf, ein Ort.
        Insgesamt {regeln.hintergrundPunkteGesamt} Punkte, höchstens {regeln.hintergrundMax} auf einen.
      </p>
      <div className="er-raster er-raster-breit">
        {regeln.hintergruende.map((h) => {
          const wert = werte[h.name] || 0;
          return (
            <div key={h.name} className="er-hintergrund">
              <div className="er-wert">
                <span className="er-wert-name">{h.name}</span>
                <DotPool
                  value={wert}
                  max={regeln.hintergrundMax}
                  onChange={(neu) => {
                    const ziel = neu === wert ? wert - 1 : neu;
                    if (vergeben - wert + ziel > regeln.hintergrundPunkteGesamt) return;
                    onWert({ ...werte, [h.name]: Math.max(0, ziel) });
                  }}
                />
              </div>
              <p className="er-hintergrund-text">{h.beschreibung}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SchrittFreebees({
  regeln,
  frei,
  punkte,
  waehlbar,
  grundwert,
  onPunkte,
  willenskraft,
  onWillenskraft,
  kredit,
  onKredit,
  eigenkapital,
  onEigenkapital,
}: {
  regeln: Erstellungsregeln;
  frei: number;
  punkte: Record<string, number>;
  /** Alles, was dieser Charakter überhaupt haben kann — mit Obergrenze. */
  waehlbar: TraitDef[];
  grundwert: (name: string) => number;
  onPunkte: (werte: Record<string, number>) => void;
  willenskraft: number;
  onWillenskraft: (n: number) => void;
  kredit: number;
  onKredit: (n: number) => void;
  eigenkapital: number;
  onEigenkapital: (n: number) => void;
}) {
  const preise = regeln.freebees.kostenJeKategorie;

  /** Fertigkeiten und Sphären dürfen nur um einen Punkt steigen (Zeile 40). */
  function obergrenzeZusatz(kategorie: string) {
    return kategorie === "Fertigkeit" || kategorie === "Sphäre" ? regeln.freebees.maxJeFertigkeit : 99;
  }

  const gruppen = waehlbar.reduce<Record<string, TraitDef[]>>((acc, t) => {
    (acc[t.category] ??= []).push(t);
    return acc;
  }, {});
  const folge = [
    ...regeln.attributKategorien.map((k) => k.id),
    "Fertigkeit",
    "Arete",
    "Sphäre",
    "NeuroWeaving",
    "Hintergrund",
  ].filter((k) => gruppen[k]?.length);

  return (
    <div>
      <p className="er-hinweis">
        {regeln.freebees.gesamt} Freebees zum Nachbessern — auf <strong>alles</strong>, nicht nur auf
        das, was schon steht. Die gefüllten Punkte sind der aktuelle Wert, die Reihe endet am Maximum
        des Wertes: darüber geht es auch mit Freebees nicht. Über das Startmaximum deiner Rasse
        allerdings schon. Ein Attributpunkt kostet 5, eine Fertigkeit 2 (und nur einen Punkt),
        ein Hintergrund 1. Geld gibt es als Kredit (billiger, muss aber zurück) oder als Eigenkapital.
      </p>

      {folge.map((kategorie) => (
        <section key={kategorie} style={{ "--cb-ton": TON[kategorie] } as React.CSSProperties}>
          <h3 className="er-spalte-titel">
            {KATEGORIE_TITEL[kategorie] ?? kategorie} · {preise[kategorie] ?? 0} je Punkt
          </h3>
          <div className="er-raster">
            {gruppen[kategorie].map((t) => {
              const basis = grundwert(t.name);
              const zusatz = punkte[t.name] || 0;
              const preis = preise[kategorie] ?? 0;
              return (
                <div key={t.id} className="er-wert er-wert-gestapelt">
                  <span className="er-wert-name">
                    {t.name}
                    {zusatz > 0 && <em className="er-freebee-plus">+{zusatz}</em>}
                  </span>
                  <DotPool
                    value={basis + zusatz}
                    max={t.defaultMax}
                    onChange={(ziel) => {
                      // Unter den bereits verteilten Grundwert geht es nicht —
                      // das wäre eine Änderung an einem früheren Schritt.
                      const neuerZusatz = Math.max(0, ziel - basis);
                      if (neuerZusatz > obergrenzeZusatz(kategorie)) return;
                      // Was schon gekauft ist, gibt der Preis wieder her.
                      if ((neuerZusatz - zusatz) * preis > frei) return;
                      onPunkte({ ...punkte, [t.name]: neuerZusatz });
                    }}
                  />
                </div>
              );
            })}
          </div>
        </section>
      ))}

      <section>
        <h3 className="er-spalte-titel">Sonstiges</h3>
        <div className="er-raster">
          <ZaehlerZeile
            name="Willenskraft"
            zusatz={`${regeln.freebees.kostenWillenskraft} je Punkt`}
            wert={willenskraft}
            preis={regeln.freebees.kostenWillenskraft}
            frei={frei}
            onWert={onWillenskraft}
          />
          <ZaehlerZeile
            name="Kredit"
            zusatz={`${regeln.freebees.kostenKredit} je ${regeln.freebees.kapitalJeFreebee.toLocaleString("de-AT")}¥`}
            wert={kredit}
            preis={regeln.freebees.kostenKredit}
            frei={frei}
            onWert={onKredit}
          />
          <ZaehlerZeile
            name="Eigenkapital"
            zusatz={`${regeln.freebees.kostenEigenkapital} je ${regeln.freebees.kapitalJeFreebee.toLocaleString("de-AT")}¥`}
            wert={eigenkapital}
            preis={regeln.freebees.kostenEigenkapital}
            frei={frei}
            onWert={onEigenkapital}
          />
        </div>
      </section>
    </div>
  );
}

function ZaehlerZeile({
  name,
  zusatz,
  wert,
  preis,
  frei,
  onWert,
}: {
  name: string;
  zusatz: string;
  wert: number;
  preis: number;
  frei: number;
  onWert: (n: number) => void;
}) {
  return (
    <div className="er-wert er-wert-freebee">
      <span className="er-wert-name">
        {name}
        <em className="er-wert-zusatz">{zusatz}</em>
      </span>
      <span className="er-freebee-wert">{wert}</span>
      <span className="er-freebee-knoepfe">
        <button type="button" onClick={() => onWert(Math.max(0, wert - 1))} disabled={wert === 0}>
          −
        </button>
        <button type="button" onClick={() => onWert(wert + 1)} disabled={preis > frei}>
          +
        </button>
      </span>
    </div>
  );
}

interface Vorlage {
  name: string;
  text: string;
}

/**
 * Anregungen für Ambition und Verlangen.
 *
 * Die Texte liegen **nicht im Code**, sondern in einer lokalen Datei neben dem
 * Server: sie stammen aus dem Magus-Regelwerk und sollen das Gerät nicht
 * verlassen, bevor sie auf NeotopiA umgeschrieben sind. Fehlt die Datei,
 * kommt eine leere Liste — dann erscheint der Knopf gar nicht erst.
 */
function VorschlagKnopf({
  campaignId,
  titel,
  onWaehlen,
}: {
  campaignId: string;
  titel: string;
  onWaehlen: (name: string) => void;
}) {
  const [vorlagen, setVorlagen] = useState<Vorlage[]>([]);
  const [offen, setOffen] = useState(false);

  useEffect(() => {
    api
      .get<Vorlage[]>(`/api/campaigns/${campaignId}/vorlagen/ambition`)
      .then(setVorlagen)
      .catch(() => setVorlagen([]));
  }, [campaignId]);

  if (vorlagen.length === 0) return null;

  return (
    <>
      <button type="button" onClick={() => setOffen(true)} title={`Anregungen für ${titel}`}>
        Vorschläge
      </button>
      <Fenster
        offen={offen}
        titel={`Anregungen — ${titel}`}
        unterzeile={`${vorlagen.length} Archetypen; du kannst auch etwas Eigenes schreiben`}
        kennung={`vorlagen:${titel}`}
        onSchliessen={() => setOffen(false)}
      >
        {vorlagen.map((v) => (
          <button
            key={v.name}
            type="button"
            className="er-karte"
            onClick={() => {
              onWaehlen(v.name);
              setOffen(false);
            }}
          >
            <span className="er-karte-titel">{v.name}</span>
            <span className="er-karte-text">{v.text}</span>
          </button>
        ))}
      </Fenster>
    </>
  );
}

function SchrittPerson({
  campaignId,
  felder,
  setzen,
}: {
  campaignId: string;
  felder: { konzept: string; alter: string; ambition: string; verlangen: string; ziel: string };
  setzen: {
    setKonzept: (v: string) => void;
    setAlter: (v: string) => void;
    setAmbition: (v: string) => void;
    setVerlangen: (v: string) => void;
    setZiel: (v: string) => void;
  };
}) {
  return (
    <div className="er-person">
      <p className="er-hinweis">
        Der Teil, den keine Zahl abbildet. <strong>Ambition</strong> ist, worauf dein Charakter
        hinarbeitet — <strong>Verlangen</strong>, was er sich nimmt, auch wenn es ihm schadet.
        Nichts davon ist Pflicht, und alles lässt sich später ändern.
      </p>
      <label className="er-feld">
        <span>Konzept</span>
        <input
          value={felder.konzept}
          onChange={(e) => setzen.setKonzept(e.target.value)}
          placeholder="Abgehalfterter Konzernanwalt mit Zugang, den er nicht mehr haben dürfte"
        />
      </label>
      <label className="er-feld er-feld-kurz">
        <span>Alter</span>
        <input value={felder.alter} onChange={(e) => setzen.setAlter(e.target.value)} placeholder="34" />
      </label>
      <label className="er-feld">
        <span>Ambition</span>
        <div className="er-feld-mit-knopf">
        <input
          value={felder.ambition}
          onChange={(e) => setzen.setAmbition(e.target.value)}
          placeholder="Woran arbeitet er, auch wenn es Jahre dauert?"
        />
        <VorschlagKnopf campaignId={campaignId} titel="Ambition" onWaehlen={setzen.setAmbition} />
        </div>
      </label>
      <label className="er-feld">
        <span>Verlangen</span>
        <div className="er-feld-mit-knopf">
        <input
          value={felder.verlangen}
          onChange={(e) => setzen.setVerlangen(e.target.value)}
          placeholder="Wonach greift er, obwohl er es besser weiß?"
        />
        <VorschlagKnopf campaignId={campaignId} titel="Verlangen" onWaehlen={setzen.setVerlangen} />
        </div>
      </label>
      <label className="er-feld">
        <span>Ziel</span>
        <input
          value={felder.ziel}
          onChange={(e) => setzen.setZiel(e.target.value)}
          placeholder="Was steht als Nächstes an?"
        />
      </label>
    </div>
  );
}
