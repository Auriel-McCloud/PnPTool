import { useRef, useState } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { KiBildPopup } from "../ki/KiBildPopup";
import { playersApi, type SpielerMe } from "./api";
import { ZeichenblockPopup } from "./ZeichenblockPopup";
import "./portrait.css";

/**
 * Charakterportrait als eigener Bereich in der Spieler-Hülle (Mark,
 * 22.09.2026: "damit im Charakterblatt mehr Platz ist" — das Blatt wächst
 * je nach Chartyp mit zusätzlichen Skills/Werten, ein Bild-Verwaltungsknopf
 * dort hätte nur Platz weggenommen). Ursprünglich als Popup über dem Blatt
 * geplant, auf Marks Wunsch zu einem eigenen Burger-Menü-Punkt gemacht.
 *
 * Galerie (24.10.2026, Mark: "weitere Bilder anlegen, und sich eines als
 * Anzeigebild aussuchen"): Hochladen/Foto/KI/Zeichnen hängen nur noch an
 * die eigene Galerie an, ohne das Anzeigebild zu klauen — welches Bild
 * oben als Portrait zählt, wählt der Spieler per Klick auf ein Thumbnail.
 * Gleiches Muster wie entities/BildGalerie.tsx auf SL-Seite, hier aber
 * über die dedizierten /mein-bild*-Routen statt freiem PATCH (ein Spieler
 * darf nur dieses eine Feld am eigenen Charakter anfassen).
 */
