import React from 'react';
import { FileText } from 'lucide-react';
import type { Citation } from '../QueryService';
import { useAuthStore } from '@/features/auth/store';

interface CitationListProps {
  citations: Citation[];
}

export const CitationList: React.FC<CitationListProps> = ({ citations }) => {
  const token = useAuthStore((state) => state.accessToken);
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-8 border-t border-slate-200 dark:border-slate-800 pt-6">
      <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
        <FileText size={20} className="text-indigo-600 dark:text-indigo-400" />
        Nguồn tham chiếu (Citations)
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {citations.map((cite, index) => (
          <div key={cite.chunk_id || index} className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:shadow-md transition-shadow mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50 px-2 py-1 rounded">
                Trích xuất {index + 1}
              </span>
              <span className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 font-medium bg-white dark:bg-slate-900 px-2 py-1 rounded border border-slate-200 dark:border-slate-700">
                <span>Trang {cite.page}</span>
                {cite.doc_id && (
                  <span className="border-l border-slate-200 dark:border-slate-700 pl-2">
                    <a
                      href={`/api/v1/documents/${cite.doc_id}/preview?token=${token || ''}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
                    >
                      Xem tài liệu
                    </a>
                  </span>
                )}
              </span>
            </div>
            <p className="text-sm text-slate-700 dark:text-slate-300 max-h-60 overflow-y-auto pr-1 scrollbar-thin whitespace-pre-wrap italic">
              "{cite.text}"
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
