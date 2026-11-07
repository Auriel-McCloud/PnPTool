import { useCallback, useEffect, useState } from "react";
import type { Person } from "../entities/api";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { GruppenChat } from "./GruppenChat";
import { gruppenApi, type Gruppe } from "./gruppenApi";
import { PersonSuchAuswahl } from "./PersonSuchAuswahl";

/**
 * SL-Verwaltung der Gruppenchats (Teil von „Kontakte“).
 *
 * Nur die SL legt Gruppen an; Mitglieder sind PCs und NPCs gemischt. Schließen
 * ist umkehrbar (die Gruppe verschwindet nur für die Spieler), Löschen entfernt
 * auch den Verlauf und fragt deshalb vorher nach.
 */
export function GruppenGm({
  campaignId,
  pcs,
  npcs,
}: {
  campaignId: string;
  pcs: Person[];
  npcs: Person[];
}) {
  const [gruppen, setGruppen] = useState<Gruppe[]>([]);
  const [editor, setEditor] = useState<{ gruppe: Gruppe | null } | null>(null);
  const [chat, setChat] = useState<Gruppe | null>(null);
  const [loeschen, setLoeschen] = useState<Gruppe | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  const laden = useCallback(async () => {
    try {
      setGruppen(await gruppenApi.liste(campaignId));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Gruppen konnten nicht geladen werden");
    }
  }, [campaignId]);

  useEffect(() => {
    void laden();
  }, [laden]);

  async function offenUmschalten(g: Gruppe) {
    try {
      await gruppenApi.aendern(campaignId, g.id, { offen: !g.offen });
      await laden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht umschalten");
    }
  }

  async function endgueltigLoeschen() {
    if (!loeschen) return;
    try {
      await gruppenApi.loeschen(campaignId, loeschen.id);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht löschen");
    }
    setLoeschen(null);
    await laden();
  }

  return (
    <fieldset className="kontakte-gm-neu">
      <legend>Gruppenchats</legend>
      <div className="kontakte-gm-neu-form">
        <button type="button" onClick={() => setEditor({ gruppe: null })}>
          ＋ Neue Gruppe
        </button>
      </div>

      {fehler && <p className="gruppen-fehler">{fehler}</p>}

      {gruppen.length === 0 ? (
        <p className="kontakte-gm-leer">Noch keine Gruppen. PCs und NPCs lassen sich frei mischen.</p>
      ) : (
        <table className="kontakte-gm-tabelle">
          <thead>
            <tr>
              <th>Gruppe</th>
              <th>Mitglieder</th>
              <th>Chat</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {gruppen.map((g) => (
              <tr key={g.id}>
                <td>{g.name}</td>
                <td className="gruppen-mitglieder">{g.teilnehmer.map((t) => t.name).join(", ") || "—"}</td>
                <td>
                  <button
                    type="button"
                    className={`kontakte-gm-toggle ${g.offen ? "aktiv" : ""}`}
                    onClick={() => void offenUmschalten(g)}
                    title={g.offen ? "Gruppe für Spieler schließen" : "Gruppe für Spieler öffnen"}
                  >
                    {g.offen ? "offen" : "zu"}
                  </button>
                </td>
                <td className="gruppen-aktionen">
                  <button type="button" className="kontakte-gm-toggle" onClick={() => setChat(g)}>
                    Verlauf
                  </button>
                  <button type="button" className="kontakte-gm-toggle" onClick={() => setEditor({ gruppe: g })}>
                    Mitglieder
                  </button>
                  <button type="button" className="kontakte-gm-loeschen" onClick={() => setLoeschen(g)}>
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {editor && (
        <GruppenEditor
          campaignId={campaignId}
          start={editor.gruppe}
          pcs={pcs}
          npcs={npcs}
          onSchliessen={() => {
            setEditor(null);
            void laden();
          }}
        />
      )}

      {chat && (
        <Fenster
          offen={true}
          titel={chat.name}
          unterzeile="Gruppenchat"
          kennung={`gm-gruppe:${chat.id}`}
          onSchliessen={() => setChat(null)}
        >
          <div className="msg-huelle msg-gm-chat">
            <GruppenChat campaignId={campaignId} gruppeId={chat.id} alsGm />
          </div>
        </Fenster>
      )}

      {loeschen && (
        <Bestaetigung
          titel="Gruppe löschen?"
          text={`„${loeschen.name}“ wird samt dem ganzen Verlauf gelöscht. Zum bloßen Verstecken reicht „schließen“.`}
          jaText="Ja, löschen"
          onJa={() => void endgueltigLoeschen()}
          onNein={() => setLoeschen(null)}
        />
      )}
    </fieldset>
  );
}

interface Mitglied {
  id: string;
  name: string;
  istNpc: boolean;
}

/**
 * Anlegen und Mitglieder bearbeiten in einem Fenster.
 *
 * Neu: Name und Mitglieder werden gesammelt und mit „Gruppe anlegen“ gespeichert.
 * Bestehende Gruppe: Hinzufügen/Entfernen wirkt sofort, der Name über „Umbenennen“.
 */
function GruppenEditor({
  campaignId,
  start,
  pcs,
  npcs,
  onSchliessen,
}: {
  campaignId: string;
  start: Gruppe | null;
  pcs: Person[];
  npcs: Person[];
  onSchliessen: () => void;
}) {
  const [gruppe, setGruppe] = useState<Gruppe | null>(start);
  const [name, setName] = useState(start?.name ?? "");
  const [entwurf, setEntwurf] = useState<Mitglied[]>([]);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  const mitglieder: Mitglied[] = gruppe
    ? gruppe.teilnehmer.map((t) => ({ id: t.id, name: t.name, istNpc: t.istNpc }))
    : entwurf;
  const drin = new Set(mitglieder.map((m) => m.id));

  // Die Suche trennt PCs und NPCs über den Namenszusatz, damit gleiche Namen unterscheidbar bleiben.
  const kandidaten: Person[] = [
    ...pcs.map((p) => ({ ...p, name: `${p.name} (PC)` })),
    ...npcs.map((p) => ({ ...p, name: `${p.name} (NPC)` })),
  ].filter((p) => !drin.has(p.id));

  async function aufruf(fn: () => Promise<void>) {
    setLaeuft(true);
    setFehler(null);
    try {
      await fn();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Das hat nicht geklappt");
    } finally {
      setLaeuft(false);
    }
  }

  function hinzufuegen(id: string) {
    if (!id || drin.has(id)) return;
    const person = [...pcs, ...npcs].find((p) => p.id === id);
    if (!person) return;
    if (!gruppe) {
      setEntwurf((alt) => [...alt, { id, name: person.name, istNpc: person.personType === "NPC" }]);
      return;
    }
    void aufruf(async () => setGruppe(await gruppenApi.teilnehmerHinzu(campaignId, gruppe.id, id)));
  }

  function entfernen(id: string) {
    if (!gruppe) {
      setEntwurf((alt) => alt.filter((m) => m.id !== id));
      return;
    }
    void aufruf(async () => setGruppe(await gruppenApi.teilnehmerEntfernen(campaignId, gruppe.id, id)));
  }

  function speichern() {
    const sauber = name.trim();
    if (!sauber) return;
    void aufruf(async () => {
      if (!gruppe) {
        await gruppenApi.anlegen(
          campaignId,
          sauber,
          entwurf.map((m) => m.id),
        );
        onSchliessen();
      } else {
        setGruppe(await gruppenApi.aendern(campaignId, gruppe.id, { name: sauber }));
      }
    });
  }

  const nameGeaendert = gruppe ? name.trim() !== gruppe.name : true;

  return (
    <Fenster
      offen={true}
      titel={gruppe ? `Gruppe: ${gruppe.name}` : "Neue Gruppe"}
      unterzeile="Name und Mitglieder"
      kennung={`gm-gruppe-editor:${start?.id ?? "neu"}`}
      onSchliessen={onSchliessen}
    >
      <div className="gruppen-editor">
        <label className="gruppen-feld">
          <span>Name</span>
          <input
            type="text"
            value={name}
            maxLength={120}
            placeholder="z.B. Nachtschicht im Hafen"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") speichern();
            }}
          />
        </label>

        <div className="gruppen-feld">
          <span>Mitglieder ({mitglieder.length})</span>
          {mitglieder.length === 0 ? (
            <p className="gruppen-leer">Noch niemand. Mischen geht frei: Spielercharaktere und NPCs.</p>
          ) : (
            <ul className="gruppen-chips">
              {mitglieder.map((m) => (
                <li key={m.id} className="gruppen-chip" data-npc={m.istNpc}>
                  <span>
                    {m.name}
                    <em>{m.istNpc ? " NPC" : " PC"}</em>
                  </span>
                  <button type="button" disabled={laeuft} title="Entfernen" onClick={() => entfernen(m.id)}>
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="gruppen-feld">
          <span>Hinzufügen</span>
          <PersonSuchAuswahl personen={kandidaten} wert="" onWaehlen={hinzufuegen} platzhalter="PC oder NPC suchen..." />
        </div>

        {fehler && <p className="gruppen-fehler">{fehler}</p>}

        <div className="gruppen-fuss">
          <button type="button" className="cl-roehre" onClick={onSchliessen}>
            {gruppe ? "Fertig" : "Abbrechen"}
          </button>
          {(!gruppe || nameGeaendert) && (
            <button type="button" className="cl-roehre" disabled={laeuft || !name.trim()} onClick={speichern}>
              {gruppe ? "Umbenennen" : "Gruppe anlegen"}
            </button>
          )}
        </div>
      </div>
    </Fenster>
  );
}
