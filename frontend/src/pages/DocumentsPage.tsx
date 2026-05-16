import { useState } from "react";
import { Plus, Search, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { PageHeader } from "@/shared/components/PageHeader";
import { EmptyState } from "@/shared/components/EmptyState";
import { DocumentTable } from "@/features/documents/DocumentTable";
import { DocumentTableSkeleton } from "@/features/documents/DocumentSkeleton";
import { UploadZone } from "@/features/documents/UploadZone";
import { MOCK_DOCUMENTS } from "@/features/documents/mock";
import type { Document } from "@/shared/types";

type LoadingState = "loading" | "empty" | "data";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>(MOCK_DOCUMENTS);
  const [query, setQuery] = useState("");
  const [state] = useState<LoadingState>("data");
  const [uploadOpen, setUploadOpen] = useState(false);

  const filtered = documents.filter((d) =>
    d.filename.toLowerCase().includes(query.toLowerCase())
  );

  function handleDelete(id: string) {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    toast.success("Đã xóa tài liệu", {
      action: {
        label: "Hoàn tác",
        onClick: () => setDocuments(MOCK_DOCUMENTS),
      },
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tài liệu"
        description="Quản lý tài liệu y khoa và theo dõi trạng thái trích xuất tri thức."
        actions={
          <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
            <DialogTrigger asChild>
              <Button size="lg" className="gap-2">
                <Plus className="h-4 w-4" />
                Tải lên
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Tải tài liệu y khoa</DialogTitle>
                <DialogDescription>
                  Hỗ trợ định dạng PDF. Pipeline sẽ tự động trích xuất Thuốc / Bệnh / Triệu chứng.
                </DialogDescription>
              </DialogHeader>
              <UploadZone />
            </DialogContent>
          </Dialog>
        }
      />

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Tìm theo tên file..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-mono tabular-nums">{filtered.length}</span>
          <span>tài liệu</span>
        </div>
      </div>

      {state === "loading" ? (
        <DocumentTableSkeleton />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={<Upload className="h-6 w-6" />}
          title="Chưa có tài liệu nào"
          description="Tải lên PDF y khoa đầu tiên để bắt đầu xây dựng đồ thị tri thức."
          action={
            <Button onClick={() => setUploadOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Tải lên tài liệu đầu tiên
            </Button>
          }
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Search className="h-6 w-6" />}
          title="Không tìm thấy tài liệu"
          description={`Không có tài liệu nào khớp với "${query}".`}
        />
      ) : (
        <DocumentTable documents={filtered} onDelete={handleDelete} />
      )}
    </div>
  );
}
