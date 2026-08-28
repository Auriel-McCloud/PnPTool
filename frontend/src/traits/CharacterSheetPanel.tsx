import { useEffect, useState, type FormEvent } from "react";
import type { Person } from "../entities/api";
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

export function CharacterSheetPanel({ campaignId, person }: { campaignId: string; person: Person }) {
  const [katalog, setKatalog] = useState<TraitDef[]>([]);
  const [werte, setWerte] = useState<TraitRating[]>([]);
  const [items, setItems] = useState<Gegenstand[]>([]);
  const [loading, setLoading] = useState(true);
  const [itemName, setItemName] = useState("");

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
              </div>
            </div>
          ))}
        </div>
      ))}

      <div>
        <h4 style={{ margin: "0 0 8px", color: "#555" }}>Gegenstände</h4>
        {items.map((item) => (
          <div key={item.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0" }}>
            <span>
              {item.name}
              <span style={{ marginLeft: 8, fontSize: "0.75em", color: "#888" }}>
                (
                {item.sichtbarkeit === "GM"
                  ? "SL-geheim"
                  : item.sichtbarkeit === "ALLE"
                    ? "für alle sichtbar"
                    : "nur Besitzer sichtbar"}
                )
              </span>
            </span>
            <button type="button" onClick={() => removeItem(item.id)}>
              Entfernen
            </button>
          </div>
        ))}
        <form onSubmit={addItem} style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <input placeholder="Neuer Gegenstand" value={itemName} onChange={(e) => setItemName(e.target.value)} />
          <button type="submit">Hinzufügen</button>
        </form>
      </div>
    </div>
  );
}
