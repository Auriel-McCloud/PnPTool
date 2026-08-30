import { useEffect, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import type { Person } from "../entities/api";
import { VisibilitySelector, type PersonOption } from "../entities/VisibilitySelector";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { EMPTY_DOC, parseRichText, serializeRichText } from "../richtext/content";
import { Fenster } from "../shell/Fenster";
import { ABLAGEN, itemsApi, VORLAGE_SENTINEL, type Ablage, type AblageZiel, type Gegenstand } from "../items/api";
import { traitsApi, type TraitDef, type TraitRating } from "./api";
import { DotPool } from "./DotPool";
import type { Chromstufe } from "../items/api";
import { StufenBlatt } from "./StufenBlatt";

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
// erscheinen dadurch als Ablageziel (siehe items/repository.py).
const TYP_OPTIONEN = [
  "Waffe",
  "Rüstung",
  "Cyberware",
  "Bioware",
  "Droge",
  "Verbrauchsgegenstand",
  "Werkzeug",
  "Fahrzeug",
  "Drohne",
  "Behälter",
  "Commlink",
  "Cyberdeck",
  "Riggerkonsole",
  "Sonstiges",
];
const KRAFT_TYPEN = new Set(["Waffe", "Rüstung"]);
// Steckt im Körper und kostet dauerhaft Willenskraft (Zeilen 112-117)
const CHROM_TYPEN = new Set(["Cyberware", "Bioware"]);
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
}) {
  const [expanded, setExpanded] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [name, setName] = useState(item.name);
  const [typ, setTyp] = useState(item.typ);
  const [preis, setPreis] = useState(item.preis);
  const [kraft, setKraft] = useState(item.kraft);
  const [seltenheit, setSeltenheit] = useState(item.seltenheit);
  const [eigenschaften, setEigenschaften] = useState<Eigenschaft[]>([]);
  const [zeigeInGraph, setZeigeInGraph] = useState(item.zeigeInGraph);
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
  const [chromstufen, setChromstufen] = useState<Chromstufe[]>([]);
  const [zonen, setZonen] = useState<string[]>([]);
  // Blatt für Drohne/Fahrzeug/Sprite/Geist (Neotopia.xlsx)
  const [stufe, setStufe] = useState(item.stufe);
  const [widerstand, setWiderstand] = useState(item.widerstand);
  const [angriff, setAngriff] = useState(item.angriff);
  const [agilitaet, setAgilitaet] = useState(item.agilitaet);
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

  // Der Preis hängt am Bonus: ändert er sich, stimmen die angebotenen Stufen
  // nicht mehr. Nur nachladen, solange das Formular offen ist.
  useEffect(() => {
    if (!expanded || !CHROM_TYPEN.has(typ)) return;
    itemsApi
      .chromstufen(campaignId, Math.max(1, kraft))
      .then((d) => {
        setChromstufen(d.stufen);
        setZonen(d.koerperzonen);
      })
      .catch(() => setChromstufen([]));
  }, [expanded, typ, kraft, campaignId]);

  function openEdit() {
    setName(item.name);
    setTyp(item.typ);
    setPreis(item.preis);
    setKraft(item.kraft);
    setSeltenheit(item.seltenheit);
    setEigenschaften(recordToPairs(item.eigenschaften));
    setZeigeInGraph(item.zeigeInGraph);
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
    setStufe(item.stufe);
    setWiderstand(item.widerstand);
    setAngriff(item.angriff);
    setAgilitaet(item.agilitaet);
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
    setExpanded(true);
  }

  async function save() {
    await itemsApi.update(campaignId, item.id, {
      name,
      typ,
      preis,
      kraft,
      seltenheit,
      eigenschaften: pairsToRecord(eigenschaften),
      zeigeInGraph,
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
      stufe,
      widerstand,
      angriff,
      agilitaet,
      description: serializeRichText(descriptionDoc),
      notes: serializeRichText(notesDoc),
      sichtbarkeit,
      sichtbarFuer,
    });
    setExpanded(false);
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

  async function removeBild() {
    await itemsApi.update(campaignId, item.id, { bildUrl: "" });
    onChanged();
  }

  // Das Detail öffnet als eigenes Fenster statt inline aufzuklappen: hält die
  // Übersicht statisch (Leitprinzip "nie scrollen") und gibt dem Ding eine
  // feste Größe — das alte Akkordeon riss die Karte bei langen Inhalten in
  // die Breite. Kachel wie Zeile öffnen dasselbe Fenster.
  const fenster = (
    <Fenster
      offen={expanded}
      onSchliessen={() => setExpanded(false)}
      kennung={item.id}
      titel={item.name}
      unterzeile={
        <>
          {item.typ}
          {item.preis > 0 && ` · ${item.preis}¥`} · {visibilityLabel(item)}
          {item.istVorlage && " · Vorlage"}
        </>
      }
    >
        {item.istVorlage && (
          <p style={{ fontSize: "0.85em", color: "var(--text-leise)", fontStyle: "italic", margin: 0 }}>
            📋 Vorlage — hat keinen Besitzer
          </p>
        )}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" />
          <select value={typ} onChange={(e) => setTyp(e.target.value)}>
            {!TYP_OPTIONEN.includes(typ) && <option value={typ}>{typ} (alt)</option>}
            {TYP_OPTIONEN.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
            Preis (¥){" "}
            <input
              type="number"
              min={0}
              value={preis}
              onChange={(e) => setPreis(Number(e.target.value))}
              style={{ width: 90 }}
            />
          </label>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)", display: "flex", alignItems: "center", gap: 6 }}>
            Seltenheit
            <DotPool value={seltenheit} max={5} onChange={(v) => setSeltenheit(Math.max(1, v))} size={12} />
          </label>
        </div>

        {CHROM_TYPEN.has(typ) && (
          <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
            <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
              Cyber-/Bioware: der <strong>Bonus</strong> steht oben bei Kraft. Je mehr du je
              Bonuspunkt zahlst, desto weniger Willenskraft kostet es dauerhaft (Regelblatt Zeilen
              112-117) — billiges Chrom reisst am meisten heraus.
            </label>
            <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9em" }}>
                Bonus
                <DotPool value={kraft} max={7} onChange={setKraft} />
              </label>
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
            </div>
            {/* Stufe antippen setzt Preis und Verlust zugleich — von Hand
                gerechnet vertut man sich, und die Formel steht im Server. */}
            <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 8 }}>
              {chromstufen.map((st) => {
                const gewaehlt = preis === st.preis && wVerlust === st.wVerlust;
                return (
                  <button
                    key={st.name}
                    type="button"
                    onClick={() => {
                      setPreis(st.preis);
                      setWVerlust(st.wVerlust);
                    }}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 10,
                      textAlign: "left",
                      borderColor: gewaehlt ? "var(--neon)" : undefined,
                      color: gewaehlt ? "var(--neon)" : undefined,
                    }}
                    title={st.beschreibung}
                  >
                    <span>{st.name}</span>
                    <span className="mono">
                      {st.preis.toLocaleString("de-AT")}¥ · −{st.wVerlust} Willenskraft
                    </span>
                  </button>
                );
              })}
            </div>
            <p style={{ fontSize: "0.85em", color: "var(--text-leise)", marginTop: 6 }}>
              Kostet eingebaut dauerhaft <strong>{wVerlust}</strong> Willenskraft. Wirkt erst, wenn
              der Gegenstand <em>ausgerüstet</em> ist — im Rucksack ist er noch nicht verbaut.
            </p>
          </div>
        )}

        {typ === "Riggerkonsole" && (
          <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
            <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
              Riggerkonsole (Regelblatt Zeilen 158-167). Der Bonus darf negativ sein — eine
              zusammengeschraubte Konsole macht das Steuern schwerer.
            </label>
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

        {FAHRZEUG_TYPEN.has(typ) && (
          <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
            <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
              Werte (Neotopia-Blatt „Drohne/Fahrzeug"): die Stufe wird beim Kauf frei auf Widerstand,
              Angriff und Agilität verteilt. Gesundheit = Stufe, Widerstand = Schadensreduktion,
              Agilität = Geschwindigkeit.
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

        <div>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Bild</label>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {item.bildUrl && <img src={item.bildUrl} alt="" style={{ width: 64, height: 64, objectFit: "cover", borderRadius: 4 }} />}
            <input type="file" accept="image/*" onChange={handleFile} disabled={uploading} />
            {uploading && <span style={{ fontSize: "0.85em" }}>lädt hoch...</span>}
            {item.bildUrl && (
              <button type="button" onClick={removeBild}>
                Bild entfernen
              </button>
            )}
          </div>
        </div>

        <div>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Beschreibung</label>
          <RichTextEditor content={descriptionDoc} onChange={setDescriptionDoc} minHeight={60} />
        </div>
        <div>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Notizen</label>
          <RichTextEditor content={notesDoc} onChange={setNotesDoc} minHeight={50} />
        </div>

        <EigenschaftenEditor pairs={eigenschaften} onChange={setEigenschaften} />

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

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ color: "var(--text-leise)" }}>Aufbewahrung</span>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {ABLAGEN.map((a) => (
              <button
                key={a.wert}
                type="button"
                onClick={() => setAblage(a.wert)}
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
            <select value={ablageZiel} onChange={(e) => setAblageZiel(e.target.value)}>
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
              <label style={{ fontSize: "0.9em", minWidth: 0, overflowWrap: "break-word" }}>
                <input type="checkbox" checked={zeigeInGraph} onChange={(e) => setZeigeInGraph(e.target.checked)} />{" "}
                Im Beziehungsgraph anzeigen (für plot-relevante Gegenstände/MacGuffins)
              </label>
              <label style={{ fontSize: "0.9em", minWidth: 0, overflowWrap: "break-word" }}>
                <input type="checkbox" checked={einzigartig} onChange={(e) => setEinzigartig(e.target.checked)} />{" "}
                Einzigartig (genau ein Exemplar in der Welt, z.B. das Amulett)
              </label>
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <label style={{ fontSize: "0.9em", flex: "1 1 240px", minWidth: 0, overflowWrap: "break-word" }}>
                  <input type="checkbox" checked={hatMenge} onChange={(e) => setHatMenge(e.target.checked)} /> Menge
                  verfolgen
                </label>
                {hatMenge && (
                  <input
                    type="number"
                    min={0}
                    value={menge}
                    onChange={(e) => setMenge(Number(e.target.value))}
                    style={{ width: 70, flex: "0 0 auto" }}
                  />
                )}
              </div>
              <label style={{ fontSize: "0.9em", minWidth: 0, overflowWrap: "break-word" }}>
                <input
                  type="checkbox"
                  checked={immerSichtbar}
                  onChange={(e) => setImmerSichtbar(e.target.checked)}
                />{" "}
                Fällt am Körper auf — ein Sturmgewehr sieht jeder, ein Messer im Stiefel nicht
              </label>
              {/* Nicht aus dem Typ geraten: ein Motorrad ist ein Fahrzeug
                  ohne Stauraum, eine Kiste hat Stauraum ohne Räder. */}
              <label style={{ fontSize: "0.9em", minWidth: 0, overflowWrap: "break-word" }}>
                <input
                  type="checkbox"
                  checked={istBehaelter}
                  onChange={(e) => setIstBehaelter(e.target.checked)}
                />{" "}
                Kann etwas aufnehmen — dann lässt sich hier etwas hineinlegen und der Gegenstand
                erscheint als Fach im Inventar
              </label>
              <label style={{ fontSize: "0.9em", minWidth: 0, overflowWrap: "break-word" }}>
                <input
                  type="checkbox"
                  checked={automatischImShop}
                  onChange={(e) => setAutomatischImShop(e.target.checked)}
                />{" "}
                Automatisch in Shops gleicher Seltenheitsstufe verfügbar (wirkt sich erst aus, sobald es Shops
                gibt — noch nicht gebaut)
              </label>
            </div>
          )}
        </div>

        {!item.istVorlage && (
          <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
            {/* Wem er gehoert, stand bisher nirgends im Formular. In der
                kampagnenweiten Uebersicht ist die Besitzer-Ueberschrift oft
                weggescrollt — und weil die Auswahl unten den aktuellen
                Besitzer ausblendet, sah es aus, als liesse sich ein
                Gegenstand keinem PC geben, obwohl er dem PC schon gehoert. */}
            <div style={{ fontSize: "0.85em", marginBottom: 6 }}>
              <span style={{ color: "var(--text-leise)" }}>Gehört </span>
              <strong style={{ color: "var(--neon)" }}>
                {alleOptionen.find((p) => p.id === personId)?.name ?? "niemandem"}
              </strong>
            </div>
            <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
              An jemand anderen übergeben (verschiebt diesen Gegenstand, erstellt keine Kopie)
            </label>
            <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
              <select
                value={besitzerZiel}
                onChange={(e) => setBesitzerZiel(e.target.value)}
                style={{ minWidth: 0, maxWidth: "100%" }}
              >
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
            // Einzigartige/MacGuffin-Vorlagen dürfen nicht vervielfältigt
            // werden — Zuweisen übergibt dann den Gegenstand selbst
            // (verschiebt ihn, wie Besitzer wechseln), statt eine Kopie zu
            // erzeugen. Das Backend entscheidet dasselbe anhand des
            // GESPEICHERTEN Stands (item.*, nicht den lokalen Edit-State) —
            // die Zuweisen-Aktion wirkt ja auf den gespeicherten Gegenstand.
            const keineKopie = item.einzigartig || item.zeigeInGraph;
            return (
              <div style={{ borderTop: "1px solid var(--linie)", paddingTop: 8 }}>
                <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                  {keineKopie
                    ? "Diesem Gegenstand zuweisen (übergibt den Gegenstand selbst — einzigartig/MacGuffin, keine Kopie möglich)"
                    : "Diesem Gegenstand zuweisen (erstellt eine Kopie)"}
                </label>
                <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
                  <select
                    value={zuweisenZiel}
                    onChange={(e) => setZuweisenZiel(e.target.value)}
                    style={{ minWidth: 0, maxWidth: "100%" }}
                  >
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

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <button type="button" onClick={save}>
          Speichern
        </button>
        {/* In der Kacheldarstellung gibt es keine Zeile mehr, an der ein
            Entfernen-Knopf haengen koennte — und hier ist er ohnehin besser
            aufgehoben, weil man den Gegenstand dabei vor sich sieht. */}
        <button
          type="button"
          onClick={onRemoved}
          style={{ marginLeft: "auto", borderColor: "var(--signal)", color: "var(--signal)" }}
        >
          Entfernen
        </button>
      </div>
    </Fenster>
  );

  if (kachel) {
    return (
      <>
        <button type="button" className="gg-kachel" onClick={openEdit} title={item.name}>
          <span className="gg-kachel-bild">
            {item.bildUrl ? <img src={item.bildUrl} alt="" /> : <span aria-hidden="true">◈</span>}
            {item.hatMenge && <span className="gg-kachel-menge">×{item.menge}</span>}
          </span>
          <span className="gg-kachel-name">{item.name}</span>
          <span className="gg-kachel-zeile">
            {item.typ}
            {item.preis > 0 && ` · ${item.preis}¥`}
            {item.gewicht > 0 && ` · ${item.gewicht} kg`}
          </span>
          <span className="gg-kachel-marken">
            {item.sichtbarkeit === "GM" && <span className="gg-marke" data-ton="signal">SL</span>}
            {item.zeigeInGraph && <span className="gg-marke" data-ton="neon">Graph</span>}
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
          {item.name}
          {item.hatMenge && <strong>×{item.menge}</strong>}
          <span style={{ fontSize: "0.75em", color: "var(--text-leise)" }}>
            [{item.typ}
            {item.preis > 0 && `, ${item.preis}¥`}] ({visibilityLabel(item)}){item.zeigeInGraph && " · im Graph"}
            {item.istVorlage && " · Vorlage"}
          </span>
        </span>
        <span style={{ display: "flex", gap: 6 }}>
          <button type="button" onClick={openEdit}>
            Bearbeiten
          </button>
          <button type="button" onClick={onRemoved}>
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
    const maxOverride = t.max !== t.defaultMax ? t.max : null;
    await traitsApi.setWert(campaignId, person.id, t.traitDefId, clamped, maxOverride);
    await refresh();
  }

  async function adjustMax(t: MergedTrait, delta: number) {
    const newMax = Math.max(1, t.max + delta);
    const newRating = Math.min(t.rating, newMax);
    const maxOverride = newMax !== t.defaultMax ? newMax : null;
    await traitsApi.setWert(campaignId, person.id, t.traitDefId, newRating, maxOverride);
    await refresh();
  }

  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!itemName.trim()) return;
    await itemsApi.create(campaignId, person.id, { name: itemName });
    setItemName("");
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
        <form onSubmit={addItem} style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <input placeholder="Neuer Gegenstand" value={itemName} onChange={(e) => setItemName(e.target.value)} />
          <button type="submit">Hinzufügen</button>
        </form>
      </div>
    </div>
  );
}
