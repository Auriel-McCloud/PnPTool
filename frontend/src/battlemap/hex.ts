/** Axiale Hex (pointy-top) für die Battlemap-Leinwand. */

export function hexNachPixel(q: number, r: number, size: number, ox: number, oy: number) {
  return {
    x: size * Math.sqrt(3) * (q + r / 2) + ox,
    y: size * (3 / 2) * r + oy,
  };
}

function cubeRunden(x: number, y: number, z: number): { q: number; r: number } {
  let rx = Math.round(x);
  let ry = Math.round(y);
  let rz = Math.round(z);
  const dx = Math.abs(rx - x);
  const dy = Math.abs(ry - y);
  const dz = Math.abs(rz - z);
  if (dx > dy && dx > dz) rx = -ry - rz;
  else if (dy > dz) ry = -rx - rz;
  return { q: rx, r: rz };
}

export function pixelNachHex(x: number, y: number, size: number, ox: number, oy: number) {
  const px = (x - ox) / size;
  const py = (y - oy) / size;
  const q = (Math.sqrt(3) / 3) * px - (1 / 3) * py;
  const r = (2 / 3) * py;
  return cubeRunden(q, -q - r, r);
}

export function hexEcken(cx: number, cy: number, size: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const winkel = (Math.PI / 180) * (60 * i - 30);
    pts.push(`${cx + size * Math.cos(winkel)},${cy + size * Math.sin(winkel)}`);
  }
  return pts.join(" ");
}

export const NACHBARN: [number, number][] = [
  [1, 0],
  [1, -1],
  [0, -1],
  [-1, 0],
  [-1, 1],
  [0, 1],
];

export function distanz(q1: number, r1: number, q2: number, r2: number) {
  return (Math.abs(q1 - q2) + Math.abs(q1 + r1 - q2 - r2) + Math.abs(r1 - r2)) / 2;
}

export function yFelder(q: number, r: number, gross: boolean, drehung = 0): [number, number][] {
  if (!gross) return [[q, r]];
  const k = ((drehung % 6) + 6) % 6;
  const [dq1, dr1] = NACHBARN[k];
  const [dq2, dr2] = NACHBARN[(k + 1) % 6];
  return [
    [q, r],
    [q + dq1, r + dr1],
    [q + dq2, r + dr2],
  ];
}

export function reichweite(sportlichkeit: number, fliegen: number | null) {
  if (fliegen !== null) return 3 + fliegen * 2;
  return 3 + sportlichkeit;
}

/**
 * Axiales Raster, das ein Rechteck füllt — kein Rhombus mit leeren Ecken.
 * `x0`/`y0` ist die linke obere Ecke des Rechtecks in Karten-Pixeln (beim
 * Schwenken liegt der sichtbare Ausschnitt nicht mehr bei 0/0).
 */
export function hexRasterRechteck(
  breite: number,
  hoehe: number,
  size: number,
  ox: number,
  oy: number,
  x0 = 0,
  y0 = 0,
): { q: number; r: number }[] {
  if (breite <= 0 || hoehe <= 0 || size <= 0) return [];
  const liste: { q: number; r: number }[] = [];
  const oben = pixelNachHex(x0 + breite / 2, y0, size, ox, oy).r - 1;
  const unten = pixelNachHex(x0 + breite / 2, y0 + hoehe, size, ox, oy).r + 1;
  for (let r = oben; r <= unten; r++) {
    const y = size * (3 / 2) * r + oy;
    const qLinks = pixelNachHex(x0, y, size, ox, oy).q - 1;
    const qRechts = pixelNachHex(x0 + breite, y, size, ox, oy).q + 1;
    for (let q = qLinks; q <= qRechts; q++) liste.push({ q, r });
  }
  return liste;
}

/** Mitte der belegten Felder in Einheiten von size (bei 3er-Y: die gemeinsame Ecke). */
function schwerpunktEinheiten(felder: [number, number][]): { x: number; y: number } {
  let sx = 0;
  let sy = 0;
  for (const [q, r] of felder) {
    sx += Math.sqrt(3) * (q + r / 2);
    sy += 1.5 * r;
  }
  return { x: sx / felder.length, y: sy / felder.length };
}

/** Mitte der belegten Felder in Pixeln. Einzelfeld = Hex-Mitte. */
export function schwerpunkt(felder: [number, number][], size: number, ox: number, oy: number) {
  const m = schwerpunktEinheiten(felder);
  return { x: m.x * size + ox, y: m.y * size + oy };
}

/** Felder rund um den Token: Nachbarn eines belegten Feldes, die nicht selbst belegt sind. */
export function ringFelder(felder: [number, number][]): [number, number][] {
  const belegt = new Set(felder.map(([q, r]) => `${q},${r}`));
  const ring = new Map<string, [number, number]>();
  for (const [q, r] of felder) {
    for (const [dq, dr] of NACHBARN) {
      const key = `${q + dq},${r + dr}`;
      if (!belegt.has(key) && !ring.has(key)) ring.set(key, [q + dq, r + dr]);
    }
  }
  return [...ring.values()];
}

