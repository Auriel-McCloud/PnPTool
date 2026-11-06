import { api, ApiError } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

export interface Gegenstand {
  id: string;
  name: string;
  description: string;
  notes: string;
  typ: string;
  preis: number;
  kraft: number;
  eigenschaften: Record<string, string>;
  storyRelevant: boolean;
  einzigartig: boolean;
  hatMenge: boolean;
  menge: number;
  istVorlage: boolean;
  seltenheit: number;
  automatischImShop: boolean;
  bildUrl: string;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  /** Wo der Gegenstand steckt. GELAGERT verweist zusätzlich auf ein Ziel. */
  /** Eigengewicht in kg; 0 = vernachlässigbar. */
  gewicht: number;
  /** Wie viel dieser Gegenstand fasst, in kg; 0 = kein Behälter. */
  kapazitaet: number;
  /** Kann etwas aufnehmen. Steht am Gegenstand, wird nicht aus dem Typ geraten. */
  istBehaelter: boolean;
  /** Leer = kein Schloss. Lösung und Schlüssel-Kennung kommen bei Spielern leer zurück. */
  schlossArt?: "" | "passwort" | "schluessel" | "spiel";
  schlossPasswort?: string;
  schlossRaetsel?: string;
  schluesselId?: string;
  aufgeschlossen?: boolean;
  spielLaenge?: number;
  /** Blatt für Drohne/Fahrzeug/Sprite/Geist — 0 heisst "kein Blatt geführt". */
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
  fahrzeugFertigkeiten: Record<string, number>;
  /** Fällt am Körper auf — ein Sturmgewehr sieht jeder, ein Chip nicht. */
  immerSichtbar: boolean;
  /** Riggerkonsole: Bonus aufs Steuern (kann negativ sein) und Drohnenzahl. */
  riggerBonus: number;
  /** Commlink: I.C.E./Matrix-Verteidigung (200¥/Punkt bis 5, danach 500¥/Punkt).
   * Cyberdecks addieren ihren eigenen Bonus hier NICHT dazu — das passiert
   * serverseitig in items/repository.py::commlink_cyberwall. */
  cyberwall: number;
  /** Cyberdeck: Bonuswürfel je NeuroWeaving-Fertigkeit (Brute Force/Schleichen/
   * Daten Verarbeiten/Kompilieren/Electronic Warfare/Matrix-Navigation) —
   * siehe items/repository.py::DECK_WERTE. Mehrere Decks summieren sich NICHT,
   * es zählt je Aktion das höchste ausgerüstete Deck (deck_boni()). */
  deckBruteForce: number;
  deckSchleichen: number;
  deckDaten: number;
  deckKompilieren: number;
  deckElectronicWarfare: number;
  deckMatrixNavigation: number;
  /** Verschiebt die Initiative, solange ausgerüstet (Reflex-Booster: +1/+3/+6). */
  initiativeBonus: number;
  wirkungDauer?: string;
  nebenwirkungBoni?: Record<string, number>;
  nebenwirkungInitiative?: number;
  heilmenge?: number;
  heilQualitaet?: string;
  willenskraftWirkung?: number;
  willenskraftNebenwirkung?: number;
  nebenwirkungSchaden?: string;
  nebenwirkungSchadenMenge?: number;
  umwandeln?: string;
  /** Chrom sitzt im Körper — nur per Operation wieder heraus. */
  verbaut: boolean;
  /** Ein Spieler hat um die Ausbau-Operation gebeten. */
  entfernungBeantragt?: boolean;
  /** Zusatzaktionen pro Kampf: 1, 2 oder -1 (jede Runde). */
  zusatzaktionen: number;
  maxDrohnen: number;
  /** Cyber-/Bioware: dauerhafter Willenskraftverlust und wo es sitzt. */
  wVerlust: number;
  /** Zusätzlicher, von Hand gesetzter Willenskraftverlust (05.11.2026) — für
   * Effekte, die die Bonus-Automatik nicht abbildet. `wVerlust` ist die
   * gespeicherte GESAMTSUMME (automatisch + dieser Wert); die Automatik
   * überschreibt beim Neuberechnen nur ihren eigenen Anteil, nie diesen hier. */
  wVerlustManuell: number;
  /** Pendant zu wVerlustManuell, nur für den Preis statt Willenskraft. */
  preisManuell: number;
  koerperzone: string;
  /** Welcher der drei Plätze der Zone belegt ist (1-3); null = kein fester Platz. */
  slot: number | null;
  /** Zusätzlich zum Typ: kann gleichzeitig als Waffe zählen (z.B. Cyber-Klinge). */
  istWaffe: boolean;
  /** Cyberware-Häkchen: verbaut schaltet Hot frei. */
  istNeurolink: boolean;
  /** Waffenschaden (1–12: Handwaffe bis 7, Schiffswaffe bis 12), separat vom Chrom-Bonus. */
  schaden: number;
  /**
   * Schlag / Tödlich / Schwerheilbar — dieselben drei wie im Treffer-Dialog.
   * Waffen ohne gesetzte Art gelten als Tödlich.
   */
  schadenArt: SchadenArt;
  /**
   * Welcher Kampfskill die Waffe würfelt. Leer = noch nicht markiert.
   * Auch an Chrom, das zusätzlich als Waffe zählt.
   */
  kampfFertigkeit: KampfFertigkeit;
  /** Extra-Würfel nur beim Parieren mit dieser Waffe, nicht auf den Angriff. 0 = keins. */
  paradeBonus: number;
  /** Leer = Schusswaffe komplett aus, sonst nur Upgrades. „nicht“ = kein Matrix-Ziel. */
  deaktivModus?: "" | "komplett" | "upgrades" | "nicht";
  /** Bonuswürfel auf BESTEHENDE Attribute/Fertigkeiten/Sphären, solange ausgerüstet. */
  traitBoni: Record<string, number>;
  /** NEUE Fertigkeiten, die es ohne diesen Gegenstand nicht gibt. */
  ausruestungsfertigkeiten: Record<string, number>;
  /** Spezialisierungen für eine ausruestungsfertigkeit (04.11.2026): von der
   * SL fix vergebene Texte, unveränderlich für den Spieler — Name (Schlüssel
   * aus ausruestungsfertigkeiten) -> Liste von Spezialisierungstexten.
   * Wirkt wie eine normale Fertigkeits-Spezialisierung (+1-Würfel-Chip in
   * der Probe), siehe backend/app/items/schemas.py::ausruestungsSpezialisierungen. */
  ausruestungsSpezialisierungen: Record<string, string[]>;
  /** Ki-Tama (29.10.2026, 30.10.2026 umbenannt von "Materia"): welche der
   * obigen Fertigkeiten der Spieler mit eigener EP hochleveln darf — Stufe
   * bleibt am Gegenstand, siehe backend/app/items/schemas.py::kiTamaFertigkeiten. */
  kiTamaFertigkeiten: Record<string, boolean>;
  /** Attacken-Fertigkeiten (30.10.2026): welche der obigen
   * ausruestungsfertigkeiten ZUSÄTZLICH Kampfangriffe sind — unabhängig von
   * kiTamaFertigkeiten. Erscheinen dann in der Kampfkarte wie eine Waffe,
   * Würfelpool = Intelligenz + Fertigkeitswert. */
  attackenFertigkeiten: Record<string, boolean>;
  /** Schadensart je Attacken-Fertigkeit — kein eigener Schadenswert, der
   * Schaden sind die Nettoerfolge des Wurfs, genau wie bei Waffen. */
  attackenSchadensart: Record<string, SchadenArt>;
  /** Beschwörungs-Ki-Tama (30.10.2026): Link auf den fest gebundenen
   * Critter-Person-Knoten. Leer = kein Beschwörungs-Ki-Tama. */
  beschworenerCritterId: string;
  /** SL-Schwierigkeitsgrad (0-2), additiv auf die benötigten Erfolge. */
  beschwoerungsSchwierigkeit: number;
  /** Liegt im Mülleimer der Spielleitung — überall sonst ausgeblendet. */
  weggeworfen: boolean;
  /** Wer es weggeworfen hat; leer, wenn es nie weggeworfen wurde. */
  weggeworfenVon: string;
  ablage: Ablage;
  ablageZielId: string | null;
  ablageZielName: string | null;
  ablageZielKind: string | null;
  /**
   * Rüstung: Kästchen + Schadensreduktion statt eines flachen Bonus — siehe
   * docs/api/ruestung.md für die vollständige Begründung. 0 = dieses Stück
   * nutzt das System nicht (Bestandsdaten oder Nicht-Rüstung).
   *
   * **Max**: Ausgangswert des Gegenstands ("wie robust gebaut").
   * **Aktuell**: sinkt mit jedem Treffer, der die Rüstung beschädigt.
   */
  ruestungKaestchenMax: number;
  ruestungKaestchenAktuell: number;
  /**
   * Wie viel Schaden die Rüstung pro Treffer direkt abfängt — höher ist
   * besser. Kein eigener "Aktuell"-Wert: die tatsächlich wirksame Reduktion
   * ergibt sich aus dem Kästchen-Verhältnis und sinkt automatisch, je
   * beschädigter die Rüstung ist (siehe `RuestungsUebersicht.reduktionEffektiv`).
   */
  ruestungReduktionBasis: number;
  /** Reparaturmaterial: verbrauchbar an einer Rüstung im Selbst-Reparieren-Popup.
   * `reparaturKapazitaet` deckelt, wie viele Kästchen ein Stück davon höchstens
   * abdeckt — siehe kampf/ruestung.py::selbstreparatur_ergebnis. */
  istReparaturmaterial: boolean;
  reparaturKapazitaet: number;
  /**
   * Natürliche Rüstung (11.10.2026 Verfeinerung, Rassen-/Kreatur-Feature —
   * z.B. Dug'Rahs Chitinpanzer): analog zu `verbaut` bei Cyberware — nicht
   * ablegbar für den Spieler (GM kann es im Ausnahmefall), nicht reparierbar
   * (409 auf allen drei Reparatur-Routen), und `ruestungKaestchenMax` wird
   * serverseitig LIVE aus der Widerstandsfähigkeit der tragenden Person
   * berechnet statt aus diesem gespeicherten Wert (siehe docs/api/ruestung.md,
   * Abschnitt „Natürliche Rüstung"). Heilt nur über die Rast-Mechanik.
   */
  istNatuerlich: boolean;
  /** Ultraschall: Battlemap-Rundumsicht, nur wenn das Stück verbaut ist. */
  rundumsicht: boolean;
  /**
   * Maschinenteil (26.10.2026, Material statt Nuyen beim Drohnen-/
   * Fahrzeug-Umbau): gestuft wie Reparaturmaterial — "" | "minderwertig" |
   * "normal" | "hochwertig", siehe backend traits/drohnen.py::maschinenteil_reicht.
   */
  istMaschinenteil: boolean;
  maschinenteilQualitaet: string;
  /**
   * Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026, siehe
   * docs/wiki/concepts/augments-ausruestung.md): wie viele Augments in
   * dieses Stück montierbar sind. Nur bei Waffe/Rüstung/Cyberdeck/
   * Riggerkonsole relevant (`AUGMENT_TRAEGER_TYPEN` im Backend).
   */
  upgradeSlots: number;
  /** Dieser Gegenstand IST ein Augment — sein `traitBoni`-Feld trägt den
   * Bonus, den es beim Montieren gibt. */
  istAugment: boolean;
  /** Leer = passt auf jedes Ziel; gesetzt = nur an Waffen mit diesem
   * kampfFertigkeit-Typ montierbar. */
  augmentWaffentyp: KampfFertigkeit;
  /** Leer = an jedem AUGMENT_TRAEGER_TYPEN montierbar; gesetzt = NUR an
   * genau diesem Gegenstandstyp (z.B. ein Reflexbooster-Upgrade nur an
   * Cyberdeck/Riggerkonsole) — Pendant zu `items/augments.py::
   * zieltyp_passt`, unabhängig von `augmentWaffentyp` oben. */
  augmentZielTyp: "" | "Waffe" | "Rüstung" | "Cyberdeck" | "Riggerkonsole" | "Commlink";
  /** Ein Patzer beim Montieren/Demontieren hat dieses Augment beschädigt —
   * der Bonus zählt nicht, bis es repariert ist. */
  defekt: boolean;
  /** Montage-Ziel (nur bei istAugment relevant) — Gegenstand ODER Person
   * (Drohne/Fahrzeug). */
  montiertAnId: string | null;
  montiertAnName: string | null;
  montiertAnKind: string | null;
  /**
   * Credstick (05.11.2026, Tresor-Modell): Geld, das auf diesem Gegenstand
   * geladen ist — hängt am STÜCK, nicht an der Person. Laden/Entladen
   * bucht zwischen diesem Feld und dem eigenen Kapital um; Weitergeben
   * und Finden brauchen keinen eigenen Mechanismus, ein Credstick ist ein
   * ganz normaler Gegenstand. Nur bei typ="Credstick" von Belang.
   */
  geladenesGeld: number;
}

