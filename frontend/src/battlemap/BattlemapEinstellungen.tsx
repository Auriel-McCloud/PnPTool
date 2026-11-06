import { useEffect, useState, type ChangeEvent } from "react";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { VisibilitySelector, type PersonOption } from "../entities/VisibilitySelector";
import { entitiesApi, type Event, type Ort } from "../entities/api";
import { battlemapApi, type Battlemap } from "./api";
import { BildZeichenKnopfe } from "../bilder/BildZeichenKnopfe";
import "../zeichnungen/whiteboard.css";

export function BattlemapEinstellungen({
  offen,
  karte,
  campaignId,
  pcOptions,
  onSchliessen,
  onGeaendert,
  onGeloescht,
}: {
  offen: boolean;
  karte: Battlemap | null;
  campaignId: string;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: (aktualisiert: Battlemap) => void;
  onGeloescht: (id: string) => void;
}) {
  const [name, setName] = useState("");
  const [ladeBild, setLadeBild] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenFrage, setLoeschenFrage] = useState(false);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    entitiesApi.listOrte(campaignId).then(setOrte).catch(() => setOrte([]));
    entitiesApi.listEvents(campaignId).then(setEvents).catch(() => setEvents([]));
  }, [campaignId]);

  if (!karte) return null;

  async function speichern(teil: Partial<Battlemap>) {
    if (!karte) return;
    try {
      onGeaendert(await battlemapApi.aktualisieren(campaignId, karte.id, teil));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }

  async function bildWaehlen(e: ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    e.target.value = "";
    if (!datei || !karte) return;
    setLadeBild(true);
    try {
      onGeaendert(await battlemapApi.bildHochladen(campaignId, karte.id, datei));
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Bild-Upload fehlgeschlagen");
    } finally {
      setLadeBild(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel={`Karte: ${karte.name}`}
      unterzeile="Einstellungen — nur Spielleitung"
      kennung={`battlemap-einstellungen-${karte.id}`}
      ton="var(--bereich-battlemap)"
      onSchliessen={onSchliessen}
    >
      <div className="zb-einstellungen">
        <label className="zb-feld">
          <span>Name</span>
          <input
            className="zb-input"
            value={name || karte.name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => name.trim() && speichern({ name: name.trim() })}
          />
        </label>
        <label className="zb-schalter-zeile">
          <input
            type="checkbox"
            checked={karte.spielerDuerfenZeichnen}
            onChange={() => speichern({ spielerDuerfenZeichnen: !karte.spielerDuerfenZeichnen })}
          />
          <span>Spieler dürfen hier live mitzeichnen</span>
        </label>
        <VisibilitySelector
          label="Sichtbarkeit der Karte"
          modus={karte.sichtbarkeit}
          sichtbarFuer={karte.sichtbarFuer}
          onChange={(modus, sichtbarFuer) => speichern({ sichtbarkeit: modus, sichtbarFuer })}
          pcOptions={pcOptions}
        />
        {/* Verknüpfung mit Ort/Event (06.11.2026, Mark: Battlemap mit Orten
            oder Events verknüpfen können) — rein organisatorisch fürs
            Vorbereiten/den Überblick, kein automatisches Anhängen beim
            Kampfbeginn (der bleibt wie bisher eine bewusste SL-Auswahl im
            Kampfmodus). Leer = keine Verknüpfung. */}
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Verknüpfte Orte</label>
          <select
            multiple
            value={karte.ortIds ?? []}
            onChange={(e) => speichern({ ortIds: Array.from(e.target.selectedOptions, (o) => o.value) })}
            style={{ minWidth: 180, minHeight: 60 }}
          >
            {orte.length === 0 && <option disabled>Noch keine Orte angelegt</option>}
            {orte.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Verknüpfte Events</label>
          <select
            multiple
            value={karte.eventIds ?? []}
            onChange={(e) => speichern({ eventIds: Array.from(e.target.selectedOptions, (o) => o.value) })}
            style={{ minWidth: 180, minHeight: 60 }}
          >
            {events.length === 0 && <option disabled>Noch keine Events angelegt</option>}
            {events.map((ev) => (
              <option key={ev.id} value={ev.id}>
                {ev.title}
              </option>
            ))}
          </select>
        </div>
        <label className="zb-feld">
          <span>Hintergrundbild</span>
          {karte.bildUrl && <img src={karte.bildUrl} alt="" className="zb-bild-vorschau" />}
          <input type="file" accept="image/*" onChange={bildWaehlen} disabled={ladeBild} />
          <BildZeichenKnopfe
            uploadPfad={`/api/campaigns/${campaignId}/battlemaps/${karte.id}/bild`}
            bildUrl={karte.bildUrl}
            disabled={ladeBild}
            onBlob={async (blob) => {
              const datei = new File([blob], "skizze.png", { type: blob.type || "image/png" });
              onGeaendert(await battlemapApi.bildHochladen(campaignId, karte.id, datei));
            }}
            onGespeichert={(antwort) => {
              if (antwort && typeof antwort.id === "string") onGeaendert(antwort as unknown as Battlemap);
            }}
          />
        </label>
        {fehler && <p className="zb-fehler">{fehler}</p>}
        <button type="button" className="zb-loeschen-btn" onClick={() => setLoeschenFrage(true)}>
          In den Papierkorb
        </button>
      </div>
      {loeschenFrage && (
        <Bestaetigung
          titel="Karte löschen"
          text={`Bist du sicher? „${karte.name}“ wandert in den Papierkorb.`}
          jaText="In Papierkorb"
          neinText="Abbrechen"
          onJa={async () => {
            await battlemapApi.geloeschtSetzen(campaignId, karte.id, true);
            onGeloescht(karte.id);
            onSchliessen();
          }}
          onNein={() => setLoeschenFrage(false)}
        />
      )}
    </Fenster>
  );
}
