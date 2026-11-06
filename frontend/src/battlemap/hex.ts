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
