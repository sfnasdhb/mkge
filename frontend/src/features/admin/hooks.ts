import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "./api";

export const useAdminUsers = (offset = 0, limit = 50) => {
  return useQuery({
    queryKey: ["admin", "users", offset, limit],
    queryFn: () => adminApi.getUsers(offset, limit),
  });
};

export const useAdminStats = () => {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: adminApi.getStats,
    refetchInterval: 30000, // Refresh stats every 30 seconds
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role, is_active }: { userId: string; role?: string; is_active?: boolean }) =>
      adminApi.updateUser(userId, { role, is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
};

export const useAuditLogs = (offset = 0, limit = 50) => {
  return useQuery({
    queryKey: ["admin", "audit", offset, limit],
    queryFn: () => adminApi.getAuditLogs(offset, limit),
  });
};