/** Pool-Infos fürs Reparatur-Popup — Handwerk-Wert der Trägerin plus freie
 * Attributwahl, dazu benötigte Erfolge und Heilung bei Erfolg. Siehe
 * docs/wiki/concepts/drohnen-fahrzeuge.md, „Reparatur". */
export interface ReparaturProbePool {
  skill: string;
  skillWert: number;
  attribute: { name: string; wert: number }[];
  benoetigteErfolge: number;
  heilungBeiErfolg: number;
  fehlendeKaestchen: number;
}

/** Auswertung der Selbst-Reparatur (Maschinenteil + selbstberichtete Probe),
 * fürs Popup. */
export interface ReparaturMaterialErgebnis {
  qualitaet: string;
  menge: number;
  repariert: number;
  materialName: string;
  materialVerbraucht: number;
  materialRestmenge: number;
  gegenstand: Gegenstand;
}

/** Reine Preisberechnung für den Händler-Vorschlag, kein Seiteneffekt. */
export interface ReparaturPreisAntwort {
  fehlendeKaestchen: number;
  kaestchenMax: number;
  neuwert: number;
  preis: number;
  deckel: number;
}

// =====================================================================
// Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026) — siehe
// docs/wiki/concepts/augments-ausruestung.md und backend items/augments.py.
// =====================================================================

