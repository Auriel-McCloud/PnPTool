import { useCallback, useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import type { PersonOption } from "../entities/VisibilitySelector";
import { entitiesApi, type Event, type Ort, type Person } from "../entities/api";
import { api } from "../api/client";
import { battlemapApi, type Battlemap } from "./api";
import { BattlemapPopup } from "./BattlemapPopup";
import { BattlemapEinstellungen } from "./BattlemapEinstellungen";
import "../zeichnungen/whiteboard.css";

const SICHTBARKEIT_LABEL: Record<Battlemap["sichtbarkeit"], string> = {
  GM: "SL-geheim",
  ALLE: "Für alle",
  SPEZIFISCH: "Einzelne Spieler",
};

export function BattlemapAnsicht({
  campaignId,
  istGm,
  eigenePersonId,
}: {
  campaignId: string;
  eigenePersonId?: string | null;
  istGm: boolean;
}) {
  const [liste, setListe] = useState<Battlemap[]>([]);
  const [ladend, setLadend] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuerName, setNeuerName] = useState("");
  const [offene, setOffene] = useState<Battlemap | null>(null);
  const [einstellungen, setEinstellungen] = useState<Battlemap | null>(null);
  const [papierkorbOffen, setPapierkorbOffen] = useState(false);
  const [papierkorb, setPapierkorb] = useState<Battlemap[]>([]);
  const [allePersonen, setAllePersonen] = useState<Person[]>([]);
  // Nur fürs Anzeigen der Verknüpfungs-Badges — die SL legt die Verknüpfung
  // selbst in den Karten-Einstellungen an (06.11.2026).
  const [alleOrte, setAlleOrte] = useState<Ort[]>([]);
  const [alleEvents, setAlleEvents] = useState<Event[]>([]);
  const pcOptions: PersonOption[] = useMemo(
    () => allePersonen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name })),
    [allePersonen],
  );

  const laden = useCallback(async () => {
    setLadend(true);
    try {
      setListe(await battlemapApi.liste(campaignId));
      if (istGm) {
        setAllePersonen(await api.get<Person[]>(`/api/campaigns/${campaignId}/personen`));
        setAlleOrte(await entitiesApi.listOrte(campaignId));
        setAlleEvents(await entitiesApi.listEvents(campaignId));
      }
    } catch {
      setFehler("Karten konnten nicht geladen werden");
    } finally {
      setLadend(false);
    }
  }, [campaignId, istGm]);

  useEffect(() => {
    void laden();
  }, [laden]);

  async function anlegen() {
    if (!neuerName.trim()) return;
    const neu = await battlemapApi.anlegen(campaignId, neuerName.trim());
    setNeuerName("");
    setAnlegenOffen(false);
    setListe((alt) => [...alt, neu]);
    setOffene(neu);
  }

  const darfZeichnen = (z: Battlemap) => istGm || z.spielerDuerfenZeichnen;

  return (
    <div className="zb-ansicht" style={{ ["--bereich-whiteboard" as string]: "var(--bereich-battlemap)" }}>
      <div className="zb-header">
        <div className="zb-header-zeile">
          <h2>Battlemap</h2>
          {istGm && (
            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                className="zb-mini-btn"
                onClick={async () => {
                  setPapierkorb(await battlemapApi.papierkorb(campaignId));
                  setPapierkorbOffen(true);
                }}
              >
                Papierkorb
              </button>
              <button type="button" className="zb-neu-btn" onClick={() => setAnlegenOffen(true)}>
                + Neue Karte
              </button>
            </div>
          )}
        </div>
        <p className="zb-beschreibung">Hex-Karten vorbereiten. Der Kampf hängt eine an.</p>
      </div>
      {fehler && <p className="zb-fehler">{fehler}</p>}
      {ladend && <p className="zb-leer">Lädt…</p>}
      {!ladend && liste.length === 0 && (
        <p className="zb-leer">{istGm ? "Noch keine Karte." : "Noch keine Karte freigegeben."}</p>
      )}
      <ul className="zb-liste">
        {liste.map((z) => (
          <li key={z.id} className="zb-item">
            <button type="button" className="zb-item-klickbar" onClick={() => setOffene(z)}>
              <span className="zb-icon">⬡</span>
              <span className="zb-inhalt">
                <strong>{z.name}</strong>
                <span className="zb-badges">
                  <span className="zb-badge">{SICHTBARKEIT_LABEL[z.sichtbarkeit]}</span>
                  {istGm &&
                    z.ortIds.map((id) => {
                      const o = alleOrte.find((x) => x.id === id);
                      return o ? (
                        <span key={id} className="zb-badge">
                          📍 {o.name}
                        </span>
                      ) : null;
                    })}
                  {istGm &&
                    z.eventIds.map((id) => {
                      const e = alleEvents.find((x) => x.id === id);
                      return e ? (
                        <span key={id} className="zb-badge">
                          ⚡ {e.title}
                        </span>
                      ) : null;
                    })}
                </span>
              </span>
            </button>
            {istGm && (
              <button type="button" className="zb-zahnrad" onClick={() => setEinstellungen(z)}>
                ⚙
              </button>
            )}
          </li>
        ))}
      </ul>
      <BattlemapPopup
        offen={Boolean(offene)}
        karte={offene}
        campaignId={campaignId}
        darfZeichnen={offene ? darfZeichnen(offene) : false}
        istGm={istGm}
        eigenePersonId={eigenePersonId}
        onSchliessen={() => setOffene(null)}
        onEinstellungenOeffnen={() => offene && setEinstellungen(offene)}
        onKarte={(k) => {
          setListe((alt) => alt.map((x) => (x.id === k.id ? k : x)));
          setOffene(k);
        }}
      />
      {istGm && (
        <BattlemapEinstellungen
          offen={Boolean(einstellungen)}
          karte={einstellungen}
          campaignId={campaignId}
          pcOptions={pcOptions}
          onSchliessen={() => setEinstellungen(null)}
          onGeaendert={(k) => {
            setListe((alt) => alt.map((x) => (x.id === k.id ? k : x)));
            setEinstellungen(k);
            setOffene((o) => (o?.id === k.id ? k : o));
          }}
          onGeloescht={(id) => {
            setListe((alt) => alt.filter((x) => x.id !== id));
            setOffene((o) => (o?.id === id ? null : o));
          }}
        />
      )}
      {istGm && (
        <Fenster
          offen={anlegenOffen}
          titel="Neue Karte"
          kennung="battlemap-anlegen"
          ton="var(--bereich-battlemap)"
          onSchliessen={() => setAnlegenOffen(false)}
        >
          <div className="zb-anlegen-form">
            <label className="zb-feld">
              <span>Name</span>
              <input
                className="zb-input"
                value={neuerName}
                onChange={(e) => setNeuerName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void anlegen()}
              />
            </label>
            <button type="button" className="zb-neu-btn" disabled={!neuerName.trim()} onClick={() => void anlegen()}>
              Anlegen
            </button>
          </div>
        </Fenster>
      )}
      {istGm && (
        <Fenster
          offen={papierkorbOffen}
          titel="Battlemap-Papierkorb"
          kennung="battlemap-papierkorb"
          ton="var(--bereich-battlemap)"
          onSchliessen={() => setPapierkorbOffen(false)}
        >
          {papierkorb.length === 0 && <p className="zb-leer">Papierkorb ist leer.</p>}
          <ul className="zb-liste">
            {papierkorb.map((z) => (
              <li key={z.id} className="zb-item">
                <strong>{z.name}</strong>
                <button
                  type="button"
                  className="zb-mini-btn"
                  onClick={async () => {
                    await battlemapApi.geloeschtSetzen(campaignId, z.id, false);
                    setPapierkorb((alt) => alt.filter((x) => x.id !== z.id));
                    await laden();
                  }}
                >
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
