import { useEffect, useState, type FormEvent } from "react";
import { entitiesApi, type Person } from "../entities/api";
import type { PersonOption } from "../entities/VisibilitySelector";
import { GegenstandRow } from "../traits/CharacterSheetPanel";
import { itemsApi, VORLAGE_SENTINEL, type GegenstandMitBesitzer } from "./api";

const VORLAGEN_GRUPPE = "__vorlagen__";

interface OwnerGroup {
  ownerId: string | null;
  ownerName: string;
  ownerPersonType: string | null;
  items: GegenstandMitBesitzer[];
}

function groupByOwner(items: GegenstandMitBesitzer[]): OwnerGroup[] {
  const groups = new Map<string, OwnerGroup>();
  for (const item of items) {
    const key = item.ownerId ?? VORLAGEN_GRUPPE;
    let group = groups.get(key);
    if (!group) {
      group = {
        ownerId: item.ownerId,
        ownerName: item.ownerName ?? "Vorlagen (kein Besitzer)",
        ownerPersonType: item.ownerPersonType,
        items: [],
      };
      groups.set(key, group);
    }
    group.items.push(item);
  }
  // Vorlagen-Gruppe zuerst anzeigen (Katalog-Charakter), danach nach Personen.
  return Array.from(groups.values()).sort((a, b) => {
    if (a.ownerId === null) return -1;
    if (b.ownerId === null) return 1;
    return a.ownerName.localeCompare(b.ownerName);
  });
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

  async function removeItem(itemId: string) {
    await itemsApi.remove(campaignId, itemId);
    await refresh();
  }

  async function addItem(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim() || !neuBesitzer) return;
    if (neuBesitzer === VORLAGE_SENTINEL) {
      await itemsApi.createVorlage(campaignId, { name: neuName });
    } else {
      await itemsApi.create(campaignId, neuBesitzer, { name: neuName });
    }
    setNeuName("");
    await refresh();
  }

  return (
    <div>
      <h2>Gegenstände</h2>
      <form onSubmit={addItem} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1.5rem" }}>
        <select value={neuBesitzer} onChange={(e) => setNeuBesitzer(e.target.value)} required>
          <option value="">Besitzer wählen...</option>
          <option value={VORLAGE_SENTINEL}>— Vorlage (kein Besitzer) —</option>
          {alleOptionen.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <input placeholder="Neuer Gegenstand" value={neuName} onChange={(e) => setNeuName(e.target.value)} />
        <button type="submit">Hinzufügen</button>
      </form>
      {groups.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Gegenstände in dieser Kampagne.</p>}
      {groups.map((group) => (
        <section key={group.ownerId ?? VORLAGEN_GRUPPE} style={{ marginBottom: "2rem" }}>
          <h3 style={{ margin: "0 0 8px", color: "var(--text)" }}>
            {group.ownerName}
            {group.ownerPersonType && <span style={{ color: "var(--text-leise)", fontWeight: "normal" }}> ({group.ownerPersonType})</span>}
          </h3>
          {group.items.map((item) => (
            <GegenstandRow
              key={item.id}
              campaignId={campaignId}
              personId={group.ownerId ?? undefined}
              item={item}
              pcOptions={pcOptions}
              alleOptionen={alleOptionen}
              onChanged={refresh}
              onRemoved={() => removeItem(item.id)}
            />
          ))}
        </section>
      ))}
    </div>
  );
}
