import { useEffect, useMemo, useState, type FormEvent } from "react";
import { begleiterApi, type Begleiter } from "../begleiter/api";
import { BegleiterBlatt } from "../begleiter/BegleiterKachel";
import { entitiesApi, type Person } from "../entities/api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { getViewAs } from "../api/client";
import { bogenApi } from "../traits/bogenApi";
import { Kampfkarte } from "./Kampfkarte";
import { DeineDrohnenImKampf } from "./DeineDrohnenImKampf";
import { DeineBeschwoerungen } from "./DeineBeschwoerungen";
import { KAMPFARTEN, kampfApi, type Kampf, type Kampfart, type Teilnehmer } from "./api";
import { battlemapApi, type Battlemap } from "../battlemap/api";
import { BattlemapPopup } from "../battlemap/BattlemapPopup";
import { Initiativliste, useKampf } from "./Initiativliste";
import { InitiativeSetzen } from "./InitiativeSetzen";
import { BoosterPopup } from "./BoosterPopup";
import { HotBleibenPopup } from "./HotBleibenPopup";
import "./kampf.css";

/**
 * Kampfmodus für die Spielleitung.
 *
 * Sie führt die Liste, alle anderen sehen sie. Der Knopf ▤ je Zeile öffnet den
 * Bogen des Betreffenden — egal ob Spielercharakter, NPC oder Begleiter; wer
 * einen Kampf leitet, will nachsehen können, ohne die Ansicht zu verlassen.
 *
 * **Initiative wird vorgeschlagen, nicht verordnet**: Geistesschärfe +
 * Geschicklichkeit (Zeile 57) steht beim Hinzufügen im Feld, überschreiben
 * kann man sie jederzeit — Cyberware und Drogen kennt das Werkzeug noch nicht.
 */
