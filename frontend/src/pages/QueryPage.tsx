import { useState } from 'react';
import { PageHeader } from "@/shared/components/PageHeader";
import { ChatBox } from '../features/query/components/ChatBox';
import { AnswerCard } from '../features/query/components/AnswerCard';
import { CitationList } from '../features/query/components/CitationList';
import { GraphViewer } from '../features/graph/GraphViewer';
import { queryService, type QueryResponse } from '../features/query/QueryService';
import { toast } from 'sonner';

export const QueryPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [response, setResponse] = useState<QueryResponse | null>(null);

  const handleSend = async (query: string) => {
    setIsLoading(true);
    setCurrentQuery(query);
    setResponse(null);
    // safety timeout: reset loading after 60s in case the request hangs
    const timeoutId = setTimeout(() => {
      setIsLoading(false);
      toast.error('Yêu cầu trả lời quá lâu, vui lòng thử lại.');
    }, 60000);

    let top_k = 20;
    let temperature = 0.2;
    try {
      const savedTopK = localStorage.getItem("mkge_rag_top_k");
      const savedTemp = localStorage.getItem("mkge_rag_temperature");
      if (savedTopK) top_k = parseInt(savedTopK, 10);
      if (savedTemp) temperature = parseFloat(savedTemp);
    } catch (e) {
      console.warn("Failed to read RAG parameters from local storage", e);
    }

    try {
      const result = await queryService.askQuestion(query, { top_k, temperature });
      setResponse(result);
    } catch (error) {
      toast.error("Đã xảy ra lỗi khi truy vấn thông tin.");
      console.error(error);
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hỏi đáp AI"
        description="Tra cứu thông tin y khoa từ Graph Database và Vector Database của bạn."
      />

      <div className="bg-card rounded-xl border p-4 shadow-sm">
        <ChatBox onSend={handleSend} isLoading={isLoading} />
      </div>

      {(isLoading || response) && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 bg-card rounded-xl border p-6 shadow-sm">
            <AnswerCard 
              question={currentQuery} 
              answer={response?.answer || ''} 
            />
            {response && <CitationList citations={response.citations} />}
          </div>
          
          {response?.subgraph && response.subgraph.nodes.length > 0 && (
            <div className="bg-card rounded-xl border p-6 shadow-sm flex flex-col h-[500px] lg:h-auto">
              <h3 className="text-sm font-semibold mb-3">Đồ thị liên quan</h3>
              <div className="flex-1 relative min-h-[300px]">
                <GraphViewer graph={{
                  nodes: response.subgraph.nodes,
                  edges: response.subgraph.edges,
                  document_id: "",
                  filename: "",
                  status: "done"
                } as any} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
