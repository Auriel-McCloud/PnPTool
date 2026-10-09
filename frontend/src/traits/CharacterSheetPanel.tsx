import { useEffect, useState, type FormEvent } from "react";
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
import { ABLAGEN, itemsApi, VORLAGE_SENTINEL, type Ablage, type AblageZiel, type Gegenstand } from "../items/api";
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
import { RuestungReparatur } from "../kampf/RuestungReparatur";
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
const KRAFT_TYPEN = new Set(["Waffe", "Rüstung"]);
// Steckt im Körper und kostet dauerhaft Willenskraft (Zeilen 112-117).
// Hexware läuft über dieselbe Formel — reine Flavor-Kategorie neben
// Cyberware/Bioware, keine eigene Kostenmechanik (Mark, 02.09.2026).
const CHROM_TYPEN = new Set(["Cyberware", "Bioware", "Hexware"]);
// Drei Plätze je Körperzone (Regelblatt: "je drei Plätze mit Bonus und Verlust").
const SLOTS_PRO_ZONE = [1, 2, 3];
// Bekommen ein eigenes Blatt (Stufe, Widerstand, Angriff, Agilität)
const FAHRZEUG_TYPEN = new Set(["Fahrzeug", "Drohne"]);
const KRAFT_MAX = 7; // wie Waffenschaden-/Rüstungsbonus-Skala im Regeln-Sheet

function kraftLabel(typ: string): string {
  return typ === "Rüstung" ? "Rüstungsbonus" : "Schadensbonus";
}

