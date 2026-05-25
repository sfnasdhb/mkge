import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, Clock, Bot, ChevronDown, ChevronUp } from "lucide-react";
import { queryService } from "@/features/query/QueryService";
import { PageHeader } from "@/shared/components/PageHeader";
import { EmptyState } from "@/shared/components/EmptyState";
import { Card } from "@/shared/components/ui/card";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface HistoryItem {
  id: string;
  question: string;
  answer: string | null;
  latency_ms: number | null;
  created_at: string;
}

export const QueryHistoryPage: React.FC = () => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["queryHistory"],
    queryFn: queryService.getHistory,
  });

  const historyItems: HistoryItem[] = data?.items || [];

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lịch Sử Truy Vấn"
        description="Xem lại toàn bộ lịch sử các câu hỏi y khoa GraphRAG đã thực hiện trên hệ thống."
      />

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 w-full animate-pulse rounded-lg bg-muted/20" />
          ))}
        </div>
      ) : historyItems.length === 0 ? (
        <EmptyState
          icon={<MessageSquare className="h-6 w-6" />}
          title="Chưa có câu hỏi nào"
          description="Đặt câu hỏi đầu tiên của bạn ở mục Hỏi Đáp GraphRAG."
        />
      ) : (
        <div className="space-y-4">
          {historyItems.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <Card
                key={item.id}
                className="overflow-hidden border border-border bg-card transition-all duration-200 hover:shadow-sm"
              >
                <div
                  className="flex cursor-pointer items-center justify-between p-4 sm:p-6"
                  onClick={() => toggleExpand(item.id)}
                >
                  <div className="flex flex-1 items-start gap-3">
                    <div className="mt-1 rounded-full bg-indigo-500/10 p-2 text-indigo-500">
                      <MessageSquare className="h-4 w-4" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="font-semibold text-foreground leading-snug">
                        {item.question}
                      </h3>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                        <span>
                          {new Date(item.created_at).toLocaleString("vi-VN", {
                            year: "numeric",
                            month: "2-digit",
                            day: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        {item.latency_ms && (
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{item.latency_ms} ms</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="ml-4 text-muted-foreground">
                    {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                  </div>
                </div>

                {isExpanded && (
                  <div className="border-t bg-muted/10 p-4 sm:p-6">
                    <div className="flex gap-3 items-start">
                      <div className="mt-1 rounded-full bg-indigo-500/10 p-1.5 text-indigo-500 shrink-0">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="prose prose-sm dark:prose-invert max-w-none text-sm text-foreground">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {item.answer || "*Không có câu trả lời.*"}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default QueryHistoryPage;
