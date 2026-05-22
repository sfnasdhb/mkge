import { useState } from 'react';
import { PageHeader } from "@/shared/components/PageHeader";
import { ChatBox } from '../features/query/components/ChatBox';
import { AnswerCard } from '../features/query/components/AnswerCard';
import { CitationList } from '../features/query/components/CitationList';
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
    // safety timeout: reset loading after 20s in case the request hangs
    const timeoutId = setTimeout(() => {
      setIsLoading(false);
      toast.error('Yêu cầu trả lời quá lâu, vui lòng thử lại.');
    }, 20000);
    try {
      const result = await queryService.askQuestion(query);
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
        <div className="bg-card rounded-xl border p-6 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
          <AnswerCard 
            question={currentQuery} 
            answer={response?.answer || ''} 
          />
          {response && <CitationList citations={response.citations} />}
        </div>
      )}
    </div>
  );
};
