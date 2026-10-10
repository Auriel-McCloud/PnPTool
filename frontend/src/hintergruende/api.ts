import { api } from "../api/client";

export interface Hintergrund {
  id: string;
  campaignId: string;
  name: string;
  kurzbeschreibung: string;
  detailbeschreibung: string;
}

export interface HintergrundEingabe {
  name?: string;
  kurzbeschreibung?: string;
  detailbeschreibung?: string;
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/hintergruende`;
}

export const hintergruendeApi = {
  liste: (cid: string) => api.get<Hintergrund[]>(basis(cid)),
  anlegen: (cid: string, body: HintergrundEingabe & { name: string }) =>
    api.post<Hintergrund>(basis(cid), body),
  aendern: (cid: string, id: string, body: HintergrundEingabe) =>
    api.patch<Hintergrund>(`${basis(cid)}/${id}`, body),
  loeschen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/${id}`),
};
