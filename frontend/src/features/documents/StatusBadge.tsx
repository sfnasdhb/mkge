import { Check, Loader2, X } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { DocumentStatus } from "@/shared/types";

const CONFIG: Record<
  DocumentStatus,
  { label: string; dotClass: string; textClass: string; icon?: typeof Check; animated?: boolean }
> = {
  queued: {
    label: "Đang chờ",
    dotClass: "bg-muted-foreground/60",
    textClass: "text-muted-foreground",
    animated: true,
  },
  parsing: {
    label: "Đang đọc",
    dotClass: "bg-primary",
    textClass: "text-primary",
    animated: true,
  },
  extracting: {
    label: "Trích xuất",
    dotClass: "bg-primary",
    textClass: "text-primary",
    animated: true,
  },
  verifying: {
    label: "Kiểm chứng",
    dotClass: "bg-primary",
    textClass: "text-primary",
    animated: true,
  },
  done: {
    label: "Hoàn tất",
    dotClass: "bg-success",
    textClass: "text-success",
    icon: Check,
  },
  failed: {
    label: "Thất bại",
    dotClass: "bg-destructive",
    textClass: "text-destructive",
    icon: X,
  },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const cfg = CONFIG[status];
  const isProcessing = ["parsing", "extracting", "verifying"].includes(status);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-card px-2 py-0.5 text-xs font-medium",
        cfg.textClass
      )}
    >
      {isProcessing ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : cfg.icon ? (
        <cfg.icon className="h-3 w-3" />
      ) : (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            cfg.dotClass,
            cfg.animated && "animate-dot-pulse"
          )}
        />
      )}
      {cfg.label}
    </span>
  );
}
