import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadDocument, getDocuments, getDocument, deleteDocument } from "./api";

export const useDocuments = () => {
  return useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const isAnyProcessing = items.some(
        (doc) => doc.status !== "done" && doc.status !== "failed"
      );
      return isAnyProcessing ? 3000 : false;
    },
  });
};

export const useDocumentStatus = (id: string, initialStatus?: string) => {
  return useQuery({
    queryKey: ["documents", id],
    queryFn: () => getDocument(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status ?? initialStatus;
      if (status === "done" || status === "failed") {
        return false;
      }
      return 3000;
    },
  });
};

export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
};
