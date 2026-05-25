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
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/features/documents/hooks";
import type { Document } from "@/shared/types";

export default function DocumentsPage() {
  const [query, setQuery] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);

  const { data, isLoading } = useDocuments();
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();

  const documents = data?.items || [];
  const filtered = documents.filter((d) =>
    d.filename.toLowerCase().includes(query.toLowerCase())
  );

  async function handleUpload(file: File) {
    try {
      await uploadMutation.mutateAsync(file);
      setUploadOpen(false);
    } catch (error) {
      toast.error("Lỗi khi tải lên tài liệu");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMutation.mutateAsync(id);
      toast.success("Đã xóa tài liệu");
    } catch (error) {
      toast.error("Lỗi khi xóa tài liệu");
    }
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
              <UploadZone onUploaded={handleUpload} />
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

      {isLoading ? (
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
