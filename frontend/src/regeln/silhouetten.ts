/**
 * Körpersilhouetten für die Chrom-Karte — im Stil der Metroid-Ausrüstungsanzeige.
 *
 * Mark: *"in metroid fusion gab es etwas ähnliches, so in etwa hab ich mir das
 * vorgestellt"* — Drahtgitter-Figur in der Mitte, Panels aussen, dünne Linien
 * vom Panel zum jeweiligen Körperteil.
 *
 * Als SVG-Pfade statt Bilddateien: skaliert verlustfrei, nimmt die Themefarben
 * an (Cyberpunk wie Hextechpunk) und braucht kein Bildmaterial, das jemand
 * pflegen müsste.
 *
 * **Zonen berühren sich nicht.** Zwischen Kopf und Torso, Torso und Armen,
 * Torso und Beinen bleibt Luft. Ein erster Versuch mit aneinandergrenzenden
 * Pfaden ergab am Bildschirm einen einzigen schwarzen Klumpen — man sah keine
 * Zone mehr. Die Trennung ist hier keine Kosmetik, sondern der Zweck.
 *
 * Je Zone zwei Pfade:
 *  - `umriss` — die Fläche, anklickbar und je nach Belegung eingefärbt
 *  - `linien` — Binnenzeichnung (Panzerungsfugen), rein optisch
 *
 * Koordinatensystem 200 × 210, Figur etwa 20…180 breit.
 */

export type Silhouette = "maennlich" | "weiblich";

export type ZonenName = "Kopf" | "Arme" | "Torso" | "Beine";

export interface Zone {
  umriss: string;
  linien: string;
}

export type ZonenPfade = Record<ZonenName, Zone>;

/** Breite Schultern, gerader Rumpf. */
export const MAENNLICH: ZonenPfade = {
  // Helm mit Kinnpartie, frei stehend über den Schultern.
  Kopf: {
    umriss:
      "M100 8c-14 0-24 11-24 25 0 9 3 16 9 21v6h30v-6c6-5 9-12 9-21 0-14-10-25-24-25z",
    linien: "M83 33h34M88 20c3-4 7-6 12-6s9 2 12 6M90 47h20",
  },
  // Beide Arme, deutlich vom Rumpf abgesetzt.
  Arme: {
    umriss:
      "M58 74c-7 2-11 7-12 15l-5 38c-1 6 3 11 8 11 5 0 8-4 9-9l5-33 5-12z" +
      "M142 74c7 2 11 7 12 15l5 38c1 6-3 11-8 11-5 0-8-4-9-9l-5-33-5-12z",
    linien: "M52 94l-4 28M148 94l4 28M45 120h12M143 120h12M55 84h10M135 84h10",
  },
  // Rumpf: Schulterlinie, Taille, Hüfte.
  Torso: {
    umriss:
      "M74 68c8-6 16-9 26-9s18 3 26 9c5 4 7 8 7 14l-3 28-3 30c0 5-4 8-9 8H84c-5 0-9-3-9-8l-3-30-3-28c0-6 2-10 7-14z",
    linien: "M100 62v82M78 84h44M77 102h46M80 122h40M88 68l-3 76M112 68l3 76",
  },
  // Zwei getrennte Beine mit Lücke in der Mitte.
  Beine: {
    umriss:
      "M79 158h18l1 30-2 18c0 4-4 7-8 7s-8-3-8-7l-2-18z" +
      "M103 158h18l1 30-2 18c0 4-4 7-8 7s-8-3-8-7l-2-18z",
    linien: "M82 176h13M106 176h13M83 192h11M106 192h11M81 202h14M105 202h14",
  },
};

/** Schmalere Schultern, betonte Taille, längere Beinlinie. */
export const WEIBLICH: ZonenPfade = {
  Kopf: {
    umriss:
      "M100 8c-13 0-22 11-22 25 0 9 3 16 8 21v6h28v-6c5-5 8-12 8-21 0-14-9-25-22-25z",
    linien: "M84 33h32M89 20c3-4 7-6 11-6s8 2 11 6M91 47h18",
  },
  Arme: {
    umriss:
      "M66 76c-6 2-10 7-11 14l-5 36c-1 6 3 10 8 10 4 0 7-4 8-9l5-31 5-11z" +
      "M134 76c6 2 10 7 11 14l5 36c1 6-3 10-8 10-4 0-7-4-8-9l-5-31-5-11z",
    linien: "M60 96l-5 32M140 96l5 32M53 126h12M135 126h12M63 86h9M128 86h9",
  },
  // Taille eingezogen, Hüfte breiter — die Silhouette macht den Unterschied.
  Torso: {
    umriss:
      "M80 68c6-6 13-9 20-9s14 3 20 9c5 4 7 8 6 13l-5 26c-1 5-4 8-8 10 5 3 8 6 9 11l3 23c1 5-3 9-8 9H83c-5 0-9-4-8-9l3-23c1-5 4-8 9-11-4-2-7-5-8-10l-5-26c-1-5 1-9 6-13z",
    linien: "M100 62v80M82 82h36M88 102h24M81 122h38M89 68l-3 74M111 68l3 74",
  },
  Beine: {
    umriss:
      "M81 158h17l1 30-2 18c0 4-3 7-8 7s-8-3-8-7l-2-18z" +
      "M102 158h17l1 30-2 18c0 4-3 7-8 7s-8-3-8-7l-2-18z",
    linien: "M84 176h11M105 176h11M85 192h10M105 192h10M83 202h13M104 202h13",
  },
};

export const SILHOUETTEN: Record<Silhouette, ZonenPfade> = {
  maennlich: MAENNLICH,
  weiblich: WEIBLICH,
};

export const ZONEN: ZonenName[] = ["Kopf", "Arme", "Torso", "Beine"];

/**
 * Wo die Verbindungslinie an der Figur andockt — am **Rand** der Zone, damit
 * die Linie nicht über die Figur läuft.
 */
export const ANDOCKPUNKTE: Record<ZonenName, { x: number; y: number }> = {
  // Werte aus den gemessenen Zonengrenzen abgeleitet (getBBox), damit der
  // Punkt wirklich am Rand der Fläche sitzt und nicht daneben schwebt.
  Kopf: { x: 122, y: 30 },   // Kopf  x 76..124, y 8..60
  Arme: { x: 43, y: 106 },   // Arme  x 41..159, y 74..138 (linker Arm)
  Torso: { x: 131, y: 104 }, // Torso x 69..133, y 59..148
  Beine: { x: 120, y: 186 }, // Beine x 78..122, y 158..213
};
