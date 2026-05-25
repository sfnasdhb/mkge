import api from "@/shared/lib/axios";
import type { Document } from "@/shared/types";

export const uploadDocument = async (file: File): Promise<{ document_id: string }> => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/documents", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const getDocuments = async (): Promise<{ items: Document[]; total: number }> => {
  const { data } = await api.get("/documents");
  return data;
};

export const getDocument = async (id: string): Promise<Document> => {
  const { data } = await api.get(`/documents/${id}`);
  return data;
};

export const deleteDocument = async (id: string): Promise<void> => {
  await api.delete(`/documents/${id}`);
};
