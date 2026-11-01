import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { kampfApi, type HotStatus, type Kampf } from "./api";
import "./booster.css";

/**
 * Der Decker ist gerade Hot gegangen. Die Zusatzaktionen des Decks zählen
 * erst ab diesem Klick — das Booster-Fenster hört zu und fragt, wenn er
 * schon dran ist. Vorher kam die Frage nur, wenn Hot schon an war, als
 * der Zug begann.
 */
export const MATRIX_HOT_AN = "pnptool-matrix-hot-an";

/** Die Bleiben-Frage ist beantwortet. Das Booster-Fenster holt den Stand neu. */
export const MATRIX_BLEIBEN_FERTIG = "pnptool-matrix-bleiben-fertig";

/**
 * Fragt, wenn der Rigger wieder dran ist, ob er in der Hot-Drohne bleibt.
 * Dieselbe Lage wie das Booster-Popup: über allem, nicht nur im Kampf-Tab.
 */
export function MatrixHotKnopf({ campaignId }: { campaignId: string }) {
  const [status, setStatus] = useState<HotStatus | null>(null);
  const [sendet, setSendet] = useState(false);

  useEffect(() => {
    let weg = false;
    async function hol() {
      if (document.hidden) return;
      try {
        const s = await kampfApi.hotStatus(campaignId);
        if (!weg) setStatus(s);
      } catch {
        if (!weg) setStatus(null);
      }
    }
    void hol();
    const uhr = window.setInterval(() => void hol(), 3000);
    return () => {
      weg = true;
      window.clearInterval(uhr);
    };
  }, [campaignId]);

  if (!status?.hatNeurolink || !status.hatDeck) return null;

  async function einschalten() {
    if (!status || status.matrixHot) return;
    setSendet(true);
    try {
      setStatus(await kampfApi.hotMatrix(campaignId, true));
      window.dispatchEvent(new CustomEvent(MATRIX_HOT_AN));
    } finally {
      setSendet(false);
    }
  }

  return (
    <button
      type="button"
      className="gg-hot-knopf"
      disabled={sendet || status.matrixHot}
      onClick={einschalten}
      data-aktiv={status.matrixHot}
      title={status.matrixHot ? "Bleibt an, bis du wieder dran bist." : undefined}
    >
      {status.matrixHot ? "Hot — Matrix" : "Hot"}
    </button>
  );
}

export function HotBleibenPopup({
  campaignId,
  kampf,
  onGeaendert,
}: {
  campaignId: string;
  kampf: Kampf | null;
  onGeaendert: () => void;
}) {
  const [status, setStatus] = useState<HotStatus | null>(null);
  const [sendet, setSendet] = useState(false);

  useEffect(() => {
    let weg = false;
    kampfApi
      .hotStatus(campaignId)
      .then((s) => {
        if (!weg) setStatus(s);
      })
      .catch(() => {
        if (!weg) setStatus(null);
      });
    return () => {
      weg = true;
    };
  }, [campaignId, kampf?.runde, kampf?.amZug]);

  async function matrixAntwort(bleiben: boolean) {
    setSendet(true);
    try {
      setStatus(await kampfApi.hotMatrixBleiben(campaignId, bleiben));
      window.dispatchEvent(new CustomEvent(MATRIX_BLEIBEN_FERTIG));
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  async function drohnenAntwort(bleiben: boolean) {
    setSendet(true);
    try {
      setStatus(await kampfApi.hotBleiben(campaignId, bleiben));
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  if (status?.matrixBleibenFaellig) {
    return createPortal(
      <div className="bo-huelle" role="alertdialog">
        <div className="bo-fenster">
          <h3 className="bo-titel">Hot bleiben?</h3>
          <p className="bo-text">
            Solange du Hot bist, kann die Matrix dich treffen. Nein klinkt aus — dann auch keine Zusatzaktion aus dem Deck.
          </p>
          <div className="bo-knoepfe">
            <button type="button" disabled={sendet} onClick={() => matrixAntwort(true)}>
              Ja, bleiben
            </button>
            <button type="button" className="bo-nein" disabled={sendet} onClick={() => matrixAntwort(false)}>
              Nein, ausklinken
            </button>
          </div>
        </div>
      </div>,
      document.body,
    );
  }

  if (!status?.bleibenFaellig) return null;

  return createPortal(
    <div className="bo-huelle" role="alertdialog">
      <div className="bo-fenster">
        <h3 className="bo-titel">In {status.hotDrohneName ?? "der Drohne"} bleiben?</h3>
        <p className="bo-text">Eine Drohne pro Runde. Nein klinkt aus, eine andere erst in der nächsten Runde.</p>
        <div className="bo-knoepfe">
          <button type="button" disabled={sendet} onClick={() => drohnenAntwort(true)}>
            Ja, bleiben
          </button>
          <button type="button" className="bo-nein" disabled={sendet} onClick={() => drohnenAntwort(false)}>
            Nein, ausklinken
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
