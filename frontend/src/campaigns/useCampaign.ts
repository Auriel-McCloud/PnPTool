import { useEffect, useState } from "react";
import { api } from "../api/client";

export interface Campaign {
  id: string;
  name: string;
}

export function useCampaign() {
  const [campaigns, setCampaigns] = useState<Campaign[] | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const list = await api.get<Campaign[]>("/api/campaigns");
    setCampaigns(list);
    return list;
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  async function createCampaign(name: string) {
    await api.post<Campaign>("/api/campaigns", { name });
    await refresh();
  }

  return { campaigns, loading, createCampaign };
}
