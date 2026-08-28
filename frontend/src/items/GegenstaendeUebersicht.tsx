import { useEffect, useState, type FormEvent } from "react";
import { entitiesApi, type Person } from "../entities/api";
import type { PersonOption } from "../entities/VisibilitySelector";
import { GegenstandRow } from "../traits/CharacterSheetPanel";
import { itemsApi, type GegenstandMitBesitzer } from "./api";

interface OwnerGroup {
  ownerId: string;
  ownerName: string;
  ownerPersonType: string;
  items: GegenstandMitBesitzer[];
}

function groupByOwner(items: GegenstandMitBesitzer[]): OwnerGroup[] {
  const groups = new Map<string, OwnerGroup>();
  for (const item of items) {
    let group = groups.get(item.ownerId);
    if (!group) {
      group = { ownerId: item.ownerId, ownerName: item.ownerName, ownerPersonType: item.ownerPersonType, items: [] };
      groups.set(item.ownerId, group);
    }
    group.items.push(item);
  }
  return Array.from(groups.values());
}

export function GegenstaendeUebersicht({ campaignId }: { campaignId: string }) {
  const [personen, setPersonen] = useState<Person[]>([]);
  const [items, setItems] = useState<GegenstandMitBesitzer[]>([]);
  const [loading, setLoading] = useState(true);
  const [neuName, setNeuName] = useState("");
  const [neuBesitzer, setNeuBesitzer] = useState("");

  async function refresh() {
    const [p, i] = await Promise.all([entitiesApi.listPersonen(campaignId), itemsApi.listAlle(campaignId)]);
    setPersonen(p);
    setItems(i);
  }

  useEffect(() => {
    setLoading(true);
    refresh().finally(() => setLoading(false));
  }, [campaignId]);

  if (loading) return <p>Lade Gegenstände...</p>;

  const pcOptions: PersonOption[] = personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name }));
  const alleOptionen: PersonOption[] = personen.map((p) => ({ id: p.id, name: `${p.name} (${p.personType})` }));
  const groups = groupByOwner(items);

  async function removeItem(ownerId: string, itemId: string) {
    await itemsApi.remove(campaignId, ownerId, itemId);
    await refresh();
  }

  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim() || !neuBesitzer) return;
    await itemsApi.create(campaignId, neuBesitzer, { name: neuName });
    setNeuName("");
    await refresh();
  }

  return (
    <div>
      <h2>Gegenstände</h2>
      <form onSubmit={addItem} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1.5rem" }}>
        <select value={neuBesitzer} onChange={(e) => setNeuBesitzer(e.target.value)} required>
          <option value="">Besitzer wählen...</option>
          {alleOptionen.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <input placeholder="Neuer Gegenstand" value={neuName} onChange={(e) => setNeuName(e.target.value)} />
        <button type="submit">Hinzufügen</button>
      </form>
      {groups.length === 0 && <p style={{ color: "#888" }}>Noch keine Gegenstände in dieser Kampagne.</p>}
      {groups.map((group) => (
        <section key={group.ownerId} style={{ marginBottom: "2rem" }}>
          <h3 style={{ margin: "0 0 8px", color: "#333" }}>
            {group.ownerName} <span style={{ color: "#888", fontWeight: "normal" }}>({group.ownerPersonType})</span>
          </h3>
          {group.items.map((item) => (
            <GegenstandRow
              key={item.id}
              campaignId={campaignId}
              personId={group.ownerId}
              item={item}
              pcOptions={pcOptions}
              alleOptionen={alleOptionen}
              onChanged={refresh}
              onRemoved={() => removeItem(group.ownerId, item.id)}
            />
          ))}
        </section>
      ))}
    </div>
  );
}
