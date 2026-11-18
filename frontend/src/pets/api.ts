import { api } from "../api/client";

/** Welche Sprites es gibt — gleiche Liste wie `PET_ARTEN` in backend/app/pets/logic.py.
 *  `fuer`: wo die SL sie zur Auswahl bekommt — Tiere am Critter, Bärbel (die
 *  fliegende Bibel, 11.11.2026) an einem Gegenstand. */
export const PET_ARTEN = [
  { wert: "drache", name: "Kleiner Drache", fuer: "critter" },
  // Mark, 12.11.2026 (Critter „Wolke Salamander“): derselbe Babydrache,
  // umgefärbt — blau mit silbernem Bauch spuckt Eis, silbern mit blauer Mähne Blitze.
  { wert: "eisdrache", name: "Kleiner Eisdrache", fuer: "critter" },
  { wert: "blitzdrache", name: "Kleiner Blitzdrache", fuer: "critter" },
  { wert: "baerbel", name: "Bärbel (fliegendes Buch)", fuer: "gegenstand" },
  // Mark, 13.11.2026: die eigene KI eines Spielers — Datenwolke und Lichtkern,
  // wechselt zwischen beiden, nimmt Farben und Gestalten an, wächst mit den EP.
  { wert: "ki", name: "KI (Datenwolke / Lichtkern)", fuer: "critter" },
  // Mark, 15.11.2026 (Dungeon Crawler Carl): Mongo, vom komischen Küken zum
  // gefiederten Raptor, und der Tummy-Acher, ein Fleischklops mit einem Zahn.
  // Ei + 6 Schritte, je Farbe eine eigene Art.
  { wert: "mongo", name: "Mongo (Dschungel)", fuer: "critter" },
  { wert: "mongo_wueste", name: "Mongo (Wüste)", fuer: "critter" },
  { wert: "mongo_bonbon", name: "Mongo (Bonbon)", fuer: "critter" },
  { wert: "tummy", name: "Tummy-Acher (Fleisch)", fuer: "critter" },
  { wert: "tummy_rosa", name: "Tummy-Acher (Rosa)", fuer: "critter" },
  { wert: "tummy_lila", name: "Tummy-Acher (Lila)", fuer: "critter" },
  // Mark, 17.11.2026: süße Fledermaus, ab Stufe 3 verwandelt sie sich nach Lust
  // in einen Vampir (Kind, Teen, ~18, erwachsen) — je eine Art für Mann und Frau.
  { wert: "fledermaus", name: "Vampir-Fledermaus (Mann)", fuer: "critter" },
  { wert: "fledermaus_w", name: "Vampir-Fledermaus (Frau)", fuer: "critter" },
] as const;
export type PetArt = (typeof PET_ARTEN)[number]["wert"];

/** Was ein Drache beim Niesen spuckt — gleiche Figur, anderer Atem (feuer.png je Art). */
export type Atem = "feuer" | "eis" | "blitz";
const ATEM: Record<string, Atem> = { drache: "feuer", eisdrache: "eis", blitzdrache: "blitz" };

/** Alle Drachen-Varianten verhalten sich gleich (Wolkenlauf, Ruß, Schleim, Bärbels Ziel). */
export function istDrache(art: string): boolean {
  return art in ATEM;
}

export function atemVon(art: string): Atem {
  return ATEM[art] ?? "feuer";
}

/** Mongo oder Tummy-Acher (15.11.2026) — Familie für Sprites/Maße (tierstufen.ts). */
export function tierFamilie(art: string): "mongo" | "tummy" | null {
  if (art === "mongo" || art.startsWith("mongo_")) return "mongo";
  if (art === "tummy" || art.startsWith("tummy_")) return "tummy";
  return null;
}

/** Tiere, die laufen, klettern, aus dem Napf fressen und Ruß abschütteln. */
export function istTier(art: string): boolean {
  return tierFamilie(art) !== null;
}

/** Vampir-Fledermaus (17.11.2026): fliegt, hängt kopfüber, ab s3 Vampir. */
export function istFledermaus(art: string | null | undefined): boolean {
  return art === "fledermaus" || art === "fledermaus_w";
}

