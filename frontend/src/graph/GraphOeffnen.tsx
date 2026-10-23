import { useEffect, useState } from "react";
import {
  entitiesApi,
  type EntityKind,
  type Event,
  type Fraktion,
  type Ort,
  type Person,
  type Verbindung,
} from "../entities/api";
import { EventDetail } from "../entities/EventDetail";
import { FraktionDetail } from "../entities/FraktionDetail";
import { NPCDetail } from "../entities/NPCDetail";
import { OrtDetail } from "../entities/OrtDetail";
import { PCDetail } from "../entities/PCDetail";
import { VerbindungBearbeiten } from "../entities/VerbindungBearbeiten";
import type { PersonOption } from "../entities/VisibilitySelector";
import { itemsApi, type Gegenstand } from "../items/api";
import { GegenstandRow } from "../traits/CharacterSheetPanel";

/**
 * Rechtsklick im Beziehungsgraphen öffnet dasselbe Fenster wie ein Klick in
 * der jeweiligen Liste — nicht eine zweite, abgespeckte Ansicht.
 *
 * Die Kante kennt der Graph nur als id/typ/Endpunkte. Beschreibung und
 * Sichtbarkeit liegen an der echten VERBINDUNG, deshalb wird die volle
 * Kante nachgeladen statt aus den Canvas-Daten zusammengebaut.
 */

export type GraphZiel =
  | { art: "knoten"; id: string; kind: EntityKind }
  | { art: "kante"; id: string };

interface Kontext {
  verbindungen: Verbindung[];
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  alleOptionen: PersonOption[];
}

type Offen =
  | { art: "person"; person: Person }
  | { art: "ort"; ort: Ort }
  | { art: "event"; event: Event }
  | { art: "fraktion"; fraktion: Fraktion }
  | { art: "gegenstand"; item: Gegenstand }
  | { art: "kante"; verbindung: Verbindung };

async function ladeKontext(campaignId: string): Promise<Kontext> {
  const [personen, orte, events, fraktionen, verbindungen, gegenstaende] = await Promise.all([
    entitiesApi.listPersonen(campaignId),
    entitiesApi.listOrte(campaignId),
    entitiesApi.listEvents(campaignId),
    entitiesApi.listFraktionen(campaignId),
    entitiesApi.listVerbindungen(campaignId),
    itemsApi.listAlle(campaignId),
  ]);
  const namen = new Map<string, { name: string; kind: EntityKind }>();
  for (const p of personen) namen.set(p.id, { name: p.name, kind: "Person" });
  for (const o of orte) namen.set(o.id, { name: o.name, kind: "Ort" });
  for (const e of events) namen.set(e.id, { name: e.title, kind: "Event" });
  for (const f of fraktionen) namen.set(f.id, { name: f.name, kind: "Fraktion" });
  for (const g of gegenstaende) namen.set(g.id, { name: g.name, kind: "Gegenstand" });
  return {
    verbindungen,
    namen,
    pcOptions: personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name })),
    alleOptionen: personen.map((p) => ({ id: p.id, name: `${p.name} (${p.personType})` })),
  };
}

async function ladeKnoten(campaignId: string, id: string, kind: EntityKind): Promise<Offen> {
  switch (kind) {
    case "Person":
      return { art: "person", person: await entitiesApi.getPerson(campaignId, id) };
    case "Ort":
      return { art: "ort", ort: await entitiesApi.getOrt(campaignId, id) };
    case "Event":
      return { art: "event", event: await entitiesApi.getEvent(campaignId, id) };
    case "Fraktion":
      return { art: "fraktion", fraktion: await entitiesApi.getFraktion(campaignId, id) };
    case "Gegenstand":
      return { art: "gegenstand", item: await itemsApi.get(campaignId, id) };
  }
}

