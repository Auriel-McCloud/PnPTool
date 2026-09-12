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
import "../regeln/infotipp.css";

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
  AttributKörperlich: "var(--wert-koerperlich)",
  AttributGesellschaftlich: "var(--wert-gesellschaftlich)",
  AttributGeistig: "var(--wert-geistig)",
  Fertigkeit: "var(--wert-fertigkeit)",
  Hexkraft: "var(--wert-hexkraft)",
  Sphäre: "var(--wert-sphaere)",
  NeuroWeavingWert: "var(--wert-neuroweaving)",
  NeuroWeaving: "var(--wert-neuroweaving)",
  Hintergrund: "var(--wert-hintergrund)",
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
    if (weg === "MAGIER") return new Set(["Fertigkeit", "Hexkraft", "Sphäre"]);
    if (weg === "NEUROWEAVER") return new Set(["Fertigkeit", "NeuroWeavingWert", "NeuroWeaving"]);
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
            katalog={katalog}
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
            rasse={gewaehlteRasse}
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
  const gewaehlt = regeln.rassen.find((r) => r.name === rasse);
  return (
    <>
      {regeln.rassen.length === 0 && (
        <p className="er-leer">
          Für diese Kampagne hat die Spielleitung noch keine Rasse freigegeben — ohne sie lässt sich kein
          Charakter bauen.
        </p>
      )}
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
              {r.bildUrl && (
                <span className="er-karte-bild">
                  <img src={r.bildUrl} alt="" />
                </span>
              )}
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

      {gewaehlt && <RassenInfobox rasse={gewaehlt} />}
    </>
  );
}

/**
 * Was die gewählte Rasse für diesen Charakter bedeutet.
 *
 * Die Karten oben vergleichen, die Infobox erklärt: sie steht deshalb erst
 * da, wenn eine Wahl getroffen ist, und wiederholt nicht die Marken der
 * Karte, sondern übersetzt sie in Folgen. Vor allem die Obergrenze — dass
 * ein Troll bei Körperkraft dauerhaft auf 8 statt 6 kommt, steht sonst
 * nirgends, obwohl es die Entscheidung fürs ganze Charakterleben prägt.
 */
