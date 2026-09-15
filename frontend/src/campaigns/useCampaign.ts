import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

export interface Campaign {
  id: string;
  name: string;
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
    setAktiveId((aktuell) => {
      const id = list.some((c) => c.id === aktuell) ? aktuell : (list[0]?.id ?? null);
      if (id) localStorage.setItem(SPEICHER_SCHLUESSEL, id);
      return id;
    });
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

  const waehleKampagne = useCallback((id: string) => {
    setAktiveId(id);
    localStorage.setItem(SPEICHER_SCHLUESSEL, id);
  }, []);

  async function createCampaign(name: string) {
    const neu = await api.post<Campaign>("/api/campaigns", { name });
    await refresh();
    waehleKampagne(neu.id);
    return neu;
  }

  const aktive = campaigns?.find((c) => c.id === aktiveId) ?? null;

  return { campaigns, loading, aktive, aktiveId, waehleKampagne, createCampaign };
}
