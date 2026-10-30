import { useEffect, useMemo, useRef, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { CampaignGraphView } from "../graph/CampaignGraphView";
import { WikiAnsicht } from "../wiki/WikiAnsicht";
import { MitteilungenAnbieter } from "../mitteilungen/MitteilungenKontext";
import { MitteilungenBlitz } from "../mitteilungen/MitteilungenBlitz";
import { MitteilungPopup } from "../mitteilungen/MitteilungPopup";
import { Warnung } from "../mitteilungen/Warnung";
import { VerhandlungPopup } from "../verhandlung/VerhandlungPopup";
import { verhandlungApi } from "../verhandlung/api";
import { AlltagswunschErgebnisPopup } from "../haendler/AlltagswunschErgebnisPopup";
import { einstellungenApi, formatiereLast, type Einstellungen } from "../campaigns/einstellungen";
import { itemsApi, type Ablage, type Gegenstand, type GegenstandMitBesitzer, type TraglastZeile } from "../items/api";
import {
  ermittleBereiche,
  // "Bereich" heisst in der Hülle bereits der Navigationsbereich links
  type Bereich as Ablagebereich,
} from "../items/aufbewahrung";
import { GegenstandKachel } from "../items/GegenstandKachel";
import { begleiterApi, type Begleiter } from "../begleiter/api";
import { Initiativliste, useKampf } from "../kampf/Initiativliste";
import { Kampfkarte } from "../kampf/Kampfkarte";
import { DranMeldung } from "../kampf/DranMeldung";
import { BoosterPopup } from "../kampf/BoosterPopup";
import { HotBleibenPopup, MatrixHotKnopf } from "../kampf/HotBleibenPopup";
import { DeineDrohnenImKampf } from "../kampf/DeineDrohnenImKampf";
import { DeineBeschwoerungen } from "../kampf/DeineBeschwoerungen";
import { InitiativeSetzen } from "../kampf/InitiativeSetzen";
import { kampfApi, type Teilnehmer } from "../kampf/api";
import { AugmentsAnsicht } from "../augments/AugmentsAnsicht";
import { Bestaetigung } from "../shell/Bestaetigung";
import { useNachladen } from "../shell/nachladen";
import { Verwundung, useZustand } from "../shell/Verwundung";
import { BegleiterKachel } from "../begleiter/BegleiterKachel";
import { Fachfenster } from "../items/Fachfenster";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Charakterblatt } from "../traits/Charakterblatt";
import { CommlinkShell, type Bereich } from "../shell/CommlinkShell";
import { MenueAnpassen } from "../shell/MenueAnpassen";
import {
  erkenneGeraet,
  LEER_LAYOUTS,
  sichtbareBereiche,
  spielerMenueApi,
  type Geraet,
  type MenueLayouts,
} from "../shell/menue";
import { VollbildKnopf } from "../shell/VollbildKnopf";
import { Messenger } from "../kontakte/Messenger";
import { kontakteApi, type Kontakt } from "../kontakte/api";
import "../items/gegenstaende.css";
import { playersApi, type SpielerMe } from "./api";
import { CharakterportraitAnsicht } from "./CharakterportraitAnsicht";
import { SpielerEinstieg } from "./SpielerEinstieg";
import { ShopUebersicht } from "../haendler/ShopUebersicht";
import { SpielerNotizen } from "../spielernotizen/SpielerNotizen";
import { LexikonAnsicht } from "../lexikon/LexikonAnsicht";
import { ZeichnungenAnsicht } from "../zeichnungen/ZeichnungenAnsicht";
import { DrohnenUebersicht } from "../drohnen/DrohnenUebersicht";
import { WerkbankUebersichtSpieler } from "../werkbank/WerkbankUebersichtSpieler";
import { MeineAchievements } from "../achievements/MeineAchievements";

/**
 * Die Spieler-Ansicht — dieselbe Hülle wie beim Spielleiter, nur mit weniger
 * Bereichen und ohne Bearbeiten (siehe docs/ui-konzept.md, "eine Hülle, zwei
 * Rollen").
 *
 * Gefiltert wird ausschließlich serverseitig: hier kommt nur an, was der
 * Spieler sehen darf. Diese Ansicht versteckt nichts selbst — sie könnte es
 * auch nicht, die Daten sind schlicht nicht da.
 */
