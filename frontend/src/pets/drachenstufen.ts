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
  halbstark: { breite: 100, hoehe: 44, fussLuft: 1, maul: [89, 23], schlafZ: [56, 7], feuerSkala: 1.15 },
  jungdrache: { breite: 116, hoehe: 50, fussLuft: 1, maul: [101, 25], schlafZ: [64, 8], feuerSkala: 1.3 },
  gross: { breite: 132, hoehe: 54, fussLuft: 1, maul: [114, 26], schlafZ: [71, 9], feuerSkala: 1.45 },
  ehrwuerdig: { breite: 148, hoehe: 62, fussLuft: 1, maul: [128, 30], schlafZ: [80, 16], feuerSkala: 1.6 },
};

/** Zzz-Anker für Schlüpfling und jungen Drachen (alte Rahmen). */
export const SCHLAF_Z: Record<string, readonly [number, number]> = {
  baby: [31, 14],
  jung: [48, 8],
};