/**
 * Blickrichtung 0–5 für ein angetipptes Ringfeld: Winkel von der Mitte der
 * belegten Felder zum Ringfeld, auf die nächste der sechs Hex-Richtungen
 * gerundet (Richtung i liegt bei −60·i Grad, y zeigt nach unten). Ein
 * Ringfeld genau zwischen zwei Richtungen (beim großen Token möglich) fällt
 * deterministisch auf die höhere Richtungsnummer. Kein Ringfeld = null.
 */
export function ringRichtung(felder: [number, number][], q: number, r: number): number | null {
  if (!ringFelder(felder).some(([fq, fr]) => fq === q && fr === r)) return null;
  const m = schwerpunktEinheiten(felder);
  const x = Math.sqrt(3) * (q + r / 2) - m.x;
  const y = 1.5 * r - m.y;
  const grad = (Math.atan2(y, x) * 180) / Math.PI;
  const i = Math.round(-grad / 60 - 1e-9);
  return ((i % 6) + 6) % 6;
}

/**
 * Umriss der Vereinigung der belegten Felder als Eckenliste in Einheiten von
 * size, relativ zur Mitte der Felder. Innenkanten (von zwei Hex geteilt)
 * fallen weg; `faktor` zieht den Umriss zur Mitte hin zusammen, damit der
 * Feldrand des Rasters sichtbar bleibt.
 */
export function umriss(felder: [number, number][], faktor = 1): [number, number][] {
  const m = schwerpunktEinheiten(felder);
  const punkt = new Map<string, [number, number]>();
  const kanten = new Map<string, { a: string; b: string; n: number }>();
  // Ganzzahl-Schlüssel: toFixed liefert für winzige Negativwerte "-0.0000".
  const schluessel = (x: number, y: number) => `${Math.round(x * 1e4)},${Math.round(y * 1e4)}`;
  for (const [q, r] of felder) {
    const cx = Math.sqrt(3) * (q + r / 2);
    const cy = 1.5 * r;
    const ecken: string[] = [];
    for (let i = 0; i < 6; i++) {
      const w = (Math.PI / 180) * (60 * i - 30);
      const x = cx + Math.cos(w);
      const y = cy + Math.sin(w);
      const k = schluessel(x, y);
      punkt.set(k, [x, y]);
      ecken.push(k);
    }
    for (let i = 0; i < 6; i++) {
      const a = ecken[i];
      const b = ecken[(i + 1) % 6];
      const k = a < b ? `${a}|${b}` : `${b}|${a}`;
      const e = kanten.get(k);
      if (e) e.n += 1;
      else kanten.set(k, { a, b, n: 1 });
    }
  }
  const nachbar = new Map<string, string[]>();
  for (const { a, b, n } of kanten.values()) {
    if (n !== 1) continue;
    nachbar.set(a, [...(nachbar.get(a) ?? []), b]);
    nachbar.set(b, [...(nachbar.get(b) ?? []), a]);
  }
  const start = nachbar.keys().next().value as string | undefined;
  if (!start) return [];
  const reihe: string[] = [start];
  let davor = "";
  let jetzt = start;
  for (let guard = 0; guard < 64; guard++) {
    const weiter = (nachbar.get(jetzt) ?? []).find((k) => k !== davor);
    if (!weiter || weiter === start) break;
    reihe.push(weiter);
    davor = jetzt;
    jetzt = weiter;
  }
  return reihe.map((k) => {
    const [x, y] = punkt.get(k)!;
    return [(x - m.x) * faktor, (y - m.y) * faktor] as [number, number];
  });
}

export type Ecke = { ax: number; ay: number; px: number; py: number };

/** Nächste Hex-Ecke. ax/ay bleiben bei Größe und Ursprung stabil. */
export function naechsteEcke(px: number, py: number, size: number, ox: number, oy: number): Ecke | null {
  if (size <= 0) return null;
  const mitte = pixelNachHex(px, py, size, ox, oy);
  let best: Ecke | null = null;
  let bestD = Infinity;
  const felder = [{ q: mitte.q, r: mitte.r }, ...NACHBARN.map(([dq, dr]) => ({ q: mitte.q + dq, r: mitte.r + dr }))];
  for (const feld of felder) {
    const c = hexNachPixel(feld.q, feld.r, size, ox, oy);
    for (let i = 0; i < 6; i++) {
      const winkel = (Math.PI / 180) * (60 * i - 30);
      const x = c.x + size * Math.cos(winkel);
      const y = c.y + size * Math.sin(winkel);
      const d = (x - px) ** 2 + (y - py) ** 2;
      if (d < bestD) {
        bestD = d;
        best = { ax: (x - ox) / size, ay: (y - oy) / size, px: x, py: y };
      }
    }
  }
  return best;
}
