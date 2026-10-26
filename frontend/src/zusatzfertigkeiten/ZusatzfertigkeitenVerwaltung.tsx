import { useEffect, useState, type FormEvent } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { rassenApi, type Rasse } from "../rassen/api";
import { traitsApi, type TraitDef } from "../traits/api";
import { spezialisierungenApi, type SpezialisierungKampagne } from "../spezialisierungen/api";
import {
  zusatzfertigkeitenApi,
  type Zusatzfertigkeit,
  type ZusatzfertigkeitVorschlag,
} from "./api";
import "./zusatzfertigkeiten.css";

/**
 * SL-Verwaltung der Zusatzfertigkeiten dieser Kampagne.
 *
 * Marks Vorgabe (28.09.2026): "im Kampagnen Menü eine einfache Tabelle
 * machen in der man Skills eintragen kann [...] nur einen Namen eine Kurz
 * und Detail Beschreibung hinzufügen können." Kein Freigabe-Schalter wie
 * bei Rassen: jeder Eintrag ist sofort für Spieler dieser Kampagne wählbar.
 *
 * Aufbau: schlichte Tabelle (Name/Kurzbeschreibung), Zeile öffnet
 * Detail-Popup mit Bearbeiten/Löschen, "+ Neu" legt einen leeren Eintrag an,
 * "✨ KI-Vorschläge" öffnet ein Popup mit Kandidaten zum Übernehmen.
 */