export interface AugmentMontagePool {
  skill: string;
  skillWert: number;
  attribute: { name: string; wert: number }[];
  level: number;
  benoetigteErfolge: number;
}

export interface AugmentZiel {
  id: string;
  name: string;
  typ: string;
  upgradeSlots: number;
  belegteSlots: number;
}

export interface AugmentAktionsErgebnis {
  erfolgreich: boolean;
  defekt: boolean;
  gegenstand: Gegenstand;
}

export interface AugmentReparaturPool {
  skill: string;
  skillWert: number;
  attribute: { name: string; wert: number }[];
  level: number;
  benoetigteErfolge: number;
  heilungBeiErfolg: number;
  vollstaendigRepariert: boolean;
}

export interface AugmentReparaturErgebnis {
  repariert: boolean;
  materialName: string;
  materialVerbraucht: number;
  materialRestmenge: number;
  gegenstand: Gegenstand;
}


/** Handwaffen 1–7 laut Regelblatt, Schiffswaffen (Raumschiff) bis 12. */
export const SCHADEN_MAX = 12;
/** Alter flacher Soak — nicht die Kästchenrüstung. */
export const RUESTUNGSBONUS_MAX = 7;

export function istVerschlossen(g: { schlossArt?: string; aufgeschlossen?: boolean }): boolean {
  return Boolean(g.schlossArt) && !g.aufgeschlossen;
}

export type Ablage = "AUSGERUESTET" | "RUCKSACK" | "GELAGERT";

/** Reihenfolge und Beschriftung der Ablagen — von "am Körper" nach "weit weg".
 *
 * `RUCKSACK` heisst hier **"Mitgeführt"** und nicht "Rucksack": der Zustand
 * setzt keinen Rucksack voraus, man trägt Dinge auch am Gürtel oder in der
 * Hand. Symbol ▣ statt eines Behälter-Icons, genau wie beim Umlegen-Dialog
 * der Spielerkachel (GegenstandKachel::grundAblagen) — 🎒 bleibt dort wie
 * hier reserviert für tatsächlich benannte Behälter (siehe
 * items/aufbewahrung.ts::ermittleBereiche), sonst zeigten zwei verschiedene
 * Zustände dasselbe Symbol (Mark-Bugreport 31.10.2026). */
export const ABLAGEN: { wert: Ablage; label: string; symbol: string }[] = [
  { wert: "AUSGERUESTET", label: "Ausgerüstet", symbol: "⚔" },
  { wert: "RUCKSACK", label: "Mitgeführt", symbol: "▣" },
  { wert: "GELAGERT", label: "Gelagert", symbol: "⌂" },
];

