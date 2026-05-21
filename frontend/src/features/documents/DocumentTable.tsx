import { motion } from "framer-motion";
import { FileText, MoreHorizontal, Network, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Progress } from "@/shared/components/ui/progress";
import { formatBytes, formatRelativeTime } from "@/shared/lib/utils";
import type { Document } from "@/shared/types";
import { StatusBadge } from "./StatusBadge";

const PROGRESS_BY_STATUS: Record<string, number> = {
  queued: 5,
  parsing: 30,
  extracting: 60,
  verifying: 85,
  done: 100,
  failed: 0,
};

interface Props {
  documents: Document[];
  onDelete?: (id: string) => void;
}

export function DocumentTable({ documents, onDelete }: Props) {
  const navigate = useNavigate();
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card/40">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40 text-xs uppercase tracking-wider text-muted-foreground">
              <th className="px-4 py-3 text-left font-medium">Tài liệu</th>
              <th className="px-4 py-3 text-left font-medium">Trạng thái</th>
              <th className="px-4 py-3 text-left font-medium">Entity</th>
              <th className="px-4 py-3 text-left font-medium">Quan hệ</th>
              <th className="px-4 py-3 text-left font-medium">Tải lên</th>
              <th className="w-12 px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {documents.map((doc, i) => (
              <motion.tr
                key={doc.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03, duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="group border-b border-border/60 last:border-0 transition-colors hover:bg-accent/30"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-foreground">{doc.filename}</p>
                      <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                        {formatBytes(doc.file_size)}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="space-y-1.5">
                    <StatusBadge status={doc.status} />
                    {["parsing", "extracting", "verifying"].includes(doc.status) && (
                      <Progress
                        value={PROGRESS_BY_STATUS[doc.status]}
                        className="h-0.5 w-24"
                      />
                    )}
                    {doc.status === "failed" && doc.error_message && (
                      <p className="max-w-xs truncate text-[11px] text-destructive/80">
                        {doc.error_message}
                      </p>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 font-mono text-xs tabular-nums text-foreground/80">
                  {doc.entity_count}
                </td>
                <td className="px-4 py-3 font-mono text-xs tabular-nums text-foreground/80">
                  {doc.relation_count}
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  {formatRelativeTime(doc.created_at)}
                </td>
                <td className="px-4 py-3 text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
                        aria-label="Thao tác"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44">
                      <DropdownMenuItem
                        disabled={doc.status !== "done"}
                        onClick={() => navigate(`/graph/${doc.id}`)}
                        className="gap-2"
                      >
                        <Network className="h-4 w-4" />
                        Xem đồ thị
                      </DropdownMenuItem>
                      <DropdownMenuItem disabled={doc.status !== "done"}>
                        Tải xuống
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => onDelete?.(doc.id)}
                        className="gap-2 text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                        Xóa
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