type Eigenschaft = { key: string; value: string };

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
  const [wVerlust, setWVerlust] = useState(item.wVerlust);
  const [koerperzone, setKoerperzone] = useState(item.koerperzone);
  const [slot, setSlot] = useState<number | null>(item.slot);
  const [istWaffe, setIstWaffe] = useState(item.istWaffe);
  const [schaden, setSchaden] = useState(item.schaden);
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
  const [ablageZiel, setAblageZiel] = useState<string>(item.ablageZielId ?? "");
  const [ziele, setZiele] = useState<AblageZiel[]>([]);
  const [descriptionDoc, setDescriptionDoc] = useState<JSONContent>(EMPTY_DOC);
  const [notesDoc, setNotesDoc] = useState<JSONContent>(EMPTY_DOC);
  const [sichtbarkeit, setSichtbarkeit] = useState(item.sichtbarkeit);
  const [sichtbarFuer, setSichtbarFuer] = useState(item.sichtbarFuer);
  const [uploading, setUploading] = useState(false);
  const [zuweisenZiel, setZuweisenZiel] = useState("");
  const [zuweisenLaeuft, setZuweisenLaeuft] = useState(false);
  const [besitzerZiel, setBesitzerZiel] = useState("");
  const [besitzerLaeuft, setBesitzerLaeuft] = useState(false);
  const [kiBildOffen, setKiBildOffen] = useState(false);

  // Summe aller Boni für Chrom-Preisberechnung:
  // traitBoni (Attribute/Fertigkeiten) + ausruestungsfertigkeiten + schaden
  const traitBoniSumme = traitBoni.reduce((sum, b) => sum + (Number(b.value) || 0), 0);
  const ausrFertSumme = ausruestungsfertigkeiten.reduce((sum, b) => sum + (Number(b.value) || 0), 0);
  const waffenSchaden = istWaffe ? schaden : 0;
  const gesamtBonus = traitBoniSumme + ausrFertSumme + waffenSchaden;

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

  // Wenn sich Boni oder die gewählte Stufe ändert, Preis/WK-Verlust neu berechnen
  useEffect(() => {
    if (!expanded || !CHROM_TYPEN.has(typ) || gewaehlteChromstufe === null) return;
    const stufe = chromstufen.find((s) => s.preisJeBonus === gewaehlteChromstufe);
    if (stufe) {
      const bonus = Math.max(1, gesamtBonus);
      setPreis(bonus * gewaehlteChromstufe);
      setWVerlust(stufe.wVerlustGenau * bonus);
      setKraft(bonus);
    }
  }, [traitBoni, ausruestungsfertigkeiten, schaden, istWaffe, gewaehlteChromstufe, gesamtBonus, chromstufen, expanded, typ]);

  // Katalog fürs Trait-Boni-Dropdown — nur laden, wenn das Formular offen
  // ist und Boni überhaupt angezeigt werden können.
  useEffect(() => {
    if (!expanded) return;
    traitsApi.getKatalog(campaignId).then(setTraitKatalog).catch(() => setTraitKatalog([]));
  }, [expanded, campaignId]);

  function openEdit() {
    setName(item.name);
    setTyp(item.typ);
    setPreis(item.preis);
    setKraft(item.kraft);
    setSeltenheit(item.seltenheit);
    setEigenschaften(recordToPairs(item.eigenschaften));
    setStoryRelevant(item.storyRelevant);
    setEinzigartig(item.einzigartig);
    setHatMenge(item.hatMenge);
    setMenge(item.menge);
    setAutomatischImShop(item.automatischImShop);
    setAblage(item.ablage);
    setGewicht(item.gewicht);
    setKapazitaet(item.kapazitaet);
    setIstBehaelter(item.istBehaelter);
    setImmerSichtbar(item.immerSichtbar);
    setRiggerBonus(item.riggerBonus);
    setMaxDrohnen(item.maxDrohnen);
    setWVerlust(item.wVerlust);
    setKoerperzone(item.koerperzone);
    setSlot(item.slot);
    setIstWaffe(item.istWaffe);
    setSchaden(item.schaden);
    setTraitBoni(
      Object.entries(item.traitBoni).map(([key, value]) => ({ key, value: String(value) })),
    );
    setAusruestungsfertigkeiten(
      Object.entries(item.ausruestungsfertigkeiten).map(([key, value]) => ({ key, value: String(value) })),
    );
    setStufe(item.stufe);
    setWiderstand(item.widerstand);
    setAngriff(item.angriff);
    setAgilitaet(item.agilitaet);
    setRuestungKaestchenMax(item.ruestungKaestchenMax);
    setRuestungReduktionBasis(item.ruestungReduktionBasis);
    setIstReparaturmaterial(item.istReparaturmaterial);
    setReparaturKapazitaet(item.reparaturKapazitaet);
    setAblageZiel(item.ablageZielId ?? "");
    // Ziele erst beim Öffnen holen — für jede Kachel im Voraus wäre es eine
    // Abfrage pro Gegenstand, nur damit ein Auswahlfeld gefüllt ist.
    itemsApi.ablageziele(campaignId, item.id).then(setZiele).catch(() => setZiele([]));
    // Preisstufen fürs Chrom — erst beim Öffnen, und nur wenn es eines ist.
    if (CHROM_TYPEN.has(item.typ)) {
      itemsApi
        .chromstufen(campaignId, Math.max(1, item.kraft))
        .then((d) => {
          setChromstufen(d.stufen);
          setZonen(d.koerperzonen);
        })
        .catch(() => setChromstufen([]));
    }
    setDescriptionDoc(parseRichText(item.description));
    setNotesDoc(parseRichText(item.notes));
    setSichtbarkeit(item.sichtbarkeit);
    setSichtbarFuer(item.sichtbarFuer);
    setAnsicht("uebersicht");
    setExpanded(true);
  }

  useEffect(() => {
    if (nurFenster) openEdit();
    // Nur beim Öffnen aus der Ideenschmiede — openEdit liest `item` vom ersten Render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function fensterZu() {
    setExpanded(false);
    onFensterSchliessen?.();
  }

  async function nameSpeichern() {
    const sauber = name.trim();
    if (!sauber) {
      setName(item.name);
      return;
    }
    if (sauber !== item.name) await itemsApi.update(campaignId, item.id, { name: sauber });
  }

  async function ablageSetzen(wert: Ablage, zielId?: string | null) {
    setAblage(wert);
    if (wert !== "GELAGERT") setAblageZiel("");
    const ziel = wert === "GELAGERT" ? (zielId !== undefined ? zielId : ablageZiel || null) : null;
    try {
      await itemsApi.setAblage(campaignId, item.id, wert, ziel);
    } catch {
      setAblage(item.ablage);
      setAblageZiel(item.ablageZielId ?? "");
    }
  }

  async function save() {
    await itemsApi.update(campaignId, item.id, {
      name,
      preis,
      kraft,
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
      wVerlust,
      koerperzone,
      slot,
      istWaffe,
      schaden,
      traitBoni: Object.fromEntries(
        traitBoni.filter((p) => p.key.trim() && Number(p.value)).map((p) => [p.key.trim(), Number(p.value)]),
      ),
      ausruestungsfertigkeiten: Object.fromEntries(
        ausruestungsfertigkeiten
          .filter((p) => p.key.trim() && Number(p.value))
          .map((p) => [p.key.trim(), Number(p.value)]),
      ),
      stufe,
      widerstand,
      angriff,
      agilitaet,
      ruestungKaestchenMax,
      ruestungReduktionBasis,
      istReparaturmaterial,
      reparaturKapazitaet,
      description: serializeRichText(descriptionDoc),
      notes: serializeRichText(notesDoc),
      sichtbarkeit,
      sichtbarFuer,
    });
    onChanged();
  }

  // Nur SL (Button ist ohnehin istGm-gated, aber der Endpunkt selbst ist
  // zusätzlich per require_campaign_gm abgesichert — doppelt hält besser).
  async function typAendern(neuerTyp: string) {
    setTypAendernOffen(false);
    await itemsApi.update(campaignId, item.id, { typ: neuerTyp });
    setTyp(neuerTyp);
    onChanged();
  }

  async function zuweisen() {
    if (!zuweisenZiel) return;
    setZuweisenLaeuft(true);
    try {
      await itemsApi.assign(campaignId, item.id, zuweisenZiel);
      setZuweisenZiel("");
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

  // Autosave nur für Beschreibung/Notizen (Mark, 27.09.2026: der Rest des
  // Formulars bleibt hinter dem bestehenden "Speichern"-Knopf) — eigenes
  // PATCH statt des großen save(), damit ein Autosave-Tick nicht versehentlich
  // noch unfertige Werte in anderen Feldern mit wegschreibt.
  // Still: kein onChanged/refresh, sonst unmountet das Fenster (siehe autosave.ts).
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
                    {KRAFT_TYPEN.has(typ) && (
                      <li>
                        {kraftLabel(typ)}: {kraft}
                      </li>
                    )}
                    {(typ === "Waffe" || istWaffe) && <li>Schaden: {schaden}</li>}
                    {typ === "Rüstung" && (
                      <li>
                        Rüstung: {item.ruestungKaestchenAktuell}/{ruestungKaestchenMax} Kästchen, Reduktion{" "}
                        {ruestungReduktionBasis}
                      </li>
                    )}
                    {CHROM_TYPEN.has(typ) && (
                      <li>
                        {koerperzone ? `${koerperzone}${slot ? ` Platz ${slot}` : ""}` : "keine Zone"}
                        {wVerlust > 0 && ` · −${wVerlust.toLocaleString("de-AT")} Willenskraft`}
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
                Hier ändert sich, was das Ding tut. Speichern, wenn der Umbau sitzt.
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
                      <input type="checkbox" checked={istWaffe} onChange={(e) => setIstWaffe(e.target.checked)} />
                      zählt zusätzlich als Waffe
                    </label>
                    {istWaffe && (
                      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                        Schaden
                        <DotPool value={schaden} max={7} onChange={setSchaden} />
                      </label>
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

                <label style={{ fontSize: "0.85em", color: "var(--text-leise)", display: "block", marginTop: 12 }}>
                  Ausrüstungsfertigkeiten (neue Fertigkeiten NUR durch diesen Gegenstand)
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

              {KRAFT_TYPEN.has(typ) && (
                <div>
                  <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>{kraftLabel(typ)}</label>
                  <div>
                    <DotPool value={kraft} max={KRAFT_MAX} onChange={setKraft} />
                  </div>
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
                  {personId &&
                    item.ruestungKaestchenMax > 0 &&
                    item.ruestungKaestchenAktuell < item.ruestungKaestchenMax && (
                      <RuestungReparatur campaignId={campaignId} personId={personId} item={item} onChanged={onChanged} />
                    )}
                </div>
              )}

              <EigenschaftenEditor pairs={eigenschaften} onChange={setEigenschaften} />

              <button type="button" onClick={save}>
                Umbau speichern
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
                      <input type="checkbox" checked={einzigartig} onChange={(e) => setEinzigartig(e.target.checked)} />{" "}
                      Einzigartig
                    </label>
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
                          ? "Diesem Gegenstand zuweisen (übergibt den Gegenstand selbst)"
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
                        <button type="button" onClick={zuweisen} disabled={!zuweisenZiel || zuweisenLaeuft}>
                          {zuweisenLaeuft ? "..." : keineKopie ? "Übergeben" : "Kopie erstellen"}
                        </button>
                      </div>
                    </div>
                  );
                })()}

              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <button type="button" onClick={save}>
                  Besitz speichern
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
