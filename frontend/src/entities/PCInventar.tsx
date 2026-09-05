import { useEffect, useState, type FormEvent } from "react";
import { itemsApi, type Gegenstand, type Ablage } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { GegenstandKachel } from "../items/GegenstandKachel";
import "./pc-inventar.css";

/**
 * Inventar eines einzelnen PCs für das PC-Detail-Popup.
 * Zeigt alle Gegenstände des Charakters mit klickbaren Kacheln.
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

  async function wegwerfen(itemId: string) {
    await itemsApi.wegwerfen(campaignId, itemId);
    refresh();
  }

  // Trenne verbaute Augments von normalen Gegenständen
  const verbaute = items.filter((i) => i.verbaut);
  const nichtVerbaut = items.filter((i) => !i.verbaut);

  // Gruppiere nicht-verbaute nach Ablage
  const nachAblage = nichtVerbaut.reduce<Record<string, Gegenstand[]>>((acc, item) => {
    const key = item.ablage ?? "RUCKSACK";
    (acc[key] ??= []).push(item);
    return acc;
  }, {});

  const ablageNamen: Record<string, string> = {
    VERBAUT: "Verbaut",
    AUSGERUESTET: "Ausgerüstet",
    RUCKSACK: "Rucksack",
    GELAGERT: "Gelagert",
  };

  const ablageReihenfolge: Ablage[] = ["AUSGERUESTET", "RUCKSACK", "GELAGERT"];

  // Finde Behälter (Rucksack etc.) für Label
  const behaelter = items.find(
    (i) => i.typ === "Behälter" && i.ablage === "AUSGERUESTET"
  );

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

      {/* Verbaute Augments zuerst, mit eigener Markierung */}
      {verbaute.length > 0 && (
        <section className="pci-sektion pci-verbaut">
          <h4 className="pci-ablage-titel">
            <span>🔩 Verbaut</span>
            <span className="pci-anzahl">{verbaute.length}</span>
          </h4>
          <div className="pci-kachel-liste">
            {verbaute.map((g) => (
              <GegenstandKachel
                key={g.id}
                item={g}
                // Verbaute Augments können nicht umgelagert werden
              />
            ))}
          </div>
        </section>
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
            <div className="pci-kachel-liste">
              {gegenstaende.map((g) => (
                <GegenstandKachel
                  key={g.id}
                  item={g}
                  behaelterName={behaelter?.name}
                  behaelterId={behaelter?.id}
                  onUmlegen={(neueAblage) => umlagern(g.id, neueAblage)}
                  onWegwerfen={() => wegwerfen(g.id)}
                />
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
