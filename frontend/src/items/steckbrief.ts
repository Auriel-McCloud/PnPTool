import type { Gegenstand } from "./api";
import { schadenArtFuerWaffe, schadenArtLabel } from "./api";

/**
 * Kurzer "Steckbrief"-Text für die Kachel — die wichtigsten Kampfwerte auf
 * einen Blick, ohne erst hineinklicken zu müssen (Mark, 10.10.2026: "wir
 * müssen den Steckbrief außen auch schon sichtbar machen, damit ich den
 * Unterschied sehe"). Spiegelt dieselbe Logik wie die "Steckbrief"-Liste im
 * ausführlichen Gegenstandsfenster (traits/CharacterSheetPanel.tsx,
 * Übersicht-Tab) — nur als eine knappe Zeile statt einer Aufzählung, damit
 * die Kachel ihre feste Höhe behält (Leitprinzip "nie scrollen").
 */
const CHROM_TYPEN = new Set(["Cyberware", "Bioware", "Hexware"]);
const FAHRZEUG_TYPEN = new Set(["Fahrzeug", "Drohne"]);

export function steckbriefKurz(item: Gegenstand): string[] {
  const teile: string[] = [];

  if (item.typ === "Rüstung") {
    teile.push(`Reduktion ${item.ruestungReduktionBasis}`);
    teile.push(`${item.ruestungKaestchenAktuell}/${item.ruestungKaestchenMax} Kästchen`);
  } else if (item.typ === "Waffe" && item.kraft > 0) {
    const basis = `Schaden ${item.kraft}`;
    teile.push(`${basis} · ${schadenArtLabel(schadenArtFuerWaffe(item.schadenArt))}`);
  } else if (item.typ === "Waffe") {
    teile.push(schadenArtLabel(schadenArtFuerWaffe(item.schadenArt)));
  }

  if (item.typ !== "Waffe" && item.istWaffe && item.schaden > 0) {
    const art = schadenArtLabel(schadenArtFuerWaffe(item.schadenArt));
    teile.push(`Schaden ${item.schaden} · ${art}`);
  } else if (item.typ !== "Waffe" && item.istWaffe) {
    teile.push(schadenArtLabel(schadenArtFuerWaffe(item.schadenArt)));
  }

  if (CHROM_TYPEN.has(item.typ) && item.wVerlust > 0) {
    teile.push(`−${item.wVerlust.toLocaleString("de-AT")} WK`);
  }

  if (item.initiativeBonus !== 0) {
    teile.push(`Init. ${item.initiativeBonus > 0 ? "+" : ""}${item.initiativeBonus}`);
  }

  if (item.zusatzaktionen !== 0) {
    teile.push(item.zusatzaktionen === -1 ? "Zusatzaktion jede Runde" : `Zusatzaktion ${item.zusatzaktionen}×/Kampf`);
  }

  // Bonuswürfel gelten unabhängig vom Typ (jeder ausgerüstete Gegenstand
  // kann sie tragen) — siehe items/api.ts::Gegenstand.traitBoni.
  for (const [name, wert] of Object.entries(item.traitBoni ?? {})) {
    teile.push(`${name} +${wert}`);
  }
  for (const [name, wert] of Object.entries(item.ausruestungsfertigkeiten ?? {})) {
    teile.push(`${name} ${wert}`);
  }

  if (FAHRZEUG_TYPEN.has(item.typ) && item.stufe > 0) {
    teile.push(`Stufe ${item.stufe}`);
  }

  if (item.typ === "Riggerkonsole") {
    teile.push(`Rigger ${item.riggerBonus >= 0 ? "+" : ""}${item.riggerBonus} · ${item.maxDrohnen} Drohnen`);
  }

  if (item.typ === "Commlink" && item.cyberwall > 0) {
    teile.push(`I.C.E. ${item.cyberwall}`);
  }

  if (item.typ === "Cyberdeck") {
    const werte: [string, number][] = (
      [
        ["B", item.deckBruteForce],
        ["S", item.deckSchleichen],
        ["D", item.deckDaten],
        ["K", item.deckKompilieren],
        ["EW", item.deckElectronicWarfare],
        ["N", item.deckMatrixNavigation],
      ] as [string, number][]
    ).filter(([, w]) => w > 0);
    if (werte.length > 0) teile.push(werte.map(([k, w]) => `${k}${w}`).join(" "));
    if (item.cyberwall > 0) teile.push(`Cyberwall +${item.cyberwall}`);
  }

  if (item.istBehaelter && item.kapazitaet > 0) {
    teile.push(`Fasst ${item.kapazitaet} kg`);
  }

  return teile;
}