export interface TraglastZeile {
  id: string;
  name: string;
  art: "Person" | "Gegenstand";
  personType: string | null;
  last: number;
  /** 0 = keine Grenze bekannt (z.B. Attribut nicht gesetzt). */
  kapazitaet: number;
  /** Kann etwas aufnehmen. Steht am Gegenstand, wird nicht aus dem Typ geraten. */
  istBehaelter: boolean;
  /** Blatt für Drohne/Fahrzeug/Sprite/Geist — 0 heisst "kein Blatt geführt". */
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
  fahrzeugFertigkeiten: Record<string, number>;
  /** Fällt am Körper auf — ein Sturmgewehr sieht jeder, ein Chip nicht. */
  immerSichtbar: boolean;
  /** Riggerkonsole: Bonus aufs Steuern (kann negativ sein) und Drohnenzahl. */
  riggerBonus: number;
  /** Verschiebt die Initiative, solange ausgerüstet (Reflex-Booster: +1/+3/+6). */
  initiativeBonus: number;
  wirkungDauer?: string;
  nebenwirkungBoni?: Record<string, number>;
  nebenwirkungInitiative?: number;
  heilmenge?: number;
  heilQualitaet?: string;
  willenskraftWirkung?: number;
  willenskraftNebenwirkung?: number;
  nebenwirkungSchaden?: string;
  nebenwirkungSchadenMenge?: number;
  umwandeln?: string;
  /** Chrom sitzt im Körper — nur per Operation wieder heraus. */
  verbaut: boolean;
  /** Ein Spieler hat um die Ausbau-Operation gebeten. */
  entfernungBeantragt?: boolean;
  /** Zusatzaktionen pro Kampf: 1, 2 oder -1 (jede Runde). */
  zusatzaktionen: number;
  maxDrohnen: number;
  /** Cyber-/Bioware: dauerhafter Willenskraftverlust und wo es sitzt. */
  wVerlust: number;
  koerperzone: string;
}

export interface AblageZiel {
  id: string;
  name: string;
  kind: string;
  /** Nur gesetzt, wenn die SL campaignweit wählt und es jemand anderem gehört. */
  besitzerName?: string | null;
}

/** Deckt sich mit Kaestchen.tsx::Schadensart und den drei schadenXY-Feldern
 * der Person — siehe backend/app/kampf/ruestung.py. Der Treffer selbst hängt
 * an der Person, nicht am Gegenstand: siehe bogenApi.ruestungTreffer. */
export type RuestungsArt = "schlag" | "schwer" | "aggraviert";

/** Leer = noch nicht markiert. Schusswaffen ist der Fernkampf-Skill. */
export type KampfFertigkeit = "" | "Schusswaffen" | "Nahkampf" | "Handgemenge";

export const KAMPF_FERTIGKEITEN = ["Schusswaffen", "Nahkampf", "Handgemenge"] as const;

/** Welche Gegenstands-Typen Augments tragen können (ausserdem Drohnen/
 * Fahrzeuge, die aber über `entities/api.ts::Person.upgradeSlots` laufen) —
 * Pendant zu `items/augments.py::AUGMENT_TRAEGER_TYPEN` im Backend. */
export const AUGMENT_TRAEGER_TYPEN = new Set(["Waffe", "Rüstung", "Cyberdeck", "Riggerkonsole", "Commlink"]);

/** Ob ein Upgrade mit diesem `augmentWaffentyp` an einem Ziel mit diesem
 * `kampfFertigkeit`-Wert montierbar ist — TS-Pendant zu
 * `items/augments.py::waffentyp_passt` (29.10.2026, carrier-zentrierte
 * Werkbank-Ansicht, Mark: "ich will ja einen Gegenstand upgraden, also
 * sollte ich die leichte Pistole sehen"). Leer passt auf alles. */
export function waffentypPasst(augmentWaffentyp: string, zielKampfFertigkeit: string): boolean {
  return !augmentWaffentyp || augmentWaffentyp === zielKampfFertigkeit;
}

/** Ob ein Upgrade mit diesem `augmentZielTyp` an einem Ziel dieses
 * Gegenstandstyps montierbar ist — TS-Pendant zu
 * `items/augments.py::zieltyp_passt` (29.10.2026 Nachbesserung). Leer
 * passt auf alles (inkl. Drohne/Fahrzeug, die keinen `typ` haben). */
export function zieltypPasst(augmentZielTyp: string, zielTyp: string): boolean {
  return !augmentZielTyp || augmentZielTyp === zielTyp;
}

export type AugmentZielTyp = "" | "Waffe" | "Rüstung" | "Cyberdeck" | "Riggerkonsole" | "Commlink";

/** Ein Menü für beide alten Filter. Waffenart gewinnt bei altem Widerspruch. */
export type AugmentPasstAn = AugmentZielTyp | Exclude<KampfFertigkeit, "">;

export function augmentPasstAnLesen(waffentyp: string, zieltyp: string): AugmentPasstAn {
  if (waffentyp === "Schusswaffen" || waffentyp === "Nahkampf" || waffentyp === "Handgemenge") {
    return waffentyp;
  }
  if (zieltyp === "Waffe" || zieltyp === "Rüstung" || zieltyp === "Cyberdeck" || zieltyp === "Riggerkonsole" || zieltyp === "Commlink") {
    return zieltyp;
  }
  return "";
}