function RassenInfobox({ rasse }: { rasse: Rasse }) {
  const mods = Object.entries(rasse.modifikatoren);
  const vorteile = mods.filter(([, w]) => w > 0);
  const nachteile = mods.filter(([, w]) => w < 0);
  return (
    <aside className="er-infobox">
      {rasse.bildUrl && <img className="er-infobox-bild" src={rasse.bildUrl} alt={rasse.name} />}
      <div className="er-infobox-text">
        <h3>{rasse.name}</h3>
        <p>{rasse.beschreibung}</p>
        <p className="er-infobox-punkte">
          Du verteilst <strong>{rasse.freiePunkte.join(" / ")}</strong> Punkte frei auf die drei
          Attributspalten — welches Kontingent auf welche Spalte fällt, entscheidest du.
        </p>
        {vorteile.length > 0 && (
          <p>
            <strong>Anlagen:</strong>{" "}
            {vorteile.map(([name, wert]) => `${name} +${wert} (Grenze ${rasse.startmaxima[name]} bei der Erstellung)`).join(", ")}
          </p>
        )}
        {nachteile.length > 0 && (
          <p>
            <strong>Schwächen:</strong>{" "}
            {nachteile.map(([name, wert]) => `${name} ${wert} (Grenze ${rasse.startmaxima[name]})`).join(", ")}
          </p>
        )}
        {mods.length > 0 && (
          <p className="er-infobox-leise">
            Diese Anlagen gelten ein Leben lang: sie verschieben nicht nur den Start, sondern auch die
            Obergrenze, bis zu der du das Attribut je steigern kannst.
          </p>
        )}
      </div>
    </aside>
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
  katalog,
}: {
  regeln: Erstellungsregeln;
  rasse: Rasse;
  schwerpunkte: Record<string, number>;
  offen: Record<string, number>;
  punkte: Record<string, number>;
  onKontingent: (kategorie: string, wert: number) => void;
  onPunkte: (werte: Record<string, number>) => void;
  /** Für das Lebensmaximum je Attribut (Katalogwert + Rassenmodifikator). */
  katalog: TraitDef[];
}) {
  // Gleiche Zahlen können mehrfach vorkommen (Elf 5/5/3) — dann ist die
  // Auswahl an dieser Stelle ohnehin eindeutig.
  const kontingente = [...new Set(rasse.freiePunkte)];

  /**
   * Wie weit dieses Attribut **je** kommen kann: Katalogmaximum plus
   * Rassenmodifikator — dieselbe Rechnung wie serverseitig in
   * `erstellung.py::lebensmaxima`. Fehlt der Katalogeintrag (sollte nicht
   * vorkommen), bleibt die Erstellungsgrenze das Sichtbare.
   */
  function lebensmaximumVon(name: string) {
    const eintrag = katalog.find((t) => t.name === name);
    if (!eintrag) return rasse.startmaxima[name];
    return eintrag.defaultMax + (rasse.modifikatoren[name] ?? 0);
  }

  return (
    <div>
      <p className="er-hinweis">
        Jeder startet mit einem Punkt je Attribut, verändert durch die Anlagen deiner Rasse.
        Die drei Kontingente <strong>{rasse.freiePunkte.join(" / ")}</strong> verteilst du frei auf die
        Spalten — und darin auf die einzelnen Attribute.
        {" "}
        <strong>Graue Punkte</strong> kommen von deiner Rasse und stehen fest.{" "}
        <strong>Farbige</strong> vergibst du jetzt. <strong>Blasse</strong> zeigen, wie weit der Wert
        später mit Erfahrung noch kommen kann — bei der Erstellung sind sie gesperrt, nur Freebees
        dürfen ein Stück darüber hinaus.
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
              const mod = rasse.modifikatoren[name] ?? 0;
              return (
                // Name darüber, Punkte darunter linksbündig: nebeneinander
                // stehen die Punktreihen unterschiedlich weit rechts, weil
                // die Namen verschieden lang sind — das sah unruhig aus.
                <div key={name} className="er-wert er-wert-gestapelt">
                  <span className="er-wert-name">
                    {name}
                    {/* Ohne diese Marke bleibt unerklärt, warum eine Reihe
                        mehr oder weniger Punkte hat als die daneben — genau
                        das hat Mark beim Bauen von Fred verwirrt. */}
                    {mod !== 0 && (
                      <span
                        className={`er-marke ${mod > 0 ? "er-marke-plus" : "er-marke-minus"}`}
                        title={
                          mod > 0
                            ? `${rasse.name}: +${mod}. Startet höher, und du kannst diesen Wert später bis ${6 + mod} steigern statt nur bis 6.`
                            : `${rasse.name}: ${mod}. Startet niedriger, und mehr als ${6 + mod} wird aus diesem Wert nie.`
                        }
                      >
                        {mod > 0 ? `+${mod}` : mod}
                      </span>
                    )}
                  </span>
                  {/* Die Reihe reicht bis zum **Lebensmaximum**, nicht nur
                      bis zur Erstellungsgrenze: so sieht man, wie weit der
                      Wert je kommen kann, und warum die Reihen verschieden
                      lang sind. Grau = kommt von der Rasse und steht fest,
                      farbig = jetzt vergebbar, blass = erst später mit
                      Erfahrung. */}
                  <DotPool
                    value={wert}
                    max={lebensmaximumVon(name)}
                    fest={start}
                    waehlbarBis={rasse.startmaxima[name]}
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
                  <span className="er-wert-grenzen">
                    bis {rasse.startmaxima[name]} jetzt · {lebensmaximumVon(name)} möglich
                  </span>
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
  const gruppenFolge = ["Fertigkeit", "Hexkraft", "Sphäre", "NeuroWeavingWert", "NeuroWeaving"].filter((k) => gruppen[k]?.length);

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
            {(gruppen.Hexkraft || gruppen.Sphäre || gruppen.NeuroWeaving) &&
              " Hexkraft, Sphären und NeuroWeaving zählen dabei mit."}
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
  rasse,
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
  /**
   * Nötig für die Obergrenze: Freebees dürfen über das **Start**maximum
   * hinaus, aber nicht über das Lebensmaximum der Rasse. Ohne sie stand hier
   * stur der Katalogwert 6 — ein Zwerg konnte Charisma auf 6 kaufen (sein
   * Deckel ist 5) und kam nie auf die 7 bei Widerstandsfähigkeit, die ihm
   * zusteht (Mark, 11.09.2026).
   */
  rasse: Rasse | undefined;
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
    "Hexkraft",
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
          <div
            className="er-spaltenraster"
            style={{ "--er-zeilen": Math.ceil(gruppen[kategorie].length / 3) } as React.CSSProperties}
          >
            {gruppen[kategorie].map((t) => {
              const basis = grundwert(t.name);
              const zusatz = punkte[t.name] || 0;
              const preis = preise[kategorie] ?? 0;
              return (
                <div key={t.id} className="er-wert">
                  <span className="er-wert-name">
                    {t.name}
                    {zusatz > 0 && <em className="er-freebee-plus">+{zusatz}</em>}
                  </span>
                  <DotPool
                    value={basis + zusatz}
                    // Lebensmaximum der Rasse statt des Katalogwerts: der
                    // Zwerg kommt bei Widerstandsfähigkeit auf 7, bei
                    // Charisma aber nur auf 5. Dieselbe Grenze prüft das
                    // Backend (erstellung.py::pruefe), sonst käme hier ein
                    // Wert zustande, den es beim Einreichen ablehnt.
                    max={t.defaultMax + (rasse?.modifikatoren[t.name] ?? 0)}
                    // Was aus Rasse und Attributschritt schon feststeht, ist
                    // hier nicht mehr verhandelbar — Freebees kommen nur
                    // obendrauf. Grau statt anklickbar macht das sichtbar,
                    // statt den Klick still verpuffen zu lassen.
                    fest={basis}
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
  const [erklaert, setErklaert] = useState<Vorlage | null>(null);

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
        {/* Nur der Name in der Zeile — die Beschreibungen sind teils sehr
            lang und machten die Liste unlesbar. Der ganze Text steht hinter
            dem Fragezeichen, in einem Fenster, in dem man scrollen darf. */}
        <div className="er-vorlagen">
          {vorlagen.map((v) => (
            <div key={v.name} className="er-vorlage">
              <button
                type="button"
                className="er-vorlage-name"
                onClick={() => {
                  onWaehlen(v.name);
                  setOffen(false);
                }}
              >
                {v.name}
              </button>
              <button
                type="button"
                className="it-zeichen"
                onClick={() => setErklaert(v)}
                aria-label={`Was bedeutet ${v.name}?`}
                title={`Was bedeutet ${v.name}?`}
              >
                ?
              </button>
            </div>
          ))}
        </div>
      </Fenster>

      {/* Fenster über dem Fenster — dafür hängen sie am Seitenkörper. */}
      <Fenster
        offen={erklaert !== null}
        titel={erklaert?.name ?? ""}
        kennung={`vorlage:${erklaert?.name ?? ""}`}
        onSchliessen={() => setErklaert(null)}
      >
        <p className="it-text">{erklaert?.text}</p>
        {erklaert && (
          <button
            type="button"
            className="er-weiter"
            onClick={() => {
              onWaehlen(erklaert.name);
              setErklaert(null);
              setOffen(false);
            }}
          >
            {erklaert.name} übernehmen
          </button>
        )}
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
