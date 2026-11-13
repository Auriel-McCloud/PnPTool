// Erzeugt von docs/assets/critter-pet/stufen_exportieren.py — nicht von Hand ändern.
// Maße der großen Drachen-Stufen (Mark, 13.11.2026) und Schlaf-Anker aller Stufen,
// gleiche Werte wie frontend/public/pets/<art>/<stufe>/sprite.json.

/** Übergang wach → eingekringelt (einkringeln.png); rückwärts = aufwachen. */
export const EINKRINGELN = { frames: 17, ms: 80 } as const;

export interface DrachenStufe {
  breite: number;
  hoehe: number;
  fussLuft: number;
  /** Maul im Sprite — dort setzen Feuer und Futter an. */
  maul: readonly [number, number];
  /** Wo das Zzz über dem Schlafkringel sitzt (Kopf-x, Oberkante). */
  schlafZ: readonly [number, number];
  /** Der Atem wächst mit. */
  feuerSkala: number;
}

/** Schlüssel = `stufe` im Pet-Dict = Ordner unter /pets/<art>/. */
export const DRACHEN_STUFEN: Record<string, DrachenStufe> = {
  jung1: { breite: 90, hoehe: 42, fussLuft: 1, maul: [79, 23], schlafZ: [50, 7], feuerSkala: 1.05 },
  jung2: { breite: 94, hoehe: 42, fussLuft: 1, maul: [84, 22], schlafZ: [52, 6], feuerSkala: 1.1 },
  halbstark: { breite: 100, hoehe: 44, fussLuft: 1, maul: [89, 23], schlafZ: [56, 7], feuerSkala: 1.15 },
  halbstark1: { breite: 106, hoehe: 46, fussLuft: 1, maul: [92, 24], schlafZ: [58, 8], feuerSkala: 1.2 },
  halbstark2: { breite: 110, hoehe: 48, fussLuft: 1, maul: [98, 24], schlafZ: [62, 8], feuerSkala: 1.25 },
  jungdrache: { breite: 116, hoehe: 50, fussLuft: 1, maul: [101, 25], schlafZ: [64, 8], feuerSkala: 1.3 },
  jungdrache1: { breite: 120, hoehe: 52, fussLuft: 1, maul: [106, 26], schlafZ: [66, 9], feuerSkala: 1.35 },
  jungdrache2: { breite: 126, hoehe: 54, fussLuft: 1, maul: [110, 27], schlafZ: [69, 11], feuerSkala: 1.4 },
  gross: { breite: 132, hoehe: 54, fussLuft: 1, maul: [114, 26], schlafZ: [71, 9], feuerSkala: 1.45 },
  gross1: { breite: 136, hoehe: 56, fussLuft: 1, maul: [118, 27], schlafZ: [74, 10], feuerSkala: 1.5 },
  gross2: { breite: 142, hoehe: 60, fussLuft: 1, maul: [122, 29], schlafZ: [77, 14], feuerSkala: 1.55 },
  ehrwuerdig: { breite: 148, hoehe: 62, fussLuft: 1, maul: [128, 30], schlafZ: [80, 16], feuerSkala: 1.6 },
};

/** Zzz-Anker für Schlüpfling und jungen Drachen (alte Rahmen). */
export const SCHLAF_Z: Record<string, readonly [number, number]> = {
  baby: [31, 14],
  jung: [48, 8],
};
