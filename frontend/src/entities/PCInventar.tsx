import { useEffect, useState, type FormEvent } from "react";
import { itemsApi, type Gegenstand, type Ablage, ABLAGEN } from "../items/api";
import { Fenster } from "../shell/Fenster";
import "./pc-inventar.css";

/**
 * Inventar eines einzelnen PCs für das PC-Detail-Popup.
 * Zeigt alle Gegenstände des Charakters und erlaubt das Anlegen neuer.
 */

interface PCInventarProps {
  campaignId: string;
  personId: string;
  personName: string;
}

export function PCInventar({ campaignId, personId, personName }: PCInventarProps) {
  const [items, setItems] = useState<Gegenstand[]>([]);
  const [loading, setLoading] = useState(true);
  const [neuName, setNeuName] = useState("");
  const [anlegenOffen, setAnlegenOffen] = useState(false);

  async function refresh() {
    try {
      const data = await itemsApi.list(campaignId, personId);
      setItems(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [campaignId, personId]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    await itemsApi.create(campaignId, personId, {
      name: neuName.trim(),
      typ: "Sonstiges",
      description: "",
      notes: "",
      eigenschaften: {},
    });
    setNeuName("");
    setAnlegenOffen(false);
    refresh();
  }

  async function umlagern(itemId: string, ablage: Ablage) {
    await itemsApi.setAblage(campaignId, itemId, ablage);
    refresh();
  }

  // Gruppiere nach Ablage
  const nachAblage = items.reduce<Record<string, Gegenstand[]>>((acc, item) => {
    const key = item.ablage ?? "RUCKSACK";
    (acc[key] ??= []).push(item);
    return acc;
  }, {});

  const ablageNamen: Record<string, string> = {
    AUSGERUESTET: "Ausgerüstet",
    RUCKSACK: "Rucksack",
    GELAGERT: "Gelagert",
  };

  const ablageReihenfolge: Ablage[] = ["AUSGERUESTET", "RUCKSACK", "GELAGERT"];

  if (loading) {
    return <p style={{ color: "var(--text-leise)" }}>Lade Inventar…</p>;
  }

  return (
    <div className="pci-inventar">
      <div className="pci-kopf">
        <h3>Inventar von {personName}</h3>
        <button type="button" className="pci-neu-btn" onClick={() => setAnlegenOffen(true)}>
          + Gegenstand
        </button>
      </div>

      {items.length === 0 && (
        <p style={{ color: "var(--text-leise)" }}>Noch keine Gegenstände.</p>
      )}

      {ablageReihenfolge.map((ablage) => {
        const gegenstaende = nachAblage[ablage];
        if (!gegenstaende?.length) return null;
        return (
          <section key={ablage} className="pci-sektion">
            <h4 className="pci-ablage-titel">
              <span>{ablageNamen[ablage] ?? ablage}</span>
              <span className="pci-anzahl">{gegenstaende.length}</span>
            </h4>
            <div className="pci-liste">
              {gegenstaende.map((g) => (
                <div key={g.id} className="pci-item">
                  <div className="pci-item-info">
                    <span className="pci-item-name">{g.name}</span>
                    <span className="pci-item-typ">{g.typ}</span>
                  </div>
                  <select
                    value={g.ablage ?? "RUCKSACK"}
                    onChange={(e) => umlagern(g.id, e.target.value as Ablage)}
                    className="pci-ablage-select"
                  >
                    {ABLAGEN.map((a) => (
                      <option key={a.wert} value={a.wert}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </section>
        );
      })}

      {/* Neuer Gegenstand Popup */}
      <Fenster
        offen={anlegenOffen}
        titel="Neuer Gegenstand"
        unterzeile={`Für ${personName}`}
        kennung="neuer-gegenstand"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
        }}
      >
        <form onSubmit={anlegen} className="pci-form">
          <input
            type="text"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
            placeholder="Gegenstandsname"
            autoFocus
            required
          />
          <button type="submit">Anlegen</button>
        </form>
      </Fenster>
    </div>
  );
}
