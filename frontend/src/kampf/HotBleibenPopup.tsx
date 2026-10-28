import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { kampfApi, type HotStatus, type Kampf } from "./api";
import "./booster.css";

/**
 * Fragt, wenn der Rigger wieder dran ist, ob er in der Hot-Drohne bleibt.
 * Dieselbe Lage wie das Booster-Popup: über allem, nicht nur im Kampf-Tab.
 */
export function MatrixHotKnopf({ campaignId }: { campaignId: string }) {
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
  }, [campaignId]);

  if (!status?.hatNeurolink || !status.hatDeck) return null;

  async function umschalten() {
    if (!status) return;
    setSendet(true);
    try {
      setStatus(await kampfApi.hotMatrix(campaignId, !status.matrixHot));
    } finally {
      setSendet(false);
    }
  }

  return (
    <button type="button" className="gg-hot-knopf" disabled={sendet} onClick={umschalten} data-aktiv={status.matrixHot}>
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

  if (!status?.bleibenFaellig) return null;

  async function antwort(bleiben: boolean) {
    setSendet(true);
    try {
      setStatus(await kampfApi.hotBleiben(campaignId, bleiben));
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  return createPortal(
    <div className="bo-huelle" role="alertdialog">
      <div className="bo-fenster">
        <h3 className="bo-titel">In {status.hotDrohneName ?? "der Drohne"} bleiben?</h3>
        <p className="bo-text">Eine Drohne pro Runde. Nein klinkt aus, eine andere erst in der nächsten Runde.</p>
        <div className="bo-knoepfe">
          <button type="button" disabled={sendet} onClick={() => antwort(true)}>
            Ja, bleiben
          </button>
          <button type="button" className="bo-nein" disabled={sendet} onClick={() => antwort(false)}>
            Nein, ausklinken
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
