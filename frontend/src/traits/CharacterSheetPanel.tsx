import { useEffect, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import type { Person } from "../entities/api";
import { VisibilitySelector, type PersonOption } from "../entities/VisibilitySelector";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { EMPTY_DOC, parseRichText, serializeRichText } from "../richtext/content";
import { itemsApi, type Gegenstand } from "../items/api";
import { traitsApi, type TraitDef, type TraitRating } from "./api";
import { DotPool } from "./DotPool";

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

const TYP_OPTIONEN = ["Waffe", "Rüstung", "Cyberware", "Droge", "Verbrauchsgegenstand", "Werkzeug", "Sonstiges"];
const KRAFT_TYPEN = new Set(["Waffe", "Rüstung"]);
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
      <label style={{ fontSize: "0.85em", color: "#555" }}>
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

function GegenstandRow({
  campaignId,
  personId,
  item,
  pcOptions,
  onChanged,
  onRemoved,
}: {
  campaignId: string;
  personId: string;
  item: Gegenstand;
  pcOptions: PersonOption[];
  onChanged: () => void;
  onRemoved: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [name, setName] = useState(item.name);
  const [typ, setTyp] = useState(item.typ);
  const [preis, setPreis] = useState(item.preis);
  const [kraft, setKraft] = useState(item.kraft);
  const [eigenschaften, setEigenschaften] = useState<Eigenschaft[]>([]);
  const [zeigeInGraph, setZeigeInGraph] = useState(item.zeigeInGraph);
  const [descriptionDoc, setDescriptionDoc] = useState<JSONContent>(EMPTY_DOC);
  const [notesDoc, setNotesDoc] = useState<JSONContent>(EMPTY_DOC);
  const [sichtbarkeit, setSichtbarkeit] = useState(item.sichtbarkeit);
  const [sichtbarFuer, setSichtbarFuer] = useState(item.sichtbarFuer);
  const [uploading, setUploading] = useState(false);

  function openEdit() {
    setName(item.name);
    setTyp(item.typ);
    setPreis(item.preis);
    setKraft(item.kraft);
    setEigenschaften(recordToPairs(item.eigenschaften));
    setZeigeInGraph(item.zeigeInGraph);
    setDescriptionDoc(parseRichText(item.description));
    setNotesDoc(parseRichText(item.notes));
    setSichtbarkeit(item.sichtbarkeit);
    setSichtbarFuer(item.sichtbarFuer);
    setExpanded(true);
  }

  async function save() {
    await itemsApi.update(campaignId, personId, item.id, {
      name,
      typ,
      preis,
      kraft,
      eigenschaften: pairsToRecord(eigenschaften),
      zeigeInGraph,
      description: serializeRichText(descriptionDoc),
      notes: serializeRichText(notesDoc),
      sichtbarkeit,
      sichtbarFuer,
    });
    setExpanded(false);
    onChanged();
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await itemsApi.uploadBild(campaignId, personId, item.id, file);
      onChanged();
    } finally {
      setUploading(false);
    }
  }

  async function removeBild() {
    await itemsApi.update(campaignId, personId, item.id, { bildUrl: "" });
    onChanged();
  }

  return (
    <div style={{ borderBottom: "1px solid #eee", padding: "6px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {item.bildUrl && (
            <img src={item.bildUrl} alt="" style={{ width: 28, height: 28, objectFit: "cover", borderRadius: 4 }} />
          )}
          {item.name}
          <span style={{ fontSize: "0.75em", color: "#888" }}>
            [{item.typ}
            {item.preis > 0 && `, ${item.preis}¥`}] ({visibilityLabel(item)}){item.zeigeInGraph && " · im Graph"}
          </span>
        </span>
        <span style={{ display: "flex", gap: 6 }}>
          <button type="button" onClick={expanded ? () => setExpanded(false) : openEdit}>
            {expanded ? "Schließen" : "Bearbeiten"}
          </button>
          <button type="button" onClick={onRemoved}>
            Entfernen
          </button>
        </span>
      </div>
      {expanded && (
        <div
          style={{
            marginTop: 8,
            paddingLeft: 10,
            borderLeft: "2px solid #eee",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
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
            <label style={{ fontSize: "0.85em", color: "#555" }}>
              Preis (¥){" "}
              <input
                type="number"
                min={0}
                value={preis}
                onChange={(e) => setPreis(Number(e.target.value))}
                style={{ width: 90 }}
              />
            </label>
          </div>

          {KRAFT_TYPEN.has(typ) && (
            <div>
              <label style={{ fontSize: "0.85em", color: "#555" }}>{kraftLabel(typ)}</label>
              <div>
                <DotPool value={kraft} max={KRAFT_MAX} onChange={setKraft} />
              </div>
            </div>
          )}

          <div>
            <label style={{ fontSize: "0.85em", color: "#555" }}>Bild</label>
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
            <label style={{ fontSize: "0.85em", color: "#555" }}>Beschreibung</label>
            <RichTextEditor content={descriptionDoc} onChange={setDescriptionDoc} minHeight={60} />
          </div>
          <div>
            <label style={{ fontSize: "0.85em", color: "#555" }}>Notizen</label>
            <RichTextEditor content={notesDoc} onChange={setNotesDoc} minHeight={50} />
          </div>

          <EigenschaftenEditor pairs={eigenschaften} onChange={setEigenschaften} />

          <label style={{ fontSize: "0.9em" }}>
            <input type="checkbox" checked={zeigeInGraph} onChange={(e) => setZeigeInGraph(e.target.checked)} /> Im
            Beziehungsgraph anzeigen (für plot-relevante Gegenstände/MacGuffins)
          </label>

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
          <button type="button" onClick={save} style={{ alignSelf: "flex-start" }}>
            Speichern
          </button>
        </div>
      )}
    </div>
  );
}

export function CharacterSheetPanel({
  campaignId,
  person,
  pcOptions,
}: {
  campaignId: string;
  person: Person;
  pcOptions: PersonOption[];
}) {
  const [katalog, setKatalog] = useState<TraitDef[]>([]);
  const [werte, setWerte] = useState<TraitRating[]>([]);
  const [items, setItems] = useState<Gegenstand[]>([]);
  const [loading, setLoading] = useState(true);
  const [itemName, setItemName] = useState("");
  const [showOptions, setShowOptions] = useState(false);

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
    await itemsApi.remove(campaignId, person.id, itemId);
    await refresh();
  }

  if (loading) return <p>Lade Charakterblatt...</p>;

  const merged = mergeCatalogWithRatings(katalog, werte);
  const grouped = groupByCategory(merged);

  return (
    <div style={{ padding: 16, background: "#fff", border: "1px solid #ddd", borderRadius: 8, marginTop: 8 }}>
      <div style={{ marginBottom: 12, textAlign: "right" }}>
        <button type="button" onClick={() => setShowOptions((v) => !v)} style={{ fontSize: "0.85em" }}>
          ⚙ {showOptions ? "Optionen ausblenden" : "Optionen anzeigen"}
        </button>
      </div>

      {grouped.map(([category, traits]) => (
        <div key={category} style={{ marginBottom: 16 }}>
          <h4 style={{ margin: "0 0 8px", color: "#555" }}>{CATEGORY_LABELS[category] ?? category}</h4>
          {traits.map((t) => (
            <div
              key={t.traitDefId}
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0" }}
            >
              <span style={{ minWidth: 160 }}>{t.name}</span>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <DotPool value={t.rating} max={t.max} onChange={(v) => setRating(t, v)} />
                {showOptions && (
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
        <h4 style={{ margin: "0 0 8px", color: "#555" }}>Gegenstände</h4>
        {items.map((item) => (
          <GegenstandRow
            key={item.id}
            campaignId={campaignId}
            personId={person.id}
            item={item}
            pcOptions={pcOptions}
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