export function Kampfmodus({ campaignId }: { campaignId: string }) {
  const { kampf, geladen, neuLaden } = useKampf(campaignId);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [begleiter, setBegleiter] = useState<Begleiter[]>([]);
  const [wer, setWer] = useState("");
  const [name, setName] = useState("");
  const [initiative, setInitiative] = useState(0);
  const [kampfart, setKampfart] = useState<Kampfart>("NAHKAMPF");
  const [bogenFuer, setBogenFuer] = useState<Teilnehmer | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [initiativeZiel, setInitiativeZiel] = useState<Teilnehmer | null>(null);
  const [suche, setSuche] = useState("");
  const [karten, setKarten] = useState<Battlemap[]>([]);
  const [karteOffen, setKarteOffen] = useState<Battlemap | null>(null);

  useEffect(() => {
    entitiesApi.listPersonen(campaignId).then(setPersonen).catch(() => setPersonen([]));
    begleiterApi.liste(campaignId).then(setBegleiter).catch(() => setBegleiter([]));
    battlemapApi.liste(campaignId).then(setKarten).catch(() => setKarten([]));
  }, [campaignId]);

  /** Auswahl: erst die Charaktere, dann die Begleiter, dann "frei benannt". */
  const auswahl = useMemo(
    () => [
      // Nebenfiguren kämpfen nicht (10.11.2026) — erst zum NPC machen.
      ...personen
        .filter((p) => !p.istNebenfigur)
        .map((p) => ({ wert: `person:${p.id}`, label: `${p.name} (${p.personType})` })),
      ...begleiter.map((b) => ({ wert: `begleiter:${b.id}`, label: `${b.name} (Begleiter)` })),
    ],
    [personen, begleiter],
  );

  /** Mark: die Auswahlliste war unübersichtlich — ein Suchfeld darüber, das
   *  sowohl nach Namen als auch nach "PC"/"NPC"/"Begleiter" filtert, da genau
   *  das schon im Label steht. */
  const gefiltert = useMemo(() => {
    const text = suche.trim().toLowerCase();
    if (!text) return auswahl;
    return auswahl.filter((a) => a.label.toLowerCase().includes(text));
  }, [auswahl, suche]);

  /**
   * Initiative vorschlagen. Nur für Personen — Begleiter haben keine
   * Attribute, ihre Agilität steht auf dem eigenen Blatt und ist etwas anderes.
   */
  async function uebernehmen(schluessel: string) {
    setWer(schluessel);
    const [art, id] = schluessel.split(":");
    if (art === "person") {
      const p = personen.find((x) => x.id === id);
      setName(p?.name ?? "");
      try {
        const bogen = await bogenApi.laden(campaignId, id);
        setInitiative(bogen.uebersicht.initiative);
      } catch {
        setInitiative(0);
      }
    } else if (art === "begleiter") {
      const b = begleiter.find((x) => x.id === id);
      setName(b?.name ?? "");
      setInitiative(b?.agilitaet ?? 0);
    }
  }

  async function hinzufuegen(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || !kampf) return;
    const [art, id] = wer ? wer.split(":") : ["", ""];
    neuLaden(
      await kampfApi.hinzu(campaignId, {
        name: name.trim(),
        initiative,
        kampfart,
        personId: art === "person" ? id : null,
        begleiterId: art === "begleiter" ? id : null,
      }),
    );
    setWer("");
    setName("");
    setInitiative(0);
  }

  async function mit<T>(aktion: Promise<T>) {
    setLaeuft(true);
    try {
      neuLaden((await aktion) as never);
    } finally {
      setLaeuft(false);
    }
  }

  if (!geladen) return <p style={{ color: "var(--text-leise)" }}>Lade Kampf…</p>;

  if (!kampf) {
    return (
      <div className="ka-leer">
        <p>Gerade wird nicht gekämpft.</p>
        <button type="button" onClick={() => mit(kampfApi.beginnen(campaignId))}>
          Kampf beginnen
        </button>
      </div>
    );
  }

  return (
    <div className="ka-seite">
      <header className="ka-kopf">
        <span className="ka-runde">
          Runde <strong>{kampf.runde}</strong>
        </span>
        {/* Marks ausdrueckliche Ausnahme: die NPCs wuerfelt das Tool, die
            Spieler wuerfeln physisch und melden selbst. */}
        <button
          type="button"
          onClick={() => mit(kampfApi.wuerfleNpcs(campaignId))}
          disabled={laeuft}
          title="Initiative aller NPCs und Begleiter automatisch würfeln"
        >
          ⚄ NPC-Initiative
        </button>
        <button type="button" className="ka-weiter" onClick={() => mit(kampfApi.weiter(campaignId))} disabled={laeuft}>
          Nächster ›
        </button>
        <button
          type="button"
          className="ka-ende"
          onClick={() => mit(kampfApi.beenden(campaignId).then(() => null))}
        >
          Kampf beenden
        </button>
        <label className="ka-suche" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          Karte
          <select
            value={kampf.battlemapId ?? ""}
            onChange={(e) => mit(kampfApi.karte(campaignId, e.target.value || null))}
          >
            <option value="">— keine —</option>
            {karten.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
          {kampf.battlemapId && (
            <button
              type="button"
              onClick={() => {
                const k = karten.find((x) => x.id === kampf.battlemapId);
                if (k) setKarteOffen(k);
              }}
            >
              Karte öffnen
            </button>
          )}
        </label>
      </header>

      <Initiativliste
        kampf={kampf}
        onAmZug={(id) => mit(kampfApi.amZug(campaignId, id))}
        onBogen={setBogenFuer}
        onEntfernen={(id) => mit(kampfApi.entfernen(campaignId, id))}
        onErledigt={(t) => mit(kampfApi.aendern(campaignId, t.id, { erledigt: !t.erledigt }))}
        initiativeBearbeitbar={() => true}
        onInitiativeBearbeiten={setInitiativeZiel}
      />

      <form onSubmit={hinzufuegen} className="ka-form">
        <input
          type="text"
          className="ka-suche"
          placeholder="Suchen… (Name, PC oder NPC)"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
          style={{ flex: "1 1 100%", minWidth: 0 }}
        />
        <select value={wer} onChange={(e) => uebernehmen(e.target.value)}>
          <option value="">— frei benannt —</option>
          {gefiltert.map((a) => (
            <option key={a.wert} value={a.wert}>
              {a.label}
            </option>
          ))}
        </select>
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ flex: "1 1 160px", minWidth: 0 }}
        />
        <input
          type="number"
          min={0}
          value={initiative}
          onChange={(e) => setInitiative(Number(e.target.value))}
          title="Initiative — Geistesschärfe + Geschicklichkeit + Cyberware"
          style={{ width: 76 }}
        />
        <select value={kampfart} onChange={(e) => setKampfart(e.target.value as Kampfart)}>
          {KAMPFARTEN.map((a) => (
            <option key={a.wert} value={a.wert}>
              {a.symbol} {a.name}
            </option>
          ))}
        </select>
        <button type="submit">Aufnehmen</button>
      </form>

      <Fenster
        offen={bogenFuer !== null}
        breit
        titel={bogenFuer?.name ?? ""}
        unterzeile="Kampfwerte"
        kennung={`kampfbogen:${bogenFuer?.id ?? ""}`}
        onSchliessen={() => setBogenFuer(null)}
      >
        {bogenFuer?.personId ? (
          <>
            <Kampfkarte
              campaignId={campaignId}
              personId={bogenFuer.personId}
              aenderbar
              zeigeMatrixHot={bogenFuer.personType !== "PC"}
              zeigeInventar
              onInitiativeKlick={() => setInitiativeZiel(bogenFuer)}
            />
            <BogenKampfzubehoer campaignId={campaignId} personId={bogenFuer.personId} kampf={kampf} />
          </>
        ) : (
          <BegleiterImKampf begleiter={begleiter.find((b) => b.id === bogenFuer?.begleiterId)} />
        )}
      </Fenster>

      {initiativeZiel && (
        <InitiativeSetzen
          teilnehmer={initiativeZiel}
          onSchliessen={() => setInitiativeZiel(null)}
          onSpeichern={async (wert) => {
            neuLaden(await kampfApi.meldeInitiative(campaignId, initiativeZiel.id, wert));
          }}
        />
      )}
      {/* Dieselben Fragen wie auf dem Spieler-Tablet, für den NPC der gerade
          dran ist. PCs entscheiden selbst. In der Vorschau nicht — da guckt
          die SL durch fremde Augen. */}
      <NpcZugPopups campaignId={campaignId} kampf={kampf} />
      <BattlemapPopup
        offen={Boolean(karteOffen)}
        karte={karteOffen}
        campaignId={campaignId}
        darfZeichnen
        istGm
        onSchliessen={() => setKarteOffen(null)}
        onKarte={setKarteOffen}
      />
    </div>
  );
}

