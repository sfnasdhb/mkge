import api from '@/shared/lib/axios';

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  confidence: number;
  evidence: string;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  description?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  page: number;
  text: string;
  score: number;
}

export interface QueryResponse {
  answer: string;
  subgraph: GraphData;
  citations: Citation[];
}

export const queryService = {
  async askQuestion(
    question: string,
    options?: { top_k?: number; temperature?: number }
  ): Promise<QueryResponse> {
    const { data } = await api.post<QueryResponse>('/query', {
      question,
      top_k: options?.top_k,
      temperature: options?.temperature,
    });
    return data;
  },

  async getHistory() {
    const { data } = await api.get('/query/history');
    return data;
  }
};
