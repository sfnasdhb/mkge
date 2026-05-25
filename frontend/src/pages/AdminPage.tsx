import React, { useState } from "react";
import { Lock } from "lucide-react";
import { useAuthStore } from "@/features/auth/store";
import { useAdminUsers, useAdminStats, useUpdateUser, useDeleteUser, useAuditLogs } from "@/features/admin/hooks";
import { StatsCards } from "@/features/admin/components/StatsCards";
import { UsersTable } from "@/features/admin/components/UsersTable";
import { AuditLogTable } from "@/features/admin/components/AuditLogTable";
import { PageHeader } from "@/shared/components/PageHeader";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/shared/components/ui/tabs";

export const AdminPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);

  // Pagination states
  const userOffset = 0;
  const userLimit = 50;

  const [auditOffset, setAuditOffset] = useState(0);
  const auditLimit = 50;

  // React Query hooks
  const { data: stats, isLoading: statsLoading } = useAdminStats();
  const { data: usersData, isLoading: usersLoading } = useAdminUsers(userOffset, userLimit);
  const { data: auditData, isLoading: auditLoading } = useAuditLogs(auditOffset, auditLimit);

  // Mutations
  const updateUserMutation = useUpdateUser();
  const deleteUserMutation = useDeleteUser();

  // Role Guard check
  if (!user || user.role !== "admin") {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center space-y-4 text-center">
        <div className="rounded-full bg-destructive/10 p-4 text-destructive">
          <Lock className="h-10 w-10 animate-bounce" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Bạn không có quyền truy cập</h2>
        <p className="text-muted-foreground max-w-md">
          Trang này chỉ dành cho quản trị viên hệ thống. Vui lòng liên hệ quản trị viên nếu bạn tin đây là một lỗi.
        </p>
      </div>
    );
  }

  const handleUpdateRole = (userId: string, role: string) => {
    updateUserMutation.mutate({ userId, role });
  };

  const handleToggleActive = (userId: string, is_active: boolean) => {
    updateUserMutation.mutate({ userId, is_active });
  };

  const handleDeleteUser = (userId: string) => {
    deleteUserMutation.mutate(userId);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản Trị Hệ Thống"
        description="Quản lý người dùng, xem thống kê hệ thống và nhật ký hoạt động y khoa."
      />

      {/* Stats Cards Section */}
      <StatsCards stats={stats} isLoading={statsLoading} />

      {/* Tabs for Admin functions */}
      <Tabs defaultValue="users" className="w-full">
        <div className="border-b pb-1">
          <TabsList className="bg-muted/50">
            <TabsTrigger value="users" className="data-[state=active]:bg-background">
              Người Dùng
            </TabsTrigger>
            <TabsTrigger value="audit" className="data-[state=active]:bg-background">
              Nhật Ký Hệ Thống
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="users" className="pt-4">
          <UsersTable
            users={usersData?.items ?? []}
            isLoading={usersLoading}
            onUpdateRole={handleUpdateRole}
            onToggleActive={handleToggleActive}
            onDeleteUser={handleDeleteUser}
          />
        </TabsContent>

        <TabsContent value="audit" className="pt-4">
          <AuditLogTable
            logs={auditData?.items ?? []}
            total={auditData?.total ?? 0}
            offset={auditOffset}
            limit={auditLimit}
            isLoading={auditLoading}
            onPageChange={setAuditOffset}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminPage;
