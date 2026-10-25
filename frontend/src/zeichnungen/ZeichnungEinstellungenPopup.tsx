import { useState, type ChangeEvent } from "react";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { VisibilitySelector, type PersonOption } from "../entities/VisibilitySelector";
import { zeichnungenApi, type Zeichnung } from "./api";

/**
 * SL-Einstellungen für EIN Board: umbenennen, Zeichenfreigabe für Spieler,
 * Sichtbarkeit, Hintergrundbild, Papierkorb.
 *
 * Eigenes Fenster statt Inline-Formular im Canvas-Popup (Marks UI-Vorgabe:
 * Listen-Bearbeitung immer als gestyltes Commlink-Popup) — erreichbar über
 * das Zahnrad in der Kachelliste UND über das Zahnrad im offenen Whiteboard.
 */
export function ZeichnungEinstellungenPopup({
  offen,
  zeichnung,
  campaignId,
  pcOptions,
  onSchliessen,
  onGeaendert,
  onGeloescht,
}: {
  offen: boolean;
  zeichnung: Zeichnung | null;
  campaignId: string;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: (aktualisiert: Zeichnung) => void;
  /** Board ist in den Papierkorb gewandert — der Aufrufer soll die Liste neu holen. */
  onGeloescht: (id: string) => void;
}) {
  const [name, setName] = useState("");
  const [speichertName, setSpeichertName] = useState(false);
  const [ladeBild, setLadeBild] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenFrage, setLoeschenFrage] = useState(false);

  if (!zeichnung) return null;

  async function nameSpeichern() {
    if (!zeichnung || !name.trim() || name.trim() === zeichnung.name) return;
    setSpeichertName(true);
    setFehler(null);
    try {
      const aktualisiert = await zeichnungenApi.aktualisieren(campaignId, zeichnung.id, { name: name.trim() });
      onGeaendert(aktualisiert);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Umbenennen fehlgeschlagen");
    } finally {
      setSpeichertName(false);
    }
  }

  async function freigabeUmschalten() {
    if (!zeichnung) return;
    setFehler(null);
    try {
      const aktualisiert = await zeichnungenApi.aktualisieren(campaignId, zeichnung.id, {
        spielerDuerfenZeichnen: !zeichnung.spielerDuerfenZeichnen,
      });
      onGeaendert(aktualisiert);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Freigabe konnte nicht geändert werden");
    }
  }

  async function sichtbarkeitAendern(modus: Zeichnung["sichtbarkeit"], sichtbarFuer: string[]) {
    if (!zeichnung) return;
    setFehler(null);
    try {
      const aktualisiert = await zeichnungenApi.aktualisieren(campaignId, zeichnung.id, {
        sichtbarkeit: modus,
        sichtbarFuer,
      });
      onGeaendert(aktualisiert);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Sichtbarkeit konnte nicht geändert werden");
    }
  }

  async function bildWaehlen(e: ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    e.target.value = "";
    if (!datei || !zeichnung) return;
    setLadeBild(true);
    setFehler(null);
    try {
      const aktualisiert = await zeichnungenApi.bildHochladen(campaignId, zeichnung.id, datei);
      onGeaendert(aktualisiert);
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Bild-Upload fehlgeschlagen");
    } finally {
      setLadeBild(false);
    }
  }

  async function wirklichLoeschen() {
    if (!zeichnung) return;
    setLoeschenFrage(false);
    try {
      await zeichnungenApi.geloeschtSetzen(campaignId, zeichnung.id, true);
      onGeloescht(zeichnung.id);
      onSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
    }
  }

  return (
    <Fenster
      offen={offen}
      titel={`Board: ${zeichnung.name}`}
      unterzeile="Einstellungen — nur Spielleitung"
      kennung={`zeichnung-einstellungen-${zeichnung.id}`}
      ton="var(--bereich-whiteboard)"
      onSchliessen={() => {
        setName("");
        onSchliessen();
      }}
    >
      <div className="zb-einstellungen">
        <label className="zb-feld">
          <span>Name</span>
          <div className="zb-feld-zeile">
            <input
              className="zb-input"
              value={name || zeichnung.name}
              onChange={(e) => setName(e.target.value)}
              onBlur={nameSpeichern}
              disabled={speichertName}
            />
          </div>
        </label>

        <label className="zb-schalter-zeile">
          <input
            type="checkbox"
            checked={zeichnung.spielerDuerfenZeichnen}
            onChange={freigabeUmschalten}
          />
          <span>Spieler dürfen hier live mitzeichnen</span>
        </label>

        <VisibilitySelector
          label="Sichtbarkeit des Boards"
          modus={zeichnung.sichtbarkeit}
          sichtbarFuer={zeichnung.sichtbarFuer}
          onChange={sichtbarkeitAendern}
          pcOptions={pcOptions}
        />

        <label className="zb-feld">
          <span>Hintergrundbild (z.B. eine Karte)</span>
          <div className="zb-feld-zeile">
            {zeichnung.bildUrl && (
              <img src={zeichnung.bildUrl} alt="" className="zb-bild-vorschau" />
            )}
            <input type="file" accept="image/*" onChange={bildWaehlen} disabled={ladeBild} />
          </div>
        </label>

        {fehler && <p className="zb-fehler">{fehler}</p>}

        <button type="button" className="zb-loeschen-btn" onClick={() => setLoeschenFrage(true)}>
          In den Papierkorb
        </button>
      </div>

      {loeschenFrage && (
        <Bestaetigung
          titel="Board löschen"
          text={`Bist du sicher? „${zeichnung.name}“ wandert in den Papierkorb und ist von dort wiederherstellbar.`}
          jaText="In Papierkorb"
          neinText="Abbrechen"
          onJa={wirklichLoeschen}
          onNein={() => setLoeschenFrage(false)}
        />
      )}
    </Fenster>
  );
}