const BEREICHE_STATISCH: Bereich[] = [
  // Das Charakterblatt steht vorn und ist die Startansicht — es ist das,
  // worauf ein Spieler während der Runde am häufigsten schaut.
  { id: "blatt", name: "Charakterblatt", symbol: "▤", farbe: "var(--bereich-blatt)" },
  // Eigener Bereich statt Knopf im Blatt (Mark, 22.09.2026): das Blatt
  // wächst je nach Chartyp schon mit zusätzlichen Skills/Werten, ein
  // Bild-Verwaltungsknopf obendrauf hätte dort nur Platz weggenommen.
  { id: "portrait", name: "Portrait", symbol: "◒", farbe: "var(--bereich-regeln)" },
  // Rucksack wie bei der SL-Ansicht „Gegenstände“ (Mark, 06.10.2026).
  { id: "inventar", name: "Inventar", symbol: "🎒", farbe: "var(--bereich-inventar)" },
  // Shop-System (24.09.2026): eigener Burgermenü-Punkt, Marks Vorgabe.
  { id: "shop", name: "Shop", symbol: "¥", farbe: "var(--bereich-shop)" },
  // Eigener Bereich, weil ein Rigger sehr viele Drohnen führt und die im
  // Inventar zwischen Munition und Kaugummi untergingen. Beide haben ein
  // eigenes Blatt (Stufe, Widerstand, Angriff, Agilität).
  { id: "fahrzeuge", name: "Fahrzeuge", symbol: "⛭", farbe: "var(--bereich-fahrzeuge)" },
  // Sprites, Geister und Verbündete teilen sich ein Blatt mit den Drohnen —
  // deshalb ein Bereich für alle drei.
  { id: "begleiter", name: "Begleiter", symbol: "❊", farbe: "var(--bereich-begleiter)" },
  // Die Initiativliste sehen alle — darum geht es: jeder weiss, wann er dran
  // ist, ohne zu fragen.
  { id: "kampf", name: "Kampf", symbol: "⚔", farbe: "var(--bereich-kampf)" },
  { id: "kontakte", name: "Kontakte", symbol: "◍", farbe: "var(--bereich-kontakte)" },
  // 🧬 wie beim SL-Rassen-Baukasten (App.tsx) — Spieler haben kein
  // Rassen-Menü, SL kein Lexikon, daher kein Symbol-Konflikt (Mark,
  // 10.10.2026).
  { id: "lexikon", name: "Lexikon", symbol: "🧬", farbe: "var(--bereich-orte)" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "var(--bereich-graph)" },
  // Das Kampagnen-Wiki: hier nur lesend, und nur was die SL freigegeben hat.
  { id: "wiki", name: "Wiki", symbol: "❋", farbe: "var(--bereich-wiki)" },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "var(--bereich-notizen)" },
  // Whiteboard (25.10.2026): nur sichtbar, was die SL freigegeben hat —
  // Zeichnen nur, wenn das jeweilige Board es erlaubt (siehe backend/app/zeichnungen).
  { id: "whiteboard", name: "Whiteboard", symbol: "🖊", farbe: "var(--bereich-whiteboard)" },
  // Drohnen & Fahrzeuge (25.10.2026, Phase 3): nur sichtbar, was die SL
  // freigegeben hat; Rigger-Bindung bleibt SL-Sache.
  { id: "drohnen", name: "Fahrzeuge & Drohnen", symbol: "⛭", farbe: "var(--bereich-drohnen)" },
  // Werkbank (29.10.2026, Mark: "natürlich war das für die
  // Spieler gedacht... damit das für sie dann auch angezeigt wird, und
  // ihre Materialien verwendet werden" — und nach einer ersten,
  // fälschlich GM-only gebauten Augments-Version: "das war alles für die
  // Spieler gedacht!"): Reparatur (Rüstung/Drohne/Fahrzeug, Selbst-Weg
  // ohne Händler) UND Augments, beide Self-Service (Probe am Tisch,
  // Ergebnis selbst eintragen, eigenes Material wird verbraucht).
  { id: "werkbank", name: "Werkbank", symbol: "🔧", farbe: "var(--bereich-drohnen)" },
];

// Augments-Bereich: erscheint nur, wenn verbaute Augments vorhanden sind.
const AUGMENTS_BEREICH: Bereich = {
  id: "augments",
  name: "Augments",
  symbol: "⚕",
  farbe: "var(--bereich-regeln)",
};

