import { useEffect, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { Koerperkarte } from "./Koerperkarte";
import { ErklaerungSchalter } from "./ErklaerungSchalter";

/**
 * Der Bereich "Regeln".
 *
 * Erster Inhalt ist die **Körperkarte**: wo sitzt welches Implantat.
 * Mark: *"Wir wollten ja auch noch dieses Menü machen das anzeigt wo was
 * verbaut ist, das könnten wir dann über das Menü Regeln"*.
 *
 * Für die Spielleitung mit Charakterauswahl (sie schaut auf fremde Bögen),
 * für Spieler direkt auf den eigenen.
 */
export function RegelnAnsicht({
  campaignId,
  eigenePersonId,
}: {
  campaignId: string;
  /** Gesetzt = Spieleransicht: nur der eigene Charakter, keine Auswahl. */
  eigenePersonId?: string | null;
}) {
  const [personen, setPersonen] = useState<Person[]>([]);
  const [gewaehlt, setGewaehlt] = useState<string | null>(eigenePersonId ?? null);
  const [laedt, setLaedt] = useState(!eigenePersonId);

  useEffect(() => {
    if (eigenePersonId) return; // Spieler brauchen keine Auswahl
    entitiesApi
      .listPersonen(campaignId)
      .then((alle) => {
        setPersonen(alle);
        // Ohne Vorauswahl bleibt die Seite leer und wirkt kaputt.
        const pcs = alle.filter((p) => p.personType === "PC");
        setGewaehlt((v) => v ?? (pcs[0]?.id ?? alle[0]?.id ?? null));
      })
      .finally(() => setLaedt(false));
  }, [campaignId, eigenePersonId]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
      <section>
        <h3 style={{ margin: "0 0 8px", fontSize: 13, letterSpacing: "0.08em", color: "var(--text-aus)" }}>
          KÖRPERKARTE
        </h3>

        {!eigenePersonId && (
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
            <label style={{ fontSize: 12, color: "var(--text-leise)" }}>Charakter</label>
            <select
              value={gewaehlt ?? ""}
              onChange={(e) => setGewaehlt(e.target.value || null)}
              style={{ minWidth: 0, maxWidth: "100%" }}
            >
              {personen.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.personType === "NPC" ? "(NPC)" : ""}
                </option>
              ))}
            </select>
          </div>
        )}

        {laedt && <p style={{ color: "var(--text-leise)" }}>Lädt…</p>}

        {!laedt && !gewaehlt && (
          <p style={{ color: "var(--text-leise)" }}>Kein Charakter vorhanden.</p>
        )}

        {gewaehlt && (
          <Koerperkarte
            campaignId={campaignId}
            personId={gewaehlt}
            // Nur die Spielleitung stellt die Silhouette um.
            aenderbar={!eigenePersonId}
            key={gewaehlt}
          />
        )}
      </section>

      {!eigenePersonId && (
        <section>
          <h3 style={{ margin: "0 0 8px", fontSize: 13, letterSpacing: "0.08em", color: "var(--text-aus)" }}>
            REGELERKLÄRUNGEN
          </h3>
          <ErklaerungSchalter />
        </section>
      )}
    </div>
  );
}
