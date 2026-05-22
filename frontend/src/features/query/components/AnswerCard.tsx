import React from 'react';
import { Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface AnswerCardProps {
  question: string;
  answer: string;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ question, answer }) => {
  return (
    <div className="flex flex-col gap-6">
      {/* User Question */}
      <div className="flex gap-4 items-start">
        <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center shrink-0">
          <User size={24} className="text-slate-600 dark:text-slate-300" />
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 shadow-sm w-full">
          <p className="text-slate-800 dark:text-slate-100 font-medium">{question}</p>
        </div>
      </div>

      {/* AI Answer */}
      <div className="flex gap-4 items-start">
        <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-950 flex items-center justify-center shrink-0 border border-indigo-200 dark:border-indigo-800">
          <Bot size={24} className="text-indigo-600 dark:text-indigo-400" />
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-5 shadow-sm w-full prose prose-sm sm:prose-base text-slate-800 dark:text-slate-100 dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {answer || "*Đang suy nghĩ...*"}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};
