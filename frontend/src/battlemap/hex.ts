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

/** Axiales Raster, das ein Rechteck füllt — kein Rhombus mit leeren Ecken. */
export function hexRasterRechteck(
  breite: number,
  hoehe: number,
  size: number,
  ox: number,
  oy: number,
): { q: number; r: number }[] {
  if (breite <= 0 || hoehe <= 0 || size <= 0) return [];
  const liste: { q: number; r: number }[] = [];
  const oben = pixelNachHex(breite / 2, 0, size, ox, oy).r - 1;
  const unten = pixelNachHex(breite / 2, hoehe, size, ox, oy).r + 1;
  for (let r = oben; r <= unten; r++) {
    const y = size * (3 / 2) * r + oy;
    const qLinks = pixelNachHex(0, y, size, ox, oy).q - 1;
    const qRechts = pixelNachHex(breite, y, size, ox, oy).q + 1;
    for (let q = qLinks; q <= qRechts; q++) liste.push({ q, r });
  }
  return liste;
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
