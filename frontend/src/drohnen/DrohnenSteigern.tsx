import { useEffect, useMemo, useState } from "react";
import { DotPool } from "../traits/DotPool";
import { KATEGORIE_TITEL } from "../traits/bogenApi";
import "../traits/levelup.css";
import { drohnenApi, type DrohnenPreisEintrag, type DrohnenSteigerungspreise } from "./api";
import { DrohnenWeitereFertigkeitenPopup } from "./DrohnenWeitereFertigkeitenPopup";
import type { Gegenstand } from "../items/api";

/**
 * Nuyen statt EP: Kauf-Ansicht für Drohnen-/Fahrzeug-Attribute und
 * -Fertigkeiten, Pendant zu `traits/LevelUp.tsx`.
 *
 * **26.10.2026, Mark:** erst auswählen, dann in einem Rutsch bestätigen —
 * genau das Sammel-Muster von `LevelUp.tsx` (`kaeufe`-State, "Speichern"
 * schickt alles sequentiell, "Zurücksetzen" verwirft). Der frühere
 * Sofort-Kauf-Kommentar ("Käufe sind seltener, Race-Condition-Risiko beim
 * geteilten Rigger-Kapital") bleibt ein Rand-Risiko bei zwei gleichzeitig
 * offenen Umbau-Fenstern desselben Riggers — der Server berechnet den Preis
 * bei "Speichern" ohnehin neu und lehnt bei zu wenig Kapital einzeln ab,
 * genau wie LevelUp es für EP schon tut.
 */

// Preisformel gespiegelt aus backend/app/traits/erfahrung.py — "Zusatzfertigkeit"
// läuft serverseitig über dieselbe "Fertigkeit"-Formel (zusatzfertigkeiten/
// routes.py), deshalb hier identische Werte unter eigenem Schlüssel.
const FAKTOR: Record<string, number> = {
  AttributDrohne: 4,
  AttributDrohneAussenhuelle: 8,
  Fertigkeit: 2,
  Zusatzfertigkeit: 2,
};
const NEU_KOSTEN: Record<string, number> = {
  AttributDrohne: 5,
  AttributDrohneAussenhuelle: 5,
  Fertigkeit: 3,
  Zusatzfertigkeit: 3,
};

function berechneKosten(category: string, von: number, nuyenProXp: number): number | null {
  const xp = von <= 0 ? NEU_KOSTEN[category] : (FAKTOR[category] != null ? von * FAKTOR[category] : null);
  return xp == null ? null : xp * nuyenProXp;
}

const REIHENFOLGE = ["AttributDrohne", "AttributDrohneAussenhuelle"];

// Mark, 26.10.2026: diese Fertigkeiten stehen bei einer Drohne/einem
// Fahrzeug standardmäßig oben — alles andere (restlicher Kern-Katalog PLUS
// campaign-eigene Zusatzfertigkeiten) landet hinter "weitere Fertigkeiten",
// für den seltenen Sonderbau. "Fliegen" ist eine Zusatzfertigkeit (siehe
// docs/wiki/concepts/drohnen-fahrzeuge.md) und wird, falls im Katalog
// vorhanden, automatisch mit hochgezogen.
const WICHTIGE_FERTIGKEITEN = ["Schusswaffen", "Nahkampf", "Wahrnehmung", "Sportlichkeit", "Fliegen"];

// Reine Anzeige-Umbenennung NUR am Drohnen-/Fahrzeug-Blatt (Mark: bei
// Menschen bleibt "Sportlichkeit") — gespeichert wird weiterhin der
// Katalogname, siehe traits/drohnen.py::DROHNE_FERTIGKEIT_LABEL.
const LABEL: Record<string, string> = { Sportlichkeit: "Ausweichen" };
const anzeigeName = (name: string) => LABEL[name] ?? name;

