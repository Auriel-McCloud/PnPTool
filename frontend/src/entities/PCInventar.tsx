import { useEffect, useState, type FormEvent } from "react";
import { itemsApi, type Gegenstand, type GegenstandMitBesitzer, type Ablage, AUGMENT_TRAEGER_TYPEN } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { GegenstandKachel } from "../items/GegenstandKachel";
import { TypKachelAuswahl } from "../items/TypKachelAuswahl";
import { symbolFuerTyp } from "../items/typKatalog";
import { ApiError } from "../api/client";
import { AugmentFenster } from "../werkbank/AugmentFenster";
import { AugmentTraegerPanel, type AugmentTraeger } from "../werkbank/AugmentTraegerPanel";
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

  // Augment/Chrom einsetzen (05.11.2026-Nachtrag: Mark fehlte dieser Knopf
  // für NPCs — „ich habe keine Möglichkeit als SL einem NPC ein Augment zu
  // verbauen"). Backend konnte es längst (chirurgie_durchfuehren erlaubt der
  // SL uneingeschränkt beides), nur diese Ansicht reichte onChirurgie nie an
  // GegenstandKachel durch — SpielerAnsicht.tsx tat das bisher nur für den
  // Spieler an SEINEM EIGENEN Chrom. Entfernen bleibt bewusst der Körperkarte
  // vorbehalten (eigener Chirurgie-Modus dort); hier nur das Einsetzen.
  const [zumEinsetzen, setZumEinsetzen] = useState<Gegenstand | null>(null);
  const [einsetzenLaeuft, setEinsetzenLaeuft] = useState(false);
  const [einsetzenFehler, setEinsetzenFehler] = useState<string | null>(null);

  async function einsetzen(item: Gegenstand) {
    setEinsetzenLaeuft(true);
    setEinsetzenFehler(null);
    try {
      await itemsApi.chirurgie(campaignId, item.id, true);
      refresh();
    } catch (e) {
      // Fehlertext in einem eigenen Popup zeigen (z.B. „Magier können keine
      // Bioware einsetzen", Platzkonflikt) — dafür die Bestätigung schliessen.
      setEinsetzenFehler(e instanceof ApiError ? e.message : "Einsetzen fehlgeschlagen.");
    } finally {
      setZumEinsetzen(null);
      setEinsetzenLaeuft(false);
    }
  }

  // Werkbank-Augment montieren (06.11.2026, Mark: „wenn ich einen NPC öffne
  // und in sein inventar gehe, habe ich nicht die möglichkeit dem NPC augments
  // zu verbauen" — gemeint sind Werkbank-Upgrades wie Zielfernrohr, Ki-Tama,
  // nicht nur Chrom-Chirurgie oben). Das AugmentFenster ist der generische
  // Werkbank-Dialog, zeigt Montage-Probe + Material + Reparatur — genau wie
  // in der Werkbank-Übersicht, nur hier für EINEN Träger direkt im Inventar.
  //
  // 10.11.2026, Mark: „ich war nicht in der Lage einem NPC Augments zu
  // installieren“ — der Knopf nahm blind das ERSTE freie Upgrade im Besitz,
  // ohne Passt-Prüfung, ohne Auswahl, und tat bei keinem freien Upgrade gar
  // nichts. Demontieren ging von hier aus überhaupt nicht. Jetzt öffnet der
  // Knopf dasselbe Träger-Fach wie die Werkbank (`AugmentTraegerPanel`):
  // montierte Upgrades (antippen = demontieren/reparieren) und die
  // passenden freien zum Einbauen, nur aus dem Besitz dieser Person.
  const [upgradeTraeger, setUpgradeTraeger] = useState<AugmentTraeger | null>(null);
  const [werkbankAugment, setWerkbankAugment] = useState<{ g: GegenstandMitBesitzer; vorwaehlen: boolean } | null>(null);
  const mitBesitzer: GegenstandMitBesitzer[] = items.map((i) => ({
    ...i,
    ownerId: personId,
    ownerName: personName,
    ownerPersonType: "NPC",
  }));

  // Trenne verbaute Augments von normalen Gegenständen. Montierte
  // Werkbank-Augments (Zielfernrohr, Ki-Tama & Co.) stecken an ihrem
  // Trägergegenstand (MONTIERT_AN) und tauchen dort schon als „montierte
  // Upgrades" auf, bekommen hier aber zusätzlich eine EIGENE Sektion —
  // vorher fielen sie komplett aus der Ablage-Gruppierung heraus und waren
  // für die SL nirgends mehr anklickbar (Mark-Bugreport 31.10.2026: „wenn
  // Ki-Tamas oder Waffen-Upgrades verbaut sind, kann ich sie als SL auch
  // nicht mehr sehen" — er will sie weiterhin öffnen können, nur mit einem
  // Fähnchen, dass sie gerade verbaut sind).
  const verbaute = items.filter((i) => i.verbaut);
  const montierte = items.filter((i) => i.montiertAnId && !i.verbaut);

  // Träger-Gegenstände mit Upgrade-Slots (06.11.2026, Mark: NPCs sollen
  // Werkbank-Augments bekommen können — die Kachel bekommt einen
  // „🔩 Upgraden"-Button, der das AugmentFenster öffnet).
  const traeger = items.filter((i) => AUGMENT_TRAEGER_TYPEN.has(i.typ) && (i.upgradeSlots ?? 0) > 0);

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
          zeigt zusätzlich das Fähnchen „Montiert an …". */}
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

      {/* Träger mit Upgrade-Slots: Gegenstände, an denen Werkbank-Upgrades
          montiert werden können (06.11.2026, Mark: NPCs sollen Werkbank-Augments
          bekommen können). Button „🔩 Upgraden" öffnet das AugmentFenster. */}
      {traeger.length > 0 && (
        <section className="pci-sektion">
          <h4 className="pci-ablage-titel">
            <span>🔧 Mit Upgrade-Slots</span>
            <span className="pci-anzahl">{traeger.length}</span>
          </h4>
          <div className="pci-kachel-liste">
            {traeger.map((g) => {
              const belegteSlots = items.filter((i) => i.montiertAnId === g.id).length;
              return (
                <div key={g.id} className="pci-traeger-kachel">
                  <GegenstandKachel
                    item={g}
                    campaignId={campaignId}
                    onGeoeffnet={() => void refresh()}
                    onUmlegen={(neueAblage, zielId) => umlagern(g.id, neueAblage, zielId)}
                    onWegwerfen={() => wegwerfen(g.id)}
                    montierteUpgrades={items.filter((i) => i.montiertAnId === g.id).map((i) => i.name)}
                    istSpielleitung
                  />
                  <button
                    type="button"
                    className="pci-upgrade-btn"
                    onClick={() =>
                      setUpgradeTraeger({
                        id: g.id,
                        name: g.name,
                        kind: "Gegenstand",
                        upgradeSlots: g.upgradeSlots ?? 0,
                        kampfFertigkeit: g.kampfFertigkeit ?? "",
                        typ: g.typ,
                      })
                    }
                  >
                    🔩 Upgraden ({belegteSlots}/{g.upgradeSlots})
                  </button>
                </div>
              );
            })}
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
                  onChirurgie={(ein) => {
                    if (ein) setZumEinsetzen(g);
                    return Promise.resolve();
                  }}
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

      {/* Bestätigung vorm Einsetzen — gleiche Warnung wie beim Spieler
          selbst (SpielerAnsicht.tsx), nur dass hier die SL es tut. */}
      {zumEinsetzen && (
        <Bestaetigung
          titel="Augment einsetzen"
          text={`„${zumEinsetzen.name}" bei ${personName} chirurgisch einsetzen?\n\nWirkt danach sofort (Willenskraftverlust, Körperplatz). Entfernen geht später nur über die Körperkarte.`}
          jaText={einsetzenLaeuft ? "..." : "Einsetzen"}
          neinText="Abbrechen"
          onJa={() => void einsetzen(zumEinsetzen)}
          onNein={() => {
            setZumEinsetzen(null);
            setEinsetzenFehler(null);
          }}
        />
      )}
      {einsetzenFehler && !zumEinsetzen && (
        <Bestaetigung
          titel="Einsetzen fehlgeschlagen"
          text={einsetzenFehler}
          jaText="Ok"
          onJa={() => setEinsetzenFehler(null)}
          onNein={() => setEinsetzenFehler(null)}
        />
      )}

      {/* Werkbank-Augment-Fenster (06.11.2026, Mark: NPCs sollen Werkbank-
          Upgrades montieren/demontieren/reparieren können — dasselbe Fenster
          wie in der Werkbank-Übersicht, nur direkt aus dem Inventar heraus). */}
      <Fenster
        offen={upgradeTraeger !== null}
        breit
        titel={`Upgraden: ${upgradeTraeger?.name ?? ""}`}
        unterzeile={`Inventar von ${personName}`}
        kennung={`pci-upgraden:${upgradeTraeger?.id ?? ""}`}
        onSchliessen={() => setUpgradeTraeger(null)}
      >
        <AugmentTraegerPanel
          traeger={upgradeTraeger}
          alleGegenstaende={mitBesitzer}
          onUpgradeKlick={(g, vorwaehlen) => setWerkbankAugment({ g, vorwaehlen })}
        />
      </Fenster>

      {werkbankAugment && (
        <AugmentFenster
          campaignId={campaignId}
          augment={werkbankAugment.g}
          vorausgewaehltesZiel={werkbankAugment.vorwaehlen && upgradeTraeger ? upgradeTraeger : undefined}
          onSchliessen={() => setWerkbankAugment(null)}
          onGeaendert={() => {
            void refresh();
            setWerkbankAugment(null);
          }}
        />
      )}
    </div>
  );
}
