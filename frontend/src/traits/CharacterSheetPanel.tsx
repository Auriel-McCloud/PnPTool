import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import type { Person } from "../entities/api";
import { useAuthFallsVorhanden } from "../auth/AuthContext";
import { VisibilitySelector, type PersonOption } from "../entities/VisibilitySelector";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { useAutosave } from "../shell/autosave";
import { EMPTY_DOC, parseRichText, serializeRichText } from "../richtext/content";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { FormelText, formelKlartext } from "../shell/formelText";
import { ABLAGEN, AUGMENT_TRAEGER_TYPEN, itemsApi, KAMPF_FERTIGKEIT_LABEL, KAMPF_FERTIGKEITEN, SCHADEN_ART_LABEL, SCHADEN_MAX, kampfFertigkeitLesen, schadenArtFuerWaffe, schadenArtLabel, VORLAGE_SENTINEL, type Ablage, type AblageZiel, type Gegenstand, type GegenstandUpdate, type KampfFertigkeit, type SchadenArt } from "../items/api";
import { steckbriefKurz } from "../items/steckbrief";
import { TypKachelAuswahl } from "../items/TypKachelAuswahl";
import { symbolFuerTyp } from "../items/typKatalog";
import { traitsApi, type TraitDef, type TraitRating } from "./api";
import { DotPool } from "./DotPool";
import type { Chromstufe } from "../items/api";
import { StufenBlatt } from "./StufenBlatt";
import { BildBlitz } from "../mitteilungen/BildBlitz";
import { KiBildPopup } from "../ki/KiBildPopup";
import { kiBildGenerieren, kiBildPrompt } from "../ki/api";
import { extrahiereReinenText } from "../richtext/content";
import { ZusammenlegenPopup } from "../items/ZusammenlegenPopup";
import "../entities/pc-detail.css";

type GgAnsicht = "uebersicht" | "beschreibung" | "umbauen" | "notizen" | "besitz";

const CATEGORY_LABELS: Record<string, string> = {
  AttributKörperlich: "Attribute — Körperlich",
  AttributGesellschaftlich: "Attribute — Gesellschaftlich",
  AttributGeistig: "Attribute — Geistig",
  Fertigkeit: "Fertigkeiten",
  NeuroWeaving: "NeuroWeaving",
  Sphäre: "Sphären",
};

interface MergedTrait {
  traitDefId: string;
  name: string;
  category: string;
  rating: number;
  max: number;
  defaultMax: number;
}

function mergeCatalogWithRatings(katalog: TraitDef[], werte: TraitRating[]): MergedTrait[] {
  const byId = new Map(werte.map((w) => [w.traitDefId, w]));
  return katalog.map((t) => {
    const rating = byId.get(t.id);
    return {
      traitDefId: t.id,
      name: t.name,
      category: t.category,
      rating: rating?.rating ?? 0,
      max: rating?.max ?? t.defaultMax,
      defaultMax: t.defaultMax,
    };
  });
}

function groupByCategory(traits: MergedTrait[]): [string, MergedTrait[]][] {
  const groups = new Map<string, MergedTrait[]>();
  for (const t of traits) {
    if (!groups.has(t.category)) groups.set(t.category, []);
    groups.get(t.category)!.push(t);
  }
  return Array.from(groups.entries());
}

function visibilityLabel(item: Gegenstand): string {
  if (item.sichtbarkeit === "GM") return "SL-geheim";
  if (item.sichtbarkeit === "ALLE") return "für alle sichtbar";
  return "nur bestimmte Spieler";
}

// Fahrzeug und Behälter können ihrerseits Gegenstände aufnehmen — sie
// erscheinen dadurch als Ablageziel (siehe items/repository.py). Der
// Typ-Katalog selbst (für die Anlegen-Kacheln) liegt zentral in
// items/typKatalog.ts.
// Steckt im Körper und kostet dauerhaft Willenskraft (Zeilen 112-117).
// Hexware läuft über dieselbe Formel — reine Flavor-Kategorie neben
// Cyberware/Bioware, keine eigene Kostenmechanik (Mark, 02.09.2026).
const CHROM_TYPEN = new Set(["Cyberware", "Bioware", "Hexware"]);
// Drei Plätze je Körperzone (Regelblatt: "je drei Plätze mit Bonus und Verlust").
const SLOTS_PRO_ZONE = [1, 2, 3];
// Bekommen ein eigenes Blatt (Stufe, Widerstand, Angriff, Agilität)
const FAHRZEUG_TYPEN = new Set(["Fahrzeug", "Drohne"]);
function SchadensartFeld({
  wert,
  onChange,
}: {
  wert: SchadenArt;
  onChange: (wert: SchadenArt) => void;
}) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em", marginTop: 6 }}>
      Schadensart
      <select
        value={wert === "schlag" || wert === "schwer" || wert === "aggraviert" ? wert : "schwer"}
        title="Schlag halbiert die Rüstung, Tödlich wird zu Schlag, Schwerheilbar geht voll durch."
        onChange={(e) => onChange(e.target.value as SchadenArt)}
      >
        <option value="schlag">{SCHADEN_ART_LABEL.schlag}</option>
        <option value="schwer">{SCHADEN_ART_LABEL.schwer}</option>
        <option value="aggraviert">{SCHADEN_ART_LABEL.aggraviert}</option>
      </select>
    </label>
  );
}

function KampfFertigkeitFeld({
  wert,
  onChange,
}: {
  wert: KampfFertigkeit;
  onChange: (wert: KampfFertigkeit) => void;
}) {
  return (
    <div style={{ marginTop: 6 }}>
      <span style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Würfelt mit</span>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
        {KAMPF_FERTIGKEITEN.map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => onChange(wert === name ? "" : name)}
            style={{
              borderColor: wert === name ? "var(--neon)" : undefined,
              color: wert === name ? "var(--neon)" : undefined,
            }}
            title={
              name === "Schusswaffen"
                ? "Fernkampf: Geschicklichkeit + Schusswaffen"
                : `Geschicklichkeit + ${name}`
            }
          >
            {KAMPF_FERTIGKEIT_LABEL[name]}
          </button>
        ))}
      </div>
    </div>
  );
}

type Eigenschaft = { key: string; value: string; kiTama?: boolean };

function recordToPairs(r: Record<string, string>): Eigenschaft[] {
  return Object.entries(r).map(([key, value]) => ({ key, value }));
}

function pairsToRecord(pairs: Eigenschaft[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const p of pairs) {
    if (p.key.trim()) out[p.key.trim()] = p.value;
  }
  return out;
}

