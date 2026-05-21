import api from "@/shared/lib/axios";
import type { DocumentGraph, GraphOverview } from "@/shared/types";

export const getDocumentGraph = async (documentId: string): Promise<DocumentGraph> => {
  const { data } = await api.get(`/graph/documents/${documentId}`);
  return data;
};

export const getGraphOverview = async (): Promise<GraphOverview> => {
  const { data } = await api.get("/graph/overview");
  return data;
};
