import { api } from "../api/client";
import type { EntityKind, Sichtbarkeit } from "../entities/api";

export interface GraphNode {
  data: {
    id: string;
    kind: EntityKind;
    label: string;
    sichtbarkeit: Sichtbarkeit;
  };
}

export interface GraphEdge {
  data: {
    id: string;
    source: string;
    target: string;
    typ: string;
    sichtbarkeit: Sichtbarkeit;
  };
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function getGraph(campaignId: string, focus?: string, depth = 2) {
  const params = new URLSearchParams();
  if (focus) {
    params.set("focus", focus);
    params.set("depth", String(depth));
  }
  const qs = params.toString();
  return api.get<GraphData>(`/api/campaigns/${campaignId}/graph${qs ? `?${qs}` : ""}`);
}
