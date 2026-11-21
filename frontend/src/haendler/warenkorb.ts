import { useEffect, useState } from "react";
import type { SortimentEintrag } from "./api";
import { ersterKaufTrifft } from "../rassen/gratisKauf";

/**
 * Warenkorb im normalen Shop (20.11.2026, Marks Vorgabe): nichts wird bezahlt,
 * bis an der Kasse "Bezahlen" bestätigt ist — bis dahin lassen sich Zeilen
 * ändern oder entfernen.
 *
 * Reiner Client-Stand, in localStorage pro Kampagne + Laden + Käufer
 * gespeichert, damit Nachladen (useNachladen), Tab-Wechsel und Schließen/
 * Wiederöffnen des Ladens ihn nicht verlieren. Preise stehen bewusst NICHT
 * im gespeicherten Stand — sie werden immer aus dem aktuellen Sortiment
 * berechnet (Rabatt/Preisänderung der SL zieht sofort nach). Bezahlt wird
 * serverseitig in einem Rutsch (POST .../kaufen-warenkorb), der Server
 * prüft alles noch einmal selbst.
 */

export const ANZAHL_MIN = 1;
export const ANZAHL_MAX = 99;

export interface WarenkorbZeile {
  gegenstandId: string;
  anzahl: number;
  /** Nur für den Hinweis, falls die Ware aus dem Sortiment verschwindet. */
  name: string;
}

export function anzahlBegrenzen(n: number): number {
  if (!Number.isFinite(n)) return ANZAHL_MIN;
  return Math.max(ANZAHL_MIN, Math.min(ANZAHL_MAX, Math.trunc(n)));
}

/** Mehr als 1 Stück pro Kauf nur bei kopierbarer, nicht einzigartiger Ware
 * (Einzelstücke gibt es nur einmal) — dieselbe Regel prüft der Server. */
export function istStapelbar(ware: Pick<SortimentEintrag, "istVorlage" | "einzigartig">): boolean {
  return ware.istVorlage && !ware.einzigartig;
}

/** Stückpreis nach Rabatt — exakt wie der Server rechnet
 * (haendler/repository.py::preis_nach_rabatt, ganzzahlig abgerundet). */
export function stueckpreis(ware: Pick<SortimentEintrag, "preis" | "rabattProzent">): number {
  const rabatt = ware.rabattProzent || 0;
  return Math.floor((ware.preis * (100 - rabatt)) / 100);
}

function schluessel(campaignId: string, haendlerId: string, kaeuferId: string): string {
  return `pnptool:warenkorb:${campaignId}:${haendlerId}:${kaeuferId}`;
}

function lesen(key: string | null): WarenkorbZeile[] {
  if (!key || typeof localStorage === "undefined") return [];
  try {
    const roh = JSON.parse(localStorage.getItem(key) || "[]");
    if (!Array.isArray(roh)) return [];
    return roh
      .filter((z) => z && typeof z.gegenstandId === "string")
      .map((z) => ({
        gegenstandId: z.gegenstandId,
        anzahl: anzahlBegrenzen(Number(z.anzahl)),
        name: typeof z.name === "string" ? z.name : "",
      }));
  } catch {
    return [];
  }
}

function schreiben(key: string | null, zeilen: WarenkorbZeile[]) {
  if (!key || typeof localStorage === "undefined") return;
  try {
    if (zeilen.length === 0) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(zeilen));
  } catch {
    // Speicher voll/gesperrt (privater Modus) — dann eben nur im Speicher.
  }
}

/** Gleicht den Warenkorb mit dem aktuellen Sortiment ab: verschwundene Ware
 * fliegt raus (Namen kommen zurück für den Hinweis), nicht mehr stapelbare
 * Ware fällt auf 1 Stück. Gibt dieselbe Liste zurück, wenn sich nichts
 * ändert — sonst würde jedes Nachladen ein unnötiges Rendern auslösen. */
export function abgleichen(
  zeilen: WarenkorbZeile[],
  sortiment: SortimentEintrag[],
): { zeilen: WarenkorbZeile[]; entfernt: string[] } {
  const nachId = new Map(sortiment.map((w) => [w.gegenstandId, w]));
  const entfernt: string[] = [];
  let geaendert = false;
  const neu: WarenkorbZeile[] = [];
  for (const z of zeilen) {
    const ware = nachId.get(z.gegenstandId);
    if (!ware) {
      entfernt.push(z.name || "Eine Ware");
      geaendert = true;
      continue;
    }
    const anzahl = istStapelbar(ware) ? z.anzahl : 1;
    if (anzahl !== z.anzahl || ware.name !== z.name) geaendert = true;
    neu.push({ ...z, anzahl, name: ware.name });
  }
  return { zeilen: geaendert ? neu : zeilen, entfernt };
}

