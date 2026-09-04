import { useEffect, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { itemsApi } from "../items/api";
import { Koerperkarte } from "../regeln/Koerperkarte";

/**
 * Augments-Bereich: zeigt wo welches Implantat sitzt.
 *
 * Dieser Bereich erscheint NUR, wenn der Charakter mindestens ein Augment
 * verbaut hat — ein Charakter ohne Cyberware braucht keine Körperkarte.
 *
 * Für die Spielleitung mit Charakterauswahl (sie schaut auf fremde Bögen),
 * für Spieler direkt auf den eigenen.
 */
export function AugmentsAnsicht({
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
    if (eigenePersonId) return;
    entitiesApi
      .listPersonen(campaignId)
      .then((alle) => {
        setPersonen(alle);
        const pcs = alle.filter((p) => p.personType === "PC");
        if (!gewaehlt && pcs.length > 0) {
          setGewaehlt(pcs[0].id);
        }
      })
      .catch(() => setPersonen([]))
      .finally(() => setLaedt(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, eigenePersonId]);

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade…</p>;

  return (
    <div style={{ padding: "var(--abstand)" }}>
      {/* Nur die SL bekommt eine Auswahl — Spieler sehen nur ihren eigenen. */}
      {!eigenePersonId && (
        <div style={{ marginBottom: "var(--abstand)", display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <label htmlFor="aug-char" style={{ color: "var(--text-leise)", fontSize: "0.85rem" }}>
            Charakter:
          </label>
          <select
            id="aug-char"
            value={gewaehlt ?? ""}
            onChange={(e) => setGewaehlt(e.target.value || null)}
            style={{ font: "inherit" }}
          >
            <option value="">— wählen —</option>
            {personen.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} {p.personType === "NPC" && "(NPC)"}
              </option>
            ))}
          </select>
        </div>
      )}

      {gewaehlt && (
        <Koerperkarte
          campaignId={campaignId}
          personId={gewaehlt}
        />
      )}
    </div>
  );
}

/**
 * Prüft, ob ein Charakter verbaute Augments hat.
 *
 * Wird verwendet, um den Menüpunkt dynamisch ein-/auszublenden.
 */
export async function hatVerbauteAugments(campaignId: string, personId: string): Promise<boolean> {
  try {
    const verbautes = await itemsApi.verbautes(campaignId, personId);
    return verbautes.length > 0;
  } catch {
    return false;
  }
}

/**
 * Hook: prüft ob der Charakter verbaute Augments hat.
 */
export function useHatAugments(campaignId: string | null, personId: string | null): boolean {
  const [hat, setHat] = useState(false);

  useEffect(() => {
    if (!campaignId || !personId) {
      setHat(false);
      return;
    }
    hatVerbauteAugments(campaignId, personId)
      .then(setHat)
      .catch(() => setHat(false));
  }, [campaignId, personId]);

  return hat;
}
