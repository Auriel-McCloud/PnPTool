import { useCallback, useEffect, useState } from "react";
import { type Gegenstand, type GegenstandMitBesitzer, itemsApi } from "../items/api";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { partyApi, type ReparaturFreigabeEintrag } from "../party/api";
import { verhandlungApi } from "../verhandlung/api";
import { ReparaturUebersichtSpieler, type ReparaturGruppe } from "./ReparaturUebersichtSpieler";
import { AugmentUebersichtSpieler } from "./AugmentUebersichtSpieler";

/**
 * Werkbank für Spieler (29.10.2026, Mark: "das war alles für die Spieler
 * gedacht!" — Korrektur, beide Unter-Features waren `require_campaign_gm`).
 * Gegenstück zu `werkbank/WerkbankUebersicht.tsx` (SL-Ansicht, campaignweit):
 * zwei Reiter Reparatur/Augments, aber nur der eigene Besitz — eigene
 * Person ODER eigene gebundene Drohne/eigenes Fahrzeug (`riggerId` statt
 * der fragilen `eigeneDrohnenIds` aus `SpielerAnsicht.tsx`, die nur gefüllt
 * ist, wenn der Kampf-Reiter schon mal offen war — hier deshalb ein
 * eigener, unabhängiger Drohnen-Fetch).
 *
 * **Party-Reparatur-Freigabe (05.11.2026):** Mark, über mehrere Nachrichten
 * entwickelt: ein Spieler (Fixer) soll die reparierbaren Sachen eines
 * Party-Mitglieds behandeln können "als wären es seine eigenen" — aber nur
 * nach Zustimmung ("er kann auf die namen klicken, dann wird der andere
 * spieler gefragt ob er zuässt"), mit eigenem Material ("der Fixer soll
 * sein eigenes Material mitbringen dürfen"), und die Freigabe "verfällt
 * automatisch" bei jeder Party-Änderung (siehe party/repository.py). Der
 * Reparatur-Reiter zeigt deshalb zusätzlich zur eigenen Ausrüstung eine
 * Gruppe pro Person, die dem Fixer Zugriff erteilt hat, plus die
 * Party-Mitgliederliste zum Anfragen/Widerrufen.
 */
export function WerkbankUebersichtSpieler({
  campaignId,
  personId,
  sachen,
  onGeaendert,
}: {
  campaignId: string;
  personId: string;
  sachen: GegenstandMitBesitzer[];
  onGeaendert: () => void;
}) {
  const [tab, setTab] = useState<"reparatur" | "augments">("reparatur");
  const [meineDrohnen, setMeineDrohnen] = useState<DrohnenEintrag[]>([]);
  const [reparaturGruppen, setReparaturGruppen] = useState<ReparaturGruppe[]>([]);
  const [partyMitglieder, setPartyMitglieder] = useState<{ id: string; name: string }[]>([]);
  const [freigeber, setFreigeber] = useState<ReparaturFreigabeEintrag[]>([]);
  const [erteilteFreigaben, setErteilteFreigaben] = useState<ReparaturFreigabeEintrag[]>([]);
  const [anfrageAn, setAnfrageAn] = useState<Set<string>>(new Set());

  useEffect(() => {
    drohnenApi
      .liste(campaignId)
      .then((liste) => setMeineDrohnen(liste.filter((d) => d.riggerId === personId)))
      .catch(() => setMeineDrohnen([]));
  }, [campaignId, personId]);

  const ladeReparaturDaten = useCallback(() => {
    Promise.all([
      partyApi.liste(campaignId),
      partyApi.reparaturFreigabenFuerMich(campaignId),
      partyApi.reparaturFreigabenVonMir(campaignId),
    ])
      .then(async ([parteien, freigeberListe, erteilteListe]) => {
        setFreigeber(freigeberListe);
        setErteilteFreigaben(erteilteListe);
        const eigeneParty = parteien.find((p) => p.mitglieder.some((m) => m.id === personId));
        const mitglieder = (eigeneParty?.mitglieder ?? []).filter((m) => m.id !== personId);
        setPartyMitglieder(mitglieder);

        const eigeneItems = await itemsApi.reparierbareItems(campaignId, personId);
        const gruppen: ReparaturGruppe[] = [{ label: "Deine Ausrüstung", personId, items: eigeneItems }];
        for (const f of freigeberListe) {
          const items = await itemsApi.reparierbareItems(campaignId, f.id).catch(() => [] as Gegenstand[]);
          gruppen.push({ label: `${f.name}s Ausrüstung`, personId: f.id, items });
        }
        setReparaturGruppen(gruppen);
      })
      .catch(() => {
        setReparaturGruppen([{ label: "Deine Ausrüstung", personId, items: [] }]);
      });
  }, [campaignId, personId]);

  useEffect(() => {
    ladeReparaturDaten();
  }, [ladeReparaturDaten]);

  async function freigabeAnfragen(zielPersonId: string) {
    setAnfrageAn((alt) => new Set(alt).add(zielPersonId));
    try {
      await verhandlungApi.reparaturFreigabeAnfragen(campaignId, zielPersonId);
    } catch {
      setAnfrageAn((alt) => {
        const neu = new Set(alt);
        neu.delete(zielPersonId);
        return neu;
      });
    }
  }

  async function freigabeWiderrufen(fixerPersonId: string) {
    await partyApi.reparaturFreigabeEntziehen(campaignId, fixerPersonId);
    ladeReparaturDaten();
  }

  const eigenerKreis = new Set([personId, ...meineDrohnen.map((d) => d.id)]);
  const meine = sachen.filter((g) => !g.weggeworfen && eigenerKreis.has(g.ownerId ?? ""));
  const meineDrohnenKaputt = meineDrohnen; // Gesundheitsschaden wird im Popup selbst geprüft/angezeigt

  // Wer mir noch keinen Zugriff erteilt hat — für die "Anfragen"-Liste.
  const freigeberIds = new Set(freigeber.map((f) => f.id));
  const anfragbar = partyMitglieder.filter((m) => !freigeberIds.has(m.id));

  function onGeaendertUndNeuLaden() {
    onGeaendert();
    ladeReparaturDaten();
  }

  return (
    <div className="gg-seite">
      <div className="gg-kopf">
        <button type="button" aria-pressed={tab === "reparatur"} onClick={() => setTab("reparatur")}>
          🔧 Reparatur
        </button>
        <button type="button" aria-pressed={tab === "augments"} onClick={() => setTab("augments")}>
          🔩 Upgraden
        </button>
      </div>
      {tab === "reparatur" && (
        <ReparaturUebersichtSpieler
          campaignId={campaignId}
          reparaturgruppen={reparaturGruppen}
          drohnen={meineDrohnenKaputt}
          onGeaendert={onGeaendertUndNeuLaden}
          partyAnfragbar={anfragbar}
          anfrageLaeuft={anfrageAn}
          onFreigabeAnfragen={freigabeAnfragen}
          erteilteFreigaben={erteilteFreigaben}
          onFreigabeWiderrufen={freigabeWiderrufen}
        />
      )}
      {tab === "augments" && (
        <AugmentUebersichtSpieler campaignId={campaignId} meine={meine} meineDrohnen={meineDrohnen} onGeaendert={onGeaendert} />
      )}
    </div>
  );
}