export function GraphOeffnen({
  campaignId,
  ziel,
  onSchliessen,
  onFehler,
  onLadend,
}: {
  campaignId: string;
  ziel: GraphZiel;
  onSchliessen: () => void;
  onFehler: (meldung: string) => void;
  onLadend: (laeuft: boolean) => void;
}) {
  const [kontext, setKontext] = useState<Kontext | null>(null);
  const [offen, setOffen] = useState<Offen | null>(null);

  useEffect(() => {
    let tot = false;
    onLadend(true);
    setKontext(null);
    setOffen(null);

    (async () => {
      const geladen = await ladeKontext(campaignId);
      const inhalt =
        ziel.art === "kante"
          ? geladen.verbindungen.find((v) => v.id === ziel.id)
          : await ladeKnoten(campaignId, ziel.id, ziel.kind);
      if (tot) return;
      if (ziel.art === "kante") {
        if (!inhalt) throw new Error("Diese Kante gibt es nicht mehr.");
        setOffen({ art: "kante", verbindung: inhalt as Verbindung });
      } else {
        setOffen(inhalt as Offen);
      }
      setKontext(geladen);
    })()
      .catch((e) => {
        if (tot) return;
        onFehler(e instanceof Error ? e.message : "Öffnen fehlgeschlagen");
      })
      .finally(() => {
        if (!tot) onLadend(false);
      });

    return () => {
      tot = true;
    };
    // ziel ist der Mount-Schlüssel des Aufrufers. Neu laden nur bei Wechsel
    // der Kampagne — ein frischer Rechtsklick hängt eine neue Instanz ein.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, ziel.art, ziel.id]);

  async function nachAenderung() {
    try {
      const geladen = await ladeKontext(campaignId);
      setKontext(geladen);
      if (!offen) return;
      if (offen.art === "kante") {
        const neu = geladen.verbindungen.find((v) => v.id === offen.verbindung.id);
        if (neu) setOffen({ art: "kante", verbindung: neu });
        return;
      }
      if (offen.art === "person") {
        setOffen({ art: "person", person: await entitiesApi.getPerson(campaignId, offen.person.id) });
      } else if (offen.art === "ort") {
        setOffen({ art: "ort", ort: await entitiesApi.getOrt(campaignId, offen.ort.id) });
      } else if (offen.art === "event") {
        setOffen({ art: "event", event: await entitiesApi.getEvent(campaignId, offen.event.id) });
      } else if (offen.art === "fraktion") {
        setOffen({ art: "fraktion", fraktion: await entitiesApi.getFraktion(campaignId, offen.fraktion.id) });
      } else if (offen.art === "gegenstand") {
        setOffen({ art: "gegenstand", item: await itemsApi.get(campaignId, offen.item.id) });
      }
    } catch (e) {
      onFehler(e instanceof Error ? e.message : "Aktualisieren fehlgeschlagen");
    }
  }

  if (!kontext || !offen) return null;

  const gemeinsam = {
    campaignId,
    verbindungen: kontext.verbindungen,
    namen: kontext.namen,
    pcOptions: kontext.pcOptions,
    onSchliessen,
    onGeaendert: () => {
      void nachAenderung();
    },
  };

  if (offen.art === "person" && offen.person.personType === "PC") {
    return (
      <PCDetail
        {...gemeinsam}
        person={offen.person}
        onLokalAktualisiert={(felder) =>
          setOffen({ art: "person", person: { ...offen.person, ...felder } })
        }
      />
    );
  }
  if (offen.art === "person") {
    return (
      <NPCDetail
        {...gemeinsam}
        person={offen.person}
        onLokalAktualisiert={(felder) =>
          setOffen({ art: "person", person: { ...offen.person, ...felder } })
        }
      />
    );
  }
  if (offen.art === "ort") {
    return (
      <OrtDetail
        {...gemeinsam}
        ort={offen.ort}
        onLokalAktualisiert={(felder) => setOffen({ art: "ort", ort: { ...offen.ort, ...felder } })}
      />
    );
  }
  if (offen.art === "event") {
    return (
      <EventDetail
        {...gemeinsam}
        event={offen.event}
        onLokalAktualisiert={(felder) =>
          setOffen({ art: "event", event: { ...offen.event, ...felder } })
        }
      />
    );
  }
  if (offen.art === "fraktion") {
    return (
      <FraktionDetail
        {...gemeinsam}
        fraktion={offen.fraktion}
        onLokalAktualisiert={(felder) =>
          setOffen({ art: "fraktion", fraktion: { ...offen.fraktion, ...felder } })
        }
      />
    );
  }
  if (offen.art === "gegenstand") {
    return (
      <GegenstandRow
        campaignId={campaignId}
        item={offen.item}
        pcOptions={kontext.pcOptions}
        alleOptionen={kontext.alleOptionen}
        nurFenster
        onChanged={() => {
          void nachAenderung();
        }}
        onRemoved={() => {
          void itemsApi.remove(campaignId, offen.item.id).then(onSchliessen, (e) => {
            onFehler(e instanceof Error ? e.message : "Entfernen fehlgeschlagen");
          });
        }}
        onFensterSchliessen={onSchliessen}
      />
    );
  }
  return (
    <VerbindungBearbeiten
      campaignId={campaignId}
      verbindung={offen.verbindung}
      namen={kontext.namen}
      pcOptions={kontext.pcOptions}
      farbe="var(--bereich-graph, var(--neon))"
      onGeaendert={() => {
        void nachAenderung();
      }}
      onSchliessen={onSchliessen}
    />
  );
}
