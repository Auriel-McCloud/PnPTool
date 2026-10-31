/** Klecks in einem eigenen Fenster. Der Upload-Pfad kommt als `ziel` mit,
 *  damit Portrait, Drohne und Gegenstand nicht dasselbe Fenster teilen. */

export const BILD_KANAL = "pnptool-bild";

export type BildAntwort = Record<string, unknown>;

const hoerer = new Map<string, (antwort: BildAntwort) => void>();
let kanal: BroadcastChannel | null = null;
let zuletzt = "";

function annehmen(data: { typ?: string; ruf?: string; antwort?: BildAntwort } | null) {
  if (!data || data.typ !== "bild-gespeichert" || typeof data.ruf !== "string") return;
  const schluessel = `${data.ruf}|${String(data.antwort?.bildUrl ?? data.antwort?.url ?? "")}`;
  if (schluessel === zuletzt) return;
  zuletzt = schluessel;
  hoerer.get(data.ruf)?.(data.antwort ?? {});
}

function kanalSicher() {
  if (typeof BroadcastChannel === "undefined" || kanal) return;
  kanal = new BroadcastChannel(BILD_KANAL);
  kanal.onmessage = (e) => annehmen(e.data);
  window.addEventListener("message", (e) => {
    if (e.origin !== window.location.origin) return;
    annehmen(e.data);
  });
}

/** Nur die Instanz, die das Fenster geöffnet hat, reagiert aufs Speichern. */
export function bildHoererSetzen(ruf: string, fn: (antwort: BildAntwort) => void) {
  kanalSicher();
  hoerer.set(ruf, fn);
  return () => {
    if (hoerer.get(ruf) === fn) hoerer.delete(ruf);
  };
}

export function oeffneZeichentisch(ziel: string, bildUrl: string | null | undefined, ruf: string): string | null {
  const url = new URL("/klecks/index.html", window.location.origin);
  url.searchParams.set("ziel", ziel);
  url.searchParams.set("ruf", ruf);
  if (bildUrl?.startsWith("/uploads/") && !bildUrl.includes("..") && !bildUrl.includes("://")) {
    url.searchParams.set("bild", bildUrl);
  }
  const name = `pnptool-zt-${ruf.replace(/[^a-zA-Z0-9]/g, "").slice(0, 24)}`;
  const bestehend = window.open("", name);
  if (!bestehend) return "Fenster blockiert — Popups für diese Seite erlauben.";
  try {
    const offen = new URL(bestehend.location.href);
    if (offen.pathname.endsWith("/klecks/index.html") && offen.searchParams.get("ruf") === ruf) {
      bestehend.focus();
      return null;
    }
  } catch {
    // anderes Origin, dann neu laden
  }
  bestehend.location.href = url.toString();
  bestehend.focus();
  return null;
}
