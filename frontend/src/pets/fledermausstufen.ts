// Erzeugt von docs/assets/critter-pet/fledermaus_exportieren.py — nicht von Hand ändern.
// Vampir-Fledermaus (Mark, 17.11.2026): Ei + 6 Schritte, Mann und Frau mit denselben
// Rahmen je Stufe (frontend/public/pets/<art>/<stufe>/sprite.json). Ab s3 Vampirgestalt (v_*).

export interface FledermausStufe {
  breite: number;
  hoehe: number;
  /** Leerraum unter den Füßen (Boden-Streifen). */
  fussLuft: number;
  /** Zeile der Krallen beim Kopfüber-Hängen (Hänge-Streifen). */
  griff: number;
  /** Maul beim Stehen — dort landet das Futter. */
  maul: readonly [number, number];
  kopfStehen: readonly [number, number];
  kopfHaengen: readonly [number, number];
  kopfFlug: readonly [number, number];
  /** Kopf der Vampirgestalt (null: noch keine Vampirgestalt). */
  kopfVampir: readonly [number, number] | null;
}

export const FLEDERMAUS_STUFEN: Record<string, FledermausStufe> = {
  s1: { breite: 42, hoehe: 44, fussLuft: 0, griff: 1, maul: [21, 28], kopfStehen: [21, 19], kopfHaengen: [21, 23], kopfFlug: [21, 6], kopfVampir: null },
  s2: { breite: 50, hoehe: 52, fussLuft: 0, griff: 1, maul: [25, 34], kopfStehen: [25, 24], kopfHaengen: [25, 26], kopfFlug: [25, 6], kopfVampir: null },
  s3: { breite: 60, hoehe: 60, fussLuft: 0, griff: 1, maul: [30, 40], kopfStehen: [30, 29], kopfHaengen: [30, 29], kopfFlug: [30, 6], kopfVampir: [30, 20] },
  s4: { breite: 68, hoehe: 68, fussLuft: 0, griff: 1, maul: [34, 46], kopfStehen: [34, 33], kopfHaengen: [34, 33], kopfFlug: [34, 5], kopfVampir: [34, 15] },
  s5: { breite: 76, hoehe: 76, fussLuft: 0, griff: 1, maul: [38, 52], kopfStehen: [38, 38], kopfHaengen: [38, 36], kopfFlug: [38, 5], kopfVampir: [38, 10] },
  s6: { breite: 84, hoehe: 86, fussLuft: 0, griff: 1, maul: [42, 60], kopfStehen: [42, 44], kopfHaengen: [42, 40], kopfFlug: [42, 6], kopfVampir: [42, 14] },
};

/** Takte aller Streifen (frames × ms). */
export const FLEDERMAUS_TAKT: Record<string, { frames: number; ms: number }> = {
  flattern: { frames: 8, ms: 70 },
  haengen: { frames: 24, ms: 110 },
  schlafen: { frames: 24, ms: 150 },
  stehen: { frames: 24, ms: 110 },
  fressen: { frames: 16, ms: 90 },
  freuen: { frames: 8, ms: 90 },
  taumeln: { frames: 8, ms: 60 },
  v_idle: { frames: 24, ms: 110 },
  v_lauf: { frames: 16, ms: 70 },
  v_freuen: { frames: 12, ms: 90 },
  v_idle_hut: { frames: 24, ms: 110 },
  v_lauf_hut: { frames: 16, ms: 70 },
  v_freuen_hut: { frames: 12, ms: 90 },
  v_hut: { frames: 12, ms: 90 },
  verwandeln: { frames: 16, ms: 70 },
};
