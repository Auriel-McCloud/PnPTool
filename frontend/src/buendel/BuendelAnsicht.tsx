/**
 * Bündel-Export (Phase 1): wiederverwendbare Welt-Inhalte dieser Kampagne
 * als ZIP zum Teilen mit anderen Runden (z.B. als GitHub-Download) —
 * backend/app/campaigns/buendel_export.py baut das Paket.
 *
 * **Invertierter Picker (Marks bewusste Entscheidung):** alles ist
 * standardmässig angehakt, die SL hakt die wenigen Dinge AB, die nicht mit
 * raus sollen — nicht umgekehrt. `ausgeschlossen` hält deshalb nur die
 * Ausnahmen, nicht die Auswahl.
 *
 * Phase 2 (Import/Upload) ist ein eigener, späterer Task — dieser
 * Bildschirm baut nur das Export-Paket.
 */

import { useEffect, useMemo, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { getBaum, type BaumKnoten } from "../wiki/api";
import { rassenApi, type Rasse } from "../rassen/api";
import { achievementsApi, type Achievement } from "../achievements/api";
import { buendelApi, type BuendelImportModus, type BuendelImportResponse } from "./api";
import "./buendel.css";

/** `Person.rasse` ist am Server gesetzt (siehe PersonResponse), aber in der
 * geteilten `Person`-Schnittstelle (entities/api.ts) bisher nicht typisiert —
 * hier lokal ergänzt statt die gemeinsame Schnittstelle für diesen einen
 * Bildschirm zu erweitern. */
type PersonMitRasse = Person & { rasse?: string };

type GruppenKey =
  | "orte"
  | "gegenstaende"
  | "fraktionen"
  | "begleiter"
  | "gewaechse"
  | "npcs"
  | "events"
  | "wiki"
  | "rassen"
  | "achievements";

interface BuendelEintrag {
  id: string;
  name: string;
}

interface Gruppe {
  key: GruppenKey;
  titel: string;
  symbol: string;
  eintraege: BuendelEintrag[];
}

function flacheSeiten(knoten: BaumKnoten[]): BuendelEintrag[] {
  const ergebnis: BuendelEintrag[] = [];
  const rekursiv = (liste: BaumKnoten[]) => {
    for (const k of liste) {
      ergebnis.push({ id: k.id, name: k.titel });
      if (k.kinder?.length) rekursiv(k.kinder);
    }
  };
  rekursiv(knoten);
  return ergebnis;
}

interface Props {
  campaignId: string;
}

type BuendelTab = "exportieren" | "importieren";

export function BuendelAnsicht({ campaignId }: Props) {
  const [tab, setTab] = useState<BuendelTab>("exportieren");
  const [ladend, setLadend] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);

  const [npcs, setNpcs] = useState<PersonMitRasse[]>([]);
  const [begleiter, setBegleiter] = useState<PersonMitRasse[]>([]);
  const [orte, setOrte] = useState<BuendelEintrag[]>([]);
  const [events, setEvents] = useState<BuendelEintrag[]>([]);
  const [fraktionen, setFraktionen] = useState<BuendelEintrag[]>([]);
  const [gewaechse, setGewaechse] = useState<BuendelEintrag[]>([]);
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [wikiSeiten, setWikiSeiten] = useState<BuendelEintrag[]>([]);
  const [rassen, setRassen] = useState<Rasse[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);

  // Nur Ausnahmen, nicht die Auswahl — siehe Modul-Docstring.
  const [ausgeschlossen, setAusgeschlossen] = useState<Set<string>>(new Set());

  const [name, setName] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [exportLaeuft, setExportLaeuft] = useState(false);
  const [exportFehler, setExportFehler] = useState<string | null>(null);
  const [exportErfolg, setExportErfolg] = useState(false);

  useEffect(() => {
    let abgebrochen = false;
    setLadend(true);
    setFehler(null);
    Promise.all([
      entitiesApi.listPersonen(campaignId, { personType: "NPC" }),
      entitiesApi.listOrte(campaignId),
      entitiesApi.listEvents(campaignId),
      entitiesApi.listFraktionen(campaignId),
      entitiesApi.listGewaechse(campaignId),
      itemsApi.listAlle(campaignId),
      getBaum(campaignId),
      rassenApi.verfuegbar(campaignId),
      achievementsApi.katalog(campaignId),
    ])
      .then(([personen, orteDaten, eventsDaten, fraktionenDaten, gewaechseDaten, itemsDaten, baum, rassenDaten, achievementsDaten]) => {
        if (abgebrochen) return;
        setNpcs(personen.filter((p) => !p.istCritter));
        setBegleiter(personen.filter((p) => p.istCritter));
        setOrte(orteDaten.map((o) => ({ id: o.id, name: o.name })));
        setEvents(eventsDaten.map((e) => ({ id: e.id, name: e.title })));
        setFraktionen(fraktionenDaten.map((f) => ({ id: f.id, name: f.name })));
        setGewaechse(gewaechseDaten.map((g) => ({ id: g.id, name: g.name })));
        setGegenstaende(itemsDaten);
        setWikiSeiten(flacheSeiten(baum));
        setRassen(rassenDaten);
        setAchievements(achievementsDaten);
      })
      .catch((e) => {
        if (abgebrochen) return;
        setFehler("Fehler beim Laden der Bündel-Kandidaten");
        console.error(e);
      })
      .finally(() => {
        if (!abgebrochen) setLadend(false);
      });
    return () => {
      abgebrochen = true;
    };
  }, [campaignId]);

  // Wie viele aktuell ausgewählte NPCs diese Rasse per Namenstext nutzen
  // (Person.rasse ist Freitext, keine Kante — siehe Modul-Docstring in
  // buendel_export.py). Rein informativ, ändert den Haken nicht automatisch.
  const rasseAutoNutzer = useMemo(() => {
    const zaehler = new Map<string, number>();
    for (const n of npcs) {
      if (ausgeschlossen.has(n.id)) continue;
      const rasseName = (n.rasse || "").trim();
      if (!rasseName) continue;
      const treffer = rassen.find((r) => r.name === rasseName);
      if (treffer) zaehler.set(treffer.id, (zaehler.get(treffer.id) ?? 0) + 1);
    }
    return zaehler;
  }, [npcs, rassen, ausgeschlossen]);

  const gruppen: Gruppe[] = useMemo(
    () => [
      { key: "orte", titel: "Orte", symbol: "🧭", eintraege: orte },
      { key: "gegenstaende", titel: "Gegenstände", symbol: "🎒", eintraege: gegenstaende.map((g) => ({ id: g.id, name: g.name })) },
      { key: "fraktionen", titel: "Fraktionen", symbol: "⬡", eintraege: fraktionen },
      { key: "begleiter", titel: "Begleiter/Critter", symbol: "❊", eintraege: begleiter.map((p) => ({ id: p.id, name: p.name })) },
      { key: "gewaechse", titel: "Flora/Fauna", symbol: "🌿", eintraege: gewaechse },
      { key: "npcs", titel: "NPCs", symbol: "◌", eintraege: npcs.map((p) => ({ id: p.id, name: p.name })) },
      { key: "events", titel: "Events", symbol: "◆", eintraege: events },
      { key: "wiki", titel: "Wiki-Seiten", symbol: "❋", eintraege: wikiSeiten },
      { key: "rassen", titel: "Rassen", symbol: "🧬", eintraege: rassen.map((r) => ({ id: r.id, name: r.name })) },
      { key: "achievements", titel: "Achievements", symbol: "🏆", eintraege: achievements.map((a) => ({ id: a.id, name: a.name })) },
    ],
    [orte, gegenstaende, fraktionen, begleiter, gewaechse, npcs, events, wikiSeiten, rassen, achievements],
  );

  const gesamtAnzahl = gruppen.reduce((summe, g) => summe + g.eintraege.length, 0);
  const ausgewaehltAnzahl = gesamtAnzahl - ausgeschlossen.size;

  function toggle(id: string) {
    setAusgeschlossen((vorher) => {
      const neu = new Set(vorher);
      if (neu.has(id)) neu.delete(id);
      else neu.add(id);
      return neu;
    });
  }

  function alleInGruppe(gruppe: Gruppe, anhaken: boolean) {
    setAusgeschlossen((vorher) => {
      const neu = new Set(vorher);
      for (const e of gruppe.eintraege) {
        if (anhaken) neu.delete(e.id);
        else neu.add(e.id);
      }
      return neu;
    });
  }

  async function exportieren() {
    if (!name.trim() || exportLaeuft) return;
    setExportLaeuft(true);
    setExportFehler(null);
    setExportErfolg(false);
    try {
      await buendelApi.exportieren(campaignId, {
        name: name.trim(),
        beschreibung: beschreibung.trim(),
        tags: tagsText
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        ausgeschlosseneIds: [...ausgeschlossen],
      });
      setExportErfolg(true);
    } catch (e) {
      setExportFehler(e instanceof Error ? e.message : "Export fehlgeschlagen");
    } finally {
      setExportLaeuft(false);
    }
  }

  if (ladend && tab === "exportieren") return <div className="bu-leer">Lade Bündel-Kandidaten…</div>;
  if (fehler && tab === "exportieren") return <div className="bu-leer bu-fehler">{fehler}</div>;

  return (
    <div className="buendel">
      <div className="bu-tabs">
        <button
          type="button"
          className={tab === "exportieren" ? "bu-tab bu-tab-aktiv" : "bu-tab"}
          onClick={() => setTab("exportieren")}
        >
          ⬇ Exportieren
        </button>
        <button
          type="button"
          className={tab === "importieren" ? "bu-tab bu-tab-aktiv" : "bu-tab"}
          onClick={() => setTab("importieren")}
        >
          ⬆ Importieren
        </button>
      </div>

      {tab === "importieren" ? (
        <BuendelImport campaignId={campaignId} />
      ) : (
        <>
      <header className="bu-header">
        <h2>📦 Bündel exportieren</h2>
        <p className="bu-beschreibung">
          Alles ist vorausgewählt — hake ab, was NICHT mit ins Bündel soll. PCs und
          bereits im Papierkorb liegende Einträge sind nie dabei.
        </p>
        <p className="bu-zaehler">
          {ausgewaehltAnzahl} von {gesamtAnzahl} Einträgen ausgewählt
        </p>
      </header>

      <div className="bu-gruppen">
        {gruppen.map((gruppe) => (
          <details key={gruppe.key} className="bu-gruppe" open={gruppe.eintraege.length > 0}>
            <summary>
              <span className="bu-gruppe-symbol">{gruppe.symbol}</span>
              <span className="bu-gruppe-titel">{gruppe.titel}</span>
              <span className="bu-gruppe-anzahl">
                ({gruppe.eintraege.filter((e) => !ausgeschlossen.has(e.id)).length}/{gruppe.eintraege.length})
              </span>
            </summary>
            {gruppe.eintraege.length === 0 ? (
              <p className="bu-gruppe-leer">Keine Einträge.</p>
            ) : (
              <>
                <div className="bu-gruppe-aktionen">
                  <button type="button" onClick={() => alleInGruppe(gruppe, true)}>
                    Alle
                  </button>
                  <button type="button" onClick={() => alleInGruppe(gruppe, false)}>
                    Keine
                  </button>
                </div>
                <ul className="bu-liste">
                  {gruppe.eintraege.map((e) => {
                    const autoNutzer = gruppe.key === "rassen" ? rasseAutoNutzer.get(e.id) : undefined;
                    return (
                      <li key={e.id} className="bu-eintrag">
                        <label>
                          <input
                            type="checkbox"
                            checked={!ausgeschlossen.has(e.id)}
                            onChange={() => toggle(e.id)}
                          />
                          {e.name || "(ohne Namen)"}
                        </label>
                        {!!autoNutzer && (
                          <span className="bu-auto-badge" title={`Rasse von ${autoNutzer} ausgewählten NPC(s) benutzt`}>
                            automatisch, weil von {autoNutzer} ausgewählten NPCs benutzt
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </details>
        ))}
      </div>

      <form
        className="bu-form"
        onSubmit={(e) => {
          e.preventDefault();
          void exportieren();
        }}
      >
        <h3>Bündel-Metadaten</h3>
        <label className="bu-label">
          Name
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="z.B. Hafenviertel-Starterpaket"
            required
          />
        </label>
        <label className="bu-label">
          Beschreibung
          <textarea
            rows={3}
            value={beschreibung}
            onChange={(e) => setBeschreibung(e.target.value)}
            placeholder="Was steckt drin, für wen ist es gedacht?"
          />
        </label>
        <label className="bu-label">
          Tags (kommagetrennt)
          <input
            type="text"
            value={tagsText}
            onChange={(e) => setTagsText(e.target.value)}
            placeholder="cyberpunk, hafenviertel, starter"
          />
        </label>

        {exportFehler && <p className="bu-fehler">{exportFehler}</p>}
        {exportErfolg && <p className="bu-erfolg">✓ Bündel exportiert — Download sollte gestartet sein.</p>}

        <button type="submit" className="bu-export-btn" disabled={exportLaeuft || !name.trim()}>
          {exportLaeuft ? "Exportiert…" : "⬇ Exportieren"}
        </button>
      </form>
        </>
      )}
    </div>
  );
}

/** Import-Tab (Phase 2): Datei wählen, Modus + Ideenschmiede-Regler setzen,
 * absenden, Ergebnis-Zähler anzeigen. Geht IMMER in `campaignId` — kein
 * Kampagnen-Picker (Marks Entscheidung, siehe Modul-Docstring im Backend). */
function BuendelImport({ campaignId }: { campaignId: string }) {
  const [datei, setDatei] = useState<File | null>(null);
  const [modus, setModus] = useState<BuendelImportModus>("ueberspringen");
  const [ideenschmiede, setIdeenschmiede] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnis, setErgebnis] = useState<BuendelImportResponse | null>(null);

  async function importieren() {
    if (!datei || laeuft) return;
    setLaeuft(true);
    setFehler(null);
    setErgebnis(null);
    try {
      const antwort = await buendelApi.importieren(campaignId, datei, modus, ideenschmiede);
      setErgebnis(antwort);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Import fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  const typNamen: Record<string, string> = {
    Ort: "Orte", Gegenstand: "Gegenstände", Fraktion: "Fraktionen", Person: "Personen/Critter",
    Gewaechs: "Flora/Fauna", Event: "Events", WikiSeite: "Wiki-Seiten", Rasse: "Rassen",
    Achievement: "Achievements",
  };

  return (
    <div className="buendel">
      <header className="bu-header">
        <h2>📥 Bündel importieren</h2>
        <p className="bu-beschreibung">
          Importiert ein Bündel-ZIP in DIESE Kampagne. Bereits vorhandene Einträge
          (gleiche Herkunft, z.B. aus einem früheren Import) werden anhand ihrer
          Herkunfts-Kennung erkannt — was damit passiert, bestimmt der Modus unten.
        </p>
      </header>

      <form
        className="bu-form"
        onSubmit={(e) => {
          e.preventDefault();
          void importieren();
        }}
      >
        <label className="bu-label">
          Bündel-Datei (.zip)
          <input
            type="file"
            accept=".zip"
            onChange={(e) => {
              setDatei(e.target.files?.[0] ?? null);
              setErgebnis(null);
              setFehler(null);
            }}
            required
          />
        </label>

        <fieldset className="bu-fieldset">
          <legend>Bei bereits vorhandenen Einträgen</legend>
          <label className="bu-radio">
            <input
              type="radio"
              name="buendel-modus"
              checked={modus === "ueberspringen"}
              onChange={() => setModus("ueberspringen")}
            />
            Überspringen — nichts anfassen
          </label>
          <label className="bu-radio">
            <input
              type="radio"
              name="buendel-modus"
              checked={modus === "aktualisieren"}
              onChange={() => setModus("aktualisieren")}
            />
            Aktualisieren — mit Bündel-Stand überschreiben (alter Stand wandert in den Papierkorb)
          </label>
        </fieldset>

        <fieldset className="bu-fieldset">
          <legend>Neu angelegte Einträge</legend>
          <label className="bu-radio">
            <input
              type="radio"
              name="buendel-ziel"
              checked={!ideenschmiede}
              onChange={() => setIdeenschmiede(false)}
            />
            Direkt live
          </label>
          <label className="bu-radio">
            <input
              type="radio"
              name="buendel-ziel"
              checked={ideenschmiede}
              onChange={() => setIdeenschmiede(true)}
            />
            Erst in die Ideenschmiede (Entwurf)
          </label>
          <p className="bu-hinweis">
            Gilt nur für Typen mit Ideenschmiede (Orte, Gegenstände, Fraktionen,
            Personen/Critter, Flora/Fauna, Events, Wiki-Seiten). Rassen und
            Achievements kennen keinen Entwurfsstatus und gehen immer direkt live.
          </p>
        </fieldset>

        {fehler && <p className="bu-fehler">{fehler}</p>}

        <button type="submit" className="bu-export-btn" disabled={laeuft || !datei}>
          {laeuft ? "Importiert…" : "⬆ Importieren"}
        </button>
      </form>

      {ergebnis && (
        <div className="bu-ergebnis">
          <h3>Ergebnis: {ergebnis.bundleName || "Bündel"}</h3>
          {ergebnis.herkunftCampaignName && (
            <p className="bu-beschreibung">Herkunft: {ergebnis.herkunftCampaignName}</p>
          )}
          <ul className="bu-ergebnis-zaehler">
            <li><strong>{ergebnis.neu}</strong> neu angelegt</li>
            <li><strong>{ergebnis.aktualisiert}</strong> aktualisiert (alter Stand im Papierkorb)</li>
            <li><strong>{ergebnis.uebersprungen}</strong> übersprungen (unverändert)</li>
          </ul>
          {Object.keys(ergebnis.proTyp).length > 0 && (
            <table className="bu-ergebnis-tabelle">
              <thead>
                <tr>
                  <th>Typ</th>
                  <th>neu</th>
                  <th>aktualisiert</th>
                  <th>übersprungen</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(ergebnis.proTyp).map(([typ, z]) => (
                  <tr key={typ}>
                    <td>{typNamen[typ] ?? typ}</td>
                    <td>{z.neu}</td>
                    <td>{z.aktualisiert}</td>
                    <td>{z.uebersprungen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
