import React from "react";
import type { AuditLog } from "../api";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";

interface AuditLogTableProps {
  logs: AuditLog[];
  total: number;
  offset: number;
  limit: number;
  isLoading: boolean;
  onPageChange: (newOffset: number) => void;
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({
  logs,
  total,
  offset,
  limit,
  isLoading,
  onPageChange,
}) => {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const getActionBadge = (action: string) => {
    switch (action) {
      case "USER_REGISTER":
        return (
          <Badge variant="default" className="bg-indigo-500/10 text-indigo-600 border-indigo-500/20">
            REGISTER
          </Badge>
        );
      case "USER_LOGIN":
        return (
          <Badge variant="default" className="bg-sky-500/10 text-sky-600 border-sky-500/20">
            LOGIN
          </Badge>
        );
      case "UPLOAD_DOCUMENT":
        return (
          <Badge variant="default" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
            UPLOAD
          </Badge>
        );
      case "DELETE_DOCUMENT":
        return (
          <Badge variant="default" className="bg-amber-500/10 text-amber-600 border-amber-500/20">
            DELETE
          </Badge>
        );
      case "QUERY_GRAPHRAG":
        return (
          <Badge variant="default" className="bg-purple-500/10 text-purple-600 border-purple-500/20">
            QUERY
          </Badge>
        );
      case "ADMIN_UPDATE_USER":
        return (
          <Badge variant="default" className="bg-orange-500/10 text-orange-600 border-orange-500/20">
            ADMIN_UPDATE
          </Badge>
        );
      case "ADMIN_DELETE_USER":
        return (
          <Badge variant="destructive" className="bg-rose-500/10 text-rose-600 border-rose-500/20">
            ADMIN_DELETE
          </Badge>
        );
      default:
        return <Badge variant="secondary">{action}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-14 w-full animate-pulse rounded bg-muted/20" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <th className="p-4">Hành Động</th>
                <th className="p-4">Người Thực Hiện</th>
                <th className="p-4">Chi Tiết</th>
                <th className="p-4">IP Address</th>
                <th className="p-4">Thời Gian</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-mono text-xs">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground font-sans text-sm">
                    Chưa có nhật ký hoạt động nào.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="transition-colors hover:bg-muted/10">
                    <td className="p-4">{getActionBadge(log.action)}</td>
                    <td className="p-4 font-sans text-sm text-muted-foreground">
                      {log.user_id ? (
                        <span className="truncate max-w-[120px] block" title={log.user_id}>
                          {log.user_id}
                        </span>
                      ) : (
                        <span className="italic text-muted-foreground/60">Hệ thống</span>
                      )}
                    </td>
                    <td className="p-4 font-sans text-sm break-all max-w-[400px]">
                      {log.details || <span className="text-muted-foreground/40">-</span>}
                    </td>
                    <td className="p-4 text-muted-foreground">{log.ip_address || "N/A"}</td>
                    <td className="p-4 text-muted-foreground font-sans text-sm">
                      {new Date(log.created_at).toLocaleString("vi-VN", {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between px-2">
        <span className="text-sm text-muted-foreground">
          Hiển thị {logs.length} / {total} nhật ký (Trang {currentPage} / {totalPages})
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => onPageChange(offset - limit)}
          >
            Trang Trước
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(offset + limit)}
          >
            Trang Sau
          </Button>
        </div>
      </div>
    </div>
  );
};