function NpcZugPopups({ campaignId, kampf }: { campaignId: string; kampf: Kampf }) {
  if (getViewAs()) return null;
  const dran = kampf.teilnehmer.find((t) => t.id === kampf.amZug);
  const npc = dran?.personId && dran.personType !== "PC" ? dran : null;
  return (
    <>
      <BoosterPopup
        key={npc?.personId ?? "kein-npc"}
        campaignId={campaignId}
        kampf={kampf}
        eigenePersonId={npc?.personId ?? null}
        personId={npc?.personId ?? null}
        name={npc?.name}
        onGeaendert={() => { /* der Takt von useKampf holt die Liste nach */ }}
      />
      <HotBleibenPopup
        key={npc?.personId ?? "kein-npc"}
        campaignId={campaignId}
        kampf={kampf}
        personId={npc?.personId ?? null}
        name={npc?.name}
        onGeaendert={() => { /* der Takt von useKampf holt die Liste nach */ }}
      />
    </>
  );
}

function BegleiterImKampf({ begleiter }: { begleiter?: Begleiter }) {
  if (!begleiter) return <p style={{ color: "var(--text-leise)" }}>Kein Bogen hinterlegt.</p>;
  // Dasselbe Blatt wie in der Begleiterverwaltung — nicht nachgebaut.
  return <BegleiterBlatt begleiter={begleiter} />;
}

/**
 * Dasselbe Drohnen-/Beschwörungs-Zubehör wie in der Spieler-Kampfansicht
 * (SpielerAnsicht.tsx), jetzt auch im SL-"Bogen von"-Fenster (Mark,
 * 30.10.2026: "wenn ich auf Bogen von klicke sehe ich viele Dinge nicht, wie
 * z.B. Drohnen oder Beschwörungs-Buttons oder Ki-Tama-Attacken"). Die
 * Ki-Tama-Attacken selbst zeigt schon die Kampfkarte — hier fehlten nur die
 * beiden interaktiven Blöcke darunter, dieselbe Filterlogik wie
 * SpielerAnsicht.tsx::eigeneKiTamas, nur für den betrachteten Charakter statt
 * den eigenen.
 */
function BogenKampfzubehoer({
  campaignId,
  personId,
  kampf,
}: {
  campaignId: string;
  personId: string;
  kampf: Kampf;
}) {
  const [sachen, setSachen] = useState<GegenstandMitBesitzer[]>([]);

  useEffect(() => {
    let weg = false;
    itemsApi
      .listAlle(campaignId)
      .then((liste) => {
        if (!weg) setSachen(liste.filter((g) => g.ownerId === personId));
      })
      .catch(() => {
        if (!weg) setSachen([]);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, personId]);

  const kiTamas = sachen.filter((g) => {
    if (g.typ !== "Ki-Tama" || !g.beschworenerCritterId) return false;
    const traeger = sachen.find((w) => w.id === g.montiertAnId);
    return Boolean(traeger && (traeger.typ === "Waffe" || traeger.istWaffe) && traeger.ablage === "AUSGERUESTET");
  });

  // Kein eigener Nachlade-Ruf nötig — der 3s-Takt von useKampf (im
  // umgebenden Kampfmodus) holt die Liste automatisch nach, genau wie in
  // SpielerAnsicht.tsx.
  const nichtsZuTun = () => {};

  return (
    <>
      <DeineDrohnenImKampf campaignId={campaignId} eigenePersonId={personId} kampf={kampf} onGeaendert={nichtsZuTun} />
      <DeineBeschwoerungen
        campaignId={campaignId}
        eigenePersonId={personId}
        kampf={kampf}
        kiTamas={kiTamas}
        onGeaendert={nichtsZuTun}
      />
    </>
  );
}
