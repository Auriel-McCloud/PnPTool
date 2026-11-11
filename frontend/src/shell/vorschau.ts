/**
 * Vorschaubild statt Original für Übersichten und Kacheln (Mark, 11.11.2026:
 * „in der grundsätzlichen Ansicht nur so groß wie nötig, damit es schneller
 * lädt“). Das Backend baut die Vorschau beim ersten Abruf und cacht sie
 * (siehe backend/app/bilder/vorschau.py).
 *
 * Detailansicht, Großbild und Bild-Pushs an die Spieler nehmen weiter die
 * Original-URL — dort soll das Bild in voller Größe aufgehen.
 *
 * Nur eigene Uploads (`/uploads/<kampagne>/<datei>`) werden umgeschrieben;
 * data:-URLs, externe Bilder (Spotify) und statische Assets bleiben, wie sie
 * sind.
 */
export type VorschauGroesse = "klein" | "kachel";

// Kürzere Bildseite in Pixeln — muss zu ERLAUBTE_BREITEN im Backend passen.
// "klein" für Avatare bis ~64 px, "kachel" für Kacheln bis ~240 px bei
// doppelter Pixeldichte (Tablet).
const KURZE_SEITE: Record<VorschauGroesse, number> = { klein: 128, kachel: 480 };

const UPLOAD = /^\/uploads\/([^/]+)\/([^/?#]+)$/;

export function vorschau(url: string | null | undefined, groesse: VorschauGroesse = "kachel"): string | undefined {
  if (!url) return undefined;
  const treffer = UPLOAD.exec(url);
  if (!treffer || treffer[1] === "_vorschau") return url;
  return `/uploads/_vorschau/${KURZE_SEITE[groesse]}/${treffer[1]}/${treffer[2]}`;
}
