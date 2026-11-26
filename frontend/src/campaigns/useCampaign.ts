import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

export interface Campaign {
  id: string;
  name: string;
  /** Name des Regelsystems = Spiel ("NeotopiA", "GridMonster"), siehe RPGrid-Startseite. */
  regelsystem?: string;
  regelsystemId?: string;
}

const SPEICHER_SCHLUESSEL = "pnptool:aktiveKampagne";

export function useCampaign() {
  const [campaigns, setCampaigns] = useState<Campaign[] | null>(null);
  const [loading, setLoading] = useState(true);
  // Die aktive Kampagne wird pro Gerät gemerkt, damit ein Neuladen dieselbe
  // Kampagne öffnet statt einfach die erste zu nehmen.
  const [aktiveId, setAktiveId] = useState<string | null>(() =>
    localStorage.getItem(SPEICHER_SCHLUESSEL),
  );

  async function refresh() {
    const list = await api.get<Campaign[]>("/api/campaigns");
    setCampaigns(list);
    // Aktive Kampagne konsistent halten — als funktionaler Update, damit
    // nicht ein veralteter Closure-Wert (React StrictMode ruft den Effekt
    // zweimal) gegen die Liste geprüft wird. Gespeicherte ID behalten, wenn
    // sie noch existiert, sonst die erste nehmen.
    // Kein localStorage-Schreiben hier drin: der Updater läuft erst beim
    // nächsten Render — nach einem direkt folgenden `waehleKampagne(neu)`
    // überschrieb er sonst die neue ID mit der alten (26.11.2026, fiel mit
    // der RPGrid-Startseite auf). Das Merken macht der Effekt unten.
    setAktiveId((aktuell) => (list.some((c) => c.id === aktuell) ? aktuell : (list[0]?.id ?? null)));
    return list;
  }

  useEffect(() => {
    refresh()
      .catch(() => {
        // z.B. 401 — campaigns bleibt null, die Login-Weiche übernimmt.
      })
      .finally(() => setLoading(false));
    // bewusst nur beim Aufbau
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (aktiveId) localStorage.setItem(SPEICHER_SCHLUESSEL, aktiveId);
  }, [aktiveId]);

  const waehleKampagne = useCallback((id: string) => {
    setAktiveId(id);
    localStorage.setItem(SPEICHER_SCHLUESSEL, id);
  }, []);

  async function createCampaign(name: string, regelsystem = "NeotopiA") {
    // `ruleset` nimmt Regelsystem-ID oder -Name (campaigns/repository.py).
    const neu = await api.post<Campaign>("/api/campaigns", { name, ruleset: regelsystem });
    await refresh();
    waehleKampagne(neu.id);
    return neu;
  }

  const aktive = campaigns?.find((c) => c.id === aktiveId) ?? null;

  /** Nach einem Kampagnen-Import (siehe EinstellungenFenster): Liste neu
   * laden und direkt zur frisch importierten Kampagne wechseln. */
  const nachImportUebernehmen = useCallback(async (id: string) => {
    await refresh();
    waehleKampagne(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waehleKampagne]);

  return { campaigns, loading, aktive, aktiveId, waehleKampagne, createCampaign, nachImportUebernehmen };
}
