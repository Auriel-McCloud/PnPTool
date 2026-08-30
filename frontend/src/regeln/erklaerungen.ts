import { useSyncExternalStore } from "react";
import { api } from "../api/client";

/**
 * Erklärungen zu Fachbegriffen — die Datenseite des Tooltip-Systems.
 *
 * Alle Texte werden **einmal je Kampagne** geladen und liegen dann hier.
 * Einzeln nachzuladen hiesse bei jedem Antippen eine Anfrage, und die
 * Oberfläche muss ohnehin vorher wissen, wozu überhaupt etwas hinterlegt
 * ist — sonst stünde neben jedem Begriff ein Zeichen, das ins Leere führt.
 *
 * Bewusst ein Modulzustand statt eines Kontexts: die Zeichen sitzen quer
 * durch die ganze Oberfläche (Charakterblatt, Gegenstände, später Regeln),
 * ein Provider müsste sonst um alles herumgelegt und in jeder neuen Ansicht
 * wieder mitgedacht werden.
 */

export interface Erklaerung {
  schluessel: string;
  titel: string;
  text: string;
  /** HAND = geschrieben, KI = erzeugt und noch von niemandem gegengelesen. */
  quelle: "HAND" | "KI";
}

const SPEICHER_SCHLUESSEL = "pnptool.erklaerungen";

let texte = new Map<string, Erklaerung>();
let geladenFuer: string | null = null;
let laeuft: Promise<void> | null = null;
// Der Schalter überlebt das Neuladen: wer die Erklärungen anhat, will sie
// beim nächsten Öffnen nicht wieder einschalten müssen.
let an = typeof localStorage !== "undefined" && localStorage.getItem(SPEICHER_SCHLUESSEL) === "an";

// useSyncExternalStore braucht einen Wert, der sich bei Änderung *ändert* —
// eine Map bliebe dieselbe Referenz. Deshalb ein Zähler als Schnappschuss.
let stand = 0;
const hoerer = new Set<() => void>();

function melden() {
  stand += 1;
  for (const h of hoerer) h();
}

function abonnieren(h: () => void) {
  hoerer.add(h);
  return () => {
    hoerer.delete(h);
  };
}

async function laden(campaignId: string) {
  if (geladenFuer === campaignId || laeuft) return;
  laeuft = api
    .get<Erklaerung[]>(`/api/campaigns/${campaignId}/erklaerungen`)
    .then((liste) => {
      texte = new Map(liste.map((e) => [e.schluessel, e]));
      geladenFuer = campaignId;
      melden();
    })
    // Fehlende Erklärungen sind kein Grund, eine Ansicht scheitern zu lassen
    .catch(() => undefined)
    .finally(() => {
      laeuft = null;
    });
  await laeuft;
}

export function schalteErklaerungen() {
  an = !an;
  try {
    localStorage.setItem(SPEICHER_SCHLUESSEL, an ? "an" : "aus");
  } catch {
    // Privater Modus o.ä. — dann gilt der Schalter eben nur für diese Sitzung
  }
  melden();
}

/** Nach dem Schreiben durch die Spielleitung den Bestand nachziehen. */
export async function speichereErklaerung(
  campaignId: string,
  schluessel: string,
  titel: string,
  text: string,
): Promise<void> {
  const gespeichert = await api.put<Erklaerung>(
    `/api/campaigns/${campaignId}/erklaerungen/${schluessel}`,
    { titel, text, quelle: "HAND" },
  );
  // Neue Map, damit useSyncExternalStore die Änderung überhaupt bemerken kann
  texte = new Map(texte);
  if (gespeichert.text) texte.set(schluessel, gespeichert);
  else texte.delete(schluessel);
  melden();
}

export function useErklaerungen(campaignId: string | null) {
  useSyncExternalStore(abonnieren, () => stand);
  if (campaignId && geladenFuer !== campaignId) void laden(campaignId);
  return {
    an,
    /** Text zu einem Schlüssel, oder undefined wenn noch keiner da ist. */
    zu: (schluessel: string) => texte.get(schluessel),
    /** Wieviele Begriffe überhaupt erklärt sind — für den Schalter. */
    anzahl: texte.size,
  };
}

/** Einheitliche Schlüssel, damit Anzeige und Ablage nicht auseinanderlaufen. */
export const schluessel = {
  trait: (name: string) => `trait:${name}`,
  bogen: (feld: string) => `bogen:${feld}`,
  regel: (begriff: string) => `regel:${begriff}`,
};
