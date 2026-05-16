import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion } from "framer-motion";
import { CloudUpload, FileText, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/shared/components/ui/button";
import { Progress } from "@/shared/components/ui/progress";
import { cn, formatBytes } from "@/shared/lib/utils";

interface PendingFile {
  id: string;
  file: File;
  progress: number;
}

interface Props {
  onUploaded?: (file: File) => void;
}

export function UploadZone({ onUploaded }: Props) {
  const [files, setFiles] = useState<PendingFile[]>([]);

  const onDrop = useCallback((accepted: File[]) => {
    const next = accepted.map((file) => ({
      id: crypto.randomUUID(),
      file,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...next]);

    next.forEach((pending) => {
      const interval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) => {
            if (f.id !== pending.id) return f;
            const nextProgress = Math.min(100, f.progress + Math.random() * 18);
            if (nextProgress >= 100) {
              clearInterval(interval);
              setTimeout(() => {
                setFiles((p) => p.filter((x) => x.id !== pending.id));
                toast.success(`${pending.file.name} đã được đưa vào hàng đợi xử lý`);
                onUploaded?.(pending.file);
              }, 400);
            }
            return { ...f, progress: nextProgress };
          })
        );
      }, 300);
    });
  }, [onUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 50 * 1024 * 1024,
    onDropRejected: (rejected) => {
      const reason = rejected[0]?.errors[0]?.message ?? "File không hợp lệ";
      toast.error(reason);
    },
  });

  return (
    <div className="space-y-4">
      <motion.div
        {...getRootProps()}
        whileHover={{ scale: 1.005 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        className={cn(
          "relative cursor-pointer overflow-hidden rounded-xl border-2 border-dashed transition-colors",
          "flex flex-col items-center justify-center gap-4 px-8 py-16 text-center",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border bg-card/40 hover:border-primary/50 hover:bg-card/60"
        )}
      >
        <input {...getInputProps()} />
        <div className="gradient-radial pointer-events-none absolute inset-0 opacity-50" />
        <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary ring-1 ring-primary/20">
          <CloudUpload className="h-6 w-6" />
        </div>
        <div className="relative space-y-1">
          <p className="text-md font-semibold text-foreground">
            {isDragActive ? "Thả file để bắt đầu xử lý" : "Tải lên tài liệu PDF y khoa"}
          </p>
          <p className="text-sm text-muted-foreground">
            Kéo thả file vào đây hoặc <span className="font-medium text-primary">chọn file</span>.
            Tối đa 50MB mỗi file.
          </p>
        </div>
        <div className="relative flex items-center gap-2 text-xs text-muted-foreground">
          <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px]">
            PDF
          </kbd>
          <span>·</span>
          <span>Báo cáo nghiên cứu, hướng dẫn điều trị, case study</span>
        </div>
      </motion.div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f) => (
            <PendingFileRow
              key={f.id}
              file={f}
              onCancel={() => setFiles((prev) => prev.filter((x) => x.id !== f.id))}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PendingFileRow({ file, onCancel }: { file: PendingFile; onCancel: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-center gap-3 rounded-lg border border-border bg-card/60 px-3 py-2.5"
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
        <FileText className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-3">
          <p className="truncate text-sm font-medium">{file.file.name}</p>
          <p className="shrink-0 text-xs text-muted-foreground">{formatBytes(file.file.size)}</p>
        </div>
        <div className="mt-1.5 flex items-center gap-2">
          <Progress value={file.progress} className="h-1" />
          <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
            {Math.round(file.progress)}%
          </span>
        </div>
      </div>
      <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onCancel}>
        <X className="h-3.5 w-3.5" />
      </Button>
    </motion.div>
  );
}