/** Waffenart setzt den Zieltyp mit auf Waffe, damit die zwei Felder nicht mehr gegeneinander stehen. */
export function augmentPasstAnSchreiben(wert: string): {
  augmentWaffentyp: KampfFertigkeit;
  augmentZielTyp: AugmentZielTyp;
} {
  if (wert === "Schusswaffen" || wert === "Nahkampf" || wert === "Handgemenge") {
    return { augmentWaffentyp: wert, augmentZielTyp: "Waffe" };
  }
  if (wert === "Waffe" || wert === "Rüstung" || wert === "Cyberdeck" || wert === "Riggerkonsole" || wert === "Commlink") {
    return { augmentWaffentyp: "", augmentZielTyp: wert };
  }
  return { augmentWaffentyp: "", augmentZielTyp: "" };
}

export const KAMPF_FERTIGKEIT_LABEL: Record<Exclude<KampfFertigkeit, "">, string> = {
  Schusswaffen: "Fernkampf",
  Nahkampf: "Nahkampf",
  Handgemenge: "Handgemenge",
};

export function kampfFertigkeitLesen(roh: string | undefined | null): KampfFertigkeit {
  if (roh === "Schusswaffen" || roh === "Nahkampf" || roh === "Handgemenge") return roh;
  return "";
}

/** Leer = noch nicht gesetzt. Waffen ohne Wert gelten als Tödlich. "elementar"
 * löst sich erst beim Treffer-Eintragen auf (Effektivitäts-Abfrage in
 * RuestungsTreffer.tsx) — siehe backend/app/items/schemas.py::SchadenArt. */
export type SchadenArt = "" | RuestungsArt | "elementar";

/** Die meisten Waffen. Schlag und Schwerheilbar setzt man extra. */
export const SCHADEN_ART_DEFAULT: RuestungsArt = "schwer";

/** Tischsprache, dieselbe wie im Treffer-Dialog — nicht die Kästchen-Namen. */
export const SCHADEN_ART_LABEL: Record<Exclude<SchadenArt, "">, string> = {
  schlag: "Schlag",
  schwer: "Tödlich",
  aggraviert: "Schwerheilbar",
  elementar: "Elementar",
};

export function schadenArtFuerWaffe(art: string | undefined): Exclude<SchadenArt, ""> {
  if (art === "schlag" || art === "schwer" || art === "aggraviert" || art === "elementar") return art;
  return SCHADEN_ART_DEFAULT;
}

export function schadenArtLabel(art: string | undefined): string {
  if (art === "schlag" || art === "schwer" || art === "aggraviert" || art === "elementar") return SCHADEN_ART_LABEL[art];
  return "";
}

export interface GegenstandMitBesitzer extends Gegenstand {
  // Vorlagen haben keinen Besitzer (siehe VORLAGE_SENTINEL) — daher nullable.
  ownerId: string | null;
  ownerName: string | null;
  ownerPersonType: "PC" | "NPC" | null;
}

// Pseudo-Wert für Besitzer-Dropdowns: "kein Besitzer, dieser Gegenstand ist
// eine Vorlage" statt einer echten Person-ID.
export const VORLAGE_SENTINEL = "__VORLAGE__";

// Pseudo-Wert für Besitzer-Dropdowns: "kein Besitzer, aber auch keine
// Vorlage" — die Invariante istVorlage <=> kein Besitzer (siehe
// items/schemas.py) gilt eigentlich, bricht aber real, wenn eine Person
// gelöscht wird, ohne dass ihre Gegenstände vorher zurückgegeben/zu Vorlagen
// gemacht wurden (02.11.2026, Mark: "Objekte die niemanden gehören,
// vielleicht weil wir den Besitzer gelöscht haben"). Eigener Sentinel statt
// Wiederverwendung von VORLAGE_SENTINEL, damit sich "aufzuräumende Waisen"
// gezielt von echten, gewollten Vorlagen trennen lassen.
export const HERRENLOS_SENTINEL = "__HERRENLOS__";

function base(campaignId: string, personId: string) {
  return `/api/campaigns/${campaignId}/personen/${personId}/gegenstaende`;
}

function campaignBase(campaignId: string) {
  return `/api/campaigns/${campaignId}/gegenstaende`;
}

function itemBase(campaignId: string, itemId: string) {
  return `${campaignBase(campaignId)}/${itemId}`;
}

