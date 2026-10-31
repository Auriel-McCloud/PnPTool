import { useEffect, useRef, useState } from "react";
import { ZeichenblockPopup } from "../players/ZeichenblockPopup";
import { bildHoererSetzen, oeffneZeichentisch, type BildAntwort } from "./zeichentisch";

/**
 * Skizze und Zeichentisch neben Hochladen/KI. Die Skizze gibt den Blob an
 * den Aufrufer. Klecks lädt selbst auf `uploadPfad` und meldet die Antwort.
 */
export function BildZeichenKnopfe({
  uploadPfad,
  bildUrl,
  disabled,
  onBlob,
  onGespeichert,
  dicht = true,
  unterzeile = "Skizze — wird als Bild gespeichert",
}: {
  uploadPfad: string;
  bildUrl?: string | null;
  disabled?: boolean;
  onBlob: (blob: Blob) => Promise<void>;
  onGespeichert: (antwort: BildAntwort) => void | Promise<void>;
  dicht?: boolean;
  unterzeile?: string;
}) {
  const [offen, setOffen] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const ruf = useRef(`zt-${Math.random().toString(36).slice(2, 10)}`).current;
  const gespeichert = useRef(onGespeichert);
  gespeichert.current = onGespeichert;

  useEffect(() => bildHoererSetzen(ruf, (antwort) => void gespeichert.current(antwort)), [ruf]);

  const knopf = dicht
    ? { minHeight: 0, padding: "4px 10px", fontSize: 12 }
    : undefined;

  return (
    <>
      <button
        type="button"
        disabled={disabled}
        style={knopf}
        onClick={() => setOffen(true)}
        title="Einfache Skizze"
      >
        ✎ Zeichnen
      </button>
      <button
        type="button"
        disabled={disabled}
        style={knopf}
        onClick={() => {
          const hinweis = oeffneZeichentisch(uploadPfad, bildUrl, ruf);
          setFehler(hinweis);
        }}
        title="Zeichentisch mit Ebenen"
      >
        ◈ Zeichentisch
      </button>
      {fehler && <span style={{ color: "var(--signal)", fontSize: 12 }}>{fehler}</span>}
      <ZeichenblockPopup
        offen={offen}
        bildUrl={bildUrl}
        unterzeile={unterzeile}
        onSchliessen={() => setOffen(false)}
        onUebernehmen={onBlob}
      />
    </>
  );
}
