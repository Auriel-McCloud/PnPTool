import { useEffect, useState } from "react";
import { setViewAs } from "../api/client";
import { entitiesApi, type Person } from "../entities/api";

/**
 * SL-Vorschau: lässt den Spielleiter die Kampagne durch die Augen einer Person
 * ansehen. Der gewählte Charakter wird im API-Client hinterlegt, der ihn dann
 * an jeden Lesezugriff anhängt (siehe api/client.ts).
 *
 * `onChange` meldet den Wechsel nach oben, damit die Ansichten neu geladen
 * werden können — der API-Client allein löst kein Rerendering aus.
 */
export function ViewAsSwitcher({
  campaignId,
  value,
  onChange,
}: {
  campaignId: string;
  value: string | null;
  onChange: (personId: string | null) => void;
}) {
  const [personen, setPersonen] = useState<Person[]>([]);

  useEffect(() => {
    // Bewusst ungefiltert geladen: sonst könnte der gerade betrachtete
    // Charakter aus der eigenen Auswahlliste verschwinden.
    entitiesApi.listPersonenAlsGm(campaignId).then(setPersonen).catch(() => setPersonen([]));
  }, [campaignId]);

  function handleChange(next: string) {
    const personId = next === "" ? null : next;
    // Erst den Client umstellen, dann nach oben melden: der Effect, der die
    // Daten nachlädt, läuft erst nach dem Rerender und sieht so den neuen Wert.
    setViewAs(personId);
    onChange(personId);
  }

  const aktiv = value !== null;
  const gewaehlt = personen.find((p) => p.id === value);

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: 8,
        marginBottom: 16,
        padding: "8px 12px",
        borderRadius: "var(--radius)",
        border: `1px solid ${aktiv ? "var(--warn)" : "var(--linie)"}`,
        background: aktiv ? "rgba(255, 182, 72, 0.1)" : "var(--flaeche)",
      }}
    >
      <label style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", minWidth: 0 }}>
        <span>Ansicht:</span>
        <select value={value ?? ""} onChange={(e) => handleChange(e.target.value)} style={{ maxWidth: "100%" }}>
          <option value="">Spielleiter (alles sichtbar)</option>
          {personen.map((p) => (
            <option key={p.id} value={p.id}>
              als {p.name} ({p.personType})
            </option>
          ))}
        </select>
      </label>

      {aktiv && (
        <>
          <strong style={{ color: "var(--warn)" }}>
            👁 Vorschau: du siehst nur, was {gewaehlt?.name ?? "dieser Charakter"} sehen darf
          </strong>
          <button type="button" onClick={() => handleChange("")}>
            Zurück zur SL-Sicht
          </button>
        </>
      )}
    </div>
  );
}
