export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "researcher" | "viewer";
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user?: User;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    request_id: string;
  };
}

export type DocumentStatus =
  | "queued"
  | "parsing"
  | "extracting"
  | "verifying"
  | "done"
  | "failed";

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  file_size: number;
  status: DocumentStatus;
  error_message?: string;
  entity_count: number;
  relation_count: number;
  created_at: string;
  processed_at?: string;
}

// PROJECT_CONTEXT §4.2 — chỉ 3 entity types, 4 relation types
export type EntityType = "DRUG" | "DISEASE" | "SYMPTOM";

export type RelationType =
  | "TREATS"      // Drug → Disease
  | "CAUSES_SE"   // Drug → Symptom (tác dụng phụ)
  | "HAS_SYMPTOM" // Disease → Symptom
  | "COMORBID";   // Disease ↔ Disease

export interface GraphNode {
  id: string;
  name: string;
  normalized_name: string;
  type: EntityType;
  description?: string | null;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: RelationType;
  confidence?: number;
  evidence?: string | null;
  source_chunk_ids?: string[];  // PROJECT_CONTEXT §9 anti-hallucination
}

export interface DocumentGraph {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphOverview {
  entity_counts_by_type: Record<string, number>;
  relationship_count: number;
}

// Legacy types kept for compatibility with query/answer code (Phase 3)
export interface Entity {
  id: string;
  name: string;
  type: EntityType;
  document_ids: string[];
  mention_count: number;
}

export interface Relation {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  confidence: number;
}

export interface Citation {
  document_id: string;
  filename: string;
  page: number;
  snippet: string;
}

export interface QueryAnswer {
  question: string;
  answer: string;
  citations: Citation[];
  related_entities: Entity[];
  latency_ms: number;
}