export function ZusatzfertigkeitenVerwaltung({ campaignId }: { campaignId: string }) {
  const [liste, setListe] = useState<Zusatzfertigkeit[]>([]);
  const [rassen, setRassen] = useState<Rasse[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [offen, setOffen] = useState<Zusatzfertigkeit | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuName, setNeuName] = useState("");
  const [kiOffen, setKiOffen] = useState(false);
  // Ansicht-Umschalter (22.10.2026, Folge-Feature): zweite Ansicht auf
  // DERSELBEN Seite statt eines neuen Menüpunkts — Mark meinte mit "dem
  // Fertigkeiten-Menü" dieses bestehende "Zusatzfertigkeiten"-Menü (siehe
  // Feature-Bericht). Die bestehende Tabelle/Editor-Logik bleibt unberührt,
  // nur hinter diesem Schalter versteckt, wenn die zweite Ansicht aktiv ist.
  const [ansicht, setAnsicht] = useState<"zusatzfertigkeiten" | "vorschlaege" | "slots">("zusatzfertigkeiten");

  async function neuLaden() {
    const daten = await zusatzfertigkeitenApi.liste(campaignId);
    setListe(daten);
    setOffen((alt) => (alt ? daten.find((z) => z.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaedt(true);
    Promise.all([neuLaden(), rassenApi.verfuegbar(campaignId).then(setRassen).catch(() => setRassen([]))]).finally(
      () => setLaedt(false),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    const neu = await zusatzfertigkeitenApi.anlegen(campaignId, { name: neuName.trim() });
    setNeuName("");
    setAnlegenOffen(false);
    await neuLaden();
    setOffen(neu);
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Zusatzfertigkeiten…</p>;

  return (
    <div className="zf-seite">
      <div className="zf-ansicht-umschalter">
        <button
          type="button"
          className={ansicht === "zusatzfertigkeiten" ? "zf-ansicht-knopf zf-ansicht-knopf-aktiv" : "zf-ansicht-knopf"}
          onClick={() => setAnsicht("zusatzfertigkeiten")}
        >
          Zusatzfertigkeiten
        </button>
        <button
          type="button"
          className={ansicht === "vorschlaege" ? "zf-ansicht-knopf zf-ansicht-knopf-aktiv" : "zf-ansicht-knopf"}
          onClick={() => setAnsicht("vorschlaege")}
        >
          Spezialisierungs-Vorschläge
        </button>
        <button
          type="button"
          className={ansicht === "slots" ? "zf-ansicht-knopf zf-ansicht-knopf-aktiv" : "zf-ansicht-knopf"}
          onClick={() => setAnsicht("slots")}
        >
          Vergebene Slots
        </button>
      </div>

      {ansicht === "vorschlaege" && <SpezialisierungsVorschlaegeVerwaltung campaignId={campaignId} />}
      {ansicht === "slots" && <SpezialisierungsSlotsVerwaltung campaignId={campaignId} />}

      {ansicht === "zusatzfertigkeiten" && (
        <>
          <div className="zf-kopf">
            <button type="button" onClick={() => setAnlegenOffen(true)}>
              + Neu
            </button>
            <button type="button" className="zf-ki-btn" onClick={() => setKiOffen(true)}>
              ✨ KI-Vorschläge
            </button>
            <span className="zf-anzahl">{liste.length} in dieser Kampagne</span>
          </div>

          {liste.length === 0 && (
            <p className="zf-leer">
              Noch keine Zusatzfertigkeiten in dieser Kampagne. Sie stehen sofort allen Spielern zur Wahl,
              sobald sie hier eingetragen sind.
            </p>
          )}

          {liste.length > 0 && (
            <table className="zf-tabelle">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Kurzbeschreibung</th>
                  <th>Rasse</th>
                  <th>Drohnen/Fahrzeuge</th>
                </tr>
              </thead>
              <tbody>
                {liste.map((z) => (
                  <tr key={z.id} onClick={() => setOffen(z)} className="zf-zeile">
                    <td className="zf-zeile-name">{z.name}</td>
                    <td className="zf-zeile-kurz">{z.kurzbeschreibung || <em>—</em>}</td>
                    <td className="zf-zeile-kurz">{z.nurFuerRasse || <em>alle</em>}</td>
                    <td className="zf-zeile-kurz">{z.fuerDrohnenFreigegeben ? "✓" : <em>—</em>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <Fenster
            offen={anlegenOffen}
            titel="Neue Zusatzfertigkeit"
            unterzeile="Erst anlegen, dann Beschreibung ausarbeiten"
            kennung="zusatzfertigkeit-neu"
            onSchliessen={() => {
              setAnlegenOffen(false);
              setNeuName("");
            }}
          >
            <form onSubmit={anlegen} className="zf-neu-form">
              <input
                type="text"
                placeholder="Name der Zusatzfertigkeit"
                value={neuName}
                onChange={(e) => setNeuName(e.target.value)}
                required
                autoFocus
              />
              <button type="submit">Anlegen und bearbeiten</button>
            </form>
          </Fenster>

          {offen && (
            <ZusatzfertigkeitEditor
              campaignId={campaignId}
              eintrag={offen}
              rassen={rassen}
              onSchliessen={() => setOffen(null)}
              onGeaendert={neuLaden}
            />
          )}

          <KiVorschlaegePopup
            campaignId={campaignId}
            offen={kiOffen}
            onSchliessen={() => setKiOffen(false)}
            onUebernommen={neuLaden}
          />
        </>
      )}
    </div>
  );
}

/**
 * Bearbeiten-Popup: Textfelder speichern per `onBlur` (Projektkonvention,
 * wie beim Rassen-Editor), kein separater Speichern-Knopf für Name/Kurz —
 * die Detailbeschreibung ist ein längeres Feld, bekommt aber denselben
 * onBlur statt eines eigenen Autosave-Hooks (kein Rich-Text-Editor hier).
 */
function ZusatzfertigkeitEditor({
  campaignId,
  eintrag,
  rassen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  eintrag: Zusatzfertigkeit;
  rassen: Rasse[];
  onSchliessen: () => void;
  onGeaendert: () => Promise<void>;
}) {
  const [name, setName] = useState(eintrag.name);
  const [kurz, setKurz] = useState(eintrag.kurzbeschreibung);
  const [detail, setDetail] = useState(eintrag.detailbeschreibung);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  useEffect(() => {
    setName(eintrag.name);
    setKurz(eintrag.kurzbeschreibung);
    setDetail(eintrag.detailbeschreibung);
  }, [eintrag.id]);

  async function nameSpeichern() {
    const wert = name.trim();
    if (!wert) {
      // Leerer Name macht den Eintrag in der Tabelle unauffindbar — wie bei
      // Ort/Fraktion/Event zurücksetzen statt speichern.
      setName(eintrag.name);
      return;
    }
    if (wert === eintrag.name) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { name: wert });
    await onGeaendert();
  }

  async function kurzSpeichern() {
    if (kurz === eintrag.kurzbeschreibung) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { kurzbeschreibung: kurz });
    await onGeaendert();
  }

  async function detailSpeichern() {
    if (detail === eintrag.detailbeschreibung) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { detailbeschreibung: detail });
    await onGeaendert();
  }

  async function rasseSpeichern(wert: string) {
    if (wert === eintrag.nurFuerRasse) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { nurFuerRasse: wert });
    await onGeaendert();
  }

  async function drohnenFreigabeSpeichern(wert: boolean) {
    if (wert === eintrag.fuerDrohnenFreigegeben) return;
    await zusatzfertigkeitenApi.aendern(campaignId, eintrag.id, { fuerDrohnenFreigegeben: wert });
    await onGeaendert();
  }

  async function loeschen() {
    await zusatzfertigkeitenApi.loeschen(campaignId, eintrag.id);
    setLoeschenOffen(false);
    onSchliessen();
    await onGeaendert();
  }

  return (
    <>
      <Fenster
        offen
        titel={eintrag.name}
        unterzeile="Zusatzfertigkeit bearbeiten"
        kennung={`zusatzfertigkeit:${eintrag.id}`}
        onSchliessen={onSchliessen}
      >
        <div className="zf-editor">
          <label className="zf-feld">
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} onBlur={nameSpeichern} />
          </label>

          <label className="zf-feld">
            Kurzbeschreibung
            <textarea
              value={kurz}
              rows={2}
              placeholder="Ein Satz, der die Fertigkeit fassbar macht — erscheint in der Auswahlliste."
              onChange={(e) => setKurz(e.target.value)}
              onBlur={kurzSpeichern}
            />
          </label>

          <label className="zf-feld">
            Detailbeschreibung
            <textarea
              value={detail}
              rows={6}
              placeholder="Ein Absatz — was die Fertigkeit umfasst, wer sie trägt, wofür sie im Spiel nützlich ist."
              onChange={(e) => setDetail(e.target.value)}
              onBlur={detailSpeichern}
            />
          </label>

          <label className="zf-feld">
            Nur für Rasse (10.10.2026, Vaet-Transformation)
            <select value={eintrag.nurFuerRasse} onChange={(e) => void rasseSpeichern(e.target.value)}>
              <option value="">alle Rassen</option>
              {rassen.map((r) => (
                <option key={r.id} value={r.name}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <p className="zf-hinweis">
            Leer = jeder kann sie wählen. Gesetzt = nur Charaktere dieser Rasse sehen/wählen sie in der
            Erstellung und im LevelUp.
          </p>

          <label className="zf-feld" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={eintrag.fuerDrohnenFreigegeben}
              onChange={(e) => void drohnenFreigabeSpeichern(e.target.checked)}
            />
            Für Drohnen/Fahrzeuge freigeben
          </label>
          <p className="zf-hinweis">
            Aus (Standard) = taucht beim Drohnen-/Fahrzeug-Umbau nicht auf — unabhängig von „Nur für Rasse“
            oben, eine Drohne hat keine Rasse. Mark, 26.10.2026: rassengebundene Zusatzfertigkeiten wie
            „Mimikry“ (nur Vael) ergeben für eine Maschine keinen Sinn, deshalb muss jede dafür passende
            Zusatzfertigkeit (z.B. „Fliegen“) hier einzeln freigeschaltet werden.
          </p>

          <div className="zf-aktionen">
            <button type="button" onClick={() => setLoeschenOffen(true)} className="zf-loeschen">
              🗑 Aus dem Katalog entfernen
            </button>
          </div>
        </div>
      </Fenster>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${eintrag.name} entfernen?`}
          text="Personen, die diese Zusatzfertigkeit bereits gewählt haben, verlieren sie dabei ebenfalls — anders als bei Rassen gibt es hier keinen reinen Textrest auf dem Charakterbogen."
          jaText="Entfernen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}

/**
 * KI-Vorschläge (Marks Wunsch: "Mit einem KI Generierungs Button für
 * Vorschläge"). Zweistufig wie beim Händler-Sortiment: Liste ansehen,
 * jeder Vorschlag einzeln übernehmen (bewusst kein Sammel-Übernehmen) —
 * vor dem Übernehmen editierbar.
 */
function KiVorschlaegePopup({
  campaignId,
  offen,
  onSchliessen,
  onUebernommen,
}: {
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
  onUebernommen: () => Promise<void>;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [vorschlaege, setVorschlaege] = useState<ZusatzfertigkeitVorschlag[]>([]);
  const [uebernommen, setUebernommen] = useState<Set<number>>(new Set());

  async function generieren() {
    setLaedt(true);
    setFehler(null);
    setUebernommen(new Set());
    try {
      const antwort = await zusatzfertigkeitenApi.kiVorschlaege(campaignId, 5);
      setVorschlaege(antwort.vorschlaege);
      if (antwort.vorschlaege.length === 0) {
        setFehler("Die KI hat keine neuen Vorschläge geliefert.");
      }
    } catch (e) {
      setFehler((e as Error).message || "KI-Vorschläge konnten nicht geladen werden.");
    } finally {
      setLaedt(false);
    }
  }

  useEffect(() => {
    if (offen) {
      setVorschlaege([]);
      setFehler(null);
      void generieren();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId]);

  async function uebernehmen(i: number, vorschlag: ZusatzfertigkeitVorschlag) {
    await zusatzfertigkeitenApi.kiVorschlagUebernehmen(campaignId, vorschlag);
    setUebernommen((alt) => new Set(alt).add(i));
    await onUebernommen();
  }

  function editieren(i: number, feld: keyof ZusatzfertigkeitVorschlag, wert: string) {
    setVorschlaege((alt) => alt.map((v, j) => (j === i ? { ...v, [feld]: wert } : v)));
  }

  return (
    <Fenster
      offen={offen}
      breit
      titel="✨ KI-Vorschläge für Zusatzfertigkeiten"
      unterzeile="Vor dem Übernehmen editierbar — jeder Vorschlag einzeln."
      kennung="zusatzfertigkeiten-ki"
      onSchliessen={onSchliessen}
    >
      <div className="zf-ki-popup">
        {laedt && <p style={{ color: "var(--text-leise)" }}>Die KI überlegt…</p>}
        {fehler && <p className="zf-ki-fehler">{fehler}</p>}
        {!laedt && vorschlaege.length > 0 && (
          <button type="button" onClick={generieren} className="zf-ki-neu">
            ↻ Neue Vorschläge
          </button>
        )}

        {vorschlaege.map((v, i) => (
          <div key={i} className="zf-ki-vorschlag" data-uebernommen={uebernommen.has(i)}>
            <label className="zf-feld">
              Name
              <input value={v.name} onChange={(e) => editieren(i, "name", e.target.value)} />
            </label>
            <label className="zf-feld">
              Kurzbeschreibung
              <textarea
                rows={2}
                value={v.kurzbeschreibung}
                onChange={(e) => editieren(i, "kurzbeschreibung", e.target.value)}
              />
            </label>
            <label className="zf-feld">
              Detailbeschreibung
              <textarea
                rows={4}
                value={v.detailbeschreibung}
                onChange={(e) => editieren(i, "detailbeschreibung", e.target.value)}
              />
            </label>
            <button
              type="button"
              className="zf-ki-uebernehmen"
              disabled={uebernommen.has(i)}
              onClick={() => uebernehmen(i, v)}
            >
              {uebernommen.has(i) ? "✓ Übernommen" : "In den Katalog übernehmen"}
            </button>
          </div>
        ))}
      </div>
    </Fenster>
  );
}

/**
 * Spezialisierungs-Vorschläge (22.10.2026, Folge-Feature zur
 * Fertigkeiten-Spezialisierung; 23.10.2026 um Sphären erweitert): je
 * Fertigkeit/NeuroWeaving/Sphären-TraitDef eine Liste von Vorschlagstexten
 * pflegen, die ein Spieler beim Benennen eines Spezialisierungs-Slots als
 * anklickbare Chips angeboten bekommt (siehe SpezialisierungVerwaltung in
 * SpezialisierungPopup.tsx — liest exakt dasselbe `trait.vorschlaege`-Feld,
 * eingehängt im Klick-Fenster der Fertigkeit).
 *
 * Bisher kam diese Liste ausschließlich aus TRAIT_VORSCHLAEGE im Backend-
 * Seed (traits/seed.py) — hier die erste GM-Oberfläche dafür. Speichert bei
 * jedem Hinzufügen/Entfernen sofort (dieselbe Konvention wie die
 * onBlur-Speicherung der Zusatzfertigkeit-Textfelder oben in dieser Datei),
 * kein separater Speichern-Knopf.
 *
 * TraitDef ist ruleset-weit, nicht campaign-gebunden — die Liste zeigt
 * deshalb den ganzen Fertigkeiten-Katalog des Regelwerks dieser Kampagne,
 * und eine Änderung gilt für jede Kampagne desselben Regelwerks (siehe
 * Backend-Routen-Docstring traits/routes.py::set_trait_vorschlaege).
 */
function SpezialisierungsVorschlaegeVerwaltung({ campaignId }: { campaignId: string }) {
  const [traits, setTraits] = useState<TraitDef[] | null>(null);
  const [ladeFehler, setLadeFehler] = useState<string | null>(null);
  const [eingabe, setEingabe] = useState<Record<string, string>>({});
  const [speichert, setSpeichert] = useState<string | null>(null);

  useEffect(() => {
    setTraits(null);
    setLadeFehler(null);
    traitsApi
      .getKatalog(campaignId)
      .then((katalog) =>
        setTraits(
          katalog.filter(
            (t) => t.category === "Fertigkeit" || t.category === "NeuroWeaving" || t.category === "Sphäre"
          )
        )
      )
      .catch(() => setLadeFehler("Fertigkeiten konnten nicht geladen werden."));
  }, [campaignId]);

  async function speichern(trait: TraitDef, neueListe: string[]) {
    setSpeichert(trait.id);
    try {
      const aktualisiert = await traitsApi.setVorschlaege(campaignId, trait.id, neueListe);
      setTraits((alt) => (alt ? alt.map((t) => (t.id === trait.id ? aktualisiert : t)) : alt));
    } catch {
      setLadeFehler("Änderung konnte nicht gespeichert werden.");
    } finally {
      setSpeichert(null);
    }
  }

  function hinzufuegen(trait: TraitDef) {
    const wert = (eingabe[trait.id] ?? "").trim();
    if (!wert || trait.vorschlaege.includes(wert)) return;
    setEingabe((alt) => ({ ...alt, [trait.id]: "" }));
    void speichern(trait, [...trait.vorschlaege, wert]);
  }

  function entfernen(trait: TraitDef, wert: string) {
    void speichern(trait, trait.vorschlaege.filter((v) => v !== wert));
  }

  if (ladeFehler && traits === null) return <p className="zf-ki-fehler">{ladeFehler}</p>;
  if (traits === null) return <p style={{ color: "var(--text-leise)" }}>Lade Fertigkeiten…</p>;

  return (
    <div className="zf-vorschlaege-liste">
      <p className="zf-hinweis">
        Vorschlagstexte, die ein Spieler beim Benennen eines Spezialisierungs-Slots (ab Fertigkeitsrating 4)
        als anklickbare Chips angeboten bekommt — zusätzlich zum freien Textfeld. Gilt für alle Kampagnen
        dieses Regelwerks, nicht nur diese.
      </p>
      {ladeFehler && <p className="zf-ki-fehler">{ladeFehler}</p>}

      {traits.map((trait) => (
        <div key={trait.id} className="zf-vorschlaege-eintrag">
          <span className="zf-vorschlaege-name">{trait.name}</span>
          <div className="zf-vorschlaege-chips">
            {trait.vorschlaege.length === 0 && <em className="zf-vorschlaege-leer">keine Vorschläge</em>}
            {trait.vorschlaege.map((v) => (
              <button
                key={v}
                type="button"
                className="zf-vorschlag-chip"
                disabled={speichert === trait.id}
                title="Klicken zum Entfernen"
                onClick={() => entfernen(trait, v)}
              >
                {v} <span aria-hidden="true">✕</span>
              </button>
            ))}
          </div>
          <div className="zf-vorschlag-add">
            <input
              type="text"
              placeholder="Neuer Vorschlag…"
              value={eingabe[trait.id] ?? ""}
              disabled={speichert === trait.id}
              onChange={(e) => setEingabe((alt) => ({ ...alt, [trait.id]: e.target.value }))}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  hinzufuegen(trait);
                }
              }}
            />
            <button type="button" disabled={speichert === trait.id} onClick={() => hinzufuegen(trait)}>
              +
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Vergebene Spezialisierungs-Slots der Kampagne (24.10.2026): die SL kann
 * einen Slot löschen, den ein Punkte-Abzug nicht wieder wegnimmt. Senken
 * des Ratings löscht nie von selbst — dieser Tab ist der ausdrückliche Weg.
 * Leere automatische Slots unter der Schwelle (der typische Vertipper)
 * gehen auch gesammelt. Benannte und gekaufte nur einzeln; gekaufte
 * erstatten die 4 EP.
 */
function SpezialisierungsSlotsVerwaltung({ campaignId }: { campaignId: string }) {
  const [liste, setListe] = useState<SpezialisierungKampagne[] | null>(null);
  const [fehler, setFehler] = useState("");
  const [nurHaengend, setNurHaengend] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [weg, setWeg] = useState<SpezialisierungKampagne | null>(null);
  const [sammelOffen, setSammelOffen] = useState(false);

  async function laden() {
    const daten = await spezialisierungenApi.vonKampagne(campaignId);
    setListe(daten);
  }

  useEffect(() => {
    setListe(null);
    setFehler("");
    laden().catch(() => setFehler("Spezialisierungen konnten nicht geladen werden."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  const sichtbar = (liste ?? []).filter((s) => !nurHaengend || s.unterSchwelle);
  const haengendeLeere = (liste ?? []).filter((s) => s.unterSchwelle && !s.text && s.quelle === "automatisch");

  async function entfernen(slot: SpezialisierungKampagne) {
    setWeg(null);
    setLaeuft(true);
    setFehler("");
    try {
      await spezialisierungenApi.entfernen(campaignId, slot.personId, slot.id);
      await laden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Entfernen fehlgeschlagen.");
    } finally {
      setLaeuft(false);
    }
  }

  async function sammeln() {
    setSammelOffen(false);
    setLaeuft(true);
    setFehler("");
    try {
      await spezialisierungenApi.leereUnterSchwelleEntfernen(campaignId);
      await laden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Aufräumen fehlgeschlagen.");
    } finally {
      setLaeuft(false);
    }
  }

  if (fehler && liste === null) return <p className="zf-ki-fehler">{fehler}</p>;
  if (liste === null) return <p style={{ color: "var(--text-leise)" }}>Lade Spezialisierungen…</p>;

  return (
    <div className="zf-vorschlaege-liste">
      <p className="zf-hinweis">
        Punkte abziehen nimmt einen schon vergebenen Slot nicht wieder weg. Hier kannst du ihn löschen — einzeln,
        oder alle leeren automatischen Slots unter der Schwelle auf einmal. Ein gekaufter Slot gibt die 4 EP zurück.
      </p>
      {fehler && <p className="zf-ki-fehler">{fehler}</p>}
      <div className="zf-kopf">
        <button type="button" disabled={laeuft || haengendeLeere.length === 0} onClick={() => setSammelOffen(true)}>
          {haengendeLeere.length} leere unter Schwelle entfernen
        </button>
        <label className="zf-filter">
          <input type="checkbox" checked={nurHaengend} onChange={(e) => setNurHaengend(e.target.checked)} />
          nur unter Schwelle
        </label>
        <span className="zf-anzahl">{sichtbar.length} Slots</span>
      </div>
      {sichtbar.length === 0 && <p className="zf-leer">Nichts zu entfernen.</p>}
      {sichtbar.length > 0 && (
        <table className="zf-tabelle">
          <thead>
            <tr>
              <th>Charakter</th>
              <th>Fertigkeit</th>
              <th>Rating</th>
              <th>Slot</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sichtbar.map((slot) => (
              <tr key={slot.id} className="zf-slot-zeile">
                <td className="zf-zeile-name">{slot.personName}</td>
                <td>{slot.traitName}</td>
                <td className={slot.unterSchwelle ? "zf-slot-haengt" : undefined}>
                  {slot.rating}
                  {slot.unterSchwelle ? " · unter Schwelle" : ""}
                </td>
                <td className="zf-zeile-kurz">
                  {slot.text || <em>noch unbenannt</em>}
                  {slot.quelle === "gekauft" ? " · gekauft" : ""}
                </td>
                <td>
                  <button type="button" className="sz-entfernen" disabled={laeuft} onClick={() => setWeg(slot)}>
                    Entfernen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {weg && (
        <Bestaetigung
          titel="Spezialisierung entfernen?"
          text={
            (weg.text ? `„${weg.text}“` : "Der leere Slot") +
            ` von ${weg.personName} an ${weg.traitName} verschwindet.` +
            (weg.quelle === "gekauft" ? " Die 4 EP kommen zurück." : "") +
            " Ein neuer automatischer Slot kommt erst wieder, wenn die Fertigkeit die Schwelle erneut überschreitet."
          }
          jaText="Entfernen"
          onJa={() => entfernen(weg)}
          onNein={() => setWeg(null)}
        />
      )}
      {sammelOffen && (
        <Bestaetigung
          titel="Leere Slots unter der Schwelle entfernen?"
          text={`${haengendeLeere.length} unbenannte automatische Slots verschwinden. Benannte und gekaufte bleiben.`}
          jaText="Entfernen"
          onJa={sammeln}
          onNein={() => setSammelOffen(false)}
        />
      )}
    </div>
  );
}
