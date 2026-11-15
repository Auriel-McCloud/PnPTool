// Erzeugt von docs/assets/critter-pet/dcc_exportieren.py — nicht von Hand ändern.
// Mongo und Tummy-Acher (Mark, 15.11.2026): Ei + 6 Schritte, je Farbe eine Art,
// alle Farben einer Familie mit denselben Maßen (frontend/public/pets/<art>/<stufe>/sprite.json).

export interface TierStufe {
  breite: number;
  hoehe: number;
  fussLuft: number;
  /** Maul im Sprite (blickt nach rechts) — dort landet, was er frisst. */
  maul: readonly [number, number];
  /** Kopf im Schlaf — dort steigt das Zzz auf. */
  schlafZ: readonly [number, number];
}

export const TIER_STUFEN: Record<"mongo" | "tummy", Record<string, TierStufe>> = {
  mongo: {
    s1: { breite: 28, hoehe: 32, fussLuft: 1, maul: [22, 23], schlafZ: [18, 12] },
    s2: { breite: 42, hoehe: 42, fussLuft: 2, maul: [36, 30], schlafZ: [30, 20] },
    s3: { breite: 64, hoehe: 50, fussLuft: 1, maul: [56, 37], schlafZ: [49, 28] },
    s4: { breite: 84, hoehe: 58, fussLuft: 0, maul: [76, 45], schlafZ: [67, 36] },
    s5: { breite: 106, hoehe: 64, fussLuft: 2, maul: [97, 49], schlafZ: [86, 42] },
    s6: { breite: 124, hoehe: 68, fussLuft: 2, maul: [112, 55], schlafZ: [101, 48] },
  },
  tummy: {
    s1: { breite: 24, hoehe: 28, fussLuft: 0, maul: [13, 19], schlafZ: [12, 13] },
    s2: { breite: 28, hoehe: 34, fussLuft: 0, maul: [16, 22], schlafZ: [15, 13] },
    s3: { breite: 34, hoehe: 40, fussLuft: 1, maul: [20, 25], schlafZ: [19, 13] },
    s4: { breite: 42, hoehe: 46, fussLuft: 1, maul: [24, 29], schlafZ: [23, 14] },
    s5: { breite: 46, hoehe: 52, fussLuft: 1, maul: [28, 32], schlafZ: [27, 15] },
    s6: { breite: 52, hoehe: 58, fussLuft: 1, maul: [33, 36], schlafZ: [31, 16] },
  },
};