export function CharakterportraitAnsicht({
  ich,
  onGeaendert,
}: {
  ich: SpielerMe;
  /** Neuer SpielerMe-Stand nach erfolgreichem Upload. */
  onGeaendert: (frisch: SpielerMe) => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenUrl, setLoeschenUrl] = useState<string | null>(null);
  const [kiOffen, setKiOffen] = useState(false);
  const [zeichnenOffen, setZeichnenOffen] = useState(false);
  const dateiRef = useRef<HTMLInputElement>(null);
  const kameraRef = useRef<HTMLInputElement>(null);

  // Fallback für Bestandsdaten ohne personBilder — dasselbe Muster wie
  // BildGalerie.tsx::effektiveBilder auf SL-Seite.
  const bilder =
    ich.personBilder && ich.personBilder.length > 0
      ? ich.personBilder
      : ich.personBildUrl
        ? [{ url: ich.personBildUrl, istPrimaer: true }]
        : [];

  function zeichentischOeffnen() {
    const url = new URL("/klecks/index.html", window.location.origin);
    if (ich.personBildUrl?.startsWith("/uploads/")) {
      url.searchParams.set("bild", ich.personBildUrl);
    }
    const name = "pnptool-zeichentisch";
    // Zweites Antippen fokussiert das offene Fenster, statt die Zeichnung neu zu laden.
    const bestehend = window.open("", name);
    if (!bestehend) {
      setFehler("Fenster blockiert — Popups für diese Seite erlauben.");
      return;
    }
    try {
      if (bestehend.location.href.includes("/klecks/index.html")) {
        bestehend.focus();
        return;
      }
    } catch {
      // anderes Origin, dann neu laden
    }
    bestehend.location.href = url.toString();
    bestehend.focus();
  }

  async function hochladen(datei: File | undefined) {
    if (!datei) return;
    setLaedt(true);
    setFehler(null);
    try {
      const frisch = await playersApi.meinBildHochladen(datei);
      onGeaendert(frisch);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    } finally {
      setLaedt(false);
      if (dateiRef.current) dateiRef.current.value = "";
      if (kameraRef.current) kameraRef.current.value = "";
    }
  }

  async function alsAnzeigebildWaehlen(url: string) {
    setLaedt(true);
    setFehler(null);
    try {
      const frisch = await playersApi.meinBildAnzeigeWaehlen(url);
      onGeaendert(frisch);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Auswahl fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  async function loeschen() {
    if (!loeschenUrl) return;
    const url = loeschenUrl;
    setLoeschenUrl(null);
    setLaedt(true);
    setFehler(null);
    try {
      const frisch = await playersApi.meinBildEntfernen(url);
      onGeaendert(frisch);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  return (
    <div className="port-seite">
      <h3 className="gg-abschnitt">
        <span>◒ Portrait</span>
      </h3>

      <div className="port-popup">
        {ich.personBildUrl && (
          <img src={ich.personBildUrl} alt={ich.personName ?? "Portrait"} className="port-vorschau" />
        )}

        {!ich.personBildUrl && <p className="port-leer">Noch kein Bild gesetzt.</p>}

        {/* Galerie: Klick wählt das Anzeigebild, ✕ entfernt das Bild. */}
        <div className="port-galerie">
          {bilder.map((bild) => (
            <div
              key={bild.url}
              className={`port-galerie-thumb ${bild.istPrimaer ? "primaer" : ""}`}
              onClick={() => !bild.istPrimaer && !laedt && alsAnzeigebildWaehlen(bild.url)}
              title={bild.istPrimaer ? "Aktuelles Anzeigebild" : "Als Anzeigebild wählen"}
            >
              <img src={bild.url} alt="" />
              <button
                type="button"
                className="port-galerie-loeschen"
                disabled={laedt}
                onClick={(e) => {
                  e.stopPropagation();
                  setLoeschenUrl(bild.url);
                }}
                title="Bild entfernen"
              >
                ✕
              </button>
            </div>
          ))}
          <div
            className="port-galerie-thumb port-galerie-neu"
            onClick={() => !laedt && dateiRef.current?.click()}
            title="Weiteres Bild hochladen"
          >
            <span aria-hidden="true">+</span>
          </div>
        </div>

        <input
          ref={dateiRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          style={{ display: "none" }}
          onChange={(e) => hochladen(e.target.files?.[0])}
        />
        {/* capture="environment" öffnet am Handy direkt die Kamera statt der
            Dateiauswahl — auf dem Desktop ohne Kamera fällt der Browser
            automatisch auf die normale Dateiauswahl zurück. */}
        <input
          ref={kameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={(e) => hochladen(e.target.files?.[0])}
        />

        {fehler && <p className="port-fehler">{fehler}</p>}

        <div className="port-aktionen">
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => dateiRef.current?.click()}>
            {laedt ? "Lädt…" : "📁 Bild hochladen"}
          </button>
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => kameraRef.current?.click()}>
            {laedt ? "Lädt…" : "📷 Foto machen"}
          </button>
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => setKiOffen(true)}>
            ✨ KI-Bild generieren
          </button>
          <button type="button" className="port-btn-primaer" disabled={laedt} onClick={() => setZeichnenOffen(true)}>
            ✎ Zeichnen
          </button>
          <button type="button" className="port-btn-sekundaer" disabled={laedt} onClick={zeichentischOeffnen}>
            ◈ Zeichentisch
          </button>
        </div>

        <p className="port-hinweis">
          Jedes neue Bild landet erst in der Galerie unten — per Klick auf ein Thumbnail wird es zum
          Anzeigebild. Zeichnen ist die Skizze hier. Der Zeichentisch öffnet Klecks mit Ebenen in einem
          eigenen Fenster — dort setzt „Portrait" das Bild. Ebenen bleiben nur in dem Fenster, danach
          liegt ein flaches Portrait.
        </p>
      </div>

      {loeschenUrl && (
        <Bestaetigung
          titel="Bild entfernen"
          text="Bist du sicher? Das Bild wird aus deiner Galerie entfernt."
          jaText="Entfernen"
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenUrl(null)}
        />
      )}

      <ZeichenblockPopup
        offen={zeichnenOffen}
        bildUrl={ich.personBildUrl}
        onSchliessen={() => setZeichnenOffen(false)}
        onUebernehmen={async (blob) => {
          const datei = new File([blob], "portrait-skizze.png", { type: blob.type || "image/png" });
          const frisch = await playersApi.meinBildHochladen(datei);
          onGeaendert(frisch);
        }}
      />

      <KiBildPopup
        offen={kiOffen}
        objektTyp="Person"
        objektName={ich.personName ?? "Charakter"}
        onSchliessen={() => setKiOffen(false)}
        onPromptVorschlagen={() => playersApi.meinBildKiPrompt()}
        onGenerieren={(provider, prompt) => playersApi.meinBildKiGenerieren(provider, prompt)}
        onUebernehmen={async (blob) => {
          const datei = new File([blob], "portrait-ki.png", { type: blob.type || "image/png" });
          const frisch = await playersApi.meinBildHochladen(datei);
          onGeaendert(frisch);
        }}
      />
    </div>
  );
}
