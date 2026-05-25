import React, { useState } from "react";
import { Trash2, Shield, User as UserIcon, Power, PowerOff, AlertTriangle } from "lucide-react";
import type { User } from "@/shared/types";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";

interface UsersTableProps {
  users: User[];
  isLoading: boolean;
  onUpdateRole: (userId: string, role: string) => void;
  onToggleActive: (userId: string, is_active: boolean) => void;
  onDeleteUser: (userId: string) => void;
}

export const UsersTable: React.FC<UsersTableProps> = ({
  users,
  isLoading,
  onUpdateRole,
  onToggleActive,
  onDeleteUser,
}) => {
  const [deleteUserId, setDeleteUserId] = useState<string | null>(null);

  const handleDeleteConfirm = () => {
    if (deleteUserId) {
      onDeleteUser(deleteUserId);
      setDeleteUserId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="h-10 w-full animate-pulse rounded bg-muted/40" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 w-full animate-pulse rounded bg-muted/20" />
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <th className="p-4">Họ và Tên</th>
              <th className="p-4">Email</th>
              <th className="p-4">Vai Trò</th>
              <th className="p-4">Trạng Thái</th>
              <th className="p-4">Ngày Tạo</th>
              <th className="p-4 text-right">Thao Tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {users.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  Không tìm thấy người dùng nào.
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id} className="transition-colors hover:bg-muted/10">
                  <td className="p-4 font-medium">{user.full_name}</td>
                  <td className="p-4 text-muted-foreground">{user.email}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <select
                        value={user.role}
                        onChange={(e) => onUpdateRole(user.id, e.target.value)}
                        className="rounded-md border border-input bg-background px-2 py-1 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-ring"
                      >
                        <option value="researcher">Researcher</option>
                        <option value="admin">Admin</option>
                      </select>
                      {user.role === "admin" ? (
                        <Shield className="h-4 w-4 text-indigo-500" />
                      ) : (
                        <UserIcon className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    {user.is_active ? (
                      <Badge variant="default" className="bg-emerald-500/15 text-emerald-600 hover:bg-emerald-500/25 border-emerald-500/20">
                        Hoạt động
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="bg-muted text-muted-foreground">
                        Đã khóa
                      </Badge>
                    )}
                  </td>
                  <td className="p-4 text-muted-foreground">
                    {new Date(user.created_at).toLocaleDateString("vi-VN", {
                      year: "numeric",
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => onToggleActive(user.id, !user.is_active)}
                        title={user.is_active ? "Khóa người dùng" : "Mở khóa người dùng"}
                      >
                        {user.is_active ? (
                          <PowerOff className="h-4 w-4 text-amber-500" />
                        ) : (
                          <Power className="h-4 w-4 text-emerald-500" />
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:bg-destructive/10"
                        onClick={() => setDeleteUserId(user.id)}
                        title="Xóa người dùng"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteUserId} onOpenChange={(open) => !open && setDeleteUserId(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Xóa người dùng vĩnh viễn?
            </DialogTitle>
            <DialogDescription className="space-y-2 pt-2">
              <p>
                Hành động này <strong>không thể hoàn tác</strong>. Bạn có chắc chắn muốn xóa người dùng này?
              </p>
              <div className="rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
                <strong>Chú ý:</strong> Toàn bộ tài liệu đã tải lên, đồ thị y khoa (Neo4j), chỉ mục vector (Qdrant), lịch sử câu hỏi của người dùng này sẽ bị <strong>xóa hoàn toàn (Cascade Cleanup)</strong>.
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 gap-2 sm:justify-end">
            <Button variant="outline" onClick={() => setDeleteUserId(null)}>
              Hủy
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              Xác Nhận Xóa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
