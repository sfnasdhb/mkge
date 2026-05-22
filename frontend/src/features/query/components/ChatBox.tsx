import React, { useState } from 'react';
import { Send } from 'lucide-react';

interface ChatBoxProps {
  onSend: (query: string) => void;
  isLoading: boolean;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ onSend, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-600 p-2 text-slate-800 dark:text-slate-100">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          placeholder="Hỏi câu hỏi về y khoa..."
          className="flex-1 px-4 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-800 dark:placeholder:text-slate-300 text-slate-800 dark:text-slate-100 transition-colors"
          disabled={isLoading}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="px-6 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <div className="flex items-center gap-2">
              <span>Hỏi</span>
              <Send size={18} />
            </div>
          )}
        </button>
      </form>
    </div>
  );
};