export interface WarenkorbPosten {
  zeile: WarenkorbZeile;
  ware: SortimentEintrag;
  stueckpreis: number;
  /** 0 oder 1 — Rassen-Feature "erster Kauf gratis" trifft höchstens ein
   * Stück, und zwar das erste passende in Warenkorb-Reihenfolge (genau wie
   * der Server, siehe haendler/kauf.py::posten_pruefen). */
  gratisStuecke: number;
  summe: number;
}

export function postenBerechnen(
  zeilen: WarenkorbZeile[],
  sortiment: SortimentEintrag[],
  gratisErsterKaufTyp: string,
): WarenkorbPosten[] {
  const nachId = new Map(sortiment.map((w) => [w.gegenstandId, w]));
  let gratisFrei = Boolean(gratisErsterKaufTyp);
  const posten: WarenkorbPosten[] = [];
  for (const zeile of zeilen) {
    const ware = nachId.get(zeile.gegenstandId);
    if (!ware) continue;
    const preis = stueckpreis(ware);
    let gratisStuecke = 0;
    if (gratisFrei && ersterKaufTrifft(gratisErsterKaufTyp, ware.typ)) {
      gratisStuecke = 1;
      gratisFrei = false;
    }
    posten.push({ zeile, ware, stueckpreis: preis, gratisStuecke, summe: preis * (zeile.anzahl - gratisStuecke) });
  }
  return posten;
}

/**
 * Warenkorb-Zustand für einen Laden + Käufer. `kaeuferId` null (SL ohne
 * gewählten Charakter) → kein Warenkorb, nichts wird gespeichert.
 */
export function useWarenkorb(campaignId: string, haendlerId: string, kaeuferId: string | null) {
  const key = kaeuferId ? schluessel(campaignId, haendlerId, kaeuferId) : null;
  const [stand, setStand] = useState(() => ({ key, zeilen: lesen(key) }));
  // Käufer/Laden gewechselt: sofort den passenden Korb lesen (Zustand
  // während des Renderns nachziehen, kein Effekt — sonst würde der alte
  // Korb einen Takt lang unter dem neuen Schlüssel gespeichert).
  let aktuell = stand;
  if (stand.key !== key) {
    aktuell = { key, zeilen: lesen(key) };
    setStand(aktuell);
  }

  useEffect(() => {
    schreiben(stand.key, stand.zeilen);
  }, [stand]);

  function aendern(fn: (z: WarenkorbZeile[]) => WarenkorbZeile[]) {
    setStand((s) => {
      const neu = fn(s.zeilen);
      return neu === s.zeilen ? s : { key: s.key, zeilen: neu };
    });
  }

  return {
    aktiv: key !== null,
    zeilen: aktuell.zeilen,
    aendern,
    hinzufuegen(ware: SortimentEintrag, anzahl: number) {
      aendern((z) => {
        const vorhanden = z.find((x) => x.gegenstandId === ware.gegenstandId);
        if (!istStapelbar(ware)) {
          // Einzelstück: genau einmal im Korb.
          return vorhanden ? z : [...z, { gegenstandId: ware.gegenstandId, anzahl: 1, name: ware.name }];
        }
        if (vorhanden) {
          return z.map((x) =>
            x.gegenstandId === ware.gegenstandId ? { ...x, anzahl: anzahlBegrenzen(x.anzahl + anzahl) } : x,
          );
        }
        return [...z, { gegenstandId: ware.gegenstandId, anzahl: anzahlBegrenzen(anzahl), name: ware.name }];
      });
    },
    anzahlSetzen(gegenstandId: string, anzahl: number) {
      aendern((z) =>
        z.map((x) => (x.gegenstandId === gegenstandId ? { ...x, anzahl: anzahlBegrenzen(anzahl) } : x)),
      );
    },
    entfernen(gegenstandId: string) {
      aendern((z) => z.filter((x) => x.gegenstandId !== gegenstandId));
    },
    leeren() {
      aendern(() => []);
    },
  };
}