export interface PetAufSchirm {
  id: string;
  name: string;
  art: PetArt;
  besitzerId: string;
  besitzerName: string;
  /** Von welcher Seite es hereinkommt. */
  seite: "links" | "rechts";
  /** Zählt jede Ankunft hoch — neuer Wert = neuer Auftritt. */
  ankunft: number;
  /** Ungelesene Bibelstelle — sie bleibt groß, bis jemand antippt. */
  lesung?: Lesung | null;
  /** Bärbel hat eine Bibelstelle, ist aber nicht beim Besitzer: bald heimfliegen
   *  (Mark, 12.11.2026: Bibelverse nur beim Besitzer). */
  heim?: boolean;
  /** Wachstum der Drachen (Mark, 12./13.11.2026): `ei` → `baby` → `jung` → … →
   *  `ehrwuerdig`, dazwischen Zwischenformen (`jung1`, `halbstark2` …). Alles ab
   *  `jung1` hat eigene Sprites je Stufe (drachenstufen.ts). */
  stufe?: string;
  /** Freigeschaltete Fähigkeiten (klettern, niesen, springen, wolken, menue). */
  kann?: string[];
  /** Risse im Ei, 0–4. */
  risse?: number;
  /** Drachenperle (Mark, 13.11.2026): was der Drache gerade damit vorhat —
   *  siehe `PerleModus` in bewegung.ts. Wo sie liegt, erfährt das Tablet nie. */
  perle?: "spiel" | "sucht" | "gefunden" | "bringt" | "zurueck" | null;
  /** Zutraulichkeit des Spielers dieses Tablets zum Pet (unsichtbar; die
   *  Vampir-Fledermaus verwandelt sich bei hohem Wert öfter und länger). */
  zutraulich?: number;
  /** KI-Reinigungslaser (Mark, 18.11.2026): wütend — diese Pets jagt sie als
   *  Schuldige (Hauptschuldiger zuerst), bis sie einen erwischt hat. */
  jagd?: string[];
  /** Einer davon ist gerade auf einem anderen Tablet der Party. */
  jagdDa?: boolean;
}

export interface Lesung {
  stelle: string;
  /** Der Vers (gern leicht umformuliert), steht im aufgeschlagenen Buch. */
  zitat: string;
}

export interface Haeufchen {
  id: string;
  petId: string;
  /** Anteile 0..1 der Bildschirmbreite/-höhe. */
  x: number;
  y: number;
  /** Häufchen (antippen), Brandfleck vom Feuerniesen/Blitz (wegwischen),
   *  Raureif vom Eisdrachen (wegwischen),
   *  Bärbels verlorene Seite (antippen = aufheben) oder Schleim vom
   *  Tentakelmonster (wegwischen). Napf: Futternapf, bis ein Drache ihn leer frisst. */
  art?: "haeufchen" | "brand" | "seite" | "schleim" | "frost" | "napf" | "perle" | "krater" | "eiskrater" | "datenpaket";
  erstellt?: string;
  /** Perle: kam von einem anderen Tablet angeflogen (fliegt herein statt aufzuleuchten). */
  geworfen?: boolean;
}

export type PetNachricht =
  | { typ: "pets"; daten: PetAufSchirm[] }
  | { typ: "haeufchen"; daten: Haeufchen[] }
  | { typ: "vorlesen"; petId: string; stelle: string; zitat: string }
  /** Feuerball von einem anderen Tablet: fliegt von `seite` herein, schlägt nach `ms` bei x/y (Anteile) ein. */
  | { typ: "feuerball"; art: string; seite: "links" | "rechts"; x: number; y: number; ms: number };

/** Pet-Art eines Critters/Gegenstands, bei Drachen am Critter samt Wachstumsstand. */
export interface PetStand {
  id: string;
  art: PetArt | null;
  /** Nur Drachen und KIs an einem Critter wachsen. */
  waechst: boolean;
  stufe: string | null;
  /** EP seit dem Schlüpfen; null = Ei oder Bestandsdrache, der (noch) nicht wächst. */
  gewachsen: number | null;
}

/** Was die SL als Wachstumsstufe einstellen kann (Mark, 13.11.2026) — gleiche
 *  Reihenfolge wie `SETZBARE_STUFEN` in backend/app/pets/logic.py. */
const GESTALTEN: [string, string][] = [
  ["jung", "Junger Drache"],
  ["halbstark", "Halbstarker"],
  ["jungdrache", "Jungdrache"],
  ["gross", "Drache"],
];
const mitZwischen = (gestalten: [string, string][]) =>
  gestalten.flatMap(([wert, name]) => [
    { wert, name },
    { wert: `${wert}1`, name: `${name} +1` },
    { wert: `${wert}2`, name: `${name} +2` },
  ]);
export const WACHSTUM_STUFEN: { wert: string; name: string }[] = [
  { wert: "ei", name: "Ei" },
  { wert: "baby", name: "Schlüpfling" },
  ...mitZwischen(GESTALTEN),
  { wert: "ehrwuerdig", name: "Ehrwürdiger Drache" },
];

/** Die KI (Mark, 13.11.2026) wächst in denselben 13 Schritten, ohne Ei —
 *  gleiche Reihenfolge wie `KI_FOLGE` in backend/app/pets/logic.py. */
