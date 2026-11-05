import { useEffect, useState, type FormEvent } from "react";
import { itemsApi, type Gegenstand, type Ablage } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { GegenstandKachel } from "../items/GegenstandKachel";
import { TypKachelAuswahl } from "../items/TypKachelAuswahl";
import { symbolFuerTyp } from "../items/typKatalog";
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
  const [neuTyp, setNeuTyp] = useState<string | null>(null);
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
    if (!neuName.trim() || !neuTyp) return;
    await itemsApi.create(campaignId, personId, {
      name: neuName.trim(),
      typ: neuTyp,
      description: "",
      notes: "",
      eigenschaften: {},
    });
    setNeuName("");
    setNeuTyp(null);
    setAnlegenOffen(false);
    refresh();
  }

  async function umlagern(itemId: string, ablage: Ablage, zielId?: string | null) {
    await itemsApi.setAblage(campaignId, itemId, ablage, zielId ?? null);
    refresh();
  }

  async function wegwerfen(itemId: string) {
    await itemsApi.wegwerfen(campaignId, itemId);
    refresh();
  }

  // Trenne verbaute Augments von normalen Gegenständen. Montierte
  // Werkbank-Augments (Zielfernrohr, Ki-Tama & Co.) stecken an ihrem
  // Trägergegenstand (MONTIERT_AN) und tauchen dort schon als "montierte
  // Upgrades" auf, bekommen hier aber zusätzlich eine EIGENE Sektion —
  // vorher fielen sie komplett aus der Ablage-Gruppierung heraus und waren
  // für die SL nirgends mehr anklickbar (Mark-Bugreport 31.10.2026: "wenn
  // Ki-Tamas oder Waffen-Upgrades verbaut sind, kann ich sie als SL auch
  // nicht mehr sehen" — er will sie weiterhin öffnen können, nur mit einem
  // Fähnchen, dass sie gerade verbaut sind).
  const verbaute = items.filter((i) => i.verbaut);
  const montierte = items.filter((i) => i.montiertAnId && !i.verbaut);

  // Körperteil (04.11.2026, Mark nach dem Wachmann-Bugreport): `istNatuerlich`
  // an Rüstung/Ki-Tama (Dug'Rah-Chitin & Co.) ist IMMER Körperteil, bleibt
  // jetzt dauerhaft `ablage=AUSGERUESTET` (siehe kampf/ruestung.py::
  // reihenfolge, traits/routes.py::ruestungstreffer) und landete deshalb
  // unsichtbar vermischt in der normalen "Ausgerüstet"-Sektion zwischen
  // Waffen und Kleidung. Eigene Sektion, damit die SL auf einen Blick sieht,
  // was wirklich abnehmbar ist und was Körperteil. Chrom-Typen (Cyberware/
  // Bioware/Hexware) NICHT hier mit rein, solange sie `verbaut=false` sind —
  // vor der Chirurgie ist so ein Stück noch ein ganz normaler, loser
  // Gegenstand im Rucksack, kein Körperteil (erst mit `verbaut=true` wandert
  // es ohnehin automatisch in die "Verbaut"-Sektion oben).
  const CHROM_TYPEN = new Set(["Cyberware", "Bioware", "Hexware"]);
  const koerperteile = items.filter(
    (i) => i.istNatuerlich && !i.verbaut && !i.montiertAnId && !CHROM_TYPEN.has(i.typ),
  );
  const koerperteilIds = new Set(koerperteile.map((i) => i.id));
  const nichtVerbaut = items.filter((i) => !i.verbaut && !i.montiertAnId && !koerperteilIds.has(i.id));

  // Gruppiere nicht-verbaute nach Ablage
  const nachAblage = nichtVerbaut.reduce<Record<string, Gegenstand[]>>((acc, item) => {
    const key = item.ablage ?? "RUCKSACK";
    (acc[key] ??= []).push(item);
    return acc;
  }, {});

  // "Rucksack" ist seit 31.10.2026 projektweit umbenannt auf "Mitgeführt" —
  // der Reiter meint "kein bestimmter Behälter" (Symbol ▣), nicht den
  // Behälter, den die Person zufällig trägt (z.B. Wachmanns Drop-Leg Bag,
  // der sein eigenes GELAGERT-Fach hat). GegenstandKachel.tsx::grundAblagen
  // und items/aufbewahrung.ts tragen das schon so; dieses Popup hatte eine
  // eigene, nie nachgezogene Kopie (Mark-Bugreport 04.11.2026: "er besitzt
  // keinen Rucksack, er hat einen Drop-Leg Bag Behälter, und da ist nichts
  // drinnen" — Items standen im neutralen Mitgeführt-Topf, nicht im Behälter).
  const ablageNamen: Record<string, string> = {
    VERBAUT: "Verbaut",
    AUSGERUESTET: "Ausgerüstet",
    RUCKSACK: "Mitgeführt",
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
                montierteUpgrades={items.filter((i) => i.montiertAnId === g.id).map((i) => i.name)}
                // Verbaute Augments können nicht umgelagert werden
              />
            ))}
          </div>
        </section>
      )}

      {/* Körperteil: natürliche Rüstung/Ki-Tama, immer ausgerüstet, nie
          "ablegbar" — eigene Sektion statt vermischt mit echter Kleidung. */}
      {koerperteile.length > 0 && (
        <section className="pci-sektion pci-verbaut">
          <h4 className="pci-ablage-titel">
            <span>🧬 Körperteil</span>
            <span className="pci-anzahl">{koerperteile.length}</span>
          </h4>
          <div className="pci-kachel-liste">
            {koerperteile.map((g) => (
              <GegenstandKachel key={g.id} item={g} />
            ))}
          </div>
        </section>
      )}

      {/* Montierte Upgrades (Ki-Tama, Zielfernrohr & Co.): eigene, weiterhin
          anklickbare Sektion statt komplett unsichtbar — die Kachel selbst
          zeigt zusätzlich das Fähnchen "Montiert an …". */}
      {montierte.length > 0 && (
        <section className="pci-sektion pci-verbaut">
          <h4 className="pci-ablage-titel">
            <span>🔩 Montierte Upgrades</span>
            <span className="pci-anzahl">{montierte.length}</span>
          </h4>
          <div className="pci-kachel-liste">
            {montierte.map((g) => (
              <GegenstandKachel key={g.id} item={g} />
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
                  campaignId={campaignId}
                  onGeoeffnet={() => void refresh()}
                  onUmlegen={(neueAblage, zielId) => umlagern(g.id, neueAblage, zielId)}
                  onWegwerfen={() => wegwerfen(g.id)}
                  montierteUpgrades={items.filter((i) => i.montiertAnId === g.id).map((i) => i.name)}
                  istSpielleitung
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
        unterzeile={neuTyp ? `Für ${personName} · Typ: ${neuTyp}` : `Für ${personName} — zuerst den Typ wählen`}
        kennung="neuer-gegenstand"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
          setNeuTyp(null);
        }}
      >
        {!neuTyp ? (
          <TypKachelAuswahl onWaehlen={setNeuTyp} />
        ) : (
          <form onSubmit={anlegen} className="pci-form">
            <span className="gg-typ-gewaehlt">
              {symbolFuerTyp(neuTyp)} {neuTyp}
              <button type="button" onClick={() => setNeuTyp(null)}>
                ändern
              </button>
            </span>
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
        )}
      </Fenster>
    </div>
  );
}
