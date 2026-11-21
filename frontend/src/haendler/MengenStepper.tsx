import { useEffect, useRef, useState } from "react";
import { ANZAHL_MAX, ANZAHL_MIN, anzahlBegrenzen } from "./warenkorb";

/**
 * [−] [Zahl] [+] für die Stückzahl im Shop (Kauf-Popup + Warenkorb-Zeile).
 *
 * Der Rohtext lebt in eigenem State (Stolperstein Zahlenfeld): onChange
 * reicht ihn ungefiltert durch — leeren oder die erste Ziffer ersetzen
 * muss gehen —, begrenzt wird nur der Zahlenwert, der nach oben geht, und
 * erst beim Verlassen des Feldes wird der Text normalisiert.
 */
export function MengenStepper({
  wert,
  onWert,
  deaktiviert = false,
  bezeichnung = "Anzahl",
}: {
  wert: number;
  onWert: (n: number) => void;
  deaktiviert?: boolean;
  bezeichnung?: string;
}) {
  const [text, setText] = useState(String(wert));
  const fokus = useRef(false);

  // Wert von außen geändert (z.B. +/− oder Warenkorb-Abgleich): Text
  // nachziehen, aber nie mitten ins Tippen hinein.
  useEffect(() => {
    if (!fokus.current) setText(String(wert));
  }, [wert]);

  function setzen(n: number) {
    const begrenzt = anzahlBegrenzen(n);
    setText(String(begrenzt));
    onWert(begrenzt);
  }

  return (
    <span className="shop-stepper" role="group" aria-label={bezeichnung}>
      <button
        type="button"
        className="shop-stepper-knopf"
        onClick={() => setzen(wert - 1)}
        disabled={deaktiviert || wert <= ANZAHL_MIN}
        aria-label="Eins weniger"
      >
        −
      </button>
      <input
        type="number"
        inputMode="numeric"
        className="shop-stepper-zahl"
        min={ANZAHL_MIN}
        max={ANZAHL_MAX}
        value={text}
        disabled={deaktiviert}
        aria-label={bezeichnung}
        onFocus={() => {
          fokus.current = true;
        }}
        onChange={(e) => {
          setText(e.target.value);
          const n = Number(e.target.value);
          if (e.target.value !== "" && Number.isFinite(n)) onWert(anzahlBegrenzen(n));
        }}
        onBlur={() => {
          fokus.current = false;
          const n = Number(text);
          setzen(text === "" || !Number.isFinite(n) ? wert : n);
        }}
      />
      <button
        type="button"
        className="shop-stepper-knopf"
        onClick={() => setzen(wert + 1)}
        disabled={deaktiviert || wert >= ANZAHL_MAX}
        aria-label="Eins mehr"
      >
        +
      </button>
    </span>
  );
}
