import { useQuery } from "@tanstack/react-query";
import { getDocumentGraph, getGraphOverview } from "./api";

export const useDocumentGraph = (documentId: string | undefined) => {
  return useQuery({
    queryKey: ["graph", "document", documentId],
    queryFn: () => getDocumentGraph(documentId!),
    enabled: !!documentId,
  });
};

export const useGraphOverview = () => {
  return useQuery({
    queryKey: ["graph", "overview"],
    queryFn: getGraphOverview,
  });
};
