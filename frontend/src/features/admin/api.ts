import api from "@/shared/lib/axios";
import type { User } from "@/shared/types";

export interface AdminStats {
  total_users: number;
  total_documents: number;
  total_queries: number;
  total_entities: number;
  total_relationships: number;
  document_stats: Record<string, number>;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  details: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogsResponse {
  total: number;
  items: AuditLog[];
}

export const adminApi = {
  getUsers: async (offset = 0, limit = 50): Promise<{ items: User[] }> => {
    const { data } = await api.get<{ items: User[] }>("/admin/users", { params: { offset, limit } });
    return data;
  },

  getStats: async (): Promise<AdminStats> => {
    const { data } = await api.get<AdminStats>("/admin/stats");
    return data;
  },

  updateUser: async (userId: string, updateData: { role?: string; is_active?: boolean }): Promise<User> => {
    const { data } = await api.patch<User>(`/admin/users/${userId}`, updateData);
    return data;
  },

  deleteUser: async (userId: string): Promise<void> => {
    await api.delete(`/admin/users/${userId}`);
  },

  getAuditLogs: async (offset = 0, limit = 50): Promise<AuditLogsResponse> => {
    const { data } = await api.get<AuditLogsResponse>("/admin/audit", { params: { offset, limit } });
    return data;
  },
};
