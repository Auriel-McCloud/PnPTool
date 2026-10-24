import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { spezialisierungenApi, type Spezialisierung } from "../spezialisierungen/api";
import { Bestaetigung } from "../shell/Bestaetigung";
import type { TraitDef } from "./api";
import "./spezialisierung.css";

/**
 * Spezialisierungs-Slots EINER Fertigkeit oder Sphäre — eingebettet ins
 * Klick-Fenster (Probe: Attributwahl, NeuroWeaving, Sphäreninfo). Kein
 * eigenes Popup und kein Badge neben den Punkten mehr (Mark, 23.10.2026:
 * der Badge rechts von den Punkten war hässlich).
 *
 * Sichtbar ab der ersten Schwelle (Fertigkeit/NeuroWeaving 4, Sphäre 2)
 * oder sobald schon Slots existieren — der Aufrufer entscheidet das.
 * Der Fenster-Titel (inkl. Häretiker-Name) kommt vom Aufrufer.
 *
 * Zweiphasiges Namensrecht (Mark, wörtlich: "nachträglich sollte nur der SL
 * sie ändern können" — Annahme: 'nachträglich' = NACH der ersten Benennung):
 * ein leerer Slot darf einmalig vom Spieler ODER der SL benannt werden
 * (Vorschlag-Chip oder Freitext). Danach ist er gesperrt — nur die SL darf
 * ihn noch ändern. Die Sperre prüft der Server (403); hier wird nur passend
 * angezeigt.
 */
export function SpezialisierungVerwaltung({
  campaignId,
  personId,
  trait,
  rating,
  erfahrungVerfuegbar,
  slots,
  istGM,
  onAenderung,
}: {
  campaignId: string;
  personId: string;
  trait: TraitDef;
  rating: number;
  erfahrungVerfuegbar: number;
  slots: Spezialisierung[];
  /** Entspricht `bearbeitbar` am Charakterblatt — nur dort ist es die SL. */
  istGM: boolean;
  onAenderung: () => void | Promise<void>;
}) {
  const [entwuerfe, setEntwuerfe] = useState<Record<string, string>>({});
  const [speichert, setSpeichert] = useState<string | null>(null);
  const [kauft, setKauft] = useState(false);
  const [kaufFehler, setKaufFehler] = useState("");
  const [weg, setWeg] = useState<Spezialisierung | null>(null);

  // Frischer Entwurf beim Wechsel der Fertigkeit — das Fenster bleibt offen,
  // während man von einer Fertigkeit zur nächsten springt.
  useEffect(() => {
    setEntwuerfe({});
    setKaufFehler("");
  }, [trait.id]);

  async function benennen(slot: Spezialisierung, text: string) {
    if (!text.trim()) return;
    setSpeichert(slot.id);
    try {
      await spezialisierungenApi.benennen(campaignId, personId, slot.id, text.trim());
      await onAenderung();
    } catch (e) {
      // Gesperrt (403, ein Spieler versucht einen bereits benannten Slot zu
      // ändern) oder Netzwerkfehler — der Entwurf bleibt einfach stehen,
      // kein zusätzlicher Toast (Mark hat das nirgends sonst in diesem
      // Blatt verlangt).
      console.error(e);
    } finally {
      setSpeichert(null);
    }
  }

  async function entfernen(slot: Spezialisierung) {
    setWeg(null);
    setSpeichert(slot.id);
    try {
      await spezialisierungenApi.entfernen(campaignId, personId, slot.id);
      await onAenderung();
    } catch (e) {
      setKaufFehler(e instanceof ApiError ? e.message : "Entfernen fehlgeschlagen.");
    } finally {
      setSpeichert(null);
    }
  }

  async function kaufen() {
    setKauft(true);
    setKaufFehler("");
    try {
      await spezialisierungenApi.kaufen(campaignId, personId, trait.id);
      await onAenderung();
    } catch (e) {
      setKaufFehler(e instanceof ApiError ? e.message : "Kauf fehlgeschlagen.");
    } finally {
      setKauft(false);
    }
  }

  // Sphären haben ihre erste Schwelle bei 2, Fertigkeiten/NeuroWeaving bei 4
  // (siehe backend/app/spezialisierungen/repository.py::SPHAERE_SCHWELLEN).
  const mindestRating = trait.category === "Sphäre" ? 2 : 4;
  const kannKaufen = rating >= mindestRating;

  return (
    <div className="sz-verwaltung">
      <div className="sz-liste">
        {slots.length === 0 && (
          <p className="cb-hinweis">
            Ab Rating {mindestRating} gibt es automatisch einen Slot — oder gleich einen kaufen.
          </p>
        )}
        {slots.map((slot) => {
          const gesperrtFuerSpieler = Boolean(slot.text) && !istGM;
          return (
            <div key={slot.id} className="sz-slot">
              <div className="sz-slot-kopf">
                <span className="sz-slot-quelle">{slot.quelle === "gekauft" ? "Gekauft" : "Automatisch"}</span>
                {istGM && (
                  <button
                    type="button"
                    className="sz-entfernen"
                    disabled={speichert === slot.id}
                    onClick={() => setWeg(slot)}
                  >
                    Entfernen
                  </button>
                )}
              </div>
              {gesperrtFuerSpieler ? (
                <p className="sz-slot-text">{slot.text}</p>
              ) : (
                <div className="sz-slot-editor">
                  {!slot.text && trait.vorschlaege.length > 0 && (
                    <div className="sz-vorschlaege">
                      {trait.vorschlaege.map((v) => (
                        <button
                          key={v}
                          type="button"
                          className="sz-chip"
                          disabled={speichert === slot.id}
                          onClick={() => benennen(slot, v)}
                        >
                          {v}
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="sz-freitext">
                    <input
                      type="text"
                      value={entwuerfe[slot.id] ?? slot.text}
                      placeholder="Eigener Text…"
                      onChange={(e) => setEntwuerfe({ ...entwuerfe, [slot.id]: e.target.value })}
                    />
                    <button
                      type="button"
                      className="sz-knopf"
                      disabled={speichert === slot.id}
                      onClick={() => benennen(slot, entwuerfe[slot.id] ?? slot.text)}
                    >
                      {speichert === slot.id ? "Speichert…" : slot.text ? "Ändern" : "Benennen"}
                    </button>
                  </div>
                  {slot.text && istGM && (
                    <p className="cb-hinweis">
                      Von der Spielleitung änderbar — der Spieler sieht diesen Text gesperrt.
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="sz-kaufen">
        <button type="button" className="sz-knopf" disabled={!kannKaufen || kauft} onClick={kaufen}>
          {kauft ? "Kauft…" : "+ Weiteren Slot für 4 EP kaufen"}
        </button>
        {!kannKaufen && <p className="cb-hinweis">Erst ab Rating {mindestRating} möglich.</p>}
        {kaufFehler && <p className="pr-warnung">{kaufFehler}</p>}
        <p className="cb-hinweis">{erfahrungVerfuegbar} EP verfügbar</p>
      </div>
      {weg && (
        <Bestaetigung
          titel="Spezialisierung entfernen?"
          text={
            (weg.text ? `„${weg.text}“` : "Der leere Slot") +
            ` an ${trait.name} verschwindet.` +
            (weg.quelle === "gekauft" ? " Die 4 EP kommen zurück." : "") +
            " Ein neuer automatischer Slot kommt erst wieder, wenn die Fertigkeit die Schwelle erneut überschreitet."
          }
          jaText="Entfernen"
          onJa={() => entfernen(weg)}
          onNein={() => setWeg(null)}
        />
      )}
    </div>
  );
}
