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
    return list;
  }

  useEffect(() => {
    refresh()
      .then((list) => {
        // Fallback: gespeicherte Kampagne existiert nicht (mehr) → erste nehmen.
        if (!list.some((c) => c.id === aktiveId)) {
          setAktiveId(list[0]?.id ?? null);
        }
      })
      .finally(() => setLoading(false));
    // bewusst nur beim Aufbau — aktiveId hier nicht als Abhängigkeit,
    // sonst würde der Effekt bei jedem Wechsel neu feuern.
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