export interface GegenstandUpdate {
  name?: string;
  description?: string;
  notes?: string;
  // typ (06.10.2026): GM-only Korrektur, siehe Backend-Kommentar in
  // schemas.py — falsch von der KI eingeordnete Gegenstände müssen
  // korrigierbar sein, ohne sie löschen und neu anlegen zu müssen.
  typ?: string;
  preis?: number;
  kraft?: number;
  eigenschaften?: Record<string, string>;
  storyRelevant?: boolean;
  einzigartig?: boolean;
  hatMenge?: boolean;
  menge?: number;
  // istVorlage bewusst nicht editierbar (siehe Backend-Kommentar in
  // schemas.py) — ergibt sich ausschließlich aus Besitzer wechseln/Vorlage
  // machen/Zuweisen.
  seltenheit?: number;
  automatischImShop?: boolean;
  bildUrl?: string;
  sichtbarkeit?: SichtbarkeitModus;
  sichtbarFuer?: string[];  gewicht?: number;
  kapazitaet?: number;
  /** Credstick: vorbefüllter Betrag beim Anlegen/Korrigieren eines
   * Fundstücks. Laden/Entladen laufen über eigene Routen, nicht über PATCH. */
  geladenesGeld?: number;
  istBehaelter?: boolean;
  schlossArt?: "" | "passwort" | "schluessel" | "spiel";
  schlossPasswort?: string;
  schlossRaetsel?: string;
  schluesselId?: string;
  aufgeschlossen?: boolean;
  spielLaenge?: number;
  stufe?: number;
  widerstand?: number;
  angriff?: number;
  agilitaet?: number;
  fahrzeugFertigkeiten?: Record<string, number>;
  immerSichtbar?: boolean;
  riggerBonus?: number;
  cyberwall?: number;
  deckBruteForce?: number;
  deckSchleichen?: number;
  deckDaten?: number;
  deckKompilieren?: number;
  deckElectronicWarfare?: number;
  deckMatrixNavigation?: number;
  initiativeBonus?: number;
  wirkungDauer?: string;
  nebenwirkungBoni?: Record<string, number>;
  nebenwirkungInitiative?: number;
  heilmenge?: number;
  heilQualitaet?: string;
  willenskraftWirkung?: number;
  willenskraftNebenwirkung?: number;
  nebenwirkungSchaden?: string;
  nebenwirkungSchadenMenge?: number;
  umwandeln?: string;
  verbaut?: boolean;
  zusatzaktionen?: number;
  maxDrohnen?: number;
  wVerlust?: number;
  wVerlustManuell?: number;
  preisManuell?: number;
  koerperzone?: string;
  slot?: number | null;
  istWaffe?: boolean;
  istNeurolink?: boolean;
  schaden?: number;
  schadenArt?: SchadenArt;
  kampfFertigkeit?: KampfFertigkeit;
  paradeBonus?: number;
  deaktivModus?: "" | "komplett" | "upgrades" | "nicht";
  traitBoni?: Record<string, number>;
  ausruestungsfertigkeiten?: Record<string, number>;
  ausruestungsSpezialisierungen?: Record<string, string[]>;
  kiTamaFertigkeiten?: Record<string, boolean>;
  attackenFertigkeiten?: Record<string, boolean>;
  attackenSchadensart?: Record<string, SchadenArt>;
  beschworenerCritterId?: string;
  beschwoerungsSchwierigkeit?: number;
  ruestungKaestchenMax?: number;
  ruestungKaestchenAktuell?: number;
  ruestungReduktionBasis?: number;
  istReparaturmaterial?: boolean;
  reparaturKapazitaet?: number;
  istNatuerlich?: boolean;
  rundumsicht?: boolean;
  istMaschinenteil?: boolean;
  maschinenteilQualitaet?: string;
  upgradeSlots?: number;
  istAugment?: boolean;
  augmentWaffentyp?: KampfFertigkeit;
  augmentZielTyp?: "" | "Waffe" | "Rüstung" | "Cyberdeck" | "Riggerkonsole" | "Commlink";
  defekt?: boolean;
}

type NeuerGegenstand = {
  name: string;
  // Der Typ wird gleich beim Anlegen per Kachel-Auswahl gewählt (siehe
  // typKatalog.ts/TypKachelAuswahl.tsx) und ist danach fix — Pflichtfeld,
  // damit kein Gegenstand mehr "versehentlich Sonstiges" bleibt.
  typ: string;
  description?: string;
  notes?: string;
  eigenschaften?: Record<string, string>;
  storyRelevant?: boolean;
};

export interface Chromstufe {
  name: string;
  beschreibung: string;
  preisJeBonus: number;
  preis: number;
  /** Was dieses Stück **allein** kostet — mindestens 1. */
  wVerlust: number;
  /**
   * Der ungerundete Bruch. Genau dieser wird gespeichert: die Brüche mehrerer
   * Implantate summieren sich, gerundet wird erst am Ende. Zwei Stücke mit
   * 0,67 kosten zusammen 1, nicht 2.
   */
  wVerlustGenau: number;
}

