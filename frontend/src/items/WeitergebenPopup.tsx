import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { partyApi, type PartyMitglied } from "../party/api";
import type { Gegenstand } from "./api";
import "./wegwerfen.css";

/**
 * Empfänger-Auswahl für die Gegenstands-Weitergabe an ein Party-Mitglied.
 *
 * Nach demselben Baustein-Muster wie `WegwerfenFrage.tsx` (eigenes Fenster,
 * das erst nach Bestätigung wirklich etwas auslöst) — hier ist die
 * Bestätigung implizit der Klick auf ein bestimmtes Mitglied, denn die
 * eigentliche Rückfrage kommt ohnehin gleich danach beim Empfänger selbst
 * (Annehmen/Ablehnen-Popup, siehe verhandlung/VerhandlungPopup.tsx) — eine
 * zweite Rückfrage hier davor wäre doppelt gemoppelt.
 */
export function WeitergebenPopup({
  item,
  offen,
  campaignId,
  eigenePersonId,
  onWeitergeben,
  onAbbrechen,
}: {
  item: Gegenstand;
  offen: boolean;
  campaignId: string;
  /** Damit man sich selbst nicht in der Liste sieht. */
  eigenePersonId: string;
  onWeitergeben: (empfaengerPersonId: string) => void;
  onAbbrechen: () => void;
}) {
  const [mitglieder, setMitglieder] = useState<PartyMitglied[]>([]);
  const [ladend, setLadend] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    setLadend(true);
    setFehler(null);
    partyApi
      .liste(campaignId)
      .then((partys) => {
        // Die eigene Party ist die, in der eigenePersonId Mitglied ist —
        // Backend liefert dem Spieler ohnehin nur sichtbare Partys.
        const eigene = partys.find((p) => p.mitglieder.some((m) => m.id === eigenePersonId));
        setMitglieder((eigene?.mitglieder ?? []).filter((m) => m.id !== eigenePersonId));
      })
      .catch(() => setFehler("Party konnte nicht geladen werden"))
      .finally(() => setLadend(false));
  }, [offen, campaignId, eigenePersonId]);

  return (
    <Fenster offen={offen} titel={`${item.name} weitergeben`} kennung={`weitergeben:${item.id}`} onSchliessen={onAbbrechen}>
      <p className="ww-hinweis">Wähle, wer aus deiner Party {item.name} bekommen soll.</p>
      <p className="ww-beruhigung">
        Die Person muss annehmen — es landet nicht sofort im fremden Inventar.
      </p>
      {ladend && <p style={{ color: "var(--text-leise)" }}>Lade Party…</p>}
      {fehler && <p className="ww-hinweis" style={{ color: "var(--signal)" }}>{fehler}</p>}
      {!ladend && !fehler && mitglieder.length === 0 && (
        <p style={{ color: "var(--text-leise)" }}>Niemand sonst ist gerade in deiner Party.</p>
      )}
      {mitglieder.length > 0 && (
        <div className="ww-knoepfe" style={{ flexWrap: "wrap" }}>
          {mitglieder.map((m) => (
            <button key={m.id} type="button" className="ww-behalten" onClick={() => onWeitergeben(m.id)}>
              {m.name}
            </button>
          ))}
        </div>
      )}
    </Fenster>
  );
}
