import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { entitiesApi, type EntityKind } from "../entities/api";
import type { VerweisAttribute } from "../richtext/EntitaetsVerweis";

interface Treffer {
  id: string;
  label: string;
  typ: EntityKind;
}

const TYP_TOKEN: Record<EntityKind, string> = {
  Person: "--kind-person",
  Ort: "--kind-ort",
  Event: "--kind-event",
  Gegenstand: "--kind-gegenstand",
};

/**
 * Auswahl einer Kampagnen-Entität zum Verknüpfen.
 *
 * Sucht über alles, was verlinkt werden kann — Suchen statt Blättern, weil
 * eine gewachsene Kampagne schnell vierzig NPCs hat.
 *
 * Bewusst *keine* Möglichkeit, hier neue Entitäten anzulegen: Marks Regel für
 * die spätere automatische Erkennung war "erkennen ja, ungefragt anlegen
 * nein". Wer im Wiki einen neuen NPC braucht, legt ihn im NPC-Bereich an —
 * sonst entstehen beim Schreiben unbemerkt halbe Karteileichen.
 */
export function VerweisWaehler({
  campaignId,
  offen,
  onWaehlen,
  onSchliessen,
}: {
  campaignId: string;
  offen: boolean;
  onWaehlen: (attrs: VerweisAttribute) => void;
  onSchliessen: () => void;
}) {
  const [alle, setAlle] = useState<Treffer[]>([]);
  const [suche, setSuche] = useState("");
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    let abgebrochen = false;
    setLaedt(true);
    setFehler(null);

    Promise.all([
      entitiesApi.listPersonen(campaignId),
      entitiesApi.listOrte(campaignId),
      entitiesApi.listEvents(campaignId),
    ])
      .then(([personen, orte, events]) => {
        if (abgebrochen) return;
        setAlle([
          ...personen.map((p) => ({ id: p.id, label: p.name, typ: "Person" as const })),
          ...orte.map((o) => ({ id: o.id, label: o.name, typ: "Ort" as const })),
          ...events.map((e) => ({ id: e.id, label: e.title, typ: "Event" as const })),
        ]);
      })
      .catch((e) => !abgebrochen && setFehler(e instanceof Error ? e.message : "Laden fehlgeschlagen"))
      .finally(() => !abgebrochen && setLaedt(false));

    return () => {
      abgebrochen = true;
    };
  }, [campaignId, offen]);

  const treffer = useMemo(() => {
    const s = suche.trim().toLowerCase();
    const gefiltert = s ? alle.filter((t) => t.label.toLowerCase().includes(s)) : alle;
    return gefiltert.slice(0, 60);
  }, [alle, suche]);

  return (
    <Fenster
      offen={offen}
      titel="Verknüpfen"
      unterzeile="Wen oder was erwähnt diese Stelle?"
      kennung="wiki-verweis-waehler"
      onSchliessen={onSchliessen}
    >
      <input
        className="wk-suche"
        autoFocus
        placeholder="Suchen…"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
      />

      {laedt && <p style={{ color: "var(--text-leise)" }}>Lade…</p>}
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      {!laedt && !fehler && treffer.length === 0 && (
        <p style={{ color: "var(--text-leise)" }}>
          {suche ? "Nichts gefunden." : "Noch nichts angelegt, was verknüpft werden könnte."}
        </p>
      )}

      <div className="wk-treffer">
        {treffer.map((t) => (
          <button
            key={`${t.typ}:${t.id}`}
            type="button"
            className="wk-treffer-zeile"
            onClick={() => {
              onWaehlen({ zielId: t.id, zielTyp: t.typ, label: t.label });
              onSchliessen();
            }}
          >
            <span
              className="wk-treffer-typ"
              style={{ "--ton": `var(${TYP_TOKEN[t.typ]})` } as React.CSSProperties}
            >
              {t.typ}
            </span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>
    </Fenster>
  );
}