export function SpielerAnsicht({ onAbgemeldet }: { onAbgemeldet: () => void }) {
  const [ich, setIch] = useState<SpielerMe | null>(null);
  // Mobile Browser/PWAs werfen die Seite im Hintergrund aus dem Speicher —
  // beim Entsperren lädt sie neu. Der zuletzt offene Bereich wird deshalb
  // gemerkt, damit dieser Neustart nicht wie ein Rücksprung zum Blatt wirkt.
  const BEREICH_SCHLUESSEL = "pnptool:bereich:spieler";
  const [bereich, setBereichRoh] = useState(
    () => (typeof localStorage !== "undefined" && localStorage.getItem(BEREICH_SCHLUESSEL)) || "blatt",
  );
  const setBereich = (b: string) => {
    setBereichRoh(b);
    localStorage.setItem(BEREICH_SCHLUESSEL, b);
  };
  const [menueLayouts, setMenueLayouts] = useState<MenueLayouts>(LEER_LAYOUTS);
  const [geraet, setGeraet] = useState<Geraet>(() => (typeof window === "undefined" ? "pc" : erkenneGeraet()));
  const [menueOffen, setMenueOffen] = useState(false);
  // Welches Fach gerade offensteht (null = nur die Ausrüstung). Abgelöst hat
  // das die frühere Mehrfachauswahl über Reiter: was man am Körper trägt,
  // liegt offen, alles andere macht man auf — und sieht schon daran, dass
  // man nicht gleich schnell drankommt.
  // Ein *Stapel* offener Fächer, keine einzelne Auswahl: aus dem Rucksack
  // heraus soll sich der Behälter darin öffnen lassen, und darin wieder einer.
  // Genau das meinte Mark mit "Pop-ups die zu Pop-ups führen".
  const [fachStapel, setFachStapel] = useState<string[]>([]);
  // Kachelraster wie beim Spielleiter: gemessen statt gescrollt.
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  // Eigenes Raster: es steht in einem anderen Bereich und misst eine andere
  // Fläche aus. Ein geteiltes ref zeigte je nach Bereich ins Leere.
  const fahrzeugRasterRef = useRef<HTMLDivElement>(null);
  const begleiterRasterRef = useRef<HTMLDivElement>(null);
  // Läuft dauerhaft mit, nicht nur im Kampfbereich: so kann später eine
  // Meldung "du bist dran" von überall aufgehen.
  const { kampf, geladen: kampfGeladen } = useKampf(ich?.campaignId ?? null);
  // Der eigene Zustand, damit der Bildschirm mitblutet — auch wenn die
  // Spielleitung den Schaden einträgt und nicht man selbst.
  const zustand = useZustand(ich?.campaignId ?? null, ich?.personId ?? null);
  const [seite, setSeite] = useState(0);
  const [einstellungen, setEinstellungen] = useState<Einstellungen | null>(null);
  const [traglast, setTraglast] = useState<TraglastZeile[]>([]);
  // personen wird für den Graphen geladen, auch wenn der Kontakte-Bereich
  // jetzt den Messenger nutzt. Später könnte eine Übersicht "Bekannte NPCs" sinnvoll sein.
  const [personen, setPersonen] = useState<Person[]>([]);
  void personen; // TypeScript: wird für den Graphen bereitgehalten
  const [sachen, setSachen] = useState<GegenstandMitBesitzer[]>([]);
  const [begleiter, setBegleiter] = useState<Begleiter[]>([]);
  const [kontakte, setKontakte] = useState<Kontakt[]>([]);
  // Für den Bestätigungsdialog beim Einsetzen von Augments.
  const [augmentFrage, setAugmentFrage] = useState<string | null>(null);
  // Fehlermeldung anzeigen (z.B. "Magier können keine Bioware...")
  const [fehlerMeldung, setFehlerMeldung] = useState<string | null>(null);
  const [achievementsOffen, setAchievementsOffen] = useState(false);
  // Eigene aktive Drohnen/Fahrzeuge (26.10.2026): wer darf in der
  // Initiativliste auf die eigene Zahl klicken — der Rigger auch für sie.
  const [eigeneDrohnenIds, setEigeneDrohnenIds] = useState<string[]>([]);
  const [initiativeZiel, setInitiativeZiel] = useState<Teilnehmer | null>(null);
  // Die eigene Zeile in der laufenden Initiative — fürs Antippen der
  // Initiative-Zahl direkt auf der eigenen Kampfkarte (Mark, 30.10.2026:
  // "das hätte ich auch gerne für den spieler selbst", bisher nur für
  // Drohnen gebaut). Dieselbe Teilnehmer-Zeile wie in der Initiativliste.
  const eigeneTeilnahme = kampf?.teilnehmer.find((t) => t.personId === ich?.personId) ?? null;
  // Beschwörungs-Ki-Tama (30.10.2026): eigene Ki-Tama-Gegenstände mit
  // verknüpftem Critter — anders als bei Drohnen reicht das schon geladene
  // `sachen`, kein eigener Ladevorgang nötig.
  const eigeneKiTamas = sachen.filter(
    (g) => g.ownerId === ich?.personId && g.typ === "Ki-Tama" && g.beschworenerCritterId,
  );
  const eigeneCritterIds = eigeneKiTamas
    .map((g) => g.beschworenerCritterId)
    .filter((id): id is string => Boolean(id));

  useEffect(() => {
    playersApi.me().then(setIch).catch(() => setIch(null));
  }, []);

  // Zeichentisch speichert in einem eigenen Fenster. Der Kanal trifft auch,
  // wenn der Portrait-Bereich gerade nicht offen ist.
  useEffect(() => {
    const neuLaden = () => {
      playersApi.me().then(setIch).catch(() => undefined);
    };
    const aufNachricht = (e: MessageEvent) => {
      if (e.origin !== window.location.origin) return;
      if (e.data?.typ === "portrait-gespeichert") neuLaden();
    };
    window.addEventListener("message", aufNachricht);
    let kanal: BroadcastChannel | null = null;
    if (typeof BroadcastChannel !== "undefined") {
      kanal = new BroadcastChannel("pnptool-portrait");
      kanal.onmessage = neuLaden;
    }
    return () => {
      window.removeEventListener("message", aufNachricht);
      kanal?.close();
    };
  }, []);

  useEffect(() => {
    spielerMenueApi.laden().then(setMenueLayouts).catch(() => undefined);
  }, []);

  useEffect(() => {
    const tick = () => setGeraet(erkenneGeraet());
    window.addEventListener("resize", tick);
    return () => window.removeEventListener("resize", tick);
  }, []);

  useEffect(() => {
    if (!ich) return;
    const cid = ich.campaignId;
    entitiesApi.listPersonen(cid).then(setPersonen).catch(() => setPersonen([]));
    einstellungenApi.lesen(cid).then(setEinstellungen).catch(() => setEinstellungen(null));
    kontakteApi.meine(cid).then(setKontakte).catch(() => setKontakte([]));
  }, [ich]);

  // Inventar, Traglast und Begleiter still nachladen — auch wenn gerade ein
  // Rucksack offen ist. Der Fach-Stapel hängt nicht an diesen Daten, neue
  // Sachen tauchen im offenen Fenster auf, statt es zuzuschlagen.
  const { ungueltig: inventarUngueltig } = useNachladen(
    async () => {
      const cid = ich?.campaignId;
      if (!cid) throw new Error("keine Kampagne");
      const [sachen, last, begleiter] = await Promise.all([
        itemsApi.listAlle(cid),
        itemsApi.traglast(cid),
        begleiterApi.liste(cid),
      ]);
      return { sachen, last, begleiter };
    },
    (frisch) => {
      setSachen(frisch.sachen);
      setTraglast(frisch.last);
      setBegleiter(frisch.begleiter);
    },
    { aktiv: Boolean(ich), quelle: ich?.campaignId ?? "" },
  );

  // Bereiche nur aus den eigenen Sachen — fremde Verstecke gehen einen nichts an
  const meineRohAlle = sachen.filter((g) => g.ownerId === ich?.personId);
  const fremdeRoh = sachen.filter((g) => g.ownerId !== ich?.personId);

  // Verbaute Augments erscheinen in der Körperkarte, nicht im Inventar.
  // Natürliche Rüstung (11.10.2026 Verfeinerung, Rassen-/Kreatur-Feature wie
  // Dug'Rah) spiegelt dasselbe Prinzip: sie ist Teil des Körpers, kein
  // normaler Inventar-Eintrag — die GM-Ansicht (PCInventar.tsx) filtert NICHT,
  // weil dort die Ausnahme-Ablege-Möglichkeit erhalten bleiben muss.
  const CHROM_TYPEN = ["Cyberware", "Bioware", "Hexware"];
  const istVersteckteAusruestung = (g: GegenstandMitBesitzer) =>
    (CHROM_TYPEN.includes(g.typ) && g.verbaut) || Boolean(g.istNatuerlich);
  const meineRoh = meineRohAlle.filter((g) => !istVersteckteAusruestung(g));

  // Werkbank (29.10.2026, Mark: "das war alles für die Spieler gedacht!"):
  // Filterung nach eigenem Besitz übernimmt `WerkbankUebersichtSpieler`
  // selbst (braucht einen eigenen Drohnen-Fetch, siehe dort) — hier nur
  // Nachladen nach einer Aktion.
  async function nachWerkbankAenderung() {
    if (!ich) return;
    inventarUngueltig();
    const frisch = await itemsApi.listAlle(ich.campaignId);
    inventarUngueltig();
    setSachen(frisch);
  }

  // Augments-Bereich erscheint nur, wenn verbaute Augments vorhanden sind.
  const hatAugments = meineRohAlle.some((g) => g.verbaut);
  const BEREICHE = useMemo(() => {
    if (!hatAugments) return BEREICHE_STATISCH;
    // Nach dem Wiki und vor den Notizen einfügen
    const mitAugments = [...BEREICHE_STATISCH];
    const wikiIdx = mitAugments.findIndex((b) => b.id === "wiki");
    mitAugments.splice(wikiIdx + 1, 0, AUGMENTS_BEREICH);
    return mitAugments;
  }, [hatAugments]);

  const menueBereiche = useMemo(() => {
    const slot = geraet === "tablet" ? menueLayouts.tablet : menueLayouts.pc;
    return sichtbareBereiche(BEREICHE, slot, geraet, bereich);
  }, [BEREICHE, menueLayouts, geraet, bereich]);

  // Was anderen gehört, ist ein Reiter wie jeder andere statt eines
  // angehängten zweiten Blocks: dann gibt es genau ein Raster, das sich
  // ausmessen lässt, und die Auswahl bleibt eine einzige Entscheidung.
  // Ein Bereich prüft laut Schnittstelle einen `Gegenstand`; den Besitzer
  // trägt erst die kampagnenweite Liste nach. Deshalb hier die einzige
  // Stelle, an der das nachgeschlagen wird.
  const gehoertMir = (g: Gegenstand) => (g as GegenstandMitBesitzer).ownerId === ich?.personId;
  const fahrzeuge = meineRoh.filter((g) => g.typ === "Fahrzeug" || g.typ === "Drohne");
  // Ausgeblendet (24.10.2026, Mark): zeigte bisher *jeden* fremden Gegenstand
  // mit sichtbarkeit ALLE/SPEZIFISCH, unabhängig davon, ob der PC je etwas
  // damit zu tun hatte — bei einem frisch erstellten Charakter verwirrend,
  // weil dort plötzlich fremde Sachen auftauchen, die er "nie gesehen" hat.
  // Konzept für später statt Löschen (siehe „ideen für später.txt" und
  // CLAUDE.md „Geplante Features"): gezielter NPC-Gegenstands-Scan per
  // Augment beim Betreten eines Raums statt pauschalem Dauer-Tab.
  const ANDERSWO_GESEHEN_AKTIV = false;
  const bereiche: Ablagebereich[] = [
    // Die eigenen Bereiche dürfen nur eigene Sachen einsammeln — sonst
    // fischte "Mitgeführt" auch den Rucksackinhalt anderer heraus.
    // Verbautes Chrom erscheint nur in der Körperkarte, nie im Inventar.
    ...ermittleBereiche(meineRoh).map((b) => ({
      ...b,
      passt: (g: Gegenstand) =>
        gehoertMir(g) && b.passt(g) && !istVersteckteAusruestung(g as GegenstandMitBesitzer),
    })),
    ...(ANDERSWO_GESEHEN_AKTIV && fremdeRoh.length > 0
      ? [
          {
            id: "FREMD",
            name: "Anderswo gesehen",
            symbol: "◇",
            greifbar: false,
            passt: (g: Gegenstand) => !gehoertMir(g),
          },
        ]
      : []),
  ];

  // Muss vor der Abbruchbedingung stehen: Hooks müssen bei jedem Aufbau in
  // derselben Reihenfolge laufen, sonst bricht React ab ("Rendered more
  // hooks than during the previous render").
  useEffect(() => {
    setSeite(0);
  }, [bereich]);

  async function abmelden() {
    await playersApi.abmelden();
    onAbgemeldet();
  }

  if (!ich) return null;

  // Ohne zugeordneten Charakter: Ersteinstieg statt der vollen Hülle — die
  // eigentliche Auswahl (selbst bauen ODER vorgefertigten PC übernehmen).
  if (!ich.personId) {
    return (
      <SpielerEinstieg
        campaignName={ich.campaignName}
        benutzername={ich.benutzername}
        onZugewiesen={setIch}
        onAbmelden={abmelden}
      />
    );
  }

  const amKoerper = bereiche.find((b) => b.greifbar);
  const faecher = bereiche.filter((b) => !b.greifbar);
  const getragen = amKoerper ? sachen.filter(amKoerper.passt) : [];
  const seiten = Math.max(1, Math.ceil(getragen.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const aufDieserSeite = getragen.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  // Der getragene Behälter gibt dem mittleren Ablageplatz seinen Namen.
  const getragenesFach = faecher.find((f) => f.id === "MITGEFUEHRT");
  const getragenerBehaelter = getragenesFach?.name;
  const getragenerBehaelterId = sachen.find(
    (g) => g.ablage === "AUSGERUESTET" && (g.typ === "Behälter" || g.typ === "Fahrzeug"),
  )?.id;

  /**
   * Zu welchem Fach ein Behälter-Gegenstand gehört. Der getragene Rucksack
   * sammelt unter "MITGEFUEHRT" ein, jeder andere Behälter unter seiner
   * eigenen Kennung.
   */
  function fachIdFuer(item: Gegenstand) {
    if (item.id === getragenerBehaelterId) return getragenesFach?.id;
    return faecher.find((f) => f.id === item.id)?.id;
  }

  function inhaltVon(item: Gegenstand) {
    const fachId = fachIdFuer(item);
    if (!fachId) return undefined;
    const fach = faecher.find((f) => f.id === fachId);
    if (!fach) return undefined;
    return {
      anzahl: sachen.filter(fach.passt).length,
      oeffnen: () => setFachStapel((alt) => [...alt, fachId]),
    };
  }

  async function augmentEinsetzen(itemId: string) {
    if (!ich) return;
    inventarUngueltig();
    try {
      await itemsApi.chirurgie(ich.campaignId, itemId, true);
    } catch (e: unknown) {
      console.error("chirurgie fehlgeschlagen", e);
      // Fehlermeldung vom Server anzeigen (z.B. "Magier können keine Bioware...")
      if (e && typeof e === "object" && "message" in e) {
        setFehlerMeldung((e as { message: string }).message);
      }
    }
    const frisch = await itemsApi.listAlle(ich.campaignId);
    inventarUngueltig();
    setSachen(frisch);
    setAugmentFrage(null);
  }

  function augmentFrageStellen(itemId: string) {
    setAugmentFrage(itemId);
  }

  async function umlegen(itemId: string, ziel: Ablage) {
    if (!ich) return;
    inventarUngueltig();
    // Ohne festes Ziel: der Spieler legt nur die Art fest, das genaue Wohin
    // (welches Fahrzeug, welcher Ort) bleibt Sache der Spielleitung.
    await itemsApi.setAblage(ich.campaignId, itemId, ziel, null);
    const [frisch, last] = await Promise.all([
      itemsApi.listAlle(ich.campaignId),
      itemsApi.traglast(ich.campaignId),
    ]);
    // Nach dem Holen verwerfen, nicht davor: ein Poll, der während des
    // Umlegens gestartet ist, darf den frischen Stand nicht überschreiben.
    inventarUngueltig();
    setSachen(frisch);
    setTraglast(last);
  }

  async function weitergeben(itemId: string, empfaengerPersonId: string) {
    if (!ich) return;
    // Der Gegenstand bleibt bis zur Annahme beim Absender — kein Refresh
    // der Sachen-Liste nötig, es hat sich (noch) nichts geändert. Das
    // Verhandlungs-Popup beim Empfänger übernimmt den eigentlichen Transfer.
    await verhandlungApi.gegenstandWeitergeben(ich.campaignId, itemId, empfaengerPersonId);
  }

  // Zusammenlegen (26.10.2026): das Popup ruft die API selbst auf (siehe
  // ZusammenlegenPopup.tsx), hier wird nur nachgeladen — dieselbe
  // Refresh-Logik wie nach `umlegen`.
  async function nachZusammenlegen() {
    if (!ich) return;
    inventarUngueltig();
    const [frisch, last] = await Promise.all([
      itemsApi.listAlle(ich.campaignId),
      itemsApi.traglast(ich.campaignId),
    ]);
    inventarUngueltig();
    setSachen(frisch);
    setTraglast(last);
  }

  return (
    <MitteilungenAnbieter campaignId={ich.campaignId} personId={ich.personId}>
    {/* Liegt ueber allem, auch ueber offenen Fenstern: eine Ansage der
        Spielleitung darf nicht dahinter verschwinden. */}
    <MitteilungPopup />
    {/* Eingehendes Verhandlungsangebot (z.B. Rüstungsreparatur beim
        Händler) — eigenes Popup, weil Annehmen/Ablehnen eine andere
        Handlung ist als das reine "Verstanden" der SL-Mitteilungen. */}
    <VerhandlungPopup />
    {/* Rückmeldung, sobald die SL einen KI-Alltagswunsch entschieden hat
        (24.09.2026) — muss nicht abgewartet werden, kommt einfach an. */}
    <AlltagswunschErgebnisPopup />
    {/* Vollbild-Warnung: pulsiert und liegt ueber allem, auch ueber dem
        normalen Popup. Fuer Initiative und Gefahr. */}
    <Warnung campaignId={ich.campaignId} />
    {/* Reflex-Booster: fragt beim Drankommen, ob aktiviert werden soll. */}
    <BoosterPopup
      campaignId={ich.campaignId}
      kampf={kampf}
      eigenePersonId={ich.personId}
      onGeaendert={() => { /* der Takt von useKampf holt die Liste nach */ }}
    />
    <HotBleibenPopup
      campaignId={ich.campaignId}
      kampf={kampf}
      onGeaendert={() => { /* der Takt von useKampf holt die Liste nach */ }}
    />
    {/* Initiative per Klick ändern — für den eigenen Charakter und eigene
        aktive Drohnen/Fahrzeuge, siehe Initiativliste weiter unten. */}
    {initiativeZiel && (
      <InitiativeSetzen
        teilnehmer={initiativeZiel}
        onSchliessen={() => setInitiativeZiel(null)}
        onSpeichern={async (wert) => {
          await kampfApi.meldeInitiative(ich.campaignId, initiativeZiel.id, wert);
        }}
      />
    )}
    <Verwundung zustand={zustand} />
    <DranMeldung
      kampf={kampf}
      eigenePersonId={ich.personId}
      imKampfbereich={bereich === "kampf"}
      onHin={() => setBereich("kampf")}
    />
    <CommlinkShell
      bereiche={menueBereiche}
      aktiv={bereich}
      onBereichWechsel={setBereich}
      titel={`${ich.campaignName} — ${BEREICHE.find((b) => b.id === bereich)?.name ?? ""}`}
      // Nur das Inventar teilt sich die Fläche selbst ein; die übrigen
      // Bereiche sind noch Listen und dürfen scrollen.
      statisch={
        bereich === "inventar" ||
        bereich === "shop" ||
        bereich === "fahrzeuge" ||
        bereich === "begleiter" ||
        bereich === "kampf" ||
        bereich === "lexikon" ||
        bereich === "wiki"
      }
      werkzeuge={
        <>
          {/* Blitz rechts in der oberen Leiste — docs/ui-konzept.md */}
          <MitteilungenBlitz personId={ich.personId} />
          {/* Pokal-Symbol (27.09.2026, Marks Vorgabe): eigene Achievements,
              scrollbares Popup, neuestes zuerst — kein eigener Bereich. */}
          <button type="button" className="cl-werkzeug" onClick={() => setAchievementsOffen(true)} title="Achievements">
            🏆
          </button>
          <VollbildKnopf />
          <button type="button" className="cl-werkzeug" onClick={abmelden} title="Abmelden">
            ⏻
          </button>
        </>
      }
      fuss={
        <>
          <button type="button" onClick={() => setMenueOffen(true)} title="Burgermenü anpassen">
            ☰
          </button>
          <div className="cl-menue-fuss-text">
            <div style={{ color: "var(--text-leise)" }}>{ich.benutzername}</div>
            <div>{ich.personName ?? "kein Charakter"}</div>
          </div>
        </>
      }
    >
      {bereich === "blatt" &&
        (ich.personId ? (
          <Charakterblatt campaignId={ich.campaignId} personId={ich.personId} />
        ) : (
          <p style={{ color: "var(--text-leise)" }}>
            Dir ist noch kein Charakter zugeordnet — deine Spielleitung muss dir einen zuweisen.
          </p>
        ))}

      {bereich === "portrait" &&
        (ich.personId ? (
          <CharakterportraitAnsicht
            ich={ich}
            onGeaendert={(frisch) => setIch(frisch)}
          />
        ) : (
          <p style={{ color: "var(--text-leise)" }}>
            Dir ist noch kein Charakter zugeordnet — deine Spielleitung muss dir einen zuweisen.
          </p>
        ))}

      {bereich === "shop" && (
        <ShopUebersicht campaignId={ich.campaignId} eigenePersonId={ich.personId} istGm={false} />
      )}

      {bereich === "fahrzeuge" && (
        <div className="gg-seite" style={KACHEL_STIL}>
          <h3 className="gg-abschnitt">
            <span>⛭ Fahrzeuge und Drohnen</span>
            <span className="gg-abschnitt-zahl">{fahrzeuge.length}</span>
          </h3>
          <div className="gg-raster" ref={fahrzeugRasterRef}>
            {fahrzeuge.map((g) => (
              <GegenstandKachel
                key={g.id}
                item={g}
                behaelterName={getragenerBehaelter}
                behaelterId={getragenerBehaelterId}
                inhalt={inhaltVon(g)}
                onUmlegen={(ziel) => umlegen(g.id, ziel)}
                onChirurgie={(einsetzen) => einsetzen ? augmentFrageStellen(g.id) : Promise.resolve()}
                campaignId={ich.campaignId}
                onZusammengelegt={nachZusammenlegen}
              />
            ))}
          </div>
          {fahrzeuge.length === 0 && <p className="gg-leer">Du besitzt kein Fahrzeug und keine Drohne.</p>}
        </div>
      )}

      {bereich === "kampf" && (
        <div className="ka-seite">
          {!kampfGeladen && <p style={{ color: "var(--text-leise)" }}>Lade…</p>}
          {kampfGeladen && !kampf && (
            <p style={{ color: "var(--text-leise)" }}>Gerade wird nicht gekämpft.</p>
          )}
          {kampf && (
            <>
              <header className="ka-kopf">
                <span className="ka-runde">
                  Runde <strong>{kampf.runde}</strong>
                </span>
                <MatrixHotKnopf campaignId={ich.campaignId} />
              </header>
              <Initiativliste
                kampf={kampf}
                eigenePersonId={ich.personId}
                initiativeBearbeitbar={(t) =>
                  t.personId === ich.personId ||
                  (t.personId != null && eigeneDrohnenIds.includes(t.personId)) ||
                  (t.personId != null && eigeneCritterIds.includes(t.personId))
                }
                onInitiativeBearbeiten={setInitiativeZiel}
              />
              {/* Die eigenen Kampfwerte gleich darunter — im Gefecht will man
                  nicht erst in den Bogen wechseln. */}
              {ich.personId && (
                <div className="ka-eigene">
                  <h3 className="gg-abschnitt">
                    <span>⚔ Deine Werte</span>
                  </h3>
                  <Kampfkarte
                    campaignId={ich.campaignId}
                    personId={ich.personId}
                    aenderbar
                    onInitiativeKlick={eigeneTeilnahme ? () => setInitiativeZiel(eigeneTeilnahme) : undefined}
                  />
                </div>
              )}
              {ich.personId && (
                <DeineDrohnenImKampf
                  campaignId={ich.campaignId}
                  eigenePersonId={ich.personId}
                  kampf={kampf}
                  onGeaendert={() => { /* der Takt von useKampf holt die Liste nach */ }}
                  onListeGeladen={setEigeneDrohnenIds}
                />
              )}
              {ich.personId && (
                <DeineBeschwoerungen
                  campaignId={ich.campaignId}
                  eigenePersonId={ich.personId}
                  kampf={kampf}
                  kiTamas={eigeneKiTamas}
                  onGeaendert={() => { /* der Takt von useKampf holt die Liste nach */ }}
                />
              )}
              {kampf.teilnehmer.length > 1 && (
                <p className="ka-ansage">
                  <span>Ansage von hinten:</span>{" "}
                  {[...kampf.teilnehmer].reverse().map((t) => t.name).join(" → ")}
                </p>
              )}
            </>
          )}
        </div>
      )}

      {bereich === "begleiter" && (
        <div className="gg-seite" style={KACHEL_STIL}>
          <h3 className="gg-abschnitt">
            <span>❊ Sprites, Geister und Verbündete</span>
            <span className="gg-abschnitt-zahl">{begleiter.length}</span>
          </h3>
          <div className="gg-raster" ref={begleiterRasterRef}>
            {begleiter.map((b) => (
              <BegleiterKachel key={b.id} begleiter={b} />
            ))}
          </div>
          {begleiter.length === 0 && <p className="gg-leer">Dir steht noch niemand zur Seite.</p>}
        </div>
      )}

      {bereich === "kontakte" && (
        <Messenger
          campaignId={ich.campaignId}
          kontakte={kontakte}
          onKontakteAktualisieren={() => {
            kontakteApi.meine(ich.campaignId).then(setKontakte).catch(() => {});
          }}
        />
      )}

      {bereich === "inventar" && (
        // Feste Fläche, gemessenes Raster: die Hauptansicht scrollt nicht.
        // In den Fächern darf sie es — dort bricht es die Illusion nicht.
        <div className="gg-seite" style={KACHEL_STIL}>
          {einstellungen?.gewichtAktiv &&
            (() => {
              const meineLast = traglast.find((z) => z.id === ich.personId);
              if (!meineLast) return null;
              const voll = meineLast.kapazitaet > 0 && meineLast.last > meineLast.kapazitaet;
              return (
                <p className="gg-kachel-last" data-voll={voll} style={{ marginBottom: 8, fontSize: 13 }}>
                  Getragen: {formatiereLast(meineLast.last, meineLast.kapazitaet)}
                  {voll && " — überladen"}
                </p>
              );
            })()}

          <h3 className="gg-abschnitt">
            <span>⚔ Am Körper</span>
            <span className="gg-abschnitt-zahl">{getragen.length}</span>
          </h3>

          <div className="gg-raster" ref={rasterRef}>
            {aufDieserSeite.map((g) => (
              <GegenstandKachel
                key={g.id}
                item={g}
                behaelterName={getragenerBehaelter}
                behaelterId={getragenerBehaelterId}
                inhalt={inhaltVon(g)}
                onUmlegen={(ziel) => umlegen(g.id, ziel)}
                onChirurgie={(einsetzen) => einsetzen ? augmentFrageStellen(g.id) : Promise.resolve()}
                campaignId={ich.campaignId}
                eigenePersonId={ich.personId ?? undefined}
                onZusammengelegt={nachZusammenlegen}
                onWeitergeben={(empfaengerId) => weitergeben(g.id, empfaengerId)}
              />
            ))}
          </div>

          {getragen.length === 0 && <p className="gg-leer">Du trägst nichts bei dir.</p>}

          {seiten > 1 && (
            <div className="gg-blaettern">
              <button type="button" onClick={() => setSeite((n) => Math.max(0, n - 1))} disabled={aktuelleSeite === 0}>
                ‹
              </button>
              <span>
                {aktuelleSeite + 1} / {seiten}
              </span>
              <button
                type="button"
                onClick={() => setSeite((n) => Math.min(seiten - 1, n + 1))}
                disabled={aktuelleSeite >= seiten - 1}
              >
                ›
              </button>
            </div>
          )}

          {/* Die Fächer unten wie eine Werkzeugleiste: Rucksack, Fahrzeug,
              Versteck. Jedes geht als Fenster auf — das ist zugleich die
              Handlung "aufmachen" und zeigt, dass man da nicht so schnell
              drankommt wie an das, was man am Körper trägt. */}
          {faecher.length > 0 && (
            <div className="gg-faecher">
              {faecher.map((f) => {
                const anzahl = sachen.filter(f.passt).length;
                return (
                  <button
                    key={f.id}
                    type="button"
                    className="gg-fach"
                    onClick={() => setFachStapel([f.id])}
                    // Auch leere Fächer lassen sich öffnen — man will
                    // nachsehen können, statt zu rätseln.
                    title={`${f.name} öffnen`}
                  >
                    <span className="gg-fach-symbol" aria-hidden="true">
                      {f.symbol}
                    </span>
                    <span className="gg-fach-name">{f.name}</span>
                    <span className="gg-fach-zahl">{anzahl}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Ein Fenster je Stufe des Stapels. Schliessen räumt alles darüber
              mit ab — sonst bliebe ein Fenster stehen, dessen Fach gar nicht
              mehr offen ist. */}
          {fachStapel.map((fachId, stufe) => {
            const fach = faecher.find((f) => f.id === fachId);
            if (!fach) return null;
            return (
              <Fachfenster
                key={`${fachId}:${stufe}`}
                fach={fach}
                offen
                items={sachen.filter(fach.passt)}
                behaelterName={getragenerBehaelter}
                behaelterId={getragenerBehaelterId}
                inhaltVon={inhaltVon}
                onSchliessen={() => setFachStapel((alt) => alt.slice(0, stufe))}
                // Fremdes lässt sich ansehen, aber nicht umlegen oder weitergeben
                onUmlegen={fach.id === "FREMD" ? undefined : (item, ziel) => umlegen(item.id, ziel)}
                onWeitergeben={fach.id === "FREMD" ? undefined : (item, empfaengerId) => weitergeben(item.id, empfaengerId)}
                campaignId={ich.campaignId}
                eigenePersonId={ich.personId ?? undefined}
                onZusammengelegt={fach.id === "FREMD" ? undefined : nachZusammenlegen}
              />
            );
          })}
        </div>
      )}

      {bereich === "lexikon" && <LexikonAnsicht />}

      {bereich === "graph" && <CampaignGraphView campaignId={ich.campaignId} />}

      {/* Nur lesend: Anlegen, Aendern und Freigeben bleibt Sache der Spielleitung.
          Was hier ankommt, hat der Server bereits gefiltert. */}
      {bereich === "wiki" && <WikiAnsicht campaignId={ich.campaignId} nurLesen />}

      {bereich === "notizen" && <SpielerNotizen />}

      {bereich === "whiteboard" && (
        <ZeichnungenAnsicht campaignId={ich.campaignId} eigenePersonId={ich.personId} istGm={false} />
      )}

      {bereich === "drohnen" && (
        <DrohnenUebersicht campaignId={ich.campaignId} istGm={false} eigenePersonId={ich.personId} />
      )}

      {bereich === "augments" && (
        <AugmentsAnsicht
          campaignId={ich.campaignId}
          eigenePersonId={ich.personId}
        />
      )}

      {bereich === "werkbank" && ich.personId && (
        <WerkbankUebersichtSpieler
          campaignId={ich.campaignId}
          personId={ich.personId}
          sachen={sachen}
          onGeaendert={nachWerkbankAenderung}
        />
      )}
    </CommlinkShell>

    <MenueAnpassen
      offen={menueOffen}
      onSchliessen={() => setMenueOffen(false)}
      bereiche={BEREICHE}
      layouts={menueLayouts}
      geraet={geraet}
      onSpeichern={async (layouts) => {
        const gespeichert = await spielerMenueApi.speichern(layouts);
        setMenueLayouts(gespeichert);
      }}
    />

    <MeineAchievements campaignId={ich.campaignId} offen={achievementsOffen} onSchliessen={() => setAchievementsOffen(false)} />

    {/* Bestätigungsdialog für Augment-Einsetzen */}
    {augmentFrage && (
      <Bestaetigung
        titel="Augment einsetzen"
        text="Bist du sicher? Das solltest du lieber einen Experten machen lassen.

Ein eingesetztes Augment kann nur die Spielleitung wieder entfernen."
        jaText="Einsetzen"
        neinText="Abbrechen"
        onJa={() => augmentEinsetzen(augmentFrage)}
        onNein={() => setAugmentFrage(null)}
      />
    )}
    {/* Fehlermeldung bei unerlaubtem Augment-Einbau (Magier/Neuroweaver) */}
    {fehlerMeldung && (
      <Bestaetigung
        titel="Operation fehlgeschlagen"
        text={fehlerMeldung}
        jaText="OK"
        neinText=""
        onJa={() => setFehlerMeldung(null)}
        onNein={() => setFehlerMeldung(null)}
      />
    )}
    </MitteilungenAnbieter>
  );
}
