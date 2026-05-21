import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Network } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";
import { GraphViewer } from "@/features/graph/GraphViewer";
import { useDocumentGraph } from "@/features/graph/hooks";
import { useDocuments } from "@/features/documents/hooks";

export default function GraphPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();

  const { data: graph, isLoading, isError, error } = useDocumentGraph(documentId);
  const { data: docList } = useDocuments();

  if (!documentId) {
    const docs = docList?.items ?? [];
    const ready = docs.filter((d) => d.status === "done");
    return (
      <div className="space-y-6">
        <PageHeader
          title="Đồ thị tri thức"
          description="Chọn tài liệu để xem đồ thị thực thể và quan hệ đã trích xuất."
        />
        {ready.length === 0 ? (
          <EmptyState
            icon={<Network className="h-6 w-6" />}
            title="Chưa có đồ thị nào"
            description="Tải lên tài liệu và đợi xử lý hoàn tất để xem đồ thị."
            action={
              <Button onClick={() => navigate("/documents")}>Đến trang Tài liệu</Button>
            }
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {ready.map((d) => (
              <button
                key={d.id}
                onClick={() => navigate(`/graph/${d.id}`)}
                className="rounded-xl border border-border bg-card/50 p-4 text-left transition hover:border-primary/50 hover:bg-card/70"
              >
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4 text-primary" />
                  <span className="truncate text-sm font-medium">{d.filename}</span>
                </div>
                <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{d.entity_count} entity</span>
                  <span>·</span>
                  <span>{d.relation_count} quan hệ</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      <PageHeader
        title={graph?.filename ?? "Đồ thị tri thức"}
        description={
          graph
            ? `${graph.nodes.length} thực thể · ${graph.edges.length} quan hệ`
            : "Đang tải đồ thị..."
        }
        actions={
          <div className="flex items-center gap-2">
            {graph && <Badge variant="outline">{graph.status}</Badge>}
            <Button variant="ghost" size="sm" onClick={() => navigate("/documents")}>
              <ArrowLeft className="mr-1 h-4 w-4" />
              Quay lại
            </Button>
          </div>
        }
      />

      <div className="flex-1 min-h-0">
        {isLoading ? (
          <div className="flex h-full items-center justify-center rounded-xl border border-border bg-card/40">
            <p className="text-sm text-muted-foreground">Đang tải đồ thị...</p>
          </div>
        ) : isError ? (
          <div className="flex h-full items-center justify-center rounded-xl border border-border bg-card/40">
            <p className="text-sm text-destructive">
              {(error as Error)?.message ?? "Không tải được đồ thị"}
            </p>
          </div>
        ) : !graph || graph.nodes.length === 0 ? (
          <EmptyState
            icon={<Network className="h-6 w-6" />}
            title="Đồ thị rỗng"
            description="Tài liệu này không trích xuất được thực thể nào. Có thể nội dung không phải y khoa hoặc pipeline gặp lỗi."
          />
        ) : (
          <GraphViewer graph={graph} />
        )}
      </div>
    </div>
  );
}
