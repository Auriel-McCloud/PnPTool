import { useCallback, useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import type { PersonOption } from "../entities/VisibilitySelector";
import type { Person } from "../entities/api";
import { api } from "../api/client";
import { zeichnungenApi, type Zeichnung } from "./api";
import { WhiteboardPopup } from "./WhiteboardPopup";
import { ZeichnungEinstellungenPopup } from "./ZeichnungEinstellungenPopup";
import "./whiteboard.css";

const SICHTBARKEIT_LABEL: Record<Zeichnung["sichtbarkeit"], string> = {
  GM: "SL-geheim",
  ALLE: "Für alle",
  SPEZIFISCH: "Einzelne Spieler",
};

/**
 * Whiteboard: mehrere speicherbare, live mitzeichenbare Boards pro Kampagne.
 *
 * Gemeinsame Komponente für SL und Spieler (wie ShopUebersicht): `istGm`
 * schaltet Anlegen/Einstellungen/Papierkorb frei, die Liste selbst zeigt dem
 * Spieler ohnehin nur, was der Server für ihn sichtbar macht.
 */
export function ZeichnungenAnsicht({
  campaignId,
  istGm,
}: {
  campaignId: string;
  /** Nur zur API-Konsistenz mit anderen geteilten Ansichten (z.B.
   *  ShopUebersicht) — die Sichtbarkeitsfilterung läuft serverseitig, das
   *  Frontend braucht die eigene Person-ID hier nicht. */
  eigenePersonId?: string | null;
  istGm: boolean;
}) {
  const [liste, setListe] = useState<Zeichnung[]>([]);
  const [ladend, setLadend] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);

  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuerName, setNeuerName] = useState("");
  const [anlegenLaeuft, setAnlegenLaeuft] = useState(false);

  const [offenesBoard, setOffenesBoard] = useState<Zeichnung | null>(null);
  const [einstellungenFuer, setEinstellungenFuer] = useState<Zeichnung | null>(null);
  const [papierkorbOffen, setPapierkorbOffen] = useState(false);
  const [papierkorb, setPapierkorb] = useState<Zeichnung[]>([]);

  // Für die Sichtbarkeits-Auswahl im Einstellungen-Popup (nur SL braucht sie).
  const [allePersonen, setAllePersonen] = useState<Person[]>([]);
  const pcOptions: PersonOption[] = useMemo(
    () => allePersonen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name })),
    [allePersonen],
  );

  const laden = useCallback(async () => {
    setLadend(true);
    setFehler(null);
    try {
      const daten = await zeichnungenApi.liste(campaignId);
      setListe(daten);
      if (istGm) {
        const personen = await api.get<Person[]>(`/api/campaigns/${campaignId}/personen`);
        setAllePersonen(personen);
      }
    } catch {
      setFehler("Boards konnten nicht geladen werden");
    } finally {
      setLadend(false);
    }
  }, [campaignId, istGm]);

  useEffect(() => {
    laden();
  }, [laden]);

  async function papierkorbLaden() {
    try {
      setPapierkorb(await zeichnungenApi.papierkorb(campaignId));
    } catch {
      setFehler("Papierkorb konnte nicht geladen werden");
    }
    setPapierkorbOffen(true);
  }

  async function anlegen() {
    if (!neuerName.trim() || anlegenLaeuft) return;
    setAnlegenLaeuft(true);
    try {
      const neu = await zeichnungenApi.anlegen(campaignId, neuerName.trim());
      setNeuerName("");
      setAnlegenOffen(false);
      setListe((alt) => [...alt, neu]);
      setOffenesBoard(neu);
    } catch {
      setFehler("Anlegen fehlgeschlagen");
    } finally {
      setAnlegenLaeuft(false);
    }
  }

  function beiGeaendert(aktualisiert: Zeichnung) {
    setListe((alt) => alt.map((z) => (z.id === aktualisiert.id ? aktualisiert : z)));
    setEinstellungenFuer(aktualisiert);
    setOffenesBoard((aktuell) => (aktuell && aktuell.id === aktualisiert.id ? aktualisiert : aktuell));
  }

  function beiGeloescht(id: string) {
    setListe((alt) => alt.filter((z) => z.id !== id));
    setOffenesBoard((aktuell) => (aktuell?.id === id ? null : aktuell));
  }

  async function wiederherstellen(z: Zeichnung) {
    try {
      await zeichnungenApi.geloeschtSetzen(campaignId, z.id, false);
      setPapierkorb((alt) => alt.filter((x) => x.id !== z.id));
      await laden();
    } catch {
      setFehler("Wiederherstellen fehlgeschlagen");
    }
  }

  const darfZeichnen = (z: Zeichnung) => istGm || z.spielerDuerfenZeichnen;

  return (
    <div className="zb-ansicht">
      <div className="zb-header">
        <div className="zb-header-zeile">
          <h2>Whiteboard</h2>
          {istGm && (
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" className="zb-mini-btn" onClick={papierkorbLaden}>
                🗑 Papierkorb
              </button>
              <button type="button" className="zb-neu-btn" onClick={() => setAnlegenOffen(true)}>
                + Neue Zeichnung
              </button>
            </div>
          )}
        </div>
        <p className="zb-beschreibung">Gemeinsame Boards zum Live-Mitzeichnen, mehrere pro Kampagne.</p>
      </div>

      {fehler && <p className="zb-fehler">{fehler}</p>}
      {ladend && <p className="zb-leer">Lädt…</p>}
      {!ladend && liste.length === 0 && (
        <p className="zb-leer">
          {istGm
            ? "Noch kein Board angelegt — leg mit „+ Neue Zeichnung“ los."
            : "Die Spielleitung hat noch kein Board freigegeben."}
        </p>
      )}

      <ul className="zb-liste">
        {liste.map((z) => (
          <li key={z.id} className="zb-item">
            <button type="button" className="zb-item-klickbar" onClick={() => setOffenesBoard(z)}>
              <span className="zb-icon">🖊</span>
              <span className="zb-inhalt">
                <strong>{z.name}</strong>
                <span className="zb-badges">
                  <span className="zb-badge">{SICHTBARKEIT_LABEL[z.sichtbarkeit]}</span>
                  {darfZeichnen(z) ? (
                    <span className="zb-badge zb-badge-gut">Zeichnen erlaubt</span>
                  ) : (
                    <span className="zb-badge">Nur Zusehen</span>
                  )}
                </span>
              </span>
            </button>
            {istGm && (
              <button
                type="button"
                className="zb-zahnrad"
                title="Einstellungen"
                onClick={() => setEinstellungenFuer(z)}
              >
                ⚙
              </button>
            )}
          </li>
        ))}
      </ul>

      <WhiteboardPopup
        offen={Boolean(offenesBoard)}
        zeichnung={offenesBoard}
        campaignId={campaignId}
        darfZeichnen={offenesBoard ? darfZeichnen(offenesBoard) : false}
        istGm={istGm}
        onSchliessen={() => setOffenesBoard(null)}
        onEinstellungenOeffnen={() => offenesBoard && setEinstellungenFuer(offenesBoard)}
      />

      {istGm && (
        <ZeichnungEinstellungenPopup
          offen={Boolean(einstellungenFuer)}
          zeichnung={einstellungenFuer}
          campaignId={campaignId}
          pcOptions={pcOptions}
          onSchliessen={() => setEinstellungenFuer(null)}
          onGeaendert={beiGeaendert}
          onGeloescht={beiGeloescht}
        />
      )}

      {istGm && (
        <Fenster
          offen={anlegenOffen}
          titel="Neue Zeichnung"
          kennung="zeichnung-anlegen"
          ton="var(--bereich-whiteboard)"
          onSchliessen={() => setAnlegenOffen(false)}
        >
          <div className="zb-anlegen-form">
            <label className="zb-feld">
              <span>Name</span>
              <input
                className="zb-input"
                autoFocus
                value={neuerName}
                onChange={(e) => setNeuerName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && anlegen()}
                placeholder="z.B. Kampfplan"
              />
            </label>
            <button type="button" className="zb-neu-btn" disabled={!neuerName.trim() || anlegenLaeuft} onClick={anlegen}>
              {anlegenLaeuft ? "Legt an…" : "Anlegen"}
            </button>
          </div>
        </Fenster>
      )}

      {istGm && (
        <Fenster
          offen={papierkorbOffen}
          titel="Whiteboard-Papierkorb"
          unterzeile="Gelöschte Boards — wiederherstellbar"
          kennung="zeichnung-papierkorb"
          ton="var(--bereich-whiteboard)"
          onSchliessen={() => setPapierkorbOffen(false)}
        >
          {papierkorb.length === 0 && <p className="zb-leer">Papierkorb ist leer.</p>}
          <ul className="zb-liste">
            {papierkorb.map((z) => (
              <li key={z.id} className="zb-item">
                <span className="zb-icon">🖊</span>
                <span className="zb-inhalt">
                  <strong>{z.name}</strong>
                </span>
                <button type="button" className="zb-mini-btn" onClick={() => wiederherstellen(z)}>
                  Wiederherstellen
                </button>
              </li>
            ))}
          </ul>
        </Fenster>
      )}
    </div>
  );
}