export const itemsApi = {
  /**
   * Preis und Willenskraftverlust je Qualitätsstufe — vom Server gerechnet,
   * damit die Formel nur an einer Stelle steht.
   */
  chromstufen: (cid: string, bonus: number) =>
    api.get<{ stufen: Chromstufe[]; koerperzonen: string[] }>(
      `/api/campaigns/${cid}/chromstufen?bonus=${bonus}`,
    ),
  // Person-gescopt: nur für Gegenstände MIT Besitzer (Anlegen/Auflisten im
  // Kontext einer Person). Alle anderen Operationen sind campaign-gescopt,
  // da Vorlagen keinen Besitzer haben.
  list: (cid: string, personId: string) => api.get<Gegenstand[]>(base(cid, personId)),
  create: (cid: string, personId: string, body: NeuerGegenstand) => api.post<Gegenstand>(base(cid, personId), body),

  listAlle: (cid: string) => api.get<GegenstandMitBesitzer[]>(campaignBase(cid)),
  get: (cid: string, itemId: string) => api.get<Gegenstand>(itemBase(cid, itemId)),
  /** Implantat einsetzen oder chirurgisch entfernen. Nur SL. */
  chirurgie: (cid: string, itemId: string, einsetzen: boolean) =>
    api.post<Gegenstand>(`/api/campaigns/${cid}/gegenstaende/${itemId}/chirurgie`, { einsetzen }),
  /** Spieler bittet um die Ausbau-Operation; die SL entscheidet. */
  entfernungBeantragen: (cid: string, itemId: string) =>
    api.post<Gegenstand>(`/api/campaigns/${cid}/gegenstaende/${itemId}/entfernung-beantragen`),
  /** Was bei dieser Person im Körper sitzt, nach Zone und Platz sortiert. */
  verbautes: (cid: string, personId: string) =>
    api.get<Gegenstand[]>(`/api/campaigns/${cid}/gegenstaende/verbaut/${personId}`),
  setAblage: (cid: string, itemId: string, ablage: Ablage, zielId?: string | null) =>
    api.post<Gegenstand>(`${campaignBase(cid)}/${itemId}/ablage`, { ablage, zielId: zielId ?? null }),
  /** Frei liegenden Gegenstand an einem erreichbaren Ort aufnehmen (eigenes
   * Versteck oder aktueller Aufenthaltsort der Party) — Besitzwechsel zu
   * sich selbst, Ablage zurück auf "mitgeführt". */
  aufheben: (cid: string, itemId: string) => api.post<Gegenstand>(`${campaignBase(cid)}/${itemId}/aufheben`),
  /** Kästchen auffüllen. Die Reduktion braucht keine eigene Reparatur mehr —
   * sie folgt automatisch aus dem wiederhergestellten Kästchen-Verhältnis.
   * Nur SL. */
  ruestungReparieren: (cid: string, itemId: string, kaestchen: number) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/ruestung/reparieren`, { kaestchen }),
  /**
   * Pool-Infos fürs Reparatur-Popup: Handwerk-Wert der Trägerin + alle
   * Attribute zur freien Partnerwahl, benötigte Erfolge für `menge` Stück
   * und voraussichtliche Heilung. Reine Leseabfrage.
   */
  ruestungReparaturPool: (cid: string, itemId: string, materialGegenstandId: string, menge: number) =>
    api.get<ReparaturProbePool>(
      `${itemBase(cid, itemId)}/ruestung/reparatur-pool?materialGegenstandId=${encodeURIComponent(
        materialGegenstandId,
      )}&menge=${menge}`,
    ),
  /**
   * Selbst-Reparieren: Maschinenteil + selbstberichtete Probe (der Spieler
   * würfelt physisch am Tisch), kein Geld. "ja" heilt + verbraucht `menge`
   * Material, "patzer" verbraucht nur das Material, "nein" lässt beides
   * unangetastet. Nur SL — siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
   */
  ruestungReparierenMaterial: (
    cid: string,
    itemId: string,
    materialGegenstandId: string,
    menge: number,
    probenErgebnis: "ja" | "nein" | "patzer",
  ) =>
    api.post<ReparaturMaterialErgebnis>(`${itemBase(cid, itemId)}/ruestung/reparieren-material`, {
      materialGegenstandId,
      menge,
      probenErgebnis,
    }),
  /** Reine Preisberechnung für den Händler-Vorschlag, kein Seiteneffekt. */
  ruestungReparaturPreis: (cid: string, itemId: string, fehlendeKaestchen?: number) =>
    api.get<ReparaturPreisAntwort>(
      `${itemBase(cid, itemId)}/ruestung/reparatur-preis${
        fehlendeKaestchen != null ? `?fehlendeKaestchen=${fehlendeKaestchen}` : ""
      }`,
    ),
  /** Maschinenteile im Besitz der Trägerin dieser Rüstung, für die Auswahl. */
  ruestungMaschinenteile: (cid: string, itemId: string) =>
    api.get<Gegenstand[]>(`${itemBase(cid, itemId)}/ruestung/maschinenteile`),
  /** Reparaturmaterial im Besitz der Trägerin dieser Rüstung, für die Auswahl. */
  reparaturmaterialListe: (cid: string, itemId: string) =>
    api.get<Gegenstand[]>(`${itemBase(cid, itemId)}/reparaturmaterial`),
  traglast: (cid: string) => api.get<TraglastZeile[]>(`${campaignBase(cid)}/traglast`),
  /** Reparierbare Rüstung/Chrom dieser Person (05.11.2026, Party-Reparatur-
   * Freigabe) — für die Werkbank: eigene Ausrüstung UND die reparierbaren
   * Sachen jedes Party-Mitglieds, das einem Zugriff erteilt hat. */
  reparierbareItems: (cid: string, personId: string) =>
    api.get<Gegenstand[]>(`${campaignBase(cid)}/reparierbar/${personId}`),
  ablageziele: (cid: string, itemId: string) =>
    api.get<AblageZiel[]>(`${campaignBase(cid)}/${itemId}/ablageziele`),

  createVorlage: (cid: string, body: NeuerGegenstand) => api.post<Gegenstand>(campaignBase(cid), body),
  update: (cid: string, itemId: string, body: GegenstandUpdate) =>
    api.patch<Gegenstand>(itemBase(cid, itemId), body),
  oeffnen: (cid: string, itemId: string, passwort = "") =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/oeffnen`, { passwort }),
  schlossSpiel: (cid: string, itemId: string, folge?: number[]) =>
    api.post<{ runde: number; anzeige: number[]; falsch: boolean; geschafft: boolean; aufgeschlossen: boolean }>(
      `${itemBase(cid, itemId)}/schloss/spiel`,
      { folge: folge ?? null },
    ),
  /** Spieler dürfen eine offene Kiste selbst wieder zusperren. */
  zusperren: (cid: string, itemId: string) => api.post<Gegenstand>(`${itemBase(cid, itemId)}/schloss/zusperren`),
  remove: (cid: string, itemId: string) => api.delete<void>(itemBase(cid, itemId)),
  assign: (cid: string, itemId: string, zielPersonId: string, kopie = false) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/zuweisen`, { zielPersonId, kopie }),
  vorlagenArt: (cid: string, itemId: string, keineVorlage: boolean) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/vorlagen-art`, { keineVorlage }),
  /** Vom Behälter aus bedient: legt gegenstandId in den Behälter itemId. */
  hineinlegen: (cid: string, behaelterId: string, gegenstandId: string) =>
    api.post<Gegenstand>(`${itemBase(cid, behaelterId)}/hineinlegen`, { gegenstandId }),
  /**
   * Andere Gegenstände derselben Besitzerin, die sich mit diesem hier zu
   * einem Stapel zusammenlegen ließen (gleicher Name/Typ/alle mechanischen
   * Felder, siehe backend items/repository.py::stapel_gleich). Nur SL.
   */
  stapelkandidaten: (cid: string, itemId: string) =>
    api.get<Gegenstand[]>(`${itemBase(cid, itemId)}/stapelkandidaten`),
  /**
   * Legt die genannten Quell-Gegenstände in diesen hier zusammen: Summe der
   * Mengen, hatMenge=true. Die Quellen landen im Mülleimer (reversibel),
   * nicht gelöscht. Nur SL.
   */
  zusammenlegen: (cid: string, itemId: string, quellItemIds: string[]) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/zusammenlegen`, { quellItemIds }),
  changeOwner: (cid: string, itemId: string, zielPersonId: string) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/besitzer`, { zielPersonId }),
  removeOwner: (cid: string, itemId: string) => api.post<Gegenstand>(`${itemBase(cid, itemId)}/vorlage`, {}),
  /**
   * Wegwerfen — **löscht nicht**, sondern legt den Gegenstand in den
   * Mülleimer der Spielleitung. Die einzige Löschung ist `remove` von dort.
   * Auch Spieler dürfen das, aber nur am eigenen Besitz (Server prüft).
   */
  wegwerfen: (cid: string, itemId: string) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/wegwerfen`, {}),
  schlucken: (cid: string, itemId: string) =>
    api.post<{ text: string }>(`${itemBase(cid, itemId)}/schlucken`, {}),
  /** Mülleimer-Liste — nur für die Spielleitung. */
  listWeggeworfen: (cid: string) =>
    api.get<GegenstandMitBesitzer[]>(`${campaignBase(cid)}/weggeworfen`),
  /** Zurück ins Spiel; landet als "gelagert" ohne festes Ziel. */
  zurueckholen: (cid: string, itemId: string) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/zurueckholen`, {}),
  uploadBild: async (cid: string, itemId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${itemBase(cid, itemId)}/bild`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, body.detail ?? "Upload fehlgeschlagen");
    }
    return (await response.json()) as Gegenstand;
  },
  bildEntfernen: (cid: string, itemId: string) => api.delete<Gegenstand>(`${itemBase(cid, itemId)}/bild`),

  // --- Augments (29.10.2026) ------------------------------------------
  /** Pool fürs Montieren UND Demontieren — dieselbe Schwelle gilt für beide. */
  augmentMontagePool: (cid: string, itemId: string, skill: string) =>
    api.get<AugmentMontagePool>(`${itemBase(cid, itemId)}/augment/montage-pool?skill=${encodeURIComponent(skill)}`),
  /** Gegenstände desselben Besitzers mit freiem, passendem Slot. */
  augmentZiele: (cid: string, itemId: string) =>
    api.get<AugmentZiel[]>(`${itemBase(cid, itemId)}/augment/ziele`),
  augmentMontieren: (cid: string, itemId: string, zielId: string, skill: string, probenErgebnis: "ja" | "nein" | "patzer") =>
    api.post<AugmentAktionsErgebnis>(`${itemBase(cid, itemId)}/augment/montieren`, { zielId, skill, probenErgebnis }),
  augmentDemontieren: (cid: string, itemId: string, skill: string, probenErgebnis: "ja" | "nein" | "patzer") =>
    api.post<AugmentAktionsErgebnis>(`${itemBase(cid, itemId)}/augment/demontieren`, { skill, probenErgebnis }),
  augmentReparaturPool: (cid: string, itemId: string, skill: string, materialGegenstandId: string, menge: number) =>
    api.get<AugmentReparaturPool>(
      `${itemBase(cid, itemId)}/augment/reparatur-pool?skill=${encodeURIComponent(skill)}&materialGegenstandId=${encodeURIComponent(
        materialGegenstandId,
      )}&menge=${menge}`,
    ),
  augmentReparierenMaterial: (
    cid: string,
    itemId: string,
    materialGegenstandId: string,
    menge: number,
    probenErgebnis: "ja" | "nein" | "patzer",
  ) =>
    api.post<AugmentReparaturErgebnis>(`${itemBase(cid, itemId)}/augment/reparieren-material`, {
      materialGegenstandId,
      menge,
      probenErgebnis,
    }),
  /** Maschinenteile im Besitz der Besitzerin dieses defekten Augments. */
  augmentMaterial: (cid: string, itemId: string) =>
    api.get<Gegenstand[]>(`${itemBase(cid, itemId)}/augment/material`),

  // --- Credstick (05.11.2026, Tresor-Modell) ---------------------------
  /** Aktuelles Vermögen des Besitzers — zeigt der Spieler vorm Aufladen/
   * Abheben, wie viel er überhaupt zur Verfügung hat. */
  credstickVermoegen: (cid: string, itemId: string) =>
    api.get<{ kapital: number }>(`${itemBase(cid, itemId)}/credstick/vermoegen`),
  /** Geld vom eigenen Kapital auf den Credstick laden. Spieler nur am
   * eigenen Besitz/eigenen Kreis, SL an jedem Credstick. */
  credstickLaden: (cid: string, itemId: string, betrag: number) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/credstick/laden`, { betrag }),
  /** Gegenstück: Geld vom Credstick zurück aufs eigene Kapital. */
  credstickEntladen: (cid: string, itemId: string, betrag: number) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/credstick/entladen`, { betrag }),
  /** Nur SL: Geld direkt auf einen Credstick erzeugen, ohne Abzug —
   * für NPC-Belohnungen oder vorbereitete Fundstücke. */
  credstickSlLaden: (cid: string, itemId: string, betrag: number) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/credstick/sl-laden`, { betrag }),
};
