/**
 * „Zum Chat“: ein Klick im Nachrichten-Popup öffnet den Chat dahinter.
 *
 * Das Popup liegt über allem und kennt weder Navigation noch Messenger. Deshalb
 * läuft der Wunsch über diesen kleinen Vermittler:
 *
 * 1. `chatOeffnen` meldet das Ziel (Einzelchat oder Gruppe plus ID).
 * 2. Die Hülle (Spieleransicht, SL-Dashboard) hört per `beiChatOeffnen` mit und
 *    schaltet auf den Kontakte-Bereich.
 * 3. Messenger (Spieler) bzw. Kontakte-/Gruppenverwaltung (SL) abonnieren ihre Art per
 *    `chatZielAbonnieren`. Sind sie noch nicht eingehängt, merkt sich der Vermittler
 *    das Ziel kurz und übergibt es beim Abonnieren.
 */

export type ChatArt = "KONTAKT" | "GRUPPE";

export interface ChatZiel {
  art: ChatArt;
  id: string;
}

/** So lange hält ein noch nicht abgeholtes Ziel — danach wäre ein Aufspringen eine Überraschung. */
const GUELTIG_MS = 5000;

const navigation = new Set<(ziel: ChatZiel) => void>();
const abonnenten = new Map<ChatArt, Set<(id: string) => void>>();
let wartend: { ziel: ChatZiel; bis: number } | null = null;

export function istChatArt(art: string): art is ChatArt {
  return art === "KONTAKT" || art === "GRUPPE";
}

/** Aufruf aus dem Popup. */
export function chatOeffnen(ziel: ChatZiel): void {
  navigation.forEach((fn) => fn(ziel));
  const hoerer = abonnenten.get(ziel.art);
  if (hoerer && hoerer.size > 0) {
    hoerer.forEach((fn) => fn(ziel.id));
    wartend = null;
  } else {
    wartend = { ziel, bis: Date.now() + GUELTIG_MS };
  }
}

/** Die Hülle schaltet auf den Kontakte-Bereich. Meldet sich mit jedem Ziel, übernimmt es nicht. */
export function beiChatOeffnen(fn: (ziel: ChatZiel) => void): () => void {
  navigation.add(fn);
  return () => {
    navigation.delete(fn);
  };
}

/** Der Chat-Besitzer übernimmt sein Ziel. Ein bereits wartendes Ziel kommt sofort. */
export function chatZielAbonnieren(art: ChatArt, fn: (id: string) => void): () => void {
  let satz = abonnenten.get(art);
  if (!satz) {
    satz = new Set();
    abonnenten.set(art, satz);
  }
  satz.add(fn);

  if (wartend && wartend.ziel.art === art && wartend.bis > Date.now()) {
    const id = wartend.ziel.id;
    wartend = null;
    fn(id);
  }
  return () => {
    satz.delete(fn);
  };
}