export function DrohnenSteigern({
  campaignId,
  drohneId,
  onGeaendert,
}: {
  campaignId: string;
  drohneId: string;
  onGeaendert?: () => void;
}) {
  const [original, setOriginal] = useState<DrohnenSteigerungspreise | null>(null);
  const [maschinenteile, setMaschinenteile] = useState<Gegenstand[]>([]);
  // Lokal gesammelt: traitDefId -> Anzahl vorgemerkter Punkte.
  const [kaeufe, setKaeufe] = useState<Record<string, number>>({});
  // traitDefId -> gewähltes Zahlungs-Maschinenteil (fehlt = mit ¥ bezahlen).
  const [materialWahl, setMaterialWahl] = useState<Record<string, string>>({});
  const [weitereOffen, setWeitereOffen] = useState(false);
  // Welche "weiteren" Fertigkeiten per Popup zu den normalen hochgezogen
  // wurden (26.10.2026, Mark) — rein lokale Anzeige-Auswahl, kein Server-Write.
  const [hervorgehobenIds, setHervorgehobenIds] = useState<Set<string>>(new Set());

  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  function laden() {
    drohnenApi
      .steigerungspreise(campaignId, drohneId)
      .then((daten) => {
        setOriginal(daten);
        setKaeufe({});
        setMaterialWahl({});
      })
      .catch(() => setFehler("Die Preise konnten nicht geladen werden."));
    drohnenApi
      .maschinenteile(campaignId, drohneId)
      .then(setMaschinenteile)
      .catch(() => {});
  }

  useEffect(laden, [campaignId, drohneId]);

  const stand = useMemo(() => {
    if (!original) return null;
    let lokalAusgegeben = 0;
    for (const [traitDefId, anzahl] of Object.entries(kaeufe)) {
      const eintrag = original.werte.find((e) => e.traitDefId === traitDefId);
      if (!eintrag) continue;
      // Mit Material bezahlte Einheiten kosten kein ¥.
      if (materialWahl[traitDefId]) continue;
      for (let i = 0; i < anzahl; i++) {
        const kosten = berechneKosten(eintrag.category, eintrag.aktuell + i, original.nuyenProXp);
        if (kosten != null) lokalAusgegeben += kosten;
      }
    }
    const werte = original.werte.map((e) => {
      const gekauft = kaeufe[e.traitDefId] ?? 0;
      const neuerWert = e.aktuell + gekauft;
      const neueKosten = berechneKosten(e.category, neuerWert, original.nuyenProXp);
      return { ...e, aktuell: neuerWert, kosten: neueKosten ?? e.kosten };
    });
    return { verfuegbar: original.verfuegbar - lokalAusgegeben, werte };
  }, [original, kaeufe, materialWahl]);

  const hatAenderungen = Object.keys(kaeufe).length > 0;

  function kaufen(traitDefId: string) {
    setKaeufe((prev) => ({ ...prev, [traitDefId]: (prev[traitDefId] ?? 0) + 1 }));
  }

  function zuruecksetzen() {
    setKaeufe({});
    setMaterialWahl({});
    setFehler(null);
  }

  async function speichern() {
    if (!hatAenderungen) return;
    setLaeuft(true);
    setFehler(null);
    try {
      for (const [traitDefId, anzahl] of Object.entries(kaeufe)) {
        const materialId = materialWahl[traitDefId] || null;
        for (let i = 0; i < anzahl; i++) {
          await drohnenApi.steigern(campaignId, drohneId, traitDefId, materialId);
        }
      }
      onGeaendert?.();
      laden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Das Speichern hat nicht geklappt.");
      // Teilweise gespeicherte Käufe nicht verschweigen — neu laden zeigt
      // den echten Serverstand, auch wenn nicht alles durchging.
      laden();
    } finally {
      setLaeuft(false);
    }
  }

  if (fehler && !stand) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;
  if (!original || !stand) return <p style={{ color: "var(--text-leise)" }}>Lade Preise…</p>;

  if (!original.riggerId) {
    return (
      <p style={{ color: "var(--text-leise)" }}>
        Ohne gebundenen Rigger kann hier nichts gekauft werden — zuerst unten einen Rigger zuweisen.
      </p>
    );
  }

  const gruppen = stand.werte.reduce<Record<string, DrohnenPreisEintrag[]>>((acc, e) => {
    (acc[e.category] ??= []).push(e);
    return acc;
  }, {});

  const fertigkeitenUndZusatz = [...(gruppen["Fertigkeit"] ?? []), ...(gruppen["Zusatzfertigkeit"] ?? [])];
  const wichtig = fertigkeitenUndZusatz.filter(
    (e) => WICHTIGE_FERTIGKEITEN.includes(e.name) || hervorgehobenIds.has(e.traitDefId),
  );
  const weitere = fertigkeitenUndZusatz.filter(
    (e) => !WICHTIGE_FERTIGKEITEN.includes(e.name) && !hervorgehobenIds.has(e.traitDefId),
  );
  // Separat gefangen (statt stand.verfuegbar in wertKarte zu lesen): TS
  // narrowt den Null-Check oben nicht in verschachtelte Funktionsdeklarationen.
  const verfuegbar = stand.verfuegbar;

  function materialOptionenFuer(eintrag: DrohnenPreisEintrag): Gegenstand[] {
    return maschinenteile.filter((m) => {
      if (!m.istMaschinenteil || m.menge <= 0) return false;
      const qualitaet = m.maschinenteilQualitaet;
      if (eintrag.category === "AttributDrohne" || eintrag.category === "AttributDrohneAussenhuelle") {
        return qualitaet === "hochwertig";
      }
      return qualitaet === "hochwertig" || qualitaet === "normal";
    });
  }

  function wertKarte(e: DrohnenPreisEintrag) {
    const voll = e.aktuell >= e.max;
    const materialOptionen = materialOptionenFuer(e);
    const bezahltMitMaterial = Boolean(materialWahl[e.traitDefId]);
    const leistbar = !voll && (bezahltMitMaterial || e.kosten <= verfuegbar);
    const geaendert = (kaeufe[e.traitDefId] ?? 0) > 0;
    return (
      <div key={e.traitDefId} className="lu-wert-zeile" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <button
          type="button"
          className={`lu-wert${leistbar ? " lu-leistbar" : ""}${voll ? " lu-voll" : ""}${geaendert ? " lu-geaendert" : ""}`}
          onClick={() => leistbar && !laeuft && kaufen(e.traitDefId)}
          disabled={!leistbar || laeuft}
          title={voll ? `${anzeigeName(e.name)} steht auf dem Maximum ${e.max}` : `${e.kosten}¥ für den nächsten Punkt`}
        >
          <span className="lu-name">{anzeigeName(e.name)}</span>
          <DotPool value={e.aktuell} max={e.max} />
          <span className="lu-preis">{voll ? "max" : bezahltMitMaterial ? "Material" : `${e.kosten}¥`}</span>
        </button>
        {!voll && materialOptionen.length > 0 && (
          <div className="lu-zahlart" style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            <button
              type="button"
              className="lu-zahlart-knopf"
              data-aktiv={!bezahltMitMaterial}
              onClick={() =>
                setMaterialWahl((prev) => {
                  const next = { ...prev };
                  delete next[e.traitDefId];
                  return next;
                })
              }
            >
              ¥
            </button>
            {materialOptionen.map((m) => (
              <button
                key={m.id}
                type="button"
                className="lu-zahlart-knopf"
                data-aktiv={materialWahl[e.traitDefId] === m.id}
                title={`${m.maschinenteilQualitaet}, ×${m.menge} vorhanden — verbraucht 1`}
                onClick={() => setMaterialWahl((prev) => ({ ...prev, [e.traitDefId]: m.id }))}
              >
                {m.name}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="lu-blatt">
      <header className="lu-kopf">
        <div className="lu-konto">
          <span className="lu-zahl">{stand.verfuegbar}¥</span>
          <span className="lu-text">
            Kapital des Riggers
            <em>bezahlt wird nicht aus einem eigenen Konto der Drohne</em>
          </span>
        </div>
        <div className="lu-aktionen">
          {hatAenderungen && (
            <>
              <button type="button" className="lu-btn lu-btn-speichern" onClick={speichern} disabled={laeuft}>
                {laeuft ? "Speichert…" : "✓ Speichern"}
              </button>
              <button type="button" className="lu-btn lu-btn-zurueck" onClick={zuruecksetzen} disabled={laeuft}>
                ✗ Zurücksetzen
              </button>
            </>
          )}
        </div>
      </header>

      <p className="lu-hinweis">
        Erst auswählen, dann "Speichern" macht den Umbau endgültig — wie bei EP. Statt ¥ kann, wenn vorhanden,
        auch ein Maschinenteil bezahlen (Gegenstand mit Flag "Maschinenteil" im Besitz des Riggers oder der
        Drohne/des Fahrzeugs selbst).
      </p>
      {maschinenteile.length === 0 && (
        <p className="lu-hinweis" style={{ color: "var(--text-leise)" }}>
          Noch kein Maschinenteil im Besitz: im Gegenstand-Bearbeiten-Popup (Rigger oder diese Drohne/dieses
          Fahrzeug als Besitzer) das Häkchen "Maschinenteil" setzen, dann erscheint hier eine Zahlart-Auswahl.
        </p>
      )}

      {fehler && <p className="lu-fehler">{fehler}</p>}

      <div className="lu-buehne">
        {REIHENFOLGE.filter((k) => gruppen[k]?.length).map((kategorie) => (
          <section key={kategorie}>
            <h3 className="lu-gruppe-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
            <div className="lu-raster">{gruppen[kategorie].map(wertKarte)}</div>
          </section>
        ))}

        {wichtig.length > 0 && (
          <section>
            <h3 className="lu-gruppe-titel">Fertigkeiten</h3>
            <div className="lu-raster">{wichtig.map(wertKarte)}</div>
          </section>
        )}

        {weitere.length > 0 && (
          <section>
            <button type="button" className="lu-btn" onClick={() => setWeitereOffen(true)}>
              + Weitere Fertigkeiten ({weitere.length})
            </button>
          </section>
        )}
      </div>

      <DrohnenWeitereFertigkeitenPopup
        offen={weitereOffen}
        eintraege={[...weitere, ...fertigkeitenUndZusatz.filter((e) => hervorgehobenIds.has(e.traitDefId))]}
        hervorgehoben={hervorgehobenIds}
        onUebernehmen={setHervorgehobenIds}
        onSchliessen={() => setWeitereOffen(false)}
      />
    </div>
  );
}