export const KI_FOLGE = [
  "funke", "funke1", "funke2",
  "keim", "keim1", "keim2",
  "geist", "geist1", "geist2",
  "wesen", "wesen1", "wesen2",
  "entitaet",
] as const;
export const KI_STUFEN: { wert: string; name: string }[] = [
  ...mitZwischen([
    ["funke", "Funke"],
    ["keim", "Keim"],
    ["geist", "Geist"],
    ["wesen", "Wesen"],
  ]),
  { wert: "entitaet", name: "Entität" },
];

/** Mongo und Tummy-Acher (15.11.2026): Ei + 6 Schritte — gleiche Reihenfolge
 *  wie `TIER_FOLGE` in backend/app/pets/logic.py. */
export function tierStufen(art: string | null | undefined): { wert: string; name: string }[] {
  const mongo = tierFamilie(art ?? "") === "mongo";
  const namen = istFledermaus(art)
    ? ["Fledermäuschen", "Fledermaus", "Vampir: Kind", "Vampir: Teen", "Vampir: ~18", "Vampir: erwachsen"]
    : mongo
      ? ["Küken", "Küken +1", "Halbstarker", "Halbstarker +1", "Junger Raptor", "Raptor"]
      : ["Klöpschen", "Klöpschen +1", "Klops", "Klops +1", "Großer Klops", "Riesenklops"];
  return [{ wert: "ei", name: "Ei" }, ...namen.map((name, i) => ({ wert: `s${i + 1}`, name }))];
}

export function istKi(art: string | null | undefined): boolean {
  return art === "ki";
}

export const petsApi = {
  /** `critterId` kann auch die id eines Gegenstands sein (Bärbel). */
  artLesen: (cid: string, critterId: string) => api.get<PetStand>(`/api/campaigns/${cid}/pets/${critterId}`),
  artSetzen: (cid: string, critterId: string, art: PetArt | null) =>
    api.put<PetStand>(`/api/campaigns/${cid}/pets/${critterId}`, { art }),
  /** SL stellt die Wachstumsstufe eines Drachen ein; er wächst danach normal weiter. */
  wachstumSetzen: (cid: string, critterId: string, stufe: string) =>
    api.put<PetStand>(`/api/campaigns/${cid}/pets/${critterId}/wachstum`, { stufe }),
  /** SL: alle Spuren (Häufchen, Brand, Raureif, Schleim, Seiten) von allen Tablets; Näpfe bleiben. */
  sauberMachen: (cid: string) => api.post<{ entfernt: number }>(`/api/campaigns/${cid}/pets/saubermachen`, {}),
  /** Tierfutter verfüttern (12.11.2026): ein Stück weg, ein Napf auf den eigenen Bildschirm. */
  fuettern: (cid: string, itemId: string) =>
    api.post<{ text: string }>(`/api/campaigns/${cid}/pets/fuettern/${itemId}`, {}),
  /** SL koppelt eine KI an einen Gegenstand (leer = lösen); neu gekoppelt ist sie an. */
  kiKoppeln: (cid: string, itemId: string, kiPersonId: string | null) =>
    api.put<KiKopplung>(`/api/campaigns/${cid}/pets/ki-gegenstand/${itemId}`, { kiPersonId }),
  /** Besitzer (oder SL) schaltet das Desktop-Pet der KI an/aus. */
  kiAktiv: (cid: string, itemId: string, aktiv: boolean) =>
    api.put<KiKopplung>(`/api/campaigns/${cid}/pets/ki-gegenstand/${itemId}/aktiv`, { aktiv }),
};

/** KI-Begleiter am Gegenstand (15.11.2026). */
export interface KiKopplung {
  id: string;
  kiPersonId: string;
  kiAktiv: boolean;
  kiName: string;
}

/**
 * Live-Leitung fürs Pet. Gleiches Wiederverbinden wie bei den Mitteilungen.
 * Gibt `senden` und `schliessen` zurück.
 */
export function verbindePets(
  campaignId: string,
  onNachricht: (n: PetNachricht) => void,
): { senden: (n: object) => void; schliessen: () => void } {
  let socket: WebSocket | null = null;
  let versuch = 0;
  let zu = false;
  let timer: number | undefined;

  const verbinde = () => {
    if (zu) return;
    const schema = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${schema}//${window.location.host}/api/campaigns/${campaignId}/pets/live`);
    socket.onopen = () => {
      versuch = 0;
    };
    socket.onmessage = (ev) => {
      try {
        onNachricht(JSON.parse(ev.data) as PetNachricht);
      } catch {
        /* kaputte Nachricht ignorieren */
      }
    };
    socket.onclose = () => {
      if (zu) return;
      versuch += 1;
      timer = window.setTimeout(verbinde, Math.min(1000 * 2 ** (versuch - 1), 15000));
    };
    socket.onerror = () => socket?.close();
  };
  verbinde();

  return {
    senden: (n) => {
      if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(n));
    },
    schliessen: () => {
      zu = true;
      window.clearTimeout(timer);
      socket?.close();
    },
  };
}