function EigenschaftenEditor({ pairs, onChange }: { pairs: Eigenschaft[]; onChange: (pairs: Eigenschaft[]) => void }) {
  function update(i: number, patch: Partial<Eigenschaft>) {
    onChange(pairs.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  }
  function remove(i: number) {
    onChange(pairs.filter((_, idx) => idx !== i));
  }
  return (
    <div>
      <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
        Zusatzeigenschaften (z.B. Munition, Schaden, Preis, Level — frei benennbar)
      </label>
      {pairs.map((p, i) => (
        <div key={i} style={{ display: "flex", gap: 6, marginTop: 4 }}>
          <input placeholder="Eigenschaft" value={p.key} onChange={(e) => update(i, { key: e.target.value })} style={{ flex: 1 }} />
          <input placeholder="Wert" value={p.value} onChange={(e) => update(i, { value: e.target.value })} style={{ flex: 1 }} />
          <button type="button" onClick={() => remove(i)}>
            ×
          </button>
        </div>
      ))}
      <button type="button" onClick={() => onChange([...pairs, { key: "", value: "" }])} style={{ marginTop: 4, fontSize: "0.85em" }}>
        + Eigenschaft
      </button>
    </div>
  );
}

export function GegenstandRow({
  campaignId,
  personId,
  item,
  pcOptions,
  alleOptionen,
  onChanged,
  onRemoved,
  onBearbeiten,
  kachel = false,
  nurFenster = false,
  onFensterSchliessen,
}: {
  campaignId: string;
  // Fehlt bei Vorlagen (die haben per Invariante keinen Besitzer).
  personId?: string;
  item: Gegenstand;
  pcOptions: PersonOption[];
  alleOptionen: PersonOption[];
  onChanged: () => void;
  onRemoved: () => void;
  /**
   * Meldet, ob das Bearbeiten-Fenster offen ist. Die Gegenstände-Übersicht
   * lädt dann nicht nach — ein Reload könnte die Kachel von der Seite
   * schieben und das Fenster zumachen.
   */
  onBearbeiten?: (offen: boolean) => void;
  /**
   * Kachel statt Listenzeile. Die kampagnenweite Übersicht stellt Gegenstände
   * als Raster dar, damit sie ohne Scrollen auf eine Seite passen; im
   * Charakterblatt bleibt die kompakte Zeile.
   */
  kachel?: boolean;
  /**
   * Nur das Bearbeiten-Fenster, sofort offen — für die Ideenschmiede, wo
   * der Klick auf den Entwurf schon passiert ist. Schließen ruft
   * `onFensterSchliessen`.
   */
  nurFenster?: boolean;
  onFensterSchliessen?: () => void;
}) {
  const [expanded, setExpanded] = useState(nurFenster);
  const onBearbeitenRef = useRef(onBearbeiten);
  onBearbeitenRef.current = onBearbeiten;
  // Nur beim Öffnen/Schließen melden, nicht bei jedem Render — sonst
  // zählt der Zähler in der Übersicht hoch und runter.
  useEffect(() => {
    if (!expanded) return;
    onBearbeitenRef.current?.(true);
    return () => onBearbeitenRef.current?.(false);
  }, [expanded]);
  // Was wir schon geschrieben haben, auch wenn die Elternliste noch den
  // alten Gegenstand hält. Sonst setzt das nächste Öffnen die Felder aus
  // dem veralteten `item` zurück und der nächste Autosave überschreibt
  // den Server wieder mit dem alten Stand.
  const lokal = useRef<Partial<Gegenstand>>({});
  const geradeGeoeffnet = useRef(false);
  const gespeichertJson = useRef("");
  const [ansicht, setAnsicht] = useState<GgAnsicht>("uebersicht");
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  // Typ ändern (06.10.2026, nur SL): eigenes Popup statt Inline-Dropdown,
  // damit dieselbe große Kachel-Auswahl wie beim Anlegen wiederverwendet
  // werden kann (TypKachelAuswahl) statt einer zweiten Picker-UI.
  const [typAendernOffen, setTypAendernOffen] = useState(false);
  const istGm = useAuthFallsVorhanden()?.me?.role === "GM";
  const [name, setName] = useState(item.name);
  const [typ, setTyp] = useState(item.typ);
  const [preis, setPreis] = useState(item.preis);
  const [kraft, setKraft] = useState(item.kraft);
  const [seltenheit, setSeltenheit] = useState(item.seltenheit);
  const [eigenschaften, setEigenschaften] = useState<Eigenschaft[]>([]);
  const [storyRelevant, setStoryRelevant] = useState(item.storyRelevant);
  const [einzigartig, setEinzigartig] = useState(item.einzigartig);
  const [istVorlageLokal, setIstVorlageLokal] = useState(item.istVorlage);
  const [artFehler, setArtFehler] = useState<string | null>(null);
  const [hatMenge, setHatMenge] = useState(item.hatMenge);
  const [menge, setMenge] = useState(item.menge);
  const [automatischImShop, setAutomatischImShop] = useState(item.automatischImShop);
  const [ablage, setAblage] = useState<Ablage>(item.ablage);
  const [gewicht, setGewicht] = useState(item.gewicht);
  const [kapazitaet, setKapazitaet] = useState(item.kapazitaet);
  const [istBehaelter, setIstBehaelter] = useState(item.istBehaelter);
  const [immerSichtbar, setImmerSichtbar] = useState(item.immerSichtbar);
  const [riggerBonus, setRiggerBonus] = useState(item.riggerBonus);
  const [maxDrohnen, setMaxDrohnen] = useState(item.maxDrohnen);
  const [cyberwall, setCyberwall] = useState(item.cyberwall);
  const [deckBruteForce, setDeckBruteForce] = useState(item.deckBruteForce);
  const [deckSchleichen, setDeckSchleichen] = useState(item.deckSchleichen);
  const [deckDaten, setDeckDaten] = useState(item.deckDaten);
  const [deckKompilieren, setDeckKompilieren] = useState(item.deckKompilieren);
  const [deckElectronicWarfare, setDeckElectronicWarfare] = useState(item.deckElectronicWarfare);
  const [deckMatrixNavigation, setDeckMatrixNavigation] = useState(item.deckMatrixNavigation);
  const [wVerlust, setWVerlust] = useState(item.wVerlust);
  const [koerperzone, setKoerperzone] = useState(item.koerperzone);
  const [slot, setSlot] = useState<number | null>(item.slot);
  const [istWaffe, setIstWaffe] = useState(item.istWaffe);
  const [istNeurolink, setIstNeurolink] = useState(Boolean(item.istNeurolink));
  const [schaden, setSchaden] = useState(item.typ === "Waffe" ? item.schaden || item.kraft : item.schaden);
  const [schadenArt, setSchadenArt] = useState<SchadenArt>(
    item.typ === "Waffe" || item.istWaffe ? schadenArtFuerWaffe(item.schadenArt) : (item.schadenArt ?? ""),
  );
  const [kampfFertigkeit, setKampfFertigkeit] = useState<KampfFertigkeit>(kampfFertigkeitLesen(item.kampfFertigkeit));
  const [initiativeBonus, setInitiativeBonus] = useState(item.initiativeBonus);
  const [zusatzaktionen, setZusatzaktionen] = useState(item.zusatzaktionen);
  const [traitBoni, setTraitBoni] = useState<Eigenschaft[]>([]);
  const [ausruestungsfertigkeiten, setAusruestungsfertigkeiten] = useState<Eigenschaft[]>([]);
  const [traitKatalog, setTraitKatalog] = useState<TraitDef[]>([]);
  const [chromstufen, setChromstufen] = useState<Chromstufe[]>([]);
  const [zonen, setZonen] = useState<string[]>([]);
  // Gewählte Chromstufe (preisJeBonus) für automatische Preisberechnung
  const [gewaehlteChromstufe, setGewaehlteChromstufe] = useState<number | null>(null);
  // Blatt für Drohne/Fahrzeug/Sprite/Geist (Neotopia.xlsx)
  const [stufe, setStufe] = useState(item.stufe);
  const [widerstand, setWiderstand] = useState(item.widerstand);
  const [angriff, setAngriff] = useState(item.angriff);
  const [agilitaet, setAgilitaet] = useState(item.agilitaet);
  // Rüstung: Kästchen + Schadensreduktion (siehe docs/api/ruestung.md). Nur
  // die Ausgangswerte (Max/Reduktion) sind hier editierbar — der aktuelle
  // Beschädigungszustand ändert sich über Treffer in der Kampfkarte, nicht
  // im Bearbeiten-Formular (genau wie die Gesundheit einer Person nicht hier
  // eingetragen wird).
  const [ruestungKaestchenMax, setRuestungKaestchenMax] = useState(item.ruestungKaestchenMax);
  const [ruestungReduktionBasis, setRuestungReduktionBasis] = useState(item.ruestungReduktionBasis);
  // Reparaturmaterial: verbrauchbar an einer Rüstung im Selbst-Reparieren-
  // Popup (siehe RuestungReparatur.tsx). Kein eigener Typ — ein Flag auf
  // jedem beliebigen Gegenstand (Klebeband, Nanopaste, Ersatzteile).
  const [istReparaturmaterial, setIstReparaturmaterial] = useState(item.istReparaturmaterial);
  const [reparaturKapazitaet, setReparaturKapazitaet] = useState(item.reparaturKapazitaet);
  // Maschinenteil (26.10.2026, Material statt Nuyen beim Drohnen-/Fahrzeug-
  // Umbau): dasselbe Flag-Muster wie Reparaturmaterial, gestuft statt mit
  // Kapazitätszahl — siehe traits/drohnen.py::maschinenteil_reicht.
  const [istMaschinenteil, setIstMaschinenteil] = useState(item.istMaschinenteil);
  const [maschinenteilQualitaet, setMaschinenteilQualitaet] = useState(item.maschinenteilQualitaet);
  // Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026, siehe
  // docs/wiki/concepts/augments-ausruestung.md): upgradeSlots nur bei
  // Waffe/Rüstung/Cyberdeck/Riggerkonsole relevant, istAugment/
  // augmentWaffentyp nur wenn DIESER Gegenstand selbst ein Augment ist.
  const [upgradeSlots, setUpgradeSlots] = useState(item.upgradeSlots);
  const [istAugment, setIstAugment] = useState(item.istAugment);
  const [augmentWaffentyp, setAugmentWaffentyp] = useState(item.augmentWaffentyp);
  const [augmentZielTyp, setAugmentZielTyp] = useState(item.augmentZielTyp);
  // Natürliche Rüstung (11.10.2026 Verfeinerung, Rassen-/Kreatur-Feature):
  // spiegelt `verbaut` bei Cyberware — nicht ablegbar für den Spieler (GM
  // kann es im Ausnahmefall), nicht reparierbar, Kästchen-Max kommt serverseitig
  // live aus der Widerstandsfähigkeit der tragenden Person (der Wert oben im
  // Formular bleibt dann nur noch ein Vorlagen-Hinweis, keine Wahrheit mehr).
  const [istNatuerlich, setIstNatuerlich] = useState(item.istNatuerlich);
  const [ablageZiel, setAblageZiel] = useState<string>(item.ablageZielId ?? "");
  const [ziele, setZiele] = useState<AblageZiel[]>([]);
  const [descriptionDoc, setDescriptionDoc] = useState<JSONContent>(EMPTY_DOC);
  const [notesDoc, setNotesDoc] = useState<JSONContent>(EMPTY_DOC);
  const [sichtbarkeit, setSichtbarkeit] = useState(item.sichtbarkeit);
  const [sichtbarFuer, setSichtbarFuer] = useState(item.sichtbarFuer);
  const [uploading, setUploading] = useState(false);
  const [zuweisenZiel, setZuweisenZiel] = useState("");
  const [zuweisenLaeuft, setZuweisenLaeuft] = useState(false);
  const [zuweisenHinweis, setZuweisenHinweis] = useState("");
  const [besitzerZiel, setBesitzerZiel] = useState("");
  const [besitzerLaeuft, setBesitzerLaeuft] = useState(false);
  const [kiBildOffen, setKiBildOffen] = useState(false);
  const [zusammenlegenOffen, setZusammenlegenOffen] = useState(false);

  // Summe aller Boni für Chrom-Preisberechnung:
  // traitBoni (Attribute/Fertigkeiten) + ausruestungsfertigkeiten + schaden + initiativeBonus + zusatzaktionen
  const traitBoniSumme = traitBoni.reduce((sum, b) => sum + (Number(b.value) || 0), 0);
  const ausrFertSumme = ausruestungsfertigkeiten.reduce((sum, b) => sum + (Number(b.value) || 0), 0);
  const waffenSchaden = istWaffe ? schaden : 0;
  // "Jede Runde" (zusatzaktionen === -1) ist kein echter Zählwert, sondern ein
  // Sentinel aus kampf/booster.py — roh addiert würde er den Bonus SENKEN statt
  // erhöhen. Stattdessen zählt hier dieselbe Zahl, die die Ampel in der
  // Kampfsektion schon kennt: wie viele Runden Nutzung, bevor der
  // Überhitzungs-Willenskraftwurf fällig wird (kampf/booster.py::AMPEL_MAX,
  // aktuell 3 — Mark, 12.10.2026: "wie viele Runden man hat, bevor man diesen
  // Willenskraftwurf machen kann"). Ändert sich AMPEL_MAX dort, bitte hier
  // mitziehen.
  const AMPEL_MAX_FUER_KOSTEN = 3;
  const zusatzaktionenBonus = zusatzaktionen === -1 ? AMPEL_MAX_FUER_KOSTEN : Math.max(0, zusatzaktionen);
  // Initiative-Bonus zählt 1:1 mit (Mark, 12.10.2026) — sonst kostet ein reiner
  // Reflex-Booster-artiger Gegenstand (nur Initiative, kein Trait/Ausrüstungs-
  // Bonus, keine Waffe) praktisch nichts, egal welche Qualitätsstufe man wählt.
  const gesamtBonus =
    traitBoniSumme + ausrFertSumme + waffenSchaden + (Number(initiativeBonus) || 0) + zusatzaktionenBonus;

  // Mirror von chrom.py::STUFEN (Teiler je preisJeBonus) — rein lokal
  // berechnet, damit der gespeicherte Willenskraft-Verlust NICHT von der
  // asynchron nachgeladenen Chromstufen-Liste abhängt. Bug bis 12.10.2026:
  // bei schnellen Bonus-Änderungen (z.B. Zahl bei den Zusatzeigenschaften
  // tippen) konnten Server-Antworten in falscher Reihenfolge ankommen und
  // den WK-Verlust auf einem veralteten Stand einfrieren — der Wert schien
  // dann "wirkungslos", obwohl die Formel selbst stimmt.
  const TEILER_JE_PREIS: Record<number, number> = { 500: 0.5, 2000: 1, 5000: 2, 10000: 3, 20000: 4 };

  // Der Preis hängt am Bonus: ändert er sich, stimmen die angebotenen Stufen
  // nicht mehr. Nur nachladen, solange das Formular offen ist.
  useEffect(() => {
    if (!expanded || !CHROM_TYPEN.has(typ)) return;
    const bonus = Math.max(1, gesamtBonus || kraft);
    itemsApi
      .chromstufen(campaignId, bonus)
      .then((d) => {
        setChromstufen(d.stufen);
        setZonen(d.koerperzonen);
      })
      .catch(() => setChromstufen([]));
  }, [expanded, typ, gesamtBonus, kraft, campaignId]);

  // Wenn sich Boni oder die gewählte Stufe ändert, Preis/WK-Verlust neu berechnen.
  // Bewusst OHNE Abhängigkeit von der (async geladenen) `chromstufen`-Liste —
  // direkt aus dem Bonus berechnet, siehe TEILER_JE_PREIS oben.
  useEffect(() => {
    if (!expanded || !CHROM_TYPEN.has(typ) || gewaehlteChromstufe === null) return;
    const teiler = TEILER_JE_PREIS[gewaehlteChromstufe];
    if (!teiler) return;
    const bonus = Math.max(1, gesamtBonus);
    setPreis(bonus * gewaehlteChromstufe);
    setWVerlust(Math.max(1, Math.floor(bonus / teiler)));
    setKraft(bonus);
  }, [traitBoni, ausruestungsfertigkeiten, schaden, istWaffe, gewaehlteChromstufe, gesamtBonus, expanded, typ]);

  // Katalog fürs Trait-Boni-Dropdown — nur laden, wenn das Formular offen
  // ist und Boni überhaupt angezeigt werden können.
  useEffect(() => {
    if (!expanded) return;
    traitsApi.getKatalog(campaignId).then(setTraitKatalog).catch(() => setTraitKatalog([]));
  }, [expanded, campaignId]);

  function openEdit() {
    geradeGeoeffnet.current = true;
    const src = { ...item, ...lokal.current };
    setName(src.name);
    setTyp(src.typ);
    setPreis(src.preis);
    setKraft(src.typ === "Waffe" ? src.schaden || src.kraft : src.kraft);
    setSeltenheit(src.seltenheit);
    setEigenschaften(recordToPairs(src.eigenschaften));
    setStoryRelevant(src.storyRelevant);
    setEinzigartig(src.einzigartig);
    setIstVorlageLokal(src.istVorlage);
    setArtFehler(null);
    setHatMenge(src.hatMenge);
    setMenge(src.menge);
    setAutomatischImShop(src.automatischImShop);
    setAblage(src.ablage);
    setGewicht(src.gewicht);
    setKapazitaet(src.kapazitaet);
    setIstBehaelter(src.istBehaelter);
    setImmerSichtbar(src.immerSichtbar);
    setRiggerBonus(src.riggerBonus);
    setMaxDrohnen(src.maxDrohnen);
    setCyberwall(src.cyberwall);
    setDeckBruteForce(src.deckBruteForce);
    setDeckSchleichen(src.deckSchleichen);
    setDeckDaten(src.deckDaten);
    setDeckKompilieren(src.deckKompilieren);
    setDeckElectronicWarfare(src.deckElectronicWarfare);
    setDeckMatrixNavigation(src.deckMatrixNavigation);
    setWVerlust(src.wVerlust);
    setKoerperzone(src.koerperzone);
    setSlot(src.slot);
    setIstWaffe(src.istWaffe);
    setIstNeurolink(Boolean(src.istNeurolink));
    setSchaden(src.typ === "Waffe" ? src.schaden || src.kraft : src.schaden);
    setSchadenArt(src.typ === "Waffe" || src.istWaffe ? schadenArtFuerWaffe(src.schadenArt) : (src.schadenArt ?? ""));
    setKampfFertigkeit(kampfFertigkeitLesen(src.kampfFertigkeit));
    setInitiativeBonus(src.initiativeBonus);
    setZusatzaktionen(src.zusatzaktionen);
    setTraitBoni(
      Object.entries(src.traitBoni).map(([key, value]) => ({ key, value: String(value) })),
    );
    setAusruestungsfertigkeiten(
      Object.entries(src.ausruestungsfertigkeiten).map(([key, value]) => ({
        key,
        value: String(value),
        kiTama: Boolean(src.kiTamaFertigkeiten?.[key]),
      })),
    );
    setStufe(src.stufe);
    setWiderstand(src.widerstand);
    setAngriff(src.angriff);
    setAgilitaet(src.agilitaet);
    setRuestungKaestchenMax(src.ruestungKaestchenMax);
    setRuestungReduktionBasis(src.ruestungReduktionBasis);
    setIstReparaturmaterial(src.istReparaturmaterial);
    setReparaturKapazitaet(src.reparaturKapazitaet);
    setIstMaschinenteil(src.istMaschinenteil);
    setMaschinenteilQualitaet(src.maschinenteilQualitaet);
    setUpgradeSlots(src.upgradeSlots);
    setIstAugment(src.istAugment);
    setAugmentWaffentyp(src.augmentWaffentyp);
    setAugmentZielTyp(src.augmentZielTyp);
    setIstNatuerlich(src.istNatuerlich);
    setAblageZiel(src.ablageZielId ?? "");
    // Ziele erst beim Öffnen holen — für jede Kachel im Voraus wäre es eine
    // Abfrage pro Gegenstand, nur damit ein Auswahlfeld gefüllt ist.
    itemsApi.ablageziele(campaignId, item.id).then(setZiele).catch(() => setZiele([]));
    // Preisstufen fürs Chrom — erst beim Öffnen, und nur wenn es eines ist.
    if (CHROM_TYPEN.has(src.typ)) {
      itemsApi
        .chromstufen(campaignId, Math.max(1, src.kraft))
        .then((d) => {
          setChromstufen(d.stufen);
          setZonen(d.koerperzonen);
        })
        .catch(() => setChromstufen([]));
      // Zeigt die bereits gewählte Qualitätsstufe als markiert an (z.B. von
      // der KI automatisch nach Beschreibung gewählt) — Preis ist immer ein
      // ganzzahliges Vielfaches von kraft, sonst kam preisJeBonus nirgendwo her.
      setGewaehlteChromstufe(
        src.kraft > 0 && src.preis % src.kraft === 0 ? src.preis / src.kraft : null,
      );
    } else {
      setGewaehlteChromstufe(null);
    }
    setDescriptionDoc(parseRichText(src.description));
    setNotesDoc(parseRichText(src.notes));
    setSichtbarkeit(src.sichtbarkeit);
    setSichtbarFuer(src.sichtbarFuer);
    setAnsicht("uebersicht");
    setExpanded(true);
  }

  useEffect(() => {
    if (nurFenster) openEdit();
    // Nur beim Öffnen aus der Ideenschmiede — openEdit liest `item` vom ersten Render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function formular(): GegenstandUpdate {
    const sauber = name.trim();
    return {
      ...(sauber ? { name: sauber } : {}),
      preis,
      kraft: typ === "Waffe" ? schaden || kraft : kraft,
      seltenheit,
      eigenschaften: pairsToRecord(eigenschaften),
      storyRelevant,
      einzigartig,
      hatMenge,
      menge: hatMenge ? menge : 1,
      automatischImShop,
      gewicht,
      kapazitaet,
      istBehaelter,
      immerSichtbar,
      riggerBonus,
      maxDrohnen,
      cyberwall,
      deckBruteForce,
      deckSchleichen,
      deckDaten,
      deckKompilieren,
      deckElectronicWarfare,
      deckMatrixNavigation,
      wVerlust,
      koerperzone,
      slot,
      istWaffe,
      istNeurolink: typ === "Cyberware" && istNeurolink,
      schaden: typ === "Waffe" ? schaden || kraft : schaden,
      schadenArt: typ === "Waffe" || istWaffe ? schadenArtFuerWaffe(schadenArt) : schadenArt,
      kampfFertigkeit: typ === "Waffe" || istWaffe ? kampfFertigkeit : "",
      initiativeBonus,
      zusatzaktionen,
      traitBoni: Object.fromEntries(
        traitBoni.filter((p) => p.key.trim() && Number(p.value)).map((p) => [p.key.trim(), Number(p.value)]),
      ),
      ausruestungsfertigkeiten: Object.fromEntries(
        ausruestungsfertigkeiten
          .filter((p) => p.key.trim() && Number(p.value))
          .map((p) => [p.key.trim(), Number(p.value)]),
      ),
      // Ki-Tama (29.10.2026, 30.10.2026 umbenannt von "Materia"): nur
      // Einträge, die auch wirklich gespeichert werden (Name + Wert
      // gesetzt) UND deren Häkchen an ist.
      kiTamaFertigkeiten: Object.fromEntries(
        ausruestungsfertigkeiten
          .filter((p) => p.key.trim() && Number(p.value) && p.kiTama)
          .map((p) => [p.key.trim(), true]),
      ),
      stufe,
      widerstand,
      angriff,
      agilitaet,
      ruestungKaestchenMax,
      ruestungReduktionBasis,
      istReparaturmaterial,
      reparaturKapazitaet,
      istMaschinenteil,
      maschinenteilQualitaet,
      upgradeSlots,
      istAugment,
      augmentWaffentyp,
      augmentZielTyp,
      istNatuerlich,
      sichtbarkeit,
      sichtbarFuer,
    };
  }

  const snapshot = useMemo(
    () => formular(),
    // formular liest genau diese Felder. Beschreibung/Notizen haben ihren
    // eigenen Autosave und dürfen hier nicht mitgeschrieben werden.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      name, preis, kraft, typ, schaden, seltenheit, eigenschaften, storyRelevant, einzigartig,
      hatMenge, menge, automatischImShop, gewicht, kapazitaet, istBehaelter, immerSichtbar,
      riggerBonus, maxDrohnen, cyberwall, deckBruteForce, deckSchleichen, deckDaten,
      deckKompilieren, deckElectronicWarfare, deckMatrixNavigation, wVerlust, koerperzone, slot,
      istWaffe, istNeurolink, schadenArt, kampfFertigkeit, initiativeBonus, zusatzaktionen, traitBoni, ausruestungsfertigkeiten,
      stufe, widerstand, angriff, agilitaet, ruestungKaestchenMax, ruestungReduktionBasis,
      istReparaturmaterial, reparaturKapazitaet, istMaschinenteil, maschinenteilQualitaet,
      upgradeSlots, istAugment, augmentWaffentyp, augmentZielTyp, istNatuerlich, sichtbarkeit, sichtbarFuer,
    ],
  );

  const formularSpeichern = useAutosave(async (payload: GegenstandUpdate) => {
    await itemsApi.update(campaignId, item.id, payload);
    lokal.current = { ...lokal.current, ...payload };
    gespeichertJson.current = JSON.stringify(payload);
  });

  useEffect(() => {
    if (!expanded) return;
    const json = JSON.stringify(snapshot);
    // Beim Öffnen nur merken, nicht schreiben — sonst überschreibt ein
    // veraltetes `item` den Stand, den wir gerade selbst gespeichert haben.
    if (geradeGeoeffnet.current || gespeichertJson.current === "") {
      geradeGeoeffnet.current = false;
      gespeichertJson.current = json;
      return;
    }
    if (json === gespeichertJson.current) return;
    formularSpeichern(snapshot);
  }, [snapshot, expanded, formularSpeichern]);

  function fensterZu() {
    // Letzten Tippstoß noch schreiben, bevor die Liste nachzieht. onChanged
    // erst danach, sonst lädt die Übersicht den alten Stand und das nächste
    // Öffnen wirft die eben gespeicherte Ablage wieder weg.
    void Promise.resolve(formularSpeichern.jetzt()).finally(() => {
      setExpanded(false);
      onFensterSchliessen?.();
      onChanged();
    });
  }

  async function nameSpeichern() {
    const sauber = name.trim();
    if (!sauber) {
      setName(lokal.current.name || item.name);
      return;
    }
    if (sauber !== (lokal.current.name ?? item.name)) {
      await itemsApi.update(campaignId, item.id, { name: sauber });
      lokal.current = { ...lokal.current, name: sauber };
    }
  }

  async function ablageSetzen(wert: Ablage, zielId?: string | null) {
    setAblage(wert);
    if (wert !== "GELAGERT") setAblageZiel("");
    const ziel = wert === "GELAGERT" ? (zielId !== undefined ? zielId : ablageZiel || null) : null;
    try {
      await itemsApi.setAblage(campaignId, item.id, wert, ziel);
      lokal.current = { ...lokal.current, ablage: wert, ablageZielId: ziel };
    } catch {
      setAblage(item.ablage);
      setAblageZiel(item.ablageZielId ?? "");
    }
  }

  async function save() {
    await formularSpeichern.jetzt();
    const payload = formular();
    if (JSON.stringify(payload) !== gespeichertJson.current) {
      await itemsApi.update(campaignId, item.id, payload);
      lokal.current = { ...lokal.current, ...payload };
      gespeichertJson.current = JSON.stringify(payload);
    }
  }

  // Nur SL (Button ist ohnehin istGm-gated, aber der Endpunkt selbst ist
  // zusätzlich per require_campaign_gm abgesichert — doppelt hält besser).
  async function typAendern(neuerTyp: string) {
    setTypAendernOffen(false);
    await itemsApi.update(campaignId, item.id, { typ: neuerTyp });
    setTyp(neuerTyp);
    onChanged();
  }

  async function vorlagenArtSetzen(keineVorlage: boolean) {
    if (keineVorlage === !istVorlageLokal) return;
    setArtFehler(null);
    try {
      const aktualisiert = await itemsApi.vorlagenArt(campaignId, item.id, keineVorlage);
      setIstVorlageLokal(aktualisiert.istVorlage);
      setEinzigartig(aktualisiert.einzigartig);
      setAutomatischImShop(aktualisiert.automatischImShop);
      onChanged();
    } catch (e) {
      setArtFehler(e instanceof Error ? e.message : "Umschalten fehlgeschlagen");
    }
  }

  async function zuweisen(alsKopie: boolean) {
    if (!zuweisenZiel) return;
    setZuweisenLaeuft(true);
    setZuweisenHinweis("");
    try {
      await itemsApi.assign(campaignId, item.id, zuweisenZiel, alsKopie);
      setZuweisenZiel("");
      if (alsKopie) setZuweisenHinweis("Kopie angelegt — die Vorlage bleibt.");
      onChanged();
    } finally {
      setZuweisenLaeuft(false);
    }
  }

  async function besitzerWechseln() {
    if (!besitzerZiel) return;
    setBesitzerLaeuft(true);
    try {
      if (besitzerZiel === VORLAGE_SENTINEL) {
        await itemsApi.removeOwner(campaignId, item.id);
      } else {
        await itemsApi.changeOwner(campaignId, item.id, besitzerZiel);
      }
      setBesitzerZiel("");
      onChanged();
    } finally {
      setBesitzerLaeuft(false);
    }
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await itemsApi.uploadBild(campaignId, item.id, file);
      onChanged();
    } finally {
      setUploading(false);
    }
  }

  async function kiBildUebernehmen(blob: Blob) {
    setUploading(true);
    try {
      const datei = new File([blob], "ki-bild.png", { type: blob.type || "image/png" });
      await itemsApi.uploadBild(campaignId, item.id, datei);
      onChanged();
    } finally {
      setUploading(false);
    }
  }

  async function removeBild() {
    await itemsApi.update(campaignId, item.id, { bildUrl: "" });
    onChanged();
  }

  // Autosave für die Felder der Übersicht, des Umbaus und des Besitzes.
  // Beschreibung/Notizen bleiben bei ihrem eigenen Autosave — ein großer
  // save() würde einen halbfertigen Text mit wegschreiben.
  // Still: kein onChanged, solange das Fenster offen ist.
  const autosaveDescription = useAutosave(async (doc: JSONContent) => {
    await itemsApi.update(campaignId, item.id, { description: serializeRichText(doc) });
  });
  const autosaveNotes = useAutosave(async (doc: JSONContent) => {
    await itemsApi.update(campaignId, item.id, { notes: serializeRichText(doc) });
  });

  // Das Detail öffnet als eigenes Fenster statt inline aufzuklappen: hält die
  // Übersicht statisch (Leitprinzip "nie scrollen") und gibt dem Ding eine
  // feste Größe — das alte Akkordeon riss die Karte bei langen Inhalten in
  // die Breite. Kachel wie Zeile öffnen dasselbe Fenster.
  const fenster = (
    <>
    <Fenster
      offen={expanded}
      breit={ansicht === "uebersicht" || ansicht === "umbauen"}
      onSchliessen={fensterZu}
      kennung={item.id}
      titel={item.name}
      unterzeile={
        <>
          {typ}
          {item.istVorlage && " · Vorlage"}
        </>
      }
      ton="var(--bereich-gegenstaende)"
    >
      <div className="pcd-inhalt">
        <nav className="pcd-nav pcd-nav-gegenstaende">
          {(
            [
              ["uebersicht", "Übersicht"],
              ["beschreibung", "Beschreibung"],
              ["umbauen", "Umbauen"],
              ["notizen", "Notizen"],
              ["besitz", "Besitz"],
            ] as [GgAnsicht, string][]
          ).map(([wert, text]) => (
            <button
              key={wert}
              type="button"
              className={ansicht === wert ? "pcd-nav-aktiv" : ""}
              onClick={() => setAnsicht(wert)}
            >
              {text}
            </button>
          ))}
        </nav>

        <div className="pcd-bereich">
          {ansicht === "uebersicht" && (
            <div className="pcd-uebersicht">
              <div className="pcd-bild-bereich">
                {item.bildUrl ? (
                  <img
                    src={item.bildUrl}
                    alt=""
                    style={{ width: "100%", aspectRatio: "1", objectFit: "cover", borderRadius: "var(--radius)" }}
                  />
                ) : (
                  <div
                    style={{
                      width: "100%",
                      aspectRatio: "1",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "var(--grund)",
                      border: "1px solid var(--linie)",
                      borderRadius: "var(--radius)",
                      fontSize: 48,
                      color: "var(--text-leise)",
                    }}
                  >
                    {symbolFuerTyp(typ)}
                  </div>
                )}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
                  <input type="file" accept="image/*" onChange={handleFile} disabled={uploading} />
                  <button type="button" onClick={() => setKiBildOffen(true)} disabled={uploading}>
                    ✨ KI-Bild
                  </button>
                  {item.bildUrl && (
                    <>
                      <BildBlitz campaignId={campaignId} bildUrl={item.bildUrl} name={item.name} />
                      <button type="button" onClick={removeBild}>
                        Bild entfernen
                      </button>
                    </>
                  )}
                </div>
                {uploading && <p style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>lädt hoch…</p>}
                <KiBildPopup
                  offen={kiBildOffen}
                  objektTyp="Gegenstand"
                  objektName={item.name}
                  onSchliessen={() => setKiBildOffen(false)}
                  onPromptVorschlagen={() =>
                    kiBildPrompt(campaignId, {
                      objektTyp: "Gegenstand",
                      objektName: item.name,
                      bisherigeBeschreibung: item.description ? extrahiereReinenText(item.description) : "",
                      notizen: item.notes ? extrahiereReinenText(item.notes) : "",
                    })
                  }
                  onGenerieren={(provider, prompt) => kiBildGenerieren(campaignId, provider, prompt)}
                  onUebernehmen={kiBildUebernehmen}
                />
              </div>

              <div className="pcd-schnellzugriff">
                {item.istVorlage && (
                  <p style={{ fontSize: "0.85em", color: "var(--text-leise)", fontStyle: "italic", margin: "0 0 8px" }}>
                    Vorlage — hat keinen Besitzer
                  </p>
                )}
                <div className="pcd-feld">
                  <label htmlFor={`gg-name-${item.id}`}>Name</label>
                  <input
                    id={`gg-name-${item.id}`}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onBlur={() => void nameSpeichern()}
                  />
                </div>
                <p style={{ margin: "0 0 12px", color: "var(--text-leise)", fontSize: "0.85em" }}>
                  <span className="gg-typ-gewaehlt">{typ}</span>
                  {" · "}
                  {visibilityLabel(item)}
                </p>

                <div className="pcd-feld">
                  <label>Wo es geführt wird</label>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {ABLAGEN.map((a) => (
                      <button
                        key={a.wert}
                        type="button"
                        onClick={() => void ablageSetzen(a.wert)}
                        style={
                          ablage === a.wert
                            ? { borderColor: "var(--neon)", color: "var(--neon)", background: "var(--neon-schwach)" }
                            : undefined
                        }
                      >
                        {a.symbol} {a.label}
                      </button>
                    ))}
                  </div>
                  {ablage === "GELAGERT" && (
                    <select
                      value={ablageZiel}
                      onChange={(e) => {
                        setAblageZiel(e.target.value);
                        void ablageSetzen("GELAGERT", e.target.value || null);
                      }}
                    >
                      <option value="">— ohne festen Platz —</option>
                      {ziele.map((z) => (
                        <option key={z.id} value={z.id}>
                          {z.kind === "Ort" ? "Ort: " : "In: "}
                          {z.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                <div className="pcd-feld">
                  <label>Steckbrief</label>
                  <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text)" }}>
                    {typ === "Rüstung" && (
                      <>
                        <li>Reduktion: {ruestungReduktionBasis}</li>
                        <li>
                          Kästchen: {item.ruestungKaestchenAktuell}/{ruestungKaestchenMax}
                        </li>
                      </>
                    )}
                    {(typ === "Waffe" || istWaffe) && (
                      <li>Schaden: {typ === "Waffe" ? schaden || kraft : schaden}</li>
                    )}
                    {(typ === "Waffe" || istWaffe) && (
                      <li>Schadensart: {schadenArtLabel(schadenArtFuerWaffe(schadenArt))}</li>
                    )}
                    {(typ === "Waffe" || istWaffe) && kampfFertigkeit && (
                      <li>Würfelt mit: {KAMPF_FERTIGKEIT_LABEL[kampfFertigkeit]}</li>
                    )}
                    {CHROM_TYPEN.has(typ) && (
                      <li>
                        {kraft > 0 && `Stufe ${kraft} · `}
                        {koerperzone ? `${koerperzone}${slot ? ` Platz ${slot}` : ""}` : "keine Zone"}
                        {wVerlust > 0 && ` · −${wVerlust.toLocaleString("de-AT")} Willenskraft`}
                        {typ === "Cyberware" && istNeurolink && " · Neurolink"}
                      </li>
                    )}
                    {initiativeBonus !== 0 && (
                      <li>
                        Initiative {initiativeBonus > 0 ? "+" : ""}
                        {initiativeBonus}
                      </li>
                    )}
                    {zusatzaktionen !== 0 && (
                      <li>
                        Zusatzaktion: {zusatzaktionen === -1 ? "jede Runde" : `${zusatzaktionen}× pro Kampf`}
                      </li>
                    )}
                    {traitBoni.filter((p) => p.key.trim()).map((p) => (
                      <li key={`b-${p.key}`}>
                        {p.key} +{p.value}
                      </li>
                    ))}
                    {ausruestungsfertigkeiten.filter((p) => p.key.trim()).map((p) => (
                      <li key={`f-${p.key}`}>
                        {p.key} {p.value}
                      </li>
                    ))}
                    {FAHRZEUG_TYPEN.has(typ) && (
                      <li>
                        Stufe {stufe} · Widerstand {widerstand} · Angriff {angriff} · Agilität {agilitaet}
                      </li>
                    )}
                    {typ === "Riggerkonsole" && (
                      <li>
                        Rigger {riggerBonus >= 0 ? "+" : ""}
                        {riggerBonus} · max. {maxDrohnen} Drohnen
                      </li>
                    )}
                    {typ === "Commlink" && <li>I.C.E. {cyberwall}</li>}
                    {typ === "Cyberdeck" && (
                      <li>
                        B {deckBruteForce} · S {deckSchleichen} · D {deckDaten} · K {deckKompilieren} · EW{" "}
                        {deckElectronicWarfare} · N {deckMatrixNavigation}
                        {cyberwall > 0 && ` · Cyberwall +${cyberwall}`}
                      </li>
                    )}
                    {istBehaelter && kapazitaet > 0 && <li>Fasst {kapazitaet} kg</li>}
                    {hatMenge && <li>Menge: {menge}</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {ansicht === "beschreibung" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor
                content={descriptionDoc}
                onChange={(doc) => {
                  setDescriptionDoc(doc);
                  autosaveDescription(doc);
                }}
                minHeight={200}
                kiKontext={{ campaignId, objektTyp: "Gegenstand", objektName: item.name, feldLabel: "Beschreibung" }}
              />
            </div>
          )}

          {ansicht === "notizen" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor
                content={notesDoc}
                onChange={(doc) => {
                  setNotesDoc(doc);
                  autosaveNotes(doc);
                }}
                minHeight={200}
                kiKontext={{ campaignId, objektTyp: "Gegenstand", objektName: item.name, feldLabel: "Notizen" }}
              />
            </div>
          )}

          {ansicht === "umbauen" && (
            <div className="pcd-editor-bereich">
              <p style={{ color: "var(--text-leise)", fontSize: "0.85em", margin: 0 }}>
                Hier ändert sich, was das Ding tut. Das wird von selbst gespeichert, sobald du kurz innehältst.
              </p>

              {istGm && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    flexWrap: "wrap",
                    borderTop: "1px solid var(--linie)",
                    paddingTop: 8,
                  }}
                >
                  <span style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    Typ: <strong style={{ color: "var(--text)" }}>{symbolFuerTyp(typ)} {typ}</strong>
                  </span>
                  <button type="button" onClick={() => setTypAendernOffen(true)} style={{ fontSize: "0.85em" }}>
                    Typ ändern
                  </button>
                </div>
              )}
              {CHROM_TYPEN.has(typ) && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    Cyber-/Bioware: Boni unten, hier die Qualitätsstufe. Je mehr du je Bonuspunkt zahlst, desto
                    weniger Willenskraft kostet es dauerhaft.
                  </label>
                  <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
                    {gesamtBonus > 0 && (
                      <span style={{ fontSize: "0.9em", color: "var(--neon)" }}>
                        Gesamt-Bonus: <strong>+{gesamtBonus}</strong>
                      </span>
                    )}
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Körperzone
                      <select value={koerperzone} onChange={(e) => setKoerperzone(e.target.value)}>
                        <option value="">— offen —</option>
                        {zonen.map((z) => (
                          <option key={z} value={z}>
                            {z}
                          </option>
                        ))}
                      </select>
                    </label>
                    {koerperzone && (
                      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                        Platz
                        <select value={slot ?? ""} onChange={(e) => setSlot(e.target.value ? Number(e.target.value) : null)}>
                          <option value="">— egal —</option>
                          {SLOTS_PRO_ZONE.map((s) => (
                            <option key={s} value={s}>
                              Platz {s}
                            </option>
                          ))}
                        </select>
                      </label>
                    )}
                    <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
                      <input
                        type="checkbox"
                        checked={istWaffe}
                        onChange={(e) => {
                          setIstWaffe(e.target.checked);
                          if (e.target.checked) setSchadenArt(schadenArtFuerWaffe(schadenArt));
                        }}
                      />
                      zählt zusätzlich als Waffe
                    </label>
                    {typ === "Cyberware" && (
                      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
                        <input
                          type="checkbox"
                          checked={istNeurolink}
                          onChange={(e) => setIstNeurolink(e.target.checked)}
                        />
                        ist ein Neurolink
                      </label>
                    )}
                    {istWaffe && (
                      <>
                        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                          Schaden
                          <DotPool value={schaden} max={SCHADEN_MAX} onChange={setSchaden} />
                        </label>
                        {typ !== "Waffe" && (
                          <SchadensartFeld wert={schadenArt} onChange={setSchadenArt} />
                        )}
                        <KampfFertigkeitFeld wert={kampfFertigkeit} onChange={setKampfFertigkeit} />
                      </>
                    )}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 8 }}>
                    {chromstufen.map((st) => {
                      const istGewaehlt = gewaehlteChromstufe === st.preisJeBonus;
                      return (
                        <button
                          key={st.name}
                          type="button"
                          onClick={() => {
                            setGewaehlteChromstufe(st.preisJeBonus);
                            setPreis(st.preis);
                            setWVerlust(st.wVerlustGenau);
                            setKraft(Math.max(1, gesamtBonus));
                          }}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            gap: 10,
                            textAlign: "left",
                            borderColor: istGewaehlt ? "var(--neon)" : undefined,
                            color: istGewaehlt ? "var(--neon)" : undefined,
                          }}
                          title={st.beschreibung}
                        >
                          <span>{st.name}</span>
                          <span className="mono">
                            {st.preis.toLocaleString("de-AT")}¥ · −{st.wVerlust}
                            {st.wVerlustGenau !== st.wVerlust && (
                              <em style={{ fontStyle: "normal", color: "var(--text-aus)" }}>
                                {" "}
                                ({st.wVerlustGenau.toLocaleString("de-AT")} gezählt)
                              </em>
                            )}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <p style={{ fontSize: "0.85em", color: "var(--text-leise)", marginTop: 6 }}>
                    Zählt mit <strong>{wVerlust.toLocaleString("de-AT")}</strong> gegen die Willenskraft.
                  </p>
                </div>
              )}

              {typ === "Riggerkonsole" && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Riggerkonsole</label>
                  <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Rigger-Bonus
                      <input
                        type="number"
                        value={riggerBonus}
                        onChange={(e) => setRiggerBonus(Number(e.target.value))}
                        style={{ width: 70 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Max. Drohnen
                      <input
                        type="number"
                        min={0}
                        value={maxDrohnen}
                        onChange={(e) => setMaxDrohnen(Number(e.target.value))}
                        style={{ width: 70 }}
                      />
                    </label>
                  </div>
                </div>
              )}

              {typ === "Commlink" && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    Commlink — I.C.E. / Matrix-Verteidigung
                  </label>
                  <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Cyberwall
                      <input
                        type="number"
                        min={0}
                        value={cyberwall}
                        onChange={(e) => setCyberwall(Number(e.target.value))}
                        style={{ width: 70 }}
                      />
                    </label>
                  </div>
                </div>
              )}

              {typ === "Cyberdeck" && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    Cyberdeck — Bonuswürfel je NeuroWeaving-Fertigkeit
                  </label>
                  <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Brute Force
                      <input
                        type="number"
                        value={deckBruteForce}
                        onChange={(e) => setDeckBruteForce(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Schleichen
                      <input
                        type="number"
                        value={deckSchleichen}
                        onChange={(e) => setDeckSchleichen(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Daten Verarbeiten
                      <input
                        type="number"
                        value={deckDaten}
                        onChange={(e) => setDeckDaten(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Kompilieren
                      <input
                        type="number"
                        value={deckKompilieren}
                        onChange={(e) => setDeckKompilieren(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Electronic Warfare
                      <input
                        type="number"
                        value={deckElectronicWarfare}
                        onChange={(e) => setDeckElectronicWarfare(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Matrix-Navigation
                      <input
                        type="number"
                        value={deckMatrixNavigation}
                        onChange={(e) => setDeckMatrixNavigation(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Cyberwall-Bonus
                      <input
                        type="number"
                        min={0}
                        value={cyberwall}
                        onChange={(e) => setCyberwall(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                  </div>
                </div>
              )}

              <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                  Bonus auf bestehende Werte (solange ausgerüstet)
                </label>
                {traitBoni.map((p, i) => (
                  <div key={i} style={{ display: "flex", gap: 6, marginTop: 4 }}>
                    <select
                      value={p.key}
                      onChange={(e) =>
                        setTraitBoni(traitBoni.map((x, idx) => (idx === i ? { ...x, key: e.target.value } : x)))
                      }
                      style={{ flex: 1 }}
                    >
                      <option value="">— Wert wählen —</option>
                      {traitKatalog.map((t) => (
                        <option key={t.id} value={t.name}>
                          {t.name}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      placeholder="Bonus"
                      value={p.value}
                      onChange={(e) =>
                        setTraitBoni(traitBoni.map((x, idx) => (idx === i ? { ...x, value: e.target.value } : x)))
                      }
                      style={{ width: 70 }}
                    />
                    <button type="button" onClick={() => setTraitBoni(traitBoni.filter((_, idx) => idx !== i))}>
                      ×
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setTraitBoni([...traitBoni, { key: "", value: "1" }])}
                  style={{ marginTop: 4, fontSize: "0.85em" }}
                >
                  + Bonus
                </button>

                {(CHROM_TYPEN.has(typ) || typ === "Cyberdeck") && (
                  <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Initiative-Bonus
                      <input
                        type="number"
                        value={initiativeBonus}
                        onChange={(e) => setInitiativeBonus(Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Zusatzaktionen
                      <select value={zusatzaktionen} onChange={(e) => setZusatzaktionen(Number(e.target.value))}>
                        <option value={0}>keine</option>
                        <option value={1}>1× pro Kampf</option>
                        <option value={2}>2× pro Kampf</option>
                        <option value={-1}>jede Runde</option>
                      </select>
                    </label>
                  </div>
                )}

                <label style={{ fontSize: "0.85em", color: "var(--text-leise)", display: "block", marginTop: 12 }}>
                  Ausrüstungsfertigkeiten (neue Fertigkeiten NUR durch diesen Gegenstand — Häkchen "Ki-Tama":
                  Spieler darf mit eigener EP hochleveln, Stufe bleibt am Gegenstand)
                </label>
                {ausruestungsfertigkeiten.map((p, i) => (
                  <div key={i} style={{ display: "flex", gap: 6, marginTop: 4 }}>
                    <input
                      placeholder="Name der neuen Fertigkeit"
                      value={p.key}
                      onChange={(e) =>
                        setAusruestungsfertigkeiten(
                          ausruestungsfertigkeiten.map((x, idx) => (idx === i ? { ...x, key: e.target.value } : x)),
                        )
                      }
                      style={{ flex: 1 }}
                    />
                    <input
                      type="number"
                      placeholder="Würfel"
                      value={p.value}
                      onChange={(e) =>
                        setAusruestungsfertigkeiten(
                          ausruestungsfertigkeiten.map((x, idx) => (idx === i ? { ...x, value: e.target.value } : x)),
                        )
                      }
                      style={{ width: 70 }}
                    />
                    <label
                      style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.8em", whiteSpace: "nowrap" }}
                      title="Ki-Tama: der Spieler darf mit eigener EP hochleveln (bis Stufe 6) — die Stufe bleibt am Gegenstand und wandert bei Besitzerwechsel mit."
                    >
                      <input
                        type="checkbox"
                        checked={Boolean(p.kiTama)}
                        onChange={(e) =>
                          setAusruestungsfertigkeiten(
                            ausruestungsfertigkeiten.map((x, idx) => (idx === i ? { ...x, kiTama: e.target.checked } : x)),
                          )
                        }
                      />
                      Ki-Tama
                    </label>
                    <button
                      type="button"
                      onClick={() => setAusruestungsfertigkeiten(ausruestungsfertigkeiten.filter((_, idx) => idx !== i))}
                    >
                      ×
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setAusruestungsfertigkeiten([...ausruestungsfertigkeiten, { key: "", value: "1" }])}
                  style={{ marginTop: 4, fontSize: "0.85em" }}
                >
                  + Ausrüstungsfertigkeit
                </button>
              </div>

              {FAHRZEUG_TYPEN.has(typ) && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    Werte (Blatt Drohne/Fahrzeug): Stufe auf Widerstand, Angriff und Agilität.
                  </label>
                  <StufenBlatt
                    werte={{ stufe, widerstand, angriff, agilitaet }}
                    onAendern={(feld, wert) => {
                      if (feld === "stufe") setStufe(wert);
                      else if (feld === "widerstand") setWiderstand(wert);
                      else if (feld === "angriff") setAngriff(wert);
                      else setAgilitaet(wert);
                    }}
                  />
                </div>
              )}

              {typ === "Waffe" && (
                <div>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Schaden</label>
                  <div>
                    <DotPool
                      value={schaden || kraft}
                      max={SCHADEN_MAX}
                      onChange={(n) => {
                        setSchaden(n);
                        setKraft(n);
                      }}
                    />
                  </div>
                  <SchadensartFeld wert={schadenArt} onChange={setSchadenArt} />
                  <KampfFertigkeitFeld wert={kampfFertigkeit} onChange={setKampfFertigkeit} />
                </div>
              )}

              {typ === "Rüstung" && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    Kästchen + Schadensreduktion. Aktueller Zustand ändert sich über Treffer, nicht hier.
                  </label>
                  <div style={{ display: "flex", gap: 16, marginTop: 6, flexWrap: "wrap" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Kästchen (max)
                      <input
                        type="number"
                        min={0}
                        value={ruestungKaestchenMax}
                        onChange={(e) => setRuestungKaestchenMax(Math.max(0, Number(e.target.value)))}
                        style={{ width: 70 }}
                      />
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                      Reduktion
                      <input
                        type="number"
                        min={0}
                        value={ruestungReduktionBasis}
                        onChange={(e) => setRuestungReduktionBasis(Math.max(0, Number(e.target.value)))}
                        style={{ width: 70 }}
                      />
                    </label>
                  </div>
                  {item.ruestungKaestchenMax > 0 && (
                    <p style={{ fontSize: "0.85em", color: "var(--text-leise)", marginTop: 6 }}>
                      Aktuell:{" "}
                      <strong>
                        {item.ruestungKaestchenAktuell}/{item.ruestungKaestchenMax}
                      </strong>{" "}
                      Kästchen.
                    </p>
                  )}
                  <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em", marginTop: 8 }}>
                    <input
                      type="checkbox"
                      checked={istNatuerlich}
                      onChange={(e) => setIstNatuerlich(e.target.checked)}
                    />
                    Natürliche Rüstung (Rassen-/Kreatur-Feature, z.B. Dug'Rah)
                  </label>
                  {istNatuerlich && (
                    <p style={{ fontSize: "0.85em", color: "var(--text-leise)", marginTop: 4 }}>
                      Kästchen-Max oben wirkt dann nur noch als Vorlagen-Hinweis — tatsächlich
                      gezählt wird live die Widerstandsfähigkeit der tragenden Person. Nicht
                      ablegbar für den Spieler (nur die SL im Ausnahmefall), nicht reparierbar —
                      heilt stattdessen über die Rast-Mechanik.
                    </p>
                  )}
                  {item.ruestungKaestchenMax > 0 && item.ruestungKaestchenAktuell < item.ruestungKaestchenMax && !item.istNatuerlich && (
                    <p style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                      Beschädigt — Reparatur läuft jetzt über das eigenständige Burgermenü "Reparatur"
                      (docs/wiki/concepts/drohnen-fahrzeuge.md).
                    </p>
                  )}
                </div>
              )}

              <EigenschaftenEditor pairs={eigenschaften} onChange={setEigenschaften} />

              <button type="button" onClick={save}>
                Jetzt speichern
              </button>
            </div>
          )}

          {ansicht === "besitz" && (
            <div className="pcd-editor-bereich">
              <div className="pcd-feld">
                <label>Preis (¥)</label>
                <input type="number" min={0} value={preis} onChange={(e) => setPreis(Number(e.target.value))} />
              </div>
              <div className="pcd-feld">
                <label>Seltenheit</label>
                <DotPool value={seltenheit} max={5} onChange={(v) => setSeltenheit(Math.max(1, v))} size={12} />
              </div>
              {AUGMENT_TRAEGER_TYPEN.has(typ) && (
                <div className="pcd-feld">
                  <label>Upgrade-Slots</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={upgradeSlots}
                    onChange={(e) => setUpgradeSlots(Math.max(0, Math.min(6, Number(e.target.value))))}
                    style={{ width: 60 }}
                  />
                </div>
              )}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  Gewicht (kg)
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    value={gewicht}
                    onChange={(e) => setGewicht(Number(e.target.value))}
                    style={{ width: 110 }}
                  />
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  Fasst (kg)
                  <input
                    type="number"
                    min={0}
                    step={1}
                    value={kapazitaet}
                    onChange={(e) => setKapazitaet(Number(e.target.value))}
                    style={{ width: 110 }}
                    title="Wie viel dieser Gegenstand aufnehmen kann. 0 = kein Behälter."
                  />
                </label>
              </div>

              <VisibilitySelector
                label="Sichtbarkeit"
                modus={sichtbarkeit}
                sichtbarFuer={sichtbarFuer}
                onChange={(m, f) => {
                  setSichtbarkeit(m);
                  setSichtbarFuer(f);
                }}
                pcOptions={pcOptions}
              />

              <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                <button type="button" onClick={() => setShowOptions((v) => !v)} style={{ fontSize: "0.85em" }}>
                  ⚙ {showOptions ? "Optionen ausblenden" : "Optionen anzeigen"}
                </button>
                {showOptions && (
                  <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
                    <label style={{ fontSize: "0.9em" }}>
                      <input type="checkbox" checked={storyRelevant} onChange={(e) => setStoryRelevant(e.target.checked)} />{" "}
                      Story relevant (im Beziehungsgraph + Spieler-Lexikon sobald entdeckt)
                    </label>
                    <label style={{ fontSize: "0.9em" }}>
                      <input
                        type="checkbox"
                        checked={istVorlageLokal}
                        disabled={!!personId}
                        onChange={() => void vorlagenArtSetzen(false)}
                      />{" "}
                      Einzigartige Kopie wird erstellt
                    </label>
                    <label style={{ fontSize: "0.9em" }}>
                      <input
                        type="checkbox"
                        checked={!istVorlageLokal}
                        onChange={() => void vorlagenArtSetzen(true)}
                      />{" "}
                      Einzigartig - keine Vorlage
                    </label>
                    {personId && (
                      <p style={{ fontSize: "0.8em", color: "var(--text-leise)", margin: 0 }}>
                        Hat einen Besitzer — Kopie erst, wenn es wieder eine Vorlage ohne Besitzer ist.
                      </p>
                    )}
                    {artFehler && (
                      <p style={{ fontSize: "0.8em", color: "var(--neon-rot, #e55)", margin: 0 }}>{artFehler}</p>
                    )}
                    {/* Eigenständiger Schalter fürs Lore-Feld `einzigartig`
                        (26.10.2026, Mark: die beiden Checkboxen oben heißen
                        zwar auch "Einzigartig...", sind aber beide an
                        istVorlage gekoppelt und setzen `einzigartig` nie auf
                        false — es gab schlicht keinen Weg, das Häkchen
                        rauszunehmen). Läuft über den normalen Autosave
                        (`formular()` führt `einzigartig` schon), kein
                        eigener Request nötig. */}
                    <label style={{ fontSize: "0.9em" }}>
                      <input type="checkbox" checked={einzigartig} onChange={(e) => setEinzigartig(e.target.checked)} />{" "}
                      Einzigartig
                    </label>
                    <p style={{ fontSize: "0.8em", color: "var(--text-leise)", margin: 0 }}>
                      Unabhängig von den beiden Kopier-Optionen oben — rein das Lore-Häkchen "gibt es nur
                      einmal in der Welt". Muss aus sein, damit Menge/Zusammenlegen unten überhaupt Sinn
                      ergeben.
                    </p>
                    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                      <label style={{ fontSize: "0.9em" }}>
                        <input type="checkbox" checked={hatMenge} onChange={(e) => setHatMenge(e.target.checked)} /> Menge
                        verfolgen
                      </label>
                      {hatMenge && (
                        <input
                          type="number"
                          min={0}
                          value={menge}
                          onChange={(e) => setMenge(Number(e.target.value))}
                          style={{ width: 70 }}
                        />
                      )}
                      {/* Mehrere einzelne Stücke desselben Dings (26.10.2026,
                          Mark: 3 Maschinenteile sollen ein Objekt mit Anzahl 3
                          werden) zu einem Stapel zusammenlegen. Nur mit
                          Besitzer — Vorlagen haben niemandem gehörende
                          Duplikate nicht in diesem Sinn. Absichtlich OHNE
                          einzigartig-Filter: das ist der Schema-Default für
                          praktisch jeden neuen Gegenstand, ein Filter davor
                          würde den Knopf fast überall verstecken — das Popup
                          erklärt es selbst, wenn es wirklich zutrifft. */}
                      {personId && (
                        <button type="button" onClick={() => setZusammenlegenOffen(true)} style={{ fontSize: "0.85em" }}>
                          <span aria-hidden="true">⧉</span> Zusammenlegen…
                        </button>
                      )}
                    </div>
                    <label style={{ fontSize: "0.9em" }}>
                      <input
                        type="checkbox"
                        checked={immerSichtbar}
                        onChange={(e) => setImmerSichtbar(e.target.checked)}
                      />{" "}
                      Fällt am Körper auf
                    </label>
                    <label style={{ fontSize: "0.9em" }}>
                      <input
                        type="checkbox"
                        checked={istBehaelter}
                        onChange={(e) => setIstBehaelter(e.target.checked)}
                      />{" "}
                      Kann etwas aufnehmen
                    </label>
                    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                      <label style={{ fontSize: "0.9em" }}>
                        <input
                          type="checkbox"
                          checked={istReparaturmaterial}
                          onChange={(e) => setIstReparaturmaterial(e.target.checked)}
                        />{" "}
                        Reparaturmaterial
                      </label>
                      {istReparaturmaterial && (
                        <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6 }}>
                          Kapazität
                          <input
                            type="number"
                            min={0}
                            value={reparaturKapazitaet}
                            onChange={(e) => setReparaturKapazitaet(Math.max(0, Number(e.target.value)))}
                            style={{ width: 60 }}
                          />
                        </label>
                      )}
                    </div>
                    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                      <label style={{ fontSize: "0.9em" }}>
                        <input
                          type="checkbox"
                          checked={istMaschinenteil}
                          onChange={(e) => {
                            setIstMaschinenteil(e.target.checked);
                            if (e.target.checked && !maschinenteilQualitaet) setMaschinenteilQualitaet("normal");
                          }}
                        />{" "}
                        Maschinenteil
                      </label>
                      {istMaschinenteil && (
                        <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6 }}>
                          Qualität
                          <select
                            value={maschinenteilQualitaet}
                            onChange={(e) => setMaschinenteilQualitaet(e.target.value)}
                          >
                            <option value="minderwertig">minderwertig (nur Reparatur)</option>
                            <option value="normal">normal (Fertigkeiten)</option>
                            <option value="hochwertig">hochwertig (Attribute + Fertigkeiten)</option>
                          </select>
                        </label>
                      )}
                    </div>
                    {AUGMENT_TRAEGER_TYPEN.has(typ) && (
                      <p style={{ fontSize: "0.8em", color: "var(--text-leise)", margin: 0 }}>
                        Upgrade-Slots lassen sich oben bei Seltenheit einstellen.
                      </p>
                    )}
                    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                      <label style={{ fontSize: "0.9em" }}>
                        <input type="checkbox" checked={istAugment} onChange={(e) => setIstAugment(e.target.checked)} />{" "}
                        Ist selbst ein Upgrade
                      </label>
                      {istAugment && (
                        <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6 }}>
                          Passt an
                          <select value={augmentWaffentyp} onChange={(e) => setAugmentWaffentyp(e.target.value as KampfFertigkeit)}>
                            <option value="">alles (Waffe/Rüstung/Cyberdeck/Riggerkonsole)</option>
                            <option value="Schusswaffen">nur Schusswaffen</option>
                            <option value="Nahkampf">nur Nahkampf</option>
                            <option value="Handgemenge">nur Handgemenge</option>
                          </select>
                        </label>
                      )}
                    </div>
                    {istAugment && (
                      <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6 }}>
                        Nur an diesem Zieltyp
                        <select
                          value={augmentZielTyp}
                          onChange={(e) => setAugmentZielTyp(e.target.value as typeof augmentZielTyp)}
                        >
                          <option value="">alle (Waffe/Rüstung/Cyberdeck/Riggerkonsole/Drohne/Fahrzeug)</option>
                          <option value="Waffe">nur Waffe</option>
                          <option value="Rüstung">nur Rüstung</option>
                          <option value="Cyberdeck">nur Cyberdeck</option>
                          <option value="Riggerkonsole">nur Riggerkonsole</option>
                        </select>
                      </label>
                    )}
                    {istAugment && (
                      <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8, marginTop: 4 }}>
                        <label style={{ fontSize: "0.85em", color: "var(--text-leise)", display: "block" }}>
                          Wirkung am Ziel, sobald montiert (addiert sich auf den Basiswert — außer
                          Schadensart, die ersetzt ihn).
                        </label>
                        <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap" }}>
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                            Schaden
                            <input
                              type="number"
                              value={schaden}
                              onChange={(e) => setSchaden(Number(e.target.value))}
                              style={{ width: 60 }}
                            />
                          </label>
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                            Reduktion
                            <input
                              type="number"
                              min={0}
                              value={ruestungReduktionBasis}
                              onChange={(e) => setRuestungReduktionBasis(Math.max(0, Number(e.target.value)))}
                              style={{ width: 60 }}
                            />
                          </label>
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                            Kästchen
                            <input
                              type="number"
                              min={0}
                              value={ruestungKaestchenMax}
                              onChange={(e) => setRuestungKaestchenMax(Math.max(0, Number(e.target.value)))}
                              style={{ width: 60 }}
                            />
                          </label>
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                            Initiative-Bonus
                            <input
                              type="number"
                              value={initiativeBonus}
                              onChange={(e) => setInitiativeBonus(Number(e.target.value))}
                              style={{ width: 60 }}
                            />
                          </label>
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                            Zusatzaktionen
                            <select value={zusatzaktionen} onChange={(e) => setZusatzaktionen(Number(e.target.value))}>
                              <option value={0}>keine</option>
                              <option value={1}>1× pro Kampf</option>
                              <option value={2}>2× pro Kampf</option>
                              <option value={-1}>jede Runde</option>
                            </select>
                          </label>
                        </div>
                        <div style={{ marginTop: 8 }}>
                          <label style={{ fontSize: "0.85em", color: "var(--text-leise)", display: "flex", alignItems: "center", gap: 8 }}>
                            Schadensart ändern
                            <select value={schadenArt} onChange={(e) => setSchadenArt(e.target.value as typeof schadenArt)}>
                              <option value="">unverändert lassen</option>
                              <option value="schlag">Schlag</option>
                              <option value="schwer">Tödlich</option>
                              <option value="aggraviert">Schwerheilbar</option>
                            </select>
                          </label>
                        </div>
                      </div>
                    )}
                    <label style={{ fontSize: "0.9em" }}>
                      <input
                        type="checkbox"
                        checked={automatischImShop}
                        onChange={(e) => setAutomatischImShop(e.target.checked)}
                      />{" "}
                      Automatisch in Shops gleicher Seltenheit
                    </label>
                  </div>
                )}
              </div>

              {!item.istVorlage && (
                <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                  <div style={{ fontSize: "0.85em", marginBottom: 6 }}>
                    <span style={{ color: "var(--text-leise)" }}>Gehört </span>
                    <strong style={{ color: "var(--neon)" }}>
                      {alleOptionen.find((p) => p.id === personId)?.name ?? "niemandem"}
                    </strong>
                  </div>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                    An jemand anderen übergeben
                  </label>
                  <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
                    <select value={besitzerZiel} onChange={(e) => setBesitzerZiel(e.target.value)}>
                      <option value="">Person wählen...</option>
                      <option value={VORLAGE_SENTINEL}>— Vorlage (kein Besitzer) —</option>
                      {alleOptionen
                        .filter((p) => p.id !== personId)
                        .map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name}
                          </option>
                        ))}
                    </select>
                    <button type="button" onClick={besitzerWechseln} disabled={!besitzerZiel || besitzerLaeuft}>
                      {besitzerLaeuft ? "..." : "Übertragen"}
                    </button>
                  </div>
                </div>
              )}

              {item.istVorlage &&
                (() => {
                  const keineKopie = item.einzigartig || item.storyRelevant;
                  return (
                    <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                      <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                        {keineKopie
                          ? "Diesem Gegenstand zuweisen"
                          : "Diesem Gegenstand zuweisen (erstellt eine Kopie)"}
                      </label>
                      <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
                        <select value={zuweisenZiel} onChange={(e) => setZuweisenZiel(e.target.value)}>
                          <option value="">Person wählen...</option>
                          {alleOptionen.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                            </option>
                          ))}
                        </select>
                        {keineKopie && (
                          <button type="button" onClick={() => void zuweisen(false)} disabled={!zuweisenZiel || zuweisenLaeuft}>
                            {zuweisenLaeuft ? "..." : "Übergeben"}
                          </button>
                        )}
                        <button type="button" onClick={() => void zuweisen(true)} disabled={!zuweisenZiel || zuweisenLaeuft}>
                          {zuweisenLaeuft ? "..." : "Kopie erstellen"}
                        </button>
                      </div>
                      {keineKopie && (
                        <p style={{ fontSize: "0.8em", color: "var(--text-leise)", margin: "6px 0 0" }}>
                          Übergeben nimmt die Vorlage. Kopie lässt sie stehen.
                        </p>
                      )}
                      {zuweisenHinweis && (
                        <p style={{ fontSize: "0.8em", color: "var(--neon)", margin: "6px 0 0" }}>{zuweisenHinweis}</p>
                      )}
                    </div>
                  );
                })()}

              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <button type="button" onClick={save}>
                  Jetzt speichern
                </button>
                <button
                  type="button"
                  onClick={() => setLoeschenOffen(true)}
                  style={{
                    marginLeft: "auto",
                    fontSize: "0.8rem",
                    padding: "4px 10px",
                    minHeight: 0,
                    color: "var(--text-leise)",
                    borderColor: "var(--linie)",
                    background: "transparent",
                  }}
                >
                  Entfernen
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Fenster>
      {loeschenOffen && (
        <Bestaetigung
          titel="Gegenstand entfernen?"
          text={`„${formelKlartext(item.name)}“ wirklich entfernen?`}
          jaText="Ja, entfernen"
          neinText="Abbrechen"
          onJa={() => {
            setLoeschenOffen(false);
            onRemoved();
          }}
          onNein={() => setLoeschenOffen(false)}
        />
      )}

      {typAendernOffen && (
        <Fenster
          offen
          titel="Gegenstandstyp ändern"
          unterzeile={`${item.name} · aktuell: ${symbolFuerTyp(typ)} ${typ}`}
          kennung={`typ-aendern:${item.id}`}
          ton="var(--bereich-gegenstaende)"
          onSchliessen={() => setTypAendernOffen(false)}
        >
          <div style={{ padding: 8 }}>
            <p style={{ color: "var(--text-leise)", fontSize: "0.85em", marginTop: 0 }}>
              Nur für die Spielleitung — z.B. um einen von der KI falsch eingeordneten Gegenstand zu
              korrigieren. Typ-spezifische Werte des alten Typs (Schaden, Rüstungskästchen, Deck-Werte, …)
              bleiben in der Datenbank stehen, auch wenn sie beim neuen Typ nicht mehr angezeigt werden.
            </p>
            <TypKachelAuswahl onWaehlen={typAendern} />
          </div>
        </Fenster>
      )}

      {personId && (
        <ZusammenlegenPopup
          item={item}
          offen={zusammenlegenOffen}
          campaignId={campaignId}
          onZusammengelegt={() => {
            setZusammenlegenOffen(false);
            onChanged();
          }}
          onAbbrechen={() => setZusammenlegenOffen(false)}
        />
      )}
    </>
  );

  if (nurFenster) return fenster;

  if (kachel) {
    return (
      <>
        <button type="button" className="gg-kachel" onClick={openEdit} title={formelKlartext(item.name)}>
          <span className="gg-kachel-bild">
            {item.bildUrl ? <img src={item.bildUrl} alt="" /> : <span aria-hidden="true">◈</span>}
            {item.hatMenge && <span className="gg-kachel-menge">×{item.menge}</span>}
          </span>
          <span className="gg-kachel-name">
            <FormelText text={item.name} />
          </span>
          <span className="gg-kachel-zeile">
            {item.typ}
            {item.preis > 0 && ` · ${item.preis}¥`}
            {item.gewicht > 0 && ` · ${item.gewicht} kg`}
          </span>
          {steckbriefKurz(item).length > 0 && (
            <span className="gg-kachel-steckbrief">{steckbriefKurz(item).join(" · ")}</span>
          )}
          <span className="gg-kachel-marken">
            {item.sichtbarkeit === "GM" && <span className="gg-marke" data-ton="signal">SL</span>}
            {item.storyRelevant && <span className="gg-marke" data-ton="neon">Story</span>}
            {item.istVorlage && <span className="gg-marke">Vorlage</span>}
          </span>
        </button>
        {fenster}
      </>
    );
  }

  return (
    <div style={{ borderBottom: "1px solid var(--linie)", padding: "6px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {item.bildUrl && (
            <img src={item.bildUrl} alt="" style={{ width: 28, height: 28, objectFit: "cover", borderRadius: 4 }} />
          )}
          <FormelText text={item.name} />
          {item.hatMenge && <strong>×{item.menge}</strong>}
          <span style={{ fontSize: "0.75em", color: "var(--text-leise)" }}>
            [{item.typ}
            {item.preis > 0 && `, ${item.preis}¥`}] ({visibilityLabel(item)}){item.storyRelevant && " · Story relevant"}
            {item.istVorlage && " · Vorlage"}
          </span>
        </span>
        <span style={{ display: "flex", gap: 6 }}>
          <button type="button" onClick={openEdit}>
            Bearbeiten
          </button>
          <button type="button" onClick={() => setLoeschenOffen(true)}>
            Entfernen
          </button>
        </span>
      </div>
      {fenster}
    </div>
  );
}

export function CharacterSheetPanel({
  campaignId,
  person,
  pcOptions,
  alleOptionen,
}: {
  campaignId: string;
  person: Person;
  pcOptions: PersonOption[];
  alleOptionen: PersonOption[];
}) {
  const [katalog, setKatalog] = useState<TraitDef[]>([]);
  const [werte, setWerte] = useState<TraitRating[]>([]);
  const [items, setItems] = useState<Gegenstand[]>([]);
  const [loading, setLoading] = useState(true);
  const [itemName, setItemName] = useState("");
  const [itemTyp, setItemTyp] = useState<string | null>(null);
  const [itemAnlegenOffen, setItemAnlegenOffen] = useState(false);
  const [showTraitOptions, setShowTraitOptions] = useState(false);

  async function refresh() {
    const [k, w, i] = await Promise.all([
      traitsApi.getKatalog(campaignId),
      traitsApi.getWerte(campaignId, person.id),
      itemsApi.list(campaignId, person.id),
    ]);
    setKatalog(k);
    setWerte(w);
    setItems(i);
  }

  useEffect(() => {
    setLoading(true);
    refresh().finally(() => setLoading(false));
  }, [campaignId, person.id]);

  async function setRating(t: MergedTrait, rating: number) {
    const clamped = Math.max(0, Math.min(rating, t.max));
    // `null` heisst "Maximum nicht anfassen" (siehe traits/repository.py::
    // set_rating). Hier wird nur der Wert gesetzt — das Maximum kommt aus
    // der Rasse oder von der Spielleitung und geht diesen Klick nichts an.
    await traitsApi.setWert(campaignId, person.id, t.traitDefId, clamped, null);
    await refresh();
  }

  async function adjustMax(t: MergedTrait, delta: number) {
    const newMax = Math.max(1, t.max + delta);
    const newRating = Math.min(t.rating, newMax);
    // **Immer die Zahl schicken, nie null.** Vorher stand hier
    // `newMax !== t.defaultMax ? newMax : null` — seit `null` "nicht
    // anfassen" bedeutet, liesse sich ein Maximum damit nicht mehr auf den
    // Katalogwert zurücksetzen: der Knopf hätte stumm nichts getan.
    await traitsApi.setWert(campaignId, person.id, t.traitDefId, newRating, newMax);
    await refresh();
  }

  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!itemName.trim() || !itemTyp) return;
    await itemsApi.create(campaignId, person.id, { name: itemName, typ: itemTyp });
    setItemName("");
    setItemTyp(null);
    setItemAnlegenOffen(false);
    await refresh();
  }

  async function removeItem(itemId: string) {
    await itemsApi.remove(campaignId, itemId);
    await refresh();
  }

  if (loading) return <p>Lade Charakterblatt...</p>;

  const merged = mergeCatalogWithRatings(katalog, werte);
  const grouped = groupByCategory(merged);

  return (
    <div style={{ padding: 16, background: "var(--flaeche-hoch)", border: "1px solid var(--linie)", borderRadius: 8, marginTop: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
        <h3 style={{ margin: 0, fontSize: "1em", color: "var(--text)" }}>Werte</h3>
        <button type="button" onClick={() => setShowTraitOptions((v) => !v)} style={{ fontSize: "0.85em" }}>
          ⚙ {showTraitOptions ? "Optionen ausblenden" : "Optionen anzeigen"}
        </button>
      </div>

      {grouped.map(([category, traits]) => (
        <div key={category} style={{ marginBottom: 16 }}>
          <h4 style={{ margin: "0 0 8px", color: "var(--text-leise)" }}>{CATEGORY_LABELS[category] ?? category}</h4>
          {traits.map((t) => (
            <div
              key={t.traitDefId}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "4px 0",
                flexWrap: "wrap",
                gap: 4,
              }}
            >
              <span style={{ minWidth: 160 }}>{t.name}</span>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", minWidth: 0 }}>
                <DotPool value={t.rating} max={t.max} onChange={(v) => setRating(t, v)} />
                {showTraitOptions && (
                  <span style={{ display: "flex", gap: 2 }}>
                    <button
                      type="button"
                      title="Maximum für diesen Wert bei dieser Person verringern"
                      onClick={() => adjustMax(t, -1)}
                      style={{ padding: "0 6px", fontSize: "0.8em" }}
                    >
                      −max
                    </button>
                    <button
                      type="button"
                      title="Maximum für diesen Wert bei dieser Person erhöhen (z.B. für besonders mächtige Charaktere)"
                      onClick={() => adjustMax(t, 1)}
                      style={{ padding: "0 6px", fontSize: "0.8em" }}
                    >
                      +max
                    </button>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ))}

      <div>
        <h4 style={{ margin: "0 0 8px", color: "var(--text-leise)" }}>Gegenstände</h4>
        {items.map((item) => (
          <GegenstandRow
            key={item.id}
            campaignId={campaignId}
            personId={person.id}
            item={item}
            pcOptions={pcOptions}
            alleOptionen={alleOptionen}
            onChanged={refresh}
            onRemoved={() => removeItem(item.id)}
          />
        ))}
        <button type="button" onClick={() => setItemAnlegenOffen(true)} style={{ marginTop: 8 }}>
          + Neuer Gegenstand
        </button>
      </div>

      <Fenster
        offen={itemAnlegenOffen}
        titel="Neuer Gegenstand"
        unterzeile={itemTyp ? `Für ${person.name} · Typ: ${itemTyp}` : `Für ${person.name} — zuerst den Typ wählen`}
        kennung="charakterblatt-neuer-gegenstand"
        onSchliessen={() => {
          setItemAnlegenOffen(false);
          setItemName("");
          setItemTyp(null);
        }}
      >
        {!itemTyp ? (
          <TypKachelAuswahl onWaehlen={setItemTyp} />
        ) : (
          <form onSubmit={addItem} style={{ display: "flex", flexDirection: "column", gap: 12, padding: 8 }}>
            <span className="gg-typ-gewaehlt">
              {symbolFuerTyp(itemTyp)} {itemTyp}
              <button type="button" onClick={() => setItemTyp(null)}>
                ändern
              </button>
            </span>
            <input
              placeholder="Neuer Gegenstand"
              value={itemName}
              onChange={(e) => setItemName(e.target.value)}
              autoFocus
              required
            />
            <button type="submit">Hinzufügen</button>
          </form>
        )}
      </Fenster>
    </div>
  );
}
