import { useEffect, useState } from "react";
import type { EntityKind, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { Bestaetigung } from "../shell/Bestaetigung";

/**
 * Zeigt, was an einer Entität hängt — und lässt Verbindungen lösen.
 *
 * Die Verbindungen sind echte `VERBINDUNG`-Kanten im Graphen, nicht ein
 * Textfeld an der Entität. Wer hier "Gegner" bei einem Event einträgt, hat
 * danach denselben Eintrag im Beziehungsgraph und im NPC-Filter.
 *
 * Richtung wird angezeigt, aber nicht gewertet: ob "Wirt → arbeitet in →
 * Bar" oder "Bar → Stammgast → Wirt" angelegt wurde, ist eine Frage des
 * Erzählens. Der Filter findet beides.
 */

export interface BeziehungsZeile {
  verbindung: Verbindung;
  /** Name der Gegenseite, bereits sichtbarkeitsgefiltert geladen. */
  gegenueber: string;
  gegenueberKind: EntityKind;
  /** Zeigt die Kante von dieser Entität weg? */
  ausgehend: boolean;
}

const ART_SYMBOL: Record<string, string> = {
  Person: "◌",
  Ort: "⌖",
  Event: "◆",
  Gegenstand: "◈",
};

export function BeziehungsListe({
  campaignId,
  zeilen,
  onGeaendert,
  farbe,
}: {
  campaignId: string;
  zeilen: BeziehungsZeile[];
  onGeaendert: () => void;
  farbe: string;
}) {
  const [loeschKandidat, setLoeschKandidat] = useState<BeziehungsZeile | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  // Der Kandidat muss zurückgesetzt werden, wenn die Liste sich unter ihm
  // ändert (z.B. weil jemand anders die Kante gelöscht hat) — sonst bestätigt
  // man das Löschen von etwas, das es nicht mehr gibt.
  useEffect(() => {
    if (loeschKandidat && !zeilen.some((z) => z.verbindung.id === loeschKandidat.verbindung.id)) {
      setLoeschKandidat(null);
    }
  }, [zeilen, loeschKandidat]);

  async function loesen() {
    if (!loeschKandidat) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await entitiesApi.deleteVerbindung(campaignId, loeschKandidat.verbindung.id);
      setLoeschKandidat(null);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verbindung konnte nicht gelöst werden");
    } finally {
      setLaeuft(false);
    }
  }

  if (zeilen.length === 0) {
    return (
      <p style={{ color: "var(--text-leise)", fontStyle: "italic" }}>
        Noch keine Verbindungen. Anlegen lassen sie sich im Bereich <strong>Verbindungen</strong> —
        von dort speisen sich auch die Filter der Übersichten.
      </p>
    );
  }

  return (
    <>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 }}>
        {zeilen.map((z) => (
          <li
            key={z.verbindung.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              flexWrap: "wrap",
              padding: "8px 10px",
              background: "var(--flaeche)",
              border: "1px solid var(--linie)",
              borderRadius: "var(--radius)",
            }}
          >
            <span style={{ color: "var(--text-leise)", fontSize: "0.8rem", minWidth: 54 }}>
              {z.ausgehend ? "hierher →" : "← dorthin"}
            </span>
            <strong style={{ color: farbe }}>{z.verbindung.typ}</strong>
            <span style={{ minWidth: 0, overflowWrap: "break-word" }}>
              {ART_SYMBOL[z.gegenueberKind] ?? "·"} {z.gegenueber}
            </span>
            {z.verbindung.sichtbarkeit === "GM" && (
              <span title="Nur für die Spielleitung sichtbar" style={{ fontSize: "0.8rem" }}>
                🔒
              </span>
            )}
            <button
              type="button"
              onClick={() => setLoeschKandidat(z)}
              title="Verbindung lösen"
              style={{
                marginLeft: "auto",
                minHeight: 0,
                padding: "4px 10px",
                fontSize: 12,
                color: "var(--signal)",
              }}
            >
              Lösen
            </button>
          </li>
        ))}
      </ul>

      {fehler && <p style={{ color: "var(--signal)", marginTop: 8 }}>{fehler}</p>}

      {/* Rückfrage wie überall im Werkzeug — eine gelöste Verbindung ist
          nicht wiederherstellbar und ändert zugleich die Filter.
          Bestaetigung rendert immer, wenn es eingehängt ist (kein offen-Prop),
          deshalb die Bedingung hier davor. */}
      {loeschKandidat && (
        <Bestaetigung
          titel="Verbindung lösen?"
          text={`„${loeschKandidat.verbindung.typ}“ zu ${loeschKandidat.gegenueber} wird entfernt. Die Entitäten selbst bleiben bestehen.`}
          jaText={laeuft ? "Löst…" : "Ja, lösen"}
          neinText="Abbrechen"
          onJa={loesen}
          onNein={() => setLoeschKandidat(null)}
        />
      )}
    </>
  );
}

/** Baut die Anzeigezeilen aus den rohen Kanten und einer Namenstabelle. */
export function beziehungsZeilen(
  eigeneId: string,
  verbindungen: Verbindung[],
  namen: Map<string, { name: string; kind: EntityKind }>
): BeziehungsZeile[] {
  const zeilen: BeziehungsZeile[] = [];
  for (const v of verbindungen) {
    const ausgehend = v.vonId === eigeneId;
    const eingehend = v.zuId === eigeneId;
    if (!ausgehend && !eingehend) continue;
    const gegenId = ausgehend ? v.zuId : v.vonId;
    const treffer = namen.get(gegenId);
    // Ohne Namen nicht anzeigen: die Gegenseite ist dann für diesen
    // Blickwinkel unsichtbar, und eine Zeile mit roher ID verriete ihre
    // Existenz.
    if (!treffer) continue;
    zeilen.push({
      verbindung: v,
      gegenueber: treffer.name,
      gegenueberKind: treffer.kind,
      ausgehend,
    });
  }
  return zeilen.sort((a, b) => a.verbindung.typ.localeCompare(b.verbindung.typ, "de"));
}
